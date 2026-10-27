import html
import logging
import os
import socket
import smtplib
import ssl
import uuid
from email.message import EmailMessage

logger = logging.getLogger(__name__)


class EmailServiceError(RuntimeError):
    """Sanitized email-provider error with delivery outcome metadata."""

    def __init__(
        self,
        message: str,
        *,
        stage: str,
        delivery_status: str,
        correlation_id: str,
        status_code: int | None = None,
        request_id: str = "unavailable",
        client_request_id: str = "unavailable",
        retry_after: str | None = None,
    ):
        self.stage = stage
        self.delivery_status = delivery_status
        self.correlation_id = correlation_id
        self.status_code = status_code
        self.request_id = request_id
        self.client_request_id = client_request_id
        self.retry_after = retry_after
        super().__init__(
            f"{message} stage={stage} "
            f"delivery_status={delivery_status} "
            f"status_code={status_code or 'unavailable'} "
            f"correlation_id={correlation_id}"
        )


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Required email configuration is missing: {name}")
    return value



# Use IPv4 for this application's SMTP connection because IPv6 is
# unreachable from the current server network.
_ORIGINAL_SMTP = smtplib.SMTP


class _IPv4SMTP(_ORIGINAL_SMTP):
    def _get_socket(self, host, port, timeout):
        addresses = socket.getaddrinfo(
            host, port, socket.AF_INET, socket.SOCK_STREAM
        )
        last_error = None

        for family, socktype, proto, _, sockaddr in addresses:
            sock = None
            try:
                sock = socket.socket(family, socktype, proto)
                sock.settimeout(timeout)
                if self.source_address:
                    sock.bind(self.source_address)
                sock.connect(sockaddr)
                return sock
            except OSError as exc:
                last_error = exc
                if sock is not None:
                    sock.close()

        if last_error is not None:
            raise last_error
        raise OSError(f"No IPv4 address found for SMTP host {host!r}")


def _smtp_client(host, port, timeout):
    # Preserve existing SMTP mocks used by the unit tests.
    factory = smtplib.SMTP
    if factory is not _ORIGINAL_SMTP:
        return factory(host, port, timeout=timeout)
    return _IPv4SMTP(host, port, timeout=timeout)


def send_password_reset_email(recipient: str, reset_url: str) -> None:
    """Send a password-reset email through authenticated SMTP with STARTTLS."""

    correlation_id = str(uuid.uuid4())

    try:
        username = _required_env("SMTP_USERNAME")
        password = _required_env("SMTP_PASSWORD")
        sender_email = _required_env("SMTP_SENDER_EMAIL")
        host = os.getenv("SMTP_HOST", "smtp.office365.com").strip()
        port = int(os.getenv("SMTP_PORT", "587").strip())

        if not host or not 1 <= port <= 65535:
            raise ValueError("Invalid SMTP host or port.")
    except (RuntimeError, ValueError):
        logger.warning(
            "PASSWORD_RESET_PROVIDER_FAILURE "
            "stage=configuration outcome=not_sent correlation_id=%s",
            correlation_id,
        )
        raise EmailServiceError(
            "Required SMTP configuration is missing or invalid.",
            stage="configuration",
            delivery_status="not_sent",
            correlation_id=correlation_id,
        ) from None

    safe_url = html.escape(reset_url, quote=True)
    message = EmailMessage()
    message["Subject"] = "Reset your GreenUp PCB LIS password"
    message["From"] = sender_email
    message["To"] = recipient
    message.set_content(
        "A password-reset request was made for your GreenUp PCB LIS account.\n\n"
        f"Reset your password using this link:\n{reset_url}\n\n"
        "This link expires in 30 minutes. "
        "If you did not request a reset, ignore this email."
    )
    message.add_alternative(
        "<p>A password-reset request was made for your "
        "GreenUp PCB LIS account.</p>"
        f'<p><a href="{safe_url}">Reset your password</a></p>'
        "<p>This link expires in 30 minutes. "
        "If you did not request a reset, ignore this email.</p>",
        subtype="html",
    )

    stage = "smtp_connect"
    send_attempt_started = False

    try:
        with _smtp_client(host, port, timeout=20) as smtp:
            stage = "smtp_ehlo"
            smtp.ehlo()

            stage = "smtp_tls"
            smtp.starttls(context=ssl.create_default_context())
            smtp.ehlo()

            stage = "smtp_auth"
            smtp.login(username, password)

            stage = "send_mail"
            send_attempt_started = True
            refused = smtp.send_message(
                message,
                from_addr=sender_email,
                to_addrs=[recipient],
            )

            if refused:
                first_refusal = next(iter(refused.values()), None)
                status_code = (
                    first_refusal[0]
                    if isinstance(first_refusal, tuple)
                    and first_refusal
                    else None
                )
                logger.warning(
                    "PASSWORD_RESET_PROVIDER_FAILURE "
                    "stage=send_mail outcome=not_sent status_code=%s "
                    "correlation_id=%s",
                    status_code or "unavailable",
                    correlation_id,
                )
                raise EmailServiceError(
                    "SMTP server rejected the recipient.",
                    stage="send_mail",
                    delivery_status="not_sent",
                    correlation_id=correlation_id,
                    status_code=status_code,
                )

        logger.info(
            "PASSWORD_RESET_EMAIL_ACCEPTED_BY_PROVIDER "
            "provider=smtp correlation_id=%s",
            correlation_id,
        )
        return

    except EmailServiceError:
        raise

    except smtplib.SMTPAuthenticationError as exc:
        status_code = exc.smtp_code
        delivery_status = "not_sent"
        stage = "smtp_auth"
        error_type = type(exc).__name__

    except smtplib.SMTPRecipientsRefused as exc:
        first_refusal = next(iter(exc.recipients.values()), None)
        status_code = (
            first_refusal[0]
            if isinstance(first_refusal, tuple) and first_refusal
            else None
        )
        delivery_status = "not_sent"
        stage = "send_mail"
        error_type = type(exc).__name__

    except (
        smtplib.SMTPConnectError,
        smtplib.SMTPHeloError,
        smtplib.SMTPNotSupportedError,
        smtplib.SMTPSenderRefused,
        smtplib.SMTPDataError,
        smtplib.SMTPResponseException,
    ) as exc:
        status_code = getattr(exc, "smtp_code", None)
        delivery_status = "not_sent"
        error_type = type(exc).__name__

    except Exception as exc:
        status_code = getattr(exc, "smtp_code", None)
        delivery_status = (
            "unknown" if send_attempt_started else "not_sent"
        )
        error_type = type(exc).__name__

    logger.warning(
        "PASSWORD_RESET_PROVIDER_FAILURE "
        "provider=smtp stage=%s outcome=%s status_code=%s "
        "correlation_id=%s error_type=%s",
        stage,
        delivery_status,
        status_code or "unavailable",
        correlation_id,
        error_type,
    )
    raise EmailServiceError(
        "SMTP email delivery failed.",
        stage=stage,
        delivery_status=delivery_status,
        correlation_id=correlation_id,
        status_code=status_code,
    ) from None

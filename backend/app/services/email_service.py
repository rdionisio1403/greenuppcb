import html
import logging
import os
import re
import uuid
from urllib.parse import quote

import httpx


logger = logging.getLogger(__name__)

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
TOKEN_BASE_URL = "https://login.microsoftonline.com"


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
        raise RuntimeError(
            f"Required email configuration is missing: {name}"
        )
    return value


def _safe_response_id(response: httpx.Response, header: str) -> str:
    value = response.headers.get(header, "").strip()
    if re.fullmatch(r"[A-Za-z0-9-]{1,128}", value):
        return value
    return "unavailable"


def _safe_retry_after(response: httpx.Response) -> str | None:
    value = response.headers.get("Retry-After", "").strip()
    if value.isdigit() and len(value) <= 6:
        return value
    return None


def _log_http_response(
    response: httpx.Response,
    *,
    stage: str,
    correlation_id: str,
    client_request_id: str,
) -> tuple[str, str]:
    request_id = _safe_response_id(response, "request-id")
    returned_client_id = _safe_response_id(
        response, "client-request-id"
    )
    if returned_client_id == "unavailable":
        returned_client_id = client_request_id

    logger.info(
        "PASSWORD_RESET_PROVIDER_RESPONSE "
        "stage=%s status_code=%s correlation_id=%s "
        "request_id=%s client_request_id=%s",
        stage,
        response.status_code,
        correlation_id,
        request_id,
        returned_client_id,
    )
    return request_id, returned_client_id


def send_password_reset_email(
    recipient: str,
    reset_url: str,
) -> None:
    """Send a password-reset email through Microsoft Graph."""

    correlation_id = str(uuid.uuid4())

    try:
        tenant_id = _required_env("MICROSOFT_TENANT_ID")
        client_id = _required_env("MICROSOFT_CLIENT_ID")
        client_secret = _required_env("MICROSOFT_CLIENT_SECRET")
        sender_email = _required_env("MICROSOFT_SENDER_EMAIL")
    except RuntimeError:
        logger.warning(
            "PASSWORD_RESET_PROVIDER_FAILURE "
            "stage=configuration outcome=not_sent "
            "correlation_id=%s",
            correlation_id,
        )
        raise EmailServiceError(
            "Required email configuration is missing.",
            stage="configuration",
            delivery_status="not_sent",
            correlation_id=correlation_id,
        ) from None

    token_client_request_id = str(uuid.uuid4())
    token_url = (
        f"{TOKEN_BASE_URL}/"
        f"{quote(tenant_id, safe='')}/oauth2/v2.0/token"
    )

    try:
        token_response = httpx.post(
            token_url,
            headers={
                "client-request-id": token_client_request_id,
                "return-client-request-id": "true",
            },
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "https://graph.microsoft.com/.default",
                "grant_type": "client_credentials",
            },
            timeout=20.0,
        )
    except httpx.RequestError as exc:
        logger.warning(
            "PASSWORD_RESET_PROVIDER_TRANSPORT_FAILURE "
            "stage=token_request outcome=not_sent "
            "correlation_id=%s client_request_id=%s error_type=%s",
            correlation_id,
            token_client_request_id,
            type(exc).__name__,
        )
        raise EmailServiceError(
            "Microsoft token request failed.",
            stage="token_request",
            delivery_status="not_sent",
            correlation_id=correlation_id,
            client_request_id=token_client_request_id,
        ) from None

    token_request_id, token_returned_client_id = _log_http_response(
        token_response,
        stage="token_request",
        correlation_id=correlation_id,
        client_request_id=token_client_request_id,
    )

    if token_response.status_code != 200:
        logger.warning(
            "PASSWORD_RESET_PROVIDER_FAILURE "
            "stage=token_request outcome=not_sent "
            "status_code=%s correlation_id=%s request_id=%s "
            "client_request_id=%s",
            token_response.status_code,
            correlation_id,
            token_request_id,
            token_returned_client_id,
        )
        raise EmailServiceError(
            "Microsoft token request was rejected.",
            stage="token_request",
            delivery_status="not_sent",
            correlation_id=correlation_id,
            status_code=token_response.status_code,
            request_id=token_request_id,
            client_request_id=token_returned_client_id,
        )

    try:
        token_payload = token_response.json()
    except ValueError:
        token_payload = None

    access_token = (
        token_payload.get("access_token")
        if isinstance(token_payload, dict)
        else None
    )
    if not isinstance(access_token, str) or not access_token.strip():
        logger.warning(
            "PASSWORD_RESET_PROVIDER_FAILURE "
            "stage=token_response outcome=not_sent "
            "correlation_id=%s request_id=%s client_request_id=%s "
            "reason=missing_access_token",
            correlation_id,
            token_request_id,
            token_returned_client_id,
        )
        raise EmailServiceError(
            "Microsoft identity platform returned no access token.",
            stage="token_response",
            delivery_status="not_sent",
            correlation_id=correlation_id,
            status_code=token_response.status_code,
            request_id=token_request_id,
            client_request_id=token_returned_client_id,
        )

    safe_url = html.escape(reset_url, quote=True)
    message = {
        "message": {
            "subject": "Reset your GreenUp PCB LIS password",
            "body": {
                "contentType": "HTML",
                "content": (
                    "<p>A password-reset request was made for your "
                    "GreenUp PCB LIS account.</p>"
                    f'<p><a href="{safe_url}">Reset your password</a></p>'
                    "<p>This link expires in 30 minutes. "
                    "If you did not request a reset, ignore this email.</p>"
                ),
            },
            "toRecipients": [
                {"emailAddress": {"address": recipient}}
            ],
        },
        "saveToSentItems": True,
    }

    send_client_request_id = str(uuid.uuid4())
    send_url = (
        f"{GRAPH_BASE_URL}/users/"
        f"{quote(sender_email, safe='')}/sendMail"
    )

    try:
        response = httpx.post(
            send_url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "client-request-id": send_client_request_id,
                "return-client-request-id": "true",
            },
            json=message,
            timeout=20.0,
        )
    except (httpx.ConnectTimeout, httpx.ConnectError, httpx.PoolTimeout) as exc:
        logger.warning(
            "PASSWORD_RESET_PROVIDER_TRANSPORT_FAILURE "
            "stage=send_mail outcome=not_sent "
            "correlation_id=%s client_request_id=%s error_type=%s",
            correlation_id,
            send_client_request_id,
            type(exc).__name__,
        )
        raise EmailServiceError(
            "Microsoft sendMail connection could not be established.",
            stage="send_mail",
            delivery_status="not_sent",
            correlation_id=correlation_id,
            client_request_id=send_client_request_id,
        ) from None
    except httpx.RequestError as exc:
        # The request may have reached Microsoft before the response failed.
        logger.warning(
            "PASSWORD_RESET_PROVIDER_TRANSPORT_FAILURE "
            "stage=send_mail outcome=unknown "
            "correlation_id=%s client_request_id=%s error_type=%s",
            correlation_id,
            send_client_request_id,
            type(exc).__name__,
        )
        raise EmailServiceError(
            "Microsoft sendMail outcome is unknown after a transport error.",
            stage="send_mail",
            delivery_status="unknown",
            correlation_id=correlation_id,
            client_request_id=send_client_request_id,
        ) from None

    request_id, returned_client_id = _log_http_response(
        response,
        stage="send_mail",
        correlation_id=correlation_id,
        client_request_id=send_client_request_id,
    )

    if response.status_code == 202:
        logger.info(
            "PASSWORD_RESET_EMAIL_ACCEPTED_BY_PROVIDER "
            "correlation_id=%s request_id=%s client_request_id=%s",
            correlation_id,
            request_id,
            returned_client_id,
        )
        return

    # A clear 4xx response is a rejection. For 3xx, 5xx, or unexpected
    # responses, conservatively treat acceptance as uncertain.
    delivery_status = (
        "not_sent"
        if 400 <= response.status_code < 500
        else "unknown"
    )
    retry_after = _safe_retry_after(response)

    logger.warning(
        "PASSWORD_RESET_PROVIDER_FAILURE "
        "stage=send_mail outcome=%s status_code=%s "
        "correlation_id=%s request_id=%s client_request_id=%s "
        "retry_after=%s",
        delivery_status,
        response.status_code,
        correlation_id,
        request_id,
        returned_client_id,
        retry_after or "unavailable",
    )

    raise EmailServiceError(
        "Microsoft Graph did not accept the sendMail request.",
        stage="send_mail",
        delivery_status=delivery_status,
        correlation_id=correlation_id,
        status_code=response.status_code,
        request_id=request_id,
        client_request_id=returned_client_id,
        retry_after=retry_after,
    )

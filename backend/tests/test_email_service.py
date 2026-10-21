import smtplib
import ssl

import pytest

from app.services import email_service


SENDER = "greenuppcb.hub@ipcb.pt"
RECIPIENT = "recipient@example.com"
RESET_URL = "https://greenuppcb.ipcb.pt/reset-password?token=abc&source=test"


class FakeSMTP:
    instances = []
    constructor_error = None
    starttls_error = None
    login_error = None
    send_error = None
    refused = {}

    @classmethod
    def reset(cls):
        cls.instances = []
        cls.constructor_error = None
        cls.starttls_error = None
        cls.login_error = None
        cls.send_error = None
        cls.refused = {}

    def __init__(self, host, port, timeout):
        if type(self).constructor_error:
            raise type(self).constructor_error
        self.host = host
        self.port = port
        self.timeout = timeout
        self.events = []
        self.message = None
        self.from_addr = None
        self.to_addrs = None
        type(self).instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def ehlo(self):
        self.events.append("ehlo")
        return 250, b"OK"

    def starttls(self, context):
        self.events.append("starttls")
        assert isinstance(context, ssl.SSLContext)
        if type(self).starttls_error:
            raise type(self).starttls_error
        return 220, b"Ready to start TLS"

    def login(self, username, password):
        self.events.append("login")
        self.username = username
        self.password = password
        if type(self).login_error:
            raise type(self).login_error
        return 235, b"Authenticated"

    def send_message(self, message, from_addr=None, to_addrs=None):
        self.events.append("send_message")
        self.message = message
        self.from_addr = from_addr
        self.to_addrs = to_addrs
        if type(self).send_error:
            raise type(self).send_error
        return type(self).refused


@pytest.fixture
def smtp_env(monkeypatch):
    FakeSMTP.reset()
    monkeypatch.setattr(email_service.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setenv("SMTP_HOST", "smtp.office365.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USERNAME", SENDER)
    monkeypatch.setenv("SMTP_PASSWORD", "test-password-not-real")
    monkeypatch.setenv("SMTP_SENDER_EMAIL", SENDER)
    return FakeSMTP


def test_smtp_email_uses_starttls_and_expected_message(smtp_env):
    email_service.send_password_reset_email(RECIPIENT, RESET_URL)

    smtp = smtp_env.instances[0]
    assert smtp.host == "smtp.office365.com"
    assert smtp.port == 587
    assert smtp.timeout == 20
    assert smtp.username == SENDER
    assert smtp.password == "test-password-not-real"
    assert smtp.events == [
        "ehlo", "starttls", "ehlo", "login", "send_message"
    ]
    assert smtp.from_addr == SENDER
    assert smtp.to_addrs == [RECIPIENT]
    assert smtp.message["From"] == SENDER
    assert smtp.message["To"] == RECIPIENT
    assert smtp.message["Subject"] == "Reset your GreenUp PCB LIS password"

    plain = smtp.message.get_body(preferencelist=("plain",)).get_content()
    html_body = smtp.message.get_body(preferencelist=("html",)).get_content()
    assert RESET_URL in plain
    assert "token=abc&amp;source=test" in html_body
    assert "expires in 30 minutes" in plain


def test_missing_smtp_configuration_fails_before_network_access(
    monkeypatch, smtp_env
):
    monkeypatch.delenv("SMTP_PASSWORD")

    with pytest.raises(email_service.EmailServiceError) as exc_info:
        email_service.send_password_reset_email(RECIPIENT, RESET_URL)

    assert exc_info.value.stage == "configuration"
    assert exc_info.value.delivery_status == "not_sent"
    assert smtp_env.instances == []


def test_invalid_smtp_port_fails_before_network_access(monkeypatch, smtp_env):
    monkeypatch.setenv("SMTP_PORT", "not-a-port")

    with pytest.raises(email_service.EmailServiceError) as exc_info:
        email_service.send_password_reset_email(RECIPIENT, RESET_URL)

    assert exc_info.value.stage == "configuration"
    assert exc_info.value.delivery_status == "not_sent"
    assert smtp_env.instances == []


def test_smtp_authentication_rejection_is_not_sent(smtp_env):
    smtp_env.login_error = smtplib.SMTPAuthenticationError(
        535, b"Authentication unsuccessful"
    )

    with pytest.raises(email_service.EmailServiceError) as exc_info:
        email_service.send_password_reset_email(RECIPIENT, RESET_URL)

    assert exc_info.value.stage == "smtp_auth"
    assert exc_info.value.delivery_status == "not_sent"
    assert exc_info.value.status_code == 535


def test_smtp_connection_timeout_is_not_sent(smtp_env):
    smtp_env.constructor_error = TimeoutError("simulated timeout")

    with pytest.raises(email_service.EmailServiceError) as exc_info:
        email_service.send_password_reset_email(RECIPIENT, RESET_URL)

    assert exc_info.value.stage == "smtp_connect"
    assert exc_info.value.delivery_status == "not_sent"


def test_starttls_failure_is_not_sent(smtp_env):
    smtp_env.starttls_error = smtplib.SMTPNotSupportedError(
        "STARTTLS unavailable"
    )

    with pytest.raises(email_service.EmailServiceError) as exc_info:
        email_service.send_password_reset_email(RECIPIENT, RESET_URL)

    assert exc_info.value.stage == "smtp_tls"
    assert exc_info.value.delivery_status == "not_sent"


def test_smtp_recipient_refusal_is_not_sent(smtp_env):
    smtp_env.send_error = smtplib.SMTPRecipientsRefused(
        {RECIPIENT: (550, b"Recipient rejected")}
    )

    with pytest.raises(email_service.EmailServiceError) as exc_info:
        email_service.send_password_reset_email(RECIPIENT, RESET_URL)

    assert exc_info.value.stage == "send_mail"
    assert exc_info.value.delivery_status == "not_sent"
    assert exc_info.value.status_code == 550


def test_smtp_data_rejection_is_not_sent(smtp_env):
    smtp_env.send_error = smtplib.SMTPDataError(550, b"Message rejected")

    with pytest.raises(email_service.EmailServiceError) as exc_info:
        email_service.send_password_reset_email(RECIPIENT, RESET_URL)

    assert exc_info.value.stage == "send_mail"
    assert exc_info.value.delivery_status == "not_sent"
    assert exc_info.value.status_code == 550


def test_smtp_disconnect_after_send_started_has_unknown_outcome(smtp_env):
    smtp_env.send_error = smtplib.SMTPServerDisconnected(
        "simulated disconnect after DATA started"
    )

    with pytest.raises(email_service.EmailServiceError) as exc_info:
        email_service.send_password_reset_email(RECIPIENT, RESET_URL)

    assert exc_info.value.stage == "send_mail"
    assert exc_info.value.delivery_status == "unknown"


def test_smtp_returned_recipient_refusal_is_not_sent(smtp_env):
    smtp_env.refused = {RECIPIENT: (550, b"Recipient rejected")}

    with pytest.raises(email_service.EmailServiceError) as exc_info:
        email_service.send_password_reset_email(RECIPIENT, RESET_URL)

    assert exc_info.value.stage == "send_mail"
    assert exc_info.value.delivery_status == "not_sent"
    assert exc_info.value.status_code == 550

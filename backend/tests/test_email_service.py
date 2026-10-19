import httpx
import pytest

from app.services import email_service


ENV_KEYS = (
    "MICROSOFT_TENANT_ID",
    "MICROSOFT_CLIENT_ID",
    "MICROSOFT_CLIENT_SECRET",
    "MICROSOFT_SENDER_EMAIL",
)


def set_graph_environment(monkeypatch):
    monkeypatch.setenv("MICROSOFT_TENANT_ID", "test-tenant-id")
    monkeypatch.setenv("MICROSOFT_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("MICROSOFT_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("MICROSOFT_SENDER_EMAIL", "greenuppcb@ipcb.pt")


def make_response(status_code, url, json_body=None):
    request = httpx.Request("POST", url)
    if json_body is None:
        return httpx.Response(status_code, request=request)
    return httpx.Response(status_code, json=json_body, request=request)


def test_graph_email_uses_client_credentials_and_expected_message(
    monkeypatch,
):
    set_graph_environment(monkeypatch)
    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        if url.endswith("/oauth2/v2.0/token"):
            return make_response(
                200,
                url,
                {"access_token": "test-access-token"},
            )
        return make_response(202, url)

    monkeypatch.setattr(email_service.httpx, "post", fake_post)

    reset_url = (
        "https://greenuppcb.ipcb.pt/reset-password"
        "?token=dummy-token&source=unit-test"
    )
    email_service.send_password_reset_email(
        recipient="recipient@example.com",
        reset_url=reset_url,
    )

    assert len(calls) == 2

    token_url, token_kwargs = calls[0]
    assert token_url == (
        "https://login.microsoftonline.com/"
        "test-tenant-id/oauth2/v2.0/token"
    )
    assert token_kwargs["data"]["grant_type"] == "client_credentials"
    assert token_kwargs["data"]["client_id"] == "test-client-id"
    assert token_kwargs["data"]["scope"] == (
        "https://graph.microsoft.com/.default"
    )

    send_url, send_kwargs = calls[1]
    assert send_url == (
        "https://graph.microsoft.com/v1.0/"
        "users/greenuppcb%40ipcb.pt/sendMail"
    )
    assert send_kwargs["headers"]["Authorization"] == (
        "Bearer test-access-token"
    )

    message = send_kwargs["json"]["message"]
    assert message["toRecipients"][0]["emailAddress"]["address"] == (
        "recipient@example.com"
    )
    assert message["body"]["contentType"] == "HTML"
    assert "&amp;source=unit-test" in message["body"]["content"]


def test_missing_graph_configuration_fails_before_network_access(
    monkeypatch,
):
    for name in ENV_KEYS:
        monkeypatch.delenv(name, raising=False)

    def unexpected_post(*args, **kwargs):
        pytest.fail("HTTP request must not occur without configuration.")

    monkeypatch.setattr(email_service.httpx, "post", unexpected_post)

    with pytest.raises(email_service.EmailServiceError) as exc_info:
        email_service.send_password_reset_email(
            recipient="recipient@example.com",
            reset_url="https://greenuppcb.ipcb.pt/reset-password?token=dummy",
        )

    assert exc_info.value.stage == "configuration"
    assert exc_info.value.delivery_status == "not_sent"


def test_token_endpoint_error_prevents_graph_send(monkeypatch):
    set_graph_environment(monkeypatch)
    calls = []

    def fake_post(url, **kwargs):
        calls.append(url)
        return make_response(401, url, {"error": "invalid_client"})

    monkeypatch.setattr(email_service.httpx, "post", fake_post)

    with pytest.raises(email_service.EmailServiceError) as exc_info:
        email_service.send_password_reset_email(
            recipient="recipient@example.com",
            reset_url="https://greenuppcb.ipcb.pt/reset-password?token=dummy",
        )

    assert exc_info.value.stage == "token_request"
    assert exc_info.value.delivery_status == "not_sent"
    assert exc_info.value.status_code == 401
    assert len(calls) == 1
    assert calls[0].endswith("/oauth2/v2.0/token")


def test_graph_send_error_is_reported(monkeypatch):
    set_graph_environment(monkeypatch)
    calls = []

    def fake_post(url, **kwargs):
        calls.append(url)
        if url.endswith("/oauth2/v2.0/token"):
            return make_response(
                200,
                url,
                {"access_token": "test-access-token"},
            )
        return make_response(403, url, {"error": "access_denied"})

    monkeypatch.setattr(email_service.httpx, "post", fake_post)

    with pytest.raises(email_service.EmailServiceError) as exc_info:
        email_service.send_password_reset_email(
            recipient="recipient@example.com",
            reset_url="https://greenuppcb.ipcb.pt/reset-password?token=dummy",
        )

    assert exc_info.value.stage == "send_mail"
    assert exc_info.value.delivery_status == "not_sent"
    assert exc_info.value.status_code == 403
    assert len(calls) == 2
    assert calls[1].endswith("/sendMail")


def test_token_response_without_access_token_is_rejected(monkeypatch):
    set_graph_environment(monkeypatch)
    calls = []

    def fake_post(url, **kwargs):
        calls.append(url)
        return make_response(200, url, {"expires_in": 3600})

    monkeypatch.setattr(email_service.httpx, "post", fake_post)

    with pytest.raises(email_service.EmailServiceError) as exc_info:
        email_service.send_password_reset_email(
            recipient="recipient@example.com",
            reset_url="https://greenuppcb.ipcb.pt/reset-password?token=dummy-token-value",
        )

    assert exc_info.value.stage == "token_response"
    assert exc_info.value.delivery_status == "not_sent"
    assert len(calls) == 1
    assert "dummy-token-value" not in str(exc_info.value)



def test_token_endpoint_timeout_is_classified_as_not_sent(monkeypatch):
    set_graph_environment(monkeypatch)
    calls = []

    def fake_post(url, **kwargs):
        calls.append(url)
        raise httpx.ConnectTimeout(
            "simulated timeout",
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(email_service.httpx, "post", fake_post)

    with pytest.raises(email_service.EmailServiceError) as exc_info:
        email_service.send_password_reset_email(
            recipient="recipient@example.com",
            reset_url="https://greenuppcb.ipcb.pt/reset-password?token=dummy",
        )

    assert exc_info.value.stage == "token_request"
    assert exc_info.value.delivery_status == "not_sent"
    assert len(calls) == 1



def test_sendmail_429_exposes_retry_after_without_retrying(monkeypatch):
    set_graph_environment(monkeypatch)
    calls = []

    def fake_post(url, **kwargs):
        calls.append(url)
        if url.endswith("/oauth2/v2.0/token"):
            return make_response(200, url, {"access_token": "test-access-token"})
        return httpx.Response(
            429,
            headers={
                "Retry-After": "7",
                "request-id": "11111111-1111-1111-1111-111111111111",
            },
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(email_service.httpx, "post", fake_post)

    with pytest.raises(email_service.EmailServiceError) as exc_info:
        email_service.send_password_reset_email(
            recipient="recipient@example.com",
            reset_url="https://greenuppcb.ipcb.pt/reset-password?token=dummy",
        )

    error = exc_info.value
    assert error.stage == "send_mail"
    assert error.delivery_status == "not_sent"
    assert error.status_code == 429
    assert error.retry_after == "7"
    assert error.request_id == "11111111-1111-1111-1111-111111111111"
    assert len(calls) == 2



def test_sendmail_503_marks_outcome_unknown_without_retrying(monkeypatch):
    set_graph_environment(monkeypatch)
    calls = []

    def fake_post(url, **kwargs):
        calls.append(url)
        if url.endswith("/oauth2/v2.0/token"):
            return make_response(200, url, {"access_token": "test-access-token"})
        return make_response(503, url, {"error": "temporarily_unavailable"})

    monkeypatch.setattr(email_service.httpx, "post", fake_post)

    with pytest.raises(email_service.EmailServiceError) as exc_info:
        email_service.send_password_reset_email(
            recipient="recipient@example.com",
            reset_url="https://greenuppcb.ipcb.pt/reset-password?token=dummy",
        )

    assert exc_info.value.stage == "send_mail"
    assert exc_info.value.delivery_status == "unknown"
    assert exc_info.value.status_code == 503
    assert len(calls) == 2



def test_sendmail_read_timeout_marks_outcome_unknown_without_retrying(monkeypatch):
    set_graph_environment(monkeypatch)
    calls = []

    def fake_post(url, **kwargs):
        calls.append(url)
        if url.endswith("/oauth2/v2.0/token"):
            return make_response(200, url, {"access_token": "test-access-token"})
        raise httpx.ReadTimeout(
            "simulated read timeout",
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(email_service.httpx, "post", fake_post)

    with pytest.raises(email_service.EmailServiceError) as exc_info:
        email_service.send_password_reset_email(
            recipient="recipient@example.com",
            reset_url="https://greenuppcb.ipcb.pt/reset-password?token=dummy-token-value",
        )

    assert exc_info.value.stage == "send_mail"
    assert exc_info.value.delivery_status == "unknown"
    assert len(calls) == 2
    assert "dummy-token-value" not in str(exc_info.value)
    assert "test-access-token" not in str(exc_info.value)

import html
import logging
import os
from urllib.parse import quote

import httpx


logger = logging.getLogger(__name__)

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
TOKEN_BASE_URL = "https://login.microsoftonline.com"


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Required email configuration is missing: {name}"
        )
    return value


def send_password_reset_email(
    recipient: str,
    reset_url: str,
) -> None:
    """
    Send a password-reset email through Microsoft Graph.

    Requires an institution-approved Entra application with
    the necessary Microsoft Graph Mail.Send permission.
    """
    tenant_id = _required_env("MICROSOFT_TENANT_ID")
    client_id = _required_env("MICROSOFT_CLIENT_ID")
    client_secret = _required_env("MICROSOFT_CLIENT_SECRET")
    sender_email = _required_env("MICROSOFT_SENDER_EMAIL")

    token_url = (
        f"{TOKEN_BASE_URL}/"
        f"{quote(tenant_id, safe='')}/oauth2/v2.0/token"
    )

    token_response = httpx.post(
        token_url,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        },
        timeout=20.0,
    )
    token_response.raise_for_status()

    access_token = token_response.json().get("access_token")
    if not access_token:
        raise RuntimeError(
            "Microsoft identity platform returned no access token."
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
                {
                    "emailAddress": {
                        "address": recipient,
                    }
                }
            ],
        },
        "saveToSentItems": True,
    }

    send_url = (
        f"{GRAPH_BASE_URL}/users/"
        f"{quote(sender_email, safe='')}/sendMail"
    )

    response = httpx.post(
        send_url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json=message,
        timeout=20.0,
    )

    if response.status_code != 202:
        response.raise_for_status()
        raise RuntimeError(
            "Microsoft Graph did not return the expected accepted status."
        )

    logger.info("Password-reset email accepted by Microsoft Graph.")

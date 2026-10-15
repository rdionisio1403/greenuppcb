from datetime import datetime, timedelta, timezone
import os
import uuid
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.dependencies import get_db
from app.main import app
from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.security import hash_password, generate_reset_token, hash_reset_token, verify_password
from app.rate_limiter import reset_attempts


def _test_session_factory():
    value = os.environ.get("DATABASE_URL")
    if not value:
        raise RuntimeError("DATABASE_URL is required for reset endpoint tests.")

    url = make_url(value)
    if url.database != "greenupcb_test":
        raise RuntimeError("Refusing to run reset endpoint tests outside greenupcb_test.")

    engine = create_engine(url)
    with engine.connect() as connection:
        actual = connection.execute(text("SELECT current_database()")).scalar_one()
    if actual != "greenupcb_test":
        engine.dispose()
        raise RuntimeError("Connected database is not greenupcb_test.")

    return engine, sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def reset_test_context():
    engine, session_factory = _test_session_factory()
    db = session_factory()
    username = f"reset_test_{uuid.uuid4().hex[:12]}"
    user = User(
        username=username,
        email=f"{username}@example.com",
        password_hash=hash_password("Original-Strong-Password-2026!"),
        role="user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    def issue_token(expires_at):
        raw_token = generate_reset_token()
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hash_reset_token(raw_token),
                expires_at=expires_at,
            )
        )
        db.commit()
        return raw_token

    try:
        yield db, user, issue_token
    finally:
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id
        ).delete(synchronize_session=False)
        db.query(User).filter(User.id == user.id).delete(synchronize_session=False)
        db.commit()
        db.close()
        engine.dispose()


@pytest.fixture
def reset_client(reset_test_context):
    db, _, _ = reset_test_context

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app, base_url="https://testserver") as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_db, None)


def _payload(token, password="New-Strong-Password-2026!"):
    return {
        "token": token,
        "new_password": password,
        "confirm_password": password,
    }


def test_valid_token_resets_password_and_marks_token_used(reset_test_context, reset_client):
    db, user, issue_token = reset_test_context
    raw_token = issue_token(datetime.now(timezone.utc) + timedelta(minutes=20))
    response = reset_client.post("/auth/password-reset/confirm", json=_payload(raw_token))

    assert response.status_code == 200, response.text
    db.refresh(user)
    assert verify_password("New-Strong-Password-2026!", user.password_hash)

    stored = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == hash_reset_token(raw_token)
    ).one()
    assert stored.used_at is not None

    second_response = reset_client.post(
        "/auth/password-reset/confirm",
        json=_payload(raw_token, "Another-Strong-Password-2026!"),
    )
    assert second_response.status_code == 400


def test_expired_token_is_rejected(reset_test_context, reset_client):
    _, _, issue_token = reset_test_context
    raw_token = issue_token(datetime.now(timezone.utc) - timedelta(minutes=1))

    response = reset_client.post("/auth/password-reset/confirm", json=_payload(raw_token))

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired password reset token."


def test_unknown_token_is_rejected(reset_client):
    response = reset_client.post(
        "/auth/password-reset/confirm",
        json=_payload(generate_reset_token()),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired password reset token."

def test_valid_token_revokes_existing_sessions(reset_test_context, reset_client):
    from app.models.session import Session as UserSession

    db, user, issue_token = reset_test_context
    raw_token = issue_token(datetime.now(timezone.utc) + timedelta(minutes=20))

    session = UserSession(
        session_id=f"reset-session-{uuid.uuid4().hex}",
        csrf_token=f"csrf-{uuid.uuid4().hex}",
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        last_activity=datetime.now(timezone.utc),
    )
    db.add(session)
    db.commit()
    session_id = session.session_id

    response = reset_client.post(
        "/auth/password-reset/confirm",
        json=_payload(raw_token),
    )

    assert response.status_code == 200, response.text
    assert db.query(UserSession).filter(
        UserSession.session_id == session_id
    ).first() is None



def test_request_endpoint_returns_generic_response_without_creating_tokens(
    reset_test_context, reset_client
):
    db, user, _ = reset_test_context
    ip_key = "password-reset:ip:testclient"
    reset_attempts(ip_key)

    try:
        before = db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id
        ).count()

        known_response = reset_client.post(
            "/auth/password-reset/request",
            json={"email": user.email},
        )
        unknown_response = reset_client.post(
            "/auth/password-reset/request",
            json={"email": f"missing-{uuid.uuid4().hex}@example.com"},
        )

        assert known_response.status_code == 202, known_response.text
        assert unknown_response.status_code == 202, unknown_response.text
        assert known_response.json() == unknown_response.json()
        assert "Email delivery is not configured yet" in known_response.json()["message"]

        db.expire_all()
        after = db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id
        ).count()
        assert after == before
    finally:
        reset_attempts(ip_key)


def test_enabled_request_sends_reset_email_and_stores_only_token_hash(
    reset_test_context, reset_client, monkeypatch
):
    import app.routers.auth as auth_router

    db, user, _ = reset_test_context
    monkeypatch.setattr(auth_router, "PASSWORD_RESET_EMAIL_ENABLED", True)
    monkeypatch.setenv("PASSWORD_RESET_BASE_URL", "https://greenuppcb.ipcb.pt")

    deliveries = []
    monkeypatch.setattr(
        auth_router,
        "send_password_reset_email",
        lambda recipient, reset_url: deliveries.append((recipient, reset_url)),
    )

    ip_key = "password-reset:ip:testclient"
    reset_attempts(ip_key)
    try:
        response = reset_client.post(
            "/auth/password-reset/request",
            json={"email": user.email},
        )

        assert response.status_code == 202, response.text
        assert response.json()["message"] == auth_router.PASSWORD_RESET_REQUEST_MESSAGE
        assert len(deliveries) == 1

        recipient, reset_url = deliveries[0]
        assert recipient == user.email

        parsed_url = urlparse(reset_url)
        assert parsed_url.scheme == "https"
        assert parsed_url.netloc == "greenuppcb.ipcb.pt"
        assert parsed_url.path == "/reset-password"

        raw_token = parse_qs(parsed_url.query).get("token", [""])[0]
        assert len(raw_token) >= 32

        records = (
            db.query(PasswordResetToken)
            .filter(PasswordResetToken.user_id == user.id)
            .all()
        )
        assert len(records) == 1
        assert records[0].token_hash == hash_reset_token(raw_token)
        assert records[0].token_hash != raw_token
    finally:
        reset_attempts(ip_key)


def test_email_delivery_failure_removes_reset_token(
    reset_test_context, reset_client, monkeypatch
):
    import app.routers.auth as auth_router

    db, user, _ = reset_test_context
    monkeypatch.setattr(auth_router, "PASSWORD_RESET_EMAIL_ENABLED", True)
    monkeypatch.setenv("PASSWORD_RESET_BASE_URL", "https://greenuppcb.ipcb.pt")

    def fail_delivery(recipient, reset_url):
        raise RuntimeError("Simulated email provider failure")

    monkeypatch.setattr(
        auth_router, "send_password_reset_email", fail_delivery
    )

    ip_key = "password-reset:ip:testclient"
    reset_attempts(ip_key)
    try:
        response = reset_client.post(
            "/auth/password-reset/request",
            json={"email": user.email},
        )

        assert response.status_code == 202, response.text
        assert response.json()["message"] == auth_router.PASSWORD_RESET_REQUEST_MESSAGE

        db.expire_all()
        assert (
            db.query(PasswordResetToken)
            .filter(PasswordResetToken.user_id == user.id)
            .count()
            == 0
        )
    finally:
        reset_attempts(ip_key)

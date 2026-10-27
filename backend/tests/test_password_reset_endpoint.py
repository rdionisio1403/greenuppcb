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
from app.rate_limiter import MAX_ATTEMPTS, reset_attempts


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
        from app.models.session import Session as UserSession

        db.query(UserSession).filter(
            UserSession.user_id == user.id
        ).delete(synchronize_session=False)
        from app.models.audit_log import AuditLog

        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id
        ).delete(synchronize_session=False)
        db.query(AuditLog).filter(
            AuditLog.user_id == user.id
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

    from app.models.audit_log import AuditLog

    assert db.query(AuditLog).filter(
        AuditLog.user_id == user.id,
        AuditLog.event_type == "PASSWORD_RESET_COMPLETED",
    ).count() == 1


def test_audit_failure_rolls_back_password_reset(
    reset_test_context, reset_client, monkeypatch
):
    import app.routers.auth as auth_router

    db, user, issue_token = reset_test_context
    original_password = "Original-Strong-Password-2026!"
    raw_token = issue_token(
        datetime.now(timezone.utc) + timedelta(minutes=20)
    )

    def fail_audit(**kwargs):
        raise RuntimeError("Simulated audit persistence failure")

    monkeypatch.setattr(auth_router, "log_audit", fail_audit)

    response = reset_client.post(
        "/auth/password-reset/confirm",
        json=_payload(raw_token),
    )

    assert response.status_code == 500

    db.expire_all()
    db.refresh(user)
    assert verify_password(original_password, user.password_hash)

    stored = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == hash_reset_token(raw_token)
    ).one()
    assert stored.used_at is None


def test_same_reset_token_cannot_be_consumed_concurrently(
    reset_test_context,
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    db, user, issue_token = reset_test_context
    raw_token = issue_token(
        datetime.now(timezone.utc) + timedelta(minutes=20)
    )

    engine = db.get_bind()
    concurrent_session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    def override_get_db():
        request_db = concurrent_session_factory()
        try:
            yield request_db
        finally:
            request_db.close()

    had_previous_override = get_db in app.dependency_overrides
    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    barrier = Barrier(2)

    passwords = [
        "Violet-Telescope-482!Orchid",
        "Amber-Pineapple-739!Quartz",
    ]

    def submit_reset(password):
        with TestClient(app, base_url="https://testserver") as client:
            barrier.wait(timeout=10)
            return client.post(
                "/auth/password-reset/confirm",
                json=_payload(raw_token, password),
            )

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            first = executor.submit(submit_reset, passwords[0])
            second = executor.submit(submit_reset, passwords[1])
            responses = [
                first.result(timeout=30),
                second.result(timeout=30),
            ]

        assert sorted(r.status_code for r in responses) == [200, 400]

        db.expire_all()
        db.refresh(user)

        password_matches = sum(
            verify_password(password, user.password_hash)
            for password in passwords
        )
        assert password_matches == 1

        stored_token = (
            db.query(PasswordResetToken)
            .filter(
                PasswordResetToken.token_hash == hash_reset_token(raw_token)
            )
            .one()
        )
        assert stored_token.used_at is not None

    finally:
        if had_previous_override:
            app.dependency_overrides[get_db] = previous_override
        else:
            app.dependency_overrides.pop(get_db, None)


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
    reset_test_context, reset_client, monkeypatch
):
    import app.routers.auth as auth_router

    monkeypatch.setattr(auth_router, "PASSWORD_RESET_EMAIL_ENABLED", False)
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
        assert known_response.json()["message"] == auth_router.PASSWORD_RESET_DISABLED_MESSAGE

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


def test_new_reset_request_invalidates_previous_unused_token(
    reset_test_context, reset_client, monkeypatch
):
    import app.routers.auth as auth_router

    db, user, issue_token = reset_test_context
    previous_raw_token = issue_token(
        datetime.now(timezone.utc) + timedelta(minutes=20)
    )

    monkeypatch.setattr(auth_router, "PASSWORD_RESET_EMAIL_ENABLED", True)
    monkeypatch.setenv(
        "PASSWORD_RESET_BASE_URL", "https://greenuppcb.ipcb.pt"
    )

    deliveries = []
    monkeypatch.setattr(
        auth_router,
        "send_password_reset_email",
        lambda recipient, reset_url: deliveries.append(
            (recipient, reset_url)
        ),
    )

    ip_key = "password-reset:ip:testclient"
    email_key = auth_router._password_reset_email_rate_limit_key(
        user.email
    )

    reset_attempts(ip_key)
    reset_attempts(email_key)

    try:
        response = reset_client.post(
            "/auth/password-reset/request",
            json={"email": user.email},
        )

        assert response.status_code == 202, response.text
        assert len(deliveries) == 1

        recipient, reset_url = deliveries[0]
        assert recipient == user.email

        new_raw_token = parse_qs(
            urlparse(reset_url).query
        ).get("token", [""])[0]

        assert new_raw_token
        assert new_raw_token != previous_raw_token

        db.expire_all()
        records = (
            db.query(PasswordResetToken)
            .filter(PasswordResetToken.user_id == user.id)
            .all()
        )

        assert len(records) == 1
        assert records[0].token_hash == hash_reset_token(new_raw_token)
        assert records[0].token_hash != hash_reset_token(previous_raw_token)

        old_response = reset_client.post(
            "/auth/password-reset/confirm",
            json=_payload(previous_raw_token),
        )
        assert old_response.status_code == 400

        new_response = reset_client.post(
            "/auth/password-reset/confirm",
            json=_payload(new_raw_token),
        )
        assert new_response.status_code == 200, new_response.text

    finally:
        reset_attempts(ip_key)
        reset_attempts(email_key)


def test_email_delivery_failure_removes_reset_token(
    reset_test_context, reset_client, monkeypatch
):
    import app.routers.auth as auth_router

    db, user, _ = reset_test_context
    monkeypatch.setattr(auth_router, "PASSWORD_RESET_EMAIL_ENABLED", True)
    monkeypatch.setenv("PASSWORD_RESET_BASE_URL", "https://greenuppcb.ipcb.pt")

    def fail_delivery(recipient, reset_url):
        raise auth_router.EmailServiceError(
            "Simulated email provider rejection.",
            stage="send_mail",
            delivery_status="not_sent",
            correlation_id="test-correlation",
        )

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


def test_password_reset_request_is_rate_limited_per_email(
    reset_test_context, reset_client, monkeypatch
):
    import app.routers.auth as auth_router

    _, user, _ = reset_test_context
    monkeypatch.setattr(auth_router, "PASSWORD_RESET_EMAIL_ENABLED", True)
    monkeypatch.setenv(
        "PASSWORD_RESET_BASE_URL", "https://greenuppcb.ipcb.pt"
    )

    deliveries = []
    monkeypatch.setattr(
        auth_router,
        "send_password_reset_email",
        lambda recipient, reset_url: deliveries.append(
            (recipient, reset_url)
        ),
    )

    ip_key = "password-reset:ip:testclient"
    email_key = auth_router._password_reset_email_rate_limit_key(
        user.email
    )

    reset_attempts(ip_key)
    reset_attempts(email_key)

    responses = []
    try:
        for index in range(MAX_ATTEMPTS + 1):
            # Reset only the IP counter to isolate the per-email limit.
            reset_attempts(ip_key)
            requested_email = (
                user.email.upper() if index % 2 else user.email
            )
            response = reset_client.post(
                "/auth/password-reset/request",
                json={"email": requested_email},
            )
            responses.append(response)

        assert all(r.status_code == 202 for r in responses)
        assert all(
            r.json()["message"] == auth_router.PASSWORD_RESET_REQUEST_MESSAGE
            for r in responses
        )
        assert len(deliveries) == MAX_ATTEMPTS
    finally:
        reset_attempts(ip_key)
        reset_attempts(email_key)


def test_unknown_email_delivery_outcome_keeps_reset_token(
    reset_test_context, reset_client, monkeypatch
):
    import app.routers.auth as auth_router

    db, user, _ = reset_test_context
    monkeypatch.setattr(auth_router, "PASSWORD_RESET_EMAIL_ENABLED", True)
    monkeypatch.setenv(
        "PASSWORD_RESET_BASE_URL", "https://greenuppcb.ipcb.pt"
    )

    def uncertain_delivery(recipient, reset_url):
        raise auth_router.EmailServiceError(
            "Simulated uncertain provider outcome.",
            stage="send_mail",
            delivery_status="unknown",
            correlation_id="test-correlation-unknown",
        )

    monkeypatch.setattr(
        auth_router, "send_password_reset_email", uncertain_delivery
    )

    ip_key = "password-reset:ip:testclient"
    email_key = auth_router._password_reset_email_rate_limit_key(
        user.email
    )

    reset_attempts(ip_key)
    reset_attempts(email_key)

    try:
        response = reset_client.post(
            "/auth/password-reset/request",
            json={"email": user.email},
        )

        assert response.status_code == 202, response.text
        assert response.json()["message"] == auth_router.PASSWORD_RESET_REQUEST_MESSAGE

        db.expire_all()
        records = (
            db.query(PasswordResetToken)
            .filter(PasswordResetToken.user_id == user.id)
            .all()
        )
        assert len(records) == 1
        assert records[0].used_at is None

    finally:
        reset_attempts(ip_key)
        reset_attempts(email_key)

def _create_password_change_session(db, user, client):
    from app.models.session import Session as UserSession

    session_id = f"password-change-{uuid.uuid4().hex}"
    csrf_token = f"csrf-{uuid.uuid4().hex}"

    db.add(
        UserSession(
            session_id=session_id,
            csrf_token=csrf_token,
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            last_activity=datetime.now(timezone.utc),
        )
    )
    db.commit()

    client.cookies.set(
        "__Host-session_id",
        session_id,
        path="/",
    )
    return session_id, csrf_token


def test_password_change_revokes_sessions_and_audits(
    reset_test_context, reset_client
):
    from app.models.audit_log import AuditLog
    from app.models.session import Session as UserSession

    db, user, _ = reset_test_context
    session_id, csrf_token = _create_password_change_session(
        db, user, reset_client
    )
    new_password = "Changed-Strong-Password-2026!"

    response = reset_client.post(
        "/auth/change-password",
        headers={"X-CSRF-Token": csrf_token},
        json={
            "current_password": "Original-Strong-Password-2026!",
            "new_password": new_password,
            "confirm_password": new_password,
        },
    )

    assert response.status_code == 200, response.text

    db.expire_all()
    db.refresh(user)
    assert verify_password(new_password, user.password_hash)
    assert db.query(UserSession).filter(
        UserSession.session_id == session_id
    ).first() is None
    assert db.query(AuditLog).filter(
        AuditLog.user_id == user.id,
        AuditLog.event_type == "PASSWORD_CHANGED",
    ).count() == 1


def test_password_change_audit_failure_rolls_back(
    reset_test_context, reset_client, monkeypatch
):
    import app.routers.auth as auth_router
    from app.models.audit_log import AuditLog
    from app.models.session import Session as UserSession

    db, user, _ = reset_test_context
    original_password = "Original-Strong-Password-2026!"
    session_id, csrf_token = _create_password_change_session(
        db, user, reset_client
    )

    def fail_audit(**kwargs):
        raise RuntimeError("Simulated audit persistence failure")

    monkeypatch.setattr(auth_router, "log_audit", fail_audit)

    new_password = "Changed-Strong-Password-2026!"
    response = reset_client.post(
        "/auth/change-password",
        headers={"X-CSRF-Token": csrf_token},
        json={
            "current_password": original_password,
            "new_password": new_password,
            "confirm_password": new_password,
        },
    )

    assert response.status_code == 500, response.text

    db.expire_all()
    db.refresh(user)
    assert verify_password(original_password, user.password_hash)
    assert db.query(UserSession).filter(
        UserSession.session_id == session_id
    ).first() is not None
    assert db.query(AuditLog).filter(
        AuditLog.user_id == user.id,
        AuditLog.event_type == "PASSWORD_CHANGED",
    ).count() == 0

def _make_admin_revocation_session(db, user):
    from app.models.session import Session as UserSession

    user.role = "admin"
    session = UserSession(
        session_id=f"admin-revoke-{uuid.uuid4().hex}",
        csrf_token=f"csrf-{uuid.uuid4().hex}",
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        last_activity=datetime.now(timezone.utc),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def _admin_revocation_request():
    from types import SimpleNamespace
    return SimpleNamespace(client=None)


def test_admin_revoke_one_session_and_audits(reset_test_context):
    import app.routers.user as user_router
    from app.models.audit_log import AuditLog
    from app.models.session import Session as UserSession

    db, user, _ = reset_test_context
    session = _make_admin_revocation_session(db, user)
    session_pk = session.id

    result = user_router.revoke_user_session(
        request=_admin_revocation_request(),
        user_id=user.id,
        session_id=session_pk,
        db=db,
        current_user=user,
        _csrf_session=session,
    )

    assert result == {"message": "Session revoked"}
    db.expire_all()
    assert db.query(UserSession).filter(
        UserSession.id == session_pk
    ).first() is None
    audit = db.query(AuditLog).filter(
        AuditLog.user_id == user.id,
        AuditLog.event_type == "SESSION_REVOKED",
    ).one()
    assert f"revoked_session_id={session_pk}" in audit.details


def test_admin_revoke_one_session_audit_failure_rolls_back(
    reset_test_context, monkeypatch
):
    import pytest
    from fastapi import HTTPException
    import app.routers.user as user_router
    from app.models.audit_log import AuditLog
    from app.models.session import Session as UserSession

    db, user, _ = reset_test_context
    session = _make_admin_revocation_session(db, user)
    session_pk = session.id

    def fail_audit(**kwargs):
        raise RuntimeError("Simulated audit persistence failure")

    monkeypatch.setattr(user_router, "log_audit", fail_audit)

    with pytest.raises(HTTPException) as exc:
        user_router.revoke_user_session(
            request=_admin_revocation_request(),
            user_id=user.id,
            session_id=session_pk,
            db=db,
            current_user=user,
            _csrf_session=session,
        )

    assert exc.value.status_code == 500
    db.expire_all()
    assert db.query(UserSession).filter(
        UserSession.id == session_pk
    ).first() is not None
    assert db.query(AuditLog).filter(
        AuditLog.user_id == user.id,
        AuditLog.event_type == "SESSION_REVOKED",
    ).count() == 0


def test_admin_revoke_all_sessions_and_audits(reset_test_context):
    import app.routers.user as user_router
    from app.models.audit_log import AuditLog
    from app.models.session import Session as UserSession

    db, user, _ = reset_test_context
    sessions = [
        _make_admin_revocation_session(db, user),
        _make_admin_revocation_session(db, user),
    ]
    session_pks = [item.id for item in sessions]

    result = user_router.revoke_all_user_sessions(
        request=_admin_revocation_request(),
        user_id=user.id,
        db=db,
        current_user=user,
        _csrf_session=sessions[0],
    )

    assert result == {
        "message": "All sessions revoked",
        "revoked_count": 2,
    }
    db.expire_all()
    assert db.query(UserSession).filter(
        UserSession.id.in_(session_pks)
    ).count() == 0
    audit = db.query(AuditLog).filter(
        AuditLog.user_id == user.id,
        AuditLog.event_type == "SESSION_REVOKED",
    ).one()
    assert "count=2" in audit.details


def test_admin_revoke_all_sessions_audit_failure_rolls_back(
    reset_test_context, monkeypatch
):
    import pytest
    from fastapi import HTTPException
    import app.routers.user as user_router
    from app.models.audit_log import AuditLog
    from app.models.session import Session as UserSession

    db, user, _ = reset_test_context
    sessions = [
        _make_admin_revocation_session(db, user),
        _make_admin_revocation_session(db, user),
    ]
    session_pks = [item.id for item in sessions]

    def fail_audit(**kwargs):
        raise RuntimeError("Simulated audit persistence failure")

    monkeypatch.setattr(user_router, "log_audit", fail_audit)

    with pytest.raises(HTTPException) as exc:
        user_router.revoke_all_user_sessions(
            request=_admin_revocation_request(),
            user_id=user.id,
            db=db,
            current_user=user,
            _csrf_session=sessions[0],
        )

    assert exc.value.status_code == 500
    db.expire_all()
    assert db.query(UserSession).filter(
        UserSession.id.in_(session_pks)
    ).count() == 2
    assert db.query(AuditLog).filter(
        AuditLog.user_id == user.id,
        AuditLog.event_type == "SESSION_REVOKED",
    ).count() == 0

def _make_disable_target(db):
    from app.models.session import Session as UserSession

    suffix = uuid.uuid4().hex
    target = User(
        username=f"disable_target_{suffix}",
        email=f"disable_target_{suffix}@example.com",
        password_hash=hash_password("Target-Strong-Password-2026!"),
        role="user",
        is_active=True,
    )
    db.add(target)
    db.commit()
    db.refresh(target)

    target_session = UserSession(
        session_id=f"disable-target-{suffix}",
        csrf_token=f"csrf-{suffix}",
        user_id=target.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        last_activity=datetime.now(timezone.utc),
    )
    db.add(target_session)
    db.commit()
    db.refresh(target_session)

    return target, target_session


def _cleanup_disable_target(db, target_id):
    from app.models.session import Session as UserSession

    db.query(UserSession).filter(
        UserSession.user_id == target_id
    ).delete(synchronize_session=False)
    db.query(User).filter(User.id == target_id).delete(
        synchronize_session=False
    )
    db.commit()


def test_admin_disable_user_revokes_sessions_and_audits(
    reset_test_context,
):
    import app.routers.user as user_router
    from app.models.audit_log import AuditLog
    from app.models.session import Session as UserSession

    db, admin, _ = reset_test_context
    admin_session = _make_admin_revocation_session(db, admin)
    target, target_session = _make_disable_target(db)
    target_id = target.id
    target_session_id = target_session.session_id

    try:
        result = user_router.disable_user(
            request=_admin_revocation_request(),
            user_id=target_id,
            db=db,
            current_user=admin,
            _csrf_session=admin_session,
        )

        assert result.is_active is False
        db.expire_all()

        assert db.query(UserSession).filter(
            UserSession.session_id == target_session_id
        ).first() is None

        audit = db.query(AuditLog).filter(
            AuditLog.user_id == admin.id,
            AuditLog.event_type == "USER_DISABLED",
            AuditLog.details.contains(f"disabled_user_id={target_id}"),
        ).one()
        assert "revoked_sessions=1" in audit.details
    finally:
        _cleanup_disable_target(db, target_id)


def test_admin_disable_user_audit_failure_rolls_back(
    reset_test_context, monkeypatch
):
    import pytest
    from fastapi import HTTPException
    import app.routers.user as user_router
    from app.models.audit_log import AuditLog
    from app.models.session import Session as UserSession

    db, admin, _ = reset_test_context
    admin_session = _make_admin_revocation_session(db, admin)
    target, target_session = _make_disable_target(db)
    target_id = target.id
    target_session_id = target_session.session_id

    def fail_audit(**kwargs):
        raise RuntimeError("Simulated audit persistence failure")

    monkeypatch.setattr(user_router, "log_audit", fail_audit)

    try:
        with pytest.raises(HTTPException) as exc:
            user_router.disable_user(
                request=_admin_revocation_request(),
                user_id=target_id,
                db=db,
                current_user=admin,
                _csrf_session=admin_session,
            )

        assert exc.value.status_code == 500
        db.expire_all()

        target_after = db.query(User).filter(
            User.id == target_id
        ).one()
        assert target_after.is_active is True
        assert db.query(UserSession).filter(
            UserSession.session_id == target_session_id
        ).first() is not None
        assert db.query(AuditLog).filter(
            AuditLog.user_id == admin.id,
            AuditLog.event_type == "USER_DISABLED",
        ).count() == 0
    finally:
        _cleanup_disable_target(db, target_id)

def test_profile_update_and_audit_are_atomic(
    reset_test_context, reset_client
):
    from app.models.audit_log import AuditLog

    db, user, _ = reset_test_context
    _, csrf_token = _create_password_change_session(
        db, user, reset_client
    )

    new_username = f"profile-{uuid.uuid4().hex[:12]}"
    new_email = f"{new_username}@example.com"

    response = reset_client.post(
        "/auth/update-profile",
        headers={"X-CSRF-Token": csrf_token},
        json={
            "username": new_username,
            "email": new_email,
            "current_password": "Original-Strong-Password-2026!",
        },
    )

    assert response.status_code == 200, response.text
    db.expire_all()
    db.refresh(user)
    assert user.username == new_username
    assert user.email == new_email
    assert db.query(AuditLog).filter(
        AuditLog.user_id == user.id,
        AuditLog.event_type == "ACCOUNT_PROFILE_UPDATED",
    ).count() == 1


def test_profile_update_audit_failure_rolls_back(
    reset_test_context, reset_client, monkeypatch
):
    import app.routers.auth as auth_router
    from app.models.audit_log import AuditLog

    db, user, _ = reset_test_context
    original_username = user.username
    original_email = user.email
    _, csrf_token = _create_password_change_session(
        db, user, reset_client
    )

    def fail_audit(**kwargs):
        raise RuntimeError("Simulated audit persistence failure")

    monkeypatch.setattr(auth_router, "log_audit", fail_audit)

    new_username = f"profile-{uuid.uuid4().hex[:12]}"
    new_email = f"{new_username}@example.com"

    response = reset_client.post(
        "/auth/update-profile",
        headers={"X-CSRF-Token": csrf_token},
        json={
            "username": new_username,
            "email": new_email,
            "current_password": "Original-Strong-Password-2026!",
        },
    )

    assert response.status_code == 500, response.text
    db.expire_all()
    db.refresh(user)
    assert user.username == original_username
    assert user.email == original_email
    assert db.query(AuditLog).filter(
        AuditLog.user_id == user.id,
        AuditLog.event_type == "ACCOUNT_PROFILE_UPDATED",
    ).count() == 0

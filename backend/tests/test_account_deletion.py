import hashlib
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

# Refuse to import the application unless this process explicitly targets
# the isolated test database.
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    database_url = dotenv_values(
        Path("/opt/greenupcb/backend/.env")
    ).get("DATABASE_URL")

if not database_url or make_url(database_url).database != "greenupcb_test":
    raise RuntimeError(
        "Account deletion tests may run only against greenupcb_test."
    )

engine = create_engine(database_url, pool_pre_ping=True)
with engine.connect() as connection:
    actual_database = connection.exec_driver_sql(
        "SELECT current_database()"
    ).scalar_one()
if actual_database != "greenupcb_test":
    engine.dispose()
    raise RuntimeError("Connected database is not greenupcb_test.")

SessionFactory = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)

from fastapi.testclient import TestClient
from app.main import app
from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.password_reset import PasswordResetToken
from app.models.session import Session as UserSession
from app.models.user import User
from app.security import hash_password
from app.services.account_deletion import cleanup_scheduled_account_deletions


def create_test_user(role="user", deletion_requested_at=None):
    suffix = uuid.uuid4().hex
    username = f"deletion_test_{suffix}"
    password = f"AccountDelete-{suffix}-Strong"
    now = datetime.now(timezone.utc)

    with SessionFactory.begin() as db:
        user = User(
            username=username,
            email=f"deletion-{suffix}@example.com",
            password_hash=hash_password(password),
            role=role,
            is_active=True,
            deletion_requested_at=deletion_requested_at,
        )
        db.add(user)
        db.flush()
        user_id = user.id

    return user_id, username, password, suffix, now


def cleanup_test_user(user_id, customer_id=None, marker=None):
    with SessionFactory.begin() as db:
        db.query(UserSession).filter(
            UserSession.user_id == user_id
        ).delete(synchronize_session=False)

        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user_id
        ).delete(synchronize_session=False)

        db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).delete(synchronize_session=False)

        if customer_id is not None:
            db.query(Customer).filter(
                Customer.id == customer_id
            ).delete(synchronize_session=False)

        user = db.query(User).filter(User.id == user_id).first()
        if user is not None:
            db.delete(user)
            db.flush()

        db.query(AuditLog).filter(
            AuditLog.details
            == f"scheduled_account_deletion_completed;deleted_user_id={user_id}"
        ).delete(synchronize_session=False)

        if marker:
            db.query(AuditLog).filter(
                AuditLog.details == marker
            ).delete(synchronize_session=False)


def login_as(client, username, password, role="user"):
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password, "role": role},
    )
    assert response.status_code == 200, response.text
    return response.json()["csrf_token"]


def test_deletion_requires_password_and_login_cancels_within_grace_period():
    user_id, username, password, _, _ = create_test_user()

    try:
        with TestClient(app, base_url="https://testserver") as client:
            csrf_token = login_as(client, username, password)
            headers = {"X-CSRF-Token": csrf_token}

            bad_password = client.post(
                "/auth/request-account-deletion",
                json={"current_password": "incorrect-password"},
                headers=headers,
            )
            assert bad_password.status_code == 400

            with SessionFactory() as db:
                account = db.query(User).filter(User.id == user_id).one()
                assert account.deletion_requested_at is None

            scheduled = client.post(
                "/auth/request-account-deletion",
                json={"current_password": password},
                headers=headers,
            )
            assert scheduled.status_code == 200, scheduled.text
            assert "30 days" in scheduled.json()["message"]

            with SessionFactory() as db:
                account = db.query(User).filter(User.id == user_id).one()
                assert account.deletion_requested_at is not None
                assert (
                    db.query(UserSession)
                    .filter(UserSession.user_id == user_id)
                    .count()
                    == 0
                )

            # Successful login inside the grace period cancels the request.
            login_response = client.post(
                "/auth/login",
                json={
                    "username": username,
                    "password": password,
                    "role": "user",
                },
            )
            assert login_response.status_code == 200, login_response.text
            assert login_response.json()["account_deletion_cancelled"] is True

            with SessionFactory() as db:
                account = db.query(User).filter(User.id == user_id).one()
                assert account.deletion_requested_at is None
    finally:
        cleanup_test_user(user_id)


def test_login_is_blocked_after_grace_period_expires():
    expired_at = datetime.now(timezone.utc) - timedelta(days=31)
    user_id, username, password, _, _ = create_test_user(
        deletion_requested_at=expired_at
    )

    try:
        with TestClient(app, base_url="https://testserver") as client:
            response = client.post(
                "/auth/login",
                json={
                    "username": username,
                    "password": password,
                    "role": "user",
                },
            )
            assert response.status_code == 403
            assert "expired" in response.json()["detail"].lower()
    finally:
        cleanup_test_user(user_id)


def test_due_deletion_preserves_customer_and_audit_history():
    now = datetime.now(timezone.utc)
    due_at = now - timedelta(days=31)
    user_id, _, _, suffix, _ = create_test_user(
        deletion_requested_at=due_at
    )
    marker = f"deletion-history-test-{suffix}"
    customer_id = None

    try:
        with SessionFactory.begin() as db:
            customer = Customer(
                name=f"Deletion test customer {suffix}",
                created_by_user_id=user_id,
            )
            db.add(customer)
            db.flush()
            customer_id = customer.id

            db.add(
                AuditLog(
                    user_id=user_id,
                    event_type="ACCOUNT_DELETION_TEST_HISTORY",
                    details=marker,
                )
            )
            db.add(
                UserSession(
                    session_id=f"deletion-test-session-{suffix}",
                    csrf_token=f"deletion-test-csrf-{suffix}",
                    user_id=user_id,
                    created_at=now,
                    expires_at=now + timedelta(hours=1),
                    last_activity=now,
                )
            )
            db.add(
                PasswordResetToken(
                    user_id=user_id,
                    token_hash=hashlib.sha256(
                        f"deletion-token-{suffix}".encode()
                    ).hexdigest(),
                    expires_at=now + timedelta(minutes=30),
                )
            )

        with SessionFactory() as db:
            deleted, _protected = cleanup_scheduled_account_deletions(
                db, now=now
            )
            assert deleted >= 1

        with SessionFactory() as db:
            assert db.query(User).filter(User.id == user_id).first() is None

            saved_customer = (
                db.query(Customer)
                .filter(Customer.id == customer_id)
                .one()
            )
            assert saved_customer.created_by_user_id is None

            saved_history = (
                db.query(AuditLog)
                .filter(AuditLog.details == marker)
                .one()
            )
            assert saved_history.user_id is None

            assert (
                db.query(UserSession)
                .filter(UserSession.user_id == user_id)
                .count()
                == 0
            )
            assert (
                db.query(PasswordResetToken)
                .filter(PasswordResetToken.user_id == user_id)
                .count()
                == 0
            )
    finally:
        cleanup_test_user(user_id, customer_id=customer_id, marker=marker)


def test_last_admin_cannot_schedule_or_complete_deletion():
    user_id, username, password, _, now = create_test_user(role="admin")
    previous_admin_states = []

    try:
        # Isolate this case in the test database: no other admin is considered
        # active while the last-admin protections are checked.
        with SessionFactory.begin() as db:
            other_admins = (
                db.query(User)
                .filter(
                    User.role == "admin",
                    User.id != user_id,
                )
                .all()
            )
            previous_admin_states = [
                (admin.id, admin.is_active) for admin in other_admins
            ]
            for admin in other_admins:
                admin.is_active = False

        with TestClient(app, base_url="https://testserver") as client:
            csrf_token = login_as(client, username, password, role="admin")
            response = client.post(
                "/auth/request-account-deletion",
                json={"current_password": password},
                headers={"X-CSRF-Token": csrf_token},
            )
            assert response.status_code == 400
            assert "last active administrator" in response.json()["detail"].lower()

        # Also verify that the scheduled cleanup protects a last admin.
        with SessionFactory.begin() as db:
            admin = db.query(User).filter(User.id == user_id).one()
            admin.deletion_requested_at = now - timedelta(days=31)

        with SessionFactory() as db:
            _deleted, protected = cleanup_scheduled_account_deletions(
                db, now=now
            )
            assert protected >= 1

        with SessionFactory() as db:
            assert db.query(User).filter(User.id == user_id).one().role == "admin"
    finally:
        with SessionFactory.begin() as db:
            for admin_id, is_active in previous_admin_states:
                admin = db.query(User).filter(User.id == admin_id).first()
                if admin is not None:
                    admin.is_active = is_active

        cleanup_test_user(user_id)


def teardown_module():
    engine.dispose()

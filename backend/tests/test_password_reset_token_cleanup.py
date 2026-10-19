from datetime import datetime, timedelta, timezone
import os
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.security import generate_reset_token, hash_password, hash_reset_token
from app.services.password_reset_cleanup import (
    cleanup_password_reset_tokens,
    count_password_reset_tokens_to_cleanup,
)


def _test_session_factory():
    value = os.environ.get("DATABASE_URL")
    if not value:
        raise RuntimeError("DATABASE_URL is required for cleanup tests.")

    url = make_url(value)
    if url.database != "greenupcb_test":
        raise RuntimeError(
            "Refusing to run cleanup tests outside greenupcb_test."
        )

    test_engine = create_engine(url)
    with test_engine.connect() as connection:
        actual = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

    if actual != "greenupcb_test":
        test_engine.dispose()
        raise RuntimeError("Connected database is not greenupcb_test.")

    return test_engine, sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )


@pytest.fixture
def cleanup_test_data():
    test_engine, factory = _test_session_factory()
    db = factory()
    username = f"token_cleanup_{uuid.uuid4().hex[:12]}"

    user = User(
        username=username,
        email=f"{username}@example.com",
        password_hash=hash_password("Cleanup-Test-Password-2026!"),
        role="user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    now = datetime.now(timezone.utc)

    def add_token(expires_at, used_at=None):
        token = PasswordResetToken(
            user_id=user.id,
            token_hash=hash_reset_token(generate_reset_token()),
            expires_at=expires_at,
            used_at=used_at,
        )
        db.add(token)
        db.flush()
        return token.token_hash

    hashes = {
        "expired": add_token(now - timedelta(minutes=1)),
        "used_old": add_token(
            now + timedelta(days=30),
            now - timedelta(days=2),
        ),
        "active": add_token(now + timedelta(minutes=30)),
        "used_recent": add_token(
            now + timedelta(minutes=30),
            now - timedelta(minutes=10),
        ),
    }
    db.commit()

    try:
        yield db, user.id, now, hashes
    finally:
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id
        ).delete(synchronize_session=False)
        db.query(User).filter(User.id == user.id).delete(
            synchronize_session=False
        )
        db.commit()
        db.close()
        test_engine.dispose()


def test_cleanup_deletes_only_expired_or_old_used_tokens(cleanup_test_data):
    db, user_id, now, hashes = cleanup_test_data

    assert count_password_reset_tokens_to_cleanup(db, now) == 2

    deleted = cleanup_password_reset_tokens(db, now)
    assert deleted == 2

    remaining = {
        record.token_hash
        for record in db.query(PasswordResetToken)
        .filter(PasswordResetToken.user_id == user_id)
        .all()
    }

    assert remaining == {hashes["active"], hashes["used_recent"]}


def test_cleanup_count_does_not_delete_records(cleanup_test_data):
    db, user_id, now, _ = cleanup_test_data

    assert count_password_reset_tokens_to_cleanup(db, now) == 2
    assert (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.user_id == user_id)
        .count()
        == 4
    )

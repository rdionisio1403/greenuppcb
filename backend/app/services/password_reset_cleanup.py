from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.password_reset import PasswordResetToken


USED_TOKEN_RETENTION = timedelta(days=1)


def _utc_now(now: datetime | None = None) -> datetime:
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _cleanup_query(db: Session, now: datetime):
    used_cutoff = now - USED_TOKEN_RETENTION

    return db.query(PasswordResetToken).filter(
        or_(
            PasswordResetToken.expires_at <= now,
            and_(
                PasswordResetToken.used_at.is_not(None),
                PasswordResetToken.used_at <= used_cutoff,
            ),
        )
    )


def count_password_reset_tokens_to_cleanup(
    db: Session,
    now: datetime | None = None,
) -> int:
    return _cleanup_query(db, _utc_now(now)).count()


def cleanup_password_reset_tokens(
    db: Session,
    now: datetime | None = None,
) -> int:
    """Delete expired or sufficiently old used tokens in one transaction."""
    try:
        deleted = _cleanup_query(
            db,
            _utc_now(now),
        ).delete(synchronize_session=False)
        db.commit()
        return deleted
    except Exception:
        db.rollback()
        raise

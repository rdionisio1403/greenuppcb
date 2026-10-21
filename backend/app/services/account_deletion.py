from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User

ACCOUNT_DELETION_GRACE_DAYS = 30


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def count_due_accounts(db: Session, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=ACCOUNT_DELETION_GRACE_DAYS)

    return (
        db.query(User)
        .filter(
            User.deletion_requested_at.is_not(None),
            User.deletion_requested_at <= cutoff,
        )
        .count()
    )


def cleanup_scheduled_account_deletions(
    db: Session,
    now: datetime | None = None,
    batch_size: int = 500,
) -> tuple[int, int]:
    """Delete due accounts, preserving linked business records and the last active admin."""
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=ACCOUNT_DELETION_GRACE_DAYS)

    candidate_ids = (
        db.query(User.id)
        .filter(
            User.deletion_requested_at.is_not(None),
            User.deletion_requested_at <= cutoff,
        )
        .order_by(User.deletion_requested_at.asc())
        .limit(batch_size)
        .all()
    )

    deleted_count = 0
    protected_count = 0

    for (user_id,) in candidate_ids:
        try:
            user = (
                db.query(User)
                .filter(User.id == user_id)
                .with_for_update()
                .first()
            )

            if user is None or user.deletion_requested_at is None:
                db.rollback()
                continue

            requested_at = _as_utc(user.deletion_requested_at)
            if requested_at > cutoff:
                db.rollback()
                continue

            if user.role == "admin" and user.is_active:
                remaining_admins = (
                    db.query(User.id)
                    .filter(
                        User.id != user.id,
                        User.role == "admin",
                        User.is_active.is_(True),
                        User.deletion_requested_at.is_(None),
                    )
                    .count()
                )
                if remaining_admins == 0:
                    protected_count += 1
                    db.rollback()
                    continue

            # Foreign keys use CASCADE for sessions/reset tokens and SET NULL
            # for audit, diagnosis and customer ownership references.
            db.delete(user)
            db.flush()
            db.add(
                AuditLog(
                    user_id=None,
                    event_type="ACCOUNT_DELETED",
                    details=(
                        "scheduled_account_deletion_completed;"
                        f"deleted_user_id={user_id}"
                    ),
                )
            )
            db.commit()
            deleted_count += 1

        except Exception:
            db.rollback()
            raise

    return deleted_count, protected_count

import logging

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.dependencies import require_admin, require_csrf
from app.audit import log_audit
from app.models.user import User
from app.models.session import Session as UserSession
from app.schemas.user import SessionResponse
from app.schemas.user import UserResponse


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return db.query(User).order_by(User.id).all()

@router.patch("/{user_id}/disable", response_model=UserResponse)
def disable_user(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    _csrf_session = Depends(require_csrf),
):
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin cannot disable their own account",
        )

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    sessions = (
        db.query(UserSession)
        .filter(UserSession.user_id == user.id)
        .all()
    )
    revoked_session_count = len(sessions)

    try:
        user.is_active = False
        for user_session in sessions:
            db.delete(user_session)

        log_audit(
            db=db,
            event_type="USER_DISABLED",
            request=request,
            user_id=current_user.id,
            details=(
                f"disabled_user_id={user.id};"
                f"username={user.username};"
                f"revoked_sessions={revoked_session_count}"
            ),
            commit=False,
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception(
            "Failed to disable user and persist audit event."
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to disable user. Please try again.",
        )

    db.refresh(user)
    return user


@router.get("/{user_id}/sessions", response_model=list[SessionResponse])
def list_user_sessions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)

    return (
        db.query(UserSession)
        .filter(
            UserSession.user_id == user_id,
            UserSession.expires_at > now,
        )
        .order_by(UserSession.last_activity.desc())
        .all()
    )


@router.delete("/{user_id}/sessions/{session_id}")
def revoke_user_session(
    request: Request,
    user_id: int,
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    _csrf_session = Depends(require_csrf),
):
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user_session = (
        db.query(UserSession)
        .filter(
            UserSession.id == session_id,
            UserSession.user_id == user_id,
        )
        .first()
    )

    if user_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    try:
        db.delete(user_session)
        log_audit(
            db=db,
            event_type="SESSION_REVOKED",
            request=request,
            user_id=current_user.id,
            details=f"revoked_session_id={session_id};target_user_id={user_id}",
            commit=False,
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception(
            "Failed to revoke user session and persist audit event."
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to revoke session. Please try again.",
        )

    return {"message": "Session revoked"}


@router.delete("/{user_id}/sessions")
def revoke_all_user_sessions(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    _csrf_session = Depends(require_csrf),
):
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    sessions = (
        db.query(UserSession)
        .filter(UserSession.user_id == user_id)
        .all()
    )

    revoked_count = len(sessions)

    try:
        for user_session in sessions:
            db.delete(user_session)

        log_audit(
            db=db,
            event_type="SESSION_REVOKED",
            request=request,
            user_id=current_user.id,
            details=f"revoked_all_sessions;target_user_id={user_id};count={revoked_count}",
            commit=False,
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception(
            "Failed to revoke all user sessions and persist audit event."
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to revoke sessions. Please try again.",
        )

    return {
        "message": "All sessions revoked",
        "revoked_count": revoked_count,
    }

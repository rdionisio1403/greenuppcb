from datetime import datetime, timedelta, timezone

from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.models.session import Session as UserSession


SESSION_COOKIE_NAME = "session_id"
SESSION_DURATION = timedelta(hours=1)
SESSION_IDLE_TIMEOUT = timedelta(minutes=30)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
):
    session_id = request.cookies.get(SESSION_COOKIE_NAME)

    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    user_session = (
        db.query(UserSession)
        .filter(UserSession.session_id == session_id)
        .first()
    )

    if user_session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
        )

    now = datetime.now(timezone.utc)

    if user_session.expires_at <= now:
        db.delete(user_session)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
        )

    if user_session.last_activity + SESSION_IDLE_TIMEOUT <= now:
        db.delete(user_session)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired due to inactivity",
        )

    user = db.query(User).filter(User.id == user_session.user_id).first()

    if user is None:
        db.delete(user_session)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        db.delete(user_session)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
        )

    user_session.last_activity = now
    db.commit()

    return user


def require_csrf(
    request: Request,
    db: Session = Depends(get_db),
):
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    csrf_token = request.headers.get("X-CSRF-Token")

    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    if not csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed",
        )

    user_session = (
        db.query(UserSession)
        .filter(UserSession.session_id == session_id)
        .first()
    )

    if user_session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
        )

    if not user_session.csrf_token or csrf_token != user_session.csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed",
        )

    return user_session


def require_admin(
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user

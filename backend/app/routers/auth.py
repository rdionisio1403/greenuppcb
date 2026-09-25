from datetime import datetime, timedelta, timezone
import secrets
import logging

from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user, require_csrf
from app.models.user import User
from app.models.session import Session as UserSession
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.security import hash_password, verify_password
from app.audit import log_audit
from app.rate_limiter import (
    is_rate_limited,
    record_failed_attempt,
    reset_attempts,
)


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


SESSION_COOKIE_NAME = "session_id"
SESSION_DURATION = timedelta(hours=1)


@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = (
        db.query(User)
        .filter(
            (User.username == user.username) |
            (User.email == user.email)
        )
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists",
        )

    new_user = User(
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password),
        role="user",
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login")
def login(
    user: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"
    ip_key = f"ip:{client_ip}"
    username_key = f"user:{user.username}"

    if is_rate_limited(ip_key) or is_rate_limited(username_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )

    db_user = (
        db.query(User)
        .filter(User.username == user.username)
        .first()
    )

    if not db_user or not db_user.is_active or not verify_password(
        user.password,
        db_user.password_hash
    ):
        record_failed_attempt(ip_key)
        record_failed_attempt(username_key)

        logger.warning(
            "LOGIN_FAILED username=%s ip=%s",
            user.username,
            client_ip,
        )

        log_audit(
            db=db,
            event_type="LOGIN_FAILED",
            request=request,
            user_id=db_user.id if db_user else None,
            details=f"username={user.username}",
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    reset_attempts(ip_key)
    reset_attempts(username_key)

    session_id = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)

    user_session = UserSession(
        session_id=session_id,
        csrf_token=csrf_token,
        user_id=db_user.id,
        created_at=now,
        expires_at=now + SESSION_DURATION,
        last_activity=now,
    )

    db.add(user_session)
    db.commit()

    logger.info(
        "LOGIN_SUCCESS username=%s ip=%s",
        db_user.username,
        client_ip,
    )

    log_audit(
        db=db,
        event_type="LOGIN_SUCCESS",
        request=request,
        user_id=db_user.id,
    )

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=int(SESSION_DURATION.total_seconds()),
    )

    return {"message": "Login successful", "csrf_token": csrf_token}


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    csrf_session: UserSession = Depends(require_csrf),
):
    session_id = request.cookies.get(SESSION_COOKIE_NAME)

    if session_id:
        db.query(UserSession).filter(
            UserSession.session_id == session_id
        ).delete(synchronize_session=False)
        db.commit()

        logger.info(
            "LOGOUT ip=%s",
            request.client.host if request.client else "unknown",
        )

        log_audit(
            db=db,
            event_type="LOGOUT",
            request=request,
            user_id=csrf_session.user_id,
        )

    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        samesite="lax",
    )

    return {"message": "Logout successful"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/users-summary")
def get_users_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    users = (
        db.query(User)
        .order_by(User.id.asc())
        .all()
    )

    return {
        "total_users": len(users),
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
            }
            for user in users
        ],
    }

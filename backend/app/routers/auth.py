from datetime import datetime, timedelta, timezone
import secrets
import logging
import os
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user, require_csrf, require_admin
from app.models.user import User
from app.models.session import Session as UserSession
from app.models.password_reset import PasswordResetToken
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    ChangePasswordRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from app.security import (
    hash_password,
    verify_password,
    hash_reset_token,
    generate_reset_token,
)
from app.audit import log_audit
from app.services.email_service import send_password_reset_email
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


SESSION_COOKIE_NAME = "__Host-session_id"
SESSION_DURATION = timedelta(hours=1)

# Email delivery remains disabled unless explicitly enabled in the environment.
PASSWORD_RESET_EMAIL_ENABLED = os.getenv(
    "PASSWORD_RESET_EMAIL_ENABLED", "false"
).strip().lower() in {"1", "true", "yes", "on"}

PASSWORD_RESET_REQUEST_MESSAGE = (
    "If an account with that email exists, password reset instructions will be sent."
)
PASSWORD_RESET_DISABLED_MESSAGE = (
    "Email delivery is not configured yet. No reset email has been sent."
)


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

    if db_user.role != user.role:
        record_failed_attempt(ip_key)
        record_failed_attempt(username_key)

        logger.warning(
            "LOGIN_FAILED username=%s ip=%s reason=role_mismatch",
            user.username,
            client_ip,
        )

        log_audit(
            db=db,
            event_type="LOGIN_FAILED",
            request=request,
            user_id=db_user.id,
            details="role_mismatch",
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
        secure=True,
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
        user_id = csrf_session.user_id

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
            user_id=user_id,
        )

    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        samesite="lax",
        secure=True,
        path="/",
    )

    return {"message": "Logout successful"}


@router.post("/change-password")
def change_password(
    password_data: ChangePasswordRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    csrf_session: UserSession = Depends(require_csrf),
):
    if csrf_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid session",
        )

    if not verify_password(
        password_data.current_password,
        current_user.password_hash,
    ):
        log_audit(
            db=db,
            event_type="PASSWORD_CHANGE_FAILED",
            request=request,
            user_id=current_user.id,
            details="current_password_invalid",
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    if password_data.current_password == password_data.new_password:
        log_audit(
            db=db,
            event_type="PASSWORD_CHANGE_FAILED",
            request=request,
            user_id=current_user.id,
            details="new_password_matches_current_password",
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current password",
        )

    current_user.password_hash = hash_password(password_data.new_password)

    sessions = (
        db.query(UserSession)
        .filter(UserSession.user_id == current_user.id)
        .all()
    )

    revoked_session_count = len(sessions)

    for user_session in sessions:
        db.delete(user_session)

    db.commit()

    log_audit(
        db=db,
        event_type="PASSWORD_CHANGED",
        request=request,
        user_id=current_user.id,
        details=f"revoked_sessions={revoked_session_count}",
    )

    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        samesite="lax",
        secure=True,
        path="/",
    )

    return {
        "message": "Password changed successfully. Please log in again.",
        "revoked_sessions": revoked_session_count,
    }


@router.post("/password-reset/request", status_code=status.HTTP_202_ACCEPTED)
def request_password_reset(
    reset_data: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"
    ip_key = f"password-reset:ip:{client_ip}"

    response_message = (
        PASSWORD_RESET_REQUEST_MESSAGE
        if PASSWORD_RESET_EMAIL_ENABLED
        else PASSWORD_RESET_DISABLED_MESSAGE
    )

    if is_rate_limited(ip_key):
        return {"message": response_message}

    record_failed_attempt(ip_key)

    if not PASSWORD_RESET_EMAIL_ENABLED:
        logger.info("PASSWORD_RESET_REQUEST_RECEIVED email_delivery_enabled=false")
        return {"message": PASSWORD_RESET_DISABLED_MESSAGE}

    # Use the same public response for known, unknown, and inactive accounts.
    user = (
        db.query(User)
        .filter(
            func.lower(User.email) == reset_data.email.lower(),
            User.is_active.is_(True),
        )
        .first()
    )

    if user is None or not user.email:
        logger.info("PASSWORD_RESET_REQUEST_PROCESSED")
        return {"message": PASSWORD_RESET_REQUEST_MESSAGE}

    reset_base_url = os.getenv("PASSWORD_RESET_BASE_URL", "").strip().rstrip("/")
    if not reset_base_url.startswith("https://"):
        logger.error(
            "Password reset email is enabled but PASSWORD_RESET_BASE_URL "
            "is missing or does not use HTTPS."
        )
        return {"message": PASSWORD_RESET_REQUEST_MESSAGE}

    raw_token = generate_reset_token()
    reset_record = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_reset_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    reset_record_id = None

    try:
        db.add(reset_record)
        db.commit()
        reset_record_id = reset_record.id

        reset_url = (
            f"{reset_base_url}/reset-password?"
            f"{urlencode({'token': raw_token})}"
        )
        send_password_reset_email(
            recipient=user.email,
            reset_url=reset_url,
        )
        logger.info("PASSWORD_RESET_EMAIL_ACCEPTED_BY_PROVIDER")

    except Exception:
        logger.exception("Password reset email delivery failed.")
        db.rollback()

        # Do not leave a usable reset token when delivery fails.
        if reset_record_id is not None:
            try:
                db.query(PasswordResetToken).filter(
                    PasswordResetToken.id == reset_record_id,
                    PasswordResetToken.used_at.is_(None),
                ).delete(synchronize_session=False)
                db.commit()
            except Exception:
                db.rollback()
                logger.exception(
                    "Failed to remove an undelivered password reset token."
                )

    return {"message": PASSWORD_RESET_REQUEST_MESSAGE}


@router.post("/password-reset/confirm")
def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    token_hash = hash_reset_token(reset_data.token)
    reset_record = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == token_hash)
        .with_for_update()
        .first()
    )

    now = datetime.now(timezone.utc)
    if reset_record is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token.",
        )

    expires_at = reset_record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if reset_record.used_at is not None or expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token.",
        )

    user = (
        db.query(User)
        .filter(User.id == reset_record.user_id)
        .with_for_update()
        .first()
    )
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token.",
        )

    user.password_hash = hash_password(reset_data.new_password)
    reset_record.used_at = now

    sessions = (
        db.query(UserSession)
        .filter(UserSession.user_id == user.id)
        .all()
    )
    revoked_session_count = len(sessions)
    for user_session in sessions:
        db.delete(user_session)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to reset password. Please try again.",
        )

    log_audit(
        db=db,
        event_type="PASSWORD_RESET_COMPLETED",
        request=request,
        user_id=user.id,
        details=f"revoked_sessions={revoked_session_count}",
    )

    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        samesite="lax",
        secure=True,
        path="/",
    )

    return {
        "message": "Password reset successful. Please log in again.",
        "revoked_sessions": revoked_session_count,
    }


@router.get("/csrf-token")
def get_csrf_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    user_session = (
        db.query(UserSession)
        .filter(
            UserSession.session_id == session_id,
            UserSession.user_id == current_user.id,
        )
        .first()
    )

    if user_session is None or not user_session.csrf_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token unavailable. Please sign in again.",
        )

    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return {"csrf_token": user_session.csrf_token}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/users-summary")
def get_users_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
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

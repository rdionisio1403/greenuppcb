from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import logging
import os
import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, Request, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.dependencies import get_db, get_current_user, require_csrf, require_admin
from app.models.user import User
from app.models.session import Session as UserSession
from app.models.password_reset import PasswordResetToken
from app.schemas.user import (
    UserCreate,
    UserLogin,
    AccountProfileUpdate,
    AccountDeletionRequest,
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
from app.services.email_service import (
    EmailServiceError,
    send_password_reset_email,
)
from app.rate_limiter import (
    check_and_record_attempt,
    is_rate_limited,
    record_failed_attempt,
    reset_attempts,
)


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

# The limiter is process-local; its ephemeral HMAC key is sufficient
# for protecting email-derived keys within this process lifetime.
_PASSWORD_RESET_EMAIL_RATE_LIMIT_HMAC_KEY = secrets.token_bytes(32)


def _password_reset_email_rate_limit_key(email: str) -> str:
    normalized_email = email.strip().casefold()
    digest = hmac.new(
        _PASSWORD_RESET_EMAIL_RATE_LIMIT_HMAC_KEY,
        normalized_email.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"password-reset:email:{digest}"



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
    identifier = user.username.strip()
    identifier_type = "email" if "@" in identifier else "username"
    ip_key = f"ip:{client_ip}"
    identifier_key = f"user:{identifier.casefold()}"

    if is_rate_limited(ip_key) or is_rate_limited(identifier_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )

    # Preserve username login for all existing accounts, including those
    # whose optional email field is NULL. If no username matches, try email.
    db_user = (
        db.query(User)
        .filter(User.username == identifier)
        .with_for_update()
        .first()
    )
    if db_user is None and "@" in identifier:
        db_user = (
            db.query(User)
            .filter(func.lower(User.email) == identifier.lower())
            .with_for_update()
            .first()
        )

    if not db_user or not db_user.is_active or not verify_password(
        user.password,
        db_user.password_hash
    ):
        record_failed_attempt(ip_key)
        record_failed_attempt(identifier_key)

        # Do not write the submitted email address into application logs.
        logger.warning(
            "LOGIN_FAILED identifier_type=%s ip=%s",
            identifier_type,
            client_ip,
        )

        log_audit(
            db=db,
            event_type="LOGIN_FAILED",
            request=request,
            user_id=db_user.id if db_user else None,
            details=f"identifier_type={identifier_type}",
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    if db_user.role != user.role:
        record_failed_attempt(ip_key)
        record_failed_attempt(identifier_key)

        logger.warning(
            "LOGIN_FAILED username=%s ip=%s reason=role_mismatch",
            db_user.username,
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

    deletion_cancelled = False
    if db_user.deletion_requested_at is not None:
        login_now = datetime.now(timezone.utc)
        requested_at = db_user.deletion_requested_at
        if requested_at.tzinfo is None:
            requested_at = requested_at.replace(tzinfo=timezone.utc)

        if login_now >= requested_at + timedelta(days=30):
            log_audit(
                db=db,
                event_type="ACCOUNT_LOGIN_BLOCKED_DELETION_EXPIRED",
                request=request,
                user_id=db_user.id,
                details="deletion_grace_period_expired",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "The 30-day deletion period has expired. "
                    "This account is awaiting permanent deletion."
                ),
            )

        db_user.deletion_requested_at = None
        log_audit(
            db=db,
            event_type="ACCOUNT_DELETION_CANCELLED",
            request=request,
            user_id=db_user.id,
            details="cancelled_by_successful_login",
            commit=False,
        )
        deletion_cancelled = True

    reset_attempts(ip_key)
    reset_attempts(identifier_key)

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

    return {
        "message": "Login successful",
        "csrf_token": csrf_token,
        "account_deletion_cancelled": deletion_cancelled,
    }


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

    try:
        # Keep the password update, session revocation and audit event atomic.
        log_audit(
            db=db,
            event_type="PASSWORD_CHANGED",
            request=request,
            user_id=current_user.id,
            details=f"revoked_sessions={revoked_session_count}",
            commit=False,
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception(
            "Failed to persist password change and audit event."
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to change password. Please try again.",
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


def _remove_reset_token_after_definite_failure(reset_record_id: int) -> None:
    cleanup_db = None
    try:
        cleanup_db = SessionLocal()
        cleanup_db.query(PasswordResetToken).filter(
            PasswordResetToken.id == reset_record_id,
            PasswordResetToken.used_at.is_(None),
        ).delete(synchronize_session=False)
        cleanup_db.commit()
    except Exception:
        if cleanup_db is not None:
            cleanup_db.rollback()
        logger.exception(
            "Failed to remove a definitely undelivered reset token."
        )
    finally:
        if cleanup_db is not None:
            cleanup_db.close()


def _deliver_password_reset_email_in_background(
    recipient: str,
    reset_url: str,
    reset_record_id: int,
) -> None:
    try:
        send_password_reset_email(
            recipient=recipient,
            reset_url=reset_url,
        )
        logger.info("PASSWORD_RESET_EMAIL_ACCEPTED_BY_PROVIDER")

    except EmailServiceError as exc:
        logger.warning(
            "PASSWORD_RESET_EMAIL_FAILURE "
            "stage=%s outcome=%s status_code=%s correlation_id=%s",
            exc.stage,
            exc.delivery_status,
            exc.status_code if exc.status_code is not None else "unavailable",
            exc.correlation_id,
        )

        if exc.delivery_status == "not_sent":
            _remove_reset_token_after_definite_failure(reset_record_id)
        else:
            logger.warning(
                "PASSWORD_RESET_TOKEN_RETAINED outcome=unknown "
                "correlation_id=%s",
                exc.correlation_id,
            )

    except Exception:
        logger.exception("Unexpected password-reset delivery failure.")
        logger.warning(
            "PASSWORD_RESET_TOKEN_RETAINED outcome=unknown "
            "reason=unexpected_error"
        )


@router.post("/password-reset/request", status_code=status.HTTP_202_ACCEPTED)
def request_password_reset(
    reset_data: PasswordResetRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"
    ip_key = f"password-reset:ip:{client_ip}"

    response_message = (
        PASSWORD_RESET_REQUEST_MESSAGE
        if PASSWORD_RESET_EMAIL_ENABLED
        else PASSWORD_RESET_DISABLED_MESSAGE
    )

    if check_and_record_attempt(ip_key):
        return {"message": response_message}

    if not PASSWORD_RESET_EMAIL_ENABLED:
        logger.info(
            "PASSWORD_RESET_REQUEST_RECEIVED email_delivery_enabled=false"
        )
        return {"message": PASSWORD_RESET_DISABLED_MESSAGE}

    email_key = _password_reset_email_rate_limit_key(reset_data.email)
    if check_and_record_attempt(email_key):
        logger.info("PASSWORD_RESET_REQUEST_PROCESSED")
        return {"message": PASSWORD_RESET_REQUEST_MESSAGE}

    # Preserve the same public response for known, unknown, and inactive accounts.
    user = (
        db.query(User)
        .filter(
            func.lower(User.email) == reset_data.email.lower(),
            User.is_active.is_(True),
            User.deletion_requested_at.is_(None),
        )
        .with_for_update()
        .first()
    )

    if user is None or not user.email:
        logger.info("PASSWORD_RESET_REQUEST_PROCESSED")
        return {"message": PASSWORD_RESET_REQUEST_MESSAGE}

    reset_base_url = os.getenv(
        "PASSWORD_RESET_BASE_URL", ""
    ).strip().rstrip("/")

    if not reset_base_url.startswith("https://"):
        logger.error(
            "Password reset email is enabled but PASSWORD_RESET_BASE_URL "
            "is missing or does not use HTTPS."
        )
        return {"message": PASSWORD_RESET_REQUEST_MESSAGE}

    recipient = user.email
    raw_token = generate_reset_token()
    reset_record = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_reset_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    reset_record_id = None
    task_scheduled = False

    try:
        # Replace older unused tokens and store the new token before scheduling email.
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        ).delete(synchronize_session=False)

        db.add(reset_record)
        db.commit()
        reset_record_id = reset_record.id

        reset_url = (
            f"{reset_base_url}/reset-password?"
            f"{urlencode({'token': raw_token})}"
        )

        background_tasks.add_task(
            _deliver_password_reset_email_in_background,
            recipient,
            reset_url,
            reset_record_id,
        )
        task_scheduled = True
        logger.info("PASSWORD_RESET_EMAIL_QUEUED")

    except Exception:
        db.rollback()
        logger.exception("Unable to prepare password-reset email delivery.")

        if reset_record_id is not None and not task_scheduled:
            _remove_reset_token_after_definite_failure(reset_record_id)

    return {"message": PASSWORD_RESET_REQUEST_MESSAGE}

@router.post("/password-reset/confirm")
def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    token_hash = hash_reset_token(reset_data.token)

    # Read the owner without locking the token row. All reset operations
    # acquire locks in the same order: user first, token second.
    token_owner_id = (
        db.query(PasswordResetToken.user_id)
        .filter(PasswordResetToken.token_hash == token_hash)
        .scalar()
    )

    if token_owner_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token.",
        )

    user = (
        db.query(User)
        .filter(User.id == token_owner_id)
        .with_for_update()
        .first()
    )
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token.",
        )

    reset_record = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.user_id == token_owner_id,
        )
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
        # Include the audit event in the same transaction as the password,
        # token-consumption and session-revocation updates.
        log_audit(
            db=db,
            event_type="PASSWORD_RESET_COMPLETED",
            request=request,
            user_id=user.id,
            details=f"revoked_sessions={revoked_session_count}",
            commit=False,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to reset password. Please try again.",
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


@router.post("/request-account-deletion")
def request_account_deletion(
    deletion_data: AccountDeletionRequest,
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
        deletion_data.current_password,
        current_user.password_hash,
    ):
        log_audit(
            db=db,
            event_type="ACCOUNT_DELETION_REQUEST_FAILED",
            request=request,
            user_id=current_user.id,
            details="current_password_invalid",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    if current_user.deletion_requested_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account deletion has already been scheduled.",
        )

    if current_user.role == "admin":
        other_active_admins = (
            db.query(User.id)
            .filter(
                User.role == "admin",
                User.is_active.is_(True),
                User.deletion_requested_at.is_(None),
                User.id != current_user.id,
            )
            .count()
        )
        if other_active_admins == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The last active administrator cannot schedule account deletion.",
            )

    requested_at = datetime.now(timezone.utc)
    scheduled_for = requested_at + timedelta(days=30)
    current_user.deletion_requested_at = requested_at

    db.query(UserSession).filter(
        UserSession.user_id == current_user.id
    ).delete(synchronize_session=False)

    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == current_user.id
    ).delete(synchronize_session=False)

    log_audit(
        db=db,
        event_type="ACCOUNT_DELETION_REQUESTED",
        request=request,
        user_id=current_user.id,
        details="permanent_deletion_after_30_days_without_successful_login",
        commit=False,
    )
    db.commit()

    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        samesite="lax",
        secure=True,
        path="/",
    )
    response.headers["Cache-Control"] = "no-store"

    return {
        "message": (
            "Account deletion is scheduled for 30 days from now. "
            "Sign in successfully within 30 days to cancel the request."
        ),
        "deletion_requested_at": requested_at,
        "deletion_scheduled_for": scheduled_for,
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


@router.post("/update-profile", response_model=UserResponse)
def update_profile(
    profile_data: AccountProfileUpdate,
    request: Request,
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
        profile_data.current_password,
        current_user.password_hash,
    ):
        log_audit(
            db=db,
            event_type="ACCOUNT_PROFILE_UPDATE_FAILED",
            request=request,
            user_id=current_user.id,
            details="current_password_invalid",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    username = profile_data.username.strip()
    email = (
        str(profile_data.email).strip().lower()
        if profile_data.email is not None
        else None
    )

    username_conflict = (
        db.query(User.id)
        .filter(
            func.lower(User.username) == username.lower(),
            User.id != current_user.id,
        )
        .first()
    )
    if username_conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email is already in use",
        )

    if email is not None:
        email_conflict = (
            db.query(User.id)
            .filter(
                func.lower(User.email) == email.lower(),
                User.id != current_user.id,
            )
            .first()
        )
        if email_conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username or email is already in use",
            )

    username_changed = current_user.username != username
    email_changed = (current_user.email or "").lower() != (email or "")

    if not username_changed and not email_changed:
        return current_user

    current_user.username = username
    current_user.email = email

    try:
        log_audit(
            db=db,
            event_type="ACCOUNT_PROFILE_UPDATED",
            request=request,
            user_id=current_user.id,
            details=(
                f"username_changed={str(username_changed).lower()};"
                f"email_changed={str(email_changed).lower()}"
            ),
            commit=False,
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email is already in use",
        ) from None
    except Exception:
        db.rollback()
        logger.exception(
            "Failed to update account profile and persist audit event."
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update profile. Please try again.",
        )

    db.refresh(current_user)
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

from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def get_client_ip(request: Request) -> Optional[str]:
    return request.client.host if request.client else None


def log_audit(
    db: Session,
    event_type: str,
    request: Optional[Request] = None,
    user_id: Optional[int] = None,
    details: Optional[str] = None,
) -> None:
    ip_address = get_client_ip(request) if request else None

    audit_log = AuditLog(
        user_id=user_id,
        event_type=event_type,
        ip_address=ip_address,
        details=details,
    )

    db.add(audit_log)
    db.commit()

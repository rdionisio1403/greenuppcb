from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.dependencies import require_admin
from app.models.user import User
from app.schemas.user import UserResponse


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

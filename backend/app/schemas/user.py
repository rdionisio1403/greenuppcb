from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator
from typing import Literal


WEAK_PASSWORDS = {
    "123456789012",
    "passwordpassword",
    "qwertyuiop12",
    "abcdefghijkl",
    "abcdefgh1234",
    "111111111111",
    "000000000000",
    "letmeinletmein",
    "adminadmin12",
}


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if value.lower() in WEAK_PASSWORDS:
            raise ValueError("Password is too weak")
        return value


class UserLogin(BaseModel):
    username: str
    password: str
    role: Literal["user", "admin"]


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=12, max_length=128)
    confirm_password: str = Field(min_length=12, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, value: str) -> str:
        if value.lower() in WEAK_PASSWORDS:
            raise ValueError("Password is too weak")
        return value

    @field_validator("confirm_password")
    @classmethod
    def validate_confirm_password_strength(cls, value: str) -> str:
        if value.lower() in WEAK_PASSWORDS:
            raise ValueError("Password is too weak")
        return value

    @field_validator("confirm_password")
    @classmethod
    def validate_password_match(cls, value: str, info):
        new_password = info.data.get("new_password")
        if new_password is not None and value != new_password:
            raise ValueError("New passwords do not match")
        return value


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr | None = None
    role: str 
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class SessionResponse(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    expires_at: datetime
    last_activity: datetime

    model_config = ConfigDict(from_attributes=True)

class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str = Field(min_length=20, max_length=256)
    new_password: str = Field(min_length=12, max_length=128)
    confirm_password: str = Field(min_length=12, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_reset_password_strength(cls, value: str) -> str:
        if value.lower() in WEAK_PASSWORDS:
            raise ValueError("Password is too weak")
        return value

    @field_validator("confirm_password")
    @classmethod
    def validate_reset_password_match(cls, value: str, info):
        new_password = info.data.get("new_password")
        if new_password is not None and value != new_password:
            raise ValueError("New passwords do not match")
        return value

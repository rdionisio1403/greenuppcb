from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator


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


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str

    model_config = ConfigDict(from_attributes=True)

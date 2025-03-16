from enum import Enum
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
import re


class UserType(str, Enum):
    COMPANY = 'company'
    GUEST = 'guest'
    STAFF = 'staff'


class PaymentGatwayEnum(str, Enum):
    FLUTTERWAVE = 'flutterwave'
    PAYSTACK = 'paystack'
    STRIPE = 'stripe'
    PAYPAL = 'payoal'


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, data: str):
        # Check if password meets requirements
        if not re.search(r"[A-Z]", data):
            raise ValueError(
                "Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", data):
            raise ValueError(
                "Password must contain at least one lowercase letter")
        if not re.search(r"\d", data):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', data):
            raise ValueError(
                "Password must contain at least one special character")
        return data


class UserCreateByAdmin(UserCreate):
    is_active: bool = True
    is_superuser: bool = False


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(None, min_length=3, max_length=50)


class UserUpdatePassword(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, data: str):
        # Check if password meets requirements
        if not re.search(r"[A-Z]", data):
            raise ValueError(
                "Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", data):
            raise ValueError(
                "Password must contain at least one lowercase letter")
        if not re.search(r"\d", data):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', data):
            raise ValueError(
                "Password must contain at least one special character")
        return data


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, data: str):
        # Check if password meets requirements
        if not re.search(r"[A-Z]", data):
            raise ValueError(
                "Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", data):
            raise ValueError(
                "Password must contain at least one lowercase letter")
        if not re.search(r"\d", data):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', data):
            raise ValueError(
                "Password must contain at least one special character")
        return data


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime = None
    company_id: str = None


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int
    page: int
    page_size: int

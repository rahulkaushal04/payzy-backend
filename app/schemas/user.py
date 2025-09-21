from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
import re


class UserBase(BaseModel):
    """Base user schema with common fields."""

    email: EmailStr = Field(..., description="User's email address")
    full_name: str = Field(
        ..., min_length=2, max_length=255, description="User's full name"
    )
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    bio: Optional[str] = Field(None, max_length=500, description="User bio")
    currency: str = Field(
        "INR", min_length=3, max_length=3, description="Preferred currency code"
    )
    timezone: str = Field("UTC", max_length=50, description="User's timezone")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            # Basic phone validation - adjust regex as needed
            if not re.match(r"^\+?[1-9]\d{1,14}$", v.replace(" ", "").replace("-", "")):
                raise ValueError("Invalid phone number format")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if not re.match(r"^[A-Z]{3}$", v):
            raise ValueError("Currency must be 3-letter ISO code (e.g., USD, EUR)")
        return v


class UserCreate(UserBase):
    """Schema for user creation."""

    password: str = Field(
        ..., min_length=8, max_length=100, description="User's password"
    )
    confirm_password: str = Field(
        ..., min_length=8, max_length=100, description="Password confirmation"
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        # Password strength validation
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserInDB(UserBase):
    """Schema for user data stored in database."""

    id: int
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class User(UserInDB):
    """Public user schema (excludes sensitive data)."""

    pass

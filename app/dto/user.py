import re
import uuid
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, model_validator, field_validator


class UserRegistrationRequest(BaseModel):
    """Schema for user creation."""

    email: EmailStr = Field(
        ..., description="User's email address", examples=["john.doe@example.com"]
    )
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="User's full name",
        examples=["John Doe"],
    )
    phone: Optional[str] = Field(
        None, max_length=20, description="Phone number", examples=["+91-9876543210"]
    )
    bio: Optional[str] = Field(
        None,
        max_length=500,
        description="User bio",
        examples=["Software developer passionate about fintech solutions"],
    )
    currency: str = Field(
        "INR",
        min_length=3,
        max_length=3,
        description="Preferred currency code",
        examples=["INR", "USD", "EUR"],
    )
    timezone: str = Field(
        "Asia/Kolkata",
        max_length=50,
        description="User's timezone",
        examples=["Asia/Kolkata", "America/New_York", "UTC"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="User's password",
        examples=["SecurePass123"],
    )
    confirm_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password confirmation",
        examples=["SecurePass123"],
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        return v

    @model_validator(mode="after")
    def validate_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserResponse(BaseModel):
    """Public user schema (all fields optional, default None)."""

    user_id: Optional[uuid.UUID] = Field(
        None, examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    email: Optional[EmailStr] = Field(
        None, description="User's email address", examples=["john.doe@example.com"]
    )
    full_name: Optional[str] = Field(None, examples=["John Doe"])
    phone: Optional[str] = Field(None, examples=["+91-9876543210"])
    bio: Optional[str] = Field(
        None, examples=["Software developer passionate about fintech solutions"]
    )
    currency: Optional[str] = Field(None, examples=["INR", "USD", "EUR"])
    timezone: Optional[str] = Field(
        None, examples=["Asia/Kolkata", "America/New_York", "UTC"]
    )
    is_active: Optional[bool] = Field(None, examples=[True])
    is_verified: Optional[bool] = Field(None, examples=[False])
    created_at: Optional[datetime] = Field(None, examples=["2024-01-15T10:30:00"])
    updated_at: Optional[datetime] = Field(None, examples=["2024-01-20T14:45:00"])

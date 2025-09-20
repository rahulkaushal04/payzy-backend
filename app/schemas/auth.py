from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class Token(BaseModel):
    """JWT token response schema."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Token expiration time in seconds")


class TokenData(BaseModel):
    """Token payload data schema."""

    user_id: int


class LoginRequest(BaseModel):
    """User login request schema."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(
        ..., min_length=8, max_length=100, description="User's password"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"email": "user@example.com", "password": "strongpassword123"}
        }
    )


class LoginResponse(BaseModel):
    """User login response schema."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict = Field(description="Basic user information")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user": {
                    "id": 1,
                    "email": "user@example.com",
                    "full_name": "John Doe",
                    "is_active": True,
                },
            }
        }
    )


class PasswordChangeRequest(BaseModel):
    """Password change request schema."""

    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(
        ..., min_length=8, max_length=100, description="New password"
    )
    confirm_password: str = Field(
        ..., min_length=8, max_length=100, description="Password confirmation"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current_password": "oldpassword123",
                "new_password": "newstrongpassword456",
                "confirm_password": "newstrongpassword456",
            }
        }
    )


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""

    email: EmailStr = Field(..., description="Email address for password reset")

    model_config = ConfigDict(
        json_schema_extra={"example": {"email": "user@example.com"}}
    )


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str = Field(..., description="Valid refresh token")

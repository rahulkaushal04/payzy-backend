import logging
from sqlalchemy import update
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta, timezone, datetime

from app.core.config import settings
from app.crud.user import User, user_crud
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, LoginResponse

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service class."""

    async def authenticate_user(
        self, db: AsyncSession, login_data: LoginRequest
    ) -> LoginResponse:
        """
        Authenticate user and generate access token.

        Args:
            db: Database session
            login_data: Login credentials

        Returns:
            Login response with token and user info

        Raises:
            HTTPException: If authentication fails
        """
        # Authenticate user
        user = await user_crud.authenticate(
            db, email=login_data.email, password=login_data.password
        )

        if not user:
            logger.warning(f"Failed login attempt for email: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user account"
            )

        # Generate access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.id, expires_delta=access_token_expires
        )

        # Update last login
        await self._update_last_login(db, user)

        logger.info(f"Successful login for user: {user.email}")

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
            user={
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "currency": user.currency,
                "timezone": user.timezone,
            },
        )

    async def _update_last_login(self, db: AsyncSession, user: User) -> None:
        """Update user's last login timestamp."""
        try:
            stmt = (
                update(User)
                .where(User.id == user.id)
                .values(last_login=datetime.now(timezone.utc))
            )
            await db.execute(stmt)
            await db.commit()
        except Exception as e:
            logger.warning(f"Failed to update last login for user {user.id}: {str(e)}")


# Create global instance
auth_service = AuthService()

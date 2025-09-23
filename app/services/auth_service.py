import logging
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, Depends
from datetime import timedelta, timezone, datetime

from app.dao.user import user_dao
from app.core.config import settings
from app.core.database import get_db
from app.entity.user import UserEntity
from app.dto.auth import LoginRequest, LoginResponse
from app.dto.user import UserRegistrationRequest, UserResponse
from app.core.security import create_access_token, verify_token

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service class."""

    async def register_user(
        self, db: AsyncSession, user_data: UserRegistrationRequest
    ) -> UserResponse:
        """
        Register a new user.

        Args:
            db: Database session
            user_data: User registration data

        Returns:
            Created user object

        Raises:
            HTTPException: If registration fails
        """
        try:
            user = await user_dao.create(db, obj_in=user_data)
            logger.info(f"New user registered: {user.email}")
            return UserResponse.model_validate(user.to_dict()).model_dump(
                mode="json", exclude_none=True
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"User registration failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed",
            )

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
        try:
            # Authenticate user
            user = await user_dao.authenticate(
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
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Inactive user account",
                )

            # Generate access token
            access_token_expires = timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
            access_token = create_access_token(
                user_id=user.user_id, expires_delta=access_token_expires
            )

            # Update last login
            await self._update_last_login(db, user)
            await db.refresh(user)

            logger.info(f"Successful login for user: {user.email}")

            return LoginResponse(
                access_token=access_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES
                * 60,  # Convert to seconds
                user=UserResponse.model_validate(user.to_dict()),
            ).model_dump(mode="json", exclude_none=True)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"User Login failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Login failed",
            )

    async def _update_last_login(self, db: AsyncSession, user: UserEntity) -> None:
        """Update user's last login timestamp."""
        try:
            stmt = (
                update(UserEntity)
                .where(UserEntity.user_id == user.user_id)
                .values(last_login=datetime.now(timezone.utc))
            )
            await db.execute(stmt)
        except Exception as e:
            logger.warning(
                f"Failed to update last login for user {user.user_id}: {str(e)}"
            )

    async def get_current_user(
        self,
        db: AsyncSession,
        access_token: str,
    ) -> UserEntity:
        """
        Get current authenticated user from JWT token.

        This dependency can be used to protect endpoints that require authentication.
        """
        try:
            credentials_exception = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

            token_data = verify_token(access_token)
            if token_data is None:
                logger.warning("Invalid token provided")
                raise credentials_exception

            user = await user_dao.get(db, user_id=token_data.user_id)
            if user is None:
                logger.warning(f"User {token_data.user_id} not found")
                raise credentials_exception

            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
                )

            return UserResponse.model_validate(user.to_dict()).model_dump(
                mode="json", exclude_none=True
            )

        except HTTPException:
            raise

        except Exception as e:
            logger.error(f"User Login failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Login failed",
            )


# Create global instance
auth_service = AuthService()

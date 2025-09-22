from fastapi import status
from typing import Optional
from sqlalchemy import select
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.entity.user import UserEntity
from app.dto.user import UserRegistrationRequest
from app.core.security import verify_password, create_password_hash


class UserCRUD:
    """User CRUD operations class."""

    async def create(
        self, db: AsyncSession, *, obj_in: UserRegistrationRequest
    ) -> UserEntity:
        # Check if user already exists
        existing_user = await self.get_by_email(db, email=obj_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Create user
        hashed_password = create_password_hash(obj_in.password)
        db_user = UserEntity(
            email=obj_in.email,
            full_name=obj_in.full_name,
            hashed_password=hashed_password,
            phone=obj_in.phone,
            bio=obj_in.bio,
            currency=obj_in.currency,
            timezone=obj_in.timezone,
            is_active=True,
            is_verified=False,
        )

        db.add(db_user)
        await db.flush()
        return db_user

    async def get(self, db: AsyncSession, *, id: int) -> Optional[UserEntity]:
        """Get user by ID."""
        result = await db.execute(select(UserEntity).where(UserEntity.id == id))
        return result.scalar_one_or_none()

    async def get_by_email(
        self, db: AsyncSession, *, email: str
    ) -> Optional[UserEntity]:
        """Get user by email address."""
        result = await db.execute(select(UserEntity).where(UserEntity.email == email))
        return result.scalar_one_or_none()

    async def authenticate(
        self, db: AsyncSession, *, email: str, password: str
    ) -> Optional[UserEntity]:
        """Authenticate user with email and password."""
        user = await self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def is_active(self, user: UserEntity) -> bool:
        """Check if user is active."""
        return user.is_active


# Create global instance
user_crud = UserCRUD()

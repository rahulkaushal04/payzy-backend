from fastapi import status
from typing import Optional
from sqlalchemy import select
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserRegistrationRequest
from app.core.security import verify_password, create_password_hash


class UserCRUD:
    """User CRUD operations class."""

    async def create(
        self, db: AsyncSession, *, obj_in: UserRegistrationRequest
    ) -> User:
        # Check if user already exists
        existing_user = await self.get_by_email(db, email=obj_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Create user
        hashed_password = create_password_hash(obj_in.password)
        db_user = User(
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
        await db.commit()
        await db.refresh(db_user)
        return db_user

    async def get(self, db: AsyncSession, *, id: int) -> Optional[User]:
        """Get user by ID."""
        result = await db.execute(select(User).where(User.id == id))
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        """Get user by email address."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def authenticate(
        self, db: AsyncSession, *, email: str, password: str
    ) -> Optional[User]:
        """Authenticate user with email and password."""
        user = await self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def is_active(self, user: User) -> bool:
        """Check if user is active."""
        return user.is_active


# Create global instance
user_crud = UserCRUD()

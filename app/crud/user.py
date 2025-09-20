from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security import verify_password


class UserCRUD:
    """User CRUD operations class."""

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

    async def is_superuser(self, user: User) -> bool:
        """Check if user is superuser."""
        return user.is_superuser


# Create global instance
user_crud = UserCRUD()

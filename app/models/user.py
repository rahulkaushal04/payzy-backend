import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean, DateTime, Integer, Text

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False
    )

    # User identification
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Authentication
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)

    # Status flags
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default="true", nullable=False
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, server_default="false", nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, server_default="false", nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Profile information
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    bio: Mapped[Optional[str]] = mapped_column(Text)

    # Preferences
    currency: Mapped[str] = mapped_column(
        String(3), server_default="USD", nullable=False
    )
    timezone: Mapped[str] = mapped_column(
        String(50), server_default="UTC", nullable=False
    )

    def __repr__(self) -> str:
        return f"<User id={self.id}, email={self.email}, full_name={self.full_name}>"

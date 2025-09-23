import uuid
import logging
import structlog
from typing import Optional
from jose import JWTError, jwt
from app.dto.auth import TokenData
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone

from app.core.config import settings

logger = structlog.get_logger(__name__)
logging.getLogger("passlib").setLevel(logging.ERROR)

# Password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # higher rounds for better security
)


def create_password_hash(password: str) -> str:
    """
    Create password hash using bcrypt.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    user_id: uuid.UUID, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token.

    Args:
        user_id: User identifier
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token string
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }

    encoded_jwt = jwt.encode(
        claims=to_encode, key=settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """
    Verify and decode JWT token.

    Args:
        token: JWT token string

    Returns:
        TokenData if valid, None if invalid
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        user_id: str = payload.get("sub")
        if user_id is None:
            logger.warning("Token missing 'sub' claim")
            return None

        # Verify token type
        token_type: str = payload.get("type", "")
        if token_type != "access":
            logger.warning("Invalid token type")
            return None

        return TokenData(user_id=uuid.UUID(user_id))

    except JWTError as e:
        logger.warning(f"Token verification failed: {str(e)}")
        return None

    except ValueError as e:
        logger.warning(f"Invalid UUID in token: {str(e)}")
        return None

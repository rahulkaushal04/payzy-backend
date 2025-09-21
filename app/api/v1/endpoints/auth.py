import structlog
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, status, Request

from app.core.database import get_db
from app.services.auth_service import auth_service
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.user import UserCreate, User as UserSchema

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post(
    "/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED
)
async def register(
    *, request: Request, db: AsyncSession = Depends(get_db), user_in: UserCreate
) -> Any:
    """
    Register a new user account.

    Creates a new user with the provided information after validation.
    The user account will be created but not verified initially.
    """
    logger.info("register_endpoint_called", email=user_in.email)
    user = await auth_service.register_user(db, user_in)
    return user


@router.post("/login", response_model=LoginResponse)
async def login(*, db: AsyncSession = Depends(get_db), login_data: LoginRequest) -> Any:
    """
    User login with email and password.

    Returns an access token that can be used to authenticate subsequent requests.
    The token expires after the configured time period.
    """
    return await auth_service.authenticate_user(db, login_data)

import structlog
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.database import get_db
from app.entity.user import UserEntity
from app.services.auth_service import auth_service
from app.dto.auth import LoginRequest, LoginResponse
from app.dto.user import UserRegistrationRequest, UserResponse

auth_router = APIRouter()
logger = structlog.get_logger(__name__)

# Security Scheme for Swagger UI
security = HTTPBearer()


@auth_router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    *, db: AsyncSession = Depends(get_db), user_in: UserRegistrationRequest
) -> Any:
    """
    Register a new user account.

    Creates a new user with the provided information after validation.
    The user account will be created but not verified initially.
    """
    logger.info("register_endpoint_called", email=user_in.email)
    responnse = await auth_service.register_user(db, user_in)
    return responnse


@auth_router.post("/login", response_model=LoginResponse)
async def login(*, db: AsyncSession = Depends(get_db), login_data: LoginRequest) -> Any:
    """
    User login with email and password.

    Returns an access token that can be used to authenticate subsequent requests.
    The token expires after the configured time period.
    """
    return await auth_service.authenticate_user(db, login_data)


@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserResponse:
    """
    Get current user information.

    Returns detailed information about the currently authenticated user.
    """
    token = credentials.credentials
    response = await auth_service.get_current_user(db, token)
    return response

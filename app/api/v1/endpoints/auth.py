from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.auth_service import auth_service
from app.schemas.auth import LoginRequest, LoginResponse

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(*, db: AsyncSession = Depends(get_db), login_data: LoginRequest) -> Any:
    """
    User login with email and password.

    Returns an access token that can be used to authenticate subsequent requests.
    The token expires after the configured time period.
    """
    return await auth_service.authenticate_user(db, login_data)

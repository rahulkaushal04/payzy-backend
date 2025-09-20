from fastapi import APIRouter
from app.api.v1.endpoints import auth, users

api_router = APIRouter()

# Include authentication routes
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Include user management routes
# api_router.include_router(users.router, prefix="/users", tags=["users"])

# TODO: Include additional routers as they are implemented
# api_router.include_router(groups.router, prefix="/groups", tags=["groups"])
# api_router.include_router(expenses.router, prefix="/expenses", tags=["expenses"]

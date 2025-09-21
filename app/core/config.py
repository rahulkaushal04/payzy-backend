import os
import secrets
from sqlalchemy import URL
from functools import lru_cache
from typing import Union, Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, AnyHttpUrl, field_validator, computed_field


class Settings(BaseSettings):
    """
    Application settings with validation and environment variable support.
    Follows Pydantic v2 patterns and production best practices.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="forbid",  # Prevent extra fields
        validate_default=True,
    )

    # API Configuration
    PROJECT_NAME: str = Field(default="payzy API", description="Project name")
    VERSION: str = Field(default="0.1.0", description="API version")
    API_V1_STR: str = Field(default="/api/v1", description="API v1 prefix")
    DESCRIPTION: str = Field(
        default="Expense tracking API", description="API description"
    )

    # Security Configuration
    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Secret key for JWT token signing",
        min_length=32,
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="JWT token expiration time in minutes",
        gt=0,
        le=60 * 24,  # Max 24 hours
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="Refresh token expiration time in days",
        gt=0,
        le=30,  # Max 30 days
    )
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    PASSWORD_MIN_LENGTH: int = Field(default=8, ge=6, le=128)

    # Database Configuration
    DATABASE_URL: Optional[PostgresDsn] = Field(
        default=None,
        description="PostgreSQL database URL (overrides individual settings if provided)",
    )
    DB_HOST: Optional[str] = Field(default=None, description="Database host")
    DB_PORT: Optional[int] = Field(
        default=None, ge=1, le=65535, description="Database port"
    )
    DB_USER: Optional[str] = Field(default=None, description="Database username")
    DB_PASSWORD: Optional[str] = Field(default=None, description="Database password")
    DB_NAME: Optional[str] = Field(default=None, description="Database name")
    DB_DRIVER: Optional[Literal["postgresql"]] = Field(
        default="postgresql",
        description="Database driver",
    )
    DB_POOL_SIZE: int = Field(default=10, ge=1, le=50)
    DB_MAX_OVERFLOW: int = Field(default=20, ge=0, le=100)
    DB_POOL_TIMEOUT: int = Field(default=30, ge=1, le=300)
    DB_POOL_RECYCLE: int = Field(default=3600, ge=300)  # 1 hour
    DB_ECHO: bool = Field(default=False, description="Echo SQL queries")

    # CORS Configuration
    BACKEND_CORS_ORIGINS: list[Union[AnyHttpUrl, str]] = Field(
        default=[], description="List of allowed CORS origins"
    )

    # Environment Configuration
    ENVIRONMENT: Literal["development", "testing", "staging", "production"] = Field(
        default="development", description="Application environment"
    )
    DEBUG: bool = Field(
        default=False, description="Enable debug mode"  # Default to False for security
    )

    # Logging Configuration
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )

    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_REQUESTS: int = Field(default=100, ge=1, le=10000)
    RATE_LIMIT_WINDOW: int = Field(default=60, ge=1, le=3600)  # seconds

    # Security Headers
    SECURITY_HEADERS_ENABLED: bool = Field(
        default=True, description="Enable security headers"
    )
    TRUSTED_HOSTS: list[str] = Field(
        default=["localhost", "127.0.0.1"], description="List of trusted host names"
    )

    # File Upload Configuration
    MAX_FILE_SIZE: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum file upload size in bytes",
    )
    ALLOWED_FILE_TYPES: list[str] = Field(
        default=["image/jpeg", "image/png", "application/pdf"],
        description="Allowed MIME types for file uploads",
    )

    # API Documentation
    DOCS_URL: Optional[str] = Field(
        default=(
            "/docs" if os.getenv("ENVIRONMENT", "development") != "production" else None
        ),
        description="Swagger UI URL path",
    )
    REDOC_URL: Optional[str] = Field(
        default=(
            "/redoc"
            if os.getenv("ENVIRONMENT", "development") != "production"
            else None
        ),
        description="ReDoc URL path",
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, list]) -> list[str]:
        """Parse and validate CORS origins from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return [str(origin) for origin in v]
        elif isinstance(v, str):
            # Handle JSON-like string format
            import ast

            try:
                parsed = ast.literal_eval(v)
                if isinstance(parsed, list):
                    return [str(origin) for origin in parsed]
            except (ValueError, SyntaxError):
                pass
        return v if isinstance(v, list) else []

    @computed_field
    @property
    def effective_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        elif all(
            [self.DB_USER, self.DB_PASSWORD, self.DB_HOST, self.DB_PORT, self.DB_NAME]
        ):
            return URL.create(
                drivername=self.DB_DRIVER,
                username=self.DB_USER,
                password=self.DB_PASSWORD,
                host=self.DB_HOST,
                port=self.DB_PORT,
                database=self.DB_NAME,
            ).render_as_string(hide_password=False)

    # Computed properties for environment checks
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Using lru_cache ensures settings are loaded once and reused across requests.
    This is the recommended pattern for FastAPI dependency injection.
    """
    return Settings()


# Global settings instance for backward compatibility
settings = get_settings()

import logging
import os
from typing import List
from functools import lru_cache
from datetime import timedelta

# Pydantic v2/v3 Imports
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# --- 🛠️ Logger Setup for Startup Output ---
# Using the root logger to ensure output is visible immediately in Docker logs.
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- ⚙️ CORE SETTINGS CLASS (Chuck Norris Approved) ---
class Settings(BaseSettings):
    """
    Configuration settings for the application, loaded from the environment
    or a local .env file. All fields are explicitly typed for Pydantic v2/v3 compliance.
    """

    # Configuration for Pydantic
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", case_sensitive=True
    )
    
    # --- FastAPI Application Metadata ---
    PROJECT_NAME: str = Field("HelixNet Core API", description="Main application name.")
    API_V1_STR: str = Field("/api/v1", description="API version prefix.")
    VERSION: str = Field("0.1.0", description="Application version.")

    # --- CORS Configuration ---
    BACKEND_CORS_ORIGINS: List[str] = Field(
        ["*"], description="Allowed origins for CORS."
    )

    # --- 🔒 SECURITY ---
    SECRET_KEY: str = Field(
        ..., description="Application secret key for signing tokens. MUST BE SET IN .ENV"
    )
    ALGORITHM: str = Field("HS256", description="JWT algorithm.")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        15, description="Access token expiry time in minutes."
    )
    REFRESH_TOKEN_EXPIRE_DAYS_DEFAULT: int = Field(
        7, description="Default refresh token expiry in days."
    )
    REFRESH_TOKEN_EXPIRE_DAYS_PRO: int = Field(
        30, description="Longer refresh token expiry for pro users."
    )
    USE_HTTP_ONLY_REFRESH_COOKIE: bool = Field(False)
    REFRESH_COOKIE_NAME: str = Field("refresh_token")

    # --- Database Configuration (PostgreSQL) ---
    POSTGRES_HOST: str = Field("postgres", description="Postgres service hostname.")
    POSTGRES_PORT: int = Field(5432, description="Postgres service port.")
    POSTGRES_DB: str = Field("helix_db", description="Postgres database name (main app).")
    POSTGRES_TEST_DB: str = Field("test_db", description="Dedicated test database name.")
    POSTGRES_USER: str = Field("helix_user", description="Postgres username.")
    POSTGRES_PASSWORD: str = Field("helix_pass", description="Postgres password.")
    
    # SQLAlchemy Pool Settings (New/Corrected fields)
    DB_POOL_SIZE: int = Field(5, description="SQLAlchemy connection pool size.")
    DB_ECHO: bool = Field(False, description="Enable SQLAlchemy logging (echo).")
    DB_MAX_OVERFLOW: int = Field(10, description="SQLAlchemy connection pool max overflow.") # Added new field

    # --- ✉️ MESSAGE BROKER (RABBITMQ for CELERY) COMPONENTS ---
    RABBITMQ_HOST: str = Field("rabbitmq", description="RabbitMQ service hostname.")
    RABBITMQ_PORT: int = Field(5672, description="RabbitMQ service port.")
    RABBITMQ_USER: str = Field("admin", description="RabbitMQ username.")
    RABBITMQ_PASS: str = Field("admin", description="RabbitMQ password.")

    # --- 🚀 CACHE / CELERY BACKEND (REDIS) COMPONENTS ---
    REDIS_HOST: str = Field("redis", description="Redis service hostname.")
    REDIS_PORT: int = Field(6379, description="Redis service port.")

    # --- 📦 OBJECT STORAGE (MINIO) COMPONENTS ---
    MINIO_HOST: str = Field("minio", description="MinIO service hostname.")
    MINIO_PORT: int = Field(9000, description="MinIO service port.")
    MINIO_BUCKET: str = Field("helixnet", description="MinIO bucket name.")
    MINIO_ACCESS_KEY: str = Field("minioadmin", description="MinIO access key.")
    MINIO_SECRET_KEY: str = Field("minioadmin", description="MinIO secret key.")
    MINIO_SECURE: bool = Field(
        False, description="Use secure (HTTPS/TLS) connection to MinIO."
    )
    
    # ======================================================================
    # 🔗 COMPUTED URI PROPERTIES (Used by FastAPI/Alembic/Celery)
    # Renamed to URI for technical correctness and consistency.
    # ======================================================================

    @property
    def POSTGRES_SYNC_URI(self) -> str:
        """Constructs the synchronous database URI (psycopg) for Alembic/Testing."""
        return (
            f"postgresql+psycopg://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )

    @property
    def POSTGRES_ASYNC_URI(self) -> str:
        """Constructs the asynchronous database URI (asyncpg). Primary app URI."""
        return (
            f"postgresql+asyncpg://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )

    @property
    def DATABASE_URI(self) -> str:
        """Legacy property pointing to the POSTGRES_ASYNC_URI."""
        return self.POSTGRES_ASYNC_URI

    @property
    def CELERY_BROKER_URI(self) -> str:
        """Constructs the Celery broker URI using RabbitMQ (AMQP)."""
        return (
            f"amqp://"
            f"{self.RABBITMQ_USER}:{self.RABBITMQ_PASS}@"
            f"{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}//"
        )

    @property
    def CELERY_BACKEND_URI(self) -> str:
        """Constructs the Celery result backend URI using Redis."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/1"

    @property
    def MINIO_ENDPOINT_URL(self) -> str:
        """Constructs the full MinIO endpoint URL."""
        protocol = "https" if self.MINIO_SECURE else "http"
        return f"{protocol}://{self.MINIO_HOST}:{self.MINIO_PORT}"

# ====================================================================
# INSTANTIATION (Singleton Factory Pattern with Chuck Norris Log Matrix)
# ====================================================================

def _print_startup_matrix(settings: Settings):
    """Prints a clear, formatted matrix of critical configuration links for Docker logs."""
    
    print("\n" + "="*80)
    print(" 💥 Helix CONFIG MATRIX: HELIXNET PLATFORM STARTUP 💥")
    print("="*80)
    
    # General Info
    print(f"  Project: {settings.PROJECT_NAME} (v{settings.VERSION})")
    print(f"  API Prefix: {settings.API_V1_STR}")
    
    # Security Summary
    print("-" * 25 + " 🔒 SECURITY " + "-" * 45)
    print(f"  JWT Algorithm: {settings.ALGORITHM}")
    print(f"  Access Token Expiry: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
    
    # Primary Services
    print("-" * 25 + " 🔗 SERVICE ENDPOINTS " + "-" * 34)
    # IMPORTANT: Reference the new URI properties
    print(f"  Postgres (Async): {settings.POSTGRES_ASYNC_URI.split('@')[0]}@...") 
    print(f"  Celery Broker:    {settings.CELERY_BROKER_URI.split('@')[0]}@...")
    print(f"  Celery Backend:   {settings.CELERY_BACKEND_URI}")
    print(f"  MinIO Endpoint:   {settings.MINIO_ENDPOINT_URL}")
    print(f"  MinIO Bucket:     {settings.MINIO_BUCKET}")
    print("="*80 + "\n")


@lru_cache
def get_settings() -> Settings:
    """Returns a cached, singleton instance of the Settings object and prints the matrix."""
    settings = Settings()
    # Print the clean matrix only once on first load
    _print_startup_matrix(settings)
    return settings


# Instantiate the singleton instance for application-wide use
settings = get_settings()

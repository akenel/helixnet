# app/core/config.py
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import  lru_cache # Note: property is the standard Python decorator

# --- ⚙️ CORE SETTINGS CLASS ---
class Settings(BaseSettings):
    """
    Configuration settings for the application, loaded from the environment 
    or a local .env file.
    """
    # Configuration for Pydantic - must be at the class level
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True
    )
    # --- FastAPI Application Metadata ---
    PROJECT_NAME: str = "HelixNet Core API"
    API_V1_STR: str = "/api/v1" 
    
    # --- Database Configuration (Values loaded from env) ---
    POSTGRES_HOST: str = Field('postgres', description="Postgres service hostname.")
    POSTGRES_PORT: int = Field(5432, description="Postgres service port.")
    POSTGRES_DB: str = Field('helix_db', description="Postgres database name.")
    POSTGRES_USER: str = Field('helix_user', description="Postgres username.")
    POSTGRES_PASSWORD: str = Field('helix_pass', description="Postgres password.")
    # Database connection tuning
    DB_POOL_SIZE: int = Field(5, description="SQLAlchemy connection pool size.")
    DB_ECHO: bool = Field(False, description="Enable SQLAlchemy logging (echo).")
    
    # --- ✉️ MESSAGE BROKER (RABBITMQ for CELERY) COMPONENTS ---
    RABBITMQ_HOST: str = Field('rabbitmq', description="RabbitMQ service hostname.")
    RABBITMQ_PORT: int = Field(5672, description="RabbitMQ service port.")
    RABBITMQ_USER: str = Field('admin', description="RabbitMQ username.")
    RABBITMQ_PASS: str = Field('admin', description="RabbitMQ password.")
    
    # --- 🚀 CACHE / CELERY BACKEND (REDIS) COMPONENTS ---
    REDIS_HOST: str = Field('redis', description="Redis service hostname.")
    REDIS_PORT: int = Field(6379, description="Redis service port.")
    
    # --- 📦 OBJECT STORAGE (MINIO) COMPONENTS ---
    MINIO_HOST: str = Field('minio', description="MinIO service hostname.")
    MINIO_PORT: int = Field(9000, description="MinIO service port.")
    MINIO_BUCKET: str = Field('helixnet', description="MinIO bucket name.")
    MINIO_ACCESS_KEY: str = Field('minioadmin', description="MinIO access key.")
    MINIO_SECRET_KEY: str = Field('minioadmin', description="MinIO secret key.")
    MINIO_SECURE: bool = Field(False, description="Use secure (HTTPS/TLS) connection to MinIO.")
    
    # --- 🔒 SECURITY ---
    SECRET_KEY: str = Field("super-secret-key", description="Application secret key for signing tokens.")
    ALGORITHM: str = Field("HS256", description="JWT algorithm.")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, description="Access token expiry time in minutes.")
    
    # --- COMPUTED URL PROPERTIES (Standard @property to avoid unpicklable locks) ---
    @property
    def POSTGRES_SYNC_URL(self) -> str:
        """Constructs the fully formatted synchronous database URL."""
        return (
            f"postgresql+psycopg://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )

    @property
    def POSTGRES_ASYNC_URL(self) -> str:
        """Constructs the fully formatted asynchronous database URL (asyncpg)."""
        return (
            f"postgresql+asyncpg://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )
    @property
    def CELERY_BROKER_URL(self) -> str:
        """Constructs the Celery broker URL using RabbitMQ (AMQP)."""
        return (
            f"amqp://"
            f"{self.RABBITMQ_USER}:{self.RABBITMQ_PASS}@"
            f"{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}//"
        )

    @property
    def CELERY_BACKEND_URL(self) -> str:
        """Constructs the Celery result backend URL using Redis (Database 1)."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/1"
    
    @property
    def MINIO_ENDPOINT(self) -> str:
        """Constructs the MinIO endpoint URL."""
        protocol = "https" if self.MINIO_SECURE else "http"
        return f"{protocol}://{self.MINIO_HOST}:{self.MINIO_PORT}"

# ====================================================================
# INSTANTIATION (Singleton Factory Pattern)
# ====================================================================

@lru_cache # Ensures the function only runs once and caches the result
def get_settings() -> Settings:
    """Returns a cached, singleton instance of the Settings object."""
    return Settings()

# 🔑 CRITICAL FIX: The global 'settings' variable is removed!
# All modules must now import and call get_settings() instead.
# Instantiate settings globally so modules can do: from app.core.config import settings
settings = get_settings()

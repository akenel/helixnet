import asyncio
import logging
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr, EmailStr

# ----------------------------------------------------------------------
# LOGGER
# ----------------------------------------------------------------------
logger = logging.getLogger("🌱 HelixNet.Config")
logger.setLevel(logging.INFO)
# ----------------------------------------------------------------------
# SETTINGS CLASS
# ----------------------------------------------------------------------

class Settings(BaseSettings):
    """
    Application configuration focused on resolving the authentication issues.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True,
    )
# 🧠 Key essentails   
    API_VERSION: str = "helix_v0.0.1"
    OPENAPI_URL: str = "/api/v1/openapi.json" # Standard FastAPI settings
    DOCS_URL: str = "/docs"
    KEYCLOAK_HELIX_REALM_INTERNAL_URL: str = "http://keycloak:8080/realms/kc-realm-dev"
    KEYCLOAK_BASE_URL: str = "https://keycloak.helix.local"
    FASTAPI_BASE_URL: str = "https://helix.local"
# Keycloak
    # FIX: Set the default to the correct internal Docker network URL (http://service:port)
    KEYCLOAK_SERVER_URL: str = "http://keycloak:8080"
    KEYCLOAK_REALM: str = "kc-realm-dev"
    KEYCLOAK_MASTER_REALM: str = "master"
    KC_HOSTNAME: str = "keycloak.helix.local"
    KC_HTTP_PORT: int = 8080
# Clients & service account
    KEYCLOAK_CLIENT_ID: str = "helix_user"
    # KEYCLOAK_CLIENT_SECRET: SecretStr

    KEYCLOAK_SERVICE_CLIENT_ID:  str = "helix_user"
    KC_HOSTNAME_ADMIN_URL: str = "https://keycloak.helix.local"

    KEYCLOAK_CLIENT_SECRET: str = "b0iGaUc9EIC7dw5KzJL1JveNWfTMxjGB"
    KEYCLOAK_SERVICE_CLIENT_SECRET: str = "b0iGaUc9EIC7dw5KzJL1JveNWfTMxjGB"



# Seeder superuser
    HX_SUPER_NAME:  str = "helix_user"
    HX_SUPER_EMAIL: EmailStr = "helix_user@helix.net"
    HX_SUPER_PASSWORD:  str = "helix_pass"
# --- App Metadata ---
    KC_EXTERNAL_URL: str = "https://keycloak.helix.local/realms/kc-realm-dev"
    HX_ENVIRONMENT: str = "dev"  # e.g., development, staging, production match .env
    PROJECT_NAME: str = "HelixNet Core API"
    PROJECT_APP_VERSION: str = "0.0.1"  # expect values from .env to replace this values
    API_V1_STR: str = "/api/v1"
    APP_HOST: str = "0.0.1"
    APP_PORT: int = 8000
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
# --- Security ---
    VAULT_DEV_ROOT_TOKEN_ID: str = "myroot"
    VAULT_ADDR: str = "http://127.0.0.1:8200"
    VAULT_TOKEN: SecretStr
    VAULT_DEV_LISTEN_ADDRESS: str = "0.0.0.0:8200"
#  SECURITY Keys / Tokens
    SECRET_KEY: str
    KEYCLOAK_ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS_DEFAULT: int = 7
    USE_HTTP_ONLY_REFRESH_COOKIE: bool = False
    REFRESH_COOKIE_NAME: str = "refresh_token"
# Database
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "helix_db"
    POSTGRES_TEST_DB: str = "test_db"
    POSTGRES_USER: str = "helix_user"
    POSTGRES_PASSWORD: SecretStr
    DB_POOL_SIZE: int = 5
    DB_ECHO: bool = False
    DB_MAX_OVERFLOW: int = 10
# RabbitMQ / Redis
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "helix_user"
    RABBITMQ_PASS: SecretStr
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
# MinIO
    MINIO_HOST: str = "minio"
    MINIO_PORT: int = 9000
    MINIO_BUCKET: str = "kc-realm-dev" 
    MINIO_ACCESS_KEY: str = SecretStr
    MINIO_SECRET_KEY: str = SecretStr
    MINIO_SECURE: bool = False
# Computed properties
    @property
    def KEYCLOAK_ISSUER_URL(self) -> str:
        # Note: This still uses KC_HOSTNAME (external) but with http and port 8080. 
        # For external clients, this might be fine, but S2S must use KEYCLOAK_SERVER_URL.
        return f"http://{self.KC_HOSTNAME}:{self.KC_HTTP_PORT}/realms/{self.KEYCLOAK_REALM}"
    @property
    def KEYCLOAK_JWKS_URL(self) -> str:
        return f"{self.KEYCLOAK_ISSUER_URL}/protocol/openid-connect/certs"
    @property
    def POSTGRES_SYNC_URI(self) -> str:
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD.get_secret_value()}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    @property
    def POSTGRES_ASYNC_URI(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD.get_secret_value()}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    @property
    def CELERY_BROKER_URI(self) -> str:
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASS}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}//"
    @property
    def CELERY_BACKEND_URI(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/1"
    @property
    def MINIO_ENDPOINT_URL(self) -> str:
        proto = "https" if self.MINIO_SECURE else "http"
        return f"{proto}://{self.MINIO_HOST}:{self.MINIO_PORT}"
    # --- KEYCLOAK ADMIN CREDENTIALS (The Fix) ---
    KEYCLOAK_ADMIN_USER: str = Field(
        default="admin",
        alias="KEYCLOAK_ADMIN_USER"
    )
    KEYCLOAK_ADMIN_PASSWORD: SecretStr = Field(
        alias="KEYCLOAK_ADMIN_PASSWORD"
    )
    # --- MINIO CREDENTIALS ---
    MINIO_ACCESS_KEY: str = Field(
        default="helix_user", 
        alias="MINIO_ACCESS_KEY"
    )
    MINIO_SECRET_KEY: str = Field(
        default="helix_pass",
        alias="MINIO_SECRET_KEY"
    )
    @property
    def DEBUG_KC_ADMIN_PASSWORD(self) -> str:
        if self.KEYCLOAK_ADMIN_PASSWORD:
            return self.KEYCLOAK_ADMIN_PASSWORD.get_secret_value()
        return "N/A"
# ----------------------------------------------------------------------
# nice clean startup printer (single definition)
# ----------------------------------------------------------------------
def _print_startup_matrix(s: Settings) -> None:
    """Console-friendly startup matrix (keeps it small and safe)."""
# Print Header with maximum pride
    print("\n" + "⚡" * 80)
    print(f" 💥 HALT! CONFIG MATRIX INITIATED: {s.PROJECT_NAME} (v{s.PROJECT_APP_VERSION}) 💥")
    print(" 🥋 QA PASSED: CHUCK NORRIS TRIPLE ROUNDHOUSE CONFIGURATION CHECK COMPLETE 🥋")
    print("⚡" * 80)   
# --- 2. IDENTITY PROVIDER (KEYCLOAK) CONFIG ---
    print("\n" + "=" * 20 + " 🔑 IDENTITY PROVIDER (KEYCLOAK) " + "=" * 23)
    # NOTE: Printing the internal host used for S2S calls
    print(f"  KC Internal Host:   {s.KEYCLOAK_SERVER_URL}") 
    print(f"  KC Realm Name:      {s.KEYCLOAK_REALM}")
    print(f"  KC Issuer URL:      {s.KEYCLOAK_ISSUER_URL}")
    print(f"  KC JWKS URL:        {s.KEYCLOAK_JWKS_URL}")

    print("-" * 59)
    print("  Service Client (Runtime Admin):")
    # print(f"    ID:             {s.KEYCLOAK_CLIENT_ID}")
    # print(f"    Secret:         {s.KEYCLOAK_CLIENT_SECRET}")

    print("-" * 59)
    print("  Master/Bootstrap Admin:")
    print(f"    User:           {s.HX_SUPER_NAME}") # Print the HX_SUPER_NAME used for bootstrapping
    print(f"    Password:       {'Present' if s.HX_SUPER_PASSWORD else '❌ MISSING'}")
    print(f"  External Admin URL: {s.KC_EXTERNAL_URL}/admin") # Assuming KC_EXTERNAL_URL is available 
# --- 3. PERSISTENCE LAYER CONFIG ---
    print("\n" + "=" * 20 + " 💾 PERSISTENCE (DB, Cache, Storage) " + "=" * 18)
# Database
    print(f"  Postgres Host:      {s.POSTGRES_HOST}:{s.POSTGRES_PORT}")
    print(f"  Postgres DB Name:   {s.POSTGRES_DB} (User: {s.POSTGRES_USER})")
    print(f"  Postgres Sync URI:  {s.POSTGRES_SYNC_URI.split('@')[0]}@...")
    print(f"  Postgres Async URI: {s.POSTGRES_ASYNC_URI.split('@')[0]}@...")
# Object Storage (MinIO)
    print(f"  MinIO Host:         {s.MINIO_HOST}:{s.MINIO_PORT}")
    print(f"  MinIO Endpoint URL: {s.MINIO_ENDPOINT_URL}")
    print(f"  MinIO Bucket:       {s.MINIO_BUCKET} (Key: {s.MINIO_ACCESS_KEY})")
# --- 4. ASYNCHRONOUS TASK CONFIG ---
    print("\n" + "=" * 20 + " 📩 MESSAGE BROKERS (Celery) " + "=" * 26)
# RabbitMQ
    print(f"  RabbitMQ Host:      {s.RABBITMQ_HOST}:{s.RABBITMQ_PORT}")
    print(f"  Celery Broker URI:  {s.CELERY_BROKER_URI.split('@')[0]}@...")
# Redis
    print(f"  Redis Host:         {s.REDIS_HOST}:{s.REDIS_PORT}")
    print(f"  Celery Backend URI: {s.CELERY_BACKEND_URI}")
    print("\n" + "⚡" * 80)
    print(" 🚀 CONFIGURATION LOADED. PROCEEDING TO SERVICE INITIALIZATION. 🚀")
    print("⚡" * 80 + "\n")
# ----------------------------------------------------------------------
# singleton factory
# ----------------------------------------------------------------------
@lru_cache()
def get_settings() -> Settings:
    s = Settings()
    # print startup matrix on creation once
    _print_startup_matrix(s)
    return s
# ----------------------------------------------------------------------
# helper functions that use lazy imports to avoid circulars
# ----------------------------------------------------------------------
async def get_keycloak_admin_token(max_retries: int = 10, retry_delay: int = 5) -> Optional[str]:
    """
    Acquire Keycloak admin token for startup tasks.
    Uses lazy imports (httpx) and references get_settings() at runtime.
    """
    import httpx  # lazy import
    s = get_settings()
    # token_url now correctly uses the fixed KEYCLOAK_SERVER_URL
    token_url = f"{s.KEYCLOAK_SERVER_URL}/realms/{s.KEYCLOAK_MASTER_REALM}/protocol/openid-connect/token"

    auth_data = {
        "grant_type": "password",
        "client_id": "admin-cli",
        # FIX: Use configuration variables for credentials
        "username": s.HX_SUPER_NAME,
        "password": s.HX_SUPER_PASSWORD,
    }
    for attempt in range(1, max_retries + 1):
        try:
            # verify=False is often needed for internal S2S calls when not using proper CAs
            async with httpx.AsyncClient(verify=False, timeout=10) as client:
                resp = await client.post(token_url, data=auth_data, headers={"Content-Type": "application/x-www-form-urlencoded"})
                resp.raise_for_status()
                payload = resp.json()
                logger.info(f"✅ [SUCCESS] Admin token acquired on attempt {attempt}")
                return payload.get("access_token")
        except httpx.HTTPStatusError as he:
            logger.warning(
                f"❌ [401 FAILED KICKiS] Status {he.response.status_code} on attempt {attempt}. Keycloak Error Body: {he.response.json()}. Retrying in {retry_delay}s."
            )
        except Exception as e:
            logger.warning(f"⚠️ [CONNECTION FAIL] Keycloak network error on attempt {attempt}/{max_retries}. Error Type: {type(e).__name__}. Retrying in {retry_delay}s.")

        if attempt < max_retries:
            await asyncio.sleep(retry_delay)
    logger.error("🚨 KEYCLOAK HALT: Admin Token acquisition failed after all attempts. Check MASTER_REALM credentials/client configuration match both realms.")
    return None

async def create_initial_users(db) -> None:
    """
    Seeder that creates initial superuser in DB and Keycloak.
    Use lazy imports to avoid circular dependencies with db/models or services.
    """
    # Lazy imports to avoid circular import at module import time
    from sqlalchemy import select
    from src.db.models import UserModel  # import here to avoid circulars
    s = get_settings()

    logger.info("🌱 Starting initial user seeding...")
    token = await get_keycloak_admin_token()
    if not token:
        logger.error("🚨 [HALT] Cannot proceed with user seeding: Keycloak Admin Token missing.")
        return
    stmt = select(UserModel).where(UserModel.username == s.HX_SUPER_NAME)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        logger.info("⏭️ Superuser already exists, skipping seeding.")
        return
    # Insert DB creation + remote Keycloak creation logic here.
    # Keep this function minimal. Prefer calling KeycloakProxyService from runtime code
    # where an aiohttp.ClientSession can be injected. Do not import KeycloakProxyService here at module level.
    logger.info("🎯 Seeder: superuser creation needs application-specific implementation.")
# ----------------------------------------------------------------------
# instantiate module-level settings singleton (safe)
# ----------------------------------------------------------------------
settings = get_settings()
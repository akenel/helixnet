import logging
from typing import List
from functools import lru_cache
# Using Pydantic V2 for configuration management
from pydantic import EmailStr, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
#

# --- 🛠️ Logger Setup for Startup Output ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- ⚙️ CORE SETTINGS CLASS (Chuck Norris Approved) ---
class Settings(BaseSettings):
    """
    Configuration settings for the application, loaded from the environment
    or a local .env file. Pydantic handles automatic loading of variables 
    that match the field names.
    """

    # Configuration for Pydantic
    model_config = SettingsConfigDict(
        env_file=".env", 
        extra="ignore", 
        case_sensitive=True # Ensure variable names match exactly
    )

    # --- FastAPI Application Metadata ---
    PROJECT_NAME: str = Field("HelixNet Core API", description="🕹️  Main application name.")
    API_V1_STR: str = Field("/api/v1", description="🕹️  API version prefix.")
    PROJECT_APP_VERSION: str = Field("0.1.0", description="🕹️  Application version.")
    APP_HOST: str = Field("0.0.0.0", description="🕹️  Uvicorn binding host.")
    APP_PORT: int = Field(8000, description="🕹️  Uvicorn binding port.")

    # --- CORS Configuration ---
    BACKEND_CORS_ORIGINS: List[str] = Field(
        ["*"], description="Allowed origins for CORS."
    )

    # ======================================================================
    # --- 🔒 SECURITY & CORE SECRETS ---
    # ======================================================================
    SECRET_KEY: str = Field(
        ...,
        description="Application secret key for signing cookies/sessions. MUST BE SET IN .ENV",
    )
    USE_HTTP_ONLY_REFRESH_COOKIE: bool = Field(
        False, description="Use HTTP-only cookie for refresh token."
    )
    REFRESH_COOKIE_NAME: str = Field("refresh_token", description="Name of the refresh token cookie.")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(3, description="Keycloak Access token expiry default in minutes.")
    REFRESH_TOKEN_EXPIRE_DAYS_DEFAULT: int = Field(7, description="Keycloak Refresh Access token expiry default in days.")
    # ---------------------------------------------------------------------
    # 3. INITIAL USER SEEDING (The Missing Fields!)
    # ---------------------------------------------------------------------
    # These environment variables MUST be set for the initial admin user creation
    HX_SUPER_NAME: str = Field(default="admin", description="Username for the initial admin account.")
    HX_SUPER_PASSWORD: str = Field("", description="Password for the initial admin account.")
    HX_SUPER_EMAIL: EmailStr = Field(default="admin@helix.net", description="Email for the initial admin account.")
    # ======================================================================
    # 🔑 IDENTITY PROVIDER (KEYCLOAK) CONFIGURATION
    # ======================================================================
    # These fields must match the environment variables in your .env / Docker Compose
    KC_REALM: str = Field("helixnet", description="🕹️  Keycloak realm name.")
    KC_CLIENT_ID: str = Field("helix-web-app", description="🔑 Keycloak client ID for the web app.")
    KC_CLIENT_SECRET: str = Field("", description="🗝️ Keycloak client secret for token exchange.")
    
    KC_AUTH_SERVER_URL: str = Field("https://keycloak.helix.local/realms/helixnet/protocol/openid-connect/token", 
                                    description="🕹️ Internal Keycloak OIDC issuer URL.")
    
    # Keycloak Admin Setup (For Docker bootstrap only)
    KEYCLOAK_ADMIN_USER: str = Field(..., description="🕹️  Keycloak initial admin user.")
    KEYCLOAK_ADMIN_PASSWORD: str = Field(..., description="🕹️  Keycloak initial admin password.")

    # KEYCLOAK VALIDATION METADATA (Used by python-keycloak library)
    KC_HOSTNAME: str = Field("keycloak", description="🕹️  Keycloak service hostname (internal).")
    KC_HTTP_PORT: int = Field(8080, description="Keycloak service port (internal).")
    KEYCLOAK_ALGORITHM: str = Field(
        "RS256",
        description="Keycloak signature algorithm (RS256 required for public key validation).",
    )

    # --- Database Configuration (PostgreSQL) ---
    POSTGRES_HOST: str = Field("postgres", description="🕹️  Postgres service hostname.")
    POSTGRES_PORT: int = Field(5432, description="Postgres service port.")
    POSTGRES_DB: str = Field("helix_db", description="Postgres database name (main app).")
    POSTGRES_TEST_DB: str = Field("test_db", description="Dedicated test database name.")
    POSTGRES_USER: str = Field("helix_user", description="Postgres username.")
    POSTGRES_PASSWORD: str = Field("helix_pass", description="Postgres password.")

    # SQLAlchemy Pool Settings
    DB_POOL_SIZE: int = Field(5, description="SQLAlchemy connection pool size.")
    DB_ECHO: bool = Field(False, description="Enable SQLAlchemy logging (echo).")
    DB_MAX_OVERFLOW: int = Field(10, description="SQLAlchemy connection pool max overflow.")

    # --- ✉️ MESSAGE BROKER (RABBITMQ for CELERY) COMPONENTS ---
    RABBITMQ_HOST: str = Field("rabbitmq", description="RabbitMQ service hostname.")
    RABBITMQ_PORT: int = Field(5672, description="RabbitMQ service port.")
    RABBITMQ_USER: str = Field("admin", description="RabbitMQ username.")
    RABBITMQ_PASS: str = Field("admin", description="RabbitMQ password.")

    # --- 🚀 CACHE / CELERY BACKEND (REDIS) COMPONENTS ---
    REDIS_HOST: str = Field("redis", description="Redis service hostname.")
    REDIS_PORT: int = Field(6379, description="Redis service port.")

    # --- 📦 OBJECT STORAGE (MINIO) COMPONENTS ---
    MINIO_HOST: str = Field("minio", description="🕹️  MinIO service hostname.")
    MINIO_PORT: int = Field(9000, description="MinIO service port.")
    MINIO_BUCKET: str = Field("helixnet", description="MinIO bucket name.")
    MINIO_ACCESS_KEY: str = Field("minioadmin", description="MinIO access key.")
    MINIO_SECRET_KEY: str = Field("minioadmin", description="MinIO secret key.")
    MINIO_SECURE: bool = Field(False, description="Use secure (HTTPS/TLS) connection to MinIO.")

    # ======================================================================
    # 🔗 COMPUTED URI PROPERTIES (Used by FastAPI/Alembic/Celery/Keycloak)
    # ======================================================================
    # These properties provide clean, ready-to-use URIs based on the settings above.

    @property
    def KEYCLOAK_ISSUER_URL(self) -> str:
        """The URL that issues the tokens (used for token validation)."""
        # This is typically the realm URL used by python-keycloak for configuration
        return self.KC_AUTH_SERVER_URL

    @property
    def KEYCLOAK_JWKS_URL(self) -> str:
        """The endpoint providing the public key for token verification."""
        # Note: python-keycloak handles the discovery of this, but it's good to know.
        return f"http://{self.KC_HOSTNAME}:{self.KC_HTTP_PORT}/realms/{self.KC_REALM}/protocol/openid-connect/certs"
    # ✅ FIX: This is the missing configuration setting causing the AttributeError.
    # It must be the base URL for Keycloak within the internal network (e.g., Docker bridge).
    KEYCLOAK_SERVER_URL: str = Field(
        default="http://keycloak:8080", 
        description="🕹️  Internal base URL for Keycloak (used for admin requests and service-to-service comms)."
    )
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
        
    def model_post_init(self, context):
        """Perform validation checks after all settings are loaded."""
        missing_vars = []
        if not self.SECRET_KEY or self.SECRET_KEY == '...':
            missing_vars.append("SECRET_KEY")
        if not self.KEYCLOAK_ADMIN_USER or self.KEYCLOAK_ADMIN_USER == '...':
            missing_vars.append("KEYCLOAK_ADMIN_USER")
        if not self.KEYCLOAK_ADMIN_PASSWORD or self.KEYCLOAK_ADMIN_PASSWORD == '...':
            missing_vars.append("KEYCLOAK_ADMIN_PASSWORD")

        if missing_vars:
            raise ValueError(
                f"🚨 Critical Configuration Error! The following variables are missing "
                f"or unset in your environment/'.env' file: {', '.join(missing_vars)}. "
                f"This must be fixed for 'Chuck's Triple Roundhouse' to succeed."
            )

# ====================================================================
# INSTANTIATION (Singleton Factory Pattern with Chuck Norris Log Matrix)
# ====================================================================

def _print_startup_matrix(settings: Settings):
    """Prints the comprehensive HelixNet startup configuration matrix, QA Approved."""

    # Dynamic URLs based on loaded settings
    KEYCLOAK_BASE_URL = f"http://{settings.KC_HOSTNAME}:{settings.KC_HTTP_PORT}"
    KEYCLOAK_EXTERNAL_BASE = "http://localhost:8080" # Assuming external port mapping

    # Print Header with maximum pride
    print("\n" + "⚡" * 80)
    print(f" 💥 HALT! CONFIG MATRIX INITIATED: {settings.PROJECT_NAME} (v{settings.PROJECT_APP_VERSION}) 💥")
    print(" 🥋 QA PASSED: CHUCK NORRIS TRIPLE ROUNDHOUSE CONFIGURATION CHECK COMPLETE 🥋")
    print("⚡" * 80)
    
    # --- 1. APPLICATION & NETWORK CONFIG ---
    print("\n" + "=" * 20 + " ⚙️ APPLICATION & NETWORK " + "=" * 34)
    print(f"  Project Name:       {settings.PROJECT_NAME}")
    print(f"  API Bind Address:   {settings.APP_HOST}:{settings.APP_PORT}")
    print(f"  CORS Allowed:       {settings.BACKEND_CORS_ORIGINS}")
    print(f"  Secret Key Set:     ✅ (Length: {len(settings.SECRET_KEY)})")
    
    # --- 2. IDENTITY PROVIDER (KEYCLOAK) CONFIG ---
    print("\n" + "=" * 20 + " 🔑 IDENTITY PROVIDER (KEYCLOAK) " + "=" * 23)
    print(f"  KC Internal Host:   {settings.KC_HOSTNAME}:{settings.KC_HTTP_PORT}")
    print(f"  KC Admin User:      {settings.KEYCLOAK_ADMIN_USER}")
    print(f"  KC Realm Name:      {settings.KC_REALM}")
    print(f"  KC Client ID:       {settings.KC_CLIENT_ID}")
    print(f"  KC Client Secret:   {'Present' if settings.KC_CLIENT_SECRET else '❌ MISSING (OK for Public Client)'}")
    print(f"  KC Issuer URL:      {settings.KEYCLOAK_ISSUER_URL}")
    print(f"  KC JWKS URL:        {settings.KEYCLOAK_JWKS_URL}")
    print(f"  External Admin URL: {KEYCLOAK_EXTERNAL_BASE}/admin")
    
    # --- 3. PERSISTENCE LAYER CONFIG ---
    print("\n" + "=" * 20 + " 💾 PERSISTENCE (DB, Cache, Storage) " + "=" * 18)
    # Database
    print(f"  Postgres Host:      {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
    print(f"  Postgres DB Name:   {settings.POSTGRES_DB} (User: {settings.POSTGRES_USER})")
    print(f"  Postgres Sync URI:  {settings.POSTGRES_SYNC_URI.split('@')[0]}@...")
    print(f"  Postgres Async URI: {settings.POSTGRES_ASYNC_URI.split('@')[0]}@...")
    
    # Object Storage (MinIO)
    print(f"  MinIO Host:         {settings.MINIO_HOST}:{settings.MINIO_PORT}")
    print(f"  MinIO Endpoint URL: {settings.MINIO_ENDPOINT_URL}")
    print(f"  MinIO Bucket:       {settings.MINIO_BUCKET} (Key: {settings.MINIO_ACCESS_KEY})")
    
    # --- 4. ASYNCHRONOUS TASK CONFIG ---
    print("\n" + "=" * 20 + " 📩 MESSAGE BROKERS (Celery) " + "=" * 26)
    # RabbitMQ
    print(f"  RabbitMQ Host:      {settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}")
    print(f"  Celery Broker URI:  {settings.CELERY_BROKER_URI.split('@')[0]}@...")
    
    # Redis
    print(f"  Redis Host:         {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    print(f"  Celery Backend URI: {settings.CELERY_BACKEND_URI}")
    
    print("\n" + "⚡" * 80)
    print(" 🚀 CONFIGURATION LOADED. PROCEEDING TO SERVICE INITIALIZATION. 🚀")
    print("⚡" * 80 + "\n")


@lru_cache
def get_settings() -> Settings:
    """Returns a cached, singleton instance of the Settings object and prints the matrix."""
    try:
        settings = Settings()
    except ValidationError as e:
        logger.error(f"Pydantic Validation Error during startup: {e}")
        # Re-raise the error to stop the application gracefully
        raise
        
    _print_startup_matrix(settings)
    return settings


# Instantiate the singleton instance for application-wide use
settings = get_settings()

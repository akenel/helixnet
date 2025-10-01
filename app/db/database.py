"""
Database configuration and session management for SQLAlchemy Async.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

# --- Configuration (Assumed from Docker/Env) ---
DATABASE_URL = "postgresql+asyncpg://helix_user:helix_pass@postgres:5432/helix_db" 

# --- Base for declarative models ---
Base = declarative_base()

# --- Engine Setup ---
engine = create_async_engine(
    DATABASE_URL,
    echo=True, # Set to False in production, helpful for debugging
    future=True
)

# --- Session Factory ---
AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# --- Dependency Function for Routes ---
async def get_db_session():
    """Provides a fresh database session for dependency injection."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# --- Initialization Function (CRITICAL FIX WITH DIAGNOSTICS) ---
async def init_db():
    """
    Initializes the database by creating all tables defined in the Base metadata.
    This must be called at application startup.
    """
    # CRITICAL FIX: Explicitly import all model CLASSES. This is the most reliable 
    # way to ensure they are registered with Base.metadata.
    try:
        from app.db.models.user import User  # Import the class
        from app.db.models.job_result import JobResult # Import the class
        print("✅ Attempted model CLASS imports for User and JobResult.")
    except ImportError as e:
        print(f"🚨 CRITICAL ERROR: Could not import models. Check folder structure and class names. Error: {e}")
        # If imports fail here, there's no way to proceed with table creation.
        raise # Raise the error to stop the application gracefully.

    # DIAGNOSTIC CHECK: Print which tables Base.metadata has registered
    registered_tables = list(Base.metadata.tables.keys())
    print(f"⚙️ SQLAlchemy Metadata check found tables: {registered_tables}")

    if not registered_tables:
        print("⚠️ WARNING: No tables found in Base.metadata. Check your model definitions and imports.")
        
    async with engine.begin() as conn:
        print("⏳ Running Base.metadata.create_all...")
        # Run the synchronous table creation within an async context
        await conn.run_sync(Base.metadata.create_all)
        print("🚀 Database tables initialized successfully. Proceeding with requests.")

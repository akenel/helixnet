import logging
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Iterator, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine, text
from src.db.models.base import Base
from src.core.config import get_settings

# Import all models so they register with Base.metadata for Alembic
from src.db.models import (  # noqa: F401
    UserModel,
    TeamModel,
    RefreshTokenModel,
    JobModel,
    TaskModel,
    ArtifactModel,
    MessageTaskModel,
    PipelineTaskModel,
    InitializerModel,
    ProductModel,
    TransactionModel,
    LineItemModel,
    # CRACK Loyalty Models
    CustomerModel,
    KBContributionModel,
    CreditTransactionModel,
    # HR/Payroll Models (BLQ Module)
    EmployeeModel,
    TimeEntryModel,
    PayrollRunModel,
    PaySlipModel,
    # Camper & Tour Service Management
    CamperVehicleModel,
    CamperCustomerModel,
    CamperServiceJobModel,
    # QA Testing Dashboard
    QATestResultModel,
    QABugReportModel,
    # LPCX -- La Piazza Compute Exchange
    ComputeJobModel,
    ComputeLedgerModel,
    ComputeTemplateModel,
    ComputeNodeModel,
    BottegaProfileModel,
    BottegaProfileHistoryModel,
)

logger = logging.getLogger("app/db/database.py 🪵️")
logger.setLevel(logging.INFO)
settings = get_settings()

# ================================================================
# ⚙️ ENGINE DEFINITIONS
# ================================================================
async_engine: Optional[AsyncEngine] = create_async_engine(
    settings.POSTGRES_ASYNC_URI,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

SyncSessionLocal: Optional[sessionmaker] = None

# ================================================================
# 🔗 ASYNC SESSION DEPENDENCY
# ================================================================
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()

# ================================================================
# 💉 CONTEXT MANAGER
# ================================================================
@asynccontextmanager
async def get_db_session_context() -> AsyncGenerator[AsyncSession, None]:
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        logger.error(f"Database transaction error: {e}")
        await session.rollback()
        raise
    finally:
        await session.close()

# ================================================================
# 🧱 INITIALIZATION
# ================================================================
async def init_db_tables() -> None:
    """Ensure all ORM models are registered and create missing tables."""
    async with async_engine.begin() as conn:
        logger.info("Checking database for missing tables and attempting creation...")
        await conn.run_sync(Base.metadata.create_all)
    await _ensure_lightweight_columns()
    logger.info("✅ Database table initialization complete.")


# Idempotent, additive-only column migrations for tables that already exist.
# create_all() only makes MISSING tables -- it never adds columns to a table that
# is already there. These ALTERs run on every env (not debug-gated) and are safe on
# a shared DB: ADD COLUMN IF NOT EXISTS is non-destructive and backward-compatible
# (older code that doesn't select the column is unaffected). Postgres only.
_ADDITIVE_COLUMNS: list[str] = [
    # Today "breakdowns" block (2026-06-12): sub-tasks, time, assignee, edit history.
    "ALTER TABLE bottega_tasks ADD COLUMN IF NOT EXISTS parent_id UUID",
    "ALTER TABLE bottega_tasks ADD COLUMN IF NOT EXISTS estimate_min INTEGER",
    "ALTER TABLE bottega_tasks ADD COLUMN IF NOT EXISTS assignee VARCHAR(100)",
    "ALTER TABLE bottega_tasks ADD COLUMN IF NOT EXISTS house VARCHAR(60)",
    "ALTER TABLE bottega_tasks ADD COLUMN IF NOT EXISTS collaborators TEXT",
    "ALTER TABLE bottega_tasks ADD COLUMN IF NOT EXISTS history TEXT",
    "ALTER TABLE bottega_tasks ADD COLUMN IF NOT EXISTS project VARCHAR(40)",
    "ALTER TABLE bottega_tasks ADD COLUMN IF NOT EXISTS task_key VARCHAR(60)",
    "CREATE INDEX IF NOT EXISTS ix_bottega_tasks_parent_id ON bottega_tasks (parent_id)",
    "CREATE INDEX IF NOT EXISTS ix_bottega_tasks_assignee ON bottega_tasks (assignee)",
    "CREATE INDEX IF NOT EXISTS ix_bottega_tasks_house ON bottega_tasks (house)",
    "CREATE INDEX IF NOT EXISTS ix_bottega_tasks_project ON bottega_tasks (project)",
    "CREATE INDEX IF NOT EXISTS ix_bottega_tasks_task_key ON bottega_tasks (task_key)",
]


async def _ensure_lightweight_columns() -> None:
    """Run the additive ALTERs above. Each is independent and forgiving -- one failure
    (e.g. table not created yet on a brand-new DB) must not block the others or boot."""
    for stmt in _ADDITIVE_COLUMNS:
        try:
            async with async_engine.begin() as conn:
                await conn.execute(text(stmt))
        except Exception as e:  # pragma: no cover - defensive, never block startup
            logger.warning(f"additive migration skipped ({stmt[:60]}...): {e}")

# ================================================================
# 🧹 CLEANUP
# ================================================================
async def close_async_engine() -> None:
    await async_engine.dispose()
    logger.info("Async engine disposed.")

# ================================================================
# 🧮 SYNC ENGINE (Celery, scripts)
# ================================================================
def create_sync_engine(url: str = settings.POSTGRES_SYNC_URI):
    logger.info("Initializing sync database engine...")
    return create_engine(url, echo=settings.DB_ECHO, pool_pre_ping=True)

@contextmanager
def get_db_session_sync() -> Iterator[Session]:
    global SyncSessionLocal
    if SyncSessionLocal is None:
        engine = create_sync_engine()
        SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()

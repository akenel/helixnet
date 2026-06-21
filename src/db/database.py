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
    # BYOH (2026-06-16): a node reports its probed capabilities (tools, ram, gpu) so
    # the Provider Console can show the no-surprises "what can this box run" window.
    "ALTER TABLE compute_nodes ADD COLUMN IF NOT EXISTS caps_json TEXT",
    # Feedback screenshots (2026-06-21): the POS 💬 widget can attach an auto-captured
    # screenshot (base64 data-URL) to a backlog item. Heavy text, deferred-loaded.
    "ALTER TABLE backlog_items ADD COLUMN IF NOT EXISTS screenshot_data TEXT",
]


# Idempotent DDL that must exist on EVERY env (the migration-not-gated lesson:
# this was only ever set up on local, so POS fuzzy search 500'd on staging/prod).
# CREATE EXTENSION / OR REPLACE FUNCTION are safe to re-run on a shared DB.
_DDL_MIGRATIONS: list[str] = [
    # Custom POS line items (manual catalog entry, product-as-change treats) carry no
    # product_id -- the name lives in notes and the price is sent by the till. Drop the
    # NOT NULL so they can be stored. Idempotent (no-op once already nullable).
    "ALTER TABLE line_items ALTER COLUMN product_id DROP NOT NULL",
    # Giveaway flag: a 'treat' is a real product given free (zero revenue) but it
    # leaves inventory -- flagged so reports/accounting can track COGS for tax.
    "ALTER TABLE line_items ADD COLUMN IF NOT EXISTS is_giveaway BOOLEAN NOT NULL DEFAULT FALSE",
    # Seed the Treats catalog so giveaways decrement real stock + carry a cost.
    # Idempotent (ON CONFLICT on the unique sku). gen_random_uuid() is built-in (PG13+).
    """
    INSERT INTO products (id, sku, name, description, price, cost, stock_quantity,
        stock_alert_threshold, category, is_active, is_age_restricted, vending_compatible,
        sync_override, created_at, updated_at)
    VALUES
      (gen_random_uuid(),'TREAT-LOLLIPOP','Lollipop','Treat / giveaway',0.50,0.10,200,20,'Treats',true,false,false,false,now(),now()),
      (gen_random_uuid(),'TREAT-STICKER','Sticker','Treat / giveaway',0.30,0.05,200,20,'Treats',true,false,false,false,now(),now()),
      (gen_random_uuid(),'TREAT-PAPERS','Rolling Papers','Treat / giveaway',0.60,0.15,200,20,'Treats',true,false,false,false,now(),now()),
      (gen_random_uuid(),'TREAT-GUMMY','CBD Gummy','Treat / giveaway',0.45,0.12,200,20,'Treats',true,false,false,false,now(),now()),
      (gen_random_uuid(),'TREAT-LIGHTER','Lighter','Treat / giveaway',1.50,0.40,200,20,'Treats',true,false,false,false,now(),now()),
      (gen_random_uuid(),'TREAT-GRINDERCARD','Grinder Card','Treat / giveaway',1.80,0.50,200,20,'Treats',true,false,false,false,now(),now())
    ON CONFLICT (sku) DO NOTHING
    """,
    # pg_trgm powers similarity() for the POS product search.
    "CREATE EXTENSION IF NOT EXISTS pg_trgm",
    # GIN trigram index keeps fuzzy/ILIKE name search fast on a big (thousands) catalog.
    "CREATE INDEX IF NOT EXISTS ix_products_name_trgm ON products USING gin (name gin_trgm_ops)",
    # Category list for the search filter (the /search/categories endpoint expects this
    # view; it was missing -> 500, same pattern as search_products).
    """
    CREATE OR REPLACE VIEW product_categories AS
    SELECT category, count(*) AS product_count, avg(price) AS avg_price
    FROM products
    WHERE is_active = true AND category IS NOT NULL AND category <> ''
    GROUP BY category
    """,
    # Fuzzy + substring product search used by GET /api/v1/pos/search.
    """
    CREATE OR REPLACE FUNCTION public.search_products(
        search_term text, category_filter text DEFAULT NULL::text, limit_rows integer DEFAULT 50)
     RETURNS TABLE(id uuid, sku character varying, barcode character varying, name character varying,
        category character varying, price numeric, stock_quantity integer, image_url character varying, relevance real)
     LANGUAGE plpgsql
    AS $function$
    BEGIN
        RETURN QUERY
        SELECT p.id, p.sku, p.barcode, p.name, p.category, p.price, p.stock_quantity, p.image_url,
            similarity(p.name, search_term) AS relevance
        FROM products p
        WHERE p.is_active = true
            AND (
                p.name ILIKE '%' || search_term || '%'
                OR p.sku ILIKE '%' || search_term || '%'
                OR p.barcode ILIKE '%' || search_term || '%'
                OR similarity(p.name, search_term) > 0.1
            )
            AND (category_filter IS NULL OR p.category ILIKE '%' || category_filter || '%')
        ORDER BY
            CASE WHEN p.name ILIKE search_term || '%' THEN 0 ELSE 1 END,
            similarity(p.name, search_term) DESC, p.name
        LIMIT limit_rows;
    END;
    $function$
    """,
]


async def _ensure_lightweight_columns() -> None:
    """Run the additive ALTERs above. Each is independent and forgiving -- one failure
    (e.g. table not created yet on a brand-new DB) must not block the others or boot."""
    for stmt in _ADDITIVE_COLUMNS + _DDL_MIGRATIONS:
        try:
            async with async_engine.begin() as conn:
                await conn.execute(text(stmt))
        except Exception as e:  # pragma: no cover - defensive, never block startup
            logger.warning(f"additive migration skipped ({stmt[:60].strip()}...): {e}")

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

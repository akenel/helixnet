import logging
import os
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
    # Feedback attachments (2026-06-21): the 💬 widget can now attach files (images
    # AND PDFs) chosen from the device or shot with the mobile camera, beyond the
    # single auto-captured screenshot. Stored as a JSON list. Heavy text, deferred.
    "ALTER TABLE backlog_items ADD COLUMN IF NOT EXISTS attachments TEXT",
    # CRM Phase 0 (2026-06-21): age gate + marketing consent on customers (the only
    # compliance must -- 18+; marketing default off per Swiss FADP).
    "ALTER TABLE customers ADD COLUMN IF NOT EXISTS age_confirmed BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE customers ADD COLUMN IF NOT EXISTS marketing_consent BOOLEAN NOT NULL DEFAULT FALSE",
    # BL-082 (2026-06-21): the IsottoOrder model grew team-order fields but there was
    # no additive migration -- create_all() never adds columns to an existing table, so
    # any env whose isotto_orders predated these 500'd on insert (seed crash + dead
    # ISOTTO order feature). These are the only two columns the model has that the live
    # table lacked (verified by diffing the model against information_schema).
    "ALTER TABLE isotto_orders ADD COLUMN IF NOT EXISTS is_team_order BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE isotto_orders ADD COLUMN IF NOT EXISTS team_name VARCHAR(200)",
    # BL-96 taxonomy (2026-06-25): product CLASS (behaviour — age/VAT/compliance) on products,
    # and the reclassify enricher's mapping on the reference catalogue (our skeleton category +
    # class + 18+ flag) so adopting a reference item carries category, class AND the age gate.
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS product_class VARCHAR(40) NOT NULL DEFAULT 'standard'",
    "ALTER TABLE reference_products ADD COLUMN IF NOT EXISTS our_category VARCHAR(60)",
    "ALTER TABLE reference_products ADD COLUMN IF NOT EXISTS our_class VARCHAR(40)",
    "ALTER TABLE reference_products ADD COLUMN IF NOT EXISTS age_restricted BOOLEAN NOT NULL DEFAULT FALSE",
    # Banco store profile (2026-06-22): hours + social links on store_settings.
    "ALTER TABLE store_settings ADD COLUMN IF NOT EXISTS opening_hours VARCHAR(500)",
    "ALTER TABLE store_settings ADD COLUMN IF NOT EXISTS facebook_url VARCHAR(255)",
    "ALTER TABLE store_settings ADD COLUMN IF NOT EXISTS instagram_url VARCHAR(255)",
    "ALTER TABLE store_settings ADD COLUMN IF NOT EXISTS founded_year VARCHAR(10)",
    # Offline outbox idempotency (P2.1, 2026-06-29): the atomic create-sale endpoint keys
    # on a client-generated UUID so a replayed sale (network retry / offline outbox sync)
    # is adopted exactly once, never double-rung. Nullable (legacy 3-step sales have none);
    # the index is UNIQUE among non-null values — Postgres counts NULLs as distinct, so the
    # backfill is a no-op and existing rows never collide. (Mirrors TransactionModel.client_uuid.)
    "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS client_uuid UUID",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_transactions_client_uuid ON transactions (client_uuid)",
    # Artemis enriched-catalog foundation (2026-06-30, migration 010): store the enriched
    # record losslessly on products + a per-language translations table (the latter is a
    # NEW table, created by create_all() — only the column adds need ALTERs here).
    # Flat hierarchy (group + category on the row; full path in tags + artemis_path) — §9.1.
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS product_group VARCHAR(60)",
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS age_reason VARCHAR(80)",
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS barcode_is_internal BOOLEAN NOT NULL DEFAULT FALSE",
    # §6a rich metadata + verbatim source facets (lossless), and enrichment provenance.
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS attributes JSONB",
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS raw_facets JSONB",
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS enrichment_confidence JSONB",
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS enrichment_flags JSONB",
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS enrichment_meta JSONB",
    # Source provenance / parity link (§9.6 'View on Artemis') + §6d translation seam.
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS source_system VARCHAR(40)",
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS source_id VARCHAR(64)",
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS source_url VARCHAR(500)",
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS source_lang VARCHAR(8)",
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS artemis_path VARCHAR(255)",
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS needs_translation BOOLEAN NOT NULL DEFAULT FALSE",
    # §6c SHARE rail permalink (QR target).
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS qr_url VARCHAR(500)",
    "CREATE INDEX IF NOT EXISTS ix_products_product_group ON products (product_group)",
    "CREATE INDEX IF NOT EXISTS ix_products_source_id ON products (source_id)",
    # Supplier Registry (2026-06-30, migration 011): formalize each import SOURCE as a
    # supplier row keyed by a unique SKU prefix (TAM-=Tamar/Artemis, FTW-=FourTwenty,
    # future CSV/manual). The `suppliers` table already exists (legacy Sourcing System,
    # created by create_all) — these are the additive registry columns. Prefix is the
    # authoritative key: 2-3 uppercase letters, UNIQUE (the index below backstops the
    # Pydantic validator), nullable so legacy rows (420/WR/ND/Hem) carry none.
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS prefix VARCHAR(3)",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS source_url VARCHAR(500)",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS adapter_type VARCHAR(40)",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS contact_name VARCHAR(120)",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS contact_email VARCHAR(255)",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(50)",
    # Succession/handoff: VAT + named contact so the supplier isn't trapped in one head.
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS vat_number VARCHAR(50)",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_suppliers_prefix ON suppliers (prefix)",
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
    # (The Treats catalog INSERT moved to _DEMO_DDL below -- it is demo *content*,
    #  gated by HX_SEED_DEMO so the Banco Day-One sandbox boots with an empty shop.)
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
    # CRM Phase 0 (2026-06-21): the transactions.customer_id FK was pointing at users.id
    # (staff) -- WRONG; a loyalty sale belongs to a CRM customer. Repoint it to
    # customers.id. Idempotent: only acts if the correct FK isn't already present, so it
    # drops whatever wrong FK is on customer_id and adds the right one exactly once.
    """
    DO $$
    DECLARE badcon text; has_good boolean;
    BEGIN
        SELECT EXISTS (
            SELECT 1 FROM pg_constraint con
            JOIN pg_class fr ON fr.oid = con.confrelid
            JOIN pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = ANY(con.conkey)
            WHERE con.conrelid = 'transactions'::regclass AND con.contype = 'f'
              AND a.attname = 'customer_id' AND fr.relname = 'customers'
        ) INTO has_good;
        IF NOT has_good THEN
            SELECT con.conname INTO badcon
            FROM pg_constraint con
            JOIN pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = ANY(con.conkey)
            WHERE con.conrelid = 'transactions'::regclass AND con.contype = 'f'
              AND a.attname = 'customer_id' LIMIT 1;
            IF badcon IS NOT NULL THEN
                EXECUTE format('ALTER TABLE transactions DROP CONSTRAINT %I', badcon);
            END IF;
            ALTER TABLE transactions
                ADD CONSTRAINT transactions_customer_id_customers_fkey
                FOREIGN KEY (customer_id) REFERENCES customers(id);
        END IF;
    END $$;
    """,
    # BL-84 (2026-06-21): Felix asked for a bank-transfer payment type (invoice/IBAN
    # paid into the shop account). payment_method is a native PG enum whose labels are
    # the Python enum NAMES (CASH, VISA, ...), so the new label is 'BANK_TRANSFER'.
    # ADD VALUE IF NOT EXISTS is idempotent; PG 12+ allows it inside a transaction.
    "ALTER TYPE paymentmethod ADD VALUE IF NOT EXISTS 'BANK_TRANSFER'",
    # Supplier Registry seed (migration 011): the two known import sources. This is
    # FOUNDATION config (not demo content), so it lives here in the always-run block —
    # banco runs HX_SEED_DEMO=false, so _DEMO_DDL would skip it. Idempotent on the
    # unique prefix. `code` is the legacy NOT NULL unique column — mirror the prefix.
    # LZ stays a RESERVED internal code (not a row); the receiving 'LZ-' lazy-create
    # path already covers internal/manual items.
    """
    INSERT INTO suppliers (id, code, prefix, name, source_url, adapter_type, country,
        lead_time_days_min, lead_time_days_max, quality_rating, swiss_certified,
        is_active, created_at, updated_at)
    VALUES
      (gen_random_uuid()::text,'TAM','TAM','Tamar Trade GmbH','https://www.artemisluzern.ch','tamar','CH',1,5,'A',true,true,now(),now()),
      (gen_random_uuid()::text,'FTW','FTW','FourTwenty','https://fourtwenty.ch','magento','CH',1,5,'A',false,true,now(),now())
    ON CONFLICT (prefix) DO NOTHING
    """,
]


# Demo *content* DDL -- skipped when HX_SEED_DEMO=false (the Banco Day-One sandbox),
# so the shop boots empty. Everything in _DDL_MIGRATIONS above is schema/infra and
# always runs; only seed rows live here.
_DEMO_DDL: list[str] = [
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
]


async def _ensure_lightweight_columns() -> None:
    """Run the additive ALTERs above. Each is independent and forgiving -- one failure
    (e.g. table not created yet on a brand-new DB) must not block the others or boot."""
    seed_demo = os.getenv("HX_SEED_DEMO", "true").strip().lower() not in ("false", "0", "no")
    statements = _ADDITIVE_COLUMNS + _DDL_MIGRATIONS + (_DEMO_DDL if seed_demo else [])
    for stmt in statements:
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

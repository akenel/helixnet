"""Supplier Registry — formalize import SOURCES on the suppliers table

Revision ID: 011_add_suppliers
Revises: 010_artemis_enrich
Create Date: 2026-06-30

Foundation for multi-source import + P2P/receiving. Each supplier = an import
source identified by a unique SKU prefix (TAM-=Tamar/Artemis, FTW-=FourTwenty,
future CSV/manual). The `suppliers` table already exists (legacy Sourcing System,
created by create_all) — this migration adds the registry columns:

  suppliers (new columns):
    - prefix          SKU prefix, 2-3 uppercase letters, UNIQUE (the registry key;
                      ^[A-Z]{2,3}$, never reserved ART/LZ — enforced in the Pydantic
                      validator + this unique index). Nullable: legacy rows carry none.
    - source_url      web origin for sync / "View on source"
    - adapter_type    import adapter: 'tamar' | 'magento' | 'csv' | 'manual'
    - contact_email   primary contact email
    - contact_phone   primary contact phone

NOTE on the operative path: this repo applies additive columns at startup via
`database._ADDITIVE_COLUMNS` (and seeds TAM/FTW idempotently in `_DDL_MIGRATIONS`).
This file is the formal alembic record; the same ALTERs live there (the
create_all↔alembic drift lesson). Reversible downgrade below.
"""
from alembic import op
import sqlalchemy as sa

revision = '011_add_suppliers'
down_revision = '010_artemis_enrich'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('suppliers', sa.Column('prefix', sa.String(length=3), nullable=True))
    op.add_column('suppliers', sa.Column('source_url', sa.String(length=500), nullable=True))
    op.add_column('suppliers', sa.Column('adapter_type', sa.String(length=40), nullable=True))
    op.add_column('suppliers', sa.Column('contact_email', sa.String(length=255), nullable=True))
    op.add_column('suppliers', sa.Column('contact_phone', sa.String(length=50), nullable=True))
    op.create_index('ix_suppliers_prefix', 'suppliers', ['prefix'], unique=True)

    # Seed the two known import sources (idempotent). `code` is the legacy NOT NULL
    # unique column — mirror the prefix. LZ stays a reserved internal code (no row).
    op.execute(
        """
        INSERT INTO suppliers (id, code, prefix, name, source_url, adapter_type, country,
            lead_time_days_min, lead_time_days_max, quality_rating, swiss_certified,
            is_active, created_at, updated_at)
        VALUES
          (gen_random_uuid()::text,'TAM','TAM','Tamar Trade GmbH','https://www.artemisluzern.ch','tamar','CH',1,5,'A',true,true,now(),now()),
          (gen_random_uuid()::text,'FTW','FTW','FourTwenty','https://fourtwenty.ch','magento','CH',1,5,'A',false,true,now(),now())
        ON CONFLICT (prefix) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM suppliers WHERE prefix IN ('TAM', 'FTW')")
    op.drop_index('ix_suppliers_prefix', table_name='suppliers')
    for col in ('contact_phone', 'contact_email', 'adapter_type', 'source_url', 'prefix'):
        op.drop_column('suppliers', col)

"""Add the reference catalog (product master) — BL-97

Revision ID: 007_reference_catalog
Revises: 006_lapiazza_bridge
Create Date: 2026-06-24

A supplier-fed, lookup-only product master (the full 420/TMR dump). The POS searches it
but never sells from it; a cashier "adopts" a row into the live `products` catalog, copying
the real title/description/photo in. Read-mostly, written only by the CSV importer.

Shipped as a real migration (not via create_all) per the create_all↔alembic drift note —
verify it lands on staging/prod. Needs the pg_trgm extension (already used by products search).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '007_reference_catalog'
down_revision = '006_lapiazza_bridge'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        'reference_products',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('supplier', sa.String(length=100), nullable=False),
        sa.Column('ref_key', sa.String(length=150), nullable=False),
        sa.Column('supplier_sku', sa.String(length=100), nullable=True),
        sa.Column('barcode', sa.String(length=100), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('suggested_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('cost', sa.Numeric(10, 2), nullable=True),
        sa.Column('raw', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('imported_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('supplier', 'ref_key', name='uq_reference_products_supplier_refkey'),
    )
    op.create_index('ix_reference_products_supplier', 'reference_products', ['supplier'])
    op.create_index('ix_reference_products_barcode', 'reference_products', ['barcode'])
    op.create_index(
        'ix_reference_products_title_trgm', 'reference_products', ['title'],
        postgresql_using='gin', postgresql_ops={'title': 'gin_trgm_ops'},
    )


def downgrade() -> None:
    op.drop_index('ix_reference_products_title_trgm', table_name='reference_products')
    op.drop_index('ix_reference_products_barcode', table_name='reference_products')
    op.drop_index('ix_reference_products_supplier', table_name='reference_products')
    op.drop_table('reference_products')

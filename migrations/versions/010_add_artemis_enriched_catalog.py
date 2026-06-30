"""Artemis enriched-catalog foundation — lossless enrichment on products + i18n skins

Revision ID: 010_artemis_enrich
Revises: 009_txn_client_uuid
Create Date: 2026-06-30

Stores the enriched Artemis catalog record (docs/BANCO-ARTEMIS-ENRICHMENT-RECIPE.md)
losslessly so the full load + multilingual + rich metadata are unblocked:

  products (new columns):
    - product_group           flat lvl-1 group (§9.1 — category stays flat; path in tags)
    - age_reason              auditable LAW-axis trail: the rule that set the 18+ gate (§3)
    - barcode_is_internal     True when `barcode` is an EAN-13 we minted (no source EAN, §6b)
    - attributes (JSONB)      §6a normalized rich-metadata bag (brand/material/size/...)
    - raw_facets (JSONB)      verbatim source spec facets (lossless)
    - enrichment_confidence   per-axis confidence {category, class, description}
    - enrichment_flags        review flags list
    - enrichment_meta         enrichment provenance {model, recipe_version, run_id}
    - source_system/id/url/lang   feeder provenance + "View on Artemis" parity link (§9.6)
    - artemis_path            full source breadcrumb verbatim (recovers the deep tree later)
    - needs_translation       text missing a language skin -> LLM layer fills it
    - qr_url                  Banco-owned SHARE permalink (QR target, §6c)

  product_translations (new table, §6d):
    one (product_id, lang) text "skin" — name/description per language + provenance
    (source vs machine) + needs_review. EN primary; DE/FR/IT fall back to EN.

NOTE on the operative path: this repo applies additive columns at startup via
`database._ADDITIVE_COLUMNS`, and create_all() creates the NEW product_translations
table on boot. This file is the formal record; the same column ALTERs live in
_ADDITIVE_COLUMNS (the create_all↔alembic drift lesson). Reversible downgrade below.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '010_artemis_enrich'
down_revision = '009_txn_client_uuid'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- products: enriched-record columns (additive, nullable / safe defaults) ---
    op.add_column('products', sa.Column('product_group', sa.String(length=60), nullable=True))
    op.add_column('products', sa.Column('age_reason', sa.String(length=80), nullable=True))
    op.add_column('products', sa.Column('barcode_is_internal', sa.Boolean(),
                                        nullable=False, server_default=sa.false()))
    op.add_column('products', sa.Column('attributes', JSONB(), nullable=True))
    op.add_column('products', sa.Column('raw_facets', JSONB(), nullable=True))
    op.add_column('products', sa.Column('enrichment_confidence', JSONB(), nullable=True))
    op.add_column('products', sa.Column('enrichment_flags', JSONB(), nullable=True))
    op.add_column('products', sa.Column('enrichment_meta', JSONB(), nullable=True))
    op.add_column('products', sa.Column('source_system', sa.String(length=40), nullable=True))
    op.add_column('products', sa.Column('source_id', sa.String(length=64), nullable=True))
    op.add_column('products', sa.Column('source_url', sa.String(length=500), nullable=True))
    op.add_column('products', sa.Column('source_lang', sa.String(length=8), nullable=True))
    op.add_column('products', sa.Column('artemis_path', sa.String(length=255), nullable=True))
    op.add_column('products', sa.Column('needs_translation', sa.Boolean(),
                                        nullable=False, server_default=sa.false()))
    op.add_column('products', sa.Column('qr_url', sa.String(length=500), nullable=True))
    op.create_index('ix_products_product_group', 'products', ['product_group'])
    op.create_index('ix_products_source_id', 'products', ['source_id'])

    # --- product_translations: per-language text skin (§6d) ---
    op.create_table(
        'product_translations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('product_id', UUID(as_uuid=True),
                  sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('lang', sa.String(length=8), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('provenance', sa.String(length=16), nullable=False, server_default='source'),
        sa.Column('needs_review', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.UniqueConstraint('product_id', 'lang', name='uq_product_translations_product_lang'),
    )
    op.create_index('ix_product_translations_product_id', 'product_translations', ['product_id'])


def downgrade() -> None:
    op.drop_index('ix_product_translations_product_id', table_name='product_translations')
    op.drop_table('product_translations')

    op.drop_index('ix_products_source_id', table_name='products')
    op.drop_index('ix_products_product_group', table_name='products')
    for col in ('qr_url', 'needs_translation', 'artemis_path', 'source_lang', 'source_url',
                'source_id', 'source_system', 'enrichment_meta', 'enrichment_flags',
                'enrichment_confidence', 'raw_facets', 'attributes', 'barcode_is_internal',
                'age_reason', 'product_group'):
        op.drop_column('products', col)

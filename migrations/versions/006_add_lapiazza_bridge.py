"""Add La Piazza bridge fields (Artemis Premium cutover -- Phase 0)

Revision ID: 006_lapiazza_bridge
Revises: 005_add_application
Create Date: 2026-06-24

Wiring for publishing a Banco product into the La Piazza marketplace as a draft listing
under the shop's own business account. Push-once-then-decouple: we record the listing
id/slug + push time on the product, and a per-shop module switch on store_settings.
All additive + nullable/defaulted -- a no-op until a shop flips the switch.
"""
from alembic import op
import sqlalchemy as sa

revision = '006_lapiazza_bridge'
down_revision = '005_add_application'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # store_settings: the per-shop "La Piazza module" switch + linked business account
    op.add_column('store_settings', sa.Column('lapiazza_enabled', sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column('store_settings', sa.Column('lapiazza_autodraft', sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column('store_settings', sa.Column('lapiazza_business_id', sa.String(length=64), nullable=True))

    # products: the one-shot push record (listing id/slug + when it was seeded)
    op.add_column('products', sa.Column('lapiazza_listing_id', sa.String(length=64), nullable=True))
    op.add_column('products', sa.Column('lapiazza_slug', sa.String(length=255), nullable=True))
    op.add_column('products', sa.Column('lapiazza_pushed_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('products', 'lapiazza_pushed_at')
    op.drop_column('products', 'lapiazza_slug')
    op.drop_column('products', 'lapiazza_listing_id')
    op.drop_column('store_settings', 'lapiazza_business_id')
    op.drop_column('store_settings', 'lapiazza_autodraft')
    op.drop_column('store_settings', 'lapiazza_enabled')

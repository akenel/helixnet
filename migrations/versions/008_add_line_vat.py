"""Add per-line Swiss VAT to line_items — cafe multi-line tax (INC2)

Revision ID: 008_line_vat
Revises: 007_reference_catalog
Create Date: 2026-06-26

The cafe split (dine-in 8.1% / takeaway 2.6%) needs the rate decided and recorded PER LINE,
not once per sale. This adds three columns to `line_items`:
  - consumption  : dine_in | takeaway — the cashier's choice, drives the rate (NOT NULL,
                   server_default 'dine_in' so existing rows backfill to the safe default)
  - vat_rate     : the rate % snapshotted at sale time (8.10 / 2.60); nullable on legacy lines
  - vat_amount   : the VAT contained in the line's gross at that rate; nullable on legacy lines

The rate/amount are frozen at sale time (resolved via vat_resolver.line_vat) so a later rate
change never rewrites a past receipt. Additive + back-compat: old lines get consumption
'dine_in' and null rate/amount.

Shipped as a real migration (not via create_all) per the create_all↔alembic drift note —
verify it lands on staging/prod.
"""
from alembic import op
import sqlalchemy as sa

revision = '008_line_vat'
down_revision = '007_reference_catalog'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('line_items', sa.Column(
        'consumption', sa.String(length=16), nullable=False, server_default='dine_in'))
    op.add_column('line_items', sa.Column('vat_rate', sa.Numeric(4, 2), nullable=True))
    op.add_column('line_items', sa.Column('vat_amount', sa.Numeric(10, 2), nullable=True))


def downgrade() -> None:
    op.drop_column('line_items', 'vat_amount')
    op.drop_column('line_items', 'vat_rate')
    op.drop_column('line_items', 'consumption')

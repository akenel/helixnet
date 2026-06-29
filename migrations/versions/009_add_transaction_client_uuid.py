"""Add client_uuid idempotency key to transactions — offline outbox / atomic sale (P2.1)

Revision ID: 009_txn_client_uuid
Revises: 008_line_vat
Create Date: 2026-06-29

The atomic create-sale endpoint (one request = whole cart + payment) keys on a
client-generated UUID so a replayed sale — a network retry, or an offline outbox
draining on reconnect — is adopted EXACTLY ONCE instead of double-ringing. This adds
one column to `transactions`:
  - client_uuid : UUID, nullable (legacy 3-step sales have none), UNIQUE among non-null
                  values. Postgres treats NULLs as distinct, so the unique index is a
                  no-op on the existing backfill and old rows never collide.

NOTE on the operative path: this repo applies additive columns at startup via
`database._ADDITIVE_COLUMNS` (create_all never ALTERs an existing table, and the alembic
chain isn't auto-run) — the same ALTER + unique index live there too, which is what
actually runs on each env. This file is the formal record; the per-env proof is a
`information_schema` check after deploy (the create_all↔alembic drift lesson).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '009_txn_client_uuid'
down_revision = '008_line_vat'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('transactions', sa.Column('client_uuid', UUID(as_uuid=True), nullable=True))
    op.create_index('ix_transactions_client_uuid', 'transactions', ['client_uuid'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_transactions_client_uuid', table_name='transactions')
    op.drop_column('transactions', 'client_uuid')

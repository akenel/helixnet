"""Add application field to backlog_items and qa_bug_reports

Revision ID: 005_add_application
Revises: 004_helix_studio
Create Date: 2026-02-25

Multi-app tracker -- one backlog, one bug tracker for HelixNet, Camper, ISOTTO.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM

revision = '005_add_application'
down_revision = '004_helix_studio'
branch_labels = None
depends_on = None

helix_application = ENUM('helixnet', 'camper', 'isotto', name='helix_application', create_type=False)


def upgrade() -> None:
    # Create the PostgreSQL enum type first
    op.execute("CREATE TYPE helix_application AS ENUM ('helixnet', 'camper', 'isotto')")

    op.add_column('backlog_items', sa.Column('application', helix_application, server_default='helixnet', nullable=False))
    op.create_index('ix_backlog_items_application', 'backlog_items', ['application'])

    op.add_column('qa_bug_reports', sa.Column('application', helix_application, server_default='helixnet', nullable=False))
    op.create_index('ix_qa_bug_reports_application', 'qa_bug_reports', ['application'])


def downgrade() -> None:
    op.drop_index('ix_qa_bug_reports_application', table_name='qa_bug_reports')
    op.drop_column('qa_bug_reports', 'application')
    op.drop_index('ix_backlog_items_application', table_name='backlog_items')
    op.drop_column('backlog_items', 'application')
    op.execute("DROP TYPE IF EXISTS helix_application")

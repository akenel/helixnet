"""Add jobs table (Initial Migration)

Revision ID: 7abf5101b458
Revises: None
Create Date: 2025-10-09 01:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7abf5101b458'
# This is the first migration, so down_revision is None
down_revision = None 
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands manually generated based on Alembic's detection ###
    op.create_table('jobs',
    sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
    sa.Column('celery_task_id', sa.String(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('job_type', sa.String(), nullable=False),
    sa.Column('parameters', postgresql.JSONB(), nullable=False),
    sa.UniqueConstraint('celery_task_id', name=op.f('uq_jobs_celery_task_id'))
    )

    # Indexes detected by Alembic:
    op.create_index(op.f('ix_jobs_user_id'), 'jobs', ['user_id'], unique=False)
    op.create_index(op.f('ix_jobs_status'), 'jobs', ['status'], unique=False)
    # ### end commands ###


def downgrade() -> None:
    # ### commands manually generated ###
    op.drop_table('jobs')
    # ### end commands ###

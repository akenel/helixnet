"""Add HELIX STUDIO tables (series, episodes, scenes, publish records)

Revision ID: 004_helix_studio
Revises: 003_add_spine_and_equipment
Create Date: 2025-12-15

PREP PREP PREP — The Media Empire Database
664 episodes planned. Tables ready.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '004_helix_studio'
down_revision = '003_add_spine_and_equipment'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    op.execute("""
        CREATE TYPE episodestatus AS ENUM (
            'idea', 'outlined', 'scripted', 'cast_ready',
            'recording', 'recorded', 'editing', 'review',
            'published', 'legendary'
        )
    """)

    op.execute("""
        CREATE TYPE episodecategory AS ENUM (
            'hells_sap_kitchen', 'tiger_tales', 'salad_bar_sessions',
            'space_odyssey', 'field_notes', 'crack_spotlight',
            'tech_tiggles', 'lost_souls', 'founders_corner'
        )
    """)

    op.execute("""
        CREATE TYPE platform AS ENUM (
            'bitchute', 'rumble', 'odysee', 'archive_org', 'helix_self'
        )
    """)

    # Create studio_series table
    op.create_table(
        'studio_series',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('code', sa.String(20), unique=True, index=True, nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('category', sa.Enum('hells_sap_kitchen', 'tiger_tales', 'salad_bar_sessions',
                                       'space_odyssey', 'field_notes', 'crack_spotlight',
                                       'tech_tiggles', 'lost_souls', 'founders_corner',
                                       name='episodecategory'), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('planned_seasons', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('episodes_per_season', sa.Integer(), nullable=False, server_default='12'),
        sa.Column('tone', sa.String(100), nullable=False, server_default='comedy'),
        sa.Column('aesthetic', sa.String(100), nullable=False, server_default='looney_tunes'),
        sa.Column('showrunner', sa.String(100), nullable=True),
        sa.Column('regular_cast', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('ix_studio_series_id', 'studio_series', ['id'])
    op.create_index('ix_studio_series_code', 'studio_series', ['code'])

    # Create studio_episodes table
    op.create_table(
        'studio_episodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('episode_code', sa.String(20), unique=True, index=True, nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('subtitle', sa.String(300), nullable=True),
        sa.Column('series_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('studio_series.id', ondelete='SET NULL'), nullable=True),
        sa.Column('category', sa.Enum('hells_sap_kitchen', 'tiger_tales', 'salad_bar_sessions',
                                       'space_odyssey', 'field_notes', 'crack_spotlight',
                                       'tech_tiggles', 'lost_souls', 'founders_corner',
                                       name='episodecategory'), nullable=False, index=True),
        sa.Column('season', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('episode_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('idea', 'outlined', 'scripted', 'cast_ready',
                                     'recording', 'recorded', 'editing', 'review',
                                     'published', 'legendary', name='episodestatus'),
                  nullable=False, server_default='idea', index=True),
        sa.Column('logline', sa.String(500), nullable=False),
        sa.Column('synopsis', sa.Text(), nullable=True),
        sa.Column('primary_cast', postgresql.JSONB(), nullable=True),
        sa.Column('guest_cast', postgresql.JSONB(), nullable=True),
        sa.Column('narrator', sa.String(100), nullable=True),
        sa.Column('writer', sa.String(100), nullable=True),
        sa.Column('director', sa.String(100), nullable=True),
        sa.Column('editor', sa.String(100), nullable=True),
        sa.Column('target_duration_minutes', sa.Integer(), nullable=False, server_default='15'),
        sa.Column('actual_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('target_record_date', sa.Date(), nullable=True),
        sa.Column('target_publish_date', sa.Date(), nullable=True),
        sa.Column('actual_publish_date', sa.Date(), nullable=True),
        sa.Column('bitchute_url', sa.Text(), nullable=True),
        sa.Column('backup_urls', postgresql.JSONB(), nullable=True),
        sa.Column('tags', postgresql.JSONB(), nullable=True),
        sa.Column('related_kbs', postgresql.JSONB(), nullable=True),
        sa.Column('related_episodes', postgresql.JSONB(), nullable=True),
        sa.Column('production_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('ix_studio_episodes_id', 'studio_episodes', ['id'])
    op.create_index('ix_studio_episodes_code', 'studio_episodes', ['episode_code'])
    op.create_index('ix_studio_episodes_series', 'studio_episodes', ['series_id'])

    # Create studio_scenes table
    op.create_table(
        'studio_scenes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('episode_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('studio_episodes.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('scene_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('location', sa.String(200), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('characters', postgresql.JSONB(), nullable=True),
        sa.Column('dialogue_notes', sa.Text(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('kb_reference', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('ix_studio_scenes_id', 'studio_scenes', ['id'])
    op.create_index('ix_studio_scenes_episode', 'studio_scenes', ['episode_id'])

    # Create studio_publish_records table
    op.create_table(
        'studio_publish_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('episode_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('studio_episodes.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('platform', sa.Enum('bitchute', 'rumble', 'odysee', 'archive_org', 'helix_self',
                                       name='platform'), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('views', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('likes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('comments', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('stats_updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_studio_publish_id', 'studio_publish_records', ['id'])
    op.create_index('ix_studio_publish_episode', 'studio_publish_records', ['episode_id'])


def downgrade() -> None:
    op.drop_index('ix_studio_publish_episode', 'studio_publish_records')
    op.drop_index('ix_studio_publish_id', 'studio_publish_records')
    op.drop_table('studio_publish_records')

    op.drop_index('ix_studio_scenes_episode', 'studio_scenes')
    op.drop_index('ix_studio_scenes_id', 'studio_scenes')
    op.drop_table('studio_scenes')

    op.drop_index('ix_studio_episodes_series', 'studio_episodes')
    op.drop_index('ix_studio_episodes_code', 'studio_episodes')
    op.drop_index('ix_studio_episodes_id', 'studio_episodes')
    op.drop_table('studio_episodes')

    op.drop_index('ix_studio_series_code', 'studio_series')
    op.drop_index('ix_studio_series_id', 'studio_series')
    op.drop_table('studio_series')

    op.execute('DROP TYPE IF EXISTS platform')
    op.execute('DROP TYPE IF EXISTS episodestatus')
    op.execute('DROP TYPE IF EXISTS episodecategory')

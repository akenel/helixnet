# File: src/db/models/helix_studio_model.py
"""
HELIX STUDIO — Database Models

PREP PREP PREP.
Ready to GO when it's GO TIME.

"The best time to plant a tree was 20 years ago.
 The second best time is now.
 The third best time is to have the schema ready."
"""
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
import uuid
from datetime import datetime, timezone, date
from enum import Enum
from sqlalchemy import String, DateTime, Integer, Boolean, Text, Date, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .base import Base


# ================================================================
# ENUMS — The Categories
# ================================================================
class EpisodeStatus(str, Enum):
    """Pipeline status — from spark to legend"""
    IDEA = "idea"
    OUTLINED = "outlined"
    SCRIPTED = "scripted"
    CAST_READY = "cast_ready"
    RECORDING = "recording"
    RECORDED = "recorded"
    EDITING = "editing"
    REVIEW = "review"
    PUBLISHED = "published"
    LEGENDARY = "legendary"


class EpisodeCategory(str, Enum):
    """Which series does this belong to?"""
    HELLS_SAP_KITCHEN = "hells_sap_kitchen"
    TIGER_TALES = "tiger_tales"
    SALAD_BAR_SESSIONS = "salad_bar_sessions"
    SPACE_ODYSSEY = "space_odyssey"
    FIELD_NOTES = "field_notes"
    CRACK_SPOTLIGHT = "crack_spotlight"
    TECH_TIGGLES = "tech_tiggles"
    LOST_SOULS = "lost_souls"
    FOUNDERS_CORNER = "founders_corner"


class Platform(str, Enum):
    """Where does content go? BitChute FIRST."""
    BITCHUTE = "bitchute"
    RUMBLE = "rumble"
    ODYSEE = "odysee"
    ARCHIVE_ORG = "archive_org"
    HELIX_SELF = "helix_self"


# ================================================================
# SERIES MODEL — The Container
# ================================================================
class SeriesModel(Base):
    """
    A series is a collection of episodes.
    Hell's SAP Kitchen, Tiger Tales, etc.
    """
    __tablename__ = 'studio_series'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Identity
    code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=False,
        comment="Series code (HK, TT, SS, etc.)"
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Series name"
    )
    category: Mapped[EpisodeCategory] = mapped_column(
        SQLEnum(EpisodeCategory),
        nullable=False,
        comment="Primary category"
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="What's this series about?"
    )

    # Planning
    planned_seasons: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="How many seasons planned"
    )
    episodes_per_season: Mapped[int] = mapped_column(
        Integer,
        default=12,
        nullable=False,
        comment="Target episodes per season"
    )

    # Style
    tone: Mapped[str] = mapped_column(
        String(100),
        default="comedy",
        nullable=False,
        comment="Overall tone"
    )
    aesthetic: Mapped[str] = mapped_column(
        String(100),
        default="looney_tunes",
        nullable=False,
        comment="Visual/audio style"
    )

    # Team
    showrunner: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Who runs this series?"
    )
    regular_cast: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Recurring cast members (handles)"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Is this series active?"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    episodes: Mapped[list["EpisodeModel"]] = relationship(
        back_populates="series",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Series({self.code}: {self.name})>"


# ================================================================
# EPISODE MODEL — The Main Unit
# ================================================================
class EpisodeModel(Base):
    """
    An episode is the atomic unit of content.
    From IDEA to LEGENDARY.
    """
    __tablename__ = 'studio_episodes'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Identity
    episode_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=False,
        comment="Unique code (HK-001, TT-042, etc.)"
    )
    title: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        comment="Episode title"
    )
    subtitle: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
        comment="Episode subtitle"
    )

    # Series Link
    series_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("studio_series.id", ondelete="SET NULL"),
        nullable=True,
        comment="Parent series (optional)"
    )

    # Classification
    category: Mapped[EpisodeCategory] = mapped_column(
        SQLEnum(EpisodeCategory),
        nullable=False,
        index=True,
        comment="Episode category"
    )
    season: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Season number"
    )
    episode_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Episode number in season"
    )

    # Status — THE PIPELINE
    status: Mapped[EpisodeStatus] = mapped_column(
        SQLEnum(EpisodeStatus),
        default=EpisodeStatus.IDEA,
        index=True,
        nullable=False,
        comment="Pipeline status"
    )

    # Content
    logline: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="One-line hook"
    )
    synopsis: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Full description"
    )

    # Cast (stored as JSON arrays of handles)
    primary_cast: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Main characters"
    )
    guest_cast: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Guest appearances"
    )
    narrator: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Narrator (if any)"
    )

    # Production Team
    writer: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Writer"
    )
    director: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Director"
    )
    editor: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Editor"
    )

    # Duration
    target_duration_minutes: Mapped[int] = mapped_column(
        Integer,
        default=15,
        nullable=False,
        comment="Target runtime"
    )
    actual_duration_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Actual runtime"
    )

    # Schedule
    target_record_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="When to record"
    )
    target_publish_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="When to publish"
    )
    actual_publish_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="When actually published"
    )

    # Platform Links
    bitchute_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="BitChute link (PRIMARY)"
    )
    backup_urls: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Backup platform links"
    )

    # Metadata
    tags: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Searchable tags"
    )
    related_kbs: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Related KB article IDs"
    )
    related_episodes: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Related episode codes"
    )

    # Notes
    production_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Internal notes"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    series: Mapped["SeriesModel"] = relationship(
        back_populates="episodes"
    )
    scenes: Mapped[list["SceneModel"]] = relationship(
        back_populates="episode",
        cascade="all, delete-orphan",
        order_by="SceneModel.scene_number"
    )

    @property
    def is_published(self) -> bool:
        return self.status in [EpisodeStatus.PUBLISHED, EpisodeStatus.LEGENDARY]

    @property
    def full_code(self) -> str:
        return f"S{self.season:02d}E{self.episode_number:02d}"

    def __repr__(self):
        return f"<Episode({self.episode_code}: {self.title} [{self.status.value}])>"


# ================================================================
# SCENE MODEL — The Building Blocks
# ================================================================
class SceneModel(Base):
    """
    A scene within an episode.
    Optional detail layer — episodes can exist without scenes.
    """
    __tablename__ = 'studio_scenes'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Episode Link
    episode_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("studio_episodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Identity
    scene_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Scene order (1, 2, 3...)"
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Scene title"
    )

    # Content
    location: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Where does this happen?"
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="What happens?"
    )
    characters: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Who's in this scene?"
    )
    dialogue_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Key dialogue or beats"
    )

    # Technical
    duration_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Estimated duration"
    )

    # Links
    kb_reference: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Related KB article"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    episode: Mapped["EpisodeModel"] = relationship(
        back_populates="scenes"
    )

    def __repr__(self):
        return f"<Scene({self.scene_number}: {self.title})>"


# ================================================================
# PLATFORM PUBLISH MODEL — Track where content lives
# ================================================================
class PublishRecordModel(Base):
    """
    Track where an episode is published.
    BitChute first, then backups.
    """
    __tablename__ = 'studio_publish_records'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    episode_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("studio_episodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    platform: Mapped[Platform] = mapped_column(
        SQLEnum(Platform),
        nullable=False,
        comment="Which platform?"
    )
    url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Direct link"
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Stats (updated periodically)
    views: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    likes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    comments: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    stats_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    def __repr__(self):
        return f"<Publish({self.platform.value}: {self.url[:30]}...)>"

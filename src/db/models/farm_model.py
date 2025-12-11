# File: src/db/models/farm_model.py
"""
FarmModel - Molly's Farm and the network of farms.
Where salads begin. Where goats get milked. Where the sun comes up at 4AM.

"Oh what a beautiful day!" - Molly
"""
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Boolean, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base


class FarmType(str, enum.Enum):
    """What kind of farm?"""
    DAIRY = "dairy"
    VEGETABLE = "vegetable"
    FRUIT = "fruit"
    MIXED = "mixed"
    HONEY = "honey"
    HERB = "herb"


class FarmModel(Base):
    """
    A farm in the Helix network.
    Molly's farm is the prototype - goats, bees, garden, brothers.
    """
    __tablename__ = 'farms'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Identity
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Farm name (e.g., Molly's Mountain Farm)"
    )
    code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=False,
        comment="Short code (e.g., MOLLY, SWISS-ALP-01)"
    )
    farm_type: Mapped[FarmType] = mapped_column(
        SQLEnum(FarmType),
        default=FarmType.MIXED,
        nullable=False
    )

    # Location
    address: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True
    )
    region: Mapped[str] = mapped_column(
        String(100),
        default="Swiss Alps",
        nullable=False
    )
    coordinates: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="GPS coordinates"
    )

    # Owner/Contact
    owner_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Farm owner (e.g., Molly)"
    )
    owner_phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True
    )
    owner_email: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )

    # The People
    has_family_workers: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Family farm with brothers/sisters helping"
    )
    worker_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False
    )

    # Animals (Molly's specialties)
    has_goats: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Goat milk, cheese"
    )
    goat_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    has_bees: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Honey production"
    )
    hive_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    has_chickens: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Eggs"
    )
    chicken_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    has_cows: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    cow_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    # Certifications
    is_organic: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    is_bio_suisse: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    certifications: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated certifications"
    )

    # Production capabilities
    produces_salads: Mapped[bool] = mapped_column(Boolean, default=False)
    produces_dairy: Mapped[bool] = mapped_column(Boolean, default=False)
    produces_eggs: Mapped[bool] = mapped_column(Boolean, default=False)
    produces_honey: Mapped[bool] = mapped_column(Boolean, default=False)
    produces_herbs: Mapped[bool] = mapped_column(Boolean, default=False)
    produces_cbd: Mapped[bool] = mapped_column(Boolean, default=False)

    # Notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
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
    batches: Mapped[list["BatchModel"]] = relationship(
        back_populates="farm",
        cascade="all, delete-orphan"
    )
    traceable_items: Mapped[list["TraceableItemModel"]] = relationship(
        back_populates="origin_farm",
        foreign_keys="TraceableItemModel.origin_farm_id"
    )

    def __repr__(self):
        return f"<FarmModel(code='{self.code}', name='{self.name}', owner='{self.owner_name}')>"

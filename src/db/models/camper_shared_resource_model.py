# File: src/db/models/camper_shared_resource_model.py
"""
CamperSharedResourceModel - Bookable shared equipment at Camper & Tour, Trapani.

A shared resource is exclusive -- only 1 vehicle at a time. Bays are concurrent
(5 bays = 5 vehicles at once). The hoist is exclusive (1 hoist = 1 vehicle).
Different data model, different rules.

"The hoist is a bottleneck. A van can sit on it for 2 days while other jobs queue up."
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Boolean, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base


class ResourceType(str, enum.Enum):
    """What kind of shared resource"""
    HOIST = "hoist"
    COMPRESSOR = "compressor"
    DIAGNOSTIC = "diagnostic"
    WELDER = "welder"


class CamperSharedResourceModel(Base):
    """
    A bookable shared resource in the shop. One vehicle at a time.
    Generic -- could be a hoist, diagnostic scanner, welder, etc.
    """
    __tablename__ = 'camper_shared_resources'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Resource identity
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Display name: 'Main Hoist', 'Diagnostic Scanner'"
    )
    resource_type: Mapped[ResourceType] = mapped_column(
        SQLEnum(ResourceType, name='camper_resource_type', create_constraint=True),
        nullable=False,
        default=ResourceType.HOIST
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional notes about the resource"
    )

    # Active flag
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

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
    bookings: Mapped[list["CamperResourceBookingModel"]] = relationship(
        back_populates="resource",
        foreign_keys="CamperResourceBookingModel.resource_id"
    )

    def __repr__(self):
        return f"<CamperSharedResource(name='{self.name}', type={self.resource_type}, active={self.is_active})>"

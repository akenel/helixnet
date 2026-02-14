# File: src/db/models/camper_bay_model.py
"""
CamperBayModel - Service bays at Camper & Tour, Trapani.
A bay is a physical workspace in the shop (e.g., "Bay 1", "Electrical Bay").

A 3-hour job can take 3 days. Bays let Nino see what's where.
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Boolean, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base


class BayType(str, enum.Enum):
    """What kind of bay"""
    GENERAL = "general"
    ELECTRICAL = "electrical"
    MECHANICAL = "mechanical"
    BODYWORK = "bodywork"
    WASH = "wash"


class CamperBayModel(Base):
    """
    A service bay in the shop. Rows on the bay timeline.
    Flexible count -- Sebastino can add/remove bays as the shop grows.
    """
    __tablename__ = 'camper_bays'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Bay identity
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Display name: 'Bay 1', 'Electrical Bay'"
    )
    bay_type: Mapped[BayType] = mapped_column(
        SQLEnum(BayType, name='camper_bay_type', create_constraint=True),
        nullable=False,
        default=BayType.GENERAL
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional notes about the bay"
    )

    # Display
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="For consistent ordering in timeline view"
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
    service_jobs: Mapped[list["CamperServiceJobModel"]] = relationship(
        back_populates="bay",
        foreign_keys="CamperServiceJobModel.bay_id"
    )

    def __repr__(self):
        return f"<CamperBay(name='{self.name}', type={self.bay_type}, active={self.is_active})>"

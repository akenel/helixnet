# File: src/db/models/customs_clearance_model.py
"""
CustomsClearanceModel - Ka-Maki's domain.
Swiss-Japanese precision. Duties, inspections, approvals.

"COOLIE... you beautiful bastard. Your papers are TIGHT." - Charlie
"""
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, DateTime, Date, Integer, Boolean, Text, Numeric, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base


class CustomsStatus(str, enum.Enum):
    """Ka-Maki's world"""
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    DOCUMENTS_SUBMITTED = "documents_submitted"
    UNDER_REVIEW = "under_review"
    INSPECTION_REQUIRED = "inspection_required"
    INSPECTING = "inspecting"
    DUTIES_CALCULATED = "duties_calculated"
    DUTIES_PAID = "duties_paid"
    CLEARED = "cleared"
    HELD = "held"
    REJECTED = "rejected"


class CustomsClearanceModel(Base):
    """
    Customs clearance for a shipment.
    Ka-Maki from Luzern. Swiss-Japanese precision.
    """
    __tablename__ = 'customs_clearances'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Identity
    clearance_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="e.g., CC-2025-ROT-1247"
    )

    # What shipment
    shipment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('shipments.id'),
        nullable=False,
        index=True
    )
    shipment_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Denormalized for display"
    )

    # Where
    port_of_entry: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="e.g., Rotterdam, Zurich Airport"
    )
    customs_office: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )

    # Who's handling
    customs_agent: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="e.g., Ka-Maki"
    )
    agent_company: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )
    agent_contact: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )

    # Status
    status: Mapped[CustomsStatus] = mapped_column(
        SQLEnum(CustomsStatus),
        default=CustomsStatus.PENDING,
        nullable=False
    )

    # Documents (stored as JSON)
    documents: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Array of document objects with type, number, status"
    )
    documents_complete: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # Classification
    hs_codes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated HS codes"
    )

    # Duties & Taxes
    duties_calculated: Mapped[bool] = mapped_column(Boolean, default=False)
    import_duty: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0,
        nullable=False
    )
    vat: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0,
        nullable=False
    )
    other_fees: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0,
        nullable=False
    )
    total_duties: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0,
        nullable=False
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        default="CHF",
        nullable=False
    )

    # Payment
    duties_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    duties_paid_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    duties_paid_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Inspection
    inspection_required: Mapped[bool] = mapped_column(Boolean, default=False)
    inspection_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    inspection_result: Mapped[str | None] = mapped_column(String(50), nullable=True)
    inspection_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timeline
    submitted_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    cleared_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    processing_days: Mapped[int] = mapped_column(Integer, default=0)

    # Issues
    has_issues: Mapped[bool] = mapped_column(Boolean, default=False)
    issue_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    issue_resolution: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

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
    # Note: Shipment.customs_clearance_id is the owning FK
    # CustomsClearanceModel.shipment_id kept for denormalization/queries
    shipments: Mapped[list["ShipmentModel"]] = relationship(
        back_populates="customs_clearance",
        foreign_keys="[ShipmentModel.customs_clearance_id]"
    )

    def __repr__(self):
        return f"<CustomsClearanceModel(num='{self.clearance_number}', status={self.status}, agent='{self.customs_agent}')>"

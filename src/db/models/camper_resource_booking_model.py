# File: src/db/models/camper_resource_booking_model.py
"""
CamperResourceBookingModel - Time-slot bookings for shared resources.

Bookings are DATE-level, not hour-level. A camper shop doesn't book by the hour.
"The hoist is yours Monday through Wednesday" is the real conversation.

Overlap detection uses inclusive dates: if you book Mon-Wed and someone tries
Wed-Fri, that's a conflict. The hoist can't be in two places on Wednesday.

Only SCHEDULED and IN_USE bookings block. CANCELLED and COMPLETED are invisible
to the overlap check.
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, date as date_type, timezone
from sqlalchemy import String, DateTime, Date, Text, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base


class BookingStatus(str, enum.Enum):
    """Lifecycle of a resource booking"""
    SCHEDULED = "scheduled"    # reserved for future
    IN_USE = "in_use"          # vehicle is on it now
    COMPLETED = "completed"    # done, freed up
    CANCELLED = "cancelled"    # cancelled, slot freed


class CamperResourceBookingModel(Base):
    """
    A time-slot booking for a shared resource.
    Links a service job to a resource for a date range.
    """
    __tablename__ = 'camper_resource_bookings'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Foreign Keys
    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("camper_shared_resources.id"),
        nullable=False,
        comment="Which shared resource is booked"
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("camper_service_jobs.id"),
        nullable=False,
        comment="Which service job this booking is for"
    )

    # Booking dates (inclusive)
    start_date: Mapped[date_type] = mapped_column(
        Date,
        nullable=False,
        comment="First day of booking"
    )
    end_date: Mapped[date_type] = mapped_column(
        Date,
        nullable=False,
        comment="Last day of booking (inclusive)"
    )

    # Status
    status: Mapped[BookingStatus] = mapped_column(
        SQLEnum(BookingStatus, name='camper_booking_status', create_constraint=True),
        nullable=False,
        default=BookingStatus.SCHEDULED
    )

    # Metadata
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="e.g., 'Need full undercarriage access for seal work'"
    )
    booked_by: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Username from token"
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
    resource: Mapped["CamperSharedResourceModel"] = relationship(
        back_populates="bookings"
    )
    job: Mapped["CamperServiceJobModel"] = relationship()

    def __repr__(self):
        return (
            f"<CamperResourceBooking(resource={self.resource_id}, "
            f"job={self.job_id}, {self.start_date}->{self.end_date}, "
            f"status={self.status})>"
        )

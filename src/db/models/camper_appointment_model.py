# File: src/db/models/camper_appointment_model.py
"""
CamperAppointmentModel - Appointment book & walk-in queue for Camper & Tour.

Solves the 8am queue problem: 3 walk-ins bump Nino's 9:30 booked customer.
Rule: booked beats walk-in. First-come beats late-comer.

"Sorry, I know, but we have other customers" -- never again.
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, date, time, timezone
from sqlalchemy import String, DateTime, Date, Time, Integer, Boolean, Text, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base


class AppointmentType(str, enum.Enum):
    """How did the customer arrive?"""
    BOOKED = "booked"      # Pre-scheduled with a time slot
    WALK_IN = "walk_in"    # Showed up at the door


class AppointmentPriority(str, enum.Enum):
    """Urgency level -- roof leaking beats new curtains"""
    NORMAL = "normal"
    URGENT = "urgent"


class AppointmentStatus(str, enum.Enum):
    """Lifecycle: SCHEDULED -> WAITING -> IN_SERVICE -> COMPLETED"""
    SCHEDULED = "scheduled"    # Booked for a future time
    WAITING = "waiting"        # Customer arrived, waiting for a bay
    IN_SERVICE = "in_service"  # Vehicle is being worked on
    COMPLETED = "completed"    # Done, customer left
    NO_SHOW = "no_show"        # Booked but never showed up
    CANCELLED = "cancelled"    # Customer cancelled


class CamperAppointmentModel(Base):
    """
    An appointment or walk-in entry at Camper & Tour.
    Combines the appointment book (booked) and walk-in queue (walk_in)
    into a single model so Nino sees one unified daily view.
    """
    __tablename__ = 'camper_appointments'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Appointment identity
    appointment_type: Mapped[AppointmentType] = mapped_column(
        SQLEnum(AppointmentType, name='camper_appointment_type', create_constraint=True),
        nullable=False,
        default=AppointmentType.BOOKED
    )
    priority: Mapped[AppointmentPriority] = mapped_column(
        SQLEnum(AppointmentPriority, name='camper_appointment_priority', create_constraint=True),
        nullable=False,
        default=AppointmentPriority.NORMAL
    )
    status: Mapped[AppointmentStatus] = mapped_column(
        SQLEnum(AppointmentStatus, name='camper_appointment_status', create_constraint=True),
        nullable=False,
        default=AppointmentStatus.SCHEDULED,
        index=True
    )

    # Customer info (nullable for quick walk-in entry)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('camper_customers.id'),
        nullable=True,
        index=True,
        comment="Link to full customer record (optional for walk-ins)"
    )
    customer_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Quick name entry -- 'Marco with the white Ducato'"
    )
    customer_phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        comment="Quick phone for walk-ins without a customer record"
    )

    # Vehicle info (nullable -- might not know yet)
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('camper_vehicles.id'),
        nullable=True,
        index=True,
        comment="Link to vehicle record (optional)"
    )
    vehicle_plate: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Quick plate entry for walk-ins"
    )

    # Bay and job (assigned during or after triage)
    bay_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('camper_bays.id'),
        nullable=True,
        comment="Assigned bay (set when IN_SERVICE)"
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('camper_service_jobs.id'),
        nullable=True,
        comment="Created job (linked after triage)"
    )

    # Scheduling
    scheduled_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="The date of the appointment"
    )
    scheduled_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
        comment="Booked time slot (null for walk-ins)"
    )
    arrival_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the customer actually showed up"
    )
    service_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When work actually began"
    )
    service_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the appointment was completed"
    )

    # What they need
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="What the customer needs: 'brake check', 'roof leak', 'oil change'"
    )
    estimated_duration_minutes: Mapped[int] = mapped_column(
        Integer,
        default=60,
        nullable=False,
        comment="Estimated time needed in minutes"
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Internal notes from Nino"
    )

    # Audit
    created_by: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Who created this entry"
    )
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
    customer: Mapped["CamperCustomerModel"] = relationship(
        foreign_keys=[customer_id]
    )
    vehicle: Mapped["CamperVehicleModel"] = relationship(
        foreign_keys=[vehicle_id]
    )
    bay: Mapped["CamperBayModel"] = relationship(
        foreign_keys=[bay_id]
    )
    job: Mapped["CamperServiceJobModel"] = relationship(
        foreign_keys=[job_id]
    )

    def __repr__(self):
        return (
            f"<CamperAppointment(type={self.appointment_type}, "
            f"customer='{self.customer_name}', "
            f"date={self.scheduled_date}, status={self.status})>"
        )

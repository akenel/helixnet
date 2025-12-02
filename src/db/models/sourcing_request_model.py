"""
Sourcing Request Model - HelixNET Sourcing System
Tracks product sourcing requests (Bestellungen) from staff.

Workflow:
NEW -> INVESTIGATING -> SOURCED -> ORDERED -> CLOSED
                    -> NOT_AVAILABLE (with recheck date)
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Integer, Boolean, Text, DateTime, Date, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.models.base import Base
import uuid


class SourcingRequestModel(Base):
    """
    A request to source/find a product supplier.

    Felix's paper system:
    - Date: When need was identified
    - Product: What to find
    - Felix Admin: Status (?, N/A, blank)
    - Lieferant: Resolved supplier code
    """
    __tablename__ = "sourcing_requests"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # Request identification
    request_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        comment="SR-2024-001 format"
    )

    # Product info
    product_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="What we're looking for"
    )
    product_sku: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Link to existing product if known"
    )
    product_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Additional details"
    )

    # Request tracking
    requested_by: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Who needs this: Pam, Ralph, Felix"
    )
    requested_date: Mapped[date] = mapped_column(
        Date,
        default=date.today,
        comment="When request was created"
    )
    assigned_to: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Who is investigating: Felix, etc"
    )

    # Status workflow
    status: Mapped[str] = mapped_column(
        String(20),
        default="new",
        comment="new, investigating, sourced, not_available, ordered, closed"
    )

    # Resolution
    supplier_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("suppliers.id"),
        nullable=True,
        comment="Resolved supplier"
    )
    resolution_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="When resolved"
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="How it was resolved"
    )

    # Not available tracking
    not_available_until: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Recheck date if not available"
    )

    # Ordering details (MRP-lite)
    min_order_qty: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Minimum order: 2 boxes, 5-pack, etc"
    )
    expected_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Expected unit price CHF"
    )
    order_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Ordering instructions"
    )

    # Priority
    priority: Mapped[str] = mapped_column(
        String(10),
        default="normal",
        comment="low, normal, high, urgent"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    supplier = relationship("SupplierModel", backref="sourcing_requests")

    def __repr__(self):
        return f"<SourcingRequest {self.request_code}: {self.product_name} ({self.status})>"


class SourcingNoteModel(Base):
    """
    Notes/history for a sourcing request.
    Tracks investigation progress, contacts made, etc.
    """
    __tablename__ = "sourcing_notes"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    request_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sourcing_requests.id"),
        nullable=False
    )

    author: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Who wrote this note"
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Note content"
    )

    source: Mapped[str] = mapped_column(
        String(20),
        default="research",
        comment="research, call, email, spannabis, helixnetwork"
    )

    # KB reference
    kb_reference: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Link to KB article: KB-004, KB-587"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    # Relationship
    request = relationship("SourcingRequestModel", backref="notes")

    def __repr__(self):
        return f"<SourcingNote by {self.author}: {self.content[:30]}...>"

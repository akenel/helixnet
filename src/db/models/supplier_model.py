"""
Supplier Model - HelixNET Sourcing System
Tracks known suppliers (Lieferanten) for product sourcing.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from src.db.models.base import Base
import uuid


class SupplierModel(Base):
    """
    Supplier/Lieferant for product sourcing.

    Examples:
    - 420: BR Break Shop
    - WR: Wellauer
    - ND: Near Dark
    - Hem: Hemag Nova
    """
    __tablename__ = "suppliers"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # Supplier identification
    code: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False,
        comment="Short code like '420', 'WR', 'Hem'"
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Full name: 'BR Break Shop'"
    )

    # Location & logistics
    country: Mapped[str] = mapped_column(
        String(2),
        default="CH",
        comment="ISO country code"
    )
    lead_time_days_min: Mapped[int] = mapped_column(
        Integer,
        default=1,
        comment="Minimum delivery days"
    )
    lead_time_days_max: Mapped[int] = mapped_column(
        Integer,
        default=5,
        comment="Maximum delivery days"
    )

    # Quality rating (A/B/C)
    quality_rating: Mapped[str] = mapped_column(
        String(1),
        default="B",
        comment="A=Premium, B=Good, C=Budget"
    )

    # Categories & products
    categories: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated: 'pipes,accessories,cbd'"
    )

    # Contact info (JSON for flexibility)
    contacts: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Contact details: {name, email, phone}"
    )

    # Swiss compliance
    swiss_certified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Has Swiss/EU certification"
    )

    # Notes & metadata
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
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

    def __repr__(self):
        return f"<Supplier {self.code}: {self.name} ({self.quality_rating})>"

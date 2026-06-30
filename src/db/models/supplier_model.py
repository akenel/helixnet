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
        comment="Short code like '420', 'WR', 'Hem' (legacy Sourcing System)"
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Full supplier name: 'Tamar Trade GmbH'"
    )

    # ---- Supplier Registry (import-source) fields -----------------------------
    # A supplier IS an import source. `prefix` is the SKU prefix the source's items
    # carry (TAM- = Tamar/Artemis, FTW- = FourTwenty, …). It is the authoritative
    # registry key — server-validated as ^[A-Z]{2,3}$, UNIQUE, never the reserved
    # codes {ART (article/Artemis), LZ (internal/manual)}. Nullable because legacy
    # Sourcing-System rows (420/WR/ND/Hem) predate the registry and carry no prefix.
    prefix: Mapped[Optional[str]] = mapped_column(
        String(3),
        unique=True,
        index=True,
        nullable=True,
        comment="SKU prefix, 2-3 UPPERCASE letters, e.g. 'TAM', 'FTW' (registry key)"
    )
    source_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Web origin for sync/'View on source', e.g. 'https://fourtwenty.ch'"
    )
    adapter_type: Mapped[Optional[str]] = mapped_column(
        String(40),
        nullable=True,
        comment="Import adapter: 'tamar' | 'magento' | 'csv' | 'manual'"
    )
    contact_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Primary contact email (registry)"
    )
    contact_phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Primary contact phone (registry)"
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


# ---- Supplier-prefix validation (shared by the Pydantic schema + any caller) ----
import re

# Reserved: never assignable as a supplier prefix.
#   ART — banned: collides with 'article'/Artemis itself.
#   LZ  — reserved: internal / manual entries (the receiving 'LZ-' lazy-create SKUs).
RESERVED_SUPPLIER_PREFIXES: set[str] = {"ART", "LZ"}
_PREFIX_RE = re.compile(r"^[A-Z]{2,3}$")


def normalize_supplier_prefix(value: str) -> str:
    """Force-uppercase, trim, and validate a supplier prefix.

    Rules: 2-3 letters A-Z only, and not in RESERVED_SUPPLIER_PREFIXES.
    Raises ValueError with a human message on any violation (DB UNIQUE handles dupes).
    """
    p = (value or "").strip().upper()
    if not _PREFIX_RE.match(p):
        raise ValueError("Prefix must be 2-3 uppercase letters (A-Z), e.g. 'TAM' or 'FTW'.")
    if p in RESERVED_SUPPLIER_PREFIXES:
        raise ValueError(f"Prefix '{p}' is reserved (ART=article/Artemis, LZ=internal/manual). Pick another.")
    return p

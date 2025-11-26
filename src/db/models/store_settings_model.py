# File: src/db/models/store_settings_model.py
"""
Store Settings Model for Felix's Artemis Store POS System

Configuration for each store location:
- VAT rate (changes yearly in Switzerland)
- Company information (name, address, VAT number)
- Contact details (phone, email, website)
- Receipt settings
- Multi-store support (Store 1, Store 2, etc.)
"""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import String, Numeric, Boolean, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base


class StoreSettingsModel(Base):
    """
    Store configuration settings.

    Each store location has its own settings record.
    Default: Store 1 (Artemis Store main location)
    Future: Store 2, 3, etc. when Felix expands
    """
    __tablename__ = "store_settings"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False
    )

    # Store Identification
    store_number: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        nullable=False,
        comment="Store number (1, 2, 3...). Used for multi-store selection."
    )

    store_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Display name (e.g., 'Artemis Store - Zurich')"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Is this store currently operational?"
    )

    # Company Information (for receipts)
    legal_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Legal business name"
    )

    address_line1: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Street address"
    )

    address_line2: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Additional address info (suite, building, etc.)"
    )

    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    postal_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    country: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Switzerland"
    )

    # Contact Information
    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Store phone number"
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Store email address"
    )

    website: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Store website URL"
    )

    # Swiss VAT Information
    vat_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Swiss VAT registration number (CHE-XXX.XXX.XXX MWST)"
    )

    vat_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("8.1"),
        comment="Current VAT rate percentage (e.g., 8.1 for 8.1%). Changes yearly in Switzerland."
    )

    # Receipt Settings
    receipt_header: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Optional header text printed on receipts"
    )

    receipt_footer: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Optional footer text (e.g., 'Thank you for your purchase!')"
    )

    receipt_logo_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="URL to store logo for receipts (MinIO path)"
    )

    # Discount Settings
    cashier_max_discount: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("10.0"),
        comment="Maximum discount percentage cashiers can apply (e.g., 10.0 = 10%)"
    )

    manager_max_discount: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("100.0"),
        comment="Maximum discount percentage managers can apply (100 = unlimited)"
    )

    # Customer Loyalty Settings
    loyalty_tier1_threshold: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Minimum purchase for tier 1 loyalty discount (CHF)"
    )

    loyalty_tier1_discount: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("10.0"),
        comment="Tier 1 loyalty discount percentage"
    )

    loyalty_tier2_threshold: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("1000.00"),
        comment="Minimum purchase for tier 2 loyalty discount (CHF)"
    )

    loyalty_tier2_discount: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("15.0"),
        comment="Tier 2 loyalty discount percentage"
    )

    loyalty_tier3_threshold: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("5000.00"),
        comment="Minimum purchase for tier 3 loyalty discount (CHF)"
    )

    loyalty_tier3_discount: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("25.0"),
        comment="Tier 3 loyalty discount percentage"
    )

    # Metadata
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

    def __repr__(self):
        return f"<StoreSettings(store_number={self.store_number}, name='{self.store_name}', vat_rate={self.vat_rate}%)>"

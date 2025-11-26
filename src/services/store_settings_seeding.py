# File: src/services/store_settings_seeding.py
"""
Store Settings Seeding Service for Felix's Artemis Store POS System

Seeds default store configuration:
- Store 1: Artemis Store (main location)
- VAT rate: 8.1% (Swiss rate for 2025)
- Default company information
- Receipt settings
- Discount limits
- Customer loyalty tiers
"""
import logging
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.models import StoreSettingsModel

logger = logging.getLogger(__name__)


async def seed_store_settings(db: AsyncSession) -> None:
    """
    Seed default store settings for Artemis Store.

    Creates Store #1 configuration if it doesn't exist.
    Idempotent - safe to run multiple times.
    """
    # Check if Store 1 already exists
    result = await db.execute(
        select(StoreSettingsModel).where(StoreSettingsModel.store_number == 1)
    )
    existing_store = result.scalar_one_or_none()

    if existing_store:
        logger.info(f"Store settings already exist for Store #{existing_store.store_number} - skipping seed")
        return

    # Create default Store #1 settings
    store1 = StoreSettingsModel(
        store_number=1,
        store_name="Artemis Store - Zurich",
        is_active=True,

        # Company Information
        legal_name="Artemis Growing Supplies GmbH",
        address_line1="Bahnhofstrasse 42",
        address_line2="",  # Optional
        city="Zurich",
        postal_code="8001",
        country="Switzerland",

        # Contact Information
        phone="+41 44 123 45 67",
        email="info@artemis-store.ch",
        website="https://artemis-store.ch",

        # Swiss VAT Information (2025 rate)
        vat_number="CHE-123.456.789 MWST",
        vat_rate=Decimal("8.1"),  # Swiss VAT rate for 2025

        # Receipt Settings
        receipt_header="Thank you for shopping at Artemis!",
        receipt_footer="Growing your dreams, one plant at a time 🌱",
        receipt_logo_url=None,  # TODO: Upload logo to MinIO

        # Discount Settings
        cashier_max_discount=Decimal("10.0"),  # Pam can give max 10%
        manager_max_discount=Decimal("100.0"),  # Felix/Ralph unlimited

        # Customer Loyalty Settings (from user requirements)
        loyalty_tier1_threshold=Decimal("0.00"),  # All customers
        loyalty_tier1_discount=Decimal("10.0"),  # 10% base loyalty

        loyalty_tier2_threshold=Decimal("1000.00"),  # CHF 1000+ lifetime
        loyalty_tier2_discount=Decimal("15.0"),  # 15% loyal customer

        loyalty_tier3_threshold=Decimal("5000.00"),  # CHF 5000+ lifetime
        loyalty_tier3_discount=Decimal("25.0"),  # 25% VIP customer
    )

    db.add(store1)
    await db.commit()
    await db.refresh(store1)

    logger.info(f"✅ Seeded Store #{store1.store_number}: {store1.store_name} (VAT: {store1.vat_rate}%)")


async def get_active_store_settings(db: AsyncSession, store_number: int = 1) -> StoreSettingsModel | None:
    """
    Get store settings for a specific store number.

    Args:
        db: Database session
        store_number: Store number (default: 1)

    Returns:
        StoreSettingsModel or None if not found
    """
    result = await db.execute(
        select(StoreSettingsModel).where(
            StoreSettingsModel.store_number == store_number,
            StoreSettingsModel.is_active == True
        )
    )
    return result.scalar_one_or_none()

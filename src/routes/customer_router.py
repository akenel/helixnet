# File: src/routes/customer_router.py
"""
Customer & CRACK Profile API Router

"Be water, my friend" - Bruce Lee
"Knowledge is the gold" - KB-001

Full CRUD + smart search for customer profiles.
Handles both spending (tiers) and knowledge (CRACK levels).
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import UUID
from typing import Optional, List

from src.db.database import get_db_session
from src.db.models import (
    CustomerModel,
    CrackLevel,
    LoyaltyTier,
    CreditTransactionModel,
    CreditTransactionType,
)
from src.schemas.customer_schema import (
    CustomerCreate,
    CustomerUpdate,
    CustomerRead,
    CustomerCheckoutView,
    CreditTransaction,
    CreditTransactionType as CreditTxType,
    CREDITS_FIRST_PURCHASE,
    CREDITS_ADD_INSTAGRAM,
    CREDITS_ADD_TELEGRAM,
    CREDITS_ADD_EMAIL,
    CREDITS_REFERRAL,
    CREDITS_REFERRED,
)
from src.core.keycloak_auth import require_any_pos_role, require_manager_or_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/customers", tags=["🎮 CRACK Loyalty"])


# ================================================================
# SEARCH - The Smart Lookup
# ================================================================

@router.get("/search")
async def search_customers(
    q: str = Query(..., min_length=1, description="Search by handle, @instagram, email, or phone"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """
    Smart customer search - finds CRACKs by any identifier.

    Supports:
    - Handle: "poppie" or "Poppie"
    - Instagram: "@poppie_420" or "poppie_420"
    - Email: "larry@example.ch" or partial
    - Phone: "+41" or partial

    Returns list of matching profiles with checkout-relevant info.
    """
    # Clean up the search term
    search_term = q.strip()

    # Build search conditions
    conditions = []

    # Handle search (case-insensitive)
    conditions.append(func.lower(CustomerModel.handle).contains(search_term.lower()))

    # Instagram search (with or without @)
    ig_term = search_term.lstrip('@')
    conditions.append(func.lower(CustomerModel.instagram).contains(ig_term.lower()))

    # Email search
    if '@' in search_term or '.' in search_term:
        conditions.append(func.lower(CustomerModel.email).contains(search_term.lower()))

    # Phone search
    if search_term.startswith('+') or search_term.isdigit():
        conditions.append(CustomerModel.phone.contains(search_term))

    # Query
    query = (
        select(CustomerModel)
        .where(CustomerModel.is_active == True)
        .where(or_(*conditions))
        .order_by(CustomerModel.handle)
        .limit(limit)
    )

    result = await db.execute(query)
    customers = result.scalars().all()

    return [
        {
            "id": str(c.id),
            "handle": c.handle,
            "real_name": c.real_name,
            "instagram": c.instagram,
            "email": c.email,
            "phone": c.phone,
            "loyalty_tier": c.loyalty_tier.value,
            "tier_discount_percent": c.tier_discount_percent,
            "credits_balance": c.credits_balance,
            "crack_level": c.crack_level.value,
            "visit_count": c.visit_count,
        }
        for c in customers
    ]


# ================================================================
# CHECKOUT VIEW - Quick lookup for POS
# ================================================================

@router.get("/checkout/{customer_id}")
async def get_checkout_view(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """
    Get customer checkout view - what cashier sees at POS.

    Returns tier discount, credits, alerts, and suggestions.
    """
    result = await db.execute(
        select(CustomerModel).where(CustomerModel.id == customer_id)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Calculate alerts
    birthday_soon = False
    if customer.birthday:
        today = datetime.now(timezone.utc).date()
        this_year_bday = customer.birthday.replace(year=today.year)
        days_until = (this_year_bday - today).days
        birthday_soon = 0 <= days_until <= 14

    # Tier upgrade check
    tier_upgrade_close = False
    spend_to_next = Decimal("0")
    if customer.loyalty_tier == LoyaltyTier.BRONZE:
        spend_to_next = Decimal("200") - customer.lifetime_spend
        tier_upgrade_close = spend_to_next <= 50
    elif customer.loyalty_tier == LoyaltyTier.SILVER:
        spend_to_next = Decimal("500") - customer.lifetime_spend
        tier_upgrade_close = spend_to_next <= 50
    elif customer.loyalty_tier == LoyaltyTier.GOLD:
        spend_to_next = Decimal("1000") - customer.lifetime_spend
        tier_upgrade_close = spend_to_next <= 50
    elif customer.loyalty_tier == LoyaltyTier.PLATINUM:
        spend_to_next = Decimal("2500") - customer.lifetime_spend
        tier_upgrade_close = spend_to_next <= 100

    # Last visit days
    last_visit_days = 999
    if customer.last_visit:
        delta = datetime.now(timezone.utc) - customer.last_visit
        last_visit_days = delta.days

    # Credits to next voucher (100 credits = CHF 5)
    credits_to_voucher = 100 - (customer.credits_balance % 100)
    if customer.credits_balance >= 100:
        credits_to_voucher = 0

    return {
        "id": str(customer.id),
        "handle": customer.handle,
        "instagram": customer.instagram,
        "loyalty_tier": customer.loyalty_tier.value,
        "tier_discount_percent": customer.tier_discount_percent,
        "credits_balance": customer.credits_balance,
        "credits_to_next_voucher": credits_to_voucher,
        "redeemable_voucher_value": (customer.credits_balance // 100) * 5,
        "crack_level": customer.crack_level.value,
        "kbs_written": customer.kbs_written,
        "last_visit_days_ago": last_visit_days,
        "favorite_products": customer.favorite_products or [],
        "birthday_soon": birthday_soon,
        "tier_upgrade_close": tier_upgrade_close,
        "spend_to_next_tier": float(spend_to_next) if spend_to_next > 0 else 0,
        "notes": customer.notes,
        "is_vip": customer.is_vip,
    }


# ================================================================
# CRUD OPERATIONS
# ================================================================

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer: CustomerCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """
    Create a new CRACK profile.

    Awards welcome credits:
    - 20 credits for first profile
    - +10 if Instagram provided
    - +10 if Telegram provided
    - +5 if email provided
    - +50 if referred (referrer gets +100)
    """
    # Check handle uniqueness
    existing = await db.execute(
        select(CustomerModel).where(
            func.lower(CustomerModel.handle) == customer.handle.lower()
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Handle '{customer.handle}' already exists"
        )

    # Check email uniqueness if provided
    if customer.email:
        existing_email = await db.execute(
            select(CustomerModel).where(CustomerModel.email == customer.email)
        )
        if existing_email.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")

    # Check Instagram uniqueness if provided
    if customer.instagram:
        ig = customer.instagram.lstrip('@')
        existing_ig = await db.execute(
            select(CustomerModel).where(
                func.lower(CustomerModel.instagram) == ig.lower()
            )
        )
        if existing_ig.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Instagram already registered")

    # Create customer
    new_customer = CustomerModel(
        handle=customer.handle,
        real_name=customer.real_name,
        email=customer.email,
        phone=customer.phone,
        instagram=customer.instagram.lstrip('@') if customer.instagram else None,
        telegram=customer.telegram,
        whatsapp=customer.whatsapp,
        preferred_contact=customer.preferred_contact,
        birthday=customer.birthday,
        language=customer.language,
        notes=customer.notes,
    )

    db.add(new_customer)
    await db.flush()  # Get the ID

    # Calculate welcome credits
    welcome_credits = CREDITS_FIRST_PURCHASE  # 20 base
    credit_descriptions = ["Welcome bonus: +20"]

    if customer.instagram:
        welcome_credits += CREDITS_ADD_INSTAGRAM
        credit_descriptions.append("Instagram linked: +10")

    if customer.telegram:
        welcome_credits += CREDITS_ADD_TELEGRAM
        credit_descriptions.append("Telegram linked: +10")

    if customer.email:
        welcome_credits += CREDITS_ADD_EMAIL
        credit_descriptions.append("Email added: +5")

    # Handle referral
    if customer.referrer_id:
        # Check referrer exists
        referrer_result = await db.execute(
            select(CustomerModel).where(CustomerModel.id == customer.referrer_id)
        )
        referrer = referrer_result.scalar_one_or_none()

        if referrer:
            # Award referral bonus to new customer
            welcome_credits += CREDITS_REFERRED
            credit_descriptions.append("Referral bonus: +50")
            new_customer.referrer_id = referrer.id

            # Award referrer
            referrer.credits_balance += CREDITS_REFERRAL
            referrer.credits_earned_total += CREDITS_REFERRAL
            referrer.referrals_made += 1
            referrer.referral_credits_earned += CREDITS_REFERRAL

            # Log referrer transaction
            referrer_tx = CreditTransactionModel(
                customer_id=referrer.id,
                transaction_type=CreditTransactionType.REFERRAL,
                credits=CREDITS_REFERRAL,
                balance_after=referrer.credits_balance,
                reference_id=new_customer.id,
                reference_type="customer",
                description=f"Referral bonus: {new_customer.handle} joined",
            )
            db.add(referrer_tx)

    # Update new customer credits
    new_customer.credits_balance = welcome_credits
    new_customer.credits_earned_total = welcome_credits

    # Log welcome credits transaction
    welcome_tx = CreditTransactionModel(
        customer_id=new_customer.id,
        transaction_type=CreditTransactionType.ACTION_BONUS,
        credits=welcome_credits,
        balance_after=welcome_credits,
        description=" | ".join(credit_descriptions),
    )
    db.add(welcome_tx)

    await db.commit()
    await db.refresh(new_customer)

    logger.info(f"New CRACK created: {new_customer.handle} (+{welcome_credits} credits)")

    return {
        "id": str(new_customer.id),
        "handle": new_customer.handle,
        "credits_awarded": welcome_credits,
        "message": f"Welcome {new_customer.handle}! {welcome_credits} credits awarded.",
    }


@router.get("/{customer_id}")
async def get_customer(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Get full customer profile by ID."""
    result = await db.execute(
        select(CustomerModel).where(CustomerModel.id == customer_id)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return {
        "id": str(customer.id),
        "handle": customer.handle,
        "real_name": customer.real_name,
        "email": customer.email,
        "phone": customer.phone,
        "instagram": customer.instagram,
        "telegram": customer.telegram,
        "whatsapp": customer.whatsapp,
        "preferred_contact": customer.preferred_contact.value,
        "birthday": customer.birthday.isoformat() if customer.birthday else None,
        "language": customer.language,
        "loyalty_tier": customer.loyalty_tier.value,
        "lifetime_spend": float(customer.lifetime_spend),
        "tier_discount_percent": customer.tier_discount_percent,
        "credits_balance": customer.credits_balance,
        "credits_earned_total": customer.credits_earned_total,
        "credits_spent_total": customer.credits_spent_total,
        "crack_level": customer.crack_level.value,
        "crack_group": customer.crack_group,
        "crack_team": customer.crack_team,
        "kbs_written": customer.kbs_written,
        "kbs_approved": customer.kbs_approved,
        "kbs_featured": customer.kbs_featured,
        "kb_credits_earned": customer.kb_credits_earned,
        "first_purchase": customer.first_purchase.isoformat() if customer.first_purchase else None,
        "last_purchase": customer.last_purchase.isoformat() if customer.last_purchase else None,
        "last_visit": customer.last_visit.isoformat() if customer.last_visit else None,
        "visit_count": customer.visit_count,
        "purchase_count": customer.purchase_count,
        "average_basket": float(customer.average_basket),
        "favorite_products": customer.favorite_products or [],
        "favorite_categories": customer.favorite_categories or [],
        "referrer_id": str(customer.referrer_id) if customer.referrer_id else None,
        "referrals_made": customer.referrals_made,
        "referral_credits_earned": customer.referral_credits_earned,
        "notes": customer.notes,
        "is_active": customer.is_active,
        "is_vip": customer.is_vip,
        "created_at": customer.created_at.isoformat(),
        "updated_at": customer.updated_at.isoformat(),
    }


@router.put("/{customer_id}")
async def update_customer(
    customer_id: UUID,
    update: CustomerUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Update customer profile."""
    result = await db.execute(
        select(CustomerModel).where(CustomerModel.id == customer_id)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Track profile completion bonuses
    bonus_credits = 0
    bonus_descriptions = []

    # Update fields
    update_data = update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        # Check for new Instagram (bonus)
        if field == "instagram" and value and not customer.instagram:
            bonus_credits += CREDITS_ADD_INSTAGRAM
            bonus_descriptions.append("Instagram linked: +10")
            value = value.lstrip('@')

        # Check for new Telegram (bonus)
        if field == "telegram" and value and not customer.telegram:
            bonus_credits += CREDITS_ADD_TELEGRAM
            bonus_descriptions.append("Telegram linked: +10")

        # Check for new email (bonus)
        if field == "email" and value and not customer.email:
            bonus_credits += CREDITS_ADD_EMAIL
            bonus_descriptions.append("Email added: +5")

        setattr(customer, field, value)

    # Award profile completion bonuses
    if bonus_credits > 0:
        customer.credits_balance += bonus_credits
        customer.credits_earned_total += bonus_credits

        bonus_tx = CreditTransactionModel(
            customer_id=customer.id,
            transaction_type=CreditTransactionType.ACTION_BONUS,
            credits=bonus_credits,
            balance_after=customer.credits_balance,
            description=" | ".join(bonus_descriptions),
        )
        db.add(bonus_tx)

    customer.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "id": str(customer.id),
        "handle": customer.handle,
        "message": f"Profile updated" + (f" (+{bonus_credits} bonus credits!)" if bonus_credits else ""),
    }


# ================================================================
# CREDIT OPERATIONS
# ================================================================

@router.post("/{customer_id}/credits")
async def add_credits(
    customer_id: UUID,
    credits: int = Query(..., description="Credits to add (positive) or subtract (negative)"),
    reason: str = Query(..., min_length=3, description="Reason for adjustment"),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """
    Manual credit adjustment (manager/admin only).

    Use for:
    - Event prizes (HelixCup 2026)
    - Error corrections
    - Special promotions
    """
    result = await db.execute(
        select(CustomerModel).where(CustomerModel.id == customer_id)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Prevent negative balance
    new_balance = customer.credits_balance + credits
    if new_balance < 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reduce below 0. Current: {customer.credits_balance}, adjustment: {credits}"
        )

    # Update balance
    customer.credits_balance = new_balance
    if credits > 0:
        customer.credits_earned_total += credits
    else:
        customer.credits_spent_total += abs(credits)

    # Log transaction
    tx = CreditTransactionModel(
        customer_id=customer.id,
        transaction_type=CreditTransactionType.ADJUSTMENT,
        credits=credits,
        balance_after=new_balance,
        description=f"Manual adjustment: {reason}",
        created_by=UUID(current_user.get('sub', '00000000-0000-0000-0000-000000000000')),
    )
    db.add(tx)

    await db.commit()

    logger.info(f"Credit adjustment: {customer.handle} {'+' if credits > 0 else ''}{credits} by {current_user['username']}")

    return {
        "customer_id": str(customer.id),
        "handle": customer.handle,
        "credits_adjusted": credits,
        "new_balance": new_balance,
    }


@router.get("/{customer_id}/credits/history")
async def get_credit_history(
    customer_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Get customer's credit transaction history."""
    # Verify customer exists
    customer_result = await db.execute(
        select(CustomerModel).where(CustomerModel.id == customer_id)
    )
    customer = customer_result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Get transactions
    result = await db.execute(
        select(CreditTransactionModel)
        .where(CreditTransactionModel.customer_id == customer_id)
        .order_by(CreditTransactionModel.created_at.desc())
        .limit(limit)
    )
    transactions = result.scalars().all()

    return {
        "customer_id": str(customer_id),
        "handle": customer.handle,
        "current_balance": customer.credits_balance,
        "transactions": [
            {
                "id": str(tx.id),
                "type": tx.transaction_type.value,
                "credits": tx.credits,
                "balance_after": tx.balance_after,
                "description": tx.description,
                "created_at": tx.created_at.isoformat(),
            }
            for tx in transactions
        ],
    }


# ================================================================
# RECENT & STATS
# ================================================================

@router.get("/recent/visitors")
async def get_recent_customers(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Get recently visited customers for quick selection at POS."""
    result = await db.execute(
        select(CustomerModel)
        .where(CustomerModel.is_active == True)
        .where(CustomerModel.last_visit.isnot(None))
        .order_by(CustomerModel.last_visit.desc())
        .limit(limit)
    )
    customers = result.scalars().all()

    return [
        {
            "id": str(c.id),
            "handle": c.handle,
            "instagram": c.instagram,
            "loyalty_tier": c.loyalty_tier.value,
            "credits_balance": c.credits_balance,
            "last_visit": c.last_visit.isoformat() if c.last_visit else None,
        }
        for c in customers
    ]


@router.post("/{customer_id}/visit")
async def record_visit(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Record a store visit (called when customer is selected at checkout)."""
    result = await db.execute(
        select(CustomerModel).where(CustomerModel.id == customer_id)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    customer.last_visit = datetime.now(timezone.utc)
    customer.visit_count += 1

    await db.commit()

    return {"message": f"Visit recorded for {customer.handle}", "visit_count": customer.visit_count}

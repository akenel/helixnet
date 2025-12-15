# File: src/services/customer_seeding_service.py
"""
Customer Seeding Service - The CRACKs of HelixNET

"Knowledge is the gold" - KB-001

Seeds the character bible into real CustomerModel records.
Classification comes from BEHAVIOR not LABELS:
- loyalty_tier: How much they SPEND
- crack_level: How much they CONTRIBUTE
- is_vip: Manual override for legends

YAGNI: No extra "type" or "category" fields needed.
"""
import logging
from decimal import Decimal
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.models.customer_model import (
    CustomerModel,
    LoyaltyTier,
    CrackLevel,
    PreferredContact
)

logger = logging.getLogger(__name__)


async def seed_customers(db: AsyncSession) -> None:
    """
    Seed the HelixNET customer base from the Character Bible.

    The Boss Tiers (by behavior):
    - LEGENDS: Diamond tier, Oracle level, VIP flag (Bruce, Mosey, Felix circle)
    - REGULARS: Silver-Gold tier, Sprout-Rooted level (shop regulars)
    - STREET: Bronze tier, Seedling level (Littau crew, walk-ins)
    """
    logger.info("🌱 Checking if customers need to be seeded...")

    # Check if customers already exist
    result = await db.execute(select(CustomerModel).limit(1))
    existing = result.scalar_one_or_none()

    if existing:
        logger.info("✅ Customers already seeded. Skipping.")
        return

    logger.info("🌱 Seeding HelixNET customer base (The CRACKs)...")

    customers = [
        # ================================================================
        # THE LEGENDS (Diamond/Platinum, Oracle/Blazing, VIP)
        # ================================================================
        {
            "handle": "BruceBLQ",
            "real_name": "Bruce Lee",
            "email": "bruce@lee-ville.ch",
            "phone": "+41 79 888 8888",
            "instagram": "@bruceblq",
            "telegram": "@bruceblq",
            "preferred_contact": PreferredContact.TELEGRAM,
            "language": "en",
            "loyalty_tier": LoyaltyTier.DIAMOND,
            "lifetime_spend": Decimal("5500.00"),
            "tier_discount_percent": 25,
            "credits_balance": 2200,
            "credits_earned_total": 5500,
            "credits_spent_total": 3300,
            "crack_level": CrackLevel.ORACLE,
            "kbs_written": 42,
            "kbs_approved": 40,
            "kbs_featured": 8,
            "kb_credits_earned": 4000,
            "visit_count": 156,
            "purchase_count": 89,
            "average_basket": Decimal("61.80"),
            "referrals_made": 12,
            "referral_credits_earned": 1200,
            "is_vip": True,
            "notes": "The Master. Lee-Ville (mountains, 500m up). Wife: Cynthia. Quality-focused. Interested in SS grinders, custom BLQ branding. Sharp eye, calm, 'go with the flow'."
        },
        {
            "handle": "MsLee",
            "real_name": "Cynthia Lee",
            "email": "cynthia@lee-ville.ch",
            "phone": "+41 79 888 8889",
            "preferred_contact": PreferredContact.EMAIL,
            "language": "en",
            "loyalty_tier": LoyaltyTier.GOLD,
            "lifetime_spend": Decimal("890.00"),
            "tier_discount_percent": 15,
            "credits_balance": 445,
            "credits_earned_total": 890,
            "credits_spent_total": 445,
            "crack_level": CrackLevel.SPROUT,
            "kbs_written": 3,
            "kbs_approved": 2,
            "visit_count": 23,
            "purchase_count": 18,
            "average_basket": Decimal("49.44"),
            "is_vip": True,
            "notes": "Bruce's wife. ~70yo. Loves coconut tea, India blends. Curious about CBD. Apple store regular (32GB laptop). Always has dinner plans."
        },
        {
            "handle": "Mosey420",
            "real_name": "Mosey",
            "email": "mosey@420breakshop.ch",
            "instagram": "@mosey420oracle",
            "telegram": "@mosey420",
            "preferred_contact": PreferredContact.TELEGRAM,
            "language": "de",
            "loyalty_tier": LoyaltyTier.DIAMOND,
            "lifetime_spend": Decimal("12500.00"),
            "tier_discount_percent": 25,
            "credits_balance": 8500,
            "credits_earned_total": 15000,
            "credits_spent_total": 6500,
            "crack_level": CrackLevel.ORACLE,
            "kbs_written": 128,
            "kbs_approved": 125,
            "kbs_featured": 34,
            "kb_credits_earned": 12500,
            "visit_count": 420,
            "purchase_count": 280,
            "average_basket": Decimal("44.64"),
            "referrals_made": 45,
            "referral_credits_earned": 4500,
            "is_vip": True,
            "notes": "THE 420 Oracle. Supplier contact at 420 Break Shop. Currently in Spain (Spannabis), prepping CannaTrade-2026. The knowledge master."
        },
        {
            "handle": "ChuckNorris",
            "real_name": "Chuck Norris",
            "email": "chuck@roundhouse.tx",
            "preferred_contact": PreferredContact.NONE,
            "language": "en",
            "loyalty_tier": LoyaltyTier.PLATINUM,
            "lifetime_spend": Decimal("2100.00"),
            "tier_discount_percent": 20,
            "credits_balance": 1050,
            "credits_earned_total": 2100,
            "credits_spent_total": 1050,
            "crack_level": CrackLevel.BLAZING,
            "kbs_written": 28,
            "kbs_approved": 28,  # Chuck's KBs are always approved
            "kbs_featured": 15,
            "kb_credits_earned": 2800,
            "visit_count": 7,  # Chuck only needs 7 visits
            "purchase_count": 7,
            "average_basket": Decimal("300.00"),
            "is_vip": True,
            "notes": "The Legend. Tourist, edge case tester. Interested in Sylvken wallets, platinum grinders, Texas papers (1980s obscure). C1-C2 level scenarios. Chuck doesn't buy products, products buy Chuck."
        },

        # ================================================================
        # THE NETWORK (Gold/Silver, Growing/Rooted)
        # ================================================================
        {
            "handle": "VeraLab",
            "real_name": "Vera",
            "email": "vera@swissmountainlab.ch",
            "instagram": "@vera_lab",
            "telegram": "@vera_lab",
            "preferred_contact": PreferredContact.TELEGRAM,
            "language": "de",
            "loyalty_tier": LoyaltyTier.GOLD,
            "lifetime_spend": Decimal("780.00"),
            "tier_discount_percent": 15,
            "credits_balance": 1200,
            "credits_earned_total": 1800,
            "credits_spent_total": 600,
            "crack_level": CrackLevel.BLAZING,
            "kbs_written": 35,
            "kbs_approved": 32,
            "kbs_featured": 12,
            "kb_credits_earned": 3200,
            "visit_count": 45,
            "purchase_count": 28,
            "average_basket": Decimal("27.86"),
            "is_vip": True,
            "notes": "The Lab Queen. Lab Operations / CBD Quality Control. Swiss Mountain Goat Farm. ~50,000 seeds per season. Vape vending venture with Felix. Filters BS from BLQ genes."
        },
        {
            "handle": "Sylvie",
            "real_name": "Sylvken",
            "email": "sylvie@snakeskins.ch",
            "instagram": "@sylvken_designs",
            "preferred_contact": PreferredContact.INSTAGRAM,
            "language": "de",
            "loyalty_tier": LoyaltyTier.SILVER,
            "lifetime_spend": Decimal("340.00"),
            "tier_discount_percent": 10,
            "credits_balance": 500,
            "credits_earned_total": 800,
            "credits_spent_total": 300,
            "crack_level": CrackLevel.ROOTED,
            "kbs_written": 8,
            "kbs_approved": 7,
            "kbs_featured": 2,
            "kb_credits_earned": 700,
            "visit_count": 32,
            "purchase_count": 15,
            "average_basket": Decimal("22.67"),
            "notes": "The Designer. Custom branding vendor / Leather designer. Logo engraving, special projects. Lead time 2-3 weeks. SNAKE SKINS leather business with Brother Mike."
        },
        {
            "handle": "BrotherMike",
            "real_name": "Mike",
            "email": "mike@snakeskins.ch",
            "telegram": "@brother_mike",
            "preferred_contact": PreferredContact.TELEGRAM,
            "language": "de",
            "loyalty_tier": LoyaltyTier.SILVER,
            "lifetime_spend": Decimal("450.00"),
            "tier_discount_percent": 10,
            "credits_balance": 600,
            "credits_earned_total": 900,
            "credits_spent_total": 300,
            "crack_level": CrackLevel.GROWING,
            "kbs_written": 12,
            "kbs_approved": 11,
            "kbs_featured": 3,
            "kb_credits_earned": 1100,
            "visit_count": 28,
            "purchase_count": 20,
            "average_basket": Decimal("22.50"),
            "notes": "The Craftsman. Felix's brother. SNAKE SKINS custom leather. Cabinet making. Has Snake (pet) who whispers in his ear. 'Could be the biggest thing for the club'."
        },
        {
            "handle": "Sally420",
            "real_name": "Sally",
            "email": "sally@420breakshop.ch",
            "telegram": "@sally_420",
            "preferred_contact": PreferredContact.TELEGRAM,
            "language": "de",
            "loyalty_tier": LoyaltyTier.GOLD,
            "lifetime_spend": Decimal("620.00"),
            "tier_discount_percent": 15,
            "credits_balance": 800,
            "credits_earned_total": 1200,
            "credits_spent_total": 400,
            "crack_level": CrackLevel.ROOTED,
            "kbs_written": 6,
            "kbs_approved": 6,
            "kb_credits_earned": 600,
            "visit_count": 38,
            "purchase_count": 25,
            "average_basket": Decimal("24.80"),
            "notes": "Contact at 420 supplier. Can pull off ASAP orders. Earns CRACK points for clutch delivery. The emergency hotline."
        },
        {
            "handle": "AndyBlowUp",
            "real_name": "Andy",
            "email": "andy@blowup-littau.ch",
            "instagram": "@andy_blowup",
            "preferred_contact": PreferredContact.INSTAGRAM,
            "language": "de",
            "loyalty_tier": LoyaltyTier.SILVER,
            "lifetime_spend": Decimal("280.00"),
            "tier_discount_percent": 10,
            "credits_balance": 200,
            "credits_earned_total": 400,
            "credits_spent_total": 200,
            "crack_level": CrackLevel.SPROUT,
            "kbs_written": 4,
            "kbs_approved": 3,
            "kb_credits_earned": 300,
            "visit_count": 45,
            "purchase_count": 18,
            "average_basket": Decimal("15.56"),
            "notes": "Works at BlowUp with Aleena. Pet: Tasha (Husky, 15yo, no grey hair). Pink Punch freeze dry fruit, coco tanner butter. Angel wings tattoo on forehead. Temporarily at Junglings Heim."
        },
        {
            "handle": "Aleena",
            "real_name": "Aleena",
            "email": "aleena@blowup-littau.ch",
            "instagram": "@aleena_hubbly",
            "preferred_contact": PreferredContact.INSTAGRAM,
            "language": "de",
            "loyalty_tier": LoyaltyTier.SILVER,
            "lifetime_spend": Decimal("220.00"),
            "tier_discount_percent": 10,
            "credits_balance": 150,
            "credits_earned_total": 300,
            "credits_spent_total": 150,
            "crack_level": CrackLevel.SPROUT,
            "kbs_written": 2,
            "kbs_approved": 2,
            "kb_credits_earned": 200,
            "visit_count": 30,
            "purchase_count": 14,
            "average_basket": Decimal("15.71"),
            "notes": "Girl Friday at BlowUp/Hubbly Cafe. Knows Andy, part of the ecosystem."
        },
        {
            "handle": "MarioArg",
            "real_name": "Mario",
            "email": "mario@argentinian-luzern.ch",
            "whatsapp": "+41 79 555 1234",
            "preferred_contact": PreferredContact.WHATSAPP,
            "language": "de",
            "loyalty_tier": LoyaltyTier.BRONZE,
            "lifetime_spend": Decimal("95.00"),
            "tier_discount_percent": 5,
            "credits_balance": 50,
            "credits_earned_total": 95,
            "credits_spent_total": 45,
            "crack_level": CrackLevel.SEEDLING,
            "visit_count": 8,
            "purchase_count": 5,
            "average_basket": Decimal("19.00"),
            "notes": "Restaurant owner around the corner. Argentinian, burgers, veggies. Dinner reservations hub for Felix + VIPs."
        },

        # ================================================================
        # THE STREET (Bronze, Seedling) - Littau Crew
        # ================================================================
        {
            "handle": "SirGessler",
            "real_name": "Gessler",
            "preferred_contact": PreferredContact.NONE,
            "language": "de",
            "loyalty_tier": LoyaltyTier.BRONZE,
            "lifetime_spend": Decimal("23.00"),  # 25 years, 23 rappen current funds
            "tier_discount_percent": 5,
            "credits_balance": 0,
            "credits_earned_total": 23,
            "credits_spent_total": 23,
            "crack_level": CrackLevel.SEEDLING,
            "visit_count": 500,  # 25 years of visits
            "purchase_count": 12,
            "average_basket": Decimal("1.92"),
            "notes": "Street bum, crack addict. 25 years homeless, multiple rehab stints. Next rehab: Jan 31, 2026. Current funds: 23 Rappen. Returns broken pipes. Chipped Zippo needs flints (3 CHF). Knows Dirk's secret stash can method."
        },
        {
            "handle": "Burt",
            "real_name": "Robber-Bear OoDough",
            "preferred_contact": PreferredContact.NONE,
            "language": "de",
            "loyalty_tier": LoyaltyTier.BRONZE,
            "lifetime_spend": Decimal("0.00"),  # Scammer, never pays
            "tier_discount_percent": 5,
            "credits_balance": 0,
            "credits_earned_total": 0,
            "credits_spent_total": 0,
            "crack_level": CrackLevel.SEEDLING,
            "visit_count": 45,
            "purchase_count": 0,  # Never actually buys
            "average_basket": Decimal("0.00"),
            "notes": "Scammer, plays games with people. Handle unpronounceable, everyone calls him Burt. Tells people they're wrong, scams for free stuff. Associates: Gessler, Fabio. DO NOT EXTEND CREDIT."
        },
        {
            "handle": "FabioLittau",
            "real_name": "Fabio",
            "preferred_contact": PreferredContact.NONE,
            "language": "de",
            "loyalty_tier": LoyaltyTier.BRONZE,
            "lifetime_spend": Decimal("15.00"),
            "tier_discount_percent": 5,
            "credits_balance": -50,  # Negative - owes KB to Felix
            "credits_earned_total": 15,
            "credits_spent_total": 65,
            "crack_level": CrackLevel.SEEDLING,
            "visit_count": 30,
            "purchase_count": 3,
            "average_basket": Decimal("5.00"),
            "notes": "'Fake friend' from Littau. Camps behind Gutsch Castle trails. Part of Gessler's crew. OWES KB TO FELIX (grinder incident). Status: DEBT."
        },
        {
            "handle": "DirtyDD",
            "real_name": "Dirk",
            "preferred_contact": PreferredContact.NONE,
            "language": "de",
            "loyalty_tier": LoyaltyTier.BRONZE,
            "lifetime_spend": Decimal("8.50"),
            "tier_discount_percent": 5,
            "credits_balance": 100,  # Earned from recycling tips KB
            "credits_earned_total": 150,
            "credits_spent_total": 50,
            "crack_level": CrackLevel.SPROUT,  # Wrote the secret stash can KB!
            "kbs_written": 1,
            "kbs_approved": 1,
            "kbs_featured": 1,  # The secret stash can method is LEGENDARY
            "kb_credits_earned": 100,
            "visit_count": 60,
            "purchase_count": 4,
            "average_basket": Decimal("2.13"),
            "notes": "Deep Dive / Dig Deeper / Dirty DD. Dumpster diver, recycling entrepreneur. 4am alley runs. Secret stash can construction method (2 dog food cans + Swiss pocket knife). TOP SECRET - Gessler won't share without free coffee. Dream: Recycling empire. Motto: 'One man's trash is another man's stash'."
        },

        # ================================================================
        # WALK-IN TEMPLATE (For new customers)
        # ================================================================
        {
            "handle": "WalkIn001",
            "real_name": None,
            "preferred_contact": PreferredContact.NONE,
            "language": "de",
            "loyalty_tier": LoyaltyTier.BRONZE,
            "lifetime_spend": Decimal("0.00"),
            "tier_discount_percent": 5,
            "credits_balance": 0,
            "crack_level": CrackLevel.SEEDLING,
            "notes": "Template for anonymous walk-in customers. No loyalty card yet."
        },
    ]

    # Insert all customers
    created_count = 0
    for customer_data in customers:
        customer = CustomerModel(**customer_data)
        # NOTE: qr_code column not yet in DB - skip QR generation for now
        # customer.generate_qr_code()
        db.add(customer)
        created_count += 1
        logger.info(f"   ✓ {customer_data['handle']}: {customer_data.get('real_name', 'Anonymous')}")

    await db.commit()

    # Summary stats
    legends = sum(1 for c in customers if c.get("is_vip"))
    network = sum(1 for c in customers if c["loyalty_tier"] in [LoyaltyTier.GOLD, LoyaltyTier.SILVER] and not c.get("is_vip"))
    street = sum(1 for c in customers if c["loyalty_tier"] == LoyaltyTier.BRONZE)

    logger.info(f"")
    logger.info(f"✅ Seeded {created_count} customers!")
    logger.info(f"")
    logger.info(f"   📊 BY BEHAVIOR (not labels):")
    logger.info(f"   👑 Legends (Diamond/Platinum + VIP): {legends}")
    logger.info(f"   🤝 Network (Gold/Silver regulars): {network}")
    logger.info(f"   🚶 Street (Bronze walk-ins): {street}")
    logger.info(f"")
    logger.info(f"   💎 Total lifetime spend in system: CHF {sum(c['lifetime_spend'] for c in customers):,.2f}")
    logger.info(f"   📝 Total KBs written: {sum(c.get('kbs_written', 0) for c in customers)}")
    logger.info(f"")
    logger.info(f"   'The customer is the boss' - HelixNET Philosophy")

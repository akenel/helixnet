# File: src/services/artemis_user_seeding.py
"""
Seed Artemis Store Staff Users
Creates Pam, Ralph, Michael (sales) and Felix (manager) for testing.
"""
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.models import UserModel

logger = logging.getLogger(__name__)


async def seed_artemis_staff(db: AsyncSession) -> None:
    """
    Seed Felix's Artemis store staff members.

    Staff:
    - Pam: Senior sales, main cashier (ID: ...0001)
    - Ralph: Sales associate (ID: ...0002)
    - Michael: Sales associate (ID: ...0003)
    - Felix: Store manager/owner (ID: ...0004)
    """
    logger.info("👥 Seeding Artemis store staff...")

    # Define staff with fixed UUIDs for consistent testing
    staff_members = [
        {
            "id": UUID("00000000-0000-0000-0000-000000000001"),
            "keycloak_id": UUID("63b279e7-9062-4065-831d-167fcdc48eab"),  # Real Keycloak sub
            "username": "pam",
            "email": "pam@artemis-luzern.ch",
            "first_name": "Pam",
            "last_name": "Beesly",
            "is_active": True,
            "is_superuser": False,
            "preferences": {
                "role": "cashier",
                "department": "Sales",
                "employee_id": "EMP-001",
                "shift": "morning"
            }
        },
        {
            "id": UUID("00000000-0000-0000-0000-000000000002"),
            "keycloak_id": UUID("bbe1529e-fb43-4a38-a949-77755d919226"),  # Real Keycloak sub
            "username": "ralph",
            "email": "ralph@artemis-luzern.ch",
            "first_name": "Ralph",
            "last_name": "Wiggum",
            "is_active": True,
            "is_superuser": False,
            "preferences": {
                "role": "cashier",
                "department": "Sales",
                "employee_id": "EMP-002",
                "shift": "afternoon"
            }
        },
        {
            "id": UUID("00000000-0000-0000-0000-000000000003"),
            "keycloak_id": UUID("10000000-0000-0000-0000-000000000003"),
            "username": "michael",
            "email": "michael@artemis-luzern.ch",
            "first_name": "Michael",
            "last_name": "Scott",
            "is_active": True,
            "is_superuser": False,
            "preferences": {
                "role": "cashier",
                "department": "Sales",
                "employee_id": "EMP-003",
                "shift": "evening"
            }
        },
        {
            "id": UUID("00000000-0000-0000-0000-000000000004"),
            "keycloak_id": UUID("729aec8c-ab47-44d2-9467-25e4d897f036"),  # Real Keycloak sub
            "username": "felix",
            "email": "felix@artemis-luzern.ch",
            "first_name": "Felix",
            "last_name": "Manager",
            "is_active": True,
            "is_superuser": True,  # Felix is admin/manager
            "preferences": {
                "role": "manager",
                "department": "Management",
                "employee_id": "MGR-001",
                "store_location": "Murbacherstrasse 37, 6003 Luzern",
                "phone": "041 220 22 22"
            }
        }
    ]

    created_count = 0
    updated_count = 0

    for staff_data in staff_members:
        # Check if user already exists
        result = await db.execute(
            select(UserModel).where(UserModel.id == staff_data["id"])
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            # Update existing user
            for key, value in staff_data.items():
                if key != "id":  # Don't update ID
                    setattr(existing_user, key, value)
            updated_count += 1
            logger.info(f"   ✓ Updated: {staff_data['username']} ({staff_data['first_name']} {staff_data['last_name']})")
        else:
            # Create new user
            new_user = UserModel(**staff_data)
            db.add(new_user)
            created_count += 1
            logger.info(f"   ✓ Created: {staff_data['username']} ({staff_data['first_name']} {staff_data['last_name']})")

    await db.commit()

    logger.info(f"✅ Artemis staff seeding complete!")
    logger.info(f"   - Created: {created_count} users")
    logger.info(f"   - Updated: {updated_count} users")
    logger.info(f"   - Total staff: {len(staff_members)}")
    logger.info("")
    logger.info("   👔 Manager: Felix (felix@artemis-luzern.ch)")
    logger.info("   👩‍💼 Cashiers: Pam, Ralph, Michael")

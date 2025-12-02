# File: src/services/hr_seeding_service.py
"""
Seed HR Data - Employees & Time Entries

Creates employee records for Artemis staff and sample time entries.
Pam's December schedule: ~40 hours, up to 45 in busy weeks.

"First Time Right" - Six Sigma meets Bruce Lee
"""
import logging
from uuid import UUID
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Dict
import random

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.models import (
    UserModel,
    EmployeeModel,
    TimeEntryModel,
)

logger = logging.getLogger(__name__)


async def seed_hr_employees(db: AsyncSession) -> Dict:
    """
    Create employee records for Artemis staff.
    Links to existing UserModel records from artemis_user_seeding.
    """
    logger.info("Creating HR employee records...")

    # Employee data with realistic Swiss values
    employees_data = [
        {
            "id": UUID("e0000000-0000-0000-0000-000000000001"),
            "user_id": UUID("00000000-0000-0000-0000-000000000001"),  # Links to Pam's user record
            "first_name": "Pam",
            "last_name": "Beesly",
            "date_of_birth": date(1989, 3, 25),
            "nationality": "CH",
            "ahv_number": "756.1234.5678.90",
            "email": "pam@artemis-luzern.ch",
            "phone": "+41 79 123 45 67",
            "street": "Hirschengraben 15",
            "postal_code": "6003",
            "city": "Luzern",
            "canton": "LU",
            "iban": "CH93 0076 2011 6238 5295 7",
            "bank_name": "Luzerner Kantonalbank",
            "employee_number": "BLQ-001",
            "contract_type": "fulltime",
            "status": "active",
            "start_date": date(2023, 4, 1),
            "hours_per_week": Decimal("40.00"),
            "hourly_rate": Decimal("28.50"),  # CHF 28.50/hour
            "remote_days_per_week": 0,  # Store work, no remote
            "health_insurance_active": True,
            "bvg_insured": True,
            "bvg_contribution_rate": Decimal("0.0700"),
            "is_quellensteuer": False,
            "notes": "Senior cashier, vending machine restocking lead"
        },
        {
            "id": UUID("e0000000-0000-0000-0000-000000000002"),
            "user_id": UUID("00000000-0000-0000-0000-000000000002"),  # Ralph
            "first_name": "Ralph",
            "last_name": "Wiggum",
            "date_of_birth": date(1995, 7, 12),
            "nationality": "CH",
            "ahv_number": "756.2345.6789.01",
            "email": "ralph@artemis-luzern.ch",
            "phone": "+41 79 234 56 78",
            "street": "Bundesplatz 8",
            "postal_code": "6003",
            "city": "Luzern",
            "canton": "LU",
            "iban": "CH82 0900 0000 1234 5678 9",
            "bank_name": "PostFinance",
            "employee_number": "BLQ-002",
            "contract_type": "parttime",
            "status": "active",
            "start_date": date(2024, 1, 15),
            "hours_per_week": Decimal("24.00"),  # 60% part-time
            "hourly_rate": Decimal("26.00"),
            "remote_days_per_week": 0,
            "health_insurance_active": True,
            "bvg_insured": True,
            "bvg_contribution_rate": Decimal("0.0700"),
            "is_quellensteuer": False,
            "notes": "Afternoon shift specialist"
        },
        {
            "id": UUID("e0000000-0000-0000-0000-000000000003"),
            "user_id": UUID("00000000-0000-0000-0000-000000000003"),  # Michael
            "first_name": "Michael",
            "last_name": "Scott",
            "date_of_birth": date(1990, 11, 3),
            "nationality": "US",  # American expat
            "ahv_number": "756.3456.7890.12",
            "email": "michael@artemis-luzern.ch",
            "phone": "+41 79 345 67 89",
            "street": "Kapellgasse 20",
            "postal_code": "6004",
            "city": "Luzern",
            "canton": "LU",
            "iban": "CH71 0024 0024 1234 5678 0",
            "bank_name": "UBS",
            "employee_number": "BLQ-003",
            "contract_type": "fulltime",
            "status": "probation",  # Still in probation
            "start_date": date(2025, 10, 1),  # Started recently
            "probation_end_date": date(2026, 1, 1),
            "hours_per_week": Decimal("40.00"),
            "hourly_rate": Decimal("27.00"),
            "remote_days_per_week": 0,
            "health_insurance_active": False,  # Not yet (probation)
            "bvg_insured": True,
            "bvg_contribution_rate": Decimal("0.0700"),
            "is_quellensteuer": True,  # Foreign worker
            "quellensteuer_code": "B1",  # Single, no kids
            "notes": "Evening shift, great with customers"
        },
        {
            "id": UUID("e0000000-0000-0000-0000-000000000004"),
            "user_id": UUID("00000000-0000-0000-0000-000000000004"),  # Felix
            "first_name": "Felix",
            "last_name": "Manager",
            "date_of_birth": date(1985, 5, 18),
            "nationality": "CH",
            "ahv_number": "756.4567.8901.23",
            "email": "felix@artemis-luzern.ch",
            "phone": "+41 79 456 78 90",
            "street": "Murbacherstrasse 37",
            "postal_code": "6003",
            "city": "Luzern",
            "canton": "LU",
            "iban": "CH56 0483 5099 8765 4321 0",
            "bank_name": "Credit Suisse",
            "employee_number": "BLQ-MGR-001",
            "contract_type": "fulltime",
            "status": "active",
            "start_date": date(2020, 1, 1),  # Senior manager
            "hours_per_week": Decimal("42.00"),  # Manager hours
            "hourly_rate": Decimal("45.00"),  # Manager rate
            "remote_days_per_week": 1,  # One day remote for admin
            "remote_rate_multiplier": Decimal("1.00"),  # Full rate for manager remote
            "health_insurance_active": True,
            "bvg_insured": True,
            "bvg_contribution_rate": Decimal("0.0800"),  # Higher BVG for age
            "is_quellensteuer": False,
            "notes": "Store manager, reports to Mosey"
        },
    ]

    created = 0
    updated = 0

    for emp_data in employees_data:
        emp_id = emp_data.pop("id")

        # Check if exists
        result = await db.execute(
            select(EmployeeModel).where(EmployeeModel.id == emp_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            for key, value in emp_data.items():
                setattr(existing, key, value)
            updated += 1
            logger.info(f"   Updated: {emp_data['first_name']} {emp_data['last_name']}")
        else:
            new_emp = EmployeeModel(id=emp_id, **emp_data)
            db.add(new_emp)
            created += 1
            logger.info(f"   Created: {emp_data['first_name']} {emp_data['last_name']}")

    await db.commit()

    logger.info(f"HR employees seeding complete: {created} created, {updated} updated")
    return {"created": created, "updated": updated}


async def seed_pam_december_entries(db: AsyncSession) -> Dict:
    """
    Create sample time entries for Pam in December 2025.

    Pam's schedule:
    - Regular weeks: ~40 hours
    - December busy weeks: up to 45 hours
    - Handles vending machine restocking
    - Some Saturday shifts
    """
    logger.info("Creating Pam's December 2025 time entries...")

    pam_employee_id = UUID("e0000000-0000-0000-0000-000000000001")

    # Check if Pam's employee record exists
    result = await db.execute(
        select(EmployeeModel).where(EmployeeModel.id == pam_employee_id)
    )
    if not result.scalar_one_or_none():
        logger.warning("Pam's employee record not found. Run seed_hr_employees first.")
        return {"created": 0, "error": "Employee not found"}

    # December 2025 calendar (Mon-Sun weeks)
    # Week 1: Dec 1-7 (Dec 1 is Monday)
    # Week 2: Dec 8-14
    # Week 3: Dec 15-21
    # Week 4: Dec 22-28 (Christmas week - busy!)
    # Week 5: Dec 29-31

    entries_data = []

    # Week 1: Dec 1-5 (Mon-Fri) - Normal week, 40 hours
    week1 = [
        (date(2025, 12, 1), "regular", Decimal("8.5"), "08:00", "17:30", "Store shift + inventory check"),
        (date(2025, 12, 2), "regular", Decimal("8.0"), "08:00", "17:00", "Store shift"),
        (date(2025, 12, 3), "regular", Decimal("8.0"), "08:00", "17:00", "Store shift + vending restock"),
        (date(2025, 12, 4), "regular", Decimal("8.0"), "08:00", "17:00", "Store shift"),
        (date(2025, 12, 5), "regular", Decimal("7.5"), "08:00", "16:30", "Store shift, early close"),
    ]
    entries_data.extend(week1)

    # Week 2: Dec 8-13 (Mon-Sat) - Busy, 44 hours with Saturday
    week2 = [
        (date(2025, 12, 8), "regular", Decimal("8.5"), "08:00", "17:30", "Store shift"),
        (date(2025, 12, 9), "regular", Decimal("8.0"), "08:00", "17:00", "Store shift"),
        (date(2025, 12, 10), "regular", Decimal("8.5"), "08:00", "17:30", "Store shift + training new staff"),
        (date(2025, 12, 11), "regular", Decimal("8.0"), "08:00", "17:00", "Store shift"),
        (date(2025, 12, 12), "regular", Decimal("8.0"), "08:00", "17:00", "Store shift"),
        (date(2025, 12, 13), "overtime", Decimal("4.0"), "09:00", "13:00", "Saturday shift - Christmas rush"),
    ]
    entries_data.extend(week2)

    # Week 3: Dec 15-20 (Mon-Sat) - Peak, 45 hours
    week3 = [
        (date(2025, 12, 15), "regular", Decimal("9.0"), "07:30", "17:30", "Early start, vending full restock"),
        (date(2025, 12, 16), "regular", Decimal("8.5"), "08:00", "17:30", "Store shift"),
        (date(2025, 12, 17), "regular", Decimal("8.5"), "08:00", "17:30", "Store shift"),
        (date(2025, 12, 18), "regular", Decimal("8.0"), "08:00", "17:00", "Store shift"),
        (date(2025, 12, 19), "regular", Decimal("8.0"), "08:00", "17:00", "Store shift"),
        (date(2025, 12, 20), "overtime", Decimal("4.5"), "08:30", "13:00", "Saturday - peak Christmas shopping"),
    ]
    entries_data.extend(week3)

    # Week 4: Dec 22-24 + 26-27 (Christmas week)
    # Dec 25 = Weihnachten (public holiday)
    week4 = [
        (date(2025, 12, 22), "regular", Decimal("9.0"), "07:30", "17:30", "Last Monday before Christmas"),
        (date(2025, 12, 23), "regular", Decimal("8.5"), "08:00", "17:30", "Christmas Eve prep"),
        (date(2025, 12, 24), "regular", Decimal("5.0"), "08:00", "13:00", "Christmas Eve - half day"),
        (date(2025, 12, 25), "public_holiday", Decimal("8.0"), None, None, "Weihnachten"),
        (date(2025, 12, 26), "public_holiday", Decimal("8.0"), None, None, "Stephanstag"),
    ]
    entries_data.extend(week4)

    # Week 5: Dec 29-31 (Mon-Wed)
    week5 = [
        (date(2025, 12, 29), "regular", Decimal("8.0"), "08:00", "17:00", "Post-Christmas returns"),
        (date(2025, 12, 30), "regular", Decimal("8.0"), "08:00", "17:00", "Year-end inventory"),
        (date(2025, 12, 31), "regular", Decimal("4.0"), "08:00", "12:00", "Silvester - half day"),
    ]
    entries_data.extend(week5)

    created = 0
    skipped = 0

    for entry_date, entry_type, hours, start_time, end_time, description in entries_data:
        # Check if entry already exists
        result = await db.execute(
            select(TimeEntryModel).where(
                TimeEntryModel.employee_id == pam_employee_id,
                TimeEntryModel.entry_date == entry_date,
                TimeEntryModel.entry_type == entry_type
            )
        )
        if result.scalar_one_or_none():
            skipped += 1
            continue

        # Create entry
        new_entry = TimeEntryModel(
            employee_id=pam_employee_id,
            entry_date=entry_date,
            entry_type=entry_type,
            hours=hours,
            start_time=start_time,
            end_time=end_time,
            break_minutes=60 if hours >= Decimal("6") else 0,
            description=description,
            status="draft",  # Start as draft
        )
        db.add(new_entry)
        created += 1

    await db.commit()

    # Calculate total hours
    total_hours = sum(h for _, _, h, _, _, _ in entries_data)
    regular_hours = sum(h for _, t, h, _, _, _ in entries_data if t == "regular")
    overtime_hours = sum(h for _, t, h, _, _, _ in entries_data if t == "overtime")
    holiday_hours = sum(h for _, t, h, _, _, _ in entries_data if t == "public_holiday")

    logger.info(f"Pam's December entries: {created} created, {skipped} skipped")
    logger.info(f"   Total: {total_hours}h (Regular: {regular_hours}h, OT: {overtime_hours}h, Holiday: {holiday_hours}h)")

    return {
        "created": created,
        "skipped": skipped,
        "total_hours": float(total_hours),
        "regular_hours": float(regular_hours),
        "overtime_hours": float(overtime_hours),
        "holiday_hours": float(holiday_hours),
    }


async def seed_all_hr_data(db: AsyncSession) -> Dict:
    """
    Seed all HR data: employees and sample time entries.
    """
    logger.info("=" * 60)
    logger.info("SEEDING HR DATA")
    logger.info("=" * 60)

    employees_result = await seed_hr_employees(db)
    entries_result = await seed_pam_december_entries(db)

    logger.info("=" * 60)
    logger.info("HR SEEDING COMPLETE")
    logger.info("=" * 60)

    return {
        "employees": employees_result,
        "time_entries": entries_result,
    }

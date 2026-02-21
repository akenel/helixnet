# File: src/services/qa_seeding_service.py
# Purpose: Seed Anne's 9-phase, 46-item testing checklist into the QA dashboard.
# Idempotent: checks if data exists before seeding.

import logging
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.qa_test_result_model import QATestResultModel, TestStatus

logger = logging.getLogger("helix.qa_seeding")

# ================================================================
# Anne's 9-Phase Testing Checklist (46 items)
# Source: docs/testing/ANNE-TESTING-CHECKLIST.md
# ================================================================
CHECKLIST = [
    # Phase 1: First Login (6 items)
    (1, "First Login", 1, "Open the app URL", "Open https://46.62.138.218/camper in your browser"),
    (1, "First Login", 2, "Click the login button", "Click the orange 'Accedi' button on the landing page"),
    (1, "First Login", 3, "Enter credentials", "On the Keycloak login page, enter: nino / helix_pass"),
    (1, "First Login", 4, "Sign in successfully", "Click 'Sign In' and wait for redirect"),
    (1, "First Login", 5, "Dashboard greeting appears", "You should land on the Dashboard with 'Good morning, Nino!' (or afternoon/evening)"),
    (1, "First Login", 6, "Stat cards visible", "Dashboard shows stat cards: Vehicles, Jobs, Parts, Revenue"),

    # Phase 2: Explore the Dashboard (4 items)
    (2, "Dashboard", 1, "Read all stat cards", "Check Vehicles in Service, Active Jobs, Waiting for Parts, etc."),
    (2, "Dashboard", 2, "Click View All links", "Click 'View all' links on any stat card and verify navigation"),
    (2, "Dashboard", 3, "Quick action icons", "Try the quick-action icons: Check-In, New Quote, Calendar, Invoices"),
    (2, "Dashboard", 4, "Greeting changes by time", "Notice the greeting changes based on time of day"),

    # Phase 3: Vehicles (5 items)
    (3, "Vehicles", 1, "Navigate to Vehicles", "Navigate to Vehicles via sidebar or dashboard"),
    (3, "Vehicles", 2, "See 4 seed vehicles", "You should see 4 vehicles: Hymer Eriba, VW California, Fiat Ducato, Knaus"),
    (3, "Vehicles", 3, "View vehicle details", "Click on a vehicle to see plates, make/model, owner, service history"),
    (3, "Vehicles", 4, "Note vehicle fields", "Check that plates, make/model, owner, service history are displayed"),
    (3, "Vehicles", 5, "Search/filter vehicles", "Try the search or filter if available"),

    # Phase 4: Customers (6 items)
    (4, "Customers", 1, "Navigate to Customers", "Navigate to Customers page"),
    (4, "Customers", 2, "See 4 seed customers", "You should see 4 customers: Angel, Marco, Hans, Sophie"),
    (4, "Customers", 3, "View customer details", "Click into a customer to see their details"),
    (4, "Customers", 4, "Create new customer", "Create a NEW customer: Anne Tester, 0041 79 123 4567, anne@test.ch"),
    (4, "Customers", 5, "Search for new customer", "Search for the customer you just created"),
    (4, "Customers", 6, "Verify customer persists", "Refresh the page and confirm the new customer is still there"),

    # Phase 5: Jobs (6 items)
    (5, "Jobs", 1, "Navigate to Jobs", "Navigate to Jobs page"),
    (5, "Jobs", 2, "See 6 seed jobs", "You should see 6 jobs: roof seal, brake service, winterization, etc."),
    (5, "Jobs", 3, "View job details", "Click into a job to see the full detail page"),
    (5, "Jobs", 4, "Check status badges", "Note status badges, work log entries, cost summary"),
    (5, "Jobs", 5, "Check different statuses", "Check the different job statuses: Open, In Progress, Waiting Parts, etc."),
    (5, "Jobs", 6, "Create a new job", "Create a new job: pick a vehicle, pick a customer, title 'Test Job -- Brake Inspection'"),

    # Phase 6: Appointments (5 items)
    (6, "Appointments", 1, "Navigate to Appointments", "Navigate to Appointments page"),
    (6, "Appointments", 2, "See appointment board", "See today's board: Booked appointments (left) vs Walk-in Queue (right)"),
    (6, "Appointments", 3, "Create Quick Walk-in", "Click '+ Quick Walk-in' -- fill in a name + description"),
    (6, "Appointments", 4, "Walk-in appears in queue", "Watch the new walk-in appear in the queue"),
    (6, "Appointments", 5, "Change appointment status", "Try changing status: Arrived -> Start Service -> Completed"),

    # Phase 7: Bay Timeline (3 items)
    (7, "Bay Timeline", 1, "Navigate to Bay Timeline", "Navigate to Bay Timeline via sidebar"),
    (7, "Bay Timeline", 2, "See weekly grid", "See the weekly grid: 5 bays x 7 days with colored bars"),
    (7, "Bay Timeline", 3, "Navigate weeks", "Click 'Next Week' and 'Today' buttons, hover over bars for details"),

    # Phase 8: Quotations + Invoices (4 items)
    (8, "Quotations + Invoices", 1, "Navigate to Quotations", "Navigate to Quotations page"),
    (8, "Quotations + Invoices", 2, "View existing quotations", "View any existing quotations and check details"),
    (8, "Quotations + Invoices", 3, "Navigate to Invoices", "Navigate to Invoices page and view existing invoices"),
    (8, "Quotations + Invoices", 4, "Check PDF preview", "Check the PDF/print preview if available"),

    # Phase 9: Role Testing (8 items)
    (9, "Role Testing", 1, "Logout from nino", "Logout by clicking your name in top-right, then Logout"),
    (9, "Role Testing", 2, "Login as maximo (mechanic)", "Login as maximo / helix_pass"),
    (9, "Role Testing", 3, "Mechanic can see dashboard", "Verify maximo can see the dashboard"),
    (9, "Role Testing", 4, "Mechanic can view jobs", "Verify maximo can view jobs"),
    (9, "Role Testing", 5, "Mechanic can edit a job", "Try editing a job -- does it work?"),
    (9, "Role Testing", 6, "Login as camper-auditor", "Logout and login as camper-auditor / helix_pass"),
    (9, "Role Testing", 7, "Auditor can view everything", "Verify auditor can VIEW everything"),
    (9, "Role Testing", 8, "Auditor cannot edit", "Try to EDIT or CREATE something -- it should be blocked"),
]


async def seed_qa_checklist(db: AsyncSession) -> None:
    """Seed the QA testing checklist. Idempotent -- skips if data exists."""
    count_result = await db.execute(
        select(func.count()).select_from(QATestResultModel)
    )
    existing_count = count_result.scalar() or 0

    if existing_count > 0:
        logger.info(f"QA checklist already seeded ({existing_count} items). Skipping.")
        return

    for phase, phase_name, sort_order, title, description in CHECKLIST:
        test_item = QATestResultModel(
            phase=phase,
            phase_name=phase_name,
            sort_order=sort_order,
            title=title,
            description=description,
            status=TestStatus.PENDING,
        )
        db.add(test_item)

    await db.flush()
    logger.info(f"QA testing checklist seeded: {len(CHECKLIST)} items across 9 phases")

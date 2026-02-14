# File: src/services/camper_seeding_service.py
"""
Camper & Tour Seeding Service - Demo data for the pitch to Nino.
Runs on application startup. Uses MAX (Angel's camper) as the hero vehicle.

v2: Adds quotations, purchase orders, invoices, and calendar scheduling.

The seal inspection story is real. Everything else is demo data.

"If one seal fails, check all the seals."
"""
import logging
from datetime import date, datetime, time, timezone, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.models.camper_vehicle_model import CamperVehicleModel, VehicleType, VehicleStatus
from src.db.models.camper_customer_model import CamperCustomerModel, CustomerLanguage
from src.db.models.camper_bay_model import CamperBayModel, BayType
from src.db.models.camper_service_job_model import CamperServiceJobModel, JobType, JobStatus
from src.db.models.camper_work_log_model import CamperWorkLogModel, LogType
from src.db.models.camper_quotation_model import CamperQuotationModel, QuotationStatus
from src.db.models.camper_purchase_order_model import CamperPurchaseOrderModel, CamperPOStatus
from src.db.models.camper_invoice_model import CamperInvoiceModel, PaymentStatus
from src.db.models.camper_shared_resource_model import CamperSharedResourceModel, ResourceType
from src.db.models.camper_resource_booking_model import CamperResourceBookingModel, BookingStatus
from src.db.models.camper_appointment_model import CamperAppointmentModel, AppointmentType, AppointmentPriority, AppointmentStatus
from src.db.models.camper_supplier_model import CamperSupplierModel

logger = logging.getLogger(__name__)


async def seed_camper_data(db: AsyncSession) -> None:
    """
    Seed demo data for Camper & Tour service management.
    Idempotent -- checks if data exists before seeding.
    """
    logger.info("Checking if Camper & Tour data needs to be seeded...")

    # Check if customers already exist
    result = await db.execute(select(CamperCustomerModel).limit(1))
    if result.scalar_one_or_none():
        logger.info("Camper & Tour data already seeded. Skipping.")
        return

    logger.info("Seeding Camper & Tour demo data...")

    # ================================================================
    # CUSTOMERS
    # ================================================================
    angel = CamperCustomerModel(
        name="Angelo Kenel",
        phone="+41 79 000 0000",
        email="angel@helixnet.ch",
        address="Baglio Xiare",
        city="Trapani",
        language=CustomerLanguage.EN,
        tax_id=None,
        telegram_chat_id="123456789",
        first_visit=date(2025, 11, 15),
        last_visit=date(2026, 2, 6),
        visit_count=8,
        total_spend=Decimal("2450.00"),
        notes="Canadian-Swiss. Owns MAX campervan. Long-term customer. Building HelixNet platform for us.",
        preferred_contact_method="telegram",
        internal_notes="Speaks English, Italian, German. Pays on time. VIP -- building our software.",
    )

    marco_rossi = CamperCustomerModel(
        name="Marco Rossi",
        phone="+39 328 111 2222",
        email="marco.rossi@gmail.com",
        address="Via Roma 42",
        city="Trapani",
        language=CustomerLanguage.IT,
        tax_id="RSSMRC80A01L219K",
        telegram_chat_id="987654321",
        first_visit=date(2025, 6, 1),
        last_visit=date(2026, 1, 20),
        visit_count=5,
        total_spend=Decimal("1800.00"),
        notes="Regular customer. Fiat Ducato motorhome. Does annual maintenance here.",
        preferred_contact_method="phone",
        internal_notes="Pays cash. Morning guy -- always drops off at 8:30. Wife calls to check status.",
    )

    hans_mueller = CamperCustomerModel(
        name="Hans Mueller",
        phone="+49 170 333 4444",
        email="hans.mueller@web.de",
        address="Hauptstrasse 7",
        city="Munich",
        language=CustomerLanguage.DE,
        first_visit=date(2026, 1, 10),
        last_visit=date(2026, 2, 1),
        visit_count=2,
        total_spend=Decimal("650.00"),
        notes="German tourist. VW California. Needed emergency plumbing repair while touring Sicily.",
        preferred_contact_method="email",
        internal_notes="Speaks German + English. Tourist, probably won't return but left 5-star review.",
    )

    sophie_dupont = CamperCustomerModel(
        name="Sophie Dupont",
        phone="+33 6 55 66 77 88",
        email="sophie.dupont@orange.fr",
        city="Lyon",
        language=CustomerLanguage.FR,
        first_visit=date(2026, 2, 5),
        last_visit=date(2026, 2, 5),
        visit_count=1,
        total_spend=Decimal("0.00"),
        notes="French tourist. Hymer caravan. Dropped off for inspection, waiting for quote.",
        preferred_contact_method="whatsapp",
        internal_notes="Speaks French only. Use Google Translate. Nervous about gas system -- reassure her.",
    )

    db.add_all([angel, marco_rossi, hans_mueller, sophie_dupont])
    await db.flush()  # Get IDs assigned

    # ================================================================
    # VEHICLES
    # ================================================================
    max_camper = CamperVehicleModel(
        registration_plate="TI 123456",
        chassis_number="ZCFC135A005678901",
        vehicle_type=VehicleType.CAMPERVAN,
        make="Fiat",
        model="Ducato Campervan",
        year=2008,
        color="White",
        length_m=6.0,
        height_m=2.7,
        weight_kg=3200,
        owner_name="Angelo Kenel",
        owner_phone="+41 79 000 0000",
        owner_email="angel@helixnet.ch",
        owner_id=angel.id,
        insurance_company="AXA",
        insurance_policy="22.831.735/0001",
        status=VehicleStatus.IN_SERVICE,
        notes="The famous MAX. Bathroom window seal failed -- water leaked behind panels for years. "
              "Entire roof structure rotted end-to-end. Discovery Feb 6, 2026. "
              "Estimated repair: EUR 5,000-10,000+, 4-6 weeks.",
    )

    marco_ducato = CamperVehicleModel(
        registration_plate="TP 987654",
        vehicle_type=VehicleType.MOTORHOME,
        make="Fiat",
        model="Ducato Maxi",
        year=2015,
        color="Silver",
        length_m=7.2,
        height_m=3.0,
        weight_kg=3800,
        owner_name="Marco Rossi",
        owner_phone="+39 328 111 2222",
        owner_id=marco_rossi.id,
        status=VehicleStatus.PICKED_UP,
        notes="Annual service customer. Last oil change Jan 2026.",
    )

    hans_california = CamperVehicleModel(
        registration_plate="M VW 4242",
        vehicle_type=VehicleType.CAMPERVAN,
        make="Volkswagen",
        model="California T6.1",
        year=2021,
        color="Blue",
        length_m=4.9,
        height_m=2.0,
        weight_kg=2500,
        owner_name="Hans Mueller",
        owner_phone="+49 170 333 4444",
        owner_id=hans_mueller.id,
        status=VehicleStatus.PICKED_UP,
        notes="Emergency plumbing fix completed. Advised full service at home dealer.",
    )

    sophie_hymer = CamperVehicleModel(
        registration_plate="AB 123 CD",
        vehicle_type=VehicleType.CARAVAN,
        make="Hymer",
        model="Eriba Touring 542",
        year=2019,
        color="White/Silver",
        length_m=5.5,
        height_m=2.6,
        weight_kg=1400,
        owner_name="Sophie Dupont",
        owner_phone="+33 6 55 66 77 88",
        owner_id=sophie_dupont.id,
        status=VehicleStatus.CHECKED_IN,
        notes="Dropped off for full inspection. Customer concerned about gas system.",
    )

    db.add_all([max_camper, marco_ducato, hans_california, sophie_hymer])
    await db.flush()

    # ================================================================
    # SERVICE BAYS
    # ================================================================
    bay_1 = CamperBayModel(
        name="Bay 1",
        bay_type=BayType.GENERAL,
        description="Main service bay - large vehicles, general repairs",
        display_order=1,
    )
    bay_2 = CamperBayModel(
        name="Bay 2",
        bay_type=BayType.GENERAL,
        description="Secondary bay - smaller vehicles, routine maintenance",
        display_order=2,
    )
    bay_electrical = CamperBayModel(
        name="Electrical Bay",
        bay_type=BayType.ELECTRICAL,
        description="Solar, batteries, 12V/230V systems",
        display_order=3,
    )
    bay_bodywork = CamperBayModel(
        name="Bodywork Bay",
        bay_type=BayType.BODYWORK,
        description="Paint, panel repair, seals, waterproofing",
        display_order=4,
    )
    bay_wash = CamperBayModel(
        name="Wash Bay",
        bay_type=BayType.WASH,
        description="Pre-delivery wash and detail",
        display_order=5,
    )

    db.add_all([bay_1, bay_2, bay_electrical, bay_bodywork, bay_wash])
    await db.flush()

    # ================================================================
    # SERVICE JOBS
    # ================================================================

    # Job 1: MAX seal inspection (THE REAL STORY)
    max_seal_job = CamperServiceJobModel(
        job_number="JOB-20260206-0001",
        title="Full roof seal inspection + water damage assessment",
        description=(
            "Customer insisted on ladder inspection of roof. Discovered bathroom window seal "
            "had failed -- water leaked behind plastic ceiling panels for YEARS. Entire roof "
            "structure rotted end-to-end. Previous shops (including Bantam in Switzerland) "
            "fixed ONE window seal but never inspected the others. Same age, same manufacturer, "
            "same exposure -- should have checked all seals when the first one failed.\n\n"
            "THE LESSON: When one component fails, check ALL similar components."
        ),
        vehicle_id=max_camper.id,
        customer_id=angel.id,
        job_type=JobType.INSPECTION,
        status=JobStatus.IN_PROGRESS,
        assigned_to="Sebastino",
        bay_id=bay_bodywork.id,
        estimated_hours=80,
        estimated_parts_cost=Decimal("3000.00"),
        estimated_total=Decimal("5800.00"),
        estimated_days=30,
        start_date=date(2026, 2, 6),
        end_date=date(2026, 3, 8),
        actual_hours=16,
        actual_parts_cost=Decimal("0.00"),
        actual_labor_cost=Decimal("560.00"),
        actual_total=Decimal("560.00"),
        scheduled_date=date(2026, 2, 6),
        started_at=datetime(2026, 2, 6, 9, 0, tzinfo=timezone.utc),
        parts_on_order=True,
        parts_po_number="PO-20260210-0001",
        current_wait_reason="Waiting for Dometic window seals (shipping from Germany)",
        current_wait_until=date(2026, 2, 18),
        deposit_required=Decimal("1450.00"),
        deposit_paid=Decimal("1450.00"),
        deposit_paid_at=datetime(2026, 2, 7, 10, 0, tzinfo=timezone.utc),
        issue_found=(
            "1. Bathroom window seal completely degraded\n"
            "2. Water ingress behind ceiling panels (both sides)\n"
            "3. Roof structure rot from front to back\n"
            "4. Sleeping area window seal also suspect\n"
            "5. All 3 window seals are same age/manufacturer -- all need replacement"
        ),
        work_performed=(
            "Phase 1 (complete): Full interior strip-out. Removed ceiling panels. "
            "Assessed extent of damage. Documented with photos.\n"
            "Phase 2 (in progress): Sourcing replacement roof panels and seals.\n"
            "Phase 3 (pending): Structural repair and seal replacement."
        ),
        customer_notes="Customer discovered the issue himself by asking for a ladder inspection. "
                       "Previous service shops missed this for years.",
        mechanic_notes="Worst water damage case this year. Will need 4-6 weeks minimum. "
                       "Roof panels may need custom fabrication.",
        follow_up_required=True,
        follow_up_notes="Check all seals again after repair. Schedule 6-month follow-up.",
        next_service_date=date(2026, 8, 1),
        # Check-in data (CYA documentation)
        mileage_in=148320,
        condition_notes_in="Visible water stain on ceiling near bathroom. Small dent rear-left panel (pre-existing). "
                           "Customer reports intermittent smell of damp inside cabin.",
        checked_in_by="nino",
        checked_in_at=datetime(2026, 2, 6, 8, 45, tzinfo=timezone.utc),
    )

    # Job 2: Marco's annual service (routine, completed + invoiced)
    marco_service = CamperServiceJobModel(
        job_number="JOB-20260120-0001",
        title="Annual maintenance + oil change",
        description="Routine annual service. Oil change, filter replacement, brake check, tire rotation.",
        vehicle_id=marco_ducato.id,
        customer_id=marco_rossi.id,
        job_type=JobType.MAINTENANCE,
        status=JobStatus.INVOICED,
        assigned_to="Maximo",
        bay_id=bay_2.id,
        estimated_hours=4,
        estimated_parts_cost=Decimal("120.00"),
        estimated_total=Decimal("260.00"),
        estimated_days=1,
        start_date=date(2026, 1, 20),
        end_date=date(2026, 1, 20),
        actual_hours=3.5,
        actual_parts_cost=Decimal("115.00"),
        actual_labor_cost=Decimal("122.50"),
        actual_total=Decimal("237.50"),
        scheduled_date=date(2026, 1, 20),
        started_at=datetime(2026, 1, 20, 8, 30, tzinfo=timezone.utc),
        completed_at=datetime(2026, 1, 20, 12, 0, tzinfo=timezone.utc),
        picked_up_at=datetime(2026, 1, 20, 16, 0, tzinfo=timezone.utc),
        inspection_passed=True,
        inspected_by="nino",
        inspected_at=datetime(2026, 1, 20, 11, 45, tzinfo=timezone.utc),
        deposit_required=Decimal("65.00"),
        deposit_paid=Decimal("65.00"),
        deposit_paid_at=datetime(2026, 1, 18, 9, 0, tzinfo=timezone.utc),
        parts_used="Oil filter, air filter, 6L 5W-30 engine oil, brake pads (front)",
        issue_found="Front brake pads at 20% -- replaced. Rear pads still good (60%).",
        work_performed="Oil change, filter replacement, front brake pad replacement, tire rotation, "
                       "fluid top-up, visual inspection of undercarriage.",
        mechanic_notes="Vehicle in good shape for its age. Recommend timing belt at next service.",
        follow_up_required=True,
        follow_up_notes="Timing belt replacement due at next annual service.",
        next_service_date=date(2027, 1, 20),
        # Check-in/out + warranty
        mileage_in=87450,
        mileage_out=87452,
        condition_notes_in="Minor scratch front bumper (pre-existing). Otherwise clean.",
        condition_notes_out="Delivered clean. All work as described.",
        checked_in_by="nino",
        checked_in_at=datetime(2026, 1, 20, 8, 30, tzinfo=timezone.utc),
        warranty_months=6,
        warranty_expires_at=date(2026, 7, 20),
        warranty_terms="Parts + labor. Brake pads guaranteed 6 months or 20,000 km.",
    )

    # Job 3: Hans emergency plumbing (completed)
    hans_plumbing = CamperServiceJobModel(
        job_number="JOB-20260201-0001",
        title="Emergency water pump replacement",
        description="Water pump failed while touring. No fresh water supply in the van.",
        vehicle_id=hans_california.id,
        customer_id=hans_mueller.id,
        job_type=JobType.PLUMBING,
        status=JobStatus.COMPLETED,
        assigned_to="Seppi",
        estimated_hours=3,
        estimated_parts_cost=Decimal("180.00"),
        estimated_total=Decimal("285.00"),
        actual_hours=2.5,
        actual_parts_cost=Decimal("165.00"),
        actual_labor_cost=Decimal("87.50"),
        actual_total=Decimal("252.50"),
        scheduled_date=date(2026, 2, 1),
        started_at=datetime(2026, 2, 1, 10, 0, tzinfo=timezone.utc),
        completed_at=datetime(2026, 2, 1, 12, 30, tzinfo=timezone.utc),
        picked_up_at=datetime(2026, 2, 1, 14, 0, tzinfo=timezone.utc),
        inspection_passed=True,
        inspected_by="nino",
        inspected_at=datetime(2026, 2, 1, 12, 15, tzinfo=timezone.utc),
        parts_used="Fiamma Aqua 8 water pump, hose clamps x4, Teflon tape",
        issue_found="Original Shurflo pump motor burned out. Water lines in good condition.",
        work_performed="Replaced water pump with Fiamma Aqua 8. Tested all connections. "
                       "Ran system for 10 minutes -- no leaks.",
        customer_notes="Pump started making noise yesterday, then stopped completely this morning.",
        follow_up_required=False,
        mileage_in=23100,
        mileage_out=23100,
        condition_notes_in="No visible damage. Clean vehicle.",
        checked_in_by="seppi",
        checked_in_at=datetime(2026, 2, 1, 9, 45, tzinfo=timezone.utc),
        warranty_months=12,
        warranty_expires_at=date(2027, 2, 1),
        warranty_terms="Water pump + installation. 12 months parts + labor.",
    )

    # Job 4: Sophie's pending quote (waiting for approval)
    sophie_inspection = CamperServiceJobModel(
        job_number="JOB-20260213-0001",
        title="Full gas system inspection + certification",
        description="Customer concerned about gas system safety. Full inspection required "
                    "for Italian camping regulations. Includes leak test, regulator check, "
                    "hose condition assessment.",
        vehicle_id=sophie_hymer.id,
        customer_id=sophie_dupont.id,
        job_type=JobType.GAS_SYSTEM,
        status=JobStatus.QUOTED,
        assigned_to=None,
        estimated_hours=5,
        estimated_parts_cost=Decimal("80.00"),
        estimated_total=Decimal("255.00"),
        quote_valid_until=date(2026, 2, 28),
        scheduled_date=date(2026, 2, 20),
        customer_notes="Je suis inquiete pour le systeme de gaz. Il y a une odeur parfois. "
                       "(I'm worried about the gas system. There's a smell sometimes.)",
        follow_up_required=False,
    )

    # Job 5: Pending electrical quote for MAX (Angel's second job)
    max_electrical = CamperServiceJobModel(
        job_number="JOB-20260213-0002",
        title="Solar panel installation + battery upgrade",
        description="Install 200W solar panel on roof. Upgrade to LiFePO4 battery bank. "
                    "New MPPT charge controller. Full rewire of 12V system.",
        vehicle_id=max_camper.id,
        customer_id=angel.id,
        job_type=JobType.ELECTRICAL,
        status=JobStatus.QUOTED,
        assigned_to=None,
        estimated_hours=16,
        estimated_parts_cost=Decimal("1200.00"),
        estimated_total=Decimal("1760.00"),
        quote_valid_until=date(2026, 3, 15),
        scheduled_date=date(2026, 3, 1),
        customer_notes="Want to be self-sufficient for off-grid camping at Baglio Xiare. "
                       "Need enough power for laptop + router + lights.",
        follow_up_required=False,
    )

    # Job 6: Upcoming scheduled work (for calendar demo)
    upcoming_job = CamperServiceJobModel(
        job_number="JOB-20260214-0001",
        title="Brake system overhaul",
        description="Full brake system inspection and replacement. Pads, rotors, fluid.",
        vehicle_id=marco_ducato.id,
        customer_id=marco_rossi.id,
        job_type=JobType.REPAIR,
        status=JobStatus.APPROVED,
        assigned_to="Maximo",
        bay_id=bay_1.id,
        estimated_hours=6,
        estimated_parts_cost=Decimal("350.00"),
        estimated_total=Decimal("560.00"),
        estimated_days=2,
        start_date=date.today() + timedelta(days=3),
        end_date=date.today() + timedelta(days=4),
        scheduled_date=date.today() + timedelta(days=3),
        deposit_required=Decimal("140.00"),
        deposit_paid=Decimal("140.00"),
        deposit_paid_at=datetime.now(timezone.utc),
    )

    db.add_all([max_seal_job, marco_service, hans_plumbing, sophie_inspection, max_electrical, upcoming_job])
    await db.flush()

    # ================================================================
    # WORK LOGS (v3 - audit trail)
    # ================================================================

    # MAX seal job work logs
    db.add_all([
        CamperWorkLogModel(
            job_id=max_seal_job.id,
            bay_id=bay_bodywork.id,
            log_type=LogType.WORK,
            hours=4.0,
            notes="Removed interior ceiling panels. Photographed extent of water damage.",
            logged_by="sebastino",
            logged_at=datetime(2026, 2, 6, 13, 0, tzinfo=timezone.utc),
        ),
        CamperWorkLogModel(
            job_id=max_seal_job.id,
            bay_id=bay_bodywork.id,
            log_type=LogType.WORK,
            hours=6.0,
            notes="Full strip-out of damaged insulation. Assessed structural integrity of roof frame.",
            logged_by="sebastino",
            logged_at=datetime(2026, 2, 7, 17, 0, tzinfo=timezone.utc),
        ),
        CamperWorkLogModel(
            job_id=max_seal_job.id,
            bay_id=bay_bodywork.id,
            log_type=LogType.WORK,
            hours=3.0,
            notes="Measured replacement panels. Prepared purchase order for Fiamma seals.",
            logged_by="sebastino",
            logged_at=datetime(2026, 2, 10, 12, 0, tzinfo=timezone.utc),
        ),
        CamperWorkLogModel(
            job_id=max_seal_job.id,
            bay_id=bay_bodywork.id,
            log_type=LogType.WORK,
            hours=3.0,
            notes="Treated exposed wood frame with anti-fungal. Prepared mounting surfaces.",
            logged_by="sebastino",
            logged_at=datetime(2026, 2, 11, 16, 0, tzinfo=timezone.utc),
        ),
        CamperWorkLogModel(
            job_id=max_seal_job.id,
            bay_id=bay_bodywork.id,
            log_type=LogType.WAIT_START,
            notes="In attesa: Waiting for Dometic window seals (shipping from Germany)",
            wait_reason="Waiting for Dometic window seals (shipping from Germany)",
            logged_by="nino",
            logged_at=datetime(2026, 2, 12, 9, 0, tzinfo=timezone.utc),
        ),
        # Hans plumbing work log
        CamperWorkLogModel(
            job_id=hans_plumbing.id,
            bay_id=bay_1.id,
            log_type=LogType.WORK,
            hours=2.5,
            notes="Replaced Shurflo pump with Fiamma Aqua 8. Tested all connections. No leaks.",
            logged_by="seppi",
            logged_at=datetime(2026, 2, 1, 12, 30, tzinfo=timezone.utc),
        ),
        # Marco annual service work log
        CamperWorkLogModel(
            job_id=marco_service.id,
            bay_id=bay_2.id,
            log_type=LogType.WORK,
            hours=3.5,
            notes="Oil change, filter replacement, front brake pad replacement, tire rotation, fluid top-up.",
            logged_by="maximo",
            logged_at=datetime(2026, 1, 20, 12, 0, tzinfo=timezone.utc),
        ),
    ])
    await db.flush()

    # ================================================================
    # QUOTATIONS (v2)
    # ================================================================

    # Accepted quotation for MAX seal repair
    max_quotation = CamperQuotationModel(
        quote_number="QUO-20260206-0001",
        job_id=max_seal_job.id,
        customer_id=angel.id,
        vehicle_id=max_camper.id,
        line_items=[
            {"description": "Roof panel removal + inspection", "quantity": 8, "unit_price": 35.0, "line_total": 280.0, "item_type": "labor"},
            {"description": "Seal replacement (3 windows)", "quantity": 12, "unit_price": 35.0, "line_total": 420.0, "item_type": "labor"},
            {"description": "Structural repair + waterproofing", "quantity": 40, "unit_price": 35.0, "line_total": 1400.0, "item_type": "labor"},
            {"description": "Window seals (3x Dometic)", "quantity": 3, "unit_price": 85.0, "line_total": 255.0, "item_type": "parts"},
            {"description": "Roof panels (marine-grade plywood)", "quantity": 6, "unit_price": 120.0, "line_total": 720.0, "item_type": "materials"},
            {"description": "Waterproof membrane + sealant", "quantity": 1, "unit_price": 180.0, "line_total": 180.0, "item_type": "materials"},
            {"description": "Ceiling panels (replacement)", "quantity": 4, "unit_price": 95.0, "line_total": 380.0, "item_type": "materials"},
        ],
        subtotal=Decimal("3635.00"),
        vat_rate=Decimal("22.00"),
        vat_amount=Decimal("799.70"),
        total=Decimal("4434.70"),
        deposit_percent=Decimal("25.00"),
        deposit_amount=Decimal("1108.68"),
        valid_until=date(2026, 3, 6),
        status=QuotationStatus.ACCEPTED,
        sent_at=datetime(2026, 2, 6, 14, 0, tzinfo=timezone.utc),
        accepted_at=datetime(2026, 2, 7, 9, 0, tzinfo=timezone.utc),
        notes="Comprehensive repair. Estimate may increase if hidden damage found behind panels.",
        created_by="nino",
    )

    # Pending quotation for Sophie's gas inspection
    sophie_quotation = CamperQuotationModel(
        quote_number="QUO-20260213-0001",
        job_id=sophie_inspection.id,
        customer_id=sophie_dupont.id,
        vehicle_id=sophie_hymer.id,
        line_items=[
            {"description": "Gas system visual inspection", "quantity": 1, "unit_price": 35.0, "line_total": 35.0, "item_type": "labor"},
            {"description": "Pressure test (leak detection)", "quantity": 2, "unit_price": 35.0, "line_total": 70.0, "item_type": "labor"},
            {"description": "Regulator function test", "quantity": 1, "unit_price": 35.0, "line_total": 35.0, "item_type": "labor"},
            {"description": "Certification report", "quantity": 1, "unit_price": 35.0, "line_total": 35.0, "item_type": "labor"},
            {"description": "Leak detection spray", "quantity": 1, "unit_price": 15.0, "line_total": 15.0, "item_type": "materials"},
            {"description": "Replacement hose (if needed)", "quantity": 1, "unit_price": 45.0, "line_total": 45.0, "item_type": "parts"},
        ],
        subtotal=Decimal("235.00"),
        vat_rate=Decimal("22.00"),
        vat_amount=Decimal("51.70"),
        total=Decimal("286.70"),
        deposit_percent=Decimal("25.00"),
        deposit_amount=Decimal("71.68"),
        valid_until=date(2026, 2, 28),
        status=QuotationStatus.SENT,
        sent_at=datetime(2026, 2, 13, 16, 0, tzinfo=timezone.utc),
        notes="Includes certification for Italian camping regulations.",
        created_by="nino",
    )

    db.add_all([max_quotation, sophie_quotation])
    await db.flush()

    # ================================================================
    # PURCHASE ORDERS (v2)
    # ================================================================

    # PO for MAX roof materials (in transit)
    max_po = CamperPurchaseOrderModel(
        po_number="PO-20260210-0001",
        job_id=max_seal_job.id,
        supplier_name="Fiamma S.p.A.",
        supplier_contact="Vendite Italia",
        supplier_email="vendite@fiamma.it",
        supplier_phone="+39 049 820 1166",
        line_items=[
            {"description": "Dometic window seal S4 76x46cm", "part_number": "DOM-S4-7646", "quantity": 3, "unit_price": 85.0, "line_total": 255.0},
            {"description": "Sikaflex 252i sealant (white)", "part_number": "SIKA-252I-W", "quantity": 4, "unit_price": 18.0, "line_total": 72.0},
            {"description": "Butyl tape 10m roll", "part_number": "BUT-10M", "quantity": 2, "unit_price": 12.0, "line_total": 24.0},
        ],
        subtotal=Decimal("351.00"),
        vat_rate=Decimal("22.00"),
        vat_amount=Decimal("77.22"),
        total=Decimal("428.22"),
        status=CamperPOStatus.SHIPPED,
        expected_delivery=date(2026, 2, 18),
        tracking_number="FI-2026-89234",
        notes="Express shipping requested. Should arrive by Tuesday.",
        created_by="nino",
    )

    # PO for Marco's brake parts (received)
    marco_po = CamperPurchaseOrderModel(
        po_number="PO-20260118-0001",
        job_id=marco_service.id,
        supplier_name="Autoricambi Ferrara",
        supplier_contact="Giovanni",
        supplier_phone="+39 0923 123456",
        line_items=[
            {"description": "Oil filter Fiat Ducato 2.3L", "part_number": "MF-FD23-OF", "quantity": 1, "unit_price": 12.0, "line_total": 12.0},
            {"description": "Air filter Fiat Ducato 2.3L", "part_number": "MF-FD23-AF", "quantity": 1, "unit_price": 18.0, "line_total": 18.0},
            {"description": "Engine oil 5W-30 6L", "part_number": "EO-5W30-6L", "quantity": 1, "unit_price": 45.0, "line_total": 45.0},
            {"description": "Front brake pads (set)", "part_number": "BP-FD-FRONT", "quantity": 1, "unit_price": 40.0, "line_total": 40.0},
        ],
        subtotal=Decimal("115.00"),
        vat_rate=Decimal("22.00"),
        vat_amount=Decimal("25.30"),
        total=Decimal("140.30"),
        status=CamperPOStatus.RECEIVED,
        expected_delivery=date(2026, 1, 19),
        actual_delivery=date(2026, 1, 19),
        notes="Local supplier. Same-day delivery.",
        created_by="nino",
    )

    db.add_all([max_po, marco_po])
    await db.flush()

    # ================================================================
    # INVOICES (v2)
    # ================================================================

    # Invoice for Marco's completed job (paid)
    marco_invoice = CamperInvoiceModel(
        invoice_number="INV-20260120-0001",
        job_id=marco_service.id,
        customer_id=marco_rossi.id,
        quotation_id=None,
        line_items=[
            {"description": "Annual maintenance labor", "quantity": 3.5, "unit_price": 35.0, "line_total": 122.5, "item_type": "labor"},
            {"description": "Oil filter", "quantity": 1, "unit_price": 12.0, "line_total": 12.0, "item_type": "parts"},
            {"description": "Air filter", "quantity": 1, "unit_price": 18.0, "line_total": 18.0, "item_type": "parts"},
            {"description": "Engine oil 5W-30 6L", "quantity": 1, "unit_price": 45.0, "line_total": 45.0, "item_type": "parts"},
            {"description": "Front brake pads (set)", "quantity": 1, "unit_price": 40.0, "line_total": 40.0, "item_type": "parts"},
        ],
        subtotal=Decimal("237.50"),
        vat_rate=Decimal("22.00"),
        vat_amount=Decimal("52.25"),
        total=Decimal("289.75"),
        deposit_applied=Decimal("65.00"),
        amount_due=Decimal("224.75"),
        payment_status=PaymentStatus.PAID,
        payment_method="card",
        paid_at=datetime(2026, 1, 20, 16, 30, tzinfo=timezone.utc),
        due_date=date(2026, 2, 3),
        notes="Annual service invoice. Payment received at pickup.",
        created_by="nino",
    )

    db.add(marco_invoice)
    await db.flush()

    # ================================================================
    # SHARED RESOURCES (v4 - hoist management)
    # ================================================================
    main_hoist = CamperSharedResourceModel(
        name="Ponte Sollevatore",
        resource_type=ResourceType.HOIST,
        description="Main vehicle hoist - full undercarriage access. Only 1 vehicle at a time.",
    )
    db.add(main_hoist)
    await db.flush()

    # Booking 1: MAX seal job needs hoist (IN_USE, Feb 6-8)
    db.add(CamperResourceBookingModel(
        resource_id=main_hoist.id,
        job_id=max_seal_job.id,
        start_date=date(2026, 2, 6),
        end_date=date(2026, 2, 8),
        status=BookingStatus.IN_USE,
        notes="Full undercarriage access for seal inspection and roof panel removal",
        booked_by="sebastino",
    ))

    # Booking 2: Hans VW scheduled for hoist (SCHEDULED, Feb 10)
    db.add(CamperResourceBookingModel(
        resource_id=main_hoist.id,
        job_id=hans_plumbing.id,
        start_date=date(2026, 2, 10),
        end_date=date(2026, 2, 10),
        status=BookingStatus.SCHEDULED,
        notes="Quick undercarriage check after plumbing work",
        booked_by="nino",
    ))

    # ================================================================
    # APPOINTMENTS (v5 - appointment book + walk-in queue)
    # ================================================================
    today = date.today()
    tomorrow = today + timedelta(days=1)

    # Today's booked appointment: Sophie coming back to discuss the quote
    db.add(CamperAppointmentModel(
        customer_name="Sophie Dupont",
        customer_phone="+33 6 55 66 77 88",
        vehicle_plate="AB 123 CD",
        appointment_type=AppointmentType.BOOKED,
        priority=AppointmentPriority.NORMAL,
        status=AppointmentStatus.SCHEDULED,
        scheduled_date=today,
        scheduled_time=time(10, 30),
        estimated_duration_minutes=30,
        description="Discuss gas inspection quotation. Customer wants to understand the process.",
        notes="Speaks French only. Have Google Translate ready.",
        created_by="nino",
    ))

    # Today's walk-in: unknown customer with flat tire
    db.add(CamperAppointmentModel(
        customer_name="Tourist (walk-in)",
        vehicle_plate="NA 456 AB",
        appointment_type=AppointmentType.WALK_IN,
        priority=AppointmentPriority.URGENT,
        status=AppointmentStatus.IN_SERVICE,
        scheduled_date=today,
        estimated_duration_minutes=60,
        description="Flat tire on camper. Needs replacement ASAP -- leaving Trapani tomorrow.",
        created_by="nino",
    ))

    # Tomorrow's appointment: Marco brake overhaul drop-off
    db.add(CamperAppointmentModel(
        customer_name="Marco Rossi",
        customer_phone="+39 328 111 2222",
        vehicle_plate="TP 987654",
        appointment_type=AppointmentType.BOOKED,
        priority=AppointmentPriority.NORMAL,
        status=AppointmentStatus.SCHEDULED,
        scheduled_date=tomorrow,
        scheduled_time=time(8, 30),
        estimated_duration_minutes=20,
        description="Drop off Ducato for brake system overhaul. Approved job JOB-20260214-0001.",
        notes="Morning guy -- always early. Have paperwork ready.",
        created_by="nino",
    ))

    # Next week: Angel picking up MAX (optimistic)
    db.add(CamperAppointmentModel(
        customer_name="Angelo Kenel",
        customer_phone="+41 79 000 0000",
        vehicle_plate="TI 123456",
        appointment_type=AppointmentType.BOOKED,
        priority=AppointmentPriority.NORMAL,
        status=AppointmentStatus.SCHEDULED,
        scheduled_date=today + timedelta(days=7),
        scheduled_time=time(14, 0),
        estimated_duration_minutes=45,
        description="Check progress on MAX roof repair. Review next phases.",
        notes="VIP customer. Building our software. Show him the system!",
        created_by="nino",
    ))

    # ================================================================
    # SUPPLIER DIRECTORY (v5)
    # ================================================================
    db.add_all([
        CamperSupplierModel(
            name="Autoricambi Ferrara",
            contact_person="Giovanni",
            phone="+39 0923 123456",
            address="Via Fardella 120",
            city="Trapani",
            specialty="General parts, filters, brakes, oil",
            lead_time_days=0,
            is_preferred=True,
            notes="Walking distance. Same-day delivery for most parts. Good prices.",
        ),
        CamperSupplierModel(
            name="Fiamma S.p.A.",
            contact_person="Vendite Italia",
            phone="+39 049 820 1166",
            email="vendite@fiamma.it",
            address="Via San Giacomo 7",
            city="Cardano al Campo (VA)",
            specialty="Camper accessories, seals, windows, awnings",
            lead_time_days=5,
            is_preferred=True,
            notes="Main camper parts supplier. Good quality. 5 business day delivery to Sicily.",
        ),
        CamperSupplierModel(
            name="Palermo Seals & Gaskets",
            contact_person="Salvatore",
            phone="+39 091 555 6789",
            city="Palermo",
            specialty="Seals, gaskets, rubber parts, waterproofing",
            lead_time_days=2,
            is_preferred=False,
            notes="Ad-hoc supplier. That guy in Palermo who has everything. Cash only.",
        ),
        CamperSupplierModel(
            name="Dometic Italia",
            contact_person="Servizio Clienti",
            phone="+39 02 123 4567",
            email="ordini@dometic.it",
            city="Milano",
            specialty="Fridges, air conditioning, windows, marine/camper systems",
            lead_time_days=7,
            is_preferred=True,
            notes="OEM parts for Dometic systems. Order online, good warranty.",
        ),
    ])

    # ================================================================
    # HANS INVOICE (overdue! -- good demo for alerts)
    # ================================================================
    hans_invoice = CamperInvoiceModel(
        invoice_number="INV-20260201-0001",
        job_id=hans_plumbing.id,
        customer_id=hans_mueller.id,
        quotation_id=None,
        line_items=[
            {"description": "Emergency plumbing labor", "quantity": 2.5, "unit_price": 35.0, "line_total": 87.5, "item_type": "labor"},
            {"description": "Fiamma Aqua 8 water pump", "quantity": 1, "unit_price": 135.0, "line_total": 135.0, "item_type": "parts"},
            {"description": "Hose clamps + fittings", "quantity": 1, "unit_price": 30.0, "line_total": 30.0, "item_type": "parts"},
        ],
        subtotal=Decimal("252.50"),
        vat_rate=Decimal("22.00"),
        vat_amount=Decimal("55.55"),
        total=Decimal("308.05"),
        deposit_applied=Decimal("0.00"),
        amount_due=Decimal("308.05"),
        payment_status=PaymentStatus.PENDING,
        due_date=date(2026, 2, 8),  # Past due!
        notes="Emergency repair. Tourist left without paying -- sent invoice by email. Follow up!",
        created_by="nino",
    )
    db.add(hans_invoice)

    await db.commit()

    logger.info("Camper & Tour seeding completed! (v5 - full demo prep)")
    logger.info("  - 4 customers (Angel, Marco, Hans, Sophie) + preferences + internal notes")
    logger.info("  - 4 vehicles (MAX, Ducato Maxi, California, Eriba) + check-in data")
    logger.info("  - 5 service bays (Bay 1, Bay 2, Electrical, Bodywork, Wash)")
    logger.info("  - 6 service jobs (with bay assignments + start/end dates + warranty):")
    logger.info("    - MAX roof seal (IN_PROGRESS, Bodywork Bay, waiting for parts)")
    logger.info("    - Marco annual service (INVOICED, Bay 2, warranty 6mo)")
    logger.info("    - Hans plumbing emergency (COMPLETED, warranty 12mo)")
    logger.info("    - Sophie gas inspection (QUOTED)")
    logger.info("    - MAX solar install (QUOTED)")
    logger.info("    - Marco brake overhaul (APPROVED, Bay 1, scheduled)")
    logger.info("  - 7 work logs (audit trail for MAX, Hans, Marco)")
    logger.info("  - 2 quotations (1 accepted, 1 sent)")
    logger.info("  - 2 purchase orders (1 shipped, 1 received)")
    logger.info("  - 2 invoices (Marco=paid, Hans=OVERDUE since Feb 8!)")
    logger.info("  - 1 shared resource (Ponte Sollevatore / Main Hoist)")
    logger.info("  - 2 hoist bookings (1 IN_USE for MAX, 1 SCHEDULED for Hans)")
    logger.info("  - 4 appointments (Sophie today, walk-in today, Marco tomorrow, Angel next week)")
    logger.info("  - 4 suppliers (Ferrara local, Fiamma, Palermo seals, Dometic)")

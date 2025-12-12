#!/usr/bin/env python3
"""
Seed Equipment Demo Data

Felix needs a centrifuge. 50,000 CHF.
Do we buy, lease, or rent?

This script creates:
1. Equipment suppliers (JURA, Borris Custom, Japan Imports)
2. Equipment (JURA COOLIE, Salad Bar, Centrifuge)
3. An acquisition request for Felix's centrifuge
4. A complete PO → Shipment → Customs → Equipment flow

"I can handle it. Found the part. Hard to find." - SAL
"""
import asyncio
import uuid
from datetime import date, datetime, timezone, timedelta

# Add parent to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.db.models import (
    EquipmentSupplierModel, SupplierType,
    EquipmentModel, EquipmentType, EquipmentStatus,
    PurchaseOrderModel, POStatus,
    ShipmentModel, ShipmentType, ShipmentStatus,
    CustomsClearanceModel, CustomsStatus,
    MaintenanceEventModel, MaintenanceType, MaintenanceStatus,
    EquipmentAcquisitionModel, AcquisitionType, AcquisitionStatus, UrgencyLevel,
    FarmModel, FarmType,
)


async def seed_equipment_data():
    """Seed the equipment supply chain with demo data"""

    # Get database URL from environment or use default
    import os
    db_url = os.environ.get(
        'ASYNC_DATABASE_URL',
        'postgresql+asyncpg://helix_user:helix_pass@postgres:5432/helix_db'
    )

    engine = create_async_engine(db_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("\n" + "="*60)
        print("🏭 SEEDING EQUIPMENT SUPPLY CHAIN DATA")
        print("="*60)

        # ================================================
        # 1. CREATE SUPPLIERS
        # ================================================
        print("\n📦 Creating Suppliers...")

        # JURA - Swiss coffee machines
        # Note: Using raw SQL to insert since model/DB schema mismatch
        from sqlalchemy import text
        await session.execute(text("""
            INSERT INTO equipment_suppliers
            (id, code, name, supplier_type, country, city, address, postal_code,
             primary_contact, email, phone, website, specialties, product_lines,
             currency, payment_terms, lead_time_days, ships_to_europe, rating, is_active, notes)
            VALUES
            (gen_random_uuid(), 'JURA-CH', 'JURA Elektroapparate AG', 'manufacturer',
             'Switzerland', 'Niederbuchsiten', 'Kaffeeweltstrasse 10', '4626',
             'Sales Team', 'professional@jura.com', '+41 62 389 82 33', 'https://www.jura.com',
             'Professional coffee machines, COOLIE hybrid system', 'GIGA, Z-Line, WE-Line, Professional',
             'CHF', 'Net 30', 14, true, 4.9, true,
             'The COOLIE - 3 months development, 500 slides, Japan craft precision')
        """))

        await session.execute(text("""
            INSERT INTO equipment_suppliers
            (id, code, name, supplier_type, country, city, address, postal_code,
             primary_contact, email, phone, specialties, product_lines,
             currency, payment_terms, lead_time_days, ships_to_europe, can_consolidate, rating, is_active, notes)
            VALUES
            (gen_random_uuid(), 'BORRIS-CH', 'Borris Custom Fabrication', 'fabricator',
             'Switzerland', 'Luzern', 'Industriestrasse 42', '6003',
             'Borris', 'borris@custom-fab.ch', '+41 41 555 1234',
             'Custom salad bars, refrigerated displays, CBD dispensers', 'Salad Bar Pro, Mobile Station',
             'CHF', '50% upfront, 50% on delivery', 45, true, true, 4.8, true,
             'Borris builds what nobody else can. The Lions vision realized.')
        """))

        await session.execute(text("""
            INSERT INTO equipment_suppliers
            (id, code, name, supplier_type, country, city, address, postal_code,
             primary_contact, email, phone, website, specialties, product_lines,
             currency, payment_terms, lead_time_days, ships_to_europe, preferred_carrier, can_consolidate, rating, is_active, notes)
            VALUES
            (gen_random_uuid(), 'MOSEY-JP', 'Mosey Scientific Instruments', 'distributor',
             'Japan', 'Yokohama', 'Minato Mirai 2-3-1', '220-0012',
             'YUKI', 'yuki@mosey-scientific.jp', '+81 45 555 7890', 'https://mosey-scientific.jp',
             'Lab centrifuges, testing equipment, precision instruments', 'Hettich, Eppendorf, Beckman Coulter',
             'JPY', 'Letter of Credit', 60, true, 'Maersk', true, 4.7, true,
             'YUKI handles all shipments. She rides WITH the equipment.')
        """))

        # Get supplier IDs for later use
        result = await session.execute(text("SELECT id, code FROM equipment_suppliers"))
        suppliers = {row[1]: row[0] for row in result.fetchall()}
        jura_id = suppliers.get('JURA-CH')
        borris_id = suppliers.get('BORRIS-CH')
        mosey_id = suppliers.get('MOSEY-JP')

        await session.flush()
        print(f"  ✓ Created JURA: JURA-CH")
        print(f"  ✓ Created Borris Custom: BORRIS-CH")
        print(f"  ✓ Created Mosey Scientific: MOSEY-JP")

        # ================================================
        # 2. CREATE FELIX'S CENTRIFUGE ACQUISITION REQUEST
        # ================================================
        print("\n🔬 Creating Felix's Centrifuge Acquisition Request...")

        centrifuge_acq = EquipmentAcquisitionModel(
            id=uuid.uuid4(),
            request_number="ACQ-2025-FELIX-001",
            equipment_type="centrifuge",
            equipment_name="Hettich ROTINA 380 R Centrifuge",
            description="""
            Felix needs a refrigerated centrifuge for lab testing of food batches.
            Critical for:
            - Contamination testing (bacterial separation)
            - Quality grading (sediment analysis)
            - Freshness verification (cell integrity)

            Current situation: Sending samples to external lab (2-day delay, 150 CHF/test)
            With own centrifuge: Same-day results, ~10 CHF/test

            ROI: 100+ tests/month = 14,000 CHF savings/month
            Payback: ~4 months
            """.strip(),
            requested_by="Felix",
            requested_date=date.today(),
            department="Lab",
            urgency=UrgencyLevel.HIGH,
            needed_by=date.today() + timedelta(days=45),
            destination_type="lab",
            destination_name="Felix's Lab - Artemis",

            # Options we're evaluating
            buy_options=[
                {
                    "vendor": "Mosey Scientific",
                    "model": "Hettich ROTINA 380 R",
                    "price": 48500,
                    "currency": "CHF",
                    "warranty_years": 2,
                    "notes": "German engineering, Japanese service"
                },
                {
                    "vendor": "Direct from Hettich",
                    "model": "Hettich ROTINA 380 R",
                    "price": 52000,
                    "currency": "CHF",
                    "warranty_years": 3,
                    "notes": "Direct, longer warranty, slower delivery"
                }
            ],
            lease_options=[
                {
                    "vendor": "MedEquip Leasing AG",
                    "model": "Hettich ROTINA 380 R",
                    "monthly": 1200,
                    "duration_months": 48,
                    "buyout_price": 8000,
                    "includes_maintenance": True,
                    "total_cost": 65600,
                    "notes": "Includes annual service"
                }
            ],
            rent_options=[
                {
                    "vendor": "LabRent CH",
                    "model": "Equivalent Eppendorf",
                    "daily_rate": 150,
                    "weekly_rate": 800,
                    "monthly_rate": 2500,
                    "notes": "Short-term only, older model"
                }
            ],

            # Cost estimates
            estimated_annual_maintenance=1500,
            estimated_consumables_yearly=500,
            estimated_energy_yearly=800,
            currency="CHF",

            # Business case
            revenue_impact="Enables in-house testing, faster batch approval, more throughput",
            productivity_gain="2-day testing delay eliminated, Felix can do 10x more tests",
            risk_if_not_acquired="Continue external lab dependency, slower TTM, higher per-test cost",
            alternatives_considered="Continue external lab (status quo), partner with university lab",

            # Approval
            requires_board_approval=True,  # Over 10K CHF
            status=AcquisitionStatus.EVALUATING,

            notes="Felix's priority. This unlocks the whole lab testing capability."
        )
        session.add(centrifuge_acq)
        print(f"  ✓ Created acquisition request: {centrifuge_acq.request_number}")

        # ================================================
        # 3. CREATE EXISTING EQUIPMENT
        # ================================================
        print("\n☕ Creating Existing Equipment...")

        # The COOLIE - JURA coffee machine (already installed)
        coolie = EquipmentModel(
            id=uuid.uuid4(),
            asset_tag="COOLIE-001",
            serial_number="JURA-COOLIE-7749",
            equipment_type=EquipmentType.COFFEE_STATION,
            name="JURA COOLIE Hybrid",
            description="""
            The COOLIE - SAL's pride and joy.
            3 months development, 500 slides, Japan craft precision.
            Fresh bean OR Nespresso compatible.
            "I can handle it. Found the part. Hard to find."
            """.strip(),
            manufacturer="JURA",
            model="COOLIE Hybrid (Custom)",
            model_year=2025,
            supplier_id=jura_id,
            supplier_name="JURA Elektroapparate AG",
            location_type="bar",
            location_name="HAIRY FISH - Main Counter",
            location_zone="Coffee Station Alpha",
            status=EquipmentStatus.OPERATIONAL,
            ordered_date=date(2024, 9, 1),
            received_date=date(2024, 12, 1),
            installed_date=date(2024, 12, 5),
            warranty_end_date=date(2026, 12, 5),
            expected_lifetime_years=10,
            purchase_price=15000,
            current_value=14000,
            currency="CHF",
            power_requirements="220V, 2200W",
            water_requirements="Direct plumb or 2.5L tank",
            dimensions="37 x 50 x 44 cm",
            weight_kg=14.5,
            maintenance_schedule="Monthly descaling, annual service",
            last_maintenance=date(2025, 11, 15),
            next_maintenance=date(2025, 12, 15),
            nespresso_compatible=True,
            fresh_bean_grinder=True,
            water_tank_liters=2.5,
            bean_hopper_kg=0.5,
            assigned_to="SAL",
            responsible_team="Bar Operations",
            notes="The heart of HAIRY FISH. SAL's baby. Don't touch without asking."
        )
        session.add(coolie)

        # Salad Bar - Custom built by Borris
        salad_bar = EquipmentModel(
            id=uuid.uuid4(),
            asset_tag="SALAD-001",
            serial_number="BORRIS-SB-2025-001",
            equipment_type=EquipmentType.SALAD_BAR,
            name="Tony Boz CBD Salad Bar",
            description="""
            The full service salad bar. Borris custom build.
            - 8 compartments for fresh ingredients
            - 4 CBD dressing dispensers
            - Refrigerated base (2-8°C)
            - Sneeze guard with LED lighting
            - Refillable bottle station
            """.strip(),
            manufacturer="Borris Custom Fabrication",
            model="Salad Bar Pro - CBD Edition",
            model_year=2025,
            supplier_id=borris_id,
            supplier_name="Borris Custom Fabrication",
            location_type="bar",
            location_name="Mosey 420",
            location_zone="Salad Station",
            status=EquipmentStatus.OPERATIONAL,
            ordered_date=date(2025, 1, 15),
            received_date=date(2025, 3, 1),
            installed_date=date(2025, 3, 5),
            warranty_end_date=date(2027, 3, 5),
            expected_lifetime_years=15,
            purchase_price=25000,
            current_value=24000,
            currency="CHF",
            power_requirements="220V, 800W",
            dimensions="200 x 80 x 120 cm",
            weight_kg=180,
            maintenance_schedule="Daily cleaning, weekly deep clean, annual compressor service",
            last_maintenance=date(2025, 12, 1),
            next_maintenance=date(2026, 1, 1),
            compartment_count=8,
            refrigerated=True,
            sneeze_guard=True,
            cbd_dispenser_count=4,
            assigned_to="Molly",
            responsible_team="Kitchen Operations",
            notes="The Lion's Vision realized. 7 days/week, 4am to 2am."
        )
        session.add(salad_bar)

        await session.flush()
        print(f"  ✓ Created COOLIE: {coolie.asset_tag}")
        print(f"  ✓ Created Salad Bar: {salad_bar.asset_tag}")

        # ================================================
        # 4. CREATE A COMPLETE IMPORT FLOW (PO → SHIPMENT → CUSTOMS)
        # ================================================
        print("\n🚢 Creating Import Flow (YUKI's Domain)...")

        # Purchase Order for lab equipment
        po = PurchaseOrderModel(
            id=uuid.uuid4(),
            po_number="PO-2025-MOSEY-003",
            supplier_id=mosey_id,
            supplier_name="Mosey Scientific Instruments",
            requested_by="Felix",
            requested_date=date(2025, 10, 15),
            destination_type="lab",
            destination_name="Felix's Lab - Artemis",
            line_items=[
                {
                    "line": 1,
                    "sku": "HET-R380R",
                    "description": "Hettich ROTINA 380 R Centrifuge",
                    "quantity": 1,
                    "unit_price": 48500,
                    "currency": "CHF"
                },
                {
                    "line": 2,
                    "sku": "HET-R380R-ROTOR",
                    "description": "Extra rotor - 24x15ml",
                    "quantity": 2,
                    "unit_price": 1200,
                    "currency": "CHF"
                },
                {
                    "line": 3,
                    "sku": "HET-TUBES-1000",
                    "description": "Centrifuge tubes 15ml (1000 pack)",
                    "quantity": 5,
                    "unit_price": 150,
                    "currency": "CHF"
                }
            ],
            items_count=3,
            subtotal=51650,
            shipping_cost=1500,
            duties_estimate=4200,
            total=57350,
            currency="CHF",
            status=POStatus.SHIPPED,
            expected_ship_date=date(2025, 11, 1),
            expected_delivery_date=date(2025, 12, 20),
            actual_ship_date=date(2025, 11, 3),
            preferred_shipment_type="container_20ft",
            consolidate_with_po="PO-2025-MOSEY-001",
            items_shipped=3,
            notes="Felix says add these 2-3 items to Mosey shipment",
            internal_notes="YUKI handling this one. Container MSCU-7749-COOLIE"
        )
        session.add(po)

        # Customs Clearance
        customs = CustomsClearanceModel(
            id=uuid.uuid4(),
            clearance_number="CC-2025-ROT-1247",
            port_of_entry="Rotterdam",
            customs_office="Rotterdam Europoort",
            customs_agent="Ka-Maki",
            agent_company="Ka-Maki Customs Services",
            agent_contact="kamaki@customs.ch",
            status=CustomsStatus.DUTIES_CALCULATED,
            documents={
                "commercial_invoice": {"number": "INV-2025-MOSEY-003", "status": "verified"},
                "packing_list": {"number": "PL-2025-003", "status": "verified"},
                "bill_of_lading": {"number": "MAEU-789456123", "status": "verified"},
                "certificate_of_origin": {"number": "CO-JP-2025-4567", "status": "verified"}
            },
            documents_complete=True,
            hs_codes="8421.19.00, 3926.90.97",
            duties_calculated=True,
            import_duty=3850,
            vat=398,
            other_fees=150,
            total_duties=4398,
            currency="CHF",
            submitted_date=date(2025, 12, 1),
            processing_days=5,
            notes="COOLIE... you beautiful bastard. Your papers are TIGHT. - Charlie"
        )
        session.add(customs)

        # Shipment
        shipment = ShipmentModel(
            id=uuid.uuid4(),
            shipment_number="SHIP-2025-YC-047",
            shipment_type=ShipmentType.CONTAINER_20FT,
            container_number="MSCU-7749-COOLIE",
            container_size="20ft",
            seal_number="SEAL-JP-456789",
            carrier_name="Maersk",
            carrier_tracking="MAEU789456123",
            vessel_name="MSC AURORA",
            voyage_number="VA2511W",
            origin_country="Japan",
            origin_city="Yokohama",
            origin_port="Yokohama",
            destination_country="Switzerland",
            destination_city="Zurich",
            destination_port="Rotterdam",
            final_destination="Felix's Lab - Artemis, Luzern",
            status=ShipmentStatus.CUSTOMS_CLEARED,
            purchase_order_id=po.id,
            total_pieces=8,
            total_weight_kg=450,
            total_volume_cbm=3.5,
            declared_value=51650,
            currency="CHF",
            ship_date=date(2025, 11, 3),
            eta_port=date(2025, 12, 10),
            eta_destination=date(2025, 12, 15),
            actual_arrival_port=date(2025, 12, 8),
            requires_customs=True,
            customs_clearance_id=customs.id,
            is_fragile=True,
            temperature_controlled=False,
            is_insured=True,
            insurance_value=60000,
            handled_by="YUKI",
            passengers="CHARLIE",  # Hidden in container, shhh
            notes="We ride WITH the equipment. - YUKI"
        )
        session.add(shipment)

        # Update customs with shipment link
        customs.shipment_id = shipment.id
        customs.shipment_number = shipment.shipment_number

        await session.flush()
        print(f"  ✓ Created PO: {po.po_number}")
        print(f"  ✓ Created Customs Clearance: {customs.clearance_number}")
        print(f"  ✓ Created Shipment: {shipment.shipment_number}")

        # ================================================
        # 5. CREATE A MAINTENANCE EVENT
        # ================================================
        print("\n🔧 Creating Maintenance Event...")

        maintenance = MaintenanceEventModel(
            id=uuid.uuid4(),
            equipment_id=coolie.id,
            equipment_name="JURA COOLIE Hybrid",
            maintenance_type=MaintenanceType.PREVENTIVE,
            title="Monthly Descaling",
            description="Regular monthly descaling to maintain optimal performance",
            performed_by="Marco",
            scheduled_date=date(2025, 12, 15),
            status=MaintenanceStatus.SCHEDULED,
            parts_cost=25,
            labor_hours=0.5,
            labor_cost=50,
            total_cost=75,
            currency="CHF",
            downtime_hours=0.5,
            next_maintenance_date=date(2026, 1, 15),
            notes="Use JURA descaling tablets only. SAL is very particular."
        )
        session.add(maintenance)

        await session.flush()
        print(f"  ✓ Created Maintenance: {maintenance.title}")

        # ================================================
        # 6. CREATE MOLLY'S FARM
        # ================================================
        print("\n🌻 Creating Molly's Farm...")

        farm = FarmModel(
            id=uuid.uuid4(),
            code="MOLLY-FARM-01",
            name="Molly's Mountain Farm",
            farm_type=FarmType.MIXED,
            address="Bergstrasse 42",
            canton="LU",
            postal_code="6010",
            country="Switzerland",
            gps_latitude=47.0502,
            gps_longitude=8.3093,
            altitude_meters=850,
            hectares=12.5,
            owned_by="Molly's Family",
            managed_by="Molly",
            goats=15,
            bees_hives=8,
            chickens=25,
            cows=0,
            bio_certified=True,
            bio_cert_number="BIO-CH-2025-1234",
            bio_cert_expiry=date(2026, 12, 31),
            ip_suisse=True,
            swiss_gap=True,
            primary_contact="Molly",
            phone="+41 79 555 1234",
            email="molly@mountain-farm.ch",
            is_active=True,
            notes="""
            The source of everything. Seed to shit and back.
            - Goat milk for cheese and soap
            - Bees for honey and pollination
            - Chickens for eggs
            - Garden for vegetables and herbs
            - Brothers help with heavy lifting
            """.strip()
        )
        session.add(farm)

        await session.flush()
        print(f"  ✓ Created Farm: {farm.name}")

        # ================================================
        # COMMIT ALL
        # ================================================
        await session.commit()

        print("\n" + "="*60)
        print("✅ EQUIPMENT SUPPLY CHAIN DATA SEEDED SUCCESSFULLY")
        print("="*60)
        print(f"""
Summary:
  - 3 Suppliers (JURA, Borris, Mosey)
  - 2 Equipment (COOLIE, Salad Bar)
  - 1 Acquisition Request (Felix's Centrifuge - EVALUATING)
  - 1 Purchase Order (SHIPPED)
  - 1 Shipment (20ft container - CUSTOMS_CLEARED)
  - 1 Customs Clearance (Ka-Maki - DUTIES_CALCULATED)
  - 1 Maintenance Event (COOLIE descaling)
  - 1 Farm (Molly's Mountain Farm)

The stage is set. YUKI and CHARLIE are in Rotterdam.
The centrifuge is almost here.
Felix will have his lab.

🐅🦁🌻
        """)


if __name__ == "__main__":
    asyncio.run(seed_equipment_data())

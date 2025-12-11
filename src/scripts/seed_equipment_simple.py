#!/usr/bin/env python3
"""
Simple Equipment Seed Script - Direct SQL

Test data for the equipment supply chain.
"""
import asyncio
import os
from sqlalchemy import create_engine, text


def seed_equipment():
    """Seed equipment data using raw SQL"""

    db_url = os.environ.get(
        'SYNC_DATABASE_URL',
        'postgresql+psycopg://helix_user:helix_pass@postgres:5432/helix_db'
    )

    engine = create_engine(db_url)

    with engine.connect() as conn:
        print("\n" + "="*60)
        print("🏭 SEEDING EQUIPMENT DATA (Simple Mode)")
        print("="*60)

        # Check if data exists
        result = conn.execute(text("SELECT COUNT(*) FROM equipment_suppliers"))
        if result.scalar() > 0:
            print("⚠️  Suppliers already exist. Skipping.")
        else:
            # 1. CREATE SUPPLIERS
            print("\n📦 Creating Suppliers...")

            conn.execute(text("""
                INSERT INTO equipment_suppliers
                (id, code, name, supplier_type, country, city, address, postal_code,
                 primary_contact, email, phone, website, specialties, product_lines,
                 currency, payment_terms, lead_time_days, ships_to_europe, can_consolidate, rating, is_active, notes)
                VALUES
                (gen_random_uuid(), 'JURA-CH', 'JURA Elektroapparate AG', 'manufacturer',
                 'Switzerland', 'Niederbuchsiten', 'Kaffeeweltstrasse 10', '4626',
                 'Sales Team', 'professional@jura.com', '+41 62 389 82 33', 'https://www.jura.com',
                 'Professional coffee machines, COOLIE hybrid system', 'GIGA, Z-Line, Professional',
                 'CHF', 'Net 30', 14, true, false, 4.9, true,
                 'The COOLIE - 3 months dev, 500 slides, Japan craft')
            """))

            conn.execute(text("""
                INSERT INTO equipment_suppliers
                (id, code, name, supplier_type, country, city, address, postal_code,
                 primary_contact, email, phone, specialties, product_lines,
                 currency, payment_terms, lead_time_days, ships_to_europe, can_consolidate, rating, is_active, notes)
                VALUES
                (gen_random_uuid(), 'BORRIS-CH', 'Borris Custom Fabrication', 'fabricator',
                 'Switzerland', 'Luzern', 'Industriestrasse 42', '6003',
                 'Borris', 'borris@custom-fab.ch', '+41 41 555 1234',
                 'Custom salad bars, refrigerated displays, CBD dispensers', 'Salad Bar Pro',
                 'CHF', '50/50', 45, true, true, 4.8, true,
                 'Borris builds what nobody else can')
            """))

            conn.execute(text("""
                INSERT INTO equipment_suppliers
                (id, code, name, supplier_type, country, city, address, postal_code,
                 primary_contact, email, phone, website, specialties, product_lines,
                 currency, payment_terms, lead_time_days, ships_to_europe, preferred_carrier, can_consolidate, rating, is_active, notes)
                VALUES
                (gen_random_uuid(), 'MOSEY-JP', 'Mosey Scientific Instruments', 'distributor',
                 'Japan', 'Yokohama', 'Minato Mirai 2-3-1', '220-0012',
                 'YUKI', 'yuki@mosey-scientific.jp', '+81 45 555 7890', 'https://mosey-scientific.jp',
                 'Lab centrifuges, testing equipment', 'Hettich, Eppendorf',
                 'JPY', 'LC', 60, true, 'Maersk', true, 4.7, true,
                 'YUKI handles all shipments. Rides WITH the equipment.')
            """))

            print("  ✓ Created 3 suppliers")

        # 2. CREATE FARM
        result = conn.execute(text("SELECT COUNT(*) FROM farms"))
        if result.scalar() > 0:
            print("⚠️  Farms already exist. Skipping.")
        else:
            print("\n🌻 Creating Molly's Farm...")

            conn.execute(text("""
                INSERT INTO farms
                (id, code, name, farm_type, address, canton, postal_code, country,
                 gps_latitude, gps_longitude, altitude_meters, hectares,
                 owned_by, managed_by, goats, bees_hives, chickens, cows,
                 bio_certified, bio_cert_number, ip_suisse, demeter, swiss_gap,
                 primary_contact, phone, email, is_active, notes)
                VALUES
                (gen_random_uuid(), 'MOLLY-FARM-01', 'Mollys Mountain Farm', 'mixed',
                 'Bergstrasse 42', 'LU', '6010', 'Switzerland',
                 47.0502, 8.3093, 850, 12.5,
                 'Molly Family', 'Molly', 15, 8, 25, 0,
                 true, 'BIO-CH-2025-1234', true, false, true,
                 'Molly', '+41 79 555 1234', 'molly@mountain-farm.ch', true,
                 'The source of everything. Seed to shit and back.')
            """))
            print("  ✓ Created Molly's Farm")

        # 3. CREATE EQUIPMENT
        result = conn.execute(text("SELECT COUNT(*) FROM equipment"))
        if result.scalar() > 0:
            print("⚠️  Equipment already exists. Skipping.")
        else:
            print("\n☕ Creating Equipment...")

            # Get supplier IDs
            result = conn.execute(text("SELECT id, code FROM equipment_suppliers"))
            suppliers = {row[1]: row[0] for row in result.fetchall()}
            jura_id = suppliers.get('JURA-CH')
            borris_id = suppliers.get('BORRIS-CH')

            # COOLIE coffee machine
            conn.execute(text("""
                INSERT INTO equipment
                (id, asset_tag, serial_number, equipment_type, name, description,
                 manufacturer, model, model_year, supplier_id, supplier_name,
                 location_type, location_name, location_zone, status,
                 ordered_date, received_date, installed_date, warranty_end_date,
                 expected_lifetime_years, purchase_price, current_value, currency,
                 power_requirements, water_requirements, dimensions, weight_kg,
                 maintenance_schedule, nespresso_compatible, fresh_bean_grinder,
                 water_tank_liters, bean_hopper_kg, assigned_to, responsible_team, notes)
                VALUES
                (gen_random_uuid(), 'COOLIE-001', 'JURA-COOLIE-7749', 'coffee_station',
                 'JURA COOLIE Hybrid', 'SALs pride and joy. 3 months, 500 slides.',
                 'JURA', 'COOLIE Hybrid (Custom)', 2025, :jura_id, 'JURA Elektroapparate AG',
                 'bar', 'HAIRY FISH - Main Counter', 'Coffee Station Alpha', 'operational',
                 '2024-09-01', '2024-12-01', '2024-12-05', '2026-12-05',
                 10, 15000, 14000, 'CHF',
                 '220V, 2200W', 'Direct plumb or 2.5L tank', '37 x 50 x 44 cm', 14.5,
                 'Monthly descaling, annual service', true, true,
                 2.5, 0.5, 'SAL', 'Bar Operations', 'The heart of HAIRY FISH')
            """), {"jura_id": jura_id})

            # Salad Bar
            conn.execute(text("""
                INSERT INTO equipment
                (id, asset_tag, serial_number, equipment_type, name, description,
                 manufacturer, model, model_year, supplier_id, supplier_name,
                 location_type, location_name, location_zone, status,
                 ordered_date, received_date, installed_date, warranty_end_date,
                 expected_lifetime_years, purchase_price, current_value, currency,
                 power_requirements, dimensions, weight_kg,
                 maintenance_schedule, compartment_count, refrigerated, sneeze_guard,
                 cbd_dispenser_count, assigned_to, responsible_team, notes)
                VALUES
                (gen_random_uuid(), 'SALAD-001', 'BORRIS-SB-2025-001', 'salad_bar',
                 'Tony Boz CBD Salad Bar', 'Full service salad bar. Borris custom.',
                 'Borris Custom Fabrication', 'Salad Bar Pro - CBD Edition', 2025,
                 :borris_id, 'Borris Custom Fabrication',
                 'bar', 'Mosey 420', 'Salad Station', 'operational',
                 '2025-01-15', '2025-03-01', '2025-03-05', '2027-03-05',
                 15, 25000, 24000, 'CHF',
                 '220V, 800W', '200 x 80 x 120 cm', 180,
                 'Daily cleaning, weekly deep clean', 8, true, true,
                 4, 'Molly', 'Kitchen Operations', 'Lions Vision realized')
            """), {"borris_id": borris_id})

            print("  ✓ Created 2 equipment (COOLIE, Salad Bar)")

        # 4. CREATE ACQUISITION REQUEST
        result = conn.execute(text("SELECT COUNT(*) FROM equipment_acquisitions"))
        if result.scalar() > 0:
            print("⚠️  Acquisitions already exist. Skipping.")
        else:
            print("\n🔬 Creating Felix's Centrifuge Request...")

            conn.execute(text("""
                INSERT INTO equipment_acquisitions
                (id, request_number, equipment_type, equipment_name, description,
                 requested_by, requested_date, department, urgency, needed_by,
                 destination_type, destination_name, status,
                 buy_options, lease_options, rent_options,
                 estimated_annual_maintenance, estimated_consumables_yearly, estimated_energy_yearly,
                 currency, revenue_impact, productivity_gain, risk_if_not_acquired,
                 requires_board_approval, notes)
                VALUES
                (gen_random_uuid(), 'ACQ-2025-FELIX-001', 'centrifuge', 'Hettich ROTINA 380 R',
                 'Felix needs refrigerated centrifuge for lab testing.',
                 'Felix', CURRENT_DATE, 'Lab', 'high', CURRENT_DATE + 45,
                 'lab', 'Felix Lab - Artemis', 'evaluating',
                 '[{"vendor": "Mosey", "price": 48500, "warranty": 2}]'::jsonb,
                 '[{"vendor": "MedEquip", "monthly": 1200, "months": 48}]'::jsonb,
                 '[{"vendor": "LabRent", "monthly": 2500}]'::jsonb,
                 1500, 500, 800, 'CHF',
                 'In-house testing, faster batch approval',
                 '2-day delay eliminated, 10x more tests',
                 'External lab dependency, slower TTM',
                 true, 'Felix priority. Unlocks lab capability.')
            """))
            print("  ✓ Created acquisition request: ACQ-2025-FELIX-001")

        conn.commit()

        print("\n" + "="*60)
        print("✅ SEED DATA COMPLETE")
        print("="*60)

        # Summary
        result = conn.execute(text("SELECT COUNT(*) FROM equipment_suppliers"))
        print(f"  Suppliers: {result.scalar()}")
        result = conn.execute(text("SELECT COUNT(*) FROM farms"))
        print(f"  Farms: {result.scalar()}")
        result = conn.execute(text("SELECT COUNT(*) FROM equipment"))
        print(f"  Equipment: {result.scalar()}")
        result = conn.execute(text("SELECT COUNT(*) FROM equipment_acquisitions"))
        print(f"  Acquisition Requests: {result.scalar()}")

        print("\n🐅🦁🌻 The stage is set.")


if __name__ == "__main__":
    seed_equipment()

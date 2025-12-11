#!/usr/bin/env python3
"""
Consolidated Shipment Seed — MOSEY-JP Special

THE REAL DEAL:
One container. Three pallets. Three destinations.
- COOLIE Torches → HAIRY FISH
- Torch Lighters → HAIRY FISH + Mosey 420 (split)
- Hettich Centrifuge 50K → Felix Lab

YUKI plans. CHARLIE watches. MOSEY consolidates.
Bread and butter teamwork.

"We ride WITH the equipment." - YUKI
"I see what others miss." - CHARLIE
"""
import os
from datetime import date, timedelta
from sqlalchemy import create_engine, text


def seed_consolidated_shipment():
    """Seed the MOSEY consolidated shipment — UAT case"""

    db_url = os.environ.get(
        'SYNC_DATABASE_URL',
        'postgresql+psycopg://helix_user:helix_pass@postgres:5432/helix_db'
    )

    engine = create_engine(db_url)

    with engine.connect() as conn:
        print("\n" + "=" * 70)
        print("🚢 SEEDING CONSOLIDATED SHIPMENT — MOSEY-JP SPECIAL")
        print("=" * 70)

        # Check if MOSEY supplier exists
        result = conn.execute(text("SELECT id FROM equipment_suppliers WHERE code = 'MOSEY-JP'"))
        mosey_row = result.fetchone()

        if not mosey_row:
            print("❌ MOSEY-JP supplier not found. Run seed_equipment_simple.py first.")
            return

        mosey_id = mosey_row[0]
        print(f"✓ Found MOSEY-JP supplier: {mosey_id}")

        # =====================================================================
        # 1. CREATE THE PURCHASE ORDER — Consolidated
        # =====================================================================
        print("\n📋 Creating Consolidated Purchase Order...")

        result = conn.execute(text("SELECT COUNT(*) FROM purchase_orders WHERE po_number = 'PO-2025-MOSEY-CONSOLIDATED'"))
        if result.scalar() > 0:
            print("⚠️  PO already exists. Skipping PO creation.")
        else:
            conn.execute(text("""
                INSERT INTO purchase_orders
                (id, po_number, supplier_id, supplier_name, status,
                 requested_date, expected_delivery_date, destination_type, destination_name,
                 items_count, subtotal, shipping_cost, duties_estimate, total, currency,
                 consolidate_with_po,
                 requested_by, notes)
                VALUES
                (gen_random_uuid(), 'PO-2025-MOSEY-CONSOLIDATED', :mosey_id, 'Mosey Scientific Instruments',
                 'shipped',
                 :order_date, :expected_delivery, 'warehouse', 'Multiple: HAIRY FISH, Mosey 420, Felix Lab',
                 3, 62500, 3500, 4200, 70200, 'CHF',
                 'CONSOLIDATED-MASTER',
                 'YUKI', 'THE BIG ONE. COOLIE Torches + Lighters → HAIRY FISH/Mosey420, Centrifuge → Felix Lab. CHARLIE rides.')
            """), {
                "mosey_id": mosey_id,
                "order_date": date.today() - timedelta(days=60),
                "expected_delivery": date.today() + timedelta(days=5)
            })
            print("  ✓ Created PO-2025-MOSEY-CONSOLIDATED")

        # =====================================================================
        # 2. CREATE THE SHIPMENT
        # =====================================================================
        print("\n🚢 Creating Consolidated Shipment...")

        result = conn.execute(text("SELECT COUNT(*) FROM shipments WHERE shipment_number = 'SHIP-2025-MOSEY-CON-001'"))
        if result.scalar() > 0:
            print("⚠️  Shipment already exists. Skipping.")
            result = conn.execute(text("SELECT id FROM shipments WHERE shipment_number = 'SHIP-2025-MOSEY-CON-001'"))
            shipment_id = result.fetchone()[0]
        else:
            # Get PO ID
            result = conn.execute(text("SELECT id FROM purchase_orders WHERE po_number = 'PO-2025-MOSEY-CONSOLIDATED'"))
            po_id = result.fetchone()[0]

            conn.execute(text("""
                INSERT INTO shipments
                (id, shipment_number, shipment_type, container_number, container_size, seal_number,
                 carrier_name, carrier_tracking, vessel_name, voyage_number,
                 origin_country, origin_city, origin_port,
                 destination_country, destination_city, destination_port, final_destination,
                 status, purchase_order_id,
                 total_pieces, total_weight_kg, total_volume_cbm,
                 declared_value, currency,
                 ship_date, eta_port, eta_destination,
                 requires_customs, is_fragile, temperature_controlled, temperature_range,
                 is_insured, insurance_value,
                 handled_by, passengers, notes)
                VALUES
                (gen_random_uuid(), 'SHIP-2025-MOSEY-CON-001', 'container_20ft',
                 'MSCU-2025-CON-7749', '20ft', 'SEAL-JP-2025-8847',
                 'Maersk', 'MAEU-2025-CON-TRACK', 'MSC AURORA', 'VOY-2025-047',
                 'Japan', 'Yokohama', 'Yokohama',
                 'Switzerland', 'Basel', 'Rotterdam', 'Multiple: HAIRY FISH, Mosey 420, Felix Lab',
                 'in_transit_sea', :po_id,
                 3, 850, 12.5,
                 70200, 'CHF',
                 :ship_date, :eta_port, :eta_dest,
                 true, true, true, '15-20C',
                 true, 75000,
                 'YUKI', 'CHARLIE',
                 'THE CONSOLIDATED SPECIAL. Three pallets, three destinations. CF needs special handling. CHARLIE watching.')
            """), {
                "po_id": po_id,
                "ship_date": date.today() - timedelta(days=40),
                "eta_port": date.today() + timedelta(days=3),
                "eta_dest": date.today() + timedelta(days=5)
            })

            result = conn.execute(text("SELECT id FROM shipments WHERE shipment_number = 'SHIP-2025-MOSEY-CON-001'"))
            shipment_id = result.fetchone()[0]
            print(f"  ✓ Created shipment: {shipment_id}")

        # =====================================================================
        # 3. CREATE CUSTOMS CLEARANCE (Ka-MAKI's domain)
        # =====================================================================
        print("\n🛃 Creating Customs Clearance...")

        result = conn.execute(text("SELECT COUNT(*) FROM customs_clearances WHERE clearance_number = 'CC-2025-ROT-MOSEY-001'"))
        if result.scalar() > 0:
            print("⚠️  Customs clearance already exists. Skipping.")
            result = conn.execute(text("SELECT id FROM customs_clearances WHERE clearance_number = 'CC-2025-ROT-MOSEY-001'"))
            customs_id = result.fetchone()[0]
        else:
            conn.execute(text("""
                INSERT INTO customs_clearances
                (id, clearance_number,
                 port_of_entry, customs_office, customs_agent, agent_company, agent_contact,
                 status, documents, documents_complete,
                 hs_codes, duties_calculated, import_duty, vat, other_fees, total_duties, currency,
                 inspection_required, has_issues, issue_description,
                 notes)
                VALUES
                (gen_random_uuid(), 'CC-2025-ROT-MOSEY-001',
                 'Rotterdam', 'Rotterdam Customs Office', 'Ka-MAKI', 'Swiss-Japan Logistics', '+41 79 555 MAKI',
                 'documents_submitted',
                 '{"docs": [
                    {"type": "commercial_invoice", "number": "INV-MOSEY-2025-CON", "status": "submitted"},
                    {"type": "packing_list", "number": "PL-MOSEY-2025-CON", "status": "submitted"},
                    {"type": "certificate_of_origin", "number": "CO-JP-2025-8847", "status": "submitted"},
                    {"type": "lab_equipment_cert", "number": "LAB-HETTICH-CF-001", "status": "MISSING"}
                 ]}'::jsonb,
                 false,
                 '8419.89, 8543.70, 9027.80', true, 2800, 5320, 280, 8400, 'CHF',
                 true, true, 'MISSING: Lab equipment import certificate for Hettich Centrifuge. Required for 50K+ scientific equipment.',
                 'CHARLIE caught it. CF needs LAB-IMPORT-CERT. Ka-MAKI working on it. YUKI did not see this one.')
            """))
            result = conn.execute(text("SELECT id FROM customs_clearances WHERE clearance_number = 'CC-2025-ROT-MOSEY-001'"))
            customs_id = result.fetchone()[0]

            # Link shipment to customs clearance
            conn.execute(text("""
                UPDATE shipments SET customs_clearance_id = :customs_id
                WHERE shipment_number = 'SHIP-2025-MOSEY-CON-001'
            """), {"customs_id": customs_id})

            print("  ✓ Created customs clearance with ISSUE flagged")

        # =====================================================================
        # 4. CREATE THE THREE ITEMS (Traceable Items)
        # =====================================================================
        print("\n📦 Creating Traceable Items (3 pallets)...")

        # Get farm ID for source
        result = conn.execute(text("SELECT id FROM farms LIMIT 1"))
        farm_row = result.fetchone()
        farm_id = farm_row[0] if farm_row else None

        items = [
            {
                "helix_id": "PALLET-COOLIE-TORCH-001",
                "name": "COOLIE Torches - Retail Pack",
                "type": "pallet",
                "dest": "HAIRY FISH - Retail Display",
                "notes": "COOLIE brand torch lighters. Premium line. 500 units."
            },
            {
                "helix_id": "PALLET-TORCH-LIGHTER-001",
                "name": "Torch Lighters - Bulk",
                "type": "pallet",
                "dest": "SPLIT: HAIRY FISH (1200) + Mosey 420 (800)",
                "notes": "Standard torch lighters. COOLIE branded. 2000 units. Split delivery."
            },
            {
                "helix_id": "PALLET-HETTICH-CF-001",
                "name": "Hettich ROTINA 380 R Centrifuge",
                "type": "equipment",
                "dest": "Felix Lab - Artemis",
                "notes": "50,000 CHF. FRAGILE. Climate controlled. ACQ-2025-FELIX-001. CHARLIE priority watch."
            }
        ]

        for item in items:
            result = conn.execute(text("SELECT COUNT(*) FROM traceable_items WHERE helix_id = :code"), {"code": item["helix_id"]})
            if result.scalar() > 0:
                print(f"  ⚠️  {item['helix_id']} exists. Skipping.")
                continue

            conn.execute(text("""
                INSERT INTO traceable_items
                (id, helix_id, qr_code, item_type, item_name, item_description,
                 current_location_type, current_location_name,
                 lifecycle_stage, quality_grade,
                 is_fresh, temp_breach, is_composite, pink_punch_rescued, lost_soul_donated, wasted, composted,
                 notes)
                VALUES
                (gen_random_uuid(), :helix_id, :qr_code, :item_type, :name, :notes,
                 'in_transit', 'Container MSCU-2025-CON-7749',
                 'in_transit', 'A',
                 true, false, false, false, false, false, false,
                 :dest)
            """), {
                "helix_id": item["helix_id"],
                "qr_code": f"QR-{item['helix_id']}",
                "item_type": item["type"],
                "name": item["name"],
                "notes": item["notes"],
                "dest": item["dest"]
            })
            print(f"  ✓ Created {item['helix_id']}")

        # =====================================================================
        # 5. CREATE TRACE EVENTS (The Journey So Far)
        # =====================================================================
        print("\n📍 Creating Trace Events...")

        # Get item IDs
        result = conn.execute(text("""
            SELECT id, helix_id FROM traceable_items
            WHERE helix_id IN ('PALLET-COOLIE-TORCH-001', 'PALLET-TORCH-LIGHTER-001', 'PALLET-HETTICH-CF-001')
        """))
        items_map = {row[1]: row[0] for row in result.fetchall()}

        events = [
            # Event 1: PO Created
            {
                "helix_id": "PALLET-COOLIE-TORCH-001",
                "event_type": "purchase_order_created",
                "description": "Part of consolidated order PO-2025-MOSEY-CONSOLIDATED",
                "stage_before": "ordered",
                "stage_after": "sourced",
                "location_type": "warehouse",
                "location_name": "HELIX HQ",
                "actor_type": "freight_coordinator",
                "actor_name": "YUKI",
                "notes": "COOLIE Torches ordered via MOSEY-JP"
            },
            {
                "helix_id": "PALLET-TORCH-LIGHTER-001",
                "event_type": "purchase_order_created",
                "description": "Part of consolidated order. SPLIT delivery planned.",
                "stage_before": "ordered",
                "stage_after": "sourced",
                "location_type": "warehouse",
                "location_name": "HELIX HQ",
                "actor_type": "freight_coordinator",
                "actor_name": "YUKI",
                "notes": "2000 lighters, split between HAIRY FISH and Mosey 420"
            },
            {
                "helix_id": "PALLET-HETTICH-CF-001",
                "event_type": "purchase_order_created",
                "description": "ACQ-2025-FELIX-001 approved. 50K centrifuge for Felix Lab.",
                "stage_before": "ordered",
                "stage_after": "sourced",
                "location_type": "warehouse",
                "location_name": "HELIX HQ",
                "actor_type": "freight_coordinator",
                "actor_name": "YUKI",
                "notes": "50,000 CHF Hettich ROTINA 380 R. Felix priority."
            },
            # Event 2: Container Loaded at Yokohama
            {
                "helix_id": "PALLET-COOLIE-TORCH-001",
                "event_type": "container_loaded",
                "description": "Loaded position: Front left. Good access for unload.",
                "stage_before": "sourced",
                "stage_after": "in_transit",
                "location_type": "port",
                "location_name": "Yokohama Port",
                "actor_type": "freight_security",
                "actor_name": "CHARLIE",
                "notes": "Container MSCU-2025-CON-7749"
            },
            {
                "helix_id": "PALLET-TORCH-LIGHTER-001",
                "event_type": "container_loaded",
                "description": "Loaded position: Front right. Split delivery markers applied.",
                "stage_before": "sourced",
                "stage_after": "in_transit",
                "location_type": "port",
                "location_name": "Yokohama Port",
                "actor_type": "freight_security",
                "actor_name": "CHARLIE",
                "notes": "Split markers: 1200 HAIRY FISH, 800 Mosey 420"
            },
            {
                "helix_id": "PALLET-HETTICH-CF-001",
                "event_type": "container_loaded",
                "description": "Center position, climate zone. FRAGILE verified. CHARLIE priority.",
                "stage_before": "sourced",
                "stage_after": "in_transit",
                "location_type": "port",
                "location_name": "Yokohama Port",
                "actor_type": "freight_security",
                "actor_name": "CHARLIE",
                "notes": "50K equipment. Climate controlled zone. CHARLIE eyes on."
            },
            # Event 3: Container Sealed — CHARLIE inside
            {
                "helix_id": "PALLET-HETTICH-CF-001",
                "event_type": "container_sealed",
                "description": "Seal SEAL-JP-2025-8847 applied. CHARLIE rides WITH container.",
                "stage_before": "in_transit",
                "stage_after": "in_transit",
                "location_type": "port",
                "location_name": "Yokohama Port",
                "actor_type": "freight_security",
                "actor_name": "CHARLIE",
                "notes": "We ride WITH the equipment. Eyes on the 50K."
            },
            # Event 4: CHARLIE catches the missing paperwork
            {
                "helix_id": "PALLET-HETTICH-CF-001",
                "event_type": "issue_detected",
                "description": "MISSING: Lab equipment import certificate LAB-HETTICH-CF-001",
                "stage_before": "in_transit",
                "stage_after": "in_transit",
                "location_type": "in_transit",
                "location_name": "MSC AURORA - Day 12",
                "actor_type": "freight_security",
                "actor_name": "CHARLIE",
                "notes": "Required for Swiss customs. YUKI notified. Ka-MAKI working on it. I see what others miss."
            },
        ]

        for event in events:
            item_id = items_map.get(event["helix_id"])
            if not item_id:
                print(f"  ⚠️  Item {event['helix_id']} not found. Skipping event.")
                continue

            result = conn.execute(text("""
                SELECT COUNT(*) FROM trace_events
                WHERE helix_id = :code AND event_type = :etype
            """), {"code": event["helix_id"], "etype": event["event_type"]})

            if result.scalar() > 0:
                print(f"  ⚠️  {event['event_type']} for {event['helix_id']} exists. Skipping.")
                continue

            conn.execute(text("""
                INSERT INTO trace_events
                (id, item_id, helix_id, event_type, event_description,
                 stage_before, stage_after,
                 location_type, location_name,
                 actor_type, actor_name,
                 quality_check,
                 notes)
                VALUES
                (gen_random_uuid(), :item_id, :helix_id, :event_type, :description,
                 :stage_before, :stage_after,
                 :loc_type, :loc_name,
                 :actor_type, :actor_name,
                 false,
                 :notes)
            """), {
                "item_id": item_id,
                "helix_id": event["helix_id"],
                "event_type": event["event_type"],
                "description": event["description"],
                "stage_before": event["stage_before"],
                "stage_after": event["stage_after"],
                "loc_type": event["location_type"],
                "loc_name": event["location_name"],
                "actor_type": event["actor_type"],
                "actor_name": event["actor_name"],
                "notes": event["notes"]
            })
            print(f"  ✓ {event['event_type']} ({event['helix_id'][:25]}...)")

        conn.commit()

        # =====================================================================
        # SUMMARY
        # =====================================================================
        print("\n" + "=" * 70)
        print("✅ CONSOLIDATED SHIPMENT SEED COMPLETE")
        print("=" * 70)

        # Show what we created
        print("\n📋 PURCHASE ORDER:")
        result = conn.execute(text("""
            SELECT po_number, status, total, currency, notes
            FROM purchase_orders WHERE po_number = 'PO-2025-MOSEY-CONSOLIDATED'
        """))
        row = result.fetchone()
        if row:
            print(f"   {row[0]} | {row[1]} | {row[2]} {row[3]}")
            if row[4]:
                print(f"   Note: {row[4][:60]}...")

        print("\n🚢 SHIPMENT:")
        result = conn.execute(text("""
            SELECT shipment_number, container_number, status, handled_by, passengers
            FROM shipments WHERE shipment_number = 'SHIP-2025-MOSEY-CON-001'
        """))
        row = result.fetchone()
        if row:
            print(f"   {row[0]} | {row[1]} | {row[2]}")
            print(f"   Handled by: {row[3]} | Passenger: {row[4]}")

        print("\n🛃 CUSTOMS (Ka-MAKI):")
        result = conn.execute(text("""
            SELECT clearance_number, status, has_issues, issue_description
            FROM customs_clearances WHERE clearance_number = 'CC-2025-ROT-MOSEY-001'
        """))
        row = result.fetchone()
        if row:
            print(f"   {row[0]} | {row[1]}")
            if row[2]:
                print(f"   ⚠️  ISSUE: {row[3][:60]}...")

        print("\n📦 PALLETS (Traceable Items):")
        result = conn.execute(text("""
            SELECT helix_id, item_name, notes
            FROM traceable_items
            WHERE helix_id LIKE 'PALLET-%'
            ORDER BY helix_id
        """))
        for row in result.fetchall():
            print(f"   {row[0]}")
            print(f"      {row[1]}")
            if row[2]:
                print(f"      → {row[2][:50]}...")

        print("\n📍 TRACE EVENTS:")
        result = conn.execute(text("""
            SELECT helix_id, event_type, actor_name, notes
            FROM trace_events
            WHERE helix_id LIKE 'PALLET-%'
            ORDER BY helix_id, event_time
        """))
        current_item = None
        for row in result.fetchall():
            if row[0] != current_item:
                current_item = row[0]
                print(f"\n   {current_item}:")
            print(f"      • {row[1]} by {row[2]}")

        print("\n" + "=" * 70)
        print("🔥 THE SITUATION:")
        print("=" * 70)
        print("""
   Container MSCU-2025-CON-7749 is IN TRANSIT (Day 40 of 45)

   CHARLIE is INSIDE the container watching the 50K centrifuge.

   On Day 12, CHARLIE noticed:
   ⚠️  MISSING LAB EQUIPMENT IMPORT CERTIFICATE

   YUKI didn't catch it. Ka-MAKI is working on it.
   Without that cert, the centrifuge gets HELD at Rotterdam customs.

   ETA Rotterdam: 3 days
   ETA Final: 5 days

   CHARLIE saved the day. Again.
   "I see what others miss."
        """)
        print("=" * 70)
        print("🐅🚢📦🔬 READY FOR UAT")
        print("=" * 70)


if __name__ == "__main__":
    seed_consolidated_shipment()

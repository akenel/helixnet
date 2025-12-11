"""Add E2E Track & Trace (SPINE) and Equipment Supply Chain tables

Revision ID: 003_spine_equipment
Revises: 002_hr_module
Create Date: 2025-12-11

THE SPINE: Farm → Batch → Lab Test → Traceable Item → Trace Event
EQUIPMENT: Supplier → PO → Shipment → Customs → Equipment → Maintenance
YUKI & CHARLIE ride the 20ft container from Yokohama to Rotterdam.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_spine_equipment'
down_revision: Union[str, None] = '002_hr_module'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =====================================================
    # E2E TRACK & TRACE TABLES (THE SPINE)
    # =====================================================

    # === FARMS TABLE ===
    op.create_table(
        'farms',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),

        # Identity
        sa.Column('code', sa.String(20), unique=True, nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('farm_type', sa.String(30), nullable=False),

        # Location
        sa.Column('address', sa.String(300), nullable=False),
        sa.Column('canton', sa.String(2), default='LU', nullable=False),
        sa.Column('postal_code', sa.String(10), nullable=False),
        sa.Column('country', sa.String(50), default='Switzerland', nullable=False),
        sa.Column('gps_latitude', sa.Float(), nullable=True),
        sa.Column('gps_longitude', sa.Float(), nullable=True),
        sa.Column('altitude_meters', sa.Integer(), nullable=True),

        # Operations
        sa.Column('hectares', sa.Float(), nullable=True),
        sa.Column('owned_by', sa.String(200), nullable=True),
        sa.Column('managed_by', sa.String(100), nullable=False),

        # Animals
        sa.Column('goats', sa.Integer(), default=0, nullable=False),
        sa.Column('bees_hives', sa.Integer(), default=0, nullable=False),
        sa.Column('chickens', sa.Integer(), default=0, nullable=False),
        sa.Column('cows', sa.Integer(), default=0, nullable=False),

        # Certifications
        sa.Column('bio_certified', sa.Boolean(), default=False, nullable=False),
        sa.Column('bio_cert_number', sa.String(50), nullable=True),
        sa.Column('bio_cert_expiry', sa.Date(), nullable=True),
        sa.Column('ip_suisse', sa.Boolean(), default=False, nullable=False),
        sa.Column('demeter', sa.Boolean(), default=False, nullable=False),
        sa.Column('swiss_gap', sa.Boolean(), default=False, nullable=False),
        sa.Column('other_certs', sa.Text(), nullable=True),

        # Contact
        sa.Column('primary_contact', sa.String(100), nullable=True),
        sa.Column('phone', sa.String(30), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_farms_code', 'farms', ['code'])
    op.create_index('ix_farms_farm_type', 'farms', ['farm_type'])

    # === BATCHES TABLE ===
    op.create_table(
        'batches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),

        # Identity
        sa.Column('batch_number', sa.String(50), unique=True, nullable=False),

        # Source
        sa.Column('farm_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('farms.id', ondelete='SET NULL'), nullable=True),
        sa.Column('farm_code', sa.String(20), nullable=True),

        # Product
        sa.Column('product_type', sa.String(100), nullable=False),
        sa.Column('product_name', sa.String(200), nullable=False),
        sa.Column('variety', sa.String(100), nullable=True),

        # Quantity
        sa.Column('initial_quantity', sa.Float(), nullable=False),
        sa.Column('current_quantity', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(20), nullable=False),
        sa.Column('package_count', sa.Integer(), default=0),
        sa.Column('package_type', sa.String(50), nullable=True),

        # Dates
        sa.Column('harvest_date', sa.Date(), nullable=True),
        sa.Column('production_date', sa.Date(), nullable=False),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('best_before_date', sa.Date(), nullable=True),

        # Freshness
        sa.Column('freshness_rule', sa.String(30), default='standard', nullable=False),
        sa.Column('max_freshness_hours', sa.Integer(), nullable=True),
        sa.Column('is_fresh', sa.Boolean(), default=True, nullable=False),
        sa.Column('freshness_check_time', sa.DateTime(timezone=True), nullable=True),

        # Status
        sa.Column('status', sa.String(30), default='pending', nullable=False),

        # Lab
        sa.Column('lab_tested', sa.Boolean(), default=False, nullable=False),
        sa.Column('lab_test_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('lab_approved', sa.Boolean(), default=False, nullable=False),
        sa.Column('lab_approved_by', sa.String(100), nullable=True),
        sa.Column('quality_grade', sa.String(10), nullable=True),

        # Issues
        sa.Column('has_issues', sa.Boolean(), default=False, nullable=False),
        sa.Column('issue_description', sa.Text(), nullable=True),

        # Pink Punch rescue
        sa.Column('pink_punch_rescue', sa.Boolean(), default=False, nullable=False),
        sa.Column('pink_punch_notes', sa.Text(), nullable=True),

        # Storage
        sa.Column('storage_location', sa.String(100), nullable=True),
        sa.Column('temperature_range', sa.String(20), nullable=True),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_batches_batch_number', 'batches', ['batch_number'])
    op.create_index('ix_batches_farm_id', 'batches', ['farm_id'])
    op.create_index('ix_batches_status', 'batches', ['status'])
    op.create_index('ix_batches_production_date', 'batches', ['production_date'])

    # === LAB TESTS TABLE ===
    op.create_table(
        'lab_tests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),

        # Identity
        sa.Column('test_number', sa.String(50), unique=True, nullable=False),

        # What
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('batches.id', ondelete='CASCADE'), nullable=False),
        sa.Column('batch_number', sa.String(50), nullable=False),

        # Who
        sa.Column('tested_by', sa.String(100), nullable=False),
        sa.Column('lab_name', sa.String(200), nullable=True),

        # When
        sa.Column('test_date', sa.Date(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),

        # Status
        sa.Column('status', sa.String(30), default='pending', nullable=False),

        # Tests
        sa.Column('contamination_tested', sa.Boolean(), default=False, nullable=False),
        sa.Column('contamination_result', sa.String(20), nullable=True),
        sa.Column('freshness_tested', sa.Boolean(), default=False, nullable=False),
        sa.Column('freshness_result', sa.String(20), nullable=True),
        sa.Column('temperature_tested', sa.Boolean(), default=False, nullable=False),
        sa.Column('temperature_result', sa.String(20), nullable=True),
        sa.Column('visual_tested', sa.Boolean(), default=False, nullable=False),
        sa.Column('visual_result', sa.String(20), nullable=True),
        sa.Column('taste_tested', sa.Boolean(), default=False, nullable=False),
        sa.Column('taste_result', sa.String(20), nullable=True),

        # Temperature
        sa.Column('sample_temp_celsius', sa.Float(), nullable=True),
        sa.Column('expected_temp_min', sa.Float(), nullable=True),
        sa.Column('expected_temp_max', sa.Float(), nullable=True),

        # Quality
        sa.Column('quality_grade', sa.String(10), nullable=True),
        sa.Column('quality_score', sa.Integer(), nullable=True),

        # Result
        sa.Column('passed', sa.Boolean(), nullable=True),
        sa.Column('issues_found', sa.Text(), nullable=True),
        sa.Column('recommendations', sa.Text(), nullable=True),

        # Pink Punch
        sa.Column('pink_punch_candidate', sa.Boolean(), default=False, nullable=False),
        sa.Column('pink_punch_notes', sa.Text(), nullable=True),

        # Sign off
        sa.Column('approved_by', sa.String(100), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_lab_tests_test_number', 'lab_tests', ['test_number'])
    op.create_index('ix_lab_tests_batch_id', 'lab_tests', ['batch_id'])
    op.create_index('ix_lab_tests_status', 'lab_tests', ['status'])

    # === TRACEABLE ITEMS TABLE (THE SPINE) ===
    op.create_table(
        'traceable_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),

        # Identity
        sa.Column('helix_id', sa.String(50), unique=True, nullable=False),
        sa.Column('qr_code', sa.String(100), unique=True, nullable=False),

        # Type
        sa.Column('item_type', sa.String(50), nullable=False),
        sa.Column('item_name', sa.String(200), nullable=False),
        sa.Column('item_description', sa.Text(), nullable=True),

        # Source
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('batches.id', ondelete='SET NULL'), nullable=True),
        sa.Column('batch_number', sa.String(50), nullable=True),
        sa.Column('farm_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('farms.id', ondelete='SET NULL'), nullable=True),
        sa.Column('farm_code', sa.String(20), nullable=True),

        # Lifecycle
        sa.Column('lifecycle_stage', sa.String(30), default='created', nullable=False),
        sa.Column('stage_changed_at', sa.DateTime(timezone=True), nullable=True),

        # Location
        sa.Column('current_location_type', sa.String(30), nullable=False),
        sa.Column('current_location_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('current_location_name', sa.String(200), nullable=True),
        sa.Column('gps_latitude', sa.Float(), nullable=True),
        sa.Column('gps_longitude', sa.Float(), nullable=True),

        # Quality
        sa.Column('quality_grade', sa.String(10), nullable=True),
        sa.Column('lab_test_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lab_tests.id', ondelete='SET NULL'), nullable=True),

        # Freshness
        sa.Column('production_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expiry_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_fresh', sa.Boolean(), default=True, nullable=False),
        sa.Column('freshness_window_hours', sa.Integer(), nullable=True),

        # Temperature
        sa.Column('last_temp_celsius', sa.Float(), nullable=True),
        sa.Column('temp_recorded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('temp_breach', sa.Boolean(), default=False, nullable=False),

        # Chain
        sa.Column('parent_item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('traceable_items.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_composite', sa.Boolean(), default=False, nullable=False),
        sa.Column('component_count', sa.Integer(), default=0),

        # Consumer
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('feedback_rating', sa.Integer(), nullable=True),
        sa.Column('feedback_text', sa.Text(), nullable=True),

        # Pink Punch
        sa.Column('pink_punch_rescued', sa.Boolean(), default=False, nullable=False),
        sa.Column('pink_punch_at', sa.DateTime(timezone=True), nullable=True),

        # Lost Soul
        sa.Column('lost_soul_donated', sa.Boolean(), default=False, nullable=False),
        sa.Column('lost_soul_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('lost_soul_location', sa.String(200), nullable=True),

        # Waste
        sa.Column('wasted', sa.Boolean(), default=False, nullable=False),
        sa.Column('waste_reason', sa.String(100), nullable=True),
        sa.Column('wasted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('composted', sa.Boolean(), default=False, nullable=False),
        sa.Column('compost_destination', sa.String(200), nullable=True),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_traceable_items_helix_id', 'traceable_items', ['helix_id'])
    op.create_index('ix_traceable_items_qr_code', 'traceable_items', ['qr_code'])
    op.create_index('ix_traceable_items_batch_id', 'traceable_items', ['batch_id'])
    op.create_index('ix_traceable_items_lifecycle_stage', 'traceable_items', ['lifecycle_stage'])
    op.create_index('ix_traceable_items_current_location_type', 'traceable_items', ['current_location_type'])

    # === TRACE EVENTS TABLE ===
    op.create_table(
        'trace_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),

        # What item
        sa.Column('item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('traceable_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('helix_id', sa.String(50), nullable=False),

        # Event
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_description', sa.Text(), nullable=True),

        # Who
        sa.Column('actor_type', sa.String(30), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('actor_name', sa.String(100), nullable=False),
        sa.Column('actor_role', sa.String(50), nullable=True),

        # Stage
        sa.Column('stage_before', sa.String(30), nullable=True),
        sa.Column('stage_after', sa.String(30), nullable=True),

        # Location
        sa.Column('location_type', sa.String(30), nullable=True),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('location_name', sa.String(200), nullable=True),
        sa.Column('gps_latitude', sa.Float(), nullable=True),
        sa.Column('gps_longitude', sa.Float(), nullable=True),

        # Temperature
        sa.Column('temperature_celsius', sa.Float(), nullable=True),

        # Quality
        sa.Column('quality_check', sa.Boolean(), default=False, nullable=False),
        sa.Column('quality_result', sa.String(20), nullable=True),
        sa.Column('quality_notes', sa.Text(), nullable=True),

        # Device
        sa.Column('device_id', sa.String(100), nullable=True),
        sa.Column('device_type', sa.String(50), nullable=True),
        sa.Column('app_version', sa.String(20), nullable=True),

        # Signature
        sa.Column('signature', sa.String(500), nullable=True),
        sa.Column('signature_type', sa.String(20), nullable=True),

        # Chain
        sa.Column('previous_event_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('trace_events.id', ondelete='SET NULL'), nullable=True),
        sa.Column('chain_hash', sa.String(100), nullable=True),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),

        # Timestamp
        sa.Column('event_time', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_trace_events_item_id', 'trace_events', ['item_id'])
    op.create_index('ix_trace_events_helix_id', 'trace_events', ['helix_id'])
    op.create_index('ix_trace_events_event_type', 'trace_events', ['event_type'])
    op.create_index('ix_trace_events_event_time', 'trace_events', ['event_time'])
    op.create_index('ix_trace_events_actor_type', 'trace_events', ['actor_type'])

    # =====================================================
    # EQUIPMENT SUPPLY CHAIN TABLES (YUKI & CHARLIE)
    # =====================================================

    # === EQUIPMENT SUPPLIERS TABLE ===
    op.create_table(
        'equipment_suppliers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),

        # Identity
        sa.Column('code', sa.String(20), unique=True, nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('supplier_type', sa.String(30), nullable=False),

        # Location
        sa.Column('country', sa.String(100), nullable=False),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('address', sa.String(300), nullable=True),
        sa.Column('postal_code', sa.String(20), nullable=True),

        # Contact
        sa.Column('primary_contact', sa.String(100), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('website', sa.String(300), nullable=True),

        # Specialties
        sa.Column('specialties', sa.Text(), nullable=True),
        sa.Column('product_lines', sa.Text(), nullable=True),

        # Business
        sa.Column('currency', sa.String(10), default='USD', nullable=False),
        sa.Column('payment_terms', sa.String(100), nullable=True),
        sa.Column('lead_time_days', sa.Integer(), nullable=True),

        # Shipping
        sa.Column('ships_to_europe', sa.Boolean(), default=True, nullable=False),
        sa.Column('preferred_carrier', sa.String(100), nullable=True),
        sa.Column('can_consolidate', sa.Boolean(), default=False, nullable=False),

        # Rating
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('total_orders', sa.Integer(), default=0),
        sa.Column('on_time_delivery_rate', sa.Float(), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_equipment_suppliers_code', 'equipment_suppliers', ['code'])
    op.create_index('ix_equipment_suppliers_country', 'equipment_suppliers', ['country'])

    # === PURCHASE ORDERS TABLE ===
    op.create_table(
        'purchase_orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),

        # Identity
        sa.Column('po_number', sa.String(50), unique=True, nullable=False),

        # Supplier
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('equipment_suppliers.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('supplier_name', sa.String(200), nullable=False),

        # Requested by
        sa.Column('requested_by', sa.String(100), nullable=False),
        sa.Column('requested_date', sa.Date(), nullable=False),

        # Destination
        sa.Column('destination_type', sa.String(50), nullable=False),
        sa.Column('destination_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('destination_name', sa.String(200), nullable=False),

        # Line items (JSON)
        sa.Column('line_items', postgresql.JSONB(), nullable=True),
        sa.Column('items_count', sa.Integer(), default=0, nullable=False),

        # Totals
        sa.Column('subtotal', sa.Numeric(12, 2), default=0, nullable=False),
        sa.Column('shipping_cost', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('duties_estimate', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('total', sa.Numeric(12, 2), default=0, nullable=False),
        sa.Column('currency', sa.String(10), default='USD', nullable=False),

        # Status
        sa.Column('status', sa.String(30), default='draft', nullable=False),

        # Dates
        sa.Column('expected_ship_date', sa.Date(), nullable=True),
        sa.Column('expected_delivery_date', sa.Date(), nullable=True),
        sa.Column('actual_ship_date', sa.Date(), nullable=True),
        sa.Column('actual_delivery_date', sa.Date(), nullable=True),

        # Shipping
        sa.Column('preferred_shipment_type', sa.String(50), nullable=True),
        sa.Column('consolidate_with_po', sa.String(50), nullable=True),

        # Receipt
        sa.Column('items_shipped', sa.Integer(), default=0),
        sa.Column('items_received', sa.Integer(), default=0),
        sa.Column('is_complete', sa.Boolean(), default=False),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('internal_notes', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_purchase_orders_po_number', 'purchase_orders', ['po_number'])
    op.create_index('ix_purchase_orders_supplier_id', 'purchase_orders', ['supplier_id'])
    op.create_index('ix_purchase_orders_status', 'purchase_orders', ['status'])

    # === CUSTOMS CLEARANCES TABLE ===
    op.create_table(
        'customs_clearances',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),

        # Identity
        sa.Column('clearance_number', sa.String(50), unique=True, nullable=False),

        # Port
        sa.Column('port_of_entry', sa.String(100), nullable=False),
        sa.Column('customs_office', sa.String(200), nullable=True),

        # Agent
        sa.Column('customs_agent', sa.String(100), nullable=False),
        sa.Column('agent_company', sa.String(200), nullable=True),
        sa.Column('agent_contact', sa.String(200), nullable=True),

        # Status
        sa.Column('status', sa.String(30), default='pending', nullable=False),

        # Documents (JSON)
        sa.Column('documents', postgresql.JSONB(), nullable=True),
        sa.Column('documents_complete', sa.Boolean(), default=False, nullable=False),

        # Classification
        sa.Column('hs_codes', sa.Text(), nullable=True),

        # Duties
        sa.Column('duties_calculated', sa.Boolean(), default=False),
        sa.Column('import_duty', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('vat', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('other_fees', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('total_duties', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('currency', sa.String(10), default='CHF', nullable=False),

        # Payment
        sa.Column('duties_paid', sa.Boolean(), default=False),
        sa.Column('duties_paid_date', sa.Date(), nullable=True),
        sa.Column('duties_paid_by', sa.String(100), nullable=True),

        # Inspection
        sa.Column('inspection_required', sa.Boolean(), default=False),
        sa.Column('inspection_date', sa.Date(), nullable=True),
        sa.Column('inspection_result', sa.String(50), nullable=True),
        sa.Column('inspection_notes', sa.Text(), nullable=True),

        # Timeline
        sa.Column('submitted_date', sa.Date(), nullable=True),
        sa.Column('cleared_date', sa.Date(), nullable=True),
        sa.Column('processing_days', sa.Integer(), default=0),

        # Issues
        sa.Column('has_issues', sa.Boolean(), default=False),
        sa.Column('issue_description', sa.Text(), nullable=True),
        sa.Column('issue_resolution', sa.Text(), nullable=True),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_customs_clearances_clearance_number', 'customs_clearances', ['clearance_number'])
    op.create_index('ix_customs_clearances_status', 'customs_clearances', ['status'])

    # === SHIPMENTS TABLE ===
    op.create_table(
        'shipments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),

        # Identity
        sa.Column('shipment_number', sa.String(50), unique=True, nullable=False),

        # Type
        sa.Column('shipment_type', sa.String(30), nullable=False),

        # Container
        sa.Column('container_number', sa.String(50), nullable=True),
        sa.Column('container_size', sa.String(20), nullable=True),
        sa.Column('seal_number', sa.String(50), nullable=True),

        # Carrier
        sa.Column('carrier_name', sa.String(200), nullable=False),
        sa.Column('carrier_tracking', sa.String(100), nullable=True),
        sa.Column('vessel_name', sa.String(100), nullable=True),
        sa.Column('voyage_number', sa.String(50), nullable=True),

        # Origin
        sa.Column('origin_country', sa.String(100), nullable=False),
        sa.Column('origin_city', sa.String(100), nullable=False),
        sa.Column('origin_port', sa.String(100), nullable=True),

        # Destination
        sa.Column('destination_country', sa.String(100), nullable=False),
        sa.Column('destination_city', sa.String(100), nullable=False),
        sa.Column('destination_port', sa.String(100), nullable=True),
        sa.Column('final_destination', sa.String(200), nullable=False),
        sa.Column('final_destination_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Status
        sa.Column('status', sa.String(30), default='pending', nullable=False),

        # Contents
        sa.Column('purchase_order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('purchase_orders.id', ondelete='SET NULL'), nullable=True),
        sa.Column('total_pieces', sa.Integer(), default=0),
        sa.Column('total_weight_kg', sa.Float(), nullable=True),
        sa.Column('total_volume_cbm', sa.Float(), nullable=True),

        # Value
        sa.Column('declared_value', sa.Numeric(14, 2), nullable=True),
        sa.Column('currency', sa.String(10), default='USD', nullable=False),

        # Dates
        sa.Column('ship_date', sa.Date(), nullable=True),
        sa.Column('eta_port', sa.Date(), nullable=True),
        sa.Column('eta_destination', sa.Date(), nullable=True),
        sa.Column('actual_arrival_port', sa.Date(), nullable=True),
        sa.Column('actual_arrival_destination', sa.Date(), nullable=True),

        # Customs
        sa.Column('requires_customs', sa.Boolean(), default=True, nullable=False),
        sa.Column('customs_clearance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customs_clearances.id', ondelete='SET NULL'), nullable=True),

        # Special
        sa.Column('is_hazardous', sa.Boolean(), default=False),
        sa.Column('is_fragile', sa.Boolean(), default=False),
        sa.Column('temperature_controlled', sa.Boolean(), default=False),
        sa.Column('temperature_range', sa.String(20), nullable=True),

        # Insurance
        sa.Column('is_insured', sa.Boolean(), default=False),
        sa.Column('insurance_value', sa.Numeric(14, 2), nullable=True),

        # Delays
        sa.Column('is_delayed', sa.Boolean(), default=False),
        sa.Column('delay_reason', sa.Text(), nullable=True),
        sa.Column('delay_days', sa.Integer(), default=0),

        # Human element
        sa.Column('handled_by', sa.String(100), nullable=True),
        sa.Column('passengers', sa.Text(), nullable=True),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_shipments_shipment_number', 'shipments', ['shipment_number'])
    op.create_index('ix_shipments_status', 'shipments', ['status'])
    op.create_index('ix_shipments_purchase_order_id', 'shipments', ['purchase_order_id'])

    # === EQUIPMENT TABLE ===
    op.create_table(
        'equipment',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),

        # Identity
        sa.Column('asset_tag', sa.String(50), unique=True, nullable=False),
        sa.Column('serial_number', sa.String(100), nullable=True),

        # Type
        sa.Column('equipment_type', sa.String(30), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),

        # Make/Model
        sa.Column('manufacturer', sa.String(200), nullable=True),
        sa.Column('model', sa.String(200), nullable=True),
        sa.Column('model_year', sa.Integer(), nullable=True),

        # Source
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('equipment_suppliers.id', ondelete='SET NULL'), nullable=True),
        sa.Column('supplier_name', sa.String(200), nullable=True),
        sa.Column('purchase_order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('purchase_orders.id', ondelete='SET NULL'), nullable=True),
        sa.Column('purchase_order_number', sa.String(50), nullable=True),

        # Location
        sa.Column('location_type', sa.String(50), nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('location_name', sa.String(200), nullable=False),
        sa.Column('location_zone', sa.String(100), nullable=True),
        sa.Column('gps_latitude', sa.Float(), nullable=True),
        sa.Column('gps_longitude', sa.Float(), nullable=True),

        # Status
        sa.Column('status', sa.String(30), default='ordered', nullable=False),

        # Dates
        sa.Column('ordered_date', sa.Date(), nullable=True),
        sa.Column('received_date', sa.Date(), nullable=True),
        sa.Column('installed_date', sa.Date(), nullable=True),
        sa.Column('warranty_end_date', sa.Date(), nullable=True),
        sa.Column('expected_lifetime_years', sa.Integer(), nullable=True),

        # Value
        sa.Column('purchase_price', sa.Numeric(12, 2), nullable=True),
        sa.Column('current_value', sa.Numeric(12, 2), nullable=True),
        sa.Column('currency', sa.String(10), default='CHF', nullable=False),

        # Operational
        sa.Column('power_requirements', sa.String(100), nullable=True),
        sa.Column('water_requirements', sa.String(100), nullable=True),
        sa.Column('dimensions', sa.String(100), nullable=True),
        sa.Column('weight_kg', sa.Float(), nullable=True),

        # Maintenance
        sa.Column('maintenance_schedule', sa.String(100), nullable=True),
        sa.Column('last_maintenance', sa.Date(), nullable=True),
        sa.Column('next_maintenance', sa.Date(), nullable=True),
        sa.Column('total_maintenance_cost', sa.Numeric(10, 2), default=0),

        # Coffee specific
        sa.Column('nespresso_compatible', sa.Boolean(), default=False),
        sa.Column('fresh_bean_grinder', sa.Boolean(), default=False),
        sa.Column('water_tank_liters', sa.Float(), nullable=True),
        sa.Column('bean_hopper_kg', sa.Float(), nullable=True),

        # Salad bar specific
        sa.Column('compartment_count', sa.Integer(), nullable=True),
        sa.Column('refrigerated', sa.Boolean(), default=False),
        sa.Column('sneeze_guard', sa.Boolean(), default=False),
        sa.Column('cbd_dispenser_count', sa.Integer(), nullable=True),

        # Documentation
        sa.Column('manual_url', sa.String(500), nullable=True),
        sa.Column('warranty_doc_url', sa.String(500), nullable=True),
        sa.Column('photos', sa.Text(), nullable=True),

        # Assigned
        sa.Column('assigned_to', sa.String(100), nullable=True),
        sa.Column('responsible_team', sa.String(100), nullable=True),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_equipment_asset_tag', 'equipment', ['asset_tag'])
    op.create_index('ix_equipment_equipment_type', 'equipment', ['equipment_type'])
    op.create_index('ix_equipment_status', 'equipment', ['status'])
    op.create_index('ix_equipment_location_type', 'equipment', ['location_type'])

    # === MAINTENANCE EVENTS TABLE ===
    op.create_table(
        'maintenance_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),

        # What
        sa.Column('equipment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('equipment.id', ondelete='CASCADE'), nullable=False),
        sa.Column('equipment_name', sa.String(200), nullable=False),

        # Type
        sa.Column('maintenance_type', sa.String(30), nullable=False),

        # Description
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),

        # Who
        sa.Column('performed_by', sa.String(100), nullable=False),

        # When
        sa.Column('scheduled_date', sa.Date(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),

        # Status
        sa.Column('status', sa.String(30), default='scheduled', nullable=False),

        # Parts
        sa.Column('parts_used', sa.Text(), nullable=True),
        sa.Column('parts_cost', sa.Numeric(10, 2), default=0, nullable=False),

        # Labor
        sa.Column('labor_hours', sa.Float(), default=0, nullable=False),
        sa.Column('labor_cost', sa.Numeric(10, 2), default=0, nullable=False),

        # Total
        sa.Column('total_cost', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('currency', sa.String(10), default='CHF', nullable=False),

        # Result
        sa.Column('issue_found', sa.Text(), nullable=True),
        sa.Column('action_taken', sa.Text(), nullable=True),
        sa.Column('result', sa.String(50), nullable=True),

        # Downtime
        sa.Column('downtime_hours', sa.Float(), default=0, nullable=False),

        # Follow-up
        sa.Column('follow_up_required', sa.Boolean(), default=False),
        sa.Column('follow_up_notes', sa.Text(), nullable=True),
        sa.Column('next_maintenance_date', sa.Date(), nullable=True),

        # Parts ordered
        sa.Column('waiting_for_parts', sa.Boolean(), default=False),
        sa.Column('parts_order_po', sa.String(50), nullable=True),

        # Photos
        sa.Column('before_photos', sa.Text(), nullable=True),
        sa.Column('after_photos', sa.Text(), nullable=True),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),

        # Timestamp
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_maintenance_events_equipment_id', 'maintenance_events', ['equipment_id'])
    op.create_index('ix_maintenance_events_maintenance_type', 'maintenance_events', ['maintenance_type'])
    op.create_index('ix_maintenance_events_status', 'maintenance_events', ['status'])

    # NOTE: shift_sessions table is already defined in shift_session_model.py
    # and will be created separately if not exists. Skipping to avoid duplication.

    # === EQUIPMENT ACQUISITIONS TABLE (BUY vs LEASE vs RENT) ===
    op.create_table(
        'equipment_acquisitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),

        # Identity
        sa.Column('request_number', sa.String(50), unique=True, nullable=False),

        # What
        sa.Column('equipment_type', sa.String(100), nullable=False),
        sa.Column('equipment_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),

        # Who requested
        sa.Column('requested_by', sa.String(100), nullable=False),
        sa.Column('requested_date', sa.Date(), nullable=False),
        sa.Column('department', sa.String(100), nullable=True),

        # Urgency
        sa.Column('urgency', sa.String(30), default='medium', nullable=False),
        sa.Column('needed_by', sa.Date(), nullable=True),

        # Destination
        sa.Column('destination_type', sa.String(50), nullable=False),
        sa.Column('destination_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('destination_name', sa.String(200), nullable=False),

        # Decision
        sa.Column('acquisition_type', sa.String(30), nullable=True),
        sa.Column('decision_date', sa.Date(), nullable=True),
        sa.Column('decision_by', sa.String(100), nullable=True),
        sa.Column('decision_reason', sa.Text(), nullable=True),

        # Status
        sa.Column('status', sa.String(30), default='requested', nullable=False),

        # Options (JSON)
        sa.Column('buy_options', postgresql.JSONB(), nullable=True),
        sa.Column('lease_options', postgresql.JSONB(), nullable=True),
        sa.Column('rent_options', postgresql.JSONB(), nullable=True),

        # Selected vendor
        sa.Column('selected_vendor', sa.String(200), nullable=True),
        sa.Column('selected_vendor_contact', sa.String(200), nullable=True),

        # Purchase details
        sa.Column('purchase_price', sa.Numeric(12, 2), nullable=True),
        sa.Column('warranty_years', sa.Integer(), nullable=True),
        sa.Column('expected_lifetime_years', sa.Integer(), nullable=True),
        sa.Column('annual_depreciation', sa.Numeric(12, 2), nullable=True),

        # Lease details
        sa.Column('lease_monthly_payment', sa.Numeric(10, 2), nullable=True),
        sa.Column('lease_duration_months', sa.Integer(), nullable=True),
        sa.Column('lease_start_date', sa.Date(), nullable=True),
        sa.Column('lease_end_date', sa.Date(), nullable=True),
        sa.Column('lease_buyout_option', sa.Boolean(), default=False),
        sa.Column('lease_buyout_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('lease_includes_maintenance', sa.Boolean(), default=False),

        # Rental details
        sa.Column('rental_daily_rate', sa.Numeric(10, 2), nullable=True),
        sa.Column('rental_weekly_rate', sa.Numeric(10, 2), nullable=True),
        sa.Column('rental_monthly_rate', sa.Numeric(10, 2), nullable=True),
        sa.Column('rental_start_date', sa.Date(), nullable=True),
        sa.Column('rental_end_date', sa.Date(), nullable=True),
        sa.Column('rental_extension_possible', sa.Boolean(), default=True),

        # Total cost of ownership
        sa.Column('estimated_annual_maintenance', sa.Numeric(10, 2), nullable=True),
        sa.Column('estimated_consumables_yearly', sa.Numeric(10, 2), nullable=True),
        sa.Column('estimated_energy_yearly', sa.Numeric(10, 2), nullable=True),
        sa.Column('total_cost_year_1', sa.Numeric(12, 2), nullable=True),
        sa.Column('total_cost_5_years', sa.Numeric(12, 2), nullable=True),
        sa.Column('currency', sa.String(10), default='CHF', nullable=False),

        # Business case
        sa.Column('revenue_impact', sa.Text(), nullable=True),
        sa.Column('productivity_gain', sa.Text(), nullable=True),
        sa.Column('risk_if_not_acquired', sa.Text(), nullable=True),
        sa.Column('alternatives_considered', sa.Text(), nullable=True),

        # Approval
        sa.Column('requires_board_approval', sa.Boolean(), default=False),
        sa.Column('approved_by', sa.String(100), nullable=True),
        sa.Column('approved_date', sa.Date(), nullable=True),
        sa.Column('approval_notes', sa.Text(), nullable=True),

        # Links
        sa.Column('purchase_order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('purchase_orders.id', ondelete='SET NULL'), nullable=True),
        sa.Column('equipment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('equipment.id', ondelete='SET NULL'), nullable=True),

        # Post-acquisition
        sa.Column('review_date', sa.Date(), nullable=True),
        sa.Column('actual_vs_expected', sa.Text(), nullable=True),
        sa.Column('lessons_learned', sa.Text(), nullable=True),
        sa.Column('would_recommend', sa.Boolean(), nullable=True),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('internal_notes', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_equipment_acquisitions_request_number', 'equipment_acquisitions', ['request_number'])
    op.create_index('ix_equipment_acquisitions_status', 'equipment_acquisitions', ['status'])
    op.create_index('ix_equipment_acquisitions_requested_by', 'equipment_acquisitions', ['requested_by'])

    # NOTE: lab_test_id FK removed from batches model
    # The relationship is now LabTestModel.batch_id -> BatchModel.id (one-to-many)


def downgrade() -> None:
    # Drop tables in reverse order (shift_sessions handled separately)
    op.drop_table('equipment_acquisitions')
    op.drop_table('maintenance_events')
    op.drop_table('equipment')
    op.drop_table('shipments')
    op.drop_table('customs_clearances')
    op.drop_table('purchase_orders')
    op.drop_table('equipment_suppliers')
    op.drop_table('trace_events')
    op.drop_table('traceable_items')
    op.drop_table('lab_tests')
    op.drop_table('batches')
    op.drop_table('farms')

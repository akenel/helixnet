# File: src/schemas/equipment_supply_chain_schema.py
"""
EQUIPMENT SUPPLY CHAIN — YUKI & CHARLIE'S DOMAIN
=================================================

THE IMPORT TEAM:
- CHARLIE: 3rd eye, sees the path, rides the containers
- YUKI: Night shift guy, knows the ports, has the contacts
- KA-MAKI: Customs liaison, Swiss-Japanese precision
- COOLIE: The parts guy, 15,000 pieces from Japan
- MARCO: Assembly, installation, "I have the machines"
- BORRIS: Custom fabrication, local builds

THE PAIN POINT:
Equipment is the biggest pain in the ass.
- Alibaba salad bars (3 months, China, 40ft container)
- COOLIE parts (specialty, Japan, 20ft)
- Borris custom (2 weeks, local)
- Milking machines (1 goat = hand, 100 goats = machine)

THE LIFECYCLE:
Food: SEED → EAT → COMPOST (days)
Equipment: ORDER → SHIP → CUSTOMS → INSTALL → MAINTAIN → REPLACE (years)

SAME SPINE. DIFFERENT SCALE. DIFFERENT TIME.

Scene 43-47: YUKI & CHARLIE — The Container Run
Built 5AM Dec 11, 2025
Tiger & Leo at the crossroads

BE WATER, MY FRIEND.
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date, timedelta
from uuid import UUID, uuid4
from typing import Optional, Any
from enum import Enum
from decimal import Decimal


# ================================================================
# ENUMS — THE EQUIPMENT WORLD
# ================================================================

class EquipmentTypeEnum(str, Enum):
    """What kind of equipment"""
    # Food service
    SALAD_BAR = "salad_bar"              # The main event
    FRIDGE_BAR = "fridge_bar"            # Smaller, grab-and-go
    COFFEE_STATION = "coffee_station"    # JURA COOLIE hybrid
    VENDING_MACHINE = "vending_machine"  # Marco's domain

    # Kitchen
    PREP_TABLE = "prep_table"
    PIZZA_OVEN = "pizza_oven"            # Molly's cookie oven
    MIXER = "mixer"
    SLICER = "slicer"

    # Farm
    MILKING_MACHINE = "milking_machine"  # 1 goat hand, 100 goats machine
    IRRIGATION = "irrigation"
    GREENHOUSE = "greenhouse"
    COMPOST_SYSTEM = "compost_system"

    # Storage
    WALK_IN_FRIDGE = "walk_in_fridge"
    FREEZER = "freezer"
    LOCKER_UNIT = "locker_unit"          # Drop box system

    # Lab
    LAB_EQUIPMENT = "lab_equipment"      # Felix's testing gear

    # Cleaning
    ROBOT_CLEANER = "robot_cleaner"      # SAL's night clean service
    DISHWASHER = "dishwasher"

    # Other
    JUKEBOX = "jukebox"                  # Toast but clean
    CUSTOM = "custom"                    # Borris specials


class EquipmentStatusEnum(str, Enum):
    """Where is it in the lifecycle"""
    # Pre-arrival
    PLANNED = "planned"                  # On the wishlist
    ORDERED = "ordered"                  # PO sent
    MANUFACTURING = "manufacturing"      # Being built
    READY_TO_SHIP = "ready_to_ship"      # At supplier

    # In transit
    IN_TRANSIT = "in_transit"            # On the water/road
    AT_PORT = "at_port"                  # Waiting customs
    CUSTOMS_HOLD = "customs_hold"        # Ka-Maki working on it
    CUSTOMS_CLEARED = "customs_cleared"  # Good to go

    # Post-arrival
    IN_WAREHOUSE = "in_warehouse"        # Waiting assembly
    ASSEMBLING = "assembling"            # Marco working
    TESTING = "testing"                  # Making sure it works
    READY_TO_INSTALL = "ready_to_install"

    # Installed
    INSTALLING = "installing"            # At the site
    INSTALLED = "installed"              # Working!
    OPERATIONAL = "operational"          # In daily use

    # Maintenance
    NEEDS_MAINTENANCE = "needs_maintenance"
    UNDER_REPAIR = "under_repair"
    WAITING_PARTS = "waiting_parts"      # COOLIE getting parts

    # End of life
    DECOMMISSIONED = "decommissioned"
    SOLD = "sold"
    SCRAPPED = "scrapped"


class SupplierTypeEnum(str, Enum):
    """What kind of supplier"""
    MANUFACTURER = "manufacturer"        # Makes the thing (Alibaba factory)
    DISTRIBUTOR = "distributor"          # Sells the thing (middleman)
    FABRICATOR = "fabricator"            # Custom builds (Borris)
    PARTS = "parts"                      # Just parts (COOLIE)
    SERVICE = "service"                  # Maintenance/repair
    REFURB = "refurb"                    # Used/refurbished


class ShipmentTypeEnum(str, Enum):
    """How it travels"""
    # Small
    PARCEL = "parcel"                    # DHL, FedEx box
    PALLET = "pallet"                    # Single pallet, truck

    # Medium
    MULTI_PALLET = "multi_pallet"        # Several pallets
    LTL = "ltl"                          # Less than truckload
    FTL = "ftl"                          # Full truckload

    # Large (containers)
    CONTAINER_10FT = "container_10ft"    # Small container
    CONTAINER_20FT = "container_20ft"    # Standard (YUKI & CHARLIE ride this)
    CONTAINER_40FT = "container_40ft"    # Big boy (Alibaba bulk)
    CONTAINER_40FT_HC = "container_40ft_hc"  # High cube

    # Special
    AIR_FREIGHT = "air_freight"          # Expensive, fast
    HAND_CARRY = "hand_carry"            # Charlie's backpack


class ShipmentStatusEnum(str, Enum):
    """Where is the shipment"""
    PENDING = "pending"                  # Not shipped yet
    PICKED_UP = "picked_up"              # Left supplier
    IN_TRANSIT_LAND = "in_transit_land"  # On truck/rail
    IN_TRANSIT_SEA = "in_transit_sea"    # On the water
    IN_TRANSIT_AIR = "in_transit_air"    # Flying
    AT_ORIGIN_PORT = "at_origin_port"    # Yokohama
    AT_DESTINATION_PORT = "at_dest_port" # Rotterdam
    CUSTOMS_PENDING = "customs_pending"  # Waiting clearance
    CUSTOMS_INSPECTION = "customs_inspection"  # Being checked
    CUSTOMS_CLEARED = "customs_cleared"  # Ka-Maki magic
    CUSTOMS_HELD = "customs_held"        # Problem
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"              # At warehouse
    RECEIVED = "received"                # Checked in


class CustomsStatusEnum(str, Enum):
    """Ka-Maki's world"""
    NOT_REQUIRED = "not_required"        # Local/EU
    PENDING = "pending"                  # Waiting
    DOCUMENTS_SUBMITTED = "docs_submitted"
    UNDER_REVIEW = "under_review"
    INSPECTION_REQUIRED = "inspection_required"
    INSPECTING = "inspecting"
    DUTIES_CALCULATED = "duties_calculated"
    DUTIES_PAID = "duties_paid"
    CLEARED = "cleared"                  # Good!
    HELD = "held"                        # Problem
    REJECTED = "rejected"                # Big problem


class POStatusEnum(str, Enum):
    """Purchase order status"""
    DRAFT = "draft"                      # Felix thinking about it
    SUBMITTED = "submitted"              # Sent to supplier
    CONFIRMED = "confirmed"              # Supplier says OK
    IN_PRODUCTION = "in_production"      # Being made
    READY = "ready"                      # Ready to ship
    PARTIALLY_SHIPPED = "partially_shipped"
    SHIPPED = "shipped"                  # On the way
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"                # Got it all
    CANCELLED = "cancelled"
    DISPUTED = "disputed"                # Problem


class MaintenanceTypeEnum(str, Enum):
    """What kind of maintenance"""
    PREVENTIVE = "preventive"            # Scheduled
    CORRECTIVE = "corrective"            # It broke
    EMERGENCY = "emergency"              # URGENT
    INSPECTION = "inspection"            # Just checking
    CALIBRATION = "calibration"          # Lab equipment
    CLEANING = "cleaning"                # Deep clean
    UPGRADE = "upgrade"                  # Making it better


# ================================================================
# SUPPLIER — Where Equipment Comes From
# ================================================================

class SupplierBase(BaseModel):
    """
    A supplier in the network.
    Alibaba, COOLIE Japan, Borris Custom, etc.
    """
    name: str = Field(..., max_length=200)
    code: str = Field(..., max_length=20)  # ALI, COOLIE, BORRIS
    supplier_type: SupplierTypeEnum

    # Location
    country: str = Field(..., max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None

    # Contact
    contact_name: Optional[str] = Field(None, max_length=100)
    contact_email: Optional[str] = Field(None, max_length=200)
    contact_phone: Optional[str] = Field(None, max_length=50)

    # Business
    website: Optional[str] = None
    payment_terms: str = Field(default="Net 30", max_length=50)
    currency: str = Field(default="USD", max_length=10)

    # Logistics
    typical_lead_time_days: int = Field(default=30, ge=0)
    ships_via: list[ShipmentTypeEnum] = []

    # Quality
    is_verified: bool = False
    quality_rating: Optional[int] = Field(None, ge=1, le=5)

    # Specialties
    equipment_types: list[EquipmentTypeEnum] = []
    specialties: list[str] = []  # "coffee machines", "custom fabrication"

    # Notes
    notes: Optional[str] = None

    # The network connection
    referred_by: Optional[str] = None  # "COOLIE", "YUKI"


class SupplierCreate(SupplierBase):
    pass


class SupplierRead(SupplierBase):
    id: UUID
    total_orders: int = 0
    total_spent: Decimal = Decimal("0.00")
    on_time_rate: float = 0.0
    is_active: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# EQUIPMENT — The Thing Itself
# ================================================================

class EquipmentBase(BaseModel):
    """
    A piece of equipment in the network.
    Salad bar, coffee machine, milking machine, etc.
    """
    name: str = Field(..., max_length=200)
    equipment_type: EquipmentTypeEnum

    # Identity
    serial_number: Optional[str] = Field(None, max_length=100)
    model_number: Optional[str] = Field(None, max_length=100)
    manufacturer: Optional[str] = Field(None, max_length=200)

    # Source
    supplier_id: Optional[UUID] = None
    po_id: Optional[UUID] = None  # Which order brought it

    # Status
    status: EquipmentStatusEnum = EquipmentStatusEnum.PLANNED

    # Location
    current_location_type: str = Field(default="unknown", max_length=50)
    current_location_id: Optional[UUID] = None
    current_location_name: Optional[str] = None

    # Installation
    installed_at_id: Optional[UUID] = None  # Which bar/farm
    installed_at_name: Optional[str] = None
    installed_date: Optional[date] = None
    installed_by: Optional[str] = None  # "Marco"

    # Specs
    dimensions_cm: Optional[str] = None  # "200x80x120"
    weight_kg: Optional[float] = None
    power_requirements: Optional[str] = None  # "220V, 16A"
    capacity: Optional[str] = None  # "50 salads/hour"

    # Value
    purchase_price: Optional[Decimal] = None
    currency: str = Field(default="CHF", max_length=10)
    warranty_until: Optional[date] = None

    # Maintenance
    last_maintenance: Optional[date] = None
    next_maintenance_due: Optional[date] = None
    maintenance_interval_days: int = Field(default=90, ge=0)

    # Documentation
    manual_url: Optional[str] = None
    photos: list[str] = []

    # Notes
    notes: Optional[str] = None

    # Custom (Borris specials)
    is_custom: bool = False
    custom_specs: Optional[str] = None


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentRead(EquipmentBase):
    id: UUID
    age_days: int = 0
    maintenance_events: int = 0
    downtime_hours: float = 0.0
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# PURCHASE ORDER — What We Want
# ================================================================

class POLineItem(BaseModel):
    """One item on a purchase order"""
    line_number: int = Field(..., ge=1)

    # What
    description: str = Field(..., max_length=500)
    equipment_type: Optional[EquipmentTypeEnum] = None
    part_number: Optional[str] = Field(None, max_length=100)

    # How many
    quantity: int = Field(..., ge=1)
    unit: str = Field(default="each", max_length=20)

    # Price
    unit_price: Decimal = Field(..., ge=0)
    currency: str = Field(default="USD", max_length=10)
    line_total: Decimal = Field(..., ge=0)

    # Status
    quantity_shipped: int = Field(default=0, ge=0)
    quantity_received: int = Field(default=0, ge=0)

    # Notes
    notes: Optional[str] = None


class PurchaseOrderBase(BaseModel):
    """
    A purchase order to a supplier.
    "Felix says add these 2-3 items to Mosey shipment"
    """
    po_number: str = Field(..., max_length=50)

    # Who
    supplier_id: UUID
    supplier_name: str = Field(..., max_length=200)

    # Requested by
    requested_by: str = Field(..., max_length=100)  # "Felix"
    requested_date: date = Field(default_factory=date.today)

    # For whom
    destination_type: str = Field(..., max_length=50)  # "bar", "farm", "warehouse"
    destination_id: Optional[UUID] = None
    destination_name: str = Field(..., max_length=200)  # "Mosey 420", "Artemis"

    # Items
    line_items: list[POLineItem] = []

    # Totals
    subtotal: Decimal = Field(default=Decimal("0.00"))
    shipping_cost: Decimal = Field(default=Decimal("0.00"))
    duties_estimate: Decimal = Field(default=Decimal("0.00"))
    total: Decimal = Field(default=Decimal("0.00"))
    currency: str = Field(default="USD", max_length=10)

    # Status
    status: POStatusEnum = POStatusEnum.DRAFT

    # Dates
    expected_ship_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    actual_ship_date: Optional[date] = None
    actual_delivery_date: Optional[date] = None

    # Shipping preference
    preferred_shipment_type: Optional[ShipmentTypeEnum] = None

    # Consolidation (add to existing shipment)
    consolidate_with_po: Optional[str] = None  # "Add to Mosey shipment"

    # Notes
    notes: Optional[str] = None
    internal_notes: Optional[str] = None  # "YUKI handling this one"


class PurchaseOrderCreate(PurchaseOrderBase):
    pass


class PurchaseOrderRead(PurchaseOrderBase):
    id: UUID
    items_count: int = 0
    items_shipped: int = 0
    items_received: int = 0
    shipment_ids: list[UUID] = []
    is_complete: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# SHIPMENT — How It Travels
# ================================================================

class ShipmentBase(BaseModel):
    """
    A shipment from supplier to destination.
    Charlie & YUKI ride the 20ft container.
    """
    shipment_number: str = Field(..., max_length=50)

    # Type
    shipment_type: ShipmentTypeEnum

    # Container details (if applicable)
    container_number: Optional[str] = Field(None, max_length=50)
    container_size: Optional[str] = None  # "20ft", "40ft"
    seal_number: Optional[str] = Field(None, max_length=50)

    # Carrier
    carrier_name: str = Field(..., max_length=200)  # "Maersk", "DHL"
    carrier_tracking: Optional[str] = Field(None, max_length=100)
    vessel_name: Optional[str] = Field(None, max_length=100)  # Ship name
    voyage_number: Optional[str] = Field(None, max_length=50)

    # Route
    origin_country: str = Field(..., max_length=100)
    origin_city: str = Field(..., max_length=100)
    origin_port: Optional[str] = Field(None, max_length=100)  # "Yokohama"

    destination_country: str = Field(..., max_length=100)
    destination_city: str = Field(..., max_length=100)
    destination_port: Optional[str] = Field(None, max_length=100)  # "Rotterdam"

    final_destination: str = Field(..., max_length=200)  # "Zurich warehouse"
    final_destination_id: Optional[UUID] = None

    # Status
    status: ShipmentStatusEnum = ShipmentStatusEnum.PENDING

    # Contents
    po_ids: list[UUID] = []  # Which POs are in this shipment
    equipment_ids: list[UUID] = []  # Which equipment
    total_pieces: int = Field(default=0, ge=0)
    total_weight_kg: Optional[float] = None
    total_volume_cbm: Optional[float] = None  # Cubic meters

    # Value
    declared_value: Optional[Decimal] = None
    currency: str = Field(default="USD", max_length=10)

    # Dates
    ship_date: Optional[date] = None
    eta_port: Optional[date] = None
    eta_destination: Optional[date] = None
    actual_arrival_port: Optional[date] = None
    actual_arrival_destination: Optional[date] = None

    # Customs
    requires_customs: bool = True
    customs_clearance_id: Optional[UUID] = None

    # Special cargo
    is_hazardous: bool = False
    is_fragile: bool = False
    temperature_controlled: bool = False
    temperature_range: Optional[str] = None  # "2-8C"

    # Insurance
    is_insured: bool = False
    insurance_value: Optional[Decimal] = None

    # The human element
    handled_by: Optional[str] = None  # "YUKI"
    passengers: list[str] = []  # ["CHARLIE"] (hidden in container, shhh)

    # Notes
    notes: Optional[str] = None


class ShipmentCreate(ShipmentBase):
    pass


class ShipmentRead(ShipmentBase):
    id: UUID
    transit_days: int = 0
    is_delayed: bool = False
    delay_reason: Optional[str] = None
    customs_status: Optional[CustomsStatusEnum] = None
    is_delivered: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# CUSTOMS CLEARANCE — Ka-Maki's Domain
# ================================================================

class CustomsDocument(BaseModel):
    """A document for customs"""
    doc_type: str = Field(..., max_length=50)  # "commercial_invoice", "packing_list"
    doc_number: Optional[str] = Field(None, max_length=100)
    file_url: Optional[str] = None
    is_submitted: bool = False
    is_approved: bool = False
    notes: Optional[str] = None


class CustomsClearanceBase(BaseModel):
    """
    Customs clearance for a shipment.
    Ka-Maki from Luzern. Swiss-Japanese precision.
    """
    clearance_number: str = Field(..., max_length=50)

    # What shipment
    shipment_id: UUID
    shipment_number: str = Field(..., max_length=50)

    # Where
    port_of_entry: str = Field(..., max_length=100)  # "Rotterdam", "Zurich Airport"
    customs_office: Optional[str] = Field(None, max_length=200)

    # Who's handling
    customs_agent: str = Field(..., max_length=100)  # "Ka-Maki"
    agent_company: Optional[str] = Field(None, max_length=200)
    agent_contact: Optional[str] = Field(None, max_length=200)

    # Status
    status: CustomsStatusEnum = CustomsStatusEnum.PENDING

    # Documents
    documents: list[CustomsDocument] = []
    documents_complete: bool = False

    # Classification
    hs_codes: list[str] = []  # Harmonized System codes

    # Duties & Taxes
    duties_calculated: bool = False
    import_duty: Decimal = Field(default=Decimal("0.00"))
    vat: Decimal = Field(default=Decimal("0.00"))
    other_fees: Decimal = Field(default=Decimal("0.00"))
    total_duties: Decimal = Field(default=Decimal("0.00"))
    currency: str = Field(default="CHF", max_length=10)

    duties_paid: bool = False
    duties_paid_date: Optional[date] = None
    duties_paid_by: Optional[str] = None

    # Inspection
    inspection_required: bool = False
    inspection_date: Optional[date] = None
    inspection_result: Optional[str] = None
    inspection_notes: Optional[str] = None

    # Timeline
    submitted_date: Optional[date] = None
    cleared_date: Optional[date] = None

    # Issues
    has_issues: bool = False
    issue_description: Optional[str] = None
    issue_resolution: Optional[str] = None

    # Notes
    notes: Optional[str] = None


class CustomsClearanceCreate(CustomsClearanceBase):
    pass


class CustomsClearanceRead(CustomsClearanceBase):
    id: UUID
    processing_days: int = 0
    is_cleared: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# MAINTENANCE — Keeping It Running
# ================================================================

class MaintenanceEventBase(BaseModel):
    """
    A maintenance event on equipment.
    When things break, COOLIE gets the parts.
    """
    # What equipment
    equipment_id: UUID
    equipment_name: str = Field(..., max_length=200)

    # Type
    maintenance_type: MaintenanceTypeEnum

    # Description
    title: str = Field(..., max_length=200)
    description: Optional[str] = None

    # Who
    performed_by: str = Field(..., max_length=100)  # "Marco"

    # When
    scheduled_date: Optional[date] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Status
    status: str = Field(default="scheduled", max_length=20)

    # Parts used
    parts_used: list[str] = []
    parts_cost: Decimal = Field(default=Decimal("0.00"))

    # Labor
    labor_hours: float = Field(default=0.0, ge=0)
    labor_cost: Decimal = Field(default=Decimal("0.00"))

    # Total
    total_cost: Decimal = Field(default=Decimal("0.00"))
    currency: str = Field(default="CHF", max_length=10)

    # Result
    issue_found: Optional[str] = None
    action_taken: Optional[str] = None
    result: Optional[str] = None  # "Fixed", "Needs parts", "Replaced"

    # Follow-up
    follow_up_required: bool = False
    follow_up_notes: Optional[str] = None
    next_maintenance_date: Optional[date] = None

    # Parts ordered
    parts_order_id: Optional[UUID] = None  # PO for parts
    waiting_for_parts: bool = False

    # Photos
    before_photos: list[str] = []
    after_photos: list[str] = []

    # Notes
    notes: Optional[str] = None


class MaintenanceEventCreate(MaintenanceEventBase):
    pass


class MaintenanceEventRead(MaintenanceEventBase):
    id: UUID
    downtime_hours: float = 0.0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# PARTS INVENTORY — COOLIE's 15,000 Pieces
# ================================================================

class PartBase(BaseModel):
    """
    A part that can be used for maintenance.
    COOLIE has 15,000 of these from Japan.
    """
    part_number: str = Field(..., max_length=100)
    name: str = Field(..., max_length=200)
    description: Optional[str] = None

    # For what equipment
    equipment_types: list[EquipmentTypeEnum] = []
    compatible_models: list[str] = []

    # Source
    supplier_id: Optional[UUID] = None
    supplier_name: Optional[str] = None
    manufacturer_part_number: Optional[str] = Field(None, max_length=100)

    # Stock
    quantity_in_stock: int = Field(default=0, ge=0)
    minimum_stock: int = Field(default=1, ge=0)
    reorder_point: int = Field(default=2, ge=0)

    # Location
    storage_location: Optional[str] = None  # "Warehouse A, Shelf 3"

    # Price
    unit_cost: Optional[Decimal] = None
    currency: str = Field(default="CHF", max_length=10)

    # Lead time
    lead_time_days: int = Field(default=14, ge=0)

    # Notes
    notes: Optional[str] = None


class PartRead(PartBase):
    id: UUID
    times_used: int = 0
    last_used: Optional[date] = None
    is_low_stock: bool = False
    is_active: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# WAREHOUSE — Where Equipment Lives Before Installation
# ================================================================

class WarehouseBase(BaseModel):
    """
    A warehouse in the network.
    Where containers get unpacked, equipment assembled.
    """
    name: str = Field(..., max_length=200)
    code: str = Field(..., max_length=20)

    # Location
    address: str = Field(..., max_length=300)
    city: str = Field(..., max_length=100)
    country: str = Field(default="Switzerland", max_length=100)

    # Contact
    manager_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)

    # Capacity
    total_area_sqm: Optional[float] = None
    storage_capacity: Optional[str] = None

    # Capabilities
    can_receive_containers: bool = True
    has_forklift: bool = True
    has_assembly_area: bool = True
    has_testing_area: bool = False

    # Who works here
    assembly_team: list[str] = []  # ["Marco", "helper 1"]

    # Notes
    notes: Optional[str] = None


class WarehouseRead(WarehouseBase):
    id: UUID
    equipment_count: int = 0
    parts_count: int = 0
    pending_shipments: int = 0
    is_active: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# DASHBOARDS — The Big Picture
# ================================================================

class EquipmentDashboard(BaseModel):
    """Equipment overview"""
    # Counts
    total_equipment: int = 0
    equipment_operational: int = 0
    equipment_needs_maintenance: int = 0
    equipment_under_repair: int = 0
    equipment_in_transit: int = 0

    # Orders
    open_purchase_orders: int = 0
    total_on_order_value: Decimal = Decimal("0.00")

    # Shipments
    shipments_in_transit: int = 0
    shipments_at_customs: int = 0
    shipments_arriving_this_week: int = 0

    # Maintenance
    maintenance_due_this_week: int = 0
    overdue_maintenance: int = 0

    # Parts
    parts_low_stock: int = 0
    parts_on_order: int = 0

    # Value
    total_equipment_value: Decimal = Decimal("0.00")
    monthly_maintenance_cost: Decimal = Decimal("0.00")


class SupplyChainDashboard(BaseModel):
    """Full supply chain view"""
    # Pipeline
    pos_pending: int = 0
    pos_value_pending: Decimal = Decimal("0.00")

    shipments_active: int = 0
    containers_on_water: int = 0

    customs_pending: int = 0
    customs_avg_days: float = 0.0

    # Performance
    on_time_delivery_rate: float = 0.0
    avg_lead_time_days: float = 0.0

    # Costs
    ytd_equipment_spend: Decimal = Decimal("0.00")
    ytd_duties_paid: Decimal = Decimal("0.00")
    ytd_shipping_cost: Decimal = Decimal("0.00")


# ================================================================
# THE NETWORK — How It All Connects
# ================================================================

THE_EQUIPMENT_NETWORK = """
THE EQUIPMENT SUPPLY CHAIN
============================================================

THE TEAM:
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  CHARLIE    YUKI       KA-MAKI     COOLIE      MARCO       │
│  (3rd eye)  (ports)    (customs)   (parts)     (assembly)  │
│     │          │           │          │           │        │
│     └──────────┴───────────┴──────────┴───────────┘        │
│                        │                                    │
│                   THE IMPORT TEAM                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘

THE FLOW:
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  FELIX: "Add 2-3 items to Mosey shipment"                  │
│     │                                                       │
│     ▼                                                       │
│  PURCHASE ORDER ─────────► SUPPLIER                         │
│     │                      (Alibaba, COOLIE, Borris)        │
│     │                           │                           │
│     │                           ▼                           │
│     │                      MANUFACTURING                    │
│     │                           │                           │
│     │                           ▼                           │
│     │                      READY TO SHIP                    │
│     │                           │                           │
│     ▼                           ▼                           │
│  SHIPMENT ◄─────────────── CONTAINER LOADED                │
│     │                      (YUKI & CHARLIE ride along)      │
│     │                           │                           │
│     │                           ▼                           │
│     │                      IN TRANSIT (sea)                 │
│     │                      Yokohama → Rotterdam             │
│     │                           │                           │
│     │                           ▼                           │
│     │                      AT PORT                          │
│     │                           │                           │
│     ▼                           ▼                           │
│  CUSTOMS ◄──────────────── KA-MAKI                         │
│     │                      (Swiss-Japanese precision)       │
│     │                           │                           │
│     │                           ▼                           │
│     │                      CLEARED!                         │
│     │                           │                           │
│     ▼                           ▼                           │
│  WAREHOUSE ◄─────────────── DELIVERED                       │
│     │                      (Marco waiting)                  │
│     │                           │                           │
│     │                           ▼                           │
│     │                      ASSEMBLED                        │
│     │                           │                           │
│     │                           ▼                           │
│     │                      TESTED                           │
│     │                           │                           │
│     ▼                           ▼                           │
│  INSTALLATION ◄──────────── AT THE BAR/FARM                │
│     │                      (SAL's new salad bar!)           │
│     │                           │                           │
│     │                           ▼                           │
│     ▼                      OPERATIONAL                      │
│  MAINTENANCE ◄─────────────────┘                           │
│     │                                                       │
│     │  (When it breaks)                                     │
│     │       │                                               │
│     │       ▼                                               │
│     │  COOLIE: "I have the parts"                          │
│     │       │                                               │
│     │       ▼                                               │
│     └──► FIXED!                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘

SAME SPINE. DIFFERENT LIFECYCLE.

Food: Days (seed → eat → compost)
Equipment: Years (order → install → maintain → replace)

============================================================
"""


# ================================================================
# EXAMPLE: The Mosey Shipment
# ================================================================

EXAMPLE_MOSEY_SHIPMENT = """
EXAMPLE: MOSEY 420 EQUIPMENT ORDER
============================================================

Felix says: "Add these to the Mosey shipment"

PURCHASE ORDER: PO-2025-MOSEY-003
├── Supplier: Alibaba (ALI-FOOD-EQUIP)
├── Destination: Mosey 420, Zurich
├── Requested by: Felix
│
├── LINE ITEMS:
│   1. Alibaba Salad Bar Model X (qty: 3) - $2,400 each
│   2. Fridge display unit (qty: 2) - $800 each
│   3. CBD display case (qty: 1) - $350
│
├── Subtotal: $9,150
├── Shipping: $1,200 (container share)
├── Duties estimate: CHF 850
├── TOTAL: ~$11,200
│
└── Notes: "Consolidate with COOLIE parts shipment"

SHIPMENT: SHIP-2025-YC-047
├── Type: 20ft container
├── Container: MSCU-7749-COOLIE
├── Route: Yokohama → Rotterdam → Zurich
│
├── CONTENTS:
│   - 3x Alibaba Salad Bars (PO-2025-MOSEY-003)
│   - COOLIE coffee parts (15,000 pieces)
│   - 2x Fridge units
│   - 1x CBD display
│   - [PASSENGERS: CHARLIE, YUKI] (shhh)
│
├── Carrier: Maersk
├── Vessel: MSC AURORA
├── ETD: Dec 15, 2025
├── ETA Rotterdam: Jan 8, 2026
├── ETA Zurich: Jan 12, 2026
│
└── Handled by: YUKI

CUSTOMS: CC-2025-ROT-1247
├── Port: Rotterdam
├── Agent: Ka-Maki (Luzern exchange program)
├── Status: Documents submitted
│
├── HS Codes:
│   - 8418.50 (refrigeration equipment)
│   - 8419.81 (food prep equipment)
│
├── Duties: CHF 847.50
├── VAT: CHF 712.00
├── TOTAL: CHF 1,559.50
│
└── Notes: "Clean paperwork. COOLIE always delivers."

ARRIVAL:
├── Warehouse: Zurich Central
├── Received by: Marco
├── Assembly time: 3 days
├── Testing: 1 day
│
└── Installation at Mosey 420: Jan 18, 2026

============================================================

Charlie: "We made it."
YUKI: "Welcome to Switzerland."
Ka-Maki: "Zugelassen. Approved."
Marco: "I have the machines."
Felix: "Oh what a beautiful day!"

============================================================
"""


# ================================================================
# CONNECT TO THE SPINE
# ================================================================

"""
HOW EQUIPMENT CONNECTS TO THE E2E SPINE:

Equipment gets TraceEvents too:
├── ORDERED (PO created)
├── SHIPPED (container loaded)
├── IN_TRANSIT (on the water)
├── CUSTOMS (Ka-Maki working)
├── CLEARED (approved)
├── DELIVERED (at warehouse)
├── ASSEMBLED (Marco working)
├── INSTALLED (at the bar)
├── OPERATIONAL (making salads!)
├── MAINTENANCE (scheduled check)
├── REPAIRED (COOLIE parts)
└── DECOMMISSIONED (end of life)

Same TraceEvent schema.
Same ItemChain concept.
Different lifecycle (years vs days).

The salad bar that serves Thommy's salad?
It has its own journey too.
From Alibaba factory → Yokohama port → Rotterdam → Zurich → SAL's bar.

EVERYTHING TRACKED.
EVERYONE RECORDED.
NOTHING LOST.

BE WATER, MY FRIEND.
"""

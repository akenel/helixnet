# File: src/schemas/shift_checklist_schema.py
"""
🧹 PAM-PROOF SHIFT CHECKLIST
============================

The Scene:
- Felix needs soap → NONE
- Felix needs ice → NONE
- Felix needs HIS bottle → EMPTY (Pam & Rafi drank it)
- Pam doesn't know how to clean
- Pam doesn't know where new items go

The Solution:
- Checklist Pam MUST complete before leaving
- Photo proof required for cleaning
- Inventory alerts for supplies
- Personal items marked DO NOT TOUCH
- Shelf location guide with pictures

No more PAM PAM PAM at midnight.

🦁🐅 Built at the crossroads.
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional
from enum import Enum


# ================================================================
# ENUMS
# ================================================================

class ChecklistStatusEnum(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"       # With reason
    BLOCKED = "blocked"       # Can't do - supply missing


class TaskPriorityEnum(str, Enum):
    MUST_DO = "must_do"       # Cannot leave without
    SHOULD_DO = "should_do"   # Expected
    NICE_TO_HAVE = "nice"     # If time permits


class ShiftTypeEnum(str, Enum):
    OPENING = "opening"
    CLOSING = "closing"
    MIDDAY = "midday"
    DELIVERY = "delivery"     # Special checklist for delivery days


class SupplyStatusEnum(str, Enum):
    OK = "ok"
    LOW = "low"
    OUT = "out"
    ORDERED = "ordered"


class OwnershipEnum(str, Enum):
    SHOP = "shop"             # Shop property
    FELIX = "felix"           # DO NOT TOUCH
    SHARED = "shared"         # Everyone can use
    CUSTOMER = "customer"     # Reserved for customer


# ================================================================
# CHECKLIST TASK SCHEMAS
# ================================================================

class ChecklistTaskBase(BaseModel):
    """One task in the checklist"""
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    instructions: Optional[str] = None  # How to do it (for Pam)
    location: Optional[str] = Field(None, max_length=100)  # Where
    priority: TaskPriorityEnum = TaskPriorityEnum.SHOULD_DO
    requires_photo: bool = False  # Proof of completion
    requires_supply: Optional[str] = None  # e.g., "soap", "ice"
    estimated_minutes: int = Field(default=5, ge=1)


class ChecklistTaskCreate(ChecklistTaskBase):
    shift_type: ShiftTypeEnum
    order: int = Field(default=0, ge=0)  # Display order


class ChecklistTaskComplete(BaseModel):
    """Pam completing a task"""
    task_id: UUID
    status: ChecklistStatusEnum
    photo_url: Optional[str] = None  # Proof
    notes: Optional[str] = None
    skip_reason: Optional[str] = None  # If skipped
    blocked_reason: Optional[str] = None  # If blocked (no soap!)
    completed_by: str = Field(default="Pam", max_length=100)
    completed_at: datetime = Field(default_factory=datetime.utcnow)


class ChecklistTaskRead(ChecklistTaskBase):
    id: UUID
    shift_type: ShiftTypeEnum
    order: int
    status: ChecklistStatusEnum
    photo_url: Optional[str] = None
    notes: Optional[str] = None
    skip_reason: Optional[str] = None
    blocked_reason: Optional[str] = None
    completed_by: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# SHIFT CHECKLIST SCHEMAS
# ================================================================

class ShiftChecklistCreate(BaseModel):
    """Start a shift checklist"""
    shift_type: ShiftTypeEnum
    date: datetime = Field(default_factory=datetime.utcnow)
    assigned_to: str = Field(default="Pam", max_length=100)
    notes: Optional[str] = None


class ShiftChecklistRead(BaseModel):
    """Full shift checklist with all tasks"""
    id: UUID
    shift_type: ShiftTypeEnum
    date: datetime
    assigned_to: str
    status: ChecklistStatusEnum
    tasks: list[ChecklistTaskRead]
    tasks_total: int
    tasks_completed: int
    tasks_blocked: int
    tasks_skipped: int
    can_leave: bool  # True only if all MUST_DO tasks done
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ShiftHandover(BaseModel):
    """Handover notes from one shift to next"""
    from_shift_id: UUID
    to_shift_type: ShiftTypeEnum
    handover_notes: str
    issues_flagged: list[str]  # "No soap", "Ice tray empty"
    supplies_needed: list[str]  # "Buy soap", "Fill ice"
    special_instructions: Optional[str] = None


# ================================================================
# SUPPLY TRACKING (Soap, Ice, etc.)
# ================================================================

class ShopSupplyBase(BaseModel):
    """Track shop supplies - the stuff Pam forgets"""
    name: str = Field(..., max_length=100)
    category: str = Field(..., max_length=50)  # cleaning, drinks, etc.
    location: str = Field(..., max_length=100)  # Where it should be
    min_quantity: int = Field(default=1, ge=0)
    current_quantity: int = Field(default=0, ge=0)
    unit: str = Field(default="piece", max_length=20)
    restock_note: Optional[str] = None  # "Buy at Aldi"


class ShopSupplyCreate(ShopSupplyBase):
    pass


class ShopSupplyUpdate(BaseModel):
    """Update supply - Pam restocks (or doesn't)"""
    supply_id: UUID
    new_quantity: int = Field(..., ge=0)
    updated_by: str = Field(default="Pam", max_length=100)
    notes: Optional[str] = None


class ShopSupplyRead(ShopSupplyBase):
    id: UUID
    status: SupplyStatusEnum
    last_restocked: Optional[datetime] = None
    last_restocked_by: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SupplyAlert(BaseModel):
    """Alert when supply is low/out"""
    supply_id: UUID
    supply_name: str
    status: SupplyStatusEnum
    current_quantity: int
    min_quantity: int
    location: str
    restock_note: Optional[str] = None
    alert_message: str  # "NO SOAP! Buy at Aldi!"


# ================================================================
# PERSONAL ITEMS — DO NOT TOUCH
# ================================================================

class PersonalItemBase(BaseModel):
    """Felix's personal items - DO NOT TOUCH"""
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    location: str = Field(..., max_length=100)
    owner: str = Field(..., max_length=100)  # Felix
    ownership: OwnershipEnum = OwnershipEnum.FELIX
    warning_message: str = Field(
        default="🚫 DO NOT TOUCH - Felix's personal item",
        max_length=200
    )


class PersonalItemCreate(PersonalItemBase):
    pass


class PersonalItemRead(PersonalItemBase):
    id: UUID
    created_at: datetime
    last_checked: Optional[datetime] = None
    last_checked_by: Optional[str] = None
    status: str = Field(default="ok")  # ok, missing, empty, tampered

    model_config = ConfigDict(from_attributes=True)


class PersonalItemCheck(BaseModel):
    """Check personal item status"""
    item_id: UUID
    status: str  # ok, missing, empty, tampered
    checked_by: str = Field(..., max_length=100)
    notes: Optional[str] = None  # "BOTTLE EMPTY - WHO DRANK IT?!"


class PersonalItemAlert(BaseModel):
    """Alert when personal item tampered"""
    item_id: UUID
    item_name: str
    owner: str
    status: str
    alert_message: str  # "🚨 Felix's bottle is EMPTY! Pam & Rafi?!"
    reported_at: datetime


# ================================================================
# SHELF LOCATION GUIDE — Where Things Go
# ================================================================

class ShelfLocationBase(BaseModel):
    """Where items go - so Pam knows"""
    shelf_name: str = Field(..., max_length=100)
    shelf_code: Optional[str] = Field(None, max_length=20)  # A1, B2, etc.
    section: str = Field(..., max_length=100)  # CBD, Accessories, etc.
    row: Optional[int] = None
    description: Optional[str] = None
    photo_url: Optional[str] = None  # Picture of the shelf
    product_categories: list[str] = []  # What goes here


class ShelfLocationCreate(ShelfLocationBase):
    pass


class ShelfLocationRead(ShelfLocationBase):
    id: UUID
    products_count: int = 0
    last_restocked: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductPlacement(BaseModel):
    """Tell Pam where to put product"""
    product_id: UUID
    product_name: str
    shelf_id: UUID
    shelf_name: str
    shelf_code: Optional[str] = None
    section: str
    row: Optional[int] = None
    quantity: int
    instructions: Optional[str] = None  # "Front facing, labels out"
    photo_url: Optional[str] = None  # Example photo


# ================================================================
# CLOSING CHECKLIST — THE BIG ONE
# ================================================================

CLOSING_CHECKLIST_TASKS = [
    {
        "name": "Clean coffee machine",
        "instructions": "1. Empty drip tray\n2. Run cleaning cycle\n3. Wipe exterior",
        "location": "Behind counter",
        "priority": "must_do",
        "requires_photo": True,
        "requires_supply": "coffee_cleaner",
        "estimated_minutes": 10,
    },
    {
        "name": "Fill ice trays",
        "instructions": "Fill ALL ice trays in freezer. Check water level.",
        "location": "Kitchen freezer",
        "priority": "must_do",
        "requires_photo": False,
        "requires_supply": None,
        "estimated_minutes": 2,
    },
    {
        "name": "Restock soap dispensers",
        "instructions": "Check all soap dispensers. Refill if below half.",
        "location": "Bathroom + Kitchen",
        "priority": "must_do",
        "requires_photo": False,
        "requires_supply": "soap",
        "estimated_minutes": 5,
    },
    {
        "name": "Clean display cases",
        "instructions": "Glass cleaner on all display cases. No streaks!",
        "location": "Shop floor",
        "priority": "should_do",
        "requires_photo": True,
        "requires_supply": "glass_cleaner",
        "estimated_minutes": 15,
    },
    {
        "name": "Sweep floors",
        "instructions": "Sweep entire shop floor. Don't forget corners.",
        "location": "Shop floor",
        "priority": "must_do",
        "requires_photo": False,
        "requires_supply": "broom",
        "estimated_minutes": 10,
    },
    {
        "name": "Mop floors",
        "instructions": "Mop after sweeping. Use cleaning solution.",
        "location": "Shop floor",
        "priority": "should_do",
        "requires_photo": True,
        "requires_supply": "mop_solution",
        "estimated_minutes": 15,
    },
    {
        "name": "Empty trash bins",
        "instructions": "All bins. Replace bags. Take trash to back.",
        "location": "All areas",
        "priority": "must_do",
        "requires_photo": False,
        "requires_supply": "trash_bags",
        "estimated_minutes": 10,
    },
    {
        "name": "Restock shelves from delivery",
        "instructions": "New items go on designated shelves. Check placement guide.",
        "location": "Shop floor",
        "priority": "must_do",
        "requires_photo": True,
        "requires_supply": None,
        "estimated_minutes": 30,
    },
    {
        "name": "Check personal items (DO NOT USE)",
        "instructions": "Verify Felix's personal items are untouched. Report if missing/empty.",
        "location": "Office",
        "priority": "must_do",
        "requires_photo": False,
        "requires_supply": None,
        "estimated_minutes": 2,
    },
    {
        "name": "Lock back door",
        "instructions": "Check back door is LOCKED. Test handle.",
        "location": "Back entrance",
        "priority": "must_do",
        "requires_photo": False,
        "requires_supply": None,
        "estimated_minutes": 1,
    },
    {
        "name": "Turn off displays",
        "instructions": "Turn off all display lights except security lights.",
        "location": "Shop floor",
        "priority": "must_do",
        "requires_photo": False,
        "requires_supply": None,
        "estimated_minutes": 2,
    },
    {
        "name": "Set alarm",
        "instructions": "Set alarm. Code is [ASK FELIX]. Wait for beep.",
        "location": "Front entrance",
        "priority": "must_do",
        "requires_photo": False,
        "requires_supply": None,
        "estimated_minutes": 1,
    },
]


class ClosingChecklistSummary(BaseModel):
    """Summary for Felix - did Pam actually do her job?"""
    date: datetime
    assigned_to: str
    shift_type: ShiftTypeEnum = ShiftTypeEnum.CLOSING

    tasks_total: int
    tasks_completed: int
    tasks_skipped: int
    tasks_blocked: int

    must_do_total: int
    must_do_completed: int
    can_leave: bool  # Only True if ALL must_do are done

    supplies_missing: list[str]  # What blocked tasks
    skipped_reasons: list[str]  # Why things were skipped
    personal_items_status: str  # "ok" or "ALERT"

    photos_submitted: int
    photos_required: int

    completion_time: Optional[datetime] = None
    total_minutes: Optional[int] = None

    felix_notes: Optional[str] = None  # Felix's review


# ================================================================
# PAM'S REPORT CARD
# ================================================================

class PamReportCard(BaseModel):
    """Weekly report - how did Pam do?"""
    week_start: datetime
    week_end: datetime

    shifts_assigned: int
    shifts_completed: int
    shifts_missed: int  # "Sick" days

    tasks_total: int
    tasks_completed: int
    tasks_skipped: int
    tasks_blocked: int

    completion_rate: float  # Percentage

    supplies_left_empty: list[str]  # Ice, soap, etc.
    personal_items_incidents: int  # How many times Felix's stuff touched

    average_completion_time: int  # Minutes
    photos_submitted: int

    grade: str  # A, B, C, D, F
    notes: Optional[str] = None

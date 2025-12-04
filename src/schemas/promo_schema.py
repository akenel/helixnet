# File: src/schemas/promo_schema.py
"""
Pydantic schemas for HelixPROMO.
Every penny tracked. Mr. TAXMAN approved.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from uuid import UUID
from typing import Optional
from enum import Enum


# ================================================================
# ENUMS
# ================================================================

class DiscountTypeEnum(str, Enum):
    COMP_OWNER = "comp_owner"
    COMP_VIP = "comp_vip"
    COMP_STAFF = "comp_staff"
    COMP_DAMAGE = "comp_damage"
    PROMO_NEW_CUSTOMER = "promo_new"
    PROMO_LOYALTY = "promo_loyalty"
    PROMO_EVENT = "promo_event"
    PROMO_INFLUENCER = "promo_influencer"
    SAMPLE_PRODUCT = "sample_product"
    SAMPLE_CBD = "sample_cbd"
    WASTE_EXPIRED = "waste_expired"
    WASTE_DAMAGED = "waste_damaged"
    WASTE_THEFT = "waste_theft"
    WASTE_MICHEL = "waste_michel"
    MEMBER_REGULAR = "member_regular"
    MEMBER_JACK = "member_jack"
    MEMBER_VIP = "member_vip"
    MEMBER_FOUNDER = "member_founder"
    HOUSE_ACCOUNT = "house_account"
    BARTER = "barter"
    ROUND_DOWN = "round_down"


class TaxCategoryEnum(str, Enum):
    PROMOTIONAL_EXPENSE = "promo_expense"
    COST_OF_GOODS = "cogs"
    STAFF_BENEFIT = "staff_benefit"
    ENTERTAINMENT = "entertainment"
    CHARITABLE = "charitable"
    NOT_DEDUCTIBLE = "not_deductible"


class PromoStatusEnum(str, Enum):
    ACTIVE = "active"
    USED = "used"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


# ================================================================
# DISCOUNT REASON SCHEMAS
# ================================================================

class DiscountReasonBase(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=20)
    description: Optional[str] = Field(None, max_length=500)
    discount_type: DiscountTypeEnum
    tax_category: TaxCategoryEnum = TaxCategoryEnum.PROMOTIONAL_EXPENSE
    default_percentage: int = Field(default=100, ge=0, le=100)
    requires_approval: bool = False
    max_daily_uses: Optional[int] = Field(None, ge=1)
    max_value_chf: Optional[float] = Field(None, ge=0)


class DiscountReasonCreate(DiscountReasonBase):
    pass


class DiscountReasonRead(DiscountReasonBase):
    id: UUID
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# PROMO TRANSACTION SCHEMAS - The Pennies
# ================================================================

class PromoTransactionCreate(BaseModel):
    """Record a discount/comp - Andy's quick entry"""
    item_description: str = Field(..., max_length=500)
    original_value: float = Field(..., ge=0)
    discount_percentage: int = Field(default=100, ge=0, le=100)
    discount_type: DiscountTypeEnum
    reason_code: Optional[str] = Field(None, max_length=20)
    reason_note: Optional[str] = Field(None, max_length=500)
    recipient_name: Optional[str] = Field(None, max_length=200)
    recipient_type: Optional[str] = Field(None, max_length=50)
    member_id: Optional[UUID] = None
    order_id: Optional[UUID] = None
    authorized_by: str = Field(default="Andy", max_length=100)


class PromoTransactionRead(BaseModel):
    id: UUID
    transaction_date: date
    transaction_time: datetime
    item_description: str
    original_value: float
    discount_percentage: int
    discount_amount: float
    final_amount: float
    discount_type: DiscountTypeEnum
    tax_category: TaxCategoryEnum
    reason_id: Optional[UUID] = None
    reason_note: Optional[str] = None
    recipient_name: Optional[str] = None
    recipient_type: Optional[str] = None
    authorized_by: str
    status: PromoStatusEnum
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# QUICK COMP - Andy's One-Click
# ================================================================

class QuickComp(BaseModel):
    """One-click comp for common scenarios"""
    reason_code: str = Field(..., max_length=20, description="LANDLORD, STAFF, VIP, etc")
    item_description: str = Field(..., max_length=500)
    original_value: float = Field(..., ge=0)
    recipient_name: Optional[str] = Field(None, max_length=200)
    note: Optional[str] = Field(None, max_length=500)


class QuickCompResponse(BaseModel):
    transaction_id: UUID
    discount_amount: float
    tax_category: str
    message: str


# ================================================================
# DAILY SUMMARY SCHEMAS
# ================================================================

class DailySummaryRead(BaseModel):
    summary_date: date
    comp_owner_total: float
    comp_vip_total: float
    comp_staff_total: float
    promo_total: float
    sample_total: float
    waste_total: float
    member_discount_total: float
    total_transactions: int
    total_discount_value: float
    total_deductible: float
    revenue_today: Optional[float] = None
    discount_to_revenue_ratio: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class WeeklySummary(BaseModel):
    week_start: date
    week_end: date
    daily_summaries: list[DailySummaryRead]
    total_discount_value: float
    total_deductible: float
    average_daily: float


# ================================================================
# TAX REPORT SCHEMAS - Mr. TAXMAN
# ================================================================

class TaxReportRequest(BaseModel):
    """Request a tax report"""
    report_type: str = Field(..., description="monthly, quarterly, yearly")
    year: int = Field(..., ge=2020, le=2100)
    month: Optional[int] = Field(None, ge=1, le=12)
    quarter: Optional[int] = Field(None, ge=1, le=4)


class TaxReportRead(BaseModel):
    id: UUID
    report_type: str
    period_start: date
    period_end: date
    year: int
    month: Optional[int] = None
    quarter: Optional[int] = None

    # Totals by category
    promotional_expense: float
    cost_of_goods: float
    staff_benefits: float
    entertainment: float
    charitable: float
    not_deductible: float

    # Grand totals
    total_discounts: float
    total_deductible: float
    estimated_tax_savings: float

    transaction_count: int
    generated_at: datetime
    is_final: bool
    auditor_approved: bool

    model_config = ConfigDict(from_attributes=True)


class TaxSummaryByCategory(BaseModel):
    """Summary for Mr. TAXMAN"""
    category: TaxCategoryEnum
    total_value: float
    transaction_count: int
    percentage_of_total: float
    is_deductible: bool
    deductible_amount: float


# ================================================================
# FREE ITEMS SCHEMAS
# ================================================================

class FreeItemBase(BaseModel):
    item_name: str = Field(..., max_length=200)
    item_category: str = Field(..., max_length=50)
    estimated_unit_cost: float = Field(default=0, ge=0)
    estimated_value_to_customer: float = Field(default=0, ge=0)
    daily_usage_estimate: int = Field(default=0, ge=0)
    tax_category: TaxCategoryEnum = TaxCategoryEnum.PROMOTIONAL_EXPENSE
    include_in_reports: bool = True
    notes: Optional[str] = None


class FreeItemCreate(FreeItemBase):
    pass


class FreeItemRead(FreeItemBase):
    id: UUID
    is_tracked_daily: bool
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# DASHBOARD SCHEMAS
# ================================================================

class PromoDashboard(BaseModel):
    """Andy's promo dashboard"""
    today_total: float
    today_transactions: int
    week_total: float
    month_total: float
    year_total: float
    year_deductible: float
    estimated_tax_savings: float
    top_discount_types: list[dict]
    recent_transactions: list[PromoTransactionRead]


class AuditorReport(BaseModel):
    """What Mr. TAXMAN sees"""
    business_name: str
    tax_id: Optional[str] = None
    report_period: str
    generated_date: date

    # By category
    categories: list[TaxSummaryByCategory]

    # Totals
    gross_discounts: float
    total_deductible: float
    total_non_deductible: float

    # Supporting data
    transaction_count: int
    unique_recipients: int
    average_discount: float

    # Certification
    prepared_by: str
    is_certified: bool = False


# ================================================================
# SEARCH & FILTER
# ================================================================

class PromoSearch(BaseModel):
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    discount_type: Optional[DiscountTypeEnum] = None
    tax_category: Optional[TaxCategoryEnum] = None
    recipient_name: Optional[str] = None
    min_value: Optional[float] = Field(None, ge=0)
    max_value: Optional[float] = Field(None, ge=0)
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)

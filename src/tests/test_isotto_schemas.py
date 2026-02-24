# File: src/tests/test_isotto_schemas.py
"""
ISOTTO Sport Print Shop - Schema-level tests.
No database or Docker needed. Tests Pydantic validation, enum handling,
invoice calculations, and realistic frontend payloads.

Same pattern as test_bug007_assignment_status.py.

"If one seal fails, check all the seals."
"""
import pytest
from datetime import datetime, date, timezone
from decimal import Decimal
from pydantic import ValidationError

# Import ONLY schemas + enums -- no app, no database, no Docker
from src.schemas.isotto_schema import (
    IsottoCustomerCreate, IsottoCustomerUpdate, IsottoCustomerRead,
    PrintOrderCreate, PrintOrderUpdate, PrintOrderRead, PrintOrderStatusUpdate,
    IsottoInvoiceCreate, IsottoInvoiceUpdate, IsottoInvoiceRead,
    IsottoInvoiceLineItem, IsottoPaymentRecord,
    IsottoOrderActivityRead, IsottoOrderCommentCreate,
    IsottoDashboardSummary,
)
from src.db.models.isotto_order_model import (
    ProductType, OrderStatus, ColorMode, DuplexMode, Lamination,
)
from src.db.models.isotto_invoice_model import IsottoPaymentStatus
from src.db.models.isotto_activity_model import IsottoActivityType


# ================================================================
# ENUM TESTS
# ================================================================

class TestIsottoEnums:
    """Verify all ISOTTO enums are case-insensitive and have correct values."""

    def test_product_type_values(self):
        """All 11 product types exist."""
        assert len(ProductType) == 11
        assert ProductType("postcard") == ProductType.POSTCARD
        assert ProductType("tshirt") == ProductType.TSHIRT
        assert ProductType("custom") == ProductType.CUSTOM

    def test_product_type_case_insensitive(self):
        """HelixEnum case-insensitive lookup."""
        assert ProductType("POSTCARD") == ProductType.POSTCARD
        assert ProductType("Postcard") == ProductType.POSTCARD

    def test_order_status_lifecycle(self):
        """Order lifecycle has 8 stages."""
        assert len(OrderStatus) == 8
        lifecycle = [
            "quoted", "approved", "in_production", "quality_check",
            "ready", "picked_up", "invoiced", "cancelled"
        ]
        for status in lifecycle:
            assert OrderStatus(status).value == status

    def test_payment_status_values(self):
        """Payment lifecycle has 5 stages."""
        assert len(IsottoPaymentStatus) == 5
        assert IsottoPaymentStatus("pending") == IsottoPaymentStatus.PENDING
        assert IsottoPaymentStatus("paid") == IsottoPaymentStatus.PAID

    def test_activity_type_values(self):
        """Activity types cover all tracked events."""
        assert len(IsottoActivityType) == 7
        assert IsottoActivityType("status_change") == IsottoActivityType.STATUS_CHANGE
        assert IsottoActivityType("invoice_created") == IsottoActivityType.INVOICE_CREATED

    def test_color_mode_values(self):
        assert ColorMode("cmyk") == ColorMode.CMYK
        assert ColorMode("bw") == ColorMode.BW

    def test_lamination_values(self):
        assert Lamination("glossy") == Lamination.GLOSSY
        assert Lamination("matte") == Lamination.MATTE
        assert Lamination("none") == Lamination.NONE


# ================================================================
# CUSTOMER SCHEMA TESTS
# ================================================================

class TestCustomerSchemas:
    """Customer schema validation."""

    def test_create_customer_minimal(self):
        """Only name is required."""
        c = IsottoCustomerCreate(name="Test Customer")
        assert c.name == "Test Customer"
        assert c.phone is None
        assert c.company_name is None

    def test_create_customer_full(self):
        """All fields accepted."""
        c = IsottoCustomerCreate(
            name="Giovanni Russo",
            company_name="Piccolo Bistratto",
            phone="+39 328 666 7890",
            email="info@piccolobistratto.it",
            city="Trapani",
            tax_id="RSSGVN80C20L219M",
            notes="Jonathan the chef",
        )
        assert c.company_name == "Piccolo Bistratto"
        assert c.tax_id == "RSSGVN80C20L219M"

    def test_create_customer_name_required(self):
        """Name field is mandatory."""
        with pytest.raises(ValidationError):
            IsottoCustomerCreate()

    def test_update_customer_all_optional(self):
        """Update schema: all fields optional."""
        u = IsottoCustomerUpdate()
        data = u.model_dump(exclude_unset=True)
        assert len(data) == 0

    def test_update_customer_partial(self):
        """Only send what changed."""
        u = IsottoCustomerUpdate(phone="+39 328 999 0000")
        data = u.model_dump(exclude_unset=True)
        assert data == {"phone": "+39 328 999 0000"}
        assert "name" not in data


# ================================================================
# ORDER SCHEMA TESTS
# ================================================================

class TestOrderSchemas:
    """Print order schema validation."""

    def test_create_order_minimal(self):
        """Title and customer_id are required."""
        o = PrintOrderCreate(
            title="Test Order",
            customer_id="00000000-0000-0000-0000-000000000001",
        )
        assert o.title == "Test Order"
        assert o.product_type == ProductType.POSTCARD  # default
        assert o.quantity == 0
        assert o.total_price == Decimal("0.00")

    def test_create_order_full_print_specs(self):
        """Full print specification payload."""
        o = PrintOrderCreate(
            title="Pizza Planet 4-UP Postcards",
            customer_id="00000000-0000-0000-0000-000000000001",
            product_type="postcard",
            quantity=200,
            unit_price=Decimal("0.25"),
            total_price=Decimal("50.00"),
            paper_weight_gsm=250,
            color_mode="cmyk",
            duplex=True,
            duplex_mode="short_edge",
            lamination="none",
            size_description="A4 portrait (4-UP)",
            copies_per_sheet=4,
            cutting_instructions="1 horizontal + 1 vertical cut through center",
            customer_notes="Short edge flip for duplex",
        )
        assert o.paper_weight_gsm == 250
        assert o.color_mode == ColorMode.CMYK
        assert o.duplex_mode == DuplexMode.SHORT_EDGE
        assert o.copies_per_sheet == 4

    def test_create_order_missing_title_fails(self):
        """Title is required."""
        with pytest.raises(ValidationError):
            PrintOrderCreate(
                customer_id="00000000-0000-0000-0000-000000000001"
            )

    def test_update_order_exclude_unset(self):
        """Only send fields that were actually changed."""
        u = PrintOrderUpdate(assigned_to="Famous", production_notes="Clean run")
        data = u.model_dump(exclude_unset=True)
        assert "assigned_to" in data
        assert "production_notes" in data
        assert "title" not in data
        assert "quantity" not in data

    def test_status_update_schema(self):
        """Status update requires a valid OrderStatus."""
        s = PrintOrderStatusUpdate(status="in_production")
        assert s.status == OrderStatus.IN_PRODUCTION

    def test_status_update_invalid_status_fails(self):
        """Invalid status value should fail."""
        with pytest.raises(ValidationError):
            PrintOrderStatusUpdate(status="nonexistent_status")

    def test_update_order_has_no_status_field(self):
        """
        CRITICAL: PrintOrderUpdate must NOT have a 'status' field.
        Status changes go through /orders/{id}/status or dedicated endpoints.
        Same lesson as BUG-007.
        """
        fields = PrintOrderUpdate.model_fields
        assert "status" not in fields, (
            "PrintOrderUpdate should NOT have a 'status' field. "
            "Status changes go through dedicated endpoints."
        )

    def test_negative_quantity_rejected(self):
        """Quantity must be >= 0."""
        with pytest.raises(ValidationError):
            PrintOrderCreate(
                title="Test",
                customer_id="00000000-0000-0000-0000-000000000001",
                quantity=-5,
            )

    def test_negative_price_rejected(self):
        """Prices must be >= 0."""
        with pytest.raises(ValidationError):
            PrintOrderCreate(
                title="Test",
                customer_id="00000000-0000-0000-0000-000000000001",
                unit_price=Decimal("-1.00"),
            )


# ================================================================
# INVOICE SCHEMA TESTS
# ================================================================

class TestInvoiceSchemas:
    """Invoice schema validation -- the core of the CRM+POS."""

    def test_line_item_schema(self):
        """Single line item validates correctly."""
        item = IsottoInvoiceLineItem(
            description="Pizza Planet 4-UP Postcards",
            quantity=200,
            unit_price=Decimal("0.25"),
            line_total=Decimal("50.00"),
        )
        assert item.quantity == 200
        assert item.line_total == Decimal("50.00")

    def test_line_item_requires_positive_quantity(self):
        """Quantity must be >= 1."""
        with pytest.raises(ValidationError):
            IsottoInvoiceLineItem(
                description="Bad item",
                quantity=0,
                unit_price=Decimal("1.00"),
                line_total=Decimal("0.00"),
            )

    def test_create_invoice_minimal(self):
        """Minimum valid invoice."""
        inv = IsottoInvoiceCreate(
            order_id="00000000-0000-0000-0000-000000000001",
            line_items=[
                IsottoInvoiceLineItem(
                    description="Postcards",
                    quantity=100,
                    unit_price=Decimal("0.25"),
                    line_total=Decimal("25.00"),
                )
            ],
            due_date="2026-03-15",
        )
        assert len(inv.line_items) == 1
        assert inv.deposit_applied == Decimal("0.00")
        assert inv.due_date == date(2026, 3, 15)

    def test_create_invoice_with_deposit(self):
        """Invoice with deposit deduction."""
        inv = IsottoInvoiceCreate(
            order_id="00000000-0000-0000-0000-000000000001",
            line_items=[
                IsottoInvoiceLineItem(
                    description="Business cards",
                    quantity=500,
                    unit_price=Decimal("0.07"),
                    line_total=Decimal("35.00"),
                )
            ],
            due_date="2026-03-01",
            deposit_applied=Decimal("10.00"),
            notes="Acconto pagato il 1 febbraio",
        )
        assert inv.deposit_applied == Decimal("10.00")
        assert inv.notes is not None

    def test_create_invoice_empty_line_items_fails(self):
        """At least one line item required."""
        with pytest.raises(ValidationError):
            IsottoInvoiceCreate(
                order_id="00000000-0000-0000-0000-000000000001",
                line_items=[],
                due_date="2026-03-15",
            )

    def test_create_invoice_no_line_items_fails(self):
        """Line items field is required."""
        with pytest.raises(ValidationError):
            IsottoInvoiceCreate(
                order_id="00000000-0000-0000-0000-000000000001",
                due_date="2026-03-15",
            )

    def test_create_invoice_multiple_line_items(self):
        """Invoice with multiple lines (real scenario: order + rush fee)."""
        inv = IsottoInvoiceCreate(
            order_id="00000000-0000-0000-0000-000000000001",
            line_items=[
                IsottoInvoiceLineItem(
                    description="4-UP Postcards x200",
                    quantity=1,
                    unit_price=Decimal("50.00"),
                    line_total=Decimal("50.00"),
                ),
                IsottoInvoiceLineItem(
                    description="Urgenza (consegna giorno stesso)",
                    quantity=1,
                    unit_price=Decimal("10.00"),
                    line_total=Decimal("10.00"),
                ),
            ],
            due_date="2026-03-15",
        )
        assert len(inv.line_items) == 2
        total = sum(item.line_total for item in inv.line_items)
        assert total == Decimal("60.00")

    def test_iva_calculation(self):
        """Verify IVA 22% math (this is what the router does)."""
        subtotal = Decimal("50.00")
        vat_rate = Decimal("22.00")
        vat_amount = (subtotal * vat_rate / Decimal("100")).quantize(Decimal("0.01"))
        total = subtotal + vat_amount
        deposit = Decimal("10.00")
        amount_due = total - deposit

        assert vat_amount == Decimal("11.00")
        assert total == Decimal("61.00")
        assert amount_due == Decimal("51.00")

    def test_update_invoice_partial(self):
        """Only send changed fields."""
        u = IsottoInvoiceUpdate(payment_status="paid", payment_method="contanti")
        data = u.model_dump(exclude_unset=True)
        assert data["payment_status"] == IsottoPaymentStatus.PAID
        assert data["payment_method"] == "contanti"
        assert "notes" not in data

    def test_payment_record_full(self):
        """Full payment (no amount = pay everything)."""
        p = IsottoPaymentRecord(payment_method="carta")
        assert p.payment_method == "carta"
        assert p.amount is None  # None = full payment

    def test_payment_record_partial(self):
        """Partial payment with specific amount."""
        p = IsottoPaymentRecord(payment_method="contanti", amount=Decimal("25.00"))
        assert p.amount == Decimal("25.00")

    def test_payment_record_requires_method(self):
        """Payment method is required."""
        with pytest.raises(ValidationError):
            IsottoPaymentRecord()

    def test_payment_methods_italian(self):
        """All three Italian payment methods work."""
        for method in ["contanti", "carta", "bonifico"]:
            p = IsottoPaymentRecord(payment_method=method)
            assert p.payment_method == method


# ================================================================
# ACTIVITY SCHEMA TESTS
# ================================================================

class TestActivitySchemas:
    """Activity trail schema validation."""

    def test_comment_create(self):
        """Comment requires non-empty text."""
        c = IsottoOrderCommentCreate(comment="Carta arrivata, inizio produzione domani")
        assert len(c.comment) > 0

    def test_comment_empty_fails(self):
        """Empty comment should fail."""
        with pytest.raises(ValidationError):
            IsottoOrderCommentCreate(comment="")

    def test_comment_max_length(self):
        """Comment has 2000 char limit."""
        long_comment = "A" * 2001
        with pytest.raises(ValidationError):
            IsottoOrderCommentCreate(comment=long_comment)

    def test_comment_at_max_length(self):
        """2000 chars exactly should work."""
        c = IsottoOrderCommentCreate(comment="A" * 2000)
        assert len(c.comment) == 2000


# ================================================================
# DASHBOARD SCHEMA TESTS
# ================================================================

class TestDashboardSchema:
    """Dashboard summary schema."""

    def test_dashboard_all_fields(self):
        """All dashboard fields present."""
        d = IsottoDashboardSummary(
            orders_in_production=3,
            orders_pending_approval=2,
            orders_ready=1,
            orders_completed_today=5,
            orders_in_quality_check=0,
            total_orders=42,
            pending_invoices=4,
            revenue_this_month=Decimal("1250.50"),
        )
        assert d.pending_invoices == 4
        assert d.revenue_this_month == Decimal("1250.50")

    def test_dashboard_defaults(self):
        """New fields have sensible defaults."""
        d = IsottoDashboardSummary(
            orders_in_production=0,
            orders_pending_approval=0,
            orders_ready=0,
            orders_completed_today=0,
            orders_in_quality_check=0,
            total_orders=0,
        )
        assert d.pending_invoices == 0
        assert d.revenue_this_month == Decimal("0.00")


# ================================================================
# REALISTIC FRONTEND PAYLOAD TESTS
# ================================================================

class TestRealisticPayloads:
    """Simulate what the ISOTTO frontend actually sends."""

    def test_counter_creates_order(self):
        """
        Counter staff creates a new quotation from the order form.
        This matches the newOrder structure in order_detail.html.
        """
        payload = {
            "title": "Flyer Sagra del Pesce 2026",
            "description": "A5 flyers for fish festival",
            "customer_id": "00000000-0000-0000-0000-000000000001",
            "product_type": "flyer",
            "quantity": 1000,
            "unit_price": 0.08,
            "total_price": 80.00,
            "paper_weight_gsm": 135,
            "size_description": "A5 (148x210mm)",
            "copies_per_sheet": 2,
            "customer_notes": "Serve entro venerdi",
        }
        order = PrintOrderCreate(**payload)
        assert order.product_type == ProductType.FLYER
        assert order.total_price == Decimal("80.00")

    def test_operator_edits_order(self):
        """
        Operator assigns themselves and adds production notes.
        Matches editData from startEditing() in order_detail.html.
        """
        payload = {
            "assigned_to": "Luca Operator",
            "customer_notes": "Serve entro venerdi",
            "production_notes": "Carta 135gsm disponibile in magazzino",
            "proof_approved": True,
            "cutting_instructions": "Taglio A4 a meta = 2 x A5",
            "finishing_notes": "",
        }
        update = PrintOrderUpdate(**payload)
        data = update.model_dump(exclude_unset=True)
        assert data["assigned_to"] == "Luca Operator"
        assert data["proof_approved"] is True
        assert "finishing_notes" in data  # empty string is still "set"

    def test_invoice_from_completed_order(self):
        """
        Manager generates invoice from order detail page.
        Matches the generateInvoice() JS function.
        """
        payload = {
            "order_id": "00000000-0000-0000-0000-000000000001",
            "line_items": [{
                "description": "Pizza Planet 4-UP Postcards",
                "quantity": 1,
                "unit_price": 50.00,
                "line_total": 50.00,
            }],
            "due_date": "2026-03-15",
            "deposit_applied": 0,
            "notes": None,
        }
        invoice = IsottoInvoiceCreate(**payload)
        assert invoice.line_items[0].line_total == Decimal("50.00")
        assert invoice.deposit_applied == Decimal("0.00")

    def test_payment_at_counter(self):
        """Customer pays at the counter with cash."""
        p = IsottoPaymentRecord(payment_method="contanti")
        assert p.amount is None  # full payment

    def test_partial_card_payment(self):
        """Customer pays partial by card."""
        p = IsottoPaymentRecord(payment_method="carta", amount=Decimal("30.00"))
        assert p.amount == Decimal("30.00")

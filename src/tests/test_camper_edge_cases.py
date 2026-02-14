# File: src/tests/test_camper_edge_cases.py
"""
Camper & Tour Edge Case Tests - 20 scenarios that will break things.

Tests financial math, status flow violations, data integrity,
integration failures, and concurrency edge cases.

"If one seal fails, check all the seals."
"""
import io
import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock, MagicMock
from decimal import Decimal
from datetime import date
from uuid import uuid4

from src.main import app
from src.db.database import get_db_session
from src.core.keycloak_auth import verify_token


# ================================================================
# FIXTURES
# ================================================================

@pytest_asyncio.fixture
async def client(db_session):
    """Async test client with camper-admin auth + test DB."""
    async def mock_verify_admin():
        return {
            "sub": "test-admin-id",
            "preferred_username": "nino",
            "email": "nino@camperandtour.it",
            "realm_access": {
                "roles": [
                    "camper-admin", "camper-manager",
                    "camper-mechanic", "camper-counter",
                ]
            },
        }

    app.dependency_overrides[get_db_session] = lambda: db_session
    app.dependency_overrides[verify_token] = mock_verify_admin

    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def counter_client(db_session):
    """Async test client with COUNTER role only (lowest privilege)."""
    async def mock_verify_counter():
        return {
            "sub": "test-counter-id",
            "preferred_username": "pam",
            "email": "pam@camperandtour.it",
            "realm_access": {
                "roles": ["camper-counter"]
            },
        }

    app.dependency_overrides[get_db_session] = lambda: db_session
    app.dependency_overrides[verify_token] = mock_verify_counter

    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


# ================================================================
# HELPER FUNCTIONS
# ================================================================

async def _create_vehicle(c: AsyncClient, plate: str = "TP-001-TEST") -> dict:
    resp = await c.post("/api/v1/camper/vehicles", json={
        "registration_plate": plate,
        "vehicle_type": "campervan",
        "make": "Fiat",
        "model": "Ducato",
        "year": 2020,
    })
    assert resp.status_code == 201, f"Vehicle create failed: {resp.text}"
    return resp.json()


async def _create_customer(c: AsyncClient, name: str = "Marco Rossi",
                           email: str = "marco@test.it",
                           telegram_chat_id: str = None) -> dict:
    data = {
        "name": name,
        "phone": "+39 333 1234567",
        "email": email,
        "city": "Trapani",
    }
    if telegram_chat_id:
        data["telegram_chat_id"] = telegram_chat_id
    resp = await c.post("/api/v1/camper/customers", json=data)
    assert resp.status_code == 201, f"Customer create failed: {resp.text}"
    return resp.json()


async def _create_job(c: AsyncClient, vehicle_id: str, customer_id: str,
                      title: str = "Seal replacement") -> dict:
    resp = await c.post("/api/v1/camper/jobs", json={
        "title": title,
        "description": "Test job",
        "vehicle_id": vehicle_id,
        "customer_id": customer_id,
        "job_type": "repair",
        "estimated_hours": 2.0,
        "estimated_parts_cost": "10.00",
        "estimated_total": "80.00",
    })
    assert resp.status_code == 201, f"Job create failed: {resp.text}"
    return resp.json()


async def _create_quotation(c: AsyncClient, job_id: str, customer_id: str,
                             vehicle_id: str, line_items: list = None) -> dict:
    if line_items is None:
        line_items = [
            {
                "description": "Labor - seal replacement",
                "quantity": 2,
                "unit_price": "35.00",
                "line_total": "70.00",
                "item_type": "labor",
            },
            {
                "description": "Seal kit",
                "quantity": 1,
                "unit_price": "15.00",
                "line_total": "15.00",
                "item_type": "parts",
            },
        ]
    resp = await c.post("/api/v1/camper/quotations", json={
        "job_id": job_id,
        "customer_id": customer_id,
        "vehicle_id": vehicle_id,
        "line_items": line_items,
        "vat_rate": "22.00",
        "deposit_percent": "25.00",
    })
    assert resp.status_code == 201, f"Quotation create failed: {resp.text}"
    return resp.json()


async def _advance_job_to(c: AsyncClient, job_id: str, target: str):
    """Walk a job through status transitions to reach the target status."""
    steps = {
        "approved": [("approve", None)],
        "in_progress": [("approve", None), ("status", "in_progress")],
        "inspection": [
            ("approve", None),
            ("status", "in_progress"),
            ("submit-inspection", None),
        ],
        "completed": [
            ("approve", None),
            ("status", "in_progress"),
            ("submit-inspection", None),
            ("pass-inspection", None),
        ],
    }
    for action, value in steps.get(target, []):
        if action == "status":
            resp = await c.patch(
                f"/api/v1/camper/jobs/{job_id}/status",
                json={"status": value},
            )
        elif action == "approve":
            resp = await c.post(f"/api/v1/camper/jobs/{job_id}/approve")
        elif action == "submit-inspection":
            resp = await c.post(
                f"/api/v1/camper/jobs/{job_id}/submit-inspection"
            )
        elif action == "pass-inspection":
            resp = await c.post(
                f"/api/v1/camper/jobs/{job_id}/pass-inspection",
                json={"notes": "Looks good"},
            )
        assert resp.status_code == 200, (
            f"Advance to '{target}' failed at '{action}': {resp.text}"
        )


# ================================================================
# GROUP 1: FINANCIAL / MATH GRENADES (Tests 1-6)
# ================================================================

@pytest.mark.asyncio
@patch("src.services.camper_email_service._send_email", return_value=True)
@patch(
    "src.services.camper_telegram_service.send_telegram_message",
    new_callable=AsyncMock,
    return_value=True,
)
async def test_01_zero_euro_quotation(mock_tg, mock_email, client):
    """
    EDGE CASE 1: Free warranty work = zero-euro quotation.
    VAT of 0 should be 0, deposit of 0 should not crash.
    """
    vehicle = await _create_vehicle(client, "ZERO-001")
    customer = await _create_customer(client, "Zero Euro Zack")
    job = await _create_job(client, vehicle["id"], customer["id"], "Free warranty")

    line_items = [
        {
            "description": "Warranty inspection",
            "quantity": 1,
            "unit_price": "0.00",
            "line_total": "0.00",
            "item_type": "labor",
        },
    ]
    quote = await _create_quotation(
        client, job["id"], customer["id"], vehicle["id"], line_items
    )

    assert Decimal(str(quote["subtotal"])) == Decimal("0.00")
    assert Decimal(str(quote["vat_amount"])) == Decimal("0.00")
    assert Decimal(str(quote["total"])) == Decimal("0.00")
    assert Decimal(str(quote["deposit_amount"])) == Decimal("0.00")

    # Accept zero-euro quote
    resp = await client.post(f"/api/v1/camper/quotations/{quote['id']}/accept")
    assert resp.status_code == 200

    # Job deposit_required should be 0
    job_resp = await client.get(f"/api/v1/camper/jobs/{job['id']}")
    assert Decimal(str(job_resp.json()["deposit_required"])) == Decimal("0.00")


@pytest.mark.asyncio
@patch("src.services.camper_email_service._send_email", return_value=True)
async def test_02_single_cent_rounding(mock_email, client):
    """
    EDGE CASE 2: 1 cent line item. VAT = 0.01 * 22% = 0.0022 -> rounds to 0.00.
    Verify subtotal + VAT == total.
    """
    vehicle = await _create_vehicle(client, "CENT-001")
    customer = await _create_customer(client, "Penny Pincher")
    job = await _create_job(client, vehicle["id"], customer["id"], "Screw tightening")

    line_items = [
        {
            "description": "One screw",
            "quantity": 1,
            "unit_price": "0.01",
            "line_total": "0.01",
            "item_type": "parts",
        },
    ]
    quote = await _create_quotation(
        client, job["id"], customer["id"], vehicle["id"], line_items
    )

    subtotal = Decimal(str(quote["subtotal"]))
    vat = Decimal(str(quote["vat_amount"]))
    total = Decimal(str(quote["total"]))
    deposit = Decimal(str(quote["deposit_amount"]))

    assert subtotal == Decimal("0.01")
    # 0.01 * 22% = 0.0022, quantized to 0.01 -> 0.00
    assert vat == Decimal("0.00"), f"VAT should round to 0.00, got {vat}"
    assert total == subtotal + vat, f"Total mismatch: {total} != {subtotal} + {vat}"
    # 0.01 * 25% = 0.0025, quantized to 0.01 -> 0.00
    assert deposit == Decimal("0.00"), f"Deposit should round to 0.00, got {deposit}"


@pytest.mark.asyncio
@patch("src.services.camper_email_service._send_email", return_value=True)
async def test_03_massive_quotation_50_items(mock_email, client):
    """
    EDGE CASE 3: 50 line items, high value. Numeric(10,2) max = 99,999,999.99.
    Subtotal 50M + 22% VAT = 61M -- should fit.
    """
    vehicle = await _create_vehicle(client, "BIG-001")
    customer = await _create_customer(client, "Mr Big Spender")
    job = await _create_job(client, vehicle["id"], customer["id"], "Full rebuild")

    line_items = [
        {
            "description": f"Part {i}",
            "quantity": 1,
            "unit_price": "1000000.00",
            "line_total": "1000000.00",
            "item_type": "parts",
        }
        for i in range(50)
    ]
    quote = await _create_quotation(
        client, job["id"], customer["id"], vehicle["id"], line_items
    )

    subtotal = Decimal(str(quote["subtotal"]))
    total = Decimal(str(quote["total"]))

    assert subtotal == Decimal("50000000.00"), f"Expected 50M, got {subtotal}"
    # 50M + 22% = 61M -- within Numeric(10,2) range
    assert total == Decimal("61000000.00"), f"Expected 61M, got {total}"


@pytest.mark.asyncio
@patch("src.services.camper_email_service._send_email", return_value=True)
@patch(
    "src.services.camper_telegram_service.send_telegram_message",
    new_callable=AsyncMock,
    return_value=True,
)
async def test_04_deposit_overpayment_rejected(mock_tg, mock_email, client):
    """
    EDGE CASE 4: Customer tries EUR 200 deposit on EUR 30.50 required.
    System rejects with 422 (overpayment guard). Then tests that the
    exact required amount is accepted, and that invoice caps deposit_applied
    to total (no negative amount_due).
    """
    vehicle = await _create_vehicle(client, "OVER-001")
    customer = await _create_customer(client, "Generous Giovanni")
    job = await _create_job(client, vehicle["id"], customer["id"], "Small fix")

    # Accept quotation to set deposit_required
    line_items = [
        {
            "description": "Quick fix",
            "quantity": 1,
            "unit_price": "100.00",
            "item_type": "labor",
        },
    ]
    quote = await _create_quotation(
        client, job["id"], customer["id"], vehicle["id"], line_items
    )
    await client.post(f"/api/v1/camper/quotations/{quote['id']}/accept")

    # Verify deposit_required was set (25% of 122 = 30.50)
    job_resp = await client.get(f"/api/v1/camper/jobs/{job['id']}")
    deposit_required = Decimal(str(job_resp.json()["deposit_required"]))
    assert deposit_required == Decimal("30.50"), f"Expected 30.50, got {deposit_required}"

    # Attempt overpayment -- should be rejected
    resp = await client.post(
        f"/api/v1/camper/jobs/{job['id']}/record-deposit",
        json={"amount": "200.00", "payment_method": "cash"},
    )
    assert resp.status_code == 422, (
        f"Overpayment should be rejected with 422, got {resp.status_code}"
    )
    assert "eccessivo" in resp.json()["detail"].lower()

    # Pay the exact required amount -- should succeed
    resp2 = await client.post(
        f"/api/v1/camper/jobs/{job['id']}/record-deposit",
        json={"amount": "30.50", "payment_method": "card"},
    )
    assert resp2.status_code == 200
    assert Decimal(str(resp2.json()["deposit_paid"])) == Decimal("30.50")

    # Complete the job (already APPROVED from quotation acceptance, skip to in_progress)
    await client.patch(
        f"/api/v1/camper/jobs/{job['id']}/status", json={"status": "in_progress"}
    )
    await client.post(f"/api/v1/camper/jobs/{job['id']}/submit-inspection")
    resp_pass = await client.post(
        f"/api/v1/camper/jobs/{job['id']}/pass-inspection", json={"notes": "OK"}
    )
    assert resp_pass.status_code == 200

    # Invoice with deposit_applied > total -- should be capped
    inv_resp = await client.post(
        "/api/v1/camper/invoices",
        json={
            "job_id": job["id"],
            "customer_id": customer["id"],
            "line_items": [
                {
                    "description": "Quick fix",
                    "quantity": 1,
                    "unit_price": "100.00",
                    "item_type": "labor",
                },
            ],
            "vat_rate": "22.00",
            "deposit_applied": "999.00",
            "due_date": date.today().isoformat(),
        },
    )
    assert inv_resp.status_code == 201
    invoice = inv_resp.json()

    # deposit_applied capped to total (122.00), amount_due = 0
    assert Decimal(str(invoice["deposit_applied"])) == Decimal("122.00")
    assert Decimal(str(invoice["amount_due"])) == Decimal("0.00")
    assert invoice["payment_status"] == "paid"


@pytest.mark.asyncio
@patch("src.services.camper_email_service._send_email", return_value=True)
@patch(
    "src.services.camper_telegram_service.send_telegram_message",
    new_callable=AsyncMock,
    return_value=True,
)
async def test_05_multiple_partial_deposits(mock_tg, mock_email, client):
    """
    EDGE CASE 5: Three partial deposits. Does deposit_paid accumulate?
    """
    vehicle = await _create_vehicle(client, "PART-001")
    customer = await _create_customer(client, "Partial Paolo")
    job = await _create_job(client, vehicle["id"], customer["id"], "Motor repair")

    amounts = [("10.00", "cash"), ("15.00", "card"), ("5.50", "transfer")]
    expected_totals = [Decimal("10.00"), Decimal("25.00"), Decimal("30.50")]

    for (amount, method), expected in zip(amounts, expected_totals):
        resp = await client.post(
            f"/api/v1/camper/jobs/{job['id']}/record-deposit",
            json={"amount": amount, "payment_method": method},
        )
        assert resp.status_code == 200
        assert Decimal(str(resp.json()["deposit_paid"])) == expected, (
            f"After {amount} deposit, expected {expected}, "
            f"got {resp.json()['deposit_paid']}"
        )

    # Final verification via GET
    job_resp = await client.get(f"/api/v1/camper/jobs/{job['id']}")
    assert Decimal(str(job_resp.json()["deposit_paid"])) == Decimal("30.50")


@pytest.mark.asyncio
@patch("src.services.camper_email_service._send_email", return_value=True)
@patch(
    "src.services.camper_telegram_service.send_telegram_message",
    new_callable=AsyncMock,
    return_value=True,
)
async def test_06_invoice_zero_amount_due(mock_tg, mock_email, client):
    """
    EDGE CASE 6: Deposit covers entire invoice. amount_due = 0.
    Can we still mark it as paid?
    """
    vehicle = await _create_vehicle(client, "ZEROD-001")
    customer = await _create_customer(client, "Full Deposit Fabio")
    job = await _create_job(client, vehicle["id"], customer["id"], "Oil change")

    await _advance_job_to(client, job["id"], "completed")

    # Invoice where deposit_applied == total (50 + 11 VAT = 61)
    inv_resp = await client.post(
        "/api/v1/camper/invoices",
        json={
            "job_id": job["id"],
            "customer_id": customer["id"],
            "line_items": [
                {
                    "description": "Oil change",
                    "quantity": 1,
                    "unit_price": "50.00",
                    "line_total": "50.00",
                    "item_type": "labor",
                },
            ],
            "vat_rate": "22.00",
            "deposit_applied": "61.00",
            "due_date": date.today().isoformat(),
        },
    )
    assert inv_resp.status_code == 201
    invoice = inv_resp.json()
    assert Decimal(str(invoice["amount_due"])) == Decimal("0.00")
    assert invoice["payment_status"] == "paid"

    # Mark zero-balance invoice as paid (already paid, should stay paid)
    paid_resp = await client.post(
        f"/api/v1/camper/invoices/{invoice['id']}/mark-paid",
        json={"payment_method": "cash"},
    )
    assert paid_resp.status_code == 200
    assert paid_resp.json()["payment_status"] == "paid"


# ================================================================
# GROUP 2: STATUS FLOW BOMBS (Tests 7-11)
# ================================================================

@pytest.mark.asyncio
@patch("src.services.camper_email_service._send_email", return_value=True)
@patch(
    "src.services.camper_telegram_service.send_telegram_message",
    new_callable=AsyncMock,
    return_value=True,
)
async def test_07_cancel_job_mid_inspection(mock_tg, mock_email, client):
    """
    EDGE CASE 7: Job is in INSPECTION, someone cancels it.
    FINDING: No status transition validation -- any status change allowed.
    """
    vehicle = await _create_vehicle(client, "CANCEL-001")
    customer = await _create_customer(client, "Cancel Carlo")
    job = await _create_job(client, vehicle["id"], customer["id"], "Brake check")

    await _advance_job_to(client, job["id"], "inspection")

    resp = await client.patch(
        f"/api/v1/camper/jobs/{job['id']}/status",
        json={"status": "cancelled"},
    )
    # DESIGN GAP: No transition validation on the generic status endpoint
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


@pytest.mark.asyncio
@patch("src.services.camper_email_service._send_email", return_value=True)
@patch(
    "src.services.camper_telegram_service.send_telegram_message",
    new_callable=AsyncMock,
    return_value=True,
)
async def test_08_double_accept_quotation(mock_tg, mock_email, client):
    """
    EDGE CASE 8: Accept an already-ACCEPTED quotation.
    Should reject (status is not DRAFT or SENT).
    """
    vehicle = await _create_vehicle(client, "DOUBLE-001")
    customer = await _create_customer(client, "Double Daniela")
    job = await _create_job(client, vehicle["id"], customer["id"], "Window repair")

    quote = await _create_quotation(client, job["id"], customer["id"], vehicle["id"])

    # First accept
    resp1 = await client.post(f"/api/v1/camper/quotations/{quote['id']}/accept")
    assert resp1.status_code == 200

    # Second accept -- should fail
    resp2 = await client.post(f"/api/v1/camper/quotations/{quote['id']}/accept")
    assert resp2.status_code == 400, (
        f"Expected 400 for double-accept, got {resp2.status_code}"
    )


@pytest.mark.asyncio
@patch("src.services.camper_email_service._send_email", return_value=True)
async def test_09_invoice_on_non_completed_job(mock_email, client):
    """
    EDGE CASE 9: Create invoice while job is still IN_PROGRESS.
    FINDING: No job-status guard -- invoice creation succeeds and
    sets job to INVOICED, skipping the COMPLETED state entirely.
    """
    vehicle = await _create_vehicle(client, "EARLYINV-001")
    customer = await _create_customer(client, "Impatient Irene")
    job = await _create_job(client, vehicle["id"], customer["id"], "Engine tune")

    await _advance_job_to(client, job["id"], "in_progress")

    inv_resp = await client.post(
        "/api/v1/camper/invoices",
        json={
            "job_id": job["id"],
            "customer_id": customer["id"],
            "line_items": [
                {
                    "description": "Engine tune",
                    "quantity": 2,
                    "unit_price": "35.00",
                    "line_total": "70.00",
                    "item_type": "labor",
                },
            ],
            "vat_rate": "22.00",
            "deposit_applied": "0.00",
            "due_date": date.today().isoformat(),
        },
    )
    # DESIGN GAP: No check that job must be COMPLETED before invoicing
    assert inv_resp.status_code == 201

    job_resp = await client.get(f"/api/v1/camper/jobs/{job['id']}")
    assert job_resp.json()["status"] == "invoiced", (
        "Job jumped IN_PROGRESS -> INVOICED (skipped COMPLETED)"
    )


@pytest.mark.asyncio
@patch("src.services.camper_email_service._send_email", return_value=True)
@patch(
    "src.services.camper_telegram_service.send_telegram_message",
    new_callable=AsyncMock,
    return_value=True,
)
async def test_10_fail_inspection_then_pass_without_resubmit(
    mock_tg, mock_email, client
):
    """
    EDGE CASE 10: Fail inspection (back to IN_PROGRESS), then try
    pass_inspection without re-submitting first. Should fail.
    """
    vehicle = await _create_vehicle(client, "INSPECT-001")
    customer = await _create_customer(client, "Inspector Luigi")
    job = await _create_job(client, vehicle["id"], customer["id"], "Gas line check")

    await _advance_job_to(client, job["id"], "inspection")

    # Fail inspection -> IN_PROGRESS
    fail_resp = await client.post(
        f"/api/v1/camper/jobs/{job['id']}/fail-inspection",
        json={"notes": "Gas valve loose"},
    )
    assert fail_resp.status_code == 200
    assert fail_resp.json()["status"] == "in_progress"

    # Try pass without re-submitting (job is IN_PROGRESS)
    pass_resp = await client.post(
        f"/api/v1/camper/jobs/{job['id']}/pass-inspection",
        json={"notes": "Trying to bypass"},
    )
    assert pass_resp.status_code == 400, (
        f"Should reject pass on IN_PROGRESS job, got {pass_resp.status_code}"
    )


@pytest.mark.asyncio
@patch("src.services.camper_email_service._send_email", return_value=True)
@patch(
    "src.services.camper_telegram_service.send_telegram_message",
    new_callable=AsyncMock,
    return_value=True,
)
async def test_11_reopen_completed_job(mock_tg, mock_email, client):
    """
    EDGE CASE 11: Re-open a COMPLETED job (customer comes back).
    FINDING: No transition guard -- COMPLETED -> IN_PROGRESS allowed.
    """
    vehicle = await _create_vehicle(client, "REOPEN-001")
    customer = await _create_customer(client, "Comeback Carlo")
    job = await _create_job(client, vehicle["id"], customer["id"], "Water pump")

    await _advance_job_to(client, job["id"], "completed")

    resp = await client.patch(
        f"/api/v1/camper/jobs/{job['id']}/status",
        json={"status": "in_progress"},
    )
    # DESIGN GAP: Allows re-opening completed jobs with no guard
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"
    # started_at should still be set (not reset)
    assert resp.json()["started_at"] is not None


# ================================================================
# GROUP 3: DATA INTEGRITY (Tests 12-15)
# ================================================================

@pytest.mark.asyncio
async def test_12_orphan_vehicle_no_customer(client):
    """
    EDGE CASE 12: Walk-in vehicle with no owner. Create job linking
    a separate customer. owner_id is nullable, so this should work.
    """
    vehicle = await _create_vehicle(client, "WALKIN-001")
    assert vehicle["owner_id"] is None

    customer = await _create_customer(client, "Walk-In Walter")

    job = await _create_job(
        client, vehicle["id"], customer["id"], "Walk-in oil change"
    )
    assert job["vehicle_id"] == vehicle["id"]
    assert job["customer_id"] == customer["id"]

    resp = await client.get(f"/api/v1/camper/jobs/{job['id']}")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_13_job_with_nonexistent_vehicle(client):
    """
    EDGE CASE 13: Create job referencing a fake vehicle_id.
    Should return 404.
    """
    customer = await _create_customer(client, "Ghost Car Gina")
    fake_vehicle_id = str(uuid4())

    resp = await client.post(
        "/api/v1/camper/jobs",
        json={
            "title": "Fix phantom car",
            "vehicle_id": fake_vehicle_id,
            "customer_id": customer["id"],
            "job_type": "repair",
        },
    )
    assert resp.status_code == 404
    assert "Vehicle not found" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_14_duplicate_job_numbers_same_day(client):
    """
    EDGE CASE 14: Multiple jobs on the same day get sequential numbers.
    """
    vehicle = await _create_vehicle(client, "MULTI-001")
    customer = await _create_customer(client, "Busy Bob")

    jobs = []
    for i in range(3):
        job = await _create_job(
            client, vehicle["id"], customer["id"], f"Job #{i+1}"
        )
        jobs.append(job)

    sequences = [int(j["job_number"].split("-")[-1]) for j in jobs]
    # Check they're sequential (N, N+1, N+2) regardless of starting value
    assert sequences[1] == sequences[0] + 1, f"Not sequential: {sequences}"
    assert sequences[2] == sequences[1] + 1, f"Not sequential: {sequences}"

    # All should share the same date prefix
    prefixes = set(j["job_number"].rsplit("-", 1)[0] for j in jobs)
    assert len(prefixes) == 1, f"Mixed date prefixes: {prefixes}"


@pytest.mark.asyncio
async def test_15_plate_case_sensitivity(client):
    """
    EDGE CASE 15: Register lowercase plate, look up with mixed case.
    Both create and lookup uppercase, so all variants should match.
    """
    vehicle = await _create_vehicle(client, "tp-123-ab")
    assert vehicle["registration_plate"] == "TP-123-AB"

    # Lookup mixed case
    resp1 = await client.get("/api/v1/camper/vehicles/plate/Tp-123-Ab")
    assert resp1.status_code == 200

    # Lookup original lowercase
    resp2 = await client.get("/api/v1/camper/vehicles/plate/tp-123-ab")
    assert resp2.status_code == 200

    # Duplicate plate with different case
    dup_resp = await client.post(
        "/api/v1/camper/vehicles",
        json={"registration_plate": "TP-123-AB", "vehicle_type": "campervan"},
    )
    assert dup_resp.status_code == 400
    assert "already registered" in dup_resp.json()["detail"]


# ================================================================
# GROUP 4: INTEGRATION / EXTERNAL (Tests 16-18)
# ================================================================

@pytest.mark.asyncio
@patch("src.services.camper_email_service._send_email", return_value=True)
@patch(
    "src.services.camper_telegram_service.send_telegram_message",
    new_callable=AsyncMock,
    return_value=True,
)
async def test_16_telegram_no_chat_id(mock_tg, mock_email, client):
    """
    EDGE CASE 16: Customer has no telegram_chat_id. pass_inspection
    should complete without crashing (Telegram call is guarded).
    """
    vehicle = await _create_vehicle(client, "NOTG-001")
    customer = await _create_customer(
        client, "No Telegram Nina", telegram_chat_id=None
    )
    job = await _create_job(client, vehicle["id"], customer["id"], "Fridge repair")

    await _advance_job_to(client, job["id"], "inspection")

    pass_resp = await client.post(
        f"/api/v1/camper/jobs/{job['id']}/pass-inspection",
        json={"notes": "All good"},
    )
    assert pass_resp.status_code == 200
    assert pass_resp.json()["status"] == "completed"
    assert pass_resp.json()["inspection_passed"] is True


@pytest.mark.asyncio
@patch(
    "src.services.camper_telegram_service.send_telegram_message",
    new_callable=AsyncMock,
    return_value=True,
)
async def test_17_email_smtp_failure(mock_tg, client):
    """
    EDGE CASE 17: SMTP server is down. Email send raises exception.
    API should NOT crash (errors are caught in try/except).
    """
    vehicle = await _create_vehicle(client, "SMTP-001")
    customer = await _create_customer(
        client, "SMTP Failure Sal", email="sal@broken.com"
    )
    job = await _create_job(client, vehicle["id"], customer["id"], "Heater fix")

    quote = await _create_quotation(
        client, job["id"], customer["id"], vehicle["id"]
    )

    # Patch email to RAISE (simulating SMTP down)
    with patch(
        "src.services.camper_email_service._send_email",
        side_effect=ConnectionRefusedError("SMTP down"),
    ):
        resp = await client.post(
            f"/api/v1/camper/quotations/{quote['id']}/send"
        )
        assert resp.status_code == 200, (
            f"API should survive email failure, got {resp.status_code}"
        )
        assert resp.json()["status"] == "sent"


@pytest.mark.asyncio
@patch("src.services.camper_email_service._send_email", return_value=True)
async def test_18_document_upload_storage_failure(mock_email, client):
    """
    EDGE CASE 18: Object storage returns None on upload (failure).
    Should return 500 with clear error message.
    """
    mock_minio = MagicMock()
    mock_minio.upload_file_stream_async = AsyncMock(return_value=None)

    with patch(
        "src.services.minio_service.minio_service", mock_minio
    ):
        files = {
            "file": ("test.pdf", io.BytesIO(b"fake pdf content"), "application/pdf")
        }
        data = {"entity_type": "job", "entity_id": str(uuid4())}

        resp = await client.post(
            "/api/v1/camper/documents/upload",
            files=files,
            data=data,
        )
        assert resp.status_code == 500, (
            f"Expected 500 on storage failure, got {resp.status_code}"
        )
        assert "MinIO" in resp.json()["detail"] or "failed" in resp.json()["detail"]


# ================================================================
# GROUP 5: CONCURRENCY / REAL WORLD (Tests 19-20)
# ================================================================

@pytest.mark.asyncio
async def test_19_concurrent_job_updates_last_write_wins(client):
    """
    EDGE CASE 19: Two mechanics update the same job with different hours.
    No optimistic locking -- last write wins. Documents the risk.
    """
    vehicle = await _create_vehicle(client, "RACE-001")
    customer = await _create_customer(client, "Race Condition Rita")
    job = await _create_job(
        client, vehicle["id"], customer["id"], "Dual mechanic job"
    )

    await _advance_job_to(client, job["id"], "in_progress")

    # Mechanic A: 3 hours
    resp_a = await client.put(
        f"/api/v1/camper/jobs/{job['id']}",
        json={"actual_hours": 3.0, "mechanic_notes": "Mechanic A did 3 hours"},
    )
    assert resp_a.status_code == 200

    # Mechanic B: 5 hours (overwrites A)
    resp_b = await client.put(
        f"/api/v1/camper/jobs/{job['id']}",
        json={"actual_hours": 5.0, "mechanic_notes": "Mechanic B did 5 hours"},
    )
    assert resp_b.status_code == 200

    # Last write wins
    final = await client.get(f"/api/v1/camper/jobs/{job['id']}")
    final_data = final.json()
    assert final_data["actual_hours"] == 5.0, "Last write should win"
    assert "Mechanic B" in final_data["mechanic_notes"]


@pytest.mark.asyncio
@patch("src.services.camper_email_service._send_email", return_value=True)
async def test_20_second_po_same_job(mock_email, client):
    """
    EDGE CASE 20: Wrong parts received. Create second PO for same job.
    parts_on_order should toggle: True -> False -> True.
    """
    vehicle = await _create_vehicle(client, "PO2-001")
    customer = await _create_customer(client, "Wrong Parts Wally")
    job = await _create_job(
        client, vehicle["id"], customer["id"], "Roof vent motor"
    )

    await _advance_job_to(client, job["id"], "in_progress")

    # First PO
    po1_resp = await client.post(
        "/api/v1/camper/purchase-orders",
        json={
            "job_id": job["id"],
            "supplier_name": "AutoParts Trapani",
            "line_items": [
                {
                    "description": "Roof vent motor v1",
                    "quantity": 1,
                    "unit_price": "200.00",
                    "line_total": "200.00",
                },
            ],
        },
    )
    assert po1_resp.status_code == 201
    po1 = po1_resp.json()

    # parts_on_order should be True
    job1 = await client.get(f"/api/v1/camper/jobs/{job['id']}")
    assert job1.json()["parts_on_order"] is True

    # Mark first PO received (wrong parts, but PO is received)
    recv_resp = await client.patch(
        f"/api/v1/camper/purchase-orders/{po1['id']}/status",
        json={"status": "received"},
    )
    assert recv_resp.status_code == 200

    # parts_on_order should be False
    job2 = await client.get(f"/api/v1/camper/jobs/{job['id']}")
    assert job2.json()["parts_on_order"] is False

    # Second PO for correct parts
    po2_resp = await client.post(
        "/api/v1/camper/purchase-orders",
        json={
            "job_id": job["id"],
            "supplier_name": "AutoParts Palermo",
            "line_items": [
                {
                    "description": "Roof vent motor v2 CORRECT",
                    "quantity": 1,
                    "unit_price": "220.00",
                    "line_total": "220.00",
                },
            ],
        },
    )
    assert po2_resp.status_code == 201

    # parts_on_order should be True AGAIN
    job3 = await client.get(f"/api/v1/camper/jobs/{job['id']}")
    assert job3.json()["parts_on_order"] is True
    assert job3.json()["parts_po_number"] == po2_resp.json()["po_number"]

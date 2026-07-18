# File: src/tests/test_terminal_sim_capture.py
"""🌍-1 M2 SANDBOX — the in-checkout terminal sim capture (_capture_terminal_sim).

Locks the "full mock capture" behaviour that Pam's in-POS terminal overlay drives:
  - a 'manual' store (prod default) → None → the sale completes byte-identically to today
  - a 'worldline_sim' store + APPROVE → PaymentResult.approved, and a PaymentModel row is
    recorded (provider, cent-precise amount_minor, scheme, txn ref, status)
  - a 'worldline_sim' store + DECLINE → not approved (the caller turns this into a 402 so
    the sale never completes — cart kept)
"""
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import delete, select

from src.db.models.payment_model import PaymentModel
from src.db.models.store_settings_model import StoreSettingsModel
from src.db.models.transaction_model import TransactionModel
from src.db.models.user_model import UserModel
from src.routes.pos_router import _capture_terminal_sim
from src.schemas.pos_schema import TerminalCapture


async def _set_store(db, provider):
    """Make THIS shop's provider the one `_store_payment_provider` reads.

    The shared in-memory test DB doesn't drop cleanly between tests (an unrelated FK cycle
    aborts drop_all), so a prior test's store can linger. Clear the table first, then add ours.
    """
    await db.execute(delete(StoreSettingsModel))
    db.add(StoreSettingsModel(
        store_number=1, store_name="Artemis", legal_name="Artemis AG",
        address_line1="Teststrasse 1", city="Luzern", postal_code="6003",
        vat_number="CHE-123.456.789 MWST", currency="CHF", payment_provider=provider))
    await db.commit()


async def _cashier(db):
    """A real cashier row so the transaction's FK is valid (FK enforcement is ON)."""
    u = UserModel(keycloak_id=uuid.uuid4(), username=f"pam-{uuid.uuid4().hex[:8]}",
                  email=f"pam-{uuid.uuid4().hex[:8]}@test.ch")
    db.add(u)
    await db.commit()
    return u.id


async def _txn(db, total="42.50", num="TXN-SIM-1"):
    """A committed transaction (committed so it isn't a pending object during the store query)."""
    txn = TransactionModel(transaction_number=num, cashier_id=await _cashier(db),
                           subtotal=Decimal(total), total=Decimal(total))
    db.add(txn)
    await db.commit()
    return txn


@pytest.mark.asyncio
async def test_manual_store_returns_none(db_session):
    await _set_store(db_session, "manual")
    txn = await _txn(db_session)
    assert await _capture_terminal_sim(db_session, txn, None) is None


@pytest.mark.asyncio
async def test_sim_approve_records_payment_row(db_session):
    await _set_store(db_session, "worldline_sim")
    txn = await _txn(db_session, "42.50", "TXN-SIM-A")
    cap = TerminalCapture(method="twint", outcome="approve",
                          terminal="AXIUM DX8000", tid="25409030")
    res = await _capture_terminal_sim(db_session, txn, cap)
    assert res is not None and res.approved
    assert res.card_scheme == "twint"
    row = (await db_session.execute(
        select(PaymentModel).where(PaymentModel.transaction_id == txn.id))).scalars().first()
    assert row is not None
    assert row.provider == "worldline_sim"
    assert row.amount_minor == 4250            # cent-precise minor units
    assert row.status == "approved"
    assert row.provider_txn_id.startswith("25409030-")   # the terminal's TID
    assert row.settled_at is not None


@pytest.mark.asyncio
async def test_sim_decline_is_not_approved(db_session):
    await _set_store(db_session, "worldline_sim")
    txn = await _txn(db_session, "10.00", "TXN-SIM-D")
    cap = TerminalCapture(method="card", outcome="decline")
    res = await _capture_terminal_sim(db_session, txn, cap)
    assert res is not None
    assert res.approved is False
    assert res.status.value == "declined"


@pytest.mark.asyncio
async def test_sim_defaults_when_no_capture_payload(db_session):
    # overlay somehow sends nothing → default to an approved AXIUM TWINT (never strands the sale)
    await _set_store(db_session, "worldline_sim")
    txn = await _txn(db_session, "5.00", "TXN-SIM-DEF")
    res = await _capture_terminal_sim(db_session, txn, None)
    assert res is not None and res.approved

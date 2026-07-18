# File: src/tests/test_payments_seam.py
"""🌍-1 payments seam — provider-agnostic terminal capture.

The M1 guarantee under test: with the default 'manual' provider (every current store),
the seam resolves to None and the checkout hook is a STRICT no-op → zero regression. Plus
the money-cent-precision of the seam's amount handling and the PaymentModel schema.
"""
from decimal import Decimal

import pytest

from src.db.models.base import Base
from src.db.models.store_settings_model import StoreSettingsModel
from src.payments import (
    PaymentIntent,
    PaymentResult,
    PaymentStatus,
    to_minor_units,
    get_payment_provider,
    capture_on_terminal_if_configured,
    _store_payment_provider,
)


def _store(**over):
    """A minimal valid StoreSettingsModel (only the NOT-NULL-without-default fields)."""
    base = dict(
        store_number=over.pop("store_number", 1),
        store_name="Artemis Test",
        legal_name="Artemis Test AG",
        address_line1="Teststrasse 1",
        city="Luzern",
        postal_code="6003",
        vat_number="CHE-123.456.789 MWST",
    )
    base.update(over)
    return StoreSettingsModel(**base)


# ---- pure money / model contract (no DB) ----

@pytest.mark.parametrize("amount,minor", [
    ("15.90", 1590), ("0", 0), ("0.01", 1), ("226.17", 22617),
    (Decimal("226.16999999"), 22617),   # imprecise Decimal must ROUND to cents, not truncate
    (7.90, 790), ("1000.00", 100000),
])
def test_to_minor_units_quantizes_to_cents(amount, minor):
    assert to_minor_units(amount) == minor


def test_payment_intent_amount_roundtrips():
    intent = PaymentIntent(intent_id="TXN-1", provider="worldline",
                           amount_minor=1590, currency="CHF", reference="TXN-1")
    assert intent.amount == Decimal("15.90")


def test_payment_result_approved_flag():
    ok = PaymentResult(intent_id="x", status=PaymentStatus.APPROVED)
    no = PaymentResult(intent_id="x", status=PaymentStatus.DECLINED)
    assert ok.approved is True
    assert no.approved is False


# ---- resolver + no-regression hook (DB) ----

@pytest.mark.asyncio
async def test_default_store_is_manual_and_hook_is_noop(db_session):
    db_session.add(_store())
    await db_session.commit()
    assert await _store_payment_provider(db_session) == "manual"
    assert await get_payment_provider(db_session) is None
    # The hook wired into BOTH checkout paths must be a strict no-op today.
    assert await capture_on_terminal_if_configured(db_session, object()) is None


@pytest.mark.asyncio
async def test_unregistered_provider_fails_safe_to_none(db_session):
    # 'worldline' is named but its adapter isn't built until M2 → must fail SAFE to None,
    # never break the till (prove-don't-assume).
    db_session.add(_store(payment_provider="worldline"))
    await db_session.commit()
    assert await _store_payment_provider(db_session) == "worldline"
    assert await get_payment_provider(db_session) is None
    assert await capture_on_terminal_if_configured(db_session, object()) is None


@pytest.mark.asyncio
async def test_no_store_row_resolves_manual(db_session):
    # An env with no store row at all resolves to 'manual' (defensive) → None.
    assert await _store_payment_provider(db_session) == "manual"
    assert await get_payment_provider(db_session) is None


# ---- PaymentModel schema ----

def test_payments_table_registered_with_expected_columns():
    assert "payments" in Base.metadata.tables
    cols = set(Base.metadata.tables["payments"].columns.keys())
    assert {"transaction_id", "provider", "intent_id", "amount_minor", "currency",
            "status", "provider_txn_id", "card_scheme", "raw", "settled_at"} <= cols

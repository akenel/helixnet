# File: src/tests/test_worldline_adapter.py
"""🌍-1 M2 — the Worldline TIM adapter, driven against the mock terminal.

The "little terminal in the computer": these lock the capture flow with NO hardware and
NO real money, so that when Worldline delivers the real spec + terminal IP we swap the
transport (MockTerminal → TimTcpTerminalLink) and this behaviour is already proven.

Under test:
  - the adapter satisfies the PaymentProvider seam Protocol
  - a full charge on each of Felix's terminals → APPROVED + a txn ref + the scheme/TWINT
  - the amount crosses as integer minor units and round-trips to the right Decimal
  - DECLINE keeps it a non-approval (cart-kept path); ABORT maps to ABORTED
  - a terminal that never answers → the charge() loop returns TIMEOUT (and cancels)
  - a delayed customer (pending polls) still resolves to APPROVED
  - cancel() aborts an in-flight session; an unknown intent fails safe to ERROR
  - the real TCP transport is a spec-pending skeleton (raises, never silently no-ops)
"""
from decimal import Decimal

import pytest

from src.payments import PaymentIntent, PaymentProvider, PaymentStatus, to_minor_units
from src.payments.mock_terminal import (
    APPROVE, DECLINE, ABORT, TIMEOUT,
    MockTerminal, axium_dx8000, move_5000,
)
from src.payments.worldline import TimTcpTerminalLink, WorldlineTIMAdapter


def _intent(amount="42.50", ref="SALE-1"):
    return PaymentIntent(
        intent_id=ref, provider="worldline",
        amount_minor=to_minor_units(amount), currency="CHF", reference=ref,
    )


def test_adapter_satisfies_seam_protocol():
    adapter = WorldlineTIMAdapter(MockTerminal())
    assert isinstance(adapter, PaymentProvider)
    assert adapter.name == "worldline"


@pytest.mark.asyncio
async def test_charge_approves_on_axium_with_txn_ref_and_scheme():
    adapter = WorldlineTIMAdapter(axium_dx8000(outcome=APPROVE, method="visa"))
    res = await adapter.charge(_intent("42.50"), timeout=1.0, poll_interval=0.001)
    assert res.approved is True
    assert res.status == PaymentStatus.APPROVED
    assert res.card_scheme == "visa"
    assert res.provider_txn_id and res.provider_txn_id.startswith("25409030-")
    # amount crossed as integer minor units, echoed back intact
    assert res.raw["amount_minor"] == 4250


@pytest.mark.asyncio
async def test_charge_approves_twint_on_move_5000():
    adapter = WorldlineTIMAdapter(move_5000(outcome=APPROVE, method="twint"))
    res = await adapter.charge(_intent("9.90", ref="SALE-2"), timeout=1.0, poll_interval=0.001)
    assert res.approved is True
    assert res.card_scheme == "twint"                      # TWINT rides the same flow
    assert res.provider_txn_id.startswith("25145450-")     # Move/5000's TID


@pytest.mark.asyncio
async def test_amount_minor_roundtrips_to_decimal():
    # an imprecise amount must reach the terminal as the correctly-rounded cents
    intent = _intent(Decimal("226.16999999"))
    assert intent.amount_minor == 22617
    adapter = WorldlineTIMAdapter(MockTerminal(outcome=APPROVE))
    res = await adapter.charge(intent, timeout=1.0, poll_interval=0.001)
    assert res.raw["amount_minor"] == 22617
    assert intent.amount == Decimal("226.17")


@pytest.mark.asyncio
async def test_decline_is_not_approved():
    adapter = WorldlineTIMAdapter(MockTerminal(outcome=DECLINE))
    res = await adapter.charge(_intent(), timeout=1.0, poll_interval=0.001)
    assert res.status == PaymentStatus.DECLINED
    assert res.approved is False
    assert res.provider_txn_id is None


@pytest.mark.asyncio
async def test_abort_maps_to_aborted():
    adapter = WorldlineTIMAdapter(MockTerminal(outcome=ABORT))
    res = await adapter.charge(_intent(), timeout=1.0, poll_interval=0.001)
    assert res.status == PaymentStatus.ABORTED
    assert res.approved is False


@pytest.mark.asyncio
async def test_terminal_that_never_answers_times_out():
    adapter = WorldlineTIMAdapter(MockTerminal(outcome=TIMEOUT))
    res = await adapter.charge(_intent(), timeout=0.03, poll_interval=0.005)
    assert res.status == PaymentStatus.TIMEOUT
    assert res.approved is False
    assert res.raw["reason"] == "no_terminal_response"


@pytest.mark.asyncio
async def test_delayed_customer_still_approves():
    # the amount shows, the customer taps a couple of beats later (2 pending polls) → APPROVED
    adapter = WorldlineTIMAdapter(MockTerminal(outcome=APPROVE, pending_polls=2))
    res = await adapter.charge(_intent(), timeout=1.0, poll_interval=0.001)
    assert res.approved is True


@pytest.mark.asyncio
async def test_cancel_aborts_in_flight_session():
    terminal = MockTerminal(outcome=APPROVE, pending_polls=99)   # would sit 'pending'
    adapter = WorldlineTIMAdapter(terminal)
    intent = _intent()
    await adapter.initiate_payment(intent)
    await adapter.cancel(intent.intent_id)
    res = await adapter.poll_status(intent.intent_id)            # now reads aborted
    assert res.status == PaymentStatus.ABORTED


@pytest.mark.asyncio
async def test_poll_unknown_intent_fails_safe_to_error():
    adapter = WorldlineTIMAdapter(MockTerminal())
    res = await adapter.poll_status("never-initiated")
    assert res.status == PaymentStatus.ERROR
    assert res.raw["reason"] == "unknown_intent"


@pytest.mark.asyncio
async def test_zero_amount_rejected_by_terminal():
    adapter = WorldlineTIMAdapter(MockTerminal(outcome=APPROVE))
    bad = PaymentIntent(intent_id="z", provider="worldline",
                        amount_minor=0, currency="CHF", reference="z")
    with pytest.raises(ValueError):
        await adapter.initiate_payment(bad)


@pytest.mark.asyncio
async def test_real_tcp_link_is_spec_pending_skeleton():
    # The go-live transport must RAISE (not silently no-op) until the spec lands.
    link = TimTcpTerminalLink("192.168.1.50", 7784, tid="25409030")
    with pytest.raises(NotImplementedError):
        await link.request_payment(amount_minor=4250, currency="CHF", reference="x")

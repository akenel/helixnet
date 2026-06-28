"""
Per-cashier cash shift (the lockbox loop): open with a float -> ring sales ->
paid-in/out -> close by counting the drawer. Locks the money story:
expected = float + cash sales + paid-in - paid-out - refunds; variance within
CHF 0.20 = green, outside needs a note; each cashier owns their own drawer.

Black-box HTTP against the running server (real Keycloak tokens). felix is the
primary cashier; pam is a second cashier used to prove isolation.
"""
from decimal import Decimal

import pytest
import requests

from conftest import POS, KC_BASE, REALM, CLIENT_ID

requests.packages.urllib3.disable_warnings()


def _ring_custom_cash(session, price="42.00"):
    """Ring a CASH sale of a custom (no-product) line item -- avoids depleting
    catalog stock so the cash-shift math stays deterministic. Returns the total."""
    price = Decimal(str(price))
    tx = session.post(f"{POS}/transactions", json={}).json()
    r = session.post(f"{POS}/transactions/{tx['id']}/items", json={
        "product_id": None, "name": "Cash test item", "unit_price": str(price), "quantity": 1})
    r.raise_for_status()
    done = session.post(f"{POS}/transactions/{tx['id']}/checkout", json={
        "payment_method": "cash", "amount_tendered": str(price + Decimal("10"))})
    done.raise_for_status()
    return Decimal(str(done.json()["total"]))


def _token(username):
    r = requests.post(
        f"{KC_BASE}/realms/{REALM}/protocol/openid-connect/token",
        data={"client_id": CLIENT_ID, "username": username,
              "password": "helix_pass", "grant_type": "password"},
        verify=False, timeout=15)
    r.raise_for_status()
    return r.json()["access_token"]


def _sess(username):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {_token(username)}"})
    s.verify = False
    return s


def _ensure_closed(session):
    """Close any leftover open shift (from a prior failed run) at exact expected."""
    cur = session.get(f"{POS}/shift/current", timeout=15).json()
    if cur.get("open"):
        session.post(f"{POS}/shift/close",
                     json={"counted_cash": cur["expected_cash"], "note": "auto-clean prior test shift"},
                     timeout=15)


@pytest.fixture
def felix():
    s = _sess("felix")
    _ensure_closed(s)
    yield s
    _ensure_closed(s)


def test_open_ring_close_balances(felix):
    op = felix.post(f"{POS}/shift/open", json={"opening_float": "100.00"}).json()
    assert op["ok"] is True
    assert op["opening_float"] == "100.00"

    price = _ring_custom_cash(felix, "42.00")

    cur = felix.get(f"{POS}/shift/current").json()
    assert cur["open"] is True
    assert Decimal(cur["expected_cash"]) == Decimal("100.00") + price
    assert Decimal(cur["cash_sales"]) == price

    counted = Decimal("100.00") + price
    res = felix.post(f"{POS}/shift/close", json={"counted_cash": str(counted)}).json()
    assert res["within_tolerance"] is True
    assert Decimal(res["variance"]) == Decimal("0.00")
    assert Decimal(res["expected_cash"]) == counted
    assert res["hours"] >= 0


def test_exact_cash_payment_as_number_not_rejected(felix):
    """Regression (Angel, prod test sale): an EXACT cash payment sent as a JSON NUMBER
    (the till's behaviour) must NOT be falsely rejected as 'Insufficient'. 226.17 round-
    trips through float as 226.16999…, which a naive `tendered < total` rejected with a
    400 even though the till showed change 0.00. Server now compares at cent precision."""
    felix.post(f"{POS}/shift/open", json={"opening_float": "100.00"}).raise_for_status()
    tx = felix.post(f"{POS}/transactions", json={}).json()
    felix.post(f"{POS}/transactions/{tx['id']}/items", json={
        "product_id": None, "name": "Exact-pay regression", "unit_price": "226.17",
        "quantity": 1}).raise_for_status()
    # amount_tendered as a NUMBER equal to the total — exactly what the EXACT button sends.
    done = felix.post(f"{POS}/transactions/{tx['id']}/checkout", json={
        "payment_method": "cash", "amount_tendered": 226.17})
    assert done.status_code in (200, 201), f"EXACT cash wrongly rejected: {done.status_code} {done.text}"
    body = done.json()
    assert body["status"] == "completed"
    assert Decimal(body["total"]) == Decimal("226.17")
    assert Decimal(body["change_given"]) == Decimal("0.00")
    cur = felix.get(f"{POS}/shift/current").json()
    felix.post(f"{POS}/shift/close", json={"counted_cash": cur["expected_cash"]}).raise_for_status()


def test_open_with_denominations_totals_the_float(felix):
    # 2x50 + 11x0.05 = 100.55
    op = felix.post(f"{POS}/shift/open", json={"opening_denoms": {"50": 2, "0.05": 11}}).json()
    assert op["opening_float"] == "100.55"
    cur = felix.get(f"{POS}/shift/current").json()
    assert Decimal(cur["opening_float"]) == Decimal("100.55")


def test_paid_in_out_changes_expected(felix):
    felix.post(f"{POS}/shift/open", json={"opening_float": "100.00"})
    felix.post(f"{POS}/shift/paid", json={"kind": "paid_out", "amount": "30.00", "reason": "milk for the back"})
    felix.post(f"{POS}/shift/paid", json={"kind": "paid_in", "amount": "10.00", "reason": "change top-up"})
    cur = felix.get(f"{POS}/shift/current").json()
    # 100 - 30 + 10 = 80 (no sales rung)
    assert Decimal(cur["expected_cash"]) == Decimal("80.00")
    assert Decimal(cur["paid_out_total"]) == Decimal("30.00")
    assert Decimal(cur["paid_in_total"]) == Decimal("10.00")
    res = felix.post(f"{POS}/shift/close", json={"counted_cash": "80.00"}).json()
    assert res["within_tolerance"] is True


def test_within_20_rappen_passes_without_note(felix):
    felix.post(f"{POS}/shift/open", json={"opening_float": "100.00"})
    # counted 15 rappen over -> green at 0.20 tolerance, no note needed
    res = felix.post(f"{POS}/shift/close", json={"counted_cash": "100.15"}).json()
    assert res["within_tolerance"] is True
    assert Decimal(res["variance"]) == Decimal("0.15")


def test_outside_tolerance_requires_note(felix):
    felix.post(f"{POS}/shift/open", json={"opening_float": "100.00"})
    # 2.00 short, no note -> blocked
    r = felix.post(f"{POS}/shift/close", json={"counted_cash": "98.00"})
    assert r.status_code == 400
    assert "note" in r.text.lower()
    # still open -> closing WITH a note succeeds and records the variance
    r2 = felix.post(f"{POS}/shift/close",
                    json={"counted_cash": "98.00", "note": "two short, gave wrong change once"}).json()
    assert r2["within_tolerance"] is False
    assert Decimal(r2["variance"]) == Decimal("-2.00")
    assert r2["short"] is True


def test_double_open_is_rejected(felix):
    felix.post(f"{POS}/shift/open", json={"opening_float": "100.00"})
    r = felix.post(f"{POS}/shift/open", json={"opening_float": "50.00"})
    assert r.status_code == 400
    assert "already" in r.text.lower()


def test_close_without_open_is_404(felix):
    # fixture already ensured closed
    r = felix.post(f"{POS}/shift/close", json={"counted_cash": "0"})
    assert r.status_code == 404


def test_paid_requires_kind_amount_reason(felix):
    felix.post(f"{POS}/shift/open", json={"opening_float": "100.00"})
    assert felix.post(f"{POS}/shift/paid", json={"kind": "bogus", "amount": "5", "reason": "x y"}).status_code == 400
    assert felix.post(f"{POS}/shift/paid", json={"kind": "paid_out", "amount": "0", "reason": "x y"}).status_code == 400
    assert felix.post(f"{POS}/shift/paid", json={"kind": "paid_out", "amount": "5", "reason": ""}).status_code == 400


def test_last_shift_returns_the_closed_report(felix):
    felix.post(f"{POS}/shift/open", json={"opening_float": "100.00"})
    felix.post(f"{POS}/shift/close", json={"counted_cash": "100.00"})
    last = felix.get(f"{POS}/shift/last").json()
    assert last["ok"] is True
    assert last["within_tolerance"] is True
    assert Decimal(last["opening_float"]) == Decimal("100.00")
    assert last["closed_at"] is not None
    assert last["hours"] is not None


def test_shift_transactions_itemized_log(felix):
    """The one-pager Pam hands in: the shift's transactions + every item sold."""
    felix.post(f"{POS}/shift/open", json={"opening_float": "100.00"})
    _ring_custom_cash(felix, "42.00")
    _ring_custom_cash(felix, "17.50")
    closed = felix.post(f"{POS}/shift/close", json={"counted_cash": "159.50"}).json()
    sid = closed["shift_id"]

    log = felix.get(f"{POS}/shift/{sid}/transactions").json()
    assert log["transaction_count"] == 2, "both sales appear in the shift log"
    assert log["item_count"] >= 2
    # Every transaction carries its line items with names + totals.
    names = [it["name"] for t in log["transactions"] for it in t["items"]]
    assert "Cash test item" in names
    totals = [Decimal(t["total"]) for t in log["transactions"]]
    assert Decimal("42.00") in totals and Decimal("17.50") in totals


def test_shift_transactions_scoped_to_window_and_cashier(felix):
    """A sale rung in a PRIOR shift must not appear in a later shift's log. (Cash sales
    require an open drawer now, so the 'before' sale lives in its own earlier shift rather
    than being rung drawer-less.)"""
    felix.post(f"{POS}/shift/open", json={"opening_float": "100.00"})
    _ring_custom_cash(felix, "99.00")          # in the FIRST shift
    felix.post(f"{POS}/shift/close", json={"counted_cash": "199.00"})

    felix.post(f"{POS}/shift/open", json={"opening_float": "100.00"})
    _ring_custom_cash(felix, "42.00")          # in the SECOND (current) shift
    closed = felix.post(f"{POS}/shift/close", json={"counted_cash": "142.00"}).json()
    log = felix.get(f"{POS}/shift/{closed['shift_id']}/transactions").json()
    totals = [Decimal(t["total"]) for t in log["transactions"]]
    assert Decimal("42.00") in totals
    assert Decimal("99.00") not in totals, "pre-shift sale excluded from the log"


def test_daily_summary_mine_is_per_cashier(felix):
    """?mine=true shows the caller's own takings; Felix's sale must not touch Pam's."""
    pam = _sess("pam")
    pam_before = Decimal(str(pam.get(
        f"{POS}/reports/daily-summary", params={"mine": "true"}).json()["total_sales"]))

    felix.post(f"{POS}/shift/open", json={"opening_float": "100.00"})
    price = _ring_custom_cash(felix, "42.00")

    fmine = felix.get(f"{POS}/reports/daily-summary", params={"mine": "true"}).json()
    store = felix.get(f"{POS}/reports/daily-summary").json()
    pam_after = Decimal(str(pam.get(
        f"{POS}/reports/daily-summary", params={"mine": "true"}).json()["total_sales"]))

    assert Decimal(str(fmine["cash_total"])) >= price, "my sale counts toward MY summary"
    assert Decimal(str(store["total_sales"])) >= Decimal(str(fmine["total_sales"])), "mine ⊆ store"
    assert pam_after == pam_before, "Felix's sale must NOT appear in Pam's own summary"

    cur = felix.get(f"{POS}/shift/current").json()
    felix.post(f"{POS}/shift/close", json={"counted_cash": cur["expected_cash"]})


def test_shifts_are_per_cashier(felix):
    """Pam's drawer must not see Felix's sales, and vice versa."""
    pam = _sess("pam")
    _ensure_closed(pam)
    try:
        felix.post(f"{POS}/shift/open", json={"opening_float": "100.00"})
        pam.post(f"{POS}/shift/open", json={"opening_float": "200.00"})

        # Felix rings a cash sale; it must land on Felix's drawer only.
        price = _ring_custom_cash(felix, "42.00")

        fcur = felix.get(f"{POS}/shift/current").json()
        pcur = pam.get(f"{POS}/shift/current").json()
        assert Decimal(fcur["cash_sales"]) == price, "Felix should see his own sale"
        assert Decimal(pcur["cash_sales"]) == Decimal("0.00"), "Pam must NOT see Felix's sale"
        assert Decimal(pcur["expected_cash"]) == Decimal("200.00"), "Pam's drawer is just her float"
    finally:
        _ensure_closed(pam)

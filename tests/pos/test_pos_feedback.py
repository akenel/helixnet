"""
POS in-app feedback -> Backlog board.

LOCKS the 2026-06-21 tie-in: a cashier can report a bug/idea from inside the
till and it lands as a real item on the SAME backlog board (/backlog) the
La Piazza 💬 button feeds. The POS token (kc-pos-realm-dev, pos-cashier) can't
call the bottega feedback endpoint (different realm/roles), so POS has its own
`POST /pos/feedback` that writes the same BacklogItemModel.
"""
from conftest import POS


def test_feedback_files_a_backlog_item(session):
    """A bug report returns ok + a BL-XXX ref + an item number."""
    r = session.post(f"{POS}/feedback", json={
        "kind": "bug",
        "title": "Till froze after scanning a grinder",
        "body": "Scanned the grinder, screen went white. Repro on staging.",
    })
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["ok"] is True
    assert j["item_number"] >= 1
    assert j["ref"] == f"BL-{j['item_number']:03d}"


def test_feedback_numbers_are_monotonic(session):
    """Two filings get two distinct, increasing BL numbers (shared sequence)."""
    a = session.post(f"{POS}/feedback", json={"kind": "idea", "title": "Add a dark mode to the till"}).json()
    b = session.post(f"{POS}/feedback", json={"kind": "other", "title": "Thanks, the receipt prints clean now"}).json()
    assert b["item_number"] > a["item_number"]


def test_feedback_rejects_short_title(session):
    """A 1-2 char title is rejected -- no junk on the board."""
    r = session.post(f"{POS}/feedback", json={"kind": "bug", "title": "x"})
    assert r.status_code == 400


def test_feedback_normalizes_unknown_kind(session):
    """An unknown kind is accepted and normalized (no 422) -- still files."""
    r = session.post(f"{POS}/feedback", json={"kind": "banana", "title": "Odd kind should still file"})
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True


def test_feedback_requires_auth():
    """No token -> 401/403, never an anonymous write to the board."""
    import requests
    requests.packages.urllib3.disable_warnings()
    r = requests.post(f"{POS}/feedback", json={"kind": "bug", "title": "anonymous attempt"},
                      verify=False, timeout=15)
    assert r.status_code in (401, 403)

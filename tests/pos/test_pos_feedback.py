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


# A 1x1 transparent PNG as a data-URL -- a valid, tiny image attachment.
_TINY_PNG = ("data:image/png;base64,"
             "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")


def test_feedback_accepts_screenshot_and_meta(session):
    """A valid image data-URL + context metadata -> filed, screenshot flag true."""
    r = session.post(f"{POS}/feedback", json={
        "kind": "bug",
        "title": "Screenshot attachment should persist",
        "body": "with a screenshot",
        "screenshot": _TINY_PNG,
        "meta": {"path": "/pos/checkout", "userAgent": "pytest-UA",
                 "viewport": "1280×720", "online": True},
    })
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["ok"] is True
    assert j.get("screenshot") is True


def test_feedback_drops_non_image_attachment(session):
    """A non-image / malformed data-URL is dropped (not stored) but the report still files."""
    r = session.post(f"{POS}/feedback", json={
        "kind": "bug", "title": "Malformed attachment is dropped",
        "screenshot": "data:text/plain;base64,aGVsbG8=",
    })
    assert r.status_code == 200, r.text
    assert r.json().get("screenshot") is False


def test_feedback_without_screenshot_is_fine(session):
    """No attachment -> filed normally, screenshot flag false."""
    r = session.post(f"{POS}/feedback", json={"kind": "idea", "title": "No screenshot here"})
    assert r.status_code == 200, r.text
    assert r.json().get("screenshot") is False


# A tiny valid PDF as a data-URL -- a one-page empty doc (minimal but parseable header).
_TINY_PDF = ("data:application/pdf;base64,"
             "JVBERi0xLjAKMSAwIG9iajw8Pj5zdHJlYW0KZW5kc3RyZWFtCmVuZG9iagp0cmFpbGVyPDwvUm9vdCAxIDAgUj4+")


def test_feedback_accepts_file_attachments(session):
    """User-attached files (an image + a PDF) ride along and the count comes back."""
    r = session.post(f"{POS}/feedback", json={
        "kind": "bug",
        "title": "Attachments should persist",
        "attachments": [
            {"name": "till.png", "type": "image/png", "data": _TINY_PNG},
            {"name": "receipt.pdf", "type": "application/pdf", "data": _TINY_PDF},
        ],
    })
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["ok"] is True
    assert j.get("attachments") == 2


def test_feedback_drops_disallowed_attachment_types(session):
    """A non-image/non-PDF attachment is dropped; valid ones in the batch survive."""
    r = session.post(f"{POS}/feedback", json={
        "kind": "bug", "title": "Mixed attachment batch",
        "attachments": [
            {"name": "ok.png", "type": "image/png", "data": _TINY_PNG},
            {"name": "evil.txt", "type": "text/plain", "data": "data:text/plain;base64,aGk="},
        ],
    })
    assert r.status_code == 200, r.text
    assert r.json().get("attachments") == 1


def test_feedback_caps_attachment_count(session):
    """More than the max files are clamped down to the cap (no DB bloat)."""
    many = [{"name": f"f{i}.png", "type": "image/png", "data": _TINY_PNG} for i in range(9)]
    r = session.post(f"{POS}/feedback", json={
        "kind": "bug", "title": "Too many files get clamped", "attachments": many,
    })
    assert r.status_code == 200, r.text
    assert r.json().get("attachments") == 5


def test_feedback_handles_malformed_attachments(session):
    """Junk attachment entries never crash the endpoint -- robust to a noisy client."""
    r = session.post(f"{POS}/feedback", json={
        "kind": "bug", "title": "Malformed attachments tolerated",
        "attachments": ["nope", 7, {"name": "x"}, {"data": 123}],
    })
    assert r.status_code == 200, r.text
    j = r.json()
    assert j.get("ok") is True
    assert j.get("attachments") == 0


def test_feedback_severity_maps_to_priority(session):
    """One-tap severity chips set the backlog priority (board sorts itself)."""
    cases = {"blocking": "high", "annoying": "medium", "cosmetic": "low"}
    for sev, prio in cases.items():
        r = session.post(f"{POS}/feedback", json={
            "kind": "bug", "severity": sev, "title": f"Severity {sev} should be {prio}"})
        assert r.status_code == 200, r.text
        j = r.json()
        assert j.get("severity") == sev
        assert j.get("priority") == prio, f"{sev} -> {j.get('priority')}, expected {prio}"


def test_feedback_unknown_severity_defaults_medium(session):
    """A bogus severity falls back to annoying/medium -- never 422, always files."""
    r = session.post(f"{POS}/feedback", json={
        "kind": "bug", "severity": "apocalyptic", "title": "Bogus severity defaults"})
    assert r.status_code == 200, r.text
    j = r.json()
    assert j.get("severity") == "annoying"
    assert j.get("priority") == "medium"


def test_feedback_accepts_diagnostics(session):
    """Console/network breadcrumbs ride along and the report still files cleanly."""
    r = session.post(f"{POS}/feedback", json={
        "kind": "bug", "severity": "blocking",
        "title": "Diagnostics should attach",
        "diagnostics": [
            {"t": "error", "m": "TypeError: x is undefined @ scan.html:412", "ts": 1},
            {"t": "net", "m": "500 Internal Server Error /api/v1/pos/search", "ts": 2},
            {"t": "warn", "m": "deprecated call", "ts": 3},
        ],
    })
    assert r.status_code == 200, r.text
    assert r.json().get("ok") is True


def test_feedback_handles_malformed_diagnostics(session):
    """Junk diagnostics never crash the endpoint -- robust to a noisy client."""
    r = session.post(f"{POS}/feedback", json={
        "kind": "bug", "title": "Malformed diagnostics are tolerated",
        "diagnostics": ["not-a-dict", 42, {"no_message": True}],
    })
    assert r.status_code == 200, r.text
    assert r.json().get("ok") is True


def test_feedback_requires_auth():
    """No token -> 401/403, never an anonymous write to the board."""
    import requests
    requests.packages.urllib3.disable_warnings()
    r = requests.post(f"{POS}/feedback", json={"kind": "bug", "title": "anonymous attempt"},
                      verify=False, timeout=15)
    assert r.status_code in (401, 403)

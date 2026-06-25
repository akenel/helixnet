"""
POS in-app feedback -> Backlog board.

LOCKS the 2026-06-21 tie-in: a cashier can report a bug/idea from inside the
till and it lands as a real item on the SAME backlog board (/backlog) the
La Piazza 💬 button feeds. The POS token (kc-pos-realm-dev, pos-cashier) can't
call the bottega feedback endpoint (different realm/roles), so POS has its own
`POST /pos/feedback` that writes the same BacklogItemModel.

HYGIENE: these are black-box tests against a LIVE server, so every successful
filing creates a REAL backlog row. To keep the shared board readable, each
row-creating test hides its title behind the `[selftest] ` sentinel via
`file_feedback()`, and the module teardown sweeps them with
`POST /pos/feedback/cleanup-selftest` (test exhaust belongs in the bin).
Tests that file NO row (short-title reject, no-auth) post raw.
"""
import pytest
import requests

from conftest import POS

requests.packages.urllib3.disable_warnings()

# Sentinel — keeps test rows identifiable + sweepable; no human report carries it.
SELFTEST = "[selftest] "


def file_feedback(session, **payload):
    """POST a feedback report with the self-test sentinel prefixed onto the title,
    so the row it creates is swept after the run (see _sweep_selftest_after)."""
    if "title" in payload:
        payload["title"] = SELFTEST + payload["title"]
    return session.post(f"{POS}/feedback", json=payload)


@pytest.fixture(scope="module", autouse=True)
def _sweep_selftest_after(cashier_token):
    """After this module's feedback tests, sweep every `[selftest] ` row off the
    shared backlog board so it stays readable. Runs even if a test fails."""
    yield
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {cashier_token}"})
    try:
        r = s.post(f"{POS}/feedback/cleanup-selftest", verify=False, timeout=15)
        if r.ok:
            print(f"\n[selftest sweep] removed {r.json().get('deleted', '?')} feedback rows")
    except Exception as e:  # never fail the suite on cleanup
        print(f"\n[selftest sweep] skipped: {e}")


def test_feedback_files_a_backlog_item(session):
    """A bug report returns ok + a BL-XXX ref + an item number."""
    r = file_feedback(session,
        kind="bug",
        title="Till froze after scanning a grinder",
        body="Scanned the grinder, screen went white. Repro on staging.",
    )
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["ok"] is True
    assert j["item_number"] >= 1
    assert j["ref"] == f"BL-{j['item_number']:03d}"


def test_feedback_numbers_are_monotonic(session):
    """Two filings get two distinct, increasing BL numbers (shared sequence)."""
    a = file_feedback(session, kind="idea", title="Add a dark mode to the till").json()
    b = file_feedback(session, kind="other", title="Thanks, the receipt prints clean now").json()
    assert b["item_number"] > a["item_number"]


def test_feedback_rejects_short_title(session):
    """A 1-2 char title is rejected -- no junk on the board. (No row -> post raw.)"""
    r = session.post(f"{POS}/feedback", json={"kind": "bug", "title": "x"})
    assert r.status_code == 400


def test_feedback_normalizes_unknown_kind(session):
    """An unknown kind is accepted and normalized (no 422) -- still files."""
    r = file_feedback(session, kind="banana", title="Odd kind should still file")
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True


# A 1x1 transparent PNG as a data-URL -- a valid, tiny image attachment.
_TINY_PNG = ("data:image/png;base64,"
             "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")


def test_feedback_accepts_screenshot_and_meta(session):
    """A valid image data-URL + context metadata -> filed, screenshot flag true."""
    r = file_feedback(session,
        kind="bug",
        title="Screenshot attachment should persist",
        body="with a screenshot",
        screenshot=_TINY_PNG,
        meta={"path": "/pos/checkout", "userAgent": "pytest-UA",
              "viewport": "1280×720", "online": True},
    )
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["ok"] is True
    assert j.get("screenshot") is True


def test_feedback_drops_non_image_attachment(session):
    """A non-image / malformed data-URL is dropped (not stored) but the report still files."""
    r = file_feedback(session,
        kind="bug", title="Malformed attachment is dropped",
        screenshot="data:text/plain;base64,aGVsbG8=",
    )
    assert r.status_code == 200, r.text
    assert r.json().get("screenshot") is False


def test_feedback_without_screenshot_is_fine(session):
    """No attachment -> filed normally, screenshot flag false."""
    r = file_feedback(session, kind="idea", title="No screenshot here")
    assert r.status_code == 200, r.text
    assert r.json().get("screenshot") is False


# A tiny valid PDF as a data-URL -- a one-page empty doc (minimal but parseable header).
_TINY_PDF = ("data:application/pdf;base64,"
             "JVBERi0xLjAKMSAwIG9iajw8Pj5zdHJlYW0KZW5kc3RyZWFtCmVuZG9iagp0cmFpbGVyPDwvUm9vdCAxIDAgUj4+")


def test_feedback_accepts_file_attachments(session):
    """User-attached files (an image + a PDF) ride along and the count comes back."""
    r = file_feedback(session,
        kind="bug",
        title="Attachments should persist",
        attachments=[
            {"name": "till.png", "type": "image/png", "data": _TINY_PNG},
            {"name": "receipt.pdf", "type": "application/pdf", "data": _TINY_PDF},
        ],
    )
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["ok"] is True
    assert j.get("attachments") == 2


def test_feedback_drops_disallowed_attachment_types(session):
    """A non-image/non-PDF attachment is dropped; valid ones in the batch survive."""
    r = file_feedback(session,
        kind="bug", title="Mixed attachment batch",
        attachments=[
            {"name": "ok.png", "type": "image/png", "data": _TINY_PNG},
            {"name": "evil.txt", "type": "text/plain", "data": "data:text/plain;base64,aGk="},
        ],
    )
    assert r.status_code == 200, r.text
    assert r.json().get("attachments") == 1


def test_feedback_caps_attachment_count(session):
    """More than the max files are clamped down to the cap (no DB bloat)."""
    many = [{"name": f"f{i}.png", "type": "image/png", "data": _TINY_PNG} for i in range(9)]
    r = file_feedback(session,
        kind="bug", title="Too many files get clamped", attachments=many,
    )
    assert r.status_code == 200, r.text
    assert r.json().get("attachments") == 5


def test_feedback_handles_malformed_attachments(session):
    """Junk attachment entries never crash the endpoint -- robust to a noisy client."""
    r = file_feedback(session,
        kind="bug", title="Malformed attachments tolerated",
        attachments=["nope", 7, {"name": "x"}, {"data": 123}],
    )
    assert r.status_code == 200, r.text
    j = r.json()
    assert j.get("ok") is True
    assert j.get("attachments") == 0


def test_feedback_severity_maps_to_priority(session):
    """One-tap severity chips set the backlog priority (board sorts itself)."""
    cases = {"blocking": "high", "annoying": "medium", "cosmetic": "low"}
    for sev, prio in cases.items():
        r = file_feedback(session,
            kind="bug", severity=sev, title=f"Severity {sev} should be {prio}")
        assert r.status_code == 200, r.text
        j = r.json()
        assert j.get("severity") == sev
        assert j.get("priority") == prio, f"{sev} -> {j.get('priority')}, expected {prio}"


def test_feedback_unknown_severity_defaults_medium(session):
    """A bogus severity falls back to annoying/medium -- never 422, always files."""
    r = file_feedback(session,
        kind="bug", severity="apocalyptic", title="Bogus severity defaults")
    assert r.status_code == 200, r.text
    j = r.json()
    assert j.get("severity") == "annoying"
    assert j.get("priority") == "medium"


def test_feedback_accepts_diagnostics(session):
    """Console/network breadcrumbs ride along and the report still files cleanly."""
    r = file_feedback(session,
        kind="bug", severity="blocking",
        title="Diagnostics should attach",
        diagnostics=[
            {"t": "error", "m": "TypeError: x is undefined @ scan.html:412", "ts": 1},
            {"t": "net", "m": "500 Internal Server Error /api/v1/pos/search", "ts": 2},
            {"t": "warn", "m": "deprecated call", "ts": 3},
        ],
    )
    assert r.status_code == 200, r.text
    assert r.json().get("ok") is True


def test_feedback_handles_malformed_diagnostics(session):
    """Junk diagnostics never crash the endpoint -- robust to a noisy client."""
    r = file_feedback(session,
        kind="bug", title="Malformed diagnostics are tolerated",
        diagnostics=["not-a-dict", 42, {"no_message": True}],
    )
    assert r.status_code == 200, r.text
    assert r.json().get("ok") is True


def test_feedback_cleanup_sweeps_selftest_rows(session):
    """The sweep endpoint deletes [selftest] rows and reports a count >= what we just
    filed — proving the board self-cleans (the teardown then runs once more)."""
    file_feedback(session, kind="idea", title="A row destined for the sweep")
    r = session.post(f"{POS}/feedback/cleanup-selftest")
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["ok"] is True
    assert j["deleted"] >= 1
    # A second sweep finds nothing left.
    assert session.post(f"{POS}/feedback/cleanup-selftest").json()["deleted"] == 0


def test_feedback_requires_auth():
    """No token -> 401/403, never an anonymous write to the board. (No row -> post raw.)"""
    r = requests.post(f"{POS}/feedback", json={"kind": "bug", "title": "anonymous attempt"},
                      verify=False, timeout=15)
    assert r.status_code in (401, 403)

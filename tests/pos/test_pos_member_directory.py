"""
The member directory + multi-match picker — with 50+ members a cashier must be able
to SEE everyone (alphabetical / newest / top spend), and a search that hits several
people must return them ALL so Pam can pick the right one (the "several Larrys" gap).
"""
import uuid

from conftest import API_BASE

CUST = f"{API_BASE}/api/v1/customers"


def _enroll(session, handle, real_name=None):
    body = {"handle": handle, "age_confirmed": True}
    if real_name:
        body["real_name"] = real_name
    r = session.post(CUST, json=body)
    r.raise_for_status()
    return r.json()["id"]


def test_search_returns_all_matches_for_the_picker(session):
    """Several members sharing a name -> search returns >1 so the UI can offer a picker
    (was: silently loaded only the first)."""
    tag = "TESTlarry" + uuid.uuid4().hex[:6]
    for n in ("a", "b", "c"):
        _enroll(session, f"{tag}_{n}")
    hits = session.get(f"{CUST}/search", params={"q": tag}).json()
    assert len([h for h in hits if h["handle"].startswith(tag)]) >= 3, "all Larrys come back"


def test_directory_lists_everyone_paginated(session):
    r = session.get(CUST, params={"sort": "name", "limit": 5, "offset": 0})
    r.raise_for_status()
    d = r.json()
    assert d["total"] >= 1
    assert d["sort"] == "name"
    assert len(d["customers"]) <= 5
    # a directory row carries what a browse list needs
    row = d["customers"][0]
    for k in ("id", "handle", "loyalty_tier", "credits_balance", "lifetime_spend", "created_at"):
        assert k in row


def test_directory_sort_alphabetical(session):
    handles = [c["handle"].lower() for c in
               session.get(CUST, params={"sort": "name", "limit": 50}).json()["customers"]]
    assert handles == sorted(handles), "A-Z order"


def test_directory_sort_recent_surfaces_new_signups(session):
    """A just-enrolled member shows near the top of the 'newest' sort."""
    handle = "TESTrecent_" + uuid.uuid4().hex[:8]
    _enroll(session, handle)
    top = [c["handle"] for c in
           session.get(CUST, params={"sort": "recent", "limit": 10}).json()["customers"]]
    assert handle in top, "newest signup is at the top of the recent sort"


def test_directory_rejects_bad_sort(session):
    assert session.get(CUST, params={"sort": "haxor"}).status_code == 422

"""Black-box: the AI End-of-Day Survey endpoint (POST /pos/day-survey/draft).

Verifies the contract My Day relies on: any POS role can draft their day, the shape is
stable, and it NEVER errors — even with no brain configured it returns the honest
deterministic fallback. (The AI quality itself is exercised by the unit tests.)
"""
from conftest import POS


def test_day_survey_draft_shape(session):
    r = session.post(f"{POS}/day-survey/draft", json={})
    assert r.status_code == 200, r.text
    d = r.json()
    # The fields My Day reads.
    assert d["busy_level"] in ("busy", "steady", "slow")
    assert isinstance(d["footfall_estimate"], int)
    assert "summary" in d and isinstance(d["summary"], str)
    assert "ai" in d                       # whether the brain drafted it or we fell back
    assert "facts" in d and "transaction_count" in d["facts"]


def test_day_survey_requires_auth():
    import requests
    requests.packages.urllib3.disable_warnings()
    r = requests.post(f"{POS}/day-survey/draft", json={}, verify=False, timeout=15)
    assert r.status_code in (401, 403), r.status_code

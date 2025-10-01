import os
# Set default API target before importing the harness module
os.environ.setdefault("API_BASE_URL", "http://localhost:8000")

from super_test_suite import run_smoke_test

def test_smoke():
    r = run_smoke_test()
    assert r.get("ok"), f"Smoke failed: {r.get('error')}"

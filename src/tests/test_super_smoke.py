"""
Smoke test suite for basic API functionality check.
"""
# CRITICAL FIX: Use relative import (the '.') since super_test_suite.py 
# is in the same directory as this file.
from .super_test_suite import run_smoke_test

def test_smoke():
    """
    Runs the comprehensive smoke test defined in super_test_suite.py 
    to check critical API endpoints (Create User, List Users).
    """
    r = run_smoke_test()
    # If the smoke test failed, the 'error' message will be displayed in the assertion.
    assert r.get("ok"), f"Smoke failed: {r.get('error')}"

# NOTE: You may also need to check test_job_submission.py for similar import issues later.

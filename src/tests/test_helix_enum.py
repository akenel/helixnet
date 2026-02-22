# File: src/tests/test_helix_enum.py
"""
HelixEnum Standard Tests -- case-insensitive enum safety net.

Proves that HelixEnum resolves any case to the correct member.
If this breaks, every enum in the system is at risk of silent
mismatches between Python, Postgres, and API inputs.

"Be water, my friend." -- case flows through, no friction.
"""
from src.core.constants import HelixEnum
from src.db.models.qa_test_result_model import (
    BugStatus, BugSeverity, BugActivityType, TestStatus,
)


class TestHelixEnumCaseInsensitive:
    """HelixEnum must resolve values regardless of case."""

    def test_lowercase_resolves(self):
        assert BugStatus("open") == BugStatus.OPEN
        assert BugSeverity("critical") == BugSeverity.CRITICAL
        assert TestStatus("pending") == TestStatus.PENDING

    def test_uppercase_resolves(self):
        assert BugStatus("OPEN") == BugStatus.OPEN
        assert BugSeverity("CRITICAL") == BugSeverity.CRITICAL
        assert TestStatus("PENDING") == TestStatus.PENDING

    def test_mixed_case_resolves(self):
        assert BugStatus("Open") == BugStatus.OPEN
        assert BugStatus("In_Progress") == BugStatus.IN_PROGRESS
        assert BugSeverity("High") == BugSeverity.HIGH

    def test_snake_case_variants(self):
        assert BugStatus("IN_PROGRESS") == BugStatus.IN_PROGRESS
        assert BugStatus("in_progress") == BugStatus.IN_PROGRESS
        assert BugStatus("In_progress") == BugStatus.IN_PROGRESS
        assert BugActivityType("STATUS_CHANGE") == BugActivityType.STATUS_CHANGE
        assert BugActivityType("status_change") == BugActivityType.STATUS_CHANGE

    def test_invalid_value_raises(self):
        """Unknown values must still raise ValueError."""
        try:
            BugStatus("nonexistent")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_value_is_lowercase(self):
        """Enum .value must always be lowercase (DB/API standard)."""
        assert BugStatus.OPEN.value == "open"
        assert BugStatus.IN_PROGRESS.value == "in_progress"
        assert BugSeverity.CRITICAL.value == "critical"
        assert BugActivityType.STATUS_CHANGE.value == "status_change"

    def test_json_value_is_lowercase(self):
        """Enum .value (used by Pydantic/JSON) must be lowercase."""
        assert BugStatus.OPEN.value == "open"
        assert BugStatus.IN_PROGRESS.value == "in_progress"

    def test_helix_enum_is_base(self):
        """All QA enums must inherit from HelixEnum."""
        assert issubclass(BugStatus, HelixEnum)
        assert issubclass(BugSeverity, HelixEnum)
        assert issubclass(BugActivityType, HelixEnum)
        assert issubclass(TestStatus, HelixEnum)

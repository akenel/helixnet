# File: src/tests/test_bug007_assignment_status.py
"""
BUG-007: "Assigned Mechanic but went to completed stage too"

Two reported issues:
  1. Assigning a mechanic set status to COMPLETED instead of IN_PROGRESS
  2. Timestamp validation error: "Input should be a valid date or date-time, input is too short"

Schema-level tests (no database or Docker needed).
Full endpoint tests require Docker -- see scripts/smoke-test.sh for live verification.

"If one seal fails, check all the seals."
"""
import pytest
from datetime import datetime, date, timezone
from decimal import Decimal
from pydantic import ValidationError

# Import ONLY the schemas -- no app, no database, no Docker needed
from src.schemas.camper_schema import ServiceJobUpdate


# ================================================================
# ISSUE 2: Timestamp / date validation in ServiceJobUpdate schema
# ================================================================

class TestServiceJobUpdateSchema:
    """Test ServiceJobUpdate Pydantic schema handles edge cases from the frontend."""

    def test_empty_string_date_fields_coerced_to_none(self):
        """
        Frontend sends empty strings for date fields when user clears a date input.
        The empty_strings_to_none validator should coerce them to None.
        """
        update = ServiceJobUpdate(
            next_service_date="",
            scheduled_date="",
            start_date="",
            end_date="",
            quote_valid_until="",
        )
        assert update.next_service_date is None
        assert update.scheduled_date is None
        assert update.start_date is None
        assert update.end_date is None
        assert update.quote_valid_until is None

    def test_empty_string_expected_updated_at_coerced_to_none(self):
        """
        BUG-007 Issue 2: Frontend might send expected_updated_at as empty string.
        Should NOT cause "input is too short" error.
        """
        update = ServiceJobUpdate(expected_updated_at="")
        assert update.expected_updated_at is None

    def test_null_date_fields_accepted(self):
        """Explicit null/None values for date fields should work."""
        update = ServiceJobUpdate(
            next_service_date=None,
            scheduled_date=None,
            expected_updated_at=None,
        )
        assert update.next_service_date is None
        assert update.expected_updated_at is None

    def test_valid_date_string_accepted(self):
        """Standard date strings should parse correctly."""
        update = ServiceJobUpdate(
            next_service_date="2026-03-15",
            scheduled_date="2026-02-24",
        )
        assert update.next_service_date == date(2026, 3, 15)
        assert update.scheduled_date == date(2026, 2, 24)

    def test_valid_datetime_for_expected_updated_at(self):
        """ISO datetime string for expected_updated_at should work."""
        update = ServiceJobUpdate(
            expected_updated_at="2026-02-24T10:30:00+00:00",
        )
        assert update.expected_updated_at is not None

    def test_empty_string_numeric_fields_coerced_to_none(self):
        """
        Frontend may send empty strings for numeric fields (hours, cost, mileage).
        Should be coerced to None, not cause validation errors.
        """
        update = ServiceJobUpdate(
            estimated_hours="",
            estimated_parts_cost="",
            mileage_in="",
        )
        assert update.estimated_hours is None
        assert update.estimated_parts_cost is None
        assert update.mileage_in is None

    def test_assigned_to_set_correctly(self):
        """Basic: assigned_to field should be accepted."""
        update = ServiceJobUpdate(assigned_to="Seppi")
        assert update.assigned_to == "Seppi"

    def test_assigned_to_empty_string_coerced_to_none(self):
        """Frontend sends empty string when unassigning."""
        update = ServiceJobUpdate(assigned_to="")
        assert update.assigned_to is None

    def test_exclude_unset_only_includes_provided_fields(self):
        """
        model_dump(exclude_unset=True) should only include fields that were
        explicitly provided. This is how update_job() works -- it only applies
        fields the client actually sent.
        """
        update = ServiceJobUpdate(assigned_to="Seppi")
        data = update.model_dump(exclude_unset=True)
        assert "assigned_to" in data
        assert "status" not in data  # ServiceJobUpdate has no status field
        assert "title" not in data  # Not sent

    def test_schema_has_no_status_field(self):
        """
        CRITICAL: ServiceJobUpdate must NOT have a 'status' field.
        Status changes happen through dedicated endpoints only.
        If someone accidentally adds status to the schema, this test catches it.
        """
        fields = ServiceJobUpdate.model_fields
        assert "status" not in fields, (
            "ServiceJobUpdate should NOT have a 'status' field. "
            "Status changes should go through /jobs/{id}/status or "
            "dedicated endpoints (approve, complete, etc.)"
        )

    def test_realistic_frontend_payload(self):
        """
        Simulate the exact payload the frontend sends when user
        edits a job and assigns a mechanic (from startEditing() in job_detail.html).
        """
        # This matches the editData structure in job_detail.html
        payload = {
            "assigned_to": "Seppi",
            "actual_hours": 0,
            "actual_parts_cost": 0,
            "parts_used": "",
            "parts_on_order": False,
            "parts_po_number": "",
            "work_performed": "",
            "issue_found": "",
            "customer_notes": "",
            "mechanic_notes": "",
            "follow_up_required": False,
            "follow_up_notes": "",
            "next_service_date": "",  # Empty date string -- this is the bug trigger
        }

        # Frontend's saveJob() does: if (v === '') payload[k] = null
        cleaned = {k: (None if v == "" else v) for k, v in payload.items()}

        update = ServiceJobUpdate(**cleaned)
        assert update.assigned_to == "Seppi"
        assert update.next_service_date is None  # Coerced from ""
        assert update.parts_po_number is None    # Coerced from ""

    def test_realistic_frontend_payload_without_js_cleanup(self):
        """
        What if the frontend's empty-string-to-null cleanup DOESN'T run
        (JS error, old cached version, etc.)? The backend validator
        must still handle empty strings.
        """
        payload = {
            "assigned_to": "Seppi",
            "actual_hours": 0,
            "parts_used": "",
            "parts_on_order": False,
            "parts_po_number": "",
            "work_performed": "",
            "customer_notes": "",
            "mechanic_notes": "",
            "follow_up_required": False,
            "follow_up_notes": "",
            "next_service_date": "",  # Raw empty string -- backend must handle
        }

        # Pass raw payload directly (no JS cleanup)
        update = ServiceJobUpdate(**payload)
        assert update.assigned_to == "Seppi"
        assert update.next_service_date is None

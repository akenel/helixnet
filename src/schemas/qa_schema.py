# File: src/schemas/qa_schema.py
# Purpose: Pydantic schemas for QA Testing Dashboard

from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from src.db.models.qa_test_result_model import TestStatus, BugSeverity, BugStatus


# ================================================================
# Test Result Schemas
# ================================================================
class TestResultUpdate(BaseModel):
    """Update a test item status + notes."""
    status: TestStatus = Field(..., description="Test result: pass, fail, skip, blocked")
    tester_name: Optional[str] = Field(None, max_length=100, description="Who ran this test")
    notes: Optional[str] = Field(None, description="Tester observations")


class TestResultRead(BaseModel):
    """Full test item for display."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    phase: int
    phase_name: str
    sort_order: int
    title: str
    description: Optional[str] = None
    status: TestStatus
    tester_name: Optional[str] = None
    notes: Optional[str] = None
    executed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# ================================================================
# Bug Report Schemas
# ================================================================
class BugReportCreate(BaseModel):
    """Create a new bug report."""
    title: str = Field(..., max_length=200, description="Bug title")
    description: str = Field(..., description="What happened and what was expected")
    severity: BugSeverity = Field(default=BugSeverity.MEDIUM, description="Bug severity")
    test_result_id: Optional[UUID] = Field(None, description="Link to the test that found this bug")
    screenshot_data: Optional[str] = Field(None, description="Screenshot as base64 data URL")
    browser_info: Optional[str] = Field(None, max_length=200, description="Browser/device info")
    reported_by: str = Field(default="Anne", max_length=100, description="Who reported this")


class BugReportUpdate(BaseModel):
    """Update a bug report."""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    severity: Optional[BugSeverity] = None
    status: Optional[BugStatus] = None
    screenshot_data: Optional[str] = Field(None, description="Screenshot as base64 data URL")


class BugReportRead(BaseModel):
    """Full bug report for display."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    severity: BugSeverity
    status: BugStatus
    test_result_id: Optional[UUID] = None
    screenshot_data: Optional[str] = None
    browser_info: Optional[str] = None
    reported_by: str
    created_at: datetime
    updated_at: datetime


# ================================================================
# Dashboard Summary Schemas
# ================================================================
class PhaseProgress(BaseModel):
    """Progress for a single phase."""
    phase: int
    phase_name: str
    total: int
    passed: int
    failed: int
    skipped: int
    blocked: int
    pending: int
    percent_complete: float = Field(description="Percentage of tests completed (non-pending)")


class DashboardSummary(BaseModel):
    """Overall testing progress."""
    total_tests: int
    passed: int
    failed: int
    skipped: int
    blocked: int
    pending: int
    percent_complete: float
    total_bugs: int
    open_bugs: int
    critical_bugs: int

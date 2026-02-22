# File: src/schemas/qa_schema.py
# Purpose: Pydantic schemas for QA Testing Dashboard

from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from src.db.models.qa_test_result_model import TestStatus, BugSeverity, BugStatus, BugCategory


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
    title: str = Field(..., min_length=3, max_length=200, description="Bug title")
    description: str = Field(..., min_length=10, description="What happened and what was expected")
    severity: BugSeverity = Field(default=BugSeverity.MEDIUM, description="Bug severity")
    category: BugCategory = Field(default=BugCategory.FUNCTIONAL, description="Bug type: functional, cosmetic, performance, data, security")
    test_result_id: Optional[UUID] = Field(None, description="Link to the test that found this bug")
    screenshot_data: Optional[str] = Field(None, description="Screenshot as base64 data URL")
    browser_info: Optional[str] = Field(None, max_length=200, description="Browser/device info")
    reported_by: str = Field(default="Anne", min_length=1, max_length=100, description="Who reported this")


class BugReportUpdate(BaseModel):
    """Update a bug report."""
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=10)
    severity: Optional[BugSeverity] = None
    category: Optional[BugCategory] = None
    status: Optional[BugStatus] = None
    assigned_to: Optional[str] = Field(None, max_length=100, description="Assign to someone (empty string to unassign)")
    git_sha: Optional[str] = Field(None, min_length=7, max_length=40, description="Git commit SHA that fixes this bug")
    screenshot_data: Optional[str] = Field(None, description="Screenshot as base64 data URL")
    comment: Optional[str] = Field(None, min_length=1, description="Activity comment (logged in activity trail)")
    actor: str = Field(default="Anne", min_length=1, max_length=100, description="Who is making this update")


class BugCommitCreate(BaseModel):
    """Link a git commit to a bug."""
    sha: str = Field(..., min_length=7, max_length=40, description="Git commit SHA")
    message: str = Field(..., min_length=3, max_length=200, description="Commit message (first ~50 chars)")
    committed_at: Optional[datetime] = Field(None, description="When the commit was made (defaults to now)")
    actor: str = Field(default="Tigs", min_length=1, max_length=100, description="Who is linking this commit")


class BugCommitRead(BaseModel):
    """Git commit linked to a bug."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sha: str
    message: str
    committed_at: datetime
    created_at: datetime


class BugReportRead(BaseModel):
    """Full bug report for display."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    bug_number: int
    title: str
    description: str
    severity: BugSeverity
    category: Optional[BugCategory] = None
    status: BugStatus
    assigned_to: Optional[str] = None
    git_sha: Optional[str] = None
    test_result_id: Optional[UUID] = None
    screenshot_data: Optional[str] = None
    browser_info: Optional[str] = None
    reported_by: str
    commits: list[BugCommitRead] = []
    created_at: datetime
    updated_at: datetime


class BugActivityRead(BaseModel):
    """Activity log entry for display."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    bug_id: UUID
    activity_type: str
    actor: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    comment: Optional[str] = None
    created_at: datetime


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

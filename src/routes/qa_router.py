# File: src/routes/qa_router.py
# Purpose: QA Testing Dashboard -- API + HTML routes
# Auth: No Keycloak auth initially (Anne accesses from Kenya)
# TODO: Add require_roles(["qa-tester"]) when ready

import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db_session
from src.db.models.qa_test_result_model import (
    QATestResultModel, TestStatus,
    QABugReportModel, BugSeverity, BugStatus,
)
from src.schemas.qa_schema import (
    TestResultUpdate, TestResultRead,
    BugReportCreate, BugReportUpdate, BugReportRead,
    DashboardSummary, PhaseProgress,
)

logger = logging.getLogger("helix.qa_router")

# ================================================================
# Router Setup
# ================================================================
router = APIRouter(prefix="/api/v1/testing", tags=["QA Testing Dashboard"])
html_router = APIRouter(tags=["QA Testing Dashboard - Web UI"])

templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


# ================================================================
# API: Dashboard Summary
# ================================================================
@router.get("/summary", response_model=DashboardSummary)
async def get_summary(db: AsyncSession = Depends(get_db_session)):
    """Overall testing progress stats."""
    # Test counts by status
    result = await db.execute(
        select(
            QATestResultModel.status,
            func.count().label("cnt"),
        ).group_by(QATestResultModel.status)
    )
    status_counts = {row.status: row.cnt for row in result}

    total = sum(status_counts.values())
    passed = status_counts.get(TestStatus.PASS, 0)
    failed = status_counts.get(TestStatus.FAIL, 0)
    skipped = status_counts.get(TestStatus.SKIP, 0)
    blocked = status_counts.get(TestStatus.BLOCKED, 0)
    pending = status_counts.get(TestStatus.PENDING, 0)
    completed = total - pending
    percent = (completed / total * 100) if total > 0 else 0

    # Bug counts
    bug_total = await db.execute(
        select(func.count()).select_from(QABugReportModel)
    )
    total_bugs = bug_total.scalar() or 0

    bug_open = await db.execute(
        select(func.count()).select_from(QABugReportModel).where(
            QABugReportModel.status.in_([BugStatus.OPEN, BugStatus.IN_PROGRESS])
        )
    )
    open_bugs = bug_open.scalar() or 0

    bug_critical = await db.execute(
        select(func.count()).select_from(QABugReportModel).where(
            and_(
                QABugReportModel.severity == BugSeverity.CRITICAL,
                QABugReportModel.status.in_([BugStatus.OPEN, BugStatus.IN_PROGRESS]),
            )
        )
    )
    critical_bugs = bug_critical.scalar() or 0

    return DashboardSummary(
        total_tests=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        blocked=blocked,
        pending=pending,
        percent_complete=round(percent, 1),
        total_bugs=total_bugs,
        open_bugs=open_bugs,
        critical_bugs=critical_bugs,
    )


# ================================================================
# API: Phase Progress
# ================================================================
@router.get("/phases", response_model=list[PhaseProgress])
async def get_phases(db: AsyncSession = Depends(get_db_session)):
    """Per-phase progress breakdown."""
    result = await db.execute(
        select(
            QATestResultModel.phase,
            QATestResultModel.phase_name,
            QATestResultModel.status,
            func.count().label("cnt"),
        ).group_by(
            QATestResultModel.phase,
            QATestResultModel.phase_name,
            QATestResultModel.status,
        ).order_by(QATestResultModel.phase)
    )

    # Build phase data
    phases = {}
    for row in result:
        key = row.phase
        if key not in phases:
            phases[key] = {
                "phase": row.phase,
                "phase_name": row.phase_name,
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "blocked": 0,
                "pending": 0,
            }
        phases[key]["total"] += row.cnt
        if row.status == TestStatus.PASS:
            phases[key]["passed"] += row.cnt
        elif row.status == TestStatus.FAIL:
            phases[key]["failed"] += row.cnt
        elif row.status == TestStatus.SKIP:
            phases[key]["skipped"] += row.cnt
        elif row.status == TestStatus.BLOCKED:
            phases[key]["blocked"] += row.cnt
        elif row.status == TestStatus.PENDING:
            phases[key]["pending"] += row.cnt

    output = []
    for key in sorted(phases.keys()):
        p = phases[key]
        completed = p["total"] - p["pending"]
        pct = (completed / p["total"] * 100) if p["total"] > 0 else 0
        output.append(PhaseProgress(
            phase=p["phase"],
            phase_name=p["phase_name"],
            total=p["total"],
            passed=p["passed"],
            failed=p["failed"],
            skipped=p["skipped"],
            blocked=p["blocked"],
            pending=p["pending"],
            percent_complete=round(pct, 1),
        ))

    return output


# ================================================================
# API: Test Items
# ================================================================
@router.get("/tests", response_model=list[TestResultRead])
async def list_tests(
    phase: int | None = None,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db_session),
):
    """List all test items. Filter by phase or status."""
    query = select(QATestResultModel)

    if phase is not None:
        query = query.where(QATestResultModel.phase == phase)

    if status_filter:
        try:
            ts = TestStatus(status_filter)
            query = query.where(QATestResultModel.status == ts)
        except ValueError:
            pass

    query = query.order_by(QATestResultModel.phase, QATestResultModel.sort_order)
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/tests/{test_id}", response_model=TestResultRead)
async def update_test(
    test_id: UUID,
    update: TestResultUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    """Mark a test as pass/fail/skip/blocked with optional notes."""
    result = await db.execute(
        select(QATestResultModel).where(QATestResultModel.id == test_id)
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Test item not found")

    test.status = update.status
    if update.tester_name is not None:
        test.tester_name = update.tester_name
    if update.notes is not None:
        test.notes = update.notes
    test.executed_at = datetime.now(timezone.utc)
    test.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(test)
    return test


@router.post("/tests/reset", status_code=status.HTTP_200_OK)
async def reset_all_tests(db: AsyncSession = Depends(get_db_session)):
    """Reset all tests to pending for a new test cycle."""
    result = await db.execute(select(QATestResultModel))
    tests = result.scalars().all()
    for test in tests:
        test.status = TestStatus.PENDING
        test.tester_name = None
        test.notes = None
        test.executed_at = None
        test.updated_at = datetime.now(timezone.utc)

    await db.commit()
    return {"message": f"Reset {len(tests)} tests to pending"}


# ================================================================
# API: Bug Reports
# ================================================================
@router.post("/bugs", response_model=BugReportRead, status_code=status.HTTP_201_CREATED)
async def create_bug(
    bug: BugReportCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """File a new bug report."""
    # Validate test_result_id if provided
    if bug.test_result_id:
        test_result = await db.execute(
            select(QATestResultModel).where(QATestResultModel.id == bug.test_result_id)
        )
        if not test_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Linked test item not found")

    new_bug = QABugReportModel(
        title=bug.title,
        description=bug.description,
        severity=bug.severity,
        test_result_id=bug.test_result_id,
        screenshot_url=bug.screenshot_url,
        browser_info=bug.browser_info,
        reported_by=bug.reported_by,
    )
    db.add(new_bug)
    await db.commit()
    await db.refresh(new_bug)
    return new_bug


@router.get("/bugs", response_model=list[BugReportRead])
async def list_bugs(db: AsyncSession = Depends(get_db_session)):
    """List all bug reports, newest first."""
    result = await db.execute(
        select(QABugReportModel).order_by(QABugReportModel.created_at.desc())
    )
    return result.scalars().all()


@router.put("/bugs/{bug_id}", response_model=BugReportRead)
async def update_bug(
    bug_id: UUID,
    update: BugReportUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    """Update a bug report status or details."""
    result = await db.execute(
        select(QABugReportModel).where(QABugReportModel.id == bug_id)
    )
    bug = result.scalar_one_or_none()
    if not bug:
        raise HTTPException(status_code=404, detail="Bug report not found")

    if update.title is not None:
        bug.title = update.title
    if update.description is not None:
        bug.description = update.description
    if update.severity is not None:
        bug.severity = update.severity
    if update.status is not None:
        bug.status = update.status
    if update.screenshot_url is not None:
        bug.screenshot_url = update.screenshot_url
    bug.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(bug)
    return bug


# ================================================================
# API: Health Check
# ================================================================
@router.get("/health-check")
async def health_check(db: AsyncSession = Depends(get_db_session)):
    """System health check for the dashboard."""
    health = {"api": "ok", "database": "error", "test_count": 0}
    try:
        result = await db.execute(
            select(func.count()).select_from(QATestResultModel)
        )
        count = result.scalar() or 0
        health["database"] = "ok"
        health["test_count"] = count
    except Exception as e:
        health["database_error"] = str(e)

    return health


# ================================================================
# HTML: Dashboard Page
# ================================================================
@html_router.get("/testing", response_class=HTMLResponse)
async def testing_dashboard(request: Request):
    """Render the QA testing dashboard."""
    return templates.TemplateResponse("testing/dashboard.html", {"request": request})

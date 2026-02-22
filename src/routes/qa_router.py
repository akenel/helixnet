# File: src/routes/qa_router.py
# Purpose: QA Testing Dashboard -- API + HTML routes
# Auth: Keycloak RBAC via camper-qa-tester role

import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db_session
from src.db.models.qa_test_result_model import (
    QATestResultModel, TestStatus,
    QABugReportModel, BugSeverity, BugStatus,
    QABugActivityModel, BugActivityType,
)
from src.schemas.qa_schema import (
    TestResultUpdate, TestResultRead,
    BugReportCreate, BugReportUpdate, BugReportRead, BugActivityRead,
    DashboardSummary, PhaseProgress,
)
from src.core.keycloak_auth import require_roles


def require_qa_tester():
    """QA tester role required."""
    return require_roles(["camper-qa-tester"])

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
async def get_summary(
    current_user: dict = Depends(require_qa_tester()),
    db: AsyncSession = Depends(get_db_session),
):
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
async def get_phases(
    current_user: dict = Depends(require_qa_tester()),
    db: AsyncSession = Depends(get_db_session),
):
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
    current_user: dict = Depends(require_qa_tester()),
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
    current_user: dict = Depends(require_qa_tester()),
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
async def reset_all_tests(
    current_user: dict = Depends(require_qa_tester()),
    db: AsyncSession = Depends(get_db_session),
):
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
    current_user: dict = Depends(require_qa_tester()),
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

    # Auto-assign next bug number
    max_num = await db.execute(
        select(func.coalesce(func.max(QABugReportModel.bug_number), 0))
    )
    next_number = max_num.scalar() + 1

    new_bug = QABugReportModel(
        bug_number=next_number,
        title=bug.title,
        description=bug.description,
        severity=bug.severity,
        test_result_id=bug.test_result_id,
        screenshot_data=bug.screenshot_data,
        browser_info=bug.browser_info,
        reported_by=bug.reported_by,
    )
    db.add(new_bug)
    await db.commit()
    await db.refresh(new_bug)
    return new_bug


@router.get("/bugs", response_model=list[BugReportRead])
async def list_bugs(
    current_user: dict = Depends(require_qa_tester()),
    db: AsyncSession = Depends(get_db_session),
):
    """List all bug reports, newest first."""
    result = await db.execute(
        select(QABugReportModel).order_by(QABugReportModel.created_at.desc())
    )
    return result.scalars().all()


@router.put("/bugs/{bug_id}", response_model=BugReportRead)
async def update_bug(
    bug_id: UUID,
    update: BugReportUpdate,
    current_user: dict = Depends(require_qa_tester()),
    db: AsyncSession = Depends(get_db_session),
):
    """Update a bug report -- auto-creates activity log entries for tracked changes."""
    result = await db.execute(
        select(QABugReportModel).where(QABugReportModel.id == bug_id)
    )
    bug = result.scalar_one_or_none()
    if not bug:
        raise HTTPException(status_code=404, detail="Bug report not found")

    actor = update.actor or "Anne"
    activities = []

    # Track status change
    if update.status is not None and update.status != bug.status:
        activities.append(QABugActivityModel(
            bug_id=bug.id,
            activity_type=BugActivityType.STATUS_CHANGE,
            actor=actor,
            old_value=bug.status.value,
            new_value=update.status.value,
        ))
        bug.status = update.status

    # Track assignment change
    if update.assigned_to is not None and update.assigned_to != (bug.assigned_to or ""):
        new_assignee = update.assigned_to if update.assigned_to else None
        activities.append(QABugActivityModel(
            bug_id=bug.id,
            activity_type=BugActivityType.ASSIGNED,
            actor=actor,
            old_value=bug.assigned_to,
            new_value=new_assignee,
        ))
        bug.assigned_to = new_assignee

    # Track git SHA link
    if update.git_sha is not None and update.git_sha != (bug.git_sha or ""):
        activities.append(QABugActivityModel(
            bug_id=bug.id,
            activity_type=BugActivityType.GIT_LINKED,
            actor=actor,
            new_value=update.git_sha if update.git_sha else None,
        ))
        bug.git_sha = update.git_sha if update.git_sha else None

    # Comment
    if update.comment:
        activities.append(QABugActivityModel(
            bug_id=bug.id,
            activity_type=BugActivityType.COMMENT,
            actor=actor,
            comment=update.comment,
        ))

    # Apply remaining field updates (not tracked in activity log)
    if update.title is not None:
        bug.title = update.title
    if update.description is not None:
        bug.description = update.description
    if update.severity is not None:
        bug.severity = update.severity
    if update.screenshot_data is not None:
        bug.screenshot_data = update.screenshot_data

    bug.updated_at = datetime.now(timezone.utc)

    for activity in activities:
        db.add(activity)

    await db.commit()
    await db.refresh(bug)

    if activities:
        logger.info(f"BUG-{bug.bug_number:03d} updated by {actor}: {len(activities)} activity entries")

    return bug


@router.get("/bugs/{bug_id}/activities", response_model=list[BugActivityRead])
async def get_bug_activities(
    bug_id: UUID,
    current_user: dict = Depends(require_qa_tester()),
    db: AsyncSession = Depends(get_db_session),
):
    """Get the activity log for a bug report, newest first."""
    bug_result = await db.execute(
        select(QABugReportModel).where(QABugReportModel.id == bug_id)
    )
    if not bug_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Bug report not found")

    result = await db.execute(
        select(QABugActivityModel)
        .where(QABugActivityModel.bug_id == bug_id)
        .order_by(QABugActivityModel.created_at.desc())
    )
    return result.scalars().all()


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
# HTML: Login + OAuth Callback
# ================================================================
@html_router.get("/testing/login", response_class=HTMLResponse)
async def testing_login(request: Request):
    """QA login page."""
    return templates.TemplateResponse("testing/login.html", {"request": request})


@html_router.get("/testing/callback")
async def testing_oauth_callback(request: Request, code: str = None, error: str = None):
    """OAuth2 callback -- exchanges code for token, redirects to dashboard."""
    import httpx

    if error:
        logger.error(f"QA OAuth callback error: {error}")
        return RedirectResponse(url="/testing/login?error=" + error)

    if not code:
        logger.warning("QA OAuth callback without code")
        return RedirectResponse(url="/testing/login?error=no_code")

    keycloak_internal_url = "http://keycloak:8080"
    realm = "kc-camper-service-realm-dev"
    client_id = "camper_service_web"

    forwarded_proto = request.headers.get("x-forwarded-proto", "https")
    forwarded_host = request.headers.get("x-forwarded-host") or request.headers.get("host", "helix.local")
    redirect_uri = f"{forwarded_proto}://{forwarded_host}/testing/callback"

    logger.info(f"QA token exchange redirect_uri: {redirect_uri}")

    token_endpoint = f"{keycloak_internal_url}/realms/{realm}/protocol/openid-connect/token"

    try:
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            response = await client.post(
                token_endpoint,
                data={
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                logger.error(f"QA token exchange failed: {response.status_code} - {response.text}")
                return RedirectResponse(url="/testing/login?error=token_exchange_failed")

            tokens = response.json()
            access_token = tokens.get("access_token")

            if not access_token:
                logger.error("QA: No access_token in response")
                return RedirectResponse(url="/testing/login?error=no_token")

            logger.info("QA OAuth callback successful, redirecting to dashboard")
            return RedirectResponse(url=f"/testing#token={access_token}")

    except Exception as e:
        logger.error(f"QA token exchange exception: {e}")
        return RedirectResponse(url="/testing/login?error=token_exchange_error")


# ================================================================
# HTML: Dashboard + Static Pages
# ================================================================
@html_router.get("/testing", response_class=HTMLResponse)
async def testing_dashboard(request: Request):
    """Render the QA testing dashboard."""
    return templates.TemplateResponse("testing/dashboard.html", {"request": request})


@html_router.get("/training", response_class=HTMLResponse)
async def training_guide():
    """Serve the training guide -- How Code Gets To You."""
    training_file = templates_dir / "testing" / "training.html"
    return FileResponse(training_file, media_type="text/html")


@html_router.get("/how-to-report-bugs", response_class=HTMLResponse)
async def how_to_report_bugs():
    """Serve the interactive bug reporting walkthrough."""
    guide_file = templates_dir / "testing" / "how-to-report-bugs.html"
    return FileResponse(guide_file, media_type="text/html")

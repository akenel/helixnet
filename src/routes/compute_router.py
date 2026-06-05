# File: src/routes/compute_router.py
# Purpose: LPCX -- La Piazza Compute Exchange. API + HTML.
# Auth: Keycloak RBAC, same roles as QA/backlog.
#
# v2: submit INSERTS the job (queued) and PUBLISHES it to RabbitMQ. A dedicated
# aio-pika consumer (src/compute/consumer.py) runs it -- the web process does no
# execution. Kill = a DB flag the consumer polls. The gauge is derived from the DB.

import json
import logging
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db_session, AsyncSessionLocal
from src.db.models.compute_model import ComputeJobModel, ComputeJobStatus, ComputeTemplateModel
from src.schemas.compute_schema import (
    ComputeJobCreate, ComputeJobRead, CreditBalance, BrainLoad, ComputeSummary,
    ComputeTemplateRead, TransferRequest, GrantRequest, LedgerEntryRead,
)
from src.core.keycloak_auth import require_roles
from src.services.compute_service import (
    credit_balance, ensure_starter_grant, brain_load, euro_per_credit,
    ledger_history, transfer_credits, grant_credits,
    LPCX_CREDIT_TOKENS,
)
from src.compute.queue import publish_job


def require_compute_access():
    """Compute access -- same roles as QA/backlog dashboards."""
    return require_roles(["camper-qa-tester", "camper-manager", "camper-admin"])


def require_compute_admin():
    """Granting credits -- managers + admins only."""
    return require_roles(["camper-manager", "camper-admin"])


logger = logging.getLogger("helix.compute_router")

router = APIRouter(prefix="/api/v1/compute", tags=["Compute - LPCX"])
html_router = APIRouter(tags=["Compute - Web UI"])

templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))





# ================================================================
# API
# ================================================================
@router.get("/credits", response_model=CreditBalance)
async def get_credits(
    current_user: dict = Depends(require_compute_access()),
    db: AsyncSession = Depends(get_db_session),
):
    account = current_user["username"]
    balance = await ensure_starter_grant(db, account)
    return CreditBalance(
        account=account, balance=balance,
        credit_tokens=LPCX_CREDIT_TOKENS, euro_per_credit=round(euro_per_credit(), 6),
    )


@router.get("/ledger", response_model=list[LedgerEntryRead])
async def my_ledger(
    limit: int = 25,
    current_user: dict = Depends(require_compute_access()),
    db: AsyncSession = Depends(get_db_session),
):
    """The caller's credit trail (in + out) -- append-only, verifiable."""
    rows = await ledger_history(db, current_user["username"], limit)
    return [LedgerEntryRead.model_validate(r) for r in rows]


@router.post("/credits/transfer")
async def transfer(
    payload: TransferRequest,
    current_user: dict = Depends(require_compute_access()),
    db: AsyncSession = Depends(get_db_session),
):
    """Pay credits to a neighbour. The earn loop: credits come IN to them."""
    sender = current_user["username"]
    await ensure_starter_grant(db, sender)
    try:
        await transfer_credits(db, sender, payload.to_account, payload.amount, payload.note)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True, "balance": await credit_balance(db, sender)}


@router.post("/credits/grant")
async def grant(
    payload: GrantRequest,
    current_user: dict = Depends(require_compute_admin()),
    db: AsyncSession = Depends(get_db_session),
):
    """Admin/manager rewards a contribution or tops up an account."""
    try:
        await grant_credits(db, payload.account, payload.amount,
                            by=current_user["username"], note=payload.note)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True, "account": payload.account,
            "balance": await credit_balance(db, payload.account)}


@router.get("/brain", response_model=BrainLoad)
async def get_brain(
    current_user: dict = Depends(require_compute_access()),
    db: AsyncSession = Depends(get_db_session),
):
    return BrainLoad(**await brain_load(db))


@router.get("/templates", response_model=list[ComputeTemplateRead])
async def list_templates(
    current_user: dict = Depends(require_compute_access()),
    db: AsyncSession = Depends(get_db_session),
):
    """The approved SOP catalog -- the allowlist users pick from."""
    rows = await db.execute(
        select(ComputeTemplateModel)
        .where(ComputeTemplateModel.enabled == True)  # noqa: E712
        .order_by(ComputeTemplateModel.est_credits, ComputeTemplateModel.slug)
    )
    return [ComputeTemplateRead.model_validate(t) for t in rows.scalars().all()]


@router.get("/jobs", response_model=list[ComputeJobRead])
async def list_jobs(
    mine: bool = False,
    limit: int = 50,
    current_user: dict = Depends(require_compute_access()),
    db: AsyncSession = Depends(get_db_session),
):
    q = select(ComputeJobModel).order_by(ComputeJobModel.created_at.desc()).limit(limit)
    if mine:
        q = q.where(ComputeJobModel.owner == current_user["username"])
    result = await db.execute(q)
    return [ComputeJobRead.model_validate(j) for j in result.scalars().all()]


@router.get("/jobs/{job_id}", response_model=ComputeJobRead)
async def get_job(
    job_id: UUID,
    current_user: dict = Depends(require_compute_access()),
    db: AsyncSession = Depends(get_db_session),
):
    job = await db.get(ComputeJobModel, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return ComputeJobRead.model_validate(job)


@router.post("/jobs", response_model=ComputeJobRead, status_code=status.HTTP_201_CREATED)
async def submit_job(
    payload: ComputeJobCreate,
    current_user: dict = Depends(require_compute_access()),
    db: AsyncSession = Depends(get_db_session),
):
    owner = current_user["username"]
    await ensure_starter_grant(db, owner)
    balance = await credit_balance(db, owner)

    # ALLOWLIST (safety by construction): only enabled catalog templates may run.
    tmpl = (await db.execute(
        select(ComputeTemplateModel).where(
            ComputeTemplateModel.slug == payload.template,
            ComputeTemplateModel.enabled == True,  # noqa: E712
        )
    )).scalar_one_or_none()

    byo = payload.brain_mode == "byo"
    # job_number is DB-assigned (IDENTITY) -- atomic, race-free, no app round-trip.
    job = ComputeJobModel(
        template=payload.template,
        node=payload.node,
        owner=owner,
        status=ComputeJobStatus.QUEUED,
        brain_mode=payload.brain_mode,
        brain_model=(payload.byo_model or "byo") if byo else "ollama/turbo",
    )
    if tmpl is None:
        job.status = ComputeJobStatus.REJECTED
        job.reject_reason = f"unknown template '{payload.template}' -- pick one from the catalog"
    # Shared brain needs credits (economic governor); BYO is on your own dime.
    elif not byo and balance <= 0:
        job.status = ComputeJobStatus.REJECTED
        job.reject_reason = "no credits -- earn more (the system teaches efficient SOP use)"
    db.add(job)
    await db.commit()
    await db.refresh(job)

    if job.status != ComputeJobStatus.REJECTED:
        # Hand off to RabbitMQ -- the consumer executes it. No work in the web process.
        await publish_job({
            "job_id": str(job.id),
            "owner": owner,
            "node": job.node,
            "brain_mode": payload.brain_mode,
            "byo_endpoint": payload.byo_endpoint,
            "byo_model": payload.byo_model,
        })

    return ComputeJobRead.model_validate(job)


@router.post("/jobs/{job_id}/kill")
async def kill_job(
    job_id: UUID,
    current_user: dict = Depends(require_compute_access()),
    db: AsyncSession = Depends(get_db_session),
):
    job = await db.get(ComputeJobModel, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    if job.status in (ComputeJobStatus.RUNNING, ComputeJobStatus.QUEUED):
        job.kill_requested = True          # cross-process: the consumer polls this
        await db.commit()
        return {"ok": True, "job_id": str(job_id), "status": "kill requested"}
    return {"ok": False, "job_id": str(job_id), "status": f"job already {job.status.value}"}


@router.get("/summary", response_model=ComputeSummary)
async def get_summary(
    current_user: dict = Depends(require_compute_access()),
    db: AsyncSession = Depends(get_db_session),
):
    total = (await db.execute(select(func.count()).select_from(ComputeJobModel))).scalar() or 0
    rows = await db.execute(
        select(ComputeJobModel.status, func.count().label("cnt")).group_by(ComputeJobModel.status)
    )
    by_status = {row.status.value: row.cnt for row in rows}
    return ComputeSummary(total_jobs=total, by_status=by_status, brain=BrainLoad(**await brain_load(db)))


# ================================================================
# SSE -- live telemetry feed (read-only aggregate; the real backing for the
# dashboard's gauge + job list). Polls the DB once a second.
# ================================================================
@router.get("/stream")
async def stream(request: Request):
    import asyncio  # local: only the stream loop needs it
    async def gen():
        # tell the client the cadence + a hello so EventSource opens cleanly
        yield "retry: 2000\n\n"
        while True:
            if await request.is_disconnected():
                break
            async with AsyncSessionLocal() as db:
                rows = await db.execute(
                    select(ComputeJobModel).order_by(ComputeJobModel.created_at.desc()).limit(12)
                )
                jobs = [ComputeJobRead.model_validate(j).model_dump(mode="json")
                        for j in rows.scalars().all()]
                brain = await brain_load(db)
            payload = {"brain": brain, "jobs": jobs}
            yield f"data: {json.dumps(payload, default=str)}\n\n"
            await asyncio.sleep(1.0)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


# ================================================================
# HTML
# ================================================================
@html_router.get("/compute", response_class=HTMLResponse)
@html_router.get("/compute/dashboard", response_class=HTMLResponse)
async def compute_dashboard(request: Request):
    return templates.TemplateResponse("compute/dashboard.html", {"request": request})


@html_router.get("/compute/faq", response_class=HTMLResponse)
@html_router.get("/compute/help", response_class=HTMLResponse)
async def compute_faq(request: Request):
    return templates.TemplateResponse("compute/faq.html", {"request": request})

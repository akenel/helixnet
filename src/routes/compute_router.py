# File: src/routes/compute_router.py
# Purpose: LPCX -- La Piazza Compute Exchange. API + HTML.
# Auth: Keycloak RBAC, same roles as QA/backlog.
#
# A submitted job is admitted against the shared-brain ceiling (BrainGuard), then a
# background runner ticks progress, consumes brain tokens, debits credits, settles
# the ledger, and wipes. Kill is a flag the runner polls. The brain is SIMULATED by
# default (LPCX_REAL_BRAIN=1 hits local Ollama) so the ceiling -- not tinyllama CPU --
# is the wall we study under load.

import asyncio
import json
import logging
import os
import random
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db_session, AsyncSessionLocal
from src.db.models.compute_model import (
    ComputeJobModel, ComputeJobStatus, ComputeLedgerKind,
)
from src.schemas.compute_schema import (
    ComputeJobCreate, ComputeJobRead, CreditBalance, BrainLoad, ComputeSummary,
)
from src.core.keycloak_auth import require_roles
from src.services.compute_service import (
    brain_guard, credit_balance, post_ledger, ensure_starter_grant,
    credits_for_tokens, verifiable_note, euro_per_credit,
    LPCX_CREDIT_TOKENS,
)


def require_compute_access():
    """Compute access -- same roles as QA/backlog dashboards."""
    return require_roles(["camper-qa-tester", "camper-manager", "camper-admin"])


logger = logging.getLogger("helix.compute_router")

router = APIRouter(prefix="/api/v1/compute", tags=["Compute - LPCX"])
html_router = APIRouter(tags=["Compute - Web UI"])

templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Brain mode
LPCX_REAL_BRAIN = os.getenv("LPCX_REAL_BRAIN", "0") == "1"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "tinyllama:latest")

# In-process kill flags (job_id str). Single-process; Redis at multi-worker scale.
_kill: set[str] = set()


# ================================================================
# Brain step -- one inference. Simulated by default.
# ================================================================
async def _brain_step(prompt: str, endpoint: str | None = None, model: str | None = None) -> int:
    """Return tokens consumed for one step. `endpoint` set => BYO brain target."""
    url = endpoint or OLLAMA_URL
    mdl = model or OLLAMA_MODEL
    if LPCX_REAL_BRAIN or endpoint:
        import httpx
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                f"{url}/api/generate",
                json={"model": mdl, "prompt": prompt, "stream": False},
            )
            r.raise_for_status()
            d = r.json()
            return int(d.get("prompt_eval_count", 0)) + int(d.get("eval_count", 0))
    # simulated brain: realistic latency + token count, no CPU melt
    await asyncio.sleep(0.3 + random.random() * 0.6)
    return random.randint(40, 160)


# ================================================================
# Background job runner
# ================================================================
async def _patch(job_id: UUID, **fields) -> None:
    """Short-lived session: hold a DB connection only for the write, never across
    the brain call. Keeps the 15-slot pool free under load."""
    async with AsyncSessionLocal() as db:
        job = await db.get(ComputeJobModel, job_id)
        if job:
            for k, v in fields.items():
                setattr(job, k, v)
            await db.commit()


async def _execute(job_id: UUID, owner: str, node: str, byo: bool,
                   byo_endpoint: str | None, byo_model: str | None) -> None:
    await _patch(job_id, status=ComputeJobStatus.RUNNING)
    total = 0
    steps = 6
    for step in range(1, steps + 1):
        if str(job_id) in _kill:
            await _patch(job_id, status=ComputeJobStatus.KILLED, reject_reason="killed by requester")
            return
        toks = await _brain_step(
            f"{node}:step{step}",
            endpoint=byo_endpoint if byo else None,
            model=byo_model if byo else None,
        )
        total += toks
        if not byo:
            await brain_guard.record_use(toks)
        await _patch(job_id,
                     tokens=total,
                     progress=min(100, round(step / steps * 100)),
                     credits_burned=0 if byo else credits_for_tokens(total))

    # settle in one short session
    async with AsyncSessionLocal() as db:
        job = await db.get(ComputeJobModel, job_id)
        if not job:
            return
        job.status = ComputeJobStatus.DONE
        job.progress = 100
        if byo:
            await post_ledger(db, owner, ComputeLedgerKind.SPEND, 0, job_id=job_id,
                              counterparty="byo",
                              note=f"CJ-{job.job_number:03d} · {total} tok on BYO brain (off shared quota)")
            logger.info(f"CJ-{job.job_number:03d} done (BYO): {total} tok, 0 shared cr")
        else:
            credits = credits_for_tokens(total)
            note = verifiable_note(job.job_number, total, credits)
            await post_ledger(db, owner, ComputeLedgerKind.SPEND, -credits,
                              job_id=job_id, counterparty=node, note=note)
            await post_ledger(db, node, ComputeLedgerKind.EARN, credits,
                              job_id=job_id, counterparty=owner, note=note)
            logger.info(f"CJ-{job.job_number:03d} done: {total} tok -> {credits} cr")
        await db.commit()


async def run_job(
    job_id: UUID, owner: str, node: str,
    brain_mode: str = "shared", byo_endpoint: str | None = None, byo_model: str | None = None,
) -> None:
    byo = brain_mode == "byo"
    try:
        if byo:
            # BYO bypasses the shared queue entirely -- the escape valve.
            await _execute(job_id, owner, node, byo=True,
                           byo_endpoint=byo_endpoint, byo_model=byo_model)
        else:
            # WAIT YOUR TURN: queue for a shared-brain slot (FIFO), then run.
            async with brain_guard.slot():
                await _execute(job_id, owner, node, byo=False,
                               byo_endpoint=None, byo_model=None)
    except Exception as e:  # noqa: BLE001
        logger.exception("job failed")
        await _patch(job_id, status=ComputeJobStatus.FAILED, reject_reason=str(e)[:200])
    finally:
        _kill.discard(str(job_id))


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


@router.get("/brain", response_model=BrainLoad)
async def get_brain(current_user: dict = Depends(require_compute_access())):
    return BrainLoad(**brain_guard.load())


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
    # Shared brain needs credits (economic governor); BYO is on your own dime.
    if not byo and balance <= 0:
        job.status = ComputeJobStatus.REJECTED
        job.reject_reason = "no credits -- earn more (the system teaches efficient SOP use)"
    db.add(job)
    await db.commit()
    await db.refresh(job)

    if job.status != ComputeJobStatus.REJECTED:
        asyncio.create_task(run_job(
            job.id, owner, job.node,
            brain_mode=payload.brain_mode,
            byo_endpoint=payload.byo_endpoint, byo_model=payload.byo_model,
        ))

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
        _kill.add(str(job_id))
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
    return ComputeSummary(total_jobs=total, by_status=by_status, brain=BrainLoad(**brain_guard.load()))


# ================================================================
# SSE -- live telemetry feed (read-only aggregate; the real backing for the
# dashboard's gauge + job list). Polls DB + BrainGuard once a second.
# ================================================================
@router.get("/stream")
async def stream(request: Request):
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
            payload = {"brain": brain_guard.load(), "jobs": jobs}
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

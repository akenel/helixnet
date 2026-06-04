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
async def _brain_step(prompt: str) -> int:
    """Return tokens consumed for one step."""
    if LPCX_REAL_BRAIN:
        import httpx
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
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
async def run_job(job_id: UUID, owner: str, job_number: int, node: str) -> None:
    admitted, reason = await brain_guard.admit(owner)
    if not admitted:
        async with AsyncSessionLocal() as db:
            job = await db.get(ComputeJobModel, job_id)
            if job:
                job.status = ComputeJobStatus.REJECTED
                job.reject_reason = reason
                await db.commit()
        logger.info(f"CJ-{job_number:03d} rejected: {reason}")
        return

    try:
        async with AsyncSessionLocal() as db:
            job = await db.get(ComputeJobModel, job_id)
            if not job:
                return
            job.status = ComputeJobStatus.RUNNING
            await db.commit()

            total_tokens = 0
            steps = 6
            for step in range(1, steps + 1):
                if str(job_id) in _kill:
                    job.status = ComputeJobStatus.KILLED
                    job.reject_reason = "killed by requester"
                    await db.commit()
                    logger.info(f"CJ-{job_number:03d} killed at {job.progress}%")
                    return
                toks = await _brain_step(f"{node}:{job_number}:step{step}")
                total_tokens += toks
                await brain_guard.record_use(toks)
                job.tokens = total_tokens
                job.progress = min(100, round(step / steps * 100))
                job.credits_burned = credits_for_tokens(total_tokens)
                await db.commit()

            # settle: debit requester, credit the provider node
            job.progress = 100
            job.status = ComputeJobStatus.DONE
            credits = credits_for_tokens(total_tokens)
            note = verifiable_note(job_number, total_tokens, credits)
            await post_ledger(db, owner, ComputeLedgerKind.SPEND, -credits,
                              job_id=job_id, counterparty=node, note=note)
            await post_ledger(db, node, ComputeLedgerKind.EARN, credits,
                              job_id=job_id, counterparty=owner, note=note)
            await db.commit()
            logger.info(f"CJ-{job_number:03d} done: {total_tokens} tok -> {credits} cr")
    except Exception as e:  # noqa: BLE001
        logger.exception(f"CJ-{job_number:03d} failed")
        async with AsyncSessionLocal() as db:
            job = await db.get(ComputeJobModel, job_id)
            if job:
                job.status = ComputeJobStatus.FAILED
                job.reject_reason = str(e)[:200]
                await db.commit()
    finally:
        await brain_guard.release(owner)
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

    next_num = (await db.execute(
        select(func.coalesce(func.max(ComputeJobModel.job_number), 0))
    )).scalar() + 1

    job = ComputeJobModel(
        job_number=next_num,
        template=payload.template,
        node=payload.node,
        owner=owner,
        status=ComputeJobStatus.QUEUED,
    )
    if balance <= 0:
        job.status = ComputeJobStatus.REJECTED
        job.reject_reason = "no credits"
    db.add(job)
    await db.commit()
    await db.refresh(job)

    if job.status != ComputeJobStatus.REJECTED:
        asyncio.create_task(run_job(job.id, owner, job.job_number, job.node))

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

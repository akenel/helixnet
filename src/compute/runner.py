# File: src/compute/runner.py
# Purpose: LPCX job executor. Runs in the CONSUMER process (not the web app).
# Short DB sessions only (never held across the brain call). Cross-process kill via
# the kill_requested column. Brain SIMULATED by default (LPCX_REAL_BRAIN=1 -> Ollama).

import asyncio
import logging
import os
import random
from uuid import UUID

from src.db.database import AsyncSessionLocal
from src.db.models.compute_model import (
    ComputeJobModel, ComputeJobStatus, ComputeLedgerKind,
)
from src.services.compute_service import (
    post_ledger, credits_for_tokens, verifiable_note,
)

logger = logging.getLogger("lpcx.runner")

LPCX_REAL_BRAIN = os.getenv("LPCX_REAL_BRAIN", "0") == "1"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "tinyllama:latest")


async def _brain_step(prompt: str, endpoint: str | None = None, model: str | None = None) -> int:
    url = endpoint or OLLAMA_URL
    mdl = model or OLLAMA_MODEL
    if LPCX_REAL_BRAIN or endpoint:
        import httpx
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(f"{url}/api/generate",
                                  json={"model": mdl, "prompt": prompt, "stream": False})
            r.raise_for_status()
            d = r.json()
            return int(d.get("prompt_eval_count", 0)) + int(d.get("eval_count", 0))
    await asyncio.sleep(0.3 + random.random() * 0.6)
    return random.randint(40, 160)


async def _patch(job_id: UUID, **fields) -> None:
    """Hold a DB connection only for the write, never across the brain call."""
    async with AsyncSessionLocal() as db:
        job = await db.get(ComputeJobModel, job_id)
        if job:
            for k, v in fields.items():
                setattr(job, k, v)
            await db.commit()


async def _is_killed(job_id: UUID) -> bool:
    async with AsyncSessionLocal() as db:
        job = await db.get(ComputeJobModel, job_id)
        return bool(job and job.kill_requested)


async def execute_job(job_id: UUID, owner: str, node: str,
                      brain_mode: str = "shared",
                      byo_endpoint: str | None = None, byo_model: str | None = None) -> None:
    """Run one job to completion. Idempotent-ish: safe to re-deliver (at-least-once);
    a job already DONE/KILLED is skipped."""
    byo = brain_mode == "byo"
    try:
        async with AsyncSessionLocal() as db:
            job = await db.get(ComputeJobModel, job_id)
            if not job or job.status in (ComputeJobStatus.DONE, ComputeJobStatus.KILLED):
                return
        await _patch(job_id, status=ComputeJobStatus.RUNNING)

        total = 0
        steps = 6
        for step in range(1, steps + 1):
            if await _is_killed(job_id):
                await _patch(job_id, status=ComputeJobStatus.KILLED, reject_reason="killed by requester")
                return
            toks = await _brain_step(f"{node}:step{step}",
                                     endpoint=byo_endpoint if byo else None,
                                     model=byo_model if byo else None)
            total += toks
            await _patch(job_id,
                         tokens=total,
                         progress=min(100, round(step / steps * 100)),
                         credits_burned=0 if byo else credits_for_tokens(total))

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
                logger.info(f"CJ-{job.job_number:03d} done (BYO): {total} tok")
            else:
                credits = credits_for_tokens(total)
                note = verifiable_note(job.job_number, total, credits)
                await post_ledger(db, owner, ComputeLedgerKind.SPEND, -credits,
                                  job_id=job_id, counterparty=node, note=note)
                await post_ledger(db, node, ComputeLedgerKind.EARN, credits,
                                  job_id=job_id, counterparty=owner, note=note)
                logger.info(f"CJ-{job.job_number:03d} done: {total} tok -> {credits} cr")
            await db.commit()
    except Exception as e:  # noqa: BLE001
        logger.exception("job execution failed")
        await _patch(job_id, status=ComputeJobStatus.FAILED, reject_reason=str(e)[:200])

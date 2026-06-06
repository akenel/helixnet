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
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

import os

from fastapi import Header

from src.db.database import get_db_session, AsyncSessionLocal
from src.db.models.compute_model import (
    ComputeJobModel, ComputeJobStatus, ComputeTemplateModel,
    ComputeNodeModel, ComputeNodeStatus, ComputeLedgerKind,
)
from src.schemas.compute_schema import (
    ComputeJobCreate, ComputeJobRead, CreditBalance, BrainLoad, ComputeSummary,
    ComputeTemplateRead, TransferRequest, GrantRequest, LedgerEntryRead,
    NodeRead, NodeRegister, NodeStatusUpdate, WorkerResult,
)
from src.core.keycloak_auth import require_roles
from src.services.compute_service import (
    credit_balance, ensure_starter_grant, brain_load, euro_per_credit,
    ledger_history, transfer_credits, grant_credits,
    credits_for_tokens, node_owner, post_ledger,
    LPCX_CREDIT_TOKENS,
)
from src.compute.queue import publish_job
from src.compute.recipes import RECIPES

# Remote worker contract -- a shared node token, and which nodes are PULL nodes
# (jobs targeting them are NOT enqueued locally; a remote worker pulls them).
LPCX_NODE_TOKEN = os.getenv("LPCX_NODE_TOKEN", "")
LPCX_PULL_NODES = set(filter(None, os.getenv("LPCX_PULL_NODES", "do-staging-0").split(",")))


async def require_node(x_node_token: str = Header(default="")):
    """Authenticate a remote worker by its node token (revocable, scoped)."""
    if not LPCX_NODE_TOKEN or x_node_token != LPCX_NODE_TOKEN:
        raise HTTPException(status_code=401, detail="bad or missing node token")
    return True


LP_ROLES = ["lapiazza-user", "lapiazza-admin"]   # La Piazza's own door
LP_ADMIN = ["lapiazza-admin"]


def require_compute_access():
    """Compute access -- La Piazza members (camper roles kept for back-compat)."""
    return require_roles(["camper-qa-tester", "camper-manager", "camper-admin", *LP_ROLES])


def require_compute_admin():
    """Granting credits -- managers + admins only."""
    return require_roles(["camper-manager", "camper-admin", *LP_ADMIN])


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


@router.get("/nodes", response_model=list[NodeRead])
async def list_nodes(
    mine: bool = False,
    current_user: dict = Depends(require_compute_access()),
    db: AsyncSession = Depends(get_db_session),
):
    """Workbench nodes, each with live earnings (sum credits_burned of done jobs on
    it) + jobs running now."""
    q = select(ComputeNodeModel).order_by(ComputeNodeModel.reputation.desc())
    if mine:
        q = q.where(ComputeNodeModel.owner == current_user["username"])
    nodes = (await db.execute(q)).scalars().all()

    # per-node earned + running, in two grouped queries
    earned_rows = await db.execute(
        select(ComputeJobModel.node, func.coalesce(func.sum(ComputeJobModel.credits_burned), 0))
        .where(ComputeJobModel.status == ComputeJobStatus.DONE)
        .group_by(ComputeJobModel.node)
    )
    earned = {n: int(c) for n, c in earned_rows}
    run_rows = await db.execute(
        select(ComputeJobModel.node, func.count())
        .where(ComputeJobModel.status == ComputeJobStatus.RUNNING)
        .group_by(ComputeJobModel.node)
    )
    running = {n: int(c) for n, c in run_rows}

    out = []
    for n in nodes:
        r = NodeRead.model_validate(n)
        r.earned = earned.get(n.slug, 0)
        r.running = running.get(n.slug, 0)
        out.append(r)
    return out


@router.post("/nodes", response_model=NodeRead, status_code=status.HTTP_201_CREATED)
async def register_node(
    payload: NodeRegister,
    current_user: dict = Depends(require_compute_access()),
    db: AsyncSession = Depends(get_db_session),
):
    """Lend your machine to the square. You become the owner -> you earn."""
    exists = (await db.execute(
        select(ComputeNodeModel).where(ComputeNodeModel.slug == payload.slug)
    )).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail=f"node '{payload.slug}' already registered")
    node = ComputeNodeModel(
        slug=payload.slug, owner=current_user["username"],
        label=payload.label or payload.slug, gpu=payload.gpu,
        status=ComputeNodeStatus.ONLINE,
    )
    db.add(node)
    await db.commit()
    await db.refresh(node)
    return NodeRead.model_validate(node)


@router.post("/nodes/{slug}/status", response_model=NodeRead)
async def set_node_status(
    slug: str,
    payload: NodeStatusUpdate,
    current_user: dict = Depends(require_compute_access()),
    db: AsyncSession = Depends(get_db_session),
):
    """Owner toggles their node online / draining / offline."""
    node = (await db.execute(
        select(ComputeNodeModel).where(ComputeNodeModel.slug == slug)
    )).scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="node not found")
    if node.owner != current_user["username"]:
        raise HTTPException(status_code=403, detail="not your node")
    node.status = ComputeNodeStatus(payload.status)
    await db.commit()
    await db.refresh(node)
    return NodeRead.model_validate(node)


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

    # Node must be a registered, online workbench.
    node_row = (await db.execute(
        select(ComputeNodeModel).where(ComputeNodeModel.slug == payload.node)
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
        inputs=json.dumps(payload.inputs or {}),
    )
    if tmpl is None:
        job.status = ComputeJobStatus.REJECTED
        job.reject_reason = f"unknown template '{payload.template}' -- pick one from the catalog"
    elif node_row is None:
        job.status = ComputeJobStatus.REJECTED
        job.reject_reason = f"unknown node '{payload.node}'"
    elif node_row.status != ComputeNodeStatus.ONLINE:
        job.status = ComputeJobStatus.REJECTED
        job.reject_reason = f"node '{payload.node}' is {node_row.status.value} -- pick an online node"
    # Shared brain needs credits (economic governor); BYO is on your own dime.
    elif not byo and balance <= 0:
        job.status = ComputeJobStatus.REJECTED
        job.reject_reason = "no credits -- earn more (the system teaches efficient SOP use)"
    db.add(job)
    await db.commit()
    await db.refresh(job)

    if job.status != ComputeJobStatus.REJECTED:
        if job.node in LPCX_PULL_NODES:
            # Remote worker pulls this via /worker/next -- do NOT enqueue locally.
            pass
        else:
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


# ================================================================
# Remote worker contract (pull-based) -- the genie on a leash.
# Worker dials OUT, pulls a fully-resolved job, runs it, posts the result.
# No inbound ports on the broker; DB/queue never exposed; worker stays dumb.
# ================================================================
@router.get("/worker/next")
async def worker_next(node: str, _=Depends(require_node),
                      db: AsyncSession = Depends(get_db_session)):
    """Hand the calling worker its next queued job for `node`, fully resolved
    (system + prompt already filled from the recipe + inputs). Allowlist is HERE,
    broker-side: a job whose template isn't a known recipe is failed, not run."""
    job = (await db.execute(
        select(ComputeJobModel).where(
            ComputeJobModel.node == node,
            ComputeJobModel.status == ComputeJobStatus.QUEUED,
        ).order_by(ComputeJobModel.job_number.asc()).limit(1)
    )).scalar_one_or_none()
    if not job:
        return {"job": None}

    recipe = RECIPES.get(job.template)
    if not recipe:
        job.status = ComputeJobStatus.FAILED
        job.reject_reason = f"no recipe for template '{job.template}' (not on the allowlist)"
        await db.commit()
        return {"job": None}

    try:
        ctx = json.loads(job.inputs or "{}")
    except Exception:  # noqa: BLE001
        ctx = {}
    safe: dict = {}
    for inp in recipe["inputs"]:
        v = ctx.get(inp["name"])
        safe[inp["name"]] = v if v not in (None, "") else inp.get("default", "")
    try:
        prompt = recipe["prompt"].format(**safe)
    except Exception as e:  # noqa: BLE001
        job.status = ComputeJobStatus.FAILED
        job.reject_reason = f"bad inputs: {e}"
        await db.commit()
        return {"job": None}

    job.status = ComputeJobStatus.RUNNING
    job.progress = 10
    await db.commit()
    return {"job": {
        "job_id": str(job.id),
        "job_number": job.job_number,
        "template": job.template,
        "system": recipe["system"],
        "prompt": prompt,
        "json_mode": recipe["output"] == "json",
    }}


@router.post("/worker/result")
async def worker_result(body: WorkerResult, _=Depends(require_node),
                        db: AsyncSession = Depends(get_db_session)):
    """Worker returns the result. Broker stores it (untrusted), settles the ledger
    at the fair price, marks done. Idempotent -- a re-post of a settled job is a no-op."""
    job = await db.get(ComputeJobModel, body.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="unknown job")
    if job.status in (ComputeJobStatus.DONE, ComputeJobStatus.KILLED):
        return {"ok": True, "note": "already settled"}

    if body.error:
        job.status = ComputeJobStatus.FAILED
        job.reject_reason = body.error[:200]
        await db.commit()
        return {"ok": True, "failed": True}

    job.output = (body.output or "")[:200000]   # store untrusted output (cap size)
    _recipe = RECIPES.get(job.template)          # type is authoritative from the recipe,
    job.output_type = _recipe["output"] if _recipe else body.output_type   # not the worker
    job.tokens = body.tokens
    job.status = ComputeJobStatus.DONE
    job.progress = 100

    # Fair price = max(recipe value, tokens) -- same rule as the local runner.
    token_cr = credits_for_tokens(body.tokens) if body.tokens else 0
    est = (await db.execute(
        select(ComputeTemplateModel.est_credits).where(ComputeTemplateModel.slug == job.template)
    )).scalar_one_or_none() or 0
    credits = max(est, token_cr)
    job.credits_burned = credits
    provider = await node_owner(db, job.node)   # the machine owner earns
    note = (f"CJ-{job.job_number:03d} · {job.template} · {body.tokens} tok "
            f"→ {credits} cr (remote {job.node})")
    await post_ledger(db, job.owner, ComputeLedgerKind.SPEND, -credits,
                      job_id=job.id, counterparty=provider, note=note)
    await post_ledger(db, provider, ComputeLedgerKind.EARN, credits,
                      job_id=job.id, counterparty=job.owner, note=note)
    await db.commit()
    return {"ok": True, "credits": credits}


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
                jobs = [{**ComputeJobRead.model_validate(j).model_dump(mode="json"),
                         "output": None}  # keep SSE lean; UI fetches output via GET /jobs/{id}
                        for j in rows.scalars().all()]
                # FIFO position among all QUEUED jobs (1-based). Approximate ETA --
                # fairness can let a less-busy user jump ahead; it's your place in line.
                qrows = (await db.execute(
                    select(ComputeJobModel.id)
                    .where(ComputeJobModel.status == ComputeJobStatus.QUEUED)
                    .order_by(ComputeJobModel.created_at.asc())
                )).all()
                pos = {str(r[0]): i + 1 for i, r in enumerate(qrows)}
                for d in jobs:
                    if d["status"] == "queued":
                        d["queue_position"] = pos.get(d["id"], 0)
                brain = await brain_load(db)
            payload = {"brain": brain, "jobs": jobs, "queue_total": len(pos)}
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


@html_router.get("/compute/bottega", response_class=HTMLResponse)
async def compute_bottega(request: Request):
    return templates.TemplateResponse("compute/bottega.html", {"request": request})


@html_router.get("/compute/me", response_class=HTMLResponse)
async def compute_me(request: Request):
    """The member's rebuild dashboard -- mind/body/spirit in one tabbed hub."""
    return templates.TemplateResponse("compute/me.html", {"request": request})


@html_router.get("/u/{slug}", response_class=HTMLResponse)
async def public_profile(slug: str, request: Request,
                         db: AsyncSession = Depends(get_db_session)):
    """Public, shareable Bottega profile page (no login). The thing you send a recruiter."""
    from src.db.models.bottega_model import BottegaProfileModel
    row = (await db.execute(
        select(BottegaProfileModel).where(
            or_(BottegaProfileModel.slug == slug, BottegaProfileModel.username == slug))
    )).scalar_one_or_none()
    profile = None
    if row and row.status == "applied":
        profile = {
            "username": row.username,
            "slug": row.slug or row.username,
            "bio": row.bio,
            "tagline": row.tagline,
            "skills": json.loads(row.skills or "[]"),
            "categories": json.loads(row.categories or "[]"),
            "completeness": row.completeness,
        }
    return templates.TemplateResponse(
        "compute/profile.html", {"request": request, "slug": slug, "profile": profile})


@html_router.get("/compute/callback")
async def compute_oauth_callback(request: Request, code: str = None,
                                 state: str = None, error: str = None):
    """La Bottega's own login-return: exchange the code, then send the user BACK to
    the page they started on (state) -- not the backlog board."""
    import httpx
    nxt = state if (state and state.startswith("/compute")) else "/compute/bottega"
    if error or not code:
        return RedirectResponse(url=f"{nxt}?login_error=1")
    realm, client_id = "lapiazza-realm-dev", "lapiazza_web"
    fp = request.headers.get("x-forwarded-proto", "https")
    fh = request.headers.get("x-forwarded-host") or request.headers.get("host", "helix.local")
    redirect_uri = f"{fp}://{fh}/compute/callback"
    token_endpoint = f"http://keycloak:8080/realms/{realm}/protocol/openid-connect/token"
    try:
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            r = await client.post(token_endpoint, data={
                "grant_type": "authorization_code", "client_id": client_id,
                "code": code, "redirect_uri": redirect_uri,
            })
            if r.status_code != 200:
                logger.error(f"compute callback token exchange failed: {r.status_code} {r.text[:200]}")
                return RedirectResponse(url=f"{nxt}?login_error=token")
            at = r.json().get("access_token")
    except Exception as e:  # noqa: BLE001
        logger.error(f"compute callback error: {e}")
        return RedirectResponse(url=f"{nxt}?login_error=exch")
    return RedirectResponse(url=f"{nxt}#token={at}")

# File: src/services/compute_service.py
# Purpose: LPCX credit economy + shared-brain rationing.
#
# CREDIT DEFINITION (verifiable, valuable, easy to calculate):
#   1 credit = LPCX_CREDIT_TOKENS tokens of shared-brain work (default 1,000).
#   credits = ceil(tokens / LPCX_CREDIT_TOKENS).
#   The model itself reports tokens consumed, so every ledger row is independently
#   recomputable -> verifiable. Pegged to the scarce resource (brain capacity) so it
#   holds value and never inflates. One division, so it's easy to calculate.
#
# SHARED BRAIN (beta): one flat-rate sponsored brain. The scarce thing is CONCURRENCY
#   against the sponsor's quota. We model the ceiling with LPCX_BRAIN_CAP distinct
#   concurrent users. At the cap, new users are REJECTED -- that's "how it blows".

import math
import os

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.compute_model import ComputeLedgerModel, ComputeLedgerKind


# ================================================================
# Tunable economy constants (env-overridable; one-line peg changes)
# ================================================================
LPCX_CREDIT_TOKENS = int(os.getenv("LPCX_CREDIT_TOKENS", "1000"))        # 1 credit = N tokens
LPCX_BRAIN_CAP = int(os.getenv("LPCX_BRAIN_CAP", "50"))                  # concurrent-user ceiling
LPCX_STARTER_GRANT = int(os.getenv("LPCX_STARTER_GRANT", "300"))         # free credits per new user
LPCX_SPONSOR_COST_EUR = float(os.getenv("LPCX_SPONSOR_COST_EUR", "30"))  # flat monthly brain cost
LPCX_MONTHLY_TOKEN_BUDGET = int(os.getenv("LPCX_MONTHLY_TOKEN_BUDGET", "60000000"))  # tokens/mo the plan serves


def credits_for_tokens(tokens: int) -> int:
    """The whole credit formula. Auditable by anyone."""
    return max(0, math.ceil(max(0, tokens) / LPCX_CREDIT_TOKENS))


def euro_per_credit() -> float:
    """Shadow euro value of a credit (reporting only; beta credits aren't redeemed)."""
    credits_per_month = LPCX_MONTHLY_TOKEN_BUDGET / LPCX_CREDIT_TOKENS
    return LPCX_SPONSOR_COST_EUR / credits_per_month if credits_per_month else 0.0


# ================================================================
# Shared-brain guard (in-process). NOTE: single-process only -- with multiple
# uvicorn workers this state is per-worker. Real multi-worker impl -> Redis.
# For local beta + the stress test, in-process is exactly what we want to watch.
# ================================================================
# In v2 the brain ceiling is enforced by the aio-pika consumer's prefetch_count
# (= LPCX_BRAIN_CAP concurrent slots) and the durable RabbitMQ queue is the FIFO
# wait line. So the gauge is DERIVED FROM THE DB (durable, cross-process, accurate),
# not an in-process counter:
#   active  = jobs RUNNING (in a consumer slot)
#   waiting = jobs QUEUED  (in the RabbitMQ line, not yet picked up)
async def brain_load(db: AsyncSession) -> dict:
    from src.db.models.compute_model import ComputeJobModel, ComputeJobStatus  # local import: avoid cycle
    rows = await db.execute(
        select(ComputeJobModel.status, func.count().label("c")).group_by(ComputeJobModel.status)
    )
    counts = {row.status.value: row.c for row in rows}
    active = counts.get("running", 0)
    waiting = counts.get("queued", 0)
    done = counts.get("done", 0)
    toks = (await db.execute(
        select(func.coalesce(func.sum(ComputeJobModel.tokens), 0))
    )).scalar() or 0
    # per-user running breakdown -- shows the fair split live
    urows = await db.execute(
        select(ComputeJobModel.owner, func.count().label("c"))
        .where(ComputeJobModel.status == ComputeJobStatus.RUNNING)
        .group_by(ComputeJobModel.owner)
        .order_by(func.count().desc())
    )
    by_user = {row.owner: row.c for row in urows}
    cap = LPCX_BRAIN_CAP
    active_users = max(1, len(by_user))
    return {
        "active": active,
        "waiting": waiting,
        "cap": cap,
        "load_pct": round(min(100, active / cap * 100)) if cap else 0,
        "tokens_total": int(toks),
        "jobs_served": done,
        "euro_per_credit": round(euro_per_credit(), 6),
        "credit_tokens": LPCX_CREDIT_TOKENS,
        "by_user": by_user,
        "cap_per_user": max(1, cap // active_users),
    }


# ================================================================
# Ledger (append-only, the single source of money truth)
# ================================================================
async def credit_balance(db: AsyncSession, account: str) -> int:
    result = await db.execute(
        select(func.coalesce(func.sum(ComputeLedgerModel.amount), 0))
        .where(ComputeLedgerModel.account == account)
    )
    return int(result.scalar() or 0)


async def post_ledger(
    db: AsyncSession,
    account: str,
    kind: ComputeLedgerKind,
    amount: int,
    job_id=None,
    counterparty: str | None = None,
    note: str | None = None,
) -> ComputeLedgerModel:
    entry = ComputeLedgerModel(
        account=account, kind=kind, amount=amount,
        job_id=job_id, counterparty=counterparty, note=note,
    )
    db.add(entry)
    await db.flush()
    return entry


async def ensure_starter_grant(db: AsyncSession, account: str) -> int:
    """Give a new account its free starter credits exactly once. Returns balance."""
    count = await db.execute(
        select(func.count()).select_from(ComputeLedgerModel)
        .where(ComputeLedgerModel.account == account)
    )
    if (count.scalar() or 0) == 0:
        await post_ledger(
            db, account, ComputeLedgerKind.GRANT, LPCX_STARTER_GRANT,
            note=f"starter grant ({LPCX_STARTER_GRANT} cr = {LPCX_STARTER_GRANT * LPCX_CREDIT_TOKENS} free tokens)",
        )
        await db.commit()
    return await credit_balance(db, account)


async def ledger_history(db: AsyncSession, account: str, limit: int = 25) -> list:
    """The account's credit trail (newest first) -- in and out."""
    rows = await db.execute(
        select(ComputeLedgerModel)
        .where(ComputeLedgerModel.account == account)
        .order_by(ComputeLedgerModel.created_at.desc())
        .limit(limit)
    )
    return list(rows.scalars().all())


async def node_owner(db: AsyncSession, slug: str) -> str:
    """Who earns when a job runs on this node. Falls back to the slug itself if the
    node isn't registered (backward-compat)."""
    from src.db.models.compute_model import ComputeNodeModel  # local: avoid cycle
    row = (await db.execute(
        select(ComputeNodeModel.owner).where(ComputeNodeModel.slug == slug)
    )).scalar_one_or_none()
    return row or slug


async def account_exists(db: AsyncSession, account: str) -> bool:
    n = (await db.execute(
        select(func.count()).select_from(ComputeLedgerModel)
        .where(ComputeLedgerModel.account == account)
    )).scalar() or 0
    return n > 0


async def transfer_credits(db: AsyncSession, sender: str, recipient: str,
                           amount: int, note: str | None = None) -> None:
    """Peer transfer: sender -> recipient. Atomic (both rows in one commit).
    NOTE: balance check is read-then-write -- a tiny overdraft race exists under
    concurrent transfers; acceptable for beta (prod: row-lock a balance row)."""
    if amount <= 0:
        raise ValueError("amount must be positive")
    if sender == recipient:
        raise ValueError("can't transfer to yourself")
    if not await account_exists(db, recipient):
        raise ValueError(f"unknown recipient '{recipient}'")
    if await credit_balance(db, sender) < amount:
        raise ValueError("insufficient credits")
    tag = (note or "transfer").strip()[:160]
    await post_ledger(db, sender, ComputeLedgerKind.SPEND, -amount,
                      counterparty=recipient, note=f"→ @{recipient}: {tag}")
    await post_ledger(db, recipient, ComputeLedgerKind.EARN, amount,
                      counterparty=sender, note=f"← @{sender}: {tag}")
    await db.commit()


async def grant_credits(db: AsyncSession, account: str, amount: int,
                        by: str, note: str | None = None) -> None:
    """Admin/system grant -- rewards a contribution or tops up."""
    if amount <= 0:
        raise ValueError("amount must be positive")
    tag = (note or "grant").strip()[:160]
    await post_ledger(db, account, ComputeLedgerKind.GRANT, amount,
                      counterparty=by, note=f"grant by @{by}: {tag}")
    await db.commit()


def verifiable_note(job_number: int, tokens: int, credits: int) -> str:
    """Self-documenting ledger note so the row recomputes: tokens / rate = credits."""
    return f"CJ-{job_number:03d} · {tokens} tok ÷ {LPCX_CREDIT_TOKENS} = {credits} cr"

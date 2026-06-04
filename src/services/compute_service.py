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

import asyncio
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
class BrainGuard:
    """Models the shared sponsored brain. The ceiling is CONCURRENT INFERENCE SLOTS
    (LPCX_BRAIN_CAP): the flat-rate brain can only serve so many at once before the
    sponsor's quota throttles. At the ceiling, admission is REFUSED -- the wall."""

    def __init__(self, cap: int):
        self.cap = cap
        self._active_slots = 0              # in-flight inference slots
        self._users: dict[str, int] = {}    # account -> in-flight jobs (for display)
        self._tokens_total = 0
        self._jobs_served = 0
        self._rejections = 0
        self._peak_slots = 0
        self._lock = asyncio.Lock()

    async def admit(self, account: str) -> tuple[bool, str]:
        async with self._lock:
            if self._active_slots >= self.cap:
                self._rejections += 1
                return False, f"shared brain at ceiling ({self.cap} concurrent slots)"
            self._active_slots += 1
            self._users[account] = self._users.get(account, 0) + 1
            self._peak_slots = max(self._peak_slots, self._active_slots)
            return True, "ok"

    async def release(self, account: str) -> None:
        async with self._lock:
            self._active_slots = max(0, self._active_slots - 1)
            if account in self._users:
                self._users[account] -= 1
                if self._users[account] <= 0:
                    del self._users[account]

    async def record_use(self, tokens: int) -> None:
        async with self._lock:
            self._tokens_total += tokens
            self._jobs_served += 1

    def load(self) -> dict:
        return {
            "active": self._active_slots,
            "users": len(self._users),
            "cap": self.cap,
            "load_pct": round(min(100, self._active_slots / self.cap * 100)) if self.cap else 0,
            "peak": self._peak_slots,
            "tokens_total": self._tokens_total,
            "jobs_served": self._jobs_served,
            "rejections": self._rejections,
            "euro_per_credit": round(euro_per_credit(), 6),
            "credit_tokens": LPCX_CREDIT_TOKENS,
        }


brain_guard = BrainGuard(LPCX_BRAIN_CAP)


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


def verifiable_note(job_number: int, tokens: int, credits: int) -> str:
    """Self-documenting ledger note so the row recomputes: tokens / rate = credits."""
    return f"CJ-{job_number:03d} · {tokens} tok ÷ {LPCX_CREDIT_TOKENS} = {credits} cr"

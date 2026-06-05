# File: src/schemas/compute_schema.py
# Purpose: LPCX request/response shapes.

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ComputeJobCreate(BaseModel):
    template: str = Field(default="print-card", max_length=80)
    node: str = Field(default="lp-hetzner-0", max_length=100)
    brain_mode: Literal["shared", "byo"] = "shared"
    byo_endpoint: str | None = Field(default=None, max_length=300)
    byo_model: str | None = Field(default=None, max_length=80)


class ComputeJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_number: int
    template: str
    status: str
    progress: int
    tokens: int
    credits_burned: int
    owner: str
    node: str
    brain_mode: str
    brain_model: str
    reject_reason: str | None = None
    created_at: datetime
    updated_at: datetime


class ComputeTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    title: str
    description: str | None = None
    category: str
    emoji: str
    est_credits: int
    enabled: bool


class CreditBalance(BaseModel):
    account: str
    balance: int
    credit_tokens: int          # 1 credit = this many tokens
    euro_per_credit: float      # shadow price (reporting only)


class TransferRequest(BaseModel):
    to_account: str = Field(..., min_length=1, max_length=100)
    amount: int = Field(..., gt=0)
    note: str | None = Field(None, max_length=200)


class GrantRequest(BaseModel):
    account: str = Field(..., min_length=1, max_length=100)
    amount: int = Field(..., gt=0)
    note: str | None = Field(None, max_length=200)


class NodeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    owner: str
    label: str
    gpu: str
    status: str
    reputation: float
    earned: int = 0      # credits earned via jobs on this node (computed)
    running: int = 0     # jobs running on it now (computed)


class NodeRegister(BaseModel):
    slug: str = Field(..., min_length=2, max_length=64, pattern=r"^[a-z0-9][a-z0-9-]*$")
    label: str = Field("", max_length=120)
    gpu: str = Field("CPU", max_length=80)


class NodeStatusUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(online|draining|offline)$")


class LedgerEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    kind: str
    amount: int
    counterparty: str | None = None
    note: str | None = None
    created_at: datetime


class BrainLoad(BaseModel):
    active: int                 # jobs running in a consumer slot
    waiting: int                # jobs queued in RabbitMQ, waiting their turn (FIFO)
    cap: int                    # the ceiling (consumer prefetch = slots)
    load_pct: int
    tokens_total: int
    jobs_served: int            # jobs done
    euro_per_credit: float
    credit_tokens: int
    by_user: dict[str, int] = {}    # owner -> running slots (the live fair split)
    cap_per_user: int = 0           # current dynamic per-user cap (total // active users)


class ComputeSummary(BaseModel):
    total_jobs: int
    by_status: dict[str, int]
    brain: BrainLoad

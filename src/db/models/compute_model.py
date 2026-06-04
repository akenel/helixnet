# File: src/db/models/compute_model.py
# Purpose: La Piazza Compute Exchange (LPCX) -- jobs run on rented Workbenches,
#          credits ration the shared sponsored Brain. We host the square, not the model.

from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, BigInteger, Text, ForeignKey, Identity
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


# ================================================================
# Enums (HelixEnum = case-insensitive, lowercase values)
# ================================================================
from src.core.constants import HelixEnum


class ComputeJobStatus(HelixEnum):
    """Lifecycle of a compute job."""
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    KILLED = "killed"
    FAILED = "failed"
    REJECTED = "rejected"   # admission refused -- shared brain at the ceiling


class ComputeLedgerKind(HelixEnum):
    """Why a credit moved. The ledger is the single source of money truth."""
    GRANT = "grant"       # starter credits / sponsorship
    SPEND = "spend"       # requester paid for a job
    EARN = "earn"         # provider earned for lending the workbench
    ADJUST = "adjust"     # manual correction


# ================================================================
# Compute Job
# ================================================================
class ComputeJobModel(Base):
    __tablename__ = "compute_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4,
    )
    job_number: Mapped[int] = mapped_column(
        BigInteger,
        Identity(start=1),
        nullable=False,
        unique=True,
        index=True,
        comment="DB-assigned display number (CJ-001) -- atomic, race-free. The real "
                "identity is id (UUID); this is cosmetic only.",
    )
    template: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        default="pdf-render",
        comment="Workbench template: pdf-render, sd-xl, blender",
    )
    status: Mapped[ComputeJobStatus] = mapped_column(
        SQLEnum(ComputeJobStatus, name="compute_job_status", create_constraint=True,
                values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ComputeJobStatus.QUEUED,
        index=True,
        comment="queued, running, done, killed, failed, rejected",
    )
    progress: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="0-100 percent complete",
    )
    tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="Tokens consumed on the shared brain so far",
    )
    credits_burned: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="Credits debited from the requester for this job",
    )
    owner: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="Requester (Keycloak username) who submitted the job",
    )
    node: Mapped[str] = mapped_column(
        String(100), nullable=False, default="lp-hetzner-0",
        comment="Provider workbench the job ran on",
    )
    brain_mode: Mapped[str] = mapped_column(
        String(16), nullable=False, default="shared", index=True,
        comment="'shared' = sponsored brain (counts against ceiling + credits); "
                "'byo' = bring-your-own brain (off the shared quota, free of shared credits)",
    )
    brain_model: Mapped[str] = mapped_column(
        String(80), nullable=False, default="ollama/turbo",
        comment="Which model served the inference (shared model or BYO model name)",
    )
    reject_reason: Mapped[str | None] = mapped_column(
        String(200), nullable=True,
        comment="If rejected: why (e.g. brain at ceiling, no credits)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ================================================================
# Credit Ledger (append-only) -- who owes who, what settled
# ================================================================
class ComputeLedgerModel(Base):
    """Append-only credit ledger. Credits ration the shared brain; during beta
    they are fairness tokens, not euros (flat-rate sponsored brain)."""
    __tablename__ = "compute_ledger"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4,
    )
    account: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="Keycloak username this entry belongs to",
    )
    kind: Mapped[ComputeLedgerKind] = mapped_column(
        SQLEnum(ComputeLedgerKind, name="compute_ledger_kind", create_constraint=True,
                values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    amount: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="Credits delta (+earn/grant, -spend)",
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compute_jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="The job this entry settled (null for grants)",
    )
    counterparty: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        comment="The other side of the trade (provider/requester)",
    )
    note: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Human note: 'rendered postcard on lp-hetzner-0'",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

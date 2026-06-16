# File: src/db/models/compute_model.py
# Purpose: La Piazza Compute Exchange (LPCX) -- jobs run on rented Workbenches,
#          credits ration the shared sponsored Brain. We host the square, not the model.

from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, BigInteger, Boolean, Float, Text, ForeignKey, Identity
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


class ComputeNodeStatus(HelixEnum):
    """A workbench's availability."""
    ONLINE = "online"       # accepting jobs
    DRAINING = "draining"   # finish current, take no new
    OFFLINE = "offline"     # not accepting


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
        comment="If rejected/killed: why (e.g. no credits, killed by requester)",
    )
    inputs: Mapped[str] = mapped_column(
        Text, nullable=False, default="{}",
        comment="JSON recipe inputs (so a remote worker can be handed a resolved job)",
    )
    output: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="The job result (untrusted -- sanitize on display)",
    )
    output_type: Mapped[str | None] = mapped_column(
        String(16), nullable=True,
        comment="json | markdown | text",
    )
    kill_requested: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="Cross-process kill flag -- the consumer polls this between steps",
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
# Template Catalog -- the approved SOP allowlist (safety by construction).
# Users run TEMPLATES, not free-form prompts. submit rejects anything not here.
# ================================================================
class ComputeTemplateModel(Base):
    __tablename__ = "compute_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4,
    )
    slug: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True,
        comment="Allowlist key used by submit (e.g. 'print-card')",
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(
        String(40), nullable=False, default="general",
        comment="print, media, modeling, text",
    )
    emoji: Mapped[str] = mapped_column(String(8), nullable=False, default="\U0001F9F0")
    est_credits: Mapped[int] = mapped_column(
        Integer, nullable=False, default=2,
        comment="Estimated credits (actual is metered by tokens used)",
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True,
        comment="Disabled templates can't be submitted (admin off-switch)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc), nullable=False,
    )


# ================================================================
# Workbench Node -- a machine someone lends to the square. The owner EARNS
# credits when jobs run on their node. (Lend your idle GPU, get paid.)
# ================================================================
class ComputeNodeModel(Base):
    __tablename__ = "compute_nodes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4,
    )
    slug: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True,
        comment="Node id used by jobs (e.g. 'frank-rtx4090')",
    )
    owner: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="Keycloak username of the machine owner -- earns the credits",
    )
    label: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    gpu: Mapped[str] = mapped_column(
        String(80), nullable=False, default="CPU",
        comment="Hardware blurb (e.g. 'RTX 4090')",
    )
    status: Mapped[ComputeNodeStatus] = mapped_column(
        SQLEnum(ComputeNodeStatus, name="compute_node_status", create_constraint=True,
                values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=ComputeNodeStatus.ONLINE, index=True,
    )
    reputation: Mapped[float] = mapped_column(
        Float, nullable=False, default=5.0,
        comment="Stars (review system is a later block; display-only for now)",
    )
    caps_json: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="JSON of probed capabilities: tools present, ram_mb, gpu. "
                "Drives the no-surprises 'what can this box run' window + dispatch preflight.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc), nullable=False,
    )

    @property
    def capabilities(self) -> dict:
        """Parsed capabilities (empty dict for legacy nodes that never reported)."""
        import json
        try:
            return json.loads(self.caps_json) if self.caps_json else {}
        except (ValueError, TypeError):
            return {}


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

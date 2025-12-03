# File: src/db/models/shift_session_model.py
"""
Shift & Session Management - The Handoff WIZARD

BLQ Scene: Pam forgot logout, Ralph needs POS, Felix on the road

"Who owns the drawer right now?" - This model answers that.

Tracks:
- Active POS sessions (who's logged in where)
- Shift handoffs (Pam → Ralph)
- Remote session kills (Felix forces logout)
- Cash accountability (drawer ownership)
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class SessionStatus(str, Enum):
    """POS session states"""
    ACTIVE = "active"          # Currently logged in
    ENDED = "ended"            # Normal logout
    FORCE_ENDED = "force_ended"  # Manager killed it
    EXPIRED = "expired"        # Auto-timeout
    HANDED_OFF = "handed_off"  # Shift change


class ShiftSessionModel(Base):
    """
    Track who's on the POS and when.

    Every login creates a session.
    Every logout (or force-logout) ends it.
    Cash drawer ownership follows the session.
    """
    __tablename__ = 'shift_sessions'

    # ================================================================
    # PRIMARY KEY
    # ================================================================
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # ================================================================
    # WHO & WHERE
    # ================================================================
    user_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Keycloak user ID or username (pam, ralph, felix)"
    )
    username: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Display name for UI"
    )
    store_number: Mapped[int] = mapped_column(
        nullable=False,
        default=1,
        comment="Which store/register"
    )
    register_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Specific register if multiple (REG-01, REG-02)"
    )

    # ================================================================
    # SESSION TIMING
    # ================================================================
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="When they logged in"
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When session ended"
    )
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Last API call / heartbeat"
    )

    # ================================================================
    # STATUS
    # ================================================================
    status: Mapped[SessionStatus] = mapped_column(
        SQLEnum(SessionStatus),
        default=SessionStatus.ACTIVE,
        nullable=False,
        comment="Current session state"
    )

    # ================================================================
    # HANDOFF / FORCE END
    # ================================================================
    ended_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Who ended it (self, manager, system)"
    )
    end_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Why it ended (logout, force, timeout, handoff)"
    )
    handed_off_to: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Next user in handoff chain"
    )

    # ================================================================
    # DRAWER ACCOUNTABILITY
    # ================================================================
    drawer_opened: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Did they open cash drawer this session?"
    )
    transaction_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        comment="Transactions during this session"
    )

    # ================================================================
    # METADATA
    # ================================================================
    ip_address: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Client IP for audit"
    )
    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Browser/device info"
    )

    def end_session(self, ended_by: str, reason: str, status: SessionStatus = SessionStatus.ENDED):
        """End this session"""
        self.status = status
        self.ended_at = datetime.now(timezone.utc)
        self.ended_by = ended_by
        self.end_reason = reason

    def force_end(self, manager_id: str, reason: str):
        """Manager force-ends this session"""
        self.end_session(
            ended_by=manager_id,
            reason=f"FORCE: {reason}",
            status=SessionStatus.FORCE_ENDED
        )

    def handoff_to(self, next_user: str, manager_id: str):
        """Handoff to next shift"""
        self.handed_off_to = next_user
        self.end_session(
            ended_by=manager_id,
            reason=f"Handoff to {next_user}",
            status=SessionStatus.HANDED_OFF
        )

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now(timezone.utc)

    def __repr__(self):
        return f"<ShiftSession(user='{self.username}', store={self.store_number}, status={self.status.value})>"

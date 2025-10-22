# File: app/db/models/team_model.py
# Updated: October 21, 2025
from sqlalchemy.dialects.postgresql import UUID
import uuid

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Boolean
from sqlalchemy.orm import Mapped
from .base import Base

class TeamModel(Base):
    """
    Represents a team or organizational unit within the application.
    Teams are used for grouping users and managing access to resources.
    """
    __tablename__ = 'teams'

    # Primary Key
    id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), primary_key=True, index=True)

    # Core Team Fields
    name: Mapped[str] = Column(String(100), unique=True, index=True, nullable=False, comment="The human-readable name of the team")
    description: Mapped[str | None] = Column(Text, nullable=True)
    is_active: Mapped[bool] = Column(Boolean, default=True, nullable=False)
    is_private: Mapped[bool] = Column(Boolean, default=False, nullable=False, comment="If true, membership must be explicitly granted")

    # Timestamps
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Note: The relationship to users (many-to-many) is often handled
    # by a separate association table model, which is omitted here.

    def __repr__(self):
        return f"<TeamModel(id='{self.id}', name='{self.name}')>"

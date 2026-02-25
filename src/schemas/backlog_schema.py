# File: src/schemas/backlog_schema.py
# Purpose: Pydantic schemas for Unified Backlog

from datetime import datetime, date
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from src.db.models.backlog_model import (
    BacklogItemType, BacklogStatus, BacklogPriority,
)
from src.core.constants import HelixApplication


# ================================================================
# Backlog Item Schemas
# ================================================================
class BacklogItemCreate(BaseModel):
    """Create a new backlog item."""
    title: str = Field(..., min_length=3, max_length=200, description="Item title")
    description: Optional[str] = Field(None, description="Detailed description")
    item_type: BacklogItemType = Field(default=BacklogItemType.DEV_TASK, description="Type of work")
    application: HelixApplication = Field(default=HelixApplication.HELIXNET, description="Which app: helixnet, camper, isotto")
    priority: BacklogPriority = Field(default=BacklogPriority.MEDIUM, description="Priority level")
    assigned_to: Optional[str] = Field(None, max_length=100, description="Assigned to")
    due_date: Optional[date] = Field(None, description="Target completion date")
    estimated_hours: Optional[float] = Field(None, ge=0, description="Estimated hours")
    tags: Optional[str] = Field(None, max_length=500, description="Comma-separated tags")
    created_by: str = Field(default="Angel", min_length=1, max_length=100, description="Who created this")


class BacklogItemUpdate(BaseModel):
    """Update a backlog item."""
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None)
    item_type: Optional[BacklogItemType] = None
    application: Optional[HelixApplication] = None
    status: Optional[BacklogStatus] = None
    priority: Optional[BacklogPriority] = None
    assigned_to: Optional[str] = Field(None, max_length=100, description="Assign to someone (empty string to unassign)")
    due_date: Optional[date] = Field(None, description="Target completion date")
    estimated_hours: Optional[float] = Field(None, ge=0)
    blocked_reason: Optional[str] = Field(None, description="Why blocked (set when status=blocked)")
    tags: Optional[str] = Field(None, max_length=500)
    comment: Optional[str] = Field(None, min_length=1, description="Activity comment (logged in trail)")
    actor: str = Field(default="Angel", min_length=1, max_length=100, description="Who is making this update")


class BacklogItemRead(BaseModel):
    """Full backlog item for display."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    item_number: int
    item_type: BacklogItemType
    application: HelixApplication
    status: BacklogStatus
    priority: BacklogPriority
    title: str
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date: Optional[date] = None
    estimated_hours: Optional[float] = None
    blocked_reason: Optional[str] = None
    tags: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime


# ================================================================
# Activity Schemas
# ================================================================
class BacklogActivityRead(BaseModel):
    """Activity log entry for display."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    item_id: UUID
    activity_type: str
    actor: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    comment: Optional[str] = None
    created_at: datetime


# ================================================================
# Summary Schema
# ================================================================
class BacklogSummary(BaseModel):
    """Backlog overview counts."""
    total: int
    pending: int
    in_progress: int
    blocked: int
    done: int
    archived: int
    by_type: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    by_application: dict[str, int] = {}

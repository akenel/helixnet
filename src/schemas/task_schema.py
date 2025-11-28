# app/schemas/task_schema.py
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

# ----------------------------------------------------------------------
# 1. ENUM: Task Status
# ----------------------------------------------------------------------

class TaskStatus(str, Enum):
    """Defines the lifecycle status of an asynchronous job/task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# ----------------------------------------------------------------------
# 2. BASE SCHEMA (Shared properties)
# ----------------------------------------------------------------------

class TaskBase(BaseModel):
    """Base Pydantic schema for task properties."""
    title: str = Field(..., example="Process Q4 Financial Data")
    description: Optional[str] = Field(None, example="Run the data extraction and aggregation script for the fourth quarter.")

# ----------------------------------------------------------------------
# 3. INPUT SCHEMAS
# ----------------------------------------------------------------------

class TaskCreate(TaskBase):
    """Schema for creating a new task."""
    pass

class TaskUpdate(TaskBase):
    """Schema for updating an existing task."""
    status: Optional[TaskStatus] = None
    # Assuming owner_id is set at creation and not typically updated here
    

# ----------------------------------------------------------------------
# 4. OUTPUT SCHEMAS
# ----------------------------------------------------------------------

class TaskRead(TaskBase):
    """Standard read schema for task data."""
    id: str = Field(..., example="task-007")
    status: TaskStatus = TaskStatus.PENDING
    owner_id: str = Field(..., example="user-12345")
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}

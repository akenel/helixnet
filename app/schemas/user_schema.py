from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from enum import Enum

from app.schemas.task_schema import TaskRead
from pydantic import BaseModel, EmailStr, Field

# ----------------------------------------------------------------------
# 1. ENUM: User Roles
# ----------------------------------------------------------------------

class UserRoles(str, Enum):
    """Defines the available roles for users."""
    BASIC = "basic"
    MANAGER = "manager"
    SUPERUSER = "admin"


# ----------------------------------------------------------------------
# 2. BASE SCHEMA (Shared properties)
# ----------------------------------------------------------------------

class UserBase(BaseModel):
    """Base Pydantic schema for user properties shared across models."""
    email: EmailStr = Field(..., example="jane.doe@helix.net")
    fullname: Optional[str] = Field(None, example="Jane Doe")


# ----------------------------------------------------------------------
# 3. INPUT SCHEMAS (For POST/PUT operations)
# ----------------------------------------------------------------------

class UserCreate(UserBase):
    """Schema for creating a new user (registration)."""
    password: str = Field(..., min_length=1)
    # Role defaults to basic
    roles: List[UserRoles] = [UserRoles.BASIC]


class UserUpdate(UserBase):
    """Schema for updating an existing user's profile."""
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    roles: Optional[List[UserRoles]] = None


# ----------------------------------------------------------------------
# 4. OUTPUT SCHEMAS (For GET responses)
# ----------------------------------------------------------------------

class UserRead(UserBase):
    """Standard read schema for user data."""
    # Using 'str' for IDs to be database-agnostic (UUID, Firestore ID, etc.)
    id: str = Field(..., example="user-12345")
    is_active: bool = True
    is_admin: bool = False
    roles: List[UserRoles]
    created_at: datetime
    updated_at: datetime

    class Config:
        # Pydantic V2 way to allow models to be built from ORM/SQLAlchemy objects
        from_attributes = True


# ----------------------------------------------------------------------
# 5. SCHEMAS WITH RELATIONSHIPS
# ----------------------------------------------------------------------

class UserReadWithTasks(UserRead):
    """
    Read schema including a list of associated tasks.
    
    The type hint 'TaskRead' is defined in app/schemas/task_schema.py.
    """
    tasks: List["TaskRead"] = [] 


# ----------------------------------------------------------------------
# 6. AUTHENTICATION SCHEMAS (Assuming this logic is used for JWTs)
# ----------------------------------------------------------------------

class TokenPairOut(BaseModel):
    """Schema for returning access and refresh tokens after successful login."""
    access_token: str
    token_type: str = "bearer"
    refresh_token: str
    refresh_jti: Optional[str] = None
    refresh_expires_at: Optional[str] = None
    
    class Config:
        from_attributes = True

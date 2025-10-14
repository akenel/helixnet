from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from enum import Enum
from uuid import UUID

from app.schemas.task_schema import TaskRead
from pydantic import BaseModel, EmailStr, Field
from pydantic import BaseModel, EmailStr

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

class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    fullname: Optional[str] = None
    is_active: bool
    is_admin: bool
    scopes: List[str] = []
    roles: List[str] = []

    class Config:
        orm_mode = True  # ✅ Allows returning SQLAlchemy objects directly
        json_encoders = {
            UUID: lambda v: str(v)  # ✅ Converts UUID → string for FastAPI response
        }


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

from __future__ import annotations # Required for forward references like List["TaskRead"]
from datetime import datetime
from typing import Any, Dict, Optional, List
from enum import Enum
from uuid import UUID
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.schemas.task_schema import TaskRead
from pydantic import BaseModel, EmailStr, Field

# Ensure TaskRead is available for UserReadWithTasks
# NOTE: TaskRead must be defined in schemas.task_schema or imported successfully.
# from src.schemas.task_schema import TaskRead 

# ----------------------------------------------------------------------
# 1. ENUM: User Roles
# ----------------------------------------------------------------------

class UserRoles(str, Enum):
    """
    Defines the available roles for users.
    Standardized, singular source of truth for all role checks.
    """
    BASIC = "basic"
    MANAGER = "manager"
    SUPERUSER = "admin" # Using 'admin' as the string value for convenience/legacy
    AUDITOR = "auditor"
    TESTER = "tester"
    DEVELOPER = "developer"
    GUEST = "guest"

# ----------------------------------------------------------------------
# 2. BASE SCHEMA (Shared properties for input/output)
# ----------------------------------------------------------------------

class UserBase(BaseModel):
    """Base Pydantic schema for core user properties."""
    email: EmailStr = Field(..., example="jane.doe@helix.net")
    username: str = Field(..., min_length=3, example="janedoe")
    fullname: Optional[str] = Field(None, example="Jane Doe")
    
    # Extended fields
    phone_number: Optional[str] = Field(None, example="+1-555-123-4567", description="User's primary contact number.")
    web_url: Optional[str] = Field(None, example="https://janedoe.com", description="Personal or professional web link.")

# ----------------------------------------------------------------------
# 3. INPUT SCHEMAS (For POST/PUT operations)
# ----------------------------------------------------------------------

# src/schemas/user_schema.py
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    username: str = Field(..., example="chuck.norris")
    email: EmailStr = Field(..., example="chuck@norris.io")
    first_name: str = Field(..., example="Chuck")
    last_name: str = Field(..., example="Norris")
    password: str = Field(..., example="roundhouseKick42!")

    class Config:
        model_config = SettingsConfigDict(from_attributes=True)
        schema_extra = {
            "example": {
                "username": "bruce.lee",
                "email": "bruce@dojo.com",
                "first_name": "Bruce",
                "last_name": "Lee",
                "password": "enterTheDragon",
            }
        }


class UserUpdate(UserBase):
    """Schema for updating an existing user's profile."""
    # Note: inherits all fields from UserBase. All fields are optional here.
    
    # Status fields for administrative updates
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = Field(None, alias="is_admin", description="Maps to the database superuser status.")
    roles: Optional[List[UserRoles]] = None
    
    # Allow password change via a separate, explicit field (optional)
    password: Optional[str] = Field(None, min_length=8, description="Optional new password.")

# ----------------------------------------------------------------------
# 4. OUTPUT SCHEMAS (For GET responses)
# ----------------------------------------------------------------------

class UserRead(UserBase):
    """
    The definitive read-only schema for a User object, containing all persisted data.
    Pydantic V2 compliant and ready for ORM mapping.
    """
    id: UUID = Field(..., description="Unique identifier for the user.")
    
    # Status and permissions
    is_active: bool
    is_superuser: bool = Field(False, description="True if the user has superuser/admin privileges.")
    
    # Redundant but kept for backward compatibility if needed, otherwise roles covers it
    scopes: List[str] = [] 
    
    # Uses the list of string values from the database model
    roles: List[str] = Field([], description="List of user roles as strings (e.g., 'basic', 'admin').")
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        # Pydantic V2 setting for ORM/SQLAlchemy compatibility (replaces 'orm_mode=True')
        from_attributes = True 
        
        # Ensures UUIDs are cleanly serialized as strings in JSON output
        json_encoders = {
            UUID: lambda v: str(v) 
        }
class UserClaimsRead(UserRead):
    """Extends the UserRead model with raw JWT claims for debugging."""
    auth_context: Dict[str, Any] = Field(..., description="Raw decoded JWT claims payload.")

# The authenticated user dependency should be based on the full UserRead structure
class APICaller(UserRead):
    """
    Schema representing the authenticated user retrieved from the token.
    Inherits all properties from UserRead.
    """
    pass

# ----------------------------------------------------------------------
# 5. SCHEMAS WITH RELATIONSHIPS
# ----------------------------------------------------------------------

class UserReadWithTasks(UserRead):
    """
    Read schema including a list of associated tasks (requires TaskRead to be imported).
    """
    # NOTE: You must ensure 'TaskRead' is imported or defined for this to resolve.
    # tasks: List[TaskRead] = [] 
    # Keeping the original form, assuming TaskRead is available via the forward reference:
    tasks: List[TaskRead] = [] 

# ----------------------------------------------------------------------
# 6. AUTHENTICATION SCHEMAS
# ----------------------------------------------------------------------

class TokenPairOut(BaseModel):
    """Schema for returning access and refresh tokens after successful login."""
    access_token: str
    token_type: str = "bearer"
    refresh_token: str
    refresh_jti: Optional[str] = Field(None, description="Unique JWT ID for the refresh token (used for revocation).")
    refresh_expires_at: Optional[str] = Field(None, description="ISO timestamp when the refresh token expires.")
    
    class Config:
        from_attributes = True

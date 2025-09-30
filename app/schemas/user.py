"""
Pydantic Schemas for the User Model.
Defines data structures for request bodies and response models.
"""
from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime

class UserBase(BaseModel):
    """Base schema for user data (used for input)."""
    email: EmailStr
    
class UserCreate(UserBase):
    """Schema for creating a new user (includes password)."""
    password: str

class UserResponse(UserBase):
    """Schema for user data returned by the API (excludes password hash)."""
    id: UUID
    is_active: bool
    created_at: datetime
    
    class Config:
        """Enables ORM mode to read data from SQLAlchemy models."""
        from_attributes = True

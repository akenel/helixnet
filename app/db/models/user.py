"""
User Model for Authentication and Authorization
"""
from datetime import datetime # <- This import is the problem
from typing import List, TYPE_CHECKING
from uuid import uuid4
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.dialects.postgresql import UUID

# Base is imported from app.db.database
from app.db.database import Base 

if TYPE_CHECKING:
    # Deferred import for type hinting to avoid circular imports
    from app.db.models.job_result import JobResult

class User(AsyncAttrs, Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"
    
    # Primary Key (Corrected to use Mapped and default to uuid4)
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid4
    )
    
    # User Fields
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps - FIX APPLIED HERE
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        # FIX: Revert to standard utcnow() for initial creation
        default=datetime.utcnow 
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        # FIX: Revert to standard utcnow() for updates
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )

    # Relationships
    job_results: Mapped[List["JobResult"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
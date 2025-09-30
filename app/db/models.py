"""
SQLAlchemy ORM Models: app/db/models.py

Defines the structure of the application's relational database tables.
We use SQLAlchemy 2.0+ declarative mapping style.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime, Boolean, ForeignKey, JSON, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

# CRITICAL FIX: Import Base from the dedicated database configuration file
from app.db.database import Base 

# --- 2. User Model ---
class User(Base):
    """Represents an application user."""
    __tablename__ = "users"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        primary_key=True, 
        default=uuid4, 
        server_default=text("gen_random_uuid()")
    )

    # Core Fields
    email: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        nullable=False, 
        index=True
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255), 
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=True
    )

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.utcnow, 
        server_default=text("now()")
    )

    # Relationships (1:N)
    job_results: Mapped[list["JobResult"]] = relationship(
        back_populates="user", 
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, email='{self.email}')"

# --- 3. Job Result Model ---
class JobResult(Base):
    """Stores the results, status, and metadata for background Celery tasks."""
    __tablename__ = "job_results"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        primary_key=True, 
        default=uuid4, 
        server_default=text("gen_random_uuid()")
    )
    
    # Celery Task ID (Used for retrieval/monitoring)
    task_id: Mapped[str] = mapped_column(
        String(64), 
        unique=True, 
        nullable=False, 
        index=True
    )
    
    # Task Metadata
    task_name: Mapped[str] = mapped_column(
        String(255), 
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), 
        default="PENDING" # e.g., PENDING, STARTED, SUCCESS, FAILURE
    )
    result_data: Mapped[Optional[dict]] = mapped_column(
        JSON, 
        nullable=True
    )

    # Foreign Key to User
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"), 
        nullable=False
    )

    # Relationships (N:1)
    user: Mapped["User"] = relationship(back_populates="job_results")

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.utcnow, 
        server_default=text("now()")
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )

    def __repr__(self) -> str:
        return f"JobResult(id={self.id}, task_id='{self.task_id}', status='{self.status}')"

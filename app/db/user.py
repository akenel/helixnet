import uuid
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from models import Base
# IMPORTANT: Ensure this import path matches where your Base is defined
from app.db.database import Base 

class User(Base):
    """
    SQLAlchemy Model for User accounts.
    This structure matches the DDL in create_tables.sql.
    """
    __tablename__ = "UserModel"

    # Primary Key (UUID for robustness and security)
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)

    # Core Fields
    email = Column(String, unique=True, index=True, nullable=False)
    # Store hashed password here, though we skip hashing in the service layer for now
    hashed_password = Column(String, nullable=False) 
    is_active = Column(Boolean, default=True, nullable=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    def __repr__(self):
        return f"<User(id='{self.id}', email='{self.email}', is_active={self.is_active})>"

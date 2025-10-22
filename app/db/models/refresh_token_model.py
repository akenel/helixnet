# File: app/db/models/refresh_token_model.py - FIX
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from sqlalchemy import DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column 
from .base import Base

class RefreshTokenModel(Base):
    __tablename__ = 'refresh_tokens'

    # Primary Key (Corrected autoincrement for UUID - UUIDs are typically not autoincrementing)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4) # Removed autoincrement=True

    # Token Data
    token: Mapped[str] = mapped_column(Text, index=True, nullable=False, unique=True, comment="The actual Keycloak Refresh Token string (hashed or encrypted)")

    # Status & Expiry
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="The date and time the token expires (as per Keycloak)")
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="If true, the token has been explicitly revoked by the user or system")
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Foreign Key to User
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    owner: Mapped["UserModel"] = relationship(back_populates="refresh_tokens")

    def __repr__(self):
        # CORRECTED: Changed 'user_id' to 'owner_id'
        return f"<RefreshTokenModel(id='{self.id}', owner_id='{self.owner_id}', expires_at='{self.expires_at}')>"
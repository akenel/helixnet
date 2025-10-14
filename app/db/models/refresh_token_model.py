import datetime
import uuid # <-- NEW: Import for UUID generation and typing
from typing import Optional
from app.db.models.user_model import User
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean
from sqlalchemy.types import Uuid # <-- NEW: Import for UUID column type
from sqlalchemy.orm import Mapped, relationship
from app.db.database import Base # Assuming Base is imported from app.db.database

class RefreshToken(Base):
    """
    Database model for managing long-lived refresh tokens.

    Refresh tokens are stored to allow for revocation (user logout) and 
    to track token issuance for enhanced security.
    """
    __tablename__ = "refresh_tokens"

    # Token ID (Primary Key). MUST be UUID to match PostgreSQL users.id.
    # Setting as_uuid=True makes SQLAlchemy handle the Python <-> SQL type conversion.
    id: Mapped[uuid.UUID] = Column(Uuid(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    
    # The actual JWT ID (JTI) from the token payload
    jti: Mapped[str] = Column(String, unique=True, nullable=False, index=True) 

    # Link to the user who owns the token. Changed to Uuid to match users.id.
    user_id: Mapped[uuid.UUID] = Column(
        Uuid(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )

    # Expiration timestamp
    expires_at: Mapped[datetime.datetime] = Column(DateTime, nullable=False)
    
    # Status flag for revocation (logout, security breach, etc.)
    is_revoked: Mapped[bool] = Column(Boolean, default=False, nullable=False)

    # Relationship to the User model
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    def __repr__(self):
        return f"<RefreshToken jti={self.jti} user_id={self.user_id} revoked={self.is_revoked}>"

# app/db/models/refresh_token_model.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Uuid
from sqlalchemy.orm import relationship
# app/db/models/refresh_token_model.py
from app.db.models.base import Base  # ✅ direct import, no circular reference

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jti = Column(String, unique=True, nullable=False, index=True)  # JWT ID
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="refresh_tokens")

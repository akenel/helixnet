import uuid
from sqlalchemy import Column, String, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.db.database import Base # We reuse your existing Base class

class Item(Base):
    """
    SQLAlchemy Model for the Item table.
    """
    __tablename__ = "items"

    # Use UUID as primary key, which is standard practice.
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Core Item fields
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    
    # Optional field to link items to users later
    owner_id = Column(PG_UUID(as_uuid=True), nullable=True) 

    def __repr__(self):
        return f"<Item(name='{self.name}', price='{self.price}')>"
# app/api/services/item_model.py
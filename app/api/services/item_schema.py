"""
Pydantic Schemas for the Item Model.
Defines data structures for request bodies and response models.
"""
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional

# --- Base Schemas ---

class ItemBase(BaseModel):
    """Common fields for Item creation/update."""
    name: str = Field(min_length=3, max_length=50, description="Name of the item.")
    description: Optional[str] = Field(None, max_length=500, description="Detailed description.")
    price: float = Field(..., gt=0.0, description="Price of the item (must be positive).")
    is_available: bool = Field(True, description="Availability status.")


# --- Input Schema ---

class ItemCreate(ItemBase):
    """Schema for creating a new item."""
    # No additional fields needed beyond ItemBase for creation in this simple case.
    pass


# --- Output Schema (Response) ---

class ItemResponse(ItemBase):
    """Schema for item data returned by the API."""
    id: UUID
    owner_id: Optional[UUID] = None
    
    class Config:
        """Enables ORM mode to read data from SQLAlchemy models."""
        from_attributes = True
# Note: We avoid circular imports by not importing SQLAlchemy models here.
# This file focuses solely on Pydantic schemas for clean data handling.
# This keeps our API layer decoupled from the database layer.
# This file can be expanded with additional schemas as needed.
# Example usage:
# item = ItemCreate(name="Sample", price=9.99)
# item_response = ItemResponse(id=uuid4(), name="Sample", price=9.99, is_available=True)
# print(item_response.json())   # app/api/services/item_schema.py   
# print(item_response.dict())   # Converts to dictionary    
# This file is part of the app/api/services module.
# It can be imported in route handlers to validate request bodies and format responses.
# For example, in a FastAPI route:
# from app.api.services.item_schema import ItemCreate, ItemResponse
# @app.post("/items/", response_model=ItemResponse)
# async def create_item(item: ItemCreate):
#     # Logic to create item in DB and return ItemResponse
#     pass
# This structure promotes clean architecture and separation of concerns.
# This file is intentionally kept simple and focused on schema definitions.
# End of item_schema.py file.
"""
Single-file isolation test, now relying on app/db/database.py for connection.
This confirms the refactoring of the core database module is successful.
"""
import os
import sys
import uuid
from typing import List, Optional
from datetime import datetime

# CRITICAL: We need to adjust the Python path temporarily for venv testing
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID, uuid4
from sqlalchemy import Column, String, Float, Boolean, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.future import select

# >>> R1 CHANGE: IMPORT CORE DB LOGIC FROM ITS NEW, PERMANENT HOME <<<
from app.db.database import Base, engine, get_db_session

# --- 1. SQLALCHEMY MODELS (TEMPORARY LOCATION, MOVING IN R2) ---

class Item(Base):
    __tablename__ = "items"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    owner_id = Column(PG_UUID(as_uuid=True), nullable=True) 
    
    def __repr__(self):
        return f"<Item(name='{self.name}')>"


# --- 2. PYDANTIC SCHEMAS (TEMPORARY LOCATION, MOVING IN R3) ---

class UserBase(BaseModel):
    email: EmailStr
    
class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class ItemBase(BaseModel):
    name: str = Field(min_length=3, max_length=50, description="Item Name")
    description: Optional[str] = Field(None, max_length=500, description="Detailed Description")
    price: float = Field(..., gt=0.0, description="Price Tag")
    is_available: bool = Field(True, description="Available Status")

class ItemCreate(ItemBase):
    pass

class ItemResponse(ItemBase):
    id: UUID = Field(..., description="Unique ID")
    owner_id: Optional[UUID] = Field(None, description="Owner ID")
    
    class Config:
        from_attributes = True


# --- 3. APPLICATION SETUP & STARTUP EVENT ---
app = FastAPI(
    title="🌟 HelixNet API - Isolated Connection Test (R1 Verified) 🚀",
    description="Refactor complete: Core DB connection logic is now imported from app.db.database.",
    version="0.1.1 (R1 Complete)",
)

@app.on_event("startup")
async def startup_db_check():
    """
    On startup, ensure a connection can be made and create the 'items' table if it doesn't exist.
    (Uses the imported 'engine' and 'Base')
    """
    print("--- [STARTUP] Attempting to connect via refactored app.db.database ---")
    try:
        async with engine.begin() as conn:
            # Create all tables defined by the imported Base (Item, and potentially others)
            await conn.run_sync(Base.metadata.create_all)
        print("--- [SUCCESS] Refactored Postgres connection established and tables ensured. ---")
    except Exception as e:
        print(f"--- [FATAL ERROR] Failed to connect to or initialize Postgres: {e} ---")
        sys.exit(1)


# --- 4. ROUTES ---
mock_db = {} 

@app.get(
    "/health",
    summary="💖 System Health Check (R1 Verification)",
    tags=["System"]
)
async def get_system_health(db: AsyncSession = Depends(get_db_session)):
    """
    Tests the imported get_db_session dependency. If this works, R1 is successful.
    """
    return {"status": "OK", "message": "Postgres connection confirmed via clean app.db.database import! 🚀"}


@app.post(
    "/users/", 
    response_model=UserResponse, 
    status_code=201,
    summary="👶 Create New User (Mock DB Test)",
    tags=["Users"]
)
def create_new_user(user_in: UserCreate):
    """(Kept simple for isolation) Creates a new user in mock_db."""
    if user_in.email in mock_db:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user_data = {
        "id": uuid4(),
        "email": user_in.email,
        "is_active": True,
        "created_at": datetime.now()
    }
    mock_db[user_in.email] = new_user_data
    return UserResponse(**new_user_data)


@app.post(
    "/items/", 
    response_model=ItemResponse, 
    status_code=201,
    summary="🛒 Create a Brand New Item (Postgres Save Test)",
    tags=["Items"]
)
async def create_item(
    item_in: ItemCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Creates a new item and saves it to the database."""
    db_item = Item(**item_in.model_dump())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

@app.get(
    "/items/", 
    response_model=List[ItemResponse],
    summary="📚 Retrieve All Items (Postgres Read Test)",
    tags=["Items"]
)
async def read_items(db: AsyncSession = Depends(get_db_session)):
    """Reads all items from the database."""
    result = await db.execute(select(Item))
    items = result.scalars().all()
    return items

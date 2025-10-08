# app/schemas/user.py
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr
import uuid
from datetime import datetime
from pydantic import ConfigDict
model_config = ConfigDict(from_attributes=True) #  You'll also need to import `ConfigDict` from `pydantic`.
class UserBase(BaseModel):
    email: EmailStr
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = None
    is_active: bool | None = None

# Assuming your UserInDB model looks something like this:
class UserInDB(BaseModel):
    id: uuid.UUID
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    # 👇️ ADD THIS SUB-CLASS TO ENABLE ORM MODE
    class Config:
        from_attributes = True  # Pydantic V2
        # orm_mode = True # Pydantic V1 (Use from_attributes if you are on Pydantic V2 or higher)


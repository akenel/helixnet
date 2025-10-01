from pydantic import BaseModel, ConfigDict, EmailStr
import uuid
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = None
    is_active: bool | None = None

class UserInDB(UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime | None = None

class Config:
    orm_mode = True
    model_config = ConfigDict(from_attributes=True)
  #  You'll also need to import `ConfigDict` from `pydantic`.

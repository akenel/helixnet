# app/schemas/user_schema.py
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
class UserBase(BaseModel):
    email: EmailStr = Field(..., example="new@helix.net")
    is_admin: Optional[bool] = Field(default=False, example=True)
class UserCreate(UserBase):
    password: str = Field(..., min_length=1, example="password123")
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, example="admin@helix.net")
    password: Optional[str] = Field(None, example="admin_pass")
    is_admin: Optional[bool] = Field(None, example=False)
class UserRead(UserBase):
    id: UUID = Field(..., example="a3f2f8e2-9a15-4f58-8f67-89b6b2e512cd")
class TokenPairOut(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str
    refresh_jti: Optional[str]
    refresh_expires_at: Optional[str]
    class Config:
        orm_mode = True
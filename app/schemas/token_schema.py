from pydantic import BaseModel, Field

from typing import Optional
from datetime import datetime
# --- Schema for Login/Refresh Responses ---
class TokenResponse(BaseModel):
    """Schema for returning both access and refresh tokens after login or refresh."""
    access_token: str = Field(..., description="The short-lived JWT used for API authorization.")
    refresh_token: str = Field(..., description="The long-lived JWT used to obtain new access tokens.")
    token_type: str = Field("bearer", description="The type of token.")

    class Config:
        from_attributes = True

# --- Schema for the /refresh request body ---
class RefreshTokenSchema(BaseModel):
    """Schema for the body of the POST request to refresh a token."""
    refresh_token: str = Field(..., description="The current valid refresh token.")

    class Config:
        from_attributes = True


# ================================================================
# 🧩 Schema for the internal JWT payload
# This schema validates the data inside the JWT after decoding.
# ================================================================
class TokenPayload(BaseModel):
    """Schema for data contained within the JWT."""
    sub: str = Field(..., description="Subject: The unique identifier (UUID string) of the user.")
    iat: Optional[datetime] = Field(None, description="Issued At (optional, included in standard JWTs).")
    exp: Optional[datetime] = Field(None, description="Expiration Time (optional, included in standard JWTs).")
    
    class Config:
        from_attributes = True

# ================================================================
# --- Schema for Login/Refresh Responses ---
# ================================================================
class TokenResponse(BaseModel):
    """Schema for returning both access and refresh tokens after login or refresh."""
    access_token: str = Field(..., description="The short-lived JWT used for API authorization.")
    refresh_token: str = Field(..., description="The long-lived JWT used to obtain new access tokens.")
    token_type: str = Field("bearer", description="The type of token.")

    class Config:
        from_attributes = True

# ================================================================
# --- Schema for the /refresh request body ---
# ================================================================
class RefreshTokenSchema(BaseModel):
    """Schema for the body of the POST request to refresh a token."""
    refresh_token: str = Field(..., description="The current valid refresh token.")

    class Config:
        from_attributes = True


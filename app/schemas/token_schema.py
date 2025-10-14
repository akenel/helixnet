from pydantic import BaseModel, Field

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

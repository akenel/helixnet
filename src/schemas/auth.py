from pydantic import BaseModel, Field

# --- Request Schemas ---

class TokenRequest(BaseModel):
    """Schema for requesting a new token using username/password or a refresh token."""
    username: str = Field(..., description="User's login username (typically email).")
    password: str = Field(..., description="User's plaintext password.")
    
    # Configuration for Pydantic v2/v3
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "username": "user_name@helix.net",
                "password": "user_pass"
            }
        }
    }

class RefreshTokenRequest(BaseModel):
    """Schema for exchanging a refresh token for a new access token."""
    refresh_token: str = Field(..., description="The refresh token provided by Keycloak.")
    
    model_config = {
        "from_attributes": True
    }


# --- Response Schemas ---

class KeycloakTokenResponse(BaseModel):
    """The successful response structure from Keycloak's /token endpoint."""
    access_token: str = Field(..., description="The short-lived JWT access token.")
    expires_in: int = Field(..., description="Access token expiry in seconds.")
    refresh_token: str = Field(..., description="The long-lived refresh token.")
    token_type: str = Field(..., description="Type of token (e.g., 'Bearer').")
    
    model_config = {
        "from_attributes": True
    }

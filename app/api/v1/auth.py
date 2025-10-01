import json
from typing import Any
from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

# --- Placeholder Models (Replace with your actual models) ---

# This model defines the structure of the token response
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str
    expires_in: int # Seconds until expiration

# This model is used for the /refresh endpoint body
class RefreshRequest(BaseModel):
    refresh_token: str

# --- API Router Setup ---

# We'll use /auth as the prefix for all token operations
router = APIRouter(prefix="/auth", tags=["Authentication"])

# --- Placeholder Functions (Replace with your actual business logic) ---

def verify_user_credentials(email: str, password: str) -> Any:
    """
    STUB: Replace this with your database logic to verify email and password.
    If valid, return the user object (or dict/UUID). Otherwise, return None.
    """
    print(f"DEBUG: Attempting to verify credentials for {email}")
    # Simulate a successful verification
    if email.endswith("@example.com") and password == "string":
        # Simulate returning a user ID or object
        return {"user_id": "9f964e96-e93f-4a2d-bb6b-af17077e9bbe", "email": email}
    # If the user was not found or credentials were bad
    return None

def create_auth_tokens(user_data: Any) -> TokenResponse:
    """
    STUB: Replace this with your JWT generation logic.
    Creates both access and refresh tokens.
    """
    # Define token lifespan
    access_token_expires = timedelta(minutes=15)
    refresh_token_expires = timedelta(days=7)

    # In a real app, you'd use a JWT library (like `python-jose`) here.
    # We'll use placeholders for now.
    
    # 1. Access Token: Typically contains the user ID and expiration time (exp).
    access_token = f"ACCESS_TOKEN_FOR_{user_data['user_id']}_EXP_{int((datetime.utcnow() + access_token_expires).timestamp())}"

    # 2. Refresh Token: A longer-lived, often opaque token stored in the database.
    refresh_token = f"REFRESH_TOKEN_FOR_{user_data['user_id']}_SECRET_{hash(user_data['user_id'])}"

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=int(access_token_expires.total_seconds()),
    )

def refresh_access_token_logic(refresh_token: str) -> TokenResponse:
    """
    STUB: Replace this with logic to validate a refresh token and issue a new access token.
    """
    # 1. Validate the refresh token against the database.
    if not refresh_token.startswith("REFRESH_TOKEN_FOR_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token format or expiry",
        )

    # 2. Extract user data from the refresh token (e.g., user ID).
    user_id = refresh_token.split("_")[3] # Mock extraction

    # 3. Create a new token set (or just a new access token)
    return create_auth_tokens({"user_id": user_id, "email": f"user_{user_id}@example.com"})

# ----------------------------------------------------
# 1. Standard OAuth2 Token Endpoint (for Login)
# ----------------------------------------------------
@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Obtain JWT Access and Refresh tokens using username (email) and password.
    This uses the standard OAuth2 Password Flow.
    """
    user = verify_user_credentials(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # User is verified, generate tokens
    tokens = create_auth_tokens(user)
    
    return tokens

# ----------------------------------------------------
# 2. Token Refresh Endpoint
# ----------------------------------------------------
@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest):
    """
    Use a valid Refresh Token to get a new Access Token (and usually a new Refresh Token).
    """
    try:
        new_tokens = refresh_access_token_logic(request.refresh_token)
        return new_tokens
    except HTTPException as e:
        # Re-raise authentication errors
        raise e
    except Exception:
        # Catch unexpected errors during the refresh process
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh token. Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

# ----------------------------------------------------
# 3. Quick Test Endpoint (to be removed later)
# ----------------------------------------------------
@router.get("/status")
async def auth_status():
    return {"status": "Authentication router online. Check /auth/token and /auth/refresh in docs."}

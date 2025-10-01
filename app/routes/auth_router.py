from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db_session as get_db
from app.services import user_service
from app.core.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES # Import both the function and the constant
from datetime import timedelta
from typing import Dict, Any
# Router setup, adhering to the user's structure (path will be /token)
auth_router = APIRouter(tags=["Authentication"])
@auth_router.post("/token", response_model=Dict[str, Any])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle user login via OAuth2 Password flow and return an access token.
    This uses the standard 'username' (which is the user's email) and 'password' fields in form data.
    """
    # 1. Fetch user by email (form_data.username)
    user = await user_service.get_user_by_email(db, form_data.username)

    # 2. Check if user exists and verify password
    # NOTE: Assumes user_service.verify_password and user.hashed_password are implemented.
    if not user or not user_service.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Create the JWT token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    access_token = create_access_token(
        data={"sub": str(user.id)}, 
        expires_delta=access_token_expires
    )
    
    # 4. Return the token in the required OAuth2 format
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60 # Return expiry in seconds
    }

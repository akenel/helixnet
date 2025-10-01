# app/core/config.py
"""
Configuration settings for the application.
Uses environment variables for secure, external management of secrets.
"""
import os

# --- Security Settings (Default values for development) ---
# NOTE: In a production environment, SECRET_KEY must be a long, randomly generated string.
SECRET_KEY = os.environ.get("SECRET_KEY", "b4A8xJ2dK0pQ7yT5cZ1vU9eW6nI3mH7g")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days for development/testing

# --- JWT Token Security ---
# This dictionary contains the security constants.
settings = {
    "SECRET_KEY": SECRET_KEY,
    "ALGORITHM": ALGORITHM,
    "ACCESS_TOKEN_EXPIRE_MINUTES": ACCESS_TOKEN_EXPIRE_MINUTES
}

"""
Service Layer: app/api/services/user.py

Handles all business logic and direct database interactions related to Users.
"""
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException

from app.db.models import User # Import SQLAlchemy model
from app.schemas.user import UserCreate, UserUpdate # Import Pydantic schemas

# --- Temporary/Dummy Password Hashing (REPLACE ME) ---
def get_password_hash(password: str) -> str:
    """
    In a real application, this would use a secure library like passlib 
    (e.g., bcrypt) to hash the password securely.
    """
    # Simply return the password string prefixed, for development only.
    return f"hashed_{password}"
# --- End of Temporary Hashing ---


def create_user(db: Session, user: UserCreate) -> User:
    """
    Creates a new user in the database.
    
    Args:
        db: The active SQLAlchemy database session.
        user: Pydantic schema containing user data.
        
    Returns:
        The created User ORM object.
    """
    # 1. Check for existing user (optional, but good practice)
    existing_user = db.scalar(select(User).where(User.email == user.email))
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered.")
        
    # 2. Hash the password
    hashed_password = get_password_hash(user.password)
    
    # 3. Create the ORM model instance
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        is_active=user.is_active
    )
    
    # 4. Add, commit, and refresh to get the generated UUID and timestamps
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_email(db: Session, email: str) -> User | None:
    """Retrieves a user by their email address."""
    # Use SQLAlchemy 2.0 style select/scalar/one_or_none
    return db.scalar(select(User).where(User.email == email))


def get_user_by_id(db: Session, user_id: str) -> User | None:
    """Retrieves a user by their UUID ID."""
    return db.scalar(select(User).where(User.id == user_id))


def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    """Retrieves a list of all users."""
    # Use .all() to get a list of ORM objects
    return list(db.scalars(select(User).offset(skip).limit(limit)))

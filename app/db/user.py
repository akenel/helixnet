# app/db/user.py
import uuid
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.database import Base
# IMPORTANT: Ensure this import path matches where your Base is defined
from app.db.database import Base 


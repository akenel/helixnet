# File: app/db/models/base.py - FIX
from sqlalchemy.orm import DeclarativeBase

# The base class from which all models will inherit.
# Inherit from DeclarativeBase for SQLAlchemy 2.0 style
class Base(DeclarativeBase):
    pass
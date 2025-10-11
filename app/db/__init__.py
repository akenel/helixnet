"""
app/db/models/__init__.py /home/angel/repos/helixnet/app/db/__init__.py

💥 Model registry initializer.
Ensures all ORM models are imported and registered to Base.metadata
before any database setup or migrations.
"""

from app.db.models.base import Base

# 🚀 Import *all* models here to register them with SQLAlchemy Base
from app.db.models.user_model import User
from app.db.models.job_model import Job
from app.db.models.artifact_model import Artifact

__all__ = [
    "Base",
    "User",
    "Job",
    "Artifact",
]

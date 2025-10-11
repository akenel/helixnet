"""
This module ensures all ORM models are imported so that Base.metadata 
can register their table definitions before database creation/migration.
"""

from .user_model import User
from .job_model import Job
from .task_model import TaskResult
from .artifact_model import Artifact

# Expose Base to make it accessible via app.db.models.Base
from app.db.database import Base 

# Explicitly export model names for easier import elsewhere (e.g., from app.db.models import Job)
__all__ = [
    "Base",
    "User",
    "Job",
    "TaskResult",
    "Artifact",
]

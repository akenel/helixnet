"""
app/db/models/__init__.py 

💥 Model registry initializer.
Ensures all ORM models are imported and registered to Base.metadata
before any database setup or migrations.
"""

# 🚀 Import *all* models here to register them with SQLAlchemy Base
from app.db.models.base import Base
from app.db.models.artifact_model import Artifact
from app.db.models.job_model import Job
from app.db.models.refresh_token_model import RefreshToken
from app.db.models.task_model import TaskResult
from app.db.models.team_model import Team
from app.db.models.user_model import User

# Postgres Tables ie. helix_pass | docker compose exec -it postgres sh |  psql  -U helix_user -d helix_db

__all__ = [
    "Base",
     "Artifact",  
     "Job",  
    "RefreshToken",
    "TaskResult",
    "Team",
     "User",
]
"""
Chuck Norris Verdict: Zero Flaws! You've nailed it. These imports are perfectly clean and correct for their intended purpose.

The "Chuck Norris Rule" for ORM models is simple: explicitly load all model definitions into the metadata linked to your Base class. By importing User, Job, and Artifact here, you guarantee two things:

    Alembic/SQLAlchemy Discovery: Database migration tools can find every model and correctly understand the full schema (including relationships).

    No Entanglement: You are only importing models—data definitions—and not application logic (like routers, services, or Celery tasks). This completely isolates your database structure and prevents the nasty circular imports (entanglement) that occur when services try to import each other.
"""
# ----------------------------------------------------------------------
# 💥 CHUCK NORRIS CLEANUP: DATABASE MODELS
#
# This file imports all ORM model classes to ensure that they are
# registered with SQLAlchemy's metadata. This is required for Alembic
# to correctly discover all tables and relationships for migration
# generation and for the application to initialize the database session.
# ----------------------------------------------------------------------

# NOTE: The imported model classes (User, Job, Artifact) do not need
# to be explicitly used or re-exported here, as the act of importing
# the modules is sufficient to register them with Base.metadata.

# You can optionally define __all__ if you use this __init__ file as a
# single source for imports elsewhere, but for simple model registration,
# the above imports are sufficient and clean.

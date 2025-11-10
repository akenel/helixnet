# File: app/db/__init__.py
# Purpose: Core database imports and setup exports.

# Export the core database initialization and session management functions
from .database import close_async_engine, get_db_session_context, init_db_tables

# Export the Base class and all Model classes for external modules that need them
from .models.base import Base

# FIX: Ensure all imports use the full, consistent model class names (e.g., ArtifactModel, not Artifact)
from .models.user_model import UserModel
from .models.team_model import TeamModel
from .models.refresh_token_model import RefreshTokenModel
from .models.job_model import JobModel
from .models.task_model import TaskModel
from .models.artifact_model import ArtifactModel
from .models.message_tasks_model import MessageTaskModel
from .models.pipeline_tasks_model import PipelineTaskModel
from .models.initializer_model import InitializerModel

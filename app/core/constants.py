# ============================================================
# ⚙️ app/core/constants.py — Application Enums & Constants
# ============================================================
from enum import Enum

class UserRoles(str, Enum):
    """Defines the organizational roles for a user."""
    ADMIN = "admin"
    BASIC = "basic"
    MANAGER = "manager"
    # Add more roles as needed

class UserScopes(str, Enum):
    """Defines the permissions or scopes granted to a user's token."""
    ADMIN = "admin"
    USER = "user"
    READ_ONLY = "read_only"
    # Add more scopes as needed

# Define other constants here (e.g., Job Status strings, API defaults)

# Note: The JobStatus enum is likely defined in app.db.models.job_model

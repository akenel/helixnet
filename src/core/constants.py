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
 
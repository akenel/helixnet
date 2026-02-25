# ============================================================
# ⚙️ app/core/constants.py — Application Enums & Constants
# ============================================================
from enum import Enum


# ============================================================
# HelixEnum -- The HelixNet Enum Standard
# ============================================================
# Names:  UPPERCASE          (PEP 8)
# Values: lowercase_snake    (clean API/JSON output)
# Safety: case-insensitive   (_missing_ hook)
#
# Usage:
#   class BugStatus(HelixEnum):
#       OPEN = "open"
#       IN_PROGRESS = "in_progress"
#
#   BugStatus("open")  -> BugStatus.OPEN
#   BugStatus("OPEN")  -> BugStatus.OPEN
#   BugStatus("Open")  -> BugStatus.OPEN
#
# SQLAlchemy columns MUST use values_callable:
#   SQLEnum(BugStatus, values_callable=lambda x: [e.value for e in x])
# ============================================================
class HelixEnum(str, Enum):
    """Base enum for all HelixNet enums. Case-insensitive value lookup."""

    @classmethod
    def _missing_(cls, value):
        if not isinstance(value, str):
            return None
        needle = value.lower()
        for member in cls:
            if member.value.lower() == needle:
                return member
        return None


class HelixApplication(HelixEnum):
    """Which application/module this item belongs to."""
    HELIXNET = "helixnet"
    CAMPER = "camper"
    ISOTTO = "isotto"


class UserRoles(HelixEnum):
    """Defines the organizational roles for a user."""
    ADMIN = "admin"
    BASIC = "basic"
    MANAGER = "manager"

class UserScopes(HelixEnum):
    """Defines the permissions or scopes granted to a user's token."""
    ADMIN = "admin"
    USER = "user"
    READ_ONLY = "read_only"
 
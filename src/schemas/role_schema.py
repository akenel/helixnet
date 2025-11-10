from typing import List
from fastapi import Depends, HTTPException, status

from src.schemas.user_schema import UserRead, UserRoles

from src.core.local_auth_service import get_current_user # Assuming this returns a UserRead object

# NOTE: The 'get_current_active_user' dependency is assumed to exist 
# and successfully decode/validate the JWT, returning the APICaller/UserRead object.

class RoleChecker:
    """
    A reusable FastAPI dependency class to check if the authenticated user 
    has at least one of the required roles.

    Usage:
        @router.get("/admin_data", dependencies=[Depends(RoleChecker([UserRoles.SUPERUSER]))])
    """
    def __init__(self, allowed_roles: List[UserRoles]):
        """
        Initializes the checker with a list of roles required to access the endpoint.
        :param allowed_roles: List of UserRoles required for access.
        """
        # Convert Pydantic Enum roles to a set of strings for fast lookup
        self.allowed_role_strings = {role.value for role in allowed_roles}

    def __call__(self, current_user: UserRead = Depends(get_current_user)):
        """
        The dependency resolution logic. Checks if the user's roles intersect 
        with the required roles.
        """
        
        # 1. Check for immediate superuser access (the fail-safe)
        if current_user.is_superuser:
            return current_user # Superuser always passes.

        # 2. Check for required roles
        # Note: current_user.roles is a List[str] from the database/token claims
        
        # Convert user's current roles (List[str]) to a set for fast intersection check
        user_roles_set = set(current_user.roles) 
        
        # Check if the user has ANY of the roles required by the endpoint
        if user_roles_set.isdisjoint(self.allowed_role_strings):
            
            # If there's no overlap, raise an authorization error
            error_msg = (
                f"User '{current_user.username}' does not have the required roles "
                f"({', '.join(self.allowed_role_strings)})."
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg,
            )
            
        # If roles overlap or user is superuser, return the user object (access granted)
        return current_user

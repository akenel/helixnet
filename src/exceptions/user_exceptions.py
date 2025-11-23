# src/exceptions/user_exceptions.py
"""
Custom exception classes for user and authentication services.
These help differentiate between service-level errors (e.g., Keycloak failure)
and business logic errors (e.g., duplicate user attempts).

The router (users_router.py) specifically uses DuplicateUserError, allowing 
it to catch this specific case and return a 409 Conflict.
"""

class UserError(Exception):
    """Base exception for all user service errors in the application."""
    pass

class UserNotFound(UserError):
    """Raised when a user cannot be found by ID or other criteria in the database."""
    def __init__(self, detail: str = "User not found."):
        self.detail = detail
        super().__init__(self.detail)
        
# ----------------------------------------------------
# Base Exception for all User-related service errors
# ----------------------------------------------------
class UserServiceError(Exception):
    """Base exception class for all custom errors in the user service."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

# ----------------------------------------------------
# Business Logic Errors
# ----------------------------------------------------

class DuplicateUserError(Exception):
    """Raised when attempting to create a Keycloak user that already exists."""
    def __init__(self, message: str):
        super().__init__(message)


class KeycloakRegistrationFailed(Exception):
    def __init__(self, detail: str = "Keycloak registration failed"):
        self.detail = detail
        super().__init__(self.detail)


class KeycloakUserDeletionFailed(UserServiceError):
    """Raised when an attempt to delete a user from Keycloak fails."""
    def __init__(self, user_id: str, detail: str, status_code: int = 500):
        message = f"Failed to delete Keycloak user '{user_id}'. Detail: {detail}"
        super().__init__(message, status_code)

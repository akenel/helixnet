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

class DuplicateUserError(UserError):
    """Raised when an attempt is made to create a user that already exists (email/username)."""
    def __init__(self, detail: str = "User with this identifier already exists."):
        self.detail = detail
        super().__init__(self.detail)

class KeycloakRegistrationFailed(UserError):
    """Raised when Keycloak rejects the user creation request (e.g., invalid password, policy violation)."""
    def __init__(self, detail: str = "Keycloak failed to register the user."):
        self.detail = detail
        super().__init__(self.detail)

class UserNotFound(UserError):
    """Raised when a user cannot be found by ID or other criteria in the database."""
    def __init__(self, detail: str = "User not found."):
        self.detail = detail
        super().__init__(self.detail)

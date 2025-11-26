"""
Admin Role Management API
Allows pos-admin users to manage role assignments via Swagger/API.
"""
import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import httpx

from src.core.config import get_settings
from src.core.keycloak_auth import require_admin

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/admin", tags=["Admin - Role Management"])


# ================================================================
# Pydantic Models
# ================================================================

class RoleInfo(BaseModel):
    """Information about a POS role"""
    name: str
    description: str
    emoji: str


class RoleAssignment(BaseModel):
    """Request body for assigning a role"""
    role_name: str


class UserRolesResponse(BaseModel):
    """Response containing user's current roles"""
    user_id: str
    username: str
    roles: List[str]


# ================================================================
# Helper Functions
# ================================================================

async def get_admin_token() -> Optional[str]:
    """
    Get admin access token from Keycloak master realm.
    Reuses logic from keycloak_health_service.py
    """
    try:
        token_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_MASTER_REALM}/protocol/openid-connect/token"

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                token_url,
                data={
                    "client_id": "admin-cli",
                    "username": settings.HX_SUPER_NAME,
                    "password": settings.HX_SUPER_PASSWORD,
                    "grant_type": "password"
                },
                timeout=10.0
            )

            if response.status_code == 200:
                token_data = response.json()
                return token_data.get("access_token")
            else:
                logger.error(f"Failed to get admin token: {response.status_code} - {response.text}")
                return None

    except Exception as e:
        logger.error(f"Error getting admin token: {e}")
        return None


async def get_user_by_id(admin_token: str, user_id: str) -> Optional[dict]:
    """
    Fetch user details from Keycloak by user ID.

    Args:
        admin_token: Admin access token
        user_id: UUID of the user

    Returns:
        User details dict or None if not found
    """
    try:
        user_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/kc-pos-realm-dev/users/{user_id}"
        headers = {"Authorization": f"Bearer {admin_token}"}

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(user_url, headers=headers, timeout=5.0)

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"User {user_id} not found: {response.status_code}")
                return None

    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        return None


# ================================================================
# API Endpoints
# ================================================================

@router.get("/roles", response_model=List[RoleInfo])
async def list_all_pos_roles(
    current_user: dict = Depends(require_admin())
):
    """
    List all available POS roles with descriptions.

    **Requires**: pos-admin role

    Returns all 5 POS roles:
    - 💰️ pos-cashier
    - 👔️ pos-manager
    - 🛠️ pos-developer
    - 📊️ pos-auditor
    - 👑️ pos-admin
    """
    logger.info(f"Admin {current_user['username']} listing all POS roles")

    return [
        RoleInfo(
            name="💰️ pos-cashier",
            description="Cashier role - Create transactions, scan products, process checkout. Limited to 10% discount threshold.",
            emoji="💰️"
        ),
        RoleInfo(
            name="👔️ pos-manager",
            description="Manager role - Full POS access including product management, unlimited discounts, and reporting.",
            emoji="👔️"
        ),
        RoleInfo(
            name="🛠️ pos-developer",
            description="Developer role - Create products for testing, limited access to production data.",
            emoji="🛠️"
        ),
        RoleInfo(
            name="📊️ pos-auditor",
            description="Auditor role - Read-only access to all transactions, products, and reports for compliance.",
            emoji="📊️"
        ),
        RoleInfo(
            name="👑️ pos-admin",
            description="System administrator - Full control over POS realm and configuration.",
            emoji="👑️"
        )
    ]


@router.get("/users/{user_id}/roles", response_model=UserRolesResponse)
async def get_user_roles(
    user_id: UUID,
    current_user: dict = Depends(require_admin())
):
    """
    Get current roles assigned to a specific user.

    **Requires**: pos-admin role

    **Args**:
    - user_id: UUID of the user (e.g., 00000000-0000-0000-0000-000000000001 for Pam)

    **Returns**:
    - user_id: User's UUID
    - username: User's username
    - roles: List of assigned POS roles
    """
    logger.info(f"Admin {current_user['username']} fetching roles for user {user_id}")

    # Get admin token
    admin_token = await get_admin_token()
    if not admin_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to authenticate with Keycloak admin"
        )

    # Get user details
    user = await get_user_by_id(admin_token, str(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )

    # Fetch user's realm roles
    try:
        roles_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/kc-pos-realm-dev/users/{user_id}/role-mappings/realm"
        headers = {"Authorization": f"Bearer {admin_token}"}

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(roles_url, headers=headers, timeout=5.0)
            response.raise_for_status()

            all_roles = response.json()
            # Filter to only POS roles (exclude default-roles-*)
            pos_roles = [
                role["name"] for role in all_roles
                if "pos-" in role["name"] or role["name"] in [
                    "💰️ pos-cashier", "👔️ pos-manager", "🛠️ pos-developer",
                    "📊️ pos-auditor", "👑️ pos-admin"
                ]
            ]

            return UserRolesResponse(
                user_id=str(user_id),
                username=user.get("username", "unknown"),
                roles=pos_roles
            )

    except httpx.HTTPStatusError as e:
        logger.error(f"Failed to fetch roles for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user roles: {e.response.status_code}"
        )
    except Exception as e:
        logger.error(f"Error fetching roles for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error fetching user roles: {str(e)}"
        )


@router.post("/users/{user_id}/roles", status_code=status.HTTP_200_OK)
async def assign_role_to_user(
    user_id: UUID,
    role_assignment: RoleAssignment,
    current_user: dict = Depends(require_admin())
):
    """
    Assign a POS role to a user.

    **Requires**: pos-admin role

    **Args**:
    - user_id: UUID of the user
    - role_name: Name of the role to assign (e.g., "👔️ pos-manager")

    **Example**:
    ```json
    {
        "role_name": "👔️ pos-manager"
    }
    ```

    **Returns**:
    - Success message
    """
    logger.info(f"Admin {current_user['username']} assigning role '{role_assignment.role_name}' to user {user_id}")

    # Validate role name
    valid_roles = [
        "💰️ pos-cashier", "👔️ pos-manager", "🛠️ pos-developer",
        "📊️ pos-auditor", "👑️ pos-admin"
    ]
    if role_assignment.role_name not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role name. Must be one of: {', '.join(valid_roles)}"
        )

    # Get admin token
    admin_token = await get_admin_token()
    if not admin_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to authenticate with Keycloak admin"
        )

    # Verify user exists
    user = await get_user_by_id(admin_token, str(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )

    try:
        # Step 1: Get the role definition from realm
        realm_roles_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/kc-pos-realm-dev/roles/{role_assignment.role_name}"
        headers = {"Authorization": f"Bearer {admin_token}"}

        async with httpx.AsyncClient(verify=False) as client:
            # Get role definition
            role_response = await client.get(realm_roles_url, headers=headers, timeout=5.0)
            if role_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Role '{role_assignment.role_name}' not found in realm"
                )

            role_data = role_response.json()

            # Step 2: Assign role to user
            assign_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/kc-pos-realm-dev/users/{user_id}/role-mappings/realm"
            assign_response = await client.post(
                assign_url,
                headers={**headers, "Content-Type": "application/json"},
                json=[role_data],  # Must be an array of role objects
                timeout=5.0
            )

            if assign_response.status_code == 204:
                logger.info(f"✅ Successfully assigned '{role_assignment.role_name}' to user {user_id}")
                return {
                    "message": f"Role '{role_assignment.role_name}' assigned to user {user.get('username', str(user_id))}",
                    "user_id": str(user_id),
                    "role": role_assignment.role_name
                }
            else:
                logger.error(f"Failed to assign role: {assign_response.status_code} - {assign_response.text}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to assign role: {assign_response.status_code}"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning role to user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error assigning role: {str(e)}"
        )


@router.delete("/users/{user_id}/roles/{role_name}", status_code=status.HTTP_200_OK)
async def remove_role_from_user(
    user_id: UUID,
    role_name: str,
    current_user: dict = Depends(require_admin())
):
    """
    Remove a POS role from a user.

    **Requires**: pos-admin role

    **Args**:
    - user_id: UUID of the user
    - role_name: Name of the role to remove (e.g., "👔️ pos-manager")

    **Note**: URL-encode the role_name if it contains emojis.
    For Swagger testing, you can use:
    - 💰️ pos-cashier → %F0%9F%92%B0%EF%B8%8F%20pos-cashier
    - 👔️ pos-manager → %F0%9F%91%94%EF%B8%8F%20pos-manager

    **Returns**:
    - Success message
    """
    logger.info(f"Admin {current_user['username']} removing role '{role_name}' from user {user_id}")

    # Get admin token
    admin_token = await get_admin_token()
    if not admin_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to authenticate with Keycloak admin"
        )

    # Verify user exists
    user = await get_user_by_id(admin_token, str(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )

    try:
        # Step 1: Get the role definition from realm
        realm_roles_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/kc-pos-realm-dev/roles/{role_name}"
        headers = {"Authorization": f"Bearer {admin_token}"}

        async with httpx.AsyncClient(verify=False) as client:
            # Get role definition
            role_response = await client.get(realm_roles_url, headers=headers, timeout=5.0)
            if role_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Role '{role_name}' not found in realm"
                )

            role_data = role_response.json()

            # Step 2: Remove role from user
            remove_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/kc-pos-realm-dev/users/{user_id}/role-mappings/realm"
            remove_response = await client.delete(
                remove_url,
                headers={**headers, "Content-Type": "application/json"},
                json=[role_data],  # Must be an array of role objects
                timeout=5.0
            )

            if remove_response.status_code == 204:
                logger.info(f"✅ Successfully removed '{role_name}' from user {user_id}")
                return {
                    "message": f"Role '{role_name}' removed from user {user.get('username', str(user_id))}",
                    "user_id": str(user_id),
                    "role": role_name
                }
            else:
                logger.error(f"Failed to remove role: {remove_response.status_code} - {remove_response.text}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to remove role: {remove_response.status_code}"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing role from user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error removing role: {str(e)}"
        )

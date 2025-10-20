# app/services/keycloak_proxy_service.py
import httpx
import logging
from typing import Dict, Any, Optional

from fastapi import HTTPException, status

from app.core.config import settings
from app.schemas.auth import KeycloakTokenResponse

logger = logging.getLogger(__name__)

class KeycloakProxyService:
    """
    Handles all direct HTTP communication with the Keycloak server for
    token generation and refresh operations using the httpx client.
    """
    
    def __init__(self, http_client: Optional[httpx.AsyncClient] = None):
        """
        Initializes the service with an httpx client.
        We use a default AsyncClient if none is provided, configuring it
        for the common Keycloak base URL.
        """
        if http_client is None:
            self.client = httpx.AsyncClient()
        else:
            self.client = http_client

        # Keycloak requires these three parameters for all token requests
        self.client_id = settings.KEYCLOAK_CLIENT_ID
        self.token_url = settings.KEYCLOAK_TOKEN_URL
        
        # Note on Client Secret: The helixnet-api client is assumed to be a 
        # public client (SPA/FastAPI backend acting as resource server), 
        # so client_secret is omitted for the token flow.

    async def _request_token(self, form_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Internal function to handle the POST request to the Keycloak token endpoint.
        """
        # 1. Add mandatory client_id to the request body
        form_data["client_id"] = self.client_id
        
        # 2. Make the HTTP POST request to the Keycloak Token URL
        try:
            response = await self.client.post(
                self.token_url,
                data=form_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10 # Set a reasonable timeout
            )
            
            # 3. Check for API errors (Keycloak returns 400 for bad credentials)
            if response.status_code == 400:
                error_data = response.json()
                logger.warning(f"Keycloak token request failed: {error_data}")
                
                # Check for common Keycloak error messages
                if error_data.get("error") == "invalid_grant":
                    # This covers bad username/password or invalid refresh token
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid credentials or expired refresh token."
                    )
                # Catch-all for 400 errors
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Keycloak error: {error_data.get('error_description', 'Unknown error.')}"
                )

            # 4. Check for general connection/server errors
            response.raise_for_status()
            
            # 5. Return the successful JSON response
            return response.json()

        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to Keycloak at {self.token_url}: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service (Keycloak) is unavailable."
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"Keycloak returned non-success status: {e.response.status_code}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal error communicating with Keycloak."
            )

    async def get_initial_tokens(self, username: str, password: str) -> KeycloakTokenResponse:
        """
        Exchanges username and password for a new Access and Refresh token.
        """
        form_data = {
            "grant_type": "password",
            "username": username,
            "password": password
        }
        
        token_data = await self._request_token(form_data)
        return KeycloakTokenResponse(**token_data)

    async def refresh_access_token(self, refresh_token: str) -> KeycloakTokenResponse:
        """
        Exchanges a Refresh token for a new Access and Refresh token pair.
        """
        form_data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        
        token_data = await self._request_token(form_data)
        return KeycloakTokenResponse(**token_data)
    
    # CRITICAL: Define a proper shutdown hook for the httpx client
    async def close(self):
        """Cleanly close the httpx client connection."""
        if self.client and not self.client.is_closed:
            await self.client.close()

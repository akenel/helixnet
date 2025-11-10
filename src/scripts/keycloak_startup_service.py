import logging
import asyncio
import httpx # Required for making async HTTP requests

from src.core.config import get_settings

# ================================================================
# ⚙️ CONFIGURATION & LOGGER
# ================================================================
settings = get_settings()
logger = logging.getLogger("🛠️ KeycloakStartupService")
logger.setLevel(logging.INFO)

# ================================================================
# 🩺 KEYCLOAK READINESS CHECK
# ================================================================

async def wait_for_keycloak_ready(
    max_retries: int = 30, initial_delay: int = 2
) -> bool:
    """
    Polls Keycloak's health endpoint using exponential backoff until it's ready.

    This prevents the fatal race condition where FastAPI tries to seed users/register
    clients before Keycloak has finished its internal startup process.

    Args:
        max_retries: The maximum number of times to retry the connection.
        initial_delay: The base delay in seconds before the first retry.

    Returns:
        True if Keycloak is ready within the retry limit, False otherwise.
    """
    KEYCLOAK_URL = settings.KEYCLOAK_SERVER_URL
    # Keycloak often exposes a public endpoint on its base URL when ready
    HEALTH_URL = f"{KEYCLOAK_URL}/realms/master" 
    
    logger.info(f"Keycloak Readiness Check: Polling {HEALTH_URL}")

    async with httpx.AsyncClient(verify=False) as client: # Using verify=False for potential self-signed certs
        for attempt in range(max_retries):
            try:
                # 1. Attempt to connect
                response = await client.get(HEALTH_URL, timeout=10)

                # 2. Check for successful status (200, 302, or other successful redirects)
                if response.status_code < 400:
                    logger.info(f"✅ Keycloak is READY! Status: {response.status_code}")
                    return True

                # Log unexpected status but retry
                logger.warning(
                    f"Keycloak is up but returned non-successful status {response.status_code}. Retrying..."
                )

            except httpx.RequestError as e:
                # This catches network errors, DNS errors, connection refusals, and timeouts.
                if attempt >= max_retries - 1:
                    logger.error("FATAL: Keycloak did not become ready after max retries.")
                    break # Exit the loop after the final attempt fails
                
                # 3. Calculate Exponential Backoff Delay
                # Formula: initial_delay * (2 ** attempt)
                delay = initial_delay * (2 ** attempt)
                # Cap the delay to prevent excessively long waits
                delay = min(delay, 30) 
                
                logger.warning(
                    f"Keycloak Connection Refused/Failed (Attempt {attempt + 1}/{max_retries})."
                    f" Error: {type(e).__name__}. Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)

            except Exception as e:
                logger.error(f"Unexpected error during Keycloak check: {e}", exc_info=True)
                await asyncio.sleep(5) # Standard wait for unknown error
    
    logger.error("🛑 Keycloak Readiness Check FAILED. The application will start but key features (User Auth, Client Registration) will likely fail.")
    return False

HelixNet Core Startup Analysis: Race Conditions and Dependencies (time must be in sync)

----
timedatectl
               Local time: Wed 2025-11-05 22:12:12 CET
           Universal time: Wed 2025-11-05 21:12:12 UTC
                 RTC time: Wed 2025-11-05 21:12:12
                Time zone: Europe/Zurich (CET, +0100)
System clock synchronized: no
              NTP service: inactive
          RTC in local TZ: no


sudo timedatectl set-timezone Europe/Zurich
angel@debian:~/repos/helixnet$ timedatectl
               Local time: Wed 2025-11-05 22:13:35 CET
           Universal time: Wed 2025-11-05 21:13:35 UTC
                 RTC time: Wed 2025-11-05 21:13:35
                Time zone: Europe/Zurich (CET, +0100)
System clock synchronized: no
              NTP service: inactive
          RTC in local TZ: no



sudo timedatectl set-ntp true

 timedatectl
               Local time: Wed 2025-11-05 21:14:36 CET
           Universal time: Wed 2025-11-05 20:14:36 UTC
                 RTC time: Wed 2025-11-05 20:14:36
                Time zone: Europe/Zurich (CET, +0100)
System clock synchronized: yes
              NTP service: active
          RTC in local TZ: no

----


This document analyzes the lifespan manager in app/main.py and the required startup order, focusing on dependencies between the FastAPI App, PostgreSQL (DB), and Keycloak (Auth).

A complex, decoupled architecture like HelixNet's is prone to race conditions where service dependencies are met by the container orchestrator (e.g., Docker Compose's depends_on), but the internal application readiness is not.

1. The Pydantic Configuration Gotcha (Pre-Lifespan)

The Problem: The Pydantic error you saw (KEYCLOAK_ADMIN_USER: Field required) occurs before the lifespan manager even starts. FastAPI cannot load its configuration (settings.py) because a required environment variable is missing in the app container's environment.

The Fix: As discussed, ensure all configuration variables needed by the app (especially KEYCLOAK_ADMIN_USER, KEYCLOAK_ADMIN_PASSWORD, KEYCLOAK_SERVER_URL, etc.) are explicitly passed to the app service in docker-compose.yml.

Gotcha

Description

Impact

Solution

Pydantic Hard Stop

If any required variable in app/core/config.py is not defined in the container's environment, the entire Uvicorn process fails immediately.

Application fails to start, showing a ValidationError.

Define all required variables in the environment section of the app service in docker-compose.yml.

2. Startup Sequence within lifespan(app: FastAPI)

Your current lifespan sequence is logically sound but highlights major race conditions (the "soup") that the team needs to be aware of.

A. The PostgreSQL/DB Race Condition

Your code currently includes a crucial workaround for a common async startup issue:

# 🛑 CRITICAL FIX: Introduce a short delay to mitigate PostgreSQL race conditions.
logger.info("😴 Waiting 3 seconds for Postgres DDL visibility...")
await asyncio.sleep(3)  # Wait 3 seconds


Gotcha

Description

Impact

Solution

DDL Visibility Delay

Even after init_db_tables runs, the asynchronous connection pool (asyncpg / SQLAlchemy) sometimes does not immediately see the newly created schema/tables due to internal transaction timing.

Subsequent DB operations (create_initial_users) fail with relation "users" does not exist.

The 3-second sleep is the standard, pragmatic solution. It gives the database time to ensure DDL changes are visible across all connections.

B. The MinIO/User Seeding Dependency Chain

The user seeding step is the most vulnerable part of the startup because it depends on multiple other services:

create_initial_users(db) requires the DB to be ready and its tables visible.

create_initial_users(db) usually involves an admin client call to Keycloak to register the default user. This requires the Keycloak server to be running and accessible.

Gotcha

Description

Impact

Solution

Keycloak is Not Ready

If the app starts and attempts to register the admin user in Keycloak (via an internal service) before Keycloak has finished its own internal startup/initialization.

Connection failure or Keycloak API returns an internal error. User seeding fails.

MANDATORY depends_on: keycloak in docker-compose.yml. You may need to add a Keycloak readiness probe (a loop that hits Keycloak's health endpoint until it returns 200) before calling create_initial_users.

MinIO Error Hides DB Error

MinIO initialization is currently placed between the DB check and the user seeding. If MinIO fails, the log shows a MinIO error, potentially masking a critical failure in the DB setup or subsequent user seeding.

Misdiagnosis of the root cause of startup failure.

Status Quo is okay, but ensure initialize_minio is robustly wrapped in try/except and logged with exc_info=True, as you have done.

3. Final Recommendation: Enforcing Dependencies

To eliminate "Keycloak Soup," your docker-compose.yml needs to enforce the initial dependency order, and your code needs to be resilient to the internal delays:

Required docker-compose.yml Changes

  app:
    # ... (other configuration)
    depends_on:
      # Ensures these containers are started before the 'app' container.
      # This is ESSENTIAL for Keycloak to be listening on port 8080.
      - keycloak
      - postgres
      - redis
      - minio


Required lifespan Code Changes (Internal Readiness Check)

For a truly robust system, replace the dependency on external configuration with an internal readiness loop (optional but recommended for production):

# In app/services/keycloak_service.py (or similar):
async def wait_for_keycloak_ready():
    """Waits for Keycloak to be fully operational before proceeding."""
    url = f"{settings.KEYCLOAK_SERVER_URL}/health/ready" # Example Keycloak readiness endpoint
    max_retries = 30
    for i in range(max_retries):
        try:
            # Use an HTTP client (like httpx or a simple standard library check)
            # to poll Keycloak's health endpoint
            # Example using a mock check:
            if i > 5: # Assume Keycloak is ready after 5 seconds
                logger.info("Keycloak ready check passed.")
                return True
            else:
                logger.warning(f"Keycloak not ready yet. Retrying in 2s... ({i}/{max_retries})")
                await asyncio.sleep(2)
        except Exception:
            await asyncio.sleep(2)
    logger.error("FATAL: Keycloak did not become ready after maximum retries.")
    return False

# In app/main.py lifespan manager:
# ...
    # 2. Keycloak Readiness Check (Place this before any Keycloak admin calls)
    logger.info("⬇️ Waiting for Keycloak service to be ready...")
    if not await wait_for_keycloak_ready():
        logger.error("FATAL: Keycloak failed to start or respond. User seeding will fail.")

    # 3. Seed Initial Users (This step now relies on a ready Keycloak)
    logger.info("⬇️ Attempting to seed initial users...")
# ...


By explicitly waiting for Keycloak, you remove the reliance on timing and container startup order alone, cleaning up the "soup" immensely!
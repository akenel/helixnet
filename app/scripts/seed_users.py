import asyncio
import os
import sys
import logging
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..')
sys.path.insert(0, project_root)
# ======================================================================
# 🧠 Core Imports
# ================================================================
from app.services.user_service import create_initial_users 
from app.db.database import async_engine
# ======================================================================
# 🛠️ SETUP & EXECUTION
# ======================================================================
logger = logging.getLogger("🌱 DataSeeder")
logging.basicConfig(level=logging.INFO)

async def run_seeder():
    """
    Initializes the database session and executes the asynchronous seeding function.
    """
    logger.info("💾 [DATABASE] Executing initial data seeding script...")
    
    # 1. Ensure the DB structure is initialized (usually done by alembic, but good to ensure engine is ready)
    if not async_engine:
        logger.error("🚨 Database Engine not initialized. Cannot proceed with seeding.")
        return

    # 2. Create a session factory instance
    AsyncSessionLocal = AsyncSessionLocal, 
    
    # 3. Get the session and call the seeding function
    async with AsyncSessionLocal() as db:
        try:
            # Your main seeding function requires the AsyncSession object
            await create_initial_users(db=db) 
            logger.info("✨ [COMPLETE] Task finished successfully. Data seeding complete! Users and base data are ready. 👤")
        except Exception as e:
            logger.error(f"❌ FATAL ERROR during seeding: {e}", exc_info=True)
            # Re-raise the exception so the calling process (like your 'make setup') fails
            raise

# 4. Run the async main function
if __name__ == "__main__":
    try:
        asyncio.run(run_seeder())
    except Exception:
        sys.exit(1)
    
    logger.info("💾 [DATABASE] Initial application setup complete! Ready to accept requests. 🚀")

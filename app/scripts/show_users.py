import asyncio
import logging
from app.db.database import get_db_session
from app.db.models import User
from sqlalchemy import select
import asyncio
# Changed from absolute 'from app.db.database' to relative '.database' 
from ..db.database import get_db_session 
from ..services.user_service import User
# Configure logging to be less verbose for cleaner output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Suppress noisy SQLAlchemy logs
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


async def display_users():
    """Queries and prints the emails of all users in the database."""
    logger.info("⏳ Connecting to DB to fetch user list...")

    # Safely get the database session using the generator
    db_generator = get_db_session()
    try:
        # Retrieve the session object from the async generator
        db = await db_generator.__anext__()
    except Exception as e:
        logger.error(f"🚨 Failed to start database session: {e}")
        # Close the generator before exiting
        await db_generator.aclose()
        return

    try:
        # Construct the query to select only the email column from the User table
        query = select(User.email)

        # Execute the query
        result = await db.execute(query)

        # Fetch all results and flatten them into a list of emails
        emails = [r[0] for r in result.all()]

        if emails:
            print("\n==============================")
            print("✅ FOUND USERS IN DATABASE:")
            print("==============================")
            # Print each email on a new line
            print("\n".join(emails))
            print("==============================\n")
        else:
            print("❌ No users found in the database.")

    except Exception as e:
        logger.error(f"🚨 Error querying users: {e}")
        raise
    finally:
        # Ensure the session is closed cleanly
        await db_generator.aclose()
        logger.info("DB connection closed. 🏁")


if __name__ == "__main__":
    try:
        asyncio.run(display_users())
    except Exception as e:
        logger.error(f"Fatal error during script execution: {e}")

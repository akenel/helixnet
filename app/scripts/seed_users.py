# app/services/user_service.py
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.user_model import User
from app.core.security import get_password_hash  # <- bcrypt-based helper
from app.db.database import get_db_session as get_db_session_async

async def create_initial_users(db: AsyncSession):
    """Seed the database with initial users if none exist."""
    from sqlalchemy import select

    result = await db.execute(select(User))
    users_exist = result.scalars().first()
    if users_exist:
        return

    users = [
        User(
            id=uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"),
            email="admin@helix.net",
            is_admin=True,
            password_hash=get_password_hash("admin_pass"),
        ),
        User(
            id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
            email="demo@helix.net",
            is_admin=False,
            password_hash=get_password_hash("demo_pass"),
        ),
        User(
            id=uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
            email="test@helix.net",
            is_admin=False,
            password_hash=get_password_hash("test_pass"),
        ),
    ]

    db.add_all(users)
    await db.commit()

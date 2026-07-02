"""Database wiring — one SQLite file, no server to babysit."""
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DB_PATH = Path(__file__).resolve().parent.parent / "postino.db"

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate() -> None:
    """Idempotent: add columns models.py gained after the DB was first created (SQLite ALTER).
    Run AFTER create_all — on a fresh DB create_all makes them and this is a no-op; on an existing
    DB it fills the gaps without touching data."""
    from sqlalchemy import text
    wanted = {
        "language": "VARCHAR(4) DEFAULT 'de'",
        "scoop_line": "VARCHAR(300) DEFAULT ''",
        "journey": "TEXT DEFAULT '{}'",
    }
    with engine.begin() as conn:
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(leads)"))}
        for name, decl in wanted.items():
            if name not in cols:
                conn.execute(text(f"ALTER TABLE leads ADD COLUMN {name} {decl}"))

# db/database.py - Database connection, session management, and initialization
# Supports SQLite (dev) and PostgreSQL (production) via DATABASE_URL env var

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import logging

from db.models import Base
from config import settings

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────
# Engine configuration
# StaticPool for SQLite ensures same connection across threads
# ─────────────────────────────────────────────────────────
if "sqlite" in settings.DATABASE_URL:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DEBUG
    )
else:
    # PostgreSQL / other databases
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        echo=settings.DEBUG
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables from ORM models."""
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created successfully")


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency: yields a database session, ensures cleanup.
    Usage:
        @app.get("/")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()

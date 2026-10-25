"""
SQLAlchemy database session management.

We use SQLAlchemy Core + text queries for simplicity.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # helps when DB restarts
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    FastAPI dependency that provides a DB session per request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

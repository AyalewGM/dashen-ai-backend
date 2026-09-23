"""
Database connection and session management for Gasha
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import os
from typing import Generator

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://demo_user:demo_password@postgres:5432/fraudshield_demo"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,  # Number of connections to keep open
    max_overflow=20,  # Max connections beyond pool_size
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=False,  # Set to True for SQL logging
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI endpoints
    Provides a database session and ensures it's closed after use
    
    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # Use db here
            pass
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for database sessions
    
    Usage:
        with get_db_context() as db:
            # Use db here
            pass
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables
    Should be called on application startup
    """
    from app.modules.fraudshield.db_models import Base
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")


def drop_all_tables():
    """
    Drop all tables - USE WITH CAUTION!
    Only for development/testing
    """
    from app.modules.fraudshield.db_models import Base
    Base.metadata.drop_all(bind=engine)
    print("⚠️  All tables dropped")

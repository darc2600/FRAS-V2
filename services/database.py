"""
Improved database service with connection pooling and better error handling
"""
import os
import logging
from contextlib import contextmanager
from typing import Optional, Generator
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.declarative import declarative_base

# Hardcoded settings for now
database_url = "sqlite:///attendance.db"
db_pool_size = 10
db_max_overflow = 20
host = "127.0.0.1"
port = 8000
debug = True
secret_key = "dev-secret-change-me"
jwt_algorithm = "HS256"
jwt_expiration_hours = 24

LOG = logging.getLogger(__name__)

# SQLAlchemy setup
engine = None
SessionLocal = None

def init_database():
    """Initialize database connection and create tables"""
    global engine, SessionLocal

    if database_url.startswith("sqlite"):
        # SQLite-specific configuration
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=debug
        )
    else:
        # PostgreSQL configuration
        engine = create_engine(
            database_url,
            pool_size=db_pool_size,
            max_overflow=db_max_overflow,
            echo=debug
        )

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables if they don't exist
    from database.schema import create_tables
    create_tables(engine)

    LOG.info("Database initialized successfully")

Base = declarative_base()

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        LOG.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def get_db_session() -> Session:
    """Get database session (for backward compatibility)"""
    return SessionLocal()

# Legacy compatibility functions
def get_connection():
    """Legacy function for existing code"""
    return get_db_session()
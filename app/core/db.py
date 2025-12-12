"""
Database connection and session management.

Provides SQLAlchemy engine and session factory for database operations.
"""

from contextlib import contextmanager
from typing import Generator
import time

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import NullPool

from app.config.settings import settings

# Create declarative base for models
Base = declarative_base()

# Global engine and session factory
_engine = None
_SessionLocal = None


def init_db() -> None:
    """
    Initialize the database engine and session factory.

    This should be called once at application startup.
    """
    global _engine, _SessionLocal

    if _engine is not None:
        return  # Already initialized

    database_url = settings.get_db_url()

    # Create engine with connection pooling
    # For Neon (serverless Postgres), we use NullPool to avoid connection pooling issues
    _engine = create_engine(
        database_url,
        poolclass=NullPool,  # Recommended for serverless databases like Neon
        echo=settings.DEBUG,  # Log SQL queries in debug mode
        future=True,  # Use SQLAlchemy 2.0 style
    )

    # Create session factory
    _SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=_engine,
        future=True,
    )


def get_engine():
    """Get the SQLAlchemy engine instance."""
    if _engine is None:
        init_db()
    return _engine


def get_session_factory():
    """Get the session factory."""
    if _SessionLocal is None:
        init_db()
    return _SessionLocal


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Get a database session as a context manager.

    Usage:
        with get_db() as db:
            # Use db session here
            result = db.execute(text("SELECT 1"))

    Yields:
        Session: SQLAlchemy database session
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _log(level: str, category: str, message: str, **kwargs) -> None:
    """Safely log to ProcessLog if available."""
    try:
        from app.services.process_log import ProcessLog
        getattr(ProcessLog, level)(category, message, **kwargs)
    except Exception:
        pass  # Silently ignore if ProcessLog not available


def test_connection() -> tuple[bool, str]:
    """
    Test the database connection.

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        start_time = time.time()
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        duration_ms = (time.time() - start_time) * 1000
        _log("success", "Database", "Connection test successful", duration_ms=duration_ms)
        return True, "Database connection successful!"
    except Exception as e:
        _log("error", "Database", f"Connection test failed: {str(e)}")
        return False, f"Database connection failed: {str(e)}"


def create_tables() -> None:
    """
    Create all tables defined in models.

    This should be called after all models are imported.
    """
    # Import models to ensure they're registered with Base
    from app.core import models  # noqa: F401

    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def drop_tables() -> None:
    """
    Drop all tables. Use with caution!

    This is primarily for development and testing.
    """
    from app.core import models  # noqa: F401

    engine = get_engine()
    Base.metadata.drop_all(bind=engine)


def initialize_schema() -> tuple[bool, str]:
    """
    Initialize the database schema by creating all tables.

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        _log("info", "Database", "Initializing database schema...")
        start_time = time.time()
        create_tables()
        duration_ms = (time.time() - start_time) * 1000
        _log("success", "Database", "Schema initialized successfully", duration_ms=duration_ms)
        return True, "Database schema initialized successfully!"
    except Exception as e:
        _log("error", "Database", f"Schema initialization failed: {str(e)}")
        return False, f"Failed to initialize schema: {str(e)}"


def check_tables_exist() -> tuple[bool, list[str]]:
    """
    Check if database tables exist.

    Returns:
        Tuple of (tables_exist: bool, list of table names)
    """
    try:
        from app.core import models  # noqa: F401

        engine = get_engine()
        from sqlalchemy import inspect

        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        # Expected tables from our models
        expected_tables = [
            "user_profiles",
            "projects",
            "project_contexts",
            "nodes",
            "node_versions",
            "draft_meta",
            "rant_summaries",
            "chat_sessions",
            "chat_messages",
            "baton_snapshots",
            "settings",
            # Roundtable Coder tables
            "roundtable_sessions",
            "roundtable_rounds",
            "roundtable_agents",
            "roundtable_responses",
        ]

        return len(existing_tables) > 0, existing_tables
    except Exception as e:
        return False, []

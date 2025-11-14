"""
conftest.py
-----------
Pytest configuration and shared fixtures for all tests.
"""

# IMPORTANT: Set DATABASE_URL before any other imports
# This prevents database.py from crashing when app is imported in API tests
import os
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/hris_test")

import pytest
from sqlalchemy import create_engine, Table, Column, String
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
from models.BaseModel import Base

# Import only AuditLog model for service tests
from models.AuditLogModel import AuditLog


@pytest.fixture(scope="function")
def db_engine():
    """
    Create an in-memory SQLite database engine for testing.
    Scope: function - each test gets a fresh database.

    Note: Creates a minimal 'users' table to satisfy foreign key constraint
    in audit_log table, without importing complex Employee/Department/Team models.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)

    # Create a minimal users table to satisfy FK constraint
    # This avoids importing complex models with relationship issues
    if "users" not in Base.metadata.tables:
        Table(
            "users",
            Base.metadata,
            Column("id", UUID(as_uuid=True), primary_key=True),
            Column("email", String, unique=True),
            extend_existing=True,
        )

    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """
    Create a database session for testing.
    Automatically rolls back after each test to maintain isolation.
    """
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()

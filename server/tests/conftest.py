"""
conftest.py
-----------
Pytest configuration and shared fixtures for all tests.
"""

# IMPORTANT: Set environment variables before any other imports
# This prevents crashes when app is imported in API tests
import os
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/hris_test")
os.environ.setdefault("WORKOS_API_KEY", "sk_test_dummy_key_for_testing")
os.environ.setdefault("WORKOS_CLIENT_ID", "client_test_dummy_id_for_testing")
os.environ.setdefault("WORKOS_COOKIE_PASSWORD", "dummy_cookie_password_for_testing_12345678")
os.environ.setdefault("WORKOS_REDIRECT_URI", "http://localhost:8000/auth/callback")
os.environ.setdefault("WORKOS_ORG_ID", "org_test_dummy_org_for_testing")
os.environ.setdefault("FRONTEND_URL", "http://localhost:5173")

import pytest
from sqlalchemy import create_engine, Table, Column, String
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from models.BaseModel import Base

# Import only AuditLog model for service tests
from models.AuditLogModel import AuditLog

# Import for authentication mocking
from core.dependencies import AuthenticatedUser


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


@pytest.fixture(scope="function")
def test_admin_user():
    """
    Create a mock admin user for API testing.
    This bypasses WorkOS authentication and returns an AuthenticatedUser
    with admin role for testing protected endpoints.
    """
    return AuthenticatedUser(
        id=uuid4(),
        workos_user_id="test_workos_admin_123",
        email="test.admin@example.com",
        name="Test Admin User",
        organization_id="test_org_id",
        role="admin",
        employee_id=None
    )

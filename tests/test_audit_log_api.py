"""
test_audit_log_api.py
---------------------
Integration tests for AuditLog API endpoints.

Testing Strategy:
1. Use FastAPI TestClient for full HTTP request/response testing
2. Test both successful responses and error cases
3. Validate response schemas and status codes
4. Test query parameter validation and filtering
5. Use real database (in-memory SQLite) for integration testing
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Table, Column, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.pool import StaticPool

from app import app
from models.BaseModel import Base
from models.AuditLogModel import AuditLog, EntityType, ChangeType
from core.dependencies import get_db

# Import all models to ensure they're registered with SQLAlchemy
# This is needed because app.py imports routes that reference these models
from models.UserModel import User
from models.EmployeeModel import Employee
from models.DepartmentModel import Department
from models.TeamModel import Team


@pytest.fixture(scope="function")
def test_db_engine():
    """Create an in-memory test database engine."""
    # Use StaticPool to ensure all connections share the same in-memory database
    # Use check_same_thread=False for SQLite to work with TestClient's threading
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    # Create all tables from imported models
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create a test database session."""
    TestSessionLocal = sessionmaker(bind=test_db_engine)
    session = TestSessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="function")
def client(test_db_session):
    """
    Create a FastAPI TestClient with dependency override.
    Injects test database session into all endpoints.
    """
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass  # Session cleanup handled by test_db_session fixture

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_audit_logs(test_db_session):
    """Create sample audit logs for testing list operations."""
    user_id_1 = uuid4()
    user_id_2 = uuid4()
    entity_id_1 = uuid4()
    entity_id_2 = uuid4()

    logs = [
        AuditLog(
            entity_type=EntityType.EMPLOYEE,
            entity_id=entity_id_1,
            change_type=ChangeType.CREATE,
            changed_by_user_id=user_id_1,
            new_state={"name": "John Doe", "department": "Engineering"},
        ),
        AuditLog(
            entity_type=EntityType.EMPLOYEE,
            entity_id=entity_id_1,
            change_type=ChangeType.UPDATE,
            changed_by_user_id=user_id_1,
            previous_state={"name": "John Doe", "department": "Engineering"},
            new_state={"name": "John Doe", "department": "Sales"},
        ),
        AuditLog(
            entity_type=EntityType.DEPARTMENT,
            entity_id=entity_id_2,
            change_type=ChangeType.CREATE,
            changed_by_user_id=user_id_2,
            new_state={"name": "Engineering"},
        ),
        AuditLog(
            entity_type=EntityType.DEPARTMENT,
            entity_id=entity_id_2,
            change_type=ChangeType.DELETE,
            changed_by_user_id=user_id_2,
            previous_state={"name": "Engineering"},
        ),
        AuditLog(
            entity_type=EntityType.TEAM,
            entity_id=uuid4(),
            change_type=ChangeType.CREATE,
            changed_by_user_id=user_id_1,
            new_state={"name": "Backend Team"},
        ),
    ]

    for log in logs:
        test_db_session.add(log)
    test_db_session.commit()

    return {
        "logs": logs,
        "user_id_1": user_id_1,
        "user_id_2": user_id_2,
        "entity_id_1": entity_id_1,
        "entity_id_2": entity_id_2,
    }


class TestListAuditLogsEndpoint:
    """Tests for GET /audit-logs endpoint"""

    def test_list_all_audit_logs(self, client, sample_audit_logs):
        """Should return paginated list of all audit logs."""
        # Act
        response = client.get("/audit-logs")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

        assert data["total"] == 5
        assert len(data["items"]) == 5
        assert data["limit"] == 25
        assert data["offset"] == 0

    def test_list_audit_logs_response_schema(self, client, sample_audit_logs):
        """Should return items with correct schema (no state fields in list)."""
        # Act
        response = client.get("/audit-logs")

        # Assert
        assert response.status_code == 200
        data = response.json()

        first_item = data["items"][0]
        assert "id" in first_item
        assert "entity_type" in first_item
        assert "entity_id" in first_item
        assert "change_type" in first_item
        assert "changed_by_user_id" in first_item
        assert "created_at" in first_item

        # List items should NOT include state fields
        assert "previous_state" not in first_item
        assert "new_state" not in first_item
        assert "updated_at" not in first_item

    def test_list_audit_logs_filter_by_entity_type(self, client, sample_audit_logs):
        """Should filter audit logs by entity_type query parameter."""
        # Act
        response = client.get("/audit-logs?entity_type=EMPLOYEE")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert all(item["entity_type"] == "EMPLOYEE" for item in data["items"])

    def test_list_audit_logs_filter_by_entity_id(self, client, sample_audit_logs):
        """Should filter audit logs by entity_id query parameter."""
        # Arrange
        entity_id = sample_audit_logs["entity_id_1"]

        # Act
        response = client.get(f"/audit-logs?entity_id={entity_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert all(item["entity_id"] == str(entity_id) for item in data["items"])

    def test_list_audit_logs_filter_by_change_type(self, client, sample_audit_logs):
        """Should filter audit logs by change_type query parameter."""
        # Act
        response = client.get("/audit-logs?change_type=CREATE")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 3
        assert len(data["items"]) == 3
        assert all(item["change_type"] == "CREATE" for item in data["items"])

    def test_list_audit_logs_filter_by_user_id(self, client, sample_audit_logs):
        """Should filter audit logs by changed_by_user_id query parameter."""
        # Arrange
        user_id = sample_audit_logs["user_id_1"]

        # Act
        response = client.get(f"/audit-logs?changed_by_user_id={user_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 3
        assert len(data["items"]) == 3
        assert all(item["changed_by_user_id"] == str(user_id) for item in data["items"])

    def test_list_audit_logs_filter_by_date_range(self, client, sample_audit_logs):
        """Should filter audit logs by date_from and date_to query parameters."""
        # Arrange
        now = datetime.now()
        date_from = (now - timedelta(days=1)).isoformat()
        date_to = (now + timedelta(days=1)).isoformat()

        # Act
        response = client.get(f"/audit-logs?date_from={date_from}&date_to={date_to}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        # All test logs should be within this range
        assert data["total"] == 5

    def test_list_audit_logs_pagination_limit(self, client, sample_audit_logs):
        """Should respect limit query parameter for pagination."""
        # Act
        response = client.get("/audit-logs?limit=2")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 5  # Total unchanged
        assert len(data["items"]) == 2  # Only 2 returned
        assert data["limit"] == 2

    def test_list_audit_logs_pagination_offset(self, client, sample_audit_logs):
        """Should respect offset query parameter for pagination."""
        # Act
        response = client.get("/audit-logs?limit=2&offset=3")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["offset"] == 3

    def test_list_audit_logs_order_asc(self, client, sample_audit_logs):
        """Should order results ascending when order=asc."""
        # Act
        response = client.get("/audit-logs?order=asc")

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify ascending order by created_at
        items = data["items"]
        for i in range(len(items) - 1):
            current_time = datetime.fromisoformat(items[i]["created_at"].replace("Z", "+00:00"))
            next_time = datetime.fromisoformat(items[i + 1]["created_at"].replace("Z", "+00:00"))
            assert current_time <= next_time

    def test_list_audit_logs_order_desc(self, client, sample_audit_logs):
        """Should order results descending when order=desc (default)."""
        # Act
        response = client.get("/audit-logs?order=desc")

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify descending order by created_at
        items = data["items"]
        for i in range(len(items) - 1):
            current_time = datetime.fromisoformat(items[i]["created_at"].replace("Z", "+00:00"))
            next_time = datetime.fromisoformat(items[i + 1]["created_at"].replace("Z", "+00:00"))
            assert current_time >= next_time

    def test_list_audit_logs_multiple_filters(self, client, sample_audit_logs):
        """Should apply multiple filters simultaneously."""
        # Arrange
        entity_id = sample_audit_logs["entity_id_1"]
        user_id = sample_audit_logs["user_id_1"]

        # Act
        response = client.get(
            f"/audit-logs?entity_type=EMPLOYEE&entity_id={entity_id}"
            f"&change_type=UPDATE&changed_by_user_id={user_id}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 1
        assert len(data["items"]) == 1
        item = data["items"][0]
        assert item["entity_type"] == "EMPLOYEE"
        assert item["entity_id"] == str(entity_id)
        assert item["change_type"] == "UPDATE"
        assert item["changed_by_user_id"] == str(user_id)

    def test_list_audit_logs_empty_result(self, client, sample_audit_logs):
        """Should return empty list when no logs match filters."""
        # Arrange
        fake_id = uuid4()

        # Act
        response = client.get(f"/audit-logs?entity_id={fake_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_list_audit_logs_invalid_entity_type(self, client):
        """Should return 422 for invalid entity_type."""
        # Act
        response = client.get("/audit-logs?entity_type=INVALID")

        # Assert
        assert response.status_code == 422

    def test_list_audit_logs_invalid_change_type(self, client):
        """Should return 422 for invalid change_type."""
        # Act
        response = client.get("/audit-logs?change_type=INVALID")

        # Assert
        assert response.status_code == 422

    def test_list_audit_logs_invalid_uuid(self, client):
        """Should return 422 for invalid UUID format."""
        # Act
        response = client.get("/audit-logs?entity_id=not-a-uuid")

        # Assert
        assert response.status_code == 422

    def test_list_audit_logs_invalid_limit_too_high(self, client):
        """Should return 422 when limit exceeds maximum (100)."""
        # Act
        response = client.get("/audit-logs?limit=101")

        # Assert
        assert response.status_code == 422

    def test_list_audit_logs_invalid_limit_zero(self, client):
        """Should return 422 when limit is less than 1."""
        # Act
        response = client.get("/audit-logs?limit=0")

        # Assert
        assert response.status_code == 422

    def test_list_audit_logs_invalid_offset_negative(self, client):
        """Should return 422 when offset is negative."""
        # Act
        response = client.get("/audit-logs?offset=-1")

        # Assert
        assert response.status_code == 422


class TestGetAuditLogEndpoint:
    """Tests for GET /audit-logs/{log_id} endpoint"""

    def test_get_audit_log_success(self, client, sample_audit_logs):
        """Should return detailed audit log including state fields."""
        # Arrange
        log_id = sample_audit_logs["logs"][1].id  # Log with both states

        # Act
        response = client.get(f"/audit-logs/{log_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(log_id)
        assert data["entity_type"] == "EMPLOYEE"
        assert data["change_type"] == "UPDATE"

        # Detail endpoint should include state fields
        assert "previous_state" in data
        assert "new_state" in data
        assert "updated_at" in data

        assert data["previous_state"] == {"name": "John Doe", "department": "Engineering"}
        assert data["new_state"] == {"name": "John Doe", "department": "Sales"}

    def test_get_audit_log_with_null_states(self, client, sample_audit_logs):
        """Should handle null previous_state and new_state."""
        # Arrange
        log_id = sample_audit_logs["logs"][0].id  # CREATE log (no previous_state)

        # Act
        response = client.get(f"/audit-logs/{log_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(log_id)
        assert data["new_state"] is not None
        assert data["previous_state"] is None

    def test_get_audit_log_not_found(self, client):
        """Should return 404 for non-existent audit log ID."""
        # Arrange
        fake_id = uuid4()

        # Act
        response = client.get(f"/audit-logs/{fake_id}")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Audit log not found"

    def test_get_audit_log_invalid_uuid(self, client):
        """Should return 422 for invalid UUID format."""
        # Act
        response = client.get("/audit-logs/not-a-uuid")

        # Assert
        assert response.status_code == 422


class TestHealthEndpoints:
    """Tests for health check endpoints (sanity check)"""

    def test_root_endpoint(self, client):
        """Should return welcome message."""
        # Act
        response = client.get("/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "HRIS" in data["message"]

    def test_health_check_endpoint(self, client):
        """Should return healthy status."""
        # Act
        response = client.get("/health")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

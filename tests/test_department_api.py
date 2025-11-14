"""
test_department_api.py
-----------------------
Integration tests for Department API endpoints.

Testing Strategy:
1. Use FastAPI TestClient for full HTTP request/response testing
2. Test CRUD operations on departments
3. Test pagination for teams and employees
4. Test response schemas
5. Test validation and error handling
6. Use real database (in-memory SQLite) for integration testing
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import app
from models.BaseModel import Base
from models.DepartmentModel import Department
from models.TeamModel import Team
from models.EmployeeModel import Employee, EmployeeStatus
from models.UserModel import User
from core.dependencies import get_db


@pytest.fixture(scope="function")
def test_db_engine():
    """Create an in-memory test database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

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
    """Create a FastAPI TestClient with dependency override."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_departments(test_db_session):
    """Create sample departments for testing."""
    departments = [
        Department(name="Engineering"),
        Department(name="Sales"),
        Department(name="HR"),
    ]
    test_db_session.add_all(departments)
    test_db_session.commit()
    return departments


@pytest.fixture
def sample_department_with_teams(test_db_session):
    """Create a department with multiple teams."""
    dept = Department(name="Engineering")
    test_db_session.add(dept)
    test_db_session.flush()

    teams = [
        Team(name="Backend Team", department_id=dept.id),
        Team(name="Frontend Team", department_id=dept.id),
        Team(name="DevOps Team", department_id=dept.id),
        Team(name="QA Team", department_id=dept.id),
    ]
    test_db_session.add_all(teams)
    test_db_session.commit()

    return {"department": dept, "teams": teams}


@pytest.fixture
def sample_department_with_employees(test_db_session):
    """Create a department with multiple employees."""
    dept = Department(name="Sales")
    test_db_session.add(dept)
    test_db_session.flush()

    employees = [
        Employee(
            name="Alice Anderson",
            email="alice@example.com",
            status=EmployeeStatus.ACTIVE,
            department_id=dept.id,
        ),
        Employee(
            name="Bob Brown",
            email="bob@example.com",
            status=EmployeeStatus.ACTIVE,
            department_id=dept.id,
        ),
        Employee(
            name="Charlie Chen",
            email="charlie@example.com",
            status=EmployeeStatus.ON_LEAVE,
            department_id=dept.id,
        ),
    ]
    test_db_session.add_all(employees)
    test_db_session.commit()

    return {"department": dept, "employees": employees}


class TestCreateDepartmentEndpoint:
    """Tests for POST /departments endpoint."""

    def test_create_department_success(self, client):
        """Should create a new department."""
        # Arrange
        create_data = {"name": "Engineering"}

        # Act
        response = client.post("/departments", json=create_data)

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert "id" in data
        assert data["name"] == "Engineering"
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_department_response_schema(self, client):
        """Should return DepartmentDetail schema."""
        # Arrange
        create_data = {"name": "Engineering"}

        # Act
        response = client.post("/departments", json=create_data)

        # Assert
        assert response.status_code == 201
        data = response.json()

        # Check all DepartmentDetail fields
        assert "id" in data
        assert "name" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert len(data) == 4

    def test_create_department_persists_to_database(self, client):
        """Should persist department to database."""
        # Arrange
        create_data = {"name": "Engineering"}

        # Act
        response = client.post("/departments", json=create_data)
        assert response.status_code == 201
        department_id = response.json()["id"]

        # Assert - Verify by fetching
        get_response = client.get(f"/departments/{department_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "Engineering"

    def test_create_department_duplicate_name(self, client, sample_departments):
        """Should return 409 for duplicate department name."""
        # Arrange
        create_data = {"name": "Engineering"}  # Already exists

        # Act
        response = client.post("/departments", json=create_data)

        # Assert
        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
        assert "already exists" in data["detail"]

    def test_create_department_empty_name(self, client):
        """Should return 422 for empty name."""
        # Arrange
        create_data = {"name": ""}

        # Act
        response = client.post("/departments", json=create_data)

        # Assert
        assert response.status_code == 422

    def test_create_department_missing_name(self, client):
        """Should return 422 for missing name field."""
        # Arrange
        create_data = {}

        # Act
        response = client.post("/departments", json=create_data)

        # Assert
        assert response.status_code == 422

    def test_create_department_creates_audit_log(self, client, test_db_session):
        """Should create audit log entry."""
        # Arrange
        from models.AuditLogModel import AuditLog, EntityType, ChangeType
        from uuid import UUID
        create_data = {"name": "Engineering"}

        # Act
        response = client.post("/departments", json=create_data)
        assert response.status_code == 201
        department_id = UUID(response.json()["id"])

        # Assert - Check audit log
        audit_logs = test_db_session.query(AuditLog).filter(
            AuditLog.entity_type == EntityType.DEPARTMENT,
            AuditLog.entity_id == department_id,
            AuditLog.change_type == ChangeType.CREATE,
        ).all()

        assert len(audit_logs) == 1
        log = audit_logs[0]
        assert log.previous_state is None
        assert log.new_state["name"] == "Engineering"


class TestGetDepartmentEndpoint:
    """Tests for GET /departments/{department_id} endpoint."""

    def test_get_department_success(self, client, sample_departments):
        """Should return department by ID."""
        # Arrange
        department_id = str(sample_departments[0].id)

        # Act
        response = client.get(f"/departments/{department_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == department_id
        assert data["name"] == "Engineering"

    def test_get_department_response_schema(self, client, sample_departments):
        """Should return DepartmentDetail schema."""
        # Arrange
        department_id = str(sample_departments[0].id)

        # Act
        response = client.get(f"/departments/{department_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Check all fields
        assert "id" in data
        assert "name" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_department_not_found(self, client):
        """Should return 404 for non-existent department."""
        # Arrange
        from uuid import uuid4
        fake_id = str(uuid4())

        # Act
        response = client.get(f"/departments/{fake_id}")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Department not found"

    def test_get_department_invalid_uuid(self, client):
        """Should return 422 for invalid UUID format."""
        # Act
        response = client.get("/departments/not-a-uuid")

        # Assert
        assert response.status_code == 422

    def test_get_department_uuid_format(self, client, sample_departments):
        """Should return valid UUID string in results."""
        # Arrange
        department_id = str(sample_departments[0].id)

        # Act
        response = client.get(f"/departments/{department_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        assert len(data["id"]) == 36
        assert data["id"].count("-") == 4

    def test_get_department_datetime_format(self, client, sample_departments):
        """Should return ISO-formatted datetime strings."""
        # Arrange
        department_id = str(sample_departments[0].id)

        # Act
        response = client.get(f"/departments/{department_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Check created_at and updated_at are present and formatted
        assert "created_at" in data
        assert "updated_at" in data
        assert isinstance(data["created_at"], str)
        assert isinstance(data["updated_at"], str)


class TestUpdateDepartmentEndpoint:
    """Tests for PATCH /departments/{department_id} endpoint."""

    def test_update_department_success(self, client, sample_departments):
        """Should update department name."""
        # Arrange
        department_id = str(sample_departments[0].id)
        update_data = {"name": "Engineering & Technology"}

        # Act
        response = client.patch(f"/departments/{department_id}", json=update_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == department_id
        assert data["name"] == "Engineering & Technology"

    def test_update_department_response_schema(self, client, sample_departments):
        """Should return DepartmentDetail schema."""
        # Arrange
        department_id = str(sample_departments[0].id)
        update_data = {"name": "New Name"}

        # Act
        response = client.patch(f"/departments/{department_id}", json=update_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Check all DepartmentDetail fields
        assert "id" in data
        assert "name" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_update_department_persists_changes(self, client, sample_departments):
        """Should persist changes to database."""
        # Arrange
        department_id = str(sample_departments[0].id)
        update_data = {"name": "Engineering & Technology"}

        # Act - Update
        response = client.patch(f"/departments/{department_id}", json=update_data)
        assert response.status_code == 200

        # Assert - Verify changes persisted by fetching again
        get_response = client.get(f"/departments/{department_id}")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["name"] == "Engineering & Technology"

    def test_update_department_not_found(self, client):
        """Should return 404 for non-existent department."""
        # Arrange
        from uuid import uuid4
        fake_id = str(uuid4())
        update_data = {"name": "New Name"}

        # Act
        response = client.patch(f"/departments/{fake_id}", json=update_data)

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Department not found"

    def test_update_department_invalid_uuid(self, client):
        """Should return 422 for invalid UUID format."""
        # Arrange
        update_data = {"name": "New Name"}

        # Act
        response = client.patch("/departments/not-a-uuid", json=update_data)

        # Assert
        assert response.status_code == 422

    def test_update_department_empty_name(self, client, sample_departments):
        """Should return 422 for empty name."""
        # Arrange
        department_id = str(sample_departments[0].id)
        update_data = {"name": ""}

        # Act
        response = client.patch(f"/departments/{department_id}", json=update_data)

        # Assert
        assert response.status_code == 422

    def test_update_department_duplicate_name(self, client, sample_departments):
        """Should return 409 for duplicate name (unique constraint violation)."""
        # Arrange
        department_id = str(sample_departments[0].id)
        update_data = {"name": "Sales"}  # Already exists

        # Act
        response = client.patch(f"/departments/{department_id}", json=update_data)

        # Assert
        assert response.status_code == 409
        data = response.json()
        assert "already exists" in data["detail"]

    def test_update_department_creates_audit_log(self, client, sample_departments, test_db_session):
        """Should create audit log entry."""
        # Arrange
        from models.AuditLogModel import AuditLog, EntityType, ChangeType
        from uuid import UUID
        department_id_str = str(sample_departments[0].id)
        department_id = UUID(department_id_str)
        update_data = {"name": "Engineering & Technology"}

        # Act
        response = client.patch(f"/departments/{department_id_str}", json=update_data)
        assert response.status_code == 200

        # Assert - Check audit log
        audit_logs = test_db_session.query(AuditLog).filter(
            AuditLog.entity_type == EntityType.DEPARTMENT,
            AuditLog.entity_id == department_id,
            AuditLog.change_type == ChangeType.UPDATE,
        ).all()

        assert len(audit_logs) == 1
        log = audit_logs[0]
        assert log.previous_state["name"] == "Engineering"
        assert log.new_state["name"] == "Engineering & Technology"


class TestDeleteDepartmentEndpoint:
    """Tests for DELETE /departments/{department_id} endpoint."""

    def test_delete_department_success(self, client, sample_departments):
        """Should delete department."""
        # Arrange
        department_id = str(sample_departments[0].id)

        # Act
        response = client.delete(f"/departments/{department_id}")

        # Assert
        assert response.status_code == 204
        assert response.text == ""  # No content

        # Verify deletion
        get_response = client.get(f"/departments/{department_id}")
        assert get_response.status_code == 404

    def test_delete_department_not_found(self, client):
        """Should return 404 for non-existent department."""
        # Arrange
        from uuid import uuid4
        fake_id = str(uuid4())

        # Act
        response = client.delete(f"/departments/{fake_id}")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Department not found"

    def test_delete_department_invalid_uuid(self, client):
        """Should return 422 for invalid UUID format."""
        # Act
        response = client.delete("/departments/not-a-uuid")

        # Assert
        assert response.status_code == 422

    def test_delete_department_creates_audit_log(self, client, sample_departments, test_db_session):
        """Should create audit log entry."""
        # Arrange
        from models.AuditLogModel import AuditLog, EntityType, ChangeType
        from uuid import UUID
        department_id_str = str(sample_departments[0].id)
        department_id = UUID(department_id_str)
        department_name = sample_departments[0].name

        # Act
        response = client.delete(f"/departments/{department_id_str}")
        assert response.status_code == 204

        # Assert - Check audit log
        audit_logs = test_db_session.query(AuditLog).filter(
            AuditLog.entity_type == EntityType.DEPARTMENT,
            AuditLog.entity_id == department_id,
            AuditLog.change_type == ChangeType.DELETE,
        ).all()

        assert len(audit_logs) == 1
        log = audit_logs[0]
        assert log.previous_state["name"] == department_name
        assert log.new_state is None

    def test_delete_department_sets_null_on_related_entities(self, client, test_db_session):
        """Should set department_id to NULL on related employees and teams."""
        # Arrange - Create department with employee and team
        dept = Department(name="Test Department")
        test_db_session.add(dept)
        test_db_session.flush()

        employee = Employee(
            name="Test Employee",
            email="test@example.com",
            status=EmployeeStatus.ACTIVE,
            department_id=dept.id,
        )
        team = Team(name="Test Team", department_id=dept.id)
        test_db_session.add_all([employee, team])
        test_db_session.commit()

        employee_id = employee.id
        team_id = team.id
        department_id = str(dept.id)

        # Act - Delete department
        response = client.delete(f"/departments/{department_id}")
        assert response.status_code == 204

        # Assert - Employee and team should have NULL department_id
        test_db_session.expire_all()  # Refresh from database
        updated_employee = test_db_session.get(Employee, employee_id)
        updated_team = test_db_session.get(Team, team_id)

        assert updated_employee.department_id is None
        assert updated_team.department_id is None


class TestListDepartmentTeamsEndpoint:
    """Tests for GET /departments/{department_id}/teams endpoint."""

    def test_list_department_teams_success(self, client, sample_department_with_teams):
        """Should return paginated list of teams."""
        # Arrange
        department_id = str(sample_department_with_teams["department"].id)

        # Act
        response = client.get(f"/departments/{department_id}/teams")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

        assert data["total"] == 4
        assert len(data["items"]) == 4
        assert data["limit"] == 25
        assert data["offset"] == 0

    def test_list_department_teams_response_schema(self, client, sample_department_with_teams):
        """Should return items with correct schema (id and name only)."""
        # Arrange
        department_id = str(sample_department_with_teams["department"].id)

        # Act
        response = client.get(f"/departments/{department_id}/teams")

        # Assert
        assert response.status_code == 200
        data = response.json()

        first_item = data["items"][0]
        assert "id" in first_item
        assert "name" in first_item
        assert len(first_item) == 2  # Only id and name fields

    def test_list_department_teams_alphabetical_order(self, client, sample_department_with_teams):
        """Should return teams ordered alphabetically by name."""
        # Arrange
        department_id = str(sample_department_with_teams["department"].id)

        # Act
        response = client.get(f"/departments/{department_id}/teams")

        # Assert
        assert response.status_code == 200
        data = response.json()

        names = [item["name"] for item in data["items"]]
        assert names == ["Backend Team", "DevOps Team", "Frontend Team", "QA Team"]

    def test_list_department_teams_pagination_limit(self, client, sample_department_with_teams):
        """Should respect limit parameter."""
        # Arrange
        department_id = str(sample_department_with_teams["department"].id)

        # Act
        response = client.get(f"/departments/{department_id}/teams?limit=2")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 4  # Total unchanged
        assert len(data["items"]) == 2  # Only 2 returned
        assert data["limit"] == 2

    def test_list_department_teams_pagination_offset(self, client, sample_department_with_teams):
        """Should respect offset parameter."""
        # Arrange
        department_id = str(sample_department_with_teams["department"].id)

        # Act
        response = client.get(f"/departments/{department_id}/teams?limit=2&offset=2")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 4
        assert len(data["items"]) == 2
        assert data["offset"] == 2
        assert data["items"][0]["name"] == "Frontend Team"

    def test_list_department_teams_empty_department(self, client, sample_departments):
        """Should return empty items for department with no teams."""
        # Arrange - Use HR department which has no teams
        department_id = str(sample_departments[2].id)

        # Act
        response = client.get(f"/departments/{department_id}/teams")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_list_department_teams_invalid_limit(self, client, sample_department_with_teams):
        """Should return 422 for invalid limit."""
        # Arrange
        department_id = str(sample_department_with_teams["department"].id)

        # Act
        response = client.get(f"/departments/{department_id}/teams?limit=0")

        # Assert
        assert response.status_code == 422

    def test_list_department_teams_invalid_offset(self, client, sample_department_with_teams):
        """Should return 422 for invalid offset."""
        # Arrange
        department_id = str(sample_department_with_teams["department"].id)

        # Act
        response = client.get(f"/departments/{department_id}/teams?offset=-1")

        # Assert
        assert response.status_code == 422


class TestListDepartmentEmployeesEndpoint:
    """Tests for GET /departments/{department_id}/employees endpoint."""

    def test_list_department_employees_success(self, client, sample_department_with_employees):
        """Should return paginated list of employees."""
        # Arrange
        department_id = str(sample_department_with_employees["department"].id)

        # Act
        response = client.get(f"/departments/{department_id}/employees")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

        assert data["total"] == 3
        assert len(data["items"]) == 3
        assert data["limit"] == 25
        assert data["offset"] == 0

    def test_list_department_employees_response_schema(self, client, sample_department_with_employees):
        """Should return items with correct schema (id and name only)."""
        # Arrange
        department_id = str(sample_department_with_employees["department"].id)

        # Act
        response = client.get(f"/departments/{department_id}/employees")

        # Assert
        assert response.status_code == 200
        data = response.json()

        first_item = data["items"][0]
        assert "id" in first_item
        assert "name" in first_item
        assert len(first_item) == 2  # Only id and name fields

    def test_list_department_employees_alphabetical_order(self, client, sample_department_with_employees):
        """Should return employees ordered alphabetically by name."""
        # Arrange
        department_id = str(sample_department_with_employees["department"].id)

        # Act
        response = client.get(f"/departments/{department_id}/employees")

        # Assert
        assert response.status_code == 200
        data = response.json()

        names = [item["name"] for item in data["items"]]
        assert names == ["Alice Anderson", "Bob Brown", "Charlie Chen"]

    def test_list_department_employees_pagination_limit(self, client, sample_department_with_employees):
        """Should respect limit parameter."""
        # Arrange
        department_id = str(sample_department_with_employees["department"].id)

        # Act
        response = client.get(f"/departments/{department_id}/employees?limit=2")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 3  # Total unchanged
        assert len(data["items"]) == 2  # Only 2 returned
        assert data["limit"] == 2

    def test_list_department_employees_pagination_offset(self, client, sample_department_with_employees):
        """Should respect offset parameter."""
        # Arrange
        department_id = str(sample_department_with_employees["department"].id)

        # Act
        response = client.get(f"/departments/{department_id}/employees?limit=2&offset=1")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 3
        assert len(data["items"]) == 2
        assert data["offset"] == 1
        assert data["items"][0]["name"] == "Bob Brown"

    def test_list_department_employees_empty_department(self, client, sample_departments):
        """Should return empty items for department with no employees."""
        # Arrange - Use HR department which has no employees
        department_id = str(sample_departments[2].id)

        # Act
        response = client.get(f"/departments/{department_id}/employees")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_list_department_employees_invalid_limit(self, client, sample_department_with_employees):
        """Should return 422 for invalid limit."""
        # Arrange
        department_id = str(sample_department_with_employees["department"].id)

        # Act
        response = client.get(f"/departments/{department_id}/employees?limit=101")

        # Assert
        assert response.status_code == 422

    def test_list_department_employees_invalid_offset(self, client, sample_department_with_employees):
        """Should return 422 for invalid offset."""
        # Arrange
        department_id = str(sample_department_with_employees["department"].id)

        # Act
        response = client.get(f"/departments/{department_id}/employees?offset=-1")

        # Assert
        assert response.status_code == 422

    def test_list_department_employees_includes_all_statuses(self, client, sample_department_with_employees):
        """Should include employees regardless of status."""
        # Arrange
        department_id = str(sample_department_with_employees["department"].id)

        # Act
        response = client.get(f"/departments/{department_id}/employees")

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Should include both ACTIVE and ON_LEAVE employees
        assert data["total"] == 3
        assert len(data["items"]) == 3

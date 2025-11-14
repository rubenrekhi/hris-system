"""
test_employee_api.py
--------------------
Integration tests for Employee API endpoints.

Testing Strategy:
1. Use FastAPI TestClient for full HTTP request/response testing
2. Test GET /employees endpoint with various filters
3. Test pagination functionality
4. Test query parameter validation
5. Test response schemas
6. Test search functionality
7. Use real database (in-memory SQLite) for integration testing
"""

import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import app
from models.BaseModel import Base
from models.EmployeeModel import Employee, EmployeeStatus
from models.DepartmentModel import Department
from models.TeamModel import Team
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
def sample_employee_data(test_db_session):
    """Create sample employee data for testing."""
    # Create departments
    eng_dept = Department(name="Engineering")
    sales_dept = Department(name="Sales")

    test_db_session.add_all([eng_dept, sales_dept])
    test_db_session.flush()

    # Create teams
    backend_team = Team(name="Backend Team", department_id=eng_dept.id)
    frontend_team = Team(name="Frontend Team", department_id=eng_dept.id)
    sales_team = Team(name="Sales Team", department_id=sales_dept.id)

    test_db_session.add_all([backend_team, frontend_team, sales_team])
    test_db_session.flush()

    # Create employees
    employees = [
        Employee(
            name="Alice Anderson",
            email="alice@example.com",
            status=EmployeeStatus.ACTIVE,
            department_id=eng_dept.id,
            team_id=backend_team.id,
            salary=120000,
        ),
        Employee(
            name="Bob Brown",
            email="bob@example.com",
            status=EmployeeStatus.ACTIVE,
            department_id=eng_dept.id,
            team_id=frontend_team.id,
            salary=110000,
        ),
        Employee(
            name="Charlie Chen",
            email="charlie@example.com",
            status=EmployeeStatus.ON_LEAVE,
            department_id=eng_dept.id,
            team_id=backend_team.id,
            salary=115000,
        ),
        Employee(
            name="Diana Davis",
            email="diana@example.com",
            status=EmployeeStatus.ACTIVE,
            department_id=sales_dept.id,
            team_id=sales_team.id,
            salary=95000,
        ),
        Employee(
            name="Eve Evans",
            email="eve@example.com",
            status=EmployeeStatus.ACTIVE,
            department_id=sales_dept.id,
            team_id=sales_team.id,
            salary=90000,
        ),
    ]

    test_db_session.add_all(employees)
    test_db_session.commit()

    return {
        "departments": {"eng": eng_dept, "sales": sales_dept},
        "teams": {"backend": backend_team, "frontend": frontend_team, "sales": sales_team},
        "employees": employees,
    }


class TestListEmployeesEndpoint:
    """Tests for GET /employees endpoint."""

    def test_list_all_employees(self, client, sample_employee_data):
        """Should return paginated list of all employees."""
        # Act
        response = client.get("/employees")

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

    def test_list_employees_response_schema(self, client, sample_employee_data):
        """Should return items with correct schema (id and name only)."""
        # Act
        response = client.get("/employees")

        # Assert
        assert response.status_code == 200
        data = response.json()

        first_item = data["items"][0]
        # Check required fields
        assert "id" in first_item
        assert "name" in first_item
        assert "email" in first_item
        assert "title" in first_item
        assert "status" in first_item
        assert "department_id" in first_item
        assert "team_id" in first_item
        assert "department_name" in first_item
        assert "team_name" in first_item
        assert len(first_item) == 9  # All EmployeeListItem fields

    def test_list_employees_alphabetical_order(self, client, sample_employee_data):
        """Should return employees ordered alphabetically by name."""
        # Act
        response = client.get("/employees")

        # Assert
        assert response.status_code == 200
        data = response.json()

        names = [item["name"] for item in data["items"]]
        assert names == ["Alice Anderson", "Bob Brown", "Charlie Chen", "Diana Davis", "Eve Evans"]

    def test_list_employees_filter_by_team(self, client, sample_employee_data):
        """Should filter employees by team_id."""
        # Arrange
        backend_team_id = str(sample_employee_data["teams"]["backend"].id)

        # Act
        response = client.get(f"/employees?team_id={backend_team_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_list_employees_filter_by_department(self, client, sample_employee_data):
        """Should filter employees by department_id."""
        # Arrange
        eng_dept_id = str(sample_employee_data["departments"]["eng"].id)

        # Act
        response = client.get(f"/employees?department_id={eng_dept_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_list_employees_filter_by_status_active(self, client, sample_employee_data):
        """Should filter employees by ACTIVE status."""
        # Act
        response = client.get("/employees?status=ACTIVE")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 4
        assert len(data["items"]) == 4

    def test_list_employees_filter_by_status_on_leave(self, client, sample_employee_data):
        """Should filter employees by ON_LEAVE status."""
        # Act
        response = client.get("/employees?status=ON_LEAVE")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Charlie Chen"

    def test_list_employees_filter_by_min_salary(self, client, sample_employee_data):
        """Should filter employees by minimum salary."""
        # Act
        response = client.get("/employees?min_salary=100000")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_list_employees_filter_by_max_salary(self, client, sample_employee_data):
        """Should filter employees by maximum salary."""
        # Act
        response = client.get("/employees?max_salary=95000")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_list_employees_filter_by_salary_range(self, client, sample_employee_data):
        """Should filter employees by salary range."""
        # Act
        response = client.get("/employees?min_salary=100000&max_salary=115000")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_list_employees_search_by_name(self, client, sample_employee_data):
        """Should search employees by name (case-insensitive)."""
        # Act
        response = client.get("/employees?name=alice")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Alice Anderson"

    def test_list_employees_search_by_name_partial(self, client, sample_employee_data):
        """Should search employees by partial name."""
        # Act
        response = client.get("/employees?name=an")

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Should find "Diana Davis" (contains "an")
        assert data["total"] >= 1

    def test_list_employees_search_by_email(self, client, sample_employee_data):
        """Should search employees by email."""
        # Act
        response = client.get("/employees?email=bob@example.com")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Bob Brown"

    def test_list_employees_search_name_and_email(self, client, sample_employee_data):
        """Should search by name OR email."""
        # Act
        response = client.get("/employees?name=alice&email=bob@example.com")

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Should find both Alice (by name) and Bob (by email)
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_list_employees_multiple_filters(self, client, sample_employee_data):
        """Should apply multiple filters simultaneously."""
        # Arrange
        eng_dept_id = str(sample_employee_data["departments"]["eng"].id)

        # Act
        response = client.get(
            f"/employees?department_id={eng_dept_id}&status=ACTIVE&min_salary=110000"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 2  # Alice and Bob
        assert len(data["items"]) == 2

    def test_list_employees_pagination_limit(self, client, sample_employee_data):
        """Should respect limit parameter."""
        # Act
        response = client.get("/employees?limit=2")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 5  # Total unchanged
        assert len(data["items"]) == 2  # Only 2 returned
        assert data["limit"] == 2

    def test_list_employees_pagination_offset(self, client, sample_employee_data):
        """Should respect offset parameter."""
        # Act
        response = client.get("/employees?limit=2&offset=2")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["offset"] == 2
        # Should get 3rd and 4th items
        assert data["items"][0]["name"] == "Charlie Chen"

    def test_list_employees_pagination_offset_beyond_results(self, client, sample_employee_data):
        """Should return empty items when offset exceeds total."""
        # Act
        response = client.get("/employees?offset=100")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 5
        assert len(data["items"]) == 0

    def test_list_employees_no_results(self, client, sample_employee_data):
        """Should return empty items when no matches found."""
        # Act
        response = client.get("/employees?name=nonexistent")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_list_employees_empty_database(self, client):
        """Should return empty results when database is empty."""
        # Act
        response = client.get("/employees")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_list_employees_invalid_team_id(self, client):
        """Should return 422 for invalid team_id format."""
        # Act
        response = client.get("/employees?team_id=not-a-uuid")

        # Assert
        assert response.status_code == 422

    def test_list_employees_invalid_department_id(self, client):
        """Should return 422 for invalid department_id format."""
        # Act
        response = client.get("/employees?department_id=not-a-uuid")

        # Assert
        assert response.status_code == 422

    def test_list_employees_invalid_status(self, client):
        """Should return 422 for invalid status value."""
        # Act
        response = client.get("/employees?status=INVALID")

        # Assert
        assert response.status_code == 422

    def test_list_employees_invalid_limit_too_high(self, client):
        """Should return 422 when limit exceeds maximum (100)."""
        # Act
        response = client.get("/employees?limit=101")

        # Assert
        assert response.status_code == 422

    def test_list_employees_invalid_limit_zero(self, client):
        """Should return 422 when limit is less than 1."""
        # Act
        response = client.get("/employees?limit=0")

        # Assert
        assert response.status_code == 422

    def test_list_employees_invalid_offset_negative(self, client):
        """Should return 422 when offset is negative."""
        # Act
        response = client.get("/employees?offset=-1")

        # Assert
        assert response.status_code == 422

    def test_list_employees_invalid_min_salary_negative(self, client):
        """Should return 422 when min_salary is negative."""
        # Act
        response = client.get("/employees?min_salary=-1000")

        # Assert
        assert response.status_code == 422

    def test_list_employees_invalid_max_salary_negative(self, client):
        """Should return 422 when max_salary is negative."""
        # Act
        response = client.get("/employees?max_salary=-1000")

        # Assert
        assert response.status_code == 422

    def test_list_employees_whitespace_name_trimmed(self, client, sample_employee_data):
        """Should trim whitespace from name parameter."""
        # Act
        response = client.get("/employees?name=%20%20alice%20%20")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 1
        assert data["items"][0]["name"] == "Alice Anderson"

    def test_list_employees_whitespace_email_trimmed(self, client, sample_employee_data):
        """Should trim whitespace from email parameter."""
        # Act
        response = client.get("/employees?email=%20%20bob@example.com%20%20")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 1
        assert data["items"][0]["name"] == "Bob Brown"

    def test_list_employees_case_insensitive_search(self, client, sample_employee_data):
        """Should perform case-insensitive search."""
        # Act
        response_lower = client.get("/employees?name=alice")
        response_upper = client.get("/employees?name=ALICE")

        # Assert
        assert response_lower.status_code == 200
        assert response_upper.status_code == 200

        data_lower = response_lower.json()
        data_upper = response_upper.json()

        assert data_lower["total"] == data_upper["total"]
        assert data_lower["items"][0]["name"] == data_upper["items"][0]["name"]

    def test_list_employees_uuid_format(self, client, sample_employee_data):
        """Should return valid UUID strings in results."""
        # Act
        response = client.get("/employees")

        # Assert
        assert response.status_code == 200
        data = response.json()

        if len(data["items"]) > 0:
            employee_id = data["items"][0]["id"]
            # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
            assert len(employee_id) == 36
            assert employee_id.count("-") == 4

    def test_list_employees_default_limit(self, client, test_db_session):
        """Should use default limit of 25."""
        # Arrange - Create 30 employees
        for i in range(30):
            test_db_session.add(Employee(
                name=f"Employee {i:02d}",
                email=f"emp{i}@example.com",
                status=EmployeeStatus.ACTIVE,
            ))
        test_db_session.commit()

        # Act
        response = client.get("/employees")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 30
        assert len(data["items"]) == 25  # Default limit
        assert data["limit"] == 25


class TestGetEmployeeEndpoint:
    """Tests for GET /employees/{employee_id} endpoint."""

    def test_get_employee_success(self, client, sample_employee_data):
        """Should return detailed employee data by ID."""
        # Arrange
        employee_id = str(sample_employee_data["employees"][0].id)

        # Act
        response = client.get(f"/employees/{employee_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == employee_id
        assert data["name"] == "Alice Anderson"
        assert data["email"] == "alice@example.com"

    def test_get_employee_response_schema(self, client, sample_employee_data):
        """Should return all fields in EmployeeDetail schema."""
        # Arrange
        employee_id = str(sample_employee_data["employees"][0].id)

        # Act
        response = client.get(f"/employees/{employee_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Check all required fields are present
        assert "id" in data
        assert "name" in data
        assert "title" in data
        assert "email" in data
        assert "hired_on" in data
        assert "salary" in data
        assert "status" in data
        assert "department_id" in data
        assert "manager_id" in data
        assert "team_id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_employee_with_all_fields(self, client, sample_employee_data):
        """Should return employee with all fields populated correctly."""
        # Arrange
        employee_id = str(sample_employee_data["employees"][0].id)
        expected_dept_id = str(sample_employee_data["departments"]["eng"].id)
        expected_team_id = str(sample_employee_data["teams"]["backend"].id)

        # Act
        response = client.get(f"/employees/{employee_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == employee_id
        assert data["name"] == "Alice Anderson"
        assert data["email"] == "alice@example.com"
        assert data["status"] == "ACTIVE"
        assert data["salary"] == 120000
        assert data["department_id"] == expected_dept_id
        assert data["team_id"] == expected_team_id

    def test_get_employee_not_found(self, client, sample_employee_data):
        """Should return 404 for non-existent employee ID."""
        # Arrange
        from uuid import uuid4
        fake_id = str(uuid4())

        # Act
        response = client.get(f"/employees/{fake_id}")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Employee not found"

    def test_get_employee_invalid_uuid(self, client):
        """Should return 422 for invalid UUID format."""
        # Act
        response = client.get("/employees/not-a-uuid")

        # Assert
        assert response.status_code == 422

    def test_get_employee_with_null_fields(self, client, test_db_session):
        """Should handle null optional fields correctly."""
        # Arrange - Create employee with minimal fields
        employee = Employee(
            name="John Doe",
            email="john@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        test_db_session.add(employee)
        test_db_session.commit()

        employee_id = str(employee.id)

        # Act
        response = client.get(f"/employees/{employee_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == employee_id
        assert data["name"] == "John Doe"
        assert data["email"] == "john@example.com"
        assert data["title"] is None
        assert data["hired_on"] is None
        assert data["salary"] is None
        assert data["department_id"] is None
        assert data["manager_id"] is None
        assert data["team_id"] is None

    def test_get_employee_uuid_format(self, client, sample_employee_data):
        """Should return valid UUID strings for ID fields."""
        # Arrange
        employee_id = str(sample_employee_data["employees"][0].id)

        # Act
        response = client.get(f"/employees/{employee_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Check UUID format for id
        assert len(data["id"]) == 36
        assert data["id"].count("-") == 4

        # Check UUID format for relationship IDs (if not null)
        if data["department_id"]:
            assert len(data["department_id"]) == 36
            assert data["department_id"].count("-") == 4

    def test_get_employee_datetime_format(self, client, sample_employee_data):
        """Should return ISO-formatted datetime strings."""
        # Arrange
        employee_id = str(sample_employee_data["employees"][0].id)

        # Act
        response = client.get(f"/employees/{employee_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Check created_at and updated_at are present and formatted
        assert "created_at" in data
        assert "updated_at" in data
        # Should be ISO format strings
        assert isinstance(data["created_at"], str)
        assert isinstance(data["updated_at"], str)

    def test_get_employee_status_enum(self, client, sample_employee_data):
        """Should return status as enum string."""
        # Arrange
        employee_id = str(sample_employee_data["employees"][0].id)

        # Act
        response = client.get(f"/employees/{employee_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"] in ["ACTIVE", "ON_LEAVE"]

    def test_get_employee_on_leave(self, client, sample_employee_data):
        """Should correctly return employee with ON_LEAVE status."""
        # Arrange - Get Charlie Chen who is ON_LEAVE
        employee_id = str(sample_employee_data["employees"][2].id)

        # Act
        response = client.get(f"/employees/{employee_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "Charlie Chen"
        assert data["status"] == "ON_LEAVE"

    def test_get_employee_empty_database(self, client):
        """Should return 404 when database is empty."""
        # Arrange
        from uuid import uuid4
        fake_id = str(uuid4())

        # Act
        response = client.get(f"/employees/{fake_id}")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Employee not found"


class TestGetCEOEndpoint:
    """Tests for GET /employees/ceo endpoint."""

    def test_get_ceo_success(self, client, test_db_session):
        """Should return CEO (employee with no manager)."""
        # Arrange - Create CEO
        ceo = Employee(
            name="CEO Smith",
            email="ceo@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        test_db_session.add(ceo)
        test_db_session.commit()

        # Create other employees reporting to CEO
        employee = Employee(
            name="Manager",
            email="manager@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=ceo.id,
        )
        test_db_session.add(employee)
        test_db_session.commit()

        # Act
        response = client.get("/employees/ceo")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(ceo.id)
        assert data["name"] == "CEO Smith"
        assert data["manager_id"] is None

    def test_get_ceo_response_schema(self, client, test_db_session):
        """Should return EmployeeDetail schema."""
        # Arrange
        ceo = Employee(
            name="CEO",
            email="ceo@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        test_db_session.add(ceo)
        test_db_session.commit()

        # Act
        response = client.get("/employees/ceo")

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Check all EmployeeDetail fields
        assert "id" in data
        assert "name" in data
        assert "title" in data
        assert "email" in data
        assert "hired_on" in data
        assert "salary" in data
        assert "status" in data
        assert "department_id" in data
        assert "manager_id" in data
        assert "team_id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_ceo_not_found(self, client, test_db_session):
        """Should return 404 when no CEO exists."""
        # Arrange - Create employee with manager (no CEO)
        employee = Employee(
            name="Employee",
            email="employee@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        test_db_session.add(employee)
        test_db_session.commit()

        # Give employee a fake manager (invalid but tests the logic)
        from uuid import uuid4
        employee.manager_id = uuid4()
        test_db_session.commit()

        # Act
        response = client.get("/employees/ceo")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "CEO not found"

    def test_get_ceo_empty_database(self, client):
        """Should return 404 when database is empty."""
        # Act
        response = client.get("/employees/ceo")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "CEO not found"

    def test_get_ceo_with_multiple_employees(self, client, test_db_session):
        """Should find CEO among multiple employees."""
        # Arrange - Create CEO
        ceo = Employee(
            name="CEO",
            email="ceo@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        test_db_session.add(ceo)
        test_db_session.commit()

        # Create multiple employees
        employees = [
            Employee(
                name=f"Employee {i}",
                email=f"emp{i}@example.com",
                status=EmployeeStatus.ACTIVE,
                manager_id=ceo.id,
            )
            for i in range(5)
        ]
        test_db_session.add_all(employees)
        test_db_session.commit()

        # Act
        response = client.get("/employees/ceo")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(ceo.id)


class TestGetDirectReportsEndpoint:
    """Tests for GET /employees/{employee_id}/direct-reports endpoint."""

    def test_get_direct_reports_success(self, client, test_db_session):
        """Should return list of direct reports."""
        # Arrange - Create manager
        manager = Employee(
            name="Manager",
            email="manager@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        test_db_session.add(manager)
        test_db_session.commit()

        # Create direct reports
        reports = [
            Employee(
                name="Alice",
                email="alice@example.com",
                status=EmployeeStatus.ACTIVE,
                manager_id=manager.id,
            ),
            Employee(
                name="Bob",
                email="bob@example.com",
                status=EmployeeStatus.ACTIVE,
                manager_id=manager.id,
            ),
            Employee(
                name="Charlie",
                email="charlie@example.com",
                status=EmployeeStatus.ON_LEAVE,
                manager_id=manager.id,
            ),
        ]
        test_db_session.add_all(reports)
        test_db_session.commit()

        # Act
        response = client.get(f"/employees/{str(manager.id)}/direct-reports")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_get_direct_reports_response_schema(self, client, test_db_session):
        """Should return list of EmployeeListItem (id and name only)."""
        # Arrange
        manager = Employee(
            name="Manager",
            email="manager@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        test_db_session.add(manager)
        test_db_session.commit()

        report = Employee(
            name="Employee",
            email="employee@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=manager.id,
        )
        test_db_session.add(report)
        test_db_session.commit()

        # Act
        response = client.get(f"/employees/{str(manager.id)}/direct-reports")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

        # Check schema - all EmployeeListItem fields
        assert "id" in data[0]
        assert "name" in data[0]
        assert "email" in data[0]
        assert "title" in data[0]
        assert "status" in data[0]
        assert "department_id" in data[0]
        assert "team_id" in data[0]
        assert "department_name" in data[0]
        assert "team_name" in data[0]
        assert len(data[0]) == 9

    def test_get_direct_reports_alphabetical_order(self, client, test_db_session):
        """Should return direct reports ordered alphabetically."""
        # Arrange
        manager = Employee(
            name="Manager",
            email="manager@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        test_db_session.add(manager)
        test_db_session.commit()

        # Create in non-alphabetical order
        reports = [
            Employee(name="Zara", email="zara@example.com", status=EmployeeStatus.ACTIVE, manager_id=manager.id),
            Employee(name="Alice", email="alice@example.com", status=EmployeeStatus.ACTIVE, manager_id=manager.id),
            Employee(name="Bob", email="bob@example.com", status=EmployeeStatus.ACTIVE, manager_id=manager.id),
        ]
        test_db_session.add_all(reports)
        test_db_session.commit()

        # Act
        response = client.get(f"/employees/{str(manager.id)}/direct-reports")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["name"] == "Alice"
        assert data[1]["name"] == "Bob"
        assert data[2]["name"] == "Zara"

    def test_get_direct_reports_empty_list(self, client, test_db_session):
        """Should return empty list when employee has no direct reports."""
        # Arrange - Employee with no reports
        employee = Employee(
            name="Solo Employee",
            email="solo@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        test_db_session.add(employee)
        test_db_session.commit()

        # Act
        response = client.get(f"/employees/{str(employee.id)}/direct-reports")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0
        assert data == []

    def test_get_direct_reports_nonexistent_employee(self, client):
        """Should return empty list for non-existent employee."""
        # Arrange
        from uuid import uuid4
        fake_id = str(uuid4())

        # Act
        response = client.get(f"/employees/{fake_id}/direct-reports")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_get_direct_reports_invalid_uuid(self, client):
        """Should return 422 for invalid UUID format."""
        # Act
        response = client.get("/employees/not-a-uuid/direct-reports")

        # Assert
        assert response.status_code == 422

    def test_get_direct_reports_excludes_indirect_reports(self, client, test_db_session):
        """Should only return direct reports, not indirect reports."""
        # Arrange - Create hierarchy: CEO -> Manager -> Employee
        ceo = Employee(
            name="CEO",
            email="ceo@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        test_db_session.add(ceo)
        test_db_session.commit()

        manager = Employee(
            name="Manager",
            email="manager@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=ceo.id,
        )
        test_db_session.add(manager)
        test_db_session.commit()

        employee = Employee(
            name="Employee",
            email="employee@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=manager.id,
        )
        test_db_session.add(employee)
        test_db_session.commit()

        # Act - Get CEO's direct reports
        response = client.get(f"/employees/{str(ceo.id)}/direct-reports")

        # Assert - Should only include Manager, not Employee
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Manager"

    def test_get_direct_reports_includes_all_statuses(self, client, test_db_session):
        """Should include direct reports regardless of status."""
        # Arrange
        manager = Employee(
            name="Manager",
            email="manager@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        test_db_session.add(manager)
        test_db_session.commit()

        reports = [
            Employee(
                name="Active Employee",
                email="active@example.com",
                status=EmployeeStatus.ACTIVE,
                manager_id=manager.id,
            ),
            Employee(
                name="On Leave Employee",
                email="onleave@example.com",
                status=EmployeeStatus.ON_LEAVE,
                manager_id=manager.id,
            ),
        ]
        test_db_session.add_all(reports)
        test_db_session.commit()

        # Act
        response = client.get(f"/employees/{str(manager.id)}/direct-reports")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


class TestUpdateEmployeeEndpoint:
    """Tests for PATCH /employees/{employee_id} endpoint."""

    def test_update_employee_name(self, client, sample_employee_data):
        """Should update employee name."""
        # Arrange
        employee_id = str(sample_employee_data["employees"][0].id)
        update_data = {"name": "Alice Johnson"}

        # Act
        response = client.patch(f"/employees/{employee_id}", json=update_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Alice Johnson"
        assert data["email"] == "alice@example.com"  # Unchanged

    def test_update_employee_title(self, client, sample_employee_data):
        """Should update employee title."""
        # Arrange
        employee_id = str(sample_employee_data["employees"][0].id)
        update_data = {"title": "Senior Software Engineer"}

        # Act
        response = client.patch(f"/employees/{employee_id}", json=update_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Senior Software Engineer"

    def test_update_employee_salary(self, client, sample_employee_data):
        """Should update employee salary."""
        # Arrange
        employee_id = str(sample_employee_data["employees"][0].id)
        update_data = {"salary": 130000}

        # Act
        response = client.patch(f"/employees/{employee_id}", json=update_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["salary"] == 130000

    def test_update_employee_status(self, client, sample_employee_data):
        """Should update employee status."""
        # Arrange
        employee_id = str(sample_employee_data["employees"][0].id)
        update_data = {"status": "ON_LEAVE"}

        # Act
        response = client.patch(f"/employees/{employee_id}", json=update_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ON_LEAVE"

    def test_update_employee_multiple_fields(self, client, sample_employee_data):
        """Should update multiple fields simultaneously."""
        # Arrange
        employee_id = str(sample_employee_data["employees"][0].id)
        update_data = {
            "name": "Alice Johnson",
            "title": "Principal Engineer",
            "salary": 150000,
            "status": "ON_LEAVE"
        }

        # Act
        response = client.patch(f"/employees/{employee_id}", json=update_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Alice Johnson"
        assert data["title"] == "Principal Engineer"
        assert data["salary"] == 150000
        assert data["status"] == "ON_LEAVE"

    def test_update_employee_partial_update(self, client, sample_employee_data):
        """Should only update provided fields."""
        # Arrange
        employee_id = str(sample_employee_data["employees"][0].id)
        original_salary = sample_employee_data["employees"][0].salary
        update_data = {"name": "Alice Johnson"}

        # Act
        response = client.patch(f"/employees/{employee_id}", json=update_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Alice Johnson"
        assert data["salary"] == original_salary  # Unchanged

    def test_update_employee_not_found(self, client):
        """Should return 404 for non-existent employee."""
        # Arrange
        from uuid import uuid4
        fake_id = str(uuid4())
        update_data = {"name": "New Name"}

        # Act
        response = client.patch(f"/employees/{fake_id}", json=update_data)

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Employee not found"

    def test_update_employee_invalid_uuid(self, client):
        """Should return 422 for invalid UUID format."""
        # Arrange
        update_data = {"name": "New Name"}

        # Act
        response = client.patch("/employees/not-a-uuid", json=update_data)

        # Assert
        assert response.status_code == 422

    def test_update_employee_invalid_status(self, client, sample_employee_data):
        """Should return 422 for invalid status value."""
        # Arrange
        employee_id = str(sample_employee_data["employees"][0].id)
        update_data = {"status": "INVALID_STATUS"}

        # Act
        response = client.patch(f"/employees/{employee_id}", json=update_data)

        # Assert
        assert response.status_code == 422

    def test_update_employee_invalid_salary_negative(self, client, sample_employee_data):
        """Should return 422 for negative salary."""
        # Arrange
        employee_id = str(sample_employee_data["employees"][0].id)
        update_data = {"salary": -1000}

        # Act
        response = client.patch(f"/employees/{employee_id}", json=update_data)

        # Assert
        assert response.status_code == 422

    def test_update_employee_empty_name(self, client, sample_employee_data):
        """Should return 422 for empty name."""
        # Arrange
        employee_id = str(sample_employee_data["employees"][0].id)
        update_data = {"name": ""}

        # Act
        response = client.patch(f"/employees/{employee_id}", json=update_data)

        # Assert
        assert response.status_code == 422

    def test_update_employee_response_schema(self, client, sample_employee_data):
        """Should return EmployeeDetail schema after update."""
        # Arrange
        employee_id = str(sample_employee_data["employees"][0].id)
        update_data = {"name": "Alice Johnson"}

        # Act
        response = client.patch(f"/employees/{employee_id}", json=update_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Should include all EmployeeDetail fields
        assert "id" in data
        assert "name" in data
        assert "title" in data
        assert "email" in data
        assert "hired_on" in data
        assert "salary" in data
        assert "status" in data
        assert "department_id" in data
        assert "manager_id" in data
        assert "team_id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_update_employee_persists_changes(self, client, sample_employee_data):
        """Should persist changes to database."""
        # Arrange
        employee_id = str(sample_employee_data["employees"][0].id)
        update_data = {"name": "Alice Johnson"}

        # Act - Update
        response = client.patch(f"/employees/{employee_id}", json=update_data)
        assert response.status_code == 200

        # Assert - Verify changes persisted by fetching again
        get_response = client.get(f"/employees/{employee_id}")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["name"] == "Alice Johnson"

    def test_update_employee_creates_audit_log(self, client, sample_employee_data, test_db_session):
        """Should create audit log entry."""
        # Arrange
        from models.AuditLogModel import AuditLog, EntityType, ChangeType
        employee_id_str = str(sample_employee_data["employees"][0].id)
        from uuid import UUID
        employee_id = UUID(employee_id_str)
        update_data = {"name": "Alice Johnson"}

        # Act
        response = client.patch(f"/employees/{employee_id_str}", json=update_data)
        assert response.status_code == 200

        # Assert - Check audit log
        audit_logs = test_db_session.query(AuditLog).filter(
            AuditLog.entity_type == EntityType.EMPLOYEE,
            AuditLog.entity_id == employee_id,
            AuditLog.change_type == ChangeType.UPDATE,
        ).all()

        assert len(audit_logs) == 1
        log = audit_logs[0]
        assert log.previous_state["name"] == "Alice Anderson"
        assert log.new_state["name"] == "Alice Johnson"

    def test_update_employee_empty_body(self, client, sample_employee_data):
        """Should accept empty body (no updates)."""
        # Arrange
        employee_id = str(sample_employee_data["employees"][0].id)

        # Act
        response = client.patch(f"/employees/{employee_id}", json={})

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Alice Anderson"  # Unchanged

    def test_update_employee_null_optional_field(self, client, sample_employee_data):
        """Should allow null for optional fields."""
        # Arrange
        employee_id = str(sample_employee_data["employees"][0].id)
        update_data = {"title": None}

        # Act
        response = client.patch(f"/employees/{employee_id}", json=update_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["title"] is None

    def test_update_employee_empty_database(self, client):
        """Should return 404 when database is empty."""
        # Arrange
        from uuid import uuid4
        fake_id = str(uuid4())
        update_data = {"name": "Test"}

        # Act
        response = client.patch(f"/employees/{fake_id}", json=update_data)

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Employee not found"
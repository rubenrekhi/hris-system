"""
test_global_search_api.py
--------------------------
Integration tests for GlobalSearch API endpoint.

Testing Strategy:
1. Use FastAPI TestClient for full HTTP request/response testing
2. Test both successful responses and error cases
3. Validate response schemas and status codes
4. Test query parameter validation (min length, whitespace)
5. Test search functionality across all entity types
6. Use real database (in-memory SQLite) for integration testing
"""

import pytest
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
def sample_search_data(test_db_session):
    """Create sample data for search testing."""
    # Create departments
    eng_dept = Department(name="Engineering")
    sales_dept = Department(name="Sales & Marketing")
    hr_dept = Department(name="Human Resources")

    test_db_session.add_all([eng_dept, sales_dept, hr_dept])
    test_db_session.flush()

    # Create teams
    backend_team = Team(name="Backend Team")
    frontend_team = Team(name="Frontend Team")
    mobile_team = Team(name="Mobile Development")

    test_db_session.add_all([backend_team, frontend_team, mobile_team])
    test_db_session.flush()

    # Create employees
    employees = [
        Employee(
            name="John Doe",
            email="john.doe@example.com",
            status=EmployeeStatus.ACTIVE,
            department_id=eng_dept.id,
            team_id=backend_team.id,
        ),
        Employee(
            name="Jane Smith",
            email="jane.smith@example.com",
            status=EmployeeStatus.ACTIVE,
            department_id=eng_dept.id,
            team_id=frontend_team.id,
        ),
        Employee(
            name="Bob Johnson",
            email="bob.johnson@example.com",
            status=EmployeeStatus.ACTIVE,
            department_id=sales_dept.id,
        ),
        Employee(
            name="Alice Williams",
            email="alice@example.com",
            status=EmployeeStatus.ACTIVE,
            department_id=hr_dept.id,
        ),
    ]

    test_db_session.add_all(employees)
    test_db_session.commit()

    return {
        "departments": [eng_dept, sales_dept, hr_dept],
        "teams": [backend_team, frontend_team, mobile_team],
        "employees": employees,
    }


class TestGlobalSearchEndpoint:
    """Tests for GET /search endpoint."""

    def test_search_employees_by_name(self, client, sample_search_data):
        """Should return employee search results by name."""
        # Act
        response = client.get("/search?q=john")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "employees" in data
        assert "departments" in data
        assert "teams" in data

        assert len(data["employees"]) >= 1
        assert any(emp["name"] == "John Doe" for emp in data["employees"])

    def test_search_employees_by_email(self, client, sample_search_data):
        """Should return employee search results by email."""
        # Act
        response = client.get("/search?q=alice@example.com")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert len(data["employees"]) == 1
        assert data["employees"][0]["name"] == "Alice Williams"

    def test_search_departments_by_name(self, client, sample_search_data):
        """Should return department search results."""
        # Act
        response = client.get("/search?q=Engineering")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert len(data["departments"]) == 1
        assert data["departments"][0]["name"] == "Engineering"

    def test_search_teams_by_name(self, client, sample_search_data):
        """Should return team search results."""
        # Act
        response = client.get("/search?q=Backend")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert len(data["teams"]) == 1
        assert data["teams"][0]["name"] == "Backend Team"

    def test_search_multiple_entity_types(self, client, sample_search_data):
        """Should return results from multiple entity types."""
        # Act - "team" appears in both team names and could be in other entities
        response = client.get("/search?q=team")

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Should find at least the teams
        assert len(data["teams"]) >= 2

    def test_search_case_insensitive(self, client, sample_search_data):
        """Should perform case-insensitive search."""
        # Act
        response_lower = client.get("/search?q=engineering")
        response_upper = client.get("/search?q=ENGINEERING")

        # Assert
        assert response_lower.status_code == 200
        assert response_upper.status_code == 200

        data_lower = response_lower.json()
        data_upper = response_upper.json()

        assert len(data_lower["departments"]) == len(data_upper["departments"])
        assert data_lower["departments"][0]["name"] == data_upper["departments"][0]["name"]

    def test_search_no_results(self, client, sample_search_data):
        """Should return empty arrays when no matches found."""
        # Act
        response = client.get("/search?q=nonexistent")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["employees"] == []
        assert data["departments"] == []
        assert data["teams"] == []

    def test_search_response_schema(self, client, sample_search_data):
        """Should return correct response schema with id and name fields."""
        # Act
        response = client.get("/search?q=John Doe")

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Check employee result schema
        if len(data["employees"]) > 0:
            employee = data["employees"][0]
            assert "id" in employee
            assert "name" in employee
            assert len(employee) == 2  # Only id and name fields

    def test_search_partial_match(self, client, sample_search_data):
        """Should find results with partial string match."""
        # Act
        response = client.get("/search?q=sales")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert len(data["departments"]) == 1
        assert data["departments"][0]["name"] == "Sales & Marketing"

    def test_search_with_special_characters(self, client, sample_search_data):
        """Should handle special characters in search query."""
        # Act
        response = client.get("/search?q=Sales%20%26%20Marketing")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert len(data["departments"]) == 1
        assert data["departments"][0]["name"] == "Sales & Marketing"

    def test_search_empty_query_validation(self, client):
        """Should return 422 for empty query string."""
        # Act
        response = client.get("/search?q=")

        # Assert
        assert response.status_code == 422

    def test_search_missing_query_parameter(self, client):
        """Should return 422 when query parameter is missing."""
        # Act
        response = client.get("/search")

        # Assert
        assert response.status_code == 422

    def test_search_trims_whitespace(self, client, sample_search_data):
        """Should trim leading/trailing whitespace from query."""
        # Act
        response = client.get("/search?q=%20%20Engineering%20%20")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert len(data["departments"]) == 1
        assert data["departments"][0]["name"] == "Engineering"

    def test_search_uuid_format(self, client, sample_search_data):
        """Should return valid UUID strings in results."""
        # Act
        response = client.get("/search?q=John")

        # Assert
        assert response.status_code == 200
        data = response.json()

        if len(data["employees"]) > 0:
            employee_id = data["employees"][0]["id"]
            # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
            assert len(employee_id) == 36
            assert employee_id.count("-") == 4

    def test_search_result_limit(self, client, test_db_session):
        """Should limit results to 10 per entity type."""
        # Arrange - Create 15 employees with similar names
        for i in range(15):
            test_db_session.add(Employee(
                name=f"Test Employee {i}",
                email=f"test{i}@example.com",
                status=EmployeeStatus.ACTIVE,
            ))
        test_db_session.commit()

        # Act
        response = client.get("/search?q=Test Employee")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert len(data["employees"]) == 10  # Limited to 10

    def test_search_empty_database(self, client):
        """Should return empty results when database is empty."""
        # Act
        response = client.get("/search?q=anything")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["employees"] == []
        assert data["departments"] == []
        assert data["teams"] == []

    def test_search_url_encoded_query(self, client, sample_search_data):
        """Should handle URL-encoded query strings."""
        # Act
        response = client.get("/search?q=jane%20smith")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert len(data["employees"]) == 1
        assert data["employees"][0]["name"] == "Jane Smith"

    def test_search_numeric_query(self, client, sample_search_data):
        """Should handle numeric characters in query."""
        # Arrange
        test_db_session = sample_search_data

        # Act
        response = client.get("/search?q=123")

        # Assert
        assert response.status_code == 200
        data = response.json()

        # No results expected, but should not error
        assert isinstance(data["employees"], list)
        assert isinstance(data["departments"], list)
        assert isinstance(data["teams"], list)
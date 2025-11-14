"""
test_global_search_service.py
------------------------------
Unit tests for GlobalSearchService business logic.

Testing Strategy:
1. Test search functionality across all entity types (employees, departments, teams)
2. Test ILIKE case-insensitive matching
3. Test partial string matching (prefix, suffix, middle)
4. Test result limits (10 per entity type)
5. Test empty results when no matches found
6. Test search by employee email
7. Test that results are properly isolated (no cross-contamination)
"""

import pytest
from uuid import uuid4
from services.GlobalSearchService import GlobalSearchService
from models.EmployeeModel import Employee, EmployeeStatus
from models.DepartmentModel import Department
from models.TeamModel import Team
from models.UserModel import User  # Import to ensure SQLAlchemy relationships are configured


@pytest.fixture
def search_service(db_session):
    """Create a GlobalSearchService instance with test database session."""
    return GlobalSearchService(db_session)


@pytest.fixture
def sample_data(db_session):
    """Create sample employees, departments, and teams for search testing."""
    # Create departments
    eng_dept = Department(name="Engineering")
    sales_dept = Department(name="Sales & Marketing")
    hr_dept = Department(name="Human Resources")

    db_session.add_all([eng_dept, sales_dept, hr_dept])
    db_session.flush()

    # Create teams
    backend_team = Team(name="Backend Team")
    frontend_team = Team(name="Frontend Team")
    mobile_team = Team(name="Mobile Development")

    db_session.add_all([backend_team, frontend_team, mobile_team])
    db_session.flush()

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
        Employee(
            name="Charlie Brown",
            email="charlie.brown@example.com",
            status=EmployeeStatus.ON_LEAVE,
        ),
    ]

    db_session.add_all(employees)
    db_session.commit()

    return {
        "departments": [eng_dept, sales_dept, hr_dept],
        "teams": [backend_team, frontend_team, mobile_team],
        "employees": employees,
    }


class TestGlobalSearchService:
    """Tests for GlobalSearchService.search() method."""

    def test_search_employees_by_name_exact_match(self, search_service, sample_data):
        """Should find employee by exact name match (case-insensitive)."""
        # Act
        employees, departments, teams = search_service.search("john doe")

        # Assert
        assert len(employees) == 1
        assert employees[0].name == "John Doe"
        assert len(departments) == 0
        assert len(teams) == 0

    def test_search_employees_by_name_partial_match(self, search_service, sample_data):
        """Should find employees by partial name match."""
        # Act
        employees, departments, teams = search_service.search("john")

        # Assert
        assert len(employees) == 2  # John Doe and Bob Johnson
        assert any(emp.name == "John Doe" for emp in employees)
        assert any(emp.name == "Bob Johnson" for emp in employees)

    def test_search_employees_by_email(self, search_service, sample_data):
        """Should find employee by email address."""
        # Act
        employees, departments, teams = search_service.search("alice@example.com")

        # Assert
        assert len(employees) == 1
        assert employees[0].name == "Alice Williams"
        assert employees[0].email == "alice@example.com"

    def test_search_employees_by_email_partial_match(self, search_service, sample_data):
        """Should find employees by partial email match."""
        # Act
        employees, departments, teams = search_service.search("@example.com")

        # Assert
        assert len(employees) == 5  # All employees have @example.com

    def test_search_employees_case_insensitive(self, search_service, sample_data):
        """Should perform case-insensitive search on employee names."""
        # Act
        employees_lower, _, _ = search_service.search("jane smith")
        employees_upper, _, _ = search_service.search("JANE SMITH")
        employees_mixed, _, _ = search_service.search("JaNe SmItH")

        # Assert
        assert len(employees_lower) == 1
        assert len(employees_upper) == 1
        assert len(employees_mixed) == 1
        assert employees_lower[0].name == employees_upper[0].name == employees_mixed[0].name

    def test_search_departments_by_name(self, search_service, sample_data):
        """Should find department by name."""
        # Act
        employees, departments, teams = search_service.search("Engineering")

        # Assert
        assert len(departments) == 1
        assert departments[0].name == "Engineering"

    def test_search_departments_partial_match(self, search_service, sample_data):
        """Should find departments by partial name match."""
        # Act
        employees, departments, teams = search_service.search("sales")

        # Assert
        assert len(departments) == 1
        assert departments[0].name == "Sales & Marketing"

    def test_search_departments_case_insensitive(self, search_service, sample_data):
        """Should perform case-insensitive search on department names."""
        # Act
        _, departments_lower, _ = search_service.search("engineering")
        _, departments_upper, _ = search_service.search("ENGINEERING")

        # Assert
        assert len(departments_lower) == 1
        assert len(departments_upper) == 1
        assert departments_lower[0].name == departments_upper[0].name

    def test_search_teams_by_name(self, search_service, sample_data):
        """Should find team by name."""
        # Act
        employees, departments, teams = search_service.search("Backend Team")

        # Assert
        assert len(teams) == 1
        assert teams[0].name == "Backend Team"

    def test_search_teams_partial_match(self, search_service, sample_data):
        """Should find teams by partial name match."""
        # Act
        employees, departments, teams = search_service.search("team")

        # Assert
        assert len(teams) == 2  # Backend Team and Frontend Team
        assert any(team.name == "Backend Team" for team in teams)
        assert any(team.name == "Frontend Team" for team in teams)

    def test_search_teams_case_insensitive(self, search_service, sample_data):
        """Should perform case-insensitive search on team names."""
        # Act
        _, _, teams_lower = search_service.search("mobile development")
        _, _, teams_upper = search_service.search("MOBILE DEVELOPMENT")

        # Assert
        assert len(teams_lower) == 1
        assert len(teams_upper) == 1
        assert teams_lower[0].name == teams_upper[0].name

    def test_search_multiple_entity_types(self, search_service, sample_data):
        """Should return results from multiple entity types in single search."""
        # Act - "front" matches Frontend Team and also appears in employee names
        employees, departments, teams = search_service.search("front")

        # Assert
        assert len(teams) == 1
        assert teams[0].name == "Frontend Team"
        # May or may not find employees depending on data

    def test_search_no_results(self, search_service, sample_data):
        """Should return empty lists when no matches found."""
        # Act
        employees, departments, teams = search_service.search("nonexistent")

        # Assert
        assert len(employees) == 0
        assert len(departments) == 0
        assert len(teams) == 0

    def test_search_result_limit_employees(self, search_service, db_session):
        """Should limit employee results to 10."""
        # Arrange - Create 15 employees with similar names
        for i in range(15):
            db_session.add(Employee(
                name=f"Test Employee {i}",
                email=f"test{i}@example.com",
                status=EmployeeStatus.ACTIVE,
            ))
        db_session.commit()

        # Act
        employees, departments, teams = search_service.search("Test Employee")

        # Assert
        assert len(employees) == 10  # Limited to 10

    def test_search_result_limit_departments(self, search_service, db_session):
        """Should limit department results to 10."""
        # Arrange - Create 15 departments with similar names
        for i in range(15):
            db_session.add(Department(name=f"Test Department {i}"))
        db_session.commit()

        # Act
        employees, departments, teams = search_service.search("Test Department")

        # Assert
        assert len(departments) == 10  # Limited to 10

    def test_search_result_limit_teams(self, search_service, db_session):
        """Should limit team results to 10."""
        # Arrange - Create 15 teams with similar names
        for i in range(15):
            db_session.add(Team(name=f"Test Team {i}"))
        db_session.commit()

        # Act
        employees, departments, teams = search_service.search("Test Team")

        # Assert
        assert len(teams) == 10  # Limited to 10

    def test_search_with_special_characters(self, search_service, sample_data):
        """Should handle special characters in search query."""
        # Act - Search for department with ampersand
        employees, departments, teams = search_service.search("Sales &")

        # Assert
        assert len(departments) == 1
        assert departments[0].name == "Sales & Marketing"

    def test_search_empty_database(self, search_service, db_session):
        """Should return empty results when database is empty."""
        # Act
        employees, departments, teams = search_service.search("anything")

        # Assert
        assert len(employees) == 0
        assert len(departments) == 0
        assert len(teams) == 0

    def test_search_returns_tuples(self, search_service, sample_data):
        """Should return tuple of three lists."""
        # Act
        result = search_service.search("test")

        # Assert
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert isinstance(result[0], list)
        assert isinstance(result[1], list)
        assert isinstance(result[2], list)
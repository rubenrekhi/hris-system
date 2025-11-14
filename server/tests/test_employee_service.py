"""
test_employee_service.py
-------------------------
Unit tests for EmployeeService business logic.

Testing Strategy:
1. Test list_employees with various filter combinations
2. Test pagination functionality (limit and offset)
3. Test search functionality (name and email)
4. Test salary range filtering
5. Test status filtering
6. Test ordering (alphabetical by name)
7. Test total count calculation
8. Test empty results
"""

import pytest
from datetime import date
from uuid import uuid4
from sqlalchemy import select
from services.EmployeeService import EmployeeService
from models.EmployeeModel import Employee, EmployeeStatus
from models.DepartmentModel import Department
from models.TeamModel import Team
from models.UserModel import User  # Import to ensure SQLAlchemy relationships are configured
from models.AuditLogModel import AuditLog, EntityType, ChangeType


@pytest.fixture
def employee_service(db_session):
    """Create an EmployeeService instance with test database session."""
    return EmployeeService(db_session)


@pytest.fixture
def sample_employees(db_session):
    """Create sample employees with departments and teams for testing."""
    # Create departments
    eng_dept = Department(name="Engineering")
    sales_dept = Department(name="Sales")
    hr_dept = Department(name="HR")

    db_session.add_all([eng_dept, sales_dept, hr_dept])
    db_session.flush()

    # Create teams
    backend_team = Team(name="Backend Team", department_id=eng_dept.id)
    frontend_team = Team(name="Frontend Team", department_id=eng_dept.id)
    sales_team = Team(name="Sales Team", department_id=sales_dept.id)

    db_session.add_all([backend_team, frontend_team, sales_team])
    db_session.flush()

    # Create employees
    employees = [
        Employee(
            name="Alice Anderson",
            email="alice@example.com",
            status=EmployeeStatus.ACTIVE,
            department_id=eng_dept.id,
            team_id=backend_team.id,
            salary=120000,
            hired_on=date(2023, 1, 15),
        ),
        Employee(
            name="Bob Brown",
            email="bob@example.com",
            status=EmployeeStatus.ACTIVE,
            department_id=eng_dept.id,
            team_id=frontend_team.id,
            salary=110000,
            hired_on=date(2023, 2, 1),
        ),
        Employee(
            name="Charlie Chen",
            email="charlie@example.com",
            status=EmployeeStatus.ON_LEAVE,
            department_id=eng_dept.id,
            team_id=backend_team.id,
            salary=115000,
            hired_on=date(2023, 3, 10),
        ),
        Employee(
            name="Diana Davis",
            email="diana@example.com",
            status=EmployeeStatus.ACTIVE,
            department_id=sales_dept.id,
            team_id=sales_team.id,
            salary=95000,
            hired_on=date(2023, 4, 5),
        ),
        Employee(
            name="Eve Evans",
            email="eve@example.com",
            status=EmployeeStatus.ACTIVE,
            department_id=sales_dept.id,
            team_id=sales_team.id,
            salary=90000,
            hired_on=date(2023, 5, 20),
        ),
        Employee(
            name="Frank Fisher",
            email="frank@example.com",
            status=EmployeeStatus.ON_LEAVE,
            department_id=hr_dept.id,
            salary=80000,
            hired_on=date(2023, 6, 1),
        ),
    ]

    db_session.add_all(employees)
    db_session.commit()

    return {
        "departments": {"eng": eng_dept, "sales": sales_dept, "hr": hr_dept},
        "teams": {"backend": backend_team, "frontend": frontend_team, "sales": sales_team},
        "employees": employees,
    }


class TestListEmployees:
    """Tests for EmployeeService.list_employees() method."""

    def test_list_all_employees_no_filters(self, employee_service, sample_employees):
        """Should return all employees ordered alphabetically by name."""
        # Act
        employees, total = employee_service.list_employees()

        # Assert
        assert total == 6
        assert len(employees) == 6
        # Check alphabetical ordering
        assert employees[0]['name'] == "Alice Anderson"
        assert employees[1]['name'] == "Bob Brown"
        assert employees[2]['name'] == "Charlie Chen"
        assert employees[3]['name'] == "Diana Davis"
        assert employees[4]['name'] == "Eve Evans"
        assert employees[5]['name'] == "Frank Fisher"

        # Check that department_name and team_name fields are present
        assert employees[0]['department_name'] == "Engineering"
        assert employees[0]['team_name'] == "Backend Team"
        assert employees[1]['department_name'] == "Engineering"
        assert employees[1]['team_name'] == "Frontend Team"
        assert employees[5]['department_name'] == "HR"
        assert employees[5]['team_name'] is None  # Frank has no team

    def test_list_employees_filter_by_team(self, employee_service, sample_employees):
        """Should filter employees by team_id."""
        # Arrange
        backend_team_id = sample_employees["teams"]["backend"].id

        # Act
        employees, total = employee_service.list_employees(team_id=backend_team_id)

        # Assert
        assert total == 2
        assert len(employees) == 2
        assert all(emp['team_id'] == backend_team_id for emp in employees)
        assert employees[0]['name'] == "Alice Anderson"
        assert employees[1]['name'] == "Charlie Chen"

        # Verify team_name and department_name are populated
        assert all(emp['team_name'] == "Backend Team" for emp in employees)
        assert all(emp['department_name'] == "Engineering" for emp in employees)

    def test_list_employees_filter_by_department(self, employee_service, sample_employees):
        """Should filter employees by department_id."""
        # Arrange
        eng_dept_id = sample_employees["departments"]["eng"].id

        # Act
        employees, total = employee_service.list_employees(department_id=eng_dept_id)

        # Assert
        assert total == 3
        assert len(employees) == 3
        assert all(emp['department_id'] == eng_dept_id for emp in employees)

        # Verify department_name is populated
        assert all(emp['department_name'] == "Engineering" for emp in employees)

    def test_list_employees_filter_by_status_active(self, employee_service, sample_employees):
        """Should filter employees by ACTIVE status."""
        # Act
        employees, total = employee_service.list_employees(status=EmployeeStatus.ACTIVE)

        # Assert
        assert total == 4
        assert len(employees) == 4
        assert all(emp['status'] == EmployeeStatus.ACTIVE for emp in employees)

    def test_list_employees_filter_by_status_on_leave(self, employee_service, sample_employees):
        """Should filter employees by ON_LEAVE status."""
        # Act
        employees, total = employee_service.list_employees(status=EmployeeStatus.ON_LEAVE)

        # Assert
        assert total == 2
        assert len(employees) == 2
        assert all(emp['status'] == EmployeeStatus.ON_LEAVE for emp in employees)

    def test_list_employees_filter_by_min_salary(self, employee_service, sample_employees):
        """Should filter employees by minimum salary."""
        # Act
        employees, total = employee_service.list_employees(min_salary=100000)

        # Assert
        assert total == 3
        assert len(employees) == 3
        assert all(emp['salary'] >= 100000 for emp in employees)

    def test_list_employees_filter_by_max_salary(self, employee_service, sample_employees):
        """Should filter employees by maximum salary."""
        # Act
        employees, total = employee_service.list_employees(max_salary=95000)

        # Assert
        assert total == 3
        assert len(employees) == 3
        assert all(emp['salary'] <= 95000 for emp in employees)

    def test_list_employees_filter_by_salary_range(self, employee_service, sample_employees):
        """Should filter employees by salary range (min and max)."""
        # Act
        employees, total = employee_service.list_employees(
            min_salary=90000, max_salary=115000
        )

        # Assert
        assert total == 4
        assert len(employees) == 4
        assert all(90000 <= emp['salary'] <= 115000 for emp in employees)

    def test_list_employees_search_by_name(self, employee_service, sample_employees):
        """Should search employees by name (case-insensitive)."""
        # Act
        employees, total = employee_service.list_employees(name="bob")

        # Assert
        assert total == 1
        assert len(employees) == 1
        assert employees[0]['name'] == "Bob Brown"

    def test_list_employees_search_by_name_partial(self, employee_service, sample_employees):
        """Should find employees by partial name match."""
        # Act
        employees, total = employee_service.list_employees(name="an")

        # Assert - "an" appears in: Alice Anderson, Diana Davis, Frank Fisher, and Evans
        assert total == 4
        assert len(employees) == 4

    def test_list_employees_search_by_email(self, employee_service, sample_employees):
        """Should search employees by email (case-insensitive)."""
        # Act
        employees, total = employee_service.list_employees(email="alice@example.com")

        # Assert
        assert total == 1
        assert len(employees) == 1
        assert employees[0]['email'] == "alice@example.com"

    def test_list_employees_search_by_email_partial(self, employee_service, sample_employees):
        """Should find employees by partial email match."""
        # Act
        employees, total = employee_service.list_employees(email="@example.com")

        # Assert
        assert total == 6  # All employees
        assert len(employees) == 6

    def test_list_employees_search_name_or_email(self, employee_service, sample_employees):
        """Should search by name OR email (widening search)."""
        # Act - Search for "eve" which matches both Eve's name and email
        employees, total = employee_service.list_employees(
            name="eve", email="diana@example.com"
        )

        # Assert - Should find both Eve (by name) and Diana (by email)
        assert total == 2
        assert len(employees) == 2

    def test_list_employees_multiple_filters(self, employee_service, sample_employees):
        """Should apply multiple filters simultaneously."""
        # Arrange
        eng_dept_id = sample_employees["departments"]["eng"].id

        # Act - Engineering department, ACTIVE status, salary >= 110000
        employees, total = employee_service.list_employees(
            department_id=eng_dept_id,
            status=EmployeeStatus.ACTIVE,
            min_salary=110000,
        )

        # Assert
        assert total == 2  # Alice and Bob
        assert len(employees) == 2
        assert all(emp['department_id'] == eng_dept_id for emp in employees)
        assert all(emp['status'] == EmployeeStatus.ACTIVE for emp in employees)
        assert all(emp['salary'] >= 110000 for emp in employees)

    def test_list_employees_pagination_limit(self, employee_service, sample_employees):
        """Should respect limit parameter."""
        # Act
        employees, total = employee_service.list_employees(limit=3)

        # Assert
        assert total == 6  # Total count unchanged
        assert len(employees) == 3  # Only 3 returned
        # First 3 alphabetically
        assert employees[0]['name'] == "Alice Anderson"
        assert employees[1]['name'] == "Bob Brown"
        assert employees[2]['name'] == "Charlie Chen"

    def test_list_employees_pagination_offset(self, employee_service, sample_employees):
        """Should respect offset parameter."""
        # Act
        employees, total = employee_service.list_employees(limit=2, offset=2)

        # Assert
        assert total == 6  # Total count unchanged
        assert len(employees) == 2  # Only 2 returned
        # Skip first 2, get next 2
        assert employees[0]['name'] == "Charlie Chen"
        assert employees[1]['name'] == "Diana Davis"

    def test_list_employees_pagination_offset_beyond_results(self, employee_service, sample_employees):
        """Should return empty list when offset exceeds total."""
        # Act
        employees, total = employee_service.list_employees(offset=100)

        # Assert
        assert total == 6  # Total count unchanged
        assert len(employees) == 0  # No results

    def test_list_employees_no_results(self, employee_service, sample_employees):
        """Should return empty list when no matches found."""
        # Act
        employees, total = employee_service.list_employees(name="nonexistent")

        # Assert
        assert total == 0
        assert len(employees) == 0

    def test_list_employees_empty_database(self, employee_service, db_session):
        """Should return empty results when database is empty."""
        # Act
        employees, total = employee_service.list_employees()

        # Assert
        assert total == 0
        assert len(employees) == 0

    def test_list_employees_ordering_with_same_names(self, employee_service, db_session):
        """Should use id as secondary sort when names are identical."""
        # Arrange - Create employees with same name
        emp1 = Employee(
            name="John Doe",
            email="john1@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        emp2 = Employee(
            name="John Doe",
            email="john2@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        db_session.add_all([emp1, emp2])
        db_session.commit()

        # Act
        employees, total = employee_service.list_employees()

        # Assert
        assert total == 2
        assert len(employees) == 2
        # Should be ordered by name, then id
        assert employees[0]['name'] == "John Doe"
        assert employees[1]['name'] == "John Doe"
        # ID ordering (ascending)
        assert employees[0]['id'] < employees[1]['id']

    def test_list_employees_returns_tuple(self, employee_service, sample_employees):
        """Should return tuple of (list, int)."""
        # Act
        result = employee_service.list_employees()

        # Assert
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], list)
        assert isinstance(result[1], int)

    def test_list_employees_default_pagination(self, employee_service, db_session):
        """Should use default limit of 25 and offset of 0."""
        # Arrange - Create 30 employees
        for i in range(30):
            db_session.add(Employee(
                name=f"Employee {i:02d}",
                email=f"emp{i}@example.com",
                status=EmployeeStatus.ACTIVE,
            ))
        db_session.commit()

        # Act
        employees, total = employee_service.list_employees()

        # Assert
        assert total == 30
        assert len(employees) == 25  # Default limit

    def test_list_employees_case_insensitive_name_search(self, employee_service, sample_employees):
        """Should perform case-insensitive name search."""
        # Act
        employees_lower, _ = employee_service.list_employees(name="alice")
        employees_upper, _ = employee_service.list_employees(name="ALICE")
        employees_mixed, _ = employee_service.list_employees(name="AlIcE")

        # Assert
        assert len(employees_lower) == 1
        assert len(employees_upper) == 1
        assert len(employees_mixed) == 1
        assert employees_lower[0]['name'] == employees_upper[0]['name'] == employees_mixed[0]['name']

    def test_list_employees_case_insensitive_email_search(self, employee_service, sample_employees):
        """Should perform case-insensitive email search."""
        # Act
        employees_lower, _ = employee_service.list_employees(email="alice@example.com")
        employees_upper, _ = employee_service.list_employees(email="ALICE@EXAMPLE.COM")

        # Assert
        assert len(employees_lower) == 1
        assert len(employees_upper) == 1
        assert employees_lower[0]['email'] == employees_upper[0]['email']


class TestGetEmployee:
    """Tests for EmployeeService.get_employee() method."""

    def test_get_existing_employee(self, employee_service, sample_employees):
        """Should return employee by ID."""
        # Arrange
        employee_id = sample_employees["employees"][0].id

        # Act
        employee = employee_service.get_employee(employee_id)

        # Assert
        assert employee is not None
        assert employee.id == employee_id
        assert employee.name == "Alice Anderson"
        assert employee.email == "alice@example.com"

    def test_get_employee_returns_all_fields(self, employee_service, sample_employees):
        """Should return employee with all fields populated."""
        # Arrange
        employee_id = sample_employees["employees"][0].id

        # Act
        employee = employee_service.get_employee(employee_id)

        # Assert
        assert employee is not None
        assert hasattr(employee, "id")
        assert hasattr(employee, "name")
        assert hasattr(employee, "email")
        assert hasattr(employee, "title")
        assert hasattr(employee, "hired_on")
        assert hasattr(employee, "salary")
        assert hasattr(employee, "status")
        assert hasattr(employee, "department_id")
        assert hasattr(employee, "manager_id")
        assert hasattr(employee, "team_id")
        assert hasattr(employee, "created_at")
        assert hasattr(employee, "updated_at")

    def test_get_nonexistent_employee(self, employee_service, sample_employees):
        """Should return None for non-existent employee ID."""
        # Arrange
        fake_id = uuid4()

        # Act
        employee = employee_service.get_employee(fake_id)

        # Assert
        assert employee is None

    def test_get_employee_with_relationships(self, employee_service, sample_employees):
        """Should return employee with relationship IDs set."""
        # Arrange
        employee_id = sample_employees["employees"][0].id
        expected_dept_id = sample_employees["departments"]["eng"].id
        expected_team_id = sample_employees["teams"]["backend"].id

        # Act
        employee = employee_service.get_employee(employee_id)

        # Assert
        assert employee is not None
        assert employee.department_id == expected_dept_id
        assert employee.team_id == expected_team_id

    def test_get_employee_empty_database(self, employee_service, db_session):
        """Should return None when database is empty."""
        # Arrange
        fake_id = uuid4()

        # Act
        employee = employee_service.get_employee(fake_id)

        # Assert
        assert employee is None


class TestGetCEO:
    """Tests for EmployeeService.get_ceo() method."""

    def test_get_ceo_success(self, employee_service, db_session):
        """Should return employee with no manager (CEO)."""
        # Arrange - Create CEO (no manager)
        ceo = Employee(
            name="CEO Johnson",
            email="ceo@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        # Create employee with manager
        employee = Employee(
            name="Regular Employee",
            email="employee@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        db_session.add_all([ceo, employee])
        db_session.commit()

        # Set employee's manager to CEO
        employee.manager_id = ceo.id
        db_session.commit()

        # Act
        result = employee_service.get_ceo()

        # Assert
        assert result is not None
        assert result.id == ceo.id
        assert result.name == "CEO Johnson"
        assert result.manager_id is None

    def test_get_ceo_no_ceo_exists(self, employee_service, db_session):
        """Should return None when no CEO exists (all employees have managers)."""
        # Arrange - Create employees but set them in a chain (no one without manager)
        emp1 = Employee(
            name="Employee 1",
            email="emp1@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        db_session.add(emp1)
        db_session.commit()

        # Give emp1 a fake manager_id (this is invalid but tests the logic)
        emp1.manager_id = uuid4()
        db_session.commit()

        # Act
        result = employee_service.get_ceo()

        # Assert
        assert result is None

    def test_get_ceo_empty_database(self, employee_service, db_session):
        """Should return None when database is empty."""
        # Act
        result = employee_service.get_ceo()

        # Assert
        assert result is None

    def test_get_ceo_with_multiple_employees(self, employee_service, db_session):
        """Should find CEO among multiple employees."""
        # Arrange - Create CEO
        ceo = Employee(
            name="CEO Smith",
            email="ceo@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        db_session.add(ceo)
        db_session.commit()

        # Create multiple employees reporting to CEO
        employees = [
            Employee(
                name=f"Employee {i}",
                email=f"emp{i}@example.com",
                status=EmployeeStatus.ACTIVE,
                manager_id=ceo.id,
            )
            for i in range(5)
        ]
        db_session.add_all(employees)
        db_session.commit()

        # Act
        result = employee_service.get_ceo()

        # Assert
        assert result is not None
        assert result.id == ceo.id
        assert result.name == "CEO Smith"

    def test_get_ceo_on_leave(self, employee_service, db_session):
        """Should return CEO even if status is ON_LEAVE."""
        # Arrange - Create CEO who is on leave
        ceo = Employee(
            name="CEO On Leave",
            email="ceo@example.com",
            status=EmployeeStatus.ON_LEAVE,
            manager_id=None,
        )
        db_session.add(ceo)
        db_session.commit()

        # Act
        result = employee_service.get_ceo()

        # Assert
        assert result is not None
        assert result.id == ceo.id
        assert result.status == EmployeeStatus.ON_LEAVE


class TestGetDirectReports:
    """Tests for EmployeeService.get_direct_reports() method."""

    def test_get_direct_reports_success(self, employee_service, db_session):
        """Should return list of employees who report to given employee."""
        # Arrange - Create manager
        manager = Employee(
            name="Manager Smith",
            email="manager@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        db_session.add(manager)
        db_session.commit()

        # Create direct reports
        direct_reports = [
            Employee(
                name="Alice Anderson",
                email="alice@example.com",
                status=EmployeeStatus.ACTIVE,
                manager_id=manager.id,
            ),
            Employee(
                name="Bob Brown",
                email="bob@example.com",
                status=EmployeeStatus.ACTIVE,
                manager_id=manager.id,
            ),
            Employee(
                name="Charlie Chen",
                email="charlie@example.com",
                status=EmployeeStatus.ON_LEAVE,
                manager_id=manager.id,
            ),
        ]
        db_session.add_all(direct_reports)
        db_session.commit()

        # Act
        result = employee_service.get_direct_reports(manager.id)

        # Assert
        assert len(result) == 3
        assert all(emp.manager_id == manager.id for emp in result)

    def test_get_direct_reports_alphabetical_order(self, employee_service, db_session):
        """Should return direct reports ordered alphabetically by name."""
        # Arrange
        manager = Employee(
            name="Manager",
            email="manager@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        db_session.add(manager)
        db_session.commit()

        # Create direct reports in non-alphabetical order
        direct_reports = [
            Employee(
                name="Zara",
                email="zara@example.com",
                status=EmployeeStatus.ACTIVE,
                manager_id=manager.id,
            ),
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
        ]
        db_session.add_all(direct_reports)
        db_session.commit()

        # Act
        result = employee_service.get_direct_reports(manager.id)

        # Assert
        assert len(result) == 3
        assert result[0].name == "Alice"
        assert result[1].name == "Bob"
        assert result[2].name == "Zara"

    def test_get_direct_reports_no_reports(self, employee_service, db_session):
        """Should return empty list when employee has no direct reports."""
        # Arrange - Create employee with no reports
        employee = Employee(
            name="Solo Employee",
            email="solo@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        db_session.add(employee)
        db_session.commit()

        # Act
        result = employee_service.get_direct_reports(employee.id)

        # Assert
        assert len(result) == 0
        assert result == []

    def test_get_direct_reports_nonexistent_employee(self, employee_service, db_session):
        """Should return empty list for non-existent employee."""
        # Arrange
        fake_id = uuid4()

        # Act
        result = employee_service.get_direct_reports(fake_id)

        # Assert
        assert len(result) == 0
        assert result == []

    def test_get_direct_reports_excludes_indirect_reports(self, employee_service, db_session):
        """Should only return direct reports, not indirect reports."""
        # Arrange - Create hierarchy: CEO -> Manager -> Employee
        ceo = Employee(
            name="CEO",
            email="ceo@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        db_session.add(ceo)
        db_session.commit()

        manager = Employee(
            name="Manager",
            email="manager@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=ceo.id,
        )
        db_session.add(manager)
        db_session.commit()

        employee = Employee(
            name="Employee",
            email="employee@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=manager.id,
        )
        db_session.add(employee)
        db_session.commit()

        # Act - Get CEO's direct reports
        result = employee_service.get_direct_reports(ceo.id)

        # Assert - Should only include Manager, not Employee
        assert len(result) == 1
        assert result[0].id == manager.id

    def test_get_direct_reports_includes_all_statuses(self, employee_service, db_session):
        """Should include direct reports regardless of status."""
        # Arrange
        manager = Employee(
            name="Manager",
            email="manager@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        db_session.add(manager)
        db_session.commit()

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
        db_session.add_all(reports)
        db_session.commit()

        # Act
        result = employee_service.get_direct_reports(manager.id)

        # Assert
        assert len(result) == 2
        statuses = {emp.status for emp in result}
        assert EmployeeStatus.ACTIVE in statuses
        assert EmployeeStatus.ON_LEAVE in statuses


class TestCreateEmployee:
    """Tests for EmployeeService.create_employee() method."""

    def test_create_first_employee_no_manager_required(self, employee_service, db_session):
        """Should create first employee without manager_id."""
        # Arrange
        user_id = uuid4()

        # Act
        employee = employee_service.create_employee(
            name="First Employee",
            email="first@example.com",
            title="CEO",
            hired_on=date(2023, 1, 1),
            salary=200000,
            status=EmployeeStatus.ACTIVE,
            manager_id=None,  # No manager for first employee
            changed_by_user_id=user_id,
        )

        # Assert
        assert employee is not None
        assert employee.name == "First Employee"
        assert employee.email == "first@example.com"
        assert employee.manager_id is None

    def test_create_second_employee_requires_manager(self, employee_service, db_session):
        """Should raise ValueError if manager_id is not provided for non-first employee."""
        # Arrange - Create first employee
        first_emp = Employee(
            name="First Employee",
            email="first@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        db_session.add(first_emp)
        db_session.commit()

        user_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="manager_id is required"):
            employee_service.create_employee(
                name="Second Employee",
                email="second@example.com",
                manager_id=None,  # This should fail
                changed_by_user_id=user_id,
            )

    def test_create_employee_with_valid_manager(self, employee_service, db_session):
        """Should create employee with valid manager_id."""
        # Arrange - Create manager
        manager = Employee(
            name="Manager",
            email="manager@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        db_session.add(manager)
        db_session.commit()

        user_id = uuid4()

        # Act
        employee = employee_service.create_employee(
            name="Employee",
            email="employee@example.com",
            manager_id=manager.id,
            changed_by_user_id=user_id,
        )

        # Assert
        assert employee is not None
        assert employee.manager_id == manager.id

    def test_create_employee_invalid_manager(self, employee_service, db_session):
        """Should raise ValueError if manager_id does not exist."""
        # Arrange - Create first employee so manager is required
        first_emp = Employee(
            name="First",
            email="first@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        db_session.add(first_emp)
        db_session.commit()

        fake_manager_id = uuid4()
        user_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="Manager with ID .* does not exist"):
            employee_service.create_employee(
                name="Employee",
                email="employee@example.com",
                manager_id=fake_manager_id,
                changed_by_user_id=user_id,
            )

    def test_create_employee_with_valid_department(self, employee_service, db_session):
        """Should create employee with valid department_id."""
        # Arrange
        department = Department(name="Engineering")
        db_session.add(department)
        db_session.commit()

        user_id = uuid4()

        # Act
        employee = employee_service.create_employee(
            name="First Employee",
            email="first@example.com",
            department_id=department.id,
            changed_by_user_id=user_id,
        )

        # Assert
        assert employee is not None
        assert employee.department_id == department.id

    def test_create_employee_invalid_department(self, employee_service, db_session):
        """Should raise ValueError if department_id does not exist."""
        # Arrange
        fake_dept_id = uuid4()
        user_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="Department with ID .* does not exist"):
            employee_service.create_employee(
                name="First Employee",
                email="first@example.com",
                department_id=fake_dept_id,
                changed_by_user_id=user_id,
            )

    def test_create_employee_with_valid_team(self, employee_service, db_session):
        """Should create employee with valid team_id."""
        # Arrange
        department = Department(name="Engineering")
        db_session.add(department)
        db_session.flush()

        team = Team(name="Backend Team", department_id=department.id)
        db_session.add(team)
        db_session.commit()

        user_id = uuid4()

        # Act
        employee = employee_service.create_employee(
            name="First Employee",
            email="first@example.com",
            team_id=team.id,
            changed_by_user_id=user_id,
        )

        # Assert
        assert employee is not None
        assert employee.team_id == team.id

    def test_create_employee_invalid_team(self, employee_service, db_session):
        """Should raise ValueError if team_id does not exist."""
        # Arrange
        fake_team_id = uuid4()
        user_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="Team with ID .* does not exist"):
            employee_service.create_employee(
                name="First Employee",
                email="first@example.com",
                team_id=fake_team_id,
                changed_by_user_id=user_id,
            )

    def test_create_employee_links_to_existing_user(self, employee_service, db_session):
        """Should link employee to user with matching email."""
        # Arrange - Create user with email
        from models.UserModel import User
        user = User(
            email="john@example.com",
            name="John User",
        )
        db_session.add(user)
        db_session.commit()

        user_id = uuid4()

        # Act
        employee = employee_service.create_employee(
            name="John Doe",
            email="john@example.com",  # Matches user email
            changed_by_user_id=user_id,
        )

        # Commit and refresh to see the linked user
        db_session.commit()
        db_session.refresh(user)

        # Assert - Employee created and user linked
        assert employee is not None
        assert user.employee_id == employee.id

    def test_create_employee_no_user_link(self, employee_service, db_session):
        """Should create employee without user link if email doesn't match."""
        # Arrange
        user_id = uuid4()

        # Act
        employee = employee_service.create_employee(
            name="John Doe",
            email="john@example.com",
            changed_by_user_id=user_id,
        )

        # Assert
        assert employee is not None
        assert employee.email == "john@example.com"

    def test_create_employee_creates_audit_log(self, employee_service, db_session):
        """Should create audit log entry for new employee."""
        # Arrange
        from models.AuditLogModel import AuditLog, EntityType, ChangeType
        user_id = uuid4()

        # Act
        employee = employee_service.create_employee(
            name="John Doe",
            email="john@example.com",
            title="Software Engineer",
            salary=100000,
            changed_by_user_id=user_id,
        )

        # Assert - Check audit log was created
        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.entity_type == EntityType.EMPLOYEE,
            AuditLog.entity_id == employee.id,
            AuditLog.change_type == ChangeType.CREATE,
        ).all()

        assert len(audit_logs) == 1
        log = audit_logs[0]
        assert log.changed_by_user_id == user_id
        assert log.previous_state is None
        assert log.new_state["name"] == "John Doe"
        assert log.new_state["email"] == "john@example.com"
        assert log.new_state["salary"] == 100000

    def test_create_employee_with_user_link_creates_two_audit_logs(self, employee_service, db_session):
        """Should create audit logs for both employee and user when linking."""
        # Arrange - Create user
        from models.UserModel import User
        from models.AuditLogModel import AuditLog, EntityType, ChangeType
        user = User(
            email="john@example.com",
            name="John User",
        )
        db_session.add(user)
        db_session.commit()

        user_id = uuid4()

        # Act
        employee = employee_service.create_employee(
            name="John Doe",
            email="john@example.com",
            changed_by_user_id=user_id,
        )

        # Assert - Check employee audit log
        employee_logs = db_session.query(AuditLog).filter(
            AuditLog.entity_type == EntityType.EMPLOYEE,
            AuditLog.entity_id == employee.id,
        ).all()
        assert len(employee_logs) == 1

        # Assert - Check user audit log
        user_logs = db_session.query(AuditLog).filter(
            AuditLog.entity_type == EntityType.USER,
            AuditLog.entity_id == user.id,
        ).all()
        assert len(user_logs) == 1
        assert user_logs[0].change_type == ChangeType.UPDATE
        assert user_logs[0].previous_state["employee_id"] is None
        assert user_logs[0].new_state["employee_id"] == str(employee.id)

    def test_create_employee_does_not_commit(self, employee_service, db_session):
        """Should not commit transaction (router's responsibility)."""
        # Arrange
        user_id = uuid4()

        # Act
        employee_service.create_employee(
            name="John Doe",
            email="john@example.com",
            changed_by_user_id=user_id,
        )
        db_session.rollback()

        # Assert - Changes should be rolled back
        employees, total = employee_service.list_employees()
        assert total == 0

    def test_create_employee_with_all_fields(self, employee_service, db_session):
        """Should create employee with all fields populated."""
        # Arrange
        department = Department(name="Engineering")
        db_session.add(department)
        db_session.flush()

        team = Team(name="Backend Team", department_id=department.id)
        db_session.add(team)
        db_session.commit()

        user_id = uuid4()

        # Act
        employee = employee_service.create_employee(
            name="John Doe",
            email="john@example.com",
            title="Senior Engineer",
            hired_on=date(2023, 1, 15),
            salary=150000,
            status=EmployeeStatus.ACTIVE,
            department_id=department.id,
            team_id=team.id,
            changed_by_user_id=user_id,
        )

        # Assert
        assert employee is not None
        assert employee.name == "John Doe"
        assert employee.email == "john@example.com"
        assert employee.title == "Senior Engineer"
        assert employee.hired_on == date(2023, 1, 15)
        assert employee.salary == 150000
        assert employee.status == EmployeeStatus.ACTIVE
        assert employee.department_id == department.id
        assert employee.team_id == team.id

    def test_create_employee_minimal_fields(self, employee_service, db_session):
        """Should create employee with only required fields."""
        # Arrange
        user_id = uuid4()

        # Act
        employee = employee_service.create_employee(
            name="John Doe",
            email="john@example.com",
            changed_by_user_id=user_id,
        )

        # Assert
        assert employee is not None
        assert employee.name == "John Doe"
        assert employee.email == "john@example.com"
        assert employee.title is None
        assert employee.hired_on is None
        assert employee.salary is None
        assert employee.status == EmployeeStatus.ACTIVE  # Default
        assert employee.manager_id is None
        assert employee.department_id is None
        assert employee.team_id is None


class TestUpdateEmployee:
    """Tests for EmployeeService.update_employee() method."""

    def test_update_employee_name(self, employee_service, sample_employees, db_session):
        """Should update employee name."""
        # Arrange
        employee_id = sample_employees["employees"][0].id
        user_id = uuid4()
        new_name = "Alice Johnson"

        # Act
        employee = employee_service.update_employee(
            employee_id,
            name=new_name,
            changed_by_user_id=user_id,
        )

        # Assert
        assert employee is not None
        assert employee.name == new_name
        assert employee.email == "alice@example.com"  # Unchanged

    def test_update_employee_title(self, employee_service, sample_employees, db_session):
        """Should update employee title."""
        # Arrange
        employee_id = sample_employees["employees"][0].id
        user_id = uuid4()
        new_title = "Senior Software Engineer"

        # Act
        employee = employee_service.update_employee(
            employee_id,
            title=new_title,
            changed_by_user_id=user_id,
        )

        # Assert
        assert employee is not None
        assert employee.title == new_title

    def test_update_employee_salary(self, employee_service, sample_employees, db_session):
        """Should update employee salary."""
        # Arrange
        employee_id = sample_employees["employees"][0].id
        user_id = uuid4()
        new_salary = 130000

        # Act
        employee = employee_service.update_employee(
            employee_id,
            salary=new_salary,
            changed_by_user_id=user_id,
        )

        # Assert
        assert employee is not None
        assert employee.salary == new_salary

    def test_update_employee_status(self, employee_service, sample_employees, db_session):
        """Should update employee status."""
        # Arrange
        employee_id = sample_employees["employees"][0].id
        user_id = uuid4()

        # Act
        employee = employee_service.update_employee(
            employee_id,
            status=EmployeeStatus.ON_LEAVE,
            changed_by_user_id=user_id,
        )

        # Assert
        assert employee is not None
        assert employee.status == EmployeeStatus.ON_LEAVE

    def test_update_employee_multiple_fields(self, employee_service, sample_employees, db_session):
        """Should update multiple fields simultaneously."""
        # Arrange
        employee_id = sample_employees["employees"][0].id
        user_id = uuid4()

        # Act
        employee = employee_service.update_employee(
            employee_id,
            name="Alice Johnson",
            title="Principal Engineer",
            salary=150000,
            status=EmployeeStatus.ON_LEAVE,
            changed_by_user_id=user_id,
        )

        # Assert
        assert employee is not None
        assert employee.name == "Alice Johnson"
        assert employee.title == "Principal Engineer"
        assert employee.salary == 150000
        assert employee.status == EmployeeStatus.ON_LEAVE

    def test_update_employee_creates_audit_log(self, employee_service, sample_employees, db_session):
        """Should create audit log entry when updating employee."""
        # Arrange
        from models.AuditLogModel import AuditLog, EntityType, ChangeType
        employee_id = sample_employees["employees"][0].id
        user_id = uuid4()

        # Act
        employee_service.update_employee(
            employee_id,
            name="Alice Johnson",
            changed_by_user_id=user_id,
        )

        # Assert - Check audit log was created
        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.entity_type == EntityType.EMPLOYEE,
            AuditLog.entity_id == employee_id,
            AuditLog.change_type == ChangeType.UPDATE,
        ).all()

        assert len(audit_logs) == 1
        log = audit_logs[0]
        assert log.changed_by_user_id == user_id
        assert log.previous_state["name"] == "Alice Anderson"
        assert log.new_state["name"] == "Alice Johnson"

    def test_update_employee_audit_log_tracks_all_changes(self, employee_service, sample_employees, db_session):
        """Should track all changed fields in audit log."""
        # Arrange
        from models.AuditLogModel import AuditLog
        employee_id = sample_employees["employees"][0].id
        user_id = uuid4()

        # Act
        employee_service.update_employee(
            employee_id,
            name="Alice Johnson",
            title="Senior Engineer",
            salary=130000,
            status=EmployeeStatus.ON_LEAVE,
            changed_by_user_id=user_id,
        )

        # Assert
        audit_log = db_session.query(AuditLog).filter(
            AuditLog.entity_id == employee_id
        ).first()

        assert audit_log.previous_state["name"] == "Alice Anderson"
        assert audit_log.new_state["name"] == "Alice Johnson"
        assert audit_log.previous_state["salary"] == 120000
        assert audit_log.new_state["salary"] == 130000
        assert audit_log.previous_state["status"] == "ACTIVE"
        assert audit_log.new_state["status"] == "ON_LEAVE"

    def test_update_employee_no_changes_no_audit_log(self, employee_service, sample_employees, db_session):
        """Should not create audit log if no changes were made."""
        # Arrange
        from models.AuditLogModel import AuditLog
        employee_id = sample_employees["employees"][0].id
        user_id = uuid4()
        original_name = sample_employees["employees"][0].name

        # Act - Update with same value
        employee_service.update_employee(
            employee_id,
            name=original_name,  # Same as current value
            changed_by_user_id=user_id,
        )

        # Assert - No audit log created
        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.entity_id == employee_id
        ).all()
        assert len(audit_logs) == 0

    def test_update_employee_not_found(self, employee_service, sample_employees, db_session):
        """Should return None for non-existent employee."""
        # Arrange
        fake_id = uuid4()
        user_id = uuid4()

        # Act
        employee = employee_service.update_employee(
            fake_id,
            name="New Name",
            changed_by_user_id=user_id,
        )

        # Assert
        assert employee is None

    def test_update_employee_does_not_commit(self, employee_service, sample_employees, db_session):
        """Should not commit transaction (router's responsibility)."""
        # Arrange
        employee_id = sample_employees["employees"][0].id
        user_id = uuid4()

        # Act
        employee_service.update_employee(
            employee_id,
            name="Alice Johnson",
            changed_by_user_id=user_id,
        )
        db_session.rollback()

        # Assert - Changes should be rolled back
        employee = employee_service.get_employee(employee_id)
        assert employee.name == "Alice Anderson"  # Original name

    def test_update_employee_partial_update(self, employee_service, sample_employees, db_session):
        """Should only update provided fields, leave others unchanged."""
        # Arrange
        employee_id = sample_employees["employees"][0].id
        user_id = uuid4()
        original_salary = sample_employees["employees"][0].salary

        # Act - Only update name
        employee = employee_service.update_employee(
            employee_id,
            name="Alice Johnson",
            changed_by_user_id=user_id,
        )

        # Assert
        assert employee.name == "Alice Johnson"
        assert employee.salary == original_salary  # Unchanged

    def test_update_employee_empty_database(self, employee_service, db_session):
        """Should return None when database is empty."""
        # Arrange
        fake_id = uuid4()
        user_id = uuid4()

        # Act
        employee = employee_service.update_employee(
            fake_id,
            name="Test Name",
            changed_by_user_id=user_id,
        )

        # Assert
        assert employee is None

    def test_update_employee_returns_updated_instance(self, employee_service, sample_employees, db_session):
        """Should return the updated employee instance."""
        # Arrange
        employee_id = sample_employees["employees"][0].id
        user_id = uuid4()

        # Act
        employee = employee_service.update_employee(
            employee_id,
            name="Alice Johnson",
            changed_by_user_id=user_id,
        )

        # Assert
        assert employee is not None
        assert isinstance(employee, Employee)
        assert employee.id == employee_id


class TestAssignDepartment:
    """Tests for EmployeeService.assign_department() method."""

    def test_assign_department_success(self, employee_service, db_session):
        """Should assign department to employee."""
        # Arrange - Create employee without department and without team
        employee = Employee(
            name="John Doe",
            email="john@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        department = Department(name="Engineering")
        db_session.add_all([employee, department])
        db_session.commit()

        user_id = uuid4()

        # Act
        result = employee_service.assign_department(
            employee.id,
            department.id,
            changed_by_user_id=user_id,
        )

        # Assert
        assert result is not None
        assert result.department_id == department.id

    def test_assign_department_remove(self, employee_service, db_session):
        """Should remove department from employee when department_id is None."""
        # Arrange - Create employee with department but no team
        department = Department(name="Engineering")
        employee = Employee(
            name="John Doe",
            email="john@example.com",
            status=EmployeeStatus.ACTIVE,
            department_id=None,
        )
        db_session.add_all([department, employee])
        db_session.commit()

        user_id = uuid4()

        # Assign department first
        employee_service.assign_department(employee.id, department.id, changed_by_user_id=user_id)
        db_session.flush()

        # Act - Remove department
        result = employee_service.assign_department(
            employee.id,
            None,
            changed_by_user_id=user_id,
        )

        # Assert
        assert result is not None
        assert result.department_id is None

    def test_assign_department_employee_not_found(self, employee_service, db_session):
        """Should return None if employee doesn't exist."""
        # Arrange
        fake_id = uuid4()
        department_id = uuid4()
        user_id = uuid4()

        # Act
        employee = employee_service.assign_department(
            fake_id,
            department_id,
            changed_by_user_id=user_id,
        )

        # Assert
        assert employee is None

    def test_assign_department_department_not_found(self, employee_service, db_session):
        """Should raise ValueError if department doesn't exist."""
        # Arrange - Create employee without team
        employee = Employee(
            name="John Doe",
            email="john@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        db_session.add(employee)
        db_session.commit()

        fake_department_id = uuid4()
        user_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="Department with ID .* does not exist"):
            employee_service.assign_department(
                employee.id,
                fake_department_id,
                changed_by_user_id=user_id,
            )

    def test_assign_department_team_conflict_different_department(self, employee_service, db_session):
        """Should raise ValueError if employee is on team with different department."""
        # Arrange - Create departments
        dept1 = Department(name="Engineering")
        dept2 = Department(name="Sales")
        db_session.add_all([dept1, dept2])
        db_session.flush()

        # Create team with department
        team = Team(name="Backend Team", department_id=dept1.id)
        db_session.add(team)
        db_session.flush()

        # Create employee on team
        employee = Employee(
            name="John Doe",
            email="john@example.com",
            status=EmployeeStatus.ACTIVE,
            team_id=team.id,
        )
        db_session.add(employee)
        db_session.commit()

        user_id = uuid4()

        # Act & Assert - Try to assign different department
        with pytest.raises(ValueError, match="Employee is on team .* which belongs to a different department"):
            employee_service.assign_department(
                employee.id,
                dept2.id,
                changed_by_user_id=user_id,
            )

    def test_assign_department_team_conflict_remove_department(self, employee_service, db_session):
        """Should raise ValueError if trying to remove department while employee is on team with department."""
        # Arrange - Create department and team
        department = Department(name="Engineering")
        db_session.add(department)
        db_session.flush()

        team = Team(name="Backend Team", department_id=department.id)
        db_session.add(team)
        db_session.flush()

        # Create employee on team with same department
        employee = Employee(
            name="John Doe",
            email="john@example.com",
            status=EmployeeStatus.ACTIVE,
            team_id=team.id,
            department_id=department.id,
        )
        db_session.add(employee)
        db_session.commit()

        user_id = uuid4()

        # Act & Assert - Try to remove department
        with pytest.raises(ValueError, match="Employee is on team .* which has a department assigned"):
            employee_service.assign_department(
                employee.id,
                None,
                changed_by_user_id=user_id,
            )

    def test_assign_department_team_same_department_allowed(self, employee_service, db_session):
        """Should allow assigning department if it matches team's department."""
        # Arrange - Create department and team
        department = Department(name="Engineering")
        db_session.add(department)
        db_session.flush()

        team = Team(name="Backend Team", department_id=department.id)
        db_session.add(team)
        db_session.flush()

        # Create employee on team without department
        employee = Employee(
            name="John Doe",
            email="john@example.com",
            status=EmployeeStatus.ACTIVE,
            team_id=team.id,
        )
        db_session.add(employee)
        db_session.commit()

        user_id = uuid4()

        # Act - Assign same department as team
        result = employee_service.assign_department(
            employee.id,
            department.id,
            changed_by_user_id=user_id,
        )

        # Assert
        assert result is not None
        assert result.department_id == department.id

    def test_assign_department_creates_audit_log(self, employee_service, db_session):
        """Should create audit log entry when assigning department."""
        # Arrange
        from models.AuditLogModel import AuditLog, EntityType, ChangeType

        employee = Employee(
            name="John Doe",
            email="john@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        department = Department(name="Engineering")
        db_session.add_all([employee, department])
        db_session.commit()

        user_id = uuid4()

        # Act
        employee_service.assign_department(
            employee.id,
            department.id,
            changed_by_user_id=user_id,
        )

        # Assert - Check audit log was created
        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.entity_type == EntityType.EMPLOYEE,
            AuditLog.entity_id == employee.id,
            AuditLog.change_type == ChangeType.UPDATE,
        ).all()

        assert len(audit_logs) == 1
        log = audit_logs[0]
        assert log.changed_by_user_id == user_id
        assert log.previous_state["department_id"] is None
        assert log.new_state["department_id"] == str(department.id)

    def test_assign_department_audit_log_tracks_previous_value(self, employee_service, db_session):
        """Should track previous department_id in audit log."""
        # Arrange - Create employee and departments
        from models.AuditLogModel import AuditLog, EntityType, ChangeType

        old_dept = Department(name="Engineering")
        new_dept = Department(name="Sales")
        employee = Employee(
            name="John Doe",
            email="john@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        db_session.add_all([old_dept, new_dept, employee])
        db_session.commit()

        user_id = uuid4()

        # Assign initial department
        employee_service.assign_department(employee.id, old_dept.id, changed_by_user_id=user_id)
        db_session.flush()

        # Act - Change to new department
        employee_service.assign_department(employee.id, new_dept.id, changed_by_user_id=user_id)

        # Assert - Check second audit log
        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.entity_type == EntityType.EMPLOYEE,
            AuditLog.entity_id == employee.id,
        ).order_by(AuditLog.created_at).all()

        assert len(audit_logs) == 2
        second_log = audit_logs[1]
        assert second_log.previous_state["department_id"] == str(old_dept.id)
        assert second_log.new_state["department_id"] == str(new_dept.id)

    def test_assign_department_does_not_commit(self, employee_service, db_session):
        """Should not commit transaction (router's responsibility)."""
        # Arrange
        employee = Employee(
            name="John Doe",
            email="john@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        department = Department(name="Engineering")
        db_session.add_all([employee, department])
        db_session.commit()

        user_id = uuid4()

        # Act
        employee_service.assign_department(
            employee.id,
            department.id,
            changed_by_user_id=user_id,
        )
        db_session.rollback()

        # Assert - Changes should be rolled back
        db_session.refresh(employee)
        assert employee.department_id is None


class TestAssignTeam:
    """Tests for EmployeeService.assign_team() method."""

    def test_assign_team_success(self, employee_service, db_session):
        """Should assign team to employee."""
        # Arrange
        department = Department(name="Engineering")
        db_session.add(department)
        db_session.flush()

        team = Team(name="Backend Team", department_id=department.id)
        db_session.add(team)
        db_session.flush()

        employee = Employee(
            name="John Doe",
            email="john@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        db_session.add(employee)
        db_session.commit()

        user_id = uuid4()

        # Act
        result = employee_service.assign_team(
            employee.id,
            team.id,
            changed_by_user_id=user_id,
        )

        # Assert
        assert result is not None
        assert result.team_id == team.id

    def test_assign_team_remove(self, employee_service, db_session):
        """Should remove team from employee when team_id is None."""
        # Arrange
        department = Department(name="Engineering")
        db_session.add(department)
        db_session.flush()

        team = Team(name="Backend Team", department_id=department.id)
        db_session.add(team)
        db_session.flush()

        employee = Employee(
            name="John Doe",
            email="john@example.com",
            status=EmployeeStatus.ACTIVE,
            team_id=team.id,
        )
        db_session.add(employee)
        db_session.commit()

        user_id = uuid4()

        # Act - Remove team
        result = employee_service.assign_team(
            employee.id,
            None,
            changed_by_user_id=user_id,
        )

        # Assert
        assert result is not None
        assert result.team_id is None

    def test_assign_team_employee_not_found(self, employee_service, db_session):
        """Should return None if employee doesn't exist."""
        # Arrange
        fake_id = uuid4()
        team_id = uuid4()
        user_id = uuid4()

        # Act
        employee = employee_service.assign_team(
            fake_id,
            team_id,
            changed_by_user_id=user_id,
        )

        # Assert
        assert employee is None

    def test_assign_team_team_not_found(self, employee_service, db_session):
        """Should raise ValueError if team doesn't exist."""
        # Arrange
        employee = Employee(
            name="John Doe",
            email="john@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        db_session.add(employee)
        db_session.commit()

        fake_team_id = uuid4()
        user_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="Team with ID .* does not exist"):
            employee_service.assign_team(
                employee.id,
                fake_team_id,
                changed_by_user_id=user_id,
            )

    def test_assign_team_removes_employee_as_lead(self, employee_service, db_session):
        """Should remove employee as team lead when changing teams."""
        # Arrange - Create departments
        department = Department(name="Engineering")
        db_session.add(department)
        db_session.flush()

        # Create two teams
        team1 = Team(name="Team 1", department_id=department.id)
        team2 = Team(name="Team 2", department_id=department.id)
        db_session.add_all([team1, team2])
        db_session.flush()

        # Create employee who is lead of team1
        employee = Employee(
            name="John Doe",
            email="john@example.com",
            status=EmployeeStatus.ACTIVE,
            team_id=team1.id,
        )
        db_session.add(employee)
        db_session.flush()

        # Make employee the lead of team1
        team1.lead_id = employee.id
        db_session.commit()

        # Store team1 ID for later query
        team1_id = team1.id
        user_id = uuid4()

        # Act - Change to team2
        result = employee_service.assign_team(
            employee.id,
            team2.id,
            changed_by_user_id=user_id,
        )

        # Assert
        assert result is not None
        assert result.team_id == team2.id
        # Employee should be removed as lead of team1
        db_session.flush()
        team1_updated = db_session.get(Team, team1_id)
        assert team1_updated.lead_id is None

    def test_assign_team_removes_employee_as_lead_when_removing_team(self, employee_service, db_session):
        """Should remove employee as team lead when removing team assignment."""
        # Arrange
        department = Department(name="Engineering")
        db_session.add(department)
        db_session.flush()

        team = Team(name="Team 1", department_id=department.id)
        db_session.add(team)
        db_session.flush()

        # Create employee who is lead of team
        employee = Employee(
            name="John Doe",
            email="john@example.com",
            status=EmployeeStatus.ACTIVE,
            team_id=team.id,
        )
        db_session.add(employee)
        db_session.flush()

        # Make employee the lead
        team.lead_id = employee.id
        db_session.commit()

        # Store team ID for later query
        team_id = team.id
        user_id = uuid4()

        # Act - Remove team
        result = employee_service.assign_team(
            employee.id,
            None,
            changed_by_user_id=user_id,
        )

        # Assert
        assert result is not None
        assert result.team_id is None
        # Employee should be removed as lead
        db_session.flush()
        team_updated = db_session.get(Team, team_id)
        assert team_updated.lead_id is None

    def test_assign_team_not_lead_no_team_update(self, employee_service, db_session):
        """Should not update team when employee is not the lead."""
        # Arrange
        department = Department(name="Engineering")
        db_session.add(department)
        db_session.flush()

        team1 = Team(name="Team 1", department_id=department.id)
        team2 = Team(name="Team 2", department_id=department.id)
        db_session.add_all([team1, team2])
        db_session.flush()

        # Create employee on team1 but not as lead
        employee = Employee(
            name="John Doe",
            email="john@example.com",
            status=EmployeeStatus.ACTIVE,
            team_id=team1.id,
        )
        db_session.add(employee)
        db_session.commit()

        # team1.lead_id should remain None
        user_id = uuid4()

        # Act - Change to team2
        result = employee_service.assign_team(
            employee.id,
            team2.id,
            changed_by_user_id=user_id,
        )

        # Assert
        assert result is not None
        assert result.team_id == team2.id
        # Team1's lead should still be None
        db_session.refresh(team1)
        assert team1.lead_id is None

    def test_assign_team_creates_audit_log(self, employee_service, db_session):
        """Should create audit log entry when assigning team."""
        # Arrange
        from models.AuditLogModel import AuditLog, EntityType, ChangeType

        department = Department(name="Engineering")
        db_session.add(department)
        db_session.flush()

        team = Team(name="Backend Team", department_id=department.id)
        db_session.add(team)
        db_session.flush()

        employee = Employee(
            name="John Doe",
            email="john@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        db_session.add(employee)
        db_session.commit()

        user_id = uuid4()

        # Act
        employee_service.assign_team(
            employee.id,
            team.id,
            changed_by_user_id=user_id,
        )

        # Assert - Check audit logs were created (one for team, one for department)
        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.entity_type == EntityType.EMPLOYEE,
            AuditLog.entity_id == employee.id,
            AuditLog.change_type == ChangeType.UPDATE,
        ).order_by(AuditLog.created_at).all()

        # Should have 2 logs: team assignment + department auto-assignment
        assert len(audit_logs) == 2

        # First log: team assignment
        team_log = audit_logs[0]
        assert team_log.changed_by_user_id == user_id
        assert team_log.previous_state["team_id"] is None
        assert team_log.new_state["team_id"] == str(team.id)

        # Second log: department assignment (auto-set to match team's department)
        dept_log = audit_logs[1]
        assert dept_log.changed_by_user_id == user_id
        assert dept_log.previous_state["department_id"] is None
        assert dept_log.new_state["department_id"] == str(department.id)

    def test_assign_team_creates_two_audit_logs_when_lead(self, employee_service, db_session):
        """Should create audit logs for both employee and team when removing as lead."""
        # Arrange
        from models.AuditLogModel import AuditLog, EntityType, ChangeType

        department = Department(name="Engineering")
        db_session.add(department)
        db_session.flush()

        team1 = Team(name="Team 1", department_id=department.id)
        team2 = Team(name="Team 2", department_id=department.id)
        db_session.add_all([team1, team2])
        db_session.flush()

        # Create employee who is lead of team1 with department set
        employee = Employee(
            name="John Doe",
            email="john@example.com",
            status=EmployeeStatus.ACTIVE,
            team_id=team1.id,
            department_id=department.id,  # Set department to match team
        )
        db_session.add(employee)
        db_session.flush()

        team1.lead_id = employee.id
        db_session.commit()

        user_id = uuid4()

        # Act - Change to team2 (should remove as lead of team1)
        employee_service.assign_team(
            employee.id,
            team2.id,
            changed_by_user_id=user_id,
        )

        # Assert - Check employee audit log (only team change, no dept change since same dept)
        employee_logs = db_session.query(AuditLog).filter(
            AuditLog.entity_type == EntityType.EMPLOYEE,
            AuditLog.entity_id == employee.id,
        ).all()
        assert len(employee_logs) == 1

        # Assert - Check team audit log
        team_logs = db_session.query(AuditLog).filter(
            AuditLog.entity_type == EntityType.TEAM,
            AuditLog.entity_id == team1.id,
        ).all()
        assert len(team_logs) == 1
        assert team_logs[0].change_type == ChangeType.UPDATE
        assert team_logs[0].previous_state["lead_id"] == str(employee.id)
        assert team_logs[0].new_state["lead_id"] is None

    def test_assign_team_audit_log_tracks_previous_value(self, employee_service, db_session):
        """Should track previous team_id in audit log."""
        # Arrange
        from models.AuditLogModel import AuditLog, EntityType

        department = Department(name="Engineering")
        db_session.add(department)
        db_session.flush()

        old_team = Team(name="Old Team", department_id=department.id)
        new_team = Team(name="New Team", department_id=department.id)
        db_session.add_all([old_team, new_team])
        db_session.flush()

        employee = Employee(
            name="John Doe",
            email="john@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        db_session.add(employee)
        db_session.commit()

        user_id = uuid4()

        # Assign initial team
        employee_service.assign_team(employee.id, old_team.id, changed_by_user_id=user_id)
        db_session.flush()

        # Act - Change to new team
        employee_service.assign_team(employee.id, new_team.id, changed_by_user_id=user_id)

        # Assert - Check audit logs
        # First assignment creates 2 logs (team + dept), second creates 1 log (team only)
        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.entity_type == EntityType.EMPLOYEE,
            AuditLog.entity_id == employee.id,
        ).order_by(AuditLog.created_at).all()

        assert len(audit_logs) == 3

        # First log: initial team assignment
        assert audit_logs[0].previous_state["team_id"] is None
        assert audit_logs[0].new_state["team_id"] == str(old_team.id)

        # Second log: initial department assignment (auto-set)
        assert audit_logs[1].previous_state["department_id"] is None
        assert audit_logs[1].new_state["department_id"] == str(department.id)

        # Third log: team reassignment (no dept change since same dept)
        assert audit_logs[2].previous_state["team_id"] == str(old_team.id)
        assert audit_logs[2].new_state["team_id"] == str(new_team.id)

    def test_assign_team_does_not_commit(self, employee_service, db_session):
        """Should not commit transaction (router's responsibility)."""
        # Arrange
        department = Department(name="Engineering")
        db_session.add(department)
        db_session.flush()

        team = Team(name="Backend Team", department_id=department.id)
        db_session.add(team)
        db_session.flush()

        employee = Employee(
            name="John Doe",
            email="john@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        db_session.add(employee)
        db_session.commit()

        user_id = uuid4()

        # Act
        employee_service.assign_team(
            employee.id,
            team.id,
            changed_by_user_id=user_id,
        )
        db_session.rollback()

        # Assert - Changes should be rolled back
        db_session.refresh(employee)
        assert employee.team_id is None


class TestDeleteEmployee:
    """Tests for EmployeeService.delete_employee() method."""

    def test_delete_employee_success(self, employee_service, db_session):
        """Should delete employee without direct reports."""
        # Arrange
        ceo = Employee(
            name="CEO",
            email="ceo@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        employee = Employee(
            name="John Doe",
            email="john@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        db_session.add_all([ceo, employee])
        db_session.flush()

        employee.manager_id = ceo.id
        db_session.commit()

        employee_id = employee.id
        user_id = uuid4()

        # Act
        result = employee_service.delete_employee(
            employee_id,
            changed_by_user_id=user_id,
        )

        # Assert
        assert result is not None
        assert result.id == employee_id

        # Verify employee is deleted (pending commit)
        db_session.flush()
        deleted = db_session.get(Employee, employee_id)
        assert deleted is None

    def test_delete_employee_with_direct_reports(self, employee_service, db_session):
        """Should delete employee and reassign direct reports to employee's manager."""
        # Arrange
        ceo = Employee(
            name="CEO",
            email="ceo@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        manager = Employee(
            name="Manager",
            email="manager@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        direct_report1 = Employee(
            name="Report 1",
            email="report1@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        direct_report2 = Employee(
            name="Report 2",
            email="report2@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        db_session.add_all([ceo, manager, direct_report1, direct_report2])
        db_session.flush()

        manager.manager_id = ceo.id
        direct_report1.manager_id = manager.id
        direct_report2.manager_id = manager.id
        db_session.commit()

        manager_id = manager.id
        ceo_id = ceo.id
        report1_id = direct_report1.id
        report2_id = direct_report2.id
        user_id = uuid4()

        # Act
        result = employee_service.delete_employee(
            manager_id,
            changed_by_user_id=user_id,
        )

        # Assert
        assert result is not None

        # Verify direct reports are reassigned to manager's manager (CEO)
        db_session.flush()
        report1_updated = db_session.get(Employee, report1_id)
        report2_updated = db_session.get(Employee, report2_id)
        assert report1_updated.manager_id == ceo_id
        assert report2_updated.manager_id == ceo_id

    def test_delete_employee_not_found(self, employee_service, db_session):
        """Should return None when employee doesn't exist."""
        # Arrange
        non_existent_id = uuid4()
        user_id = uuid4()

        # Act
        result = employee_service.delete_employee(
            non_existent_id,
            changed_by_user_id=user_id,
        )

        # Assert
        assert result is None

    def test_delete_employee_ceo_raises_error(self, employee_service, db_session):
        """Should raise ValueError when trying to delete CEO."""
        # Arrange
        ceo = Employee(
            name="CEO",
            email="ceo@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        db_session.add(ceo)
        db_session.commit()

        user_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="CEO cannot be deleted, only replaced"):
            employee_service.delete_employee(
                ceo.id,
                changed_by_user_id=user_id,
            )

    def test_delete_employee_creates_audit_log(self, employee_service, db_session):
        """Should create audit log for deleted employee."""
        # Arrange
        ceo = Employee(
            name="CEO",
            email="ceo@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        employee = Employee(
            name="John Doe",
            email="john@example.com",
            title="Engineer",
            status=EmployeeStatus.ACTIVE,
            salary=100000,
        )
        db_session.add_all([ceo, employee])
        db_session.flush()

        employee.manager_id = ceo.id
        db_session.commit()

        employee_id = employee.id
        user_id = uuid4()

        # Act
        employee_service.delete_employee(
            employee_id,
            changed_by_user_id=user_id,
        )

        # Assert - Check audit log was created
        audit_logs = db_session.execute(
            select(AuditLog).where(
                AuditLog.entity_type == EntityType.EMPLOYEE,
                AuditLog.entity_id == employee_id,
                AuditLog.change_type == ChangeType.DELETE,
            )
        ).scalars().all()

        assert len(audit_logs) == 1
        audit_log = audit_logs[0]
        assert audit_log.changed_by_user_id == user_id
        assert audit_log.previous_state["name"] == "John Doe"
        assert audit_log.previous_state["title"] == "Engineer"
        assert audit_log.previous_state["email"] == "john@example.com"
        assert audit_log.previous_state["salary"] == 100000
        assert audit_log.previous_state["status"] == EmployeeStatus.ACTIVE.value
        assert audit_log.new_state is None

    def test_delete_employee_creates_audit_logs_for_reassigned_reports(self, employee_service, db_session):
        """Should create audit logs for each reassigned direct report."""
        # Arrange
        ceo = Employee(
            name="CEO",
            email="ceo@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        manager = Employee(
            name="Manager",
            email="manager@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        direct_report1 = Employee(
            name="Report 1",
            email="report1@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        direct_report2 = Employee(
            name="Report 2",
            email="report2@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        db_session.add_all([ceo, manager, direct_report1, direct_report2])
        db_session.flush()

        manager.manager_id = ceo.id
        direct_report1.manager_id = manager.id
        direct_report2.manager_id = manager.id
        db_session.commit()

        manager_id = manager.id
        ceo_id = ceo.id
        report1_id = direct_report1.id
        report2_id = direct_report2.id
        user_id = uuid4()

        # Act
        employee_service.delete_employee(
            manager_id,
            changed_by_user_id=user_id,
        )

        # Assert - Check audit logs for direct reports
        report1_logs = db_session.execute(
            select(AuditLog).where(
                AuditLog.entity_type == EntityType.EMPLOYEE,
                AuditLog.entity_id == report1_id,
                AuditLog.change_type == ChangeType.UPDATE,
            )
        ).scalars().all()

        report2_logs = db_session.execute(
            select(AuditLog).where(
                AuditLog.entity_type == EntityType.EMPLOYEE,
                AuditLog.entity_id == report2_id,
                AuditLog.change_type == ChangeType.UPDATE,
            )
        ).scalars().all()

        assert len(report1_logs) == 1
        assert len(report2_logs) == 1

        assert report1_logs[0].previous_state["manager_id"] == str(manager_id)
        assert report1_logs[0].new_state["manager_id"] == str(ceo_id)

        assert report2_logs[0].previous_state["manager_id"] == str(manager_id)
        assert report2_logs[0].new_state["manager_id"] == str(ceo_id)

    def test_delete_employee_does_not_commit(self, employee_service, db_session):
        """Should not commit transaction."""
        # Arrange
        ceo = Employee(
            name="CEO",
            email="ceo@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        employee = Employee(
            name="John Doe",
            email="john@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        db_session.add_all([ceo, employee])
        db_session.flush()

        employee.manager_id = ceo.id
        db_session.commit()

        employee_id = employee.id
        user_id = uuid4()

        # Act
        employee_service.delete_employee(
            employee_id,
            changed_by_user_id=user_id,
        )

        # Rollback to verify it wasn't committed
        db_session.rollback()

        # Assert - Employee should still exist after rollback
        employee_still_exists = db_session.get(Employee, employee_id)
        assert employee_still_exists is not None


class TestAssignManager:
    """Tests for EmployeeService.assign_manager() method."""

    def test_assign_manager_success(self, employee_service, db_session):
        """Should assign manager to employee."""
        # Arrange - Create CEO and two employees
        ceo = Employee(
            name="CEO",
            email="ceo@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        manager = Employee(
            name="Manager",
            email="manager@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        employee = Employee(
            name="Employee",
            email="employee@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        db_session.add_all([ceo, manager, employee])
        db_session.flush()

        # Set initial managers
        manager.manager_id = ceo.id
        employee.manager_id = ceo.id
        db_session.commit()

        user_id = uuid4()

        # Act - Reassign employee from CEO to Manager
        result = employee_service.assign_manager(
            employee.id,
            manager.id,
            changed_by_user_id=user_id,
        )

        # Assert
        assert result is not None
        assert result.manager_id == manager.id

        # Verify in database (flush to make changes visible)
        db_session.flush()
        db_session.refresh(employee)
        assert employee.manager_id == manager.id

    def test_assign_manager_to_employee_with_no_manager(self, employee_service, db_session):
        """Should assign first manager to employee who has none."""
        # Arrange - Create two employees, one is CEO
        ceo = Employee(
            name="CEO",
            email="ceo@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        employee = Employee(
            name="Employee",
            email="employee@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,  # No manager initially
        )
        db_session.add_all([ceo, employee])
        db_session.commit()

        user_id = uuid4()

        # Act
        result = employee_service.assign_manager(
            employee.id,
            ceo.id,
            changed_by_user_id=user_id,
        )

        # Assert
        assert result is not None
        assert result.manager_id == ceo.id

    def test_assign_manager_employee_with_direct_reports(self, employee_service, db_session):
        """Should assign manager to employee who has direct reports (reports stay with employee)."""
        # Arrange - Create hierarchy: CEO -> Manager1, Employee -> Direct Report
        ceo = Employee(
            name="CEO",
            email="ceo@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        manager1 = Employee(
            name="Manager 1",
            email="manager1@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        employee = Employee(
            name="Employee",
            email="employee@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        direct_report = Employee(
            name="Direct Report",
            email="report@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        db_session.add_all([ceo, manager1, employee, direct_report])
        db_session.flush()

        # Set initial hierarchy: CEO -> Manager1, CEO -> Employee -> Direct Report
        manager1.manager_id = ceo.id
        employee.manager_id = ceo.id
        direct_report.manager_id = employee.id
        db_session.commit()

        user_id = uuid4()

        # Act - Reassign employee to Manager1
        result = employee_service.assign_manager(
            employee.id,
            manager1.id,
            changed_by_user_id=user_id,
        )

        # Assert
        assert result is not None
        assert result.manager_id == manager1.id

        # Verify direct report still reports to employee
        db_session.refresh(direct_report)
        assert direct_report.manager_id == employee.id

    def test_assign_manager_employee_not_found(self, employee_service, db_session):
        """Should return None when employee does not exist."""
        # Arrange
        fake_employee_id = uuid4()
        fake_manager_id = uuid4()
        user_id = uuid4()

        # Act
        result = employee_service.assign_manager(
            fake_employee_id,
            fake_manager_id,
            changed_by_user_id=user_id,
        )

        # Assert
        assert result is None

    def test_assign_manager_manager_not_found(self, employee_service, db_session):
        """Should raise ValueError when new manager does not exist."""
        # Arrange - Create employee
        employee = Employee(
            name="Employee",
            email="employee@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        db_session.add(employee)
        db_session.commit()

        fake_manager_id = uuid4()
        user_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="Manager with ID .* does not exist"):
            employee_service.assign_manager(
                employee.id,
                fake_manager_id,
                changed_by_user_id=user_id,
            )

    def test_assign_manager_self_management(self, employee_service, db_session):
        """Should raise ValueError when employee tries to be their own manager."""
        # Arrange - Create employee
        employee = Employee(
            name="Employee",
            email="employee@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        db_session.add(employee)
        db_session.commit()

        user_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="circular dependency"):
            employee_service.assign_manager(
                employee.id,
                employee.id,  # Self-management
                changed_by_user_id=user_id,
            )

    def test_assign_manager_direct_circular_dependency(self, employee_service, db_session):
        """Should raise ValueError for direct circular dependency (A->B, trying B->A)."""
        # Arrange - Create hierarchy: A -> B
        employee_a = Employee(
            name="Employee A",
            email="a@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        employee_b = Employee(
            name="Employee B",
            email="b@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        db_session.add_all([employee_a, employee_b])
        db_session.flush()

        # A -> B (B reports to A)
        employee_b.manager_id = employee_a.id
        db_session.commit()

        user_id = uuid4()

        # Act & Assert - Try to make A report to B (would create cycle)
        with pytest.raises(ValueError, match="circular dependency"):
            employee_service.assign_manager(
                employee_a.id,
                employee_b.id,
                changed_by_user_id=user_id,
            )

    def test_assign_manager_three_level_circular_dependency(self, employee_service, db_session):
        """Should raise ValueError for 3-level circular dependency (A->B->C, trying C->A)."""
        # Arrange - Create hierarchy: A -> B -> C
        employee_a = Employee(
            name="Employee A",
            email="a@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        employee_b = Employee(
            name="Employee B",
            email="b@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        employee_c = Employee(
            name="Employee C",
            email="c@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        db_session.add_all([employee_a, employee_b, employee_c])
        db_session.flush()

        # A -> B -> C
        employee_b.manager_id = employee_a.id
        employee_c.manager_id = employee_b.id
        db_session.commit()

        user_id = uuid4()

        # Act & Assert - Try to make A report to C (would create cycle)
        with pytest.raises(ValueError, match="circular dependency"):
            employee_service.assign_manager(
                employee_a.id,
                employee_c.id,
                changed_by_user_id=user_id,
            )

    def test_assign_manager_deep_circular_dependency_five_levels(self, employee_service, db_session):
        """Should raise ValueError for deep 5-level circular dependency (A->B->C->D->E, trying E->A)."""
        # Arrange - Create hierarchy: A -> B -> C -> D -> E
        employees = []
        for letter in ['A', 'B', 'C', 'D', 'E']:
            emp = Employee(
                name=f"Employee {letter}",
                email=f"{letter.lower()}@example.com",
                status=EmployeeStatus.ACTIVE,
                manager_id=None,
            )
            employees.append(emp)
            db_session.add(emp)
        db_session.flush()

        # Create chain: A -> B -> C -> D -> E
        for i in range(1, len(employees)):
            employees[i].manager_id = employees[i-1].id
        db_session.commit()

        user_id = uuid4()

        # Act & Assert - Try to make A report to E (would create deep cycle)
        with pytest.raises(ValueError, match="circular dependency"):
            employee_service.assign_manager(
                employees[0].id,  # Employee A
                employees[4].id,  # Employee E
                changed_by_user_id=user_id,
            )

    def test_assign_manager_middle_node_circular_dependency(self, employee_service, db_session):
        """Should raise ValueError for circular dependency at middle node (A->B->C->D, trying B->D)."""
        # Arrange - Create hierarchy: A -> B -> C -> D
        employee_a = Employee(
            name="Employee A",
            email="a@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        employee_b = Employee(
            name="Employee B",
            email="b@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        employee_c = Employee(
            name="Employee C",
            email="c@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        employee_d = Employee(
            name="Employee D",
            email="d@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        db_session.add_all([employee_a, employee_b, employee_c, employee_d])
        db_session.flush()

        # A -> B -> C -> D
        employee_b.manager_id = employee_a.id
        employee_c.manager_id = employee_b.id
        employee_d.manager_id = employee_c.id
        db_session.commit()

        user_id = uuid4()

        # Act & Assert - Try to make B report to D (would create cycle B->C->D->B)
        with pytest.raises(ValueError, match="circular dependency"):
            employee_service.assign_manager(
                employee_b.id,
                employee_d.id,
                changed_by_user_id=user_id,
            )

    def test_assign_manager_complex_valid_reassignment(self, employee_service, db_session):
        """Should allow valid reassignment in complex hierarchy without creating cycle."""
        # Arrange - Create hierarchy:
        #     CEO
        #    /   \
        #   A     B
        #   |     |
        #   C     D
        ceo = Employee(name="CEO", email="ceo@example.com", status=EmployeeStatus.ACTIVE, manager_id=None)
        emp_a = Employee(name="Employee A", email="a@example.com", status=EmployeeStatus.ACTIVE)
        emp_b = Employee(name="Employee B", email="b@example.com", status=EmployeeStatus.ACTIVE)
        emp_c = Employee(name="Employee C", email="c@example.com", status=EmployeeStatus.ACTIVE)
        emp_d = Employee(name="Employee D", email="d@example.com", status=EmployeeStatus.ACTIVE)

        db_session.add_all([ceo, emp_a, emp_b, emp_c, emp_d])
        db_session.flush()

        emp_a.manager_id = ceo.id
        emp_b.manager_id = ceo.id
        emp_c.manager_id = emp_a.id
        emp_d.manager_id = emp_b.id
        db_session.commit()

        user_id = uuid4()

        # Act - Move D from B's branch to A's branch (valid, no cycle)
        result = employee_service.assign_manager(
            emp_d.id,
            emp_a.id,
            changed_by_user_id=user_id,
        )

        # Assert
        assert result is not None
        assert result.manager_id == emp_a.id

        # Verify in database (flush to make changes visible)
        db_session.flush()
        db_session.refresh(emp_d)
        assert emp_d.manager_id == emp_a.id

    def test_assign_manager_sibling_to_sibling_valid(self, employee_service, db_session):
        """Should allow assigning sibling as manager (both report to same manager initially)."""
        # Arrange - Create hierarchy: CEO -> A, CEO -> B
        ceo = Employee(name="CEO", email="ceo@example.com", status=EmployeeStatus.ACTIVE, manager_id=None)
        emp_a = Employee(name="Employee A", email="a@example.com", status=EmployeeStatus.ACTIVE)
        emp_b = Employee(name="Employee B", email="b@example.com", status=EmployeeStatus.ACTIVE)

        db_session.add_all([ceo, emp_a, emp_b])
        db_session.flush()

        emp_a.manager_id = ceo.id
        emp_b.manager_id = ceo.id
        db_session.commit()

        user_id = uuid4()

        # Act - Make B report to A (both were siblings)
        result = employee_service.assign_manager(
            emp_b.id,
            emp_a.id,
            changed_by_user_id=user_id,
        )

        # Assert
        assert result is not None
        assert result.manager_id == emp_a.id

        # A should still report to CEO
        db_session.refresh(emp_a)
        assert emp_a.manager_id == ceo.id

    def test_assign_manager_creates_audit_log(self, employee_service, db_session):
        """Should create audit log entry for manager assignment."""
        # Arrange
        ceo = Employee(name="CEO", email="ceo@example.com", status=EmployeeStatus.ACTIVE, manager_id=None)
        manager = Employee(name="Manager", email="manager@example.com", status=EmployeeStatus.ACTIVE)
        employee = Employee(name="Employee", email="employee@example.com", status=EmployeeStatus.ACTIVE)

        db_session.add_all([ceo, manager, employee])
        db_session.flush()

        manager.manager_id = ceo.id
        employee.manager_id = ceo.id
        db_session.commit()

        user_id = uuid4()

        # Act
        employee_service.assign_manager(
            employee.id,
            manager.id,
            changed_by_user_id=user_id,
        )
        db_session.flush()

        # Assert - Verify audit log was created
        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.entity_type == EntityType.EMPLOYEE,
            AuditLog.entity_id == employee.id,
            AuditLog.change_type == ChangeType.UPDATE,
        ).all()

        assert len(audit_logs) == 1
        assert audit_logs[0].changed_by_user_id == user_id
        assert audit_logs[0].previous_state["manager_id"] == str(ceo.id)
        assert audit_logs[0].new_state["manager_id"] == str(manager.id)

    def test_assign_manager_audit_log_tracks_previous_value(self, employee_service, db_session):
        """Should track previous manager_id in audit log."""
        # Arrange
        ceo = Employee(name="CEO", email="ceo@example.com", status=EmployeeStatus.ACTIVE, manager_id=None)
        old_manager = Employee(name="Old Manager", email="old@example.com", status=EmployeeStatus.ACTIVE)
        new_manager = Employee(name="New Manager", email="new@example.com", status=EmployeeStatus.ACTIVE)
        employee = Employee(name="Employee", email="employee@example.com", status=EmployeeStatus.ACTIVE)

        db_session.add_all([ceo, old_manager, new_manager, employee])
        db_session.flush()

        old_manager.manager_id = ceo.id
        new_manager.manager_id = ceo.id
        employee.manager_id = old_manager.id
        db_session.commit()

        old_manager_id = old_manager.id
        user_id = uuid4()

        # Act - Reassign from old_manager to new_manager
        employee_service.assign_manager(
            employee.id,
            new_manager.id,
            changed_by_user_id=user_id,
        )
        db_session.flush()

        # Assert - Verify audit log captured old manager
        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.entity_type == EntityType.EMPLOYEE,
            AuditLog.entity_id == employee.id,
        ).all()

        assert len(audit_logs) == 1
        assert audit_logs[0].previous_state["manager_id"] == str(old_manager_id)
        assert audit_logs[0].new_state["manager_id"] == str(new_manager.id)

    def test_assign_manager_does_not_commit(self, employee_service, db_session):
        """Should not commit transaction (router's responsibility)."""
        # Arrange
        ceo = Employee(name="CEO", email="ceo@example.com", status=EmployeeStatus.ACTIVE, manager_id=None)
        manager = Employee(name="Manager", email="manager@example.com", status=EmployeeStatus.ACTIVE)
        employee = Employee(name="Employee", email="employee@example.com", status=EmployeeStatus.ACTIVE)

        db_session.add_all([ceo, manager, employee])
        db_session.flush()

        manager.manager_id = ceo.id
        employee.manager_id = ceo.id
        db_session.commit()

        user_id = uuid4()

        # Act
        employee_service.assign_manager(
            employee.id,
            manager.id,
            changed_by_user_id=user_id,
        )

        # Rollback to verify service didn't commit
        db_session.rollback()

        # Assert - Changes should be rolled back
        db_session.refresh(employee)
        assert employee.manager_id == ceo.id  # Should still be CEO, not manager


class TestReplaceCEO:
    """Tests for EmployeeService.replace_ceo() method."""

    def test_replace_ceo_success(self, employee_service, db_session):
        """Should create new CEO and reassign old CEO as subordinate."""
        # Arrange - Create current CEO
        old_ceo = Employee(
            name="Old CEO",
            email="old@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        db_session.add(old_ceo)
        db_session.commit()

        old_ceo_id = old_ceo.id
        user_id = uuid4()

        # Act
        new_ceo = employee_service.replace_ceo(
            name="New CEO",
            email="new@example.com",
            title="Chief Executive Officer",
            salary=300000,
            changed_by_user_id=user_id,
        )

        # Assert
        assert new_ceo is not None
        assert new_ceo.name == "New CEO"
        assert new_ceo.email == "new@example.com"
        assert new_ceo.manager_id is None

        # Old CEO should now report to new CEO
        db_session.refresh(old_ceo)
        assert old_ceo.manager_id == new_ceo.id

    def test_replace_ceo_no_ceo_exists(self, employee_service, db_session):
        """Should raise ValueError when no current CEO exists."""
        # Arrange
        user_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="No current CEO exists to replace"):
            employee_service.replace_ceo(
                name="New CEO",
                email="new@example.com",
                changed_by_user_id=user_id,
            )

    def test_replace_ceo_with_direct_reports(self, employee_service, db_session):
        """Should reassign old CEO's direct reports to new CEO."""
        # Arrange - Create CEO with direct reports
        old_ceo = Employee(
            name="Old CEO",
            email="old@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        db_session.add(old_ceo)
        db_session.flush()

        report1 = Employee(
            name="Report 1",
            email="report1@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=old_ceo.id,
        )
        report2 = Employee(
            name="Report 2",
            email="report2@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=old_ceo.id,
        )
        db_session.add_all([report1, report2])
        db_session.commit()

        report1_id = report1.id
        report2_id = report2.id
        user_id = uuid4()

        # Act
        new_ceo = employee_service.replace_ceo(
            name="New CEO",
            email="new@example.com",
            changed_by_user_id=user_id,
        )

        # Assert - Direct reports should now report to new CEO
        db_session.flush()
        report1_updated = db_session.get(Employee, report1_id)
        report2_updated = db_session.get(Employee, report2_id)
        assert report1_updated.manager_id == new_ceo.id
        assert report2_updated.manager_id == new_ceo.id

    def test_replace_ceo_invalid_department(self, employee_service, db_session):
        """Should raise ValueError if department doesn't exist."""
        # Arrange - Create CEO
        old_ceo = Employee(
            name="Old CEO",
            email="old@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        db_session.add(old_ceo)
        db_session.commit()

        fake_dept_id = uuid4()
        user_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="Department with ID .* does not exist"):
            employee_service.replace_ceo(
                name="New CEO",
                email="new@example.com",
                department_id=fake_dept_id,
                changed_by_user_id=user_id,
            )

    def test_replace_ceo_invalid_team(self, employee_service, db_session):
        """Should raise ValueError if team doesn't exist."""
        # Arrange - Create CEO
        old_ceo = Employee(
            name="Old CEO",
            email="old@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        db_session.add(old_ceo)
        db_session.commit()

        fake_team_id = uuid4()
        user_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="Team with ID .* does not exist"):
            employee_service.replace_ceo(
                name="New CEO",
                email="new@example.com",
                team_id=fake_team_id,
                changed_by_user_id=user_id,
            )

    def test_replace_ceo_with_valid_department_and_team(self, employee_service, db_session):
        """Should create new CEO with department and team."""
        # Arrange - Create CEO
        old_ceo = Employee(
            name="Old CEO",
            email="old@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        db_session.add(old_ceo)
        db_session.flush()

        department = Department(name="Executive")
        db_session.add(department)
        db_session.flush()

        team = Team(name="Leadership", department_id=department.id)
        db_session.add(team)
        db_session.commit()

        user_id = uuid4()

        # Act
        new_ceo = employee_service.replace_ceo(
            name="New CEO",
            email="new@example.com",
            department_id=department.id,
            team_id=team.id,
            changed_by_user_id=user_id,
        )

        # Assert
        assert new_ceo is not None
        assert new_ceo.department_id == department.id
        assert new_ceo.team_id == team.id

    def test_replace_ceo_links_to_existing_user(self, employee_service, db_session):
        """Should link new CEO to user with matching email."""
        # Arrange - Create CEO and user
        old_ceo = Employee(
            name="Old CEO",
            email="old@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        user = User(
            email="new@example.com",
            name="New User",
        )
        db_session.add_all([old_ceo, user])
        db_session.commit()

        user_id = uuid4()

        # Act
        new_ceo = employee_service.replace_ceo(
            name="New CEO",
            email="new@example.com",  # Matches user email
            changed_by_user_id=user_id,
        )

        # Flush and refresh user to see link
        db_session.flush()
        db_session.refresh(user)

        # Assert
        assert new_ceo is not None
        assert user.employee_id == new_ceo.id

    def test_replace_ceo_creates_audit_log_for_new_ceo(self, employee_service, db_session):
        """Should create CREATE audit log for new CEO."""
        # Arrange
        old_ceo = Employee(
            name="Old CEO",
            email="old@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        db_session.add(old_ceo)
        db_session.commit()

        user_id = uuid4()

        # Act
        new_ceo = employee_service.replace_ceo(
            name="New CEO",
            email="new@example.com",
            title="Chief Executive Officer",
            salary=300000,
            changed_by_user_id=user_id,
        )

        # Assert - Check audit log for new CEO
        audit_logs = db_session.execute(
            select(AuditLog).where(
                AuditLog.entity_type == EntityType.EMPLOYEE,
                AuditLog.entity_id == new_ceo.id,
                AuditLog.change_type == ChangeType.CREATE,
            )
        ).scalars().all()

        assert len(audit_logs) == 1
        log = audit_logs[0]
        assert log.changed_by_user_id == user_id
        assert log.previous_state is None
        assert log.new_state["name"] == "New CEO"
        assert log.new_state["email"] == "new@example.com"
        assert log.new_state["title"] == "Chief Executive Officer"
        assert log.new_state["salary"] == 300000
        assert log.new_state["manager_id"] is None

    def test_replace_ceo_creates_audit_log_for_old_ceo(self, employee_service, db_session):
        """Should create UPDATE audit log for old CEO."""
        # Arrange
        old_ceo = Employee(
            name="Old CEO",
            email="old@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        db_session.add(old_ceo)
        db_session.commit()

        old_ceo_id = old_ceo.id
        user_id = uuid4()

        # Act
        new_ceo = employee_service.replace_ceo(
            name="New CEO",
            email="new@example.com",
            changed_by_user_id=user_id,
        )

        # Assert - Check audit log for old CEO
        audit_logs = db_session.execute(
            select(AuditLog).where(
                AuditLog.entity_type == EntityType.EMPLOYEE,
                AuditLog.entity_id == old_ceo_id,
                AuditLog.change_type == ChangeType.UPDATE,
            )
        ).scalars().all()

        assert len(audit_logs) == 1
        log = audit_logs[0]
        assert log.changed_by_user_id == user_id
        assert log.previous_state["manager_id"] is None
        assert log.new_state["manager_id"] == str(new_ceo.id)

    def test_replace_ceo_creates_audit_logs_for_reassigned_reports(self, employee_service, db_session):
        """Should create UPDATE audit logs for each reassigned direct report."""
        # Arrange
        old_ceo = Employee(
            name="Old CEO",
            email="old@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        db_session.add(old_ceo)
        db_session.flush()

        old_ceo_id = old_ceo.id

        report1 = Employee(
            name="Report 1",
            email="report1@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=old_ceo.id,
        )
        report2 = Employee(
            name="Report 2",
            email="report2@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=old_ceo.id,
        )
        db_session.add_all([report1, report2])
        db_session.commit()

        report1_id = report1.id
        report2_id = report2.id
        user_id = uuid4()

        # Act
        new_ceo = employee_service.replace_ceo(
            name="New CEO",
            email="new@example.com",
            changed_by_user_id=user_id,
        )

        # Assert - Check audit logs for reassigned reports
        report1_logs = db_session.execute(
            select(AuditLog).where(
                AuditLog.entity_type == EntityType.EMPLOYEE,
                AuditLog.entity_id == report1_id,
                AuditLog.change_type == ChangeType.UPDATE,
            )
        ).scalars().all()

        report2_logs = db_session.execute(
            select(AuditLog).where(
                AuditLog.entity_type == EntityType.EMPLOYEE,
                AuditLog.entity_id == report2_id,
                AuditLog.change_type == ChangeType.UPDATE,
            )
        ).scalars().all()

        assert len(report1_logs) == 1
        assert len(report2_logs) == 1

        assert report1_logs[0].previous_state["manager_id"] == str(old_ceo_id)
        assert report1_logs[0].new_state["manager_id"] == str(new_ceo.id)

        assert report2_logs[0].previous_state["manager_id"] == str(old_ceo_id)
        assert report2_logs[0].new_state["manager_id"] == str(new_ceo.id)

    def test_replace_ceo_creates_audit_log_for_linked_user(self, employee_service, db_session):
        """Should create UPDATE audit log when linking user to new CEO."""
        # Arrange
        old_ceo = Employee(
            name="Old CEO",
            email="old@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        user = User(
            email="new@example.com",
            name="New User",
        )
        db_session.add_all([old_ceo, user])
        db_session.commit()

        user_id_actor = uuid4()

        # Act
        new_ceo = employee_service.replace_ceo(
            name="New CEO",
            email="new@example.com",
            changed_by_user_id=user_id_actor,
        )

        # Assert - Check user audit log
        user_logs = db_session.execute(
            select(AuditLog).where(
                AuditLog.entity_type == EntityType.USER,
                AuditLog.entity_id == user.id,
                AuditLog.change_type == ChangeType.UPDATE,
            )
        ).scalars().all()

        assert len(user_logs) == 1
        log = user_logs[0]
        assert log.changed_by_user_id == user_id_actor
        assert log.previous_state["employee_id"] is None
        assert log.new_state["employee_id"] == str(new_ceo.id)

    def test_replace_ceo_does_not_commit(self, employee_service, db_session):
        """Should not commit transaction."""
        # Arrange
        old_ceo = Employee(
            name="Old CEO",
            email="old@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        db_session.add(old_ceo)
        db_session.commit()

        user_id = uuid4()

        # Act
        employee_service.replace_ceo(
            name="New CEO",
            email="new@example.com",
            changed_by_user_id=user_id,
        )

        # Rollback to verify it wasn't committed
        db_session.rollback()

        # Assert - New CEO should not exist after rollback
        new_ceo_count = db_session.execute(
            select(Employee).where(Employee.email == "new@example.com")
        ).scalars().all()
        assert len(new_ceo_count) == 0

        # Old CEO should still have no manager
        db_session.refresh(old_ceo)
        assert old_ceo.manager_id is None


class TestPromoteEmployeeToCEO:
    """Tests for EmployeeService.promote_employee_to_ceo() method."""

    def test_promote_employee_reporting_to_ceo_success(self, employee_service, db_session):
        """Should promote employee who reports to CEO and reassign CEO's other reports."""
        # Arrange - Create CEO with 2 direct reports
        ceo = Employee(
            name="Old CEO",
            email="ceo@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        db_session.add(ceo)
        db_session.flush()

        employee_to_promote = Employee(
            name="Future CEO",
            email="future@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=ceo.id,
        )
        other_report = Employee(
            name="Other Report",
            email="other@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=ceo.id,
        )
        db_session.add_all([employee_to_promote, other_report])
        db_session.commit()

        promote_id = employee_to_promote.id
        other_id = other_report.id
        user_id = uuid4()

        # Act
        new_ceo = employee_service.promote_employee_to_ceo(
            promote_id,
            changed_by_user_id=user_id,
        )

        # Assert
        assert new_ceo is not None
        assert new_ceo.id == promote_id
        assert new_ceo.manager_id is None

        # Old CEO should now report to new CEO
        db_session.flush()
        db_session.refresh(ceo)
        assert ceo.manager_id == promote_id

        # Other report should now report to new CEO
        db_session.flush()
        other_updated = db_session.get(Employee, other_id)
        assert other_updated.manager_id == promote_id

    def test_promote_employee_not_reporting_to_ceo_success(self, employee_service, db_session):
        """Should promote employee not reporting to CEO and reassign their reports."""
        # Arrange - Create hierarchy: CEO -> Manager -> Employee
        ceo = Employee(
            name="CEO",
            email="ceo@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        db_session.add(ceo)
        db_session.flush()

        manager = Employee(
            name="Manager",
            email="manager@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=ceo.id,
        )
        db_session.add(manager)
        db_session.flush()

        employee_to_promote = Employee(
            name="Future CEO",
            email="future@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=manager.id,
        )
        employee_report = Employee(
            name="Employee's Report",
            email="report@example.com",
            status=EmployeeStatus.ACTIVE,
        )
        db_session.add_all([employee_to_promote, employee_report])
        db_session.flush()

        employee_report.manager_id = employee_to_promote.id
        db_session.commit()

        promote_id = employee_to_promote.id
        manager_id = manager.id
        report_id = employee_report.id
        user_id = uuid4()

        # Act
        new_ceo = employee_service.promote_employee_to_ceo(
            promote_id,
            changed_by_user_id=user_id,
        )

        # Assert
        assert new_ceo is not None
        assert new_ceo.id == promote_id
        assert new_ceo.manager_id is None

        # Employee's report should now report to employee's original manager
        db_session.flush()
        report_updated = db_session.get(Employee, report_id)
        assert report_updated.manager_id == manager_id

        # Manager should now report to new CEO
        manager_updated = db_session.get(Employee, manager_id)
        assert manager_updated.manager_id == promote_id

    def test_promote_employee_no_ceo_exists(self, employee_service, db_session):
        """Should raise ValueError when no CEO exists."""
        # Arrange - No employees in database, so no CEO
        fake_id = uuid4()
        user_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="No current CEO exists"):
            employee_service.promote_employee_to_ceo(
                fake_id,
                changed_by_user_id=user_id,
            )

    def test_promote_employee_not_found(self, employee_service, db_session):
        """Should raise ValueError when employee doesn't exist."""
        # Arrange - Create CEO
        ceo = Employee(
            name="CEO",
            email="ceo@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        db_session.add(ceo)
        db_session.commit()

        fake_id = uuid4()
        user_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="Employee with ID .* does not exist"):
            employee_service.promote_employee_to_ceo(
                fake_id,
                changed_by_user_id=user_id,
            )

    def test_promote_employee_already_ceo(self, employee_service, db_session):
        """Should raise ValueError when trying to promote CEO."""
        # Arrange - Create CEO
        ceo = Employee(
            name="CEO",
            email="ceo@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        db_session.add(ceo)
        db_session.commit()

        user_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="Employee is already CEO"):
            employee_service.promote_employee_to_ceo(
                ceo.id,
                changed_by_user_id=user_id,
            )

    def test_promote_creates_audit_log_for_promoted_employee(self, employee_service, db_session):
        """Should create UPDATE audit log for promoted employee."""
        # Arrange
        ceo = Employee(
            name="CEO",
            email="ceo@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        db_session.add(ceo)
        db_session.flush()

        employee = Employee(
            name="Employee",
            email="emp@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=ceo.id,
        )
        db_session.add(employee)
        db_session.commit()

        employee_id = employee.id
        ceo_id = ceo.id
        user_id = uuid4()

        # Act
        employee_service.promote_employee_to_ceo(
            employee_id,
            changed_by_user_id=user_id,
        )

        # Assert - Check audit log for promoted employee
        audit_logs = db_session.execute(
            select(AuditLog).where(
                AuditLog.entity_type == EntityType.EMPLOYEE,
                AuditLog.entity_id == employee_id,
                AuditLog.change_type == ChangeType.UPDATE,
            )
        ).scalars().all()

        assert len(audit_logs) == 1
        log = audit_logs[0]
        assert log.changed_by_user_id == user_id
        assert log.previous_state["manager_id"] == str(ceo_id)
        assert log.new_state["manager_id"] is None

    def test_promote_creates_audit_log_for_old_ceo(self, employee_service, db_session):
        """Should create UPDATE audit log for old CEO."""
        # Arrange
        ceo = Employee(
            name="CEO",
            email="ceo@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        db_session.add(ceo)
        db_session.flush()

        employee = Employee(
            name="Employee",
            email="emp@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=ceo.id,
        )
        db_session.add(employee)
        db_session.commit()

        employee_id = employee.id
        ceo_id = ceo.id
        user_id = uuid4()

        # Act
        employee_service.promote_employee_to_ceo(
            employee_id,
            changed_by_user_id=user_id,
        )

        # Assert - Check audit log for old CEO
        audit_logs = db_session.execute(
            select(AuditLog).where(
                AuditLog.entity_type == EntityType.EMPLOYEE,
                AuditLog.entity_id == ceo_id,
                AuditLog.change_type == ChangeType.UPDATE,
            )
        ).scalars().all()

        assert len(audit_logs) == 1
        log = audit_logs[0]
        assert log.changed_by_user_id == user_id
        assert log.previous_state["manager_id"] is None
        assert log.new_state["manager_id"] == str(employee_id)

    def test_promote_creates_audit_logs_for_reassigned_ceo_reports(self, employee_service, db_session):
        """Should create audit logs for CEO's other direct reports when employee reports to CEO."""
        # Arrange
        ceo = Employee(
            name="CEO",
            email="ceo@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        db_session.add(ceo)
        db_session.flush()

        ceo_id = ceo.id

        employee = Employee(
            name="Employee",
            email="emp@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=ceo.id,
        )
        other1 = Employee(
            name="Other 1",
            email="other1@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=ceo.id,
        )
        other2 = Employee(
            name="Other 2",
            email="other2@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=ceo.id,
        )
        db_session.add_all([employee, other1, other2])
        db_session.commit()

        employee_id = employee.id
        other1_id = other1.id
        other2_id = other2.id
        user_id = uuid4()

        # Act
        employee_service.promote_employee_to_ceo(
            employee_id,
            changed_by_user_id=user_id,
        )

        # Assert - Check audit logs for other reports
        other1_logs = db_session.execute(
            select(AuditLog).where(
                AuditLog.entity_type == EntityType.EMPLOYEE,
                AuditLog.entity_id == other1_id,
                AuditLog.change_type == ChangeType.UPDATE,
            )
        ).scalars().all()

        other2_logs = db_session.execute(
            select(AuditLog).where(
                AuditLog.entity_type == EntityType.EMPLOYEE,
                AuditLog.entity_id == other2_id,
                AuditLog.change_type == ChangeType.UPDATE,
            )
        ).scalars().all()

        assert len(other1_logs) == 1
        assert len(other2_logs) == 1

        assert other1_logs[0].previous_state["manager_id"] == str(ceo_id)
        assert other1_logs[0].new_state["manager_id"] == str(employee_id)

        assert other2_logs[0].previous_state["manager_id"] == str(ceo_id)
        assert other2_logs[0].new_state["manager_id"] == str(employee_id)

    def test_promote_creates_audit_logs_for_employee_reports(self, employee_service, db_session):
        """Should create audit logs for employee's reports when not reporting to CEO."""
        # Arrange - CEO -> Manager -> Employee (with reports)
        ceo = Employee(
            name="CEO",
            email="ceo@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        db_session.add(ceo)
        db_session.flush()

        manager = Employee(
            name="Manager",
            email="manager@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=ceo.id,
        )
        db_session.add(manager)
        db_session.flush()

        manager_id = manager.id

        employee = Employee(
            name="Employee",
            email="emp@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=manager.id,
        )
        db_session.add(employee)
        db_session.flush()

        employee_id = employee.id

        report1 = Employee(
            name="Report 1",
            email="report1@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=employee.id,
        )
        report2 = Employee(
            name="Report 2",
            email="report2@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=employee.id,
        )
        db_session.add_all([report1, report2])
        db_session.commit()

        report1_id = report1.id
        report2_id = report2.id
        user_id = uuid4()

        # Act
        employee_service.promote_employee_to_ceo(
            employee_id,
            changed_by_user_id=user_id,
        )

        # Assert - Check audit logs for employee's reports
        report1_logs = db_session.execute(
            select(AuditLog).where(
                AuditLog.entity_type == EntityType.EMPLOYEE,
                AuditLog.entity_id == report1_id,
                AuditLog.change_type == ChangeType.UPDATE,
            )
        ).scalars().all()

        report2_logs = db_session.execute(
            select(AuditLog).where(
                AuditLog.entity_type == EntityType.EMPLOYEE,
                AuditLog.entity_id == report2_id,
                AuditLog.change_type == ChangeType.UPDATE,
            )
        ).scalars().all()

        assert len(report1_logs) == 1
        assert len(report2_logs) == 1

        # Should be reassigned to employee's original manager
        assert report1_logs[0].previous_state["manager_id"] == str(employee_id)
        assert report1_logs[0].new_state["manager_id"] == str(manager_id)

        assert report2_logs[0].previous_state["manager_id"] == str(employee_id)
        assert report2_logs[0].new_state["manager_id"] == str(manager_id)

    def test_promote_does_not_commit(self, employee_service, db_session):
        """Should not commit transaction."""
        # Arrange
        ceo = Employee(
            name="CEO",
            email="ceo@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=None,
        )
        db_session.add(ceo)
        db_session.flush()

        employee = Employee(
            name="Employee",
            email="emp@example.com",
            status=EmployeeStatus.ACTIVE,
            manager_id=ceo.id,
        )
        db_session.add(employee)
        db_session.commit()

        employee_id = employee.id
        user_id = uuid4()

        # Act
        employee_service.promote_employee_to_ceo(
            employee_id,
            changed_by_user_id=user_id,
        )

        # Rollback to verify it wasn't committed
        db_session.rollback()

        # Assert - Employee should still have manager after rollback
        db_session.refresh(employee)
        assert employee.manager_id == ceo.id
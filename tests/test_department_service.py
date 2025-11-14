"""
test_department_service.py
---------------------------
Unit tests for DepartmentService business logic.

Testing Strategy:
1. Test create_department with audit logging
2. Test get_department by ID
3. Test update_department with audit logging
4. Test delete_department with audit logging
5. Test list_department_teams with pagination
6. Test list_department_employees with pagination
"""

import pytest
from uuid import uuid4
from sqlalchemy import select
from services.DepartmentService import DepartmentService
from models.DepartmentModel import Department
from models.TeamModel import Team
from models.EmployeeModel import Employee, EmployeeStatus
from models.UserModel import User  # Import to ensure SQLAlchemy relationships are configured
from models.AuditLogModel import AuditLog, EntityType, ChangeType


@pytest.fixture
def department_service(db_session):
    """Create a DepartmentService instance with test database session."""
    return DepartmentService(db_session)


@pytest.fixture
def sample_departments(db_session):
    """Create sample departments for testing."""
    departments = [
        Department(name="Engineering"),
        Department(name="Sales"),
        Department(name="HR"),
    ]
    db_session.add_all(departments)
    db_session.commit()
    return departments


@pytest.fixture
def sample_department_with_teams(db_session):
    """Create a department with multiple teams for testing."""
    # Create department
    dept = Department(name="Engineering")
    db_session.add(dept)
    db_session.flush()

    # Create teams
    teams = [
        Team(name="Backend Team", department_id=dept.id),
        Team(name="Frontend Team", department_id=dept.id),
        Team(name="DevOps Team", department_id=dept.id),
        Team(name="QA Team", department_id=dept.id),
    ]
    db_session.add_all(teams)
    db_session.commit()

    return {"department": dept, "teams": teams}


@pytest.fixture
def sample_department_with_employees(db_session):
    """Create a department with multiple employees for testing."""
    # Create department
    dept = Department(name="Sales")
    db_session.add(dept)
    db_session.flush()

    # Create employees
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
    db_session.add_all(employees)
    db_session.commit()

    return {"department": dept, "employees": employees}


class TestCreateDepartment:
    """Tests for DepartmentService.create_department() method."""

    def test_create_department_success(self, department_service, db_session):
        """Should create a new department."""
        # Arrange
        user_id = uuid4()

        # Act
        department = department_service.create_department(
            name="Engineering",
            changed_by_user_id=user_id,
        )

        # Assert
        assert department.name == "Engineering"
        assert department.id is not None

    def test_create_department_persists_to_db(self, department_service, db_session):
        """Should persist department to database after flush."""
        # Arrange
        user_id = uuid4()

        # Act
        department = department_service.create_department(
            name="Engineering",
            changed_by_user_id=user_id,
        )
        db_session.commit()

        # Assert - Verify it exists in database
        query = select(Department).where(Department.name == "Engineering")
        result = db_session.execute(query).scalar_one_or_none()
        assert result is not None
        assert result.id == department.id

    def test_create_department_creates_audit_log(self, department_service, db_session):
        """Should create audit log entry for new department."""
        # Arrange
        user_id = uuid4()

        # Act
        department = department_service.create_department(
            name="Engineering",
            changed_by_user_id=user_id,
        )
        db_session.commit()

        # Assert - Check audit log was created
        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.entity_type == EntityType.DEPARTMENT,
            AuditLog.entity_id == department.id,
        ).all()

        assert len(audit_logs) == 1
        log = audit_logs[0]
        assert log.change_type == ChangeType.CREATE
        assert log.previous_state is None
        assert log.new_state == {"name": "Engineering"}
        assert log.changed_by_user_id == user_id

    def test_create_department_without_user_id(self, department_service, db_session):
        """Should allow creating department without user_id."""
        # Act
        department = department_service.create_department(name="Engineering")
        db_session.commit()

        # Assert
        assert department.name == "Engineering"
        # Check audit log has None for user_id
        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.entity_id == department.id
        ).all()
        assert len(audit_logs) == 1
        assert audit_logs[0].changed_by_user_id is None

    def test_create_department_unique_constraint(self, department_service, db_session):
        """Should fail when creating duplicate department name."""
        # Arrange - Create first department
        department_service.create_department(name="Engineering")
        db_session.commit()

        # Act & Assert - Try to create duplicate
        from sqlalchemy.exc import IntegrityError
        with pytest.raises(IntegrityError):  # Database will raise unique constraint error
            department_service.create_department(name="Engineering")
            db_session.commit()


class TestGetDepartment:
    """Tests for DepartmentService.get_department() method."""

    def test_get_department_success(self, department_service, sample_departments):
        """Should return department by ID."""
        # Arrange
        department_id = sample_departments[0].id

        # Act
        department = department_service.get_department(department_id)

        # Assert
        assert department is not None
        assert department.id == department_id
        assert department.name == "Engineering"

    def test_get_department_not_found(self, department_service):
        """Should return None when department doesn't exist."""
        # Arrange
        fake_id = uuid4()

        # Act
        department = department_service.get_department(fake_id)

        # Assert
        assert department is None

    def test_get_department_returns_correct_department(self, department_service, sample_departments):
        """Should return the correct department from multiple departments."""
        # Arrange
        sales_dept = sample_departments[1]

        # Act
        department = department_service.get_department(sales_dept.id)

        # Assert
        assert department.name == "Sales"
        assert department.id == sales_dept.id


class TestUpdateDepartment:
    """Tests for DepartmentService.update_department() method."""

    def test_update_department_name(self, department_service, sample_departments, db_session):
        """Should update department name."""
        # Arrange
        department_id = sample_departments[0].id
        user_id = uuid4()

        # Act
        department = department_service.update_department(
            department_id,
            name="Engineering & Technology",
            changed_by_user_id=user_id,
        )

        # Assert
        assert department is not None
        assert department.name == "Engineering & Technology"
        assert department.id == department_id

    def test_update_department_persists_changes(self, department_service, sample_departments, db_session):
        """Should persist changes to database."""
        # Arrange
        department_id = sample_departments[0].id
        user_id = uuid4()

        # Act
        department_service.update_department(
            department_id,
            name="Engineering & Technology",
            changed_by_user_id=user_id,
        )
        db_session.commit()

        # Assert - Verify changes persisted
        updated = department_service.get_department(department_id)
        assert updated.name == "Engineering & Technology"

    def test_update_department_creates_audit_log(self, department_service, sample_departments, db_session):
        """Should create audit log entry for update."""
        # Arrange
        department_id = sample_departments[0].id
        user_id = uuid4()

        # Act
        department_service.update_department(
            department_id,
            name="Engineering & Technology",
            changed_by_user_id=user_id,
        )
        db_session.commit()

        # Assert - Check audit log
        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.entity_type == EntityType.DEPARTMENT,
            AuditLog.entity_id == department_id,
            AuditLog.change_type == ChangeType.UPDATE,
        ).all()

        assert len(audit_logs) == 1
        log = audit_logs[0]
        assert log.previous_state == {"name": "Engineering"}
        assert log.new_state == {"name": "Engineering & Technology"}
        assert log.changed_by_user_id == user_id

    def test_update_department_no_changes(self, department_service, sample_departments, db_session):
        """Should not create audit log when no changes are made."""
        # Arrange
        department_id = sample_departments[0].id
        user_id = uuid4()
        original_name = sample_departments[0].name

        # Act
        department = department_service.update_department(
            department_id,
            name=original_name,  # Same name
            changed_by_user_id=user_id,
        )
        db_session.commit()

        # Assert - No audit log should be created
        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.entity_type == EntityType.DEPARTMENT,
            AuditLog.entity_id == department_id,
        ).all()

        assert len(audit_logs) == 0
        assert department.name == original_name

    def test_update_department_not_found(self, department_service):
        """Should return None when department doesn't exist."""
        # Arrange
        fake_id = uuid4()

        # Act
        department = department_service.update_department(
            fake_id,
            name="New Name",
        )

        # Assert
        assert department is None

    def test_update_department_without_user_id(self, department_service, sample_departments, db_session):
        """Should allow updating without user_id."""
        # Arrange
        department_id = sample_departments[0].id

        # Act
        department = department_service.update_department(
            department_id,
            name="New Name",
        )
        db_session.commit()

        # Assert
        assert department.name == "New Name"
        # Check audit log has None for user_id
        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.entity_id == department_id
        ).all()
        assert len(audit_logs) == 1
        assert audit_logs[0].changed_by_user_id is None


class TestDeleteDepartment:
    """Tests for DepartmentService.delete_department() method."""

    def test_delete_department_success(self, department_service, sample_departments, db_session):
        """Should delete department."""
        # Arrange
        department_id = sample_departments[0].id
        user_id = uuid4()

        # Act
        department = department_service.delete_department(
            department_id,
            changed_by_user_id=user_id,
        )
        db_session.commit()

        # Assert
        assert department is not None
        # Verify it's deleted
        result = department_service.get_department(department_id)
        assert result is None

    def test_delete_department_creates_audit_log(self, department_service, sample_departments, db_session):
        """Should create audit log entry for deletion."""
        # Arrange
        department_id = sample_departments[0].id
        department_name = sample_departments[0].name
        user_id = uuid4()

        # Act
        department_service.delete_department(
            department_id,
            changed_by_user_id=user_id,
        )
        db_session.commit()

        # Assert - Check audit log
        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.entity_type == EntityType.DEPARTMENT,
            AuditLog.entity_id == department_id,
            AuditLog.change_type == ChangeType.DELETE,
        ).all()

        assert len(audit_logs) == 1
        log = audit_logs[0]
        assert log.previous_state == {"name": department_name}
        assert log.new_state is None
        assert log.changed_by_user_id == user_id

    def test_delete_department_not_found(self, department_service):
        """Should return None when department doesn't exist."""
        # Arrange
        fake_id = uuid4()

        # Act
        department = department_service.delete_department(fake_id)

        # Assert
        assert department is None

    def test_delete_department_without_user_id(self, department_service, sample_departments, db_session):
        """Should allow deleting without user_id."""
        # Arrange
        department_id = sample_departments[0].id

        # Act
        department = department_service.delete_department(department_id)
        db_session.commit()

        # Assert - Department should be deleted
        result = department_service.get_department(department_id)
        assert result is None


class TestListDepartmentTeams:
    """Tests for DepartmentService.list_department_teams() method."""

    def test_list_department_teams_success(self, department_service, sample_department_with_teams):
        """Should return all teams in department."""
        # Arrange
        department_id = sample_department_with_teams["department"].id

        # Act
        teams, total = department_service.list_department_teams(department_id)

        # Assert
        assert total == 4
        assert len(teams) == 4

    def test_list_department_teams_alphabetical_order(self, department_service, sample_department_with_teams):
        """Should return teams ordered alphabetically by name."""
        # Arrange
        department_id = sample_department_with_teams["department"].id

        # Act
        teams, total = department_service.list_department_teams(department_id)

        # Assert
        assert teams[0].name == "Backend Team"
        assert teams[1].name == "DevOps Team"
        assert teams[2].name == "Frontend Team"
        assert teams[3].name == "QA Team"

    def test_list_department_teams_pagination_limit(self, department_service, sample_department_with_teams):
        """Should respect limit parameter."""
        # Arrange
        department_id = sample_department_with_teams["department"].id

        # Act
        teams, total = department_service.list_department_teams(
            department_id,
            limit=2,
        )

        # Assert
        assert total == 4  # Total unchanged
        assert len(teams) == 2  # Only 2 returned
        assert teams[0].name == "Backend Team"
        assert teams[1].name == "DevOps Team"

    def test_list_department_teams_pagination_offset(self, department_service, sample_department_with_teams):
        """Should respect offset parameter."""
        # Arrange
        department_id = sample_department_with_teams["department"].id

        # Act
        teams, total = department_service.list_department_teams(
            department_id,
            limit=2,
            offset=2,
        )

        # Assert
        assert total == 4
        assert len(teams) == 2
        assert teams[0].name == "Frontend Team"
        assert teams[1].name == "QA Team"

    def test_list_department_teams_offset_beyond_results(self, department_service, sample_department_with_teams):
        """Should return empty list when offset exceeds total."""
        # Arrange
        department_id = sample_department_with_teams["department"].id

        # Act
        teams, total = department_service.list_department_teams(
            department_id,
            offset=100,
        )

        # Assert
        assert total == 4
        assert len(teams) == 0

    def test_list_department_teams_empty_department(self, department_service, db_session):
        """Should return empty list for department with no teams."""
        # Arrange - Create department with no teams
        dept = Department(name="Empty Department")
        db_session.add(dept)
        db_session.commit()

        # Act
        teams, total = department_service.list_department_teams(dept.id)

        # Assert
        assert total == 0
        assert len(teams) == 0

    def test_list_department_teams_nonexistent_department(self, department_service):
        """Should return empty list for non-existent department."""
        # Arrange
        fake_id = uuid4()

        # Act
        teams, total = department_service.list_department_teams(fake_id)

        # Assert
        assert total == 0
        assert len(teams) == 0

    def test_list_department_teams_default_pagination(self, department_service, sample_department_with_teams):
        """Should use default limit of 25."""
        # Arrange
        department_id = sample_department_with_teams["department"].id

        # Act
        teams, total = department_service.list_department_teams(department_id)

        # Assert
        assert len(teams) == 4  # All teams returned (less than default limit)


class TestListDepartmentEmployees:
    """Tests for DepartmentService.list_department_employees() method."""

    def test_list_department_employees_success(self, department_service, sample_department_with_employees):
        """Should return all employees in department."""
        # Arrange
        department_id = sample_department_with_employees["department"].id

        # Act
        employees, total = department_service.list_department_employees(department_id)

        # Assert
        assert total == 3
        assert len(employees) == 3

    def test_list_department_employees_alphabetical_order(self, department_service, sample_department_with_employees):
        """Should return employees ordered alphabetically by name."""
        # Arrange
        department_id = sample_department_with_employees["department"].id

        # Act
        employees, total = department_service.list_department_employees(department_id)

        # Assert
        assert employees[0].name == "Alice Anderson"
        assert employees[1].name == "Bob Brown"
        assert employees[2].name == "Charlie Chen"

    def test_list_department_employees_pagination_limit(self, department_service, sample_department_with_employees):
        """Should respect limit parameter."""
        # Arrange
        department_id = sample_department_with_employees["department"].id

        # Act
        employees, total = department_service.list_department_employees(
            department_id,
            limit=2,
        )

        # Assert
        assert total == 3  # Total unchanged
        assert len(employees) == 2  # Only 2 returned
        assert employees[0].name == "Alice Anderson"
        assert employees[1].name == "Bob Brown"

    def test_list_department_employees_pagination_offset(self, department_service, sample_department_with_employees):
        """Should respect offset parameter."""
        # Arrange
        department_id = sample_department_with_employees["department"].id

        # Act
        employees, total = department_service.list_department_employees(
            department_id,
            limit=2,
            offset=1,
        )

        # Assert
        assert total == 3
        assert len(employees) == 2
        assert employees[0].name == "Bob Brown"
        assert employees[1].name == "Charlie Chen"

    def test_list_department_employees_offset_beyond_results(self, department_service, sample_department_with_employees):
        """Should return empty list when offset exceeds total."""
        # Arrange
        department_id = sample_department_with_employees["department"].id

        # Act
        employees, total = department_service.list_department_employees(
            department_id,
            offset=100,
        )

        # Assert
        assert total == 3
        assert len(employees) == 0

    def test_list_department_employees_empty_department(self, department_service, db_session):
        """Should return empty list for department with no employees."""
        # Arrange - Create department with no employees
        dept = Department(name="Empty Department")
        db_session.add(dept)
        db_session.commit()

        # Act
        employees, total = department_service.list_department_employees(dept.id)

        # Assert
        assert total == 0
        assert len(employees) == 0

    def test_list_department_employees_nonexistent_department(self, department_service):
        """Should return empty list for non-existent department."""
        # Arrange
        fake_id = uuid4()

        # Act
        employees, total = department_service.list_department_employees(fake_id)

        # Assert
        assert total == 0
        assert len(employees) == 0

    def test_list_department_employees_includes_all_statuses(self, department_service, sample_department_with_employees):
        """Should include employees regardless of status."""
        # Arrange
        department_id = sample_department_with_employees["department"].id

        # Act
        employees, total = department_service.list_department_employees(department_id)

        # Assert
        assert total == 3
        # Should include both ACTIVE and ON_LEAVE employees
        statuses = {emp.status for emp in employees}
        assert EmployeeStatus.ACTIVE in statuses
        assert EmployeeStatus.ON_LEAVE in statuses

    def test_list_department_employees_default_pagination(self, department_service, sample_department_with_employees):
        """Should use default limit of 25."""
        # Arrange
        department_id = sample_department_with_employees["department"].id

        # Act
        employees, total = department_service.list_department_employees(department_id)

        # Assert
        assert len(employees) == 3  # All employees returned (less than default limit)

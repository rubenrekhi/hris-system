"""
test_import_service.py
----------------------
Comprehensive tests for ImportService including:
- Valid bulk import scenarios
- Circular dependency detection (various depths)
- Multiple subtrees with mixed DB/CSV managers
- Validation error handling
- Edge cases
"""

import pytest
from datetime import date
from uuid import uuid4
from sqlalchemy.orm import Session

from services.ImportService import ImportService
from services.DepartmentService import DepartmentService
from services.TeamService import TeamService
from services.EmployeeService import EmployeeService
from models.EmployeeModel import Employee, EmployeeStatus
from models.DepartmentModel import Department
from models.TeamModel import Team
from models.UserModel import User
from schemas.ImportSchemas import BulkImportResult


class TestImportServiceValidScenarios:
    """Tests for valid bulk import scenarios."""

    def test_import_single_employee_as_ceo(self, db_session: Session):
        """Test importing a single employee (CEO) with no manager."""
        import_service = ImportService(db_session)

        csv_data = [
            {
                "name": "Jane CEO",
                "email": "jane.ceo@example.com",
                "title": "CEO",
                "hired_on": "2024-01-01",
                "salary": "200000",
                "status": "ACTIVE",
                "manager_email": "",
                "department_name": "",
                "team_name": "",
            }
        ]

        result = import_service.import_employees(csv_data, changed_by_user_id=uuid4())

        assert result.total_rows == 1
        assert result.successful_imports == 1
        assert len(result.failed_rows) == 0
        assert len(result.created_employee_ids) == 1

        # Verify employee created
        emp = db_session.query(Employee).filter_by(email="jane.ceo@example.com").first()
        assert emp is not None
        assert emp.name == "Jane CEO"
        assert emp.title == "CEO"
        assert emp.manager_id is None

    def test_import_simple_hierarchy_two_levels(self, db_session: Session):
        """Test importing a simple 2-level hierarchy (CEO + 1 report)."""
        import_service = ImportService(db_session)

        csv_data = [
            {
                "name": "Jane CEO",
                "email": "jane.ceo@example.com",
                "title": "CEO",
                "manager_email": "",
            },
            {
                "name": "John CTO",
                "email": "john.cto@example.com",
                "title": "CTO",
                "manager_email": "jane.ceo@example.com",
            },
        ]

        result = import_service.import_employees(csv_data, changed_by_user_id=uuid4())

        assert result.total_rows == 2
        assert result.successful_imports == 2
        assert len(result.failed_rows) == 0

        # Verify hierarchy
        ceo = db_session.query(Employee).filter_by(email="jane.ceo@example.com").first()
        cto = db_session.query(Employee).filter_by(email="john.cto@example.com").first()

        assert ceo.manager_id is None
        assert cto.manager_id == ceo.id

    def test_import_deep_hierarchy_five_levels(self, db_session: Session):
        """Test importing a deep 5-level hierarchy."""
        import_service = ImportService(db_session)

        csv_data = [
            {"name": "L1 CEO", "email": "l1@example.com", "manager_email": ""},
            {"name": "L2 VP", "email": "l2@example.com", "manager_email": "l1@example.com"},
            {"name": "L3 Director", "email": "l3@example.com", "manager_email": "l2@example.com"},
            {"name": "L4 Manager", "email": "l4@example.com", "manager_email": "l3@example.com"},
            {"name": "L5 IC", "email": "l5@example.com", "manager_email": "l4@example.com"},
        ]

        result = import_service.import_employees(csv_data, changed_by_user_id=uuid4())

        assert result.total_rows == 5
        assert result.successful_imports == 5
        assert len(result.failed_rows) == 0

        # Verify chain
        l1 = db_session.query(Employee).filter_by(email="l1@example.com").first()
        l2 = db_session.query(Employee).filter_by(email="l2@example.com").first()
        l3 = db_session.query(Employee).filter_by(email="l3@example.com").first()
        l4 = db_session.query(Employee).filter_by(email="l4@example.com").first()
        l5 = db_session.query(Employee).filter_by(email="l5@example.com").first()

        assert l1.manager_id is None
        assert l2.manager_id == l1.id
        assert l3.manager_id == l2.id
        assert l4.manager_id == l3.id
        assert l5.manager_id == l4.id

    def test_import_with_departments_and_teams(self, db_session: Session):
        """Test importing employees with department and team assignments."""
        # Setup: Create department and team
        dept_service = DepartmentService(db_session)
        team_service = TeamService(db_session)

        dept = dept_service.create_department(
            name="Engineering",
            changed_by_user_id=uuid4(),
        )
        team = team_service.create_team(
            name="Backend Team",
            changed_by_user_id=uuid4(),
        )
        db_session.flush()

        import_service = ImportService(db_session)

        csv_data = [
            {
                "name": "Jane Engineer",
                "email": "jane.eng@example.com",
                "title": "Senior Engineer",
                "department_name": "Engineering",
                "team_name": "Backend Team",
                "manager_email": "",
            },
        ]

        result = import_service.import_employees(csv_data, changed_by_user_id=uuid4())

        assert result.successful_imports == 1

        emp = db_session.query(Employee).filter_by(email="jane.eng@example.com").first()
        assert emp.department_id == dept.id
        assert emp.team_id == team.id

    def test_import_single_tree(self, db_session: Session):
        """Test importing a single organizational tree (first import scenario)."""
        import_service = ImportService(db_session)

        csv_data = [
            # Root (CEO)
            {"name": "CEO", "email": "ceo@example.com", "manager_email": ""},
            # Level 1
            {"name": "VP1", "email": "vp1@example.com", "manager_email": "ceo@example.com"},
            {"name": "VP2", "email": "vp2@example.com", "manager_email": "ceo@example.com"},
            # Level 2
            {"name": "Dir1", "email": "dir1@example.com", "manager_email": "vp1@example.com"},
        ]

        result = import_service.import_employees(csv_data, changed_by_user_id=uuid4())

        assert result.total_rows == 4
        assert result.successful_imports == 4
        assert len(result.failed_rows) == 0

        # Verify hierarchy
        ceo = db_session.query(Employee).filter_by(email="ceo@example.com").first()
        vp1 = db_session.query(Employee).filter_by(email="vp1@example.com").first()
        vp2 = db_session.query(Employee).filter_by(email="vp2@example.com").first()
        dir1 = db_session.query(Employee).filter_by(email="dir1@example.com").first()

        assert ceo.manager_id is None  # CEO has no manager
        assert vp1.manager_id == ceo.id
        assert vp2.manager_id == ceo.id
        assert dir1.manager_id == vp1.id

    def test_import_with_existing_db_managers(self, db_session: Session):
        """Test importing employees whose managers already exist in DB."""
        # Setup: Create existing manager in DB
        emp_service = EmployeeService(db_session)
        existing_ceo = emp_service.create_employee(
            name="Existing CEO",
            email="existing.ceo@example.com",
            title="CEO",
            changed_by_user_id=uuid4(),
        )
        db_session.flush()

        import_service = ImportService(db_session)

        csv_data = [
            {
                "name": "New VP",
                "email": "new.vp@example.com",
                "title": "VP",
                "manager_email": "existing.ceo@example.com",  # Manager in DB
            },
            {
                "name": "New Director",
                "email": "new.director@example.com",
                "title": "Director",
                "manager_email": "new.vp@example.com",  # Manager in CSV
            },
        ]

        result = import_service.import_employees(csv_data, changed_by_user_id=uuid4())

        assert result.total_rows == 2
        assert result.successful_imports == 2
        assert len(result.failed_rows) == 0

        # Verify hierarchy
        vp = db_session.query(Employee).filter_by(email="new.vp@example.com").first()
        director = db_session.query(Employee).filter_by(email="new.director@example.com").first()

        assert vp.manager_id == existing_ceo.id
        assert director.manager_id == vp.id

    def test_import_with_mixed_db_and_csv_managers(self, db_session: Session):
        """Test complex scenario with managers in both DB and CSV."""
        # Setup: Create existing managers in DB
        emp_service = EmployeeService(db_session)
        db_ceo = emp_service.create_employee(
            name="DB CEO",
            email="db.ceo@example.com",
            changed_by_user_id=uuid4(),
        )
        db_vp = emp_service.create_employee(
            name="DB VP",
            email="db.vp@example.com",
            manager_id=db_ceo.id,
            changed_by_user_id=uuid4(),
        )
        db_session.flush()

        import_service = ImportService(db_session)

        csv_data = [
            # Employees whose managers are in DB
            {"name": "New Dir1", "email": "dir1@example.com", "manager_email": "db.vp@example.com"},
            {"name": "New Dir2", "email": "dir2@example.com", "manager_email": "db.ceo@example.com"},
            # Employees whose managers are in CSV (created in same import)
            {"name": "New Mgr1", "email": "mgr1@example.com", "manager_email": "dir1@example.com"},
            {"name": "New Mgr2", "email": "mgr2@example.com", "manager_email": "dir2@example.com"},
        ]

        result = import_service.import_employees(csv_data, changed_by_user_id=uuid4())

        assert result.total_rows == 4
        assert result.successful_imports == 4
        assert len(result.failed_rows) == 0

        # Verify relationships
        dir1 = db_session.query(Employee).filter_by(email="dir1@example.com").first()
        dir2 = db_session.query(Employee).filter_by(email="dir2@example.com").first()
        mgr1 = db_session.query(Employee).filter_by(email="mgr1@example.com").first()
        mgr2 = db_session.query(Employee).filter_by(email="mgr2@example.com").first()

        # Verify managers in DB
        assert dir1.manager_id == db_vp.id
        assert dir2.manager_id == db_ceo.id

        # Verify managers in CSV (from same import)
        assert mgr1.manager_id == dir1.id
        assert mgr2.manager_id == dir2.id

    def test_import_with_user_linking(self, db_session: Session):
        """Test that employees are automatically linked to users with matching emails."""
        # Setup: Create existing user
        user = User(
            email="jane@example.com",
            name="Jane User",
        )
        db_session.add(user)
        db_session.flush()

        import_service = ImportService(db_session)

        csv_data = [
            {
                "name": "Jane Employee",
                "email": "jane@example.com",  # Matches user email
                "manager_email": "",
            },
        ]

        result = import_service.import_employees(csv_data, changed_by_user_id=uuid4())

        assert result.successful_imports == 1

        # Flush to make changes visible
        db_session.flush()

        # Verify user was linked
        db_session.refresh(user)
        emp = db_session.query(Employee).filter_by(email="jane@example.com").first()
        assert user.employee_id == emp.id

    def test_import_does_not_relink_already_linked_users(self, db_session: Session):
        """Test that users already linked to an employee are not re-linked."""
        # Setup: Create CEO and existing employee with user already linked
        ceo = Employee(
            name="CEO",
            email="ceo@example.com",
        )
        db_session.add(ceo)
        db_session.flush()

        existing_emp = Employee(
            name="Existing Employee",
            email="existing@example.com",
            manager_id=ceo.id,
        )
        db_session.add(existing_emp)
        db_session.flush()

        user = User(
            email="john@example.com",
            name="John User",
            employee_id=existing_emp.id,  # Already linked to existing_emp
        )
        db_session.add(user)
        db_session.flush()

        import_service = ImportService(db_session)

        # Import new employee with same email as the user
        csv_data = [
            {
                "name": "John New Employee",
                "email": "john@example.com",  # Matches user email
                "manager_email": "ceo@example.com",  # Reports to CEO
            },
        ]

        result = import_service.import_employees(csv_data, changed_by_user_id=uuid4())

        assert result.successful_imports == 1

        # Flush to make changes visible
        db_session.flush()

        # Verify user is STILL linked to the original employee (not re-linked)
        db_session.refresh(user)
        assert user.employee_id == existing_emp.id  # Should NOT change

        # New employee was created but user was not linked to it
        new_emp = db_session.query(Employee).filter_by(name="John New Employee").first()
        assert new_emp is not None
        assert user.employee_id != new_emp.id


class TestImportServiceCircularDependencies:
    """Tests for circular dependency detection."""

    def test_reject_self_manager(self, db_session: Session):
        """Test that self-management is rejected."""
        import_service = ImportService(db_session)

        csv_data = [
            {
                "name": "Self Manager",
                "email": "self@example.com",
                "manager_email": "self@example.com",  # Self-reference
            },
        ]

        result = import_service.import_employees(csv_data, changed_by_user_id=uuid4())

        assert result.total_rows == 1
        assert result.successful_imports == 0
        assert len(result.failed_rows) == 1
        assert "Circular dependency" in result.failed_rows[0].error_message

    def test_reject_two_node_cycle(self, db_session: Session):
        """Test that 2-node circular dependency is rejected (A→B→A)."""
        import_service = ImportService(db_session)

        csv_data = [
            {
                "name": "Employee A",
                "email": "a@example.com",
                "manager_email": "b@example.com",
            },
            {
                "name": "Employee B",
                "email": "b@example.com",
                "manager_email": "a@example.com",
            },
        ]

        result = import_service.import_employees(csv_data, changed_by_user_id=uuid4())

        assert result.total_rows == 2
        assert result.successful_imports == 0
        assert len(result.failed_rows) == 1
        assert "Circular dependency" in result.failed_rows[0].error_message

    def test_reject_three_node_cycle(self, db_session: Session):
        """Test that 3-node circular dependency is rejected (A→B→C→A)."""
        import_service = ImportService(db_session)

        csv_data = [
            {
                "name": "Employee A",
                "email": "a@example.com",
                "manager_email": "b@example.com",
            },
            {
                "name": "Employee B",
                "email": "b@example.com",
                "manager_email": "c@example.com",
            },
            {
                "name": "Employee C",
                "email": "c@example.com",
                "manager_email": "a@example.com",
            },
        ]

        result = import_service.import_employees(csv_data, changed_by_user_id=uuid4())

        assert result.total_rows == 3
        assert result.successful_imports == 0
        assert len(result.failed_rows) == 1
        assert "Circular dependency" in result.failed_rows[0].error_message

    def test_reject_five_node_cycle(self, db_session: Session):
        """Test that 5-node circular dependency is rejected (A→B→C→D→E→A)."""
        import_service = ImportService(db_session)

        csv_data = [
            {"name": "A", "email": "a@example.com", "manager_email": "b@example.com"},
            {"name": "B", "email": "b@example.com", "manager_email": "c@example.com"},
            {"name": "C", "email": "c@example.com", "manager_email": "d@example.com"},
            {"name": "D", "email": "d@example.com", "manager_email": "e@example.com"},
            {"name": "E", "email": "e@example.com", "manager_email": "a@example.com"},
        ]

        result = import_service.import_employees(csv_data, changed_by_user_id=uuid4())

        assert result.total_rows == 5
        assert result.successful_imports == 0
        assert len(result.failed_rows) == 1
        assert "Circular dependency" in result.failed_rows[0].error_message

    def test_reject_cycle_with_valid_subtree(self, db_session: Session):
        """Test that cycle is detected even when CSV has valid subtrees too."""
        import_service = ImportService(db_session)

        csv_data = [
            # Valid tree
            {"name": "Valid CEO", "email": "valid.ceo@example.com", "manager_email": ""},
            {"name": "Valid VP", "email": "valid.vp@example.com", "manager_email": "valid.ceo@example.com"},
            # Circular dependency
            {"name": "Cycle A", "email": "cycle.a@example.com", "manager_email": "cycle.b@example.com"},
            {"name": "Cycle B", "email": "cycle.b@example.com", "manager_email": "cycle.a@example.com"},
        ]

        result = import_service.import_employees(csv_data, changed_by_user_id=uuid4())

        # All-or-nothing: entire import fails
        assert result.total_rows == 4
        assert result.successful_imports == 0
        assert len(result.failed_rows) == 1
        assert "Circular dependency" in result.failed_rows[0].error_message


class TestImportServiceValidation:
    """Tests for validation error handling."""

    def test_reject_duplicate_email_in_csv(self, db_session: Session):
        """Test that duplicate emails within CSV are rejected."""
        import_service = ImportService(db_session)

        csv_data = [
            {"name": "First", "email": "duplicate@example.com", "manager_email": ""},
            {"name": "Second", "email": "duplicate@example.com", "manager_email": ""},
        ]

        result = import_service.import_employees(csv_data, changed_by_user_id=uuid4())

        assert result.total_rows == 2
        assert result.successful_imports == 0
        assert len(result.failed_rows) == 1
        assert "Duplicate email in CSV" in result.failed_rows[0].error_message

    def test_reject_duplicate_email_in_db(self, db_session: Session):
        """Test that emails already in DB are rejected."""
        # Setup: Create existing employee
        emp_service = EmployeeService(db_session)
        emp_service.create_employee(
            name="Existing",
            email="existing@example.com",
            changed_by_user_id=uuid4(),
        )
        db_session.flush()

        import_service = ImportService(db_session)

        csv_data = [
            {"name": "Duplicate", "email": "existing@example.com", "manager_email": ""},
        ]

        result = import_service.import_employees(csv_data, changed_by_user_id=uuid4())

        assert result.successful_imports == 0
        assert len(result.failed_rows) == 1
        assert "already exists in database" in result.failed_rows[0].error_message

    def test_reject_nonexistent_department(self, db_session: Session):
        """Test that nonexistent departments are rejected."""
        import_service = ImportService(db_session)

        csv_data = [
            {
                "name": "Jane",
                "email": "jane@example.com",
                "department_name": "Nonexistent Department",
                "manager_email": "",
            },
        ]

        result = import_service.import_employees(csv_data, changed_by_user_id=uuid4())

        assert result.successful_imports == 0
        assert len(result.failed_rows) == 1
        assert "Department not found" in result.failed_rows[0].error_message

    def test_reject_nonexistent_team(self, db_session: Session):
        """Test that nonexistent teams are rejected."""
        import_service = ImportService(db_session)

        csv_data = [
            {
                "name": "Jane",
                "email": "jane@example.com",
                "team_name": "Nonexistent Team",
                "manager_email": "",
            },
        ]

        result = import_service.import_employees(csv_data, changed_by_user_id=uuid4())

        assert result.successful_imports == 0
        assert len(result.failed_rows) == 1
        assert "Team not found" in result.failed_rows[0].error_message

    def test_reject_nonexistent_manager_email(self, db_session: Session):
        """Test that manager emails not in CSV or DB are rejected."""
        import_service = ImportService(db_session)

        csv_data = [
            {
                "name": "Jane",
                "email": "jane@example.com",
                "manager_email": "nonexistent@example.com",
            },
        ]

        result = import_service.import_employees(csv_data, changed_by_user_id=uuid4())

        assert result.successful_imports == 0
        assert len(result.failed_rows) == 1
        assert "Manager email not found" in result.failed_rows[0].error_message

    def test_reject_missing_required_fields(self, db_session: Session):
        """Test that rows with missing required fields are rejected."""
        import_service = ImportService(db_session)

        csv_data = [
            {
                "name": "Jane",
                # Missing email
            },
        ]

        result = import_service.import_employees(csv_data, changed_by_user_id=uuid4())

        assert result.successful_imports == 0
        assert len(result.failed_rows) == 1
        assert "Validation error" in result.failed_rows[0].error_message

    def test_reject_invalid_salary(self, db_session: Session):
        """Test that negative salaries are rejected."""
        import_service = ImportService(db_session)

        csv_data = [
            {
                "name": "Jane",
                "email": "jane@example.com",
                "salary": "-50000",  # Invalid
                "manager_email": "",
            },
        ]

        result = import_service.import_employees(csv_data, changed_by_user_id=uuid4())

        assert result.successful_imports == 0
        assert len(result.failed_rows) == 1

    def test_all_or_nothing_validation(self, db_session: Session):
        """Test that if any row fails, no employees are created."""
        import_service = ImportService(db_session)

        csv_data = [
            # Valid row
            {"name": "Valid Employee", "email": "valid@example.com", "manager_email": ""},
            # Invalid row - duplicate email
            {"name": "Invalid", "email": "valid@example.com", "manager_email": ""},
        ]

        result = import_service.import_employees(csv_data, changed_by_user_id=uuid4())

        # No employees should be created
        assert result.successful_imports == 0
        assert len(result.failed_rows) > 0

        # Verify no employees in DB
        count = db_session.query(Employee).count()
        assert count == 0


class TestImportServiceEdgeCases:
    """Tests for edge cases."""

    def test_import_empty_csv(self, db_session: Session):
        """Test importing empty CSV data."""
        import_service = ImportService(db_session)

        csv_data = []

        result = import_service.import_employees(csv_data, changed_by_user_id=uuid4())

        assert result.total_rows == 0
        assert result.successful_imports == 0
        assert len(result.failed_rows) == 0

    def test_import_minimal_data(self, db_session: Session):
        """Test importing with only required fields."""
        import_service = ImportService(db_session)

        csv_data = [
            {
                "name": "Minimal Employee",
                "email": "minimal@example.com",
                # All optional fields omitted
            },
        ]

        result = import_service.import_employees(csv_data, changed_by_user_id=uuid4())

        assert result.successful_imports == 1

        emp = db_session.query(Employee).filter_by(email="minimal@example.com").first()
        assert emp.name == "Minimal Employee"
        assert emp.title is None
        assert emp.salary is None
        assert emp.status == EmployeeStatus.ACTIVE  # Default value

    def test_import_large_batch(self, db_session: Session):
        """Test importing a large batch of employees."""
        import_service = ImportService(db_session)

        # Generate 100 employees in a simple hierarchy
        csv_data = [
            {"name": "CEO", "email": "ceo@example.com", "manager_email": ""},
        ]

        for i in range(99):
            csv_data.append({
                "name": f"Employee {i}",
                "email": f"emp{i}@example.com",
                "manager_email": "ceo@example.com",
            })

        result = import_service.import_employees(csv_data, changed_by_user_id=uuid4())

        assert result.total_rows == 100
        assert result.successful_imports == 100
        assert len(result.failed_rows) == 0

    def test_import_multiple_roots_rejected(self, db_session: Session):
        """Test that multiple employees without managers (root nodes) are NOT allowed."""
        # Setup: Create existing CEO in DB
        emp_service = EmployeeService(db_session)
        emp_service.create_employee(
            name="Existing CEO",
            email="existing.ceo@example.com",
            changed_by_user_id=uuid4(),
        )
        db_session.flush()

        import_service = ImportService(db_session)

        csv_data = [
            # Multiple employees without managers - should be rejected
            {"name": "New CEO 1", "email": "new.ceo1@example.com", "manager_email": ""},
            {"name": "New CEO 2", "email": "new.ceo2@example.com", "manager_email": ""},
        ]

        result = import_service.import_employees(csv_data, changed_by_user_id=uuid4())

        # Both employees should fail - only one CEO allowed
        assert result.successful_imports == 0
        assert len(result.failed_rows) == 2
        assert "Only one employee can have no manager" in result.failed_rows[0].error_message


class TestImportServiceAuditLogs:
    """Tests for audit log creation during import."""

    def test_audit_logs_created_for_employees(self, db_session: Session):
        """Test that audit logs are created for imported employees."""
        from models.AuditLogModel import AuditLog, EntityType, ChangeType

        import_service = ImportService(db_session)
        user_id = uuid4()

        csv_data = [
            {"name": "Jane", "email": "jane@example.com", "manager_email": ""},
            {"name": "John", "email": "john@example.com", "manager_email": "jane@example.com"},
        ]

        result = import_service.import_employees(csv_data, changed_by_user_id=user_id)
        db_session.flush()

        assert result.successful_imports == 2

        # Check audit logs created
        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.entity_type == EntityType.EMPLOYEE,
            AuditLog.change_type == ChangeType.CREATE,
        ).all()

        assert len(audit_logs) == 2
        assert all(log.changed_by_user_id == user_id for log in audit_logs)

    def test_audit_logs_created_for_user_linking(self, db_session: Session):
        """Test that audit logs are created when users are linked."""
        from models.AuditLogModel import AuditLog, EntityType, ChangeType

        # Setup: Create existing user
        user = User(email="jane@example.com", name="Jane User")
        db_session.add(user)
        db_session.flush()

        import_service = ImportService(db_session)
        user_id = uuid4()

        csv_data = [
            {"name": "Jane", "email": "jane@example.com", "manager_email": ""},
        ]

        result = import_service.import_employees(csv_data, changed_by_user_id=user_id)
        db_session.flush()

        # Check audit logs for user update
        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.entity_type == EntityType.USER,
            AuditLog.change_type == ChangeType.UPDATE,
        ).all()

        assert len(audit_logs) == 1
        assert audit_logs[0].changed_by_user_id == user_id

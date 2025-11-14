"""
test_team_service.py
--------------------
Unit tests for TeamService business logic.

Testing Strategy:
1. Test list_teams with filters, search, and pagination
2. Test get_team, get_team_members, get_child_teams
3. Test create_team with validations and lead assignment
4. Test update_team with circular dependency detection
5. Test update_team with cascading department changes
6. Test delete_team with member/child reassignment
7. Test audit logging for all operations
"""

import pytest
from uuid import uuid4
from sqlalchemy import select
from services.TeamService import TeamService
from models.TeamModel import Team
from models.DepartmentModel import Department
from models.EmployeeModel import Employee, EmployeeStatus
from models.UserModel import User  # Import to ensure SQLAlchemy relationships are configured
from models.AuditLogModel import AuditLog, EntityType, ChangeType


@pytest.fixture
def team_service(db_session):
    """Create a TeamService instance with test database session."""
    return TeamService(db_session)


@pytest.fixture
def sample_department(db_session):
    """Create a sample department for testing."""
    dept = Department(name="Engineering")
    db_session.add(dept)
    db_session.commit()
    return dept


@pytest.fixture
def sample_employee(db_session):
    """Create a sample employee for testing."""
    emp = Employee(
        name="John Doe",
        email="john@example.com",
        status=EmployeeStatus.ACTIVE,
    )
    db_session.add(emp)
    db_session.commit()
    return emp


class TestListTeams:
    """Test team listing with filters and pagination."""

    def test_list_teams_empty(self, team_service):
        """Test listing teams when none exist."""
        teams, total = team_service.list_teams()

        assert teams == []
        assert total == 0

    def test_list_teams_basic(self, db_session, team_service, sample_department):
        """Test listing all teams."""
        # Create teams
        teams_data = [
            Team(name="Backend Team", department_id=sample_department.id),
            Team(name="Frontend Team", department_id=sample_department.id),
            Team(name="DevOps Team", department_id=sample_department.id),
        ]
        db_session.add_all(teams_data)
        db_session.commit()

        teams, total = team_service.list_teams()

        assert len(teams) == 3
        assert total == 3
        # Verify alphabetical ordering
        assert teams[0].name == "Backend Team"
        assert teams[1].name == "DevOps Team"
        assert teams[2].name == "Frontend Team"

    def test_list_teams_filter_by_department(self, db_session, team_service):
        """Test filtering teams by department."""
        # Create two departments
        dept1 = Department(name="Engineering")
        dept2 = Department(name="Sales")
        db_session.add_all([dept1, dept2])
        db_session.flush()

        # Create teams in different departments
        team1 = Team(name="Backend", department_id=dept1.id)
        team2 = Team(name="Frontend", department_id=dept1.id)
        team3 = Team(name="Sales Team", department_id=dept2.id)
        db_session.add_all([team1, team2, team3])
        db_session.commit()

        teams, total = team_service.list_teams(department_id=dept1.id)

        assert len(teams) == 2
        assert total == 2
        assert all(team.department_id == dept1.id for team in teams)

    def test_list_teams_filter_by_parent(self, db_session, team_service, sample_department):
        """Test filtering teams by parent team."""
        # Create parent team
        parent = Team(name="Engineering", department_id=sample_department.id)
        db_session.add(parent)
        db_session.flush()

        # Create child teams
        child1 = Team(name="Backend", parent_team_id=parent.id, department_id=sample_department.id)
        child2 = Team(name="Frontend", parent_team_id=parent.id, department_id=sample_department.id)
        independent = Team(name="DevOps", department_id=sample_department.id)
        db_session.add_all([child1, child2, independent])
        db_session.commit()

        teams, total = team_service.list_teams(parent_team_id=parent.id)

        assert len(teams) == 2
        assert total == 2
        assert all(team.parent_team_id == parent.id for team in teams)

    def test_list_teams_search_by_name(self, db_session, team_service, sample_department):
        """Test searching teams by name (case-insensitive)."""
        teams_data = [
            Team(name="Backend Team", department_id=sample_department.id),
            Team(name="Frontend Team", department_id=sample_department.id),
            Team(name="DevOps", department_id=sample_department.id),
        ]
        db_session.add_all(teams_data)
        db_session.commit()

        teams, total = team_service.list_teams(name="team")

        assert len(teams) == 2
        assert total == 2
        assert all("Team" in team.name for team in teams)

    def test_list_teams_pagination(self, db_session, team_service, sample_department):
        """Test pagination of team list."""
        # Create 5 teams
        teams_data = [
            Team(name=f"Team {i}", department_id=sample_department.id)
            for i in range(5)
        ]
        db_session.add_all(teams_data)
        db_session.commit()

        # Get first page
        teams, total = team_service.list_teams(limit=2, offset=0)
        assert len(teams) == 2
        assert total == 5

        # Get second page
        teams, total = team_service.list_teams(limit=2, offset=2)
        assert len(teams) == 2
        assert total == 5

        # Get last page
        teams, total = team_service.list_teams(limit=2, offset=4)
        assert len(teams) == 1
        assert total == 5


class TestGetTeam:
    """Test fetching individual teams and related data."""

    def test_get_team_success(self, db_session, team_service, sample_department):
        """Test getting a team by ID."""
        team = Team(name="Backend Team", department_id=sample_department.id)
        db_session.add(team)
        db_session.commit()

        result = team_service.get_team(team.id)

        assert result is not None
        assert result.id == team.id
        assert result.name == "Backend Team"

    def test_get_team_not_found(self, team_service):
        """Test getting a non-existent team."""
        result = team_service.get_team(uuid4())

        assert result is None

    def test_get_team_members(self, db_session, team_service, sample_department):
        """Test getting all members of a team."""
        # Create team
        team = Team(name="Backend Team", department_id=sample_department.id)
        db_session.add(team)
        db_session.flush()

        # Create employees on the team
        emp1 = Employee(name="Alice", email="alice@example.com", team_id=team.id)
        emp2 = Employee(name="Bob", email="bob@example.com", team_id=team.id)
        emp3 = Employee(name="Charlie", email="charlie@example.com")  # Not on team
        db_session.add_all([emp1, emp2, emp3])
        db_session.commit()

        members = team_service.get_team_members(team.id)

        assert len(members) == 2
        assert all(member.team_id == team.id for member in members)
        # Verify alphabetical ordering
        assert members[0].name == "Alice"
        assert members[1].name == "Bob"

    def test_get_team_members_empty(self, db_session, team_service, sample_department):
        """Test getting members of a team with no members."""
        team = Team(name="Empty Team", department_id=sample_department.id)
        db_session.add(team)
        db_session.commit()

        members = team_service.get_team_members(team.id)

        assert members == []

    def test_get_child_teams(self, db_session, team_service, sample_department):
        """Test getting all direct child teams."""
        # Create parent team
        parent = Team(name="Engineering", department_id=sample_department.id)
        db_session.add(parent)
        db_session.flush()

        # Create child teams
        child1 = Team(name="Backend", parent_team_id=parent.id, department_id=sample_department.id)
        child2 = Team(name="Frontend", parent_team_id=parent.id, department_id=sample_department.id)
        db_session.add_all([child1, child2])
        db_session.flush()

        # Create grandchild (should not be included)
        grandchild = Team(name="API Team", parent_team_id=child1.id, department_id=sample_department.id)
        db_session.add(grandchild)
        db_session.commit()

        children = team_service.get_child_teams(parent.id)

        assert len(children) == 2
        assert all(child.parent_team_id == parent.id for child in children)
        # Verify alphabetical ordering
        assert children[0].name == "Backend"
        assert children[1].name == "Frontend"


class TestCreateTeam:
    """Test team creation with validations."""

    def test_create_team_minimal(self, db_session, team_service):
        """Test creating a team with minimal required fields."""
        user_id = uuid4()

        team = team_service.create_team(
            name="Backend Team",
            changed_by_user_id=user_id,
        )

        assert team.name == "Backend Team"
        assert team.lead_id is None
        assert team.parent_team_id is None
        assert team.department_id is None

        # Verify audit log
        audit_log = db_session.query(AuditLog).filter_by(entity_id=team.id).first()
        assert audit_log is not None
        assert audit_log.entity_type == EntityType.TEAM
        assert audit_log.change_type == ChangeType.CREATE
        assert audit_log.changed_by_user_id == user_id

    def test_create_team_with_department(self, db_session, team_service, sample_department):
        """Test creating a team with a department."""
        team = team_service.create_team(
            name="Backend Team",
            department_id=sample_department.id,
            changed_by_user_id=uuid4(),
        )

        assert team.department_id == sample_department.id

    def test_create_team_with_parent(self, db_session, team_service, sample_department):
        """Test creating a team with a parent team."""
        # Create parent team
        parent = Team(name="Engineering", department_id=sample_department.id)
        db_session.add(parent)
        db_session.commit()

        team = team_service.create_team(
            name="Backend Team",
            parent_team_id=parent.id,
            changed_by_user_id=uuid4(),
        )

        assert team.parent_team_id == parent.id

    def test_create_team_with_lead(self, db_session, team_service, sample_employee):
        """Test creating a team with a team lead."""
        user_id = uuid4()

        team = team_service.create_team(
            name="Backend Team",
            lead_id=sample_employee.id,
            changed_by_user_id=user_id,
        )

        assert team.lead_id == sample_employee.id

        # Verify employee was assigned to team (need to query fresh from session)
        employee = db_session.query(Employee).filter_by(id=sample_employee.id).one()
        assert employee.team_id == team.id

        # Verify audit logs (1 for team CREATE, 1 for employee UPDATE)
        audit_logs = db_session.query(AuditLog).filter_by(changed_by_user_id=user_id).all()
        assert len(audit_logs) == 2

    def test_create_team_lead_removed_from_previous_team(self, db_session, team_service, sample_department):
        """Test that creating a team with a lead removes them from their previous team."""
        # Create employee on existing team
        existing_team = Team(name="Old Team", department_id=sample_department.id)
        db_session.add(existing_team)
        db_session.flush()

        employee = Employee(name="John", email="john@example.com", team_id=existing_team.id)
        db_session.add(employee)
        db_session.commit()

        employee_id = employee.id

        # Create new team with employee as lead
        new_team = team_service.create_team(
            name="New Team",
            lead_id=employee_id,
            changed_by_user_id=uuid4(),
        )

        # Verify employee moved to new team (query fresh from DB)
        employee = db_session.query(Employee).filter_by(id=employee_id).one()
        assert employee.team_id == new_team.id

    def test_create_team_invalid_lead(self, team_service):
        """Test creating a team with non-existent lead."""
        with pytest.raises(ValueError, match="Employee with ID .* does not exist"):
            team_service.create_team(
                name="Backend Team",
                lead_id=uuid4(),
                changed_by_user_id=uuid4(),
            )

    def test_create_team_invalid_parent(self, team_service):
        """Test creating a team with non-existent parent team."""
        with pytest.raises(ValueError, match="Team with ID .* does not exist"):
            team_service.create_team(
                name="Backend Team",
                parent_team_id=uuid4(),
                changed_by_user_id=uuid4(),
            )

    def test_create_team_invalid_department(self, team_service):
        """Test creating a team with non-existent department."""
        with pytest.raises(ValueError, match="Department with ID .* does not exist"):
            team_service.create_team(
                name="Backend Team",
                department_id=uuid4(),
                changed_by_user_id=uuid4(),
            )

    def test_create_team_parent_department_mismatch(self, db_session, team_service):
        """Test that parent team's department must match specified department."""
        # Create two departments
        dept1 = Department(name="Engineering")
        dept2 = Department(name="Sales")
        db_session.add_all([dept1, dept2])
        db_session.flush()

        # Create parent team in dept1
        parent = Team(name="Engineering Team", department_id=dept1.id)
        db_session.add(parent)
        db_session.commit()

        # Try to create child team with dept2 (should fail)
        with pytest.raises(ValueError, match="Parent team's department does not match"):
            team_service.create_team(
                name="Backend Team",
                parent_team_id=parent.id,
                department_id=dept2.id,
                changed_by_user_id=uuid4(),
            )


class TestUpdateTeam:
    """Test team updates with complex validations."""

    def test_update_team_name(self, db_session, team_service, sample_department):
        """Test updating team name."""
        team = Team(name="Old Name", department_id=sample_department.id)
        db_session.add(team)
        db_session.commit()

        user_id = uuid4()
        updated = team_service.update_team(
            team.id,
            name="New Name",
            changed_by_user_id=user_id,
        )

        assert updated.name == "New Name"

        # Verify audit log
        audit_log = db_session.query(AuditLog).filter_by(
            entity_id=team.id,
            change_type=ChangeType.UPDATE
        ).first()
        assert audit_log is not None
        assert audit_log.previous_state["name"] == "Old Name"
        assert audit_log.new_state["name"] == "New Name"

    def test_update_team_lead(self, db_session, team_service, sample_department, sample_employee):
        """Test updating team lead."""
        team = Team(name="Backend Team", department_id=sample_department.id)
        db_session.add(team)
        db_session.commit()

        employee_id = sample_employee.id
        team_id = team.id

        user_id = uuid4()
        updated = team_service.update_team(
            team_id,
            lead_id=employee_id,
            changed_by_user_id=user_id,
        )

        assert updated.lead_id == employee_id

        # Verify employee assigned to team (query fresh from DB)
        employee = db_session.query(Employee).filter_by(id=employee_id).one()
        assert employee.team_id == team_id

    def test_update_team_parent(self, db_session, team_service, sample_department):
        """Test updating team's parent team."""
        # Create teams
        parent = Team(name="Engineering", department_id=sample_department.id)
        team = Team(name="Backend", department_id=sample_department.id)
        db_session.add_all([parent, team])
        db_session.commit()

        updated = team_service.update_team(
            team.id,
            parent_team_id=parent.id,
            changed_by_user_id=uuid4(),
        )

        assert updated.parent_team_id == parent.id

    def test_update_team_parent_circular_dependency_self(self, db_session, team_service, sample_department):
        """Test that a team cannot be its own parent."""
        team = Team(name="Backend", department_id=sample_department.id)
        db_session.add(team)
        db_session.commit()

        with pytest.raises(ValueError, match="circular dependency"):
            team_service.update_team(
                team.id,
                parent_team_id=team.id,
                changed_by_user_id=uuid4(),
            )

    def test_update_team_parent_circular_dependency_descendant(self, db_session, team_service, sample_department):
        """Test that a team cannot have its descendant as parent."""
        # Create hierarchy: A -> B -> C
        team_a = Team(name="A", department_id=sample_department.id)
        db_session.add(team_a)
        db_session.flush()

        team_b = Team(name="B", parent_team_id=team_a.id, department_id=sample_department.id)
        db_session.add(team_b)
        db_session.flush()

        team_c = Team(name="C", parent_team_id=team_b.id, department_id=sample_department.id)
        db_session.add(team_c)
        db_session.commit()

        # Try to make A a child of C (would create cycle)
        with pytest.raises(ValueError, match="circular dependency"):
            team_service.update_team(
                team_a.id,
                parent_team_id=team_c.id,
                changed_by_user_id=uuid4(),
            )

    def test_update_team_parent_inherits_department(self, db_session, team_service):
        """Test that team inherits parent's department when parent is assigned."""
        # Create two departments
        dept1 = Department(name="Engineering")
        dept2 = Department(name="Sales")
        db_session.add_all([dept1, dept2])
        db_session.flush()

        # Create parent in dept1
        parent = Team(name="Engineering", department_id=dept1.id)
        db_session.add(parent)
        db_session.flush()

        # Create team in dept2
        team = Team(name="Backend", department_id=dept2.id)
        db_session.add(team)
        db_session.commit()

        # Update team's parent (should inherit dept1)
        team_service.update_team(
            team.id,
            parent_team_id=parent.id,
            changed_by_user_id=uuid4(),
        )

        db_session.refresh(team)
        assert team.department_id == dept1.id

    def test_update_team_parent_cascades_department_to_children(self, db_session, team_service):
        """Test that changing parent cascades department to all descendants."""
        # Create two departments
        dept1 = Department(name="Engineering")
        dept2 = Department(name="Sales")
        db_session.add_all([dept1, dept2])
        db_session.flush()

        # Create hierarchy in dept1: A -> B -> C
        team_a = Team(name="A", department_id=dept1.id)
        db_session.add(team_a)
        db_session.flush()

        team_b = Team(name="B", parent_team_id=team_a.id, department_id=dept1.id)
        db_session.add(team_b)
        db_session.flush()

        team_c = Team(name="C", parent_team_id=team_b.id, department_id=dept1.id)
        db_session.add(team_c)
        db_session.flush()

        # Create parent in dept2
        new_parent = Team(name="Sales Parent", department_id=dept2.id)
        db_session.add(new_parent)
        db_session.commit()

        # Move A under new_parent (should cascade dept2 to B and C)
        team_service.update_team(
            team_a.id,
            parent_team_id=new_parent.id,
            changed_by_user_id=uuid4(),
        )

        db_session.refresh(team_a)
        db_session.refresh(team_b)
        db_session.refresh(team_c)

        assert team_a.department_id == dept2.id
        assert team_b.department_id == dept2.id
        assert team_c.department_id == dept2.id

    def test_update_team_department_only_if_no_parent(self, db_session, team_service):
        """Test that department can only be changed if team has no parent."""
        # Create departments
        dept1 = Department(name="Engineering")
        dept2 = Department(name="Sales")
        db_session.add_all([dept1, dept2])
        db_session.flush()

        # Create parent and child
        parent = Team(name="Engineering", department_id=dept1.id)
        db_session.add(parent)
        db_session.flush()

        child = Team(name="Backend", parent_team_id=parent.id, department_id=dept1.id)
        db_session.add(child)
        db_session.commit()

        # Try to change child's department (should fail)
        with pytest.raises(ValueError, match="Cannot change department.*has a parent"):
            team_service.update_team(
                child.id,
                department_id=dept2.id,
                changed_by_user_id=uuid4(),
            )

    def test_update_team_department_cascades_to_children(self, db_session, team_service):
        """Test that changing department cascades to all descendants."""
        # Create departments
        dept1 = Department(name="Engineering")
        dept2 = Department(name="Sales")
        db_session.add_all([dept1, dept2])
        db_session.flush()

        # Create hierarchy: A -> B -> C (all in dept1, A has no parent)
        team_a = Team(name="A", department_id=dept1.id)
        db_session.add(team_a)
        db_session.flush()

        team_b = Team(name="B", parent_team_id=team_a.id, department_id=dept1.id)
        db_session.add(team_b)
        db_session.flush()

        team_c = Team(name="C", parent_team_id=team_b.id, department_id=dept1.id)
        db_session.add(team_c)
        db_session.commit()

        # Change A's department (should cascade to B and C)
        team_service.update_team(
            team_a.id,
            department_id=dept2.id,
            changed_by_user_id=uuid4(),
        )

        db_session.refresh(team_a)
        db_session.refresh(team_b)
        db_session.refresh(team_c)

        assert team_a.department_id == dept2.id
        assert team_b.department_id == dept2.id
        assert team_c.department_id == dept2.id

    def test_update_team_not_found(self, team_service):
        """Test updating non-existent team."""
        with pytest.raises(ValueError, match="Team with ID .* does not exist"):
            team_service.update_team(
                uuid4(),
                name="New Name",
                changed_by_user_id=uuid4(),
            )

    def test_update_team_no_changes(self, db_session, team_service, sample_department):
        """Test that updating with same values doesn't create audit log."""
        team = Team(name="Backend", department_id=sample_department.id)
        db_session.add(team)
        db_session.commit()

        # Clear existing audit logs
        db_session.query(AuditLog).delete()
        db_session.commit()

        # Update with same name
        team_service.update_team(
            team.id,
            name="Backend",
            changed_by_user_id=uuid4(),
        )

        # No audit log should be created
        audit_logs = db_session.query(AuditLog).all()
        assert len(audit_logs) == 0


class TestDeleteTeam:
    """Test team deletion with member and child reassignment."""

    def test_delete_team_basic(self, db_session, team_service, sample_department):
        """Test deleting a team with no members or children."""
        team = Team(name="Backend", department_id=sample_department.id)
        db_session.add(team)
        db_session.commit()

        user_id = uuid4()
        deleted = team_service.delete_team(team.id, changed_by_user_id=user_id)

        assert deleted is not None

        # Verify team is deleted
        result = db_session.query(Team).filter_by(id=team.id).first()
        assert result is None

        # Verify audit log
        audit_log = db_session.query(AuditLog).filter_by(
            entity_id=team.id,
            change_type=ChangeType.DELETE
        ).first()
        assert audit_log is not None

    def test_delete_team_removes_members(self, db_session, team_service, sample_department):
        """Test that deleting a team removes all members from it."""
        # Create team with members
        team = Team(name="Backend", department_id=sample_department.id)
        db_session.add(team)
        db_session.flush()

        emp1 = Employee(name="Alice", email="alice@example.com", team_id=team.id)
        emp2 = Employee(name="Bob", email="bob@example.com", team_id=team.id)
        db_session.add_all([emp1, emp2])
        db_session.commit()

        team_service.delete_team(team.id, changed_by_user_id=uuid4())

        # Verify members removed from team
        db_session.refresh(emp1)
        db_session.refresh(emp2)
        assert emp1.team_id is None
        assert emp2.team_id is None

    def test_delete_team_reassigns_children_to_parent(self, db_session, team_service, sample_department):
        """Test that deleting a team reassigns children to the deleted team's parent."""
        # Create hierarchy: Parent -> Middle -> Child
        parent = Team(name="Parent", department_id=sample_department.id)
        db_session.add(parent)
        db_session.flush()

        middle = Team(name="Middle", parent_team_id=parent.id, department_id=sample_department.id)
        db_session.add(middle)
        db_session.flush()

        child = Team(name="Child", parent_team_id=middle.id, department_id=sample_department.id)
        db_session.add(child)
        db_session.commit()

        parent_id = parent.id
        child_id = child.id

        # Delete middle team
        team_service.delete_team(middle.id, changed_by_user_id=uuid4())

        # Verify child reassigned to parent (query fresh from DB)
        child = db_session.query(Team).filter_by(id=child_id).one()
        assert child.parent_team_id == parent_id

    def test_delete_team_children_become_independent(self, db_session, team_service, sample_department):
        """Test that deleting a top-level team makes children independent."""
        # Create hierarchy: Parent (no parent) -> Child
        parent = Team(name="Parent", department_id=sample_department.id)
        db_session.add(parent)
        db_session.flush()

        child = Team(name="Child", parent_team_id=parent.id, department_id=sample_department.id)
        db_session.add(child)
        db_session.commit()

        child_id = child.id

        # Delete parent
        team_service.delete_team(parent.id, changed_by_user_id=uuid4())

        # Verify child has no parent (query fresh from DB)
        child = db_session.query(Team).filter_by(id=child_id).one()
        assert child.parent_team_id is None

    def test_delete_team_creates_audit_logs_for_members(self, db_session, team_service, sample_department):
        """Test that deleting a team creates audit logs for member updates."""
        # Create team with members
        team = Team(name="Backend", department_id=sample_department.id)
        db_session.add(team)
        db_session.flush()

        emp1 = Employee(name="Alice", email="alice@example.com", team_id=team.id)
        emp2 = Employee(name="Bob", email="bob@example.com", team_id=team.id)
        db_session.add_all([emp1, emp2])
        db_session.commit()

        user_id = uuid4()
        team_service.delete_team(team.id, changed_by_user_id=user_id)

        # Verify audit logs (1 DELETE for team, 2 UPDATEs for employees)
        audit_logs = db_session.query(AuditLog).filter_by(changed_by_user_id=user_id).all()
        assert len(audit_logs) == 3

        delete_log = [log for log in audit_logs if log.change_type == ChangeType.DELETE]
        update_logs = [log for log in audit_logs if log.change_type == ChangeType.UPDATE]

        assert len(delete_log) == 1
        assert len(update_logs) == 2

    def test_delete_team_not_found(self, team_service):
        """Test deleting non-existent team."""
        with pytest.raises(ValueError, match="Team with ID .* does not exist"):
            team_service.delete_team(uuid4(), changed_by_user_id=uuid4())

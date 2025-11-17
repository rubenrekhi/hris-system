"""
test_team_api.py
----------------
Integration tests for Team API endpoints.

Testing Strategy:
1. Use FastAPI TestClient for full HTTP request/response testing
2. Test CRUD operations on teams
3. Test filtering, searching, and pagination
4. Test response schemas
5. Test validation and error handling
6. Test role-based access control
7. Use real database (in-memory SQLite) for integration testing
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import app
from models.BaseModel import Base
from models.TeamModel import Team
from models.DepartmentModel import Department
from models.EmployeeModel import Employee, EmployeeStatus
from models.UserModel import User
from core.dependencies import get_db, get_current_user


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
def client(test_db_session, test_admin_user):
    """Create a FastAPI TestClient with dependency override."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    async def override_get_current_user():
        return test_admin_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_department(test_db_session):
    """Create a sample department for testing."""
    dept = Department(name="Engineering")
    test_db_session.add(dept)
    test_db_session.commit()
    return dept


@pytest.fixture
def sample_teams(test_db_session, sample_department):
    """Create sample teams for testing."""
    teams = [
        Team(name="Backend Team", department_id=sample_department.id),
        Team(name="Frontend Team", department_id=sample_department.id),
        Team(name="DevOps Team", department_id=sample_department.id),
    ]
    test_db_session.add_all(teams)
    test_db_session.commit()
    return teams


@pytest.fixture
def sample_team_with_members(test_db_session, sample_department):
    """Create a team with members for testing."""
    # Create team
    team = Team(name="Backend Team", department_id=sample_department.id)
    test_db_session.add(team)
    test_db_session.flush()

    # Create members
    members = [
        Employee(name="Alice Anderson", email="alice@example.com", team_id=team.id),
        Employee(name="Bob Brown", email="bob@example.com", team_id=team.id),
        Employee(name="Charlie Chen", email="charlie@example.com", team_id=team.id),
    ]
    test_db_session.add_all(members)
    test_db_session.commit()

    return {"team": team, "members": members}


@pytest.fixture
def sample_team_hierarchy(test_db_session, sample_department):
    """Create a team hierarchy for testing."""
    # Create parent team
    parent = Team(name="Engineering", department_id=sample_department.id)
    test_db_session.add(parent)
    test_db_session.flush()

    # Create child teams
    child1 = Team(name="Backend", parent_team_id=parent.id, department_id=sample_department.id)
    child2 = Team(name="Frontend", parent_team_id=parent.id, department_id=sample_department.id)
    test_db_session.add_all([child1, child2])
    test_db_session.commit()

    return {"parent": parent, "children": [child1, child2]}


class TestListTeams:
    """Test GET /teams endpoint."""

    def test_list_teams_empty(self, client):
        """Test listing teams when none exist."""
        response = client.get("/teams")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["limit"] == 25
        assert data["offset"] == 0

    def test_list_teams_basic(self, client, sample_teams):
        """Test listing all teams."""
        response = client.get("/teams")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3

        # Verify alphabetical ordering
        assert data["items"][0]["name"] == "Backend Team"
        assert data["items"][1]["name"] == "DevOps Team"
        assert data["items"][2]["name"] == "Frontend Team"

    def test_list_teams_filter_by_department(self, client, test_db_session):
        """Test filtering teams by department."""
        # Create two departments with teams
        dept1 = Department(name="Engineering")
        dept2 = Department(name="Sales")
        test_db_session.add_all([dept1, dept2])
        test_db_session.flush()

        team1 = Team(name="Backend", department_id=dept1.id)
        team2 = Team(name="Frontend", department_id=dept1.id)
        team3 = Team(name="Sales Team", department_id=dept2.id)
        test_db_session.add_all([team1, team2, team3])
        test_db_session.commit()

        response = client.get(f"/teams?department_id={dept1.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2

    def test_list_teams_filter_by_parent(self, client, sample_team_hierarchy):
        """Test filtering teams by parent team."""
        parent = sample_team_hierarchy["parent"]

        response = client.get(f"/teams?parent_team_id={parent.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2

    def test_list_teams_search_by_name(self, client, sample_teams):
        """Test searching teams by name."""
        response = client.get("/teams?name=Backend")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Backend Team"

    def test_list_teams_pagination(self, client, sample_teams):
        """Test pagination of team list."""
        # First page
        response = client.get("/teams?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 3
        assert data["limit"] == 2
        assert data["offset"] == 0

        # Second page
        response = client.get("/teams?limit=2&offset=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 3


class TestGetTeam:
    """Test GET /teams/{team_id} endpoint."""

    def test_get_team_success(self, client, sample_team_with_members):
        """Test getting a team by ID."""
        team = sample_team_with_members["team"]

        response = client.get(f"/teams/{team.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(team.id)
        assert data["name"] == "Backend Team"
        assert len(data["members"]) == 3

    def test_get_team_includes_members(self, client, sample_team_with_members):
        """Test that team detail includes member list."""
        team = sample_team_with_members["team"]
        members = sample_team_with_members["members"]

        response = client.get(f"/teams/{team.id}")

        assert response.status_code == 200
        data = response.json()
        assert "members" in data
        assert len(data["members"]) == 3

        # Verify member fields
        member_data = data["members"][0]
        assert "id" in member_data
        assert "name" in member_data
        assert "email" in member_data

        # Verify joined name fields
        assert "lead_name" in data
        assert "parent_team_name" in data
        assert "department_name" in data
        assert data["lead_name"] is None  # No lead assigned in fixture
        assert data["parent_team_name"] is None  # No parent team in fixture
        assert data["department_name"] == "Engineering"  # Has department

    def test_get_team_not_found(self, client):
        """Test getting non-existent team."""
        from uuid import uuid4
        response = client.get(f"/teams/{uuid4()}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestGetChildTeams:
    """Test GET /teams/{team_id}/children endpoint."""

    def test_get_child_teams_success(self, client, sample_team_hierarchy):
        """Test getting child teams."""
        parent = sample_team_hierarchy["parent"]

        response = client.get(f"/teams/{parent.id}/children")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Backend"
        assert data[1]["name"] == "Frontend"

    def test_get_child_teams_empty(self, client, sample_department, test_db_session):
        """Test getting child teams when none exist."""
        team = Team(name="Leaf Team", department_id=sample_department.id)
        test_db_session.add(team)
        test_db_session.commit()

        response = client.get(f"/teams/{team.id}/children")

        assert response.status_code == 200
        data = response.json()
        assert data == []


class TestCreateTeam:
    """Test POST /teams endpoint."""

    def test_create_team_minimal(self, client):
        """Test creating a team with minimal required fields."""
        response = client.post(
            "/teams",
            json={"name": "Backend Team"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Backend Team"
        assert data["lead_id"] is None
        assert data["parent_team_id"] is None
        assert data["department_id"] is None
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_team_with_department(self, client, sample_department):
        """Test creating a team with a department."""
        response = client.post(
            "/teams",
            json={
                "name": "Backend Team",
                "department_id": str(sample_department.id)
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["department_id"] == str(sample_department.id)

    def test_create_team_with_parent(self, client, sample_department, test_db_session):
        """Test creating a team with a parent team."""
        # Create parent
        parent = Team(name="Engineering", department_id=sample_department.id)
        test_db_session.add(parent)
        test_db_session.commit()

        response = client.post(
            "/teams",
            json={
                "name": "Backend Team",
                "parent_team_id": str(parent.id)
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["parent_team_id"] == str(parent.id)

    def test_create_team_with_lead(self, client, test_db_session):
        """Test creating a team with a team lead."""
        # Create employee
        employee = Employee(name="John Doe", email="john@example.com")
        test_db_session.add(employee)
        test_db_session.commit()

        employee_id = employee.id

        response = client.post(
            "/teams",
            json={
                "name": "Backend Team",
                "lead_id": str(employee_id)
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["lead_id"] == str(employee_id)

        # Verify employee assigned to team (query fresh from DB)
        employee = test_db_session.query(Employee).filter_by(id=employee_id).one()
        assert str(employee.team_id) == data["id"]

    def test_create_team_invalid_department(self, client):
        """Test creating team with non-existent department."""
        from uuid import uuid4

        response = client.post(
            "/teams",
            json={
                "name": "Backend Team",
                "department_id": str(uuid4())
            }
        )

        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"]

    def test_create_team_invalid_parent(self, client):
        """Test creating team with non-existent parent."""
        from uuid import uuid4

        response = client.post(
            "/teams",
            json={
                "name": "Backend Team",
                "parent_team_id": str(uuid4())
            }
        )

        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"]

    def test_create_team_invalid_lead(self, client):
        """Test creating team with non-existent lead."""
        from uuid import uuid4

        response = client.post(
            "/teams",
            json={
                "name": "Backend Team",
                "lead_id": str(uuid4())
            }
        )

        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"]

    def test_create_team_parent_department_mismatch(self, client, test_db_session):
        """Test that parent team's department must match specified department."""
        # Create two departments
        dept1 = Department(name="Engineering")
        dept2 = Department(name="Sales")
        test_db_session.add_all([dept1, dept2])
        test_db_session.flush()

        # Create parent in dept1
        parent = Team(name="Engineering Team", department_id=dept1.id)
        test_db_session.add(parent)
        test_db_session.commit()

        response = client.post(
            "/teams",
            json={
                "name": "Backend Team",
                "parent_team_id": str(parent.id),
                "department_id": str(dept2.id)
            }
        )

        assert response.status_code == 400
        assert "department does not match" in response.json()["detail"].lower()


class TestUpdateTeam:
    """Test PATCH /teams/{team_id} endpoint."""

    def test_update_team_name(self, client, sample_department, test_db_session):
        """Test updating team name."""
        team = Team(name="Old Name", department_id=sample_department.id)
        test_db_session.add(team)
        test_db_session.commit()

        response = client.patch(
            f"/teams/{team.id}",
            json={"name": "New Name"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"

    def test_update_team_lead(self, client, sample_department, test_db_session):
        """Test updating team lead."""
        team = Team(name="Backend", department_id=sample_department.id)
        employee = Employee(name="John", email="john@example.com")
        test_db_session.add_all([team, employee])
        test_db_session.commit()

        response = client.patch(
            f"/teams/{team.id}",
            json={"lead_id": str(employee.id)}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["lead_id"] == str(employee.id)

    def test_update_team_parent(self, client, sample_department, test_db_session):
        """Test updating team's parent."""
        parent = Team(name="Engineering", department_id=sample_department.id)
        team = Team(name="Backend", department_id=sample_department.id)
        test_db_session.add_all([parent, team])
        test_db_session.commit()

        response = client.patch(
            f"/teams/{team.id}",
            json={"parent_team_id": str(parent.id)}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["parent_team_id"] == str(parent.id)

    def test_update_team_circular_dependency(self, client, sample_department, test_db_session):
        """Test that circular dependencies are rejected."""
        # Create hierarchy: A -> B -> C
        team_a = Team(name="A", department_id=sample_department.id)
        test_db_session.add(team_a)
        test_db_session.flush()

        team_b = Team(name="B", parent_team_id=team_a.id, department_id=sample_department.id)
        test_db_session.add(team_b)
        test_db_session.flush()

        team_c = Team(name="C", parent_team_id=team_b.id, department_id=sample_department.id)
        test_db_session.add(team_c)
        test_db_session.commit()

        # Try to make A a child of C
        response = client.patch(
            f"/teams/{team_a.id}",
            json={"parent_team_id": str(team_c.id)}
        )

        assert response.status_code == 400
        assert "circular dependency" in response.json()["detail"].lower()

    def test_update_team_department(self, client, test_db_session):
        """Test updating team's department (only if no parent)."""
        dept1 = Department(name="Engineering")
        dept2 = Department(name="Sales")
        test_db_session.add_all([dept1, dept2])
        test_db_session.flush()

        team = Team(name="Backend", department_id=dept1.id)
        test_db_session.add(team)
        test_db_session.commit()

        response = client.patch(
            f"/teams/{team.id}",
            json={"department_id": str(dept2.id)}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["department_id"] == str(dept2.id)

    def test_update_team_department_with_parent_fails(self, client, sample_department, test_db_session):
        """Test that department cannot be changed if team has parent."""
        dept2 = Department(name="Sales")
        test_db_session.add(dept2)
        test_db_session.flush()

        parent = Team(name="Engineering", department_id=sample_department.id)
        test_db_session.add(parent)
        test_db_session.flush()

        child = Team(name="Backend", parent_team_id=parent.id, department_id=sample_department.id)
        test_db_session.add(child)
        test_db_session.commit()

        response = client.patch(
            f"/teams/{child.id}",
            json={"department_id": str(dept2.id)}
        )

        assert response.status_code == 400
        assert "has a parent" in response.json()["detail"].lower()

    def test_update_team_not_found(self, client):
        """Test updating non-existent team."""
        from uuid import uuid4

        response = client.patch(
            f"/teams/{uuid4()}",
            json={"name": "New Name"}
        )

        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"]


class TestDeleteTeam:
    """Test DELETE /teams/{team_id} endpoint."""

    def test_delete_team_success(self, client, sample_department, test_db_session):
        """Test deleting a team."""
        team = Team(name="Backend", department_id=sample_department.id)
        test_db_session.add(team)
        test_db_session.commit()

        response = client.delete(f"/teams/{team.id}")

        assert response.status_code == 204

        # Verify team deleted
        result = test_db_session.query(Team).filter_by(id=team.id).first()
        assert result is None

    def test_delete_team_removes_members(self, client, sample_team_with_members, test_db_session):
        """Test that deleting team removes members from it."""
        team = sample_team_with_members["team"]
        members = sample_team_with_members["members"]

        response = client.delete(f"/teams/{team.id}")

        assert response.status_code == 204

        # Verify members removed from team
        for member in members:
            test_db_session.refresh(member)
            assert member.team_id is None

    def test_delete_team_reassigns_children(self, client, sample_team_hierarchy, test_db_session):
        """Test that deleting team reassigns children to parent."""
        parent = sample_team_hierarchy["parent"]
        children = sample_team_hierarchy["children"]

        # Create grandchild
        grandchild = Team(name="API Team", parent_team_id=children[0].id, department_id=parent.department_id)
        test_db_session.add(grandchild)
        test_db_session.commit()

        # Delete middle team
        response = client.delete(f"/teams/{children[0].id}")

        assert response.status_code == 204

        # Verify grandchild reassigned to parent
        test_db_session.refresh(grandchild)
        assert grandchild.parent_team_id == parent.id

    def test_delete_team_not_found(self, client):
        """Test deleting non-existent team."""
        from uuid import uuid4

        response = client.delete(f"/teams/{uuid4()}")

        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"]


class TestTeamResponseSchemas:
    """Test response schema validation."""

    def test_team_list_response_schema(self, client, sample_teams):
        """Test that list response has correct schema."""
        response = client.get("/teams")

        assert response.status_code == 200
        data = response.json()

        # Verify top-level fields
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

        # Verify item fields (TeamListItem schema)
        if data["items"]:
            item = data["items"][0]
            assert "id" in item
            assert "name" in item
            assert "lead_id" in item
            assert "parent_team_id" in item
            assert "department_id" in item
            # Note: TeamListItem does not include created_at/updated_at

    def test_team_detail_response_schema(self, client, sample_team_with_members):
        """Test that detail response has correct schema."""
        team = sample_team_with_members["team"]

        response = client.get(f"/teams/{team.id}")

        assert response.status_code == 200
        data = response.json()

        # Verify team fields
        assert "id" in data
        assert "name" in data
        assert "lead_id" in data
        assert "parent_team_id" in data
        assert "department_id" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert "members" in data

        # Verify member schema
        if data["members"]:
            member = data["members"][0]
            assert "id" in member
            assert "name" in member
            assert "email" in member


class TestTeamCascadingBehavior:
    """Test complex cascading behaviors."""

    def test_parent_change_cascades_department(self, client, test_db_session):
        """Test that changing parent cascades department to children."""
        # Create departments
        dept1 = Department(name="Engineering")
        dept2 = Department(name="Sales")
        test_db_session.add_all([dept1, dept2])
        test_db_session.flush()

        # Create hierarchy in dept1: A -> B -> C
        team_a = Team(name="A", department_id=dept1.id)
        test_db_session.add(team_a)
        test_db_session.flush()

        team_b = Team(name="B", parent_team_id=team_a.id, department_id=dept1.id)
        test_db_session.add(team_b)
        test_db_session.flush()

        team_c = Team(name="C", parent_team_id=team_b.id, department_id=dept1.id)
        test_db_session.add(team_c)
        test_db_session.flush()

        # Create new parent in dept2
        new_parent = Team(name="Sales Parent", department_id=dept2.id)
        test_db_session.add(new_parent)
        test_db_session.commit()

        # Move A under new_parent
        response = client.patch(
            f"/teams/{team_a.id}",
            json={"parent_team_id": str(new_parent.id)}
        )

        assert response.status_code == 200

        # Verify all teams now in dept2
        test_db_session.refresh(team_a)
        test_db_session.refresh(team_b)
        test_db_session.refresh(team_c)

        assert team_a.department_id == dept2.id
        assert team_b.department_id == dept2.id
        assert team_c.department_id == dept2.id

    def test_department_change_cascades_to_children(self, client, test_db_session):
        """Test that changing department cascades to all descendants."""
        # Create departments
        dept1 = Department(name="Engineering")
        dept2 = Department(name="Sales")
        test_db_session.add_all([dept1, dept2])
        test_db_session.flush()

        # Create hierarchy: A -> B -> C (all in dept1, A has no parent)
        team_a = Team(name="A", department_id=dept1.id)
        test_db_session.add(team_a)
        test_db_session.flush()

        team_b = Team(name="B", parent_team_id=team_a.id, department_id=dept1.id)
        test_db_session.add(team_b)
        test_db_session.flush()

        team_c = Team(name="C", parent_team_id=team_b.id, department_id=dept1.id)
        test_db_session.add(team_c)
        test_db_session.commit()

        # Change A's department
        response = client.patch(
            f"/teams/{team_a.id}",
            json={"department_id": str(dept2.id)}
        )

        assert response.status_code == 200

        # Verify cascaded to B and C
        test_db_session.refresh(team_a)
        test_db_session.refresh(team_b)
        test_db_session.refresh(team_c)

        assert team_a.department_id == dept2.id
        assert team_b.department_id == dept2.id
        assert team_c.department_id == dept2.id

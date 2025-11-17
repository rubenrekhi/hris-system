"""
test_export_api.py
------------------
API endpoint tests for export functionality.

Tests all export endpoints including:
- Directory exports (CSV, Excel, PDF)
- Org chart exports (CSV, Excel, PDF)
- Filter functionality
- File format validation
"""

import pytest
import csv
import io
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
from services.DepartmentService import DepartmentService
from services.TeamService import TeamService
from services.EmployeeService import EmployeeService
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
def sample_data(test_db_session):
    """Create sample data for export tests."""
    # Create departments
    dept_service = DepartmentService(test_db_session)
    dept1 = dept_service.create_department(
        name="Engineering",
        changed_by_user_id=None
    )
    dept2 = dept_service.create_department(
        name="Sales",
        changed_by_user_id=None
    )
    dept1_id = dept1.id
    dept2_id = dept2.id

    # Create teams
    team_service = TeamService(test_db_session)
    team1 = team_service.create_team(
        name="Backend Team",
        department_id=dept1_id,
        lead_id=None,
        parent_team_id=None,
        changed_by_user_id=None
    )
    team1_id = team1.id

    # Create employees
    emp_service = EmployeeService(test_db_session)

    # CEO (no manager)
    ceo = emp_service.create_employee(
        name="Jane CEO",
        email="jane.ceo@example.com",
        title="Chief Executive Officer",
        hired_on=date(2024, 1, 1),
        salary=200000,
        status=EmployeeStatus.ACTIVE,
        manager_id=None,
        department_id=None,
        team_id=None,
        changed_by_user_id=None
    )
    ceo_id = ceo.id

    # CTO (reports to CEO)
    cto = emp_service.create_employee(
        name="John CTO",
        email="john.cto@example.com",
        title="Chief Technology Officer",
        hired_on=date(2024, 2, 1),
        salary=180000,
        status=EmployeeStatus.ACTIVE,
        manager_id=ceo_id,
        department_id=dept1_id,
        team_id=None,
        changed_by_user_id=None
    )
    cto_id = cto.id

    # Developer (reports to CTO)
    dev = emp_service.create_employee(
        name="Alice Developer",
        email="alice.dev@example.com",
        title="Senior Developer",
        hired_on=date(2024, 3, 1),
        salary=120000,
        status=EmployeeStatus.ACTIVE,
        manager_id=cto_id,
        department_id=dept1_id,
        team_id=team1_id,
        changed_by_user_id=None
    )
    dev_id = dev.id

    # Sales person (reports to CEO, different department)
    sales = emp_service.create_employee(
        name="Bob Sales",
        email="bob.sales@example.com",
        title="Sales Manager",
        hired_on=date(2024, 4, 1),
        salary=100000,
        status=EmployeeStatus.ON_LEAVE,
        manager_id=ceo_id,
        department_id=dept2_id,
        team_id=None,
        changed_by_user_id=None
    )
    sales_id = sales.id

    test_db_session.commit()

    return {
        "dept1_id": dept1_id,
        "dept2_id": dept2_id,
        "team1_id": team1_id,
        "ceo_id": ceo_id,
        "cto_id": cto_id,
        "dev_id": dev_id,
        "sales_id": sales_id,
    }


class TestDirectoryExportCSV:
    """Tests for GET /exports/directory/csv endpoint."""

    def test_export_all_employees_csv(self, client, sample_data):
        """Test exporting all employees as CSV."""
        response = client.get("/exports/directory/csv")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert "employee_directory" in response.headers["content-disposition"]

        # Parse CSV content
        csv_content = response.content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)

        assert len(rows) == 4  # 4 employees
        assert rows[0]["Name"] == "Alice Developer"  # Alphabetically sorted
        assert rows[1]["Name"] == "Bob Sales"
        assert rows[2]["Name"] == "Jane CEO"
        assert rows[3]["Name"] == "John CTO"

    def test_export_filtered_by_department_csv(self, client, sample_data):
        """Test filtering by department."""
        response = client.get(f"/exports/directory/csv?department_id={sample_data['dept1_id']}")

        assert response.status_code == 200

        csv_content = response.content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)

        assert len(rows) == 2  # Only Engineering employees
        names = [row["Name"] for row in rows]
        assert "Alice Developer" in names
        assert "John CTO" in names
        assert "Bob Sales" not in names

    def test_export_filtered_by_status_csv(self, client, sample_data):
        """Test filtering by status."""
        response = client.get("/exports/directory/csv?status=ACTIVE")

        assert response.status_code == 200

        csv_content = response.content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)

        assert len(rows) == 3  # Only active employees
        statuses = [row["Status"] for row in rows]
        assert all(status == "ACTIVE" for status in statuses)

    def test_export_filtered_by_date_range_csv(self, client, sample_data):
        """Test filtering by hire date range."""
        response = client.get("/exports/directory/csv?hired_from=2024-02-01&hired_to=2024-03-31")

        assert response.status_code == 200

        csv_content = response.content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)

        assert len(rows) == 2  # CTO and Developer
        names = [row["Name"] for row in rows]
        assert "John CTO" in names
        assert "Alice Developer" in names


class TestDirectoryExportExcel:
    """Tests for GET /exports/directory/excel endpoint."""

    def test_export_all_employees_excel(self, client, sample_data):
        """Test exporting all employees as Excel."""
        response = client.get("/exports/directory/excel")

        assert response.status_code == 200
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers["content-type"]
        assert "attachment" in response.headers["content-disposition"]
        assert "employee_directory" in response.headers["content-disposition"]
        assert ".xlsx" in response.headers["content-disposition"]

        # Verify it's valid Excel by checking it's not empty and has proper size
        assert len(response.content) > 1000  # Excel files are larger than CSV

    def test_export_filtered_excel(self, client, sample_data):
        """Test filtered export as Excel."""
        response = client.get(f"/exports/directory/excel?team_id={sample_data['team1_id']}")

        assert response.status_code == 200
        assert len(response.content) > 0


class TestDirectoryExportPDF:
    """Tests for GET /exports/directory/pdf endpoint."""

    def test_export_all_employees_pdf(self, client, sample_data):
        """Test exporting all employees as PDF."""
        response = client.get("/exports/directory/pdf")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert "employee_directory" in response.headers["content-disposition"]
        assert ".pdf" in response.headers["content-disposition"]

        # Verify it's a valid PDF by checking magic bytes
        assert response.content.startswith(b"%PDF")

    def test_export_filtered_pdf(self, client, sample_data):
        """Test filtered export as PDF."""
        response = client.get(f"/exports/directory/pdf?status=ON_LEAVE")

        assert response.status_code == 200
        assert response.content.startswith(b"%PDF")


class TestOrgChartExportCSV:
    """Tests for GET /exports/org-chart/csv endpoint."""

    def test_export_org_chart_csv(self, client, sample_data):
        """Test exporting org chart as CSV with hierarchy."""
        response = client.get("/exports/org-chart/csv")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "org_chart" in response.headers["content-disposition"]

        # Parse CSV content
        csv_content = response.content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)

        assert len(rows) == 4

        # Check hierarchy levels
        # CEO should be level 0
        ceo_row = [r for r in rows if r["Name"] == "Jane CEO"][0]
        assert ceo_row["Level"] == "0"

        # CTO and Sales should be level 1 (report to CEO)
        cto_row = [r for r in rows if r["Name"] == "John CTO"][0]
        assert cto_row["Level"] == "1"

        sales_row = [r for r in rows if r["Name"] == "Bob Sales"][0]
        assert sales_row["Level"] == "1"

        # Developer should be level 2 (reports to CTO)
        dev_row = [r for r in rows if r["Name"] == "Alice Developer"][0]
        assert dev_row["Level"] == "2"

    def test_export_org_chart_filtered_csv(self, client, sample_data):
        """Test org chart export with filters."""
        response = client.get(f"/exports/org-chart/csv?department_id={sample_data['dept1_id']}")

        assert response.status_code == 200

        csv_content = response.content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)

        # Only Engineering department employees
        assert len(rows) == 2
        names = [row["Name"] for row in rows]
        assert "John CTO" in names
        assert "Alice Developer" in names


class TestOrgChartExportExcel:
    """Tests for GET /exports/org-chart/excel endpoint."""

    def test_export_org_chart_excel(self, client, sample_data):
        """Test exporting org chart as Excel."""
        response = client.get("/exports/org-chart/excel")

        assert response.status_code == 200
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers["content-type"]
        assert "org_chart" in response.headers["content-disposition"]

        # Verify it's valid Excel
        assert len(response.content) > 1000


class TestOrgChartExportPDF:
    """Tests for GET /exports/org-chart/pdf endpoint."""

    def test_export_org_chart_pdf(self, client, sample_data):
        """Test exporting org chart as visual PDF."""
        response = client.get("/exports/org-chart/pdf")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "org_chart" in response.headers["content-disposition"]

        # Verify it's a valid PDF
        assert response.content.startswith(b"%PDF")

    def test_export_org_chart_filtered_pdf(self, client, sample_data):
        """Test org chart PDF with filters."""
        response = client.get("/exports/org-chart/pdf?status=ACTIVE")

        assert response.status_code == 200
        assert response.content.startswith(b"%PDF")


class TestExportFilters:
    """Test various filter combinations."""

    def test_multiple_filters(self, client, sample_data):
        """Test applying multiple filters simultaneously."""
        response = client.get(
            f"/exports/directory/csv?department_id={sample_data['dept1_id']}&status=ACTIVE"
        )

        assert response.status_code == 200

        csv_content = response.content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)

        # Only active Engineering employees
        assert len(rows) == 2
        for row in rows:
            assert row["Status"] == "ACTIVE"
            assert row["Department"] == "Engineering"

    def test_empty_result_with_filters(self, client, sample_data):
        """Test export when filters return no results."""
        # Filter by non-existent department
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/exports/directory/csv?department_id={fake_uuid}")

        assert response.status_code == 200

        csv_content = response.content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)

        assert len(rows) == 0  # No employees match

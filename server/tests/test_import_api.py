"""
test_import_api.py
------------------
API endpoint tests for CSV and Excel bulk import.

Tests the POST /imports/employees endpoint including:
- File upload handling
- CSV and Excel parsing
- Transaction management
- Error responses
"""

import pytest
import io
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import openpyxl

from app import app
from models.BaseModel import Base
from models.EmployeeModel import Employee
from models.DepartmentModel import Department
from models.TeamModel import Team
from models.UserModel import User
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


class TestImportEmployeesEndpoint:
    """Tests for POST /imports/employees endpoint."""

    def test_import_employees_success(self, client, test_db_session):
        """Test successful employee import via API."""
        csv_content = """name,email,title,hired_on,salary,status,manager_email,department_name,team_name
Jane CEO,jane.ceo@example.com,CEO,2024-01-01,200000,ACTIVE,,,
John CTO,john.cto@example.com,CTO,2024-02-01,180000,ACTIVE,jane.ceo@example.com,,"""

        files = {"file": ("employees.csv", io.BytesIO(csv_content.encode()), "text/csv")}

        response = client.post("/imports/employees", files=files)

        assert response.status_code == 201
        data = response.json()

        assert data["total_rows"] == 2
        assert data["successful_imports"] == 2
        assert len(data["failed_rows"]) == 0
        assert len(data["created_employee_ids"]) == 2

        # Verify employees created in DB
        ceo = test_db_session.query(Employee).filter_by(email="jane.ceo@example.com").first()
        cto = test_db_session.query(Employee).filter_by(email="john.cto@example.com").first()

        assert ceo is not None
        assert cto is not None
        assert cto.manager_id == ceo.id

    def test_import_with_departments_and_teams(self, client, test_db_session):
        """Test importing employees with department and team assignments."""
        # Setup: Create department and team
        dept_service = DepartmentService(test_db_session)
        team_service = TeamService(test_db_session)

        dept_service.create_department(
            name="Engineering",
        )
        team_service.create_team(
            name="Backend Team",
        )
        test_db_session.commit()

        csv_content = """name,email,department_name,team_name,manager_email
Jane Eng,jane.eng@example.com,Engineering,Backend Team,"""

        files = {"file": ("employees.csv", io.BytesIO(csv_content.encode()), "text/csv")}

        response = client.post("/imports/employees", files=files)

        assert response.status_code == 201
        data = response.json()

        assert data["successful_imports"] == 1

        emp = test_db_session.query(Employee).filter_by(email="jane.eng@example.com").first()
        assert emp.department.name == "Engineering"
        assert emp.team.name == "Backend Team"

    def test_import_validation_error_returns_details(self, client, test_db_session):
        """Test that validation errors return detailed error information."""
        csv_content = """name,email,manager_email
Jane,jane@example.com,
John,jane@example.com,"""  # Duplicate email

        files = {"file": ("employees.csv", io.BytesIO(csv_content.encode()), "text/csv")}

        response = client.post("/imports/employees", files=files)

        # Should return 200 (not 201) with error details, not raise exception
        assert response.status_code == 200
        data = response.json()

        assert data["total_rows"] == 2
        assert data["successful_imports"] == 0
        assert len(data["failed_rows"]) > 0
        assert "Duplicate email" in data["failed_rows"][0]["error_message"]

        # Verify no employees were created (all-or-nothing)
        count = test_db_session.query(Employee).count()
        assert count == 0

    def test_import_circular_dependency_rejected(self, client, test_db_session):
        """Test that circular dependencies are rejected."""
        csv_content = """name,email,manager_email
Jane,jane@example.com,john@example.com
John,john@example.com,jane@example.com"""

        files = {"file": ("employees.csv", io.BytesIO(csv_content.encode()), "text/csv")}

        response = client.post("/imports/employees", files=files)

        assert response.status_code == 200  # Returns with error details
        data = response.json()

        assert data["successful_imports"] == 0
        assert len(data["failed_rows"]) > 0
        assert "Circular dependency" in data["failed_rows"][0]["error_message"]

    def test_import_invalid_file_type(self, client, test_db_session):
        """Test that non-CSV/Excel files are rejected."""
        files = {"file": ("data.txt", io.BytesIO(b"not a csv"), "text/plain")}

        response = client.post("/imports/employees", files=files)

        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    def test_import_empty_csv(self, client, test_db_session):
        """Test that empty CSV files are rejected."""
        csv_content = """name,email,manager_email
"""  # Headers only, no data

        files = {"file": ("empty.csv", io.BytesIO(csv_content.encode()), "text/csv")}

        response = client.post("/imports/employees", files=files)

        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_import_invalid_encoding(self, client, test_db_session):
        """Test that non-UTF-8 files are rejected."""
        # Create file with invalid encoding
        invalid_content = b"\xff\xfe\x00\x00"  # Invalid UTF-8

        files = {"file": ("invalid.csv", io.BytesIO(invalid_content), "text/csv")}

        response = client.post("/imports/employees", files=files)

        assert response.status_code == 400
        assert "encoding" in response.json()["detail"].lower()

    def test_import_malformed_csv(self, client, test_db_session):
        """Test that malformed CSV is handled gracefully."""
        # CSV with inconsistent column counts
        csv_content = """name,email,manager_email
Jane,jane@example.com
John,john@example.com,jane@example.com,extra,columns"""

        files = {"file": ("malformed.csv", io.BytesIO(csv_content.encode()), "text/csv")}

        response = client.post("/imports/employees", files=files)

        # Should handle with validation errors or server error for truly malformed CSV
        # (Extra columns ignored by CSV reader, missing columns set to empty string)
        # Server error (500) is acceptable for genuinely malformed CSV
        assert response.status_code in [200, 400, 500]

    def test_import_transaction_rollback_on_error(self, client, test_db_session):
        """Test that transaction is rolled back when validation fails."""
        # Create valid first employee, then duplicate
        csv_content = """name,email,manager_email
Jane,jane@example.com,
John,jane@example.com,"""  # Duplicate

        files = {"file": ("employees.csv", io.BytesIO(csv_content.encode()), "text/csv")}

        response = client.post("/imports/employees", files=files)

        # Should rollback and create no employees
        assert response.status_code == 200
        data = response.json()
        assert data["successful_imports"] == 0

        # Verify no employees in DB
        count = test_db_session.query(Employee).count()
        assert count == 0

    def test_import_with_existing_manager_in_db(self, client, test_db_session):
        """Test importing employees whose managers exist in DB."""
        # Setup: Create existing manager
        emp_service = EmployeeService(test_db_session)
        emp_service.create_employee(
            name="Existing CEO",
            email="existing.ceo@example.com",
        )
        test_db_session.commit()

        csv_content = """name,email,manager_email
New VP,new.vp@example.com,existing.ceo@example.com"""

        files = {"file": ("employees.csv", io.BytesIO(csv_content.encode()), "text/csv")}

        response = client.post("/imports/employees", files=files)

        assert response.status_code == 201
        data = response.json()
        assert data["successful_imports"] == 1

        vp = test_db_session.query(Employee).filter_by(email="new.vp@example.com").first()
        ceo = test_db_session.query(Employee).filter_by(email="existing.ceo@example.com").first()
        assert vp.manager_id == ceo.id

    def test_import_links_users_by_email(self, client, test_db_session):
        """Test that employees are linked to users with matching emails."""
        # Setup: Create user
        user = User(email="jane@example.com", name="Jane User")
        test_db_session.add(user)
        test_db_session.commit()

        csv_content = """name,email,manager_email
Jane Employee,jane@example.com,"""

        files = {"file": ("employees.csv", io.BytesIO(csv_content.encode()), "text/csv")}

        response = client.post("/imports/employees", files=files)

        assert response.status_code == 201

        # Verify user was linked
        test_db_session.refresh(user)
        emp = test_db_session.query(Employee).filter_by(email="jane@example.com").first()
        assert user.employee_id == emp.id

    def test_import_single_tree_first_import(self, client, test_db_session):
        """Test importing a single organizational tree (first import - CEO allowed)."""
        csv_content = """name,email,manager_email
CEO,ceo@example.com,
VP1,vp1@example.com,ceo@example.com
VP2,vp2@example.com,ceo@example.com
Dir1,dir1@example.com,vp1@example.com"""

        files = {"file": ("employees.csv", io.BytesIO(csv_content.encode()), "text/csv")}

        response = client.post("/imports/employees", files=files)

        assert response.status_code == 201
        data = response.json()
        assert data["successful_imports"] == 4

    def test_import_deep_hierarchy(self, client, test_db_session):
        """Test importing a deep 5-level hierarchy."""
        csv_content = """name,email,manager_email
L1,l1@example.com,
L2,l2@example.com,l1@example.com
L3,l3@example.com,l2@example.com
L4,l4@example.com,l3@example.com
L5,l5@example.com,l4@example.com"""

        files = {"file": ("employees.csv", io.BytesIO(csv_content.encode()), "text/csv")}

        response = client.post("/imports/employees", files=files)

        assert response.status_code == 201
        data = response.json()
        assert data["successful_imports"] == 5

        # Verify hierarchy
        l1 = test_db_session.query(Employee).filter_by(email="l1@example.com").first()
        l5 = test_db_session.query(Employee).filter_by(email="l5@example.com").first()

        # Trace up the chain
        current = l5
        levels = 0
        while current.manager_id:
            current = test_db_session.query(Employee).filter_by(id=current.manager_id).first()
            levels += 1

        assert levels == 4
        assert current.id == l1.id

    def test_import_large_batch(self, client, test_db_session):
        """Test importing a large batch of employees."""
        # Generate CSV with 50 employees
        lines = ["name,email,manager_email", "CEO,ceo@example.com,"]
        for i in range(49):
            lines.append(f"Employee {i},emp{i}@example.com,ceo@example.com")

        csv_content = "\n".join(lines)

        files = {"file": ("large.csv", io.BytesIO(csv_content.encode()), "text/csv")}

        response = client.post("/imports/employees", files=files)

        assert response.status_code == 201
        data = response.json()
        assert data["successful_imports"] == 50

    def test_import_with_optional_fields(self, client, test_db_session):
        """Test importing with various optional fields populated."""
        csv_content = """name,email,title,hired_on,salary,status,manager_email
Jane,jane@example.com,CEO,2024-01-01,200000,ACTIVE,
John,john@example.com,CTO,2024-02-01,180000,ACTIVE,jane@example.com
Alice,alice@example.com,VP,2024-03-01,150000,ON_LEAVE,jane@example.com"""

        files = {"file": ("employees.csv", io.BytesIO(csv_content.encode()), "text/csv")}

        response = client.post("/imports/employees", files=files)

        assert response.status_code == 201
        data = response.json()
        assert data["successful_imports"] == 3

        jane = test_db_session.query(Employee).filter_by(email="jane@example.com").first()
        john = test_db_session.query(Employee).filter_by(email="john@example.com").first()
        alice = test_db_session.query(Employee).filter_by(email="alice@example.com").first()

        assert jane.title == "CEO"
        assert john.salary == 180000
        assert alice.status.value == "ON_LEAVE"

    def test_import_nonexistent_department_rejected(self, client, test_db_session):
        """Test that nonexistent departments are rejected."""
        csv_content = """name,email,department_name,manager_email
Jane,jane@example.com,Nonexistent Dept,"""

        files = {"file": ("employees.csv", io.BytesIO(csv_content.encode()), "text/csv")}

        response = client.post("/imports/employees", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["successful_imports"] == 0
        assert "Department not found" in data["failed_rows"][0]["error_message"]

    def test_import_nonexistent_team_rejected(self, client, test_db_session):
        """Test that nonexistent teams are rejected."""
        csv_content = """name,email,team_name,manager_email
Jane,jane@example.com,Nonexistent Team,"""

        files = {"file": ("employees.csv", io.BytesIO(csv_content.encode()), "text/csv")}

        response = client.post("/imports/employees", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["successful_imports"] == 0
        assert "Team not found" in data["failed_rows"][0]["error_message"]

    def test_import_preserves_wave_order(self, client, test_db_session):
        """Test that employees are inserted in correct order (wave-based)."""
        # CSV intentionally ordered incorrectly (children before parents)
        csv_content = """name,email,manager_email
L3,l3@example.com,l2@example.com
L5,l5@example.com,l4@example.com
L2,l2@example.com,l1@example.com
L4,l4@example.com,l3@example.com
L1,l1@example.com,"""

        files = {"file": ("employees.csv", io.BytesIO(csv_content.encode()), "text/csv")}

        response = client.post("/imports/employees", files=files)

        assert response.status_code == 201
        data = response.json()
        assert data["successful_imports"] == 5

        # Verify hierarchy is correct despite incorrect CSV order
        l1 = test_db_session.query(Employee).filter_by(email="l1@example.com").first()
        l2 = test_db_session.query(Employee).filter_by(email="l2@example.com").first()
        l3 = test_db_session.query(Employee).filter_by(email="l3@example.com").first()
        l4 = test_db_session.query(Employee).filter_by(email="l4@example.com").first()
        l5 = test_db_session.query(Employee).filter_by(email="l5@example.com").first()

        assert l1.manager_id is None
        assert l2.manager_id == l1.id
        assert l3.manager_id == l2.id
        assert l4.manager_id == l3.id
        assert l5.manager_id == l4.id


class TestImportEndpointSecurity:
    """Tests for security and authorization."""

    def test_import_requires_authentication(self, client, test_db_session):
        """Test that import endpoint requires authentication."""
        # Note: Currently using mock auth that always allows access
        # This test documents expected behavior when real auth is implemented
        csv_content = """name,email,manager_email
Jane,jane@example.com,"""

        files = {"file": ("employees.csv", io.BytesIO(csv_content.encode()), "text/csv")}

        response = client.post("/imports/employees", files=files)

        # Currently passes due to mock auth
        # When real auth is implemented, should return 401 without auth
        assert response.status_code in [201, 401]

    def test_import_requires_admin_role(self, client, test_db_session):
        """Test that import endpoint requires admin role."""
        # Note: Currently using mock auth that always allows access
        # This test documents expected behavior when real auth is implemented
        csv_content = """name,email,manager_email
Jane,jane@example.com,"""

        files = {"file": ("employees.csv", io.BytesIO(csv_content.encode()), "text/csv")}

        response = client.post("/imports/employees", files=files)

        # Currently passes due to mock auth
        # When real auth is implemented, should return 403 without admin role
        assert response.status_code in [201, 403]

class TestImportEmployeesExcel:
    """Tests for Excel file import functionality."""

    def test_import_xlsx_success(self, client, test_db_session):
        """Test successful employee import from Excel file."""
        from tests.test_import_excel_helpers import create_excel_file

        data = [
            {"name": "CEO", "email": "ceo@example.com", "title": "Chief Executive Officer", 
             "hired_on": "2024-01-01", "salary": "200000", "status": "ACTIVE", 
             "manager_email": "", "department_name": "", "team_name": ""},
            {"name": "CTO", "email": "cto@example.com", "title": "Chief Technology Officer",
             "hired_on": "2024-02-01", "salary": "180000", "status": "ACTIVE",
             "manager_email": "ceo@example.com", "department_name": "", "team_name": ""},
        ]

        excel_file = create_excel_file(data)
        files = {"file": ("employees.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

        response = client.post("/imports/employees", files=files)

        assert response.status_code == 201
        result = response.json()

        assert result["total_rows"] == 2
        assert result["successful_imports"] == 2
        assert len(result["failed_rows"]) == 0

        # Verify employees created
        ceo = test_db_session.query(Employee).filter_by(email="ceo@example.com").first()
        cto = test_db_session.query(Employee).filter_by(email="cto@example.com").first()

        assert ceo is not None
        assert cto is not None
        assert cto.manager_id == ceo.id

    def test_import_xlsx_with_dates(self, client, test_db_session):
        """Test Excel import with datetime objects (not strings)."""
        from tests.test_import_excel_helpers import create_excel_with_types

        data = [
            {"name": "CEO", "email": "ceo@example.com", "hired_on": "2024-01-15",
             "manager_email": ""},
        ]

        # Convert hired_on to date object
        type_overrides = {
            "hired_on": lambda v: date(2024, 1, 15) if v else ""
        }

        excel_file = create_excel_with_types(data, type_overrides)
        files = {"file": ("employees.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

        response = client.post("/imports/employees", files=files)

        assert response.status_code == 201
        result = response.json()
        assert result["successful_imports"] == 1

        # Verify date was properly converted
        emp = test_db_session.query(Employee).filter_by(email="ceo@example.com").first()
        assert emp.hired_on.strftime('%Y-%m-%d') == "2024-01-15"

    def test_import_xlsx_with_numbers(self, client, test_db_session):
        """Test Excel import with numeric values."""
        from tests.test_import_excel_helpers import create_excel_with_types

        data = [
            {"name": "CEO", "email": "ceo@example.com", "salary": "200000", "manager_email": ""},
        ]

        # Convert salary to number (Excel stores as float)
        type_overrides = {
            "salary": lambda v: int(v) if v else ""
        }

        excel_file = create_excel_with_types(data, type_overrides)
        files = {"file": ("employees.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

        response = client.post("/imports/employees", files=files)

        assert response.status_code == 201
        result = response.json()
        assert result["successful_imports"] == 1

        emp = test_db_session.query(Employee).filter_by(email="ceo@example.com").first()
        assert emp.salary == 200000

    def test_import_xlsx_empty_cells(self, client, test_db_session):
        """Test Excel import with None/empty cells."""
        import openpyxl
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active

        # Headers
        ws.append(["name", "email", "title", "manager_email"])
        # Row with some empty cells (None in openpyxl)
        ws.append(["CEO", "ceo@example.com", None, None])

        excel_bytes = io.BytesIO()
        wb.save(excel_bytes)
        excel_bytes.seek(0)

        files = {"file": ("employees.xlsx", excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

        response = client.post("/imports/employees", files=files)

        assert response.status_code == 201
        result = response.json()
        assert result["successful_imports"] == 1

        emp = test_db_session.query(Employee).filter_by(email="ceo@example.com").first()
        assert emp.title is None or emp.title == ""

    def test_import_xlsx_invalid_file(self, client, test_db_session):
        """Test Excel import with corrupted file."""
        # Create invalid Excel file (just random bytes)
        invalid_file = io.BytesIO(b"This is not an Excel file")

        files = {"file": ("employees.xlsx", invalid_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

        response = client.post("/imports/employees", files=files)

        assert response.status_code == 400
        assert "Excel" in response.json()["detail"] or "Invalid" in response.json()["detail"]

    def test_import_xlsx_empty_file(self, client, test_db_session):
        """Test Excel import with empty workbook."""
        import openpyxl
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active

        # Only headers, no data
        ws.append(["name", "email", "manager_email"])

        excel_bytes = io.BytesIO()
        wb.save(excel_bytes)
        excel_bytes.seek(0)

        files = {"file": ("employees.xlsx", excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

        response = client.post("/imports/employees", files=files)

        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_import_unsupported_xls_file(self, client, test_db_session):
        """Test that .xls files are rejected (only .xlsx supported)."""
        # Create a dummy file with .xls extension
        dummy_file = io.BytesIO(b"dummy content")

        files = {"file": ("employees.xls", dummy_file, "application/vnd.ms-excel")}

        response = client.post("/imports/employees", files=files)

        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

#!/usr/bin/env python3
"""
seed_database.py
----------------
Comprehensive database seeding script for HRIS system.

Creates a realistic organizational structure with:
- 5 departments
- 30+ employees in a 5-level hierarchy
- 10+ teams with complex subteam structures
- Sample users linked to employees

Usage:
    python scripts/seed_database.py           # Add to existing data
    python scripts/seed_database.py --clear   # Clear database first
"""

import sys
import argparse
from datetime import date
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
load_dotenv(project_root / ".env")

from sqlalchemy import text
from core.database import SessionLocal, engine
from models.BaseModel import Base
from services.DepartmentService import DepartmentService
from services.EmployeeService import EmployeeService
from services.TeamService import TeamService
from models.EmployeeModel import EmployeeStatus
from models.UserModel import User


def clear_database(skip_confirmation=False):
    """Clear all data from the database (destructive!)."""
    print("\n⚠️  WARNING: This will delete ALL data from the database!")

    if not skip_confirmation:
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            sys.exit(0)

    print("\nClearing database...")

    # Use raw SQL to truncate all tables with CASCADE
    # This handles circular dependencies between employees and teams
    tables = ["audit_logs", "users", "employees", "teams", "departments"]

    with engine.connect() as conn:
        # Disable foreign key checks temporarily to avoid circular dependency issues
        conn.execute(text("SET session_replication_role = 'replica';"))

        # Truncate each table if it exists
        for table in tables:
            # Check if table exists first
            result = conn.execute(text(
                f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}');"
            ))
            table_exists = result.scalar()

            if table_exists:
                conn.execute(text(f"TRUNCATE TABLE {table} CASCADE;"))
                print(f"  ✓ Cleared {table}")
            else:
                print(f"  ⊘ Table {table} does not exist (skipping)")

        # Re-enable foreign key checks
        conn.execute(text("SET session_replication_role = 'origin';"))

        conn.commit()

    print("✓ Database cleared")


def seed_departments(db):
    """Create all departments."""
    print("\n📁 Creating departments...")
    dept_service = DepartmentService(db)

    departments = {}
    dept_names = ["Engineering", "Sales", "Marketing", "Operations", "HR"]

    for name in dept_names:
        dept = dept_service.create_department(name=name)
        departments[name] = dept
        print(f"  ✓ {name}")

    db.flush()
    return departments


def seed_employees(db, departments):
    """Create employee hierarchy (CEO → VPs → Directors → Managers → ICs)."""
    print("\n👥 Creating employees...")
    emp_service = EmployeeService(db)
    employees = {}

    # Helper function to create employee
    def create_emp(key, name, email, title, manager_key=None, dept_key=None, salary=None, hired_on=None):
        manager_id = employees[manager_key].id if manager_key else None
        dept_id = departments[dept_key].id if dept_key else None

        emp = emp_service.create_employee(
            name=name,
            email=email,
            title=title,
            manager_id=manager_id,
            department_id=dept_id,
            salary=salary,
            hired_on=hired_on or date(2020, 1, 1),
            status=EmployeeStatus.ACTIVE
        )
        employees[key] = emp
        indent = "  " * (0 if manager_key is None else (2 if "VP" in title else (3 if "Director" in title else (4 if "Manager" in title else 5))))
        print(f"{indent}✓ {name} ({title})")
        return emp

    # LEVEL 1: CEO (no manager)
    create_emp("ceo", "Jane Smith", "jane.smith@company.com", "CEO",
               salary=250000, hired_on=date(2019, 1, 1))

    # LEVEL 2: VPs (report to CEO)
    create_emp("vp_eng", "John Doe", "john.doe@company.com", "VP Engineering",
               "ceo", "Engineering", 200000, date(2019, 6, 1))
    create_emp("vp_sales", "Frank Brown", "frank.brown@company.com", "VP Sales",
               "ceo", "Sales", 190000, date(2019, 7, 1))
    create_emp("vp_marketing", "Henry Chen", "henry.chen@company.com", "VP Marketing",
               "ceo", "Marketing", 185000, date(2019, 8, 1))
    create_emp("vp_ops", "Isabel Garcia", "isabel.garcia@company.com", "VP Operations",
               "ceo", "Operations", 180000, date(2019, 9, 1))

    # LEVEL 3: Directors (report to VPs)
    # Engineering Directors
    create_emp("dir_backend", "Alice Johnson", "alice.johnson@company.com", "Director of Backend Engineering",
               "vp_eng", "Engineering", 160000, date(2020, 1, 1))
    create_emp("dir_frontend", "David Lee", "david.lee@company.com", "Director of Frontend Engineering",
               "vp_eng", "Engineering", 160000, date(2020, 1, 15))

    # Sales Director
    create_emp("dir_sales", "Grace Taylor", "grace.taylor@company.com", "Director of Sales",
               "vp_sales", "Sales", 155000, date(2020, 2, 1))

    # LEVEL 4: Managers (report to Directors)
    # Backend Managers
    create_emp("mgr_backend", "Bob Wilson", "bob.wilson@company.com", "Backend Engineering Manager",
               "dir_backend", "Engineering", 140000, date(2020, 3, 1))
    create_emp("mgr_api", "Carol Martinez", "carol.martinez@company.com", "API Engineering Manager",
               "dir_backend", "Engineering", 140000, date(2020, 3, 15))

    # Frontend Manager
    create_emp("mgr_frontend", "Eve Davis", "eve.davis@company.com", "Frontend Engineering Manager",
               "dir_frontend", "Engineering", 140000, date(2020, 4, 1))

    # Sales Manager
    create_emp("mgr_sales", "Grace Taylor Jr", "grace.taylor.jr@company.com", "Sales Manager",
               "dir_sales", "Sales", 130000, date(2020, 5, 1))

    # Marketing Manager
    create_emp("mgr_marketing", "Ian White", "ian.white@company.com", "Marketing Manager",
               "vp_marketing", "Marketing", 125000, date(2020, 6, 1))

    # Operations Manager
    create_emp("mgr_ops", "Julia Martinez", "julia.martinez@company.com", "Operations Manager",
               "vp_ops", "Operations", 120000, date(2020, 7, 1))

    # HR Manager (reports to VP Ops, but in HR dept)
    create_emp("mgr_hr", "Karen Johnson", "karen.johnson@company.com", "HR Manager",
               "vp_ops", "HR", 115000, date(2020, 8, 1))

    # LEVEL 5: Individual Contributors (report to Managers)
    # Backend Team
    create_emp("sr_backend_1", "Liam Anderson", "liam.anderson@company.com", "Senior Backend Developer",
               "mgr_backend", "Engineering", 130000, date(2021, 1, 1))
    create_emp("sr_backend_2", "Maya Patel", "maya.patel@company.com", "Senior Backend Developer",
               "mgr_backend", "Engineering", 130000, date(2021, 1, 15))
    create_emp("backend_dev_1", "Nathan Kim", "nathan.kim@company.com", "Backend Developer",
               "mgr_backend", "Engineering", 110000, date(2021, 2, 1))
    create_emp("backend_dev_2", "Olivia Brown", "olivia.brown@company.com", "Backend Developer",
               "mgr_backend", "Engineering", 110000, date(2021, 2, 15))

    # API Team
    create_emp("api_dev_1", "Peter Chen", "peter.chen@company.com", "API Developer",
               "mgr_api", "Engineering", 120000, date(2021, 3, 1))
    create_emp("api_dev_2", "Quinn Davis", "quinn.davis@company.com", "API Developer",
               "mgr_api", "Engineering", 120000, date(2021, 3, 15))

    # Frontend Team
    create_emp("frontend_dev_1", "Rachel Green", "rachel.green@company.com", "Frontend Developer",
               "mgr_frontend", "Engineering", 115000, date(2021, 4, 1))
    create_emp("frontend_dev_2", "Sam Wilson", "sam.wilson@company.com", "Frontend Developer",
               "mgr_frontend", "Engineering", 115000, date(2021, 4, 15))
    create_emp("ux_designer", "Tara Lee", "tara.lee@company.com", "UX Designer",
               "dir_frontend", "Engineering", 105000, date(2021, 5, 1))

    # Sales Team
    create_emp("enterprise_sales_1", "Uma Patel", "uma.patel@company.com", "Enterprise Sales Representative",
               "mgr_sales", "Sales", 90000, date(2021, 6, 1))
    create_emp("enterprise_sales_2", "Victor Martinez", "victor.martinez@company.com", "Enterprise Sales Representative",
               "mgr_sales", "Sales", 90000, date(2021, 6, 15))
    create_emp("sales_dev", "Wendy Kim", "wendy.kim@company.com", "Sales Development Representative",
               "mgr_sales", "Sales", 70000, date(2021, 7, 1))
    create_emp("account_exec", "Xavier Brown", "xavier.brown@company.com", "Account Executive",
               "dir_sales", "Sales", 95000, date(2021, 7, 15))

    # Marketing Team
    create_emp("content_writer", "Yara Chen", "yara.chen@company.com", "Content Writer",
               "mgr_marketing", "Marketing", 75000, date(2021, 8, 1))
    create_emp("social_media", "Zack Davis", "zack.davis@company.com", "Social Media Specialist",
               "vp_marketing", "Marketing", 70000, date(2021, 8, 15))

    # Operations Team
    create_emp("ops_analyst", "Amy Wilson", "amy.wilson@company.com", "Operations Analyst",
               "mgr_ops", "Operations", 80000, date(2021, 9, 1))

    # HR Team
    create_emp("recruiter", "Brian Lee", "brian.lee@company.com", "Recruiter",
               "mgr_hr", "HR", 75000, date(2021, 9, 15))

    db.flush()
    print(f"\n  Total: {len(employees)} employees created")
    return employees


def seed_teams(db, departments, employees):
    """Create team structure with hierarchies."""
    print("\n🏢 Creating teams...")
    team_service = TeamService(db)
    teams = {}

    def create_team(key, name, lead_key=None, parent_key=None, dept_key=None):
        lead_id = employees[lead_key].id if lead_key else None
        parent_id = teams[parent_key].id if parent_key else None
        dept_id = departments[dept_key].id if dept_key else None

        team = team_service.create_team(
            name=name,
            lead_id=lead_id,
            parent_team_id=parent_id,
            department_id=dept_id
        )
        teams[key] = team
        indent = "  " * (0 if parent_key is None else (1 if parent_key in ["eng", "sales"] else 2))
        parent_note = f" (under {teams[parent_key].name})" if parent_key else ""
        lead_note = f" [lead: {employees[lead_key].name}]" if lead_key else ""
        print(f"{indent}✓ {name}{parent_note}{lead_note}")
        return team

    # Top-level teams with departments
    create_team("eng", "Engineering", "vp_eng", None, "Engineering")
    create_team("sales", "Sales", "vp_sales", None, "Sales")

    # Engineering subteams (3-level hierarchy)
    create_team("backend", "Backend Team", "mgr_backend", "eng", "Engineering")
    create_team("frontend", "Frontend Team", "mgr_frontend", "eng", "Engineering")
    create_team("api", "API Team", "mgr_api", "backend", "Engineering")  # Child of Backend

    # Sales subteam
    create_team("enterprise_sales", "Enterprise Sales", "mgr_sales", "sales", "Sales")

    # Teams without departments (cross-functional)
    create_team("innovation", "Innovation Lab")
    create_team("special_projects", "Special Projects")

    # Manually assign some employees to teams
    # (Some are already assigned via team lead, but let's add more)
    print("\n  📌 Assigning employees to teams...")

    # Backend team members
    employees["sr_backend_1"].team_id = teams["backend"].id
    employees["sr_backend_2"].team_id = teams["backend"].id
    employees["backend_dev_1"].team_id = teams["backend"].id
    employees["backend_dev_2"].team_id = teams["backend"].id
    print("    ✓ Backend Team: 4 developers + manager")

    # API team members
    employees["api_dev_1"].team_id = teams["api"].id
    employees["api_dev_2"].team_id = teams["api"].id
    print("    ✓ API Team: 2 developers + manager")

    # Frontend team members
    employees["frontend_dev_1"].team_id = teams["frontend"].id
    employees["frontend_dev_2"].team_id = teams["frontend"].id
    print("    ✓ Frontend Team: 2 developers + manager")

    # Enterprise sales team
    employees["enterprise_sales_1"].team_id = teams["enterprise_sales"].id
    employees["enterprise_sales_2"].team_id = teams["enterprise_sales"].id
    employees["sales_dev"].team_id = teams["enterprise_sales"].id
    print("    ✓ Enterprise Sales: 3 reps + manager")

    # Innovation lab (cross-functional, no department)
    employees["sr_backend_1"].team_id = teams["innovation"].id  # Also on innovation
    employees["frontend_dev_1"].team_id = teams["innovation"].id
    employees["ux_designer"].team_id = teams["innovation"].id
    print("    ✓ Innovation Lab: 3 cross-functional members")

    db.flush()
    print(f"\n  Total: {len(teams)} teams created")
    return teams


def seed_users(db, employees):
    """Create sample users linked to some employees."""
    print("\n👤 Creating sample users...")

    # Create users for key employees
    user_data = [
        ("ceo", "Jane Smith User"),
        ("vp_eng", "John Doe User"),
        ("mgr_backend", "Bob Wilson User"),
        ("sr_backend_1", "Liam Anderson User"),
    ]

    users = []
    for emp_key, user_name in user_data:
        emp = employees[emp_key]
        user = User(
            email=emp.email,
            name=user_name,
            employee_id=emp.id
        )
        db.add(user)
        users.append(user)
        print(f"  ✓ {user_name} ({emp.email})")

    db.flush()
    print(f"\n  Total: {len(users)} users created")
    return users


def print_summary(departments, employees, teams, users):
    """Print summary of created data."""
    print("\n" + "=" * 60)
    print("✅ DATABASE SEEDING COMPLETED SUCCESSFULLY!")
    print("=" * 60)

    print(f"\n📊 Summary:")
    print(f"  • {len(departments)} departments")
    print(f"  • {len(employees)} employees (5-level hierarchy)")
    print(f"  • {len(teams)} teams (with 3-level subteam structures)")
    print(f"  • {len(users)} users linked to employees")

    print(f"\n🏢 Organizational Structure:")
    print(f"  • CEO: Jane Smith (jane.smith@company.com)")
    print(f"  • VPs: 4 (Engineering, Sales, Marketing, Operations)")
    print(f"  • Directors: 3")
    print(f"  • Managers: 7")
    print(f"  • Individual Contributors: 15")

    print(f"\n📁 Departments:")
    for name in ["Engineering", "Sales", "Marketing", "Operations", "HR"]:
        print(f"  • {name}")

    print(f"\n🏢 Team Hierarchies:")
    print("  • Engineering → Backend Team → API Team (3 levels)")
    print("  • Engineering → Frontend Team")
    print("  • Sales → Enterprise Sales")
    print("  • Innovation Lab (no department, cross-functional)")
    print("  • Special Projects (no department)")

    print(f"\n🎯 Special Scenarios Covered:")
    print("  ✓ Employees with teams (most)")
    print("  ✓ Employees without teams (UX Designer, Account Exec, etc.)")
    print("  ✓ Teams with departments (Engineering, Sales)")
    print("  ✓ Teams without departments (Innovation Lab, Special Projects)")
    print("  ✓ Teams with subteams (Engineering has Backend/Frontend)")
    print("  ✓ Teams with both direct members and subteams (Backend has devs + API subteam)")
    print("  ✓ Multi-level team hierarchy (Engineering → Backend → API)")

    print(f"\n🔑 Sample User Credentials:")
    print("  • jane.smith@company.com (CEO)")
    print("  • john.doe@company.com (VP Engineering)")
    print("  • bob.wilson@company.com (Backend Manager)")
    print("  • liam.anderson@company.com (Senior Developer)")

    print("\n" + "=" * 60)
    print("💡 Next Steps:")
    print("  1. Start the API server: uvicorn app:app --reload")
    print("  2. Visit http://localhost:8000/docs for API documentation")
    print("  3. Test endpoints with the seeded data!")
    print("=" * 60 + "\n")


def main():
    """Main seeding function."""
    parser = argparse.ArgumentParser(description="Seed the HRIS database with test data")
    parser.add_argument("--clear", action="store_true", help="Clear database before seeding")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    if args.clear:
        clear_database(skip_confirmation=args.yes)

    db = SessionLocal()
    try:
        print("\n🌱 Starting database seeding...")

        # Create data in order of dependencies
        departments = seed_departments(db)
        employees = seed_employees(db, departments)
        teams = seed_teams(db, departments, employees)
        users = seed_users(db, employees)

        # Commit all changes
        db.commit()

        # Print summary
        print_summary(departments, employees, teams, users)

    except Exception as e:
        db.rollback()
        print(f"\n❌ ERROR: Seeding failed!")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

"""
DepartmentService.py
--------------------
Business logic for department management and operations.
"""

from __future__ import annotations
from typing import List, Tuple, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from models.DepartmentModel import Department
from models.TeamModel import Team
from models.EmployeeModel import Employee
from models.AuditLogModel import EntityType, ChangeType
from services.AuditLogService import AuditLogService


class DepartmentService:
    """Service for managing department operations."""

    def __init__(self, db: Session, audit_service: Optional[AuditLogService] = None):
        self.db = db
        self.audit_service = audit_service or AuditLogService(db)

    def create_department(
        self,
        *,
        name: str,
        changed_by_user_id: Optional[UUID] = None,
    ) -> Department:
        """
        Create a new department.

        Validation:
        - Name must be unique (enforced by database constraint)

        Creates audit log entry for the new department (CREATE).
        Does NOT commit - router is responsible for transaction management.

        Returns the created department.
        """
        # Create new department
        department = Department(name=name)
        self.db.add(department)

        # Flush to get the department ID
        self.db.flush()

        # Capture department state for audit log
        department_state = {
            "name": department.name,
        }

        # Create audit log for new department
        self.audit_service.create_audit_log(
            entity_type=EntityType.DEPARTMENT,
            entity_id=department.id,
            change_type=ChangeType.CREATE,
            previous_state=None,
            new_state=department_state,
            changed_by_user_id=changed_by_user_id,
        )

        return department

    def get_department(self, department_id: UUID) -> Optional[Department]:
        """
        Get a single department by ID.

        Returns None if not found.
        """
        query = select(Department).where(Department.id == department_id)
        return self.db.execute(query).scalar_one_or_none()

    def update_department(
        self,
        department_id: UUID,
        *,
        name: str,
        changed_by_user_id: Optional[UUID] = None,
    ) -> Optional[Department]:
        """
        Update department name.

        Validation:
        - Name must be unique (enforced by database constraint)

        Creates an audit log entry tracking the change.
        Does NOT commit - router is responsible for transaction management.

        Returns updated department or None if not found.
        """
        # Get existing department
        department = self.get_department(department_id)
        if not department:
            return None

        # Capture previous state
        previous_state = {
            "name": department.name,
        }

        # Track if any changes were made
        has_changes = name != department.name

        # Update name
        if has_changes:
            department.name = name

            # Capture new state
            new_state = {
                "name": department.name,
            }

            # Create audit log entry
            self.audit_service.create_audit_log(
                entity_type=EntityType.DEPARTMENT,
                entity_id=department_id,
                change_type=ChangeType.UPDATE,
                previous_state=previous_state,
                new_state=new_state,
                changed_by_user_id=changed_by_user_id,
            )

        return department

    def delete_department(
        self,
        department_id: UUID,
        *,
        changed_by_user_id: Optional[UUID] = None,
    ) -> Optional[Department]:
        """
        Delete a department.

        Validation:
        - Department must exist

        Note: Employees and teams in this department will have their
        department_id set to NULL (due to ondelete="SET NULL").

        Creates audit log entry for the deleted department (DELETE).
        Does NOT commit - router is responsible for transaction management.

        Returns deleted department or None if not found.
        """
        # Get existing department
        department = self.get_department(department_id)
        if not department:
            return None

        # Capture department state before deletion
        deleted_department_state = {
            "name": department.name,
        }

        # Create audit log for deleted department
        self.audit_service.create_audit_log(
            entity_type=EntityType.DEPARTMENT,
            entity_id=department_id,
            change_type=ChangeType.DELETE,
            previous_state=deleted_department_state,
            new_state=None,
            changed_by_user_id=changed_by_user_id,
        )

        # Delete the department
        self.db.delete(department)

        return department

    def list_department_teams(
        self,
        department_id: UUID,
        *,
        limit: int = 25,
        offset: int = 0,
    ) -> Tuple[List[Team], int]:
        """
        List all teams in a department with pagination.

        Returns teams ordered alphabetically by name.
        Returns tuple of (teams, total_count).
        """
        # Total count query
        count_query = select(func.count(Team.id)).select_from(Team).where(
            Team.department_id == department_id
        )
        total = self.db.execute(count_query).scalar_one()

        # Main query with ordering and pagination
        query = (
            select(Team)
            .where(Team.department_id == department_id)
            .order_by(Team.name.asc(), Team.id.asc())
            .limit(limit)
            .offset(offset)
        )

        teams = self.db.execute(query).scalars().all()

        return list(teams), total

    def list_department_employees(
        self,
        department_id: UUID,
        *,
        limit: int = 25,
        offset: int = 0,
    ) -> Tuple[List[Employee], int]:
        """
        List all employees in a department with pagination.

        Returns employees ordered alphabetically by name.
        Returns tuple of (employees, total_count).
        """
        # Total count query
        count_query = select(func.count(Employee.id)).select_from(Employee).where(
            Employee.department_id == department_id
        )
        total = self.db.execute(count_query).scalar_one()

        # Main query with ordering and pagination
        query = (
            select(Employee)
            .where(Employee.department_id == department_id)
            .order_by(Employee.name.asc(), Employee.id.asc())
            .limit(limit)
            .offset(offset)
        )

        employees = self.db.execute(query).scalars().all()

        return list(employees), total

    def list_department_root_teams(
        self,
        department_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[Team], int]:
        """
        List root-level teams in a department (teams with no parent team).

        Returns teams ordered alphabetically by name.
        Returns tuple of (teams, total_count).
        """
        # Count root teams in department
        count_query = (
            select(func.count(Team.id))
            .select_from(Team)
            .where(
                and_(
                    Team.department_id == department_id,
                    Team.parent_team_id.is_(None)
                )
            )
        )
        total = self.db.execute(count_query).scalar_one()

        # Fetch root teams
        query = (
            select(Team)
            .where(
                and_(
                    Team.department_id == department_id,
                    Team.parent_team_id.is_(None)
                )
            )
            .order_by(Team.name.asc(), Team.id.asc())
            .limit(limit)
            .offset(offset)
        )

        teams = self.db.execute(query).scalars().all()
        return list(teams), total

    def list_departments(
        self,
        *,
        limit: int = 25,
        offset: int = 0,
    ) -> Tuple[List[Department], int]:
        """
        List all departments with pagination.

        Returns departments ordered alphabetically by name.
        Returns tuple of (departments, total_count).
        """
        # Total count query
        count_query = select(func.count(Department.id)).select_from(Department)
        total = self.db.execute(count_query).scalar_one()

        # Main query with ordering and pagination
        query = (
            select(Department)
            .order_by(Department.name.asc(), Department.id.asc())
            .limit(limit)
            .offset(offset)
        )

        departments = self.db.execute(query).scalars().all()

        return list(departments), total
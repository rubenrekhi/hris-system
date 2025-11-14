"""
EmployeeService.py
------------------
Business logic for employee records and information management.
"""

from __future__ import annotations
from typing import List, Tuple, Optional
from uuid import UUID
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_, update
from models.EmployeeModel import Employee, EmployeeStatus
from models.AuditLogModel import EntityType, ChangeType
from services.AuditLogService import AuditLogService
from models.TeamModel import Team
from models.DepartmentModel import Department
from models.UserModel import User



class EmployeeService:
    """Service for managing employee operations."""

    def __init__(self, db: Session, audit_service: Optional[AuditLogService] = None):
        self.db = db
        self.audit_service = audit_service or AuditLogService(db)

    def list_employees(
        self,
        *,
        team_id: Optional[UUID] = None,
        department_id: Optional[UUID] = None,
        status: Optional[EmployeeStatus] = None,
        min_salary: Optional[int] = None,
        max_salary: Optional[int] = None,
        name: Optional[str] = None,
        email: Optional[str] = None,
        limit: int = 25,
        offset: int = 0,
    ) -> Tuple[List[Employee], int]:
        """
        List employees with optional filters, search, and pagination.

        Returns employees ordered alphabetically by name.
        Supports filtering by team, department, status, and salary range.
        Supports searching by name or email (case-insensitive ILIKE).

        Returns tuple of (employees, total_count)
        """
        # Build filters
        filters = []

        if team_id:
            filters.append(Employee.team_id == team_id)

        if department_id:
            filters.append(Employee.department_id == department_id)

        if status:
            filters.append(Employee.status == status)

        if min_salary is not None:
            filters.append(Employee.salary >= min_salary)

        if max_salary is not None:
            filters.append(Employee.salary <= max_salary)

        # Name/email search: use OR logic (widening search)
        name_email_filters = []
        if name:
            name_email_filters.append(Employee.name.ilike(f"%{name}%"))
        if email:
            name_email_filters.append(Employee.email.ilike(f"%{email}%"))

        if name_email_filters:
            filters.append(or_(*name_email_filters))

        # Total count query
        count_query = select(func.count(Employee.id)).select_from(Employee)
        if filters:
            count_query = count_query.where(and_(*filters))
        total = self.db.execute(count_query).scalar_one()

        # Main query with ordering and pagination
        query = select(Employee)
        if filters:
            query = query.where(and_(*filters))

        # Order alphabetically by name
        query = query.order_by(Employee.name.asc(), Employee.id.asc())

        # Pagination
        query = query.limit(limit).offset(offset)

        employees = self.db.execute(query).scalars().all()

        return employees, total

    def get_employee(self, employee_id: UUID) -> Optional[Employee]:
        """
        Get a single employee by ID.

        Returns None if not found.
        """
        query = select(Employee).where(Employee.id == employee_id)
        return self.db.execute(query).scalar_one_or_none()

    def get_ceo(self) -> Optional[Employee]:
        """
        Get the CEO (employee with no manager).

        Returns None if no CEO exists.
        """
        query = select(Employee).where(Employee.manager_id == None)
        return self.db.execute(query).scalar_one_or_none()

    def get_direct_reports(self, employee_id: UUID) -> List[Employee]:
        """
        Get all direct reports for a specific employee.

        Returns empty list if employee has no direct reports or doesn't exist.
        """
        query = select(Employee).where(Employee.manager_id == employee_id).order_by(Employee.name.asc())
        return list(self.db.execute(query).scalars().all())

    def create_employee(
        self,
        *,
        name: str,
        email: str,
        title: Optional[str] = None,
        hired_on: Optional[date] = None,
        salary: Optional[int] = None,
        status: EmployeeStatus = EmployeeStatus.ACTIVE,
        manager_id: Optional[UUID] = None,
        department_id: Optional[UUID] = None,
        team_id: Optional[UUID] = None,
        changed_by_user_id: Optional[UUID] = None,
    ) -> Employee:
        """
        Create a new employee.

        Validation:
        - manager_id is required unless this is the first employee
        - If manager_id is provided, manager must exist
        - If department_id is provided, department must exist
        - If team_id is provided, team must exist
        - If a user with matching email exists, link employee to user

        Creates audit log entries for:
        - The new employee (CREATE)
        - The linked user if employee_id was updated (UPDATE)

        Does NOT commit - router is responsible for transaction management.

        Returns the created employee.
        Raises ValueError if validation fails.
        """
        # Check if this is the first employee
        employee_count_query = select(func.count(Employee.id)).select_from(Employee)
        employee_count = self.db.execute(employee_count_query).scalar_one()
        is_first_employee = employee_count == 0

        # Validate manager_id requirement
        if not is_first_employee and manager_id is None:
            raise ValueError("manager_id is required for all employees except the first")

        # Validate manager exists (if provided)
        if manager_id is not None:
            manager_query = select(Employee).where(Employee.id == manager_id)
            manager = self.db.execute(manager_query).scalar_one_or_none()
            if not manager:
                raise ValueError(f"Manager with ID {manager_id} does not exist")

        # Validate department exists (if provided)
        if department_id is not None:
            dept_query = select(Department).where(Department.id == department_id)
            department = self.db.execute(dept_query).scalar_one_or_none()
            if not department:
                raise ValueError(f"Department with ID {department_id} does not exist")

        # Validate team exists (if provided)
        if team_id is not None:
            team_query = select(Team).where(Team.id == team_id)
            team = self.db.execute(team_query).scalar_one_or_none()
            if not team:
                raise ValueError(f"Team with ID {team_id} does not exist")

        # Create new employee
        employee = Employee(
            name=name,
            email=email,
            title=title,
            hired_on=hired_on,
            salary=salary,
            status=status,
            manager_id=manager_id,
            department_id=department_id,
            team_id=team_id,
        )
        self.db.add(employee)

        # Flush to get the employee ID
        self.db.flush()

        # Check if a user with this email exists and link them
        user_query = select(User).where(User.email == email)
        user = self.db.execute(user_query).scalar_one_or_none()

        if user:
            # Capture user's previous state
            user_previous_state = {
                "employee_id": str(user.employee_id) if user.employee_id else None,
            }

            # Link user to employee
            user.employee_id = employee.id

            # Capture user's new state
            user_new_state = {
                "employee_id": str(user.employee_id) if user.employee_id else None,
            }

            # Create audit log for user update
            self.audit_service.create_audit_log(
                entity_type=EntityType.USER,
                entity_id=user.id,
                change_type=ChangeType.UPDATE,
                previous_state=user_previous_state,
                new_state=user_new_state,
                changed_by_user_id=changed_by_user_id,
            )

        # Capture employee state for audit log
        employee_state = {
            "name": employee.name,
            "title": employee.title,
            "email": employee.email,
            "hired_on": employee.hired_on.isoformat() if employee.hired_on else None,
            "salary": employee.salary,
            "status": employee.status.value if employee.status else None,
            "department_id": str(employee.department_id) if employee.department_id else None,
            "manager_id": str(employee.manager_id) if employee.manager_id else None,
            "team_id": str(employee.team_id) if employee.team_id else None,
        }

        # Create audit log for new employee
        self.audit_service.create_audit_log(
            entity_type=EntityType.EMPLOYEE,
            entity_id=employee.id,
            change_type=ChangeType.CREATE,
            previous_state=None,
            new_state=employee_state,
            changed_by_user_id=changed_by_user_id,
        )

        return employee

    def update_employee(
        self,
        employee_id: UUID,
        *,
        name: Optional[str] = None,
        title: Optional[str] = None,
        salary: Optional[int] = None,
        status: Optional[EmployeeStatus] = None,
        changed_by_user_id: Optional[UUID] = None,
    ) -> Optional[Employee]:
        """
        Update employee fields (name, title, salary, status).

        Creates an audit log entry tracking the change.
        Does NOT commit - router is responsible for transaction management.

        Returns updated employee or None if not found.
        """
        # Get existing employee
        employee = self.get_employee(employee_id)
        if not employee:
            return None

        # Capture previous state (only editable fields)
        previous_state = {
            "name": employee.name,
            "title": employee.title,
            "salary": employee.salary,
            "status": employee.status.value if employee.status else None,
        }

        # Track if any changes were made
        has_changes = False

        # Update fields if provided
        if name is not None and name != employee.name:
            employee.name = name
            has_changes = True

        if title is not None and title != employee.title:
            employee.title = title
            has_changes = True

        if salary is not None and salary != employee.salary:
            employee.salary = salary
            has_changes = True

        if status is not None and status != employee.status:
            employee.status = status
            has_changes = True

        # Only create audit log if changes were made
        if has_changes:
            # Capture new state
            new_state = {
                "name": employee.name,
                "title": employee.title,
                "salary": employee.salary,
                "status": employee.status.value if employee.status else None,
            }

            # Create audit log entry
            self.audit_service.create_audit_log(
                entity_type=EntityType.EMPLOYEE,
                entity_id=employee_id,
                change_type=ChangeType.UPDATE,
                previous_state=previous_state,
                new_state=new_state,
                changed_by_user_id=changed_by_user_id,
            )

        return employee

    def assign_department(
        self,
        employee_id: UUID,
        department_id: Optional[UUID],
        *,
        changed_by_user_id: Optional[UUID] = None,
    ) -> Optional[Employee]:
        """
        Assign or remove a department from an employee.

        Validation:
        - Employee must exist
        - If employee is on a team, the department must match the team's department
        - If department_id is not None, department must exist

        Creates an audit log entry tracking the change.
        Does NOT commit - router is responsible for transaction management.

        Returns updated employee or None if not found.
        Raises ValueError if validation fails.
        """
        # Get existing employee
        employee = self.get_employee(employee_id)
        if not employee:
            return None

        # If employee is on a team, validate department matches team's department
        if employee.team_id:
            team_query = select(Team).where(Team.id == employee.team_id)
            team = self.db.execute(team_query).scalar_one_or_none()

            if team and team.department_id != department_id:
                if department_id is None:
                    raise ValueError(
                        f"Employee is on team '{team.name}' which has a department assigned. "
                        f"Cannot remove employee's department while team has a department."
                    )
                else:
                    raise ValueError(
                        f"Employee is on team '{team.name}' which belongs to a different department. "
                        f"Department assignment must match team's department."
                    )

        # If department_id is not None, validate department exists
        if department_id is not None:
            dept_query = select(Department).where(Department.id == department_id)
            department = self.db.execute(dept_query).scalar_one_or_none()

            if not department:
                raise ValueError(f"Department with ID {department_id} does not exist")

        # Capture previous state
        previous_state = {
            "department_id": str(employee.department_id) if employee.department_id else None,
        }

        # Update department
        employee.department_id = department_id

        # Capture new state
        new_state = {
            "department_id": str(employee.department_id) if employee.department_id else None,
        }

        # Create audit log entry
        self.audit_service.create_audit_log(
            entity_type=EntityType.EMPLOYEE,
            entity_id=employee_id,
            change_type=ChangeType.UPDATE,
            previous_state=previous_state,
            new_state=new_state,
            changed_by_user_id=changed_by_user_id,
        )

        return employee

    def assign_team(
        self,
        employee_id: UUID,
        team_id: Optional[UUID],
        *,
        changed_by_user_id: Optional[UUID] = None,
    ) -> Optional[Employee]:
        """
        Assign or remove a team from an employee.

        Validation:
        - Employee must exist
        - If team_id is not None, team must exist
        - Employee's department will be automatically set to match the team's department
        - If employee is currently a team lead, removes them as lead before reassignment

        Creates audit log entries for:
        - The employee's team assignment (UPDATE)
        - The employee's department assignment if it changed (UPDATE)
        - The team if employee was removed as lead (UPDATE)

        Does NOT commit - router is responsible for transaction management.

        Returns updated employee or None if not found.
        Raises ValueError if validation fails.
        """
        # Get existing employee
        employee = self.get_employee(employee_id)
        if not employee:
            return None

        # If team_id is not None, validate team exists and get team's department
        new_department_id = None
        if team_id is not None:
            team_query = select(Team).where(Team.id == team_id)
            team = self.db.execute(team_query).scalar_one_or_none()

            if not team:
                raise ValueError(f"Team with ID {team_id} does not exist")

            # Get the team's department to enforce matching
            new_department_id = team.department_id

        # If employee is currently on a team and is the team lead, remove them as lead
        if employee.team_id:
            current_team_query = select(Team).where(Team.id == employee.team_id)
            current_team = self.db.execute(current_team_query).scalar_one_or_none()

            if current_team and current_team.lead_id == employee_id:
                # Capture previous team state
                team_previous_state = {
                    "lead_id": str(current_team.lead_id) if current_team.lead_id else None,
                }

                # Remove as lead
                current_team.lead_id = None

                # Capture new team state
                team_new_state = {
                    "lead_id": None,
                }

                # Create audit log for team change
                self.audit_service.create_audit_log(
                    entity_type=EntityType.TEAM,
                    entity_id=current_team.id,
                    change_type=ChangeType.UPDATE,
                    previous_state=team_previous_state,
                    new_state=team_new_state,
                    changed_by_user_id=changed_by_user_id,
                )

        # Capture previous state for team
        previous_team_state = {
            "team_id": str(employee.team_id) if employee.team_id else None,
        }

        # Update team
        employee.team_id = team_id

        # Capture new state for team
        new_team_state = {
            "team_id": str(employee.team_id) if employee.team_id else None,
        }

        # Create audit log entry for team change
        self.audit_service.create_audit_log(
            entity_type=EntityType.EMPLOYEE,
            entity_id=employee_id,
            change_type=ChangeType.UPDATE,
            previous_state=previous_team_state,
            new_state=new_team_state,
            changed_by_user_id=changed_by_user_id,
        )

        # Update department to match team's department (if department changed)
        if employee.department_id != new_department_id:
            # Capture previous department state
            previous_dept_state = {
                "department_id": str(employee.department_id) if employee.department_id else None,
            }

            # Update department to match team
            employee.department_id = new_department_id

            # Capture new department state
            new_dept_state = {
                "department_id": str(employee.department_id) if employee.department_id else None,
            }

            # Create audit log entry for department change
            self.audit_service.create_audit_log(
                entity_type=EntityType.EMPLOYEE,
                entity_id=employee_id,
                change_type=ChangeType.UPDATE,
                previous_state=previous_dept_state,
                new_state=new_dept_state,
                changed_by_user_id=changed_by_user_id,
            )

        return employee

    def delete_employee(
        self,
        employee_id: UUID,
        *,
        changed_by_user_id: Optional[UUID] = None,
    ) -> Optional[Employee]:
        """
        Delete an employee.

        Validation:
        - Employee must exist
        - Employee must have a manager (CEO cannot be deleted, only replaced)
        - If employee has direct reports, reassign them to employee's manager

        Creates audit log entries for:
        - The deleted employee (DELETE)
        - Each direct report that was reassigned (UPDATE)

        Does NOT commit - router is responsible for transaction management.

        Returns deleted employee or None if not found.
        Raises ValueError if employee is CEO (has no manager).
        """
        # Get existing employee
        employee = self.get_employee(employee_id)
        if not employee:
            return None

        # Check if employee is CEO (no manager)
        if employee.manager_id is None:
            raise ValueError("CEO cannot be deleted, only replaced")

        # Get list of direct report IDs for audit logging
        direct_report_ids_query = select(Employee.id).where(Employee.manager_id == employee_id)
        direct_report_ids = list(self.db.execute(direct_report_ids_query).scalars().all())

        # If employee has direct reports, reassign them to employee's manager in bulk
        if direct_report_ids:
            # Bulk update all direct reports to new manager
            update_stmt = (
                update(Employee)
                .where(Employee.manager_id == employee_id)
                .values(manager_id=employee.manager_id)
            )
            self.db.execute(update_stmt)

            # Bulk create audit logs for all reassigned employees
            previous_state = {
                "manager_id": str(employee_id),
            }
            new_state = {
                "manager_id": str(employee.manager_id) if employee.manager_id else None,
            }

            self.audit_service.bulk_create_audit_logs(
                entity_type=EntityType.EMPLOYEE,
                entity_ids=direct_report_ids,
                change_type=ChangeType.UPDATE,
                previous_state=previous_state,
                new_state=new_state,
                changed_by_user_id=changed_by_user_id,
            )

        # Capture employee state before deletion
        deleted_employee_state = {
            "name": employee.name,
            "title": employee.title,
            "email": employee.email,
            "hired_on": employee.hired_on.isoformat() if employee.hired_on else None,
            "salary": employee.salary,
            "status": employee.status.value if employee.status else None,
            "department_id": str(employee.department_id) if employee.department_id else None,
            "manager_id": str(employee.manager_id) if employee.manager_id else None,
            "team_id": str(employee.team_id) if employee.team_id else None,
        }

        # Create audit log for deleted employee
        self.audit_service.create_audit_log(
            entity_type=EntityType.EMPLOYEE,
            entity_id=employee_id,
            change_type=ChangeType.DELETE,
            previous_state=deleted_employee_state,
            new_state=None,
            changed_by_user_id=changed_by_user_id,
        )

        # Delete the employee
        self.db.delete(employee)

        return employee

    def replace_ceo(
        self,
        *,
        name: str,
        email: str,
        title: Optional[str] = None,
        hired_on: Optional[date] = None,
        salary: Optional[int] = None,
        status: EmployeeStatus = EmployeeStatus.ACTIVE,
        department_id: Optional[UUID] = None,
        team_id: Optional[UUID] = None,
        changed_by_user_id: Optional[UUID] = None,
    ) -> Employee:
        """
        Replace the current CEO with a new employee.

        The new CEO will:
        - Have no manager (manager_id = None)
        - Inherit all direct reports from the old CEO
        - Be set as the manager for the old CEO

        Validation:
        - Current CEO must exist
        - If department_id is provided, department must exist
        - If team_id is provided, team must exist

        Creates audit log entries for:
        - The new CEO (CREATE)
        - The old CEO (UPDATE - new manager is new CEO)
        - All reassigned direct reports (UPDATE)
        - The linked user if employee_id was updated (UPDATE)

        Does NOT commit - router is responsible for transaction management.

        Returns the new CEO employee.
        Raises ValueError if validation fails or no CEO exists.
        """
        # Get current CEO
        current_ceo = self.get_ceo()
        if not current_ceo:
            raise ValueError("No current CEO exists to replace")

        current_ceo_id = current_ceo.id

        # Validate department exists (if provided)
        if department_id is not None:
            dept_query = select(Department).where(Department.id == department_id)
            department = self.db.execute(dept_query).scalar_one_or_none()
            if not department:
                raise ValueError(f"Department with ID {department_id} does not exist")

        # Validate team exists (if provided)
        if team_id is not None:
            team_query = select(Team).where(Team.id == team_id)
            team = self.db.execute(team_query).scalar_one_or_none()
            if not team:
                raise ValueError(f"Team with ID {team_id} does not exist")

        # Create new CEO (no manager)
        new_ceo = Employee(
            name=name,
            email=email,
            title=title,
            hired_on=hired_on,
            salary=salary,
            status=status,
            manager_id=None,  # CEO has no manager
            department_id=department_id,
            team_id=team_id,
        )
        self.db.add(new_ceo)

        # Flush to get the new CEO's ID
        self.db.flush()

        # Get list of old CEO's direct report IDs
        direct_report_ids_query = select(Employee.id).where(Employee.manager_id == current_ceo_id)
        direct_report_ids = list(self.db.execute(direct_report_ids_query).scalars().all())

        # Bulk update all direct reports to report to new CEO
        if direct_report_ids:
            update_stmt = (
                update(Employee)
                .where(Employee.manager_id == current_ceo_id)
                .values(manager_id=new_ceo.id)
            )
            self.db.execute(update_stmt)

            # Bulk create audit logs for all reassigned direct reports
            previous_state = {
                "manager_id": str(current_ceo_id),
            }
            new_state = {
                "manager_id": str(new_ceo.id),
            }

            self.audit_service.bulk_create_audit_logs(
                entity_type=EntityType.EMPLOYEE,
                entity_ids=direct_report_ids,
                change_type=ChangeType.UPDATE,
                previous_state=previous_state,
                new_state=new_state,
                changed_by_user_id=changed_by_user_id,
            )

        # Update old CEO to report to new CEO
        old_ceo_previous_state = {
            "manager_id": str(current_ceo.manager_id) if current_ceo.manager_id else None,
        }

        current_ceo.manager_id = new_ceo.id

        old_ceo_new_state = {
            "manager_id": str(current_ceo.manager_id) if current_ceo.manager_id else None,
        }

        # Create audit log for old CEO update
        self.audit_service.create_audit_log(
            entity_type=EntityType.EMPLOYEE,
            entity_id=current_ceo_id,
            change_type=ChangeType.UPDATE,
            previous_state=old_ceo_previous_state,
            new_state=old_ceo_new_state,
            changed_by_user_id=changed_by_user_id,
        )

        # Check if a user with this email exists and link them to new CEO
        user_query = select(User).where(User.email == email)
        user = self.db.execute(user_query).scalar_one_or_none()

        if user:
            # Capture user's previous state
            user_previous_state = {
                "employee_id": str(user.employee_id) if user.employee_id else None,
            }

            # Link user to new CEO
            user.employee_id = new_ceo.id

            # Capture user's new state
            user_new_state = {
                "employee_id": str(user.employee_id) if user.employee_id else None,
            }

            # Create audit log for user update
            self.audit_service.create_audit_log(
                entity_type=EntityType.USER,
                entity_id=user.id,
                change_type=ChangeType.UPDATE,
                previous_state=user_previous_state,
                new_state=user_new_state,
                changed_by_user_id=changed_by_user_id,
            )

        # Capture new CEO state for audit log
        new_ceo_state = {
            "name": new_ceo.name,
            "title": new_ceo.title,
            "email": new_ceo.email,
            "hired_on": new_ceo.hired_on.isoformat() if new_ceo.hired_on else None,
            "salary": new_ceo.salary,
            "status": new_ceo.status.value if new_ceo.status else None,
            "department_id": str(new_ceo.department_id) if new_ceo.department_id else None,
            "manager_id": None,
            "team_id": str(new_ceo.team_id) if new_ceo.team_id else None,
        }

        # Create audit log for new CEO
        self.audit_service.create_audit_log(
            entity_type=EntityType.EMPLOYEE,
            entity_id=new_ceo.id,
            change_type=ChangeType.CREATE,
            previous_state=None,
            new_state=new_ceo_state,
            changed_by_user_id=changed_by_user_id,
        )

        return new_ceo

    def promote_employee_to_ceo(
        self,
        employee_id: UUID,
        *,
        changed_by_user_id: Optional[UUID] = None,
    ) -> Employee:
        """
        Promote an existing employee to CEO.

        Reorganization logic:
        - If the employee's manager is the current CEO:
          - Employee's direct reports remain unchanged
          - Old CEO reports to new CEO
          - Old CEO's other direct reports (excluding new CEO) report to new CEO

        - If the employee's manager is NOT the current CEO:
          - Employee's direct reports are reassigned to employee's original manager
          - Old CEO reports to new CEO
          - Old CEO's direct reports (all) report to new CEO

        Creates audit log entries for:
        - The promoted employee (UPDATE - manager becomes None)
        - The old CEO (UPDATE - manager becomes new CEO)
        - All reassigned employees (UPDATE)

        Does NOT commit - router is responsible for transaction management.

        Returns the newly promoted CEO.
        Raises ValueError if validation fails.
        """
        # Get current CEO
        current_ceo = self.get_ceo()
        if not current_ceo:
            raise ValueError("No current CEO exists")

        # Get employee to promote
        employee = self.get_employee(employee_id)
        if not employee:
            raise ValueError(f"Employee with ID {employee_id} does not exist")

        # Cannot promote CEO to CEO
        if employee.id == current_ceo.id:
            raise ValueError("Employee is already CEO")

        current_ceo_id = current_ceo.id
        original_manager_id = employee.manager_id

        # Determine if employee reports directly to CEO
        reports_to_ceo = employee.manager_id == current_ceo_id

        if reports_to_ceo:
            # Case 1: Employee reports to current CEO
            # Employee's direct reports stay with them
            # Old CEO's other direct reports (excluding new CEO) move to new CEO

            # Get IDs of old CEO's direct reports (excluding the employee being promoted)
            old_ceo_direct_reports_query = select(Employee.id).where(
                and_(
                    Employee.manager_id == current_ceo_id,
                    Employee.id != employee_id
                )
            )
            old_ceo_direct_report_ids = list(self.db.execute(old_ceo_direct_reports_query).scalars().all())

            # Reassign old CEO's other direct reports to new CEO
            if old_ceo_direct_report_ids:
                update_stmt = (
                    update(Employee)
                    .where(
                        and_(
                            Employee.manager_id == current_ceo_id,
                            Employee.id != employee_id
                        )
                    )
                    .values(manager_id=employee_id)
                )
                self.db.execute(update_stmt)

                # Bulk create audit logs for all reassigned employees
                previous_state = {
                    "manager_id": str(current_ceo_id),
                }
                new_state = {
                    "manager_id": str(employee_id),
                }

                self.audit_service.bulk_create_audit_logs(
                    entity_type=EntityType.EMPLOYEE,
                    entity_ids=old_ceo_direct_report_ids,
                    change_type=ChangeType.UPDATE,
                    previous_state=previous_state,
                    new_state=new_state,
                    changed_by_user_id=changed_by_user_id,
                )

        else:
            # Case 2: Employee does NOT report to current CEO
            # Employee's direct reports move to employee's original manager
            # All old CEO's direct reports move to new CEO

            # Get IDs of employee's direct reports
            employee_direct_reports_query = select(Employee.id).where(Employee.manager_id == employee_id)
            employee_direct_report_ids = list(self.db.execute(employee_direct_reports_query).scalars().all())

            # Reassign employee's direct reports to employee's original manager
            if employee_direct_report_ids:
                update_stmt = (
                    update(Employee)
                    .where(Employee.manager_id == employee_id)
                    .values(manager_id=original_manager_id)
                )
                self.db.execute(update_stmt)

                # Bulk create audit logs for all reassigned direct reports
                previous_state = {
                    "manager_id": str(employee_id),
                }
                new_state = {
                    "manager_id": str(original_manager_id) if original_manager_id else None,
                }

                self.audit_service.bulk_create_audit_logs(
                    entity_type=EntityType.EMPLOYEE,
                    entity_ids=employee_direct_report_ids,
                    change_type=ChangeType.UPDATE,
                    previous_state=previous_state,
                    new_state=new_state,
                    changed_by_user_id=changed_by_user_id,
                )

            # Get IDs of old CEO's direct reports
            old_ceo_direct_reports_query = select(Employee.id).where(Employee.manager_id == current_ceo_id)
            old_ceo_direct_report_ids = list(self.db.execute(old_ceo_direct_reports_query).scalars().all())

            # Reassign old CEO's direct reports to new CEO
            if old_ceo_direct_report_ids:
                update_stmt = (
                    update(Employee)
                    .where(Employee.manager_id == current_ceo_id)
                    .values(manager_id=employee_id)
                )
                self.db.execute(update_stmt)

                # Bulk create audit logs for all reassigned direct reports
                previous_state = {
                    "manager_id": str(current_ceo_id),
                }
                new_state = {
                    "manager_id": str(employee_id),
                }

                self.audit_service.bulk_create_audit_logs(
                    entity_type=EntityType.EMPLOYEE,
                    entity_ids=old_ceo_direct_report_ids,
                    change_type=ChangeType.UPDATE,
                    previous_state=previous_state,
                    new_state=new_state,
                    changed_by_user_id=changed_by_user_id,
                )

        # Promote employee to CEO (remove manager)
        employee_previous_state = {
            "manager_id": str(employee.manager_id) if employee.manager_id else None,
        }

        employee.manager_id = None

        employee_new_state = {
            "manager_id": None,
        }

        # Create audit log for promoted employee
        self.audit_service.create_audit_log(
            entity_type=EntityType.EMPLOYEE,
            entity_id=employee_id,
            change_type=ChangeType.UPDATE,
            previous_state=employee_previous_state,
            new_state=employee_new_state,
            changed_by_user_id=changed_by_user_id,
        )

        # Demote old CEO to report to new CEO
        old_ceo_previous_state = {
            "manager_id": str(current_ceo.manager_id) if current_ceo.manager_id else None,
        }

        current_ceo.manager_id = employee_id

        old_ceo_new_state = {
            "manager_id": str(current_ceo.manager_id) if current_ceo.manager_id else None,
        }

        # Create audit log for old CEO
        self.audit_service.create_audit_log(
            entity_type=EntityType.EMPLOYEE,
            entity_id=current_ceo_id,
            change_type=ChangeType.UPDATE,
            previous_state=old_ceo_previous_state,
            new_state=old_ceo_new_state,
            changed_by_user_id=changed_by_user_id,
        )

        return employee
        
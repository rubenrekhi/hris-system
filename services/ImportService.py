"""
ImportService.py
----------------
Business logic for bulk CSV import operations.

Uses Kahn's algorithm for topological sorting to handle manager
dependencies and detect circular references.
"""

from __future__ import annotations
from typing import List, Dict, Any, Tuple, Optional
from uuid import UUID
from collections import deque
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import ValidationError

from models.EmployeeModel import Employee, EmployeeStatus
from models.DepartmentModel import Department
from models.TeamModel import Team
from models.UserModel import User
from models.AuditLogModel import EntityType, ChangeType
from services.AuditLogService import AuditLogService
from services.EmployeeService import EmployeeService
from schemas.ImportSchemas import EmployeeCSVRow, BulkImportResult, BulkImportError


class ImportService:
    """Service for handling bulk import operations."""

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditLogService(db)
        self.employee_service = EmployeeService(db)

    def import_employees(
        self,
        csv_data: List[Dict[str, Any]],
        *,
        changed_by_user_id: Optional[UUID] = None,
    ) -> BulkImportResult:
        """
        Bulk import employees from CSV data.

        Uses Kahn's algorithm to:
        1. Detect circular dependencies within CSV
        2. Determine correct insertion order (topological sort)
        3. Handle multiple disconnected subtrees

        Validation Strategy:
        - All-or-nothing: If any validation fails, no employees are imported
        - Pre-loads reference data for O(1) lookups
        - Returns detailed errors for all failed rows

        Does NOT commit - router is responsible for transaction management.

        Args:
            csv_data: List of dicts with employee data from CSV
            changed_by_user_id: User performing the import

        Returns:
            BulkImportResult with success/failure details

        Raises:
            No exceptions - all errors captured in result
        """
        result = BulkImportResult(total_rows=len(csv_data))

        # Phase 1: Pre-load all reference data
        reference_data = self._preload_reference_data()

        # Phase 2: Validate and parse all CSV rows
        validated_rows, validation_errors = self._validate_csv_rows(
            csv_data, reference_data
        )

        if validation_errors:
            result.failed_rows = validation_errors
            return result

        # Phase 3: Topological sort using Kahn's algorithm
        try:
            insertion_order = self._topological_sort(validated_rows)
        except ValueError as e:
            # Circular dependency detected
            result.failed_rows = [BulkImportError(
                row_number=0,
                email=None,
                error_message=str(e),
                row_data={}
            )]
            return result

        # Phase 4: Bulk insert employees in correct order
        try:
            created_employees = self._bulk_insert_employees(
                insertion_order,
                reference_data,
                changed_by_user_id,
            )
            result.successful_imports = len(created_employees)
            result.created_employee_ids = [emp.id for emp in created_employees]

        except Exception as e:
            result.failed_rows = [BulkImportError(
                row_number=0,
                email=None,
                error_message=f"Bulk insert failed: {str(e)}",
                row_data={}
            )]

        return result

    def _preload_reference_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Pre-load all reference data for O(1) lookups.

        Returns dict with:
        - departments: {name: department_obj}
        - teams: {name: team_obj}
        - employees_by_email: {email: employee_id}
        """
        # Load departments
        dept_query = select(Department)
        departments = {
            dept.name: dept
            for dept in self.db.execute(dept_query).scalars().all()
        }

        # Load teams
        team_query = select(Team)
        teams = {
            team.name: team
            for team in self.db.execute(team_query).scalars().all()
        }

        # Load existing employees (for manager lookup)
        emp_query = select(Employee.id, Employee.email)
        employees_by_email = {
            emp.email: emp.id
            for emp in self.db.execute(emp_query).all()
        }

        return {
            "departments": departments,
            "teams": teams,
            "employees_by_email": employees_by_email,
        }

    def _validate_csv_rows(
        self,
        csv_data: List[Dict[str, Any]],
        reference_data: Dict[str, Dict[str, Any]],
    ) -> Tuple[List[EmployeeCSVRow], List[BulkImportError]]:
        """
        Validate all CSV rows and collect errors.

        Two-pass validation:
        1. Parse all rows and collect emails (to detect duplicates and build complete email set)
        2. Validate references (managers, departments, teams)

        This allows circular dependencies to pass validation and be caught by topological sort.

        Returns:
            (validated_rows, errors)
        """
        errors = []

        # Check if this is the first import (no employees exist)
        is_first_import = len(reference_data["employees_by_email"]) == 0

        # Pass 1: Parse and collect all emails
        parsed_rows = []  # List of (row_num, row_data, validated_row)
        emails_in_csv = set()

        for row_num, row_data in enumerate(csv_data, start=1):
            try:
                # Pydantic validation
                validated_row = EmployeeCSVRow(**row_data)

                # Check duplicate email within CSV
                if validated_row.email in emails_in_csv:
                    errors.append(BulkImportError(
                        row_number=row_num,
                        email=validated_row.email,
                        error_message=f"Duplicate email in CSV: {validated_row.email}",
                        row_data=row_data,
                    ))
                    continue

                # Check duplicate email in database
                if validated_row.email in reference_data["employees_by_email"]:
                    errors.append(BulkImportError(
                        row_number=row_num,
                        email=validated_row.email,
                        error_message=f"Email already exists in database: {validated_row.email}",
                        row_data=row_data,
                    ))
                    continue

                emails_in_csv.add(validated_row.email)
                parsed_rows.append((row_num, row_data, validated_row))

            except ValidationError as e:
                errors.append(BulkImportError(
                    row_number=row_num,
                    email=row_data.get("email"),
                    error_message=f"Validation error: {str(e)}",
                    row_data=row_data,
                ))

        # Pass 2: Check for multiple root nodes (employees with no manager)
        employees_without_manager = [
            (row_num, row_data, validated_row)
            for row_num, row_data, validated_row in parsed_rows
            if not validated_row.manager_email
        ]

        if len(employees_without_manager) > 1:
            # Multiple root nodes not allowed
            for row_num, row_data, validated_row in employees_without_manager:
                errors.append(BulkImportError(
                    row_number=row_num,
                    email=validated_row.email,
                    error_message="Only one employee can have no manager (the CEO).",
                    row_data=row_data,
                ))
            return [], errors  # Return early with errors
        elif len(employees_without_manager) == 1:
            # One employee with no manager
            if not is_first_import:
                # DB already has employees - can't add another root
                row_num, row_data, validated_row = employees_without_manager[0]
                errors.append(BulkImportError(
                    row_number=row_num,
                    email=validated_row.email,
                    error_message="manager_email is required. CEO already exists in the system.",
                    row_data=row_data,
                ))
                return [], errors  # Return early with error

        # Pass 3: Validate references
        validated_rows = []

        for row_num, row_data, validated_row in parsed_rows:
            # Check department exists
            if validated_row.department_name:
                if validated_row.department_name not in reference_data["departments"]:
                    errors.append(BulkImportError(
                        row_number=row_num,
                        email=validated_row.email,
                        error_message=f"Department not found: {validated_row.department_name}",
                        row_data=row_data,
                    ))
                    continue

            # Check team exists
            if validated_row.team_name:
                if validated_row.team_name not in reference_data["teams"]:
                    errors.append(BulkImportError(
                        row_number=row_num,
                        email=validated_row.email,
                        error_message=f"Team not found: {validated_row.team_name}",
                        row_data=row_data,
                    ))
                    continue

            # Check manager email exists (in DB or CSV) if specified
            if validated_row.manager_email:
                manager_in_db = validated_row.manager_email in reference_data["employees_by_email"]
                manager_in_csv = validated_row.manager_email in emails_in_csv

                if not manager_in_db and not manager_in_csv:
                    errors.append(BulkImportError(
                        row_number=row_num,
                        email=validated_row.email,
                        error_message=f"Manager email not found: {validated_row.manager_email}",
                        row_data=row_data,
                    ))
                    continue
            # Note: Employees without manager_email are validated in Pass 2

            validated_rows.append(validated_row)

        return validated_rows, errors

    def _topological_sort(
        self,
        validated_rows: List[EmployeeCSVRow],
    ) -> List[List[EmployeeCSVRow]]:
        """
        Perform topological sort using Kahn's algorithm.

        Only considers dependencies WITHIN the CSV (employees whose
        managers are also in the CSV). Employees with managers in the
        database are treated as having no prerequisites.

        Returns:
            List of lists, where each sublist is a "wave" of employees
            that can be inserted together (in parallel if desired).

        Raises:
            ValueError: If circular dependency detected
        """
        # Build graph and in-degree map
        graph = {}  # email -> EmployeeCSVRow
        in_degree = {}  # email -> int (number of dependencies)

        for row in validated_rows:
            graph[row.email] = row
            in_degree[row.email] = 0

        # Calculate in-degrees (only for CSV-to-CSV edges)
        for row in validated_rows:
            if row.manager_email and row.manager_email in graph:
                # This employee depends on their manager (who is also in CSV)
                # Manager must be inserted before this employee
                in_degree[row.email] += 1

        # Find starting nodes (in_degree = 0)
        # These are employees whose managers are in DB or have no manager
        queue = deque([email for email, degree in in_degree.items() if degree == 0])

        # Process in waves (for batch insertion)
        insertion_order = []
        processed_count = 0

        while queue:
            # Process all employees at current level
            current_wave = []

            for _ in range(len(queue)):
                email = queue.popleft()
                current_wave.append(graph[email])
                processed_count += 1

                # Find employees who report to this person (in CSV)
                for row in validated_rows:
                    if row.manager_email == email:
                        in_degree[row.email] -= 1
                        if in_degree[row.email] == 0:
                            queue.append(row.email)

            insertion_order.append(current_wave)

        # Check if we processed all employees
        if processed_count < len(validated_rows):
            # Some employees still have in_degree > 0 → circular dependency
            unprocessed = [email for email, degree in in_degree.items() if degree > 0]
            raise ValueError(
                f"Circular dependency detected among employees: {', '.join(unprocessed)}"
            )

        return insertion_order

    def _bulk_insert_employees(
        self,
        insertion_order: List[List[EmployeeCSVRow]],
        reference_data: Dict[str, Dict[str, Any]],
        changed_by_user_id: Optional[UUID],
    ) -> List[Employee]:
        """
        Insert employees in waves according to topological order.

        Each wave can be inserted together since they have no inter-dependencies.

        Returns:
            List of all created Employee objects
        """
        all_created_employees = []
        csv_email_to_id = {}  # Track newly created employee IDs

        for wave in insertion_order:
            wave_employees = []

            for row in wave:
                # Resolve foreign keys
                department_id = None
                if row.department_name:
                    department_id = reference_data["departments"][row.department_name].id

                team_id = None
                if row.team_name:
                    team_id = reference_data["teams"][row.team_name].id

                manager_id = None
                if row.manager_email:
                    # Check if manager is in DB
                    if row.manager_email in reference_data["employees_by_email"]:
                        manager_id = reference_data["employees_by_email"][row.manager_email]
                    # Check if manager is in CSV (already created in earlier wave)
                    elif row.manager_email in csv_email_to_id:
                        manager_id = csv_email_to_id[row.manager_email]

                # Create employee object
                employee = Employee(
                    name=row.name,
                    email=row.email,
                    title=row.title,
                    hired_on=row.hired_on,
                    salary=row.salary,
                    status=row.status,
                    manager_id=manager_id,
                    department_id=department_id,
                    team_id=team_id,
                )
                wave_employees.append(employee)

            # Bulk add all employees in this wave
            self.db.add_all(wave_employees)

            # Flush to get IDs for next wave's manager resolution
            self.db.flush()

            # Track created employee IDs
            for employee in wave_employees:
                csv_email_to_id[employee.email] = employee.id
                all_created_employees.append(employee)

        # Bulk create audit logs for all created employees
        employee_ids = [emp.id for emp in all_created_employees]
        self.audit_service.bulk_create_audit_logs(
            entity_type=EntityType.EMPLOYEE,
            entity_ids=employee_ids,
            change_type=ChangeType.CREATE,
            previous_state=None,
            new_state={"bulk_import": True},
            changed_by_user_id=changed_by_user_id,
        )

        # Link users by email (bulk)
        self._bulk_link_users(all_created_employees, changed_by_user_id)

        return all_created_employees

    def _bulk_link_users(
        self,
        employees: List[Employee],
        changed_by_user_id: Optional[UUID],
    ) -> None:
        """
        Link users to employees by matching email addresses.

        Only links users whose employee_id is currently None (not already linked).
        This ensures audit log accuracy - we only link unlinked users.

        Creates audit logs for any users that were linked.
        """
        # Get all user emails that match employee emails
        employee_emails = [emp.email for emp in employees]
        user_query = select(User).where(User.email.in_(employee_emails))
        users = self.db.execute(user_query).scalars().all()

        # Create email -> employee_id mapping
        email_to_emp_id = {emp.email: emp.id for emp in employees}

        # Link users and track for audit logs
        # Only link users whose employee_id is currently None
        linked_user_ids = []

        for user in users:
            if user.email in email_to_emp_id and user.employee_id is None:
                user.employee_id = email_to_emp_id[user.email]
                linked_user_ids.append(user.id)

        # Bulk create audit logs for linked users
        if linked_user_ids:
            self.audit_service.bulk_create_audit_logs(
                entity_type=EntityType.USER,
                entity_ids=linked_user_ids,
                change_type=ChangeType.UPDATE,
                previous_state={"employee_id": None},
                new_state={"employee_id": "linked"},
                changed_by_user_id=changed_by_user_id,
            )

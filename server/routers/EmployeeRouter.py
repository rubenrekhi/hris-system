"""
EmployeeRouter.py
-----------------
API routes for employee records and information management.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from services.EmployeeService import EmployeeService
from schemas.EmployeeSchemas import (
    EmployeeListQuery,
    EmployeeListResponse,
    EmployeeListItem,
    EmployeeDetail,
    EmployeeCreate,
    EmployeeReplaceCEO,
    EmployeeUpdate,
    EmployeeDepartmentAssign,
    EmployeeTeamAssign,
    EmployeeManagerAssign,
)
from core.dependencies import get_employee_service, require_roles, get_current_user, get_db, AnonymousUser
from sqlalchemy.orm import Session

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("", response_model=EmployeeListResponse)
def list_employees(
    query: EmployeeListQuery = Depends(),
    user = Depends(require_roles("member")),
    employee_service: EmployeeService = Depends(get_employee_service),
):
    """
    List employees with optional filters and search.

    Returns employees ordered alphabetically by name.

    Filters:
    - team_id: Filter by team
    - department_id: Filter by department
    - status: Filter by employee status (ACTIVE, ON_LEAVE)
    - min_salary/max_salary: Filter by salary range

    Search:
    - name: Case-insensitive search in employee names
    - email: Case-insensitive search in employee emails

    Pagination:
    - limit: Number of results per page (1-100, default 25)
    - offset: Number of results to skip (default 0)
    """
    employees, total = employee_service.list_employees(
        team_id=query.team_id,
        department_id=query.department_id,
        status=query.status,
        min_salary=query.min_salary,
        max_salary=query.max_salary,
        name=query.name,
        email=query.email,
        limit=query.limit,
        offset=query.offset,
    )

    return EmployeeListResponse(
        items=[EmployeeListItem.model_validate(emp) for emp in employees],
        total=total,
        limit=query.limit,
        offset=query.offset,
    )


@router.get("/unassigned", response_model=EmployeeListResponse)
def list_unassigned_employees(
    limit: int = Query(25, ge=1, le=100, description="Number of results per page"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    user = Depends(require_roles("member")),
    employee_service: EmployeeService = Depends(get_employee_service),
):
    """
    List unassigned employees.

    Returns employees that are:
    - Not assigned to any department (department_id IS NULL)
    - Not assigned to any team (team_id IS NULL)

    Employees are ordered alphabetically by name.

    Pagination:
    - limit: Number of results per page (1-100, default 25)
    - offset: Number of results to skip (default 0)
    """
    employees, total = employee_service.list_unassigned_employees(
        limit=limit,
        offset=offset,
    )

    return EmployeeListResponse(
        items=[EmployeeListItem.model_validate(emp) for emp in employees],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=EmployeeDetail, status_code=201)
def create_employee(
    create_data: EmployeeCreate,
    user = Depends(require_roles("hr")),
    employee_service: EmployeeService = Depends(get_employee_service),
    db: Session = Depends(get_db),
):
    """
    Create a new employee.

    Requires HR role.

    Validation:
    - manager_id is required unless this is the first employee
    - If manager_id is provided, manager must exist
    - If department_id is provided, department must exist
    - If team_id is provided, team must exist
    - If a user with matching email exists, links employee to user

    Creates audit logs for:
    - The new employee (CREATE)
    - The linked user if employee_id was updated (UPDATE)
    """
    try:
        employee = employee_service.create_employee(
            name=create_data.name,
            email=create_data.email,
            title=create_data.title,
            hired_on=create_data.hired_on,
            salary=create_data.salary,
            status=create_data.status,
            manager_id=create_data.manager_id,
            department_id=create_data.department_id,
            team_id=create_data.team_id,
            changed_by_user_id=user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Commit the transaction (including audit logs)
    try:
        db.commit()
        db.refresh(employee)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create employee: {str(e)}")

    return EmployeeDetail.model_validate(employee)


@router.get("/ceo", response_model=EmployeeDetail)
def get_ceo(
    user = Depends(require_roles("member")),
    employee_service: EmployeeService = Depends(get_employee_service),
):
    """
    Get the CEO (employee with no manager).

    Returns the CEO employee details.
    """
    employee = employee_service.get_ceo()

    if not employee:
        raise HTTPException(status_code=404, detail="CEO not found")

    return EmployeeDetail.model_validate(employee)


@router.post("/ceo/replace", response_model=EmployeeDetail, status_code=201)
def replace_ceo(
    replace_data: EmployeeReplaceCEO,
    user = Depends(require_roles("admin")),
    employee_service: EmployeeService = Depends(get_employee_service),
    db: Session = Depends(get_db),
):
    """
    Replace the current CEO with a new employee.

    Requires HR role.

    The new CEO will:
    - Have no manager (automatically set)
    - Inherit all direct reports from the old CEO
    - Become the manager of the old CEO

    Validation:
    - Current CEO must exist
    - If department_id is provided, department must exist
    - If team_id is provided, team must exist
    - If a user with matching email exists, links employee to user

    Creates audit logs for:
    - The new CEO (CREATE)
    - The old CEO (UPDATE - manager changed to new CEO)
    - All reassigned direct reports (UPDATE)
    - The linked user if employee_id was updated (UPDATE)
    """
    try:
        new_ceo = employee_service.replace_ceo(
            name=replace_data.name,
            email=replace_data.email,
            title=replace_data.title,
            hired_on=replace_data.hired_on,
            salary=replace_data.salary,
            status=replace_data.status,
            department_id=replace_data.department_id,
            team_id=replace_data.team_id,
            changed_by_user_id=user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Commit the transaction (including all audit logs)
    try:
        db.commit()
        db.refresh(new_ceo)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to replace CEO: {str(e)}")

    return EmployeeDetail.model_validate(new_ceo)


@router.post("/ceo/promote/{employee_id}", response_model=EmployeeDetail, status_code=200)
def promote_employee_to_ceo(
    employee_id: UUID,
    user = Depends(require_roles("admin")),
    employee_service: EmployeeService = Depends(get_employee_service),
    db: Session = Depends(get_db),
):
    """
    Promote an existing employee to CEO.

    Requires admin role.

    Reorganization logic depends on the employee's current reporting structure:

    If the employee reports to the current CEO:
    - Employee's direct reports remain unchanged
    - Old CEO's other direct reports (excluding promoted employee) report to new CEO
    - Old CEO reports to new CEO

    If the employee does NOT report to the current CEO:
    - Employee's direct reports are reassigned to employee's original manager
    - Old CEO's direct reports (all) report to new CEO
    - Old CEO reports to new CEO

    Validation:
    - Employee must exist
    - Employee cannot already be CEO
    - Current CEO must exist

    Creates audit logs for:
    - The promoted employee (UPDATE - manager changed to None)
    - The demoted CEO (UPDATE - manager changed to new CEO)
    - All reassigned direct reports (UPDATE)
    """
    try:
        new_ceo = employee_service.promote_employee_to_ceo(
            employee_id,
            changed_by_user_id=user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Commit the transaction (including all audit logs)
    try:
        db.commit()
        db.refresh(new_ceo)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to promote employee to CEO: {str(e)}")

    return EmployeeDetail.model_validate(new_ceo)


@router.get("/{employee_id}", response_model=EmployeeDetail)
def get_employee(
    employee_id: UUID,
    user = Depends(require_roles("member")),
    employee_service: EmployeeService = Depends(get_employee_service),
):
    """
    Get a single employee by ID.

    Returns all employee fields including:
    - Basic info: name, title, email
    - Employment: hired_on, salary, status
    - Relationships: department_id, manager_id, team_id
    - Metadata: created_at, updated_at
    - Related names: department_name, team_name, manager_name
    """
    employee = employee_service.get_employee_with_details(employee_id)

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    return EmployeeDetail.model_validate(employee)


@router.get("/{employee_id}/direct-reports", response_model=list[EmployeeListItem])
def get_direct_reports(
    employee_id: UUID,
    user = Depends(require_roles("member")),
    employee_service: EmployeeService = Depends(get_employee_service),
):
    """
    Get all direct reports for a specific employee.

    Returns a list of employees who report directly to the specified employee.
    Results are ordered alphabetically by name.
    """
    direct_reports = employee_service.get_direct_reports(employee_id)

    return [EmployeeListItem.model_validate(emp) for emp in direct_reports]


@router.patch("/{employee_id}", response_model=EmployeeDetail)
def update_employee(
    employee_id: UUID,
    update_data: EmployeeUpdate,
    user = Depends(require_roles("hr")),
    employee_service: EmployeeService = Depends(get_employee_service),
    db: Session = Depends(get_db),
):
    """
    Update employee fields (name, title, salary, status).

    Requires HR role.

    Updates are logged to the audit log with previous and new states.
    Only provided fields will be updated.

    Editable fields:
    - name: Employee name
    - title: Job title
    - salary: Employee salary
    - status: Employee status (ACTIVE, ON_LEAVE)
    """
    # Update employee
    employee = employee_service.update_employee(
        employee_id,
        name=update_data.name,
        title=update_data.title,
        salary=update_data.salary,
        status=update_data.status,
        changed_by_user_id=user.id,
    )

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Commit the transaction (including audit log)
    try:
        db.commit()
        db.refresh(employee)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update employee: {str(e)}")

    return EmployeeDetail.model_validate(employee)


@router.patch("/{employee_id}/department", response_model=EmployeeDetail)
def assign_department(
    employee_id: UUID,
    assign_data: EmployeeDepartmentAssign,
    user = Depends(require_roles("hr")),
    employee_service: EmployeeService = Depends(get_employee_service),
    db: Session = Depends(get_db),
):
    """
    Assign or remove a department from an employee.

    Requires HR role.

    Validation:
    - If employee is on a team, the department must match the team's department
    - If department_id is null, removes the department assignment
    - If department_id is provided, validates department exists

    Updates are logged to the audit log with previous and new states.
    """
    try:
        employee = employee_service.assign_department(
            employee_id,
            assign_data.department_id,
            changed_by_user_id=user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Commit the transaction (including audit log)
    try:
        db.commit()
        db.refresh(employee)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update department: {str(e)}")

    return EmployeeDetail.model_validate(employee)


@router.patch("/{employee_id}/team", response_model=EmployeeDetail)
def assign_team(
    employee_id: UUID,
    assign_data: EmployeeTeamAssign,
    user = Depends(require_roles("hr")),
    employee_service: EmployeeService = Depends(get_employee_service),
    db: Session = Depends(get_db),
):
    """
    Assign or remove a team from an employee.

    Requires HR role.

    Validation:
    - If team_id is not null, validates team exists
    - If employee is currently a team lead, removes them as lead before reassignment

    Updates are logged to the audit log with previous and new states.
    """
    try:
        employee = employee_service.assign_team(
            employee_id,
            assign_data.team_id,
            changed_by_user_id=user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Commit the transaction (including audit log)
    try:
        db.commit()
        db.refresh(employee)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update team: {str(e)}")

    return EmployeeDetail.model_validate(employee)


@router.patch("/{employee_id}/manager", response_model=EmployeeDetail)
def assign_manager(
    employee_id: UUID,
    assign_data: EmployeeManagerAssign,
    user = Depends(require_roles("hr")),
    employee_service: EmployeeService = Depends(get_employee_service),
    db: Session = Depends(get_db),
):
    """
    Assign a new manager to an employee.

    Requires HR role.

    Validation:
    - Employee must exist
    - New manager must exist
    - Assignment must not create a circular dependency in the org tree
    - Employee cannot become their own manager

    The system uses a recursive CTE to detect and prevent circular dependencies
    in the organizational hierarchy before allowing the assignment.

    Updates are logged to the audit log with previous and new states.
    """
    try:
        employee = employee_service.assign_manager(
            employee_id,
            assign_data.manager_id,
            changed_by_user_id=user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Commit the transaction (including audit log)
    try:
        db.commit()
        db.refresh(employee)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update manager: {str(e)}")

    return EmployeeDetail.model_validate(employee)


@router.delete("/{employee_id}", status_code=204)
def delete_employee(
    employee_id: UUID,
    user = Depends(require_roles("hr")),
    employee_service: EmployeeService = Depends(get_employee_service),
    db: Session = Depends(get_db),
):
    """
    Delete an employee.

    Requires HR role.

    Validation:
    - Employee must have a manager (CEO cannot be deleted, only replaced)
    - If employee has direct reports, they will be reassigned to the employee's manager

    All changes are logged to the audit log:
    - DELETE entry for the deleted employee
    - UPDATE entries for each reassigned direct report
    """
    try:
        employee = employee_service.delete_employee(
            employee_id,
            changed_by_user_id=user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Commit the transaction (including all audit logs)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete employee: {str(e)}")

    return None
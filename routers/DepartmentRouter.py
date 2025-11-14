"""
DepartmentRouter.py
-------------------
API routes for department management and operations.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from services.DepartmentService import DepartmentService
from schemas.DepartmentSchemas import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentDetail,
    PaginationQuery,
    TeamListResponse,
    TeamListItem,
    EmployeeListResponse,
    EmployeeListItem,
)
from core.dependencies import get_department_service, require_roles, get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/departments", tags=["departments"])


@router.post("", response_model=DepartmentDetail, status_code=201)
def create_department(
    create_data: DepartmentCreate,
    user = Depends(require_roles("hr")),
    department_service: DepartmentService = Depends(get_department_service),
    db: Session = Depends(get_db),
):
    """
    Create a new department.

    Requires HR role.

    Validation:
    - Name must be unique (enforced by database constraint)

    Creates audit log for the new department (CREATE).
    """
    try:
        department = department_service.create_department(
            name=create_data.name,
            changed_by_user_id=user.id,
        )
    except Exception as e:
        # Handle unique constraint violation
        raise HTTPException(status_code=400, detail=f"Failed to create department: {str(e)}")

    # Commit the transaction (including audit log)
    try:
        db.commit()
        db.refresh(department)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create department: {str(e)}")

    return DepartmentDetail.model_validate(department)


@router.get("/{department_id}", response_model=DepartmentDetail)
def get_department(
    department_id: UUID,
    user = Depends(require_roles("member")),
    department_service: DepartmentService = Depends(get_department_service),
):
    """
    Get a single department by ID.

    Returns all department fields including:
    - id, name
    - created_at, updated_at
    """
    department = department_service.get_department(department_id)

    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    return DepartmentDetail.model_validate(department)


@router.patch("/{department_id}", response_model=DepartmentDetail)
def update_department(
    department_id: UUID,
    update_data: DepartmentUpdate,
    user = Depends(require_roles("hr")),
    department_service: DepartmentService = Depends(get_department_service),
    db: Session = Depends(get_db),
):
    """
    Update department name.

    Requires HR role.

    Validation:
    - Name must be unique (enforced by database constraint)

    Updates are logged to the audit log with previous and new states.
    """
    department = department_service.update_department(
        department_id,
        name=update_data.name,
        changed_by_user_id=user.id,
    )

    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    # Commit the transaction (including audit log)
    try:
        db.commit()
        db.refresh(department)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update department: {str(e)}")

    return DepartmentDetail.model_validate(department)


@router.delete("/{department_id}", status_code=204)
def delete_department(
    department_id: UUID,
    user = Depends(require_roles("hr")),
    department_service: DepartmentService = Depends(get_department_service),
    db: Session = Depends(get_db),
):
    """
    Delete a department.

    Requires HR role.

    Note: Employees and teams in this department will have their
    department_id set to NULL (due to ondelete="SET NULL").

    Creates audit log for the deleted department (DELETE).
    """
    department = department_service.delete_department(
        department_id,
        changed_by_user_id=user.id,
    )

    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    # Commit the transaction (including audit log)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete department: {str(e)}")

    return None


@router.get("/{department_id}/teams", response_model=TeamListResponse)
def list_department_teams(
    department_id: UUID,
    query: PaginationQuery = Depends(),
    user = Depends(require_roles("member")),
    department_service: DepartmentService = Depends(get_department_service),
):
    """
    List all teams in a department.

    Returns teams ordered alphabetically by name.

    Pagination:
    - limit: Number of results per page (1-100, default 25)
    - offset: Number of results to skip (default 0)
    """
    teams, total = department_service.list_department_teams(
        department_id,
        limit=query.limit,
        offset=query.offset,
    )

    return TeamListResponse(
        items=[TeamListItem.model_validate(team) for team in teams],
        total=total,
        limit=query.limit,
        offset=query.offset,
    )


@router.get("/{department_id}/employees", response_model=EmployeeListResponse)
def list_department_employees(
    department_id: UUID,
    query: PaginationQuery = Depends(),
    user = Depends(require_roles("member")),
    department_service: DepartmentService = Depends(get_department_service),
):
    """
    List all employees in a department.

    Returns employees ordered alphabetically by name.

    Pagination:
    - limit: Number of results per page (1-100, default 25)
    - offset: Number of results to skip (default 0)
    """
    employees, total = department_service.list_department_employees(
        department_id,
        limit=query.limit,
        offset=query.offset,
    )

    return EmployeeListResponse(
        items=[EmployeeListItem.model_validate(emp) for emp in employees],
        total=total,
        limit=query.limit,
        offset=query.offset,
    )
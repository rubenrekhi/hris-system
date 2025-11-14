"""
TeamRouter.py
-------------
API routes for team management and operations.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from services.TeamService import TeamService
from schemas.TeamSchemas import (
    TeamListQuery,
    TeamListResponse,
    TeamListItem,
    TeamDetail,
    TeamMember,
    TeamCreate,
    TeamUpdate,
)
from core.dependencies import get_team_service, require_roles
from sqlalchemy.orm import Session
from core.dependencies import get_db

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", response_model=TeamListResponse)
def list_teams(
    query: TeamListQuery = Depends(),
    user = Depends(require_roles("member")),
    team_service: TeamService = Depends(get_team_service),
):
    """
    List teams with optional filters and search.

    Returns teams ordered alphabetically by name.

    Filters:
    - department_id: Filter by department
    - parent_team_id: Filter by parent team

    Search:
    - name: Case-insensitive search in team names

    Pagination:
    - limit: Number of results per page (1-100, default 25)
    - offset: Number of results to skip (default 0)
    """
    teams, total = team_service.list_teams(
        department_id=query.department_id,
        parent_team_id=query.parent_team_id,
        name=query.name,
        limit=query.limit,
        offset=query.offset,
    )

    return TeamListResponse(
        items=[TeamListItem.model_validate(team) for team in teams],
        total=total,
        limit=query.limit,
        offset=query.offset,
    )


@router.get("/{team_id}", response_model=TeamDetail)
def get_team(
    team_id: UUID,
    user = Depends(require_roles("member")),
    team_service: TeamService = Depends(get_team_service),
):
    """
    Get a single team by ID.

    Returns all team fields including:
    - Basic info: name
    - Relationships: lead_id, parent_team_id, department_id
    - Members: List of all team members with their basic info
    - Metadata: created_at, updated_at
    """
    team = team_service.get_team(team_id)

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Get team members
    members = team_service.get_team_members(team_id)

    # Create response with members
    team_dict = {
        "id": team.id,
        "name": team.name,
        "lead_id": team.lead_id,
        "parent_team_id": team.parent_team_id,
        "department_id": team.department_id,
        "created_at": team.created_at,
        "updated_at": team.updated_at,
        "members": [TeamMember.model_validate(member) for member in members],
    }

    return TeamDetail.model_validate(team_dict)


@router.get("/{team_id}/children", response_model=list[TeamListItem])
def get_child_teams(
    team_id: UUID,
    user = Depends(require_roles("member")),
    team_service: TeamService = Depends(get_team_service),
):
    """
    Get all direct child teams of a specific team.

    Returns a list of teams that have this team as their parent.
    Results are ordered alphabetically by name.
    """
    child_teams = team_service.get_child_teams(team_id)

    return [TeamListItem.model_validate(team) for team in child_teams]


@router.post("", response_model=TeamDetail, status_code=201)
def create_team(
    create_data: TeamCreate,
    user = Depends(require_roles("hr")),
    team_service: TeamService = Depends(get_team_service),
    db: Session = Depends(get_db),
):
    """
    Create a new team.

    Requires HR role.

    Validation:
    - If lead_id is provided, employee must exist
    - If parent_team_id is provided, team must exist
    - If department_id is provided, department must exist
    - If both parent_team_id and department_id provided, they must match

    Creates audit logs for the new team (CREATE).
    """
    try:
        team = team_service.create_team(
            name=create_data.name,
            lead_id=create_data.lead_id,
            parent_team_id=create_data.parent_team_id,
            department_id=create_data.department_id,
            changed_by_user_id=user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Commit the transaction (including audit logs)
    try:
        db.commit()
        db.refresh(team)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create team: {str(e)}")

    # Get team members for response
    members = team_service.get_team_members(team.id)

    team_dict = {
        "id": team.id,
        "name": team.name,
        "lead_id": team.lead_id,
        "parent_team_id": team.parent_team_id,
        "department_id": team.department_id,
        "created_at": team.created_at,
        "updated_at": team.updated_at,
        "members": [TeamMember.model_validate(member) for member in members],
    }

    return TeamDetail.model_validate(team_dict)


@router.patch("/{team_id}", response_model=TeamDetail)
def update_team(
    team_id: UUID,
    update_data: TeamUpdate,
    user = Depends(require_roles("hr")),
    team_service: TeamService = Depends(get_team_service),
    db: Session = Depends(get_db),
):
    """
    Update team fields (name, lead_id, parent_team_id, department_id).

    Requires HR role.

    Updates are logged to the audit log with previous and new states.
    Only provided fields will be updated.

    Editable fields:
    - name: Team name
    - lead_id: Team lead employee ID
    - parent_team_id: Parent team ID (validates no circular dependencies)
    - department_id: Department ID (only if team has no parent)
    """
    try:
        team = team_service.update_team(
            team_id,
            name=update_data.name,
            lead_id=update_data.lead_id,
            parent_team_id=update_data.parent_team_id,
            department_id=update_data.department_id,
            changed_by_user_id=user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Commit the transaction (including audit log)
    try:
        db.commit()
        db.refresh(team)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update team: {str(e)}")

    # Get team members for response
    members = team_service.get_team_members(team.id)

    team_dict = {
        "id": team.id,
        "name": team.name,
        "lead_id": team.lead_id,
        "parent_team_id": team.parent_team_id,
        "department_id": team.department_id,
        "created_at": team.created_at,
        "updated_at": team.updated_at,
        "members": [TeamMember.model_validate(member) for member in members],
    }

    return TeamDetail.model_validate(team_dict)


@router.delete("/{team_id}", status_code=204)
def delete_team(
    team_id: UUID,
    user = Depends(require_roles("hr")),
    team_service: TeamService = Depends(get_team_service),
    db: Session = Depends(get_db),
):
    """
    Delete a team.

    Requires HR role.

    Validation:
    - Team members are automatically removed from the team
    - Child teams are reassigned to the deleted team's parent

    All changes are logged to the audit log (DELETE entry).
    """
    try:
        team = team_service.delete_team(
            team_id,
            changed_by_user_id=user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Commit the transaction (including audit logs)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete team: {str(e)}")

    return None

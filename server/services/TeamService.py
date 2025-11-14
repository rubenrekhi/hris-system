"""
TeamService.py
--------------
Business logic for team management and operations.
"""

from __future__ import annotations
from typing import List, Tuple, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, update, func, and_
from models.TeamModel import Team
from models.EmployeeModel import Employee
from models.DepartmentModel import Department
from models.AuditLogModel import EntityType, ChangeType
from services.AuditLogService import AuditLogService


class TeamService:
    """Service for managing team operations."""

    def __init__(self, db: Session, audit_service: Optional[AuditLogService] = None):
        self.db = db
        self.audit_service = audit_service or AuditLogService(db)

    # ============================================================================
    # Private Helper Methods
    # ============================================================================

    def _remove_employee_from_team(
        self,
        employee: Employee,
        changed_by_user_id: Optional[UUID] = None,
    ) -> None:
        """
        Remove an employee from their team.

        If the employee is on a team and is the team lead, removes them as lead.
        Then removes the employee from the team (sets team_id to None).

        Creates audit log entries for:
        - The team if employee was removed as lead (UPDATE)
        - The employee's team assignment (UPDATE)

        Args:
            employee: Employee object to remove from team
            changed_by_user_id: UUID of user making the change
        """
        # Check if employee is on a team
        if not employee.team_id:
            return

        # Get the team
        team_query = select(Team).where(Team.id == employee.team_id)
        team = self.db.execute(team_query).scalar_one_or_none()

        if team and team.lead_id == employee.id:
            # Employee is the team lead, remove them as lead
            team_previous_state = {
                "lead_id": str(team.lead_id) if team.lead_id else None,
            }

            team.lead_id = None

            team_new_state = {
                "lead_id": None,
            }

            # Create audit log for team lead removal
            self.audit_service.create_audit_log(
                entity_type=EntityType.TEAM,
                entity_id=team.id,
                change_type=ChangeType.UPDATE,
                previous_state=team_previous_state,
                new_state=team_new_state,
                changed_by_user_id=changed_by_user_id,
            )

        # Remove employee from team
        employee_previous_state = {
            "team_id": str(employee.team_id) if employee.team_id else None,
        }

        employee.team_id = None

        employee_new_state = {
            "team_id": None,
        }

        # Create audit log for employee team removal
        self.audit_service.create_audit_log(
            entity_type=EntityType.EMPLOYEE,
            entity_id=employee.id,
            change_type=ChangeType.UPDATE,
            previous_state=employee_previous_state,
            new_state=employee_new_state,
            changed_by_user_id=changed_by_user_id,
        )

    def _validate_employee_exists(self, employee_id: UUID) -> Employee:
        """
        Validate that an employee exists and return it.

        Args:
            employee_id: UUID of the employee to validate

        Returns:
            The Employee object

        Raises:
            ValueError: If employee does not exist
        """
        emp_query = select(Employee).where(Employee.id == employee_id)
        employee = self.db.execute(emp_query).scalar_one_or_none()
        if not employee:
            raise ValueError(f"Employee with ID {employee_id} does not exist")
        return employee

    def _validate_department_exists(self, department_id: UUID) -> Department:
        """
        Validate that a department exists and return it.

        Args:
            department_id: UUID of the department to validate

        Returns:
            The Department object

        Raises:
            ValueError: If department does not exist
        """
        dept_query = select(Department).where(Department.id == department_id)
        department = self.db.execute(dept_query).scalar_one_or_none()
        if not department:
            raise ValueError(f"Department with ID {department_id} does not exist")
        return department

    def _validate_team_exists(self, team_id: UUID) -> Team:
        """
        Validate that a team exists and return it.

        Args:
            team_id: UUID of the team to validate

        Returns:
            The Team object

        Raises:
            ValueError: If team does not exist
        """
        team_query = select(Team).where(Team.id == team_id)
        team = self.db.execute(team_query).scalar_one_or_none()
        if not team:
            raise ValueError(f"Team with ID {team_id} does not exist")
        return team

    def _can_assign_parent_team(
        self,
        team_id: UUID,
        new_parent_team_id: Optional[UUID],
    ) -> bool:
        """
        Return True if assigning new_parent_team_id as parent for team_id
        will NOT create a cycle in the team tree.

        Rules:
        - new_parent_team_id is None → valid (cycle-free by definition)
        - new_parent_team_id == team_id → invalid (self-parenting)
        - Otherwise, invalid if new_parent_team_id is in team_id's subtree

        Args:
            team_id: UUID of the team being reassigned
            new_parent_team_id: UUID of the proposed new parent team (or None for top-level)

        Returns:
            True if assignment is valid (no cycle), False otherwise
        """
        # 1) No parent (become top-level team) is always safe from a cycle perspective
        if new_parent_team_id is None:
            return True

        # 2) Can't be your own parent
        if new_parent_team_id == team_id:
            return False

        # 3) Recursive CTE to get the full subtree under team_id
        #    If new_parent_team_id shows up in that subtree, it's invalid.

        # base: start from the team we're reparenting
        base = select(Team.id).where(Team.id == team_id)
        subtree = base.cte(name="team_subtree", recursive=True)

        # recursive step: all child teams of any node in subtree
        children = (
            select(Team.id)
            .where(Team.parent_team_id == subtree.c.id)
        )

        subtree = subtree.union_all(children)

        # now check whether new_parent_team_id appears anywhere in this subtree
        check = (
            select(subtree.c.id)
            .where(subtree.c.id == new_parent_team_id)
            .limit(1)
        )

        result = self.db.execute(check).scalar_one_or_none()
        # if result is not None, new_parent_team_id is in the subtree → invalid
        return result is None

    def _recursively_update_department(
        self,
        team_id: UUID,
        new_department_id: Optional[UUID],
        changed_by_user_id: Optional[UUID] = None,
    ) -> None:
        """
        Recursively update department for a team and all its descendant teams.

        Uses a recursive CTE to find all descendant teams, then performs a
        bulk update and creates bulk audit logs.

        Args:
            team_id: UUID of the root team to start from
            new_department_id: New department ID to assign (can be None)
            changed_by_user_id: UUID of user making the change
        """
        # Build recursive CTE to get all descendant teams (including root)
        base = select(Team.id).where(Team.id == team_id)
        subtree = base.cte(name="team_subtree", recursive=True)

        # recursive step: all child teams
        children = (
            select(Team.id)
            .where(Team.parent_team_id == subtree.c.id)
        )

        subtree = subtree.union_all(children)

        # Get all team IDs in subtree
        team_ids_query = select(subtree.c.id)
        team_ids = list(self.db.execute(team_ids_query).scalars().all())

        if not team_ids:
            return

        # Bulk update all teams' department_id
        update_stmt = (
            update(Team)
            .where(Team.id.in_(team_ids))
            .values(department_id=new_department_id)
        )
        self.db.execute(update_stmt)

        # Create bulk audit logs
        previous_state = {
            "department_id": "VARIED",  # Teams may have different previous departments
        }
        new_state = {
            "department_id": str(new_department_id) if new_department_id else None,
        }

        self.audit_service.bulk_create_audit_logs(
            entity_type=EntityType.TEAM,
            entity_ids=team_ids,
            change_type=ChangeType.UPDATE,
            previous_state=previous_state,
            new_state=new_state,
            changed_by_user_id=changed_by_user_id,
        )

    def _serialize_team_state(self, team: Team) -> dict:
        """
        Serialize a team to a dictionary for audit logging.

        Args:
            team: Team object to serialize

        Returns:
            Dictionary with team fields serialized for audit logging
        """
        return {
            "name": team.name,
            "lead_id": str(team.lead_id) if team.lead_id else None,
            "parent_team_id": str(team.parent_team_id) if team.parent_team_id else None,
            "department_id": str(team.department_id) if team.department_id else None,
        }

    # ============================================================================
    # Public Methods
    # ============================================================================

    def list_teams(
        self,
        *,
        department_id: Optional[UUID] = None,
        parent_team_id: Optional[UUID] = None,
        name: Optional[str] = None,
        limit: int = 25,
        offset: int = 0,
    ) -> Tuple[List[Team], int]:
        """
        List teams with optional filters, search, and pagination.

        Returns teams ordered alphabetically by name.
        Supports filtering by department and parent team.
        Supports searching by name (case-insensitive ILIKE).

        Returns tuple of (teams, total_count)
        """
        # Build filters
        filters = []

        if department_id:
            filters.append(Team.department_id == department_id)

        if parent_team_id:
            filters.append(Team.parent_team_id == parent_team_id)

        if name:
            filters.append(Team.name.ilike(f"%{name}%"))

        # Total count query
        count_query = select(func.count(Team.id)).select_from(Team)
        if filters:
            count_query = count_query.where(and_(*filters))
        total = self.db.execute(count_query).scalar_one()

        # Main query with ordering and pagination
        query = select(Team)
        if filters:
            query = query.where(and_(*filters))

        # Order alphabetically by name
        query = query.order_by(Team.name.asc(), Team.id.asc())

        # Pagination
        query = query.limit(limit).offset(offset)

        teams = self.db.execute(query).scalars().all()

        return teams, total

    def get_team(self, team_id: UUID) -> Optional[Team]:
        """
        Get a single team by ID.

        Returns None if not found.
        """
        query = select(Team).where(Team.id == team_id)
        return self.db.execute(query).scalar_one_or_none()

    def get_team_with_details(self, team_id: UUID) -> Optional[dict]:
        """
        Get a single team by ID with lead, parent team, and department names.

        Returns a dictionary with all team fields plus:
        - lead_name: Name of the team lead employee (if assigned)
        - parent_team_name: Name of the parent team (if assigned)
        - department_name: Name of the department (if assigned)
        - members: List of team member dictionaries

        Returns None if team not found.
        """
        # Alias for the parent team join to get parent team's name
        ParentTeam = Team.__table__.alias("parent_team")

        query = (
            select(
                Team.id,
                Team.name,
                Team.lead_id,
                Team.parent_team_id,
                Team.department_id,
                Team.created_at,
                Team.updated_at,
                Employee.name.label("lead_name"),
                ParentTeam.c.name.label("parent_team_name"),
                Department.name.label("department_name"),
            )
            .outerjoin(Employee, Team.lead_id == Employee.id)
            .outerjoin(ParentTeam, Team.parent_team_id == ParentTeam.c.id)
            .outerjoin(Department, Team.department_id == Department.id)
            .where(Team.id == team_id)
        )

        result = self.db.execute(query).mappings().first()
        if not result:
            return None

        # Convert to dict and fetch members
        team_dict = dict(result)
        members = self.get_team_members(team_id)
        team_dict["members"] = members

        return team_dict

    def get_team_members(self, team_id: UUID) -> List[Employee]:
        """
        Get all members of a specific team.

        Returns empty list if team has no members or doesn't exist.
        Members are ordered alphabetically by name.
        """
        query = select(Employee).where(Employee.team_id == team_id).order_by(Employee.name.asc())
        return list(self.db.execute(query).scalars().all())

    def get_child_teams(self, team_id: UUID) -> List[Team]:
        """
        Get all direct child teams of a specific team.

        Returns empty list if team has no children or doesn't exist.
        Child teams are ordered alphabetically by name.
        """
        query = select(Team).where(Team.parent_team_id == team_id).order_by(Team.name.asc())
        return list(self.db.execute(query).scalars().all())

    def create_team(
        self,
        *,
        name: str,
        lead_id: Optional[UUID] = None,
        parent_team_id: Optional[UUID] = None,
        department_id: Optional[UUID] = None,
        changed_by_user_id: Optional[UUID] = None,
    ) -> Team:
        """
        Create a new team.

        Validation:
        - If lead_id is provided, employee must exist
        - If parent_team_id is provided, team must exist
        - If department_id is provided, department must exist
        - If both parent_team_id and department_id are provided,
          parent team's department must match department_id

        If a team lead is assigned:
        - Removes employee from their current team (if any)
        - Sets employee's team_id to the new team
        - Sets new team's lead_id to the employee

        Creates audit log entries for:
        - The new team (CREATE)
        - The team lead if removed from previous team (UPDATE)
        - The team lead's new team assignment (UPDATE)

        Does NOT commit - router is responsible for transaction management.

        Returns the created team.
        Raises ValueError if validation fails.
        """
        # Validate foreign keys
        lead_employee = None
        if lead_id is not None:
            lead_employee = self._validate_employee_exists(lead_id)

        parent_team = None
        if parent_team_id is not None:
            parent_team = self._validate_team_exists(parent_team_id)

        if department_id is not None:
            self._validate_department_exists(department_id)

        # Validate parent team's department matches department_id
        if parent_team and department_id is not None:
            if parent_team.department_id != department_id:
                raise ValueError(
                    f"Parent team's department does not match the specified department. "
                    f"Parent team belongs to department {parent_team.department_id}, "
                    f"but department {department_id} was specified."
                )

        # Create new team
        team = Team(
            name=name,
            lead_id=None,  # Will be set after handling lead assignment
            parent_team_id=parent_team_id,
            department_id=department_id,
        )
        self.db.add(team)

        # Flush to get the team ID
        self.db.flush()

        # If a lead is assigned, handle their team reassignment
        if lead_employee:
            # Remove employee from their current team (if any)
            self._remove_employee_from_team(lead_employee, changed_by_user_id)

            # Assign employee to this team
            employee_previous_state = {
                "team_id": str(lead_employee.team_id) if lead_employee.team_id else None,
            }

            lead_employee.team_id = team.id

            employee_new_state = {
                "team_id": str(lead_employee.team_id) if lead_employee.team_id else None,
            }

            # Create audit log for employee's team assignment
            self.audit_service.create_audit_log(
                entity_type=EntityType.EMPLOYEE,
                entity_id=lead_employee.id,
                change_type=ChangeType.UPDATE,
                previous_state=employee_previous_state,
                new_state=employee_new_state,
                changed_by_user_id=changed_by_user_id,
            )

            # Set employee as team lead
            team.lead_id = lead_employee.id

        # Capture team state for audit log
        team_state = self._serialize_team_state(team)

        # Create audit log for new team
        self.audit_service.create_audit_log(
            entity_type=EntityType.TEAM,
            entity_id=team.id,
            change_type=ChangeType.CREATE,
            previous_state=None,
            new_state=team_state,
            changed_by_user_id=changed_by_user_id,
        )

        return team

    def update_team(
        self,
        team_id: UUID,
        *,
        name: Optional[str] = None,
        lead_id: Optional[UUID] = None,
        parent_team_id: Optional[UUID] = None,
        department_id: Optional[UUID] = None,
        changed_by_user_id: Optional[UUID] = None,
    ) -> Optional[Team]:
        """
        Update team fields (name, lead_id, parent_team_id, department_id).

        Validation:
        - Team must exist
        - If lead_id is provided, employee must exist
        - If parent_team_id is provided:
          - Parent team must exist
          - Cannot create circular dependency (validates using CTE)
          - Team's department will be set to parent's department
          - Department change cascades to all descendant teams
        - If department_id is provided:
          - Department must exist (if not None)
          - Team must not have a parent (can only change department if top-level)
          - Department change cascades to all descendant teams

        Team lead assignment:
        - If lead_id is provided, employee is removed from current team and assigned as lead
        - Previous lead (if any) remains on the team as regular member

        Creates audit log entries for:
        - The team itself (UPDATE)
        - The new team lead if reassigned (UPDATE)
        - All descendant teams if department changed (BULK UPDATE)

        Does NOT commit - router is responsible for transaction management.

        Returns updated team or None if not found.
        Raises ValueError if validation fails.
        """
        # Get existing team
        team = self._validate_team_exists(team_id)

        # Track changes for audit logging
        has_changes = False
        previous_state = {}
        new_state = {}

        # Update name if provided
        if name is not None and name != team.name:
            previous_state["name"] = team.name
            team.name = name
            new_state["name"] = team.name
            has_changes = True

        # Handle parent team assignment
        parent_team_changed = parent_team_id is not None and parent_team_id != team.parent_team_id

        if parent_team_changed:
            # Validate parent team exists
            parent_team = self._validate_team_exists(parent_team_id)

            # Check for circular dependency
            if not self._can_assign_parent_team(team_id, parent_team_id):
                raise ValueError(
                    f"Cannot assign parent team: would create a circular dependency in the team tree. "
                    f"The new parent team is a descendant of this team."
                )

            # Capture previous state
            previous_state["parent_team_id"] = str(team.parent_team_id) if team.parent_team_id else None

            # Update parent team
            team.parent_team_id = parent_team_id

            # Capture new state
            new_state["parent_team_id"] = str(team.parent_team_id) if team.parent_team_id else None
            has_changes = True

            # Inherit parent team's department and cascade to descendants
            new_department_id = parent_team.department_id
            if team.department_id != new_department_id:
                self._recursively_update_department(
                    team_id=team_id,
                    new_department_id=new_department_id,
                    changed_by_user_id=changed_by_user_id,
                )

        # Handle department assignment (only if no parent team change)
        elif department_id is not None and department_id != team.department_id:
            # Can only change department if team has no parent
            if team.parent_team_id is not None:
                raise ValueError(
                    f"Cannot change department: team has a parent team. "
                    f"Department must match parent team's department."
                )

            # Validate department exists (if not None)
            if department_id is not None:
                self._validate_department_exists(department_id)

            # Recursively update department for this team and all descendants
            self._recursively_update_department(
                team_id=team_id,
                new_department_id=department_id,
                changed_by_user_id=changed_by_user_id,
            )

        # Handle team lead assignment
        if lead_id is not None and lead_id != team.lead_id:
            # Validate employee exists
            lead_employee = self._validate_employee_exists(lead_id)

            # Remove new lead from their current team (if any)
            self._remove_employee_from_team(lead_employee, changed_by_user_id)

            # Assign employee to this team
            employee_previous_state = {
                "team_id": str(lead_employee.team_id) if lead_employee.team_id else None,
            }

            lead_employee.team_id = team_id

            employee_new_state = {
                "team_id": str(lead_employee.team_id) if lead_employee.team_id else None,
            }

            # Create audit log for employee's team assignment
            self.audit_service.create_audit_log(
                entity_type=EntityType.EMPLOYEE,
                entity_id=lead_employee.id,
                change_type=ChangeType.UPDATE,
                previous_state=employee_previous_state,
                new_state=employee_new_state,
                changed_by_user_id=changed_by_user_id,
            )

            # Capture previous lead state
            previous_state["lead_id"] = str(team.lead_id) if team.lead_id else None

            # Set employee as team lead
            team.lead_id = lead_id

            # Capture new lead state
            new_state["lead_id"] = str(team.lead_id) if team.lead_id else None
            has_changes = True

        # Create audit log for team update if there were changes
        if has_changes:
            self.audit_service.create_audit_log(
                entity_type=EntityType.TEAM,
                entity_id=team_id,
                change_type=ChangeType.UPDATE,
                previous_state=previous_state,
                new_state=new_state,
                changed_by_user_id=changed_by_user_id,
            )

        return team

    def delete_team(
        self,
        team_id: UUID,
        *,
        changed_by_user_id: Optional[UUID] = None,
    ) -> Optional[Team]:
        """
        Delete a team.

        Validation:
        - Team must exist

        If team has members:
        - All members' team_id is set to None
        - Audit logs created for each member

        If team has child teams:
        - Child teams' parent_team_id is set to the deleted team's parent_team_id
        - If deleted team has no parent, child teams become independent (parent_team_id = None)
        - Child teams' department_id remains unchanged

        Creates audit log entries for:
        - The deleted team (DELETE)
        - Each member that was removed from the team (UPDATE)
        - Each child team that was reassigned (UPDATE)

        Does NOT commit - router is responsible for transaction management.

        Returns deleted team or None if not found.
        """
        # Get existing team
        team = self._validate_team_exists(team_id)

        # Get all team members and remove them from the team
        members_query = select(Employee).where(Employee.team_id == team_id)
        members = list(self.db.execute(members_query).scalars().all())

        for member in members:
            # Capture previous state
            member_previous_state = {
                "team_id": str(member.team_id) if member.team_id else None,
            }

            # Remove from team
            member.team_id = None

            # Capture new state
            member_new_state = {
                "team_id": None,
            }

            # Create audit log for member update
            self.audit_service.create_audit_log(
                entity_type=EntityType.EMPLOYEE,
                entity_id=member.id,
                change_type=ChangeType.UPDATE,
                previous_state=member_previous_state,
                new_state=member_new_state,
                changed_by_user_id=changed_by_user_id,
            )

        # Get all child teams
        child_teams_query = select(Team).where(Team.parent_team_id == team_id)
        child_teams = list(self.db.execute(child_teams_query).scalars().all())

        # Reassign child teams to the deleted team's parent
        new_parent_id = team.parent_team_id

        for child_team in child_teams:
            # Capture previous state
            child_previous_state = {
                "parent_team_id": str(child_team.parent_team_id) if child_team.parent_team_id else None,
            }

            # Update parent team
            child_team.parent_team_id = new_parent_id

            # Capture new state
            child_new_state = {
                "parent_team_id": str(child_team.parent_team_id) if child_team.parent_team_id else None,
            }

            # Create audit log for child team update
            self.audit_service.create_audit_log(
                entity_type=EntityType.TEAM,
                entity_id=child_team.id,
                change_type=ChangeType.UPDATE,
                previous_state=child_previous_state,
                new_state=child_new_state,
                changed_by_user_id=changed_by_user_id,
            )

        # Capture team state before deletion
        deleted_team_state = self._serialize_team_state(team)

        # Create audit log for deleted team
        self.audit_service.create_audit_log(
            entity_type=EntityType.TEAM,
            entity_id=team_id,
            change_type=ChangeType.DELETE,
            previous_state=deleted_team_state,
            new_state=None,
            changed_by_user_id=changed_by_user_id,
        )

        # Delete the team
        self.db.delete(team)

        return team

"""
GlobalSearchService.py
----------------------
Business logic for global search operations across entities.
"""

from __future__ import annotations
from typing import List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from models.EmployeeModel import Employee
from models.DepartmentModel import Department
from models.TeamModel import Team


class GlobalSearchService:
    """Service for global search across employees, departments, and teams."""

    def __init__(self, db: Session):
        self.db = db

    def search(self, query: str) -> Tuple[List[Employee], List[Department], List[Team]]:
        """
        Search across employees, departments, and teams using ILIKE.

        For employees: searches name or email (limit 10)
        For departments: searches name only (limit 10)
        For teams: searches name only (limit 10)

        Returns tuple of (employees, departments, teams)
        """
        search_pattern = f"%{query}%"
        RESULT_LIMIT = 10

        # Search employees by name OR email
        employee_query = (
            select(Employee)
            .where(
                or_(
                    Employee.name.ilike(search_pattern),
                    Employee.email.ilike(search_pattern)
                )
            )
            .limit(RESULT_LIMIT)
        )
        employees = self.db.execute(employee_query).scalars().all()

        # Search departments by name
        department_query = (
            select(Department)
            .where(Department.name.ilike(search_pattern))
            .limit(RESULT_LIMIT)
        )
        departments = self.db.execute(department_query).scalars().all()

        # Search teams by name
        team_query = (
            select(Team)
            .where(Team.name.ilike(search_pattern))
            .limit(RESULT_LIMIT)
        )
        teams = self.db.execute(team_query).scalars().all()

        return employees, departments, teams
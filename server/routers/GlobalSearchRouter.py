"""
GlobalSearchRouter.py
---------------------
API routes for global search across entities.
"""

from fastapi import APIRouter, Depends
from services.GlobalSearchService import GlobalSearchService
from schemas.GlobalSearchSchemas import (
    GlobalSearchQuery,
    GlobalSearchResponse,
    EmployeeSearchResult,
    DepartmentSearchResult,
    TeamSearchResult,
)
from core.dependencies import get_global_search_service, require_roles

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=GlobalSearchResponse)
def global_search(
    query: GlobalSearchQuery = Depends(),
    user = Depends(require_roles("member")),
    search_service: GlobalSearchService = Depends(get_global_search_service),
):
    """
    Global search across employees, departments, and teams.

    Searches:
    - Employees: by name or email (ILIKE)
    - Departments: by name (ILIKE)
    - Teams: by name (ILIKE)

    Returns deduplicated results with only id and name fields.
    """
    employees, departments, teams = search_service.search(query.q)

    return GlobalSearchResponse(
        employees=[EmployeeSearchResult.model_validate(emp) for emp in employees],
        departments=[DepartmentSearchResult.model_validate(dept) for dept in departments],
        teams=[TeamSearchResult.model_validate(team) for team in teams],
    )
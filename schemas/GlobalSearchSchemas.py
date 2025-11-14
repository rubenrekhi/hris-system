"""
GlobalSearchSchemas.py
----------------------
Pydantic schemas for global search request/response validation.
"""

from __future__ import annotations
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================================
# Query Schemas
# ============================================================================

class GlobalSearchQuery(BaseModel):
    """Query parameters for global search."""
    q: str = Field(..., min_length=1, description="Search query string")

    @field_validator("q")
    @classmethod
    def validate_query_not_empty(cls, v: str) -> str:
        """Ensure query is not empty or just whitespace."""
        if not v.strip():
            raise ValueError("Search query cannot be empty or contain only whitespace")
        return v.strip()


# ============================================================================
# Response Schemas
# ============================================================================

class EmployeeSearchResult(BaseModel):
    """Schema for employee search results."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class DepartmentSearchResult(BaseModel):
    """Schema for department search results."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class TeamSearchResult(BaseModel):
    """Schema for team search results."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class GlobalSearchResponse(BaseModel):
    """Response schema containing all search results."""
    employees: list[EmployeeSearchResult]
    departments: list[DepartmentSearchResult]
    teams: list[TeamSearchResult]

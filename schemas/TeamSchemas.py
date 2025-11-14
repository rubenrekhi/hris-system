"""
TeamSchemas.py
--------------
Pydantic schemas for team request/response validation.
"""

from __future__ import annotations
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# Request Schemas
# ============================================================================

class TeamCreate(BaseModel):
    """Schema for creating a new team."""
    name: str = Field(..., min_length=1, description="Team name")
    lead_id: Optional[UUID] = Field(None, description="Team lead employee ID")
    parent_team_id: Optional[UUID] = Field(None, description="Parent team ID")
    department_id: Optional[UUID] = Field(None, description="Department ID")


class TeamUpdate(BaseModel):
    """Schema for updating team fields."""
    name: Optional[str] = Field(None, min_length=1, description="Team name")
    lead_id: Optional[UUID] = Field(None, description="Team lead employee ID")
    parent_team_id: Optional[UUID] = Field(None, description="Parent team ID")
    department_id: Optional[UUID] = Field(None, description="Department ID")


# ============================================================================
# Query Schemas
# ============================================================================

class TeamListQuery(BaseModel):
    """Query parameters for listing teams."""
    department_id: Optional[UUID] = Field(None, description="Filter by department ID")
    parent_team_id: Optional[UUID] = Field(None, description="Filter by parent team ID")
    name: Optional[str] = Field(None, min_length=1, description="Search by name (case-insensitive)")
    limit: int = Field(25, ge=1, le=100, description="Number of items per page")
    offset: int = Field(0, ge=0, description="Number of items to skip")


# ============================================================================
# Response Schemas
# ============================================================================

class TeamMember(BaseModel):
    """Schema for team member information."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    title: Optional[str]
    email: str


class TeamListItem(BaseModel):
    """Schema for team list items."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    department_id: Optional[UUID]
    parent_team_id: Optional[UUID]
    lead_id: Optional[UUID]


class TeamListResponse(BaseModel):
    """Paginated response for team listing."""
    items: list[TeamListItem]
    total: int
    limit: int
    offset: int


class TeamDetail(BaseModel):
    """Schema for detailed team view with all fields including members."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    lead_id: Optional[UUID]
    parent_team_id: Optional[UUID]
    department_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    members: list[TeamMember] = Field(default_factory=list)

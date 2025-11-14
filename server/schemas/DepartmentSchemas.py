"""
DepartmentSchemas.py
--------------------
Pydantic schemas for department request/response validation.
"""

from __future__ import annotations
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# Request Schemas
# ============================================================================

class DepartmentCreate(BaseModel):
    """Schema for creating a new department."""
    name: str = Field(..., min_length=1, description="Department name")


class DepartmentUpdate(BaseModel):
    """Schema for updating department fields."""
    name: str = Field(..., min_length=1, description="Department name")


# ============================================================================
# Query Schemas
# ============================================================================

class PaginationQuery(BaseModel):
    """Query parameters for pagination."""
    limit: int = Field(25, ge=1, le=100, description="Number of items per page")
    offset: int = Field(0, ge=0, description="Number of items to skip")


# ============================================================================
# Response Schemas
# ============================================================================

class DepartmentDetail(BaseModel):
    """Schema for detailed department view with all fields."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime


class DepartmentListItem(BaseModel):
    """Schema for department list items (id and name only)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class TeamListItem(BaseModel):
    """Schema for team list items (id and name only)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class EmployeeListItem(BaseModel):
    """Schema for employee list items (id and name only)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class TeamListResponse(BaseModel):
    """Paginated response for team listing."""
    items: list[TeamListItem]
    total: int
    limit: int
    offset: int


class EmployeeListResponse(BaseModel):
    """Paginated response for employee listing."""
    items: list[EmployeeListItem]
    total: int
    limit: int
    offset: int


class DepartmentListResponse(BaseModel):
    """Paginated response for department listing."""
    items: list[DepartmentListItem]
    total: int
    limit: int
    offset: int
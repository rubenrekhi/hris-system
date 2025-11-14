"""
EmployeeSchemas.py
------------------
Pydantic schemas for employee request/response validation.
"""

from __future__ import annotations
from typing import Optional
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from models.EmployeeModel import EmployeeStatus


# ============================================================================
# Request Schemas
# ============================================================================

class EmployeeCreate(BaseModel):
    """Schema for creating a new employee."""
    name: str = Field(..., min_length=1, description="Employee name")
    title: Optional[str] = Field(None, description="Job title")
    email: str = Field(..., min_length=1, description="Employee email")
    hired_on: Optional[date] = Field(None, description="Hire date")
    salary: Optional[int] = Field(None, ge=0, description="Employee salary")
    status: EmployeeStatus = Field(default=EmployeeStatus.ACTIVE, description="Employee status")
    manager_id: Optional[UUID] = Field(None, description="Manager employee ID (required unless first employee)")
    department_id: Optional[UUID] = Field(None, description="Department ID")
    team_id: Optional[UUID] = Field(None, description="Team ID")


class EmployeeReplaceCEO(BaseModel):
    """Schema for replacing the CEO."""
    name: str = Field(..., min_length=1, description="Employee name")
    title: Optional[str] = Field(None, description="Job title")
    email: str = Field(..., min_length=1, description="Employee email")
    hired_on: Optional[date] = Field(None, description="Hire date")
    salary: Optional[int] = Field(None, ge=0, description="Employee salary")
    status: EmployeeStatus = Field(default=EmployeeStatus.ACTIVE, description="Employee status")
    department_id: Optional[UUID] = Field(None, description="Department ID")
    team_id: Optional[UUID] = Field(None, description="Team ID")


class EmployeeUpdate(BaseModel):
    """Schema for updating employee fields."""
    name: Optional[str] = Field(None, min_length=1, description="Employee name")
    title: Optional[str] = Field(None, description="Job title")
    salary: Optional[int] = Field(None, ge=0, description="Employee salary")
    status: Optional[EmployeeStatus] = Field(None, description="Employee status")


class EmployeeDepartmentAssign(BaseModel):
    """Schema for assigning or removing a department from an employee."""
    department_id: Optional[UUID] = Field(None, description="Department ID to assign (null to remove)")


class EmployeeTeamAssign(BaseModel):
    """Schema for assigning or removing a team from an employee."""
    team_id: Optional[UUID] = Field(None, description="Team ID to assign (null to remove)")


# ============================================================================
# Query Schemas
# ============================================================================

class EmployeeListQuery(BaseModel):
    """Query parameters for listing employees."""
    team_id: Optional[UUID] = Field(None, description="Filter by team ID")
    department_id: Optional[UUID] = Field(None, description="Filter by department ID")
    status: Optional[EmployeeStatus] = Field(None, description="Filter by employee status")
    min_salary: Optional[int] = Field(None, ge=0, description="Minimum salary (inclusive)")
    max_salary: Optional[int] = Field(None, ge=0, description="Maximum salary (inclusive)")
    name: Optional[str] = Field(None, min_length=1, description="Search by name (case-insensitive)")
    email: Optional[str] = Field(None, min_length=1, description="Search by email (case-insensitive)")
    limit: int = Field(25, ge=1, le=100, description="Number of items per page")
    offset: int = Field(0, ge=0, description="Number of items to skip")

    @field_validator("name", "email")
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        """Strip whitespace and return None if empty."""
        if v is None:
            return None
        stripped = v.strip()
        return stripped if stripped else None


# ============================================================================
# Response Schemas
# ============================================================================

class EmployeeListItem(BaseModel):
    """Schema for employee list items."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class EmployeeListResponse(BaseModel):
    """Paginated response for employee listing."""
    items: list[EmployeeListItem]
    total: int
    limit: int
    offset: int


class EmployeeDetail(BaseModel):
    """Schema for detailed employee view with all fields."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    title: Optional[str]
    email: str
    hired_on: Optional[date]
    salary: Optional[int]
    status: EmployeeStatus
    department_id: Optional[UUID]
    manager_id: Optional[UUID]
    team_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

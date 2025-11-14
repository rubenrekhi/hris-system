"""
ExportSchemas.py
----------------
Pydantic schemas for employee export filtering.
"""

from typing import Optional
from uuid import UUID
from datetime import date
from pydantic import BaseModel, Field
from models.EmployeeModel import EmployeeStatus


# ============================================================================
# Request Schemas
# ============================================================================

class ExportFilterSchema(BaseModel):
    """Schema for filtering employee exports."""
    department_id: Optional[UUID] = Field(None, description="Filter by department ID")
    team_id: Optional[UUID] = Field(None, description="Filter by team ID")
    status: Optional[EmployeeStatus] = Field(None, description="Filter by employee status (ACTIVE, ON_LEAVE)")
    hired_from: Optional[date] = Field(None, description="Filter employees hired on or after this date")
    hired_to: Optional[date] = Field(None, description="Filter employees hired on or before this date")

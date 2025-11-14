"""
ImportSchemas.py
----------------
Pydantic schemas for CSV bulk import operations.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from datetime import date
from uuid import UUID
from models.EmployeeModel import EmployeeStatus


class EmployeeCSVRow(BaseModel):
    """
    Schema for validating a single row from employee CSV import.

    Designed to match CSV columns where manager is referenced by email
    and department/team are referenced by name (not IDs).
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Jane Smith",
                "email": "jane.smith@example.com",
                "title": "Senior Engineer",
                "hired_on": "2024-01-15",
                "salary": 120000,
                "status": "ACTIVE",
                "manager_email": "john.doe@example.com",
                "department_name": "Engineering",
                "team_name": "Backend Team"
            }
        }
    )

    name: str = Field(..., min_length=1, description="Employee name (required)")
    email: str = Field(..., min_length=1, description="Employee email (required, must be unique)")
    title: Optional[str] = Field(None, description="Job title")
    hired_on: Optional[date] = Field(None, description="Hire date (YYYY-MM-DD format)")
    salary: Optional[int] = Field(None, ge=0, description="Salary (must be >= 0 if provided)")
    status: EmployeeStatus = Field(default=EmployeeStatus.ACTIVE, description="Employee status (ACTIVE or ON_LEAVE)")
    manager_email: Optional[str] = Field(None, description="Manager's email (can be in CSV or existing in DB)")
    department_name: Optional[str] = Field(None, description="Department name (must exist in DB)")
    team_name: Optional[str] = Field(None, description="Team name (must exist in DB)")


class BulkImportError(BaseModel):
    """Details about a failed row in bulk import."""
    row_number: int = Field(..., description="Row number in CSV (1-indexed)")
    email: Optional[str] = Field(None, description="Email from the row (if parseable)")
    error_message: str = Field(..., description="Error description")
    row_data: dict[str, Any] = Field(..., description="Raw row data from CSV")


class BulkImportResult(BaseModel):
    """
    Result of bulk employee import operation.

    Contains success statistics, created employee IDs, and detailed
    error information for any failed rows.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_rows": 100,
                "successful_imports": 98,
                "failed_rows": [
                    {
                        "row_number": 15,
                        "email": "duplicate@example.com",
                        "error_message": "Email already exists in database",
                        "row_data": {"name": "John Duplicate", "email": "duplicate@example.com"}
                    }
                ],
                "created_employee_ids": ["uuid1", "uuid2", "..."],
                "warnings": ["Row 50: Manager email not found, will report to NULL"]
            }
        }
    )

    total_rows: int = Field(..., description="Total number of rows in CSV")
    successful_imports: int = Field(default=0, description="Number of employees successfully created")
    failed_rows: List[BulkImportError] = Field(default_factory=list, description="Details of failed rows")
    created_employee_ids: List[UUID] = Field(default_factory=list, description="IDs of created employees")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings")

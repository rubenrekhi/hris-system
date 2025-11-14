"""
AuditLogSchemas.py
------------------
Pydantic schemas for audit log request/response validation.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, Any, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from models.AuditLogModel import EntityType, ChangeType

# ============================================================================
# Response Schemas 
# ============================================================================
class AuditLogBase(BaseModel):
    """Base schema with common audit log fields."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    entity_type: EntityType
    entity_id: UUID
    change_type: ChangeType
    changed_by_user_id: Optional[UUID]
    created_at: datetime


class AuditLogListItem(AuditLogBase):
    """
    Schema for audit log list items.
    Excludes previous_state and new_state for performance.
    """
    pass


class AuditLogDetail(AuditLogBase):
    """
    Schema for detailed audit log view.
    Includes full state information.
    """
    previous_state: Optional[dict[str, Any]]
    new_state: Optional[dict[str, Any]]
    updated_at: datetime


class AuditLogListResponse(BaseModel):
    """Paginated response for audit log listing."""
    items: list[AuditLogListItem]
    total: int
    limit: int
    offset: int


# ============================================================================
# Request Schemas (Query Parameters)
# ============================================================================

class AuditLogListQuery(BaseModel):
    """Query parameters for listing audit logs."""
    entity_type: Optional[EntityType] = Field(None, description="Filter by entity type")
    entity_id: Optional[UUID] = Field(None, description="Filter by entity ID")
    change_type: Optional[ChangeType] = Field(None, description="Filter by change type")
    changed_by_user_id: Optional[UUID] = Field(None, description="Filter by user who made the change")
    date_from: Optional[datetime] = Field(None, description="Filter logs from this date (inclusive)")
    date_to: Optional[datetime] = Field(None, description="Filter logs until this date (exclusive)")
    limit: int = Field(25, ge=1, le=100, description="Number of items per page")
    offset: int = Field(0, ge=0, description="Number of items to skip")
    order: Literal["asc", "desc"] = Field("desc", description="Sort order by created_at")

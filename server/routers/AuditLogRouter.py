"""
AuditLogRouter.py
-----------------
API routes for audit log operations and activity tracking.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from services.AuditLogService import AuditLogService
from schemas.AuditLogSchemas import (
    AuditLogListResponse,
    AuditLogDetail,
    AuditLogListItem,
    AuditLogListQuery,
)
from core.dependencies import get_audit_log_service, require_roles

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("", response_model=AuditLogListResponse)
def list_audit_logs(
    query: AuditLogListQuery = Depends(),
    user = Depends(require_roles("admin")),
    audit_service: AuditLogService = Depends(get_audit_log_service),
):
    """
    List audit logs with optional filters and pagination.

    Returns a paginated list without previous_state and new_state for performance.
    Use the detail endpoint to get full state information.
    """
    items, total = audit_service.list_audit_logs(
        entity_type=query.entity_type,
        entity_id=query.entity_id,
        change_type=query.change_type,
        changed_by_user_id=query.changed_by_user_id,
        date_from=query.date_from,
        date_to=query.date_to,
        limit=query.limit,
        offset=query.offset,
        order=query.order,
    )

    return AuditLogListResponse(
        items=[AuditLogListItem.model_validate(item) for item in items],
        total=total,
        limit=query.limit,
        offset=query.offset,
    )


@router.get("/{log_id}", response_model=AuditLogDetail)
def get_audit_log(
    log_id: UUID,
    user = Depends(require_roles("admin")),
    audit_service: AuditLogService = Depends(get_audit_log_service),
):
    """
    Get detailed audit log by ID.

    Includes full previous_state and new_state information.
    """
    log = audit_service.get_audit_log(log_id)

    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")

    return AuditLogDetail.model_validate(log)

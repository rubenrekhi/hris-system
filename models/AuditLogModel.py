"""
AuditLogModel.py
----------------
Database model for audit log entries tracking system activity.
"""

from __future__ import annotations
from enum import Enum
from sqlalchemy import Column, JSON, Enum as SAEnum, Index
from sqlalchemy.dialects.postgresql import UUID
from models.BaseModel import BaseModel
from sqlalchemy.schema import ForeignKey

class EntityType(str, Enum):
    EMPLOYEE = "EMPLOYEE"
    USER = "USER"
    TEAM = "TEAM"
    DEPARTMENT = "DEPARTMENT"

class ChangeType(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"

class AuditLog(BaseModel):
    __tablename__ = "audit_log"

    entity_type = Column(SAEnum(EntityType), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    change_type = Column(SAEnum(ChangeType), nullable=False)
    previous_state = Column(JSON, nullable=True)
    new_state = Column(JSON, nullable=True)
    changed_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    __table_args__ = (
        Index("idx_audit_entity", "entity_type", "entity_id"),
    )

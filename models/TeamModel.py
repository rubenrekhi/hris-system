"""
TeamModel.py
------------
Database model for team structure and management.
"""

from __future__ import annotations
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from models.BaseModel import BaseModel


class Team(BaseModel):
    __tablename__ = "teams"

    name = Column(String, nullable=False, unique=True)

    lead_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    parent_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), index=True, nullable=True)

    # Relationships
    department = relationship("Department", back_populates="teams")
    lead = relationship("Employee", foreign_keys=[lead_id])
    parent_team = relationship("Team", remote_side="Team.id")
    members = relationship("Employee", back_populates="team")
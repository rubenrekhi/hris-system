"""
EmployeeModel.py
----------------
Database model for employee records and information.
"""

from __future__ import annotations
from enum import Enum
from sqlalchemy import Column, String, Date, ForeignKey, Integer, Enum as SAEnum, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from models.BaseModel import BaseModel


class EmployeeStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ON_LEAVE = "ON_LEAVE"

class Employee(BaseModel):
    __tablename__ = "employees"

    name = Column(String, nullable=False)
    title = Column(String, nullable=True)
    email = Column(String, nullable=False, unique=True)

    hired_on = Column(Date, nullable=True)
    salary = Column(Integer, nullable=True)
    status = Column(SAEnum(EmployeeStatus), nullable=False, default=EmployeeStatus.ACTIVE)

    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), index=True, nullable=True)
    manager_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    department = relationship("Department", back_populates="employees")
    manager = relationship("Employee", remote_side="Employee.id", back_populates="direct_reports", foreign_keys=[manager_id])
    direct_reports = relationship("Employee", back_populates="manager", foreign_keys=[manager_id], cascade="save-update", passive_deletes=False)
    team = relationship("Team", back_populates="members", foreign_keys=[team_id])
    user = relationship("User", back_populates="employee", uselist=False)

    __table_args__ = (
        # integrity
        CheckConstraint("manager_id IS NULL OR id <> manager_id", name="chk_emp_self_manager"),
        # read-heavy indexes
        Index("idx_emp_manager", "manager_id"),
        Index("idx_emp_team_name", "team_id", "name"),
        Index("idx_emp_dept_name", "department_id", "name"),
    )

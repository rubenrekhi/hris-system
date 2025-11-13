"""
DepartmentModel.py
------------------
Database model for department organization and management.
"""

from __future__ import annotations
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from models.BaseModel import BaseModel

class Department(BaseModel):
    __tablename__ = "departments"

    name = Column(String, nullable=False, unique=True)

    # Backrefs
    employees = relationship("Employee", back_populates="department")
    teams = relationship("Team", back_populates="department")

"""
UserModel.py
------------
Database model for user authentication and account management.
"""

from __future__ import annotations
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from models.BaseModel import BaseModel

class User(BaseModel):
    __tablename__ = "users"

    email = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=True)

    workos_user_id = Column(String, nullable=True, unique=True)

    # 1:1 link to Employee via unique FK
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, unique=True)
    employee = relationship("Employee", back_populates="user", uselist=False)

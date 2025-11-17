"""
UserService.py
--------------
Business logic for user authentication and account management.
"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from models.UserModel import User
from models.EmployeeModel import Employee


class UserService:
    """Service for managing user operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_or_update_from_workos(
        self,
        workos_user_id: str,
        email: str,
        name: str,
    ) -> User:
        """
        Create or update User from WorkOS authentication.
        Automatically links to Employee if one exists with matching email.

        Args:
            workos_user_id: WorkOS user ID (e.g., "user_01ABC123")
            email: User email address
            name: User full name

        Returns:
            User object (new or updated)

        Note:
            Does NOT commit - router is responsible for transaction management.
        """
        # Check if user already exists by workos_user_id or email
        existing_user_query = select(User).where(
            or_(
                User.workos_user_id == workos_user_id,
                User.email == email
            )
        )
        existing_user = self.db.execute(existing_user_query).scalar_one_or_none()

        if existing_user:
            # Update existing user
            existing_user.workos_user_id = workos_user_id
            existing_user.email = email
            existing_user.name = name
            user = existing_user
        else:
            # Create new user
            user = User(
                workos_user_id=workos_user_id,
                email=email,
                name=name
            )
            self.db.add(user)

        # Flush to get user ID for potential linking
        self.db.flush()

        # Try to link to existing employee by email if not already linked
        if not user.employee_id:
            employee_query = select(Employee).where(Employee.email == email)
            employee = self.db.execute(employee_query).scalar_one_or_none()

            if employee and not employee.user:  # Employee exists and has no user
                user.employee_id = employee.id

        # Flush again to persist the employee link
        self.db.flush()

        return user

    def get_user_by_workos_id(self, workos_user_id: str) -> Optional[User]:
        """
        Get user by WorkOS user ID.

        Args:
            workos_user_id: WorkOS user ID

        Returns:
            User object or None if not found
        """
        query = select(User).where(User.workos_user_id == workos_user_id)
        return self.db.execute(query).scalar_one_or_none()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            email: User email address

        Returns:
            User object or None if not found
        """
        query = select(User).where(User.email == email)
        return self.db.execute(query).scalar_one_or_none()

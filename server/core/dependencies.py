"""
dependencies.py
------------
Defines all dependency injections for the API.
"""

import os
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from core.database import SessionLocal
from core.workos_client import workos_client
from services.AuditLogService import AuditLogService
from services.GlobalSearchService import GlobalSearchService
from services.EmployeeService import EmployeeService
from services.DepartmentService import DepartmentService
from services.TeamService import TeamService
from services.ImportService import ImportService
from services.ExportService import ExportService
from services.UserService import UserService
from uuid import UUID


# Authenticated user class from WorkOS
class AuthenticatedUser:
    """Represents an authenticated WorkOS user with role."""

    def __init__(
        self,
        id: UUID,
        workos_user_id: str,
        email: str,
        name: str,
        organization_id: str = None,
        role: str = None,
        employee_id: UUID = None
    ):
        self.id = id
        self.workos_user_id = workos_user_id
        self.email = email
        self.name = name
        self.organization_id = organization_id
        self.role = role  # "admin", "hr", or "member"
        self.employee_id = employee_id



# --------------------------------------------------------------------
# Dependency
# --------------------------------------------------------------------
def get_db():
    """
    FastAPI dependency — yields a database session per request.
    Ensures session is closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



# --------------------------------------------------------------------
# Dependency: get_current_user(). Returns user and verifies authentication.
# --------------------------------------------------------------------
async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> AuthenticatedUser:
    """
    Verify WorkOS session cookie and return authenticated user.
    Also creates/updates User record in database.

    Raises:
        HTTPException: 401 if not authenticated or session invalid
    """
    sealed_session = request.cookies.get("workos_session")

    if not sealed_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    try:
        # Load and verify session
        session = workos_client.user_management.load_sealed_session(
            sealed_session=sealed_session,
            cookie_password=os.getenv("WORKOS_COOKIE_PASSWORD")
        )

        # Authenticate (verifies validity, auto-refreshes if needed)
        auth_response = session.authenticate()

        if not auth_response.authenticated:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or invalid"
            )

        workos_user = auth_response.user

        # Extract role and organization_id from auth_response
        role = auth_response.role if hasattr(auth_response, 'role') else None
        organization_id = auth_response.organization_id if hasattr(auth_response, 'organization_id') else None

        # Create/update user in database
        user_service = UserService(db)
        db_user = user_service.create_or_update_from_workos(
            workos_user_id=workos_user.id,
            email=workos_user.email,
            name=f"{workos_user.first_name or ''} {workos_user.last_name or ''}".strip() or workos_user.email
        )
        db.commit()

        return AuthenticatedUser(
            id = db_user.id,
            workos_user_id=workos_user.id,
            email=workos_user.email,
            name=f"{workos_user.first_name or ''} {workos_user.last_name or ''}".strip() or workos_user.email,
            organization_id=organization_id,
            role=role,
            employee_id=db_user.employee_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )


# --------------------------------------------------------------------
# Role Hierarchy Definition
# --------------------------------------------------------------------
ROLE_HIERARCHY = {
    "member": 1,
    "hr": 2,
    "admin": 3,
}


def _get_role_level(role: str) -> int:
    """Get the hierarchy level of a role. Higher number = more permissions."""
    return ROLE_HIERARCHY.get(role, 0)


# --------------------------------------------------------------------
# Dependency: require_roles()
# --------------------------------------------------------------------
def require_roles(minimum_role: str):
    """
    Dependency that requires user to have a minimum role level or higher.
    Uses hierarchical role checking: admin > hr > member

    Args:
        minimum_role: Minimum role slug required (e.g., "admin", "hr", "member")

    Returns:
        Authenticated user if they have sufficient role level

    Raises:
        HTTPException: 403 if user doesn't have sufficient role level
    """
    async def dependency(user: AuthenticatedUser = Depends(get_current_user)):
        if not user.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Minimum required role: {minimum_role}"
            )

        user_level = _get_role_level(user.role)
        required_level = _get_role_level(minimum_role)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Minimum required role: {minimum_role} (you have: {user.role})"
            )

        return user

    return dependency


# --------------------------------------------------------------------
# Dependency: get_audit_log_service()
# --------------------------------------------------------------------
def get_audit_log_service(db: Session = Depends(get_db)) -> AuditLogService:
    """
    FastAPI dependency — returns an AuditLogService instance for the current request.
    The service is initialized with the database session.
    """
    return AuditLogService(db)


# --------------------------------------------------------------------
# Dependency: get_global_search_service()
# --------------------------------------------------------------------
def get_global_search_service(db: Session = Depends(get_db)) -> GlobalSearchService:
    """
    FastAPI dependency — returns a GlobalSearchService instance for the current request.
    The service is initialized with the database session.
    """
    return GlobalSearchService(db)


# --------------------------------------------------------------------
# Dependency: get_employee_service()
# --------------------------------------------------------------------
def get_employee_service(db: Session = Depends(get_db)) -> EmployeeService:
    """
    FastAPI dependency — returns an EmployeeService instance for the current request.
    The service is initialized with the database session.
    """
    return EmployeeService(db)


# --------------------------------------------------------------------
# Dependency: get_department_service()
# --------------------------------------------------------------------
def get_department_service(db: Session = Depends(get_db)) -> DepartmentService:
    """
    FastAPI dependency — returns a DepartmentService instance for the current request.
    The service is initialized with the database session.
    """
    return DepartmentService(db)


# --------------------------------------------------------------------
# Dependency: get_team_service()
# --------------------------------------------------------------------
def get_team_service(db: Session = Depends(get_db)) -> TeamService:
    """
    FastAPI dependency — returns a TeamService instance for the current request.
    The service is initialized with the database session.
    """
    return TeamService(db)


# --------------------------------------------------------------------
# Dependency: get_import_service()
# --------------------------------------------------------------------
def get_import_service(db: Session = Depends(get_db)) -> ImportService:
    """
    FastAPI dependency — returns an ImportService instance for the current request.
    The service is initialized with the database session.
    """
    return ImportService(db)


def get_export_service(db: Session = Depends(get_db)) -> ExportService:
    """
    FastAPI dependency — returns an ExportService instance for the current request.
    The service is initialized with the database session.
    """
    return ExportService(db)
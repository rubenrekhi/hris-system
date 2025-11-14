"""
dependencies.py
------------
Defines all dependency injections for the API.
"""

from fastapi import Depends
from sqlalchemy.orm import Session
from core.database import SessionLocal
from services.AuditLogService import AuditLogService
from services.GlobalSearchService import GlobalSearchService
from services.EmployeeService import EmployeeService
from services.DepartmentService import DepartmentService
from services.TeamService import TeamService
from services.ImportService import ImportService
from services.ExportService import ExportService


# Temporary mock user class until auth is implemented
class AnonymousUser:
    id = None
    email = "anonymous@example.com"
    name = "Anonymous User"
    roles = {"admin"}  # default full access for development



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
def get_current_user(db: Session = Depends(get_db)) -> AnonymousUser:
    """
    Mock version of WorkOS-authenticated user.
    Returns a dummy user so endpoints that require auth still work.
    """
    return AnonymousUser()


# --------------------------------------------------------------------
# Dependency: require_roles()
# --------------------------------------------------------------------
def require_roles(*allowed_roles: str):
    """
    Decorator-style dependency that gates access by role.

    In this stub version, everyone passes through.
    Later, this will inspect the WorkOS roles claim.
    """
    def dep(user: AnonymousUser = Depends(get_current_user)):
        # since we're in dev, allow all
        # but keep the same signature and usage
        return user

    return dep


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
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import AuditLogRouter, GlobalSearchRouter, EmployeeRouter, DepartmentRouter, TeamRouter, ImportRouter, ExportRouter


app = FastAPI(
    title="HRIS System API",
    description="""
Human Resources Information System API for managing employees, departments, teams, and user administration.

## Features

- Users: User authentication and management
- Employees: Employee records and reporting hierarchy
- Departments: Department organization
- Teams: Team management
- Audit Logs: System activity tracking
    """,
    version="1.0.0",
    openapi_tags=[
        {
            "name": "health",
            "description": "Health check and system status endpoints",
        },
        {
            "name": "users",
            "description": "Operations with users. Login, registration, and user management.",
        },
        {
            "name": "employees",
            "description": "Manage employee records, profiles, and reporting hierarchy.",
        },
        {
            "name": "departments",
            "description": "Department management and organization.",
        },
        {
            "name": "teams",
            "description": "Team creation and management.",
        },
        {
            "name": "audit",
            "description": "Audit log operations and system activity tracking.",
        },
        {
            "name": "search",
            "description": "Global search across employees, departments, and teams.",
        },
        {
            "name": "imports",
            "description": "Bulk import operations for employees and other entities.",
        },
        {
            "name": "exports",
            "description": "Export employee data and org charts in various formats (CSV, Excel, PDF).",
        },
    ],
)

origins = [
    "http://localhost:5173",       # local React dev
    "https://deployed-frontend.vercel.app",  # deployed frontend (mock)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health"])
def read_root():
    """Root endpoint - Welcome message"""
    return {"message": "Welcome to HRIS System API"}


@app.get("/health", tags=["health"])
def health_check():
    """
    Health check endpoint
    
    Returns the current health status of the API.
    """
    return {"status": "healthy"}


# Register routers
app.include_router(AuditLogRouter.router)
app.include_router(GlobalSearchRouter.router)
app.include_router(EmployeeRouter.router)
app.include_router(DepartmentRouter.router)
app.include_router(TeamRouter.router)
app.include_router(ImportRouter.router)
app.include_router(ExportRouter.router)

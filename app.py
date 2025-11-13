from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


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


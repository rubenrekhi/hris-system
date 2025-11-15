# HRIS System

A comprehensive Human Resource Information System (HRIS) built with modern web technologies. This application provides core employee management functionality including organizational chart visualization, employee directory, bulk import/export capabilities, and audit logging.

## Features

### Employee Management
- 📋 **Employee Directory** - Searchable, filterable employee list with advanced filtering
- 👤 **Employee Profiles** - Detailed employee information with editing capabilities
- 🌳 **Organizational Chart** - Interactive visual hierarchy showing reporting relationships
- ➕ **Create/Edit Employees** - Form-based employee creation and updates

### Organizational Structure
- 🏢 **Department Management** - Create and manage departments
- 👥 **Team Management** - Organize employees into teams with hierarchy support
- 🔄 **Manager Assignment** - Assign and reassign reporting relationships
- 👔 **CEO Management** - Promote to CEO or replace existing CEO

### Data Operations
- 📥 **Bulk Import** - Import employees from CSV or Excel files with validation
- 📤 **Export** - Export employee data in multiple formats (CSV, Excel, PDF)
  - Directory view export
  - Organizational chart export
- 🔍 **Global Search** - Search across employees, departments, and teams

### System Features
- 📊 **Audit Logging** - Track all changes to employee records
- 📈 **Reports** - View organizational insights and metrics
- ✅ **Data Validation** - Prevent circular hierarchies and enforce business rules

## Tech Stack

### Backend
- **FastAPI** - Modern, fast web framework for building APIs
- **SQLAlchemy** - SQL toolkit and ORM
- **PostgreSQL** - Relational database
- **Alembic** - Database migration tool
- **Pydantic** - Data validation using Python type annotations
- **Pytest** - Testing framework

### Frontend
- **React 19** - UI library with latest features
- **Vite 7** - Next-generation frontend build tool
- **Material-UI (MUI)** - React component library
- **React Router** - Client-side routing
- **JavaScript** - No TypeScript for simplicity

## Prerequisites

- **Python 3.9+** - For backend
- **Node.js 18+** - For frontend
- **PostgreSQL 12+** - Database
- **pip** - Python package manager
- **npm** - Node package manager

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/rubenrekhi/hris-system
cd hris-system
```

### 2. Backend Setup

```bash
# Navigate to server directory
cd server

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://username:password@localhost:5432/hris_db
EOF

# Run database migrations
alembic upgrade head

# Seed database with test data (optional but recommended)
python scripts/seed_database.py
```

### 3. Frontend Setup

```bash
# Navigate to client directory (from root)
cd client

# Install dependencies
npm install

# Create .env file
cat > .env << EOF
VITE_API_URL=http://localhost:8000
EOF
```

## Running the Application

### Start the Backend Server

```bash
cd server
source venv/bin/activate
uvicorn app:app --reload
```

The API will be available at:
- **API Base:** http://localhost:8000
- **Interactive API Docs:** http://localhost:8000/docs
- **Alternative Docs:** http://localhost:8000/redoc

### Start the Frontend Development Server

```bash
cd client
npm run dev
```

The application will be available at:
- **Frontend:** http://localhost:5173

## Project Structure

```
hris-system/
├── server/                 # Backend FastAPI application
│   ├── alembic/           # Database migrations
│   ├── core/              # Core utilities (database, dependencies)
│   ├── models/            # SQLAlchemy ORM models
│   ├── routers/           # API route handlers
│   ├── schemas/           # Pydantic schemas for validation
│   ├── services/          # Business logic layer
│   ├── scripts/           # Utility scripts (seeding, etc.)
│   ├── tests/             # Backend tests
│   ├── app.py             # FastAPI application entry point
│   └── requirements.txt   # Python dependencies
│
├── client/                # Frontend React application
│   ├── src/
│   │   ├── components/   # Reusable React components
│   │   ├── pages/        # Page components (routes)
│   │   ├── services/     # API communication layer
│   │   ├── hooks/        # Custom React hooks
│   │   ├── utils/        # Utility functions
│   │   ├── theme/        # MUI theme configuration
│   │   ├── App.jsx       # Root component with routing
│   │   └── main.jsx      # Application entry point
│   ├── public/           # Static assets
│   └── package.json      # Node dependencies
│
├── CLAUDE.md             # AI assistant guidance
└── README.md             # This file
```

## Key API Endpoints

### Employees
- `GET /employees` - List all employees with filtering
- `POST /employees` - Create new employee
- `GET /employees/{id}` - Get employee details
- `PUT /employees/{id}` - Update employee
- `DELETE /employees/{id}` - Delete employee

### Departments
- `GET /departments` - List all departments
- `POST /departments` - Create new department
- `PUT /departments/{id}` - Update department
- `DELETE /departments/{id}` - Delete department

### Teams
- `GET /teams` - List all teams
- `POST /teams` - Create new team
- `PUT /teams/{id}` - Update team
- `DELETE /teams/{id}` - Delete team

### Import/Export
- `POST /imports/employees` - Bulk import employees (CSV/Excel)
- `GET /exports/employees` - Export employees (CSV/Excel/PDF)

### Search & Audit
- `GET /search` - Global search across all entities
- `GET /audit-logs` - Retrieve audit log entries

For complete API documentation, visit http://localhost:8000/docs when the server is running.

## Development

### Database Management

**Create a new migration after model changes:**
```bash
cd server
alembic revision --autogenerate -m "description of changes"
```

**Apply migrations:**
```bash
alembic upgrade head
```

**Rollback migration:**
```bash
alembic downgrade -1
```

**View migration history:**
```bash
alembic history
```

**Re-seed database:**
```bash
python scripts/seed_database.py --clear
```

### Running Tests

**Backend tests:**
```bash
cd server
source venv/bin/activate

# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=term-missing

# Run specific test file
pytest tests/test_employee_service.py

# Run specific test
pytest tests/test_employee_service.py::test_list_employees

# Run tests by marker
pytest -m unit        # Unit tests (service layer)
pytest -m integration # Integration tests (API endpoints)
```

**Frontend linting:**
```bash
cd client
npm run lint
```

### Building for Production

**Backend:**
```bash
cd server
source venv/bin/activate
# Backend runs with uvicorn (no build step)
```

**Frontend:**
```bash
cd client
npm run build
npm run preview  # Preview production build
```

## Database Schema

### Core Models

**Employee**
- Personal information (name, email, phone, etc.)
- Employment details (hire date, job title, status)
- Self-referential hierarchy (manager_id)
- Relationships to Department and Team

**Department**
- Department information and structure
- Contains many employees

**Team**
- Team information with optional hierarchy
- Contains many employees

**User**
- Authentication and authorization
- 1:1 relationship with Employee

**AuditLog**
- Tracks all entity changes
- Stores previous and new state as JSON
- Links to user who made the change

### Business Rules

- Organization must have exactly one CEO (employee with no manager)
- Employees cannot be their own manager (database constraint)
- No circular manager relationships allowed
- No circular team hierarchies allowed
- All updates and deletes are logged in audit system

## Sample Data

The seed script creates realistic test data:
- **5 departments** (Engineering, Marketing, Sales, HR, Finance)
- **30+ employees** in a 5-level organizational hierarchy
- **10+ teams** with parent-child relationships
- **5 sample users** for authentication testing
- **Audit logs** for all initial data

Run the seeder:
```bash
cd server
python scripts/seed_database.py
```

Clear and re-seed:
```bash
python scripts/seed_database.py --clear
```

## Features in Detail

### Organizational Chart
- Interactive tree visualization of reporting structure
- Click nodes to view employee details
- Expand/collapse branches
- Visual hierarchy representation

### Bulk Import
- Support for CSV and Excel files
- Comprehensive data validation
- Preview before import
- Detailed error reporting
- Create new or update existing employees

### Export Functionality
- Multiple format support (CSV, Excel, PDF)
- View options:
  - Employee directory (list view)
  - Organizational chart (hierarchy view)
  - Department view
- Customizable column selection
- Professional PDF formatting

### Audit System
- Automatic logging of all changes
- Captures before/after state
- User attribution
- Timestamp tracking
- Searchable audit history

## Architecture

This application follows a **layered architecture** pattern:

### Backend Layers
1. **Models** - Database entities (SQLAlchemy ORM)
2. **Services** - Business logic (validation, calculations)
3. **Routers** - API endpoints (request/response handling)
4. **Schemas** - Data validation (Pydantic models)

**Key Pattern:** Services handle business logic but do NOT commit transactions. Routers manage transactions (commit/rollback).

### Frontend Patterns
- **Functional components** with React hooks
- **Custom hooks** for reusable logic (API calls, state management)
- **Service layer** for API communication
- **Component composition** for UI reusability

## Environment Variables

### Backend (`server/.env`)
```
DATABASE_URL=postgresql://user:password@localhost:5432/database_name
```

### Frontend (`client/.env`)
```
VITE_API_URL=http://localhost:8000
```

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running
- Verify DATABASE_URL in server/.env
- Check database exists and user has permissions

### CORS Errors
- Backend has CORS middleware configured
- Verify frontend is running on expected port (5173)
- Check VITE_API_URL in client/.env

### Migration Errors
- Ensure all models are imported in alembic/env.py
- Review generated migration before applying
- Check database is at expected version: `alembic current`

### Port Conflicts
- Backend defaults to port 8000
- Frontend defaults to port 5173 (Vite auto-increments if busy)
- Check terminal output for actual ports

## License

This is a demonstration project for educational purposes.

## Support

For issues or questions:
1. Check the API documentation at http://localhost:8000/docs
2. Review CLAUDE.md for development guidance
3. Inspect browser console and network tab for frontend issues
4. Check server logs for backend errors

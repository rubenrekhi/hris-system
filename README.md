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

### Authentication & Authorization
- 🔐 **WorkOS AuthKit Integration** - Enterprise-grade authentication
- 👥 **Role-Based Access Control (RBAC)** - Three permission levels
  - **Admin** - Full system access (create/edit/delete employees, manage CEO role)
  - **HR** - Employee management access (cannot promote/replace CEO)
  - **Member** - Read-only access to view employees and org structure
- 🔒 **Secure Session Management** - Encrypted HTTP-only cookies
- 🔗 **Automatic User-Employee Linking** - Auto-link users to employee records by email
- 🚪 **Seamless Login/Logout** - Single sign-on with WorkOS AuthKit

## Tech Stack

### Backend
- **FastAPI** - Modern, fast web framework for building APIs
- **SQLAlchemy** - SQL toolkit and ORM
- **PostgreSQL** - Relational database
- **Alembic** - Database migration tool
- **Pydantic** - Data validation using Python type annotations
- **WorkOS** - Authentication and user management
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
- **WorkOS Account** - For authentication (free tier available at [workos.com](https://workos.com))

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/rubenrekhi/hris-system
cd hris-system
```

### 2. WorkOS Setup

1. **Create a WorkOS account** at [dashboard.workos.com](https://dashboard.workos.com)

2. **Set up AuthKit:**
   - In the WorkOS Dashboard, go to **Authentication** → **Set up AuthKit**
   - Follow the setup wizard

3. **Create an organization:**
   - Go to **Organizations** → **Create Organization**
   - Name it (e.g., "hris-system")
   - Note the **Organization ID** (starts with `org_`)

4. **Create roles:**
   - Go to **Roles** → **Create Role**
   - Create three roles:
     - `admin` - Full system access
     - `hr` - Employee management access
     - `member` - Read-only access

5. **Configure redirect URIs:**
   - Go to **Redirects** section
   - Add callback redirect: `http://localhost:8000/auth/callback`
   - Add logout redirect: `http://localhost:5173/login`

6. **Get your credentials:**
   - Go to **API Keys** to find your:
     - **API Key** (starts with `sk_`)
     - **Client ID** (starts with `client_`)
   - Generate a **Cookie Password**:
     ```bash
     openssl rand -base64 24
     ```

### 3. Backend Setup

```bash
# Navigate to server directory
cd server

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your WorkOS credentials
cat > .env << EOF
DATABASE_URL=postgresql://username:password@localhost:5432/hris_db
WORKOS_API_KEY=sk_your_api_key_here
WORKOS_CLIENT_ID=client_your_client_id_here
WORKOS_REDIRECT_URI=http://localhost:8000/auth/callback
WORKOS_ORG_ID=org_your_org_id_here
WORKOS_COOKIE_PASSWORD=your_generated_cookie_password_here
FRONTEND_URL=http://localhost:5173
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

**Note:** All endpoints (except `/auth/login` and health checks) require authentication via WorkOS session cookie.

### Authentication
- `GET /auth/login` - Redirect to WorkOS login
- `GET /auth/callback` - Handle OAuth callback (auto-redirect)
- `GET /auth/logout` - Log out and clear session
- `GET /auth/me` - Get current user information

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

## Production Deployment

### Environment Configuration

When deploying to production (e.g., Vercel, Heroku, AWS), you must set the `ENVIRONMENT` variable to enable production-mode security settings:

**Backend environment variables:**
```bash
# Required for all deployments
DATABASE_URL=postgresql://user:password@host:5432/database_name
WORKOS_API_KEY=sk_your_production_api_key
WORKOS_CLIENT_ID=client_your_production_client_id
WORKOS_ORG_ID=org_your_production_org_id
WORKOS_COOKIE_PASSWORD=your_production_cookie_password

# Production-specific
ENVIRONMENT=production  # CRITICAL: Enables HTTPS-only cookies and cross-domain support
WORKOS_REDIRECT_URI=https://your-backend-domain.com/auth/callback
FRONTEND_URL=https://your-frontend-domain.com
```

**Frontend environment variables:**
```bash
VITE_API_URL=https://your-backend-domain.com
```

### Cross-Domain Deployment

If your frontend and backend are deployed on **different domains** (e.g., frontend on `app.example.com`, backend on `api.example.com`), the `ENVIRONMENT=production` setting is **required** to enable secure cross-domain cookies.

**What happens with `ENVIRONMENT=production`:**
- Cookies use `secure=true` (requires HTTPS)
- Cookies use `samesite=none` (allows cross-domain)
- Both settings are necessary for authentication to work across different domains

**Without this setting:**
- Cookies will use `secure=false` and `samesite=lax` (localhost defaults)
- Authentication will fail in production with redirect loops
- Session cookies won't persist across domains

### WorkOS Production Configuration

Update your WorkOS Dashboard settings for production:

1. **Redirect URIs:**
   - Add production callback: `https://your-backend-domain.com/auth/callback`
   - Add production logout: `https://your-frontend-domain.com/login`

2. **CORS Origins:**
   - Ensure your backend's CORS configuration includes your production frontend URL
   - Update `server/app.py` if needed:
   ```python
   origins = [
       "http://localhost:5173",  # local dev
       "https://your-frontend-domain.com",  # production
   ]
   ```

3. **Environment Variables:**
   - Use production API keys (not test keys)
   - Generate a new `WORKOS_COOKIE_PASSWORD` for production
   - Never commit production secrets to version control

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
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/database_name

# WorkOS Authentication
WORKOS_API_KEY=sk_your_api_key          # From WorkOS Dashboard → API Keys
WORKOS_CLIENT_ID=client_your_client_id  # From WorkOS Dashboard → API Keys
WORKOS_REDIRECT_URI=http://localhost:8000/auth/callback
WORKOS_ORG_ID=org_your_org_id           # From WorkOS Dashboard → Organizations
WORKOS_COOKIE_PASSWORD=your_password    # Generate with: openssl rand -base64 24
FRONTEND_URL=http://localhost:5173

# Optional: Set to "production" when deploying (enables HTTPS cookies and cross-domain support)
# ENVIRONMENT=production
```

### Frontend (`client/.env`)
```bash
VITE_API_URL=http://localhost:8000
```

## Troubleshooting

### Authentication Issues
- **401 Unauthorized errors:**
  - Ensure you're logged in at `http://localhost:8000/auth/login`
  - Check that WorkOS credentials in `.env` are correct
  - Verify cookie is being set (check browser DevTools → Application → Cookies)
- **Redirect loop:**
  - Verify `WORKOS_REDIRECT_URI` matches WorkOS Dashboard redirect URI
  - Check `FRONTEND_URL` in `.env` is correct
- **Cannot assign roles to users:**
  - In WorkOS Dashboard → Users, click on user
  - Assign role (admin, hr, or member) to the user

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

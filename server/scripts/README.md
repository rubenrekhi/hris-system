# Database Seeding Scripts

This directory contains scripts for populating the database with comprehensive test data.

## seed_database.py

A script that populates the database with realistic organizational data for manual testing of all API endpoints.

### Features

- Uses service layer functions (not raw SQL) to ensure all validation rules are enforced
- Creates a complex 5-level employee hierarchy (CEO → VP → Director → Manager → IC)
- Generates 5 departments with teams and employees
- Creates 3-level team substructures
- Includes teams with and without departments
- Creates teams with both direct employees and subteams
- Links sample users to key employees

### Usage

**Activate virtual environment first:**
```bash
source venv/bin/activate
```

**Seed database (preserving existing data):**
```bash
python scripts/seed_database.py
```

**Clear database and seed from scratch:**
```bash
python scripts/seed_database.py --clear
```

### Created Data Structure

#### Departments (5)
- Engineering
- Sales
- Marketing
- Operations
- HR

#### Employees (30+)

**5-Level Hierarchy:**
```
CEO (Jane Smith)
├── VP Engineering (John Doe)
│   ├── Director Backend Engineering (Alice Johnson)
│   │   ├── Backend Engineering Manager (Bob Wilson)
│   │   │   ├── Senior Backend Developer (Carol Martinez)
│   │   │   ├── Backend Developer (David Brown)
│   │   │   ├── Backend Developer (Eve Davis)
│   │   │   └── Junior Backend Developer (Frank Garcia)
│   │   └── API Engineering Manager (Grace Lee)
│   │       ├── Senior API Developer (Henry Chen)
│   │       └── API Developer (Iris Wang)
│   └── Director Frontend Engineering (Jack Taylor)
│       ├── Frontend Engineering Manager (Kate Anderson)
│       │   ├── Senior Frontend Developer (Laura Martinez)
│       │   └── Frontend Developer (Mike Johnson)
│       └── UX Designer (Nina Patel)
│
├── VP Sales (Oliver Thompson)
│   └── Director Sales (Paula White)
│       ├── Sales Manager (Quinn Robinson)
│       │   ├── Sales Representative (Rachel Green)
│       │   ├── Sales Representative (Steve Harris)
│       │   └── Junior Sales Rep (Tina Clark)
│       └── Account Executive (Uma Lewis)
│
├── VP Marketing (Victor Martinez)
│   ├── Marketing Manager (Wendy Scott)
│   │   └── Content Writer (Xavier Adams)
│   └── Social Media Specialist (Yolanda King)
│
├── VP Operations (Zoe Campbell)
│   ├── Operations Manager (Aaron Mitchell)
│   │   └── Operations Analyst (Beth Turner)
│   └── HR Manager (Charlie Evans)
│       └── Recruiter (Diana Parker)
│
└── Special Projects Lead (Emma Collins) [no department]
```

#### Teams (10+)

**3-Level Team Hierarchy:**
```
Engineering (dept: Engineering, lead: VP Engineering)
├── Backend Team (lead: Backend Manager)
│   ├── Direct members: 4 backend developers
│   └── API Team (lead: API Manager)
│       └── Direct members: 2 API developers
└── Frontend Team (lead: Frontend Manager)
    └── Direct members: 2 frontend developers + UX designer

Sales (dept: Sales, lead: VP Sales)
└── Enterprise Sales (lead: Sales Manager)
    └── Direct members: 3 sales representatives

Marketing (dept: Marketing, lead: VP Marketing)
└── Direct members: Marketing Manager + team

Operations (dept: Operations, lead: VP Operations)
└── Direct members: Operations Manager + team

Innovation Lab (no department, cross-functional)
└── Direct members: Various ICs from different departments

Special Projects (no department)
└── Direct members: Special Projects Lead
```

#### Users (5)

Sample user accounts linked to key employees for testing authentication:

| Email | Name | Linked Employee | Role |
|-------|------|-----------------|------|
| jane.smith@company.com | Jane Smith (User) | CEO | Admin |
| john.doe@company.com | John Doe (User) | VP Engineering | Manager |
| alice.johnson@company.com | Alice Johnson (User) | Director Backend | Manager |
| oliver.thompson@company.com | Oliver Thompson (User) | VP Sales | Manager |
| carol.martinez@company.com | Carol Martinez (User) | Senior Backend Dev | Employee |

### Output

The script provides detailed progress information:

```
=== Database Seeding Started ===

Creating departments...
✓ Created department: Engineering
✓ Created department: Sales
...

Creating employees...
✓ Created CEO: Jane Smith
✓ Created VP: John Doe (Engineering)
...

Creating teams...
✓ Created team: Engineering
✓ Created team: Backend Team (parent: Engineering)
...

Creating users...
✓ Created user: jane.smith@company.com → Jane Smith (CEO)
...

=== Seeding Complete ===

Summary:
  Departments: 5
  Employees: 30
  Teams: 10
  Users: 5

Database has been populated with test data!
```

### Resetting the Database

To completely reset and re-seed:

```bash
python scripts/seed_database.py --clear
```

This will:
1. Drop all tables
2. Recreate tables from models
3. Seed with fresh data

**Warning:** This deletes ALL data in the database.

### Testing Endpoints

After seeding, you can test various endpoints with realistic data:

**Employee hierarchy queries:**
```bash
# Get CEO
GET /employees?email=jane.smith@company.com

# Get all direct reports of VP Engineering
GET /employees/{john_doe_id}/direct-reports

# Get organizational chart
GET /employees/org-chart
```

**Department queries:**
```bash
# List all departments
GET /departments

# Get Engineering department with employees
GET /departments/{engineering_id}

# Get department teams
GET /departments/{engineering_id}/teams
```

**Team queries:**
```bash
# Get team hierarchy
GET /teams/{engineering_team_id}/subtree

# Get team members
GET /teams/{backend_team_id}/members

# Get teams with parent-child relationships
GET /teams?parent_team_id={engineering_team_id}
```

### Troubleshooting

**Import errors:**
Make sure you're in the project root directory and the virtual environment is activated:
```bash
cd /path/to/hris-system
source venv/bin/activate
python scripts/seed_database.py
```

**Database connection errors:**
Ensure your `.env` file has the correct `DATABASE_URL`:
```
DATABASE_URL=postgresql://user@localhost:5432/database_name
```

**Validation errors:**
The script uses service layer functions, so all validation rules are enforced. If you see validation errors, it may indicate:
- Database migration issues (run `alembic upgrade head`)
- Corrupt data from previous runs (try `--clear` flag)
- Service layer validation changes

### Development Notes

- Script uses service functions (`EmployeeService`, `DepartmentService`, `TeamService`) to ensure data validity
- All validation rules are enforced (CEO requirement, manager chains, team hierarchies, etc.)
- Data is created in dependency order (departments → CEO → employees top-down → teams → users)
- Transaction is committed only if all data creation succeeds
- If any error occurs, all changes are rolled back

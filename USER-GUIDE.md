# HRIS User Guide

Welcome to the Human Resource Information System (HRIS). This guide will help you understand how to use the application, what you can do, and important rules that govern how the system works.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Navigation](#navigation)
3. [Employee Management](#employee-management)
4. [Organizational Chart](#organizational-chart)
5. [Departments & Teams](#departments--teams)
6. [Bulk Import](#bulk-import)
7. [Reports & Exports](#reports--exports)
8. [Search](#search)
9. [Audit Logs](#audit-logs)
10. [Business Rules & Constraints](#business-rules--constraints)
11. [Frequently Asked Questions](#frequently-asked-questions)

---

## Getting Started

### Accessing the Application

The HRIS application is accessible through your web browser at the designated URL. The system provides a clean, modern interface for managing your organization's employee data.

### Main Interface

The application uses a navigation header at the top with the following main sections:
- **Home** - Global search across all employees, departments, and teams
- **Directory** - Browse and manage all employees
- **Org Chart** - Visual organizational hierarchy
- **Departments** - Manage departments and teams
- **Reports** - Export data in various formats
- **Management** - Administrative operations
- **Audits** - View system change history

---

## Navigation

### Using Modals

The application uses modal windows (pop-up dialogs) for viewing and editing details. When you click on an employee, department, or team, a modal will open showing detailed information. You can:
- **View** - See all details about the selected item
- **Edit** - Click the Edit button to modify information
- **Delete** - Remove the item (with confirmation)
- **Navigate** - Click on related items (like a manager or department) to open their details

### Clickable Links

Throughout the application, you'll see clickable links for:
- Employee names
- Manager names
- Department names
- Team names

Clicking these will open a detail modal for that item, making it easy to navigate between related information.

---

## Employee Management

### Viewing the Employee Directory

Navigate to **Directory** to see all employees in the organization.

**Features:**
- **Pagination** - Browse through employees (default: 20 per page)
- **Search** - Search by employee name or email
- **Filters** - Filter by:
  - Department
  - Team
  - Employment status (Active or On Leave)
  - Salary range (minimum and maximum)

**Employee Information Displayed:**
- Name
- Email
- Job title
- Department
- Team
- Manager
- Employment status
- Hire date
- Salary

### Viewing Employee Details

Click on any employee to see their full profile, including:
- Basic information (name, email, title)
- Employment details (status, hire date, salary)
- Organizational placement (department, team, manager)
- Direct reports (employees who report to them)

### Creating a New Employee

Two ways to add employees:

**Option 1: Individual Entry**
1. Go to **Management** → **Create Employee**
2. Fill in the required information:
   - **Name** (required)
   - **Email** (required, must be unique)
   - Job title
   - Department
   - Team
   - Manager (required for all non-CEO employees)
   - Hire date
   - Salary
   - Status (Active or On Leave)
3. Click **Create**

**Option 2: Bulk Import**
See the [Bulk Import](#bulk-import) section for importing multiple employees at once.

### Editing Employee Information

1. Click on an employee to open their detail modal
2. Click the **Edit** button
3. Modify the information you want to change:
   - Name
   - Job title
   - Salary
   - Employment status
   - Department assignment
   - Team assignment
   - Manager assignment
4. Click **Save** to apply changes or **Cancel** to discard

**Note:** Email addresses cannot be changed after an employee is created.

### Deleting an Employee

1. Click on an employee to open their detail modal
2. Click the **Delete** button
3. Confirm the deletion

**Important:**
- When you delete an employee, their direct reports will be automatically reassigned to that employee's manager
- You cannot delete the CEO directly (see [Managing the CEO](#managing-the-ceo))

### Managing the CEO

Every organization must have exactly one CEO - an employee with no manager who sits at the top of the organizational hierarchy.

**Promoting an Existing Employee to CEO:**
1. Go to **Management** → **Promote to CEO**
2. Select the employee you want to promote
3. Confirm the promotion

**What happens:**
- The selected employee becomes the new CEO (their manager is removed)
- If they had a manager who was the CEO, they inherit all of the CEO's direct reports
- If they had a different manager, their direct reports are reassigned to their original manager, and they inherit all of the CEO's reports

**Replacing the CEO with a New Employee:**
1. Go to **Management** → **Replace CEO**
2. Enter the new CEO's information (name, email, title, etc.)
3. Click **Create**

**What happens:**
- A new employee is created as the CEO
- The previous CEO becomes a direct report of the new CEO
- All other direct reports of the old CEO remain as direct reports of the new CEO

**Important Constraints:**
- You must always have exactly one CEO
- You cannot delete the CEO without first promoting someone else or creating a replacement
- The CEO is the only employee who doesn't have a manager

### Unassigned Employees

Employees can exist without being assigned to a department or team. To view these employees:
- Navigate to the Departments Page
- View under "Unassigned Employees"

---

## Organizational Chart

### Viewing the Org Chart

Navigate to **Org Chart** to see a visual representation of your organization's reporting structure.

**Features:**
- **Hierarchical Tree View** - Shows CEO at the top with all reporting relationships
- **Expandable Nodes** - Click to expand/collapse employee nodes to show/hide their direct reports
- **Clickable Employees** - Click any employee to see their details
- **Visual Layout** - Automatically arranges the hierarchy for easy viewing

**Understanding the Chart:**
- The CEO appears at the top
- Lines connect each employee to their manager
- Employees at the same level report to the same manager
- The depth of the tree shows how many management levels exist

### Navigating the Chart

- **Click** on an employee to open their detail modal
- **Expand/Collapse** sections to focus on specific parts of the organization
- Use the detail modal to navigate to related employees (manager, direct reports)

---

## Departments & Teams

### Understanding Departments and Teams

**Departments** are top-level organizational units (e.g., Engineering, Sales, HR).

**Teams** are groups within departments that can have hierarchical relationships (e.g., Frontend Team within Engineering, with Web Platform as a child team).

### Viewing Departments

Navigate to **Departments** to see all departments in the organization.

**Information Shown:**
- Department name
- Number of teams in the department
- Number of employees in the department

### Creating a Department

1. Go to **Management** → **Create Department**
2. Enter the department name (must be unique)
3. Click **Create**

### Editing a Department

1. Click on a department to open its detail modal
2. Click **Edit**
3. Change the department name
4. Click **Save**

### Deleting a Department

1. Click on a department to open its detail modal
2. Click **Delete**
3. Confirm the deletion

**What happens:**
- All employees in that department will have their department assignment removed
- All teams in that department will have their department assignment removed
- The employees and teams still exist, just unassigned

### Viewing Teams

In the **Departments** section, you can:
- View all teams within a department
- See team hierarchies (parent and child teams)
- View team members

### Creating a Team

1. Go to **Management** → **Create Team**
2. Enter:
   - **Team name** (required)
   - **Department** (optional)
   - **Parent team** (optional, must be in the same department)
   - **Team lead** (optional, employee assigned as the leader)
3. Click **Create**

### Team Hierarchy

Teams can have parent-child relationships, creating sub-teams:
- A team can have one parent team
- A team can have multiple child teams
- Parent and child teams must be in the same department
- You cannot create circular hierarchies (Team A → Team B → Team A)

**Example Structure:**
```
Engineering Department
├── Frontend Team
│   ├── Web Platform Team
│   └── Mobile Team
└── Backend Team
    └── API Team
```

### Editing a Team

1. Click on a team to open its detail modal
2. Click **Edit**
3. Modify:
   - Team name
   - Department assignment
   - Parent team
   - Team lead
4. Click **Save**

### Deleting a Team

1. Click on a team to open its detail modal
2. Click **Delete**
3. Confirm the deletion

**What happens:**
- All employees on that team will have their team assignment removed
- Child teams of the deleted team will have their parent team assignment removed
- Employees and child teams still exist, just unassigned

### Team Leads

You can assign an employee as a team lead:
- The employee must be on the same team
- If you reassign the team lead to another team, they will automatically be removed as the lead
- A team can have zero or one team lead

### Unassigned Teams

Teams can exist without being assigned to a department or having a parent team. These are "root-level" teams.

---

## Bulk Import

The bulk import feature allows you to upload multiple employees at once from a CSV or Excel file.

### Preparing Your Import File

**Supported Formats:**
- CSV (.csv)
- Excel (.xlsx)

**File Size Limit:** 10 MB maximum

**Required Column:**
- `name` - Employee's full name

**Optional Columns:**
- `email` - Email address (must be unique if provided)
- `job_title` - Job title
- `department_name` - Name of the department
- `team_name` - Name of the team
- `manager_email` - Email of the employee's manager
- `hire_date` - Hire date (format: YYYY-MM-DD)
- `salary` - Salary amount (integer)
- `status` - Employment status (ACTIVE or ON_LEAVE)

**Example CSV:**
```csv
name,email,job_title,department_name,team_name,manager_email,hire_date,salary,status
John Doe,john@company.com,CEO,,,2020-01-01,200000,ACTIVE
Jane Smith,jane@company.com,CTO,Engineering,,john@company.com,2020-02-01,180000,ACTIVE
Bob Johnson,bob@company.com,Senior Engineer,Engineering,Backend Team,jane@company.com,2021-03-15,120000,ACTIVE
```

### How Import Works

**Validation First:**
The system validates all rows before importing any data. If any row has errors, nothing is imported.

**Manager Dependencies:**
The system automatically resolves manager relationships:
- Managers are created before their direct reports
- Circular manager relationships are detected and rejected
- If a manager doesn't exist, they will be created from the import file

**Department and Team Matching:**
- Departments and teams are matched by name (case-sensitive)
- If a department or team doesn't exist, the import will fail
- Create departments and teams before importing employees assigned to them

**User Account Linking:**
If a user account exists with the same email as an imported employee, they will be automatically linked.

### Importing Employees

1. Go to **Management** → **Bulk Import**
2. Click **Choose File** and select your CSV or Excel file
3. Click **Upload**
4. Wait for validation and import to complete

**Success:**
- You'll see a confirmation message
- All employees from the file are created
- You can navigate to the Directory to see them

**Failure:**
- You'll see an error message
- No employees are created
- You can download an error report showing which rows failed and why
- Fix the errors in your file and try again

### Common Import Errors

- **Duplicate email** - An employee with that email already exists
- **Invalid status** - Status must be ACTIVE or ON_LEAVE
- **Invalid date format** - Use YYYY-MM-DD
- **Department not found** - Create the department first
- **Team not found** - Create the team first
- **Circular manager relationship** - Manager dependencies form a loop
- **Invalid salary** - Must be a number
- **File too large** - Maximum 10 MB
- **Unsupported format** - Only CSV and Excel (.xlsx) are supported

### Tips for Successful Imports

1. **Start with the CEO** - Include the CEO (employee with no manager) in your import file (ONLY if you do not already have a CEO in the system)
2. **Create departments and teams first** - Make sure they exist before importing employees
3. **Use consistent emails** - Emails are the primary way to link managers to reports
4. **Check for duplicates** - Don't include employees who already exist in the system
5. **Validate your data** - Double-check dates, emails, and status values
6. **Test with a small file** - Import a few employees first to verify your format
7. **Review error reports** - If import fails, download the error report for specific issues

---

## Reports & Exports

The system allows you to export employee data in multiple formats for reporting and analysis.

### Export Formats

**CSV** - Simple text format, can be opened in Excel or any spreadsheet program

**Excel (.xlsx)** - Formatted spreadsheet with proper column widths and styling

**PDF** - Print-ready document with formatted tables

### Export Types

Navigate to **Reports** to access export options.

**Directory Export:**
- Exports a flat list of employees
- Includes: name, email, title, department, team, manager, status, hire date, salary
- Go to **Reports** → **Directory Export**

**Org Chart Export:**
- Exports the organizational hierarchy
- CSV/Excel include hierarchy levels and reporting paths
- PDF includes a visual organizational chart
- Go to **Reports** → **Org Chart Export**

### Export Filters

You can filter what data to export:

**Department Filter** - Export only employees in a specific department

**Team Filter** - Export only employees on a specific team

**Status Filter** - Export only Active or On Leave employees

**Hire Date Range** - Export employees hired between specific dates

**Example Uses:**
- Export all Engineering department employees
- Export only active employees
- Export employees hired in the last year
- Export a specific team for review

### Generating an Export

1. Navigate to **Reports**
2. Choose export type (Directory or Org Chart)
3. Select format (CSV, Excel, or PDF)
4. Apply any filters (optional)
5. Click **Export**
6. The file will download to your computer

### API Export Endpoints

For programmatic access, the following API endpoints are available:

**Directory Exports:**
- `GET /exports/directory/csv` - CSV format
- `GET /exports/directory/excel` - Excel format
- `GET /exports/directory/pdf` - PDF format

**Org Chart Exports:**
- `GET /exports/org-chart/csv` - CSV with hierarchy
- `GET /exports/org-chart/excel` - Excel with formatting
- `GET /exports/org-chart/pdf` - Visual PDF chart

**Query Parameters for Filtering:**
- `department_id` - Filter by department
- `team_id` - Filter by team
- `status` - Filter by status (ACTIVE or ON_LEAVE)
- `hired_from` - Start date for hire date range (YYYY-MM-DD)
- `hired_to` - End date for hire date range (YYYY-MM-DD)

---

## Search

### Global Search

The **Home** page provides a global search feature that searches across:
- **Employees** (by name or email)
- **Departments** (by name)
- **Teams** (by name)

**How to Use:**
1. Navigate to **Home**
2. Type in the search box
3. Results appear as you type (with a short delay to improve performance)
4. Click on any result to open its detail modal

### Directory Search and Filters

The **Directory** page provides more advanced search and filtering:

**Search:** Type to search employee names and emails

**Filters:**
- **Department** - Filter by specific department
- **Team** - Filter by specific team
- **Status** - Active or On Leave
- **Salary Range** - Minimum and maximum salary

**Combining Filters:**
You can use multiple filters together (e.g., Engineering department + Active status + Salary between $80,000-$120,000)

---

## Audit Logs

The audit log tracks all changes made in the system for accountability and compliance.

**Note:** Viewing audit logs requires administrator access.

### What is Tracked

Every create, update, and delete operation is logged:

**Employee Changes:**
- Creating new employees
- Updating employee information (name, title, salary, status, etc.)
- Changing department, team, or manager assignments
- Deleting employees

**Department Changes:**
- Creating departments
- Renaming departments
- Deleting departments

**Team Changes:**
- Creating teams
- Updating team information
- Changing team hierarchy
- Deleting teams

**CEO Changes:**
- Promoting an employee to CEO
- Replacing the CEO

### Viewing Audit Logs

Navigate to **Audits** to see the change history.

**Information Shown:**
- **Action Type** - CREATE, UPDATE, or DELETE
- **Entity Type** - Employee, Department, or Team
- **Entity ID** - The ID of the changed item
- **Changed By** - Who made the change
- **Changed At** - When the change occurred
- **Previous State** - What the data looked like before
- **New State** - What the data looks like after

### Filtering Audit Logs

You can filter the audit log by:
- **Entity Type** - Show only employee, department, or team changes
- **Entity ID** - Show changes to a specific item
- **Action Type** - Show only creates, updates, or deletes
- **User** - Show changes made by a specific user
- **Date Range** - Show changes within a time period

### Viewing Audit Details

Click on any audit log entry to see:
- Full before and after state comparison
- Specific fields that changed
- Complete timestamp and user information

---

## Business Rules & Constraints

Understanding these rules will help you use the system effectively and avoid errors.

### Organizational Hierarchy Rules

1. **One CEO Required**
   - The organization must always have exactly one CEO
   - The CEO is the only employee without a manager
   - You cannot delete the CEO without promoting/replacing them first

2. **Manager Relationships**
   - All employees except the CEO must have a manager
   - An employee cannot be their own manager
   - You cannot create circular reporting relationships (A reports to B, B reports to A)

3. **Deleting Employees**
   - When you delete an employee, their direct reports are reassigned to that employee's manager
   - The CEO cannot be deleted directly

### Department Rules

1. **Unique Names** - Department names must be unique across the organization

2. **Deletion Effects** - Deleting a department:
   - Removes the department assignment from all employees
   - Removes the department assignment from all teams
   - Does not delete employees or teams

### Team Rules

1. **Team Hierarchy**
   - Teams can have parent-child relationships
   - A team can only have one parent team
   - You cannot create circular team hierarchies
   - Parent and child teams must be in the same department

2. **Team Leads**
   - An employee can be designated as team lead
   - The team lead must be a member of the team
   - If a team lead is reassigned to another team, they are automatically removed as lead

3. **Department Consistency**
   - If a team has a parent team, they must be in the same department
   - If an employee is on a team, they should be in the same department as the team

4. **Deletion Effects** - Deleting a team:
   - Removes the team assignment from all employees
   - Removes the parent team from all child teams
   - Does not delete employees or child teams

### Data Validation Rules

1. **Email Addresses**
   - Must be unique across all employees
   - Cannot be changed after an employee is created
   - Used to link employees to user accounts

2. **Required Fields**
   - **Employee**: name, email
   - **Department**: name
   - **Team**: name

3. **Employment Status**
   - Must be either ACTIVE or ON_LEAVE
   - Case-sensitive

4. **Dates**
   - Must be in YYYY-MM-DD format
   - Example: 2024-01-15

5. **Salary**
   - Must be a whole number (integer)
   - No decimal points

### Import Constraints

1. **File Size** - Maximum 10 MB per upload

2. **All-or-Nothing** - If any row fails validation, no employees are imported

3. **Manager Dependencies** - Managers must be included in the import file or already exist in the system

4. **Department/Team Existence** - Referenced departments and teams must already exist

### Export Limitations

1. **Format Support** - Only CSV, Excel (.xlsx), and PDF formats

2. **Filter Combinations** - You can apply multiple filters, but they work with AND logic (all conditions must match)

---

## Frequently Asked Questions

### General Questions

**Q: Can I undo a change I made?**
A: The system does not have a built-in undo feature, but all changes are logged in the Audit Logs. You can view what changed and manually revert it if needed.

**Q: Why can't I see certain features?**
A: Some features require specific permissions (HR or Admin access). Check with your system administrator.

**Q: Can I export a partial organizational chart?**
A: Yes, use the filters when exporting to limit the data to a specific department, team, or employee status.

### Employee Management

**Q: What happens to an employee's direct reports when I delete them?**
A: Their direct reports are automatically reassigned to the deleted employee's manager.

**Q: Can I change an employee's email address?**
A: No, email addresses cannot be changed after creation. If needed, delete the employee and create a new one.

**Q: Can an employee have no manager?**
A: Only the CEO can have no manager. All other employees must have a manager assigned.

**Q: Can I create an employee without assigning them to a department or team?**
A: Yes, department and team assignments are optional. Employees can exist unassigned.

### CEO Management

**Q: Can I have multiple CEOs?**
A: No, the organization must have exactly one CEO at all times.

**Q: What's the difference between promoting someone to CEO vs. replacing the CEO?**
A: Promoting makes an existing employee the CEO. Replacing creates a brand new employee as CEO and makes the old CEO report to them.

**Q: Can I delete the CEO?**
A: No, you must first promote another employee to CEO or create a replacement, then the former CEO can be deleted as a regular employee.

### Department & Team Management

**Q: What's the difference between a department and a team?**
A: Departments are top-level organizational units. Teams are groups that can exist within departments and have hierarchical relationships (parent/child teams).

**Q: Can a team belong to multiple departments?**
A: No, a team can only belong to one department.

**Q: Can a team exist without a department?**
A: Yes, teams can exist without being assigned to a department.

**Q: What happens if I delete a department that has teams?**
A: The teams will have their department assignment removed but will not be deleted.

### Bulk Import

**Q: Can I update existing employees via bulk import?**
A: No, the bulk import feature only creates new employees. It will fail if any email in the import file already exists.

**Q: Why did my import fail?**
A: Download the error report to see specific errors for each row. Common issues include duplicate emails, missing departments/teams, or invalid data formats.

**Q: Do I need to import employees in a specific order?**
A: No, the system automatically resolves manager dependencies and imports in the correct order.

**Q: Can I import departments and teams via CSV?**
A: No, currently only employees can be bulk imported. Create departments and teams individually first.

**Q: What if my import file has more than 10 MB of data?**
A: Split the file into smaller chunks and import them separately.

### Search & Reporting

**Q: Can I search for employees by salary?**
A: Not in the global search, but you can use the salary range filter in the Employee Directory.

**Q: Can I export only specific employees?**
A: You can filter by department, team, status, or hire date range before exporting.

**Q: What format should I use for exporting?**
A: CSV for data analysis, Excel for formatted spreadsheets, PDF for printing or presentations.

**Q: Can I schedule regular exports?**
A: The web interface doesn't support scheduling, but you can use the API endpoints to automate exports programmatically.

### Audit Logs

**Q: Who can view audit logs?**
A: Only users with administrator access can view audit logs.

**Q: How long are audit logs kept?**
A: Audit logs are kept indefinitely in the system.

**Q: Can I export audit logs?**
A: Not through the UI currently, but you can use the API endpoint `GET /audit-logs` to retrieve audit data programmatically.

---

## Additional Resources

### API Documentation

For developers or advanced users who want to interact with the system programmatically, full API documentation is available at:

**`https://hric-system-rubenrekhi-rubenrekhis-projects.vercel.app/docs`** 

This interactive documentation shows:
- All available endpoints
- Required and optional parameters
- Request/response formats
- Example requests you can test directly

### Common API Endpoints

**Employees:**
- `GET /employees` - List all employees with filters
- `POST /employees` - Create new employee
- `GET /employees/{id}` - Get employee details
- `PATCH /employees/{id}` - Update employee
- `DELETE /employees/{id}` - Delete employee

**Departments:**
- `GET /departments` - List all departments
- `POST /departments` - Create department
- `PATCH /departments/{id}` - Update department
- `DELETE /departments/{id}` - Delete department

**Teams:**
- `GET /teams` - List all teams with filters
- `POST /teams` - Create team
- `PATCH /teams/{id}` - Update team
- `DELETE /teams/{id}` - Delete team

**Import/Export:**
- `POST /imports/employees` - Bulk import employees
- `GET /exports/directory/{format}` - Export employee directory
- `GET /exports/org-chart/{format}` - Export org chart

**Search:**
- `GET /search` - Global search across entities

**Audit:**
- `GET /audit-logs` - List audit logs with filters

### Support

For technical issues, feature requests, or questions not covered in this guide, please contact your system administrator.

---

## Glossary

**CEO** - Chief Executive Officer, the top employee in the organization with no manager

**Direct Reports** - Employees who report directly to a specific manager

**Org Chart** - Organizational Chart, a visual representation of the reporting hierarchy

**Department** - Top-level organizational unit (e.g., Engineering, Sales, HR)

**Team** - Group of employees within a department, can have hierarchical structure

**Team Lead** - Employee designated as the leader of a team

**Audit Log** - Record of all changes made in the system

**Bulk Import** - Uploading multiple employees at once from a file

**Manager** - The employee that another employee reports to

**Status** - Employment status, either ACTIVE or ON_LEAVE

**Circular Relationship** - Invalid situation where A reports to B, and B reports to A (or longer chains)

**Root Team** - A team with no parent team

**Unassigned** - Employees or teams not assigned to a department

---

*Last Updated: 2025*
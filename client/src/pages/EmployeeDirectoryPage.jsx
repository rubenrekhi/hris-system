import { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Alert,
  Collapse,
  IconButton,
  InputAdornment,
  Chip,
  Link,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import FilterListIcon from '@mui/icons-material/FilterList';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import { employeeService, departmentService, teamService } from '@/services';
import { cache } from '@/utils/cache';
import DetailModal from '@/components/common/DetailModal';
import EmployeeDetail from '@/components/employees/EmployeeDetail';
import TeamDetail from '@/components/teams/TeamDetail';
import DepartmentDetail from '@/components/departments/DepartmentDetail';

export default function EmployeeDirectoryPage() {
  // Employees data
  const [employees, setEmployees] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Pagination
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [teamFilter, setTeamFilter] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState('');
  const [filtersOpen, setFiltersOpen] = useState(true);

  // Filter options
  const [departments, setDepartments] = useState([]);
  const [teams, setTeams] = useState([]);
  const [departmentsLoading, setDepartmentsLoading] = useState(false);
  const [teamsLoading, setTeamsLoading] = useState(false);

  // Modal state for detail views
  const [selectedEmployeeId, setSelectedEmployeeId] = useState(null);
  const [selectedTeamId, setSelectedTeamId] = useState(null);
  const [selectedDepartmentId, setSelectedDepartmentId] = useState(null);

  // Edit mode state for modals
  const [employeeEditMode, setEmployeeEditMode] = useState(false);
  const [employeeSaving, setEmployeeSaving] = useState(false);
  const [teamEditMode, setTeamEditMode] = useState(false);
  const [teamSaving, setTeamSaving] = useState(false);
  const [deptEditMode, setDeptEditMode] = useState(false);
  const [deptSaving, setDeptSaving] = useState(false);

  // Refs to detail components
  const employeeDetailRef = useRef();
  const teamDetailRef = useRef();
  const deptDetailRef = useRef();

  // Load departments and teams for filter dropdowns
  useEffect(() => {
    const loadFilterOptions = async () => {
      // Load departments - check cache first
      const cachedDepartments = cache.get('departments');
      if (cachedDepartments) {
        // Use cached data, no loading state needed
        setDepartments(cachedDepartments.items || []);
      } else {
        // Fetch from API if not cached
        setDepartmentsLoading(true);
        try {
          const deptData = await departmentService.listDepartments({ limit: 100 });
          setDepartments(deptData.items || []);
          cache.set('departments', deptData);
        } catch (err) {
          console.error('Failed to load departments:', err);
        } finally {
          setDepartmentsLoading(false);
        }
      }

      // Load teams - check cache first
      const cachedTeams = cache.get('teams');
      if (cachedTeams) {
        // Use cached data, no loading state needed
        setTeams(cachedTeams.items || []);
      } else {
        // Fetch from API if not cached
        setTeamsLoading(true);
        try {
          const teamData = await teamService.listTeams({ limit: 100 });
          setTeams(teamData.items || []);
          cache.set('teams', teamData);
        } catch (err) {
          console.error('Failed to load teams:', err);
        } finally {
          setTeamsLoading(false);
        }
      }
    };

    loadFilterOptions();
  }, []);

  // Load employees with debouncing for search
  useEffect(() => {
    // Only debounce when user is actively searching
    // Skip debounce for initial load and filter changes (instant feedback)
    const shouldDebounce = searchQuery.trim().length > 0;

    if (shouldDebounce) {
      const timer = setTimeout(() => {
        loadEmployees();
      }, 300); // 300ms debounce for search
      return () => clearTimeout(timer);
    } else {
      // No debounce for initial load or when clearing search
      loadEmployees();
    }
  }, [page, rowsPerPage, searchQuery, statusFilter, teamFilter, departmentFilter]);

  const loadEmployees = async () => {
    // Check if we can use cached data for first page with no filters
    const isFirstPageNoFilters =
      page === 0 &&
      rowsPerPage === 25 &&
      !searchQuery.trim() &&
      !statusFilter &&
      !teamFilter &&
      !departmentFilter;

    if (isFirstPageNoFilters) {
      const cachedEmployees = cache.get('employees_page_0');
      if (cachedEmployees) {
        // Use cached data instantly, no loading state
        setEmployees(cachedEmployees.items || []);
        setTotal(cachedEmployees.total || 0);
        return;
      }
    }

    // Fetch from API
    setLoading(true);
    setError(null);

    try {
      const params = {
        limit: rowsPerPage,
        offset: page * rowsPerPage,
      };

      // Add search query (for both name and email)
      if (searchQuery.trim()) {
        params.name = searchQuery.trim();
        params.email = searchQuery.trim();
      }

      // Add filters
      if (statusFilter) {
        params.status = statusFilter;
      }
      if (teamFilter) {
        params.team_id = teamFilter;
      }
      if (departmentFilter) {
        params.department_id = departmentFilter;
      }

      const data = await employeeService.listEmployees(params);
      setEmployees(data.items || []);
      setTotal(data.total || 0);

      // Cache first page with no filters
      if (isFirstPageNoFilters) {
        cache.set('employees_page_0', data);
      }
    } catch (err) {
      setError(err.message);
      setEmployees([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0); // Reset to first page
  };

  const handleClearFilters = () => {
    setSearchQuery('');
    setStatusFilter('');
    setTeamFilter('');
    setDepartmentFilter('');
    setPage(0);
  };

  // Handle navigation between modals
  const handleNavigate = (type, id) => {
    if (type === 'employee') {
      setSelectedEmployeeId(id);
    } else if (type === 'team') {
      setSelectedTeamId(id);
    } else if (type === 'department') {
      setSelectedDepartmentId(id);
    }
  };

  // Employee modal edit handlers
  const handleEmployeeEdit = () => {
    employeeDetailRef.current?.enterEditMode();
    setEmployeeEditMode(true);
  };

  const handleEmployeeSave = async () => {
    try {
      setEmployeeSaving(true);
      await employeeDetailRef.current?.save();
      setEmployeeEditMode(false);
    } catch (err) {
      // Error is handled by the detail component
    } finally {
      setEmployeeSaving(false);
    }
  };

  const handleEmployeeCancel = () => {
    employeeDetailRef.current?.cancel();
    setEmployeeEditMode(false);
  };

  // Team modal edit handlers
  const handleTeamEdit = () => {
    teamDetailRef.current?.enterEditMode();
    setTeamEditMode(true);
  };

  const handleTeamSave = async () => {
    try {
      setTeamSaving(true);
      await teamDetailRef.current?.save();
      setTeamEditMode(false);
    } catch (err) {
      // Error is handled by the detail component
    } finally {
      setTeamSaving(false);
    }
  };

  const handleTeamCancel = () => {
    teamDetailRef.current?.cancel();
    setTeamEditMode(false);
  };

  // Department modal edit handlers
  const handleDeptEdit = () => {
    deptDetailRef.current?.enterEditMode();
    setDeptEditMode(true);
  };

  const handleDeptSave = async () => {
    try {
      setDeptSaving(true);
      await deptDetailRef.current?.save();
      setDeptEditMode(false);
    } catch (err) {
      // Error is handled by the detail component
    } finally {
      setDeptSaving(false);
    }
  };

  const handleDeptCancel = () => {
    deptDetailRef.current?.cancel();
    setDeptEditMode(false);
  };

  // Delete handlers
  const handleEmployeeDelete = () => {
    employeeDetailRef.current?.delete();
  };

  const handleEmployeeDeleteSuccess = () => {
    setSelectedEmployeeId(null);
    setEmployeeEditMode(false);
    loadEmployees(); // Refresh the list
  };

  const handleTeamDelete = () => {
    teamDetailRef.current?.delete();
  };

  const handleTeamDeleteSuccess = () => {
    setSelectedTeamId(null);
    setTeamEditMode(false);
    loadEmployees(); // Refresh the list
  };

  const handleDeptDelete = () => {
    deptDetailRef.current?.delete();
  };

  const handleDeptDeleteSuccess = () => {
    setSelectedDepartmentId(null);
    setDeptEditMode(false);
    loadEmployees(); // Refresh the list
  };

  // Count active filters
  const activeFilterCount =
    (searchQuery ? 1 : 0) +
    (statusFilter ? 1 : 0) +
    (teamFilter ? 1 : 0) +
    (departmentFilter ? 1 : 0);

  return (
    <Box sx={{ px: 3, py: 2 }}>
      {/* Page Title */}
      <Typography variant="h3" component="h1" gutterBottom sx={{ mb: 3 }}>
        Employee Directory
      </Typography>

      {/* Filters Panel */}
      <Paper sx={{ mb: 3, backgroundColor: 'background.paper' }}>
        {/* Filter Header */}
        <Box
          sx={{
            px: 2,
            py: 1.5,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            cursor: 'pointer',
            backgroundColor: 'rgba(144, 202, 249, 0.08)',
          }}
          onClick={() => setFiltersOpen(!filtersOpen)}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <FilterListIcon />
            <Typography variant="h6">Filters</Typography>
            {activeFilterCount > 0 && (
              <Chip
                label={activeFilterCount}
                size="small"
                color="primary"
                sx={{ ml: 1 }}
              />
            )}
          </Box>
          <IconButton size="small">
            {filtersOpen ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>

        {/* Filter Controls */}
        <Collapse in={filtersOpen}>
          <Box sx={{ p: 2 }}>
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: {
                  xs: '1fr',
                  sm: 'repeat(2, 1fr)',
                  md: 'repeat(4, 1fr)',
                },
                gap: 2,
              }}
            >
              {/* Search Field */}
              <TextField
                fullWidth
                label="Search"
                placeholder="Name or email"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
              />

              {/* Status Filter */}
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  label="Status"
                >
                  <MenuItem value="">
                    <em>All</em>
                  </MenuItem>
                  <MenuItem value="ACTIVE">Active</MenuItem>
                  <MenuItem value="ON_LEAVE">On Leave</MenuItem>
                </Select>
              </FormControl>

              {/* Department Filter */}
              <FormControl fullWidth>
                <InputLabel>Department</InputLabel>
                <Select
                  value={departmentFilter}
                  onChange={(e) => setDepartmentFilter(e.target.value)}
                  label="Department"
                  disabled={departmentsLoading}
                >
                  <MenuItem value="">
                    <em>All</em>
                  </MenuItem>
                  {departments.map((dept) => (
                    <MenuItem key={dept.id} value={dept.id}>
                      {dept.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Team Filter */}
              <FormControl fullWidth>
                <InputLabel>Team</InputLabel>
                <Select
                  value={teamFilter}
                  onChange={(e) => setTeamFilter(e.target.value)}
                  label="Team"
                  disabled={teamsLoading}
                >
                  <MenuItem value="">
                    <em>All</em>
                  </MenuItem>
                  {teams.map((team) => (
                    <MenuItem key={team.id} value={team.id}>
                      {team.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>

            {/* Clear Filters Button */}
            {activeFilterCount > 0 && (
              <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
                <Typography
                  variant="body2"
                  sx={{
                    color: 'primary.main',
                    cursor: 'pointer',
                    '&:hover': { textDecoration: 'underline' },
                  }}
                  onClick={handleClearFilters}
                >
                  Clear all filters
                </Typography>
              </Box>
            )}
          </Box>
        </Collapse>
      </Paper>

      {/* Error State */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Employee Table */}
      <Paper sx={{ backgroundColor: 'background.paper' }}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Email</TableCell>
                <TableCell>Title</TableCell>
                <TableCell>Department</TableCell>
                <TableCell>Team</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {/* Loading State */}
              {loading && (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              )}

              {/* Empty State */}
              {!loading && employees.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                    <Typography variant="body1" color="text.secondary">
                      No employees found
                    </Typography>
                  </TableCell>
                </TableRow>
              )}

              {/* Employee Rows */}
              {!loading &&
                employees.map((employee) => (
                  <TableRow key={employee.id} hover>
                    <TableCell>
                      <Link
                        component="button"
                        variant="body2"
                        onClick={() => setSelectedEmployeeId(employee.id)}
                        sx={{ textAlign: 'left' }}
                      >
                        {employee.name}
                      </Link>
                    </TableCell>
                    <TableCell>{employee.email}</TableCell>
                    <TableCell>{employee.title || '—'}</TableCell>
                    <TableCell>
                      {employee.department_id ? (
                        <Link
                          component="button"
                          variant="body2"
                          onClick={() => setSelectedDepartmentId(employee.department_id)}
                          sx={{ textAlign: 'left' }}
                        >
                          {employee.department_name}
                        </Link>
                      ) : (
                        '—'
                      )}
                    </TableCell>
                    <TableCell>
                      {employee.team_id ? (
                        <Link
                          component="button"
                          variant="body2"
                          onClick={() => setSelectedTeamId(employee.team_id)}
                          sx={{ textAlign: 'left' }}
                        >
                          {employee.team_name}
                        </Link>
                      ) : (
                        '—'
                      )}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={employee.status}
                        size="small"
                        color={employee.status === 'ACTIVE' ? 'success' : 'default'}
                        sx={{ minWidth: 80 }}
                      />
                    </TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Pagination */}
        <TablePagination
          component="div"
          count={total}
          page={page}
          onPageChange={handleChangePage}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          rowsPerPageOptions={[10, 25, 50, 100]}
        />
      </Paper>

      {/* Detail Modals */}
      <DetailModal
        open={!!selectedEmployeeId}
        onClose={() => {
          setSelectedEmployeeId(null);
          setEmployeeEditMode(false);
        }}
        title="Employee Details"
        maxWidth="lg"
        showEditButton={true}
        showDeleteButton={true}
        isEditMode={employeeEditMode}
        onEdit={handleEmployeeEdit}
        onDelete={handleEmployeeDelete}
        onSave={handleEmployeeSave}
        onCancel={handleEmployeeCancel}
        isSaving={employeeSaving}
      >
        <EmployeeDetail
          ref={employeeDetailRef}
          employeeId={selectedEmployeeId}
          onNavigate={handleNavigate}
          onDeleteSuccess={handleEmployeeDeleteSuccess}
        />
      </DetailModal>

      <DetailModal
        open={!!selectedTeamId}
        onClose={() => {
          setSelectedTeamId(null);
          setTeamEditMode(false);
        }}
        title="Team Details"
        maxWidth="lg"
        showEditButton={true}
        showDeleteButton={true}
        isEditMode={teamEditMode}
        onEdit={handleTeamEdit}
        onDelete={handleTeamDelete}
        onSave={handleTeamSave}
        onCancel={handleTeamCancel}
        isSaving={teamSaving}
      >
        <TeamDetail
          ref={teamDetailRef}
          teamId={selectedTeamId}
          onNavigate={handleNavigate}
          onDeleteSuccess={handleTeamDeleteSuccess}
        />
      </DetailModal>

      <DetailModal
        open={!!selectedDepartmentId}
        onClose={() => {
          setSelectedDepartmentId(null);
          setDeptEditMode(false);
        }}
        title="Department Details"
        showEditButton={true}
        showDeleteButton={true}
        isEditMode={deptEditMode}
        onEdit={handleDeptEdit}
        onDelete={handleDeptDelete}
        onSave={handleDeptSave}
        onCancel={handleDeptCancel}
        isSaving={deptSaving}
      >
        <DepartmentDetail
          ref={deptDetailRef}
          departmentId={selectedDepartmentId}
          onDeleteSuccess={handleDeptDeleteSuccess}
        />
      </DetailModal>
    </Box>
  );
}

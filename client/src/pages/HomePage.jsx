import { useState, useEffect, useRef } from 'react';
import {
  Box,
  TextField,
  Typography,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  CircularProgress,
  Alert,
  Paper,
  InputAdornment,
  Divider,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import PersonIcon from '@mui/icons-material/Person';
import BusinessIcon from '@mui/icons-material/Business';
import GroupsIcon from '@mui/icons-material/Groups';
import { searchService } from '@/services';
import DetailModal from '@/components/common/DetailModal';
import EmployeeDetail from '@/components/employees/EmployeeDetail';
import TeamDetail from '@/components/teams/TeamDetail';
import DepartmentDetail from '@/components/departments/DepartmentDetail';

export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // State for selected items to show in detail modals
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

  // Debounced search effect
  useEffect(() => {
    // Clear results if search is empty
    if (!searchQuery.trim()) {
      setResults(null);
      setError(null);
      return;
    }

    // Debounce search to avoid excessive API calls
    const timer = setTimeout(async () => {
      setLoading(true);
      setError(null);

      try {
        const data = await searchService.globalSearch(searchQuery);
        setResults(data);
      } catch (err) {
        setError(err.message);
        setResults(null);
      } finally {
        setLoading(false);
      }
    }, 300); // 300ms debounce

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Calculate total results
  const totalResults =
    (results?.employees?.length || 0) +
    (results?.departments?.length || 0) +
    (results?.teams?.length || 0);

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
    handleSearch(); // Refresh search results
  };

  const handleTeamDelete = () => {
    teamDetailRef.current?.delete();
  };

  const handleTeamDeleteSuccess = () => {
    setSelectedTeamId(null);
    setTeamEditMode(false);
    handleSearch(); // Refresh search results
  };

  const handleDeptDelete = () => {
    deptDetailRef.current?.delete();
  };

  const handleDeptDeleteSuccess = () => {
    setSelectedDepartmentId(null);
    setDeptEditMode(false);
    handleSearch(); // Refresh search results
  };

  return (
    <Box sx={{ px: 3, py: 2, maxWidth: 800, mx: 'auto' }}>
      {/* Page Title */}
      <Typography variant="h3" component="h1" gutterBottom sx={{ mb: 3 }}>
        Home
      </Typography>

      {/* Search Bar */}
      <TextField
        fullWidth
        variant="outlined"
        placeholder="Search for people, teams, or departments"
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon />
            </InputAdornment>
          ),
        }}
        sx={{ mb: 3 }}
      />

      {/* Loading State */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Error State */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Results */}
      {!loading && results && (
        <>
          {/* No Results Found */}
          {totalResults === 0 && (
            <Paper sx={{ p: 4, textAlign: 'center', backgroundColor: 'background.paper' }}>
              <Typography variant="body1" color="text.secondary">
                No results found for "{searchQuery}"
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Try searching for employee names, departments, or teams
              </Typography>
            </Paper>
          )}

          {/* Employees Section */}
          {results.employees && results.employees.length > 0 && (
            <Paper sx={{ mb: 2, backgroundColor: 'background.paper' }}>
              <Box sx={{ px: 2, py: 1.5, backgroundColor: 'rgba(144, 202, 249, 0.08)' }}>
                <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <PersonIcon fontSize="small" />
                  Employees ({results.employees.length})
                </Typography>
              </Box>
              <Divider />
              <List disablePadding>
                {results.employees.map((employee, index) => (
                  <Box key={employee.id}>
                    <ListItem disablePadding>
                      <ListItemButton onClick={() => setSelectedEmployeeId(employee.id)}>
                        <ListItemIcon>
                          <PersonIcon color="primary" />
                        </ListItemIcon>
                        <ListItemText
                          primary={employee.name}
                          primaryTypographyProps={{ fontWeight: 500 }}
                        />
                      </ListItemButton>
                    </ListItem>
                    {index < results.employees.length - 1 && <Divider />}
                  </Box>
                ))}
              </List>
            </Paper>
          )}

          {/* Departments Section */}
          {results.departments && results.departments.length > 0 && (
            <Paper sx={{ mb: 2, backgroundColor: 'background.paper' }}>
              <Box sx={{ px: 2, py: 1.5, backgroundColor: 'rgba(144, 202, 249, 0.08)' }}>
                <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <BusinessIcon fontSize="small" />
                  Departments ({results.departments.length})
                </Typography>
              </Box>
              <Divider />
              <List disablePadding>
                {results.departments.map((department, index) => (
                  <Box key={department.id}>
                    <ListItem disablePadding>
                      <ListItemButton onClick={() => setSelectedDepartmentId(department.id)}>
                        <ListItemIcon>
                          <BusinessIcon color="primary" />
                        </ListItemIcon>
                        <ListItemText
                          primary={department.name}
                          primaryTypographyProps={{ fontWeight: 500 }}
                        />
                      </ListItemButton>
                    </ListItem>
                    {index < results.departments.length - 1 && <Divider />}
                  </Box>
                ))}
              </List>
            </Paper>
          )}

          {/* Teams Section */}
          {results.teams && results.teams.length > 0 && (
            <Paper sx={{ mb: 2, backgroundColor: 'background.paper' }}>
              <Box sx={{ px: 2, py: 1.5, backgroundColor: 'rgba(144, 202, 249, 0.08)' }}>
                <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <GroupsIcon fontSize="small" />
                  Teams ({results.teams.length})
                </Typography>
              </Box>
              <Divider />
              <List disablePadding>
                {results.teams.map((team, index) => (
                  <Box key={team.id}>
                    <ListItem disablePadding>
                      <ListItemButton onClick={() => setSelectedTeamId(team.id)}>
                        <ListItemIcon>
                          <GroupsIcon color="primary" />
                        </ListItemIcon>
                        <ListItemText
                          primary={team.name}
                          primaryTypographyProps={{ fontWeight: 500 }}
                        />
                      </ListItemButton>
                    </ListItem>
                    {index < results.teams.length - 1 && <Divider />}
                  </Box>
                ))}
              </List>
            </Paper>
          )}
        </>
      )}

      {/* Initial State - No Search Yet */}
      {!loading && !results && !searchQuery && (
        <Paper sx={{ p: 4, textAlign: 'center', backgroundColor: 'background.paper' }}>
          <SearchIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.primary" gutterBottom>
            Search the HRIS System
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Find employees, departments, and teams by name
          </Typography>
        </Paper>
      )}

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

import { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActionArea,
  CircularProgress,
  Alert,
  Divider,
  Paper,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import BusinessIcon from '@mui/icons-material/Business';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import PersonIcon from '@mui/icons-material/Person';
import { departmentService, teamService, employeeService } from '@/services';
import { cache } from '@/utils/cache';
import DetailModal from '@/components/common/DetailModal';
import DepartmentDetailView from '@/components/departments/DepartmentDetailView';
import EmployeeDetail from '@/components/employees/EmployeeDetail';
import TeamDetail from '@/components/teams/TeamDetail';

export default function TeamsPage() {
  // Department list state
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Unassigned data state
  const [unassignedTeams, setUnassignedTeams] = useState([]);
  const [unassignedEmployees, setUnassignedEmployees] = useState([]);

  // Selected department for detail view
  const [selectedDepartmentId, setSelectedDepartmentId] = useState(null);

  // Modal state for nested navigation
  const [selectedEmployeeId, setSelectedEmployeeId] = useState(null);
  const [selectedTeamId, setSelectedTeamId] = useState(null);

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

  // Load departments and unassigned data on mount
  useEffect(() => {
    loadDepartments();
    loadUnassignedData();
  }, []);

  const loadDepartments = async () => {
    // Check cache first
    const cachedDepartments = cache.get('departments');
    if (cachedDepartments) {
      // Use cached data instantly, no loading state
      setDepartments(cachedDepartments.items || []);
      return;
    }

    // Fetch from API if not cached
    setLoading(true);
    setError(null);

    try {
      const data = await departmentService.listDepartments({ limit: 100 });
      setDepartments(data.items || []);
      cache.set('departments', data);
    } catch (err) {
      setError(err.message || 'Failed to load departments');
      setDepartments([]);
    } finally {
      setLoading(false);
    }
  };

  const loadUnassignedData = async () => {
    // Fetch unassigned teams and employees
    try {
      const [teamsData, employeesData] = await Promise.all([
        teamService.listUnassignedTeams({ limit: 100 }),
        employeeService.listUnassignedEmployees({ limit: 100 }),
      ]);

      setUnassignedTeams(teamsData.items || []);
      setUnassignedEmployees(employeesData.items || []);
    } catch (err) {
      // Silently fail for unassigned data - not critical
      console.error('Failed to load unassigned data:', err);
      setUnassignedTeams([]);
      setUnassignedEmployees([]);
    }
  };

  // Navigation handler for modal-to-modal navigation
  const handleNavigate = (type, id) => {
    if (type === 'employee') {
      setSelectedEmployeeId(id);
    } else if (type === 'team') {
      setSelectedTeamId(id);
    } else if (type === 'department') {
      // Close any open modals and open department detail
      setSelectedEmployeeId(null);
      setSelectedTeamId(null);
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
    loadDepartments(); // Refresh the list
  };

  const handleTeamDelete = () => {
    teamDetailRef.current?.delete();
  };

  const handleTeamDeleteSuccess = () => {
    setSelectedTeamId(null);
    setTeamEditMode(false);
    loadDepartments(); // Refresh the list
  };

  const handleDeptDelete = () => {
    deptDetailRef.current?.delete();
  };

  const handleDeptDeleteSuccess = () => {
    setSelectedDepartmentId(null);
    setDeptEditMode(false);
    loadDepartments(); // Refresh the list
  };

  // Handle department card click
  const handleDepartmentClick = (departmentId) => {
    setSelectedDepartmentId(departmentId);
  };

  // Handle department detail close
  const handleDepartmentClose = () => {
    setSelectedDepartmentId(null);
    setSelectedEmployeeId(null);
    setSelectedTeamId(null);
    setDeptEditMode(false);
  };

  return (
    <Box sx={{ px: 3, py: 2 }}>
      {/* Page Title */}
      <Typography variant="h3" component="h1" gutterBottom sx={{ mb: 3 }}>
        Departments
      </Typography>

      {/* Error State */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Loading State */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Department Cards Grid */}
      {!loading && departments.length > 0 && (
        <Grid container spacing={3}>
          {departments.map((department) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={department.id}>
              <Card
                sx={{
                  height: '100%',
                  transition: 'all 0.2s',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 4,
                  },
                }}
              >
                <CardActionArea
                  onClick={() => handleDepartmentClick(department.id)}
                  sx={{ height: '100%' }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <BusinessIcon color="primary" sx={{ mr: 1, fontSize: 32 }} />
                      <Typography variant="h6" component="div" sx={{ fontWeight: 500 }}>
                        {department.name}
                      </Typography>
                    </Box>
                    <Divider sx={{ my: 1 }} />
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      Click to view teams and employees
                    </Typography>
                  </CardContent>
                </CardActionArea>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Divider between departments and unassigned */}
      {!loading && departments.length > 0 && (unassignedTeams.length > 0 || unassignedEmployees.length > 0) && (
        <Divider sx={{ my: 4 }} />
      )}

      {/* Unassigned Teams Section */}
      {!loading && unassignedTeams.length > 0 && (
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" component="h2" gutterBottom sx={{ mb: 2 }}>
            Unassigned Teams
          </Typography>
          <Grid container spacing={2}>
            {unassignedTeams.map((team) => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={team.id}>
                <Card
                  sx={{
                    height: '100%',
                    transition: 'all 0.2s',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: 4,
                    },
                  }}
                >
                  <CardActionArea
                    onClick={() => handleNavigate('team', team.id)}
                    sx={{ height: '100%' }}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <AccountTreeIcon color="primary" sx={{ fontSize: 24 }} />
                        <Typography variant="body1" sx={{ fontWeight: 500 }}>
                          {team.name}
                        </Typography>
                      </Box>
                    </CardContent>
                  </CardActionArea>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* Unassigned Employees Section */}
      {!loading && unassignedEmployees.length > 0 && (
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" component="h2" gutterBottom sx={{ mb: 2 }}>
            Unassigned Employees
          </Typography>
          <Paper variant="outlined">
            <List disablePadding>
              {unassignedEmployees.map((employee, index) => (
                <Box key={employee.id}>
                  <ListItem disablePadding>
                    <ListItemButton onClick={() => handleNavigate('employee', employee.id)}>
                      <ListItemIcon>
                        <PersonIcon color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary={employee.name}
                        secondary={employee.title || employee.email}
                      />
                    </ListItemButton>
                  </ListItem>
                  {index < unassignedEmployees.length - 1 && <Divider />}
                </Box>
              ))}
            </List>
          </Paper>
        </Box>
      )}

      {/* Empty State */}
      {!loading && departments.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="body1" color="text.secondary">
            No departments found
          </Typography>
        </Box>
      )}

      {/* Department Detail Modal */}
      <DetailModal
        open={!!selectedDepartmentId && !selectedEmployeeId && !selectedTeamId}
        onClose={handleDepartmentClose}
        title="Department Details"
        maxWidth="lg"
        showEditButton={true}
        showDeleteButton={true}
        isEditMode={deptEditMode}
        onEdit={handleDeptEdit}
        onDelete={handleDeptDelete}
        onSave={handleDeptSave}
        onCancel={handleDeptCancel}
        isSaving={deptSaving}
      >
        <DepartmentDetailView
          ref={deptDetailRef}
          departmentId={selectedDepartmentId}
          onNavigate={handleNavigate}
          onDeleteSuccess={handleDeptDeleteSuccess}
        />
      </DetailModal>

      {/* Employee Detail Modal (for nested navigation from department view) */}
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

      {/* Team Detail Modal (for nested navigation from department view) */}
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
    </Box>
  );
}

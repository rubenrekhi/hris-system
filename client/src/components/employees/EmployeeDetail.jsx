import { useState, useEffect, forwardRef, useImperativeHandle } from 'react';
import {
  Box,
  Typography,
  Grid,
  CircularProgress,
  Alert,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Paper,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Autocomplete,
  InputAdornment,
} from '@mui/material';
import PersonIcon from '@mui/icons-material/Person';
import { useEmployee } from '@/hooks/useEmployee';
import { useDirectReports } from '@/hooks/useDirectReports';
import { formatCurrency, formatDate, formatStatus } from '@/utils/formatters';
import EntityLink from '@/components/common/EntityLink';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { employeeService } from '@/services/employeeService';
import { departmentService } from '@/services/departmentService';
import { teamService } from '@/services/teamService';

/**
 * Employee detail component that displays comprehensive employee information.
 * Fetches employee data automatically when employeeId changes.
 * Employee data includes embedded manager_name, department_name, and team_name.
 * Fetches direct reports separately.
 * Supports edit mode for updating employee information and delete functionality.
 *
 * @param {string} employeeId - The ID of the employee to display
 * @param {function} onNavigate - Callback for navigating to related entities: (type, id) => void
 * @param {boolean} enableEdit - Whether to show the edit button
 * @param {function} onDeleteSuccess - Callback when employee is successfully deleted
 *
 * Exposed methods (via ref):
 * - enterEditMode() - Enter edit mode
 * - save() - Save changes
 * - cancel() - Cancel editing
 * - delete() - Show delete confirmation dialog
 * - getEditState() - Get current edit state {isEditMode, isSaving}
 */
const EmployeeDetail = forwardRef(function EmployeeDetail({
  employeeId,
  onNavigate,
  enableEdit = true,
  onDeleteSuccess,
}, ref) {
  const { employee, loading, error, refetch } = useEmployee(employeeId);
  const { directReports, loading: directReportsLoading } = useDirectReports(employeeId);

  // Edit mode state
  const [isEditMode, setIsEditMode] = useState(false);
  const [formData, setFormData] = useState({});
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [success, setSuccess] = useState(false);

  // Delete confirmation state
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState(null);

  // Dropdown options
  const [managers, setManagers] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [teams, setTeams] = useState([]);
  const [loadingOptions, setLoadingOptions] = useState(false);

  // Load dropdown options when component mounts
  useEffect(() => {
    const loadOptions = async () => {
      setLoadingOptions(true);
      try {
        const [employeesData, departmentsData, teamsData] = await Promise.all([
          employeeService.listEmployees({ limit: 100 }),
          departmentService.listDepartments({ limit: 100 }),
          teamService.listTeams({ limit: 100 }),
        ]);

        setManagers(employeesData.items || []);
        setDepartments(departmentsData.items || []);
        setTeams(teamsData.items || []);
      } catch (err) {
        console.error('Failed to load dropdown options:', err);
      } finally {
        setLoadingOptions(false);
      }
    };

    loadOptions();
  }, []);

  // Initialize form data when employee loads or edit mode changes
  useEffect(() => {
    if (employee && isEditMode) {
      setFormData({
        name: employee.name || '',
        title: employee.title || '',
        salary: employee.salary || '',
        status: employee.status || 'ACTIVE',
        manager_id: employee.manager_id || null,
        department_id: employee.department_id || null,
        team_id: employee.team_id || null,
      });
      setSaveError(null);
      setSuccess(false);
    }
  }, [employee, isEditMode]);

  // Handle form field changes
  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  // Handle save
  const handleSave = async () => {
    setSaveError(null);
    setIsSaving(true);

    try {
      // Prepare data for each API call
      const basicFields = {
        name: formData.name,
        title: formData.title,
        salary: formData.salary ? Number(formData.salary) : null,
        status: formData.status,
      };

      // Track what changed
      const managerChanged = formData.manager_id !== employee.manager_id;
      const departmentChanged = formData.department_id !== employee.department_id;
      const teamChanged = formData.team_id !== employee.team_id;

      // Execute API calls
      const promises = [];

      // Always update basic fields
      promises.push(employeeService.updateEmployee(employeeId, basicFields));

      // Update manager if changed (and employee is not CEO)
      if (managerChanged && formData.manager_id) {
        promises.push(employeeService.assignManager(employeeId, formData.manager_id));
      }

      // Update department if changed
      if (departmentChanged) {
        promises.push(employeeService.assignDepartment(employeeId, formData.department_id));
      }

      // Update team if changed
      if (teamChanged) {
        promises.push(employeeService.assignTeam(employeeId, formData.team_id));
      }

      // Execute all updates
      await Promise.all(promises);

      // Refresh employee data
      await refetch();

      // Show success and exit edit mode
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
      setIsEditMode(false);
    } catch (err) {
      console.error('Failed to save employee:', err);
      setSaveError(
        err.response?.data?.detail || err.message || 'Failed to save employee'
      );
      throw err; // Re-throw so parent can handle if needed
    } finally {
      setIsSaving(false);
    }
  };

  // Handle cancel
  const handleCancel = () => {
    setSaveError(null);
    setSuccess(false);
    setIsEditMode(false);
  };

  // Handle edit
  const handleEdit = () => {
    setIsEditMode(true);
  };

  // Handle delete button click
  const handleDelete = () => {
    setShowDeleteConfirm(true);
  };

  // Handle confirm delete
  const handleConfirmDelete = async () => {
    setDeleteError(null);
    setIsDeleting(true);

    try {
      await employeeService.deleteEmployee(employeeId);
      setShowDeleteConfirm(false);

      // Notify parent of successful deletion
      if (onDeleteSuccess) {
        onDeleteSuccess();
      }
    } catch (err) {
      console.error('Failed to delete employee:', err);
      setDeleteError(
        err.response?.data?.detail || err.message || 'Failed to delete employee'
      );
    } finally {
      setIsDeleting(false);
    }
  };

  // Handle cancel delete
  const handleCancelDelete = () => {
    setShowDeleteConfirm(false);
    setDeleteError(null);
  };

  // Expose methods to parent via ref
  useImperativeHandle(ref, () => ({
    enterEditMode: handleEdit,
    save: handleSave,
    cancel: handleCancel,
    delete: handleDelete,
    getEditState: () => ({ isEditMode, isSaving }),
  }), [isEditMode, isSaving, handleSave]);

  // Loading state
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  // Error state
  if (error) {
    return (
      <Alert severity="error">
        Failed to load employee details: {error.message || 'Unknown error'}
      </Alert>
    );
  }

  // No data state
  if (!employee) {
    return null;
  }

  // Create entity objects from embedded data
  const managerEntity = employee.manager_id && employee.manager_name
    ? { id: employee.manager_id, name: employee.manager_name }
    : null;

  const departmentEntity = employee.department_id && employee.department_name
    ? { id: employee.department_id, name: employee.department_name }
    : null;

  const teamEntity = employee.team_id && employee.team_name
    ? { id: employee.team_id, name: employee.team_name }
    : null;

  // Helper to render a field with label and value/component
  const renderField = (label, content) => (
    <Box sx={{ mb: 2 }}>
      <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
        {label}
      </Typography>
      {typeof content === 'string' ? (
        <Typography variant="body1">{content || 'N/A'}</Typography>
      ) : (
        content
      )}
    </Box>
  );

  return (
    <Box>
      {/* Success Message */}
      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Employee updated successfully!
        </Alert>
      )}

      {/* Error Message */}
      {saveError && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setSaveError(null)}>
          {saveError}
        </Alert>
      )}

      {isEditMode ? (
        /* EDIT MODE */
        <Box>
          <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
            Edit Employee
          </Typography>

          <Grid container spacing={3}>
            {/* Name */}
            <Grid item xs={12}>
              <TextField
                label="Name"
                value={formData.name || ''}
                onChange={(e) => handleChange('name', e.target.value)}
                fullWidth
                required
                disabled={isSaving}
              />
            </Grid>

            {/* Title */}
            <Grid item xs={12}>
              <TextField
                label="Title"
                value={formData.title || ''}
                onChange={(e) => handleChange('title', e.target.value)}
                fullWidth
                disabled={isSaving}
              />
            </Grid>

            {/* Status */}
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth disabled={isSaving}>
                <InputLabel>Status</InputLabel>
                <Select
                  value={formData.status || 'ACTIVE'}
                  onChange={(e) => handleChange('status', e.target.value)}
                  label="Status"
                >
                  <MenuItem value="ACTIVE">Active</MenuItem>
                  <MenuItem value="ON_LEAVE">On Leave</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            {/* Salary */}
            <Grid item xs={12} sm={6}>
              <TextField
                label="Salary"
                type="number"
                value={formData.salary || ''}
                onChange={(e) => handleChange('salary', e.target.value)}
                fullWidth
                disabled={isSaving}
                InputProps={{
                  startAdornment: <InputAdornment position="start">$</InputAdornment>,
                }}
              />
            </Grid>

            {/* Manager */}
            <Grid item xs={12}>
              <Autocomplete
                fullWidth
                sx={{ width: '100%' }}
                options={managers.filter((m) => m.id !== employeeId)}
                getOptionLabel={(option) => option.name || ''}
                value={managers.find((m) => m.id === formData.manager_id) || null}
                onChange={(_, newValue) => handleChange('manager_id', newValue?.id || null)}
                disabled={isSaving || loadingOptions || !employee.manager_id}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Manager"
                    helperText={
                      !employee.manager_id ? 'CEO has no manager' : ''
                    }
                  />
                )}
              />
            </Grid>

            {/* Department */}
            <Grid item xs={12}>
              <Autocomplete
                fullWidth
                sx={{ width: '100%' }}
                options={departments}
                getOptionLabel={(option) => option.name || ''}
                value={departments.find((d) => d.id === formData.department_id) || null}
                onChange={(_, newValue) => handleChange('department_id', newValue?.id || null)}
                disabled={isSaving || loadingOptions}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Department"
                  />
                )}
              />
            </Grid>

            {/* Team */}
            <Grid item xs={12}>
              <Autocomplete
                fullWidth
                sx={{ width: '100%' }}
                options={teams}
                getOptionLabel={(option) => option.name || ''}
                value={teams.find((t) => t.id === formData.team_id) || null}
                onChange={(_, newValue) => handleChange('team_id', newValue?.id || null)}
                disabled={isSaving || loadingOptions}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Team"
                  />
                )}
              />
            </Grid>
          </Grid>
        </Box>
      ) : (
        /* VIEW MODE */
        <Box>
          {/* Employee Name as Header */}
          <Typography variant="h5" gutterBottom sx={{ mb: 1 }}>
            {employee.name}
          </Typography>

          {/* Status Chip */}
          {employee.status && (
            <Box sx={{ mb: 3 }}>
              <Chip
                label={formatStatus(employee.status)}
                color={employee.status === 'ACTIVE' ? 'success' : 'warning'}
                size="small"
              />
            </Box>
          )}

          {/* Personal Information Section */}
          <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
            Personal Information
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6}>
              {renderField('Email', employee.email)}
              {renderField('Title', employee.title)}
            </Grid>
            <Grid item xs={12} sm={6}>
              {renderField('Hire Date', formatDate(employee.hired_on))}
              {renderField('Salary', formatCurrency(employee.salary))}
            </Grid>
          </Grid>

          <Divider sx={{ my: 3 }} />

          {/* Organizational Structure Section */}
          <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
            Organizational Structure
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6}>
              {renderField(
                'Manager',
                <EntityLink
                  entity={managerEntity}
                  loading={false}
                  type="employee"
                  onNavigate={onNavigate}
                />
              )}
              {renderField(
                'Department',
                <EntityLink
                  entity={departmentEntity}
                  loading={false}
                  type="department"
                  onNavigate={onNavigate}
                />
              )}
            </Grid>
            <Grid item xs={12} sm={6}>
              {renderField(
                'Team',
                <EntityLink
                  entity={teamEntity}
                  loading={false}
                  type="team"
                  onNavigate={onNavigate}
                />
              )}
            </Grid>
          </Grid>
        </Box>
      )}

      {/* Direct Reports Section */}
      {directReportsLoading ? (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
            Direct Reports
          </Typography>
          <CircularProgress size={24} />
        </Box>
      ) : directReports && directReports.length > 0 ? (
        <Box sx={{ mt: 3 }}>
          <Divider sx={{ mb: 3 }} />
          <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
            Direct Reports ({directReports.length})
          </Typography>
          <Paper variant="outlined">
            <List disablePadding>
              {directReports.map((report, index) => (
                <Box key={report.id}>
                  <ListItem disablePadding>
                    <ListItemButton onClick={() => onNavigate?.('employee', report.id)}>
                      <ListItemIcon>
                        <PersonIcon color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary={report.name}
                        secondary={report.title}
                        primaryTypographyProps={{ fontWeight: 500 }}
                      />
                    </ListItemButton>
                  </ListItem>
                  {index < directReports.length - 1 && <Divider />}
                </Box>
              ))}
            </List>
          </Paper>
        </Box>
      ) : null}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={showDeleteConfirm}
        onClose={handleCancelDelete}
        onConfirm={handleConfirmDelete}
        title="Delete Employee?"
        message={`Are you sure you want to delete ${employee?.name || 'this employee'}? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        severity="error"
        loading={isDeleting}
      />

      {/* Delete Error Alert */}
      {deleteError && (
        <Alert severity="error" sx={{ mt: 2 }} onClose={() => setDeleteError(null)}>
          {deleteError}
        </Alert>
      )}
    </Box>
  );
});

export default EmployeeDetail;

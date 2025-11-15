import { useState, useEffect, forwardRef, useImperativeHandle } from 'react';
import {
  Box,
  Typography,
  Grid,
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Paper,
  Card,
  CardContent,
  CardActionArea,
  TextField,
} from '@mui/material';
import PersonIcon from '@mui/icons-material/Person';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { departmentService } from '@/services';

/**
 * Department detail view component that displays root-level teams and unassigned employees.
 * Fetches department, teams, and employees data.
 * Filters client-side for:
 * - Root teams: parent_team_id === null
 * - Unassigned employees: team_id === null
 * Supports edit mode for updating department information and delete functionality.
 *
 * @param {string} departmentId - The ID of the department to display
 * @param {function} onNavigate - Callback for navigating to related entities: (type, id) => void
 * @param {boolean} enableEdit - Whether to show the edit button
 * @param {function} onDeleteSuccess - Callback when department is successfully deleted
 *
 * Exposed methods (via ref):
 * - enterEditMode() - Enter edit mode
 * - save() - Save changes
 * - cancel() - Cancel editing
 * - delete() - Show delete confirmation dialog
 * - getEditState() - Get current edit state {isEditMode, isSaving}
 */
const DepartmentDetailView = forwardRef(function DepartmentDetailView(
  { departmentId, onNavigate, enableEdit = true, onDeleteSuccess },
  ref
) {
  const [department, setDepartment] = useState(null);
  const [teams, setTeams] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

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

  // Load department data
  useEffect(() => {
    if (!departmentId) return;

    loadDepartmentData();
  }, [departmentId]);

  // Initialize form data when department loads or edit mode changes
  useEffect(() => {
    if (department && isEditMode) {
      setFormData({
        name: department.name || '',
      });
      setSaveError(null);
      setSuccess(false);
    }
  }, [department, isEditMode]);

  const loadDepartmentData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch department details, root teams, and employees in parallel
      const [deptData, rootTeamsData, employeesData] = await Promise.all([
        departmentService.getDepartment(departmentId),
        departmentService.listDepartmentRootTeams(departmentId, { limit: 100 }),
        departmentService.listDepartmentEmployees(departmentId, { limit: 100 }),
      ]);

      setDepartment(deptData);
      setTeams(rootTeamsData.items || []);
      setEmployees(employeesData.items || []);
    } catch (err) {
      setError(err.message || 'Failed to load department data');
      setDepartment(null);
      setTeams([]);
      setEmployees([]);
    } finally {
      setLoading(false);
    }
  };

  // Handle form field changes
  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  // Handle save
  const handleSave = async () => {
    setSaveError(null);
    setIsSaving(true);

    try {
      // Update department
      await departmentService.updateDepartment(departmentId, {
        name: formData.name,
      });

      // Refresh department data
      await loadDepartmentData();

      // Show success and exit edit mode
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
      setIsEditMode(false);
    } catch (err) {
      console.error('Failed to save department:', err);
      setSaveError(
        err.response?.data?.detail || err.message || 'Failed to save department'
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
      await departmentService.deleteDepartment(departmentId);
      setShowDeleteConfirm(false);

      // Notify parent of successful deletion
      if (onDeleteSuccess) {
        onDeleteSuccess();
      }
    } catch (err) {
      console.error('Failed to delete department:', err);
      setDeleteError(
        err.response?.data?.detail || err.message || 'Failed to delete department'
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
  useImperativeHandle(
    ref,
    () => ({
      enterEditMode: handleEdit,
      save: handleSave,
      cancel: handleCancel,
      delete: handleDelete,
      getEditState: () => ({ isEditMode, isSaving }),
    }),
    [isEditMode, isSaving, handleSave]
  );

  // teams already contains only root-level teams from backend
  const rootTeams = teams;

  // Filter for unassigned employees (team_id is null)
  const unassignedEmployees = employees.filter((employee) => employee.team_id === null);

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
        Failed to load department details: {error}
      </Alert>
    );
  }

  // No data state
  if (!department) {
    return null;
  }

  return (
    <Box>
      {/* Success Message */}
      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Department updated successfully!
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
        <Box sx={{ mb: 4 }}>
          <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
            Edit Department
          </Typography>

          <TextField
            label="Department Name"
            value={formData.name || ''}
            onChange={(e) => handleChange('name', e.target.value)}
            fullWidth
            required
            disabled={isSaving}
          />
        </Box>
      ) : (
        /* VIEW MODE */
        <>
          {/* Department Name as Header */}
          <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
            {department.name}
          </Typography>

          {/* Root-Level Teams Section */}
          <Box sx={{ mb: 4 }}>
            <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
              Root-Level Teams ({rootTeams.length})
            </Typography>

            {rootTeams.length > 0 ? (
              <Grid container spacing={2}>
                {rootTeams.map((team) => (
                  <Grid item xs={12} sm={6} md={4} key={team.id}>
                    <Card
                      sx={{
                        height: '100%',
                        transition: 'all 0.2s',
                        '&:hover': {
                          transform: 'translateY(-2px)',
                          boxShadow: 3,
                        },
                      }}
                    >
                      <CardActionArea
                        onClick={() => onNavigate?.('team', team.id)}
                        sx={{ height: '100%' }}
                      >
                        <CardContent>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <AccountTreeIcon color="primary" />
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
            ) : (
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  No root-level teams found in this department.
                </Typography>
              </Paper>
            )}
          </Box>

          <Divider sx={{ my: 3 }} />

          {/* Unassigned Employees Section */}
          <Box>
            <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
              Unassigned Employees ({unassignedEmployees.length})
            </Typography>

            {unassignedEmployees.length > 0 ? (
              <Paper variant="outlined">
                <List disablePadding>
                  {unassignedEmployees.map((employee, index) => (
                    <Box key={employee.id}>
                      <ListItem disablePadding>
                        <ListItemButton onClick={() => onNavigate?.('employee', employee.id)}>
                          <ListItemIcon>
                            <PersonIcon color="primary" />
                          </ListItemIcon>
                          <ListItemText
                            primary={employee.name}
                            secondary={employee.title || employee.email}
                            primaryTypographyProps={{ fontWeight: 500 }}
                          />
                        </ListItemButton>
                      </ListItem>
                      {index < unassignedEmployees.length - 1 && <Divider />}
                    </Box>
                  ))}
                </List>
              </Paper>
            ) : (
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  No unassigned employees found in this department.
                </Typography>
              </Paper>
            )}
          </Box>
        </>
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={showDeleteConfirm}
        onClose={handleCancelDelete}
        onConfirm={handleConfirmDelete}
        title="Delete Department?"
        message={`Are you sure you want to delete ${department?.name || 'this department'}? This action cannot be undone.`}
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

export default DepartmentDetailView;

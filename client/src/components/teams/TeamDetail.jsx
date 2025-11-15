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
  TextField,
  Autocomplete,
} from '@mui/material';
import PersonIcon from '@mui/icons-material/Person';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import { useTeam } from '@/hooks/useTeam';
import { useChildTeams } from '@/hooks/useChildTeams';
import EntityLink from '@/components/common/EntityLink';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { teamService } from '@/services/teamService';
import { employeeService } from '@/services/employeeService';
import { departmentService } from '@/services/departmentService';

/**
 * Team detail component that displays comprehensive team information.
 * Fetches team data automatically when teamId changes.
 * Uses embedded name fields from team API response (lead_name, parent_team_name, department_name).
 * Note: Backend returns team with members included.
 * Supports edit mode for updating team information and delete functionality.
 *
 * @param {string} teamId - The ID of the team to display
 * @param {function} onNavigate - Callback for navigating to related entities: (type, id) => void
 * @param {boolean} enableEdit - Whether to show the edit button
 * @param {function} onDeleteSuccess - Callback when team is successfully deleted
 *
 * Exposed methods (via ref):
 * - enterEditMode() - Enter edit mode
 * - save() - Save changes
 * - cancel() - Cancel editing
 * - delete() - Show delete confirmation dialog
 * - getEditState() - Get current edit state {isEditMode, isSaving}
 */
const TeamDetail = forwardRef(function TeamDetail({ teamId, onNavigate, enableEdit = true, onDeleteSuccess }, ref) {
  const { team, loading, error, refetch } = useTeam(teamId);
  const { childTeams, loading: childTeamsLoading } = useChildTeams(teamId);

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
  const [employees, setEmployees] = useState([]);
  const [teams, setTeams] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loadingOptions, setLoadingOptions] = useState(false);

  // Load dropdown options when component mounts
  useEffect(() => {
    const loadOptions = async () => {
      setLoadingOptions(true);
      try {
        const [employeesData, teamsData, departmentsData] = await Promise.all([
          employeeService.listEmployees({ limit: 100 }),
          teamService.listTeams({ limit: 100 }),
          departmentService.listDepartments({ limit: 100 }),
        ]);

        setEmployees(employeesData.items || []);
        setTeams(teamsData.items || []);
        setDepartments(departmentsData.items || []);
      } catch (err) {
        console.error('Failed to load dropdown options:', err);
      } finally {
        setLoadingOptions(false);
      }
    };

    loadOptions();
  }, []);

  // Initialize form data when team loads or edit mode changes
  useEffect(() => {
    if (team && isEditMode) {
      setFormData({
        name: team.name || '',
        lead_id: team.lead_id || null,
        parent_team_id: team.parent_team_id || null,
        department_id: team.department_id || null,
      });
      setSaveError(null);
      setSuccess(false);
    }
  }, [team, isEditMode]);

  // Handle form field changes
  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  // Handle save
  const handleSave = async () => {
    setSaveError(null);
    setIsSaving(true);

    try {
      // Update team
      await teamService.updateTeam(teamId, {
        name: formData.name,
        lead_id: formData.lead_id,
        parent_team_id: formData.parent_team_id,
        department_id: formData.department_id,
      });

      // Refresh team data
      await refetch();

      // Show success and exit edit mode
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
      setIsEditMode(false);
    } catch (err) {
      console.error('Failed to save team:', err);
      setSaveError(
        err.response?.data?.detail || err.message || 'Failed to save team'
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
      await teamService.deleteTeam(teamId);
      setShowDeleteConfirm(false);

      // Notify parent of successful deletion
      if (onDeleteSuccess) {
        onDeleteSuccess();
      }
    } catch (err) {
      console.error('Failed to delete team:', err);
      setDeleteError(
        err.response?.data?.detail || err.message || 'Failed to delete team'
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

  // Create entity objects from embedded data
  const teamLeadEntity = team?.lead_id && team?.lead_name
    ? { id: team.lead_id, name: team.lead_name }
    : null;

  const parentTeamEntity = team?.parent_team_id && team?.parent_team_name
    ? { id: team.parent_team_id, name: team.parent_team_name }
    : null;

  const departmentEntity = team?.department_id && team?.department_name
    ? { id: team.department_id, name: team.department_name }
    : null;

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
        Failed to load team details: {error.message || 'Unknown error'}
      </Alert>
    );
  }

  // No data state
  if (!team) {
    return null;
  }

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
          Team updated successfully!
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
            Edit Team
          </Typography>

          <Grid container spacing={3}>
            {/* Name */}
            <Grid item xs={12}>
              <TextField
                label="Team Name"
                value={formData.name || ''}
                onChange={(e) => handleChange('name', e.target.value)}
                fullWidth
                required
                disabled={isSaving}
              />
            </Grid>

            {/* Team Lead */}
            <Grid item xs={12}>
              <Autocomplete
                options={employees}
                getOptionLabel={(option) => option.name || ''}
                value={employees.find((e) => e.id === formData.lead_id) || null}
                onChange={(_, newValue) => handleChange('lead_id', newValue?.id || null)}
                disabled={isSaving || loadingOptions}
                renderInput={(params) => <TextField {...params} label="Team Lead" />}
              />
            </Grid>

            {/* Parent Team */}
            <Grid item xs={12}>
              <Autocomplete
                fullWidth
                sx={{ width: '100%' }}
                options={teams.filter((t) => t.id !== teamId)}
                getOptionLabel={(option) => option.name || ''}
                value={teams.find((t) => t.id === formData.parent_team_id) || null}
                onChange={(_, newValue) => handleChange('parent_team_id', newValue?.id || null)}
                disabled={isSaving || loadingOptions}
                renderInput={(params) => <TextField {...params} label="Parent Team" />}
              />
            </Grid>

            {/* Department */}
            <Grid item xs={12}>
              <Autocomplete
                fullWidth
                options={departments}
                getOptionLabel={(option) => option.name || ''}
                value={departments.find((d) => d.id === formData.department_id) || null}
                onChange={(_, newValue) => handleChange('department_id', newValue?.id || null)}
                disabled={isSaving || loadingOptions}
                renderInput={(params) => <TextField {...params} label="Department" />}
              />
            </Grid>
          </Grid>
        </Box>
      ) : (
        /* VIEW MODE */
        <Box>
          {/* Team Name as Header */}
          <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
            {team.name}
          </Typography>

          {/* Team Information Section */}
          <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
            Team Information
          </Typography>
          <Grid container spacing={3}>
            {/* Left Column */}
            <Grid item xs={12} sm={6}>
              {renderField(
                'Team Lead',
                <EntityLink
                  entity={teamLeadEntity}
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

            {/* Right Column */}
            <Grid item xs={12} sm={6}>
              {renderField(
                'Parent Team',
                <EntityLink
                  entity={parentTeamEntity}
                  loading={false}
                  type="team"
                  onNavigate={onNavigate}
                />
              )}
            </Grid>
          </Grid>
        </Box>
      )}

      {/* Team Members Section */}
      {team.members && team.members.length > 0 && !isEditMode && (
        <Box sx={{ mt: 3 }}>
          <Divider sx={{ mb: 3 }} />
          <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
            Team Members ({team.members.length})
          </Typography>
          <Paper variant="outlined">
            <List disablePadding>
              {team.members.map((member, index) => (
                <Box key={member.id}>
                  <ListItem disablePadding>
                    <ListItemButton onClick={() => onNavigate?.('employee', member.id)}>
                      <ListItemIcon>
                        <PersonIcon color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary={member.name}
                        secondary={member.title || member.email}
                        primaryTypographyProps={{ fontWeight: 500 }}
                      />
                    </ListItemButton>
                  </ListItem>
                  {index < team.members.length - 1 && <Divider />}
                </Box>
              ))}
            </List>
          </Paper>
        </Box>
      )}

      {/* Empty Members State */}
      {team.members && team.members.length === 0 && !isEditMode && (
        <Box sx={{ mt: 3 }}>
          <Divider sx={{ mb: 3 }} />
          <Typography variant="body2" color="text.secondary">
            No team members found.
          </Typography>
        </Box>
      )}

      {/* Child Teams Section */}
      {!isEditMode && (childTeamsLoading ? (
        <Box sx={{ mt: 3 }}>
          <Divider sx={{ mb: 3 }} />
          <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
            Child Teams
          </Typography>
          <CircularProgress size={24} />
        </Box>
      ) : childTeams && childTeams.length > 0 ? (
        <Box sx={{ mt: 3 }}>
          <Divider sx={{ mb: 3 }} />
          <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
            Child Teams ({childTeams.length})
          </Typography>
          <Paper variant="outlined">
            <List disablePadding>
              {childTeams.map((childTeam, index) => (
                <Box key={childTeam.id}>
                  <ListItem disablePadding>
                    <ListItemButton onClick={() => onNavigate?.('team', childTeam.id)}>
                      <ListItemIcon>
                        <AccountTreeIcon color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary={childTeam.name}
                        primaryTypographyProps={{ fontWeight: 500 }}
                      />
                    </ListItemButton>
                  </ListItem>
                  {index < childTeams.length - 1 && <Divider />}
                </Box>
              ))}
            </List>
          </Paper>
        </Box>
      ) : null)}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={showDeleteConfirm}
        onClose={handleCancelDelete}
        onConfirm={handleConfirmDelete}
        title="Delete Team?"
        message={`Are you sure you want to delete ${team?.name || 'this team'}? This action cannot be undone.`}
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

export default TeamDetail;

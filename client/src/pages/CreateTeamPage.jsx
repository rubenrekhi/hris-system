import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  IconButton,
  Alert,
  CircularProgress,
  Autocomplete,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import SaveIcon from '@mui/icons-material/Save';
import { teamService, employeeService, departmentService } from '@/services';
import DetailModal from '@/components/common/DetailModal';
import TeamDetail from '@/components/teams/TeamDetail';

export default function CreateTeamPage() {
  const navigate = useNavigate();

  // Form data state
  const [formData, setFormData] = useState({
    name: '',
    lead_id: '',
    parent_team_id: '',
    department_id: '',
  });

  // Dropdown data
  const [employees, setEmployees] = useState([]);
  const [teams, setTeams] = useState([]);
  const [departments, setDepartments] = useState([]);

  // UI state
  const [loadingDropdowns, setLoadingDropdowns] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Success state
  const [createdTeam, setCreatedTeam] = useState(null);
  const [showSuccessModal, setShowSuccessModal] = useState(false);

  // Load dropdown data on mount
  useEffect(() => {
    const loadDropdownData = async () => {
      setLoadingDropdowns(true);
      try {
        // Load all in parallel
        const [employeesData, teamsData, departmentsData] = await Promise.all([
          employeeService.listEmployees({ limit: 100 }),
          teamService.listTeams({ limit: 100 }),
          departmentService.listDepartments({ limit: 100 }),
        ]);

        setEmployees(employeesData.items || []);
        setTeams(teamsData.items || []);
        setDepartments(departmentsData.items || []);
      } catch (err) {
        console.error('Failed to load dropdown data:', err);
        setError('Failed to load form options. Please refresh the page.');
      } finally {
        setLoadingDropdowns(false);
      }
    };

    loadDropdownData();
  }, []);

  // Handle form field changes
  const handleChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    // Basic validation
    if (!formData.name.trim()) {
      setError('Team name is required.');
      return;
    }

    setSubmitting(true);

    try {
      // Filter out empty fields
      const cleanData = Object.fromEntries(
        Object.entries(formData).filter(([_, value]) => value !== '')
      );

      const result = await teamService.createTeam(cleanData);
      setCreatedTeam(result);
      setShowSuccessModal(true);
    } catch (err) {
      console.error('Failed to create team:', err);
      setError(err.message || 'Failed to create team. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  // Handle cancel
  const handleCancel = () => {
    navigate('/management');
  };

  // Handle create another team
  const handleCreateAnother = () => {
    setShowSuccessModal(false);
    setCreatedTeam(null);
    setFormData({
      name: '',
      lead_id: '',
      parent_team_id: '',
      department_id: '',
    });
  };

  // Handle view teams page
  const handleViewTeams = () => {
    navigate('/teams');
  };

  return (
    <Box sx={{ px: 3, py: 2 }}>
      {/* Back Button and Title */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <IconButton onClick={handleCancel} sx={{ color: 'primary.main' }}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h3" component="h1">
          Create New Team
        </Typography>
      </Box>

      <Typography variant="body1" sx={{ mb: 4, color: 'text.secondary' }}>
        Create a new team and optionally assign a team lead, parent team, and department
      </Typography>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Success Alert */}
      {createdTeam && !showSuccessModal && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Team "{createdTeam.name}" created successfully!
        </Alert>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit}>
        {/* Basic Information */}
        <Paper sx={{ p: 3, mb: 3, backgroundColor: 'background.paper' }}>
          <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
            Basic Information
          </Typography>

          <TextField
            fullWidth
            label="Team Name"
            value={formData.name}
            onChange={(e) => handleChange('name', e.target.value)}
            required
            disabled={submitting || loadingDropdowns}
            helperText="Required - Enter a unique name for the team"
          />
        </Paper>

        {/* Team Structure (Optional) */}
        <Paper sx={{ p: 3, mb: 3, backgroundColor: 'background.paper' }}>
          <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
            Team Structure (Optional)
          </Typography>

          {loadingDropdowns ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: {
                  xs: '1fr',
                  sm: 'repeat(2, 1fr)',
                },
                gap: 2,
              }}
            >
              <Autocomplete
                options={employees}
                getOptionLabel={(option) => `${option.name} (${option.email})`}
                value={employees.find((emp) => emp.id === formData.lead_id) || null}
                onChange={(_, newValue) => handleChange('lead_id', newValue?.id || '')}
                disabled={submitting}
                renderInput={(params) => (
                  <TextField {...params} label="Team Lead" helperText="Employee who leads this team" />
                )}
              />

              <Autocomplete
                options={teams}
                getOptionLabel={(option) => option.name}
                value={teams.find((team) => team.id === formData.parent_team_id) || null}
                onChange={(_, newValue) => handleChange('parent_team_id', newValue?.id || '')}
                disabled={submitting}
                renderInput={(params) => (
                  <TextField {...params} label="Parent Team" helperText="Team this team reports to" />
                )}
              />

              <Autocomplete
                options={departments}
                getOptionLabel={(option) => option.name}
                value={departments.find((dept) => dept.id === formData.department_id) || null}
                onChange={(_, newValue) => handleChange('department_id', newValue?.id || '')}
                disabled={submitting}
                renderInput={(params) => (
                  <TextField {...params} label="Department" helperText="Department this team belongs to" />
                )}
              />
            </Box>
          )}
        </Paper>

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
          <Button variant="outlined" onClick={handleCancel} disabled={submitting}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            startIcon={submitting ? <CircularProgress size={20} /> : <SaveIcon />}
            disabled={submitting || loadingDropdowns}
          >
            {submitting ? 'Creating...' : 'Create Team'}
          </Button>
        </Box>
      </form>

      {/* Success Modal */}
      {createdTeam && (
        <DetailModal
          open={showSuccessModal}
          onClose={() => setShowSuccessModal(false)}
          title="Team Created Successfully"
          maxWidth="md"
        >
          <Alert severity="success" sx={{ mb: 3 }}>
            Team "{createdTeam.name}" has been created successfully!
          </Alert>

          <TeamDetail teamId={createdTeam.id} onNavigate={() => {}} />

          <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button variant="outlined" onClick={handleViewTeams}>
              View Teams Page
            </Button>
            <Button variant="contained" onClick={handleCreateAnother}>
              Create Another Team
            </Button>
          </Box>
        </DetailModal>
      )}
    </Box>
  );
}

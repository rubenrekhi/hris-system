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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Autocomplete,
  InputAdornment,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import SaveIcon from '@mui/icons-material/Save';
import { employeeService, departmentService, teamService } from '@/services';
import DetailModal from '@/components/common/DetailModal';
import EmployeeDetail from '@/components/employees/EmployeeDetail';

export default function CreateEmployeePage() {
  const navigate = useNavigate();

  // Form data state
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    title: '',
    hired_on: '',
    salary: '',
    status: 'ACTIVE',
    manager_id: '',
    department_id: '',
    team_id: '',
  });

  // Dropdown data
  const [managers, setManagers] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [teams, setTeams] = useState([]);

  // UI state
  const [loadingDropdowns, setLoadingDropdowns] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Success state
  const [createdEmployee, setCreatedEmployee] = useState(null);
  const [showSuccessModal, setShowSuccessModal] = useState(false);

  // Load dropdown data on mount
  useEffect(() => {
    const loadDropdownData = async () => {
      setLoadingDropdowns(true);
      try {
        // Load all in parallel
        const [managersData, departmentsData, teamsData] = await Promise.all([
          employeeService.listEmployees({ limit: 100 }),
          departmentService.listDepartments({ limit: 100 }),
          teamService.listTeams({ limit: 100 }),
        ]);

        setManagers(managersData.items || []);
        setDepartments(departmentsData.items || []);
        setTeams(teamsData.items || []);
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
    if (!formData.name.trim() || !formData.email.trim()) {
      setError('Name and email are required fields.');
      return;
    }

    setSubmitting(true);

    try {
      // Filter out empty fields
      const cleanData = Object.fromEntries(
        Object.entries(formData).filter(([_, value]) => value !== '')
      );

      const result = await employeeService.createEmployee(cleanData);
      setCreatedEmployee(result);
      setShowSuccessModal(true);
    } catch (err) {
      console.error('Failed to create employee:', err);
      setError(err.message || 'Failed to create employee. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  // Handle cancel
  const handleCancel = () => {
    navigate('/management');
  };

  // Handle create another employee
  const handleCreateAnother = () => {
    setShowSuccessModal(false);
    setCreatedEmployee(null);
    setFormData({
      name: '',
      email: '',
      title: '',
      hired_on: '',
      salary: '',
      status: 'ACTIVE',
      manager_id: '',
      department_id: '',
      team_id: '',
    });
  };

  // Handle view directory
  const handleViewDirectory = () => {
    navigate('/employees');
  };

  return (
    <Box sx={{ px: 3, py: 2 }}>
      {/* Back Button and Title */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <IconButton onClick={handleCancel} sx={{ color: 'primary.main' }}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h3" component="h1">
          Create New Employee
        </Typography>
      </Box>

      <Typography variant="body1" sx={{ mb: 4, color: 'text.secondary' }}>
        Add a new employee to the organization manually
      </Typography>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Success Alert */}
      {createdEmployee && !showSuccessModal && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Employee "{createdEmployee.name}" created successfully!
        </Alert>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit}>
        {/* Basic Information */}
        <Paper sx={{ p: 3, mb: 3, backgroundColor: 'background.paper' }}>
          <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
            Basic Information
          </Typography>

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
            <TextField
              fullWidth
              label="Name"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              required
              disabled={submitting}
            />

            <TextField
              fullWidth
              label="Email"
              type="email"
              value={formData.email}
              onChange={(e) => handleChange('email', e.target.value)}
              required
              disabled={submitting}
            />

            <TextField
              fullWidth
              label="Title"
              value={formData.title}
              onChange={(e) => handleChange('title', e.target.value)}
              disabled={submitting}
            />

            <TextField
              fullWidth
              type="date"
              label="Hire Date"
              value={formData.hired_on}
              onChange={(e) => handleChange('hired_on', e.target.value)}
              InputLabelProps={{ shrink: true }}
              disabled={submitting}
            />
          </Box>
        </Paper>

        {/* Employment Details */}
        <Paper sx={{ p: 3, mb: 3, backgroundColor: 'background.paper' }}>
          <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
            Employment Details
          </Typography>

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
            <TextField
              fullWidth
              label="Salary"
              type="number"
              value={formData.salary}
              onChange={(e) => handleChange('salary', e.target.value)}
              InputProps={{
                startAdornment: <InputAdornment position="start">$</InputAdornment>,
              }}
              disabled={submitting}
            />

            <FormControl fullWidth disabled={submitting}>
              <InputLabel>Status</InputLabel>
              <Select
                value={formData.status}
                onChange={(e) => handleChange('status', e.target.value)}
                label="Status"
              >
                <MenuItem value="ACTIVE">Active</MenuItem>
                <MenuItem value="ON_LEAVE">On Leave</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </Paper>

        {/* Organizational Structure */}
        <Paper sx={{ p: 3, mb: 3, backgroundColor: 'background.paper' }}>
          <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
            Organizational Structure
          </Typography>

          {loadingDropdowns ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
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
                options={managers}
                getOptionLabel={(option) => `${option.name} (${option.email})`}
                onChange={(event, value) => handleChange('manager_id', value?.id || '')}
                disabled={submitting}
                renderInput={(params) => (
                  <TextField {...params} label="Manager" placeholder="Search by name or email" />
                )}
              />

              <Autocomplete
                options={departments}
                getOptionLabel={(option) => option.name}
                onChange={(event, value) => handleChange('department_id', value?.id || '')}
                disabled={submitting}
                renderInput={(params) => (
                  <TextField {...params} label="Department" placeholder="Search department" />
                )}
              />

              <Autocomplete
                options={teams}
                getOptionLabel={(option) => option.name}
                onChange={(event, value) => handleChange('team_id', value?.id || '')}
                disabled={submitting}
                sx={{ gridColumn: { xs: 'span 1', sm: 'span 2' } }}
                renderInput={(params) => (
                  <TextField {...params} label="Team" placeholder="Search team" />
                )}
              />
            </Box>
          )}
        </Paper>

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
          <Button variant="outlined" size="large" onClick={handleCancel} disabled={submitting}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            size="large"
            startIcon={submitting ? <CircularProgress size={20} /> : <SaveIcon />}
            disabled={submitting || loadingDropdowns}
          >
            {submitting ? 'Creating...' : 'Create Employee'}
          </Button>
        </Box>
      </form>

      {/* Success Modal */}
      {createdEmployee && (
        <DetailModal
          open={showSuccessModal}
          onClose={() => setShowSuccessModal(false)}
          title="Employee Created Successfully"
          maxWidth="md"
        >
          <Alert severity="success" sx={{ mb: 3 }}>
            Employee "{createdEmployee.name}" has been created successfully!
          </Alert>

          <EmployeeDetail employeeId={createdEmployee.id} onNavigate={() => {}} />

          <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button variant="outlined" onClick={handleViewDirectory}>
              View Employee Directory
            </Button>
            <Button variant="contained" onClick={handleCreateAnother}>
              Create Another Employee
            </Button>
          </Box>
        </DetailModal>
      )}
    </Box>
  );
}

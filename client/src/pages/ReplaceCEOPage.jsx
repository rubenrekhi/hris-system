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
  Chip,
  DialogContentText,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';
import WorkspacePremiumIcon from '@mui/icons-material/WorkspacePremium';
import WarningIcon from '@mui/icons-material/Warning';
import { employeeService, departmentService, teamService } from '@/services';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import DetailModal from '@/components/common/DetailModal';
import EmployeeDetail from '@/components/employees/EmployeeDetail';

export default function ReplaceCEOPage() {
  const navigate = useNavigate();

  // Form data state
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    title: '',
    hired_on: '',
    salary: '',
    status: 'ACTIVE',
    department_id: '',
    team_id: '',
  });

  // Current CEO state
  const [currentCEO, setCurrentCEO] = useState(null);
  const [loadingCEO, setLoadingCEO] = useState(true);

  // Dropdown data
  const [departments, setDepartments] = useState([]);
  const [teams, setTeams] = useState([]);
  const [loadingDropdowns, setLoadingDropdowns] = useState(true);

  // UI state
  const [replacing, setReplacing] = useState(false);
  const [error, setError] = useState(null);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);

  // Success state
  const [newCEO, setNewCEO] = useState(null);
  const [showSuccessModal, setShowSuccessModal] = useState(false);

  // Load current CEO and dropdown data on mount
  useEffect(() => {
    const loadData = async () => {
      // Load current CEO
      setLoadingCEO(true);
      try {
        const ceo = await employeeService.getCEO();
        setCurrentCEO(ceo);
      } catch (err) {
        console.error('Failed to load current CEO:', err);
        // CEO might not exist yet
        setCurrentCEO(null);
      } finally {
        setLoadingCEO(false);
      }

      // Load dropdown data
      setLoadingDropdowns(true);
      try {
        const [departmentsData, teamsData] = await Promise.all([
          departmentService.listDepartments({ limit: 100 }),
          teamService.listTeams({ limit: 100 }),
        ]);

        setDepartments(departmentsData.items || []);
        setTeams(teamsData.items || []);
      } catch (err) {
        console.error('Failed to load dropdown data:', err);
        setError('Failed to load form options. Please refresh the page.');
      } finally {
        setLoadingDropdowns(false);
      }
    };

    loadData();
  }, []);

  // Handle form field changes
  const handleChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault();
    setError(null);

    // Basic validation
    if (!formData.name.trim() || !formData.email.trim()) {
      setError('Name and email are required fields.');
      return;
    }

    setShowConfirmDialog(true);
  };

  // Handle confirmed replacement
  const handleConfirmReplace = async () => {
    setReplacing(true);
    setError(null);

    try {
      // Filter out empty fields
      const cleanData = Object.fromEntries(
        Object.entries(formData).filter(([_, value]) => value !== '')
      );

      // Single API call creates employee AND replaces CEO
      const result = await employeeService.replaceCEO(cleanData);
      setNewCEO(result);
      setShowConfirmDialog(false);
      setShowSuccessModal(true);

      // Refresh current CEO info
      const updatedCEO = await employeeService.getCEO();
      setCurrentCEO(updatedCEO);
    } catch (err) {
      console.error('Failed to replace CEO:', err);
      setError(err.message || 'Failed to replace CEO. Please try again.');
      setShowConfirmDialog(false);
    } finally {
      setReplacing(false);
    }
  };

  // Handle cancel
  const handleCancel = () => {
    navigate('/management');
  };

  return (
    <Box sx={{ px: 3, py: 2 }}>
      {/* Back Button and Title */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <IconButton onClick={handleCancel} sx={{ color: 'primary.main' }}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h3" component="h1">
          Replace CEO with New Employee
        </Typography>
      </Box>

      <Typography variant="body1" sx={{ mb: 4, color: 'text.secondary' }}>
        Create a new employee and assign them as Chief Executive Officer
      </Typography>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Current CEO Info */}
      <Paper sx={{ p: 3, mb: 3, backgroundColor: 'background.paper' }}>
        <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
          Current CEO
        </Typography>

        {loadingCEO ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
            <CircularProgress />
          </Box>
        ) : currentCEO ? (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <WorkspacePremiumIcon sx={{ fontSize: 40, color: 'warning.main' }} />
            <Box>
              <Typography variant="h6">{currentCEO.name}</Typography>
              <Typography variant="body2" color="text.secondary">
                {currentCEO.email}
              </Typography>
              {currentCEO.title && (
                <Typography variant="body2" color="text.secondary">
                  {currentCEO.title}
                </Typography>
              )}
            </Box>
            <Chip label="CEO" color="warning" sx={{ ml: 'auto' }} />
          </Box>
        ) : (
          <Alert severity="info">
            No CEO currently assigned. This will be the first CEO.
          </Alert>
        )}
      </Paper>

      {/* Warning about replacement */}
      {currentCEO && (
        <Alert severity="warning" icon={<WarningIcon />} sx={{ mb: 3 }}>
          <Typography variant="body2" gutterBottom sx={{ fontWeight: 600 }}>
            This action will replace the current CEO
          </Typography>
          <Typography variant="body2">
            • <strong>{currentCEO.name}</strong> will be demoted and will report to the new CEO
          </Typography>
          <Typography variant="body2">
            • All of {currentCEO.name}'s direct reports will be reassigned to the new CEO
          </Typography>
          <Typography variant="body2">
            • This action will create audit log entries for all changes
          </Typography>
        </Alert>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit}>
        {/* Basic Information */}
        <Paper sx={{ p: 3, mb: 3, backgroundColor: 'background.paper' }}>
          <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
            New CEO Information
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
              disabled={replacing}
            />

            <TextField
              fullWidth
              label="Email"
              type="email"
              value={formData.email}
              onChange={(e) => handleChange('email', e.target.value)}
              required
              disabled={replacing}
            />

            <TextField
              fullWidth
              label="Title"
              value={formData.title}
              onChange={(e) => handleChange('title', e.target.value)}
              disabled={replacing}
            />

            <TextField
              fullWidth
              type="date"
              label="Hire Date"
              value={formData.hired_on}
              onChange={(e) => handleChange('hired_on', e.target.value)}
              InputLabelProps={{ shrink: true }}
              disabled={replacing}
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
              disabled={replacing}
            />

            <FormControl fullWidth disabled={replacing}>
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
            <>
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
                  options={departments}
                  getOptionLabel={(option) => option.name}
                  onChange={(event, value) => handleChange('department_id', value?.id || '')}
                  disabled={replacing}
                  renderInput={(params) => (
                    <TextField {...params} label="Department" placeholder="Search department" />
                  )}
                />

                <Autocomplete
                  options={teams}
                  getOptionLabel={(option) => option.name}
                  onChange={(event, value) => handleChange('team_id', value?.id || '')}
                  disabled={replacing}
                  renderInput={(params) => (
                    <TextField {...params} label="Team" placeholder="Search team" />
                  )}
                />
              </Box>

              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  Note: The new CEO will not have a manager. They will be at the top of the organizational
                  hierarchy.
                </Typography>
              </Alert>
            </>
          )}
        </Paper>

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
          <Button variant="outlined" size="large" onClick={handleCancel} disabled={replacing}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            size="large"
            color="secondary"
            startIcon={<SwapHorizIcon />}
            disabled={replacing || loadingDropdowns || loadingCEO}
          >
            Replace CEO
          </Button>
        </Box>
      </form>

      {/* Confirmation Dialog */}
      <ConfirmDialog
        open={showConfirmDialog}
        onClose={() => setShowConfirmDialog(false)}
        onConfirm={handleConfirmReplace}
        title="Confirm CEO Replacement"
        severity="warning"
        confirmText="Yes, Replace CEO"
        cancelText="Cancel"
        loading={replacing}
        message={
          <Box>
            <DialogContentText sx={{ mb: 2 }}>
              Are you sure you want to replace{' '}
              {currentCEO ? (
                <>
                  <strong>{currentCEO.name}</strong> with <strong>{formData.name}</strong>
                </>
              ) : (
                <>
                  create <strong>{formData.name}</strong>
                </>
              )}{' '}
              as CEO?
            </DialogContentText>
            {currentCEO && (
              <>
                <DialogContentText sx={{ mb: 1 }}>This will have the following effects:</DialogContentText>
                <Box component="ul" sx={{ mt: 1, pl: 3 }}>
                  <li>
                    <DialogContentText>
                      A new employee record will be created for <strong>{formData.name}</strong>
                    </DialogContentText>
                  </li>
                  <li>
                    <DialogContentText>
                      <strong>{currentCEO.name}</strong> will be demoted from CEO
                    </DialogContentText>
                  </li>
                  <li>
                    <DialogContentText>
                      {currentCEO.name} will report to <strong>{formData.name}</strong>
                    </DialogContentText>
                  </li>
                  <li>
                    <DialogContentText>
                      All direct reports will be reorganized under the new CEO
                    </DialogContentText>
                  </li>
                  <li>
                    <DialogContentText>Audit logs will be created for all changes</DialogContentText>
                  </li>
                </Box>
              </>
            )}
          </Box>
        }
      />

      {/* Success Modal */}
      {newCEO && (
        <DetailModal
          open={showSuccessModal}
          onClose={() => setShowSuccessModal(false)}
          title="CEO Replacement Successful"
          maxWidth="md"
        >
          <Alert severity="success" sx={{ mb: 3 }}>
            <strong>{newCEO.name}</strong> has been successfully created and assigned as CEO!
          </Alert>

          <EmployeeDetail employeeId={newCEO.id} onNavigate={() => {}} />

          <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button variant="outlined" onClick={() => navigate('/org-chart')}>
              View Org Chart
            </Button>
            <Button variant="contained" onClick={() => navigate('/management')}>
              Back to Management
            </Button>
          </Box>
        </DetailModal>
      )}
    </Box>
  );
}

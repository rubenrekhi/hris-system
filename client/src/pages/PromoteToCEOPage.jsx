import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  IconButton,
  Alert,
  CircularProgress,
  Autocomplete,
  TextField,
  Chip,
  DialogContentText,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import WorkspacePremiumIcon from '@mui/icons-material/WorkspacePremium';
import WarningIcon from '@mui/icons-material/Warning';
import { employeeService } from '@/services';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import DetailModal from '@/components/common/DetailModal';
import EmployeeDetail from '@/components/employees/EmployeeDetail';

export default function PromoteToCEOPage() {
  const navigate = useNavigate();

  // Current CEO state
  const [currentCEO, setCurrentCEO] = useState(null);
  const [loadingCEO, setLoadingCEO] = useState(true);

  // Employee selection state
  const [employees, setEmployees] = useState([]);
  const [loadingEmployees, setLoadingEmployees] = useState(true);
  const [selectedEmployee, setSelectedEmployee] = useState(null);

  // Promotion state
  const [promoting, setPromoting] = useState(false);
  const [error, setError] = useState(null);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);

  // Success state
  const [promotedEmployee, setPromotedEmployee] = useState(null);
  const [showSuccessModal, setShowSuccessModal] = useState(false);

  // Load current CEO and employees on mount
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

      // Load all employees
      setLoadingEmployees(true);
      try {
        const employeesData = await employeeService.listEmployees({ limit: 100 });
        // Filter out current CEO from the list
        const filteredEmployees = employeesData.items || [];
        setEmployees(filteredEmployees);
      } catch (err) {
        console.error('Failed to load employees:', err);
        setError('Failed to load employees. Please refresh the page.');
      } finally {
        setLoadingEmployees(false);
      }
    };

    loadData();
  }, []);

  // Handle promotion button click
  const handlePromoteClick = () => {
    if (!selectedEmployee) return;
    setShowConfirmDialog(true);
  };

  // Handle confirmed promotion
  const handleConfirmPromotion = async () => {
    if (!selectedEmployee) return;

    setPromoting(true);
    setError(null);

    try {
      const result = await employeeService.promoteEmployeeToCEO(selectedEmployee.id);
      setPromotedEmployee(result);
      setShowConfirmDialog(false);
      setShowSuccessModal(true);

      // Refresh current CEO info
      const newCEO = await employeeService.getCEO();
      setCurrentCEO(newCEO);
      setSelectedEmployee(null);
    } catch (err) {
      console.error('Failed to promote employee:', err);
      setError(err.message || 'Failed to promote employee to CEO. Please try again.');
      setShowConfirmDialog(false);
    } finally {
      setPromoting(false);
    }
  };

  // Handle back navigation
  const handleBack = () => {
    navigate('/management');
  };

  // Filter out current CEO from employee options
  const availableEmployees = currentCEO
    ? employees.filter((emp) => emp.id !== currentCEO.id)
    : employees;

  return (
    <Box sx={{ px: 3, py: 2 }}>
      {/* Back Button and Title */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <IconButton onClick={handleBack} sx={{ color: 'primary.main' }}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h3" component="h1">
          Promote Employee to CEO
        </Typography>
      </Box>

      <Typography variant="body1" sx={{ mb: 4, color: 'text.secondary' }}>
        Select an employee to promote to Chief Executive Officer
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
            No CEO currently assigned. The first employee promoted will become the CEO.
          </Alert>
        )}
      </Paper>

      {/* Employee Selection */}
      <Paper sx={{ p: 3, mb: 3, backgroundColor: 'background.paper' }}>
        <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
          Select Employee to Promote
        </Typography>

        {loadingEmployees ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            <Autocomplete
              options={availableEmployees}
              getOptionLabel={(option) => `${option.name} (${option.email})`}
              value={selectedEmployee}
              onChange={(event, value) => setSelectedEmployee(value)}
              disabled={promoting}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Employee"
                  placeholder="Search by name or email"
                  helperText={
                    currentCEO
                      ? 'Select an employee to promote. Current CEO is excluded from this list.'
                      : 'Select an employee to become the first CEO.'
                  }
                />
              )}
            />

            {selectedEmployee && (
              <Box sx={{ mt: 3, p: 2, backgroundColor: 'rgba(144, 202, 249, 0.1)', borderRadius: 1 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Selected Employee:
                </Typography>
                <Typography variant="h6">{selectedEmployee.name}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {selectedEmployee.email}
                </Typography>
                {selectedEmployee.title && (
                  <Typography variant="body2" color="text.secondary">
                    Current Title: {selectedEmployee.title}
                  </Typography>
                )}
              </Box>
            )}
          </>
        )}
      </Paper>

      {/* Warning */}
      {currentCEO && selectedEmployee && (
        <Alert severity="warning" icon={<WarningIcon />} sx={{ mb: 3 }}>
          <Typography variant="body2" gutterBottom sx={{ fontWeight: 600 }}>
            Important: This action will reorganize the reporting structure
          </Typography>
          <Typography variant="body2">
            • <strong>{currentCEO.name}</strong> will be demoted and will report to{' '}
            <strong>{selectedEmployee.name}</strong>
          </Typography>
          <Typography variant="body2">
            • All of {currentCEO.name}'s direct reports will be reassigned to {selectedEmployee.name}
          </Typography>
          <Typography variant="body2">
            • This action cannot be easily undone and will create audit log entries
          </Typography>
        </Alert>
      )}

      {/* Action Button */}
      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
        <Button variant="outlined" size="large" onClick={handleBack} disabled={promoting}>
          Cancel
        </Button>
        <Button
          variant="contained"
          size="large"
          color="warning"
          startIcon={<WorkspacePremiumIcon />}
          onClick={handlePromoteClick}
          disabled={!selectedEmployee || promoting || loadingEmployees || loadingCEO}
        >
          Promote to CEO
        </Button>
      </Box>

      {/* Confirmation Dialog */}
      <ConfirmDialog
        open={showConfirmDialog}
        onClose={() => setShowConfirmDialog(false)}
        onConfirm={handleConfirmPromotion}
        title="Confirm CEO Promotion"
        severity="warning"
        confirmText="Yes, Promote to CEO"
        cancelText="Cancel"
        loading={promoting}
        message={
          <Box>
            <DialogContentText sx={{ mb: 2 }}>
              Are you sure you want to promote <strong>{selectedEmployee?.name}</strong> to CEO?
            </DialogContentText>
            {currentCEO && (
              <>
                <DialogContentText sx={{ mb: 1 }}>
                  This will have the following effects:
                </DialogContentText>
                <Box component="ul" sx={{ mt: 1, pl: 3 }}>
                  <li>
                    <DialogContentText>
                      <strong>{currentCEO.name}</strong> will be demoted from CEO
                    </DialogContentText>
                  </li>
                  <li>
                    <DialogContentText>
                      {currentCEO.name} will report to <strong>{selectedEmployee?.name}</strong>
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
      {promotedEmployee && (
        <DetailModal
          open={showSuccessModal}
          onClose={() => setShowSuccessModal(false)}
          title="CEO Promotion Successful"
          maxWidth="md"
        >
          <Alert severity="success" sx={{ mb: 3 }}>
            <strong>{promotedEmployee.name}</strong> has been successfully promoted to CEO!
          </Alert>

          <EmployeeDetail employeeId={promotedEmployee.id} onNavigate={() => {}} />

          <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button variant="outlined" onClick={() => navigate('/org-chart')}>
              View Org Chart
            </Button>
            <Button variant="contained" onClick={() => setShowSuccessModal(false)}>
              Done
            </Button>
          </Box>
        </DetailModal>
      )}
    </Box>
  );
}

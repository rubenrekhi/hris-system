import { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  IconButton,
  Alert,
  CircularProgress,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import SaveIcon from '@mui/icons-material/Save';
import { departmentService } from '@/services';
import DetailModal from '@/components/common/DetailModal';
import DepartmentDetailView from '@/components/departments/DepartmentDetailView';

export default function CreateDepartmentPage() {
  const navigate = useNavigate();

  // Form data state
  const [formData, setFormData] = useState({
    name: '',
  });

  // UI state
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Success state
  const [createdDepartment, setCreatedDepartment] = useState(null);
  const [showSuccessModal, setShowSuccessModal] = useState(false);

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
      setError('Department name is required.');
      return;
    }

    setSubmitting(true);

    try {
      const result = await departmentService.createDepartment(formData);
      setCreatedDepartment(result);
      setShowSuccessModal(true);
    } catch (err) {
      console.error('Failed to create department:', err);
      setError(err.message || 'Failed to create department. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  // Handle cancel
  const handleCancel = () => {
    navigate('/management');
  };

  // Handle create another department
  const handleCreateAnother = () => {
    setShowSuccessModal(false);
    setCreatedDepartment(null);
    setFormData({
      name: '',
    });
  };

  // Handle view departments page
  const handleViewDepartments = () => {
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
          Create New Department
        </Typography>
      </Box>

      <Typography variant="body1" sx={{ mb: 4, color: 'text.secondary' }}>
        Create a new department to organize teams and employees
      </Typography>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Success Alert */}
      {createdDepartment && !showSuccessModal && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Department "{createdDepartment.name}" created successfully!
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
            label="Department Name"
            value={formData.name}
            onChange={(e) => handleChange('name', e.target.value)}
            required
            disabled={submitting}
            helperText="Required - Enter a unique name for the department"
          />
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
            disabled={submitting}
          >
            {submitting ? 'Creating...' : 'Create Department'}
          </Button>
        </Box>
      </form>

      {/* Success Modal */}
      {createdDepartment && (
        <DetailModal
          open={showSuccessModal}
          onClose={() => setShowSuccessModal(false)}
          title="Department Created Successfully"
          maxWidth="lg"
        >
          <Alert severity="success" sx={{ mb: 3 }}>
            Department "{createdDepartment.name}" has been created successfully!
          </Alert>

          <DepartmentDetailView departmentId={createdDepartment.id} onNavigate={() => {}} />

          <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button variant="outlined" onClick={handleViewDepartments}>
              View Departments Page
            </Button>
            <Button variant="contained" onClick={handleCreateAnother}>
              Create Another Department
            </Button>
          </Box>
        </DetailModal>
      )}
    </Box>
  );
}

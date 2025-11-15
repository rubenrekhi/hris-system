import { useState, useEffect, forwardRef, useImperativeHandle } from 'react';
import {
  Box,
  Typography,
  CircularProgress,
  Alert,
  TextField,
} from '@mui/material';
import { useDepartment } from '@/hooks/useDepartment';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { departmentService } from '@/services/departmentService';

/**
 * Department detail component that displays department information.
 * Fetches department data automatically when departmentId changes.
 * Supports edit mode for updating department information and delete functionality.
 *
 * @param {string} departmentId - The ID of the department to display
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
const DepartmentDetail = forwardRef(function DepartmentDetail(
  { departmentId, enableEdit = true, onDeleteSuccess },
  ref
) {
  const { department, loading, error, refetch } = useDepartment(departmentId);

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
      await refetch();

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
        Failed to load department details: {error.message || 'Unknown error'}
      </Alert>
    );
  }

  // No data state
  if (!department) {
    return null;
  }

  // Helper to render a field with label and value
  const renderField = (label, value) => (
    <Box sx={{ mb: 2 }}>
      <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
        {label}
      </Typography>
      <Typography variant="body1">{value || 'N/A'}</Typography>
    </Box>
  );

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
        <Box>
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
        <Box>
          {/* Department Name as Header */}
          <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
            {department.name}
          </Typography>

          {/* Department Details */}
          {renderField('Department ID', department.id)}

          {/* Additional Information */}
          <Box sx={{ mt: 3 }}>
            <Typography variant="body2" color="text.secondary">
              For detailed employee and team information, please visit the respective
              sections.
            </Typography>
          </Box>
        </Box>
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

export default DepartmentDetail;

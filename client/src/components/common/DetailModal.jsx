import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  IconButton,
  CircularProgress,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';
import DeleteIcon from '@mui/icons-material/Delete';

/**
 * Reusable modal shell for displaying detail views.
 * Provides consistent modal structure with title, content area, and close button.
 * Supports edit mode with Save/Cancel buttons and delete functionality.
 *
 * @param {boolean} open - Whether the modal is open
 * @param {function} onClose - Callback when modal should close
 * @param {string} title - Modal title
 * @param {React.ReactNode} children - Content to display in the modal
 * @param {string} maxWidth - Maximum width of the modal (xs, sm, md, lg, xl)
 * @param {boolean} showEditButton - Whether to show edit button
 * @param {boolean} showDeleteButton - Whether to show delete button
 * @param {boolean} isEditMode - Whether the modal is in edit mode
 * @param {function} onEdit - Callback when edit button is clicked
 * @param {function} onDelete - Callback when delete button is clicked
 * @param {function} onSave - Callback when save button is clicked
 * @param {function} onCancel - Callback when cancel button is clicked
 * @param {boolean} isSaving - Whether save operation is in progress
 */
export default function DetailModal({
  open,
  onClose,
  title,
  children,
  maxWidth = 'md',
  showEditButton = false,
  showDeleteButton = false,
  isEditMode = false,
  onEdit,
  onDelete,
  onSave,
  onCancel,
  isSaving = false,
}) {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth={maxWidth}
      fullWidth
      aria-labelledby="detail-modal-title"
    >
      <DialogTitle id="detail-modal-title" sx={{ pr: 6 }}>
        {title}
        <IconButton
          aria-label="close"
          onClick={onClose}
          sx={{
            position: 'absolute',
            right: 8,
            top: 8,
            color: (theme) => theme.palette.grey[500],
          }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers>{children}</DialogContent>

      <DialogActions>
        {!isEditMode && (showEditButton || showDeleteButton) && (
          <>
            {showEditButton && (
              <Button
                onClick={onEdit}
                variant="contained"
                startIcon={<EditIcon />}
                sx={{ mr: 1 }}
              >
                Edit
              </Button>
            )}
            {showDeleteButton && (
              <Button
                onClick={onDelete}
                variant="outlined"
                color="error"
                startIcon={<DeleteIcon />}
                sx={{ mr: 'auto' }}
              >
                Delete
              </Button>
            )}
          </>
        )}

        {isEditMode ? (
          <>
            <Button
              onClick={onCancel}
              variant="outlined"
              disabled={isSaving}
            >
              Cancel
            </Button>
            <Button
              onClick={onSave}
              variant="contained"
              startIcon={isSaving ? <CircularProgress size={20} /> : <SaveIcon />}
              disabled={isSaving}
            >
              {isSaving ? 'Saving...' : 'Save'}
            </Button>
          </>
        ) : (
          <Button onClick={onClose} variant="outlined">
            Close
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}

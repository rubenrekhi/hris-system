import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  CircularProgress,
} from '@mui/material';

/**
 * Reusable confirmation dialog component.
 *
 * @param {boolean} open - Whether the dialog is open
 * @param {function} onClose - Callback when dialog is closed/cancelled
 * @param {function} onConfirm - Callback when user confirms
 * @param {string} title - Dialog title
 * @param {string|React.ReactNode} message - Dialog message/content
 * @param {string} confirmText - Text for confirm button (default: "Confirm")
 * @param {string} cancelText - Text for cancel button (default: "Cancel")
 * @param {string} severity - Visual severity: 'warning', 'error', 'info' (default: 'warning')
 * @param {boolean} loading - Whether the confirm action is in progress
 */
export default function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  severity = 'warning',
  loading = false,
}) {
  const getButtonColor = () => {
    if (severity === 'error') return 'error';
    if (severity === 'warning') return 'warning';
    return 'primary';
  };

  return (
    <Dialog open={open} onClose={loading ? undefined : onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        {typeof message === 'string' ? (
          <DialogContentText>{message}</DialogContentText>
        ) : (
          message
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} variant="outlined" disabled={loading}>
          {cancelText}
        </Button>
        <Button
          onClick={onConfirm}
          variant="contained"
          color={getButtonColor()}
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : null}
        >
          {loading ? 'Processing...' : confirmText}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

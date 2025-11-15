import {
  Box,
  Typography,
  Grid,
  CircularProgress,
  Alert,
  Chip,
  Paper,
  Divider,
} from '@mui/material';
import { useAuditLog } from '@/hooks/useAuditLog';
import { formatDateTime, formatStatus } from '@/utils/formatters';

/**
 * Audit log detail component that displays comprehensive audit log information.
 * Fetches audit log data automatically when auditLogId changes.
 * Displays previous_state and new_state as formatted JSON.
 *
 * @param {string} auditLogId - The ID of the audit log to display
 */
export default function AuditLogDetail({ auditLogId }) {
  const { auditLog, loading, error } = useAuditLog(auditLogId);

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
        Failed to load audit log details: {error.message || 'Unknown error'}
      </Alert>
    );
  }

  // No data state
  if (!auditLog) {
    return null;
  }

  // Helper to get change type color
  const getChangeTypeColor = (changeType) => {
    switch (changeType) {
      case 'CREATE':
        return 'success';
      case 'UPDATE':
        return 'info';
      case 'DELETE':
        return 'error';
      case 'BULK_UPDATE':
        return 'warning';
      default:
        return 'default';
    }
  };

  // Helper to get entity type color
  const getEntityTypeColor = (entityType) => {
    switch (entityType) {
      case 'EMPLOYEE':
        return 'primary';
      case 'DEPARTMENT':
        return 'secondary';
      case 'TEAM':
        return 'info';
      case 'USER':
        return 'warning';
      default:
        return 'default';
    }
  };

  // Helper to render a field with label and value
  const renderField = (label, value) => (
    <Box sx={{ mb: 2 }}>
      <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
        {label}
      </Typography>
      <Typography variant="body1">{value || 'N/A'}</Typography>
    </Box>
  );

  // Helper to render state JSON
  const renderState = (state, emptyMessage) => {
    if (state === null || state === undefined) {
      return (
        <Paper sx={{ p: 2, backgroundColor: 'background.default' }}>
          <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
            {emptyMessage}
          </Typography>
        </Paper>
      );
    }

    return (
      <Paper sx={{ p: 2, backgroundColor: 'background.default', overflow: 'auto' }}>
        <Typography
          component="pre"
          sx={{
            fontFamily: 'monospace',
            fontSize: '0.875rem',
            margin: 0,
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
          }}
        >
          {JSON.stringify(state, null, 2)}
        </Typography>
      </Paper>
    );
  };

  return (
    <Box>
      {/* Header with Change Type and Entity Type Chips */}
      <Box sx={{ mb: 3, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
        <Chip
          label={formatStatus(auditLog.change_type)}
          color={getChangeTypeColor(auditLog.change_type)}
          size="small"
        />
        <Chip
          label={formatStatus(auditLog.entity_type)}
          color={getEntityTypeColor(auditLog.entity_type)}
          size="small"
        />
      </Box>

      {/* Audit Log Details */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6}>
          {renderField('Audit Log ID', auditLog.id)}
          {renderField('Entity ID', auditLog.entity_id)}
        </Grid>
        <Grid item xs={12} sm={6}>
          {renderField('Changed By User', auditLog.changed_by_user_id || 'System')}
          {renderField('Created At', formatDateTime(auditLog.created_at))}
        </Grid>
      </Grid>

      <Divider sx={{ my: 3 }} />

      {/* State Comparison */}
      <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
        State Comparison
      </Typography>

      <Grid container spacing={2}>
        {/* Previous State */}
        <Grid item xs={12} md={6}>
          <Typography variant="subtitle2" gutterBottom>
            Previous State
          </Typography>
          {renderState(
            auditLog.previous_state,
            'N/A - New Record Created'
          )}
        </Grid>

        {/* New State */}
        <Grid item xs={12} md={6}>
          <Typography variant="subtitle2" gutterBottom>
            New State
          </Typography>
          {renderState(
            auditLog.new_state,
            'N/A - Record Deleted'
          )}
        </Grid>
      </Grid>
    </Box>
  );
}

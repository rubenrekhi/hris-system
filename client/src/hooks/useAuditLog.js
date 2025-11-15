import { useEffect } from 'react';
import { useApi } from './useApi';
import { auditLogService } from '@/services';

/**
 * Custom hook for fetching a single audit log with full details.
 * Automatically fetches when auditLogId changes.
 * Includes previous_state and new_state fields.
 *
 * @param {string} auditLogId - The audit log ID to fetch
 * @returns {Object} - { auditLog, loading, error, refetch }
 *
 * @example
 * const { auditLog, loading, error } = useAuditLog(auditLogId);
 *
 * if (loading) return <CircularProgress />;
 * if (error) return <Alert severity="error">{error.message}</Alert>;
 * if (!auditLog) return null;
 * return <div>{auditLog.change_type}</div>;
 */
export function useAuditLog(auditLogId) {
  const { data: auditLog, loading, error, execute } = useApi(auditLogService.getAuditLog);

  useEffect(() => {
    // Skip if no audit log ID provided
    if (!auditLogId) {
      return;
    }

    // Fetch audit log data
    execute(auditLogId).catch(() => {
      // Error is already handled by useApi hook
    });
  }, [auditLogId, execute]);

  return {
    auditLog,
    loading,
    error,
    refetch: () => execute(auditLogId),
  };
}

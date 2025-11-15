import { useEffect } from 'react';
import { useApi } from './useApi';
import { employeeService } from '@/services';

/**
 * Custom hook for fetching an employee's direct reports.
 * Automatically fetches when employeeId changes.
 *
 * @param {string} employeeId - The employee ID to fetch direct reports for
 * @returns {Object} - { directReports, loading, error, refetch }
 *
 * @example
 * const { directReports, loading, error } = useDirectReports(employeeId);
 *
 * if (loading) return <CircularProgress />;
 * if (error) return <Alert severity="error">{error.message}</Alert>;
 * if (!directReports || directReports.length === 0) return <div>No direct reports</div>;
 * return <List>{directReports.map(emp => <ListItem>{emp.name}</ListItem>)}</List>;
 */
export function useDirectReports(employeeId) {
  const { data: directReports, loading, error, execute } = useApi(employeeService.getDirectReports);

  useEffect(() => {
    // Skip if no employee ID provided
    if (!employeeId) {
      return;
    }

    // Fetch direct reports
    execute(employeeId).catch(() => {
      // Error is already handled by useApi hook
    });
  }, [employeeId, execute]);

  return {
    directReports,
    loading,
    error,
    refetch: () => execute(employeeId),
  };
}

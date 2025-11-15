import { useEffect } from 'react';
import { useApi } from './useApi';
import { employeeService } from '@/services';

/**
 * Custom hook for fetching employee details by ID.
 * Automatically fetches when employeeId changes.
 *
 * @param {string} employeeId - The employee ID to fetch
 * @returns {Object} - { employee, loading, error, refetch }
 *
 * @example
 * const { employee, loading, error } = useEmployee(employeeId);
 *
 * if (loading) return <CircularProgress />;
 * if (error) return <Alert severity="error">{error.message}</Alert>;
 * if (!employee) return null;
 * return <div>{employee.name}</div>;
 */
export function useEmployee(employeeId) {
  const { data: employee, loading, error, execute } = useApi(employeeService.getEmployee);

  useEffect(() => {
    // Skip if no employee ID provided
    if (!employeeId) {
      return;
    }

    // Fetch employee data
    execute(employeeId).catch(() => {
      // Error is already handled by useApi hook
    });
  }, [employeeId, execute]);

  return {
    employee,
    loading,
    error,
    refetch: () => execute(employeeId),
  };
}

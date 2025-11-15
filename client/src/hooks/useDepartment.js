import { useEffect } from 'react';
import { useApi } from './useApi';
import { departmentService } from '@/services';

/**
 * Custom hook for fetching department details by ID.
 * Automatically fetches when departmentId changes.
 *
 * @param {string} departmentId - The department ID to fetch
 * @returns {Object} - { department, loading, error, refetch }
 *
 * @example
 * const { department, loading, error } = useDepartment(departmentId);
 *
 * if (loading) return <CircularProgress />;
 * if (error) return <Alert severity="error">{error.message}</Alert>;
 * if (!department) return null;
 * return <div>{department.name}</div>;
 */
export function useDepartment(departmentId) {
  const { data: department, loading, error, execute } = useApi(departmentService.getDepartment);

  useEffect(() => {
    // Skip if no department ID provided
    if (!departmentId) {
      return;
    }

    // Fetch department data
    execute(departmentId).catch(() => {
      // Error is already handled by useApi hook
    });
  }, [departmentId, execute]);

  return {
    department,
    loading,
    error,
    refetch: () => execute(departmentId),
  };
}

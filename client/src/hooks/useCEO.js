import { useEffect } from 'react';
import { useApi } from './useApi';
import { employeeService } from '@/services';

/**
 * Custom hook for fetching the CEO (employee with no manager).
 * Automatically fetches on mount.
 *
 * @returns {Object} - { ceo, loading, error, refetch }
 *
 * @example
 * const { ceo, loading, error } = useCEO();
 *
 * if (loading) return <CircularProgress />;
 * if (error) return <Alert severity="error">{error.message}</Alert>;
 * if (!ceo) return null;
 * return <div>{ceo.name} - CEO</div>;
 */
export function useCEO() {
  const { data: ceo, loading, error, execute } = useApi(employeeService.getCEO);

  useEffect(() => {
    // Fetch CEO data on mount
    execute().catch(() => {
      // Error is already handled by useApi hook
    });
  }, [execute]);

  return {
    ceo,
    loading,
    error,
    refetch: () => execute(),
  };
}

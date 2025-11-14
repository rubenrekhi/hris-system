/**
 * useApi Hook
 * Custom hook for managing API calls with loading and error states.
 */

import { useState, useCallback } from 'react';

/**
 * Hook for making API calls with automatic state management.
 * Provides loading, error, and data states with an execute function.
 *
 * @param {Function} apiFunction - API function to call (should return a Promise)
 * @returns {Object} - { data, loading, error, execute, reset }
 *
 * @example
 * const { data, loading, error, execute } = useApi(employeeService.listEmployees);
 *
 * useEffect(() => {
 *   execute({ limit: 50 });
 * }, []);
 *
 * if (loading) return <CircularProgress />;
 * if (error) return <Alert severity="error">{error.message}</Alert>;
 * return <EmployeeList employees={data?.items} />;
 */
export function useApi(apiFunction) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Execute the API function with provided arguments.
   * Updates loading/error states automatically.
   */
  const execute = useCallback(
    async (...args) => {
      setLoading(true);
      setError(null);

      try {
        const result = await apiFunction(...args);
        setData(result);
        return result;
      } catch (err) {
        setError(err);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [apiFunction]
  );

  /**
   * Reset all state to initial values.
   */
  const reset = useCallback(() => {
    setData(null);
    setLoading(false);
    setError(null);
  }, []);

  return {
    data,
    loading,
    error,
    execute,
    reset,
  };
}

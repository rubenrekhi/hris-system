import { useEffect } from 'react';
import { useApi } from './useApi';
import { teamService } from '@/services';

/**
 * Custom hook for fetching team details by ID.
 * Automatically fetches when teamId changes.
 * Note: Backend returns team with members included.
 *
 * @param {string} teamId - The team ID to fetch
 * @returns {Object} - { team, loading, error, refetch }
 *
 * @example
 * const { team, loading, error } = useTeam(teamId);
 *
 * if (loading) return <CircularProgress />;
 * if (error) return <Alert severity="error">{error.message}</Alert>;
 * if (!team) return null;
 * return <div>{team.name}</div>;
 */
export function useTeam(teamId) {
  const { data: team, loading, error, execute } = useApi(teamService.getTeam);

  useEffect(() => {
    // Skip if no team ID provided
    if (!teamId) {
      return;
    }

    // Fetch team data
    execute(teamId).catch(() => {
      // Error is already handled by useApi hook
    });
  }, [teamId, execute]);

  return {
    team,
    loading,
    error,
    refetch: () => execute(teamId),
  };
}

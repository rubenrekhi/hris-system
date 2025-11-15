import { useEffect } from 'react';
import { useApi } from './useApi';
import { teamService } from '@/services';

/**
 * Custom hook for fetching a team's child teams (sub-teams).
 * Automatically fetches when teamId changes.
 *
 * @param {string} teamId - The team ID to fetch child teams for
 * @returns {Object} - { childTeams, loading, error, refetch }
 *
 * @example
 * const { childTeams, loading, error } = useChildTeams(teamId);
 *
 * if (loading) return <CircularProgress />;
 * if (error) return <Alert severity="error">{error.message}</Alert>;
 * if (!childTeams || childTeams.length === 0) return <div>No child teams</div>;
 * return <List>{childTeams.map(team => <ListItem>{team.name}</ListItem>)}</List>;
 */
export function useChildTeams(teamId) {
  const { data: childTeams, loading, error, execute } = useApi(teamService.getChildTeams);

  useEffect(() => {
    // Skip if no team ID provided
    if (!teamId) {
      return;
    }

    // Fetch child teams
    execute(teamId).catch(() => {
      // Error is already handled by useApi hook
    });
  }, [teamId, execute]);

  return {
    childTeams,
    loading,
    error,
    refetch: () => execute(teamId),
  };
}

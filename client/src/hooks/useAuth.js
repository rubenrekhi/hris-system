/**
 * Custom hook for managing authentication state.
 * Fetches current user on mount and provides logout function.
 */

import { useState, useEffect } from 'react';
import { authService } from '../services/authService';

export function useAuth() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchCurrentUser() {
      try {
        setLoading(true);
        const userData = await authService.getCurrentUser();
        setUser(userData);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch user:', err);
        setUser(null);
        setError(err);
      } finally {
        setLoading(false);
      }
    }

    fetchCurrentUser();
  }, []);

  const logout = () => {
    // Logout will redirect to backend, which clears cookie and redirects to login
    authService.logout();
    // Page will redirect, so setting user to null is not necessary but harmless
  };

  return {
    user,
    loading,
    error,
    logout,
    isAuthenticated: !!user,
  };
}

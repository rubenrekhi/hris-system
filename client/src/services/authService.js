/**
 * Authentication service for handling user login, logout, and session management.
 */

import { api } from './api';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const authService = {
  /**
   * Redirect to backend login endpoint.
   * Backend will redirect to WorkOS AuthKit for authentication.
   */
  login: () => {
    window.location.href = `${API_BASE_URL}/auth/login`;
  },

  /**
   * Logout the current user.
   * Clears session cookie and redirects to login page.
   * Uses full page redirect to ensure cookie deletion is processed.
   */
  logout: () => {
    // Redirect to backend logout endpoint which will clear cookie and redirect
    window.location.href = `${API_BASE_URL}/auth/logout`;
  },

  /**
   * Get current authenticated user information.
   * @returns {Promise<Object|null>} User object or null if not authenticated
   */
  getCurrentUser: async () => {
    try {
      const user = await api.get('/auth/me');
      return user;
    } catch (error) {
      // If 401, user will be redirected to login by api.js handleResponse
      // For other errors, return null
      if (error.status !== 401) {
        console.error('Get current user error:', error);
      }
      return null;
    }
  },
};

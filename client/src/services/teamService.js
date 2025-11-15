/**
 * Team Service
 * API functions for team management operations.
 */

import { api } from './api';

export const teamService = {
  /**
   * List teams with optional filters and pagination.
   * @param {Object} filters - Filter options
   * @param {string} [filters.department_id] - Filter by department ID
   * @param {string} [filters.parent_team_id] - Filter by parent team ID
   * @param {string} [filters.name] - Filter by name (partial match)
   * @param {number} [filters.limit=25] - Results per page
   * @param {number} [filters.offset=0] - Pagination offset
   * @returns {Promise<{items: Array, total: number, limit: number, offset: number}>}
   */
  listTeams: async (filters = {}) => {
    return api.get('/teams', filters);
  },

  /**
   * List unassigned root-level teams (no department, no parent).
   * @param {Object} filters - Filter options
   * @param {number} [filters.limit=25] - Results per page
   * @param {number} [filters.offset=0] - Pagination offset
   * @returns {Promise<{items: Array, total: number, limit: number, offset: number}>}
   */
  listUnassignedTeams: async (filters = {}) => {
    return api.get('/teams/unassigned', filters);
  },

  /**
   * Get a single team by ID with members.
   * @param {string} id - Team ID (UUID)
   * @returns {Promise<Object>} Team details with members
   */
  getTeam: async (id) => {
    return api.get(`/teams/${id}`);
  },

  /**
   * Get child teams of a team.
   * @param {string} teamId - Team ID
   * @returns {Promise<Array>} List of child teams
   */
  getChildTeams: async (teamId) => {
    return api.get(`/teams/${teamId}/children`);
  },

  /**
   * Create a new team.
   * @param {Object} data - Team data
   * @param {string} data.name - Team name (required)
   * @param {string} [data.lead_id] - Team lead's employee ID
   * @param {string} [data.parent_team_id] - Parent team ID
   * @param {string} [data.department_id] - Department ID
   * @returns {Promise<Object>} Created team
   */
  createTeam: async (data) => {
    return api.post('/teams', data);
  },

  /**
   * Update team fields.
   * @param {string} id - Team ID
   * @param {Object} data - Fields to update
   * @param {string} [data.name] - Team name
   * @param {string} [data.lead_id] - Team lead's employee ID
   * @param {string} [data.parent_team_id] - Parent team ID
   * @param {string} [data.department_id] - Department ID
   * @returns {Promise<Object>} Updated team
   */
  updateTeam: async (id, data) => {
    return api.patch(`/teams/${id}`, data);
  },

  /**
   * Delete a team.
   * @param {string} id - Team ID
   * @returns {Promise<null>}
   */
  deleteTeam: async (id) => {
    return api.delete(`/teams/${id}`);
  },
};

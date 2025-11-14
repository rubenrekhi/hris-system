/**
 * Search Service
 * API functions for global search across employees, departments, and teams.
 */

import { api } from './api';

export const searchService = {
  /**
   * Perform a global search across employees, departments, and teams.
   * Searches by name and email (for employees).
   *
   * @param {string} query - Search query string (required)
   * @returns {Promise<Object>} Search results
   * @returns {Array} return.employees - Matching employees
   * @returns {Array} return.departments - Matching departments
   * @returns {Array} return.teams - Matching teams
   *
   * @example
   * const results = await searchService.globalSearch('engineering');
   * console.log(results.employees);  // Employees matching 'engineering'
   * console.log(results.departments); // Departments matching 'engineering'
   * console.log(results.teams);       // Teams matching 'engineering'
   */
  globalSearch: async (query) => {
    return api.get('/search', { q: query });
  },
};

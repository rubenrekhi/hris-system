/**
 * Department Service
 * API functions for department management operations.
 */

import { api } from './api';

export const departmentService = {
  /**
   * Create a new department.
   * @param {Object} data - Department data
   * @param {string} data.name - Department name (required)
   * @returns {Promise<Object>} Created department
   */
  createDepartment: async (data) => {
    return api.post('/departments', data);
  },

  /**
   * List all departments with pagination.
   * @param {Object} pagination - Pagination options
   * @param {number} [pagination.limit=25] - Results per page
   * @param {number} [pagination.offset=0] - Pagination offset
   * @returns {Promise<{items: Array, total: number, limit: number, offset: number}>}
   */
  listDepartments: async (pagination = {}) => {
    return api.get('/departments', pagination);
  },

  /**
   * Get a single department by ID.
   * @param {string} id - Department ID (UUID)
   * @returns {Promise<Object>} Department details
   */
  getDepartment: async (id) => {
    return api.get(`/departments/${id}`);
  },

  /**
   * Update department name.
   * @param {string} id - Department ID
   * @param {Object} data - Fields to update
   * @param {string} data.name - New department name
   * @returns {Promise<Object>} Updated department
   */
  updateDepartment: async (id, data) => {
    return api.patch(`/departments/${id}`, data);
  },

  /**
   * Delete a department.
   * @param {string} id - Department ID
   * @returns {Promise<null>}
   */
  deleteDepartment: async (id) => {
    return api.delete(`/departments/${id}`);
  },

  /**
   * List teams in a department.
   * @param {string} departmentId - Department ID
   * @param {Object} pagination - Pagination options
   * @param {number} [pagination.limit=25] - Results per page
   * @param {number} [pagination.offset=0] - Pagination offset
   * @returns {Promise<{items: Array, total: number, limit: number, offset: number}>}
   */
  listDepartmentTeams: async (departmentId, pagination = {}) => {
    return api.get(`/departments/${departmentId}/teams`, pagination);
  },

  /**
   * List root-level teams in a department (teams with no parent team).
   * @param {string} departmentId - Department ID
   * @param {Object} pagination - Pagination options
   * @param {number} [pagination.limit=100] - Results per page
   * @param {number} [pagination.offset=0] - Pagination offset
   * @returns {Promise<{items: Array, total: number, limit: number, offset: number}>}
   */
  listDepartmentRootTeams: async (departmentId, pagination = {}) => {
    return api.get(`/departments/${departmentId}/teams/root`, pagination);
  },

  /**
   * List employees in a department.
   * @param {string} departmentId - Department ID
   * @param {Object} pagination - Pagination options
   * @param {number} [pagination.limit=25] - Results per page
   * @param {number} [pagination.offset=0] - Pagination offset
   * @returns {Promise<{items: Array, total: number, limit: number, offset: number}>}
   */
  listDepartmentEmployees: async (departmentId, pagination = {}) => {
    return api.get(`/departments/${departmentId}/employees`, pagination);
  },
};

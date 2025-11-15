/**
 * Employee Service
 * API functions for employee management operations.
 */

import { api } from './api';

export const employeeService = {
  /**
   * List employees with optional filters and pagination.
   * @param {Object} filters - Filter options
   * @param {string} [filters.team_id] - Filter by team ID
   * @param {string} [filters.department_id] - Filter by department ID
   * @param {string} [filters.status] - Filter by status ('ACTIVE' or 'ON_LEAVE')
   * @param {number} [filters.min_salary] - Minimum salary filter
   * @param {number} [filters.max_salary] - Maximum salary filter
   * @param {string} [filters.name] - Filter by name (partial match)
   * @param {string} [filters.email] - Filter by email (partial match)
   * @param {number} [filters.limit=25] - Results per page
   * @param {number} [filters.offset=0] - Pagination offset
   * @returns {Promise<{items: Array, total: number, limit: number, offset: number}>}
   */
  listEmployees: async (filters = {}) => {
    return api.get('/employees', filters);
  },

  /**
   * List unassigned employees (no department, no team).
   * @param {Object} filters - Filter options
   * @param {number} [filters.limit=25] - Results per page
   * @param {number} [filters.offset=0] - Pagination offset
   * @returns {Promise<{items: Array, total: number, limit: number, offset: number}>}
   */
  listUnassignedEmployees: async (filters = {}) => {
    return api.get('/employees/unassigned', filters);
  },

  /**
   * Get a single employee by ID.
   * @param {string} id - Employee ID (UUID)
   * @returns {Promise<Object>} Employee details
   */
  getEmployee: async (id) => {
    return api.get(`/employees/${id}`);
  },

  /**
   * Create a new employee.
   * @param {Object} data - Employee data
   * @param {string} data.name - Employee name (required)
   * @param {string} data.email - Employee email (required)
   * @param {string} [data.title] - Job title
   * @param {string} [data.hired_on] - Hire date (YYYY-MM-DD)
   * @param {number} [data.salary] - Annual salary
   * @param {string} [data.status] - Status ('ACTIVE' or 'ON_LEAVE')
   * @param {string} [data.manager_id] - Manager's employee ID
   * @param {string} [data.department_id] - Department ID
   * @param {string} [data.team_id] - Team ID
   * @returns {Promise<Object>} Created employee
   */
  createEmployee: async (data) => {
    return api.post('/employees', data);
  },

  /**
   * Update employee fields.
   * @param {string} id - Employee ID
   * @param {Object} data - Fields to update
   * @param {string} [data.name] - Employee name
   * @param {string} [data.title] - Job title
   * @param {number} [data.salary] - Annual salary
   * @param {string} [data.status] - Status ('ACTIVE' or 'ON_LEAVE')
   * @returns {Promise<Object>} Updated employee
   */
  updateEmployee: async (id, data) => {
    return api.patch(`/employees/${id}`, data);
  },

  /**
   * Delete an employee.
   * @param {string} id - Employee ID
   * @returns {Promise<null>}
   */
  deleteEmployee: async (id) => {
    return api.delete(`/employees/${id}`);
  },

  /**
   * Get the CEO employee.
   * @returns {Promise<Object>} CEO employee details
   */
  getCEO: async () => {
    return api.get('/employees/ceo');
  },

  /**
   * Replace CEO with a new employee.
   * @param {Object} data - New CEO employee data
   * @param {string} data.name - Employee name
   * @param {string} data.email - Employee email
   * @param {string} [data.title] - Job title
   * @param {string} [data.hired_on] - Hire date
   * @param {number} [data.salary] - Annual salary
   * @returns {Promise<Object>} New CEO employee
   */
  replaceCEO: async (data) => {
    return api.post('/employees/ceo/replace', data);
  },

  /**
   * Promote an existing employee to CEO.
   * @param {string} employeeId - Employee ID to promote
   * @returns {Promise<Object>} Promoted CEO employee
   */
  promoteEmployeeToCEO: async (employeeId) => {
    return api.post(`/employees/ceo/promote/${employeeId}`);
  },

  /**
   * Get direct reports of an employee.
   * @param {string} employeeId - Employee ID
   * @returns {Promise<Array>} List of direct reports
   */
  getDirectReports: async (employeeId) => {
    return api.get(`/employees/${employeeId}/direct-reports`);
  },

  /**
   * Assign or remove employee's department.
   * @param {string} employeeId - Employee ID
   * @param {string|null} departmentId - Department ID (null to remove)
   * @returns {Promise<Object>} Updated employee
   */
  assignDepartment: async (employeeId, departmentId) => {
    return api.patch(`/employees/${employeeId}/department`, {
      department_id: departmentId,
    });
  },

  /**
   * Assign or remove employee's team.
   * @param {string} employeeId - Employee ID
   * @param {string|null} teamId - Team ID (null to remove)
   * @returns {Promise<Object>} Updated employee
   */
  assignTeam: async (employeeId, teamId) => {
    return api.patch(`/employees/${employeeId}/team`, {
      team_id: teamId,
    });
  },

  /**
   * Assign a new manager to an employee.
   * @param {string} employeeId - Employee ID
   * @param {string} managerId - Manager's employee ID
   * @returns {Promise<Object>} Updated employee
   */
  assignManager: async (employeeId, managerId) => {
    return api.patch(`/employees/${employeeId}/manager`, {
      manager_id: managerId,
    });
  },
};

/**
 * Audit Log Service
 * API functions for viewing audit logs and change history.
 */

import { api } from './api';

export const auditLogService = {
  /**
   * List audit logs with optional filters, pagination, and ordering.
   * @param {Object} filters - Filter options
   * @param {string} [filters.entity_type] - Filter by entity type ('EMPLOYEE', 'DEPARTMENT', 'TEAM', 'USER')
   * @param {string} [filters.entity_id] - Filter by specific entity ID
   * @param {string} [filters.change_type] - Filter by change type ('CREATE', 'UPDATE', 'DELETE')
   * @param {string} [filters.changed_by_user_id] - Filter by user who made the change
   * @param {string} [filters.date_from] - Filter by date from (YYYY-MM-DD or ISO)
   * @param {string} [filters.date_to] - Filter by date to (YYYY-MM-DD or ISO)
   * @param {number} [filters.limit=25] - Results per page
   * @param {number} [filters.offset=0] - Pagination offset
   * @param {string} [filters.order='desc'] - Sort order ('asc' or 'desc', by created_at)
   * @returns {Promise<{items: Array, total: number, limit: number, offset: number}>}
   */
  listAuditLogs: async (filters = {}) => {
    return api.get('/audit-logs', filters);
  },

  /**
   * Get a single audit log by ID.
   * @param {string} id - Audit log ID (UUID)
   * @returns {Promise<Object>} Audit log details with full state information
   */
  getAuditLog: async (id) => {
    return api.get(`/audit-logs/${id}`);
  },
};

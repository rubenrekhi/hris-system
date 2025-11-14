/**
 * Export Service
 * API functions for exporting employee data in various formats.
 */

import { api } from './api';

/**
 * Helper function to trigger file download in the browser.
 * @param {Blob} blob - File blob
 * @param {string} filename - Desired filename for download
 */
export function downloadFile(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

export const exportService = {
  // ============================================================================
  // Directory Exports (Flat List)
  // ============================================================================

  /**
   * Export employee directory as CSV.
   * @param {Object} filters - Export filters
   * @param {string} [filters.department_id] - Filter by department
   * @param {string} [filters.team_id] - Filter by team
   * @param {string} [filters.status] - Filter by status ('ACTIVE' or 'ON_LEAVE')
   * @param {string} [filters.hired_from] - Filter by hire date from (YYYY-MM-DD)
   * @param {string} [filters.hired_to] - Filter by hire date to (YYYY-MM-DD)
   * @returns {Promise<Blob>} CSV file blob
   */
  exportDirectoryCSV: async (filters = {}) => {
    return api.download('/exports/directory/csv', filters);
  },

  /**
   * Export employee directory as Excel.
   * @param {Object} filters - Export filters (same as CSV)
   * @returns {Promise<Blob>} Excel file blob
   */
  exportDirectoryExcel: async (filters = {}) => {
    return api.download('/exports/directory/excel', filters);
  },

  /**
   * Export employee directory as PDF.
   * @param {Object} filters - Export filters (same as CSV)
   * @returns {Promise<Blob>} PDF file blob
   */
  exportDirectoryPDF: async (filters = {}) => {
    return api.download('/exports/directory/pdf', filters);
  },

  // ============================================================================
  // Org Chart Exports (Hierarchical)
  // ============================================================================

  /**
   * Export organizational chart as CSV.
   * @param {Object} filters - Export filters
   * @param {string} [filters.department_id] - Filter by department
   * @param {string} [filters.team_id] - Filter by team
   * @param {string} [filters.status] - Filter by status ('ACTIVE' or 'ON_LEAVE')
   * @param {string} [filters.hired_from] - Filter by hire date from (YYYY-MM-DD)
   * @param {string} [filters.hired_to] - Filter by hire date to (YYYY-MM-DD)
   * @returns {Promise<Blob>} CSV file blob with hierarchy levels
   */
  exportOrgChartCSV: async (filters = {}) => {
    return api.download('/exports/org-chart/csv', filters);
  },

  /**
   * Export organizational chart as Excel.
   * @param {Object} filters - Export filters (same as CSV)
   * @returns {Promise<Blob>} Excel file blob with visual hierarchy
   */
  exportOrgChartExcel: async (filters = {}) => {
    return api.download('/exports/org-chart/excel', filters);
  },

  /**
   * Export organizational chart as PDF.
   * @param {Object} filters - Export filters (same as CSV)
   * @returns {Promise<Blob>} PDF file blob with visual org chart
   */
  exportOrgChartPDF: async (filters = {}) => {
    return api.download('/exports/org-chart/pdf', filters);
  },

  // ============================================================================
  // Helper Methods
  // ============================================================================

  /**
   * Download file helper (re-exported for convenience).
   * Triggers browser download of a blob with specified filename.
   *
   * @param {Blob} blob - File blob from export function
   * @param {string} filename - Desired filename (e.g., 'employees.csv')
   *
   * @example
   * const blob = await exportService.exportDirectoryCSV();
   * exportService.downloadFile(blob, 'employee-directory.csv');
   */
  downloadFile,
};

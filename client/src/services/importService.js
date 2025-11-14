/**
 * Import Service
 * API functions for bulk import operations.
 */

import { api } from './api';

export const importService = {
  /**
   * Import employees from CSV or Excel file.
   * Supports .csv and .xlsx formats.
   *
   * @param {File} file - File object from input element
   * @returns {Promise<Object>} Import result
   * @returns {number} return.total_rows - Total rows in file
   * @returns {number} return.successful_imports - Number of successful imports
   * @returns {Array} return.failed_rows - Array of failed rows with errors
   * @returns {Array} return.created_employee_ids - IDs of created employees
   * @returns {Array} return.warnings - Any warnings from the import
   *
   * @example
   * const file = event.target.files[0];
   * const result = await importService.importEmployees(file);
   * if (result.failed_rows.length > 0) {
   *   console.log('Some rows failed:', result.failed_rows);
   * }
   */
  importEmployees: async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    return api.upload('/imports/employees', formData);
  },
};

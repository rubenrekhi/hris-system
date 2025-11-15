/**
 * CSV Helper Functions
 * Utilities for generating and downloading CSV files.
 */

/**
 * Generate a sample CSV template for employee bulk import.
 * Includes headers and example data rows.
 *
 * @returns {Blob} CSV file blob
 */
export function generateSampleCSV() {
  const headers = [
    'name',
    'email',
    'title',
    'hired_on',
    'salary',
    'status',
    'manager_email',
    'department_name',
    'team_name',
  ];

  const exampleRows = [
    [
      'John Doe',
      'john.doe@company.com',
      'Software Engineer',
      '2024-01-15',
      '120000',
      'ACTIVE',
      'jane.smith@company.com',
      'Engineering',
      'Backend',
    ],
    [
      'Jane Smith',
      'jane.smith@company.com',
      'Engineering Manager',
      '2023-06-01',
      '150000',
      'ACTIVE',
      '',
      'Engineering',
      '',
    ],
    [
      'Bob Wilson',
      'bob.wilson@company.com',
      'Product Designer',
      '2024-03-20',
      '110000',
      'ACTIVE',
      'jane.smith@company.com',
      'Product',
      'Design',
    ],
  ];

  // Build CSV content
  const csvContent = [
    headers.join(','),
    ...exampleRows.map((row) => row.map((cell) => escapeCSVCell(cell)).join(',')),
  ].join('\n');

  return new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
}

/**
 * Generate a CSV error report from failed import rows.
 *
 * @param {Array} failedRows - Array of failed row objects from import result
 * @param {number} failedRows[].row_number - Row number in original file
 * @param {string} failedRows[].email - Email from failed row
 * @param {string} failedRows[].error_message - Error description
 * @param {Object} failedRows[].row_data - Original row data
 * @returns {Blob} CSV file blob with error details
 */
export function generateErrorReportCSV(failedRows) {
  if (!failedRows || failedRows.length === 0) {
    return new Blob(['No errors to report'], { type: 'text/csv;charset=utf-8;' });
  }

  // Extract all possible keys from row_data
  const allKeys = new Set(['row_number', 'error_message']);
  failedRows.forEach((row) => {
    if (row.row_data) {
      Object.keys(row.row_data).forEach((key) => allKeys.add(key));
    }
  });

  const headers = Array.from(allKeys);

  // Build CSV rows
  const csvRows = failedRows.map((failedRow) => {
    return headers.map((header) => {
      if (header === 'row_number') {
        return failedRow.row_number || '';
      } else if (header === 'error_message') {
        return failedRow.error_message || '';
      } else if (failedRow.row_data && failedRow.row_data[header] !== undefined) {
        return failedRow.row_data[header];
      }
      return '';
    });
  });

  // Build CSV content
  const csvContent = [
    headers.join(','),
    ...csvRows.map((row) => row.map((cell) => escapeCSVCell(String(cell))).join(',')),
  ].join('\n');

  return new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
}

/**
 * Trigger browser download of a CSV blob.
 *
 * @param {Blob} blob - CSV blob to download
 * @param {string} filename - Desired filename (e.g., 'template.csv')
 */
export function downloadCSV(blob, filename) {
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

/**
 * Escape a CSV cell value to handle commas, quotes, and newlines.
 *
 * @param {string} cell - Cell value to escape
 * @returns {string} Escaped cell value
 */
function escapeCSVCell(cell) {
  if (cell === null || cell === undefined) {
    return '';
  }

  const stringCell = String(cell);

  // If cell contains comma, quote, or newline, wrap in quotes and escape quotes
  if (stringCell.includes(',') || stringCell.includes('"') || stringCell.includes('\n')) {
    return `"${stringCell.replace(/"/g, '""')}"`;
  }

  return stringCell;
}

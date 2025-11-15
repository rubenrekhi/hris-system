/**
 * Utility functions for formatting data for display.
 */

/**
 * Format a number as USD currency.
 * @param {number} amount - The amount to format
 * @returns {string} Formatted currency string (e.g., "$75,000")
 */
export function formatCurrency(amount) {
  if (amount == null) return 'N/A';

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

/**
 * Format an ISO date string to a readable format.
 * @param {string} dateString - ISO date string (e.g., "2024-01-15")
 * @returns {string} Formatted date string (e.g., "Jan 15, 2024")
 */
export function formatDate(dateString) {
  if (!dateString) return 'N/A';

  const date = new Date(dateString);

  // Check if date is valid
  if (isNaN(date.getTime())) return 'Invalid Date';

  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(date);
}

/**
 * Format employee status for display.
 * @param {string} status - Employee status (e.g., "ACTIVE", "ON_LEAVE")
 * @returns {string} Formatted status string (e.g., "Active", "On Leave")
 */
export function formatStatus(status) {
  if (!status) return 'N/A';

  // Convert SNAKE_CASE to Title Case
  return status
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

/**
 * Format an ISO datetime string to a readable format with time.
 * @param {string} dateString - ISO datetime string (e.g., "2024-01-15T14:30:00Z")
 * @returns {string} Formatted datetime string (e.g., "Jan 15, 2024 2:30 PM")
 */
export function formatDateTime(dateString) {
  if (!dateString) return 'N/A';

  const date = new Date(dateString);

  // Check if date is valid
  if (isNaN(date.getTime())) return 'Invalid Date';

  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(date);
}

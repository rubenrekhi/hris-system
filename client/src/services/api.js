/**
 * Base API client for communicating with the FastAPI backend.
 * Provides HTTP methods with automatic error handling and response parsing.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Custom error class for API errors with status code and response data.
 */
export class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

/**
 * Format error message from FastAPI error response.
 * Handles both HTTPException errors (string detail) and Pydantic validation errors (array detail).
 * @param {any} detail - Error detail from FastAPI response
 * @returns {string} Formatted error message
 */
function formatErrorMessage(detail) {
  // HTTPException: detail is a string
  if (typeof detail === 'string') {
    return detail;
  }

  // Pydantic validation error: detail is an array of validation errors
  if (Array.isArray(detail)) {
    const errors = detail.map((err) => {
      const field = err.loc ? err.loc.slice(1).join('.') : 'unknown';
      const message = err.msg || 'validation error';
      return `${field}: ${message}`;
    });
    return errors.join('; ');
  }

  // Fallback for unexpected formats
  return JSON.stringify(detail);
}

/**
 * Handle API response, extracting data or throwing ApiError.
 * Includes special handling for 401 (redirect to login).
 * @param {Response} response - Fetch API response object
 * @returns {Promise<any>} Parsed JSON data or null for 204 responses
 * @throws {ApiError} If response is not ok
 */
async function handleResponse(response) {
  if (!response.ok) {
    // Handle 401 Unauthorized - redirect to backend login
    if (response.status === 401) {
      window.location.href = `${API_BASE_URL}/auth/login`;
      throw new ApiError('Authentication required', 401, {});
    }

    let errorData;
    try {
      errorData = await response.json();
    } catch {
      errorData = { detail: response.statusText };
    }

    // Format error message from FastAPI response
    const message = errorData.detail
      ? formatErrorMessage(errorData.detail)
      : `HTTP ${response.status}: ${response.statusText}`;

    throw new ApiError(message, response.status, errorData);
  }

  // Handle empty responses (204 No Content, DELETE operations)
  if (response.status === 204) {
    return null;
  }

  // Parse and return JSON
  return response.json();
}

/**
 * Build query string from parameters object.
 * Filters out undefined and null values.
 * @param {Object} params - Query parameters
 * @returns {URLSearchParams}
 */
function buildQueryParams(params = {}) {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.append(key, value);
    }
  });

  return searchParams;
}

/**
 * Base API client with HTTP methods.
 */
export const api = {
  /**
   * Perform a GET request.
   * @param {string} endpoint - API endpoint (e.g., '/employees')
   * @param {Object} params - Query parameters
   * @returns {Promise<any>} Response data
   */
  get: async (endpoint, params = {}) => {
    const queryString = buildQueryParams(params).toString();
    const url = queryString
      ? `${API_BASE_URL}${endpoint}?${queryString}`
      : `${API_BASE_URL}${endpoint}`;

    const response = await fetch(url, {
      credentials: 'include', // Include cookies for authentication
    });
    return handleResponse(response);
  },

  /**
   * Perform a POST request.
   * @param {string} endpoint - API endpoint
   * @param {Object} data - Request body data
   * @returns {Promise<any>} Response data
   */
  post: async (endpoint, data) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include', // Include cookies for authentication
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  /**
   * Perform a PATCH request.
   * @param {string} endpoint - API endpoint
   * @param {Object} data - Request body data
   * @returns {Promise<any>} Response data
   */
  patch: async (endpoint, data) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include', // Include cookies for authentication
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  /**
   * Perform a DELETE request.
   * @param {string} endpoint - API endpoint
   * @returns {Promise<any>} Response data (usually null)
   */
  delete: async (endpoint) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'DELETE',
      credentials: 'include', // Include cookies for authentication
    });
    return handleResponse(response);
  },

  /**
   * Upload a file using multipart/form-data.
   * @param {string} endpoint - API endpoint
   * @param {FormData} formData - FormData object with file
   * @returns {Promise<any>} Response data
   */
  upload: async (endpoint, formData) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      credentials: 'include', // Include cookies for authentication
      body: formData, // Don't set Content-Type, browser handles it with boundary
    });
    return handleResponse(response);
  },

  /**
   * Download a file (blob).
   * @param {string} endpoint - API endpoint
   * @param {Object} params - Query parameters
   * @returns {Promise<Blob>} File blob
   * @throws {ApiError} If download fails
   */
  download: async (endpoint, params = {}) => {
    const queryString = buildQueryParams(params).toString();
    const url = queryString
      ? `${API_BASE_URL}${endpoint}?${queryString}`
      : `${API_BASE_URL}${endpoint}`;

    const response = await fetch(url, {
      credentials: 'include', // Include cookies for authentication
    });

    if (!response.ok) {
      throw new ApiError(
        `Download failed: ${response.statusText}`,
        response.status,
        null
      );
    }

    return response.blob();
  },
};

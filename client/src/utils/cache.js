/**
 * Lightweight in-memory cache utility for API responses.
 * Stores data with TTL (time-to-live) for automatic expiration.
 */

class Cache {
  constructor() {
    this.store = new Map();
  }

  /**
   * Set a value in the cache with optional TTL.
   * @param {string} key - Cache key
   * @param {*} value - Value to cache
   * @param {number} ttl - Time to live in seconds (default: 300 = 5 minutes)
   */
  set(key, value, ttl = 300) {
    const expiresAt = Date.now() + ttl * 1000;
    this.store.set(key, { value, expiresAt });
  }

  /**
   * Get a value from the cache.
   * Returns null if key doesn't exist or has expired.
   * @param {string} key - Cache key
   * @returns {*} Cached value or null
   */
  get(key) {
    const entry = this.store.get(key);

    if (!entry) {
      return null;
    }

    // Check if expired
    if (Date.now() > entry.expiresAt) {
      this.store.delete(key);
      return null;
    }

    return entry.value;
  }

  /**
   * Check if a key exists and is not expired.
   * @param {string} key - Cache key
   * @returns {boolean}
   */
  has(key) {
    return this.get(key) !== null;
  }

  /**
   * Clear a specific key or entire cache.
   * @param {string} [key] - Cache key to clear, or omit to clear all
   */
  clear(key) {
    if (key) {
      this.store.delete(key);
    } else {
      this.store.clear();
    }
  }

  /**
   * Get all cache keys (for debugging).
   * @returns {string[]}
   */
  keys() {
    return Array.from(this.store.keys());
  }
}

// Export singleton instance
export const cache = new Cache();

/**
 * Validate a PromiseBlock's required fields.
 * @param {Object} promise
 * @returns {string|null} Error message or null if valid.
 */
export function validatePromiseBlock(promise) {
  if (!promise || typeof promise !== 'object') {
    return 'Promise must be an object';
  }
  if (typeof promise.id !== 'string') {
    return 'Missing or invalid id';
  }
  if (typeof promise.wallet !== 'string' || !promise.wallet.endsWith('Q')) {
    return 'wallet must be a .Q-suffixed string';
  }
  if (typeof promise.intent !== 'string') {
    return 'Missing or invalid intent';
  }
  if (promise.amount !== undefined && typeof promise.amount !== 'number') {
    return 'amount, if provided, must be a number';
  }
  if (promise.emotion !== undefined && typeof promise.emotion !== 'string') {
    return 'emotion, if provided, must be a string';
  }
  if (typeof promise.signature !== 'string') {
    return 'Missing or invalid signature';
  }
  return null;
}

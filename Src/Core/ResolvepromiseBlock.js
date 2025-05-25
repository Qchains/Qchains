import crypto from 'crypto';
import { fetchQuantumTimestamp } from '../services/qtime.js';
import { validatePromiseBlock } from '../validators/promiseValidator.js';

/**
 * @typedef {Object} PromiseBlock
 * @property {string} id
 * @property {string} wallet
 * @property {string} intent
 * @property {number} [amount]
 * @property {string} [emotion]
 * @property {string} signature
 */

/**
 * @typedef {Object} ResolvedBlock
 * @property {string} id
 * @property {string} wallet
 * @property {string} intent
 * @property {number} [amount]
 * @property {string} [emotion]
 * @property {string} signature
 * @property {'fulfilled'} status
 * @property {number} timestamp
 * @property {number} nonce
 * @property {string} resultHash
 */

/** Compute SHA-256 hash of a string. */
function computeHash(data) {
  return crypto.createHash('sha256').update(data).digest('hex');
}

/**
 * Finalizes a PromiseBlock into a ResolvedBlock.
 * @param {PromiseBlock} promise
 * @returns {ResolvedBlock}
 * @throws {Error} If validation fails.
 */
export function resolvePromiseBlock(promise) {
  // 1. Validate structure
  const errorMsg = validatePromiseBlock(promise);
  if (errorMsg) {
    throw new Error(`PromiseBlock validation failed: ${errorMsg}`);
  }

  // 2. Anchor to QTime
  const timestamp = fetchQuantumTimestamp();

  // 3. Add random nonce
  const nonce = Math.floor(Math.random() * Number.MAX_SAFE_INTEGER);

  // 4. Assemble resolved object
  const resolved = {
    ...promise,
    status: 'fulfilled',
    timestamp,
    nonce,
  };

  // 5. Compute resultHash over full block
  resolved.resultHash = computeHash(JSON.stringify(resolved));

  return resolved;
}

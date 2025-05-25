// src/core/resolvePromiseBlock.js

import crypto from 'crypto';
import { fetchQuantumTimestamp } from '../services/qtime.js';
import { validatePromiseBlock } from '../validators/promiseValidator.js';

/**
 * @typedef {Object} PromiseBlock
 * @property {string}   id         - Unique identifier for the promise
 * @property {string}   wallet     - `.Q`-suffixed wallet address (e.g. 'QAQ123Q')
 * @property {string}   intent     - What this promise intends to do
 * @property {number}   [amount]   - Optional amount to transfer
 * @property {string}   [emotion]  - Emotional tag or sigil context
 * @property {string}   signature  - Cryptographic signature of the promise payload
 */

/**
 * @typedef {Object} ResolvedBlock
 * @property {string}   id
 * @property {string}   wallet
 * @property {string}   intent
 * @property {number}   [amount]
 * @property {string}   [emotion]
 * @property {string}   signature
 * @property {'fulfilled'} status
 * @property {number}   timestamp   - QTime-anchored timestamp
 * @property {number}   nonce       - Random nonce for additional entropy
 * @property {string}   resultHash  - SHA-256 hash of the entire block
 */

/**
 * Compute a SHA-256 hash of the given data.
 * @param {string} data
 * @returns {string}
 */
function computeHash(data) {
  return crypto.createHash('sha256').update(data).digest('hex');
}

/**
 * Finalizes a PromiseBlock into a ResolvedBlock.
 *
 * @param {PromiseBlock} promise
 * @returns {ResolvedBlock}
 * @throws {Error} If the promise is invalid.
 */
export function resolvePromiseBlock(promise) {
  // 1. Validate the incoming block
  const errorMsg = validatePromiseBlock(promise);
  if (errorMsg) {
    throw new Error(`PromiseBlock validation failed: ${errorMsg}`);
  }

  // 2. Anchor to QTime (could be a quantum-synced timestamp service)
  const timestamp = fetchQuantumTimestamp(); // e.g. returns Date.now() wrapped with quantum entropy

  // 3. Add a random nonce for extra entropy
  const nonce = Math.floor(Math.random() * Number.MAX_SAFE_INTEGER);

  // 4. Assemble the resolved block
  const resolved = {
    ...promise,
    status: 'fulfilled',
    timestamp,
    nonce,
  };

  // 5. Compute the resultHash over the full block
  resolved.resultHash = computeHash(JSON.stringify(resolved));

  return resolved;
}

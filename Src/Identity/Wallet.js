/**
 * Generate a `.Q`-suffixed wallet address from a user ID.
 * @param {string} userId
 * @returns {string}
 */
export function generateWalletQ(userId) {
  return `Q${userId.slice(0, 6)}Q`;
}

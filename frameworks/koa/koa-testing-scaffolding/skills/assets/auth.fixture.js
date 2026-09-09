/**
 * @file auth.fixture.js
 * @description Test fixture for generating mock JWT authentication tokens and headers
 * without requiring live authentication endpoints during unit and integration tests.
 */

const jwt = require('jsonwebtoken');

const TEST_JWT_SECRET = process.env.JWT_SECRET || 'test-jwt-secret-key-1234567890';

/**
 * Generates a signed JWT authentication token for a given user payload.
 *
 * @param {Object} [payload={}] - User claims to embed in token
 * @param {number} [payload.userId=1] - Mock user identifier
 * @param {string} [payload.role='USER'] - User role (e.g. ADMIN, AGENT, USER)
 * @param {string} [payload.email='test@example.com'] - User email address
 * @param {string} [expiresIn='1h'] - Expiration window
 * @returns {string} Signed JWT Bearer token string
 */
function generateAuthToken(payload = {}, expiresIn = '1h') {
  const defaultClaims = {
    userId: 1,
    role: 'USER',
    email: 'test@example.com',
    ...payload,
  };

  return jwt.sign(defaultClaims, TEST_JWT_SECRET, { expiresIn });
}

/**
 * Generates an Authorization header object with a valid Bearer token.
 *
 * @param {Object} [payload={}] - User claims
 * @returns {{ Authorization: string }} Header object suitable for Supertest .set()
 */
function getAuthHeader(payload = {}) {
  const token = generateAuthToken(payload);
  return { Authorization: `Bearer ${token}` };
}

module.exports = {
  TEST_JWT_SECRET,
  generateAuthToken,
  getAuthHeader,
};

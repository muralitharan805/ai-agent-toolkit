/**
 * @file external-api.mock.js
 * @description Mock harness for third-party HTTP services (e.g. Stripe, CRM, SMS gateways).
 * Prevents real outbound network calls during test execution and simulates edge cases (timeouts, errors).
 */

const { vi } = require('vitest');

/**
 * Creates a controllable mock client for external HTTP requests.
 * Simulates standard success, network error, timeout, and custom response scenarios.
 *
 * @returns {Object} Controllable mock client
 */
function createExternalApiMock() {
  const mockGet = vi.fn();
  const mockPost = vi.fn();
  const mockPut = vi.fn();
  const mockDelete = vi.fn();

  return {
    get: mockGet,
    post: mockPost,
    put: mockPut,
    delete: mockDelete,

    /**
     * Configures the mock to resolve with a successful payload.
     * @param {Object} data - Response body
     * @param {number} [status=200] - HTTP status code
     */
    mockSuccess(data, status = 200) {
      mockGet.mockResolvedValue({ status, data });
      mockPost.mockResolvedValue({ status, data });
    },

    /**
     * Configures the mock to reject with a simulated network timeout.
     */
    mockTimeout() {
      const timeoutErr = new Error('Gateway Timeout');
      timeoutErr.code = 'ECONNABORTED';
      mockGet.mockRejectedValue(timeoutErr);
      mockPost.mockRejectedValue(timeoutErr);
    },

    /**
     * Configures the mock to reject with an HTTP error status.
     * @param {number} status - HTTP status (e.g. 400, 429, 500)
     * @param {string} message - Error description
     */
    mockHttpError(status, message) {
      const err = new Error(message);
      err.response = { status, data: { error: message } };
      mockGet.mockRejectedValue(err);
      mockPost.mockRejectedValue(err);
    },

    /**
     * Resets all call history and configured implementations.
     */
    reset() {
      mockGet.mockReset();
      mockPost.mockReset();
      mockPut.mockReset();
      mockDelete.mockReset();
    },
  };
}

module.exports = {
  createExternalApiMock,
};

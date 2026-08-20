/**
 * Core API utilities for 墨灵 Dashboard
 * @module api/core
 */

import { markApiOffline, markApiOnline } from './connectivity.js';
import { logger } from '../utils/logger.js';

const BASE_URL = import.meta.env.VITE_API_BASE || '/api';
const DEFAULT_TIMEOUT_MS = 15_000;
const MAX_RETRIES = 2;
const RETRY_DELAY_MS = 1000;

const errorEventTarget = new EventTarget();

export const API_ERROR_EVENT = 'api-error';

/**
 * Subscribe to API error events
 * @param {(error: ApiError) => void} callback - Error handler
 * @returns {() => void} Unsubscribe function
 */
export function onApiError(callback) {
  errorEventTarget.addEventListener(API_ERROR_EVENT, callback);
  return () => errorEventTarget.removeEventListener(API_ERROR_EVENT, callback);
}

/**
 * Dispatch an API error event
 * @param {ApiError} error
 */
function dispatchApiError(error) {
  errorEventTarget.dispatchEvent(new CustomEvent(API_ERROR_EVENT, { detail: error }));
}

/**
 * Base API error class
 * @extends Error
 */
export class ApiError extends Error {
  /**
   * @param {string} message
   * @param {{ status?: number|null, code?: string|null, path?: string|null, response?: Response|null }} [options]
   */
  constructor(message, { status = null, code = null, path = null, response = null } = {}) {
    super(message);
    this.name = 'ApiError';
    /** @type {number|null} */
    this.status = status;
    /** @type {string|null} */
    this.code = code;
    /** @type {string|null} */
    this.path = path;
    /** @type {Response|null} */
    this.response = response;
  }
}

/**
 * Network error (no connection)
 * @extends ApiError
 */
export class NetworkError extends ApiError {
  /** @param {string} message */
  constructor(message) {
    super(message, { code: 'NETWORK_ERROR' });
    this.name = 'NetworkError';
  }
}

/**
 * Request timeout error
 * @extends ApiError
 */
export class TimeoutError extends ApiError {
  /** @param {string} message */
  constructor(message) {
    super(message, { code: 'TIMEOUT_ERROR' });
    this.name = 'TimeoutError';
  }
}

/**
 * Authentication error (401)
 * @extends ApiError
 */
export class AuthError extends ApiError {
  /** @param {string} message */
  constructor(message) {
    super(message, { code: 'AUTH_ERROR', status: 401 });
    this.name = 'AuthError';
  }
}

/**
 * Forbidden error (403)
 * @extends ApiError
 */
export class ForbiddenError extends ApiError {
  /** @param {string} message */
  constructor(message) {
    super(message, { code: 'FORBIDDEN_ERROR', status: 403 });
    this.name = 'ForbiddenError';
  }
}

/**
 * Not found error (404)
 * @extends ApiError
 */
export class NotFoundError extends ApiError {
  /** @param {string} message */
  constructor(message) {
    super(message, { code: 'NOT_FOUND_ERROR', status: 404 });
    this.name = 'NotFoundError';
  }
}

/**
 * Server error (500)
 * @extends ApiError
 */
export class ServerError extends ApiError {
  /** @param {string} message */
  constructor(message) {
    super(message, { code: 'SERVER_ERROR', status: 500 });
    this.name = 'ServerError';
  }
}

/**
 * Create appropriate error class from HTTP response
 * @param {Response} response
 * @param {string} path
 * @param {string} errorText
 * @returns {ApiError}
 */
function createErrorFromResponse(response, path, errorText) {
  const status = response.status;
  const baseMessage = `API Error ${status}: ${response.statusText}`;
  const detailMessage = errorText ? `${baseMessage}. Details: ${errorText}` : baseMessage;

  switch (status) {
    case 401:
      return new AuthError(detailMessage);
    case 403:
      return new ForbiddenError(detailMessage);
    case 404:
      return new NotFoundError(detailMessage);
    case 500:
      return new ServerError(detailMessage);
    default:
      return new ApiError(detailMessage, { status, path });
  }
}

/**
 * Merge multiple AbortSignals into one
 * @param {AbortSignal[]} signals
 * @returns {AbortSignal}
 */
function anySignal(signals) {
  const controller = new AbortController();
  for (const sig of signals) {
    if (sig.aborted) {
      controller.abort(sig.reason);
      return controller.signal;
    }
    sig.addEventListener('abort', () => controller.abort(sig.reason), { once: true });
  }
  return controller.signal;
}

/**
 * Execute a single HTTP request
 * @param {string} path - API endpoint path
 * @param {{ method?: string, body?: unknown, signal?: AbortSignal }} opts
 * @returns {Promise<unknown>} Parsed response data
 * @throws {ApiError} On HTTP errors
 * @throws {NetworkError} On network failures
 */
async function executeRequest(path, opts) {
  const { method = 'GET', body, signal: externalSignal } = opts;
  const timeoutSignal = AbortSignal.timeout(DEFAULT_TIMEOUT_MS);
  const fetchSignal = externalSignal
    ? anySignal([externalSignal, timeoutSignal])
    : timeoutSignal;

  const fetchOpts = {
    method,
    headers: { 'Content-Type': 'application/json' },
    signal: fetchSignal,
  };
  if (body !== undefined) {
    fetchOpts.body = typeof body === 'string' ? body : JSON.stringify(body);
  }

  const response = await fetch(`${BASE_URL}${path}`, fetchOpts);

  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error');
    throw createErrorFromResponse(response, path, errorText);
  }

  const data = await response.json();
  markApiOnline();
  return data;
}

/**
 * Make an API request with retry logic
 * @param {string} path - API endpoint path
 * @param {{ retries?: number, method?: string, body?: unknown, signal?: AbortSignal }} [opts]
 * @returns {Promise<T>} Parsed response data
 * @template T
 * @throws {ApiError} On HTTP errors after all retries
 * @throws {TimeoutError} On request timeout
 * @throws {NetworkError} On network failures
 */
export async function request(path, opts = {}) {
  const { retries = MAX_RETRIES, ...restOpts } = opts;
  let lastError = null;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      return await executeRequest(path, restOpts);
    } catch (error) {
      lastError = error;
      logger.warn(`Request failed (attempt ${attempt + 1}/${retries + 1}): ${path}`, error.message);

      if (error instanceof AuthError || error instanceof NotFoundError) {
        break;
      }

      if (attempt < retries) {
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAY_MS * (attempt + 1)));
      }
    }
  }

  if (lastError?.name === 'AbortError') {
    const timeoutError = new TimeoutError(`Request timeout after ${DEFAULT_TIMEOUT_MS}ms: ${path}`);
    dispatchApiError(timeoutError);
    throw timeoutError;
  }

  if (lastError instanceof TypeError && lastError.message.includes('fetch')) {
    const networkError = new NetworkError(`Network error: Unable to connect to ${BASE_URL}. Is the server running?`);
    markApiOffline(networkError.message);
    dispatchApiError(networkError);
    throw networkError;
  }

  dispatchApiError(lastError);
  throw lastError;
}

export { apiConnectivity, markApiOffline, markApiOnline } from './connectivity.js';

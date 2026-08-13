/**
 * Detect API connectivity failures surfaced by api/index.js request().
 * @param {unknown} message
 */
export function isNetworkConnectivityError(message) {
  if (typeof message !== 'string' || !message) return false;
  return message.includes('Network error: Unable to connect');
}

/**
 * Hide per-page network errors when the global API offline banner is shown.
 * @param {unknown} message
 * @param {boolean} apiOffline
 */
export function filterPageErrorMessage(message, apiOffline) {
  if (!message) return '';
  if (apiOffline && isNetworkConnectivityError(message)) return '';
  return String(message);
}

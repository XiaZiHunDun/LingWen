/**
 * API Client for LingWen Dashboard
 * Communicates with FastAPI backend on port 8765
 */

const BASE_URL = 'http://localhost:8765/api';

/**
 * Make a request to the API with error handling
 * @param {string} path - API endpoint path
 * @returns {Promise<any>} Response JSON
 * @throws {Error} Descriptive error on failure
 */
async function request(path) {
  try {
    const response = await fetch(`${BASE_URL}${path}`);

    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      throw new Error(`API Error ${response.status}: ${response.statusText}. Details: ${errorText}`);
    }

    return response.json();
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(`Network error: Unable to connect to ${BASE_URL}. Is the server running?`);
    }
    throw error;
  }
}

/**
 * Fetch overview data from the API
 * @returns {Promise<OverviewResponse>} Overview data
 */
export async function fetchOverview() {
  return request('/overview');
}

/**
 * Fetch chapters data from the API
 * @param {string} [range] - Optional range filter (e.g., "1-50")
 * @returns {Promise<ChaptersResponse>} Chapters data
 */
export async function fetchChapters(range) {
  const query = range ? `?range=${encodeURIComponent(range)}` : '';
  return request(`/chapters${query}`);
}

/**
 * Fetch health status from the API
 * @returns {Promise<HealthResponse>} Health data
 */
export async function fetchHealth() {
  return request('/health');
}
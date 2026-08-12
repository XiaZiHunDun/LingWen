import { describe, expect, it } from 'vitest';
import {
  filterPageErrorMessage,
  isNetworkConnectivityError,
} from '../../src/utils/networkErrorUtils.js';

describe('networkErrorUtils', () => {
  it('detects connectivity errors from api client', () => {
    const msg = 'Network error: Unable to connect to /api. Is the server running?';
    expect(isNetworkConnectivityError(msg)).toBe(true);
  });

  it('does not treat API 500 as connectivity', () => {
    expect(isNetworkConnectivityError('API Error 500: Internal Server Error')).toBe(false);
  });

  it('filters page errors when api offline', () => {
    const msg = 'Network error: Unable to connect to /api. Is the server running?';
    expect(filterPageErrorMessage(msg, true)).toBe('');
    expect(filterPageErrorMessage('api down', true)).toBe('api down');
    expect(filterPageErrorMessage(msg, false)).toBe(msg);
  });
});

// tests/unit/text-scale.spec.js
import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  TEXT_SCALE_OPTIONS,
  applyTextScale,
  getStoredTextScale,
  initTextScale,
  setTextScale,
} from '../../src/utils/textScale.js';

describe('textScale', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute('data-text-scale');
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  test('getStoredTextScale defaults to normal', () => {
    expect(getStoredTextScale()).toBe('normal');
    localStorage.setItem('lingwen_dashboard_text_scale', 'large');
    expect(getStoredTextScale()).toBe('large');
  });

  test('setTextScale persists and applies attribute', () => {
    const next = setTextScale('xlarge');
    expect(next).toBe('xlarge');
    expect(document.documentElement.getAttribute('data-text-scale')).toBe('xlarge');
    expect(localStorage.getItem('lingwen_dashboard_text_scale')).toBe('xlarge');
  });

  test('applyTextScale clears attribute for normal', () => {
    document.documentElement.setAttribute('data-text-scale', 'large');
    applyTextScale('normal');
    expect(document.documentElement.hasAttribute('data-text-scale')).toBe(false);
  });

  test('setTextScale ignores invalid values', () => {
    expect(setTextScale('huge')).toBe('normal');
  });

  test('initTextScale applies stored value', () => {
    localStorage.setItem('lingwen_dashboard_text_scale', 'large');
    initTextScale();
    expect(document.documentElement.getAttribute('data-text-scale')).toBe('large');
  });

  test('TEXT_SCALE_OPTIONS lists presets', () => {
    expect(TEXT_SCALE_OPTIONS.map((o) => o.id)).toEqual(['normal', 'large', 'xlarge']);
  });
});

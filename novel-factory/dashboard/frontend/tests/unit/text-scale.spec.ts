import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  TEXT_SCALE_OPTIONS,
  getStoredTextScale,
  applyTextScale,
  setTextScale,
} from '../../src/utils/textScale.js';

describe('textScale', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute('data-text-scale');
  });

  afterEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute('data-text-scale');
  });

  it('defaults to normal when nothing stored', () => {
    expect(getStoredTextScale()).toBe('normal');
  });

  it('persists and applies large scale', () => {
    const scale = setTextScale('large');
    expect(scale).toBe('large');
    expect(localStorage.getItem('lingwen_dashboard_text_scale')).toBe('large');
    expect(document.documentElement.getAttribute('data-text-scale')).toBe('large');
  });

  it('removes attribute for normal scale', () => {
    setTextScale('xlarge');
    setTextScale('normal');
    expect(document.documentElement.hasAttribute('data-text-scale')).toBe(false);
  });

  it('falls back for invalid stored value', () => {
    localStorage.setItem('lingwen_dashboard_text_scale', 'bogus');
    expect(getStoredTextScale()).toBe('normal');
    applyTextScale(getStoredTextScale());
    expect(document.documentElement.hasAttribute('data-text-scale')).toBe(false);
  });

  it('exports three scale options', () => {
    expect(TEXT_SCALE_OPTIONS.map((o) => o.id)).toEqual(['normal', 'large', 'xlarge']);
  });
});

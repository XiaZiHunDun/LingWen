import { describe, expect, it } from 'vitest';
import {
  isCompanionBrandedProject,
  resolveEffectiveCreationMode,
} from '../../src/utils/effectiveCreationMode.js';

describe('effectiveCreationMode', () => {
  it('forces companion for 创作伴侣 project', () => {
    const project = { slug: 'demo', name: 'E2E 创作伴侣' };
    expect(isCompanionBrandedProject(project)).toBe(true);
    expect(resolveEffectiveCreationMode('advance', project)).toBe('companion');
    expect(resolveEffectiveCreationMode('studio', project)).toBe('companion');
  });

  it('forces companion for companion slug', () => {
    const project = { slug: 'my-companion-book', name: '某书' };
    expect(isCompanionBrandedProject(project)).toBe(true);
    expect(resolveEffectiveCreationMode('advance', project)).toBe('companion');
  });

  it('keeps advance for non-branded projects', () => {
    const project = { slug: 'anye-xinbiao', name: '暗夜信标' };
    expect(isCompanionBrandedProject(project)).toBe(false);
    expect(resolveEffectiveCreationMode('advance', project)).toBe('advance');
  });
});

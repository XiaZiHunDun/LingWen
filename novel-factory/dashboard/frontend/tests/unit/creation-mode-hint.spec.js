// tests/unit/creation-mode-hint.spec.js
import { describe, test, expect } from 'vitest';
import { creationModeMeta, resolveTodayPrimaryAction } from '../../src/utils/creationModeHint.js';

describe('creationModeHint', () => {
  test('creationModeMeta empty mode', () => {
    expect(creationModeMeta('').label).toBe('未知模式');
    expect(creationModeMeta('studio').tagline).toContain('工厂');
  });

  test('resolveTodayPrimaryAction prioritizes pending decisions', () => {
    const action = resolveTodayPrimaryAction({ pendingDecisions: 2, creationMode: 'companion' });
    expect(action.id).toBe('decisions');
    expect(action.label).toContain('待决策');
  });

  test('resolveTodayPrimaryAction micro task for companion', () => {
    const action = resolveTodayPrimaryAction({
      creationMode: 'companion',
      chaptersWritten: 2,
      activeChapter: 2,
      microTask: { remaining: 120, current: 380, goal: 500 },
    });
    expect(action.id).toBe('write-micro');
    expect(action.label).toMatch(/再写 120 字/);
    expect(action.chapter).toBe(2);
  });

  test('resolveTodayPrimaryAction ripples when no decisions', () => {
    const action = resolveTodayPrimaryAction({ pendingRipples: 3, creationMode: 'companion' });
    expect(action.id).toBe('ripples');
    expect(action.label).toContain('一致性变更');
  });

  test('resolveTodayPrimaryAction batch progress', () => {
    const action = resolveTodayPrimaryAction({ batchActive: true, creationMode: 'companion' });
    expect(action.id).toBe('batch');
    expect(action.nav).toBe('produce');
  });

  test('resolveTodayPrimaryAction wizard incomplete', () => {
    const action = resolveTodayPrimaryAction({ wizardProgressPct: 40, creationMode: 'companion' });
    expect(action.id).toBe('wizard');
    expect(action.wizard).toBe(true);
  });

  test('resolveTodayPrimaryAction companion first chapter', () => {
    const action = resolveTodayPrimaryAction({ creationMode: 'companion', chaptersWritten: 0 });
    expect(action.id).toBe('write-first');
    expect(action.chapter).toBe(1);
  });

  test('resolveTodayPrimaryAction advance pulse when coverage complete', () => {
    const action = resolveTodayPrimaryAction({ creationMode: 'advance', coveragePct: 100 });
    expect(action.id).toBe('pulse');
  });

  test('resolveTodayPrimaryAction studio produce when coverage low', () => {
    const action = resolveTodayPrimaryAction({ creationMode: 'studio', coveragePct: 20 });
    expect(action.id).toBe('studio-produce');
  });

  test('resolveTodayPrimaryAction reviewer ripples', () => {
    const action = resolveTodayPrimaryAction({ isReviewer: true, pendingRipples: 2 });
    expect(action.id).toBe('ripples');
    expect(action.tab).toBe('ripples');
  });

  test('resolveTodayPrimaryAction reviewer decisions', () => {
    const action = resolveTodayPrimaryAction({ isReviewer: true, pendingDecisions: 1 });
    expect(action.id).toBe('decisions');
    expect(action.label).toContain('查看');
  });

  test('resolveTodayPrimaryAction reviewer insight fallback', () => {
    const action = resolveTodayPrimaryAction({ isReviewer: true });
    expect(action.id).toBe('insight');
    expect(action.nav).toBe('insight');
  });

  test('resolveTodayPrimaryAction companion continue with alerts', () => {
    const action = resolveTodayPrimaryAction({
      creationMode: 'companion',
      chaptersWritten: 3,
      alertCount: 2,
    });
    expect(action.id).toBe('write');
    expect(action.reason).toContain('脉络预警');
  });

  test('resolveTodayPrimaryAction advance produce when coverage low', () => {
    const action = resolveTodayPrimaryAction({ creationMode: 'advance', coveragePct: 40 });
    expect(action.id).toBe('produce');
    expect(action.nav).toBe('produce');
  });

  test('resolveTodayPrimaryAction studio quality when coverage complete', () => {
    const action = resolveTodayPrimaryAction({ creationMode: 'studio', coveragePct: 100 });
    expect(action.id).toBe('studio-quality');
  });
});

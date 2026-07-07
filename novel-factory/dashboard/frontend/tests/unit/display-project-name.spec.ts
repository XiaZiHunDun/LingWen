import { describe, expect, it } from 'vitest';
import {
  formatDisplayLabel,
  formatDisplayProjectName,
  normalizeVolumePlanVolume,
  normalizeVolumePlanVolumes,
} from '../../src/utils/displayProjectName.js';

describe('formatDisplayLabel', () => {
  it('strips E2E prefix from dev seed names', () => {
    expect(formatDisplayLabel('E2E 创作伴侣')).toBe('创作伴侣');
    expect(formatDisplayLabel('E2E 分享卷纲')).toBe('分享卷纲');
    expect(formatDisplayLabel('EZE 分享案例')).toBe('分享案例');
  });

  it('returns original when no prefix', () => {
    expect(formatDisplayLabel('星陨纪元')).toBe('星陨纪元');
  });

  it('handles empty', () => {
    expect(formatDisplayLabel('')).toBe('');
  });

  it('aliases formatDisplayProjectName', () => {
    expect(formatDisplayProjectName('E2E 创作伴侣')).toBe('创作伴侣');
  });
});

describe('normalizeVolumePlanVolumes', () => {
  it('strips E2E from volume labels on load', () => {
    const rows = normalizeVolumePlanVolumes([
      { label: 'E2E 分享卷纲', start_chapter: 1, end_chapter: 5 },
    ]);
    expect(rows[0].label).toBe('分享卷纲');
  });

  it('normalizeVolumePlanVolume preserves other fields', () => {
    const row = normalizeVolumePlanVolume({
      label: 'E2E 卷一',
      core_conflict: '冲突',
      locked: true,
    });
    expect(row.label).toBe('卷一');
    expect(row.core_conflict).toBe('冲突');
    expect((row as { locked?: boolean }).locked).toBe(true);
  });

  it('strips E2E/EZE from core_conflict on load', () => {
    const rows = normalizeVolumePlanVolumes([
      { label: '第一卷', start_chapter: 1, end_chapter: 5, core_conflict: 'EZE 分享案例' },
    ]);
    expect(rows[0].core_conflict).toBe('分享案例');
  });
});

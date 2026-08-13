// tests/unit/use-creator-page-header.spec.ts — human-first 导出/发布顶栏可见性

import { describe, test, expect } from 'vitest';
import { computed, ref } from 'vue';
import { useCreatorPageHeader } from '../../src/composables/useCreatorPageHeader.js';

function mountHeader(creationMode: string | null = 'companion') {
  const overview = ref(
    creationMode
      ? {
          creation_mode: creationMode,
          slug: 'demo',
          name: 'Demo',
          deviation_count: 0,
          alert_count: 0,
        }
      : null,
  );
  const uiProfile = computed(() => ({
    creation_mode_badge_hint: true,
    studio_creation_mode_badge_hint: true,
    deviation_min_severity: 'all',
  }));
  const saveMessage = ref('');
  return useCreatorPageHeader({ uiProfile, overview, saveMessage });
}

describe('useCreatorPageHeader', () => {
  test('human-first companion shows export/publish in header actions', () => {
    const api = mountHeader('companion');
    expect(api.showHeaderPublishExport.value).toBe(true);
    expect(api.showHeaderActionsRow.value).toBe(true);
    expect(api.showPageTitle.value).toBe(false);
    expect(api.showHeaderPreferences.value).toBe(false);
  });

  test('human-first advance shows export/publish in header actions', () => {
    const api = mountHeader('advance');
    expect(api.showHeaderPublishExport.value).toBe(true);
    expect(api.showHeaderActionsRow.value).toBe(true);
  });

  test('studio keeps export/publish when overview loaded', () => {
    const api = mountHeader('studio');
    expect(api.showHeaderPublishExport.value).toBe(true);
    expect(api.showPageTitle.value).toBe(true);
    expect(api.showHeaderPreferences.value).toBe(true);
  });

  test('no overview hides publish/export row', () => {
    const api = mountHeader(null);
    expect(api.showHeaderPublishExport.value).toBe(false);
    expect(api.showHeaderActionsRow.value).toBe(false);
  });
});

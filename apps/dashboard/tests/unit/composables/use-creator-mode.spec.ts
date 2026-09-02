import { computed, ref } from 'vue';
import { describe, expect, it, vi } from 'vitest';

vi.mock('@/composables/useEffectiveCreationMode.js', () => ({
  // 让 effective mode 直接等于原始模式，仅验证矩阵解析逻辑
  useEffectiveCreationMode: (rawMode: { value: string }) => computed(() => rawMode.value),
}));

import { useCreatorMode } from '@/composables/useCreatorMode';
import { CREATOR_WRITE_WORKBENCH_MATRIX } from '@/config/creatorPanelMatrix';

describe('useCreatorMode', () => {
  it('默认 mode 回退 companion', () => {
    const c = useCreatorMode({ source: ref(null) });
    expect(c.creationMode.value).toBe('companion');
  });

  it('暴露当前 mode 与 isMode 判断', () => {
    const c = useCreatorMode({ source: ref({ creation_mode: 'advance' }) });
    expect(c.creationMode.value).toBe('advance');
    expect(c.isMode('advance')).toBe(true);
    expect(c.isMode('companion')).toBe(false);
  });

  it('按矩阵解析写栏面板可见性（studio hidden / companion required）', () => {
    const studio = useCreatorMode({ source: ref({ creation_mode: 'studio' }) });
    expect(studio.isWriteWorkbenchPanelVisible('workbenchLayout')).toBe(false);

    const companion = useCreatorMode({ source: ref({ creation_mode: 'companion' }) });
    expect(companion.isWriteWorkbenchPanelVisible('workbenchLayout')).toBe(true);
    expect(companion.isHumanFirstDesk()).toBe(true);
  });

  it('标记 optional_collapsed 面板为默认折叠', () => {
    const c = useCreatorMode({ source: ref({ creation_mode: 'advance' }) });
    expect(c.isPanelCollapsed(CREATOR_WRITE_WORKBENCH_MATRIX, 'goalCard')).toBe(true);
    expect(c.isPanelCollapsed(CREATOR_WRITE_WORKBENCH_MATRIX, 'microTaskBar')).toBe(false);
  });

  it('按模式开启人类习惯书桌布局', () => {
    const companion = useCreatorMode({ source: ref({ creation_mode: 'companion' }) });
    expect(companion.isWriteWorkbenchLayoutEnabled({})).toBe(true);

    const studio = useCreatorMode({ source: ref({ creation_mode: 'studio' }) });
    expect(studio.isWriteWorkbenchLayoutEnabled({})).toBe(false);
  });
});
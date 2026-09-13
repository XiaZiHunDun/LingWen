/**
 * Phase 65 — WorldImportExport.vue unit tests.
 *
 * WorldImportExport is the markdown import/export panel on the World
 * page (Phase 117 Task 21). It wraps useWorldImportExport composable
 * with two action buttons + inline summary display.
 *
 * 4 tests covering render + button states + import/export flows.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';

// Stub the composable before importing the component.
const importMarkdownMock = vi.fn();
const exportMarkdownMock = vi.fn();

vi.mock('@/composables/world/useWorldImportExport.js', () => ({
  useWorldImportExport: () => ({
    importMarkdown: importMarkdownMock,
    exportMarkdown: exportMarkdownMock,
  }),
}));

// Import after vi.mock so the mock is in place.
import WorldImportExport from '@/components/world/WorldImportExport.vue';

beforeEach(() => {
  importMarkdownMock.mockReset();
  exportMarkdownMock.mockReset();
});

// ---------------------------------------------------------------------------
// Render
// ---------------------------------------------------------------------------

describe('WorldImportExport — render', () => {
  it('renders import + export buttons with stable testids', () => {
    const wrapper = mount(WorldImportExport);

    expect(wrapper.find('[data-testid="world-import-btn"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="world-export-btn"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="world-import-btn"]').text()).toContain('导入');
    expect(wrapper.find('[data-testid="world-export-btn"]').text()).toContain('导出');
  });

  it('does not render summary element before any action runs', () => {
    const wrapper = mount(WorldImportExport);
    expect(wrapper.find('[data-testid="export-summary"]').exists()).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Import flow
// ---------------------------------------------------------------------------

describe('WorldImportExport — import action', () => {
  it('calls importMarkdown and shows summary with imported counts', async () => {
    importMarkdownMock.mockResolvedValue({
      characters_imported: 3,
      factions_imported: 2,
      lore_imported: 5,
    });

    const wrapper = mount(WorldImportExport);
    await wrapper.find('[data-testid="world-import-btn"]').trigger('click');
    await flushPromises();

    expect(importMarkdownMock).toHaveBeenCalledTimes(1);
    const summary = wrapper.find('[data-testid="export-summary"]');
    expect(summary.exists()).toBe(true);
    expect(summary.text()).toContain('3');
    expect(summary.text()).toContain('2');
    expect(summary.text()).toContain('5');
    expect(summary.text()).toContain('导入');
  });
});

// ---------------------------------------------------------------------------
// Export flow
// ---------------------------------------------------------------------------

describe('WorldImportExport — export action', () => {
  it('calls exportMarkdown and shows summary with files_written + output_dir', async () => {
    exportMarkdownMock.mockResolvedValue({
      files_written: 4,
      output_dir: '/tmp/world-export',
    });

    const wrapper = mount(WorldImportExport);
    await wrapper.find('[data-testid="world-export-btn"]').trigger('click');
    await flushPromises();

    expect(exportMarkdownMock).toHaveBeenCalledTimes(1);
    const summary = wrapper.find('[data-testid="export-summary"]');
    expect(summary.exists()).toBe(true);
    expect(summary.text()).toContain('4');
    expect(summary.text()).toContain('/tmp/world-export');
    expect(summary.text()).toContain('导出');
  });

  it('overwrites summary on subsequent action (import then export)', async () => {
    importMarkdownMock.mockResolvedValue({
      characters_imported: 1,
      factions_imported: 1,
      lore_imported: 1,
    });
    exportMarkdownMock.mockResolvedValue({
      files_written: 7,
      output_dir: '/tmp/world-export-2',
    });

    const wrapper = mount(WorldImportExport);
    await wrapper.find('[data-testid="world-import-btn"]').trigger('click');
    await flushPromises();
    expect(wrapper.find('[data-testid="export-summary"]').text()).toContain('导入');

    await wrapper.find('[data-testid="world-export-btn"]').trigger('click');
    await flushPromises();
    expect(wrapper.find('[data-testid="export-summary"]').text()).toContain('导出');
    expect(wrapper.find('[data-testid="export-summary"]').text()).toContain('7');
  });
});

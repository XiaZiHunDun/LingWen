import { describe, expect, it } from 'vitest';
import {
  buildCreatorWorkspaceTabs,
  getModeUiProfileDefaults,
  isChapterTaskCardsVisible,
  isHubProduceTabVisible,
  isPanelVisible,
  isPulseSubpanelVisible,
  isWriteWorkbenchLayoutEnabled,
  isWriteWorkbenchPanelVisible,
  isHumanFirstDeskMode,
  splitHumanFirstDeskTabs,
  resolveDefaultWorkspaceTab,
  STYLE_STRENGTH_LEVELS,
  CREATOR_WORKSPACE_TAB_MATRIX,
  CREATOR_PULSE_SUBPANEL_MATRIX,
} from '../../src/config/creatorPanelMatrix.js';

describe('creatorPanelMatrix', () => {
  it('companion defaults to write tab and shows all workspace tabs', () => {
    const tabs = buildCreatorWorkspaceTabs('companion');
    expect(resolveDefaultWorkspaceTab('companion')).toBe('write');
    expect(tabs.map((t) => t.id)).toEqual(['write', 'pulse', 'memory', 'settings']);
  });

  it('advance defaults to write tab and enables human-first workbench', () => {
    expect(resolveDefaultWorkspaceTab('advance')).toBe('write');
    expect(isPanelVisible(CREATOR_WORKSPACE_TAB_MATRIX, 'advance', 'write')).toBe(true);
    expect(isPanelVisible(CREATOR_WORKSPACE_TAB_MATRIX, 'advance', 'pulse')).toBe(true);
    const profile = getModeUiProfileDefaults('advance');
    expect(profile.creator_write_workbench).toBe(true);
    expect(isWriteWorkbenchLayoutEnabled('advance', profile)).toBe(true);
  });

  it('human-first desk splits memory/settings into secondary tabs', () => {
    expect(isHumanFirstDeskMode('advance')).toBe(true);
    expect(isHumanFirstDeskMode('studio')).toBe(false);
    const { primary, secondary } = splitHumanFirstDeskTabs('advance');
    expect(primary.map((t) => t.id)).toEqual(['write', 'pulse']);
    expect(secondary.map((t) => t.id)).toEqual(['memory', 'settings']);
  });

  it('studio hides write tab and defaults to pulse', () => {
    const tabs = buildCreatorWorkspaceTabs('studio');
    expect(tabs.map((t) => t.id)).not.toContain('write');
    expect(resolveDefaultWorkspaceTab('studio')).toBe('pulse');
  });

  it('pulse subpanels hide advance batch for companion and studio', () => {
    expect(isPulseSubpanelVisible('companion', 'advanceBatch')).toBe(false);
    expect(isPulseSubpanelVisible('advance', 'advanceBatch')).toBe(true);
    expect(isPulseSubpanelVisible('studio', 'advanceBatch')).toBe(false);
  });

  it('produce hub tabs hidden for companion', () => {
    expect(isHubProduceTabVisible('companion', 'studio')).toBe(false);
    expect(isHubProduceTabVisible('advance', 'studio')).toBe(true);
    expect(isHubProduceTabVisible('studio', 'chapters')).toBe(true);
  });

  it('mode ui defaults set collapsed mode guide', () => {
    expect(getModeUiProfileDefaults('companion').creator_mode_guide_default_collapsed).toBe(true);
    expect(getModeUiProfileDefaults('companion').creator_write_workbench).toBe(true);
    expect(getModeUiProfileDefaults('companion').agent_execution_mode_default).toBe('preview');
    expect(getModeUiProfileDefaults('advance').advance_batch_panel_on_creator).toBe(true);
    expect(getModeUiProfileDefaults('studio').show_studio_workflow).toBe(true);
  });

  it('companion write workbench on by profile default', () => {
    const profile = getModeUiProfileDefaults('companion');
    expect(isWriteWorkbenchLayoutEnabled('companion', profile)).toBe(true);
    expect(isChapterTaskCardsVisible('companion')).toBe(false);
    expect(isChapterTaskCardsVisible('advance')).toBe(true);
    expect(isWriteWorkbenchPanelVisible('companion', 'scopeBar')).toBe(true);
    expect(isWriteWorkbenchPanelVisible('companion', 'directorPaths')).toBe(true);
    expect(STYLE_STRENGTH_LEVELS[0].label).toBe('只建议');
  });

  it('pulse matrix covers structure graph for advance', () => {
    expect(isPanelVisible(CREATOR_PULSE_SUBPANEL_MATRIX, 'advance', 'structureGraph')).toBe(true);
  });
});

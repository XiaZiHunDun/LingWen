/**
 * useCreatorPageProviders — 注册创作页各栏 provide/inject 上下文
 */
import { provide } from 'vue';
import { CREATOR_MODE_GUIDE_KEY, createCreatorModeGuideContext } from '../components/creator/creatorModeGuideKey.js';
import { CREATOR_ONBOARDING_KEY, createCreatorOnboardingContext } from '../components/creator/creatorOnboardingKey.js';
import { CREATOR_SETTINGS_KEY, createCreatorSettingsContext } from '../components/creator/creatorSettingsKey.js';
import { CREATOR_WRITE_KEY, createCreatorWriteContext } from '../components/creator/creatorWriteKey.js';
import { CREATOR_PULSE_KEY, createCreatorPulseContext } from '../components/creator/creatorPulseKey.js';
import { CREATOR_ADVANCE_BATCH_KEY, createCreatorAdvanceBatchContext } from '../components/creator/creatorAdvanceBatchKey.js';
import { CREATOR_BATCH_HISTORY_KEY, createCreatorBatchHistoryContext } from '../components/creator/creatorBatchHistoryKey.js';
import { CREATOR_VOLUME_PLAN_KEY, createCreatorVolumePlanContext } from '../components/creator/creatorVolumePlanKey.js';
import { CREATOR_PAGE_CHROME_KEY, createCreatorPageChromeContext } from '../components/creator/creatorPageChromeKey.js';
import { CREATOR_PRODUCT_TOOLS_KEY, createCreatorProductToolsContext } from '../components/creator/creatorProductToolsKey.js';

/**
 * @param {{
 *   chromeContext: Record<string, unknown>,
 *   pulsePanelContext: Record<string, unknown>,
 *   advanceBatchPanelContext: Record<string, unknown>,
 *   writePanelContext: Record<string, unknown>,
 *   settingsPanelContext: Record<string, unknown>,
 *   onboardingPanelContext: Record<string, unknown>,
 *   modeGuidePanelContext: Record<string, unknown>,
 *   batchHistoryPanelContext: Record<string, unknown>,
 *   volumePlanPanelContext: Record<string, unknown>,
 *   productToolsPanelContext: Record<string, unknown>,
 * }} contexts
 */
export function useCreatorPageProviders(contexts) {
  provide(CREATOR_PAGE_CHROME_KEY, createCreatorPageChromeContext(contexts.chromeContext));
  provide(CREATOR_PULSE_KEY, createCreatorPulseContext(contexts.pulsePanelContext));
  provide(CREATOR_ADVANCE_BATCH_KEY, createCreatorAdvanceBatchContext(contexts.advanceBatchPanelContext));
  provide(CREATOR_WRITE_KEY, createCreatorWriteContext(contexts.writePanelContext));
  provide(CREATOR_SETTINGS_KEY, createCreatorSettingsContext(contexts.settingsPanelContext));
  provide(CREATOR_ONBOARDING_KEY, createCreatorOnboardingContext(contexts.onboardingPanelContext));
  provide(CREATOR_MODE_GUIDE_KEY, createCreatorModeGuideContext(contexts.modeGuidePanelContext));
  provide(CREATOR_BATCH_HISTORY_KEY, createCreatorBatchHistoryContext(contexts.batchHistoryPanelContext));
  provide(CREATOR_VOLUME_PLAN_KEY, createCreatorVolumePlanContext(contexts.volumePlanPanelContext));
  provide(CREATOR_PRODUCT_TOOLS_KEY, createCreatorProductToolsContext(contexts.productToolsPanelContext));
}

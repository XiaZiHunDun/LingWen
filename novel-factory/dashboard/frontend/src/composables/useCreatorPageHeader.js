/**
 * useCreatorPageHeader — 创作页顶栏徽章与偏离计数（从 CreatorPage 抽出）
 */
import { computed } from 'vue';
import { isHumanFirstDeskMode } from '../config/creatorPanelMatrix.js';
import { useEffectiveCreationMode } from './useEffectiveCreationMode.js';

/**
 * @param {{
 *   uiProfile: import('vue').ComputedRef<object>,
 *   overview: import('vue').Ref<object|null>,
 *   saveMessage: import('vue').Ref<string>,
 * }} deps
 */
export function useCreatorPageHeader(deps) {
  const { uiProfile, overview, saveMessage } = deps;

  const creationMode = useEffectiveCreationMode(
    computed(() => overview.value?.creation_mode ?? null),
    computed(() => (overview.value
      ? { slug: overview.value.slug, name: overview.value.name }
      : null)),
  );

  const humanFirstDesk = computed(() => isHumanFirstDeskMode(creationMode.value));

  const modeLabel = computed(() => {
    if (!overview.value) return '';
    const map = { companion: '陪伴', advance: '推进', studio: '工作室' };
    return map[overview.value.creation_mode] || overview.value.creation_mode;
  });

  const creationModeBadgeHintText = computed(() => {
    if (!overview.value) return '';
    const mode = overview.value.creation_mode;
    if (uiProfile.value.creation_mode_badge_hint) {
      if (mode === 'companion') return '陪伴：人主笔 + P0 守门';
      if (mode === 'advance') return '推进：人定卷纲 + batch 产章';
    }
    if (uiProfile.value.studio_creation_mode_badge_hint && mode === 'studio') {
      return '工作室：工厂流水线与批量产章';
    }
    return '';
  });

  const modeBadgeHintEnabled = computed(
    () => Boolean(
      (uiProfile.value.creation_mode_badge_hint || uiProfile.value.studio_creation_mode_badge_hint)
      && creationModeBadgeHintText.value,
    ),
  );

  const displayDeviationCount = computed(() => {
    const ov = overview.value;
    if (!ov) return 0;
    if (uiProfile.value.deviation_min_severity === 'alert') {
      return ov.alert_count || 0;
    }
    return ov.deviation_count || 0;
  });

  const displayDeviationBadge = computed(() => displayDeviationCount.value > 0);

  const showCreationModeBadge = computed(() => {
    if (!overview.value || humanFirstDesk.value) return false;
    return true;
  });

  const showPageTitle = computed(() => !humanFirstDesk.value);

  const showHeaderPreferences = computed(() => !humanFirstDesk.value);

  const showHeaderPublishExport = computed(() => Boolean(overview.value));

  const showHeaderRefresh = computed(() => !humanFirstDesk.value);

  const showHeaderActionsRow = computed(() => {
    if (!overview.value) return false;
    if (showHeaderPreferences.value || showHeaderPublishExport.value || showHeaderRefresh.value) {
      return true;
    }
    return false;
  });

  function showCreationModeBadgeHint() {
    if (!creationModeBadgeHintText.value) return;
    saveMessage.value = creationModeBadgeHintText.value;
  }

  return {
    modeLabel,
    creationModeBadgeHintText,
    modeBadgeHintEnabled,
    showCreationModeBadge,
    showPageTitle,
    showHeaderPreferences,
    showHeaderPublishExport,
    showHeaderRefresh,
    showHeaderActionsRow,
    displayDeviationCount,
    displayDeviationBadge,
    showCreationModeBadgeHint,
  };
}

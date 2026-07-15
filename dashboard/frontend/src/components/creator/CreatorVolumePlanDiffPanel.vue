<!--
  CreatorVolumePlanDiffPanel — 卷纲 diff 预览与导出（从 CreatorVolumePlanPanel 拆出）
-->
<template>
          <label
            v-if="vp.uiProfile.volume_plan_diff_type_filter && vp.volumePlanDiffPreview?.has_changes && vp.volumePlanDiffTypeOptions.length"
            class="meta-line volume-plan-diff-type-filter"
            data-testid="volume-plan-diff-type-filter-label"
          >
            变更类型
            <select
              v-model="vp.volumePlanDiffTypeFilter"
              class="vol-input"
              data-testid="volume-plan-diff-type-filter"
            >
              <option value="">全部</option>
              <option
                v-for="diffType in vp.volumePlanDiffTypeOptions"
                :key="`vol-diff-type-${diffType}`"
                :value="diffType"
              >
                {{ diffType }}
              </option>
            </select>
          </label>
          <label
            v-if="vp.uiProfile.volume_plan_diff_volume_filter && vp.volumePlanDiffPreview?.has_changes && vp.volumePlanDiffVolumeOptions.length"
            class="meta-line volume-plan-diff-volume-filter"
            data-testid="volume-plan-diff-volume-filter-label"
          >
            变更卷
            <select
              v-model="vp.volumePlanDiffVolumeFilter"
              class="vol-input"
              data-testid="volume-plan-diff-volume-filter"
            >
              <option value="">全部卷</option>
              <option
                v-for="volLabel in vp.volumePlanDiffVolumeOptions"
                :key="`vol-diff-volume-${volLabel}`"
                :value="volLabel"
              >
                卷{{ volLabel }}
              </option>
            </select>
          </label>
          <div
            v-if="vp.uiProfile.volume_plan_diff_preview && vp.volumePlanDiffPreview?.has_changes && !vp.uiProfile.volume_plan_diff_auto_collapse"
            class="volume-plan-diff-panel pixel-border"
            data-testid="volume-plan-diff-panel"
          >
            <p class="meta-line">
              卷纲未保存变更
              <span
                v-if="vp.uiProfile.volume_plan_diff_change_count && vp.volumePlanDiffChangeCount"
                class="volume-plan-diff-count"
                data-testid="volume-plan-diff-change-count"
              >
                {{ vp.volumePlanDiffChangeCount }} 处
              </span>
            </p>
            <CreatorVolumePlanDiffContent />
          </div>
          <details
            v-else-if="vp.uiProfile.volume_plan_diff_preview && vp.volumePlanDiffPreview && vp.uiProfile.volume_plan_diff_auto_collapse"
            class="volume-plan-diff-panel pixel-border"
            :open="vp.volumePlanDiffExpanded"
            data-testid="volume-plan-diff-panel"
            @toggle="vp.onVolumePlanDiffToggle"
          >
            <summary class="volume-plan-diff-summary" data-testid="volume-plan-diff-summary">
              {{ vp.volumePlanDiffPreview?.has_changes ? '卷纲未保存变更' : '卷纲与已保存一致' }}
              <span
                v-if="vp.uiProfile.volume_plan_diff_change_count && vp.volumePlanDiffPreview?.has_changes && vp.volumePlanDiffChangeCount"
                class="volume-plan-diff-count"
                data-testid="volume-plan-diff-change-count"
              >
                {{ vp.volumePlanDiffChangeCount }} 处
              </span>
            </summary>
            <template v-if="vp.volumePlanDiffPreview?.has_changes">
              <CreatorVolumePlanDiffContent key-prefix="collapse-" />
            </template>
            <p v-else class="meta-line" data-testid="volume-plan-diff-no-changes">
              当前编辑与已保存卷纲一致
            </p>
          </details>
</template>

<script setup>
import { inject } from 'vue';
import { CREATOR_VOLUME_PLAN_KEY } from './creatorVolumePlanKey.js';
import CreatorVolumePlanDiffContent from './CreatorVolumePlanDiffContent.vue';

const vp = inject(CREATOR_VOLUME_PLAN_KEY);
if (!vp) {
  throw new Error('CreatorVolumePlanDiffPanel requires CREATOR_VOLUME_PLAN_KEY provide');
}
</script>

<style scoped>
.volume-plan-diff-count {
  margin-left: var(--space-xs);
  padding: 1px 4px;
  border-radius: 2px;
  color: #a60;
  background: rgba(255, 200, 80, 0.35);
  font-family: 'Press Start 2P', monospace;
  font-size: 6px;
}

.volume-plan-diff-volume-filter {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  margin-top: var(--space-xs);
  margin-left: var(--space-sm);
}

.volume-plan-diff-type-filter {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  margin-top: var(--space-xs);
}

.volume-plan-diff-summary {
  cursor: pointer;
  font-family: 'Press Start 2P', monospace;
  font-size: var(--text-xs);
}

.volume-plan-diff-panel {
  margin-top: var(--space-sm);
  padding: var(--space-xs);
  background: rgba(200, 160, 80, 0.1);
}
</style>

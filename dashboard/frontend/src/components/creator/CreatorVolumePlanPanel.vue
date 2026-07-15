<!--
  CreatorVolumePlanPanel.vue — 脉络栏卷纲编辑区（从 CreatorPage 拆出）
-->
<template>
  <div class="volume-plan-panel" data-testid="volume-plan-panel">
    <div class="volume-plan-header" :class="{ 'volume-plan-header--inline': hideTitle }">
      <h3 v-if="!hideTitle" class="subsection-title">卷纲</h3>
      <button
        type="button"
        class="mini-btn pixel-border"
        data-testid="add-volume-btn"
        @click="vp.addVolume"
      >
        + 卷
      </button>
    </div>
    <CreatorVolumePlanTemplatesPanel />
    <CreatorVolumePlanEditPanel />
    <CreatorVolumePlanDiffPanel />
    <CreatorVolumePlanMergeSplitPanel />
  </div>
</template>

<script setup>
import { inject } from 'vue';
import { CREATOR_VOLUME_PLAN_KEY } from './creatorVolumePlanKey.js';
import CreatorVolumePlanTemplatesPanel from './CreatorVolumePlanTemplatesPanel.vue';
import CreatorVolumePlanEditPanel from './CreatorVolumePlanEditPanel.vue';
import CreatorVolumePlanDiffPanel from './CreatorVolumePlanDiffPanel.vue';
import CreatorVolumePlanMergeSplitPanel from './CreatorVolumePlanMergeSplitPanel.vue';

defineProps({
  hideTitle: { type: Boolean, default: false },
});

const vp = inject(CREATOR_VOLUME_PLAN_KEY);
if (!vp) {
  throw new Error('CreatorVolumePlanPanel requires CREATOR_VOLUME_PLAN_KEY provide');
}
</script>

<style scoped>
.subsection-title {
  font-size: var(--text-sm);
  margin: var(--space-md) 0 var(--space-xs);
}

.volume-plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.volume-plan-header--inline {
  justify-content: flex-end;
  margin-bottom: var(--space-xs);
}

.mini-btn {
  font-size: var(--text-xs);
  padding: 2px 6px;
  cursor: pointer;
}
</style>

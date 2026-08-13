<!--
  CreatorVolumePlanCollabPanel.vue — 卷纲 diff 协作批注（从 CreatorVolumePlanPanel 拆出）
-->
<template>
  <div
    v-if="vp.uiProfile.volume_plan_diff_share_collab_v2 && vp.volumePlanDiffCollabRows.length"
    class="volume-plan-diff-collab-panel pixel-border"
    data-testid="volume-plan-diff-collab-panel"
  >
    <p class="meta-line">协作批注（分享链接 v3 附带，按卷联动 diff）</p>
    <label
      v-for="row in vp.volumePlanDiffCollabRows"
      :key="`collab-edit-${row.label}`"
      class="volume-plan-diff-collab-row"
    >
      卷 {{ row.label }}
      <input
        class="vol-input volume-plan-diff-collab-input"
        :data-testid="`diff-collab-note-input-${row.label}`"
        :value="vp.diffCollabNotes[row.label] || ''"
        placeholder="@reviewer 请确认"
        @input="vp.setDiffCollabNote(row.label, $event.target.value)"
      />
    </label>
  </div>
</template>

<script setup>
import { inject } from 'vue';
import { CREATOR_VOLUME_PLAN_KEY } from './creatorVolumePlanKey.js';

const vp = inject(CREATOR_VOLUME_PLAN_KEY);
</script>

<style scoped>
.volume-plan-diff-collab-panel {
  margin: var(--space-xs) 0;
  padding: var(--space-sm);
}

.volume-plan-diff-collab-row {
  display: block;
  margin: var(--space-xs) 0;
  font-size: var(--text-md);
}

.volume-plan-diff-collab-input {
  display: block;
  width: 100%;
  margin-top: 2px;
}
</style>

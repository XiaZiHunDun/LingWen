<!--
  CreatorVolumePlanMergeSplitPanel — 卷纲合并/拆分（从 CreatorVolumePlanPanel 拆出）
-->
<template>
  <div
    v-if="vp.editableVolumes.length >= 2"
    class="volume-merge-panel pixel-border"
    data-testid="volume-merge-panel"
  >
    <h3 class="subsection-title">合并向导</h3>
    <ol class="merge-wizard-steps" data-testid="merge-wizard-steps">
      <li :class="{ 'merge-wizard-steps__item--active': mergeStep >= 1 }">选卷范围</li>
      <li :class="{ 'merge-wizard-steps__item--active': mergeStep >= 2 }">预览冲突</li>
      <li :class="{ 'merge-wizard-steps__item--active': mergeStep >= 3 }">应用合并</li>
    </ol>

    <template v-if="mergeStep === 1">
      <div class="merge-range">
        <label>
          从
          <select v-model.number="vp.mergeStartIdx" class="vol-input" data-testid="merge-start-select">
            <option v-for="(vol, idx) in vp.editableVolumes" :key="`s-${idx}`" :value="idx">
              {{ vol.label || `卷${idx + 1}` }}
            </option>
          </select>
        </label>
        <label>
          到
          <select v-model.number="vp.mergeEndIdx" class="vol-input" data-testid="merge-end-select">
            <option
              v-for="(vol, idx) in vp.editableVolumes"
              :key="`e-${idx}`"
              :value="idx"
              :disabled="idx < vp.mergeStartIdx"
            >
              {{ vol.label || `卷${idx + 1}` }}
            </option>
          </select>
        </label>
        <input
          v-model="vp.mergeLabel"
          class="vol-input vol-conflict"
          data-testid="merge-label-input"
          placeholder="合并后卷名（可选）"
        />
      </div>
      <button
        type="button"
        class="mini-btn pixel-border"
        data-testid="merge-wizard-next-btn"
        :disabled="vp.mergeStartIdx > vp.mergeEndIdx"
        @click="mergeStep = 2"
      >
        下一步：预览
      </button>
    </template>

    <template v-else-if="mergeStep === 2">
      <ul class="merge-conflict-preview" data-testid="merge-conflict-preview">
        <li v-for="(line, idx) in vp.mergeConflictPreview" :key="idx">{{ line }}</li>
      </ul>
      <div class="merge-wizard-actions">
        <button type="button" class="mini-btn" @click="mergeStep = 1">上一步</button>
        <button type="button" class="mini-btn pixel-border" data-testid="merge-wizard-confirm-btn" @click="mergeStep = 3">
          确认继续
        </button>
      </div>
    </template>

    <template v-else>
      <p class="meta-line">范围与预览已确认，点击下方应用合并。</p>
      <div class="merge-wizard-actions">
        <button type="button" class="mini-btn" @click="mergeStep = 2">返回预览</button>
        <button
          type="button"
          class="mini-btn pixel-border"
          data-testid="apply-merge-btn"
          :disabled="vp.mergeApplying || vp.mergeStartIdx > vp.mergeEndIdx"
          @click="applyMerge"
        >
          {{ vp.mergeApplying ? '合并中…' : '应用合并' }}
        </button>
      </div>
    </template>
  </div>
  <p
    v-if="vp.mergePreview"
    class="meta-line"
    data-testid="merge-preview-line"
  >
    已合并为「{{ vp.mergePreview.merged_label }}」· {{ vp.mergePreview.merged_range }} · 请保存卷纲
  </p>
  <div
    v-if="vp.editableVolumes.length >= 1"
    class="volume-split-panel pixel-border"
    data-testid="volume-split-panel"
  >
    <h3 class="subsection-title">拆分向导</h3>
    <div class="merge-range">
      <label>
        卷
        <select v-model.number="vp.splitVolumeIdx" class="vol-input" data-testid="split-volume-select">
          <option v-for="(vol, idx) in vp.editableVolumes" :key="`split-${idx}`" :value="idx">
            {{ vol.label || `卷${idx + 1}` }} ({{ vol.start_chapter }}–{{ vol.end_chapter }})
          </option>
        </select>
      </label>
      <label>
        从章
        <input
          v-model.number="vp.splitAtChapter"
          type="number"
          min="1"
          class="vol-input vol-num"
          data-testid="split-at-chapter"
        />
      </label>
    </div>
    <button
      type="button"
      class="mini-btn pixel-border"
      data-testid="apply-split-btn"
      :disabled="vp.splitApplying"
      @click="vp.applyVolumeSplit"
    >
      {{ vp.splitApplying ? '拆分中…' : '应用拆分' }}
    </button>
  </div>
  <p
    v-if="vp.splitPreview"
    class="meta-line"
    data-testid="split-preview-line"
  >
    已拆为「{{ vp.splitPreview.first_label }}」{{ vp.splitPreview.first_range }}
    与「{{ vp.splitPreview.second_label }}」{{ vp.splitPreview.second_range }} · 请保存卷纲
  </p>
</template>

<script setup>
import { inject, ref } from 'vue';
import { CREATOR_VOLUME_PLAN_KEY } from './creatorVolumePlanKey.js';

const vp = inject(CREATOR_VOLUME_PLAN_KEY);
if (!vp) {
  throw new Error('CreatorVolumePlanMergeSplitPanel requires CREATOR_VOLUME_PLAN_KEY provide');
}

const mergeStep = ref(1);

async function applyMerge() {
  await vp.applyVolumeMerge();
  mergeStep.value = 1;
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
  font-size: 8px;
}
.merge-wizard-steps {
  display: flex;
  gap: var(--space-sm);
  list-style: none;
  margin: 0 0 var(--space-md);
  padding: 0;
  font-size: var(--text-xs);
  color: var(--color-text-dim);
}
.merge-wizard-steps__item--active {
  color: var(--color-accent);
  font-weight: 600;
}
.merge-wizard-actions {
  display: flex;
  gap: var(--space-sm);
  margin-top: var(--space-sm);
}
.merge-conflict-preview {
  margin: 0;
  padding-left: 1.2rem;
  font-size: var(--text-xs);
}
</style>

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
              data-testid="apply-merge-btn"
              :disabled="vp.mergeApplying || vp.mergeStartIdx > vp.mergeEndIdx"
              @click="vp.applyVolumeMerge"
            >
              {{ vp.mergeApplying ? '合并中…' : '应用合并' }}
            </button>
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
import { inject } from 'vue';
import { CREATOR_VOLUME_PLAN_KEY } from './creatorVolumePlanKey.js';

const vp = inject(CREATOR_VOLUME_PLAN_KEY);
if (!vp) {
  throw new Error('CreatorVolumePlanMergeSplitPanel requires CREATOR_VOLUME_PLAN_KEY provide');
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

.volume-plan-outline-lines {
  list-style: none;
  padding: 0;
  margin: var(--space-xs) 0;
  font-size: var(--text-xs);
  line-height: 1.5;
  max-height: 220px;
  overflow: auto;
}

.volume-plan-outline-line {
  padding: 2px 0;
  white-space: pre-wrap;
}

.volume-plan-outline-line--highlight {
  background: rgba(255, 220, 100, 0.35);
  box-shadow: inset 0 0 0 1px rgba(200, 180, 80, 0.65);
}

.volume-plan-diff-panel {
  margin-top: var(--space-sm);
  padding: var(--space-xs);
  background: rgba(200, 160, 80, 0.1);
}

.volume-plan-diff-side-by-side {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: var(--space-sm);
  align-items: start;
}

.volume-plan-diff-outline-col {
  padding: var(--space-xs);
  background: rgba(100, 140, 200, 0.08);
  max-height: 220px;
  overflow: auto;
}

.volume-plan-outline-excerpt {
  margin: var(--space-xs) 0;
  white-space: pre-wrap;
  font-size: var(--text-xs);
  line-height: 1.5;
}

.volume-plan-diff-list {
  list-style: none;
  padding: 0;
  margin: var(--space-xs) 0 0;
  font-size: var(--text-sm);
}

.volume-plan-diff-item .diff-type {
  font-family: 'Press Start 2P', monospace;
  font-size: var(--text-xs);
  margin-right: var(--space-xs);
  text-transform: uppercase;
}

.volume-plan-diff-details summary {
  cursor: pointer;
  list-style: none;
}

.volume-plan-diff-details summary::-webkit-details-marker {
  display: none;
}

.volume-plan-diff-detail-list {
  list-style: none;
  padding: var(--space-xs) 0 0 var(--space-sm);
  margin: 0;
  font-size: var(--text-xs);
  opacity: 0.9;
}

.volume-plan-save-confirm {
  margin-top: var(--space-xs);
  padding: var(--space-xs);
  background: rgba(200, 120, 80, 0.1);
}

.link-btn {
  background: none;
  border: none;
  padding: 0;
  color: inherit;
  text-decoration: underline;
  cursor: pointer;
  font: inherit;
}

.subsection-title {
  font-size: var(--text-sm);
  margin: var(--space-md) 0 var(--space-xs);
}

.volume-plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.volume-edit-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 6px;
  margin-bottom: 6px;
  font-size: var(--text-sm);
}

.volume-edit-row--locked {
  border-color: var(--color-accent);
  background: rgba(100, 140, 200, 0.08);
}

.volume-edit-row--dragging {
  opacity: 0.55;
}

.volume-reorder {
  display: flex;
  flex-direction: column;
  gap: 2px;
  align-items: center;
}

.drag-handle {
  cursor: grab;
  font-size: var(--text-sm);
  opacity: 0.6;
  user-select: none;
}

.vol-input {
  font-size: var(--text-sm);
  padding: 2px 4px;
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--color-text);
}

.vol-label { width: 3em; }

.vol-num { width: 3em; }

.vol-conflict { flex: 1; min-width: 80px; }

.vol-range { display: flex; align-items: center; gap: 2px; }

.mini-btn,
.save-btn {
  font-size: var(--text-xs);
  padding: 2px 6px;
  cursor: pointer;
}

.save-btn {
  margin-top: var(--space-xs);
}

.batch-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.path-line,
.cmd-block code {
  font-size: var(--text-xs);
  word-break: break-all;
  display: block;
}

.meta-line {
  font-size: var(--text-sm);
  opacity: 0.75;
}

.mini-btn--danger {
  color: #c44;
}

.template-changelog ul {
  margin: 4px 0 0;
  padding-left: 1.2em;
  font-size: var(--text-sm);
}

.changelog-row {
  margin-bottom: 2px;
}

.changelog-diff {
  color: var(--color-accent);
}

.changelog-visual-diff {
  margin-top: 4px;
  font-size: var(--text-xs);
  white-space: pre-wrap;
  max-height: 120px;
  overflow: auto;
  background: rgba(127, 127, 127, 0.08);
  padding: 4px;
}

.visual-diff-line--add {
  color: #4a4;
}

.visual-diff-line--remove {
  color: #c44;
}

.template-approvals {
  margin-top: var(--space-sm);
}

.template-approval-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  align-items: center;
  margin-bottom: var(--space-xs);
}

.version-semver-warn {
  color: var(--color-warn, #c90);
}

.import-templates-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  margin-top: var(--space-xs);
}

.import-templates-json {
  width: 100%;
  min-height: 72px;
  font-family: monospace;
}

.volume-template-panel {
  margin-bottom: var(--space-sm);
  padding: var(--space-sm);
}

.pulse-empty-guide .meta-line {
  margin: var(--space-xs) 0 var(--space-sm);
}

.companion-logic-check-write .subsection-title {
  margin-bottom: var(--space-xs);
}

.volume-merge-panel {
  margin-top: var(--space-sm);
  padding: var(--space-sm);
}

.volume-split-panel {
  margin-top: var(--space-sm);
  padding: var(--space-sm);
}

.merge-range {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: var(--text-sm);
  margin-bottom: 6px;
  align-items: center;
}
</style>

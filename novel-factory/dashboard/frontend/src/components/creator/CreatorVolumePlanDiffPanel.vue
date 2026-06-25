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
            <button
              v-if="vp.uiProfile.volume_plan_diff_jump_outline_edit"
              type="button"
              class="mini-btn pixel-border"
              data-testid="jump-global-outline-edit-btn"
              @click="vp.jumpToGlobalOutlineEdit"
            >
              编辑全局大纲
            </button>
            <button
              v-if="vp.uiProfile.volume_plan_diff_export && vp.volumePlanDiffPreview?.has_changes"
              type="button"
              class="mini-btn pixel-border"
              data-testid="export-volume-plan-diff-btn"
              @click="vp.exportVolumePlanDiff"
            >
              导出 diff JSON
            </button>
            <button
              v-if="vp.uiProfile.volume_plan_diff_export_markdown && vp.volumePlanDiffPreview?.has_changes"
              type="button"
              class="mini-btn pixel-border"
              data-testid="export-volume-plan-diff-markdown-btn"
              @click="vp.exportVolumePlanDiffMarkdown"
            >
              导出 diff Markdown
            </button>
            <button
              v-if="vp.uiProfile.volume_plan_diff_export_email_share && vp.volumePlanDiffPreview?.has_changes"
              type="button"
              class="mini-btn pixel-border"
              data-testid="share-volume-plan-diff-email-btn"
              @click="vp.shareVolumePlanDiffEmail"
            >
              邮件分享 diff
            </button>
            <button
              v-if="vp.uiProfile.volume_plan_diff_export_pdf && vp.volumePlanDiffPreview?.has_changes"
              type="button"
              class="mini-btn pixel-border"
              data-testid="export-volume-plan-diff-pdf-btn"
              @click="vp.exportVolumePlanDiffPdf"
            >
              导出 diff PDF
            </button>
            <button
              v-if="vp.uiProfile.volume_plan_diff_export_print_preview && vp.volumePlanDiffPreview?.has_changes"
              type="button"
              class="mini-btn pixel-border"
              data-testid="preview-volume-plan-diff-print-btn"
              @click="vp.openVolumePlanDiffPrintPreview"
            >
              打印预览
            </button>
            <button
              v-if="vp.uiProfile.volume_plan_diff_export_zip && vp.volumePlanDiffPreview?.has_changes"
              type="button"
              class="mini-btn pixel-border"
              data-testid="export-volume-plan-diff-zip-btn"
              @click="vp.exportVolumePlanDiffZip"
            >
              导出 ZIP
            </button>
            <button
              v-if="vp.uiProfile.volume_plan_diff_export_share_link && vp.volumePlanDiffPreview?.has_changes"
              type="button"
              class="mini-btn pixel-border"
              data-testid="share-volume-plan-diff-link-btn"
              @click="vp.shareVolumePlanDiffLink"
            >
              复制分享链接
            </button>
            <CreatorVolumePlanCollabPanel />
            <div
              class="volume-plan-diff-body"
              :class="{ 'volume-plan-diff-side-by-side': vp.uiProfile.volume_plan_diff_outline_side_by_side }"
            >
              <div class="volume-plan-diff-main">
                <ul class="volume-plan-diff-list" data-testid="volume-plan-diff-list">
                  <li
                    v-for="(row, idx) in vp.filteredVolumePlanDiffChanges"
                    :key="`vol-diff-${row.label}-${idx}`"
                    class="volume-plan-diff-item"
                    :data-testid="`volume-plan-diff-${row.type}-${row.label}`"
                  >
                    <details
                      v-if="vp.uiProfile.volume_plan_diff_expand_detail && row.details?.length"
                      class="volume-plan-diff-details"
                      :data-testid="`volume-plan-diff-details-${row.type}-${row.label}`"
                    >
                      <summary>
                        <span class="diff-type">{{ row.type }}</span> {{ row.message }}
                      </summary>
                      <ul class="volume-plan-diff-detail-list">
                        <li
                          v-for="(line, detailIdx) in row.details"
                          :key="`vol-diff-detail-${row.label}-${detailIdx}`"
                          :data-testid="`volume-plan-diff-detail-${row.label}-${detailIdx}`"
                        >
                          {{ line }}
                        </li>
                      </ul>
                    </details>
                    <template v-else>
                      <span class="diff-type">{{ row.type }}</span> {{ row.message }}
                    </template>
                  </li>
                </ul>
              </div>
              <aside
                v-if="vp.uiProfile.volume_plan_diff_outline_side_by_side && vp.volumePlanDiffPreview.global_outline_excerpt"
                class="volume-plan-diff-outline-col pixel-border"
                data-testid="volume-plan-diff-outline-side-by-side"
              >
                <p class="meta-line">全局大纲摘录</p>
                <pre
                  v-if="!vp.uiProfile.volume_plan_diff_outline_row_highlight || !vp.volumePlanDiffPreview.global_outline_lines?.length"
                  class="volume-plan-outline-excerpt"
                >{{ vp.volumePlanDiffPreview.global_outline_excerpt }}</pre>
                <ul
                  v-else
                  class="volume-plan-outline-lines"
                  data-testid="volume-plan-diff-outline-lines"
                >
                  <li
                    v-for="(line, lineIdx) in vp.volumePlanDiffPreview.global_outline_lines"
                    :key="`outline-line-${lineIdx}`"
                    class="volume-plan-outline-line"
                    :class="{ 'volume-plan-outline-line--highlight': line.highlighted }"
                    :data-testid="line.highlighted ? `volume-plan-outline-line-highlight-${lineIdx}` : `volume-plan-outline-line-${lineIdx}`"
                  >
                    {{ line.text }}
                  </li>
                </ul>
                <code class="path-line">{{ vp.volumePlanDiffPreview.global_outline_path }}</code>
              </aside>
            </div>
            <div
              v-if="vp.volumePlanSaveConfirmOpen"
              class="volume-plan-save-confirm pixel-border"
              data-testid="volume-plan-save-confirm-panel"
            >
              <p class="meta-line">确认保存以上卷纲变更？</p>
              <div class="batch-actions">
                <button
                  type="button"
                  class="save-btn pixel-border"
                  data-testid="confirm-volume-plan-save-btn"
                  :disabled="vp.saving"
                  @click="vp.confirmSaveVolumePlan"
                >
                  {{ vp.saving ? '保存中…' : '确认保存' }}
                </button>
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="cancel-volume-plan-save-btn"
                  :disabled="vp.saving"
                  @click="vp.cancelVolumePlanSave"
                >
                  取消
                </button>
              </div>
            </div>
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
              <button
                v-if="vp.uiProfile.volume_plan_diff_jump_outline_edit"
                type="button"
                class="mini-btn pixel-border"
                data-testid="jump-global-outline-edit-btn"
                @click="vp.jumpToGlobalOutlineEdit"
              >
                编辑全局大纲
              </button>
              <button
                v-if="vp.uiProfile.volume_plan_diff_export && vp.volumePlanDiffPreview?.has_changes"
                type="button"
                class="mini-btn pixel-border"
                data-testid="export-volume-plan-diff-btn"
                @click="vp.exportVolumePlanDiff"
              >
                导出 diff JSON
              </button>
              <button
                v-if="vp.uiProfile.volume_plan_diff_export_markdown && vp.volumePlanDiffPreview?.has_changes"
                type="button"
                class="mini-btn pixel-border"
                data-testid="export-volume-plan-diff-markdown-btn"
                @click="vp.exportVolumePlanDiffMarkdown"
              >
                导出 diff Markdown
              </button>
              <button
                v-if="vp.uiProfile.volume_plan_diff_export_email_share && vp.volumePlanDiffPreview?.has_changes"
                type="button"
                class="mini-btn pixel-border"
                data-testid="share-volume-plan-diff-email-btn"
                @click="vp.shareVolumePlanDiffEmail"
              >
                邮件分享 diff
              </button>
              <button
                v-if="vp.uiProfile.volume_plan_diff_export_pdf && vp.volumePlanDiffPreview?.has_changes"
                type="button"
                class="mini-btn pixel-border"
                data-testid="export-volume-plan-diff-pdf-btn"
                @click="vp.exportVolumePlanDiffPdf"
              >
                导出 diff PDF
              </button>
              <button
                v-if="vp.uiProfile.volume_plan_diff_export_print_preview && vp.volumePlanDiffPreview?.has_changes"
                type="button"
                class="mini-btn pixel-border"
                data-testid="preview-volume-plan-diff-print-btn"
                @click="vp.openVolumePlanDiffPrintPreview"
              >
                打印预览
              </button>
              <button
                v-if="vp.uiProfile.volume_plan_diff_export_zip && vp.volumePlanDiffPreview?.has_changes"
                type="button"
                class="mini-btn pixel-border"
                data-testid="export-volume-plan-diff-zip-btn"
                @click="vp.exportVolumePlanDiffZip"
              >
                导出 ZIP
              </button>
              <button
                v-if="vp.uiProfile.volume_plan_diff_export_share_link && vp.volumePlanDiffPreview?.has_changes"
                type="button"
                class="mini-btn pixel-border"
                data-testid="share-volume-plan-diff-link-btn"
                @click="vp.shareVolumePlanDiffLink"
              >
                复制分享链接
              </button>
              <div
                class="volume-plan-diff-body"
                :class="{ 'volume-plan-diff-side-by-side': vp.uiProfile.volume_plan_diff_outline_side_by_side }"
              >
                <div class="volume-plan-diff-main">
                  <ul class="volume-plan-diff-list" data-testid="volume-plan-diff-list">
                    <li
                      v-for="(row, idx) in vp.filteredVolumePlanDiffChanges"
                      :key="`vol-diff-collapse-${row.label}-${idx}`"
                      class="volume-plan-diff-item"
                      :data-testid="`volume-plan-diff-${row.type}-${row.label}`"
                    >
                      <details
                        v-if="vp.uiProfile.volume_plan_diff_expand_detail && row.details?.length"
                        class="volume-plan-diff-details"
                        :data-testid="`volume-plan-diff-details-${row.type}-${row.label}`"
                      >
                        <summary>
                          <span class="diff-type">{{ row.type }}</span> {{ row.message }}
                        </summary>
                        <ul class="volume-plan-diff-detail-list">
                          <li
                            v-for="(line, detailIdx) in row.details"
                            :key="`vol-diff-detail-collapse-${row.label}-${detailIdx}`"
                            :data-testid="`volume-plan-diff-detail-${row.label}-${detailIdx}`"
                          >
                            {{ line }}
                          </li>
                        </ul>
                      </details>
                      <template v-else>
                        <span class="diff-type">{{ row.type }}</span> {{ row.message }}
                      </template>
                    </li>
                  </ul>
                </div>
                <aside
                  v-if="vp.uiProfile.volume_plan_diff_outline_side_by_side && vp.volumePlanDiffPreview.global_outline_excerpt"
                  class="volume-plan-diff-outline-col pixel-border"
                  data-testid="volume-plan-diff-outline-side-by-side"
                >
                  <p class="meta-line">全局大纲摘录</p>
                  <pre
                    v-if="!vp.uiProfile.volume_plan_diff_outline_row_highlight || !vp.volumePlanDiffPreview.global_outline_lines?.length"
                    class="volume-plan-outline-excerpt"
                  >{{ vp.volumePlanDiffPreview.global_outline_excerpt }}</pre>
                  <ul
                    v-else
                    class="volume-plan-outline-lines"
                    data-testid="volume-plan-diff-outline-lines"
                  >
                    <li
                      v-for="(line, lineIdx) in vp.volumePlanDiffPreview.global_outline_lines"
                      :key="`outline-line-collapse-${lineIdx}`"
                      class="volume-plan-outline-line"
                      :class="{ 'volume-plan-outline-line--highlight': line.highlighted }"
                      :data-testid="line.highlighted ? `volume-plan-outline-line-highlight-${lineIdx}` : `volume-plan-outline-line-${lineIdx}`"
                    >
                      {{ line.text }}
                    </li>
                  </ul>
                  <code class="path-line">{{ vp.volumePlanDiffPreview.global_outline_path }}</code>
                </aside>
              </div>
              <div
                v-if="vp.volumePlanSaveConfirmOpen"
                class="volume-plan-save-confirm pixel-border"
                data-testid="volume-plan-save-confirm-panel"
              >
                <p class="meta-line">确认保存以上卷纲变更？</p>
                <div class="batch-actions">
                  <button
                    type="button"
                    class="save-btn pixel-border"
                    data-testid="confirm-volume-plan-save-btn"
                    :disabled="vp.saving"
                    @click="vp.confirmSaveVolumePlan"
                  >
                    {{ vp.saving ? '保存中…' : '确认保存' }}
                  </button>
                  <button
                    type="button"
                    class="mini-btn pixel-border"
                    data-testid="cancel-volume-plan-save-btn"
                    :disabled="vp.saving"
                    @click="vp.cancelVolumePlanSave"
                  >
                    取消
                  </button>
                </div>
              </div>
            </template>
            <p v-else class="meta-line" data-testid="volume-plan-diff-no-changes">
              当前编辑与已保存卷纲一致
            </p>
          </details>
</template>

<script setup>
import { inject } from 'vue';
import { CREATOR_VOLUME_PLAN_KEY } from './creatorVolumePlanKey.js';
import CreatorVolumePlanCollabPanel from './CreatorVolumePlanCollabPanel.vue';

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

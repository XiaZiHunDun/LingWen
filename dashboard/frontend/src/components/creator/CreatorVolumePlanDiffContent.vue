<!--
  CreatorVolumePlanDiffContent — diff 操作区/列表/保存确认（静态与折叠面板共用）
-->
<template>
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
          :key="`${keyPrefix}vol-diff-${row.label}-${idx}`"
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
                :key="`${keyPrefix}vol-diff-detail-${row.label}-${detailIdx}`"
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
          :key="`${keyPrefix}outline-line-${lineIdx}`"
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

<script setup>
import { inject } from 'vue';
import { CREATOR_VOLUME_PLAN_KEY } from './creatorVolumePlanKey.js';
import CreatorVolumePlanCollabPanel from './CreatorVolumePlanCollabPanel.vue';

defineProps({
  keyPrefix: { type: String, default: '' },
});

const vp = inject(CREATOR_VOLUME_PLAN_KEY);
if (!vp) {
  throw new Error('CreatorVolumePlanDiffContent requires CREATOR_VOLUME_PLAN_KEY provide');
}
</script>

<style scoped>
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
}

.volume-plan-diff-item {
  margin-bottom: var(--space-xs);
  font-size: var(--text-xs);
}

.volume-plan-diff-details summary {
  cursor: pointer;
}

.volume-plan-diff-detail-list {
  margin: var(--space-xs) 0 0 var(--space-md);
  padding: 0;
  list-style: disc;
}

.diff-type {
  font-family: 'Press Start 2P', monospace;
  font-size: 6px;
  color: #a60;
  margin-right: var(--space-xs);
}

.volume-plan-save-confirm {
  margin-top: var(--space-sm);
  padding: var(--space-xs);
  background: rgba(200, 80, 80, 0.1);
}
</style>

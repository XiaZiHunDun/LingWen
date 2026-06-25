<!--
  CreatorVolumePlanShareModals.vue — 卷纲 diff 分享链接预览 / 应用确认 / 打印预览
-->
<template>
  <div
    v-if="vp.uiProfile.volume_plan_diff_share_link_preview && vp.volumePlanDiffShareLinkPreview"
    class="volume-plan-diff-share-link-preview pixel-border"
    data-testid="volume-plan-diff-share-link-preview"
  >
    <p
      v-if="vp.volumePlanDiffShareLinkPreview.valid === false"
      class="meta-line volume-plan-diff-share-link-error"
      data-testid="volume-plan-diff-share-token-error"
    >
      {{ vp.volumePlanDiffShareLinkPreview.error_label }}
    </p>
    <template v-else>
      <p class="meta-line">
        分享链接解析：{{ vp.volumePlanDiffShareLinkPreview.change_count }} 条变更
        <span v-if="vp.volumePlanDiffShareLinkPreview.global_outline_path">
          · {{ vp.volumePlanDiffShareLinkPreview.global_outline_path }}
        </span>
      </p>
      <ul class="volume-plan-diff-share-link-preview-list">
        <li
          v-for="(row, idx) in vp.volumePlanDiffShareLinkPreview.changes"
          :key="`share-diff-${row.label}-${idx}`"
          class="meta-line"
        >
          {{ row.label }}：{{ row.message }}
          <span
            v-if="vp.uiProfile.volume_plan_diff_share_collab_v2 && vp.volumePlanDiffShareLinkPreview.collab_notes?.[row.label]"
            class="volume-plan-diff-share-collab-note"
            :data-testid="`share-collab-note-${row.label}`"
          >
            批注：{{ vp.volumePlanDiffShareLinkPreview.collab_notes[row.label] }}
          </span>
        </li>
      </ul>
      <button
        v-if="vp.uiProfile.volume_plan_diff_share_link_apply && vp.volumePlanDiffShareLinkPreview.can_apply"
        type="button"
        class="mini-btn pixel-border"
        data-testid="apply-volume-plan-diff-share-btn"
        @click="vp.requestApplyVolumePlanDiffShareLink"
      >
        一键应用卷纲
      </button>
      <ol
        v-if="vp.uiProfile.volume_plan_diff_share_link_e2e && vp.volumePlanDiffShareLinkPreview.can_apply"
        class="volume-plan-diff-share-e2e-steps"
        data-testid="volume-plan-diff-share-e2e-steps"
      >
        <li
          class="volume-plan-diff-share-e2e-step volume-plan-diff-share-e2e-step--done"
          data-testid="share-e2e-step-parse"
        >
          1. 解析分享链接
        </li>
        <li
          class="volume-plan-diff-share-e2e-step"
          :class="{ 'volume-plan-diff-share-e2e-step--done': vp.shareE2eApplyDone }"
          data-testid="share-e2e-step-apply"
        >
          2. 应用卷纲
        </li>
        <li
          class="volume-plan-diff-share-e2e-step"
          data-testid="share-e2e-step-save"
        >
          3. 保存卷纲
        </li>
      </ol>
    </template>
    <button
      type="button"
      class="mini-btn pixel-border"
      data-testid="dismiss-volume-plan-diff-share-preview-btn"
      @click="vp.dismissVolumePlanDiffShareLinkPreview"
    >
      关闭预览
    </button>
  </div>

  <div
    v-if="vp.pendingShareApply"
    class="volume-plan-diff-share-apply-confirm pixel-border"
    data-testid="volume-plan-diff-share-apply-confirm"
  >
    <p class="meta-line">
      确认应用分享卷纲（{{ vp.pendingShareApply.draft_volumes?.length || 0 }} 卷）？
    </p>
    <div class="mode-switch-confirm-actions">
      <button
        type="button"
        class="mini-btn pixel-border"
        data-testid="confirm-share-apply-btn"
        @click="vp.confirmApplyVolumePlanDiffShareLink"
      >
        确认应用
      </button>
      <button
        type="button"
        class="mini-btn pixel-border"
        data-testid="cancel-share-apply-btn"
        @click="vp.cancelApplyVolumePlanDiffShareLink"
      >
        取消
      </button>
    </div>
  </div>

  <div
    v-if="vp.pendingShareMerge"
    class="volume-plan-diff-share-merge-wizard pixel-border"
    data-testid="volume-plan-diff-share-merge-wizard"
  >
    <p class="meta-line">分享卷纲与本地存在 {{ vp.pendingShareMerge.conflicts.length }} 处冲突</p>
    <ul class="volume-plan-diff-share-merge-list">
      <li
        v-for="row in vp.pendingShareMerge.conflicts"
        :key="`share-merge-${row.label}`"
        class="meta-line"
      >
        {{ row.label }}：本地「{{ row.local.core_conflict }}」 / 分享「{{ row.share.core_conflict }}」
      </li>
    </ul>
    <div class="mode-switch-confirm-actions">
      <button
        type="button"
        class="mini-btn pixel-border"
        data-testid="share-merge-use-share-btn"
        @click="vp.confirmShareMergeUseShare"
      >
        使用分享版
      </button>
      <button
        type="button"
        class="mini-btn pixel-border"
        data-testid="share-merge-keep-local-btn"
        @click="vp.cancelShareMerge"
      >
        保留本地
      </button>
    </div>
  </div>

  <div
    v-if="vp.showVolumePlanDiffPrintPreview"
    class="volume-plan-diff-print-preview pixel-border"
    data-testid="volume-plan-diff-print-preview"
  >
    <p class="meta-line">卷纲 diff 打印预览</p>
    <pre class="volume-plan-diff-print-preview-body">{{ vp.volumePlanDiffPrintPreviewText }}</pre>
    <div class="volume-plan-diff-print-preview-actions">
      <button
        type="button"
        class="mini-btn pixel-border"
        data-testid="print-volume-plan-diff-btn"
        @click="vp.printVolumePlanDiffPrintPreview"
      >
        打印
      </button>
      <button
        type="button"
        class="mini-btn pixel-border"
        data-testid="close-volume-plan-diff-print-preview-btn"
        @click="vp.closeVolumePlanDiffPrintPreview"
      >
        关闭
      </button>
    </div>
  </div>
</template>

<script setup>
import { inject } from 'vue';
import { CREATOR_VOLUME_PLAN_KEY } from './creatorVolumePlanKey.js';

const vp = inject(CREATOR_VOLUME_PLAN_KEY);
</script>

<style scoped>
.meta-line {
  font-size: var(--text-sm);
  opacity: 0.75;
}

.mini-btn {
  font-size: var(--text-xs);
  padding: 2px 6px;
  cursor: pointer;
}

.volume-plan-diff-share-link-preview {
  margin: var(--space-sm) 0;
  padding: var(--space-sm);
}

.volume-plan-diff-share-link-preview-list {
  margin: var(--space-xs) 0;
  padding-left: 1.2rem;
}

.volume-plan-diff-share-link-error {
  color: var(--danger, #a33);
}

.volume-plan-diff-share-apply-confirm,
.volume-plan-diff-share-merge-wizard {
  margin: var(--space-sm) 0;
  padding: var(--space-sm);
}

.volume-plan-diff-share-merge-list {
  margin: var(--space-xs) 0;
  padding-left: 1.2rem;
}

.volume-plan-diff-share-e2e-steps {
  margin: var(--space-xs) 0;
  padding-left: 1.2rem;
  font-size: var(--text-md);
}

.volume-plan-diff-share-e2e-step--done {
  font-weight: bold;
}

.volume-plan-diff-share-collab-note {
  display: block;
  margin-top: 2px;
  opacity: 0.9;
  font-size: var(--text-md);
}

.volume-plan-diff-print-preview {
  margin: var(--space-xs) 0;
  padding: var(--space-sm);
}

.volume-plan-diff-print-preview-body {
  max-height: 240px;
  overflow: auto;
  font-size: var(--text-sm);
  white-space: pre-wrap;
  margin: var(--space-xs) 0;
}

.volume-plan-diff-print-preview-actions {
  display: flex;
  gap: var(--space-xs);
}

.mode-switch-confirm-actions {
  display: flex;
  gap: var(--space-xs);
  margin-top: var(--space-xs);
}
</style>

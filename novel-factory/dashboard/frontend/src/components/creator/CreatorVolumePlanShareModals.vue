<!--
  CreatorVolumePlanShareModals.vue — 卷纲 diff 分享链接预览 / 应用确认 / 打印预览（从 CreatorPage 拆出）
-->
<template>
  <div
    v-if="uiProfile.volume_plan_diff_share_link_preview && volumePlanDiffShareLinkPreview"
    class="volume-plan-diff-share-link-preview pixel-border"
    data-testid="volume-plan-diff-share-link-preview"
  >
    <p
      v-if="volumePlanDiffShareLinkPreview.valid === false"
      class="meta-line volume-plan-diff-share-link-error"
      data-testid="volume-plan-diff-share-token-error"
    >
      {{ volumePlanDiffShareLinkPreview.error_label }}
    </p>
    <template v-else>
      <p class="meta-line">
        分享链接解析：{{ volumePlanDiffShareLinkPreview.change_count }} 条变更
        <span v-if="volumePlanDiffShareLinkPreview.global_outline_path">
          · {{ volumePlanDiffShareLinkPreview.global_outline_path }}
        </span>
      </p>
      <ul class="volume-plan-diff-share-link-preview-list">
        <li
          v-for="(row, idx) in volumePlanDiffShareLinkPreview.changes"
          :key="`share-diff-${row.label}-${idx}`"
          class="meta-line"
        >
          {{ row.label }}：{{ row.message }}
          <span
            v-if="uiProfile.volume_plan_diff_share_collab_v2 && volumePlanDiffShareLinkPreview.collab_notes?.[row.label]"
            class="volume-plan-diff-share-collab-note"
            :data-testid="`share-collab-note-${row.label}`"
          >
            批注：{{ volumePlanDiffShareLinkPreview.collab_notes[row.label] }}
          </span>
        </li>
      </ul>
      <button
        v-if="uiProfile.volume_plan_diff_share_link_apply && volumePlanDiffShareLinkPreview.can_apply"
        type="button"
        class="mini-btn pixel-border"
        data-testid="apply-volume-plan-diff-share-btn"
        @click="$emit('request-apply-share')"
      >
        一键应用卷纲
      </button>
      <ol
        v-if="uiProfile.volume_plan_diff_share_link_e2e && volumePlanDiffShareLinkPreview.can_apply"
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
          :class="{ 'volume-plan-diff-share-e2e-step--done': shareE2eApplyDone }"
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
      @click="$emit('dismiss-share-preview')"
    >
      关闭预览
    </button>
  </div>

  <div
    v-if="pendingShareApply"
    class="volume-plan-diff-share-apply-confirm pixel-border"
    data-testid="volume-plan-diff-share-apply-confirm"
  >
    <p class="meta-line">
      确认应用分享卷纲（{{ pendingShareApply.draft_volumes?.length || 0 }} 卷）？
    </p>
    <div class="mode-switch-confirm-actions">
      <button
        type="button"
        class="mini-btn pixel-border"
        data-testid="confirm-share-apply-btn"
        @click="$emit('confirm-share-apply')"
      >
        确认应用
      </button>
      <button
        type="button"
        class="mini-btn pixel-border"
        data-testid="cancel-share-apply-btn"
        @click="$emit('cancel-share-apply')"
      >
        取消
      </button>
    </div>
  </div>

  <div
    v-if="pendingShareMerge"
    class="volume-plan-diff-share-merge-wizard pixel-border"
    data-testid="volume-plan-diff-share-merge-wizard"
  >
    <p class="meta-line">分享卷纲与本地存在 {{ pendingShareMerge.conflicts.length }} 处冲突</p>
    <ul class="volume-plan-diff-share-merge-list">
      <li
        v-for="row in pendingShareMerge.conflicts"
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
        @click="$emit('confirm-share-merge')"
      >
        使用分享版
      </button>
      <button
        type="button"
        class="mini-btn pixel-border"
        data-testid="share-merge-keep-local-btn"
        @click="$emit('cancel-share-merge')"
      >
        保留本地
      </button>
    </div>
  </div>

  <div
    v-if="showVolumePlanDiffPrintPreview"
    class="volume-plan-diff-print-preview pixel-border"
    data-testid="volume-plan-diff-print-preview"
  >
    <p class="meta-line">卷纲 diff 打印预览</p>
    <pre class="volume-plan-diff-print-preview-body">{{ volumePlanDiffPrintPreviewText }}</pre>
    <div class="volume-plan-diff-print-preview-actions">
      <button
        type="button"
        class="mini-btn pixel-border"
        data-testid="print-volume-plan-diff-btn"
        @click="$emit('print-preview')"
      >
        打印
      </button>
      <button
        type="button"
        class="mini-btn pixel-border"
        data-testid="close-volume-plan-diff-print-preview-btn"
        @click="$emit('close-print-preview')"
      >
        关闭
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  uiProfile: { type: Object, required: true },
  volumePlanDiffShareLinkPreview: { type: Object, default: null },
  shareE2eApplyDone: { type: Boolean, default: false },
  pendingShareApply: { type: Object, default: null },
  pendingShareMerge: { type: Object, default: null },
  showVolumePlanDiffPrintPreview: { type: Boolean, default: false },
  volumePlanDiffPrintPreviewText: { type: String, default: '' },
});

defineEmits([
  'request-apply-share',
  'dismiss-share-preview',
  'confirm-share-apply',
  'cancel-share-apply',
  'confirm-share-merge',
  'cancel-share-merge',
  'print-preview',
  'close-print-preview',
]);
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

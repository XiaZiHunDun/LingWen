<!--
  CreatorExportModal.vue — 作品导出
-->
<template>
  <div
    v-if="pt.exportModalOpen"
    class="creator-modal"
    data-testid="creator-export-modal"
    @click.self="pt.closeExportModal"
  >
    <div class="creator-modal__panel pixel-card" data-testid="creator-export-panel">
      <header class="creator-modal__header">
        <h2>导出作品</h2>
        <button type="button" class="link-btn" data-testid="export-modal-close" @click="pt.closeExportModal">
          关闭
        </button>
      </header>

      <div class="export-modes">
        <label
          v-for="mode in modes"
          :key="mode.id"
          class="export-mode"
          :data-testid="`export-mode-${mode.id}`"
        >
          <input v-model="pt.exportMode" type="radio" :value="mode.id">
          <span>
            <strong>{{ mode.label }}</strong>
            <span class="meta-line">{{ mode.hint }}</span>
          </span>
        </label>
      </div>

      <div class="export-meta pixel-border">
        <label>
          作者
          <input v-model="pt.exportAuthor" class="vol-input" data-testid="export-author">
        </label>
        <label>
          简介 / 描述（EPUB·DOCX 元数据）
          <textarea
            v-model="pt.exportDescription"
            rows="2"
            class="settings-textarea"
            data-testid="export-description"
          />
        </label>
      </div>

      <div v-if="pt.exportMode === 'range'" class="export-range">
        <label>
          起始章
          <input v-model.number="pt.exportRangeStart" type="number" min="1" class="vol-input" data-testid="export-range-start">
        </label>
        <label>
          结束章
          <input v-model.number="pt.exportRangeEnd" type="number" min="1" class="vol-input" data-testid="export-range-end">
        </label>
      </div>

      <div v-if="pt.exportMode === 'submission'" class="export-intro">
        <label>
          试读章数
          <input
            v-model.number="pt.exportSubmissionSampleCount"
            type="number"
            min="1"
            max="12"
            class="vol-input vol-input--narrow"
            data-testid="export-submission-sample-count"
          >
        </label>
        <label>
          作品简介（投稿用）
          <textarea
            v-model="pt.exportIntro"
            rows="3"
            class="settings-textarea"
            data-testid="export-submission-intro"
            placeholder="一句话卖点 + 类型标签"
          />
        </label>
      </div>

      <div class="export-actions">
        <button
          type="button"
          class="mini-btn pixel-border"
          data-testid="export-preview-btn"
          :disabled="pt.exportBusy"
          @click="pt.refreshExportPreview"
        >
          {{ pt.exportBusy ? '生成中…' : '预览' }}
        </button>
        <button
          type="button"
          class="save-btn pixel-border"
          data-testid="export-download-btn"
          :disabled="pt.exportBusy"
          @click="pt.runExportDownload"
        >
          下载 Markdown
        </button>
        <button
          type="button"
          class="mini-btn pixel-border"
          data-testid="export-epub-btn"
          :disabled="pt.exportBusy"
          @click="pt.runExportEpub"
        >
          下载 EPUB
        </button>
        <button
          type="button"
          class="mini-btn pixel-border"
          data-testid="export-docx-btn"
          :disabled="pt.exportBusy"
          @click="pt.runExportDocx"
        >
          下载 DOCX
        </button>
      </div>

      <pre
        v-if="pt.exportPreview"
        class="export-preview"
        data-testid="export-preview-text"
      >{{ pt.exportPreview.slice(0, 2000) }}{{ pt.exportPreview.length > 2000 ? '\n…' : '' }}</pre>
    </div>
  </div>
</template>

<script setup>
import { inject } from 'vue';
import { CREATOR_PRODUCT_TOOLS_KEY } from './creatorProductToolsKey.js';

const pt = inject(CREATOR_PRODUCT_TOOLS_KEY);

const modes = [
  { id: 'full', label: '全书正文', hint: '导出所有已写章节 + 设定附录' },
  { id: 'range', label: '章节范围', hint: '指定起止章' },
  { id: 'submission', label: '投稿包', hint: '简介 + 大纲节选 + 试读 3 章' },
];
</script>

<style scoped>
.export-modes {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.export-mode {
  display: flex;
  gap: var(--space-sm);
  align-items: flex-start;
  font-size: var(--text-sm);
  cursor: pointer;
}

.export-range,
.export-intro,
.export-meta {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
  font-size: var(--text-sm);
}

.export-meta {
  padding: var(--space-xs);
}

.export-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.export-preview {
  max-height: 200px;
  overflow: auto;
  font-size: var(--text-xs);
  background: #f8f8f8;
  padding: var(--space-xs);
  white-space: pre-wrap;
}
</style>

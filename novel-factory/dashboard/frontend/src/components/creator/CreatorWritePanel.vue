<!--
  CreatorWritePanel.vue — 写栏（从 CreatorPage 拆出）
-->
<template>
      <section
        v-show="w.isWorkspaceColumnVisible('write')"
        class="creator-column"
        :class="w.wb.workbenchEnabled ? 'creator-column--workbench creator-column--write-desk' : 'pixel-card'"
        data-testid="column-write"
      >
        <h2 v-if="!w.wb.workbenchEnabled" class="column-title">写</h2>
        <p v-if="!w.wb.workbenchEnabled" class="column-hint">章节状态 · 偏离章高亮</p>

        <component :is="w.wb.workbenchEnabled ? CreatorWriteWorkbench : 'div'">
        <template v-if="w.wb.workbenchEnabled" #chapters>
          <CreatorChapterList compact />
        </template>

        <CreatorChapterList v-if="!w.wb.workbenchEnabled" />
        <div
          v-if="w.showCompanionLogicCheckInWrite && !w.wb?.humanFirstDesk"
          class="companion-logic-check-write pixel-border"
          data-testid="companion-logic-check-write"
        >
          <p class="subsection-title">逻辑审查</p>
          <p class="meta-line">写完一章后，可一键检查 P0 逻辑问题。</p>
          <button
            type="button"
            class="save-btn pixel-border"
            data-testid="run-companion-logic-check-btn"
            :disabled="w.logicCheckRunning"
            @click="w.runCompanionLogicCheck"
          >
            {{ w.logicCheckRunning ? '检查中…' : '一键逻辑审查' }}
          </button>
          <p v-if="w.logicCheckResult" class="meta-line" data-testid="companion-logic-check-write-result">
            {{ w.logicCheckResult.passed ? '通过' : '未通过' }} · P0 {{ w.logicCheckResult.p0_count }}
            <span v-if="w.logicCheckResult.total_issues != null"> · 共 {{ w.logicCheckResult.total_issues }} 条</span>
            <span v-if="w.logicCheckResult.p0_only">（仅展示 P0）</span>
          </p>
          <ul
            v-if="w.uiProfile.logic_check_inline_issues && w.logicCheckResult?.issues?.length"
            class="logic-check-issues"
            data-testid="logic-check-issues"
          >
            <li
              v-for="(issue, idx) in w.logicCheckResult.issues"
              :key="`write-${issue.chapter}-${idx}`"
              class="logic-check-issue"
              :class="{
                'logic-check-issue--clickable': Boolean(issue.chapter),
                'logic-check-issue--active': !w.uiProfile.issue_paragraph_highlight_unified
                  && w.uiProfile.logic_check_issue_highlight
                  && w.activeLogicCheckIssueIdx === idx,
                'issue-line--active': w.uiProfile.issue_paragraph_highlight_unified
                  && w.activeLogicCheckIssueIdx === idx,
              }"
              role="button"
              tabindex="0"
              :data-testid="`logic-check-issue-${idx}`"
              @click="w.handleLogicCheckIssueClick(issue, idx)"
              @keydown.enter="w.handleLogicCheckIssueClick(issue, idx)"
              @keydown="w.onLogicCheckIssueKeydown($event, issue, idx)"
            >
              <span class="issue-severity">{{ issue.severity }}</span>
              <span v-if="issue.chapter">ch{{ String(issue.chapter).padStart(3, '0') }}</span>
              {{ issue.title || issue.message }}
            </li>
          </ul>
        </div>
        <div
          v-if="w.uiProfile.batch_deviation_inline_summary && w.batchDeviationInlineSummary?.items?.length"
          class="batch-deviation-inline-summary pixel-border"
          data-testid="batch-deviation-inline-summary"
        >
          <p class="meta-line" data-testid="batch-deviation-inline-summary-title">
            Batch ch{{ String(w.batchDeviationInlineSummary.start).padStart(3, '0') }}–ch{{
              String(w.batchDeviationInlineSummary.end).padStart(3, '0')
            }} · {{ w.batchDeviationInlineSummary.items.length }} 条偏离
          </p>
          <ul class="batch-deviation-inline-list" data-testid="batch-deviation-inline-list">
            <li
              v-for="(d, i) in w.batchDeviationInlineSummary.items"
              :key="`batch-dev-${d.chapter}-${i}`"
              class="batch-deviation-inline-item"
              :class="[
                `deviation-${d.severity}`,
                {
                  'deviation-item--clickable': w.uiProfile.deviation_chapter_jump && d.chapter,
                  'deviation-item--active': w.deviationHighlightEnabled && w.highlightedDeviationChapter === d.chapter,
                },
              ]"
              role="button"
              tabindex="0"
              :data-testid="`batch-deviation-inline-ch${d.chapter}`"
              @click="w.handleDeviationClick(d)"
              @keydown.enter="w.handleDeviationClick(d)"
            >
              <span v-if="d.chapter" class="deviation-chapter">ch{{ String(d.chapter).padStart(3, '0') }}</span>
              {{ d.message }}
            </li>
          </ul>
          <div v-if="w.uiProfile.batch_deviation_summary_link || w.uiProfile.batch_deviation_inline_dismiss" class="batch-deviation-inline-actions">
            <button
              v-if="w.uiProfile.batch_deviation_summary_link"
              type="button"
              class="save-btn pixel-border"
              data-testid="batch-deviation-open-summary-btn"
              @click="w.openVolumeSummaryForRange(w.batchDeviationInlineSummary.start, w.batchDeviationInlineSummary.end)"
            >
              查看卷摘要
            </button>
            <button
              v-if="w.uiProfile.batch_deviation_inline_dismiss"
              type="button"
              class="mini-btn pixel-border"
              data-testid="dismiss-batch-deviation-inline-btn"
              @click="w.dismissBatchDeviationInlineSummary"
            >
              知道了
            </button>
          </div>
        </div>
        <div
          v-if="w.chapterPreview"
          class="chapter-preview"
          :class="{
            'chapter-preview--workbench': w.wb.workbenchEnabled,
            'pixel-border': !w.wb.workbenchEnabled,
          }"
          data-testid="chapter-preview-panel"
        >
          <h3 v-if="!w.wb?.humanFirstDesk" class="subsection-title">
            ch{{ String(w.chapterPreview.chapter).padStart(3, '0') }} 预览
            <span v-if="w.chapterPreview.word_count">（{{ w.chapterPreview.word_count }} 字）</span>
          </h3>
          <p v-if="w.previewLoading" class="meta-line">加载中…</p>
          <template v-else>
            <div
              v-if="w.uiProfile.chapter_outline_inline_edit"
              class="chapter-dual-edit"
              :class="{ 'chapter-dual-edit--human': w.wb?.humanFirstDesk }"
              data-testid="chapter-dual-edit"
            >
              <details
                v-if="w.wb?.humanFirstDesk"
                class="chapter-outline-edit chapter-outline-edit--collapsible"
                data-testid="chapter-outline-details"
              >
                <summary class="meta-line chapter-outline-edit__summary">分章大纲</summary>
                <textarea
                  v-model="w.chapterOutlineDraft"
                  class="settings-textarea chapter-outline-textarea"
                  :rows="w.wb?.humanFirstDesk ? 4 : 8"
                  data-testid="chapter-outline-textarea"
                />
                <button
                  type="button"
                  class="mini-btn"
                  data-testid="save-chapter-outline-btn"
                  :disabled="w.chapterOutlineSaving"
                  @click="w.saveChapterOutline"
                >
                  {{ w.chapterOutlineSaving ? '保存中…' : '保存大纲' }}
                </button>
              </details>
              <div v-else class="chapter-outline-edit">
                <label class="meta-line">分章大纲</label>
                <textarea
                  v-model="w.chapterOutlineDraft"
                  class="settings-textarea chapter-outline-textarea"
                  rows="10"
                  data-testid="chapter-outline-textarea"
                />
                <button
                  type="button"
                  class="save-btn pixel-border"
                  data-testid="save-chapter-outline-btn"
                  :disabled="w.chapterOutlineSaving"
                  @click="w.saveChapterOutline"
                >
                  {{ w.chapterOutlineSaving ? '保存中…' : '保存大纲' }}
                </button>
              </div>
              <div
                v-if="w.uiProfile.chapter_inline_edit"
                class="chapter-inline-edit"
                data-testid="chapter-inline-edit"
              >
                <label class="meta-line" for="chapter-body-textarea">正文（内嵌编辑）</label>
                <CreatorChapterBodyEditor
                  :show-gutter="Boolean(w.wb?.showInlineConflictGutter)"
                  :markers="w.wb?.inlineConflictMarkers || []"
                  :active-marker-id="w.wb?.activeInlineConflictId"
                  @focus-marker="w.wb?.focusInlineConflict"
                >
                  <textarea
                    :ref="w.bindChapterBodyTextareaRef"
                    v-model="w.chapterBodyDraft"
                    class="settings-textarea chapter-body-textarea"
                    :class="bodyTextareaClass"
                    :rows="w.wb?.humanFirstDesk ? 4 : 12"
                    id="chapter-body-textarea"
                    data-testid="chapter-body-textarea"
                    @mouseup="onBodyTextareaInteraction"
                    @keyup="onBodyTextareaInteraction"
                    @select="onBodyTextareaInteraction"
                  />
                </CreatorChapterBodyEditor>
                <CreatorChapterBodySaveFooter
                  :status-label="w.bodySaveStatusLabel"
                  :auto-save-status="w.bodyAutoSaveStatus"
                  :saving="w.chapterBodySaving"
                  :human-first="Boolean(w.wb?.humanFirstDesk)"
                  @save="w.saveChapterBody"
                />
              </div>
            </div>
            <div
              v-if="w.uiProfile.chapter_outline_read_preview && w.chapterPreview.has_outline && !w.uiProfile.chapter_outline_inline_edit"
              class="chapter-outline-read-preview"
              data-testid="chapter-outline-read-preview"
            >
              <label class="meta-line">分章大纲（只读）</label>
              <pre class="preview-text chapter-outline-full-text">{{
                w.chapterPreview.outline_text || w.chapterPreview.outline_preview || '（空）'
              }}</pre>
            </div>
            <details
              v-else-if="w.chapterPreview.has_outline && !w.uiProfile.chapter_outline_read_preview && !w.uiProfile.chapter_outline_inline_edit"
              open
            >
              <summary>分章大纲</summary>
              <pre class="preview-text">{{ w.chapterPreview.outline_preview || '（空）' }}</pre>
            </details>
            <div
              v-if="!w.uiProfile.chapter_outline_inline_edit && w.uiProfile.chapter_inline_edit"
              class="chapter-inline-edit"
              data-testid="chapter-inline-edit"
            >
              <label class="meta-line" for="chapter-body-textarea">正文（内嵌编辑）</label>
              <CreatorChapterBodyEditor
                :show-gutter="Boolean(w.wb?.showInlineConflictGutter)"
                :markers="w.wb?.inlineConflictMarkers || []"
                :active-marker-id="w.wb?.activeInlineConflictId"
                @focus-marker="w.wb?.focusInlineConflict"
              >
                <textarea
                  :ref="w.bindChapterBodyTextareaRef"
                  v-model="w.chapterBodyDraft"
                  class="settings-textarea chapter-body-textarea"
                  :class="bodyTextareaClass"
                  rows="12"
                  data-testid="chapter-body-textarea"
                  @mouseup="onBodyTextareaInteraction"
                  @keyup="onBodyTextareaInteraction"
                  @select="onBodyTextareaInteraction"
                />
              </CreatorChapterBodyEditor>
              <CreatorChapterBodySaveFooter
                :status-label="w.bodySaveStatusLabel"
                :auto-save-status="w.bodyAutoSaveStatus"
                :saving="w.chapterBodySaving"
                :human-first="Boolean(w.wb?.humanFirstDesk)"
                @save="w.saveChapterBody"
              />
            </div>
            <div
              v-if="
                w.uiProfile.chapter_recheck_inline
                  && w.chapterRecheckResult
                  && w.chapterRecheckResult.chapter === w.selectedChapter
              "
              class="chapter-recheck-panel pixel-border"
              data-testid="chapter-recheck-inline-panel"
            >
              <p class="meta-line" data-testid="chapter-recheck-inline-summary">
                保存后复查 · {{ w.chapterRecheckResult.passed ? '通过' : '未通过' }}
                · P0 {{ w.chapterRecheckResult.p0_count }}
              </p>
              <ul
                v-if="w.chapterRecheckResult.issues?.length"
                class="logic-check-issues"
                data-testid="chapter-recheck-inline-issues"
              >
                <li
                  v-for="(issue, idx) in w.chapterRecheckResult.issues"
                  :key="`recheck-${issue.chapter}-${idx}`"
                  class="logic-check-issue"
                  :class="{
                    'logic-check-issue--clickable': w.uiProfile.recheck_issue_paragraph_jump && issue.paragraph,
                    'logic-check-issue--active': !w.uiProfile.issue_paragraph_highlight_unified
                      && w.uiProfile.recheck_issue_highlight
                      && w.activeRecheckIssueIdx === idx,
                    'issue-line--active': w.uiProfile.issue_paragraph_highlight_unified
                      && w.activeRecheckIssueIdx === idx,
                  }"
                  role="button"
                  tabindex="0"
                  :data-testid="`chapter-recheck-issue-${idx}`"
                  @click="w.focusIssueParagraph(issue, idx)"
                  @keydown.enter="w.focusIssueParagraph(issue, idx)"
                  @keydown="w.onRecheckIssueKeydown($event, issue, idx)"
                >
                  <span class="issue-severity">{{ issue.severity }}</span>
                  {{ issue.title || issue.message }}
                </li>
              </ul>
            </div>
            <div
              v-else-if="w.uiProfile.chapter_full_preview && w.chapterPreview.has_body"
              class="chapter-read-preview"
              data-testid="chapter-read-preview"
            >
              <label class="meta-line">正文（只读全文）</label>
              <pre class="preview-text chapter-full-text">{{ w.chapterPreview.body_text || w.chapterPreview.body_preview }}</pre>
            </div>
            <details v-else-if="w.chapterPreview.has_body" :open="!w.chapterPreview.has_outline">
              <summary>正文</summary>
              <pre class="preview-text">{{ w.chapterPreview.body_preview || '（空）' }}</pre>
              <p v-if="w.chapterPreview.body_truncated" class="meta-line">正文已截断 · 完整内容请在编辑器查看</p>
            </details>
            <p
              v-if="!w.uiProfile.chapter_inline_edit && !w.chapterPreview.has_body && !w.chapterPreview.has_outline"
              class="meta-line"
            >
              本章尚无大纲与正文
            </p>
            <p
              v-if="w.uiProfile.chapter_inline_edit && !w.chapterPreview.has_body && !w.chapterPreview.has_outline"
              class="meta-line"
            >
              本章尚无大纲，可直接在上方编写正文
            </p>
          </template>
        </div>
        </component>
      </section>

</template>

<script setup>
import { computed, inject } from 'vue';
import CreatorWriteWorkbench from './CreatorWriteWorkbench.vue';
import CreatorChapterList from './CreatorChapterList.vue';
import CreatorChapterBodyEditor from './CreatorChapterBodyEditor.vue';
import CreatorChapterBodySaveFooter from './CreatorChapterBodySaveFooter.vue';
import { CREATOR_WRITE_KEY } from './creatorWriteKey.js';

const w = inject(CREATOR_WRITE_KEY);

const bodyTextareaClass = computed(() => ({
  'chapter-body-textarea--highlight': w.chapterBodyHighlightActive,
  'chapter-body-textarea--conflict': w.wb?.chapterBodyConflictHighlightActive,
}));

function onBodyTextareaInteraction(event) {
  w.wb?.captureBodySelection?.(event.target);
}
</script>

<style scoped>
.chapter-preview {
  margin-top: var(--space-md);
  padding: var(--space-sm);
  max-height: 320px;
  overflow: auto;
}

.chapter-preview--workbench {
  margin-top: 0;
  max-height: none;
  flex: 1;
  min-height: 240px;
}

.chapter-dual-edit {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-sm);
  margin-top: var(--space-sm);
}

@media (max-width: 960px) {
  .chapter-dual-edit {
    grid-template-columns: 1fr;
  }
}
.chapter-outline-textarea {
  width: 100%;
  min-height: 160px;
}
.logic-check-issue--clickable {
  cursor: pointer;
  text-decoration: underline;
}
.logic-check-issue--active {
  animation: recheck-issue-flash 1.2s ease-out;
  background: var(--color-highlight-soft);
}
.batch-deviation-inline-summary {
  margin: var(--space-sm) 0;
  padding: var(--space-xs);
  background: rgba(200, 80, 80, 0.08);
}
.batch-deviation-inline-list {
  list-style: none;
  padding: 0;
  margin: var(--space-xs) 0 0;
  font-size: var(--text-sm);
}
.batch-deviation-inline-item {
  padding: 4px 0;
}
.batch-deviation-inline-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  margin-top: var(--space-xs);
}
.logic-check-issue:focus-visible {
  outline: 2px solid rgba(200, 180, 80, 0.85);
  outline-offset: 1px;
}
.chapter-body-textarea--highlight {
  animation: chapter-body-highlight-pulse 1.2s ease-out;
  box-shadow: 0 0 0 2px var(--color-highlight-soft);
}
.chapter-body-textarea--conflict {
  animation: chapter-body-conflict-pulse 1.4s ease-out;
  box-shadow: 0 0 0 2px var(--color-conflict-outline);
  background-image: linear-gradient(
    transparent 90%,
    var(--color-conflict-bg-stripe) 90%,
    var(--color-conflict-bg-stripe) 95%,
    transparent 95%
  );
  background-size: 100% 1.4em;
}
.chapter-outline-read-preview {
  margin-bottom: var(--space-sm);
}
@keyframes recheck-issue-flash {
  0% { background: rgba(255, 220, 100, 0.55); }
  100% { background: rgba(255, 220, 100, 0.35); }
}
@keyframes chapter-body-highlight-pulse {
  0% { background: rgba(255, 220, 100, 0.4); }
  100% { background: transparent; }
}
@keyframes chapter-body-conflict-pulse {
  0% { background-color: var(--color-danger-soft); }
  100% { background-color: transparent; }
}

@media (prefers-reduced-motion: reduce) {
  .logic-check-issue--active,
  .chapter-body-textarea--highlight,
  .chapter-body-textarea--conflict {
    animation: none;
  }
}
.chapter-inline-edit {
  margin-top: var(--space-sm);
}
.chapter-dual-edit--human {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}
.chapter-outline-edit--collapsible {
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-md);
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
}
.chapter-outline-edit__summary {
  cursor: pointer;
  font-weight: 600;
  list-style: none;
  user-select: none;
}
.chapter-outline-edit__summary::-webkit-details-marker {
  display: none;
}
.chapter-body-textarea {
  width: 100%;
  min-height: 180px;
}
.chapter-read-preview {
  margin-top: var(--space-sm);
}
.chapter-full-text {
  max-height: 280px;
  overflow: auto;
}
.logic-check-issues {
  margin: var(--space-sm) 0 0;
  padding: 0;
  list-style: none;
}
.logic-check-issue {
  cursor: pointer;
  margin-bottom: var(--space-xs);
  font-size: var(--text-sm);
}
.chapter-recheck-panel {
  margin-top: var(--space-sm);
  padding: var(--space-xs);
  background: rgba(200, 180, 80, 0.1);
}
.chapter-row--warn {
  background: rgba(200, 180, 80, 0.15);
  border-color: var(--color-warning);
}
.chapter-row--alert {
  background: rgba(200, 80, 80, 0.15);
  border-color: #c66;
}
.companion-logic-check-write {
  margin-top: var(--space-md);
  padding: var(--space-md);
}

.companion-logic-check-write--compact {
  margin-top: 0;
  padding: 0;
  border: none;
  background: transparent;
}

.companion-logic-check-write--compact details {
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-muted);
  border-radius: var(--radius-sm);
}

.companion-logic-check-write__summary {
  cursor: pointer;
  font-weight: 600;
  list-style: none;
}

.companion-logic-check-write__summary::-webkit-details-marker {
  display: none;
}

.creator-column--write-desk {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.companion-logic-check-write .subsection-title {
  margin-bottom: var(--space-xs);
}

</style>

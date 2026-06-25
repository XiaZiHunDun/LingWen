<!--
  CreatorPage.vue — 创作者三栏：写 / 脉络 / 设定 + 卷纲锁定与偏离 diff
-->
<template>
  <div class="creator-page">
    <header class="page-header">
      <h1 class="page-title" data-testid="page-title">创作伴侣</h1>
      <div class="header-actions">
        <span
          v-if="overview"
          class="mode-badge pixel-border"
          :class="{
            'mode-badge--hintable': modeBadgeHintEnabled && creationModeBadgeHintText,
            'mode-badge--companion-tint': uiProfile.companion_creation_mode_badge_tint && overview.creation_mode === 'companion',
            'mode-badge--advance-tint': uiProfile.advance_creation_mode_badge_tint && overview.creation_mode === 'advance',
            'mode-badge--studio-tint': uiProfile.studio_creation_mode_badge_tint && overview.creation_mode === 'studio',
          }"
          data-testid="creation-mode-badge"
          :title="modeBadgeHintEnabled ? creationModeBadgeHintText : undefined"
          @click="showCreationModeBadgeHint"
        >
          {{ modeLabel }}
        </span>
        <span
          v-if="overview && displayDeviationBadge"
          class="deviation-badge pixel-border deviation-badge--clickable"
          data-testid="deviation-badge"
          role="button"
          tabindex="0"
          :title="workspaceTabsEnabled ? '查看脉络与偏离' : undefined"
          @click="onDeviationBadgeClick"
          @keydown.enter="onDeviationBadgeClick"
        >
          偏离 {{ displayDeviationCount }}
        </span>
        <button
          class="refresh-btn pixel-border"
          data-testid="refresh-btn"
          :disabled="loading"
          @click="refresh"
        >
          {{ loading ? '加载中…' : '刷新' }}
        </button>
      </div>
    </header>

    <div v-if="error" class="error-banner pixel-border" data-testid="error-banner">
      {{ error }}
    </div>
    <div v-if="conflictMessage" class="conflict-banner pixel-border" data-testid="conflict-banner">
      {{ conflictMessage }}
      <button type="button" class="mini-btn pixel-border" data-testid="conflict-reload-btn" @click="refresh">
        重新加载
      </button>
    </div>
    <div v-if="saveMessage" class="save-banner pixel-border" data-testid="save-banner">
      {{ saveMessage }}
    </div>

    <HubTabBar
      v-if="overview && workspaceTabsEnabled"
      v-model="workspaceActiveTab"
      :tabs="workspaceTabs"
      :badges="workspaceTabBadges"
      test-id="creator-workspace-tab"
      class="creator-workspace-tabs"
      data-testid="creator-workspace-tabs"
    />

    <div
      v-if="overview"
      class="creator-grid"
      :class="{ 'creator-grid--tabbed': workspaceTabsEnabled }"
      data-testid="creator-grid"
    >
      <!-- 写 -->
      <section
        v-show="isWorkspaceColumnVisible('write')"
        class="creator-column pixel-card"
        data-testid="column-write"
      >
        <h2 class="column-title">写</h2>
        <p class="column-hint">章节状态 · 偏离章高亮</p>
        <ul class="chapter-list">
          <li
            v-for="ch in visibleChapters"
            :key="ch.chapter"
            class="chapter-row"
            :class="[chapterRowClass(ch.chapter), { 'chapter-row--selected': selectedChapter === ch.chapter }]"
            role="button"
            tabindex="0"
            :data-testid="`chapter-row-${ch.chapter}`"
            @click="selectChapter(ch.chapter)"
            @keydown.enter="selectChapter(ch.chapter)"
          >
            <span class="ch-label">ch{{ String(ch.chapter).padStart(3, '0') }}</span>
            <span class="ch-status">
              {{ ch.has_body ? `${ch.word_count} 字` : (ch.has_outline ? '仅大纲' : '空') }}
            </span>
          </li>
        </ul>
        <div
          v-if="showCompanionLogicCheckInWrite"
          class="companion-logic-check-write pixel-border"
          data-testid="companion-logic-check-write"
        >
          <p class="subsection-title">逻辑审查</p>
          <p class="meta-line">写完一章后，可一键检查 P0 逻辑问题。</p>
          <button
            type="button"
            class="save-btn pixel-border"
            data-testid="run-companion-logic-check-btn"
            :disabled="logicCheckRunning"
            @click="runCompanionLogicCheck"
          >
            {{ logicCheckRunning ? '检查中…' : '一键逻辑审查' }}
          </button>
          <p v-if="logicCheckResult" class="meta-line" data-testid="companion-logic-check-write-result">
            {{ logicCheckResult.passed ? '通过' : '未通过' }} · P0 {{ logicCheckResult.p0_count }}
            <span v-if="logicCheckResult.total_issues != null"> · 共 {{ logicCheckResult.total_issues }} 条</span>
            <span v-if="logicCheckResult.p0_only">（仅展示 P0）</span>
          </p>
          <ul
            v-if="uiProfile.logic_check_inline_issues && logicCheckResult?.issues?.length"
            class="logic-check-issues"
            data-testid="logic-check-issues"
          >
            <li
              v-for="(issue, idx) in logicCheckResult.issues"
              :key="`write-${issue.chapter}-${idx}`"
              class="logic-check-issue"
              :class="{
                'logic-check-issue--clickable': Boolean(issue.chapter),
                'logic-check-issue--active': !uiProfile.issue_paragraph_highlight_unified
                  && uiProfile.logic_check_issue_highlight
                  && activeLogicCheckIssueIdx === idx,
                'issue-line--active': uiProfile.issue_paragraph_highlight_unified
                  && activeLogicCheckIssueIdx === idx,
              }"
              role="button"
              tabindex="0"
              :data-testid="`logic-check-issue-${idx}`"
              @click="handleLogicCheckIssueClick(issue, idx)"
              @keydown.enter="handleLogicCheckIssueClick(issue, idx)"
              @keydown="onLogicCheckIssueKeydown($event, issue, idx)"
            >
              <span class="issue-severity">{{ issue.severity }}</span>
              <span v-if="issue.chapter">ch{{ String(issue.chapter).padStart(3, '0') }}</span>
              {{ issue.title || issue.message }}
            </li>
          </ul>
        </div>
        <div
          v-if="uiProfile.batch_deviation_inline_summary && batchDeviationInlineSummary?.items?.length"
          class="batch-deviation-inline-summary pixel-border"
          data-testid="batch-deviation-inline-summary"
        >
          <p class="meta-line" data-testid="batch-deviation-inline-summary-title">
            Batch ch{{ String(batchDeviationInlineSummary.start).padStart(3, '0') }}–ch{{
              String(batchDeviationInlineSummary.end).padStart(3, '0')
            }} · {{ batchDeviationInlineSummary.items.length }} 条偏离
          </p>
          <ul class="batch-deviation-inline-list" data-testid="batch-deviation-inline-list">
            <li
              v-for="(d, i) in batchDeviationInlineSummary.items"
              :key="`batch-dev-${d.chapter}-${i}`"
              class="batch-deviation-inline-item"
              :class="[
                `deviation-${d.severity}`,
                {
                  'deviation-item--clickable': uiProfile.deviation_chapter_jump && d.chapter,
                  'deviation-item--active': deviationHighlightEnabled && highlightedDeviationChapter === d.chapter,
                },
              ]"
              role="button"
              tabindex="0"
              :data-testid="`batch-deviation-inline-ch${d.chapter}`"
              @click="handleDeviationClick(d)"
              @keydown.enter="handleDeviationClick(d)"
            >
              <span v-if="d.chapter" class="deviation-chapter">ch{{ String(d.chapter).padStart(3, '0') }}</span>
              {{ d.message }}
            </li>
          </ul>
          <div v-if="uiProfile.batch_deviation_summary_link || uiProfile.batch_deviation_inline_dismiss" class="batch-deviation-inline-actions">
            <button
              v-if="uiProfile.batch_deviation_summary_link"
              type="button"
              class="save-btn pixel-border"
              data-testid="batch-deviation-open-summary-btn"
              @click="openVolumeSummaryForRange(batchDeviationInlineSummary.start, batchDeviationInlineSummary.end)"
            >
              查看卷摘要
            </button>
            <button
              v-if="uiProfile.batch_deviation_inline_dismiss"
              type="button"
              class="mini-btn pixel-border"
              data-testid="dismiss-batch-deviation-inline-btn"
              @click="dismissBatchDeviationInlineSummary"
            >
              知道了
            </button>
          </div>
        </div>
        <div
          v-if="chapterPreview"
          class="chapter-preview pixel-border"
          data-testid="chapter-preview-panel"
        >
          <h3 class="subsection-title">
            ch{{ String(chapterPreview.chapter).padStart(3, '0') }} 预览
            <span v-if="chapterPreview.word_count">（{{ chapterPreview.word_count }} 字）</span>
          </h3>
          <p v-if="previewLoading" class="meta-line">加载中…</p>
          <template v-else>
            <div
              v-if="uiProfile.chapter_outline_inline_edit"
              class="chapter-dual-edit"
              data-testid="chapter-dual-edit"
            >
              <div class="chapter-outline-edit">
                <label class="meta-line">分章大纲</label>
                <textarea
                  v-model="chapterOutlineDraft"
                  class="settings-textarea chapter-outline-textarea"
                  rows="10"
                  data-testid="chapter-outline-textarea"
                />
                <button
                  type="button"
                  class="save-btn pixel-border"
                  data-testid="save-chapter-outline-btn"
                  :disabled="chapterOutlineSaving"
                  @click="saveChapterOutline"
                >
                  {{ chapterOutlineSaving ? '保存中…' : '保存大纲' }}
                </button>
              </div>
              <div
                v-if="uiProfile.chapter_inline_edit"
                class="chapter-inline-edit"
                data-testid="chapter-inline-edit"
              >
                <label class="meta-line">正文（内嵌编辑）</label>
                <textarea
                  ref="chapterBodyTextareaRef"
                  v-model="chapterBodyDraft"
                  class="settings-textarea chapter-body-textarea"
                  :class="{ 'chapter-body-textarea--highlight': chapterBodyHighlightActive }"
                  rows="12"
                  data-testid="chapter-body-textarea"
                />
                <button
                  type="button"
                  class="save-btn pixel-border"
                  data-testid="save-chapter-body-btn"
                  :disabled="chapterBodySaving"
                  @click="saveChapterBody"
                >
                  {{ chapterBodySaving ? '保存中…' : '保存正文' }}
                </button>
              </div>
            </div>
            <div
              v-if="uiProfile.chapter_outline_read_preview && chapterPreview.has_outline"
              class="chapter-outline-read-preview"
              data-testid="chapter-outline-read-preview"
            >
              <label class="meta-line">分章大纲（只读）</label>
              <pre class="preview-text chapter-outline-full-text">{{
                chapterPreview.outline_text || chapterPreview.outline_preview || '（空）'
              }}</pre>
            </div>
            <details v-else-if="chapterPreview.has_outline && !uiProfile.chapter_outline_read_preview" open>
              <summary>分章大纲</summary>
              <pre class="preview-text">{{ chapterPreview.outline_preview || '（空）' }}</pre>
            </details>
            <div
              v-if="!uiProfile.chapter_outline_inline_edit && uiProfile.chapter_inline_edit"
              class="chapter-inline-edit"
              data-testid="chapter-inline-edit"
            >
              <label class="meta-line">正文（内嵌编辑）</label>
              <textarea
                ref="chapterBodyTextareaRef"
                v-model="chapterBodyDraft"
                class="settings-textarea chapter-body-textarea"
                :class="{ 'chapter-body-textarea--highlight': chapterBodyHighlightActive }"
                rows="12"
                data-testid="chapter-body-textarea"
              />
              <button
                type="button"
                class="save-btn pixel-border"
                data-testid="save-chapter-body-btn"
                :disabled="chapterBodySaving"
                @click="saveChapterBody"
              >
                {{ chapterBodySaving ? '保存中…' : '保存正文' }}
              </button>
            </div>
            <div
              v-if="
                uiProfile.chapter_recheck_inline
                  && chapterRecheckResult
                  && chapterRecheckResult.chapter === selectedChapter
              "
              class="chapter-recheck-panel pixel-border"
              data-testid="chapter-recheck-inline-panel"
            >
              <p class="meta-line" data-testid="chapter-recheck-inline-summary">
                保存后复查 · {{ chapterRecheckResult.passed ? '通过' : '未通过' }}
                · P0 {{ chapterRecheckResult.p0_count }}
              </p>
              <ul
                v-if="chapterRecheckResult.issues?.length"
                class="logic-check-issues"
                data-testid="chapter-recheck-inline-issues"
              >
                <li
                  v-for="(issue, idx) in chapterRecheckResult.issues"
                  :key="`recheck-${issue.chapter}-${idx}`"
                  class="logic-check-issue"
                  :class="{
                    'logic-check-issue--clickable': uiProfile.recheck_issue_paragraph_jump && issue.paragraph,
                    'logic-check-issue--active': !uiProfile.issue_paragraph_highlight_unified
                      && uiProfile.recheck_issue_highlight
                      && activeRecheckIssueIdx === idx,
                    'issue-line--active': uiProfile.issue_paragraph_highlight_unified
                      && activeRecheckIssueIdx === idx,
                  }"
                  role="button"
                  tabindex="0"
                  :data-testid="`chapter-recheck-issue-${idx}`"
                  @click="focusIssueParagraph(issue, idx)"
                  @keydown.enter="focusIssueParagraph(issue, idx)"
                  @keydown="onRecheckIssueKeydown($event, issue, idx)"
                >
                  <span class="issue-severity">{{ issue.severity }}</span>
                  {{ issue.title || issue.message }}
                </li>
              </ul>
            </div>
            <div
              v-else-if="uiProfile.chapter_full_preview && chapterPreview.has_body"
              class="chapter-read-preview"
              data-testid="chapter-read-preview"
            >
              <label class="meta-line">正文（只读全文）</label>
              <pre class="preview-text chapter-full-text">{{ chapterPreview.body_text || chapterPreview.body_preview }}</pre>
            </div>
            <details v-else-if="chapterPreview.has_body" :open="!chapterPreview.has_outline">
              <summary>正文</summary>
              <pre class="preview-text">{{ chapterPreview.body_preview || '（空）' }}</pre>
              <p v-if="chapterPreview.body_truncated" class="meta-line">正文已截断 · 完整内容请在编辑器查看</p>
            </details>
            <p
              v-if="!uiProfile.chapter_inline_edit && !chapterPreview.has_body && !chapterPreview.has_outline"
              class="meta-line"
            >
              本章尚无大纲与正文
            </p>
            <p
              v-if="uiProfile.chapter_inline_edit && !chapterPreview.has_body && !chapterPreview.has_outline"
              class="meta-line"
            >
              本章尚无大纲，可直接在上方编写正文
            </p>
          </template>
        </div>
        <p v-if="overview.chapters.length > 15" class="meta-line">
          显示前 15 章 · 共 {{ overview.max_chapter }} 章上限
        </p>
      </section>

      <!-- 脉络 -->
      <section
        v-show="isWorkspaceColumnVisible('pulse')"
        class="creator-column pixel-card"
        data-testid="column-pulse"
      >
        <CreatorPulseIntro
          :overview="overview"
          :show-empty-guide="showPulseCompanionEmpty"
          @go-write="setWorkspaceTab('write')"
        />

        <div
          v-if="overview.volume_pulse?.volume_count"
          class="volume-pulse-panel pixel-border"
          :class="`volume-pulse-panel--${overview.volume_pulse.overall_status}`"
          data-testid="volume-pulse-panel"
        >
          <h3 class="subsection-title">卷级脉络</h3>
          <p class="meta-line" data-testid="volume-pulse-overall">
            <template v-if="overview.volume_pulse.alerts_only">
              {{ overview.volume_pulse.alert_count ? `${overview.volume_pulse.alert_count} 卷需关注` : '暂无 alert 级偏离' }}
            </template>
            <template v-else>
              {{ overview.volume_pulse.alert_count ? `${overview.volume_pulse.alert_count} 卷需关注` : '各卷按计划推进' }}
            </template>
          </p>
          <ul>
            <li
              v-for="row in overview.volume_pulse.volumes"
              :key="row.label"
              class="volume-pulse-row"
              :class="[
                `volume-pulse-row--${row.status}`,
                { 'volume-pulse-row--active': highlightedVolumeLabel === row.label },
              ]"
              role="button"
              tabindex="0"
              :data-testid="`volume-pulse-row-${row.label}`"
              @click="jumpToVolume(row)"
              @keydown.enter="jumpToVolume(row)"
            >
              <strong>{{ row.label }}</strong>
              <span class="meta-line">{{ row.headline }}</span>
              <button
                v-if="uiProfile.volume_pulse_summary_generate"
                type="button"
                class="mini-btn pixel-border volume-pulse-generate-btn"
                :data-testid="`volume-pulse-generate-${row.label}`"
                @click.stop="generateVolumeSummaryForRow(row)"
              >
                生成摘要
              </button>
            </li>
          </ul>
          <button
            v-if="overview.volume_pulse.latest_summary"
            type="button"
            class="link-btn meta-line"
            data-testid="volume-pulse-jump-summary-btn"
            @click="openVolumeSummaryByName(overview.volume_pulse.latest_summary.name)"
          >
            最新摘要：{{ overview.volume_pulse.latest_summary.name }}
          </button>
        </div>

        <CreatorVolumePlanPanel />

        <CreatorDeviationList
          :deviations="visibleDeviations"
          :ui-profile="uiProfile"
          :highlight-enabled="deviationHighlightEnabled"
          :highlighted-chapter="highlightedDeviationChapter"
          @deviation-click="handleDeviationClick"
        />

        <CreatorAdvanceBatchPanel
          :show-advance-batch="showAdvanceBatch"
          :show-advance-batch-on-creator="showAdvanceBatchOnCreator"
          v-model:batch-start="batchStart"
          v-model:batch-end="batchEnd"
          v-model:batch-budget="batchBudget"
          :ui-profile="uiProfile"
          :batch-history-budget-hint="batchHistoryBudgetHint"
          :batch-running="batchRunning"
          :preflight-ok="preflightOk"
          :batch-command="batchCommand"
          :batch-error="batchError"
          :batch-job="batchJob"
          @preflight="runAdvancePreflight"
          @run-batch="runAdvanceBatch"
          @go-produce="goProduceConsole"
        />

        <CreatorBatchHistoryPanel />

        <CreatorBatchSummaryPrompt
          :prompt="batchSummaryPrompt"
          :ui-profile="uiProfile"
          @open-summary="openVolumeSummaryForRange"
          @dismiss="batchSummaryPrompt = null"
        />

        <template v-if="overview.volume_summaries.length">
          <h3 class="subsection-title">卷摘要</h3>
          <details
            v-for="vol in overview.volume_summaries"
            :key="vol.path"
            class="volume-block"
            :class="vol.pulse_status ? `volume-block--${vol.pulse_status}` : ''"
            :open="openVolumeSummaryName === vol.name"
            :data-testid="`volume-summary-block-${vol.name}`"
          >
            <summary>
              <span v-if="vol.volume_label" class="volume-summary-label">{{ vol.volume_label }} · </span>
              {{ vol.name }}
              <span v-if="vol.pulse_status" class="volume-summary-status">（{{ vol.pulse_status }}）</span>
            </summary>
            <pre class="volume-excerpt">{{ vol.excerpt }}</pre>
          </details>
        </template>
      </section>

      <!-- 设定 -->
      <CreatorSettingsPanel />
    </div>

    <CreatorModeGuidePanel :mode-label="modeLabel" />

    <CreatorVolumePlanShareModals
      :ui-profile="uiProfile"
      :volume-plan-diff-share-link-preview="volumePlanDiffShareLinkPreview"
      :share-e2e-apply-done="shareE2eApplyDone"
      :pending-share-apply="pendingShareApply"
      :pending-share-merge="pendingShareMerge"
      :show-volume-plan-diff-print-preview="showVolumePlanDiffPrintPreview"
      :volume-plan-diff-print-preview-text="volumePlanDiffPrintPreviewText"
      @request-apply-share="requestApplyVolumePlanDiffShareLink"
      @dismiss-share-preview="dismissVolumePlanDiffShareLinkPreview"
      @confirm-share-apply="confirmApplyVolumePlanDiffShareLink"
      @cancel-share-apply="cancelApplyVolumePlanDiffShareLink"
      @confirm-share-merge="confirmShareMergeUseShare"
      @cancel-share-merge="cancelShareMerge"
      @print-preview="printVolumePlanDiffPrintPreview"
      @close-print-preview="closeVolumePlanDiffPrintPreview"
    />

    <CreatorOnboardingWizardPanel />
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, provide, ref, watch } from 'vue';
import {
  fetchCreatorOverview,
  runCreatorLogicCheck,
  fetchCreatorVolumePlan,
  previewCreatorVolumePlanDiff,
  fetchCreatorBatchHistory,
  exportCreatorBatchHistory,
  fetchCreatorChapterPreview,
  saveCreatorChapterBody,
  saveCreatorChapterOutline,
  generateCreatorVolumeSummary,
  dismissCreatorWizardPanel,
  saveCreatorWizardPanelCollapsed,
  fetchCreatorSettingsDocs,
  saveCreatorVolumePlan,
  mergeCreatorVolumePlan,
  splitCreatorVolumePlan,
  fetchCreatorVolumeTemplates,
  applyCreatorVolumeTemplate,
  saveCreatorVolumeTemplate,
  deleteCreatorVolumeTemplate,
  renameCreatorVolumeTemplate,
  exportCreatorVolumeTemplates,
  importCreatorVolumeTemplates,
  fetchCreatorVolumeTemplateSyncSources,
  syncCreatorVolumeTemplates,
  publishCreatorVolumeTemplateToFactory,
  pullCreatorFactoryVolumeTemplates,
  deleteCreatorFactoryVolumeTemplate,
  fetchCreatorOnboarding,
  saveCreatorOnboardingProgress,
  applyCreatorOnboardingShare,
  saveCreatorOnboardingNotes,
  fetchCreatorDiffCollabNotes,
  saveCreatorDiffCollabNotes,
  setCreatorVolumeTemplateVersion,
  fetchCreatorVolumeTemplateChangelog,
  rollbackCreatorVolumeTemplate,
  fetchCreatorTemplateApprovals,
  submitCreatorTemplateVersionApproval,
  approveCreatorTemplateApproval,
  rejectCreatorTemplateApproval,
  fetchCreatorTemplateApprovalChainConfig,
  saveCreatorTemplateApprovalChainConfig,
  fetchCreatorTemplateApprovalHistory,
  exportCreatorTemplateApprovalAudit,
  fetchCreatorTemplateApprovalSlaConfig,
  saveCreatorTemplateApprovalSlaConfig,
  fetchCreatorTemplateApprovalOverdue,
  transferCreatorTemplateApproval,
  fetchCreatorTemplateApprovalSnapshotDiff,
  fetchCreatorTemplateApprovalSnapshotDrift,
  batchApproveCreatorTemplateApprovals,
  batchRejectCreatorTemplateApprovals,
  fetchCreatorOnboardingDigestDeadLetter,
  replayCreatorOnboardingDigestDeadLetter,
  preflightCreatorFactoryMergePresetPull,
  fetchCreatorMergePresetChangelog,
  fetchCreatorMergePresetChangelogDiff,
  fetchCreatorMergePresetToposort,
  fetchCreatorOnboardingNotifications,
  fetchCreatorOnboardingNotificationDigest,
  fetchCreatorOnboardingDigestSchedule,
  saveCreatorOnboardingDigestSchedule,
  dispatchCreatorOnboardingDigest,
  fetchCreatorOnboardingDigestRetryQueue,
  fetchCreatorOnboardingDigestStats,
  processCreatorOnboardingDigestRetries,
  ackCreatorOnboardingNotifications,
  fetchCreatorOnboardingWebhook,
  saveCreatorOnboardingWebhook,
  fetchCreatorOnboardingEmail,
  saveCreatorOnboardingEmail,
  fetchCreatorMergePresetPackages,
  fetchCreatorFactoryMergePresetPackages,
  fetchCreatorMergePresetGraph,
  fetchCreatorMergePresetConflicts,
  fetchCreatorMergePresetConflictFixes,
  applyCreatorMergePresetConflictFix,
  applyAllCreatorMergePresetConflictFixes,
  preflightCreatorMergePresetImport,
  previewCreatorMergePresetImportDiff,
  applyCreatorMergePresetToposort,
  exportCreatorMergePresetPackages,
  importCreatorMergePresetPackages,
  publishCreatorMergePresetToFactory,
  pullCreatorFactoryMergePresetPackages,
  saveCreatorSettingsDocs,
  previewCreatorSettingsDocs,
  previewCreatorSettingsThreeWay,
  previewCreatorSettingsMerge,
  fetchCreatorMergePreferences,
  exportCreatorMergePreferences,
  importCreatorMergePreferences,
  fetchCreatorSettingsHistory,
  restoreCreatorSettingsSnapshot,
  studioProductionPreflight,
  studioProductionRun,
  fetchStudioActiveBatchJob,
} from '../api/index.js';
import { useStudioProject } from '../composables/useStudioProject.js';
import { useDashboardNav } from '../composables/useDashboardNav.js';
import { useCreatorWorkspace } from '../composables/useCreatorWorkspace.js';
import { useCreatorVolumePlan } from '../composables/useCreatorVolumePlan.js';
import { useCreatorBatchHistory } from '../composables/useCreatorBatchHistory.js';
import HubTabBar from '../components/HubTabBar.vue';
import CreatorPulseIntro from '../components/creator/CreatorPulseIntro.vue';
import CreatorDeviationList from '../components/creator/CreatorDeviationList.vue';
import CreatorVolumePlanPanel from '../components/creator/CreatorVolumePlanPanel.vue';
import CreatorAdvanceBatchPanel from '../components/creator/CreatorAdvanceBatchPanel.vue';
import CreatorBatchHistoryPanel from '../components/creator/CreatorBatchHistoryPanel.vue';
import CreatorBatchSummaryPrompt from '../components/creator/CreatorBatchSummaryPrompt.vue';
import CreatorVolumePlanShareModals from '../components/creator/CreatorVolumePlanShareModals.vue';
import CreatorModeGuidePanel from '../components/creator/CreatorModeGuidePanel.vue';
import CreatorOnboardingWizardPanel from '../components/creator/CreatorOnboardingWizardPanel.vue';
import CreatorSettingsPanel from '../components/creator/CreatorSettingsPanel.vue';
import { useCreatorModeGuide } from '../composables/useCreatorModeGuide.js';
import { useCreatorOnboarding } from '../composables/useCreatorOnboarding.js';
import { useCreatorSettings } from '../composables/useCreatorSettings.js';
import { CREATOR_MODE_GUIDE_KEY, createCreatorModeGuideContext } from '../components/creator/creatorModeGuideKey.js';
import { CREATOR_ONBOARDING_KEY, createCreatorOnboardingContext } from '../components/creator/creatorOnboardingKey.js';
import { CREATOR_SETTINGS_KEY, createCreatorSettingsContext } from '../components/creator/creatorSettingsKey.js';
import { CREATOR_BATCH_HISTORY_KEY, createCreatorBatchHistoryContext } from '../components/creator/creatorBatchHistoryKey.js';
import { CREATOR_VOLUME_PLAN_KEY, createCreatorVolumePlanContext } from '../components/creator/creatorVolumePlanKey.js';

const { projectRevision } = useStudioProject();
const { focusWizard, focusWizardStep, focusWizardDone, focusWizardNotes, setWizardDeepLink, buildWizardShareUrl, navigateTo, focusCreatorWorkspace, setCreatorWorkspace } = useDashboardNav();
const overview = ref(null);
const selectedChapter = ref(null);
const chapterPreview = ref(null);
const chapterBodyDraft = ref('');
const chapterOutlineDraft = ref('');
const chapterBodySaving = ref(false);
const chapterOutlineSaving = ref(false);
const chapterBodyTextareaRef = ref(null);
const chapterBodyHighlightActive = ref(false);
const activeRecheckIssueIdx = ref(null);
const activeLogicCheckIssueIdx = ref(null);
const highlightedDeviationChapter = ref(null);
let chapterBodyHighlightTimer = null;
let logicCheckIssueHighlightTimer = null;
let deviationHighlightTimer = null;
const batchSummaryPrompt = ref(null);
const batchDeviationInlineSummary = ref(null);
const chapterRecheckResult = ref(null);
const openVolumeSummaryName = ref(null);
const highlightedVolumeLabel = ref(null);
const previewLoading = ref(false);
const loading = ref(false);
const saving = ref(false);
const globalOutlineText = ref('');
const globalOutlineEditorRef = ref(null);
const conflictMessage = ref('');
const batchStart = ref(1);
const batchEnd = ref(10);
const batchBudget = ref(0.3);
const batchCommand = ref('');
const preflightOk = ref(false);
const batchRunning = ref(false);
const batchError = ref(null);
const batchJob = ref(null);

const error = ref(null);
const saveMessage = ref('');
const logicCheckRunning = ref(false);
const logicCheckResult = ref(null);

const defaultUiProfile = {
  show_studio_workflow: true,
  show_digest_ops: true,
  show_factory_presets: true,
  show_template_version_ops: true,
  show_merge_preset_advanced: true,
  simplified_notifications: false,
  volume_pulse_enabled: false,
  wizard_default_collapsed: false,
  wizard_expand_if_incomplete: false,
  chapter_inline_edit: false,
  chapter_full_preview: false,
  logic_check_inline_issues: false,
  logic_check_p0_only: false,
  deviation_chapter_jump: false,
  chapter_save_p0_recheck: false,
  batch_highlight_alert_volumes: false,
  volume_pulse_summary_generate: false,
  batch_auto_open_summary: false,
  batch_deviation_prompt: false,
  chapter_recheck_inline: false,
  chapter_outline_inline_edit: false,
  recheck_issue_paragraph_jump: false,
  batch_clear_pulse_no_alert: false,
  recheck_issue_highlight: false,
  batch_scroll_deviation_list: false,
  chapter_outline_read_preview: false,
  logic_check_issue_highlight: false,
  deviation_list_highlight: false,
  batch_open_first_deviation: false,
  deviation_click_highlight: false,
  batch_deviation_inline_summary: false,
  batch_deviation_inline_dismiss: false,
  batch_deviation_summary_link: false,
  issue_keyboard_navigation: false,
  issue_paragraph_highlight_unified: false,
  volume_plan_diff_preview: false,
  volume_plan_diff_save_confirm: false,
  volume_plan_diff_expand_detail: false,
  batch_history_panel: false,
  batch_history_replay_range: false,
  batch_history_status_filter: false,
  volume_plan_diff_outline_side_by_side: false,
  batch_history_export: false,
  volume_plan_diff_outline_row_highlight: false,
  batch_history_date_group: false,
  volume_plan_diff_jump_outline_edit: false,
  batch_history_status_color: false,
  volume_plan_diff_refresh_on_save: false,
  batch_history_running_pulse: false,
  volume_plan_diff_auto_collapse: false,
  batch_history_failed_retry: false,
  volume_plan_diff_change_count: false,
  batch_history_budget_hint: false,
  volume_plan_diff_type_filter: false,
  batch_history_duration: false,
  volume_plan_diff_export: false,
  batch_history_success_rate: false,
  volume_plan_diff_volume_filter: false,
  batch_history_avg_duration: false,
  volume_plan_diff_export_outline: false,
  volume_plan_diff_export_highlight: false,
  batch_history_failure_trend: false,
  batch_history_weekly_summary: false,
  batch_history_monthly_summary: false,
  volume_plan_diff_export_markdown: false,
  volume_plan_diff_export_email_share: false,
  volume_plan_diff_export_pdf: false,
  batch_history_success_rate_chart: false,
  batch_history_failure_reason_label: false,
  volume_plan_diff_export_print_preview: false,
  batch_history_status_stack_chart: false,
  volume_plan_diff_export_zip: false,
  batch_history_duration_distribution: false,
  volume_plan_diff_export_share_link: false,
  batch_history_concurrency_chart: false,
  volume_plan_diff_share_link_preview: false,
  batch_history_queue_depth_chart: false,
  volume_plan_diff_share_link_apply: false,
  batch_history_throughput_chart: false,
  volume_plan_diff_share_link_apply_confirm: false,
  batch_history_cost_efficiency_chart: false,
  creation_mode_switch_reduced_motion: false,
  volume_plan_diff_share_token_validation: false,
  batch_history_retry_rate_stack: false,
  creation_mode_switch_aria_live: false,
  volume_plan_diff_share_link_merge: false,
  batch_history_chapter_failure_heatmap: false,
  creation_mode_preview_pinned_sidebar: false,
  volume_plan_diff_share_link_e2e: false,
  batch_history_ops_summary: false,
  volume_plan_diff_share_collab_v2: false,
  creation_mode_accessibility_checklist: false,
  creation_mode_switch_confirm_dialog: false,
  creation_mode_switch_history: false,
  creation_mode_switch_undo_hint: false,
  creation_mode_switch_hotkey: false,
  creation_mode_switch_speech: false,
  creation_mode_switch_haptic: false,
  creation_mode_badge_hint: false,
  creation_mode_capability_matrix: false,
  creation_mode_switch_guide_animation: false,
  creation_mode_onboarding_step_link: false,
  studio_creation_mode_badge_hint: false,
  studio_creation_mode_badge_tint: false,
  companion_creation_mode_badge_tint: false,
  advance_creation_mode_badge_tint: false,
  creation_mode_badge_legend: false,
  creation_mode_switch_preview: false,
  creation_mode_yaml_snippet: false,
  creation_mode_switch_doc_open: false,
  creation_mode_switch_hint: false,
  creation_mode_switch_doc_link: false,
  studio_creation_entry_hint: false,
  studio_wizard_collapse_memory: false,
  deviation_min_severity: null,
  primary_action: 'studio_quality',
  creator_workspace_tabs: false,
  creator_mode_guide_default_collapsed: false,
  creator_simplified_mode_ops: false,
};

const uiProfile = computed(() => overview.value?.ui_profile || defaultUiProfile);

const {
  activeTab: workspaceActiveTab,
  tabsEnabled: workspaceTabsEnabled,
  workspaceTabs,
  isColumnVisible: isWorkspaceColumnVisible,
  setWorkspaceTab,
} = useCreatorWorkspace(uiProfile, overview);


function onDeviationBadgeClick() {
  if (workspaceTabsEnabled.value) {
    setWorkspaceTab('pulse');
    setCreatorWorkspace('pulse');
  }
}

watch(workspaceActiveTab, (tab) => {
  if (workspaceTabsEnabled.value) {
    setCreatorWorkspace(tab);
  }
});

watch(
  () => [focusCreatorWorkspace.value, workspaceTabsEnabled.value, overview.value],
  () => {
    if (!workspaceTabsEnabled.value || !focusCreatorWorkspace.value) return;
    setWorkspaceTab(focusCreatorWorkspace.value);
  },
  { immediate: true },
);

function maybeAutoSelectWritingChapter() {
  if (!workspaceTabsEnabled.value || selectedChapter.value) return;
  const ov = overview.value;
  if (!ov || ov.creation_mode !== 'companion') return;
  const chapters = ov.chapters || [];
  const target = chapters.find((ch) => !ch.has_body) || chapters[0];
  if (target?.chapter) {
    selectChapter(target.chapter);
  }
}


const deviationHighlightEnabled = computed(
  () => Boolean(
    uiProfile.value.deviation_list_highlight || uiProfile.value.deviation_click_highlight,
  ),
);

const visibleDeviations = computed(() => overview.value?.deviations || []);

const displayDeviationCount = computed(() => {
  const ov = overview.value;
  if (!ov) return 0;
  if (uiProfile.value.deviation_min_severity === 'alert') {
    return ov.alert_count || 0;
  }
  return ov.deviation_count || 0;
});

const displayDeviationBadge = computed(() => displayDeviationCount.value > 0);

const workspaceTabBadges = computed(() => {
  if (!displayDeviationCount.value) return null;
  return { pulse: displayDeviationCount.value };
});

const showCompanionLogicCheckInWrite = computed(
  () => uiProfile.value.primary_action === 'logic_check' && workspaceTabsEnabled.value,
);

const showPulseCompanionEmpty = computed(() => {
  if (overview.value?.creation_mode !== 'companion') return false;
  if (!workspaceTabsEnabled.value) return false;
  if (editableVolumes.value.length > 0) return false;
  if (visibleDeviations.value.length > 0) return false;
  if (overview.value.volume_pulse?.volume_count) return false;
  return true;
});


let batchPollTimer = null;
const lastBatchStatus = ref(null);

const modeLabel = computed(() => {
  if (!overview.value) return '';
  const map = { companion: '陪伴', advance: '推进', studio: '工作室' };
  return map[overview.value.creation_mode] || overview.value.creation_mode;
});

const creationModeBadgeHintText = computed(() => {
  if (!overview.value) return '';
  const mode = overview.value.creation_mode;
  if (uiProfile.value.creation_mode_badge_hint) {
    if (mode === 'companion') return '陪伴：人主笔 + P0 守门';
    if (mode === 'advance') return '推进：人定卷纲 + batch 产章';
  }
  if (uiProfile.value.studio_creation_mode_badge_hint && mode === 'studio') {
    return '工作室：工厂流水线与批量产章';
  }
  return '';
});

const modeBadgeHintEnabled = computed(
  () => Boolean(
    (uiProfile.value.creation_mode_badge_hint || uiProfile.value.studio_creation_mode_badge_hint)
    && creationModeBadgeHintText.value,
  ),
);















const deviationChapters = computed(() => {
  const set = new Set();
  for (const d of overview.value?.deviations || []) {
    if (d.chapter) set.add(d.chapter);
  }
  return set;
});

const alertChapters = computed(() => {
  const set = new Set();
  for (const d of overview.value?.deviations || []) {
    if (d.severity === 'alert' && d.chapter) set.add(d.chapter);
  }
  return set;
});

const visibleChapters = computed(() =>
  (overview.value?.chapters || []).filter((ch) => ch.chapter <= 15),
);

const showAdvanceBatch = computed(
  () => overview.value?.creation_mode === 'advance' || overview.value?.advance_volume_summary,
);

const showAdvanceBatchOnCreator = computed(
  () => uiProfile.value.advance_batch_panel_on_creator === true,
);

function goProduceConsole() {
  navigateTo('produce', { tab: 'studio', clearFocus: true });
}









function chapterRowClass(chapter) {
  if (alertChapters.value.has(chapter)) return 'chapter-row--alert';
  if (deviationChapters.value.has(chapter)) return 'chapter-row--warn';
  const ch = overview.value?.chapters?.find((c) => c.chapter === chapter);
  if (ch?.has_body) return 'chapter-row--done';
  return '';
}

async function selectChapter(chapter) {
  selectedChapter.value = chapter;
  previewLoading.value = true;
  chapterPreview.value = null;
  chapterBodyDraft.value = '';
  chapterOutlineDraft.value = '';
  if (chapterRecheckResult.value?.chapter !== chapter) {
    chapterRecheckResult.value = null;
  }
  try {
    const full = Boolean(
      uiProfile.value.chapter_inline_edit
        || uiProfile.value.chapter_full_preview
        || uiProfile.value.chapter_outline_inline_edit
        || uiProfile.value.chapter_outline_read_preview,
    );
    chapterPreview.value = await fetchCreatorChapterPreview(chapter, { full });
    chapterBodyDraft.value = chapterPreview.value.body_text ?? chapterPreview.value.body_preview ?? '';
    chapterOutlineDraft.value = chapterPreview.value.outline_text ?? chapterPreview.value.outline_preview ?? '';
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    previewLoading.value = false;
  }
}

async function jumpToChapter(chapter) {
  if (!chapter) return;
  await selectChapter(chapter);
  await nextTick();
  try {
    document.querySelector('[data-testid="chapter-preview-panel"]')?.scrollIntoView?.({
      behavior: 'smooth',
      block: 'start',
    });
  } catch {
    /* jsdom */
  }
}

async function jumpToVolume(row) {
  if (!row) return;
  highlightedVolumeLabel.value = row.label;
  await jumpToChapter(row.start_chapter);
}

function openVolumeSummaryByName(name) {
  if (!name) return;
  openVolumeSummaryName.value = name;
  nextTick(() => {
    try {
      document.querySelector(`[data-testid="volume-summary-block-${name}"]`)?.scrollIntoView?.({
        behavior: 'smooth',
        block: 'start',
      });
    } catch {
      /* jsdom */
    }
  });
}

function openVolumeSummaryForRange(start, end) {
  const pad = (n) => String(n).padStart(3, '0');
  const target = `volume-summary-ch${pad(start)}-${pad(end)}.md`;
  const match = overview.value?.volume_summaries?.find((vol) => vol.name === target);
  if (match) {
    openVolumeSummaryByName(match.name);
  }
}

function volumeOverlapsRange(row, start, end) {
  return row.start_chapter <= end && row.end_chapter >= start;
}

function collectBatchAlertVolumeLabels(start, end) {
  const rows = overview.value?.volume_pulse?.volumes || [];
  return rows
    .filter((row) => row.status === 'alert' && volumeOverlapsRange(row, start, end))
    .map((row) => row.label);
}

async function highlightBatchAlertVolumes(start, end) {
  if (!uiProfile.value.batch_highlight_alert_volumes && !uiProfile.value.batch_clear_pulse_no_alert) {
    return;
  }
  await nextTick();
  const rows = overview.value?.volume_pulse?.volumes || [];
  const alertRow = rows.find(
    (row) => row.status === 'alert' && volumeOverlapsRange(row, start, end),
  );
  if (alertRow) {
    highlightedVolumeLabel.value = alertRow.label;
    try {
      document.querySelector('[data-testid="volume-pulse-panel"]')?.scrollIntoView?.({
        behavior: 'smooth',
        block: 'start',
      });
    } catch {
      /* jsdom */
    }
    return;
  }
  if (uiProfile.value.batch_clear_pulse_no_alert) {
    highlightedVolumeLabel.value = null;
  }
}

async function generateVolumeSummaryForRow(row) {
  if (!row) return;
  try {
    await generateCreatorVolumeSummary({
      startChapter: row.start_chapter,
      endChapter: row.end_chapter,
    });
    saveMessage.value = `已生成「${row.label}」卷摘要`;
    await refresh();
    openVolumeSummaryForRange(row.start_chapter, row.end_chapter);
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
}

async function recheckChapterP0(chapter) {
  logicCheckRunning.value = true;
  try {
    const result = await runCreatorLogicCheck({ chapter });
    if (uiProfile.value.chapter_recheck_inline) {
      chapterRecheckResult.value = { ...result, chapter };
    } else {
      logicCheckResult.value = result;
    }
    if (result.p0_count > 0) {
      saveMessage.value = `ch${String(chapter).padStart(3, '0')} 保存后复查：发现 ${result.p0_count} 条 P0`;
    }
  } catch (e) {
    handleSaveError(e);
  } finally {
    logicCheckRunning.value = false;
  }
}

async function saveChapterBody() {
  if (!selectedChapter.value) return;
  chapterBodySaving.value = true;
  saveMessage.value = '';
  try {
    chapterPreview.value = await saveCreatorChapterBody(selectedChapter.value, chapterBodyDraft.value);
    chapterBodyDraft.value = chapterPreview.value.body_text ?? chapterBodyDraft.value;
    chapterOutlineDraft.value = chapterPreview.value.outline_text ?? chapterOutlineDraft.value;
    saveMessage.value = `ch${String(selectedChapter.value).padStart(3, '0')} 正文已保存`;
    await refresh();
    if (uiProfile.value.chapter_save_p0_recheck) {
      await recheckChapterP0(selectedChapter.value);
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    chapterBodySaving.value = false;
  }
}

async function saveChapterOutline() {
  if (!selectedChapter.value) return;
  chapterOutlineSaving.value = true;
  saveMessage.value = '';
  try {
    chapterPreview.value = await saveCreatorChapterOutline(selectedChapter.value, chapterOutlineDraft.value);
    chapterOutlineDraft.value = chapterPreview.value.outline_text ?? chapterOutlineDraft.value;
    chapterBodyDraft.value = chapterPreview.value.body_text ?? chapterBodyDraft.value;
    saveMessage.value = `ch${String(selectedChapter.value).padStart(3, '0')} 大纲已保存`;
    await refresh();
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    chapterOutlineSaving.value = false;
  }
}

function pulseChapterBodyHighlight(issueIdx, source = 'recheck') {
  const bodyHighlight = uiProfile.value.recheck_issue_highlight
    || (uiProfile.value.issue_paragraph_highlight_unified && source === 'logic');
  if (bodyHighlight) {
    if (source === 'recheck') {
      activeRecheckIssueIdx.value = issueIdx ?? null;
    }
    chapterBodyHighlightActive.value = true;
    if (chapterBodyHighlightTimer) {
      clearTimeout(chapterBodyHighlightTimer);
    }
    chapterBodyHighlightTimer = setTimeout(() => {
      chapterBodyHighlightActive.value = false;
      if (source === 'recheck') {
        activeRecheckIssueIdx.value = null;
      }
      chapterBodyHighlightTimer = null;
    }, 1200);
  } else if (source === 'recheck') {
    activeRecheckIssueIdx.value = issueIdx ?? null;
    if (chapterBodyHighlightTimer) {
      clearTimeout(chapterBodyHighlightTimer);
    }
    chapterBodyHighlightTimer = setTimeout(() => {
      activeRecheckIssueIdx.value = null;
      chapterBodyHighlightTimer = null;
    }, 1200);
  }
}

function focusIssueParagraph(issue, issueIdx, source = 'recheck') {
  if (!uiProfile.value.recheck_issue_paragraph_jump || !issue?.paragraph) return;
  const textarea = chapterBodyTextareaRef.value;
  if (!textarea) return;
  const paragraphs = chapterBodyDraft.value.split(/\n\s*\n/);
  const idx = Math.max(0, Number(issue.paragraph) - 1);
  const target = paragraphs[idx] ?? '';
  if (!target) return;
  const offset = chapterBodyDraft.value.indexOf(target);
  if (offset < 0) return;
  textarea.focus();
  textarea.setSelectionRange(offset, offset + target.length);
  try {
    const lineHeight = 16;
    textarea.scrollTop = Math.max(0, (offset / Math.max(chapterBodyDraft.value.length, 1)) * textarea.scrollHeight - lineHeight * 2);
  } catch {
    /* jsdom */
  }
  pulseChapterBodyHighlight(issueIdx, source);
}

function pulseLogicCheckIssueHighlight(issueIdx) {
  if (!uiProfile.value.logic_check_issue_highlight && !uiProfile.value.issue_paragraph_highlight_unified) {
    return;
  }
  activeLogicCheckIssueIdx.value = issueIdx ?? null;
  if (logicCheckIssueHighlightTimer) {
    clearTimeout(logicCheckIssueHighlightTimer);
  }
  logicCheckIssueHighlightTimer = setTimeout(() => {
    activeLogicCheckIssueIdx.value = null;
    logicCheckIssueHighlightTimer = null;
  }, 1200);
}

function pulseDeviationHighlight(chapter) {
  if (!deviationHighlightEnabled.value || !chapter) return;
  highlightedDeviationChapter.value = chapter;
  if (deviationHighlightTimer) {
    clearTimeout(deviationHighlightTimer);
  }
  deviationHighlightTimer = setTimeout(() => {
    highlightedDeviationChapter.value = null;
    deviationHighlightTimer = null;
  }, 1200);
}

function batchDeviationsInRange(start, end) {
  return visibleDeviations.value
    .filter((row) => row.chapter && row.chapter >= start && row.chapter <= end)
    .sort((a, b) => a.chapter - b.chapter);
}

async function handleLogicCheckIssueClick(issue, issueIdx) {
  if (!issue?.chapter) return;
  pulseLogicCheckIssueHighlight(issueIdx);
  await jumpToChapter(issue.chapter);
  if (uiProfile.value.recheck_issue_paragraph_jump && issue.paragraph) {
    await nextTick();
    focusIssueParagraph(issue, issueIdx, 'logic');
  }
}

async function handleDeviationClick(deviation) {
  if (!deviation?.chapter || !uiProfile.value.deviation_chapter_jump) return;
  pulseDeviationHighlight(deviation.chapter);
  await jumpToChapter(deviation.chapter);
}

function updateBatchDeviationInlineSummary(start, end) {
  if (!uiProfile.value.batch_deviation_inline_summary) {
    batchDeviationInlineSummary.value = null;
    return;
  }
  const items = batchDeviationsInRange(start, end);
  batchDeviationInlineSummary.value = items.length
    ? { start, end, items }
    : null;
}

async function linkBatchDeviationInlineSummary(start, end) {
  if (
    !batchDeviationInlineSummary.value
    || !uiProfile.value.batch_deviation_summary_link
    || !overview.value?.volume_summaries?.length
  ) {
    return;
  }
  await nextTick();
  openVolumeSummaryForRange(start, end);
}

function dismissBatchDeviationInlineSummary() {
  batchDeviationInlineSummary.value = null;
}

function navigateIssueList(event, issues, currentIdx, onSelect, testIdPrefix) {
  if (!uiProfile.value.issue_keyboard_navigation || !issues?.length) return;
  if (event.key !== 'ArrowDown' && event.key !== 'ArrowUp') return;
  event.preventDefault();
  const delta = event.key === 'ArrowDown' ? 1 : -1;
  const nextIdx = Math.max(0, Math.min(issues.length - 1, currentIdx + delta));
  if (nextIdx === currentIdx) return;
  onSelect(issues[nextIdx], nextIdx);
  nextTick(() => {
    try {
      document.querySelector(`[data-testid="${testIdPrefix}-${nextIdx}"]`)?.focus?.();
    } catch {
      /* jsdom */
    }
  });
}

function onRecheckIssueKeydown(event, issue, idx) {
  navigateIssueList(
    event,
    chapterRecheckResult.value?.issues,
    idx,
    (item, newIdx) => focusIssueParagraph(item, newIdx),
    'chapter-recheck-issue',
  );
}

function onLogicCheckIssueKeydown(event, issue, idx) {
  navigateIssueList(
    event,
    logicCheckResult.value?.issues,
    idx,
    (item, newIdx) => handleLogicCheckIssueClick(item, newIdx),
    'logic-check-issue',
  );
}

async function scrollToBatchDeviationList(start, end) {
  if (!uiProfile.value.batch_scroll_deviation_list) return;
  const rows = batchDeviationsInRange(start, end);
  if (!rows.length) return;
  pulseDeviationHighlight(rows[0].chapter);
  await nextTick();
  try {
    document.querySelector('[data-testid="deviation-list"]')?.scrollIntoView?.({
      behavior: 'smooth',
      block: 'start',
    });
  } catch {
    /* jsdom */
  }
}

async function openFirstBatchDeviationChapter(start, end) {
  if (!uiProfile.value.batch_open_first_deviation) return;
  const rows = batchDeviationsInRange(start, end);
  if (!rows.length) return;
  pulseDeviationHighlight(rows[0].chapter);
  await jumpToChapter(rows[0].chapter);
}

function isConflictError(err) {
  return err instanceof Error && err.message.includes('409');
}

function handleSaveError(err) {
  if (isConflictError(err)) {
    conflictMessage.value = '磁盘上的文件已被修改（可能在编辑器中），请重新加载后再保存。';
    error.value = null;
    return;
  }
  error.value = err instanceof Error ? err.message : String(err);
}


const onboardingHub = useCreatorOnboarding({
  uiProfile,
  overview,
  error,
  saveMessage,
  handleSaveError,
  focusWizard,
  focusWizardStep,
  focusWizardDone,
  focusWizardNotes,
  setWizardDeepLink,
  buildWizardShareUrl,
});
const {
  panelContext: onboardingPanelContext,
  wizardEmailTo,
  loadOnboardingWizard,
  syncWizardPanelOpen,
} = onboardingHub;

const refreshRef = { fn: async () => {} };

const batchHistoryHub = useCreatorBatchHistory({
  uiProfile,
  batchStart,
  batchEnd,
  batchBudget,
  saveMessage,
  error,
});

const { panelContext: batchHistoryPanelContext, batchHistoryBudgetHint, loadBatchHistory } = batchHistoryHub;

const volumePlan = useCreatorVolumePlan({
  uiProfile,
  overview,
  saving,
  error,
  saveMessage,
  conflictMessage,
  globalOutlineEditorRef,
  globalOutlineText,
  batchStart,
  batchEnd,
  wizardEmailTo,
  handleSaveError,
  onAfterVolumePlanSave: async () => refreshRef.fn(),
});

const {
  panelContext: volumePlanPanelContext,
  editableVolumes,
  showVolumePlanDiffPrintPreview,
  volumePlanDiffShareLinkPreview,
  pendingShareApply,
  pendingShareMerge,
  shareE2eApplyDone,
  volumePlanDiffPrintPreviewText,
  loadVolumePlan,
  loadVolumeTemplates,
  loadTemplateSyncSources,
  loadTemplateApprovals,
  loadDiffCollabNotes,
  refreshVolumePlanDiffPreview,
  tryLoadVolumePlanDiffShareLinkPreview,
  dismissVolumePlanDiffShareLinkPreview,
  requestApplyVolumePlanDiffShareLink,
  confirmApplyVolumePlanDiffShareLink,
  cancelApplyVolumePlanDiffShareLink,
  confirmShareMergeUseShare,
  cancelShareMerge,
  closeVolumePlanDiffPrintPreview,
  printVolumePlanDiffPrintPreview,
  applyVolumePlanDiffShareLink,
  formatHistoryTime,
} = volumePlan;


const modeGuideHub = useCreatorModeGuide({
  uiProfile,
  overview,
  saveMessage,
  onboardingWizard: onboardingHub.onboardingWizard,
  linkModeToOnboardingStep: onboardingHub.linkModeToOnboardingStep,
});
const { panelContext: modeGuidePanelContext, loadCreationModeSwitchHistory, onCreationModeSwitchHotkey } = modeGuideHub;

















function showCreationModeBadgeHint() {
  if (!creationModeBadgeHintText.value) return;
  saveMessage.value = creationModeBadgeHintText.value;
}
















































async function runAdvancePreflight() {
  batchError.value = null;
  preflightOk.value = false;
  try {
    const data = await studioProductionPreflight({
      start_chapter: batchStart.value,
      end_chapter: batchEnd.value,
      budget_usd: batchBudget.value,
    });
    batchCommand.value = data.batch_command || '';
    preflightOk.value = Boolean(data.all_ok);
    if (!data.all_ok) {
      batchError.value = 'Preflight 未通过，请检查大纲与支柱';
    }
  } catch (e) {
    batchError.value = e instanceof Error ? e.message : String(e);
  }
}

async function runAdvanceBatch() {
  batchError.value = null;
  batchRunning.value = true;
  try {
    batchJob.value = await studioProductionRun({
      start_chapter: batchStart.value,
      end_chapter: batchEnd.value,
      budget_usd: batchBudget.value,
    });
    lastBatchStatus.value = batchJob.value?.status ?? 'running';
    if (batchJob.value?.status === 'running') {
      startBatchPolling();
    }
  } catch (e) {
    batchError.value = e instanceof Error ? e.message : String(e);
  } finally {
    batchRunning.value = false;
  }
}

function stopBatchPolling() {
  if (batchPollTimer) {
    clearInterval(batchPollTimer);
    batchPollTimer = null;
  }
}

function startBatchPolling() {
  stopBatchPolling();
  batchPollTimer = setInterval(async () => {
    const prev = lastBatchStatus.value;
    await pollBatchJob();
    const status = batchJob.value?.status ?? null;
    if (prev === 'running' && status === 'completed') {
      if (showAdvanceBatch.value && overview.value?.advance_volume_summary) {
        try {
          await generateCreatorVolumeSummary({
            startChapter: batchStart.value,
            endChapter: batchEnd.value,
          });
          batchSummaryPrompt.value = {
            start: batchStart.value,
            end: batchEnd.value,
            alert_volume_labels: [],
          };
        } catch {
          /* volume summary optional */
        }
      }
      saveMessage.value = 'Batch 已完成，卷摘要已更新';
      await refresh();
      if (batchSummaryPrompt.value) {
        batchSummaryPrompt.value = {
          ...batchSummaryPrompt.value,
          alert_volume_labels: uiProfile.value.batch_deviation_prompt
            ? collectBatchAlertVolumeLabels(batchStart.value, batchEnd.value)
            : [],
        };
      }
      if (uiProfile.value.batch_highlight_alert_volumes || uiProfile.value.batch_clear_pulse_no_alert) {
        await highlightBatchAlertVolumes(batchStart.value, batchEnd.value);
      }
      if (uiProfile.value.batch_auto_open_summary && batchSummaryPrompt.value) {
        openVolumeSummaryForRange(batchStart.value, batchEnd.value);
      }
      if (uiProfile.value.batch_scroll_deviation_list) {
        await scrollToBatchDeviationList(batchStart.value, batchEnd.value);
      }
      if (uiProfile.value.batch_open_first_deviation) {
        await openFirstBatchDeviationChapter(batchStart.value, batchEnd.value);
      }
      updateBatchDeviationInlineSummary(batchStart.value, batchEnd.value);
      await linkBatchDeviationInlineSummary(batchStart.value, batchEnd.value);
      await loadBatchHistory();
    }
    if (status === 'completed' || status === 'failed') {
      stopBatchPolling();
    }
    lastBatchStatus.value = status;
  }, 3000);
}

async function pollBatchJob() {
  try {
    const job = await fetchStudioActiveBatchJob();
    if (job) {
      batchJob.value = job;
      batchRunning.value = job.status === 'running';
    } else if (batchJob.value?.status === 'running') {
      batchJob.value = { ...batchJob.value, status: 'completed' };
      batchRunning.value = false;
    }
  } catch {
    /* optional */
  }
}

refreshRef.fn = refresh;

async function runCompanionLogicCheck() {
  logicCheckRunning.value = true;
  error.value = null;
  try {
    logicCheckResult.value = await runCreatorLogicCheck();
    saveMessage.value = logicCheckResult.value.passed
      ? '逻辑审查通过'
      : `发现 ${logicCheckResult.value.p0_count} 条 P0`;
    await refresh();
  } catch (e) {
    handleSaveError(e);
  } finally {
    logicCheckRunning.value = false;
  }
}


const settingsHub = useCreatorSettings({
  uiProfile,
  overview,
  error,
  saveMessage,
  conflictMessage,
  handleSaveError,
  onAfterSettingsSave: async () => refresh(),
  globalOutlineEditorRef,
  globalOutlineText,
  isWorkspaceColumnVisible,
  workspaceTabsEnabled,
  logicCheckRunning,
  logicCheckResult,
  activeLogicCheckIssueIdx,
  runCompanionLogicCheck,
  handleLogicCheckIssueClick,
  onLogicCheckIssueKeydown,
});
const {
  panelContext: settingsPanelContext,
  loadSettingsDocs,
  loadSettingsHistory,
  loadMergePreferences,
  loadMergePresetPackages,
} = settingsHub;


async function refresh() {
  loading.value = true;
  error.value = null;
  conflictMessage.value = '';
  try {
    const [ov] = await Promise.all([
      fetchCreatorOverview(),
      loadVolumePlan(),
      loadSettingsDocs(),
      loadSettingsHistory(),
      loadVolumeTemplates(),
      loadTemplateSyncSources(),
      loadOnboardingWizard(),
      pollBatchJob(),
    ]);
    overview.value = ov;
    maybeAutoSelectWritingChapter();
    syncWizardPanelOpen();
    loadCreationModeSwitchHistory();
    await refreshVolumePlanDiffPreview();
    await loadMergePreferences();
    await loadMergePresetPackages();
    await loadTemplateApprovals();
    await loadBatchHistory();
    await loadDiffCollabNotes();
    tryLoadVolumePlanDiffShareLinkPreview();
    if (batchJob.value?.status === 'running' && !batchPollTimer) {
      lastBatchStatus.value = 'running';
      startBatchPolling();
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    loading.value = false;
  }
}



provide(
  CREATOR_SETTINGS_KEY,
  createCreatorSettingsContext(settingsPanelContext),
);
provide(
  CREATOR_ONBOARDING_KEY,
  createCreatorOnboardingContext(onboardingPanelContext),
);
provide(
  CREATOR_MODE_GUIDE_KEY,
  createCreatorModeGuideContext(modeGuidePanelContext),
);

provide(
  CREATOR_BATCH_HISTORY_KEY,
  createCreatorBatchHistoryContext(batchHistoryPanelContext),
);

provide(
  CREATOR_VOLUME_PLAN_KEY,
  createCreatorVolumePlanContext(volumePlanPanelContext),
);

onMounted(() => {
  refresh();
  window.addEventListener('keydown', onCreationModeSwitchHotkey);
});

onUnmounted(() => {
  window.removeEventListener('keydown', onCreationModeSwitchHotkey);
  stopBatchPolling();
  if (chapterBodyHighlightTimer) {
    clearTimeout(chapterBodyHighlightTimer);
    chapterBodyHighlightTimer = null;
  }
  if (logicCheckIssueHighlightTimer) {
    clearTimeout(logicCheckIssueHighlightTimer);
    logicCheckIssueHighlightTimer = null;
  }
  if (deviationHighlightTimer) {
    clearTimeout(deviationHighlightTimer);
    deviationHighlightTimer = null;
  }
});

watch(projectRevision, () => {
  refresh();
});


watch(
  editableVolumes,
  () => {
    refreshVolumePlanDiffPreview();
  },
  { deep: true },
);
</script>

<style scoped>
.creator-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.creator-grid--tabbed {
  grid-template-columns: 1fr;
}

.creator-workspace-tabs {
  padding: 0 var(--space-md);
}

.deviation-badge--clickable {
  cursor: pointer;
}

.deviation-badge--clickable:hover {
  outline: 2px solid var(--color-accent);
}



.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.page-title {
  font-size: 14px;
  color: var(--color-accent);
  font-family: 'Press Start 2P', monospace;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.mode-badge,
.deviation-badge {
  font-size: var(--text-sm);
  padding: var(--space-xs) var(--space-sm);
  font-family: 'Press Start 2P', monospace;
}

.deviation-badge {
  color: #c44;
}

.creator-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-md);
  align-items: start;
}

@media (max-width: 960px) {
  .creator-grid {
    grid-template-columns: 1fr;
  }
}

.creator-column {
  padding: var(--space-md);
  min-height: 280px;
}

.column-title {
  font-size: var(--text-lg);
  margin-bottom: var(--space-sm);
  color: var(--color-accent);
  font-family: 'Press Start 2P', monospace;
}

.column-hint {
  font-size: var(--text-sm);
  opacity: 0.7;
  margin-bottom: var(--space-md);
}

.chapter-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.chapter-row {
  display: flex;
  justify-content: space-between;
  font-size: var(--text-sm);
  padding: 4px 6px;
  border: 1px solid var(--border-color);
}

.chapter-row--done {
  background: rgba(100, 200, 100, 0.08);
}

.chapter-row {
  cursor: pointer;
}

.chapter-row--selected {
  outline: 2px solid var(--color-accent);
}

.chapter-preview {
  margin-top: var(--space-md);
  padding: var(--space-sm);
  max-height: 320px;
  overflow: auto;
}

.chapter-dual-edit {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-sm);
  margin-top: var(--space-sm);
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
  background: rgba(255, 220, 100, 0.35);
}

.issue-line--active {
  animation: issue-line-flash 1.2s ease-out;
  background: rgba(255, 220, 100, 0.35);
  box-shadow: inset 0 0 0 1px rgba(200, 180, 80, 0.65);
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


.mode-badge--hintable {
  cursor: help;
}

.mode-badge--companion-tint {
  color: #2a6;
  background: rgba(80, 180, 120, 0.15);
  box-shadow: inset 0 0 0 1px rgba(60, 140, 90, 0.45);
}

.mode-badge--advance-tint {
  color: #36a;
  background: rgba(80, 140, 220, 0.15);
  box-shadow: inset 0 0 0 1px rgba(60, 110, 180, 0.45);
}

.mode-badge--studio-tint {
  color: #a63;
  background: rgba(200, 140, 80, 0.15);
  box-shadow: inset 0 0 0 1px rgba(160, 110, 60, 0.45);
}

.volume-plan-diff-count {
  margin-left: var(--space-xs);
  padding: 1px 4px;
  border-radius: 2px;
  color: #a60;
  background: rgba(255, 200, 80, 0.35);
  font-family: 'Press Start 2P', monospace;
  font-size: 6px;
}









































































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

.logic-check-issue:focus-visible {
  outline: 2px solid rgba(200, 180, 80, 0.85);
  outline-offset: 1px;
}

@keyframes issue-line-flash {
  0% { background: rgba(255, 220, 100, 0.55); }
  100% { background: rgba(255, 220, 100, 0.35); }
}

.chapter-body-textarea--highlight {
  animation: chapter-body-highlight-pulse 1.2s ease-out;
  box-shadow: 0 0 0 2px rgba(200, 180, 80, 0.75);
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

.chapter-inline-edit {
  margin-top: var(--space-sm);
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

.volume-pulse-row {
  cursor: pointer;
  padding-left: var(--space-xs);
  margin-bottom: var(--space-xs);
}

.volume-pulse-row--alert {
  border-left: 3px solid #c66;
}

.volume-pulse-row--warn {
  border-left: 3px solid #aa8;
}

.volume-pulse-row--ok {
  border-left: 3px solid #6a6;
}

.volume-pulse-panel--alert {
  border-color: #c66;
}

.volume-pulse-panel--warn {
  border-color: #aa8;
}

.volume-pulse-row--active {
  outline: 2px solid var(--color-accent);
}

.volume-pulse-generate-btn {
  margin-left: var(--space-xs);
  font-size: var(--text-xs);
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

.issue-severity {
  display: inline-block;
  min-width: 2.5em;
  margin-right: var(--space-xs);
  font-weight: bold;
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

.chapter-recheck-panel {
  margin-top: var(--space-sm);
  padding: var(--space-xs);
  background: rgba(200, 180, 80, 0.1);
}

.batch-alert-volumes {
  color: #c44;
  font-weight: bold;
}

.batch-summary-prompt {
  margin: var(--space-sm) 0;
  padding: var(--space-sm);
  background: rgba(80, 160, 120, 0.12);
}

.preview-text {
  font-size: var(--text-sm);
  white-space: pre-wrap;
  margin: var(--space-xs) 0;
}

.chapter-row--warn {
  background: rgba(200, 180, 80, 0.15);
  border-color: #aa8;
}

.chapter-row--alert {
  background: rgba(200, 80, 80, 0.15);
  border-color: #c66;
}

.progress-bar {
  height: 12px;
  margin-top: var(--space-sm);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-accent);
  transition: width 0.2s;
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

.deviation-list {
  list-style: none;
  padding: 0;
  margin: var(--space-sm) 0 0;
  font-size: var(--text-sm);
}

.deviation-warn { color: #886600; }
.deviation-alert { color: #c44; }

.deviation-item--clickable {
  cursor: pointer;
}

.deviation-item--clickable:hover {
  text-decoration: underline;
}

.deviation-item--active {
  animation: deviation-item-flash 1.2s ease-out;
  box-shadow: inset 0 0 0 2px rgba(200, 80, 80, 0.55);
}

@keyframes deviation-item-flash {
  0% { background: rgba(255, 200, 120, 0.45); }
  100% { background: transparent; }
}

.deviation-chapter {
  display: inline-block;
  min-width: 3.5em;
  margin-right: var(--space-xs);
  font-weight: bold;
}

.volume-block--alert summary {
  color: #c44;
}

.volume-block--warn summary {
  color: #886600;
}

.volume-block--ok summary {
  color: #3a7;
}

.volume-summary-status {
  opacity: 0.85;
  font-size: var(--text-xs);
}


.batch-range {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: var(--text-sm);
  margin-bottom: 6px;
}


.advance-batch-panel {
  margin-top: var(--space-md);
  padding: var(--space-sm);
}

.batch-error {
  color: #c44;
  font-size: var(--text-sm);
  margin-top: 4px;
}




.path-line,


.meta-line {
  font-size: var(--text-sm);
  opacity: 0.75;
}

.refresh-btn {
  font-size: var(--text-sm);
  padding: var(--space-xs) var(--space-sm);
  cursor: pointer;
}

.error-banner {
  padding: var(--space-sm);
  color: #c44;
  font-size: var(--text-sm);
}

.save-banner {
  padding: var(--space-sm);
  color: #484;
  font-size: var(--text-sm);
}

.conflict-banner {
  padding: var(--space-sm);
  color: #a60;
  font-size: var(--text-sm);
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}




.mini-btn--danger {
  color: #c44;
}





























.volume-template-panel {
  margin-bottom: var(--space-sm);
  padding: var(--space-sm);
}

.pulse-empty-guide {
  margin-bottom: var(--space-sm);
  padding: var(--space-md);
}

.pulse-empty-guide .meta-line {
  margin: var(--space-xs) 0 var(--space-sm);
}

.companion-logic-check-write {
  margin-top: var(--space-md);
  padding: var(--space-md);
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





</style>

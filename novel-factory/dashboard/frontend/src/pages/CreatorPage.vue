<!--
  CreatorPage.vue — 创作者三栏：写 / 脉络 / 设定 + 卷纲锁定与偏离 diff
-->
<template>
  <div class="creator-page">
    <header class="page-header">
      <h1 class="page-title" data-testid="page-title">创作伴侣</h1>
      <div class="header-actions">
        <span v-if="overview" class="mode-badge pixel-border" data-testid="creation-mode-badge">
          {{ modeLabel }}
        </span>
        <span
          v-if="overview && overview.deviation_count"
          class="deviation-badge pixel-border"
          data-testid="deviation-badge"
        >
          偏离 {{ overview.deviation_count }}
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

    <details
      v-if="onboardingWizard"
      ref="wizardPanelRef"
      class="onboarding-wizard pixel-border"
      data-testid="onboarding-wizard-panel"
      :open="focusWizard"
      @toggle="onWizardToggle"
    >
      <summary>
        入门向导 · {{ onboardingWizard.mode_label }}（{{ onboardingWizard.max_chapter }} 章上限）
        <span v-if="onboardingWizard.progress_pct != null" class="wizard-progress-badge" data-testid="wizard-progress-label">
          · {{ onboardingWizard.progress_pct }}%
        </span>
        <span
          v-if="wizardUnreadMentions > 0"
          class="wizard-notification-badge"
          data-testid="wizard-notification-badge"
        >
          · {{ wizardUnreadMentions }} 条 @提及
        </span>
      </summary>
      <div
        v-if="wizardNotifications.length"
        class="wizard-notifications"
        data-testid="wizard-notifications-panel"
      >
        <p class="meta-line">批注通知</p>
        <label v-if="wizardNotificationHandles.length" class="meta-line">
          按 handle 过滤
          <select
            v-model="wizardNotificationHandleFilter"
            class="vol-input"
            data-testid="wizard-notification-handle-filter"
            @change="loadWizardNotifications"
          >
            <option value="">全部</option>
            <option v-for="handle in wizardNotificationHandles" :key="handle" :value="handle">
              @{{ handle }}
            </option>
          </select>
        </label>
        <div
          v-if="wizardNotificationDigest.groups?.length"
          class="wizard-digest-panel"
          data-testid="wizard-notification-digest"
        >
          <p class="meta-line">通知摘要（{{ wizardNotificationDigest.unread }} 条未读）</p>
          <ul>
            <li
              v-for="group in wizardNotificationDigest.groups"
              :key="group.handle"
              class="wizard-digest-row"
              data-testid="wizard-digest-row"
            >
              <strong>@{{ group.handle }}</strong>
              <span class="meta-line">{{ group.count }} 条 · {{ group.steps.map((s) => s.step_id).join(', ') }}</span>
            </li>
          </ul>
        </div>
        <div class="wizard-digest-schedule-panel" data-testid="wizard-digest-schedule-panel">
          <p class="meta-line">定时 digest</p>
          <label class="meta-line">
            <input v-model="wizardDigestScheduleEnabled" type="checkbox" data-testid="wizard-digest-schedule-enabled" />
            启用（每 {{ wizardDigestScheduleHours }} 小时）
          </label>
          <input
            v-model.number="wizardDigestScheduleHours"
            type="number"
            min="1"
            max="168"
            class="vol-input"
            data-testid="wizard-digest-schedule-hours"
          />
          <button
            type="button"
            class="mini-btn pixel-border"
            data-testid="save-wizard-digest-schedule-btn"
            @click="saveWizardDigestSchedule"
          >
            保存定时
          </button>
          <button
            type="button"
            class="mini-btn pixel-border"
            data-testid="dispatch-wizard-digest-btn"
            @click="dispatchWizardDigest"
          >
            立即发送 digest
          </button>
            <p class="meta-line" data-testid="wizard-digest-background-hint">
            Dashboard 后台每 15 分钟自动检查到期 digest
          </p>
          <p
            v-if="wizardDigestStats.sent_total || wizardDigestStats.failed_total"
            class="meta-line"
            data-testid="wizard-digest-stats"
          >
            发送统计：成功 {{ wizardDigestStats.sent_total }} / 失败 {{ wizardDigestStats.failed_total }}
          </p>
          <input
            v-model="wizardDigestHandleChannelsJson"
            class="vol-input"
            data-testid="wizard-digest-handle-channels"
            placeholder='handle 路由 JSON，如 {"batch":["webhook"],"*":["email"]}'
          />
          <input
            v-model="wizardDigestHandleQuietJson"
            class="vol-input"
            data-testid="wizard-digest-handle-quiet-hours"
            placeholder='handle 静默 JSON，如 {"batch":{"start":22,"end":6}}'
          />
          <label class="meta-line">
            静默时段（UTC）
            <input
              v-model.number="wizardDigestQuietStart"
              type="number"
              min="0"
              max="23"
              class="vol-input"
              data-testid="wizard-digest-quiet-start"
              placeholder="起"
            />
            –
            <input
              v-model.number="wizardDigestQuietEnd"
              type="number"
              min="0"
              max="23"
              class="vol-input"
              data-testid="wizard-digest-quiet-end"
              placeholder="止"
            />
          </label>
          <div
            v-if="wizardDigestRetryQueue.item_count"
            class="wizard-digest-retry"
            data-testid="wizard-digest-retry-panel"
          >
            <p class="meta-line">重试队列 {{ wizardDigestRetryQueue.item_count }} 条</p>
            <button
              type="button"
              class="mini-btn pixel-border"
              data-testid="process-wizard-digest-retry-btn"
              @click="processWizardDigestRetries"
            >
              重试失败 digest
            </button>
          </div>
          <div
            v-if="wizardDigestDeadLetter.item_count"
            class="wizard-digest-dead-letter"
            data-testid="wizard-digest-dead-letter-panel"
          >
            <p class="meta-line">死信队列 {{ wizardDigestDeadLetter.item_count }} 条</p>
          </div>
        </div>
        <ul>
          <li
            v-for="note in wizardNotifications"
            :key="note.id"
            class="wizard-notification-row"
            :class="{ 'wizard-notification-row--unread': !note.read }"
            data-testid="wizard-notification-row"
          >
            <strong>@{{ note.handle }}</strong>
            <span class="meta-line">{{ note.step_id }} · {{ note.note_excerpt }}</span>
          </li>
        </ul>
        <button
          type="button"
          class="mini-btn pixel-border"
          data-testid="wizard-ack-notifications-btn"
          @click="ackWizardNotifications"
        >
          全部标为已读
        </button>
        <div class="wizard-webhook-panel" data-testid="wizard-webhook-panel">
          <p class="meta-line">通知 Webhook</p>
          <label class="meta-line">
            <input v-model="wizardWebhookEnabled" type="checkbox" data-testid="wizard-webhook-enabled" />
            启用
          </label>
          <input
            v-model="wizardWebhookUrl"
            class="vol-input"
            data-testid="wizard-webhook-url"
            placeholder="https://example.com/hooks/mentions"
          />
          <input
            v-model="wizardWebhookSigningSecret"
            class="vol-input"
            data-testid="wizard-webhook-signing-secret"
            placeholder="Webhook 签名密钥（可选）"
          />
          <button
            type="button"
            class="mini-btn pixel-border"
            data-testid="save-wizard-webhook-btn"
            @click="saveWizardWebhook"
          >
            保存 Webhook
          </button>
        </div>
        <div class="wizard-email-panel" data-testid="wizard-email-panel">
          <p class="meta-line">通知邮件</p>
          <label class="meta-line">
            <input v-model="wizardEmailEnabled" type="checkbox" data-testid="wizard-email-enabled" />
            启用
          </label>
          <input
            v-model="wizardEmailTo"
            class="vol-input"
            data-testid="wizard-email-to"
            placeholder="user@example.com"
          />
          <input
            v-model="wizardEmailSmtpHost"
            class="vol-input"
            data-testid="wizard-email-smtp-host"
            placeholder="smtp.example.com"
          />
          <button
            type="button"
            class="mini-btn pixel-border"
            data-testid="save-wizard-email-btn"
            @click="saveWizardEmail"
          >
            保存邮件
          </button>
        </div>
      </div>
      <ol class="wizard-steps">
        <li
          v-for="step in onboardingWizard.steps"
          :key="step.id"
          class="wizard-step"
          :class="{ 'wizard-step--focused': step.id === focusWizardStep }"
        >
          <label class="wizard-step-label">
            <input
              type="checkbox"
              :checked="completedWizardSteps.has(step.id)"
              :data-testid="`wizard-step-${step.id}`"
              @change="toggleWizardStep(step.id, $event.target.checked)"
            />
            <span>
              <strong>{{ step.title }}</strong>
              <span
                v-if="autoCompletedWizardSteps.has(step.id)"
                class="wizard-auto-badge"
                data-testid="wizard-auto-badge"
              >自动</span>
              <span class="meta-line">{{ step.detail }}</span>
            </span>
          </label>
          <textarea
            :value="wizardStepNotes[step.id] || ''"
            class="vol-input wizard-step-note"
            :data-testid="`wizard-note-${step.id}`"
            placeholder="协作批注（可选，支持 @volume @reviewer）"
            rows="2"
            @input="wizardStepNotes[step.id] = $event.target.value"
            @blur="saveWizardStepNote(step.id)"
          />
          <div
            v-if="wizardMentionsForStep(step.id).length"
            class="wizard-mentions"
            data-testid="wizard-mentions"
          >
            <span
              v-for="mention in wizardMentionsForStep(step.id)"
              :key="`${step.id}-${mention}`"
              class="wizard-mention-badge"
              data-testid="wizard-mention-badge"
            >@{{ mention }}</span>
          </div>
        </li>
      </ol>
      <p class="meta-line">
        清单：<code>{{ onboardingWizard.checklist_doc }}</code> ·
        冒烟：<code>{{ onboardingWizard.smoke_command }}</code>
      </p>
      <div class="merge-range">
        <button
          type="button"
          class="mini-btn pixel-border"
          data-testid="wizard-share-link-btn"
          @click="copyWizardShareLink"
        >
          复制分享链接
        </button>
        <span v-if="wizardShareMessage" class="meta-line" data-testid="wizard-share-message">{{ wizardShareMessage }}</span>
      </div>
    </details>

    <div v-if="overview" class="creator-grid" data-testid="creator-grid">
      <!-- 写 -->
      <section class="creator-column pixel-card" data-testid="column-write">
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
            <details v-if="chapterPreview.has_outline" open>
              <summary>分章大纲</summary>
              <pre class="preview-text">{{ chapterPreview.outline_preview || '（空）' }}</pre>
            </details>
            <details v-if="chapterPreview.has_body" :open="!chapterPreview.has_outline">
              <summary>正文</summary>
              <pre class="preview-text">{{ chapterPreview.body_preview || '（空）' }}</pre>
              <p v-if="chapterPreview.body_truncated" class="meta-line">正文已截断 · 完整内容请在编辑器查看</p>
            </details>
            <p v-if="!chapterPreview.has_body && !chapterPreview.has_outline" class="meta-line">
              本章尚无大纲与正文
            </p>
          </template>
        </div>
        <p v-if="overview.chapters.length > 15" class="meta-line">
          显示前 15 章 · 共 {{ overview.max_chapter }} 章上限
        </p>
      </section>

      <!-- 脉络 -->
      <section class="creator-column pixel-card" data-testid="column-pulse">
        <h2 class="column-title">脉络</h2>
        <div class="progress-block">
          <p class="progress-text">
            已写 <strong>{{ overview.chapters_written }}</strong> / {{ overview.max_chapter }} 章
            （{{ overview.coverage_pct }}%）
          </p>
          <div class="progress-bar pixel-border">
            <div
              class="progress-fill"
              :style="{ width: `${Math.min(100, overview.coverage_pct)}%` }"
            />
          </div>
        </div>

        <div class="volume-plan-panel" data-testid="volume-plan-panel">
          <div class="volume-plan-header">
            <h3 class="subsection-title">卷纲</h3>
            <button
              type="button"
              class="mini-btn pixel-border"
              data-testid="add-volume-btn"
              @click="addVolume"
            >
              + 卷
            </button>
          </div>
          <div
            v-if="volumeTemplates.length"
            class="volume-template-panel pixel-border"
            data-testid="volume-template-panel"
          >
            <h3 class="subsection-title">模板库</h3>
            <div class="merge-range">
              <select v-model="selectedTemplateId" class="vol-input" data-testid="volume-template-select">
                <option v-for="t in volumeTemplates" :key="t.id" :value="t.id">
                  {{ formatTemplateOption(t) }}
                </option>
              </select>
              <button
                type="button"
                class="mini-btn pixel-border"
                data-testid="apply-template-btn"
                :disabled="templateApplying"
                @click="applyVolumeTemplate"
              >
                {{ templateApplying ? '套用中…' : '套用模板' }}
              </button>
              <button
                v-if="selectedTemplateProject"
                type="button"
                class="mini-btn pixel-border"
                data-testid="delete-template-btn"
                :disabled="templateDeleting"
                @click="deleteSelectedVolumeTemplate"
              >
                {{ templateDeleting ? '删除中…' : '删除模板' }}
              </button>
              <button
                v-if="selectedTemplateProject"
                type="button"
                class="mini-btn pixel-border"
                data-testid="publish-factory-template-btn"
                :disabled="templatePublishing"
                @click="publishSelectedTemplateToFactory"
              >
                {{ templatePublishing ? '发布中…' : '发布到工厂库' }}
              </button>
              <button
                v-if="selectedTemplateFactory"
                type="button"
                class="mini-btn mini-btn--danger pixel-border"
                data-testid="delete-factory-template-btn"
                :disabled="factoryDeleting"
                @click="deleteSelectedFactoryTemplate"
              >
                {{ factoryDeleting ? '删除中…' : '从工厂库删除' }}
              </button>
            </div>
            <div v-if="selectedTemplateProject || selectedTemplateFactory" class="merge-range">
              <input
                v-model="templateVersionLabel"
                class="vol-input vol-conflict"
                data-testid="template-version-input"
                placeholder="版本标签（semver，如 v1.2.0）"
              />
              <p
                v-if="templateVersionLabel && !isSemverVersionLabel(templateVersionLabel)"
                class="meta-line version-semver-warn"
                data-testid="template-version-semver-warn"
              >
                版本标签需符合 semver（如 v1.2.0）
              </p>
              <button
                type="button"
                class="mini-btn pixel-border"
                data-testid="set-template-version-btn"
                :disabled="templateVersionSaving"
                @click="saveTemplateVersionLabel"
              >
                {{ templateVersionSaving ? '保存中…' : '设版本标签' }}
              </button>
              <button
                v-if="selectedTemplateProject || selectedTemplateFactory"
                type="button"
                class="mini-btn pixel-border"
                data-testid="submit-template-version-approval-btn"
                :disabled="templateApprovalSubmitting"
                @click="submitTemplateVersionApproval"
              >
                {{ templateApprovalSubmitting ? '提交中…' : '提交审批' }}
              </button>
            </div>
            <div
              class="template-approval-chain-config"
              data-testid="template-approval-chain-config"
            >
              <p class="meta-line">审批链步数</p>
              <input
                v-model.number="templateApprovalChainSteps"
                type="number"
                min="1"
                max="5"
                class="vol-input"
                data-testid="template-approval-chain-steps"
              />
              <input
                v-model="templateApprovalStepAssignees"
                type="text"
                class="vol-input"
                data-testid="template-approval-step-assignees"
                placeholder="审批人（逗号分步）"
              />
              <input
                v-model="templateApprovalOrGroups"
                type="text"
                class="vol-input"
                data-testid="template-approval-or-groups"
                placeholder="OR 签：alice|bob,carol"
              />
              <button
                type="button"
                class="mini-btn pixel-border"
                data-testid="save-template-approval-chain-btn"
                @click="saveTemplateApprovalChainConfig"
              >
                保存审批链
              </button>
            </div>
            <div
              class="template-approval-sla-config"
              data-testid="template-approval-sla-config"
            >
              <p class="meta-line">审批 SLA（{{ templateApprovalSlaHours }} 小时）</p>
              <input
                v-model.number="templateApprovalSlaHours"
                type="number"
                min="1"
                max="720"
                class="vol-input"
                data-testid="template-approval-sla-hours"
              />
              <label class="meta-line">
                <input v-model="templateApprovalEmailOnSubmit" type="checkbox" data-testid="template-approval-email-submit" />
                提交时发邮件
              </label>
              <label class="meta-line">
                <input v-model="templateApprovalEmailOnReject" type="checkbox" data-testid="template-approval-email-reject" />
                驳回时发邮件
              </label>
              <label class="meta-line">
                <input v-model="templateApprovalEmailOnOverdue" type="checkbox" data-testid="template-approval-email-overdue" />
                超时时发邮件
              </label>
              <button
                type="button"
                class="mini-btn pixel-border"
                data-testid="save-template-approval-sla-btn"
                @click="saveTemplateApprovalSlaConfig"
              >
                保存 SLA
              </button>
            </div>
            <div
              v-if="overdueTemplateApprovals.length"
              class="template-approval-overdue"
              data-testid="template-approval-overdue-panel"
            >
              <p class="meta-line">超时待审批（{{ overdueTemplateApprovals.length }}）</p>
              <ul>
                <li
                  v-for="approval in overdueTemplateApprovals"
                  :key="approval.id"
                  data-testid="template-approval-overdue-row"
                >
                  {{ approval.template_id }} · {{ approval.hours_pending }}h
                </li>
              </ul>
            </div>
            <div
              v-if="pendingTemplateApprovals.length"
              class="template-approvals"
              data-testid="template-approvals-panel"
            >
              <p class="meta-line">待审批版本变更</p>
              <ul>
                <li
                  v-for="approval in pendingTemplateApprovals"
                  :key="approval.id"
                  class="template-approval-row"
                  data-testid="template-approval-row"
                >
                  <span>{{ approval.previous_label || '—' }} → {{ approval.version_label || '（清除）' }}</span>
                  <span class="meta-line" data-testid="template-approval-chain-progress">{{ approval.chain_progress }}</span>
                  <span
                    v-if="approval.or_signing && approval.current_assignees?.length"
                    class="meta-line"
                    data-testid="template-approval-or-assignees"
                  >
                    OR 签：{{ approval.current_assignees.join(' / ') }}
                  </span>
                  <span
                    v-else-if="approval.current_assignee"
                    class="meta-line"
                    data-testid="template-approval-current-assignee"
                  >
                    指派：{{ approval.current_assignee }}
                  </span>
                  <span
                    v-if="approval.submit_note"
                    class="meta-line"
                    data-testid="template-approval-submit-note"
                  >
                    备注：{{ approval.submit_note }}
                  </span>
                  <button
                    type="button"
                    class="mini-btn pixel-border"
                    data-testid="preview-approval-snapshot-diff-btn"
                    @click="previewApprovalSnapshotDiff(approval.id)"
                  >
                    快照 diff
                  </button>
                  <button
                    type="button"
                    class="mini-btn pixel-border"
                    data-testid="transfer-template-approval-btn"
                    @click="transferTemplateApproval(approval.id)"
                  >
                    转交
                  </button>
                  <button
                    type="button"
                    class="mini-btn pixel-border"
                    data-testid="approve-template-version-btn"
                    @click="approveTemplateVersion(approval.id)"
                  >
                    批准
                  </button>
                  <button
                    type="button"
                    class="mini-btn pixel-border"
                    data-testid="reject-template-version-btn"
                    @click="rejectTemplateVersion(approval.id)"
                  >
                    驳回
                  </button>
                </li>
              </ul>
            </div>
            <div
              v-if="templateApprovalHistory.length"
              class="template-approval-history"
              data-testid="template-approval-history-panel"
            >
              <p class="meta-line">
                审批历史
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="export-template-approval-audit-btn"
                  @click="exportTemplateApprovalAudit"
                >
                  导出审计
                </button>
              </p>
              <ul>
                <li
                  v-for="row in templateApprovalHistory"
                  :key="row.id"
                  class="template-approval-row"
                  data-testid="template-approval-history-row"
                >
                  <span>{{ row.template_id }} · {{ row.status }}</span>
                  <span class="meta-line">{{ row.previous_label || '—' }} → {{ row.version_label || '（清除）' }}</span>
                  <span
                    v-if="row.chain_log?.length"
                    class="meta-line"
                    data-testid="template-approval-chain-log"
                  >
                    链 {{ row.chain_log.length }} 步
                  </span>
                </li>
              </ul>
            </div>
            <div
              v-if="(selectedTemplateProject || selectedTemplateFactory) && templateVersionChangelog.length"
              class="template-changelog"
              data-testid="template-version-changelog"
            >
              <p class="meta-line">版本变更日志</p>
              <ul>
                <li
                  v-for="(entry, idx) in templateVersionChangelog"
                  :key="`${entry.changed_at}-${idx}`"
                  class="changelog-row"
                  data-testid="template-changelog-row"
                >
                  <span v-if="entry.previous_label">{{ entry.previous_label }} → </span>
                  <strong>{{ entry.version_label || '（清除）' }}</strong>
                  <span v-if="entry.changed_at" class="meta-line"> · {{ formatHistoryTime(entry.changed_at) }}</span>
                  <span
                    v-if="entry.diff_summary?.changed"
                    class="meta-line changelog-diff"
                    data-testid="template-changelog-diff"
                  >
                    · 卷纲 +{{ entry.diff_summary.lines_added }}/-{{ entry.diff_summary.lines_removed }}
                  </span>
                  <button
                    v-if="entry.visual_diff?.lines?.length"
                    type="button"
                    class="mini-btn pixel-border changelog-visual-btn"
                    data-testid="template-changelog-visual-btn"
                    @click="toggleChangelogVisual(idx)"
                  >
                    {{ expandedChangelogVisual === idx ? '收起对比' : '可视化对比' }}
                  </button>
                  <button
                    v-if="entry.can_rollback"
                    type="button"
                    class="mini-btn pixel-border"
                    data-testid="template-changelog-rollback-btn"
                    :disabled="templateRollbackSaving"
                    @click="rollbackTemplateVersion(entry, idx)"
                  >
                    {{ templateRollbackSaving ? '回滚中…' : '回滚到此版本' }}
                  </button>
                  <pre
                    v-if="expandedChangelogVisual === idx && entry.visual_diff?.lines?.length"
                    class="changelog-visual-diff"
                    data-testid="template-changelog-visual-diff"
                  ><span
                    v-for="(line, lineIdx) in entry.visual_diff.lines"
                    :key="`${idx}-${lineIdx}`"
                    :class="`visual-diff-line visual-diff-line--${line.type}`"
                  >{{ line.type === 'add' ? '+ ' : line.type === 'remove' ? '- ' : '  ' }}{{ line.text }}
</span></pre>
                </li>
              </ul>
            </div>
            <div v-if="selectedTemplateProject" class="merge-range">
              <input
                v-model="renameTemplateName"
                class="vol-input vol-conflict"
                data-testid="rename-template-name-input"
                placeholder="重命名模板"
              />
              <button
                type="button"
                class="mini-btn pixel-border"
                data-testid="rename-template-btn"
                :disabled="templateRenaming || !renameTemplateName.trim()"
                @click="renameSelectedVolumeTemplate"
              >
                {{ templateRenaming ? '重命名中…' : '重命名' }}
              </button>
            </div>
            <p v-if="selectedTemplateHint" class="meta-line">{{ selectedTemplateHint }}</p>
            <div v-if="editableVolumes.length" class="merge-range">
              <input
                v-model="customTemplateName"
                class="vol-input vol-conflict"
                data-testid="save-template-name-input"
                placeholder="自定义模板名"
              />
              <button
                type="button"
                class="mini-btn pixel-border"
                data-testid="save-template-btn"
                :disabled="templateSaving || !customTemplateName.trim()"
                @click="saveCustomVolumeTemplate"
              >
                {{ templateSaving ? '保存中…' : '存为模板' }}
              </button>
            </div>
            <div class="merge-range">
              <button
                type="button"
                class="mini-btn pixel-border"
                data-testid="export-templates-btn"
                @click="exportCustomTemplates"
              >
                导出 JSON
              </button>
              <button
                type="button"
                class="mini-btn pixel-border"
                data-testid="toggle-import-templates-btn"
                @click="showImportTemplates = !showImportTemplates"
              >
                {{ showImportTemplates ? '收起导入' : '导入 JSON' }}
              </button>
              <button
                v-if="templateSyncSources.length"
                type="button"
                class="mini-btn pixel-border"
                data-testid="sync-templates-btn"
                :disabled="templateSyncing"
                @click="syncTemplatesFromProjects"
              >
                {{ templateSyncing ? '同步中…' : '跨项目同步' }}
              </button>
              <button
                v-if="factoryTemplateCount"
                type="button"
                class="mini-btn pixel-border"
                data-testid="pull-factory-templates-btn"
                :disabled="factoryPulling"
                @click="pullFactoryTemplates"
              >
                {{ factoryPulling ? '拉取中…' : '从工厂库拉取' }}
              </button>
            </div>
            <div v-if="showImportTemplates" class="import-templates-panel" data-testid="import-templates-panel">
              <textarea
                v-model="importTemplatesJson"
                class="vol-input import-templates-json"
                data-testid="import-templates-json"
                placeholder='{"templates":[...]}'
                rows="4"
              />
              <button
                type="button"
                class="mini-btn pixel-border"
                data-testid="import-templates-btn"
                :disabled="templateImporting || !importTemplatesJson.trim()"
                @click="importCustomTemplates"
              >
                {{ templateImporting ? '导入中…' : '确认导入' }}
              </button>
            </div>
          </div>
          <div v-if="!editableVolumes.length" class="meta-line">暂无卷纲，点击「+ 卷」或套用模板。</div>
          <div
            v-for="(vol, idx) in editableVolumes"
            :key="`${idx}-${vol.label}`"
            class="volume-edit-row pixel-border"
            :class="{
              'volume-edit-row--locked': vol.locked,
              'volume-edit-row--dragging': dragVolumeIndex === idx,
            }"
            draggable="true"
            :data-testid="`volume-row-${idx}`"
            @dragstart="onVolumeDragStart(idx, $event)"
            @dragover.prevent
            @drop.prevent="onVolumeDrop(idx)"
          >
            <div class="volume-reorder">
              <button
                type="button"
                class="mini-btn pixel-border"
                :data-testid="`volume-move-up-${idx}`"
                :disabled="idx === 0"
                title="上移"
                @click="moveVolume(idx, idx - 1)"
              >
                ↑
              </button>
              <button
                type="button"
                class="mini-btn pixel-border"
                :data-testid="`volume-move-down-${idx}`"
                :disabled="idx === editableVolumes.length - 1"
                title="下移"
                @click="moveVolume(idx, idx + 1)"
              >
                ↓
              </button>
              <span class="drag-handle" data-testid="volume-drag-handle" title="拖拽排序">⋮⋮</span>
            </div>
            <input v-model="vol.label" class="vol-input vol-label" placeholder="卷名" />
            <div class="vol-range">
              <input v-model.number="vol.start_chapter" type="number" min="1" class="vol-input vol-num" />
              <span>–</span>
              <input v-model.number="vol.end_chapter" type="number" min="1" class="vol-input vol-num" />
            </div>
            <input
              v-model="vol.core_conflict"
              class="vol-input vol-conflict"
              placeholder="核心冲突"
            />
            <button
              type="button"
              class="mini-btn pixel-border"
              :data-testid="`lock-volume-${idx}`"
              @click="toggleLock(idx)"
            >
              {{ vol.locked ? '已锁' : '锁定' }}
            </button>
          </div>
          <button
            v-if="editableVolumes.length"
            type="button"
            class="save-btn pixel-border"
            data-testid="save-volume-plan-btn"
            :disabled="saving"
            @click="saveVolumePlan"
          >
            {{ saving ? '保存中…' : '保存卷纲' }}
          </button>
          <div
            v-if="editableVolumes.length >= 2"
            class="volume-merge-panel pixel-border"
            data-testid="volume-merge-panel"
          >
            <h3 class="subsection-title">合并向导</h3>
            <div class="merge-range">
              <label>
                从
                <select v-model.number="mergeStartIdx" class="vol-input" data-testid="merge-start-select">
                  <option v-for="(vol, idx) in editableVolumes" :key="`s-${idx}`" :value="idx">
                    {{ vol.label || `卷${idx + 1}` }}
                  </option>
                </select>
              </label>
              <label>
                到
                <select v-model.number="mergeEndIdx" class="vol-input" data-testid="merge-end-select">
                  <option
                    v-for="(vol, idx) in editableVolumes"
                    :key="`e-${idx}`"
                    :value="idx"
                    :disabled="idx < mergeStartIdx"
                  >
                    {{ vol.label || `卷${idx + 1}` }}
                  </option>
                </select>
              </label>
              <input
                v-model="mergeLabel"
                class="vol-input vol-conflict"
                data-testid="merge-label-input"
                placeholder="合并后卷名（可选）"
              />
            </div>
            <button
              type="button"
              class="mini-btn pixel-border"
              data-testid="apply-merge-btn"
              :disabled="mergeApplying || mergeStartIdx > mergeEndIdx"
              @click="applyVolumeMerge"
            >
              {{ mergeApplying ? '合并中…' : '应用合并' }}
            </button>
          </div>
          <p
            v-if="mergePreview"
            class="meta-line"
            data-testid="merge-preview-line"
          >
            已合并为「{{ mergePreview.merged_label }}」· {{ mergePreview.merged_range }} · 请保存卷纲
          </p>
          <div
            v-if="editableVolumes.length >= 1"
            class="volume-split-panel pixel-border"
            data-testid="volume-split-panel"
          >
            <h3 class="subsection-title">拆分向导</h3>
            <div class="merge-range">
              <label>
                卷
                <select v-model.number="splitVolumeIdx" class="vol-input" data-testid="split-volume-select">
                  <option v-for="(vol, idx) in editableVolumes" :key="`split-${idx}`" :value="idx">
                    {{ vol.label || `卷${idx + 1}` }} ({{ vol.start_chapter }}–{{ vol.end_chapter }})
                  </option>
                </select>
              </label>
              <label>
                从章
                <input
                  v-model.number="splitAtChapter"
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
              :disabled="splitApplying"
              @click="applyVolumeSplit"
            >
              {{ splitApplying ? '拆分中…' : '应用拆分' }}
            </button>
          </div>
          <p
            v-if="splitPreview"
            class="meta-line"
            data-testid="split-preview-line"
          >
            已拆为「{{ splitPreview.first_label }}」{{ splitPreview.first_range }}
            与「{{ splitPreview.second_label }}」{{ splitPreview.second_range }} · 请保存卷纲
          </p>
        </div>

        <ul
          v-if="overview.deviations.length"
          class="deviation-list"
          data-testid="deviation-list"
        >
          <li
            v-for="(d, i) in overview.deviations"
            :key="i"
            :class="`deviation-item deviation-${d.severity}`"
          >
            {{ d.message }}
          </li>
        </ul>

        <div
          v-if="showAdvanceBatch"
          class="advance-batch-panel pixel-border"
          data-testid="advance-batch-panel"
        >
          <h3 class="subsection-title">推进 batch</h3>
          <div class="batch-range">
            <label>
              起
              <input v-model.number="batchStart" type="number" min="1" class="vol-input vol-num" />
            </label>
            <label>
              止
              <input v-model.number="batchEnd" type="number" min="1" class="vol-input vol-num" />
            </label>
            <label>
              预算 $
              <input v-model.number="batchBudget" type="number" min="0" step="0.01" class="vol-input vol-num" />
            </label>
          </div>
          <div class="batch-actions">
            <button
              type="button"
              class="mini-btn pixel-border"
              data-testid="advance-preflight-btn"
              :disabled="batchRunning"
              @click="runAdvancePreflight"
            >
              Preflight
            </button>
            <button
              type="button"
              class="save-btn pixel-border"
              data-testid="advance-batch-btn"
              :disabled="batchRunning || !preflightOk"
              @click="runAdvanceBatch"
            >
              {{ batchRunning ? '运行中…' : '启动 Batch' }}
            </button>
          </div>
          <p v-if="batchCommand" class="meta-line"><code>{{ batchCommand }}</code></p>
          <p v-if="batchError" class="batch-error">{{ batchError }}</p>
          <p v-if="batchJob" class="meta-line" data-testid="batch-job-status">
            任务 {{ batchJob.job_id }} · {{ batchJob.status }}
          </p>
        </div>

        <template v-if="overview.volume_summaries.length">
          <h3 class="subsection-title">卷摘要</h3>
          <details
            v-for="vol in overview.volume_summaries"
            :key="vol.path"
            class="volume-block"
          >
            <summary>{{ vol.name }}</summary>
            <pre class="volume-excerpt">{{ vol.excerpt }}</pre>
          </details>
        </template>
      </section>

      <!-- 设定 -->
      <section class="creator-column pixel-card" data-testid="column-settings">
        <h2 class="column-title">设定</h2>
        <details class="settings-block" open>
          <summary>创作支柱</summary>
          <textarea
            v-model="pillarsText"
            class="settings-textarea"
            data-testid="pillars-textarea"
            rows="6"
          />
          <code class="path-line">{{ settingsDocs?.pillars_path || overview.pillars_path }}</code>
        </details>
        <details class="settings-block" open>
          <summary>全局大纲</summary>
          <textarea
            v-model="globalOutlineText"
            class="settings-textarea"
            data-testid="global-outline-textarea"
            rows="8"
          />
          <code class="path-line">{{ settingsDocs?.global_outline_path || overview.global_outline_path }}</code>
        </details>
        <button
          type="button"
          class="save-btn pixel-border"
          data-testid="save-settings-btn"
          :disabled="settingsSaving"
          @click="requestSaveSettings"
        >
          {{ settingsSaving ? '保存中…' : '保存设定' }}
        </button>
        <div
          v-if="showSettingsDiff && settingsDiffPreview"
          class="settings-diff-panel pixel-border"
          data-testid="settings-diff-panel"
        >
          <h3 class="subsection-title">变更预览</h3>
          <p v-if="!settingsDiffPreview.has_changes" class="meta-line">无变更</p>
          <template v-else>
            <p v-if="settingsDiffPreview.pillars.changed" class="diff-line">
              支柱：+{{ settingsDiffPreview.pillars.lines_added }}
              / -{{ settingsDiffPreview.pillars.lines_removed }} 行
            </p>
            <p v-if="settingsDiffPreview.global_outline.changed" class="diff-line">
              全局大纲：+{{ settingsDiffPreview.global_outline.lines_added }}
              / -{{ settingsDiffPreview.global_outline.lines_removed }} 行
            </p>
            <pre v-if="settingsDiffSnippet.length" class="preview-text">{{ settingsDiffSnippet.join('\n') }}</pre>
            <template v-if="settingsDiffPreview.has_history">
              <p class="diff-line" data-testid="three-way-history-label">三路对比（含历史快照）</p>
              <label v-if="settingsHistory.length" class="meta-line">
                对比快照
                <select
                  v-model="compareSnapshotId"
                  class="vol-input"
                  data-testid="compare-snapshot-select"
                  @change="refreshThreeWayPreview"
                >
                  <option v-for="snap in settingsHistory" :key="snap.id" :value="snap.id">
                    {{ snap.label }} · {{ formatHistoryTime(snap.saved_at) }}
                  </option>
                </select>
              </label>
              <p v-if="settingsDiffPreview.disk_vs_history?.pillars?.changed" class="diff-line">
                磁盘 vs 历史（支柱）：+{{ settingsDiffPreview.disk_vs_history.pillars.lines_added }}
                / -{{ settingsDiffPreview.disk_vs_history.pillars.lines_removed }}
              </p>
              <p v-if="settingsDiffPreview.editor_vs_history?.pillars?.changed" class="diff-line">
                编辑器 vs 历史（支柱）：+{{ settingsDiffPreview.editor_vs_history.pillars.lines_added }}
                / -{{ settingsDiffPreview.editor_vs_history.pillars.lines_removed }}
              </p>
            </template>
            <div
              v-if="showMergeStrategy"
              class="merge-strategy-panel"
              data-testid="merge-strategy-panel"
            >
              <p class="diff-line">合并策略（三路冲突时选择保留来源）</p>
              <p
                v-if="usesGlobalMergeDefault"
                class="meta-line"
                data-testid="merge-global-default-badge"
              >
                当前使用全局默认合并策略
              </p>
              <div class="merge-presets" data-testid="merge-presets">
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="merge-preset-disk"
                  @click="applyMergePreset('disk')"
                >
                  全选磁盘
                </button>
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="merge-preset-history"
                  @click="applyMergePreset('history')"
                >
                  全选历史
                </button>
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="merge-preset-editor"
                  @click="applyMergePreset('editor')"
                >
                  全选编辑器
                </button>
              </div>
              <label class="meta-line">
                预设包
                <select
                  v-model="selectedMergePresetPackage"
                  class="vol-input"
                  data-testid="merge-preset-package-select"
                  @change="onMergePresetPackageChange"
                >
                  <option value="">选择组合预设…</option>
                  <option
                    v-for="pkg in mergePresetPackages"
                    :key="pkg.id"
                    :value="pkg.id"
                  >
                    {{ formatMergePresetOption(pkg) }}
                  </option>
                </select>
              </label>
              <div class="merge-range">
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="export-merge-preset-packages-btn"
                  @click="exportMergePresetPackages"
                >
                  分享预设包
                </button>
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="toggle-import-merge-preset-packages-btn"
                  @click="showImportMergePresetPackages = !showImportMergePresetPackages"
                >
                  {{ showImportMergePresetPackages ? '收起导入' : '导入预设包' }}
                </button>
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="publish-merge-preset-factory-btn"
                  :disabled="mergePresetFactoryPublishing || !selectedProjectMergePreset"
                  @click="publishMergePresetToFactory"
                >
                  {{ mergePresetFactoryPublishing ? '发布中…' : '发布到工厂库' }}
                </button>
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="pull-merge-preset-factory-btn"
                  :disabled="mergePresetFactoryPulling || !factoryMergePresetCount"
                  @click="pullFactoryMergePresets"
                >
                  {{ mergePresetFactoryPulling ? '拉取中…' : '从工厂库拉取' }}
                </button>
              </div>
              <div
                v-if="mergePresetToposort.edges?.length"
                class="merge-preset-toposort"
                data-testid="merge-preset-toposort-panel"
              >
                <p class="meta-line">拓扑序（{{ mergePresetToposort.order?.join(' → ') }}）</p>
                <ul>
                  <li
                    v-for="edge in mergePresetToposort.edges"
                    :key="`${edge.from}-${edge.to}`"
                    data-testid="merge-preset-toposort-edge"
                  >
                    {{ edge.from }} → {{ edge.to }}
                  </li>
                </ul>
              </div>
              <div
                v-if="mergePresetChangelog.entries?.length"
                class="merge-preset-changelog"
                data-testid="merge-preset-changelog-panel"
              >
                <p class="meta-line">预设变更（{{ mergePresetChangelog.entry_count }}）</p>
                <ul>
                  <li
                    v-for="(entry, idx) in mergePresetChangelog.entries"
                    :key="idx"
                    data-testid="merge-preset-changelog-row"
                  >
                    {{ entry.action }} · {{ entry.changed_fields?.join(', ') }}
                  </li>
                </ul>
              </div>
              <div
                v-if="mergePresetGraph.edges?.length"
                class="merge-preset-graph"
                data-testid="merge-preset-graph-panel"
              >
                <p class="meta-line">预设包依赖图（{{ mergePresetGraph.edge_count }} 条边）</p>
                <ul>
                  <li
                    v-for="edge in mergePresetGraph.edges"
                    :key="`${edge.from_pkg}-${edge.to}`"
                    data-testid="merge-preset-graph-edge"
                  >
                    {{ edge.from_pkg }} → {{ edge.to }}
                  </li>
                </ul>
              </div>
              <div
                v-if="mergePresetConflicts.conflicts?.length"
                class="merge-preset-conflicts"
                data-testid="merge-preset-conflicts-panel"
              >
                <p class="meta-line">预设包冲突（{{ mergePresetConflicts.conflict_count }}）</p>
                <ul>
                  <li
                    v-for="(conflict, idx) in mergePresetConflicts.conflicts"
                    :key="`${conflict.type}-${idx}`"
                    data-testid="merge-preset-conflict-row"
                  >
                    {{ conflict.message }}
                  </li>
                </ul>
              </div>
              <div
                v-if="mergePresetConflictFixes.fixes?.length"
                class="merge-preset-conflict-fixes"
                data-testid="merge-preset-conflict-fixes-panel"
              >
                <p class="meta-line">修复建议（{{ mergePresetConflictFixes.fix_count }}）</p>
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="apply-all-merge-preset-fixes-btn"
                  @click="applyAllMergePresetConflictFixes"
                >
                  批量应用可修复项
                </button>
                <ul>
                  <li
                    v-for="fix in mergePresetConflictFixes.fixes"
                    :key="fix.id"
                    class="merge-preset-fix-row"
                    data-testid="merge-preset-conflict-fix-row"
                  >
                    <span>{{ fix.label }}</span>
                    <button
                      v-if="fix.applicable"
                      type="button"
                      class="mini-btn pixel-border"
                      data-testid="apply-merge-preset-fix-btn"
                      @click="applyMergePresetConflictFix(fix)"
                    >
                      应用
                    </button>
                  </li>
                </ul>
              </div>
              <div
                v-if="showImportMergePresetPackages"
                class="import-templates-panel"
                data-testid="import-merge-preset-packages-panel"
              >
                <textarea
                  v-model="importMergePresetPackagesJson"
                  class="vol-input import-templates-json"
                  data-testid="import-merge-preset-packages-json"
                  placeholder='{"packages":[...]}'
                  rows="3"
                />
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="preview-merge-preset-import-diff-btn"
                  :disabled="mergePresetPackagesImporting || !importMergePresetPackagesJson.trim()"
                  @click="previewMergePresetImportDiff"
                >
                  预览 diff
                </button>
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="toposort-merge-preset-btn"
                  @click="applyMergePresetToposort"
                >
                  拓扑重排
                </button>
                <p
                  v-if="mergePresetImportDiff.added?.length || mergePresetImportDiff.updated?.length"
                  class="meta-line"
                  data-testid="merge-preset-import-diff-panel"
                >
                  diff：新增 {{ mergePresetImportDiff.added?.length || 0 }} /
                  更新 {{ mergePresetImportDiff.updated?.length || 0 }}
                </p>
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="preflight-merge-preset-import-btn"
                  :disabled="mergePresetPackagesImporting || !importMergePresetPackagesJson.trim()"
                  @click="preflightMergePresetImport"
                >
                  预检冲突
                </button>
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="import-merge-preset-packages-btn"
                  :disabled="mergePresetPackagesImporting || !importMergePresetPackagesJson.trim()"
                  @click="importMergePresetPackagesFromJson"
                >
                  {{ mergePresetPackagesImporting ? '导入中…' : '确认导入' }}
                </button>
              </div>
              <label class="meta-line">
                支柱
                <select v-model="pillarsMergeSource" class="vol-input" data-testid="pillars-merge-source" @change="refreshMergeStrategyPreview">
                  <option value="editor">编辑器</option>
                  <option value="disk">磁盘</option>
                  <option value="history">历史快照</option>
                </select>
              </label>
              <label v-if="pillarsMergeSource === 'history' && settingsHistory.length" class="meta-line">
                支柱历史快照
                <select
                  v-model="pillarsSnapshotId"
                  class="vol-input"
                  data-testid="pillars-snapshot-select"
                  @change="refreshMergeStrategyPreview"
                >
                  <option v-for="snap in settingsHistory" :key="`p-${snap.id}`" :value="snap.id">
                    {{ snap.label }} · {{ formatHistoryTime(snap.saved_at) }}
                  </option>
                </select>
              </label>
              <label class="meta-line">
                全局大纲
                <select
                  v-model="outlineMergeSource"
                  class="vol-input"
                  data-testid="outline-merge-source"
                  @change="refreshMergeStrategyPreview"
                >
                  <option value="editor">编辑器</option>
                  <option value="disk">磁盘</option>
                  <option value="history">历史快照</option>
                </select>
              </label>
              <label v-if="outlineMergeSource === 'history' && settingsHistory.length" class="meta-line">
                大纲历史快照
                <select
                  v-model="outlineSnapshotId"
                  class="vol-input"
                  data-testid="outline-snapshot-select"
                  @change="refreshMergeStrategyPreview"
                >
                  <option v-for="snap in settingsHistory" :key="`o-${snap.id}`" :value="snap.id">
                    {{ snap.label }} · {{ formatHistoryTime(snap.saved_at) }}
                  </option>
                </select>
              </label>
              <div v-if="mergeStrategyPreview" class="merge-preview-visual" data-testid="merge-preview-visual">
                <p v-if="mergeStrategyPreview.pillars.vs_disk.changed" class="diff-line">
                  支柱将写入 vs 磁盘：+{{ mergeStrategyPreview.pillars.vs_disk.lines_added }}
                  / -{{ mergeStrategyPreview.pillars.vs_disk.lines_removed }}
                </p>
                <pre
                  v-if="mergeStrategySnippet.length"
                  class="preview-text"
                  data-testid="merge-strategy-snippet"
                >{{ mergeStrategySnippet.join('\n') }}</pre>
              </div>
              <div class="merge-range">
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="export-merge-prefs-btn"
                  @click="exportMergePreferences"
                >
                  导出合并策略
                </button>
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="toggle-import-merge-prefs-btn"
                  @click="showImportMergePrefs = !showImportMergePrefs"
                >
                  {{ showImportMergePrefs ? '收起导入' : '导入合并策略' }}
                </button>
              </div>
              <div v-if="showImportMergePrefs" class="import-templates-panel" data-testid="import-merge-prefs-panel">
                <textarea
                  v-model="importMergePrefsJson"
                  class="vol-input import-templates-json"
                  data-testid="import-merge-prefs-json"
                  placeholder='{"project":{...},"global":{...}}'
                  rows="4"
                />
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="import-merge-prefs-btn"
                  :disabled="mergePrefsImporting || !importMergePrefsJson.trim()"
                  @click="importMergePreferencesFromJson"
                >
                  {{ mergePrefsImporting ? '导入中…' : '确认导入' }}
                </button>
              </div>
            </div>
          </template>
          <div class="batch-actions">
            <button
              type="button"
              class="save-btn pixel-border"
              data-testid="confirm-settings-btn"
              :disabled="settingsSaving || !settingsDiffPreview.has_changes"
              @click="confirmSaveSettings"
            >
              确认保存
            </button>
            <button
              type="button"
              class="mini-btn pixel-border"
              data-testid="cancel-settings-btn"
              @click="cancelSettingsDiff"
            >
              取消
            </button>
          </div>
        </div>
        <details v-if="settingsHistory.length" class="settings-block" data-testid="settings-history-panel">
          <summary>版本历史（{{ settingsHistory.length }}）</summary>
          <ul class="history-list">
            <li
              v-for="snap in settingsHistory"
              :key="snap.id"
              class="history-row pixel-border"
              :data-testid="`history-row-${snap.id}`"
            >
              <span class="history-meta">{{ snap.label }} · {{ formatHistoryTime(snap.saved_at) }}</span>
              <span class="history-excerpt">{{ snap.pillars_excerpt || '（空支柱）' }}</span>
              <button
                type="button"
                class="mini-btn pixel-border"
                :data-testid="`restore-history-${snap.id}`"
                :disabled="settingsRestoring"
                @click="restoreSettingsHistory(snap.id)"
              >
                恢复
              </button>
            </li>
          </ul>
        </details>
        <details v-if="overview.quality_report_available" class="settings-block">
          <summary>P0 问题（点开才看）</summary>
          <p class="p0-line" :class="overview.p0_count ? 'warn' : 'ok'">
            {{ overview.p0_count ? `发现 ${overview.p0_count} 条 P0` : '无 P0' }}
          </p>
        </details>
        <div class="cmd-block">
          <p class="subsection-title">守门命令</p>
          <code>{{ overview.companion_check_cmd }}</code>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import {
  fetchCreatorOverview,
  fetchCreatorVolumePlan,
  fetchCreatorChapterPreview,
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
  fetchCreatorOnboardingDigestDeadLetter,
  preflightCreatorFactoryMergePresetPull,
  fetchCreatorMergePresetChangelog,
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

const { projectRevision } = useStudioProject();
const { focusWizard, focusWizardStep, focusWizardDone, focusWizardNotes, setWizardDeepLink, buildWizardShareUrl } = useDashboardNav();
const wizardPanelRef = ref(null);
const overview = ref(null);
const editableVolumes = ref([]);
const selectedChapter = ref(null);
const chapterPreview = ref(null);
const previewLoading = ref(false);
const loading = ref(false);
const saving = ref(false);
const settingsSaving = ref(false);
const settingsDocs = ref(null);
const pillarsText = ref('');
const globalOutlineText = ref('');
const settingsBaseline = ref({ pillars: '', outline: '' });
const settingsDiffPreview = ref(null);
const showSettingsDiff = ref(false);
const dragVolumeIndex = ref(null);
const volumePlanRevision = ref('');
const settingsRevisions = ref({ pillars: '', outline: '' });
const conflictMessage = ref('');
const mergeStartIdx = ref(0);
const mergeEndIdx = ref(1);
const mergeLabel = ref('');
const mergePreview = ref(null);
const mergeApplying = ref(false);
const splitVolumeIdx = ref(0);
const splitAtChapter = ref(2);
const splitPreview = ref(null);
const splitApplying = ref(false);
const settingsHistory = ref([]);
const settingsRestoring = ref(false);
const volumeTemplates = ref([]);
const selectedTemplateId = ref('three_act');
const templateApplying = ref(false);
const customTemplateName = ref('');
const templateSaving = ref(false);
const templateDeleting = ref(false);
const templateRenaming = ref(false);
const renameTemplateName = ref('');
const showImportTemplates = ref(false);
const importTemplatesJson = ref('');
const templateImporting = ref(false);
const templateSyncSources = ref([]);
const templateSyncing = ref(false);
const templatePublishing = ref(false);
const factoryPulling = ref(false);
const factoryDeleting = ref(false);
const wizardShareMessage = ref('');
const wizardStepNotes = ref({});
const usesGlobalMergeDefault = ref(false);
const templateVersionLabel = ref('');
const templateVersionSaving = ref(false);
const templateVersionChangelog = ref([]);
const versionSemverPattern = /^v?\d+\.\d+(?:\.\d+)?(?:-[a-zA-Z0-9][a-zA-Z0-9.-]*)?$/i;
const mergePresetPackages = ref([]);
const selectedMergePresetPackage = ref('');
const wizardNotifications = ref([]);
const wizardUnreadMentions = ref(0);
const wizardNotificationHandleFilter = ref('');
const wizardNotificationHandles = ref([]);
const showImportMergePresetPackages = ref(false);
const importMergePresetPackagesJson = ref('');
const mergePresetPackagesImporting = ref(false);
const expandedChangelogVisual = ref(null);
const wizardWebhookUrl = ref('');
const wizardWebhookEnabled = ref(false);
const wizardEmailTo = ref('');
const wizardEmailSmtpHost = ref('');
const wizardEmailEnabled = ref(false);
const wizardNotificationDigest = ref({ unread: 0, group_count: 0, groups: [] });
const wizardDigestScheduleEnabled = ref(false);
const wizardDigestScheduleHours = ref(24);
const wizardDigestQuietStart = ref(null);
const wizardDigestQuietEnd = ref(null);
const wizardDigestHandleChannelsJson = ref('');
const wizardDigestHandleQuietJson = ref('');
const wizardDigestStats = ref({ sent_total: 0, failed_total: 0 });
const wizardDigestDeadLetter = ref({ item_count: 0, items: [] });
const wizardDigestRetryQueue = ref({ item_count: 0, items: [] });
const wizardWebhookSigningSecret = ref('');
const templateApprovals = ref([]);
const templateApprovalHistory = ref([]);
const overdueTemplateApprovals = ref([]);
const templateApprovalChainSteps = ref(2);
const templateApprovalStepAssignees = ref('');
const templateApprovalOrGroups = ref('');
const templateApprovalSnapshotDiff = ref(null);
const templateApprovalSlaHours = ref(72);
const templateApprovalEmailOnSubmit = ref(true);
const templateApprovalEmailOnReject = ref(true);
const templateApprovalEmailOnOverdue = ref(true);
const mergePresetImportDiff = ref({ added: [], updated: [], removed: [] });
const mergePresetToposort = ref({ order: [], edges: [], edge_count: 0 });
const mergePresetChangelog = ref({ package_id: '', entry_count: 0, entries: [] });
const mergePresetImportPreflight = ref(null);
const templateApprovalSubmitting = ref(false);
const mergePresetGraph = ref({ node_count: 0, edge_count: 0, nodes: [], edges: [] });
const mergePresetConflicts = ref({ conflict_count: 0, conflicts: [] });
const mergePresetConflictFixes = ref({ fix_count: 0, fixes: [] });
const templateRollbackSaving = ref(false);
const mergePresetFactoryPublishing = ref(false);
const mergePresetFactoryPulling = ref(false);
const factoryMergePresetPackages = ref([]);
const showImportMergePrefs = ref(false);
const importMergePrefsJson = ref('');
const mergePrefsImporting = ref(false);
const pillarsSnapshotId = ref('');
const outlineSnapshotId = ref('');
const onboardingWizard = ref(null);
const completedWizardSteps = ref(new Set());
const autoCompletedWizardSteps = ref(new Set());
const compareSnapshotId = ref('');
const pillarsMergeSource = ref('editor');
const outlineMergeSource = ref('editor');
const mergeStrategyPreview = ref(null);
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

let batchPollTimer = null;
const lastBatchStatus = ref(null);

const modeLabel = computed(() => {
  if (!overview.value) return '';
  const map = { companion: '陪伴', advance: '推进', studio: '工作室' };
  return map[overview.value.creation_mode] || overview.value.creation_mode;
});

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

const settingsDiffSnippet = computed(() => {
  const preview = settingsDiffPreview.value;
  if (!preview) return [];
  return [
    ...(preview.pillars?.snippet || []),
    ...(preview.global_outline?.snippet || []),
  ].slice(0, 10);
});

const selectedTemplateHint = computed(() => {
  const row = volumeTemplates.value.find((t) => t.id === selectedTemplateId.value);
  return row?.description || '';
});

const selectedTemplateProject = computed(() => {
  const row = volumeTemplates.value.find((t) => t.id === selectedTemplateId.value);
  return row?.scope === 'project';
});

const selectedTemplateFactory = computed(() => {
  const row = volumeTemplates.value.find((t) => t.id === selectedTemplateId.value);
  return row?.scope === 'factory';
});

const factoryTemplateCount = computed(() => volumeTemplates.value.filter((t) => t.scope === 'factory').length);

const factoryMergePresetCount = computed(
  () => mergePresetPackages.value.filter((pkg) => pkg.scope === 'factory').length,
);

const pendingTemplateApprovals = computed(() =>
  templateApprovals.value.filter((row) => row.status === 'pending'),
);

const selectedProjectMergePreset = computed(() => {
  const pkg = mergePresetPackages.value.find((row) => row.id === selectedMergePresetPackage.value);
  return pkg?.scope === 'project' && !pkg?.builtin;
});

function toggleChangelogVisual(index) {
  expandedChangelogVisual.value = expandedChangelogVisual.value === index ? null : index;
}

watch(selectedMergePresetPackage, (packageId) => {
  if (packageId) applyMergePresetPackage(packageId);
});

const selectedTemplateCustom = computed(() => selectedTemplateProject.value);

watch(selectedTemplateId, () => {
  const row = volumeTemplates.value.find((t) => t.id === selectedTemplateId.value);
  renameTemplateName.value = row?.name || '';
  templateVersionLabel.value = row?.version_label || '';
  templateVersionChangelog.value = row?.version_changelog || [];
  loadTemplateVersionChangelog();
});

function formatTemplateOption(template) {
  if (template.version_label) {
    const prefix = template.version_semver_valid === false ? '!' : '';
    return `${prefix}[${template.version_label}] ${template.name}`;
  }
  return template.name;
}

function formatMergePresetOption(pkg) {
  if (pkg.version_label) {
    const prefix = pkg.version_semver_valid === false ? '!' : '';
    return `${prefix}[${pkg.version_label}] ${pkg.name}`;
  }
  return pkg.name;
}

function isSemverVersionLabel(label) {
  return versionSemverPattern.test(String(label || '').trim());
}

function extractMentionsFromText(text) {
  const re = /@([a-zA-Z][a-zA-Z0-9_-]{0,31})/g;
  const found = [];
  let match = re.exec(String(text || ''));
  while (match) {
    const handle = match[1].toLowerCase();
    if (!found.includes(handle)) found.push(handle);
    match = re.exec(String(text || ''));
  }
  return found;
}

function wizardMentionsForStep(stepId) {
  const fromApi = onboardingWizard.value?.step_mentions?.[stepId];
  if (fromApi?.length) return fromApi;
  return extractMentionsFromText(wizardStepNotes.value[stepId] || '');
}

const showMergeStrategy = computed(() => {
  const preview = settingsDiffPreview.value;
  if (!preview?.has_history) return false;
  const diskHist = preview.disk_vs_history;
  const editorHist = preview.editor_vs_history;
  return Boolean(
    diskHist?.pillars?.changed
    || diskHist?.global_outline?.changed
    || editorHist?.pillars?.changed
    || editorHist?.global_outline?.changed,
  );
});

const mergeStrategySnippet = computed(() => {
  const preview = mergeStrategyPreview.value;
  if (!preview) return [];
  return [
    ...(preview.pillars?.vs_disk?.snippet || []),
    ...(preview.global_outline?.vs_disk?.snippet || []),
  ].slice(0, 12);
});

function formatHistoryTime(iso) {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleString('zh-CN', { hour12: false });
  } catch {
    return iso;
  }
}

function syncSplitChapterFromVolume() {
  const vol = editableVolumes.value[splitVolumeIdx.value];
  if (!vol) return;
  const mid = vol.start_chapter + Math.floor((vol.end_chapter - vol.start_chapter) / 2);
  splitAtChapter.value = Math.min(vol.end_chapter, Math.max(vol.start_chapter + 1, mid));
}

function syncBatchRangeFromVolumes() {
  const locked = editableVolumes.value.filter((v) => v.locked);
  if (!locked.length) return;
  const vol = locked[0];
  batchStart.value = vol.start_chapter;
  batchEnd.value = Math.min(vol.end_chapter, overview.value?.max_chapter || vol.end_chapter);
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
  try {
    chapterPreview.value = await fetchCreatorChapterPreview(chapter);
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    previewLoading.value = false;
  }
}

function addVolume() {
  const nextStart = editableVolumes.value.length
    ? editableVolumes.value[editableVolumes.value.length - 1].end_chapter + 1
    : 1;
  editableVolumes.value.push({
    label: `卷${editableVolumes.value.length + 1}`,
    start_chapter: nextStart,
    end_chapter: Math.min(nextStart + 9, overview.value?.max_chapter || nextStart + 9),
    core_conflict: '',
    locked: false,
  });
}

function toggleLock(idx) {
  editableVolumes.value[idx].locked = !editableVolumes.value[idx].locked;
}

function moveVolume(from, to) {
  if (from === to || to < 0 || to >= editableVolumes.value.length) return;
  const items = [...editableVolumes.value];
  const [item] = items.splice(from, 1);
  items.splice(to, 0, item);
  editableVolumes.value = items;
}

function onVolumeDragStart(idx, event) {
  dragVolumeIndex.value = idx;
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/plain', String(idx));
  }
}

function onVolumeDrop(idx) {
  if (dragVolumeIndex.value === null || dragVolumeIndex.value === idx) {
    dragVolumeIndex.value = null;
    return;
  }
  moveVolume(dragVolumeIndex.value, idx);
  dragVolumeIndex.value = null;
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

async function loadVolumePlan() {
  const plan = await fetchCreatorVolumePlan();
  editableVolumes.value = (plan.volumes || []).map((v) => ({ ...v }));
  volumePlanRevision.value = plan.revision || '';
  mergeStartIdx.value = 0;
  mergeEndIdx.value = Math.min(1, Math.max(0, editableVolumes.value.length - 1));
  mergePreview.value = null;
  splitVolumeIdx.value = 0;
  splitPreview.value = null;
  syncSplitChapterFromVolume();
  syncBatchRangeFromVolumes();
}

async function loadOnboardingWizard() {
  try {
    onboardingWizard.value = await fetchCreatorOnboarding();
    completedWizardSteps.value = new Set(onboardingWizard.value?.completed_step_ids || []);
    autoCompletedWizardSteps.value = new Set(onboardingWizard.value?.auto_completed_step_ids || []);
    wizardStepNotes.value = { ...(onboardingWizard.value?.step_notes || {}) };
    wizardUnreadMentions.value = onboardingWizard.value?.unread_mention_count || 0;
    await loadWizardNotifications();
    if (focusWizard.value) {
      await nextTick();
      try {
        wizardPanelRef.value?.scrollIntoView?.({ behavior: 'smooth', block: 'start' });
      } catch {
        /* jsdom */
      }
    }
    await focusWizardStepFromUrl();
    await applyWizardShareFromUrl();
  } catch {
    onboardingWizard.value = null;
  }
}

function onWizardToggle(event) {
  setWizardDeepLink(
    event.target.open,
    event.target.open ? focusWizardStep.value : null,
    event.target.open ? [...completedWizardSteps.value] : [],
    event.target.open ? { ...wizardStepNotes.value } : {},
  );
}

async function applyWizardShareFromUrl() {
  const done = focusWizardDone.value;
  const notes = focusWizardNotes.value;
  if (!done?.length && (!notes || !Object.keys(notes).length)) return;
  try {
    await applyCreatorOnboardingShare({
      completed_step_ids: done || [],
      step_notes: notes || {},
    });
    onboardingWizard.value = await fetchCreatorOnboarding();
    completedWizardSteps.value = new Set(onboardingWizard.value?.completed_step_ids || []);
    autoCompletedWizardSteps.value = new Set(onboardingWizard.value?.auto_completed_step_ids || []);
    wizardStepNotes.value = { ...(onboardingWizard.value?.step_notes || {}) };
  } catch {
    /* ignore share apply errors */
  }
}

async function saveWizardStepNote(stepId) {
  try {
    await saveCreatorOnboardingNotes({
      step_notes: { [stepId]: wizardStepNotes.value[stepId] || '' },
    });
    await loadWizardNotifications();
  } catch {
    /* ignore note save errors */
  }
}

async function copyWizardShareLink() {
  const url = buildWizardShareUrl(
    [...completedWizardSteps.value],
    focusWizardStep.value,
    wizardStepNotes.value,
  );
  try {
    await navigator.clipboard.writeText(url);
    wizardShareMessage.value = '已复制分享链接';
  } catch {
    wizardShareMessage.value = url;
  }
  setTimeout(() => {
    wizardShareMessage.value = '';
  }, 3000);
}

async function focusWizardStepFromUrl() {
  if (!focusWizardStep.value || !onboardingWizard.value) return;
  const exists = onboardingWizard.value.steps.some((s) => s.id === focusWizardStep.value);
  if (!exists) return;
  await nextTick();
  const el = document.querySelector(`[data-testid="wizard-step-${focusWizardStep.value}"]`);
  try {
    el?.closest('.wizard-step')?.scrollIntoView?.({ behavior: 'smooth', block: 'center' });
  } catch {
    /* jsdom */
  }
}

async function toggleWizardStep(stepId, checked) {
  const next = new Set(completedWizardSteps.value);
  if (checked) {
    next.add(stepId);
  } else {
    next.delete(stepId);
  }
  try {
    const result = await saveCreatorOnboardingProgress({
      completed_step_ids: [...next],
    });
    completedWizardSteps.value = new Set(result.completed_step_ids || []);
    autoCompletedWizardSteps.value = new Set(result.auto_completed_step_ids || []);
    if (onboardingWizard.value) {
      onboardingWizard.value = {
        ...onboardingWizard.value,
        completed_step_ids: result.completed_step_ids,
        auto_completed_step_ids: result.auto_completed_step_ids,
        progress_pct: result.progress_pct,
      };
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
}

function applyMergePreset(source) {
  pillarsMergeSource.value = source;
  outlineMergeSource.value = source;
  selectedMergePresetPackage.value = '';
  if (source === 'history' && settingsHistory.value.length) {
    const snapId = compareSnapshotId.value || settingsHistory.value[0].id;
    pillarsSnapshotId.value = snapId;
    outlineSnapshotId.value = snapId;
  }
  refreshMergeStrategyPreview();
}

function applyMergePresetPackage(packageId) {
  const pkg = mergePresetPackages.value.find((row) => row.id === packageId);
  if (!pkg) return;
  pillarsMergeSource.value = pkg.pillars_merge_source;
  outlineMergeSource.value = pkg.global_outline_merge_source;
  if (pkg.pillars_merge_source === 'history' && settingsHistory.value.length) {
    pillarsSnapshotId.value = compareSnapshotId.value || settingsHistory.value[0].id;
  }
  if (pkg.global_outline_merge_source === 'history' && settingsHistory.value.length) {
    outlineSnapshotId.value = compareSnapshotId.value || settingsHistory.value[0].id;
  }
  refreshMergeStrategyPreview();
}

function onMergePresetPackageChange() {
  const packageId = selectedMergePresetPackage.value;
  if (packageId) applyMergePresetPackage(packageId);
}

async function loadTemplateVersionChangelog() {
  if (!selectedTemplateProject.value && !selectedTemplateFactory.value) {
    templateVersionChangelog.value = [];
    return;
  }
  try {
    const data = await fetchCreatorVolumeTemplateChangelog(selectedTemplateId.value);
    templateVersionChangelog.value = data.entries || [];
  } catch {
    const row = volumeTemplates.value.find((t) => t.id === selectedTemplateId.value);
    templateVersionChangelog.value = row?.version_changelog || [];
  }
}

async function loadWizardNotifications() {
  try {
    const handle = wizardNotificationHandleFilter.value || undefined;
    const data = await fetchCreatorOnboardingNotifications(handle);
    wizardNotifications.value = data.notifications || [];
    wizardNotificationHandles.value = data.handles || [];
    wizardUnreadMentions.value = data.unread ?? wizardNotifications.value.filter((n) => !n.read).length;
    const digest = await fetchCreatorOnboardingNotificationDigest(handle);
    wizardNotificationDigest.value = digest;
    await loadWizardDigestSchedule();
    await loadWizardWebhook();
    await loadWizardEmail();
  } catch {
    wizardNotifications.value = [];
    wizardNotificationHandles.value = [];
    wizardUnreadMentions.value = onboardingWizard.value?.unread_mention_count || 0;
    wizardNotificationDigest.value = { unread: 0, group_count: 0, groups: [] };
    wizardDigestScheduleEnabled.value = false;
    wizardDigestScheduleHours.value = 24;
  }
}

async function loadWizardDigestSchedule() {
  try {
    const data = await fetchCreatorOnboardingDigestSchedule();
    wizardDigestScheduleEnabled.value = Boolean(data.enabled);
    wizardDigestScheduleHours.value = data.interval_hours || 24;
    wizardDigestQuietStart.value = data.quiet_hours_start ?? null;
    wizardDigestQuietEnd.value = data.quiet_hours_end ?? null;
    wizardDigestHandleChannelsJson.value = JSON.stringify(data.handle_channels || {});
    wizardDigestHandleQuietJson.value = JSON.stringify(data.handle_quiet_hours || {});
    const stats = await fetchCreatorOnboardingDigestStats();
    wizardDigestStats.value = stats;
    const retry = await fetchCreatorOnboardingDigestRetryQueue();
    wizardDigestRetryQueue.value = retry;
    const deadLetter = await fetchCreatorOnboardingDigestDeadLetter();
    wizardDigestDeadLetter.value = deadLetter;
  } catch {
    wizardDigestScheduleEnabled.value = false;
    wizardDigestScheduleHours.value = 24;
    wizardDigestQuietStart.value = null;
    wizardDigestQuietEnd.value = null;
    wizardDigestRetryQueue.value = { item_count: 0, items: [] };
  }
}

async function saveWizardDigestSchedule() {
  try {
    let handleChannels = {};
    let handleQuietHours = {};
    if (wizardDigestHandleChannelsJson.value.trim()) {
      handleChannels = JSON.parse(wizardDigestHandleChannelsJson.value);
    }
    if (wizardDigestHandleQuietJson.value.trim()) {
      handleQuietHours = JSON.parse(wizardDigestHandleQuietJson.value);
    }
    await saveCreatorOnboardingDigestSchedule({
      enabled: wizardDigestScheduleEnabled.value,
      interval_hours: wizardDigestScheduleHours.value,
      channels: ['webhook', 'email'],
      handle_channels: handleChannels,
      handle_quiet_hours: handleQuietHours,
      quiet_hours_start: wizardDigestQuietStart.value,
      quiet_hours_end: wizardDigestQuietEnd.value,
    });
    saveMessage.value = '已保存 digest 定时';
    await loadWizardDigestSchedule();
  } catch (e) {
    handleSaveError(e);
  }
}

async function processWizardDigestRetries() {
  try {
    const result = await processCreatorOnboardingDigestRetries();
    saveMessage.value = `已重试 ${result.retried} 条，剩余 ${result.remaining}`;
    await loadWizardDigestSchedule();
  } catch (e) {
    handleSaveError(e);
  }
}

async function dispatchWizardDigest() {
  try {
    const result = await dispatchCreatorOnboardingDigest(true);
    saveMessage.value = result.sent ? '已发送 digest' : `跳过：${result.reason || '未知'}`;
  } catch (e) {
    handleSaveError(e);
  }
}

async function loadWizardWebhook() {
  try {
    const data = await fetchCreatorOnboardingWebhook();
    wizardWebhookUrl.value = data.url || '';
    wizardWebhookEnabled.value = Boolean(data.enabled);
    wizardWebhookSigningSecret.value = data.signing_secret || '';
  } catch {
    wizardWebhookUrl.value = '';
    wizardWebhookEnabled.value = false;
  }
}

async function saveWizardWebhook() {
  try {
    await saveCreatorOnboardingWebhook({
      url: wizardWebhookUrl.value.trim(),
      enabled: wizardWebhookEnabled.value,
      mention_handles: wizardNotificationHandles.value,
      signing_secret: wizardWebhookSigningSecret.value.trim(),
    });
    saveMessage.value = '已保存通知 Webhook';
  } catch (e) {
    handleSaveError(e);
  }
}

async function loadWizardEmail() {
  try {
    const data = await fetchCreatorOnboardingEmail();
    wizardEmailTo.value = (data.to_addresses || []).join(', ');
    wizardEmailSmtpHost.value = data.smtp_host || '';
    wizardEmailEnabled.value = Boolean(data.enabled);
  } catch {
    wizardEmailTo.value = '';
    wizardEmailSmtpHost.value = '';
    wizardEmailEnabled.value = false;
  }
}

async function saveWizardEmail() {
  try {
    const toAddresses = wizardEmailTo.value
      .split(',')
      .map((addr) => addr.trim())
      .filter(Boolean);
    await saveCreatorOnboardingEmail({
      enabled: wizardEmailEnabled.value,
      to_addresses: toAddresses,
      mention_handles: wizardNotificationHandles.value,
      smtp_host: wizardEmailSmtpHost.value.trim(),
      smtp_port: 587,
      smtp_use_tls: true,
      from_address: toAddresses[0] || '',
    });
    saveMessage.value = '已保存通知邮件';
  } catch (e) {
    handleSaveError(e);
  }
}

async function rollbackTemplateVersion(entry, changelogIndex) {
  if (!selectedTemplateId.value) return;
  templateRollbackSaving.value = true;
  error.value = null;
  try {
    await rollbackCreatorVolumeTemplate(selectedTemplateId.value, {
      version_label: entry.version_label || undefined,
      changelog_index: changelogIndex,
    });
    saveMessage.value = `已回滚到 ${entry.version_label || '选定版本'}`;
    await loadVolumeTemplates();
    await loadTemplateVersionChangelog();
  } catch (e) {
    handleSaveError(e);
  } finally {
    templateRollbackSaving.value = false;
  }
}

async function ackWizardNotifications() {
  try {
    const result = await ackCreatorOnboardingNotifications({
      all_notifications: true,
      handle: wizardNotificationHandleFilter.value || undefined,
    });
    wizardUnreadMentions.value = result.unread ?? 0;
    await loadWizardNotifications();
    saveMessage.value = `已标记 ${result.acked} 条通知为已读`;
  } catch (e) {
    handleSaveError(e);
  }
}

async function exportMergePresetPackages() {
  error.value = null;
  try {
    const data = await exportCreatorMergePresetPackages();
    const text = JSON.stringify(data, null, 2);
    importMergePresetPackagesJson.value = text;
    if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      saveMessage.value = '已导出预设包并复制到剪贴板';
    } else {
      saveMessage.value = '已导出预设包（见导入框）';
      showImportMergePresetPackages.value = true;
    }
  } catch (e) {
    handleSaveError(e);
  }
}

async function importMergePresetPackagesFromJson() {
  mergePresetPackagesImporting.value = true;
  error.value = null;
  try {
    const payload = JSON.parse(importMergePresetPackagesJson.value);
    if (mergePresetImportPreflight.value?.blocked) {
      saveMessage.value = '预检仍有冲突，请先修复或调整 JSON';
      return;
    }
    await importCreatorMergePresetPackages(payload);
    importMergePresetPackagesJson.value = '';
    showImportMergePresetPackages.value = false;
    mergePresetImportPreflight.value = null;
    await loadMergePresetPackages();
    saveMessage.value = '已导入合并策略预设包';
  } catch (e) {
    handleSaveError(e);
  } finally {
    mergePresetPackagesImporting.value = false;
  }
}

async function loadMergePresetPackages() {
  try {
    const data = await fetchCreatorMergePresetPackages();
    mergePresetPackages.value = data.packages || [];
    const factoryData = await fetchCreatorFactoryMergePresetPackages();
    factoryMergePresetPackages.value = factoryData.packages || [];
    const graph = await fetchCreatorMergePresetGraph();
    mergePresetGraph.value = graph;
    const conflicts = await fetchCreatorMergePresetConflicts();
    mergePresetConflicts.value = conflicts;
    const fixes = await fetchCreatorMergePresetConflictFixes();
    mergePresetConflictFixes.value = fixes;
    const topo = await fetchCreatorMergePresetToposort();
    mergePresetToposort.value = topo;
    if (selectedMergePresetPackage.value) {
      const changelog = await fetchCreatorMergePresetChangelog(selectedMergePresetPackage.value);
      mergePresetChangelog.value = changelog;
    } else {
      mergePresetChangelog.value = { package_id: '', entry_count: 0, entries: [] };
    }
  } catch {
    mergePresetPackages.value = [];
    factoryMergePresetPackages.value = [];
    mergePresetGraph.value = { node_count: 0, edge_count: 0, nodes: [], edges: [] };
    mergePresetConflicts.value = { conflict_count: 0, conflicts: [] };
    mergePresetConflictFixes.value = { fix_count: 0, fixes: [] };
  }
}

async function loadTemplateApprovalChainConfig() {
  try {
    const data = await fetchCreatorTemplateApprovalChainConfig();
    templateApprovalChainSteps.value = data.required_steps || 2;
    templateApprovalStepAssignees.value = (data.step_assignees || []).join(', ');
    if (data.step_assignee_groups?.length) {
      templateApprovalOrGroups.value = data.step_assignee_groups
        .map((group) => group.join('|'))
        .join(',');
    }
    const sla = await fetchCreatorTemplateApprovalSlaConfig();
    templateApprovalSlaHours.value = sla.timeout_hours || 72;
    templateApprovalEmailOnSubmit.value = Boolean(sla.email_on_submit);
    templateApprovalEmailOnReject.value = Boolean(sla.email_on_reject);
    templateApprovalEmailOnOverdue.value = Boolean(sla.email_on_overdue);
    const overdue = await fetchCreatorTemplateApprovalOverdue();
    overdueTemplateApprovals.value = overdue.approvals || [];
  } catch {
    templateApprovalChainSteps.value = 2;
    templateApprovalSlaHours.value = 72;
    overdueTemplateApprovals.value = [];
  }
}

async function saveTemplateApprovalSlaConfig() {
  try {
    await saveCreatorTemplateApprovalSlaConfig({
      timeout_hours: templateApprovalSlaHours.value,
      email_on_submit: templateApprovalEmailOnSubmit.value,
      email_on_reject: templateApprovalEmailOnReject.value,
      email_on_overdue: templateApprovalEmailOnOverdue.value,
    });
    saveMessage.value = `已保存审批 SLA（${templateApprovalSlaHours.value}h）`;
    await loadTemplateApprovalChainConfig();
  } catch (e) {
    handleSaveError(e);
  }
}

async function saveTemplateApprovalChainConfig() {
  try {
    const assignees = templateApprovalStepAssignees.value
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);
    const orGroups = templateApprovalOrGroups.value
      .split(',')
      .map((step) => step.split('|').map((s) => s.trim()).filter(Boolean))
      .filter((group) => group.length);
    const data = await saveCreatorTemplateApprovalChainConfig({
      required_steps: templateApprovalChainSteps.value,
      step_assignees: assignees,
      step_assignee_groups: orGroups.length ? orGroups : undefined,
    });
    templateApprovalChainSteps.value = data.required_steps || 2;
    templateApprovalStepAssignees.value = (data.step_assignees || []).join(', ');
    saveMessage.value = `已保存审批链（${templateApprovalChainSteps.value} 步）`;
  } catch (e) {
    handleSaveError(e);
  }
}

async function loadTemplateApprovals() {
  try {
    const data = await fetchCreatorTemplateApprovals({ status: 'pending' });
    templateApprovals.value = data.approvals || [];
    const history = await fetchCreatorTemplateApprovalHistory();
    templateApprovalHistory.value = history.approvals || [];
    await loadTemplateApprovalChainConfig();
  } catch {
    templateApprovals.value = [];
    templateApprovalHistory.value = [];
  }
}

async function exportTemplateApprovalAudit() {
  try {
    const data = await exportCreatorTemplateApprovalAudit();
    const text = JSON.stringify(data, null, 2);
    if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      saveMessage.value = `已导出 ${data.count} 条审批审计`;
    } else {
      saveMessage.value = `已导出 ${data.count} 条审批审计（无剪贴板）`;
    }
  } catch (e) {
    handleSaveError(e);
  }
}

async function applyMergePresetConflictFix(fix) {
  try {
    const result = await applyCreatorMergePresetConflictFix({
      package_id: fix.package_id,
      action: fix.action,
      dependency_id: fix.dependency_id,
      version_label: fix.version_label,
    });
    saveMessage.value = `已应用修复，剩余冲突 ${result.conflict_count}`;
    await loadMergePresetPackages();
  } catch (e) {
    handleSaveError(e);
  }
}

async function applyAllMergePresetConflictFixes() {
  try {
    const result = await applyAllCreatorMergePresetConflictFixes();
    saveMessage.value = `已批量应用 ${result.applied} 项，剩余冲突 ${result.conflict_count}`;
    await loadMergePresetPackages();
  } catch (e) {
    handleSaveError(e);
  }
}

async function previewMergePresetImportDiff() {
  try {
    const payload = JSON.parse(importMergePresetPackagesJson.value);
    mergePresetImportDiff.value = await previewCreatorMergePresetImportDiff(payload);
    saveMessage.value = `diff：新增 ${mergePresetImportDiff.value.added?.length || 0}，更新 ${mergePresetImportDiff.value.updated?.length || 0}`;
  } catch (e) {
    handleSaveError(e);
  }
}

async function applyMergePresetToposort() {
  try {
    const result = await applyCreatorMergePresetToposort();
    saveMessage.value = `已拓扑重排 ${result.reordered} 个预设包`;
    await loadMergePresetPackages();
  } catch (e) {
    handleSaveError(e);
  }
}

async function preflightMergePresetImport() {
  try {
    const payload = JSON.parse(importMergePresetPackagesJson.value);
    const result = await preflightCreatorMergePresetImport(payload);
    mergePresetImportPreflight.value = result;
    saveMessage.value = result.blocked
      ? `预检发现 ${result.conflict_count} 个冲突，导入已阻断`
      : `预检通过，可导入 ${result.would_import} 个包`;
  } catch (e) {
    handleSaveError(e);
  }
}

async function publishMergePresetToFactory() {
  if (!selectedProjectMergePreset.value) return;
  mergePresetFactoryPublishing.value = true;
  error.value = null;
  try {
    await publishCreatorMergePresetToFactory({ package_id: selectedMergePresetPackage.value });
    saveMessage.value = '已发布预设包到工厂库';
    await loadMergePresetPackages();
  } catch (e) {
    handleSaveError(e);
  } finally {
    mergePresetFactoryPublishing.value = false;
  }
}

async function pullFactoryMergePresets() {
  const ids = mergePresetPackages.value.filter((pkg) => pkg.scope === 'factory').map((pkg) => pkg.id);
  const fallback = factoryMergePresetPackages.value.map((pkg) => pkg.id);
  const packageIds = ids.length ? ids : fallback;
  if (!packageIds.length) return;
  mergePresetFactoryPulling.value = true;
  error.value = null;
  try {
    const preflight = await preflightCreatorFactoryMergePresetPull({ package_ids: packageIds });
    if (preflight.blocked) {
      saveMessage.value = `工厂拉取预检发现 ${preflight.conflict_count} 个冲突`;
      return;
    }
    const result = await pullCreatorFactoryMergePresetPackages({ package_ids: packageIds });
    saveMessage.value = `已从工厂库拉取 ${result.imported} 个预设包`;
    await loadMergePresetPackages();
  } catch (e) {
    handleSaveError(e);
  } finally {
    mergePresetFactoryPulling.value = false;
  }
}

async function deleteSelectedVolumeTemplate() {
  if (!selectedTemplateCustom.value) return;
  templateDeleting.value = true;
  error.value = null;
  try {
    const deletedId = selectedTemplateId.value;
    await deleteCreatorVolumeTemplate(deletedId);
    saveMessage.value = '已删除自定义模板';
    await loadVolumeTemplates();
    if (!volumeTemplates.value.some((t) => t.id === deletedId)) {
      selectedTemplateId.value = volumeTemplates.value[0]?.id || 'three_act';
    }
  } catch (e) {
    handleSaveError(e);
  } finally {
    templateDeleting.value = false;
  }
}

async function renameSelectedVolumeTemplate() {
  if (!selectedTemplateCustom.value || !renameTemplateName.value.trim()) return;
  templateRenaming.value = true;
  error.value = null;
  try {
    const renamed = await renameCreatorVolumeTemplate(selectedTemplateId.value, {
      name: renameTemplateName.value.trim(),
    });
    saveMessage.value = `已重命名为「${renamed.name}」`;
    await loadVolumeTemplates();
    selectedTemplateId.value = renamed.id;
  } catch (e) {
    handleSaveError(e);
  } finally {
    templateRenaming.value = false;
  }
}

async function loadMergePreferences() {
  try {
    const prefs = await fetchCreatorMergePreferences();
    pillarsMergeSource.value = prefs.pillars_merge_source || 'editor';
    outlineMergeSource.value = prefs.global_outline_merge_source || 'editor';
    if (prefs.merge_snapshot_id) {
      const known = settingsHistory.value.some((s) => s.id === prefs.merge_snapshot_id);
      if (known) compareSnapshotId.value = prefs.merge_snapshot_id;
    }
    const pillarsSnap = prefs.pillars_merge_snapshot_id || prefs.merge_snapshot_id;
    const outlineSnap = prefs.global_outline_merge_snapshot_id || prefs.merge_snapshot_id;
    if (pillarsSnap && settingsHistory.value.some((s) => s.id === pillarsSnap)) {
      pillarsSnapshotId.value = pillarsSnap;
    }
    if (outlineSnap && settingsHistory.value.some((s) => s.id === outlineSnap)) {
      outlineSnapshotId.value = outlineSnap;
    }
    usesGlobalMergeDefault.value = Boolean(prefs.uses_global_default);
  } catch {
    /* optional */
  }
}

async function loadTemplateSyncSources() {
  try {
    const data = await fetchCreatorVolumeTemplateSyncSources();
    templateSyncSources.value = data.sources || [];
  } catch {
    templateSyncSources.value = [];
  }
}

async function saveTemplateVersionLabel() {
  if (!selectedTemplateProject.value && !selectedTemplateFactory.value) return;
  if (templateVersionLabel.value.trim() && !isSemverVersionLabel(templateVersionLabel.value)) {
    saveMessage.value = '版本标签需符合 semver（如 v1.2.0）';
    return;
  }
  templateVersionSaving.value = true;
  error.value = null;
  try {
    await setCreatorVolumeTemplateVersion(selectedTemplateId.value, {
      version_label: templateVersionLabel.value.trim() || null,
    });
    saveMessage.value = '已更新版本标签';
    await loadVolumeTemplates();
    await loadTemplateVersionChangelog();
  } catch (e) {
    handleSaveError(e);
  } finally {
    templateVersionSaving.value = false;
  }
}

async function submitTemplateVersionApproval() {
  if (!selectedTemplateId.value) return;
  if (templateVersionLabel.value.trim() && !isSemverVersionLabel(templateVersionLabel.value)) {
    saveMessage.value = '版本标签需符合 semver（如 v1.2.0）';
    return;
  }
  templateApprovalSubmitting.value = true;
  error.value = null;
  try {
    await submitCreatorTemplateVersionApproval(selectedTemplateId.value, {
      version_label: templateVersionLabel.value.trim() || null,
    });
    saveMessage.value = '已提交版本变更审批';
    await loadTemplateApprovals();
  } catch (e) {
    handleSaveError(e);
  } finally {
    templateApprovalSubmitting.value = false;
  }
}

async function approveTemplateVersion(approvalId) {
  try {
    const result = await approveCreatorTemplateApproval(approvalId);
    saveMessage.value = result.chain_advanced
      ? `审批链进度 ${result.chain_progress}`
      : '已批准版本变更';
    await loadTemplateApprovals();
    if (!result.chain_advanced) {
      await loadVolumeTemplates();
      await loadTemplateVersionChangelog();
    }
  } catch (e) {
    handleSaveError(e);
  }
}

async function rejectTemplateVersion(approvalId) {
  try {
    await rejectCreatorTemplateApproval(approvalId, { reason: '驳回' });
    saveMessage.value = '已驳回版本变更';
    await loadTemplateApprovals();
  } catch (e) {
    handleSaveError(e);
  }
}

async function transferTemplateApproval(approvalId) {
  const toAssignee = window.prompt('转交给（审批人 ID）');
  if (!toAssignee?.trim()) return;
  try {
    await transferCreatorTemplateApproval(approvalId, {
      to_assignee: toAssignee.trim(),
      note: '委派转交',
    });
    saveMessage.value = `已转交给 ${toAssignee.trim()}`;
    await loadTemplateApprovals();
  } catch (e) {
    handleSaveError(e);
  }
}

async function previewApprovalSnapshotDiff(approvalId) {
  try {
    templateApprovalSnapshotDiff.value = await fetchCreatorTemplateApprovalSnapshotDiff(approvalId);
    const summary = templateApprovalSnapshotDiff.value?.diff_summary;
    saveMessage.value = summary?.changed
      ? `快照 diff：+${summary.lines_added} / -${summary.lines_removed}`
      : '快照与当前卷纲一致';
  } catch (e) {
    handleSaveError(e);
  }
}

async function syncTemplatesFromProjects() {
  templateSyncing.value = true;
  error.value = null;
  try {
    if (!templateSyncSources.value.length) {
      await loadTemplateSyncSources();
    }
    const slugs = templateSyncSources.value.map((s) => s.slug);
    if (!slugs.length) {
      saveMessage.value = '没有其他项目的自定义模板';
      return;
    }
    const result = await syncCreatorVolumeTemplates({ source_slugs: slugs });
    saveMessage.value = `已从 ${result.sources.length} 个项目同步 ${result.imported} 个模板`;
    await loadVolumeTemplates();
    await loadTemplateSyncSources();
  } catch (e) {
    handleSaveError(e);
  } finally {
    templateSyncing.value = false;
  }
}

async function publishSelectedTemplateToFactory() {
  if (!selectedTemplateProject.value) return;
  templatePublishing.value = true;
  error.value = null;
  try {
    await publishCreatorVolumeTemplateToFactory({ template_id: selectedTemplateId.value });
    saveMessage.value = '已发布到工厂模板库';
    await loadVolumeTemplates();
  } catch (e) {
    handleSaveError(e);
  } finally {
    templatePublishing.value = false;
  }
}

async function pullFactoryTemplates() {
  const ids = volumeTemplates.value.filter((t) => t.scope === 'factory').map((t) => t.id);
  if (!ids.length) return;
  factoryPulling.value = true;
  error.value = null;
  try {
    const result = await pullCreatorFactoryVolumeTemplates({ template_ids: ids });
    saveMessage.value = `已从工厂库拉取 ${result.imported} 个模板`;
    await loadVolumeTemplates();
  } catch (e) {
    handleSaveError(e);
  } finally {
    factoryPulling.value = false;
  }
}

async function deleteSelectedFactoryTemplate() {
  if (!selectedTemplateFactory.value) return;
  factoryDeleting.value = true;
  error.value = null;
  try {
    await deleteCreatorFactoryVolumeTemplate(selectedTemplateId.value);
    saveMessage.value = '已从工厂库删除模板';
    await loadVolumeTemplates();
    selectedTemplateId.value = volumeTemplates.value[0]?.id || 'three_act';
  } catch (e) {
    handleSaveError(e);
  } finally {
    factoryDeleting.value = false;
  }
}

async function exportMergePreferences() {
  error.value = null;
  try {
    const data = await exportCreatorMergePreferences();
    const text = JSON.stringify(data, null, 2);
    importMergePrefsJson.value = text;
    if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      saveMessage.value = '已导出合并策略并复制到剪贴板';
    } else {
      saveMessage.value = '已导出合并策略（见导入框）';
      showImportMergePrefs.value = true;
    }
  } catch (e) {
    handleSaveError(e);
  }
}

async function importMergePreferencesFromJson() {
  mergePrefsImporting.value = true;
  error.value = null;
  try {
    const payload = JSON.parse(importMergePrefsJson.value);
    await importCreatorMergePreferences({ ...payload, scope: payload.scope || 'both' });
    saveMessage.value = '已导入合并策略';
    importMergePrefsJson.value = '';
    showImportMergePrefs.value = false;
    await loadMergePreferences();
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    mergePrefsImporting.value = false;
  }
}

async function exportCustomTemplates() {
  error.value = null;
  try {
    const data = await exportCreatorVolumeTemplates();
    const text = JSON.stringify(data, null, 2);
    importTemplatesJson.value = text;
    if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      saveMessage.value = `已导出 ${data.count} 个模板并复制到剪贴板`;
    } else {
      saveMessage.value = `已导出 ${data.count} 个模板（见导入框）`;
      showImportTemplates.value = true;
    }
  } catch (e) {
    handleSaveError(e);
  }
}

async function importCustomTemplates() {
  templateImporting.value = true;
  error.value = null;
  try {
    const payload = JSON.parse(importTemplatesJson.value);
    const templates = payload.templates || payload;
    const result = await importCreatorVolumeTemplates({
      templates: Array.isArray(templates) ? templates : [],
      replace: false,
    });
    saveMessage.value = `已导入 ${result.imported} 个模板（共 ${result.total} 个）`;
    importTemplatesJson.value = '';
    showImportTemplates.value = false;
    await loadVolumeTemplates();
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    templateImporting.value = false;
  }
}

async function saveCustomVolumeTemplate() {
  if (!customTemplateName.value.trim() || !editableVolumes.value.length) return;
  templateSaving.value = true;
  error.value = null;
  try {
    const saved = await saveCreatorVolumeTemplate({
      name: customTemplateName.value.trim(),
      volumes: editableVolumes.value,
      max_chapter: overview.value?.max_chapter,
    });
    saveMessage.value = `已保存模板「${saved.name}」`;
    customTemplateName.value = '';
    await loadVolumeTemplates();
    selectedTemplateId.value = saved.id;
  } catch (e) {
    handleSaveError(e);
  } finally {
    templateSaving.value = false;
  }
}

async function loadVolumeTemplates() {
  try {
    const data = await fetchCreatorVolumeTemplates();
    volumeTemplates.value = data.templates || [];
    if (volumeTemplates.value.length && !volumeTemplates.value.some((t) => t.id === selectedTemplateId.value)) {
      selectedTemplateId.value = volumeTemplates.value[0].id;
    }
  } catch {
    volumeTemplates.value = [];
  }
}

async function applyVolumeTemplate() {
  templateApplying.value = true;
  error.value = null;
  try {
    const result = await applyCreatorVolumeTemplate({
      template_id: selectedTemplateId.value,
      max_chapter: overview.value?.max_chapter,
    });
    editableVolumes.value = (result.volumes || []).map((v) => ({ ...v }));
    mergePreview.value = null;
    splitPreview.value = null;
    saveMessage.value = `已套用模板「${result.template_name}」，请保存卷纲`;
    syncSplitChapterFromVolume();
  } catch (e) {
    handleSaveError(e);
  } finally {
    templateApplying.value = false;
  }
}

async function loadSettingsHistory() {
  try {
    const data = await fetchCreatorSettingsHistory();
    settingsHistory.value = data.snapshots || [];
    if (settingsHistory.value.length && !compareSnapshotId.value) {
      compareSnapshotId.value = settingsHistory.value[0].id;
    }
  } catch {
    settingsHistory.value = [];
  }
}

async function applyVolumeSplit() {
  splitApplying.value = true;
  error.value = null;
  try {
    const result = await splitCreatorVolumePlan({
      volumes: editableVolumes.value,
      volume_index: splitVolumeIdx.value,
      split_at_chapter: splitAtChapter.value,
    });
    editableVolumes.value = (result.volumes || []).map((v) => ({ ...v }));
    splitPreview.value = {
      first_label: result.first_label,
      second_label: result.second_label,
      first_range: result.first_range,
      second_range: result.second_range,
    };
    mergePreview.value = null;
    saveMessage.value = `已拆为「${result.first_label}」与「${result.second_label}」，请保存卷纲`;
    syncSplitChapterFromVolume();
  } catch (e) {
    handleSaveError(e);
  } finally {
    splitApplying.value = false;
  }
}

async function restoreSettingsHistory(snapshotId) {
  settingsRestoring.value = true;
  error.value = null;
  try {
    const docs = await restoreCreatorSettingsSnapshot(snapshotId);
    settingsDocs.value = docs;
    pillarsText.value = docs.pillars_text || '';
    globalOutlineText.value = docs.global_outline_text || '';
    settingsBaseline.value = {
      pillars: docs.pillars_text || '',
      outline: docs.global_outline_text || '',
    };
    settingsRevisions.value = {
      pillars: docs.pillars_revision || '',
      outline: docs.global_outline_revision || '',
    };
    saveMessage.value = '已从历史版本恢复设定';
    conflictMessage.value = '';
    await loadSettingsHistory();
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    settingsRestoring.value = false;
  }
}

async function applyVolumeMerge() {
  if (mergeStartIdx.value > mergeEndIdx.value) return;
  mergeApplying.value = true;
  error.value = null;
  try {
    const result = await mergeCreatorVolumePlan({
      volumes: editableVolumes.value,
      start_index: mergeStartIdx.value,
      end_index: mergeEndIdx.value,
      label: mergeLabel.value.trim() || undefined,
    });
    editableVolumes.value = (result.volumes || []).map((v) => ({ ...v }));
    mergePreview.value = {
      merged_label: result.merged_label,
      merged_range: result.merged_range,
    };
    mergeStartIdx.value = 0;
    mergeEndIdx.value = Math.min(1, Math.max(0, editableVolumes.value.length - 1));
    mergeLabel.value = '';
    saveMessage.value = `已合并为「${result.merged_label}」，请保存卷纲`;
  } catch (e) {
    handleSaveError(e);
  } finally {
    mergeApplying.value = false;
  }
}

async function loadSettingsDocs() {
  const docs = await fetchCreatorSettingsDocs();
  settingsDocs.value = docs;
  pillarsText.value = docs.pillars_text || '';
  globalOutlineText.value = docs.global_outline_text || '';
  settingsBaseline.value = {
    pillars: docs.pillars_text || '',
    outline: docs.global_outline_text || '',
  };
  settingsRevisions.value = {
    pillars: docs.pillars_revision || '',
    outline: docs.global_outline_revision || '',
  };
  settingsDiffPreview.value = null;
  showSettingsDiff.value = false;
}

function cancelSettingsDiff() {
  showSettingsDiff.value = false;
  settingsDiffPreview.value = null;
}

async function refreshMergeStrategyPreview() {
  if (!showMergeStrategy.value) {
    mergeStrategyPreview.value = null;
    return;
  }
  try {
    mergeStrategyPreview.value = await previewCreatorSettingsMerge({
      pillars_text: pillarsText.value,
      global_outline_text: globalOutlineText.value,
      pillars_merge_source: pillarsMergeSource.value,
      global_outline_merge_source: outlineMergeSource.value,
      snapshot_id: compareSnapshotId.value || undefined,
      pillars_merge_snapshot_id: pillarsSnapshotId.value || compareSnapshotId.value || undefined,
      global_outline_merge_snapshot_id: outlineSnapshotId.value || compareSnapshotId.value || undefined,
    });
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
}

async function refreshThreeWayPreview() {
  if (!showSettingsDiff.value) return;
  try {
    settingsDiffPreview.value = await previewCreatorSettingsThreeWay({
      pillars_text: pillarsText.value,
      global_outline_text: globalOutlineText.value,
      snapshot_id: compareSnapshotId.value || undefined,
    });
    await refreshMergeStrategyPreview();
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
}

async function requestSaveSettings() {
  error.value = null;
  if (
    pillarsText.value === settingsBaseline.value.pillars
    && globalOutlineText.value === settingsBaseline.value.outline
  ) {
    saveMessage.value = '设定无变更';
    return;
  }
  try {
    if (settingsHistory.value.length) {
      settingsDiffPreview.value = await previewCreatorSettingsThreeWay({
        pillars_text: pillarsText.value,
        global_outline_text: globalOutlineText.value,
        snapshot_id: compareSnapshotId.value || undefined,
      });
    } else {
      settingsDiffPreview.value = await previewCreatorSettingsDocs({
        pillars_text: pillarsText.value,
        global_outline_text: globalOutlineText.value,
      });
    }
    showSettingsDiff.value = true;
    await refreshMergeStrategyPreview();
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
}

async function confirmSaveSettings() {
  settingsSaving.value = true;
  saveMessage.value = '';
  error.value = null;
  try {
    const body = {
      pillars_text: pillarsText.value,
      global_outline_text: globalOutlineText.value,
      expected_pillars_revision: settingsRevisions.value.pillars,
      expected_global_outline_revision: settingsRevisions.value.outline,
    };
    if (showMergeStrategy.value) {
      body.pillars_merge_source = pillarsMergeSource.value;
      body.global_outline_merge_source = outlineMergeSource.value;
      body.merge_snapshot_id = compareSnapshotId.value || undefined;
      body.pillars_merge_snapshot_id = pillarsSnapshotId.value || compareSnapshotId.value || undefined;
      body.global_outline_merge_snapshot_id = outlineSnapshotId.value || compareSnapshotId.value || undefined;
    }
    await saveCreatorSettingsDocs(body);
    saveMessage.value = '设定已保存';
    conflictMessage.value = '';
    showSettingsDiff.value = false;
    settingsDiffPreview.value = null;
    mergeStrategyPreview.value = null;
    await refresh();
  } catch (e) {
    handleSaveError(e);
  } finally {
    settingsSaving.value = false;
  }
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
      saveMessage.value = 'Batch 已完成，卷摘要已更新';
      await refresh();
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

async function saveVolumePlan() {
  saving.value = true;
  saveMessage.value = '';
  error.value = null;
  try {
    await saveCreatorVolumePlan(editableVolumes.value, volumePlanRevision.value);
    saveMessage.value = '卷纲已保存并同步到全局大纲';
    conflictMessage.value = '';
    await refresh();
  } catch (e) {
    handleSaveError(e);
  } finally {
    saving.value = false;
  }
}

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
    await loadMergePreferences();
    await loadMergePresetPackages();
    await loadTemplateApprovals();
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

onMounted(refresh);

onUnmounted(() => {
  stopBatchPolling();
});

watch(projectRevision, () => {
  refresh();
});
</script>

<style scoped>
.creator-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
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
  font-size: 8px;
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
  font-size: 12px;
  margin-bottom: var(--space-sm);
  color: var(--color-accent);
  font-family: 'Press Start 2P', monospace;
}

.column-hint {
  font-size: 8px;
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
  font-size: 8px;
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

.preview-text {
  font-size: 8px;
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
  font-size: 9px;
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
  font-size: 8px;
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
  font-size: 8px;
  opacity: 0.6;
  user-select: none;
}

.vol-input {
  font-size: 8px;
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
  font-size: 7px;
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
  font-size: 8px;
}

.deviation-warn { color: #886600; }
.deviation-alert { color: #c44; }

.settings-textarea {
  width: 100%;
  font-size: 8px;
  font-family: inherit;
  padding: var(--space-xs);
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--color-text);
  resize: vertical;
  min-height: 80px;
}

.batch-range {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 8px;
  margin-bottom: 6px;
}

.batch-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.advance-batch-panel {
  margin-top: var(--space-md);
  padding: var(--space-sm);
}

.batch-error {
  color: #c44;
  font-size: 8px;
  margin-top: 4px;
}

.settings-diff-panel {
  margin-top: var(--space-sm);
  padding: var(--space-sm);
}

.diff-line {
  font-size: 8px;
  margin: 2px 0;
}

.settings-excerpt,
.volume-excerpt {
  font-size: 8px;
  white-space: pre-wrap;
  max-height: 160px;
  overflow: auto;
  margin: var(--space-sm) 0;
}

.path-line,
.cmd-block code {
  font-size: 7px;
  word-break: break-all;
  display: block;
}

.p0-line.ok { color: #4a4; }
.p0-line.warn { color: #c44; }

.meta-line {
  font-size: 8px;
  opacity: 0.75;
}

.refresh-btn {
  font-size: 8px;
  padding: var(--space-xs) var(--space-sm);
  cursor: pointer;
}

.error-banner {
  padding: var(--space-sm);
  color: #c44;
  font-size: 8px;
}

.save-banner {
  padding: var(--space-sm);
  color: #484;
  font-size: 8px;
}

.conflict-banner {
  padding: var(--space-sm);
  color: #a60;
  font-size: 8px;
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.merge-strategy-panel {
  margin-top: var(--space-xs);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.merge-presets {
  display: flex;
  gap: var(--space-xs);
  flex-wrap: wrap;
  margin-bottom: 4px;
}

.merge-preview-visual {
  margin-top: var(--space-xs);
}

.mini-btn--danger {
  color: #c44;
}

.onboarding-wizard {
  padding: var(--space-sm);
  font-size: 8px;
}

.wizard-steps {
  margin: var(--space-xs) 0 0;
  padding-left: 1.2em;
}

.wizard-step {
  margin-bottom: 4px;
}

.wizard-step--focused {
  outline: 2px solid var(--color-accent);
  border-radius: 4px;
  padding: 2px;
}

.wizard-step-label {
  display: flex;
  gap: var(--space-xs);
  align-items: flex-start;
  cursor: pointer;
}

.wizard-step-note {
  width: 100%;
  margin-top: 4px;
  font-size: 0.85rem;
}

.wizard-mentions {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.wizard-mention-badge {
  font-size: 7px;
  color: var(--color-accent);
  background: rgba(127, 127, 127, 0.12);
  padding: 1px 4px;
  border-radius: 3px;
}

.wizard-notification-badge {
  color: var(--color-warn, #c90);
  font-size: 8px;
}

.wizard-notifications {
  margin: var(--space-sm) 0;
  padding: var(--space-sm);
  border: 1px dashed rgba(127, 127, 127, 0.35);
}

.wizard-notification-row--unread strong {
  color: var(--color-warn, #c90);
}

.template-changelog ul {
  margin: 4px 0 0;
  padding-left: 1.2em;
  font-size: 8px;
}

.changelog-row {
  margin-bottom: 2px;
}

.changelog-diff {
  color: var(--color-accent);
}

.changelog-visual-diff {
  margin-top: 4px;
  font-size: 7px;
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

.wizard-webhook-panel {
  margin-top: var(--space-sm);
  padding-top: var(--space-sm);
  border-top: 1px dashed rgba(127, 127, 127, 0.35);
}

.wizard-email-panel {
  margin-top: var(--space-sm);
  padding-top: var(--space-sm);
  border-top: 1px dashed rgba(127, 127, 127, 0.35);
}

.wizard-digest-panel {
  margin-top: var(--space-sm);
  padding: var(--space-sm);
  border: 1px dashed rgba(127, 127, 127, 0.25);
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

.merge-preset-graph ul {
  margin: 0;
  padding-left: 1.2rem;
}

.version-semver-warn {
  color: var(--color-warn, #c90);
}

.wizard-progress-badge {
  opacity: 0.85;
}

.wizard-auto-badge {
  margin-left: 4px;
  font-size: 7px;
  color: var(--color-accent);
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

.volume-merge-panel {
  margin-top: var(--space-sm);
  padding: var(--space-sm);
}

.volume-split-panel {
  margin-top: var(--space-sm);
  padding: var(--space-sm);
}

.history-list {
  list-style: none;
  padding: 0;
  margin: var(--space-xs) 0 0;
}

.history-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 6px;
  margin-bottom: 4px;
  font-size: 8px;
}

.history-meta {
  opacity: 0.75;
}

.history-excerpt {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.merge-range {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 8px;
  margin-bottom: 6px;
  align-items: center;
}
</style>

<!--
  CreatorOnboardingWizardPanel.vue — 入门向导面板（从 CreatorPage 拆出）
-->
<template>
    <details
      v-if="ob.onboardingWizard"
      ref="wizardPanelRef"
      class="onboarding-wizard pixel-border"
      data-testid="onboarding-wizard-panel"
      :open="ob.wizardPanelOpen"
      @toggle="ob.onWizardToggle"
    >
      <summary>
        入门向导 · {{ ob.onboardingWizard.mode_label }}（{{ ob.onboardingWizard.max_chapter }} 章上限）
        <span v-if="ob.onboardingWizard.progress_pct != null" class="wizard-progress-badge" data-testid="wizard-progress-label">
          · {{ ob.onboardingWizard.progress_pct }}%
        </span>
        <span
          v-if="ob.wizardUnreadMentions > 0"
          class="wizard-notification-badge"
          data-testid="wizard-notification-badge"
        >
          · {{ ob.wizardUnreadMentions }} 条 @提及
        </span>
      </summary>
      <div
        v-if="ob.wizardNotifications.length"
        class="wizard-notifications"
        data-testid="wizard-notifications-panel"
      >
        <p class="meta-line">批注通知</p>
        <label v-if="ob.wizardNotificationHandles.length" class="meta-line">
          按 handle 过滤
          <select
            v-model="ob.wizardNotificationHandleFilter"
            class="vol-input"
            data-testid="wizard-notification-handle-filter"
            @change="ob.loadWizardNotifications"
          >
            <option value="">全部</option>
            <option v-for="handle in ob.wizardNotificationHandles" :key="handle" :value="handle">
              @{{ handle }}
            </option>
          </select>
        </label>
        <div
          v-if="ob.wizardNotificationDigest.groups?.length"
          class="wizard-digest-panel"
          data-testid="wizard-notification-digest"
        >
          <p class="meta-line">通知摘要（{{ ob.wizardNotificationDigest.unread }} 条未读）</p>
          <ul>
            <li
              v-for="group in ob.wizardNotificationDigest.groups"
              :key="group.handle"
              class="wizard-digest-row"
              data-testid="wizard-digest-row"
            >
              <strong>@{{ group.handle }}</strong>
              <span class="meta-line">{{ group.count }} 条 · {{ group.steps.map((s) => s.step_id).join(', ') }}</span>
            </li>
          </ul>
        </div>
        <div
          v-if="ob.uiProfile.show_digest_ops"
          class="wizard-digest-schedule-panel"
          data-testid="wizard-digest-schedule-panel"
        >
          <p class="meta-line">定时 digest</p>
          <label class="meta-line">
            <input v-model="ob.wizardDigestScheduleEnabled" type="checkbox" data-testid="wizard-digest-schedule-enabled" />
            启用（每 {{ ob.wizardDigestScheduleHours }} 小时）
          </label>
          <input
            v-model.number="ob.wizardDigestScheduleHours"
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
            @click="ob.saveWizardDigestSchedule"
          >
            保存定时
          </button>
          <button
            type="button"
            class="mini-btn pixel-border"
            data-testid="dispatch-wizard-digest-btn"
            @click="ob.dispatchWizardDigest"
          >
            立即发送 digest
          </button>
            <p class="meta-line" data-testid="wizard-digest-background-hint">
            Dashboard 后台每 15 分钟自动检查到期 digest
          </p>
          <p
            v-if="ob.wizardDigestStats.sent_total || ob.wizardDigestStats.failed_total"
            class="meta-line"
            data-testid="wizard-digest-stats"
          >
            发送统计：成功 {{ ob.wizardDigestStats.sent_total }} / 失败 {{ ob.wizardDigestStats.failed_total }}
          </p>
          <input
            v-model="ob.wizardDigestHandleChannelsJson"
            class="vol-input"
            data-testid="wizard-digest-handle-channels"
            placeholder='handle 路由 JSON，如 {"batch":["webhook"],"*":["email"]}'
          />
          <input
            v-model="ob.wizardDigestHandleQuietJson"
            class="vol-input"
            data-testid="wizard-digest-handle-quiet-hours"
            placeholder='handle 静默 JSON，如 {"batch":{"start":22,"end":6}}'
          />
          <label class="meta-line">
            静默时段（UTC）
            <input
              v-model.number="ob.wizardDigestQuietStart"
              type="number"
              min="0"
              max="23"
              class="vol-input"
              data-testid="wizard-digest-quiet-start"
              placeholder="起"
            />
            –
            <input
              v-model.number="ob.wizardDigestQuietEnd"
              type="number"
              min="0"
              max="23"
              class="vol-input"
              data-testid="wizard-digest-quiet-end"
              placeholder="止"
            />
          </label>
          <div
            v-if="ob.wizardDigestRetryQueue.item_count"
            class="wizard-digest-retry"
            data-testid="wizard-digest-retry-panel"
          >
            <p class="meta-line">重试队列 {{ ob.wizardDigestRetryQueue.item_count }} 条</p>
            <button
              type="button"
              class="mini-btn pixel-border"
              data-testid="process-wizard-digest-retry-btn"
              @click="ob.processWizardDigestRetries"
            >
              重试失败 digest
            </button>
          </div>
          <div
            v-if="ob.wizardDigestDeadLetter.item_count"
            class="wizard-digest-dead-letter"
            data-testid="wizard-digest-dead-letter-panel"
          >
            <p class="meta-line">死信队列 {{ ob.wizardDigestDeadLetter.item_count }} 条</p>
            <button
              type="button"
              class="mini-btn pixel-border"
              data-testid="replay-wizard-digest-dead-letter-btn"
              @click="ob.replayWizardDigestDeadLetter"
            >
              重放首条死信
            </button>
          </div>
        </div>
        <ul>
          <li
            v-for="note in ob.wizardNotifications"
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
          @click="ob.ackWizardNotifications"
        >
          全部标为已读
        </button>
        <div v-if="!ob.uiProfile.simplified_notifications" class="wizard-webhook-panel" data-testid="wizard-webhook-panel">
          <p class="meta-line">通知 Webhook</p>
          <label class="meta-line">
            <input v-model="ob.wizardWebhookEnabled" type="checkbox" data-testid="wizard-webhook-enabled" />
            启用
          </label>
          <input
            v-model="ob.wizardWebhookUrl"
            class="vol-input"
            data-testid="wizard-webhook-url"
            placeholder="https://example.com/hooks/mentions"
          />
          <input
            v-model="ob.wizardWebhookSigningSecret"
            class="vol-input"
            data-testid="wizard-webhook-signing-secret"
            placeholder="Webhook 签名密钥（可选）"
          />
          <button
            type="button"
            class="mini-btn pixel-border"
            data-testid="save-wizard-webhook-btn"
            @click="ob.saveWizardWebhook"
          >
            保存 Webhook
          </button>
        </div>
        <div v-if="!ob.uiProfile.simplified_notifications" class="wizard-email-panel" data-testid="wizard-email-panel">
          <p class="meta-line">通知邮件</p>
          <label class="meta-line">
            <input v-model="ob.wizardEmailEnabled" type="checkbox" data-testid="wizard-email-enabled" />
            启用
          </label>
          <input
            v-model="ob.wizardEmailTo"
            class="vol-input"
            data-testid="wizard-email-to"
            placeholder="user@example.com"
          />
          <input
            v-model="ob.wizardEmailSmtpHost"
            class="vol-input"
            data-testid="wizard-email-smtp-host"
            placeholder="smtp.example.com"
          />
          <button
            type="button"
            class="mini-btn pixel-border"
            data-testid="save-wizard-email-btn"
            @click="ob.saveWizardEmail"
          >
            保存邮件
          </button>
        </div>
      </div>
      <ol class="wizard-steps">
        <li
          v-for="step in ob.onboardingWizard.steps"
          :key="step.id"
          class="wizard-step"
          :class="{
            'wizard-step--focused': step.id === ob.focusWizardStep,
            'wizard-step--mode-linked': ob.uiProfile.creation_mode_onboarding_step_link
              && ob.isOnboardingStepLinkedToCurrentMode(step.id),
          }"
        >
          <label class="wizard-step-label">
            <input
              type="checkbox"
              :checked="ob.completedWizardSteps.has(step.id)"
              :data-testid="`wizard-step-${step.id}`"
              @change="ob.toggleWizardStep(step.id, $event.target.checked)"
            />
            <span>
              <strong>{{ step.title }}</strong>
              <span
                v-if="ob.autoCompletedWizardSteps.has(step.id)"
                class="wizard-auto-badge"
                data-testid="wizard-auto-badge"
              >自动</span>
              <span
                v-if="ob.uiProfile.creation_mode_onboarding_step_link && ob.onboardingModesForStep(step.id).length"
                class="wizard-step-mode-badges"
                :data-testid="`wizard-step-modes-${step.id}`"
              >
                <span
                  v-for="modeRow in ob.onboardingModesForStep(step.id)"
                  :key="`${step.id}-${modeRow.mode}`"
                  class="wizard-step-mode-badge"
                >{{ modeRow.label }}</span>
              </span>
              <span class="meta-line">{{ step.detail }}</span>
            </span>
          </label>
          <textarea
            :value="ob.wizardStepNotes[step.id] || ''"
            class="vol-input wizard-step-note"
            :data-testid="`wizard-note-${step.id}`"
            placeholder="协作批注（可选，支持 @volume @reviewer）"
            rows="2"
            @input="ob.wizardStepNotes[step.id] = $event.target.value"
            @blur="ob.saveWizardStepNote(step.id)"
          />
          <div
            v-if="ob.wizardMentionsForStep(step.id).length"
            class="wizard-mentions"
            data-testid="wizard-mentions"
          >
            <span
              v-for="mention in ob.wizardMentionsForStep(step.id)"
              :key="`${step.id}-${mention}`"
              class="wizard-mention-badge"
              data-testid="wizard-mention-badge"
            >@{{ mention }}</span>
          </div>
        </li>
      </ol>
      <p class="meta-line">
        清单：<code>{{ ob.onboardingWizard.checklist_doc }}</code> ·
        冒烟：<code>{{ ob.onboardingWizard.smoke_command }}</code>
      </p>
      <div class="merge-range">
        <button
          type="button"
          class="mini-btn pixel-border"
          data-testid="wizard-share-link-btn"
          @click="ob.copyWizardShareLink"
        >
          复制分享链接
        </button>
        <span v-if="ob.wizardShareMessage" class="meta-line" data-testid="wizard-share-message">{{ ob.wizardShareMessage }}</span>
      </div>
    </details>

</template>

<script setup>
import { inject } from 'vue';
import { CREATOR_ONBOARDING_KEY } from './creatorOnboardingKey.js';

const ob = inject(CREATOR_ONBOARDING_KEY);
</script>

<style scoped>
.wizard-step--mode-linked {
  border-color: rgba(100, 140, 200, 0.45);
  background: rgba(100, 140, 200, 0.06);
}
.wizard-step-mode-badges {
  display: inline-flex;
  gap: 4px;
  margin-left: 6px;
}
.wizard-step-mode-badge {
  font-size: var(--text-xs);
  padding: 1px 4px;
  border: 1px solid rgba(100, 140, 200, 0.45);
  border-radius: 2px;
  color: var(--color-accent);
}
.onboarding-wizard {
  padding: var(--space-sm);
  font-size: var(--text-sm);
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
  font-size: var(--text-xs);
  color: var(--color-accent);
  background: rgba(127, 127, 127, 0.12);
  padding: 1px 4px;
  border-radius: 3px;
}
.wizard-notification-badge {
  color: var(--color-warn, #c90);
  font-size: var(--text-sm);
}
.wizard-notifications {
  margin: var(--space-sm) 0;
  padding: var(--space-sm);
  border: 1px dashed rgba(127, 127, 127, 0.35);
}
.wizard-notification-row--unread strong {
  color: var(--color-warn, #c90);
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
.wizard-progress-badge {
  opacity: 0.85;
}
.wizard-auto-badge {
  margin-left: 4px;
  font-size: var(--text-xs);
  color: var(--color-accent);
}

</style>

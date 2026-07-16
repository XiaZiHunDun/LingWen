<!--
  AskPage.vue — L1 聊聊（frontend-ia-v1）
-->
<template>
  <div class="ask-page l1-page" data-testid="ask-page">
    <div
      :key="tab"
      class="ask-page__panel l1-panel-enter"
      :class="{ 'ask-page__panel--thread': tab === 'chat' && hasUserMessages }"
    >
      <template v-if="tab === 'chat'">
        <div class="ask-page__chat-stack">
          <PageLeadBar
            page-id="ask-chat"
            inline
            text="查进度、问设定、理思路——正文请在「书桌」上落字"
          />
          <div class="ask-page__messages" data-testid="ask-messages">
            <div
              v-for="(msg, idx) in messages"
              :key="idx"
              class="ask-page__msg"
              :class="`ask-page__msg--${msg.role}`"
            >
              <pre class="ask-page__msg-text">{{ msg.text }}</pre>
              <div
                v-if="msg.role === 'assistant' && idx === messages.length - 1 && !loading && hasUserMessages"
                class="ask-page__msg-actions"
              >
                <button
                  type="button"
                  class="ask-page__text-link"
                  data-testid="ask-copy-to-note-btn"
                  @click="copyToNote(msg.text)"
                >
                  记入速记
                </button>
                <button
                  type="button"
                  class="ask-page__text-link"
                  data-testid="ask-go-write-btn"
                  @click="goWrite()"
                >
                  去书桌
                </button>
              </div>
            </div>
            <p v-if="loading" class="ask-page__typing">思考中…</p>
          </div>
        </div>

        <div class="ask-page__footer">
          <div
            v-if="suggestions.length && !hasUserMessages"
            class="ask-composer__hints"
            data-testid="ask-topic-list"
          >
            <button
              v-for="s in suggestions"
              :key="s.id"
              type="button"
              class="ask-composer__pill"
              :data-testid="`ask-suggestion-${s.id}`"
              @click="sendMessage(s.prompt)"
            >
              {{ s.label }}
            </button>
          </div>
          <form class="ask-composer" @submit.prevent="sendMessage()">
            <p
              v-if="isLongDraft"
              class="ask-composer__long-hint"
              data-testid="ask-long-draft-hint"
            >
              长文续写请在「书桌」进行。
              <button
                type="button"
                class="ask-page__text-link"
                data-testid="ask-long-go-write-btn"
                @click="goWrite()"
              >
                去书桌
              </button>
            </p>
            <div class="ask-composer__card">
              <textarea
                v-model="draft"
                class="ask-composer__input"
                rows="2"
                placeholder="随便问：进度、人物、这章怎么写…"
                data-testid="ask-input"
                @keydown.enter.exact.prevent="sendMessage()"
              />
              <div class="ask-composer__toolbar ask-composer__toolbar--send-only">
                <button
                  type="submit"
                  class="ask-composer__send"
                  data-testid="ask-send-btn"
                  :disabled="loading || !draft.trim() || isLongDraft"
                  aria-label="发送"
                >
                  <svg class="ask-composer__send-icon" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M12 19V5m0 0l-6 6m6-6l6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                </button>
              </div>
            </div>
          </form>
        </div>
      </template>

      <template v-else>
        <div class="ask-page__note-body">
          <PageLeadBar
            page-id="ask-note"
            inline
            text="碎片灵感先记这里，凑齐再收成新书——长文写作请去「书桌」"
          />
          <ul v-if="notes.length" class="ask-page__notes" data-testid="ask-notes">
            <li v-for="n in notes" :key="n.id" class="ask-page__note-item">{{ n.text }}</li>
          </ul>
          <p v-else class="ask-page__note-empty" data-testid="ask-notes-empty">
            <span class="ask-page__note-empty-title">速记是空的</span>
            碎片灵感先记在这里，稍后可收成新书。
          </p>
        </div>
        <div class="ask-page__footer">
          <form class="ask-composer" @submit.prevent="saveNote()">
            <div class="ask-composer__card">
              <textarea
                v-model="noteDraft"
                class="ask-composer__input"
                rows="2"
                placeholder="碎片灵感、一句对白…"
                data-testid="ask-note-input"
              />
              <div class="ask-composer__toolbar">
                <div class="ask-composer__tools">
                  <button
                    type="button"
                    class="ask-composer__pill"
                    data-testid="ask-new-project-btn"
                    @click="startNewProject()"
                  >
                    收成新书
                  </button>
                </div>
                <button
                  type="submit"
                  class="ask-composer__send"
                  data-testid="ask-note-save-btn"
                  :disabled="!noteDraft.trim()"
                  aria-label="保存"
                >
                  <svg class="ask-composer__send-icon" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M12 19V5m0 0l-6 6m6-6l6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                </button>
              </div>
            </div>
          </form>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue';
import PageLeadBar from '../components/PageLeadBar.vue';
import { useAskAssistant } from '../composables/useAskAssistant.js';
import { useDashboardNav } from '../composables/useDashboardNav.js';
import { getWriteResume } from '../utils/writeResumeStorage.js';
import { useStudioProject } from '../composables/useStudioProject.js';

const { navigateTo } = useDashboardNav();
const studio = useStudioProject();

const {
  tab,
  messages,
  draft,
  noteDraft,
  notes,
  loading,
  isLongDraft,
  suggestions,
  bootstrap,
  sendMessage,
  saveNote,
  copyToNote,
  goWrite,
  startNewProject,
} = useAskAssistant({
  onGoWrite(chapter) {
    const slug = studio.activeSlug.value;
    const resume = getWriteResume(slug);
    const ch = chapter ?? resume?.chapter ?? null;
    navigateTo('write', { chapter: ch, clearFocus: false, workspace: 'write' });
  },
  onNewProject() {
    navigateTo('write', { wizard: true, clearFocus: true });
  },
});

const hasUserMessages = computed(() => messages.value.some((m) => m.role === 'user'));

onMounted(() => {
  bootstrap();
});
</script>

<style scoped>
.ask-page {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  width: 100%;
  max-width: none;
  margin: 0;
}
.ask-page__panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  flex: 1;
  min-height: 0;
  width: 100%;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  background: linear-gradient(135deg, var(--bg-elevated) 0%, var(--bg-secondary) 100%);
  box-shadow: var(--shadow-card);
}
.ask-page__chat-stack {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  width: 100%;
}
.ask-page__messages {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}
.ask-page__panel--thread .ask-page__messages {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}
.ask-page__note-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}
.ask-page__msg {
  animation: msg-fade-in 0.3s ease-out;
}
@keyframes msg-fade-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
.ask-page__msg-text {
  margin: 0;
  white-space: pre-wrap;
  font-family: var(--font-ui);
  font-size: var(--text-sm);
}
.ask-page__msg--user {
  display: flex;
  flex-direction: row-reverse;
}
.ask-page__msg--user .ask-page__msg-text {
  background: linear-gradient(135deg, var(--color-accent) 0%, var(--color-accent-gradient-end) 100%);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md) 4px var(--radius-md) var(--radius-md);
  color: var(--color-on-accent);
  max-width: 70%;
}
.ask-page__panel--thread {
  padding-bottom: var(--space-md);
}
.ask-page__panel--thread .ask-page__chat-stack {
  flex: 1;
  min-height: 0;
}
.ask-page__msg--assistant {
  display: flex;
}
.ask-page__msg--assistant .ask-page__msg-text {
  background: var(--bg-elevated);
  padding: var(--space-sm) var(--space-md);
  border-radius: 4px var(--radius-md) var(--radius-md) var(--radius-md);
  color: var(--color-text);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
  max-width: 80%;
}
.ask-page__footer {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  flex-shrink: 0;
  margin-top: auto;
  width: 100%;
  max-width: 52rem;
  margin-left: auto;
  margin-right: auto;
}

/* —— DeepSeek 风格输入卡片 —— */
.ask-composer__hints {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-start;
  gap: 8px;
}
.ask-composer__pill {
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  font-weight: 500;
  padding: 6px 12px;
  cursor: pointer;
  background: var(--color-accent-soft);
  border: none;
  border-radius: 999px;
  color: var(--color-accent);
  white-space: nowrap;
  transition: all var(--transition-fast);
}
.ask-composer__pill:hover {
  background: color-mix(in srgb, var(--color-accent-soft) 70%, var(--color-accent) 30%);
  color: var(--color-accent-hover);
  transform: translateY(-1px);
}
.ask-composer {
  width: 100%;
}
.ask-composer__card {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  padding: 14px 14px 12px;
  background: var(--bg-elevated);
  border: var(--border-width) solid var(--border-color);
  border-radius: 20px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}
.ask-composer__card:focus-within {
  border-color: var(--color-accent-muted);
  box-shadow: 0 0 0 3px var(--color-accent-soft), var(--shadow-md);
}
.ask-composer__input {
  width: 100%;
  box-sizing: border-box;
  min-height: 2.75rem;
  max-height: 10rem;
  resize: none;
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  line-height: var(--leading-normal);
  color: var(--color-text);
  background: transparent;
  border: none;
  padding: 0 4px;
}
.ask-composer__input::placeholder {
  color: var(--color-text-dim);
}
.ask-composer__input:focus {
  outline: none;
}
.ask-composer__toolbar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-sm);
  min-height: 36px;
}
.ask-composer__toolbar--send-only {
  justify-content: flex-end;
}
.ask-composer__tools {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}
.ask-composer__tools--spacer {
  flex: 1;
}
.ask-composer__send {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  border: none;
  border-radius: 50%;
  color: #fff;
  background: linear-gradient(135deg, var(--color-accent) 0%, var(--color-accent-gradient-end) 100%);
  cursor: pointer;
  transition: all var(--transition-fast);
  box-shadow: 0 2px 8px rgba(124, 58, 237, 0.3);
}
.ask-composer__send:hover:not(:disabled) {
  background: linear-gradient(135deg, var(--color-accent-hover) 0%, var(--color-accent-gradient-end) 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(124, 58, 237, 0.4);
}
.ask-composer__send:active:not(:disabled) {
  transform: scale(0.96);
}
.ask-composer__long-hint {
  margin: 0 0 var(--space-xs);
  padding: var(--space-xs) var(--space-sm);
  font-size: var(--text-xs);
  color: var(--color-warning);
  background: var(--color-warning-soft);
  border-radius: var(--radius-sm);
}
.ask-composer__send:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.ask-composer__send-icon {
  width: 18px;
  height: 18px;
}


.ask-page__text-link {
  background: none;
  border: none;
  padding: 0;
  font: inherit;
  font-size: inherit;
  color: var(--color-accent);
  font-weight: 600;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
  transition: color var(--transition-fast);
}
.ask-page__text-link:hover {
  color: var(--color-accent-hover);
}
.ask-page__notes {
  list-style: none;
  margin: 0;
  padding: 0;
}
.ask-page__note-item {
  font-size: var(--text-sm);
  padding: 10px 14px;
  border-bottom: var(--border-width) solid var(--border-color);
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  margin-bottom: 6px;
  transition: background var(--transition-fast);
}
.ask-page__note-item:hover {
  background: var(--bg-muted);
}
.ask-page__msg-actions {
  display: flex;
  gap: var(--space-md);
  margin-top: var(--space-xs);
}
.ask-page__note-empty {
  margin: 0;
  padding: var(--space-lg);
  text-align: center;
  border: 1px dashed var(--border-color);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  background: var(--bg-elevated);
}
.ask-page__note-empty-title {
  font-weight: 600;
  color: var(--color-text);
}
.ask-page__typing {
  font-size: var(--text-xs);
  color: var(--color-text-dim);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 6px;
}
.ask-page__typing::before {
  content: '';
  display: flex;
  gap: 3px;
}
.ask-page__typing::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-text-dim);
  animation: typing-dot 1.4s infinite ease-in-out;
}
.ask-page__typing::after {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-text-dim);
  animation: typing-dot 1.4s infinite ease-in-out;
  animation-delay: 0.4s;
}
@keyframes typing-dot {
  0%, 80%, 100% {
    opacity: 0.3;
    transform: scale(0.8);
  }
  40% {
    opacity: 1;
    transform: scale(1);
  }
}
</style>

<template>
  <footer class="writer-desk__footer">
    <div class="writer-desk__footer-left">
      <span class="writer-desk__progress">
        📖 已完成 {{ w.overview?.chapters_written || 0 }}/{{ w.overview?.max_chapter || 0 }} 章
      </span>
      <span class="writer-desk__word-count">📝 {{ wordCount }} 字</span>
    </div>
    <div class="writer-desk__footer-right">
      <button
        type="button"
        class="writer-desk__action-btn writer-desk__action-btn--secondary"
        @click="$emit('open-outline')"
      >
        <span>📋</span>
        <span>大纲</span>
      </button>
      <button
        type="button"
        class="writer-desk__action-btn writer-desk__action-btn--secondary"
        @click="$emit('open-stats')"
      >
        <span>📊</span>
        <span>统计</span>
      </button>
      <div class="writer-desk__ai-actions">
        <button
          type="button"
          class="writer-desk__generate-btn"
          :disabled="wb.generateRunning || wb.agent?.generating"
          @click="wb.startQuickWrite?.()"
        >
          <span>✨</span>
          <span>{{ wb.generateRunning ? '生成中…' : 'AI 续写' }}</span>
        </button>
        <div class="writer-desk__ai-action-dropdown">
          <button
            type="button"
            class="writer-desk__ai-action-toggle"
            :disabled="wb.generateRunning || wb.agent?.generating"
            @click="showAiActions = !showAiActions"
          >
            <span>更多</span>
            <span>{{ showAiActions ? '▲' : '▼' }}</span>
          </button>
          <Transition name="slide-down">
            <div v-if="showAiActions" class="writer-desk__ai-action-menu">
              <button
                type="button"
                class="writer-desk__ai-action-item"
                @click="runAiAction('润色')"
              >
                💎 润色
              </button>
              <button
                type="button"
                class="writer-desk__ai-action-item"
                @click="runAiAction('扩充')"
              >
                📝 扩充
              </button>
              <button
                type="button"
                class="writer-desk__ai-action-item"
                @click="runAiAction('精简')"
              >
                ✂️ 精简
              </button>
              <button
                type="button"
                class="writer-desk__ai-action-item"
                @click="runAiAction('续写')"
              >
                ➕ 续写
              </button>
            </div>
          </Transition>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { inject, ref } from 'vue';
import { CREATOR_WRITE_KEY } from './creatorWriteKey.js';

defineEmits(['open-outline', 'open-stats']);

const w = inject(CREATOR_WRITE_KEY);
const wb = w.wb;

const showAiActions = ref(false);
const wordCount = ref(0);

async function runAiAction(actionLabel) {
  showAiActions.value = false;
  await wb.startQuickWrite?.(actionLabel);
}
</script>

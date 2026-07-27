<template>
  <div class="write-workbench__footer">
    <div class="write-workbench__footer-left">
      <span class="write-workbench__progress">📖 已完成 {{ w.overview?.chapters_written || 0 }}/{{ w.overview?.max_chapter || 0 }} 章</span>
      <span class="write-workbench__word-count">📝 {{ wordCount }} 字</span>
      <span class="write-workbench__auto-save" :class="`write-workbench__auto-save--${autoSaveStatus}`">
        <span class="write-workbench__auto-save-icon">
          <span v-if="autoSaveStatus === 'saving'" class="write-workbench__save-spinner"></span>
          <span v-else-if="autoSaveStatus === 'saved'">✓</span>
          <span v-else-if="autoSaveStatus === 'dirty'">•</span>
          <span v-else>!</span>
        </span>
        {{ autoSaveStatus === 'saving' ? '保存中…' : autoSaveStatus === 'saved' ? `已保存 ${formatTime(lastSaveTime)}` : autoSaveStatus === 'dirty' ? '未保存' : '保存失败' }}
      </span>
    </div>
    <div class="write-workbench__footer-right">
      <button
        class="write-workbench__footer-btn write-workbench__footer-btn--primary"
        :class="{ 'write-workbench__footer-btn--loading': w.wb?.generateRunning || w.wb?.agent?.generating }"
        @click="w.wb?.startQuickWrite?.()"
      >
        ✨ {{ w.wb?.generateRunning ? '生成中…' : 'AI 续写' }}
      </button>
      <button class="write-workbench__footer-btn" @click="c?.openExportModal('full')">
        📥 导出
      </button>
      <button class="write-workbench__footer-btn" @click="c?.openPublishWizard">
        🚀 发布
      </button>
    </div>
  </div>
</template>

<script setup>
import { inject, ref, watch, onMounted, onUnmounted } from 'vue';
import { CREATOR_WRITE_KEY } from './creatorWriteKey.js';
import { CREATOR_PAGE_CHROME_KEY } from './creatorPageChromeKey.js';

const w = inject(CREATOR_WRITE_KEY);
const c = inject(CREATOR_PAGE_CHROME_KEY);
const toast = inject('toast', null);

const autoSaveStatus = ref('saved');
const lastSaveTime = ref(null);
const wordCount = ref(0);
let saveTimeout = null;
let contentChangeTimer = null;
let wordCountTimer = null;

function updateWordCount() {
  if (w.chapterBodyDraft && typeof w.chapterBodyDraft === 'string') {
    wordCount.value = w.chapterBodyDraft.replace(/\s/g, '').length;
  } else {
    wordCount.value = 0;
  }
}

function debouncedUpdateWordCount() {
  if (wordCountTimer) clearTimeout(wordCountTimer);
  wordCountTimer = setTimeout(updateWordCount, 300);
}

function formatTime(date) {
  if (!date) return '';
  const now = new Date();
  const diff = now - date;
  if (diff < 1000) return '刚刚';
  if (diff < 60000) return `${Math.floor(diff / 1000)}秒前`;
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
}

function triggerAutoSave() {
  if (saveTimeout) clearTimeout(saveTimeout);
  saveTimeout = setTimeout(async () => {
    autoSaveStatus.value = 'saving';
    try {
      await w.saveChapterBody?.();
      autoSaveStatus.value = 'saved';
      lastSaveTime.value = new Date();
      if (toast) {
        toast.success('✓ 已自动保存');
      }
    } catch (error) {
      autoSaveStatus.value = 'error';
      if (toast) {
        toast.error('保存失败，请重试');
      }
    }
  }, 2000);
}

function handleContentChange() {
  if (autoSaveStatus.value === 'saved') {
    autoSaveStatus.value = 'dirty';
  }
  if (contentChangeTimer) clearTimeout(contentChangeTimer);
  contentChangeTimer = setTimeout(triggerAutoSave, 1500);
}

watch(w.chapterBodyDraft, () => {
  debouncedUpdateWordCount();
  handleContentChange();
});

onMounted(() => {
  lastSaveTime.value = new Date();
  updateWordCount();
});

onUnmounted(() => {
  if (saveTimeout) clearTimeout(saveTimeout);
  if (contentChangeTimer) clearTimeout(contentChangeTimer);
  if (wordCountTimer) clearTimeout(wordCountTimer);
});
</script>
<template>
  <aside class="writer-desk__sidebar" v-show="!wb.leftPanelCollapsed">
    <section class="writer-desk__sidebar-section">
      <h2 class="writer-desk__sidebar-title">章节列表</h2>
      <div class="writer-desk__chapter-list">
        <slot name="chapters" />
      </div>
    </section>

    <section class="writer-desk__sidebar-section">
      <h2 class="writer-desk__sidebar-title">本章意图</h2>
      <input
        v-model="wb.intentText"
        type="text"
        class="writer-desk__intent-input"
        placeholder="本章要写什么…"
      />
      <div class="writer-desk__intent-templates">
        <span class="writer-desk__intent-templates-label">模板：</span>
        <button
          v-for="template in intentTemplates"
          :key="template.id"
          type="button"
          class="writer-desk__intent-template"
          @click="applyIntentTemplate(template.text)"
        >
          {{ template.label }}
        </button>
      </div>
      <div class="writer-desk__mood-tags">
        <span class="writer-desk__tag-group-label">情绪：</span>
        <button
          v-for="tag in moodTags"
          :key="'mood-' + tag"
          type="button"
          class="writer-desk__mood-tag"
          :class="{ 'writer-desk__mood-tag--active': wb.intentMood === tag }"
          @click="wb.intentMood = wb.intentMood === tag ? '' : tag"
        >
          {{ tag }}
        </button>
      </div>
      <div class="writer-desk__type-tags">
        <span class="writer-desk__tag-group-label">类型：</span>
        <button
          v-for="tag in typeTags"
          :key="'type-' + tag"
          type="button"
          class="writer-desk__type-tag"
          :class="{ 'writer-desk__type-tag--active': wb.intentType === tag }"
          @click="wb.intentType = wb.intentType === tag ? '' : tag"
        >
          {{ tag }}
        </button>
      </div>
      <div class="writer-desk__theme-tags">
        <span class="writer-desk__tag-group-label">主题：</span>
        <button
          v-for="tag in themeTags"
          :key="'theme-' + tag"
          type="button"
          class="writer-desk__theme-tag"
          :class="{ 'writer-desk__theme-tag--active': wb.intentTheme === tag }"
          @click="wb.intentTheme = wb.intentTheme === tag ? '' : tag"
        >
          {{ tag }}
        </button>
      </div>
      <div class="writer-desk__intent-history" v-if="wb.intentHistory?.length">
        <h3 class="writer-desk__intent-history-title">意图历史</h3>
        <div class="writer-desk__intent-history-list">
          <button
            v-for="intent in wb.intentHistory"
            :key="intent.id"
            type="button"
            class="writer-desk__intent-history-item"
            @click="wb.loadIntentFromHistory(intent)"
          >
            <span class="writer-desk__intent-history-text">{{ intent.text }}</span>
            <span class="writer-desk__intent-history-meta">
              <span v-if="intent.mood">{{ intent.mood }}</span>
              <span v-if="intent.type">{{ intent.type }}</span>
              <span v-if="intent.theme">{{ intent.theme }}</span>
            </span>
          </button>
        </div>
      </div>
    </section>

    <section class="writer-desk__sidebar-section">
      <h2 class="writer-desk__sidebar-title">写作目标</h2>
      <div class="writer-desk__goal-summary">
        <div class="writer-desk__goal-item">
          <span class="writer-desk__goal-value">{{ progressPercent }}%</span>
          <span class="writer-desk__goal-label">完成进度</span>
        </div>
        <div class="writer-desk__goal-item">
          <span class="writer-desk__goal-value">{{ wordCount }}/{{ targetWordCount }}</span>
          <span class="writer-desk__goal-label">字数目标</span>
        </div>
        <div class="writer-desk__goal-item">
          <span class="writer-desk__goal-value">{{ completedChapters }}/{{ totalChapters }}</span>
          <span class="writer-desk__goal-label">章节进度</span>
        </div>
      </div>
      <div class="writer-desk__goal-progress-bar">
        <div class="writer-desk__goal-progress-fill" :style="{ width: progressPercent + '%', backgroundColor: modeColor }"></div>
      </div>
      <p class="writer-desk__goal-line">{{ wb.goalCardLines.line1 }}</p>
      <p class="writer-desk__goal-line">{{ wb.goalCardLines.line2 }}</p>
    </section>

    <section class="writer-desk__sidebar-section" v-show="wb.creationMode === 'companion'">
      <h2 class="writer-desk__sidebar-title">写作步骤</h2>
      <div class="writer-desk__writing-steps">
        <div
          v-for="step in writingSteps"
          :key="step.id"
          class="writer-desk__writing-step"
          :class="{ 'writer-desk__writing-step--active': currentWritingStep === step.id }"
          :style="currentWritingStep === step.id ? { '--mode-color': modeColor } : {}"
        >
          <span class="writer-desk__writing-step-number">{{ step.number }}</span>
          <span class="writer-desk__writing-step-name">{{ step.name }}</span>
          <span class="writer-desk__writing-step-desc">{{ step.description }}</span>
        </div>
      </div>
    </section>

    <CreatorBatchOperations />
    <CreatorFactoryPipeline />
  </aside>
</template>

<script setup>
import { inject, ref, computed, defineAsyncComponent } from 'vue';
import { CREATOR_WRITE_KEY } from './creatorWriteKey.js';
import CreatorBatchOperations from './CreatorBatchOperations.vue';
const CreatorFactoryPipeline = defineAsyncComponent(() => import('./CreatorFactoryPipeline.vue'));

const w = inject(CREATOR_WRITE_KEY);
const wb = w.wb;

const moodTags = ['克制', '戏剧', '幽默', '抒情'];
const typeTags = ['战斗', '对话', '回忆', '探索', '日常'];
const themeTags = ['成长', '冒险', '爱情', '悬疑', '友情'];
const intentTemplates = [
  { id: 'action', label: '冲突', text: '本章发生一场激烈冲突，主角面临挑战' },
  { id: 'dialogue', label: '对话', text: '本章通过对话揭示人物关系和背景' },
  { id: 'reveal', label: '揭秘', text: '本章揭示一个重要秘密或转折' },
  { id: 'develop', label: '发展', text: '本章推进剧情发展，铺垫后续情节' },
];
const writingSteps = [
  { id: 'conceive', number: '01', name: '构思', description: '确定本章核心意图' },
  { id: 'draft', number: '02', name: '起草', description: '写出初稿内容' },
  { id: 'polish', number: '03', name: '润色', description: '优化语言表达' },
  { id: 'check', number: '04', name: '检查', description: '逻辑与质量检查' },
];
const currentWritingStep = ref('conceive');

const wordCount = ref(0);
const targetWordCount = computed(() => 2000);
const totalChapters = computed(() => w.overview?.max_chapter || 0);
const completedChapters = computed(() => w.overview?.chapters_written || 0);
const progressPercent = computed(() => {
  if (!totalChapters.value) return 0;
  return Math.round((completedChapters.value / totalChapters.value) * 100);
});

const modeColors = {
  companion: '#3b82f6',
  advance: '#7c3aed',
  studio: '#f97316',
};
const modeColor = computed(() => {
  return modeColors[wb.creationMode] || '#3b82f6';
});

function applyIntentTemplate(text) {
  wb.intentText = text;
}
</script>

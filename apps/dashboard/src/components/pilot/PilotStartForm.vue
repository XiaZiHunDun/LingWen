<!--
  PilotStartForm.vue — 启动批章节表单 + Preflight + Start（P1）
-->
<template>
  <section class="pilot-start-form pixel-card" data-testid="pilot-start-form">
    <h2 class="section-title">启动批章节</h2>
    <form class="start-form" @submit.prevent="onStart">
      <div class="form-row">
        <label for="pilot-mode">模式</label>
        <select
          id="pilot-mode"
          v-model="mode"
          data-testid="start-mode"
          class="form-input start-mode pixel-border"
        >
          <option value="canon">canon</option>
          <option value="pilot">pilot</option>
        </select>
      </div>
      <div class="form-row">
        <label for="pilot-from">起始章</label>
        <input
          id="pilot-from"
          v-model.number="startChapter"
          type="number"
          min="1"
          data-testid="start-chapter-from"
          class="form-input start-chapter-from pixel-border"
        />
      </div>
      <div class="form-row">
        <label for="pilot-to">结束章</label>
        <input
          id="pilot-to"
          v-model.number="endChapter"
          type="number"
          min="1"
          data-testid="start-chapter-to"
          class="form-input start-chapter-to pixel-border"
        />
      </div>
      <div class="form-row">
        <label for="pilot-budget">预算 (USD)</label>
        <input
          id="pilot-budget"
          v-model.number="budgetUsd"
          type="number"
          min="0"
          max="100"
          step="0.01"
          data-testid="start-budget-usd"
          class="form-input start-budget-usd pixel-border"
        />
      </div>
      <div class="form-actions">
        <button
          type="button"
          class="run-btn pixel-border preflight-btn"
          data-testid="preflight-btn"
          :disabled="preflightLoading || !isValid"
          @click="onPreflight"
        >
          {{ preflightLoading ? '检查中…' : 'Preflight 检查' }}
        </button>
        <button
          type="button"
          class="run-btn pixel-border start-submit-btn start-btn"
          data-testid="start-submit-btn"
          :disabled="startLoading || !isValid || !preflightAllOk"
          @click="onStart"
        >
          {{ startLoading ? '启动中…' : '启动批处理' }}
        </button>
      </div>
      <p
        v-if="error"
        class="form-error start-form-error"
        data-testid="start-form-error"
        role="alert"
      >
        {{ error }}
      </p>
    </form>
    <PilotPreflightTable :rows="preflightRows" />
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import PilotPreflightTable from './PilotPreflightTable.vue';

interface PreflightRow {
  chapter: number;
  ok: boolean;
  message: string;
}

const props = defineProps<{
  slug: string;
  preflightRows: PreflightRow[];
  preflightLoading: boolean;
  startLoading: boolean;
  error: string | null;
  preflightAllOk?: boolean;
}>();

const emit = defineEmits<{
  'submit-preflight': [payload: { slug: string; start_chapter: number; end_chapter: number }];
  'submit-start': [
    payload: {
      slug: string;
      start_chapter: number;
      end_chapter: number;
      budget_usd: number;
      mode: 'canon' | 'pilot';
    },
  ];
}>();

const mode = ref<'canon' | 'pilot'>('pilot');
const startChapter = ref<number>(1);
const endChapter = ref<number>(10);
const budgetUsd = ref<number>(5);

const isValid = computed(
  () => startChapter.value <= endChapter.value && startChapter.value >= 1,
);

function onPreflight() {
  if (!isValid.value) return;
  emit('submit-preflight', {
    slug: props.slug,
    start_chapter: startChapter.value,
    end_chapter: endChapter.value,
  });
}

function onStart() {
  if (!isValid.value || !props.preflightAllOk) return;
  emit('submit-start', {
    slug: props.slug,
    start_chapter: startChapter.value,
    end_chapter: endChapter.value,
    budget_usd: budgetUsd.value,
    mode: mode.value,
  });
}
</script>

<style scoped>
.pilot-start-form {
  padding: 1rem;
  margin-bottom: 1rem;
}

.start-form {
  display: grid;
  gap: 0.75rem;
  max-width: 400px;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.form-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.form-error {
  color: var(--error, #c33);
  margin-top: 0.5rem;
}

.run-btn {
  padding: 0.4rem 0.8rem;
  cursor: pointer;
}

.run-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}
</style>
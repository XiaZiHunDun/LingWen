<!--
  PilotTemplatePanel.vue — 批量模板（保存 / 应用 / 删除）
  后端 Track B batch templates 的轻量前端消费：把常用批次配置存成模板，一键复用。
  纯展示组件：数据来自 usePilotBatch，动作通过 emit 上抛给页面。
-->
<template>
  <section class="pilot-template-panel pixel-card" data-testid="pilot-template-panel">
    <h2 class="section-title">批量模板</h2>
    <p class="template-hint">把常用批次配置存成模板，下次一键复用。</p>
    <div class="template-row">
      <select
        class="form-input template-select pixel-border"
        data-testid="template-select"
        :value="selectedTemplateId"
        :disabled="loading || !templates.length"
        @change="onSelect"
      >
        <option value="" disabled>{{ templates.length ? '选择模板…' : '暂无模板' }}</option>
        <option
          v-for="t in templates"
          :key="t.template_id"
          :value="t.template_id"
        >
          {{ t.name }}（ch{{ pad(t.start_chapter) }}–ch{{ pad(t.end_chapter) }} · {{ t.mode }}）
        </option>
      </select>
      <button
        type="button"
        class="run-btn pixel-border template-apply template-apply-btn"
        data-testid="template-apply"
        :disabled="!selectedTemplateId"
        @click="onApply"
      >应用</button>
      <button
        type="button"
        class="run-btn pixel-border template-delete template-delete-btn"
        data-testid="template-delete"
        :disabled="!selectedTemplateId"
        @click="onRemove"
      >删除</button>
    </div>
    <div class="template-save-row">
      <template v-if="savingOpen">
        <input
          v-model="saveName"
          class="form-input template-name pixel-border"
          data-testid="template-name"
          placeholder="模板名称"
        />
        <button
          type="button"
          class="run-btn pixel-border template-save-confirm"
          data-testid="template-save-confirm"
          :disabled="saveLoading || !saveName.trim()"
          @click="onSave"
        >{{ saveLoading ? '保存中…' : '保存' }}</button>
        <button
          type="button"
          class="run-btn pixel-border template-save-cancel"
          data-testid="template-save-cancel"
          @click="savingOpen = false"
        >取消</button>
      </template>
      <button
        v-else
        type="button"
        class="run-btn pixel-border template-save template-save-btn"
        data-testid="template-save"
        :disabled="!slug"
        @click="savingOpen = true"
      >保存当前配置</button>
    </div>
    <p
      v-if="message"
      class="template-message template-success"
      data-testid="template-message"
      role="status"
    >{{ message }}</p>
    <p
      v-if="error"
      class="template-message template-error"
      data-testid="template-error"
      role="alert"
    >{{ error }}</p>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import type { StudioBatchTemplateDTO } from '@/api/studio';

const props = defineProps<{
  slug: string;
  templates: StudioBatchTemplateDTO[];
  loading: boolean;
  saveLoading: boolean;
  error: string | null;
  message: string | null;
}>();

const emit = defineEmits<{
  apply: [templateId: string];
  remove: [templateId: string];
  save: [payload: { name: string }];
}>();

const selectedTemplateId = ref('');
const savingOpen = ref(false);
const saveName = ref('');

const selectedTemplate = computed(
  () => props.templates.find((t) => t.template_id === selectedTemplateId.value) ?? null,
);

function pad(n: number): string {
  return String(n).padStart(3, '0');
}

function onSelect(event: Event): void {
  selectedTemplateId.value = (event.target as HTMLSelectElement).value;
}

function onApply(): void {
  if (!selectedTemplate.value) return;
  emit('apply', selectedTemplate.value.template_id);
}

function onRemove(): void {
  if (!selectedTemplate.value) return;
  emit('remove', selectedTemplate.value.template_id);
  selectedTemplateId.value = '';
}

function onSave(): void {
  const name = saveName.value.trim();
  if (!name) return;
  emit('save', { name });
  saveName.value = '';
  savingOpen.value = false;
}
</script>

<style scoped>
.pilot-template-panel {
  padding: 1rem;
  margin-bottom: 1rem;
}

.template-hint {
  color: var(--text-tertiary, #888);
  font-size: var(--text-sm, 13px);
  margin: 0 0 0.5rem;
}

.template-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  max-width: 480px;
}

.template-select {
  flex: 1;
}

.template-save-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-top: 0.5rem;
  max-width: 480px;
}

.template-name {
  flex: 1;
}

.template-message {
  margin-top: 0.5rem;
  font-size: var(--text-sm, 13px);
}

.template-success {
  color: var(--success, #15803d);
}

.template-error {
  color: var(--error, #c33);
}

.run-btn {
  padding: 0.4rem 0.8rem;
  cursor: pointer;
  white-space: nowrap;
}

.run-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}
</style>

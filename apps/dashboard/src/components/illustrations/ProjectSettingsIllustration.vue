<!--
  ProjectSettingsIllustration.vue — 插图偏好（Phase 90 Task 17 + Phase 96 Task 16）

  包含：
  - 默认风格预设（古风水墨 / 现代写实 / 动漫厚涂）
  - 章节完成时自动生成插图 toggle
  - 资产数量上限 number
  - 生成前确认 toggle
  - 默认图片生成器 dropdown（Phase 96：minimax / openai / stability，
    变更后通过 useProjectSettingsStore.save 自动持久化到
    /api/projects/{slug}/settings）

  通过 v-model 双向绑定整组设置；provider 字段额外触发 store.save。
-->
<script setup>
import { useProjectSettingsStore } from '@/stores/useProjectSettings.js'

const props = defineProps({
  modelValue: { type: Object, required: true },
  slug: { type: String, required: true }, // Phase 96: required for provider auto-save
})
const emit = defineEmits(['update:modelValue'])

const store = useProjectSettingsStore()

const presets = [
  { id: 'ink', label: '古风水墨' },
  { id: 'realistic', label: '现代写实' },
  { id: 'anime', label: '动漫厚涂' },
]

const providers = [
  { id: 'minimax', label: 'MiniMax' },
  { id: 'openai', label: 'OpenAI DALL-E 3' },
  { id: 'stability', label: 'Stability SD3' },
]

function update(key, value) {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
}

async function on_provider_change(value) {
  update('default_provider', value)
  await store.save(props.slug, { default_provider: value })
}
</script>

<template>
  <section
    class="illustration-prefs project-settings-illustration"
    data-testid="illustration-prefs"
  >
    <h3 class="section-title project-settings-illustration-title">插图偏好</h3>
    <p class="empty-hint project-settings-illustration-hint-intro">
      章节插图的默认生成策略；v1 仅保留本地偏好，持久化在 v2 接入。
    </p>

    <div class="field project-settings-illustration-field">
      <p class="label project-settings-illustration-label">默认风格</p>
      <div class="presets project-settings-illustration-presets">
        <button
          v-for="p in presets"
          :key="p.id"
          type="button"
          :class="['preset', `project-settings-illustration-preset-${p.id}`, { selected: modelValue.style_preset === p.id }]"
          :data-testid="`project-settings-illustration-default-style-${p.id}`"
          @click="update('style_preset', p.id)"
        >
          {{ p.label }}
        </button>
      </div>
    </div>

    <div class="field project-settings-illustration-field project-settings-illustration-toggle">
      <label class="project-settings-illustration-toggle-label-auto">
        <input
          type="checkbox"
          class="project-settings-illustration-toggle-input project-settings-illustration-auto-generate"
          :checked="modelValue.auto_generate"
          data-testid="project-settings-illustration-auto-generate"
          @change="update('auto_generate', $event.target.checked)"
        />
        章节完成时自动生成插图
      </label>
      <p class="empty-hint project-settings-illustration-hint">每章约消耗 1 次 LLM 调用 + 1 次图片生成</p>
    </div>

    <div class="field project-settings-illustration-field">
      <label class="project-settings-illustration-label" for="project-settings-illustration-default-provider">
        默认图片生成器
      </label>
      <select
        id="project-settings-illustration-default-provider"
        class="project-settings-illustration-provider-select"
        :value="modelValue.default_provider || 'minimax'"
        data-testid="project-settings-illustration-default-provider"
        @change="on_provider_change($event.target.value)"
      >
        <option v-for="p in providers" :key="p.id" :value="p.id">
          {{ p.label }}
        </option>
      </select>
    </div>

    <div class="field project-settings-illustration-field">
      <label class="project-settings-illustration-label" for="project-settings-illustration-max-assets">
        资产数量上限
      </label>
      <input
        id="project-settings-illustration-max-assets"
        type="number"
        class="project-settings-illustration-max-input project-settings-illustration-max-assets"
        :value="modelValue.max_assets"
        data-testid="project-settings-illustration-max-assets"
        min="0"
        max="1000"
        step="1"
        @input="update('max_assets', parseInt($event.target.value, 10))"
      />
    </div>

    <div class="field project-settings-illustration-field project-settings-illustration-toggle">
      <label class="project-settings-illustration-toggle-label-confirm">
        <input
          type="checkbox"
          class="project-settings-illustration-toggle-input project-settings-illustration-confirm"
          :checked="modelValue.confirm_before_generate"
          data-testid="project-settings-illustration-confirm"
          @change="update('confirm_before_generate', $event.target.checked)"
        />
        生成前确认
      </label>
    </div>
  </section>
</template>

<style scoped>
.project-settings-illustration {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  max-width: 520px;
}

.project-settings-illustration-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.project-settings-illustration-label {
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  color: var(--color-text);
  margin: 0;
}

.project-settings-illustration-presets {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.project-settings-illustration-preset-ink,
.project-settings-illustration-preset-realistic,
.project-settings-illustration-preset-anime {
  padding: 6px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
  cursor: pointer;
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  color: var(--color-text);
}

.project-settings-illustration-preset-ink.selected,
.project-settings-illustration-preset-realistic.selected,
.project-settings-illustration-preset-anime.selected {
  border: 2px solid var(--color-accent);
  background: var(--bg-muted);
}

.project-settings-illustration-toggle-label-auto,
.project-settings-illustration-toggle-label-confirm {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  cursor: pointer;
}

.project-settings-illustration-max-input {
  font-size: var(--text-sm);
  font-family: var(--font-mono);
  padding: 6px 8px;
  background: var(--bg-primary);
  width: 120px;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-sm);
}
</style>
<!--
  GenerateIllustrationDialog.vue — Phase 90 (cover/chapter illustration dialog)
  + Phase 96 (provider dropdown) + Phase 97 (reference image toggle) +
  Phase 98 (confirm_before_generate) + Phase 100 (model picker).

  Phase 100 Task 9: model picker appears after provider selection.
  Catalog fetched via fetchProviderModels(provider); options filtered by
  provider; default selection = project default_models[provider] (if set
  and in catalog) else adapter.default_model. Disabled when
  use_project_reference=true (i2i path ignores model in v1).
-->
<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { NDialog, NButton, NInput } from 'naive-ui'
import { useProjectSettingsStore } from '@/stores/useProjectSettings.js'
import { fetchProviderModels } from '@/api/illustrations'

const props = defineProps({
  projectSlug: { type: String, required: true },
  chapterNum: { type: Number, default: null },
  type: { type: String, default: 'chapter' },
  modelValue: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'generate'])

const presets = [
  { id: 'ink', label: '古风水墨', icon: '🏯' },
  { id: 'realistic', label: '现代写实', icon: '📷' },
  { id: 'anime', label: '动漫厚涂', icon: '🎨' },
]

const providers = [
  { id: 'minimax', label: 'MiniMax' },
  { id: 'openai', label: 'OpenAI DALL-E 3' },
  { id: 'stability', label: 'Stability SD3' },
]

const store = useProjectSettingsStore()

const selectedPreset = ref('ink')
const customPrompt = ref('')
const selectedProvider = ref('minimax')  // NEW (Phase 96)
const useProjectReference = ref(true)
const perCallFile = ref(null)

// Phase 100 Task 9: model picker state.
const modelCatalog = ref(null)  // { provider, models: string[], default_model: string } | null
const selectedModel = ref('')

const availableModels = computed(() => modelCatalog.value?.models || [])

const projectDefaultHint = computed(() => {
  if (!modelCatalog.value) return ''
  const projDefault = store.settings?.default_models?.[selectedProvider.value]
  if (projDefault && projDefault !== selectedModel.value) {
    return projDefault
  }
  return modelCatalog.value.default_model
})

watch(selectedProvider, (newVal) => {
  if (newVal === 'openai' && useProjectReference.value) {
    useProjectReference.value = false
  }
})

// Phase 100 Task 9: fetch catalog when provider changes; default selection =
// project override (if in catalog) else adapter.default_model.
watch(selectedProvider, async (newProvider) => {
  if (!newProvider) {
    modelCatalog.value = null
    selectedModel.value = ''
    return
  }
  try {
    const catalog = await fetchProviderModels(newProvider)
    modelCatalog.value = catalog
    const projDefault = store.settings?.default_models?.[newProvider]
    if (projDefault && catalog.models.includes(projDefault)) {
      selectedModel.value = projDefault
    } else {
      selectedModel.value = catalog.default_model
    }
  } catch {
    modelCatalog.value = null
    selectedModel.value = ''
  }
}, { immediate: true })

// Preselect from project default on mount
onMounted(async () => {
  if (props.projectSlug) {
    await store.fetch(props.projectSlug)
    if (store.settings?.default_provider) {
      selectedProvider.value = store.settings.default_provider
    }
  }
})

const isValid = computed(() => selectedPreset.value !== null)

function onPerCallFileChange(event) {
  perCallFile.value = (event.target.files && event.target.files[0]) || null
  if (perCallFile.value) {
    useProjectReference.value = false
  }
}

function close() {
  emit('update:modelValue', false)
}

function submit() {
  if (!isValid.value) return

  // Phase 98: confirm_before_generate check (front-end only — backend
  // audit log records bypassed state but doesn't reject).
  if (store.settings?.confirm_before_generate) {
    const provider = store.settings.default_provider || selectedProvider.value
    const ok = window.confirm(`将使用 ${provider} 生成插图。继续？`)
    if (!ok) return
  }

  emit('generate', {
    type: props.type,
    chapter_num: props.chapterNum,
    style_preset: selectedPreset.value,
    custom_prompt: customPrompt.value || null,
    provider: selectedProvider.value,  // NEW (Phase 96). Per-call override.
    // Phase 100 Task 9: model selection. null when catalog not loaded or
    // i2i path (backend falls back to adapter default).
    model: selectedModel.value || null,
    use_project_reference: useProjectReference.value,
    per_call_reference: perCallFile.value,
  })
  close()
}

// Expose for tests
defineExpose({ selectedPreset, customPrompt, selectedProvider, store, useProjectReference, perCallFile, selectedModel, modelCatalog })
</script>

<template>
  <NDialog
    :show="modelValue"
    @update:show="emit('update:modelValue', $event)"
    preset="card"
    title="生成插图"
    style="max-width: 520px"
  >
    <div class="form">
      <p class="label">风格预设</p>
      <div class="presets">
        <button
          v-for="p in presets"
          :key="p.id"
          :class="['preset', 'style-preset-' + p.id, { selected: selectedPreset === p.id }]"
          :data-testid="`style-preset-${p.id}`"
          @click="selectedPreset = p.id"
          type="button"
        >
          <span class="icon">{{ p.icon }}</span>
          <span class="name">{{ p.label }}</span>
        </button>
      </div>

      <p class="label">图片生成器</p>
      <div class="providers">
        <button
          v-for="p in providers"
          :key="p.id"
          type="button"
          :class="['provider', 'provider-' + p.id, { selected: selectedProvider === p.id }]"
          :data-testid="`illustration-provider-${p.id}`"
          @click="selectedProvider = p.id"
        >
          {{ p.label }}
        </button>
      </div>

      <!-- Phase 100 Task 9: model picker — filtered by selectedProvider. -->
      <div
        v-if="modelCatalog"
        class="model-row generate-illustration-model-row"
        data-testid="model-row"
      >
        <label for="model-select" class="model-label">模型</label>
        <select
          id="model-select"
          data-testid="model-select"
          v-model="selectedModel"
          :disabled="useProjectReference"
          class="model-select"
        >
          <option v-for="m in availableModels" :key="m" :value="m">{{ m }}</option>
        </select>
        <small
          v-if="projectDefaultHint"
          class="hint generate-illustration-model-hint"
          data-testid="model-hint"
        >
          默认: {{ projectDefaultHint }}
        </small>
      </div>

      <p class="label">参考图（可选）</p>
      <div class="reference-options">
        <label class="reference-option-label">
          <input
            type="checkbox"
            :disabled="selectedProvider === 'openai'"
            :checked="useProjectReference"
            data-testid="dialog-use-project-reference"
            @change="useProjectReference = $event.target.checked"
          />
          使用项目默认参考图
        </label>
        <input
          type="file"
          accept="image/jpeg,image/png"
          data-testid="dialog-per-call-reference"
          @change="onPerCallFileChange"
        />
        <p
          v-if="selectedProvider === 'openai' && (useProjectReference || perCallFile)"
          class="warning"
          data-testid="dialog-openai-warning"
        >
          OpenAI DALL-E 3 不支持参考图，已自动取消
        </p>
      </div>

      <p class="label">补充描述（可选）</p>
      <NInput
        v-model:value="customPrompt"
        placeholder="e.g. 远景镜头、林渊侧脸、雾气弥漫"
        type="text"
      />

      <p class="label">使用上下文</p>
      <div class="context">
        ✓ 章节文本（{{ chapterNum ? `第 ${chapterNum} 章` : '封面' }}）<br>
        ✓ 角色档案（自动加载）<br>
        <span class="hint">→ 提取后显示预览</span>
      </div>
    </div>

    <template #action>
      <NButton @click="close">取消</NButton>
      <NButton
        type="primary"
        :disabled="!isValid"
        class="generate-submit"
        data-testid="generate-submit"
        @click="submit"
      >
        开始生成
      </NButton>
    </template>
  </NDialog>
</template>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.label {
  font-size: 12px;
  text-transform: uppercase;
  color: var(--text-muted, #4b5563);
  margin: 0 0 8px 0;
}
.presets {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}
.preset {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px;
  border: 2px solid var(--border-color, #e5e7eb);
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
  color: inherit;
}
.preset.selected {
  border-color: var(--color-accent, #7c3aed);
  background: var(--color-accent-soft, rgba(124, 58, 237, 0.08));
}
.preset .icon { font-size: 24px; }
.preset .name { font-size: 12px; }
.providers {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.provider {
  padding: 8px 14px;
  border: 2px solid var(--border-color, #e5e7eb);
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
  color: inherit;
  font-size: 13px;
}
.provider.selected {
  border-color: var(--color-accent, #7c3aed);
  background: var(--color-accent-soft, rgba(124, 58, 237, 0.08));
}
.context {
  font-size: 12px;
  color: var(--text-muted, #4b5563);
  line-height: 1.6;
}
.hint { color: var(--color-accent, #7c3aed); }
.reference-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.reference-option-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}
.warning {
  font-size: 12px;
  color: #dc2626;
  margin: 0;
}

/* Phase 100 Task 9: model picker. */
.generate-illustration-model-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  flex-wrap: wrap;
}
.generate-illustration-model-row .model-label {
  font-size: 12px;
  text-transform: uppercase;
  color: var(--text-muted, #4b5563);
  min-width: 56px;
}
.generate-illustration-model-row .model-select {
  padding: 6px 8px;
  border: 1px solid var(--border-color, #e5e7eb);
  border-radius: 6px;
  background: transparent;
  color: inherit;
  font-size: 13px;
  min-width: 200px;
  font-family: var(--font-mono, monospace);
}
.generate-illustration-model-row .model-select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.generate-illustration-model-hint {
  font-size: 12px;
  color: var(--text-muted, #4b5563);
}
</style>
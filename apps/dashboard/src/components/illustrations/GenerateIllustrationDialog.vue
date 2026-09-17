<script setup>
import { ref, computed, onMounted } from 'vue'
import { NDialog, NButton, NInput } from 'naive-ui'
import { useProjectSettingsStore } from '@/stores/useProjectSettings.js'

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

function close() {
  emit('update:modelValue', false)
}

function submit() {
  if (!isValid.value) return
  emit('generate', {
    type: props.type,
    chapter_num: props.chapterNum,
    style_preset: selectedPreset.value,
    custom_prompt: customPrompt.value || null,
    provider: selectedProvider.value,  // NEW (Phase 96). Per-call override.
  })
  close()
}

// Expose for tests
defineExpose({ selectedPreset, customPrompt, selectedProvider, store })
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
</style>
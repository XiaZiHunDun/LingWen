<!--
  ProjectSettingsIllustration.vue — 插图偏好（Phase 90 Task 17 + Phase 96 Task 16 + Phase 97 Task 10 + Phase 98 Task 13 + Phase 100 Task 8 + Phase 102 Task 9 + Phase 102 Task 10）

  包含：
  - 默认风格预设（古风水墨 / 现代写实 / 动漫厚涂）
  - 章节完成时自动生成插图 toggle
  - 资产数量上限 number
  - 生成前确认 toggle
  - 默认图片生成器 dropdown（Phase 96：minimax / openai / stability，
    变更后通过 useProjectSettingsStore.save 自动持久化到
    /api/projects/{slug}/settings）
  - 项目参考图上传 (Phase 97: ReferenceImageUpload 子组件，
    参考图与 provider 概念相关 — i2i 仅 MiniMax / Stability 支持 — 因此放在
    provider 之前；放在 max_assets 之后以便字段视觉分组 [风格 / 自动 / 参考图 /
    provider / 上限 / 确认])
  - Phase 100 Task 8: 每个 provider 的默认模型 dropdown（3 个 select），
    模型列表从 GET /api/illustrations/providers/{name}/models 拉取，
    "Provider 默认" sentinel 选项（空串）表示回退到 adapter 自身的
    default_model。整组 dict 持久化到 default_models 字段。
  - Phase 101: fallback_chain 多选 — 主 provider 失败时按序尝试。
  - Phase 102 Task 9: fallback_models — 每个 provider 在 fallback chain
    retry 路径使用的模型 dropdown（mirror default_models 模式，整组 dict
    持久化到 fallback_models 字段）。主路径仍用 default_models[provider]。
  - Phase 102 Task 10: chapter_overrides — per-chapter 子集覆写
    (dict[chapter_num, subset])，逐章覆盖 max_assets / confirm_before_generate /
    auto_generate / fallback_chain 中任意子集；存到 chapter_overrides 字段。

  Phase 98 Task 13: update() 现在 emit + save (Phase 96 只对 provider save)。
  三个新字段 (auto_generate / max_assets / confirm_before_generate) 现在持久化
  到 backend。on_provider_change 简化为 update() 调用（去重复）。

  Phase 100 Task 8: 新增 update_model_default(provider, model) — 切换单 provider
  选择后立刻持久化 dict；'' 表示 sentinel（被持久化为不含该 provider 的 dict）。

  Phase 102 Task 9: 新增 update_fallback_model_default(provider, model) — 与
  update_model_default 同 shape，但写入 fallback_models 字段。仅在 provider
  被 fallback chain 调起时由 pipeline.resolve_model(is_fallback=True) 优先
  读取 (packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py
  resolve_model:108-141)；主路径仍用 default_models[provider]。
-->
<script setup>
import { ref, onMounted } from 'vue'
import { useProjectSettingsStore } from '@/stores/useProjectSettings.js'
import { fetchProviderModels } from '@/api/illustrations'
import ReferenceImageUpload from './ReferenceImageUpload.vue'

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

// Phase 100 Task 8: per-provider model catalogs + selected overrides.
const modelCatalogs = ref({}) // { provider: { models: string[], default_model: string } | null }
const selectedModels = ref({}) // { provider: string } — '' means "use provider default"

// Phase 102 Task 9: per-provider model override for fallback chain retry path.
// Same shape as selectedModels but written to `fallback_models` field. Pipeline
// reads fallback_models[provider] ONLY when is_fallback=True (chain retry).
const selectedFallbackModels = ref({}) // { provider: string }

onMounted(async () => {
  // Pre-populate selectedModels from current settings (defaults may be empty
  // string sentinel or an explicit model id).
  const currentDefaults = props.modelValue?.default_models || {}
  for (const p of providers) {
    const existing = currentDefaults[p.id]
    selectedModels.value[p.id] = typeof existing === 'string' ? existing : ''
  }

  // Phase 102 Task 9: pre-populate fallback model overrides from settings.
  // Empty dict means "no override" — pipeline falls back to default_models.
  const currentFallbackModels = props.modelValue?.fallback_models || {}
  for (const p of providers) {
    const existing = currentFallbackModels[p.id]
    selectedFallbackModels.value[p.id] = typeof existing === 'string' ? existing : ''
  }

  // Fetch each provider's model catalog in parallel — catalogs are independent.
  await Promise.all(
    providers.map(async (p) => {
      try {
        modelCatalogs.value[p.id] = await fetchProviderModels(p.id)
      } catch {
        // Best-effort: if a provider's catalog fetch fails (e.g. backend down
        // for one adapter), leave that dropdown empty rather than blocking the
        // whole settings panel.
        modelCatalogs.value[p.id] = null
      }
    }),
  )
})

async function update(key, value) {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
  await store.save(props.slug, { [key]: value })
}

async function update_model_default(provider, model) {
  // Sentinel '' is dropped from the saved dict so the backend falls back to
  // adapter.default_model.
  const next = { ...selectedModels.value, [provider]: model }
  selectedModels.value = next
  const filtered = Object.fromEntries(
    Object.entries(next).filter(([, v]) => v !== ''),
  )
  await update('default_models', filtered)
}

// Phase 102 Task 9: parallel of update_model_default for fallback chain retry
// path. Sentinel '' is dropped so the backend pipeline falls back to
// default_models[provider] (which in turn falls back to adapter.default_model).
async function update_fallback_model_default(provider, model) {
  const next = { ...selectedFallbackModels.value, [provider]: model }
  selectedFallbackModels.value = next
  const filtered = Object.fromEntries(
    Object.entries(next).filter(([, v]) => v !== ''),
  )
  await update('fallback_models', filtered)
}

// Phase 102 Task 10: chapter_overrides row helpers.
// chapter_overrides is dict[chapter_num, subset-of-overridable-fields].
// Backend pipeline merges per-chapter subset onto base settings at request time
// (overrides win on conflict). Subset fields are whitelisted on the backend
// (_CHAPTER_OVERRIDABLE_FIELDS in
// apps/studio_api/routes/project_settings.py:35-37): max_assets /
// confirm_before_generate / auto_generate / fallback_chain.

// Compute the next available chapter number for "+ Add chapter" — keep it
// monotonic vs. existing keys so the user can keep clicking without collision.
function next_chapter_number() {
  const existing = Object.keys(props.modelValue?.chapter_overrides || {}).map(
    (k) => Number(k),
  )
  if (existing.length === 0) return 1
  return Math.max(...existing) + 1
}

async function addChapterOverrideRow() {
  const overrides = { ...(props.modelValue?.chapter_overrides || {}) }
  // Skip if next number already exists (defensive — should not happen).
  const next = next_chapter_number()
  if (Object.prototype.hasOwnProperty.call(overrides, String(next))) return
  overrides[next] = {}
  await update('chapter_overrides', overrides)
}

async function removeChapterOverrideRow(chapter) {
  const overrides = { ...(props.modelValue?.chapter_overrides || {}) }
  delete overrides[chapter]
  await update('chapter_overrides', overrides)
}

async function updateChapterOverrideChapter(oldChapter, newChapterRaw) {
  const newChapter = Number(newChapterRaw)
  if (!Number.isInteger(newChapter) || newChapter < 0) return
  const overrides = { ...(props.modelValue?.chapter_overrides || {}) }
  // Collision check: if newChapter key already exists (different from oldChapter),
  // refuse to clobber — let the user clear the existing row first.
  if (
    newChapter !== oldChapter &&
    Object.prototype.hasOwnProperty.call(overrides, String(newChapter))
  ) {
    return
  }
  const subset = overrides[oldChapter]
  delete overrides[oldChapter]
  overrides[newChapter] = subset ?? {}
  await update('chapter_overrides', overrides)
}

async function updateChapterOverrideField(chapter, field, value) {
  const overrides = { ...(props.modelValue?.chapter_overrides || {}) }
  const subset = { ...(overrides[chapter] || {}) }
  if (
    value === '' ||
    value === null ||
    value === undefined ||
    (Array.isArray(value) && value.length === 0)
  ) {
    // Empty sentinel — drop the field from the subset so backend sees
    // "no override for this field" (it then falls back to base settings).
    delete subset[field]
  } else if (field === 'max_assets') {
    // max_assets is a number — coerce after the sentinel check so that an
    // empty input (Number('') === 0) is treated as "drop override" rather
    // than persisting 0 to the backend.
    const num = Number(value)
    if (Number.isFinite(num)) {
      subset[field] = num
    } else {
      delete subset[field]
    }
  } else if (field === 'confirm_before_generate' || field === 'auto_generate') {
    subset[field] = Boolean(value)
  } else if (field === 'fallback_chain') {
    subset[field] = Array.isArray(value) ? value : [value]
  } else {
    subset[field] = value
  }
  overrides[chapter] = subset
  await update('chapter_overrides', overrides)
}

const on_provider_change = (value) => update('default_provider', value)

// Phase 101: collect selected options from native multi-select change event.
const on_fallback_chain_change = (event) => {
  const selected = Array.from(event.target.selectedOptions).map((o) => o.value)
  update('fallback_chain', selected)
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

    <ReferenceImageUpload :slug="props.slug" />

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

    <!-- Phase 100 Task 8: per-provider default model dropdowns.
         Each select shows the adapter's model catalog with a "Provider 默认"
         sentinel option (empty string) that resets to adapter.default_model
         on the backend. -->
    <div
      class="field project-settings-illustration-field project-settings-illustration-models"
      data-testid="default-models-section"
    >
      <p class="label project-settings-illustration-label">默认模型 (按 provider)</p>
      <div
        v-for="p in providers"
        :key="`model-default-${p.id}`"
        class="model-row project-settings-illustration-model-row"
      >
        <label
          class="project-settings-illustration-model-label"
          :for="`default-model-${p.id}`"
        >
          {{ p.label }}
        </label>
        <select
          :id="`default-model-${p.id}`"
          :data-testid="`default-model-${p.id}`"
          :value="selectedModels[p.id] || ''"
          class="project-settings-illustration-model-select"
          @change="update_model_default(p.id, $event.target.value)"
        >
          <option value="">Provider 默认</option>
          <option
            v-for="m in (modelCatalogs[p.id] && modelCatalogs[p.id].models) || []"
            :key="m"
            :value="m"
          >
            {{ m }}
          </option>
        </select>
      </div>
    </div>

    <!-- Phase 101: fallback chain multi-select. Empty chain = no fallback.
         When non-empty, the pipeline tries each provider in order if the
         primary fails with a transient error (5xx / 429 / timeout). -->
    <div class="field project-settings-illustration-field">
      <label
        class="project-settings-illustration-label"
        for="project-settings-illustration-fallback-chain"
      >
        Fallback Chain
      </label>
      <select
        id="project-settings-illustration-fallback-chain"
        class="project-settings-illustration-fallback-chain-select"
        multiple
        :value="modelValue.fallback_chain || []"
        data-testid="project-settings-illustration-fallback-chain"
        @change="on_fallback_chain_change($event)"
      >
        <option v-for="p in providers" :key="p.id" :value="p.id">
          {{ p.label }}
        </option>
      </select>
      <p class="empty-hint project-settings-illustration-hint">
        主 provider 失败时按序尝试。可留空（仅主 provider）。
      </p>
    </div>

    <!-- Phase 102 Task 9: per-provider model override for fallback chain retry
         path. Mirrors the default_models section above but writes to
         `fallback_models` field. Pipeline.resolve_model(is_fallback=True) reads
         fallback_models[provider] FIRST, falling back to default_models[provider]
         only when fallback_models[provider] is absent (see
         packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py
         resolve_model:108-141). "Provider 默认" sentinel ('') means "no
         fallback override" — pipeline uses default_models[provider]. -->
    <div
      class="field project-settings-illustration-field project-settings-illustration-models"
      data-testid="fallback-models-section"
    >
      <p class="label project-settings-illustration-label">
        Fallback 模型 (按 provider)
      </p>
      <div
        v-for="p in providers"
        :key="`fallback-model-default-${p.id}`"
        class="model-row project-settings-illustration-model-row"
      >
        <label
          class="project-settings-illustration-model-label"
          :for="`fallback-model-${p.id}`"
        >
          {{ p.label }}
        </label>
        <select
          :id="`fallback-model-${p.id}`"
          :data-testid="`fallback-model-${p.id}`"
          :value="selectedFallbackModels[p.id] || ''"
          class="project-settings-illustration-model-select"
          @change="update_fallback_model_default(p.id, $event.target.value)"
        >
          <option value="">Provider 默认</option>
          <option
            v-for="m in (modelCatalogs[p.id] && modelCatalogs[p.id].models) || []"
            :key="m"
            :value="m"
          >
            {{ m }}
          </option>
        </select>
      </div>
      <p class="empty-hint project-settings-illustration-hint">
        仅当该 provider 通过 fallback chain 调起时生效。主路径仍用默认模型。
      </p>
    </div>

    <!-- Phase 102 Task 10: chapter_overrides — per-chapter subset merge.
         dict[chapter_num, subset-of-overridable-fields] where the subset is
         any combination of max_assets / confirm_before_generate / auto_generate
         / fallback_chain. Backend pipeline.merge_chapter_settings() merges each
         chapter's subset onto base settings at request time (overrides win).
         Add row appends next monotonic chapter number; remove deletes the row.
         Editing chapter-num renames the dict key (with collision check); editing
         a field within a row updates only that field in the subset (empty value
         drops the field from the subset so backend falls back to base). -->
    <div
      class="field project-settings-illustration-field project-settings-illustration-chapter-overrides"
      data-testid="chapter-overrides-section"
    >
      <p class="label project-settings-illustration-label">章节覆写</p>
      <p class="empty-hint project-settings-illustration-hint">
        按章节覆盖部分字段；留空表示沿用上方默认值。
      </p>
      <table
        class="project-settings-illustration-chapter-overrides-table"
        data-testid="chapter-overrides-table"
      >
        <thead>
          <tr>
            <th>章节</th>
            <th>max_assets</th>
            <th>confirm</th>
            <th>auto</th>
            <th>fallback_chain</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="chapter in Object.keys(props.modelValue?.chapter_overrides || {}).sort(
              (a, b) => Number(a) - Number(b)
            )"
            :key="chapter"
            :data-testid="`chapter-override-row-${chapter}`"
            class="project-settings-illustration-chapter-override-row"
          >
            <td>
              <input
                type="number"
                class="project-settings-illustration-chapter-override-chapter-num"
                :value="chapter"
                :min="0"
                :step="1"
                :data-testid="`chapter-override-chapter-num-${chapter}`"
                @change="updateChapterOverrideChapter(chapter, $event.target.value)"
              />
            </td>
            <td>
              <input
                type="number"
                class="project-settings-illustration-chapter-override-max-assets"
                :value="(props.modelValue?.chapter_overrides?.[chapter]?.max_assets) ?? ''"
                :min="0"
                :step="1"
                :data-testid="`chapter-override-max-assets-${chapter}`"
                @change="updateChapterOverrideField(chapter, 'max_assets', $event.target.value)"
              />
            </td>
            <td>
              <input
                type="checkbox"
                class="project-settings-illustration-chapter-override-confirm"
                :checked="
                  !!props.modelValue?.chapter_overrides?.[chapter]?.confirm_before_generate
                "
                :data-testid="`chapter-override-confirm-${chapter}`"
                @change="
                  updateChapterOverrideField(
                    chapter,
                    'confirm_before_generate',
                    $event.target.checked
                  )
                "
              />
            </td>
            <td>
              <input
                type="checkbox"
                class="project-settings-illustration-chapter-override-auto"
                :checked="
                  !!props.modelValue?.chapter_overrides?.[chapter]?.auto_generate
                "
                :data-testid="`chapter-override-auto-generate-${chapter}`"
                @change="
                  updateChapterOverrideField(
                    chapter,
                    'auto_generate',
                    $event.target.checked
                  )
                "
              />
            </td>
            <td>
              <input
                type="text"
                class="project-settings-illustration-chapter-override-fallback-chain"
                :value="
                  (
                    props.modelValue?.chapter_overrides?.[chapter]?.fallback_chain || []
                  ).join(',')
                "
                placeholder="(use default)"
                :data-testid="`chapter-override-fallback-chain-${chapter}`"
                @change="
                  updateChapterOverrideField(
                    chapter,
                    'fallback_chain',
                    $event.target.value
                      .split(',')
                      .map((s) => s.trim())
                      .filter(Boolean)
                  )
                "
              />
            </td>
            <td>
              <button
                type="button"
                class="project-settings-illustration-chapter-override-remove"
                :data-testid="`chapter-override-remove-${chapter}`"
                @click="removeChapterOverrideRow(chapter)"
              >×</button>
            </td>
          </tr>
        </tbody>
      </table>
      <button
        type="button"
        class="project-settings-illustration-add-chapter-override"
        data-testid="add-chapter-override"
        @click="addChapterOverrideRow"
      >+ Add chapter</button>
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

/* Phase 100 Task 8: per-provider model defaults. */
.project-settings-illustration-models {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.project-settings-illustration-model-row {
  display: grid;
  grid-template-columns: 140px 1fr;
  align-items: center;
  gap: var(--space-xs);
}

.project-settings-illustration-model-label {
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  color: var(--color-text-muted, #4b5563);
}

.project-settings-illustration-model-select {
  font-size: var(--text-sm);
  font-family: var(--font-mono);
  padding: 6px 8px;
  background: var(--bg-primary);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-sm);
  min-width: 180px;
}

/* Phase 102 Task 10: chapter_overrides table. */
.project-settings-illustration-chapter-overrides {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.project-settings-illustration-chapter-overrides-table {
  border-collapse: collapse;
  width: 100%;
  font-size: var(--text-sm);
  font-family: var(--font-ui);
}

.project-settings-illustration-chapter-overrides-table th,
.project-settings-illustration-chapter-overrides-table td {
  border: var(--border-width) solid var(--border-color);
  padding: 4px 6px;
  text-align: left;
  vertical-align: middle;
}

.project-settings-illustration-chapter-overrides-table th {
  font-weight: 600;
  color: var(--color-text-muted, #4b5563);
  background: var(--bg-muted);
}

.project-settings-illustration-chapter-override-chapter-num,
.project-settings-illustration-chapter-override-max-assets {
  width: 70px;
  font-family: var(--font-mono);
  padding: 4px 6px;
  background: var(--bg-primary);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-sm);
}

.project-settings-illustration-chapter-override-fallback-chain {
  width: 160px;
  font-family: var(--font-mono);
  padding: 4px 6px;
  background: var(--bg-primary);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-sm);
}

.project-settings-illustration-chapter-override-remove {
  cursor: pointer;
  background: transparent;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: 2px 8px;
  font-size: var(--text-sm);
  color: var(--color-text-muted, #4b5563);
}

.project-settings-illustration-chapter-override-remove:hover {
  color: var(--color-accent);
  border-color: var(--color-accent);
}

.project-settings-illustration-add-chapter-override {
  align-self: flex-start;
  padding: 4px 10px;
  background: var(--bg-primary);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  color: var(--color-text);
}

.project-settings-illustration-add-chapter-override:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}
</style>

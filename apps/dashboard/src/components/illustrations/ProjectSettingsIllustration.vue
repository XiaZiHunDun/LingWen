<!--
  ProjectSettingsIllustration.vue — 插图偏好（Phase 90 Task 17 + Phase 96 Task 16 + Phase 97 Task 10 + Phase 98 Task 13 + Phase 100 Task 8 + Phase 102 Task 9 + Phase 102 Task 10 + Phase 102 Task 11 + Phase 103 Task 8）

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
  - Phase 102 Task 11: notify_threshold slider — 连续失败次数达到阈值后
    触发 warning 通知（1-10，默认 3，counter 在下次成功时重置）。
  - Phase 103 Task 8: chapter_overrides.default_models — per-chapter
    provider→model 映射表（在 chapter_overrides 表新增列）；cascade picker
    每行一对 (provider select + model select + ×)，+ Add 行追加第一 provider
    的 default_model。

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

  Phase 103 Task 8: 新增 addChapterDefaultModel / removeChapterDefaultModel /
  updateChapterDefaultModel — 与 chapter_overrides 行 helpers 同样 shape，
  但写入 chapter_overrides[chapter].default_models 子字段，触发 update()。
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

// Phase 103: per-chapter default_models provider-model pairs. Each chapter's
// default_models is dict[provider, model] (same shape as the project-level
// default_models); pipeline.merge_chapter_settings() merges it onto base
// settings at request time (override wins on conflict).
async function addChapterDefaultModel(chapter, provider) {
  const overrides = { ...(props.modelValue?.chapter_overrides || {}) }
  const existing = { ...(overrides[chapter] || {}) }
  const currentDefaultModels = { ...(existing.default_models || {}) }
  // Pull the provider's default model from the cached modelCatalogs — same
  // source the project-level default_models dropdown uses.
  const catalog = modelCatalogs.value[provider]
  const defaultModel = catalog?.default_model || ''
  currentDefaultModels[provider] = defaultModel
  overrides[chapter] = { ...existing, default_models: currentDefaultModels }
  await update('chapter_overrides', overrides)
}

async function removeChapterDefaultModel(chapter, provider) {
  const overrides = { ...(props.modelValue?.chapter_overrides || {}) }
  const existing = { ...(overrides[chapter] || {}) }
  const currentDefaultModels = { ...(existing.default_models || {}) }
  delete currentDefaultModels[provider]
  overrides[chapter] = { ...existing, default_models: currentDefaultModels }
  await update('chapter_overrides', overrides)
}

async function updateChapterDefaultModel(chapter, provider, model) {
  const overrides = { ...(props.modelValue?.chapter_overrides || {}) }
  const existing = { ...(overrides[chapter] || {}) }
  const currentDefaultModels = { ...(existing.default_models || {}) }
  currentDefaultModels[provider] = model
  overrides[chapter] = { ...existing, default_models: currentDefaultModels }
  await update('chapter_overrides', overrides)
}

// Swap the provider key on an existing pair — build the new default_models
// dict in one shot so the chapter is never briefly persisted in an intermediate
// "neither provider" state. Extracted so the template can call a single
// function (Vue templates can't parse inline TypeScript casts like
// `e.target as HTMLSelectElement`). Preserves the old model value if the new
// provider supports it; otherwise falls back to the new provider's default.
async function swapChapterDefaultModelProvider(chapter, oldProvider, e) {
  const target = e?.target
  const newProvider = target?.value
  if (newProvider === oldProvider || !newProvider) return
  const overrides = { ...(props.modelValue?.chapter_overrides || {}) }
  const existing = { ...(overrides[chapter] || {}) }
  const currentDefaultModels = { ...(existing.default_models || {}) }
  const oldModel = currentDefaultModels[oldProvider] ?? ''
  delete currentDefaultModels[oldProvider]
  const catalog = modelCatalogs.value[newProvider]
  currentDefaultModels[newProvider] =
    oldModel && catalog?.models?.includes(oldModel)
      ? oldModel
      : catalog?.default_model ?? ''
  overrides[chapter] = { ...existing, default_models: currentDefaultModels }
  await update('chapter_overrides', overrides)
}

const on_provider_change = (value) => update('default_provider', value)

// Phase 101: collect selected options from native multi-select change event.
const on_fallback_chain_change = (event) => {
  const selected = Array.from(event.target.selectedOptions).map((o) => o.value)
  update('fallback_chain', selected)
}

// Phase 102 Task 11 + Phase 104 Task 8: notify_threshold per-event-type.
// Phase 102 form was a single int slider (1-10, default 3). Phase 104 widens
// to per-event_type dict (generation / regeneration / cleanup / deletion),
// each independently configurable. Empty input on a row means "never warn
// for that event type" (∞). Backend Pydantic validator auto-expands legacy
// int payloads to a 4-key dict on read; see
// apps/studio_api/routes/project_settings.py:_validate_notify_threshold.
import { NOTIFY_EVENT_TYPES } from '@/api/illustrations'

const DEFAULT_THRESHOLD = 3

function formatThreshold(value, et) {
  // Phase 104: legacy int (post-Phase 104 backend never sends raw int, but the
  // UI handles the form defensively in case a stale API/cache leaks through)
  // shows the same number in every row.
  if (typeof value === 'number') return value
  // Per-event_type dict — show the configured value or empty (∞).
  if (value && typeof value === 'object' && et in value) return value[et]
  // undefined / empty dict / unknown shape → opt-out all.
  return ''
}

async function onThresholdChange(et, event) {
  // Build a normalized dict from current value (handles int legacy / dict /
  // undefined uniformly). We spread to avoid mutating props.
  const current = props.modelValue?.notify_threshold
  const dict =
    current && typeof current === 'object' && !Array.isArray(current)
      ? { ...current }
      : {}

  const raw = event.target.value.trim()
  if (raw === '') {
    // Empty → opt out of warnings for this event type.
    delete dict[et]
  } else {
    const parsed = parseInt(raw, 10)
    if (Number.isFinite(parsed) && parsed >= 1) {
      dict[et] = parsed
    } else {
      // Invalid input (zero / negative / non-numeric) — silently ignore. The
      // input's `min="1"` attribute catches most cases in the browser.
      return
    }
  }
  await update('notify_threshold', dict)
}

async function resetAllThresholds() {
  const dict = {}
  for (const et of NOTIFY_EVENT_TYPES) {
    dict[et] = DEFAULT_THRESHOLD
  }
  await update('notify_threshold', dict)
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
            <th>Default Models</th>
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
            <td
              class="project-settings-illustration-chapter-override-default-models"
              :data-testid="`chapter-override-default-models-${chapter}`"
            >
              <div
                v-for="(model, provider) in props.modelValue?.chapter_overrides?.[chapter]?.default_models || {}"
                :key="`${chapter}-${provider}`"
                class="project-settings-illustration-chapter-default-model-pair"
                :data-testid="`chapter-override-default-model-pair-${chapter}-${provider}`"
              >
                <select
                  :value="provider"
                  class="project-settings-illustration-chapter-default-model-provider"
                  :data-testid="`chapter-override-default-model-provider-${chapter}-${provider}`"
                  @change="swapChapterDefaultModelProvider(chapter, provider, $event)"
                >
                  <option v-for="p in providers" :key="p.id" :value="p.id">{{ p.label }}</option>
                </select>
                <select
                  :value="model"
                  class="project-settings-illustration-chapter-default-model-name"
                  :data-testid="`chapter-override-default-model-name-${chapter}-${provider}`"
                  @change="updateChapterDefaultModel(chapter, provider, $event.target.value)"
                >
                  <option
                    v-for="m in (modelCatalogs[provider] && modelCatalogs[provider].models) || []"
                    :key="m"
                    :value="m"
                  >{{ m }}</option>
                </select>
                <button
                  type="button"
                  class="project-settings-illustration-chapter-default-model-remove"
                  :data-testid="`chapter-override-default-model-remove-${chapter}-${provider}`"
                  @click="removeChapterDefaultModel(chapter, provider)"
                >×</button>
              </div>
              <button
                type="button"
                class="project-settings-illustration-chapter-default-model-add"
                :data-testid="`chapter-override-default-model-add-${chapter}`"
                @click="addChapterDefaultModel(chapter, providers[0].id)"
              >+ Add</button>
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

    <!-- Phase 102 Task 11 + Phase 104 Task 8: notify_threshold per-event-type.
         Phase 102 was a single int slider (1-10, default 3) shared across all
         event types. Phase 104 widens to a per-event_type dict — 4 fixed rows
         (generation / regeneration / cleanup / deletion), each independently
         configurable. Empty input on a row means "never warn for that event
         type" (∞). Reset button sets all 4 rows back to the default (3). -->
    <div
      class="field project-settings-illustration-field project-settings-illustration-notify-thresholds"
      data-testid="notify-thresholds-section"
    >
      <p class="label project-settings-illustration-label">通知阈值（按事件类型）</p>
      <p class="empty-hint project-settings-illustration-hint">
        连续失败次数达到该值后触发警告通知；留空表示从不警告。
      </p>
      <table
        class="project-settings-illustration-notify-thresholds-table"
        data-testid="notify-thresholds-table"
      >
        <thead>
          <tr>
            <th>Event type</th>
            <th>Threshold</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="et in NOTIFY_EVENT_TYPES"
            :key="et"
            class="project-settings-illustration-notify-threshold-row"
            :data-testid="`notify-threshold-row-${et}`"
          >
            <td>{{ et }}</td>
            <td>
              <input
                type="number"
                class="project-settings-illustration-notify-threshold-input"
                :value="formatThreshold(props.modelValue?.notify_threshold, et)"
                min="1"
                step="1"
                placeholder="∞"
                :data-testid="`notify-threshold-input-${et}`"
                @change="onThresholdChange(et, $event)"
              />
            </td>
          </tr>
        </tbody>
      </table>
      <button
        type="button"
        class="project-settings-illustration-notify-threshold-reset-all"
        data-testid="notify-threshold-reset-all"
        @click="resetAllThresholds"
      >
        Reset all to default
      </button>
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

/* Phase 103: per-chapter default_models cascade picker. */
.project-settings-illustration-chapter-override-default-models {
  min-width: 240px;
  vertical-align: top;
}

.project-settings-illustration-chapter-default-model-pair {
  display: flex;
  gap: 4px;
  align-items: center;
  margin-bottom: 4px;
}

.project-settings-illustration-chapter-default-model-provider,
.project-settings-illustration-chapter-default-model-name {
  flex: 1;
  font-size: var(--text-sm);
  font-family: var(--font-mono);
  padding: 2px 4px;
  background: var(--bg-primary);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-sm);
  min-width: 70px;
}

.project-settings-illustration-chapter-default-model-remove {
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--color-text-muted, #888);
  padding: 0 4px;
  font-size: var(--text-sm);
}
.project-settings-illustration-chapter-default-model-remove:hover {
  color: var(--color-accent);
}

.project-settings-illustration-chapter-default-model-add {
  background: transparent;
  border: 1px dashed var(--border-color, #ccc);
  padding: 2px 8px;
  cursor: pointer;
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  border-radius: var(--radius-sm);
  color: var(--color-text-muted, #4b5563);
}

.project-settings-illustration-chapter-default-model-add:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
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

/* Phase 104 Task 8: notify_thresholds per-event-type table. */
.project-settings-illustration-notify-thresholds {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.project-settings-illustration-notify-thresholds-table {
  border-collapse: collapse;
  width: 100%;
  font-size: var(--text-sm);
  font-family: var(--font-ui);
}

.project-settings-illustration-notify-thresholds-table th,
.project-settings-illustration-notify-thresholds-table td {
  border: var(--border-width) solid var(--border-color);
  padding: 4px 6px;
  text-align: left;
  vertical-align: middle;
}

.project-settings-illustration-notify-thresholds-table th {
  font-weight: 600;
  color: var(--color-text-muted, #4b5563);
  background: var(--bg-muted);
}

.project-settings-illustration-notify-threshold-input {
  width: 100px;
  font-family: var(--font-mono);
  padding: 4px 6px;
  background: var(--bg-primary);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-sm);
}

.project-settings-illustration-notify-threshold-reset-all {
  align-self: flex-start;
  margin-top: var(--space-xs);
  padding: 4px 10px;
  background: var(--bg-primary);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  color: var(--color-text);
}

.project-settings-illustration-notify-threshold-reset-all:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}
</style>

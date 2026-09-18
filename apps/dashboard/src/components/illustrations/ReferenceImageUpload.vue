<script setup>
import { ref, onMounted } from 'vue'
import { NButton } from 'naive-ui'
import { useProjectSettingsStore } from '@/stores/useProjectSettings.js'

const props = defineProps({
  slug: { type: String, required: true },
})

const store = useProjectSettingsStore()
const fileInput = ref(null)
const previewUrl = ref(null)
const uploading = ref(false)
const removing = ref(false)
const errorMessage = ref(null)

onMounted(async () => {
  await loadInfo()
})

async function loadInfo() {
  try {
    const info = await store.fetchReferenceImage(props.slug)
    if (info && info.exists) {
      try {
        previewUrl.value = await store.fetchReferenceImageBlob(props.slug)
      } catch (e) {
        previewUrl.value = null
      }
    } else {
      previewUrl.value = null
    }
  } catch (e) {
    previewUrl.value = null
  }
}

async function onFileChange(event) {
  const file = event.target.files && event.target.files[0]
  if (!file) return
  uploading.value = true
  errorMessage.value = null
  try {
    await store.uploadReferenceImage(props.slug, file)
    await loadInfo()
  } catch (e) {
    errorMessage.value =
      (e && e.data && (e.data.detail?.error || e.data.detail)) ||
      e.message ||
      '上传失败'
  } finally {
    uploading.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

async function onRemove() {
  removing.value = true
  errorMessage.value = null
  try {
    await store.deleteReferenceImage(props.slug)
    previewUrl.value = null
  } catch (e) {
    errorMessage.value = (e && e.data && e.data.detail) || e.message || '删除失败'
  } finally {
    removing.value = false
  }
}

function triggerFileInput() {
  if (fileInput.value) fileInput.value.click()
}

function formatSize(bytes) {
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}
</script>

<template>
  <div
    class="field reference-image-upload-component"
    data-testid="reference-image-upload"
  >
    <p class="label">项目参考图（可选）</p>
    <p class="hint">
      上传后所有插图生成将以此图为风格基准。
      OpenAI DALL-E 3 不支持参考图，请切换至 MiniMax 或 Stability。
    </p>

    <input
      ref="fileInput"
      type="file"
      accept="image/jpeg,image/png"
      class="hidden"
      data-testid="reference-image-upload-input"
      @change="onFileChange"
    />

    <div v-if="store.referenceImage && store.referenceImage.exists" class="current">
      <img
        v-if="previewUrl"
        :src="previewUrl"
        alt="参考图预览"
        class="preview"
        data-testid="reference-image-preview"
      />
      <div class="meta">
        <span data-testid="reference-image-size">
          {{ formatSize(store.referenceImage.size_bytes) }}
        </span>
        <span class="mime">{{ store.referenceImage.mime_type }}</span>
      </div>
      <div class="actions">
        <NButton
          size="small"
          data-testid="reference-image-replace"
          @click="triggerFileInput"
        >替换</NButton>
        <NButton
          size="small"
          type="error"
          :loading="removing"
          data-testid="reference-image-remove"
          @click="onRemove"
        >删除</NButton>
      </div>
    </div>

    <NButton
      v-else
      :loading="uploading"
      data-testid="reference-image-upload-button"
      @click="triggerFileInput"
    >上传参考图</NButton>

    <p
      v-if="errorMessage"
      class="error"
      data-testid="reference-image-error"
    >
      {{ errorMessage }}
    </p>
  </div>
</template>

<style scoped>
.reference-image-upload-component {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.hidden {
  display: none;
}
.preview {
  max-width: 200px;
  max-height: 200px;
  border-radius: 4px;
  border: 1px solid var(--border-color, #e5e7eb);
}
.meta {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: var(--text-muted, #4b5563);
}
.actions {
  display: flex;
  gap: 8px;
}
.error {
  font-size: 12px;
  color: #dc2626;
  margin: 0;
}
.hint {
  font-size: 12px;
  color: var(--text-muted, #4b5563);
  margin: 0;
}
.label {
  font-size: 12px;
  text-transform: uppercase;
  color: var(--text-muted, #4b5563);
  margin: 0;
}
</style>

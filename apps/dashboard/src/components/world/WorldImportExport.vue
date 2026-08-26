<!--
  WorldImportExport.vue — Phase 117 (Task 21) 世界页 markdown 导入/导出
  - 从后端拉取 markdown 导入人物 / 阵营 / 世界观条目
  - 把当前世界状态打包为 markdown 写到磁盘
  - 复用 useWorldImportExport composable（已由 Task 11 创建）
  - 顶部按钮触发，结果摘要内联展示
-->
<template>
  <div class="world-import-export" data-testid="world-import-export">
    <button
      type="button"
      class="world-import-btn import-btn"
      data-testid="world-import-btn"
      :disabled="busy"
      @click="doImport"
    >从 markdown 导入</button>
    <button
      type="button"
      class="world-export-btn export-btn"
      data-testid="world-export-btn"
      :disabled="busy"
      @click="doExport"
    >导出 markdown</button>
    <p v-if="lastSummary" class="world-import-export__summary export-summary" data-testid="export-summary">
      {{ lastSummary }}
    </p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useWorldImportExport } from '@/composables/world/useWorldImportExport.js'

const { importMarkdown, exportMarkdown } = useWorldImportExport()
const busy = ref(false)
const lastSummary = ref(null)

async function doImport() {
  busy.value = true
  try {
    const r = await importMarkdown()
    lastSummary.value = `导入: 人物 ${r.characters_imported}, 阵营 ${r.factions_imported}, 世界观 ${r.lore_imported}`
  } finally {
    busy.value = false
  }
}

async function doExport() {
  busy.value = true
  try {
    const r = await exportMarkdown()
    lastSummary.value = `导出 ${r.files_written} 文件到 ${r.output_dir}`
  } finally {
    busy.value = false
  }
}
</script>
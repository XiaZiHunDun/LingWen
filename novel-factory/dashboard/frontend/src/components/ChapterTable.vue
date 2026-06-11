<template>
  <div class="chapter-table-wrapper pixel-border">
    <table class="chapter-table" data-testid="chapter-table">
      <thead>
        <tr>
          <th
            v-for="column in columns"
            :key="column.key"
            @click="sortBy(column.key)"
            :class="{ 'sortable': true, 'sorted': sortKey === column.key }"
          >
            {{ column.label }}
            <span class="sort-indicator" v-if="sortKey === column.key">
              {{ sortOrder === 'asc' ? '▲' : '▼' }}
            </span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(chapter, index) in sortedChapters"
          :key="chapter.chapter"
          :class="{ 'zebra-odd': index % 2 === 0, 'zebra-even': index % 2 !== 0 }"
        >
          <td>{{ chapter.chapter }}</td>
          <td>{{ chapter.hook_count }}</td>
          <td>{{ formatPercent(chapter.hook_strength_avg) }}</td>
          <td>{{ chapter.coolpoint_count }}</td>
          <td>{{ formatPercent(chapter.coolpoint_density) }}</td>
          <td>
            <button
              v-if="showDecisionLink(chapter.chapter)"
              type="button"
              class="decision-link-btn pixel-border"
              data-testid="chapter-decision-link"
              @click.stop="emitDecisionLink(chapter.chapter)"
            >
              决策
            </button>
            <span
              v-if="productionBadge(chapter.chapter)"
              class="production-badge"
              data-testid="chapter-production-badge"
            >
              {{ productionBadge(chapter.chapter) }}
            </span>
            <span
              v-if="!showDecisionLink(chapter.chapter) && !productionBadge(chapter.chapter)"
              class="production-badge-empty"
            >-</span>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="chapters.length === 0" class="empty-state">
      暂无章节数据
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { chapterProductionBadge } from '../utils/productionRecords.js'

const props = defineProps({
  chapters: {
    type: Array,
    default: () => []
  },
  productionByChapter: {
    type: Object,
    default: () => ({})
  },
  decisionLinkChapters: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['decision-link'])

const columns = [
  { key: 'chapter', label: '章节' },
  { key: 'hook_count', label: '钩子数' },
  { key: 'hook_strength_avg', label: '钩子强度' },
  { key: 'coolpoint_count', label: '爽点数' },
  { key: 'coolpoint_density', label: '爽点密度' },
  { key: 'production', label: '生产/决策' }
]

const sortKey = ref('chapter')
const sortOrder = ref('asc')

const sortedChapters = computed(() => {
  const sorted = [...props.chapters].sort((a, b) => {
    const aVal = a[sortKey.value]
    const bVal = b[sortKey.value]

    if (typeof aVal === 'number' && typeof bVal === 'number') {
      return sortOrder.value === 'asc' ? aVal - bVal : bVal - aVal
    }

    const aStr = String(aVal)
    const bStr = String(bVal)
    return sortOrder.value === 'asc'
      ? aStr.localeCompare(bStr)
      : bStr.localeCompare(aStr)
  })

  return sorted
})

const sortBy = (key) => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortOrder.value = 'asc'
  }
}

const formatPercent = (value) => {
  if (value === undefined || value === null) return '-'
  return (value * 100).toFixed(1) + '%'
}

const productionBadge = (chapterNum) =>
  chapterProductionBadge(chapterNum, props.productionByChapter)

const showDecisionLink = (chapterNum) => Boolean(props.decisionLinkChapters[chapterNum])

const emitDecisionLink = (chapterNum) => {
  emit('decision-link', chapterNum)
}
</script>

<style scoped>
.chapter-table-wrapper {
  background-color: var(--bg-secondary);
  padding: var(--space-md);
  overflow-x: auto;
}

.chapter-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 8px;
}

.chapter-table th,
.chapter-table td {
  padding: var(--space-sm) var(--space-md);
  text-align: left;
  border-bottom: 2px solid var(--border-color);
}

.chapter-table th {
  background-color: var(--bg-primary);
  color: var(--color-text);
  font-weight: bold;
  border-bottom: 4px solid var(--border-color);
  white-space: nowrap;
}

.chapter-table th.sortable {
  cursor: pointer;
  user-select: none;
}

.chapter-table th.sortable:hover {
  background-color: var(--color-accent);
  color: white;
}

.chapter-table th.sorted {
  background-color: var(--color-accent);
  color: white;
}

.sort-indicator {
  margin-left: var(--space-xs);
  font-size: 6px;
}

.chapter-table tbody tr {
  transition: background-color 0.1s;
}

.chapter-table tbody tr.zebra-odd {
  background-color: var(--bg-primary);
}

.chapter-table tbody tr.zebra-even {
  background-color: var(--bg-secondary);
}

.chapter-table tbody tr:hover {
  background-color: var(--color-warning);
  color: white;
}

.chapter-table td {
  color: var(--color-text);
}

.production-badge {
  font-size: 7px;
  padding: 2px 4px;
  background: #c8e6c9;
  border: 1px solid var(--border-color);
}

.production-badge-empty {
  opacity: 0.5;
}

.decision-link-btn {
  font-size: 7px;
  font-family: 'Press Start 2P', monospace;
  padding: 2px 4px;
  margin-right: 4px;
  cursor: pointer;
  background: #fff59d;
}

.empty-state {
  text-align: center;
  padding: var(--space-xl);
  color: var(--color-text);
  opacity: 0.6;
  font-size: 8px;
}
</style>
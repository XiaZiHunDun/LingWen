<!--
  PilotHistoryList.vue — 历史 batch 列表（状态表格 + row click → select-job）
-->
<template>
  <section class="pilot-history-list pixel-card" data-testid="pilot-history-list">
    <h2 class="section-title">历史 batch</h2>
    <p v-if="history.length === 0" class="empty-msg" data-testid="pilot-history-empty">无历史 batch</p>
    <table v-else class="history-table" aria-label="Pilot 历史 batch">
      <thead>
        <tr>
          <th>Job</th>
          <th>模式</th>
          <th>章节</th>
          <th>状态</th>
          <th>启动时间</th>
          <th>预算</th>
          <th>退出码</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="row in history"
          :key="row.job_id"
          :data-testid="`history-row-${row.job_id}`"
          class="history-row"
          @click="emit('select-job', row.job_id)"
        >
          <td><code>{{ row.job_id }}</code></td>
          <td>{{ row.mode }}</td>
          <td>ch{{ String(row.start_chapter).padStart(3, '0') }}–{{ String(row.end_chapter).padStart(3, '0') }}</td>
          <td :class="`status-${row.status}`">{{ row.status }}</td>
          <td>{{ row.started_at }}</td>
          <td>${{ row.budget_usd }}</td>
          <td>{{ row.exit_code ?? '—' }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup lang="ts">
interface HistoryRow {
  job_id: string;
  status: string;
  start_chapter: number;
  end_chapter: number;
  mode: string;
  started_at: string;
  budget_usd: number;
  exit_code: number | null;
  finished_at?: string | null;
  error?: string | null;
}

defineProps<{ history: HistoryRow[] }>();
const emit = defineEmits<{ 'select-job': [jobId: string] }>();
</script>

<style scoped>
.pilot-history-list { padding: 1rem; }
.history-table { width: 100%; border-collapse: collapse; }
.history-table th,
.history-table td { padding: 0.5rem; text-align: left; border-bottom: 1px solid var(--border, #ddd); }
.history-row { cursor: pointer; }
.history-row:hover { background: var(--hover, rgba(0, 0, 0, 0.05)); }
.status-running { color: var(--success, #2c7a2c); font-weight: 600; }
.status-completed { color: var(--info, #2c6cb0); font-weight: 600; }
.status-failed,
.status-cancelled { color: var(--error, #c33); font-weight: 600; }
.empty-msg { color: var(--muted, #888); font-style: italic; }
</style>
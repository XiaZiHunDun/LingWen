<!--
  PilotPreflightTable.vue — 章节 preflight 检查结果表（P1）
-->
<template>
  <div class="pilot-preflight" data-testid="pilot-preflight">
    <p v-if="rows.length === 0" data-testid="pilot-preflight-empty" class="empty-msg">
      无 preflight 结果
    </p>
    <table v-else class="preflight-table" aria-label="Pilot preflight 检查结果">
      <thead>
        <tr>
          <th scope="col">章</th>
          <th scope="col">状态</th>
          <th scope="col">说明</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="row in rows"
          :key="row.chapter"
          :data-testid="`pilot-preflight-row-${row.chapter}`"
        >
          <td>ch{{ String(row.chapter).padStart(3, '0') }}</td>
          <td
            :class="row.ok ? 'status-ok' : 'status-fail'"
            :data-testid="row.ok ? 'pilot-preflight-status-ok' : 'pilot-preflight-status-fail'"
          >
            {{ row.ok ? 'PASS' : 'FAIL' }}
          </td>
          <td>{{ row.message }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
interface PreflightRow {
  chapter: number;
  ok: boolean;
  message: string;
}

defineProps<{ rows: PreflightRow[] }>();
</script>

<style scoped>
.pilot-preflight {
  width: 100%;
}

.preflight-table {
  width: 100%;
  border-collapse: collapse;
}

.preflight-table th,
.preflight-table td {
  padding: 0.5rem;
  text-align: left;
  border-bottom: 1px solid var(--border, #ddd);
}

.status-ok {
  color: var(--success, #2c7a2c);
  font-weight: 600;
}

.status-fail {
  color: var(--error, #c33);
  font-weight: 600;
}

.empty-msg {
  color: var(--muted, #888);
  font-style: italic;
}
</style>
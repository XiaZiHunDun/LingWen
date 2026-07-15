<!--
  CreatorPublishHistoryModal.vue — 完整发布历史
-->
<template>
  <div
    v-if="pt.publishHistoryModalOpen"
    class="creator-modal creator-modal--nested"
    data-testid="creator-publish-history-modal"
    @click.self="pt.closePublishHistoryModal"
  >
    <div class="creator-modal__panel pixel-card" data-testid="creator-publish-history-panel">
      <header class="creator-modal__header">
        <h2>发布历史</h2>
        <button type="button" class="link-btn" data-testid="publish-history-close" @click="pt.closePublishHistoryModal">
          关闭
        </button>
      </header>

      <p v-if="!pt.publishHistory.length" class="meta-line" data-testid="publish-history-empty">
        暂无发布记录。
      </p>

      <ul v-else class="history-table" data-testid="publish-history-list">
        <li
          v-for="row in pt.publishHistory"
          :key="row.id"
          class="history-row"
          :data-testid="`publish-history-row-${row.id}`"
        >
          <div class="history-row__head">
            <strong>{{ row.platform }}</strong>
            <span class="status-tag" :class="`status-tag--${row.status}`">{{ row.status }}</span>
          </div>
          <p class="meta-line">{{ row.created_at }}</p>
          <p v-if="row.message" class="history-msg">{{ row.message }}</p>
          <p class="meta-line">
            <span v-if="row.adapter_id">适配器 {{ row.adapter_id }}</span>
            <span v-if="row.connection"> · {{ row.connection }}</span>
            <span v-if="row.mode"> · {{ row.mode }}</span>
          </p>
          <p v-if="row.intro" class="meta-line history-intro">简介：{{ row.intro.slice(0, 120) }}{{ row.intro.length > 120 ? '…' : '' }}</p>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { inject } from 'vue';
import { CREATOR_PRODUCT_TOOLS_KEY } from './creatorProductToolsKey.js';

const pt = inject(CREATOR_PRODUCT_TOOLS_KEY);
</script>

<style scoped>
.history-table {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.history-row {
  padding: var(--space-sm);
  border: 1px dashed #bbb;
  font-size: var(--text-sm);
}

.history-row__head {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.status-tag {
  font-size: var(--text-xs);
  padding: 1px 6px;
  border: 1px solid #ccc;
}

.status-tag--adapter_stub,
.status-tag--queued {
  background: #fff9c4;
}

.history-msg {
  margin: 4px 0;
  font-size: var(--text-sm);
}

.history-intro {
  font-style: italic;
}
</style>

<!--
  CreatorInterventionBanner.vue — 待介入事项摘要
-->
<template>
  <div
    v-if="pt.interventionItems.length"
    class="intervention-banner pixel-border"
    data-testid="creator-intervention-banner"
  >
    <h3 class="intervention-title">需要你关注</h3>
    <ul class="intervention-list">
      <li
        v-for="item in pt.interventionItems"
        :key="item.id"
        class="intervention-item"
        :data-testid="`intervention-item-${item.id}`"
      >
        <div class="intervention-copy">
          <strong>{{ item.title }}</strong>
          <span class="meta-line">{{ item.detail }}</span>
        </div>
        <button
          type="button"
          class="mini-btn pixel-border"
          :data-testid="`intervention-action-${item.id}`"
          @click="pt.handleInterventionAction(item)"
        >
          去处理
        </button>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { inject } from 'vue';
import { CREATOR_PRODUCT_TOOLS_KEY } from './creatorProductToolsKey.js';

const pt = inject(CREATOR_PRODUCT_TOOLS_KEY);
</script>

<style scoped>
.intervention-banner {
  padding: var(--space-sm) var(--space-md);
  background: rgba(255, 249, 196, 0.35);
}

.intervention-title {
  margin: 0 0 var(--space-xs);
  font-size: var(--text-sm);
  color: #a60;
}

.intervention-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.intervention-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-sm);
  font-size: var(--text-sm);
}

.intervention-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}
</style>

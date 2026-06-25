<!--
  CreatorPageBanners.vue — 创作页全局状态横幅（inject 页级 chrome 上下文）
-->
<template>
  <div v-if="c.error" class="error-banner pixel-border" data-testid="error-banner">
    {{ c.error }}
  </div>
  <div v-if="c.conflictMessage" class="conflict-banner pixel-border" data-testid="conflict-banner">
    {{ c.conflictMessage }}
    <button type="button" class="mini-btn pixel-border" data-testid="conflict-reload-btn" @click="c.refresh">
      重新加载
    </button>
  </div>
  <div v-if="c.saveMessage" class="save-banner pixel-border" data-testid="save-banner">
    {{ c.saveMessage }}
  </div>
</template>

<script setup>
import { inject } from 'vue';
import { CREATOR_PAGE_CHROME_KEY } from './creatorPageChromeKey.js';

const c = inject(CREATOR_PAGE_CHROME_KEY);
</script>

<style scoped>
.error-banner {
  padding: var(--space-sm);
  color: #c44;
  font-size: var(--text-sm);
}

.save-banner {
  padding: var(--space-sm);
  color: #484;
  font-size: var(--text-sm);
}

.conflict-banner {
  padding: var(--space-sm);
  color: #a60;
  font-size: var(--text-sm);
}

.mini-btn {
  font-size: var(--text-xs);
  padding: 2px 6px;
  cursor: pointer;
  margin-left: var(--space-sm);
}
</style>

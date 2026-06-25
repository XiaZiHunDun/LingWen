<!--
  CreatorPageBanners.vue — 创作页全局状态横幅（从 CreatorPage 拆出）
-->
<template>
  <div v-if="error" class="error-banner pixel-border" data-testid="error-banner">
    {{ error }}
  </div>
  <div v-if="conflictMessage" class="conflict-banner pixel-border" data-testid="conflict-banner">
    {{ conflictMessage }}
    <button type="button" class="mini-btn pixel-border" data-testid="conflict-reload-btn" @click="$emit('reload')">
      重新加载
    </button>
  </div>
  <div v-if="saveMessage" class="save-banner pixel-border" data-testid="save-banner">
    {{ saveMessage }}
  </div>
</template>

<script setup>
defineProps({
  error: { type: [String, Object], default: null },
  conflictMessage: { type: String, default: '' },
  saveMessage: { type: String, default: '' },
});

defineEmits(['reload']);
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

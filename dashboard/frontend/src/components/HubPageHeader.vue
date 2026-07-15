<!--
  HubPageHeader.vue — Hub 页统一页头（标题 + 元信息 + 刷新）
-->
<template>
  <header
    v-if="showChrome"
    class="hub-page-header"
    :class="{ 'hub-page-header--compact': compactChrome }"
    :data-testid="testId || 'hub-page-header'"
  >
    <div v-if="showTitleBlock" class="hub-page-header__main">
      <h1 v-if="title" class="page-title" data-testid="page-title">{{ title }}</h1>
      <p v-if="subtitle" class="hub-subtitle">{{ subtitle }}</p>
      <p v-if="meta && !compactChrome" class="hub-meta" :data-testid="metaTestId">{{ meta }}</p>
    </div>
    <p
      v-else-if="compactChrome && meta"
      class="hub-meta hub-page-header__meta-compact"
      :data-testid="metaTestId"
    >
      {{ meta }}
    </p>
    <div class="hub-page-header__actions">
      <slot name="actions" />
      <button
        v-if="showRefresh"
        type="button"
        class="l1-pill"
        data-testid="refresh-btn"
        :disabled="loading"
        @click="$emit('refresh')"
      >
        {{ loading ? '加载中…' : '刷新' }}
      </button>
    </div>
  </header>
</template>

<script setup>
import { computed, inject } from 'vue';

const props = defineProps({
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  meta: { type: String, default: '' },
  metaTestId: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  showRefresh: { type: Boolean, default: true },
  testId: { type: String, default: '' },
});

defineEmits(['refresh']);

const isHumanFirstShell = inject('isHumanFirstShell', computed(() => false));

const compactChrome = computed(() => Boolean(isHumanFirstShell.value));
const showTitleBlock = computed(
  () => !compactChrome.value && Boolean(props.title || props.subtitle),
);
const showChrome = computed(
  () => showTitleBlock.value
    || (compactChrome.value && Boolean(props.meta))
    || props.showRefresh
    || Boolean(props.subtitle),
);
</script>

<style scoped>
.hub-page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-md);
  flex-wrap: wrap;
}

.hub-page-header--compact {
  align-items: center;
}

.hub-page-header__main {
  flex: 1;
  min-width: 0;
}

.hub-page-header__meta-compact {
  flex: 1;
  min-width: 0;
  margin: 0;
}

.hub-page-header__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  align-items: center;
  margin-left: auto;
}

.page-title {
  font-size: var(--text-xl);
  font-family: var(--font-ui);
  font-weight: 700;
  margin: 0;
}

.hub-subtitle {
  margin: var(--space-xs) 0 0;
  font-size: var(--text-sm);
  color: var(--text-muted, var(--color-text-dim));
}

.hub-meta {
  margin: var(--space-xs) 0 0;
  font-size: var(--text-sm);
  color: var(--color-text-dim);
}
</style>

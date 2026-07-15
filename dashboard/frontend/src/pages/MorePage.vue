<!--
  MorePage.vue — L1 更多（frontend-ia-v1）
-->
<template>
  <div class="more-page l1-page" data-testid="more-page">
    <div class="more-page__body l1-page__body l1-panel-enter">
      <PageLeadBar
        page-id="more"
        inline
        text="生产、待办与洞察——日常写作请回「书桌」"
      />

      <div class="more-page__grid">
      <button
        v-for="link in links"
        :key="link.id"
        type="button"
        class="more-card"
        :data-testid="`more-link-${link.id}`"
        @click="open(link)"
      >
        <span class="more-card__mark" aria-hidden="true">{{ link.mark }}</span>
        <span class="more-card__label">{{ link.label }}</span>
        <span class="more-card__desc">{{ link.desc }}</span>
      </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, inject } from 'vue';
import PageLeadBar from '../components/PageLeadBar.vue';
import { buildMorePageLinks } from '../config/dashboardNavByMode.js';
import { useDashboardNav } from '../composables/useDashboardNav.js';

const { navigateTo } = useDashboardNav();
const creationMode = inject('creationMode', computed(() => 'companion'));

const links = computed(() => buildMorePageLinks(creationMode.value));

function open(link) {
  if (link.tab) {
    navigateTo(link.nav, { tab: link.tab, clearFocus: true });
    return;
  }
  navigateTo(link.nav, { clearFocus: true });
}
</script>

<style scoped>
.more-page {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  width: 100%;
  max-width: none;
  margin: 0;
}
.more-page__body {
  /* 见 style.css .l1-page__body */
}
.more-page__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--space-lg);
}
.more-card {
  display: grid;
  grid-template-columns: 36px 1fr;
  grid-template-rows: auto auto;
  column-gap: var(--space-md);
  row-gap: 4px;
  align-items: start;
  padding: var(--space-lg);
  text-align: left;
  cursor: pointer;
  background: var(--bg-elevated);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  transition: box-shadow 0.15s ease, border-color 0.15s ease, transform 0.15s ease;
}
.more-card:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}
.more-card__mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  grid-row: 1 / span 2;
  font-size: var(--text-sm);
  font-weight: 700;
  color: #fff;
  border-radius: var(--radius-sm);
  background: linear-gradient(145deg, var(--color-accent), var(--color-accent-gradient-end));
}
.more-card__label {
  font-weight: 600;
  font-size: var(--text-sm);
  align-self: end;
}
.more-card__desc {
  font-size: var(--text-xs);
  color: var(--color-text-dim);
  grid-column: 2;
}
</style>

<template>
  <section
    v-show="p.isWorkspaceColumnVisible('pulse')"
    class="creator-column"
    :class="{
      'creator-column--pulse-desk': p.workspaceTabsEnabled,
      'creator-column--desk-drawer': p.deskDrawerActive?.(),
      'creator-column--desk-drawer--open': p.deskDrawerActive?.(),
    }"
    data-testid="column-pulse"
    :id="p.deskDrawerActive?.() ? 'creator-desk-drawer-panel-pulse' : undefined"
    :role="p.deskDrawerActive?.() ? 'dialog' : undefined"
    :aria-modal="p.deskDrawerActive?.() ? 'true' : undefined"
    :aria-labelledby="p.deskDrawerActive?.() ? 'desk-drawer-title-pulse' : undefined"
  >
    <div v-if="p.deskDrawerActive?.()" class="desk-drawer-chrome" data-testid="desk-drawer-chrome-pulse">
      <h2 id="desk-drawer-title-pulse" class="desk-drawer-chrome__title">脉络</h2>
      <button
        type="button"
        class="mini-btn pixel-border"
        data-testid="desk-drawer-close-pulse"
        aria-label="关闭脉络抽屉"
        @click="p.closeDeskDrawer()"
      >
        关闭
      </button>
    </div>
    <div class="pulse-desk" :class="{ 'pulse-desk--legacy': !p.workspaceTabsEnabled }">
      <div class="pulse-desk__hero">
        <p class="pulse-desk__intro">查看故事脉络与进度，发现潜在问题</p>
      </div>

      <div class="pulse-desk__scroll">
        <div v-if="p.overview.volume_pulse?.volume_count" class="pulse-desk__section">
          <h3 class="pulse-desk__section-title">📊 卷级进度</h3>
          <p class="pulse-desk__section-hint">
            {{ p.overview.volume_pulse.alert_count ? `${p.overview.volume_pulse.alert_count} 卷需关注` : '各卷按计划推进' }}
          </p>
          <ul class="pulse-desk__list">
            <li
              v-for="row in p.overview.volume_pulse.volumes"
              :key="row.label"
              class="volume-pulse-row"
              :class="`volume-pulse-row--${row.status}`"
              @click="p.jumpToVolume(row)"
            >
              <strong>{{ formatDisplayLabel(row.label) }}</strong>
              <span class="meta-line">{{ row.headline }}</span>
            </li>
          </ul>
        </div>

        <div v-if="p.isPulseSubpanelVisible('deviationList') && p.visibleDeviations.length" class="pulse-desk__section">
          <h3 class="pulse-desk__section-title">⚠️ 偏离提醒</h3>
          <ul class="pulse-desk__list">
            <li
              v-for="dev in p.visibleDeviations.slice(0, 5)"
              :key="dev.id"
              class="deviation-row"
              :class="`deviation-row--${dev.severity}`"
              @click="p.handleDeviationClick(dev)"
            >
              <span class="deviation-row__icon">{{ dev.severity === 'error' ? '✗' : '⚠' }}</span>
              <span class="deviation-row__text">{{ dev.headline }}</span>
            </li>
          </ul>
        </div>

        <div v-if="p.isPulseSubpanelVisible('deviationList') && !p.visibleDeviations.length" class="pulse-desk__section pulse-desk__section--empty">
          <p class="pulse-desk__empty-text">✓ 暂无偏离问题</p>
        </div>

        <div v-if="p.overview.volume_summaries.length" class="pulse-desk__section">
          <h3 class="pulse-desk__section-title">📝 卷摘要</h3>
          <ul class="pulse-desk__list">
            <li
              v-for="vol in p.overview.volume_summaries.slice(0, 3)"
              :key="vol.path"
              class="summary-row"
            >
              <span class="summary-row__label">{{ formatDisplayLabel(vol.volume_label || vol.name) }}</span>
              <span class="summary-row__excerpt">{{ vol.excerpt?.substring(0, 80) }}...</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { inject } from 'vue';
import { formatDisplayLabel } from '../../utils/displayProjectName.js';
import { CREATOR_PULSE_KEY } from './creatorPulseKey.js';

const p = inject(CREATOR_PULSE_KEY);
</script>

<style scoped>
.creator-column--pulse-desk {
  padding: 0;
  min-height: 0;
  border: none;
  background: transparent;
  box-shadow: none;
}

.pulse-desk {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  background: var(--bg-elevated);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.pulse-desk--legacy {
  border: none;
  box-shadow: none;
  background: transparent;
  overflow: visible;
}

.pulse-desk__hero {
  flex-shrink: 0;
  padding: var(--space-md) var(--space-lg);
  border-bottom: var(--border-width) solid var(--border-color);
  background: linear-gradient(180deg, var(--bg-primary) 0%, var(--bg-elevated) 100%);
}

.pulse-desk__intro {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.pulse-desk__scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--space-md) var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.pulse-desk__section {
  padding: var(--space-md);
  background: var(--bg-muted);
  border-radius: var(--radius-md);
}

.pulse-desk__section--empty {
  text-align: center;
  padding: var(--space-lg);
}

.pulse-desk__section-title {
  font-size: var(--text-sm);
  font-weight: 700;
  margin: 0 0 var(--space-sm);
  color: var(--color-text);
}

.pulse-desk__section-hint {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  margin: 0 0 var(--space-sm);
}

.pulse-desk__empty-text {
  font-size: var(--text-sm);
  color: var(--color-text-dim);
  margin: 0;
}

.pulse-desk__list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.meta-line {
  font-size: var(--text-sm);
  opacity: 0.75;
}

.volume-pulse-row {
  cursor: pointer;
  padding: 10px 12px;
  margin-bottom: var(--space-xs);
  border-radius: var(--radius-sm);
  transition: all 0.18s ease;
}

.volume-pulse-row:hover {
  background: var(--bg-elevated);
}

.volume-pulse-row--alert {
  border-left: 3px solid var(--color-danger);
  background: rgba(180, 35, 24, 0.04);
}

.volume-pulse-row--warn {
  border-left: 3px solid var(--color-warning);
  background: rgba(154, 103, 0, 0.04);
}

.volume-pulse-row--ok {
  border-left: 3px solid var(--color-success);
  background: rgba(46, 125, 90, 0.04);
}

.deviation-row {
  cursor: pointer;
  padding: 10px 12px;
  margin-bottom: var(--space-xs);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.18s ease;
}

.deviation-row:hover {
  background: var(--bg-elevated);
}

.deviation-row--error {
  border-left: 3px solid var(--color-danger);
  background: rgba(180, 35, 24, 0.04);
}

.deviation-row--warn {
  border-left: 3px solid var(--color-warning);
  background: rgba(154, 103, 0, 0.04);
}

.deviation-row__icon {
  font-size: var(--text-sm);
  font-weight: 600;
}

.deviation-row--error .deviation-row__icon {
  color: var(--color-danger);
}

.deviation-row--warn .deviation-row__icon {
  color: var(--color-warning);
}

.deviation-row__text {
  font-size: var(--text-sm);
  color: var(--color-text);
}

.summary-row {
  padding: 10px 12px;
  margin-bottom: var(--space-xs);
  border-radius: var(--radius-sm);
  background: var(--bg-elevated);
}

.summary-row__label {
  display: block;
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 4px;
}

.summary-row__excerpt {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.mini-btn {
  font-size: var(--text-xs);
  padding: 4px 10px;
  cursor: pointer;
  border-radius: var(--radius-xs);
}

.desk-drawer-chrome {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
  flex-shrink: 0;
}

.desk-drawer-chrome__title {
  margin: 0;
  font-size: var(--text-md);
  font-weight: 700;
}
</style>

<!--
  CreatorPulsePanel.vue — 脉络栏（从 CreatorPage 拆出）
-->
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
        <CreatorPulseIntro
          :overview="p.overview"
          :show-empty-guide="p.showPulseCompanionEmpty"
          :tabbed="p.workspaceTabsEnabled"
          @go-write="p.setWorkspaceTab('write')"
        />
      </div>

      <div class="pulse-desk__scroll">
        <CreatorChapterTaskCards
          @generate="onChapterTaskGenerate"
          @confirm="onChapterTaskConfirm"
        />

        <div v-if="p.isPulseSubpanelVisible('structureGraph')" class="pulse-desk__section pulse-desk__section--collapsible">
          <details :open="!p.isPulseSubpanelCollapsed('structureGraph')">
            <summary class="pulse-desk__section-title pulse-desk__section-summary">故事结构图</summary>
            <CreatorStructureGraph hide-title />
          </details>
        </div>

        <div
          v-if="p.isPulseSubpanelVisible('volumePulse') && p.overview.volume_pulse?.volume_count"
          class="pulse-desk__section volume-pulse-panel pixel-border pulse-desk__section--collapsible"
          :class="`volume-pulse-panel--${p.overview.volume_pulse.overall_status}`"
          data-testid="volume-pulse-panel"
        >
          <details :open="!p.isPulseSubpanelCollapsed('volumePulse')">
            <summary class="pulse-desk__section-title pulse-desk__section-summary">卷级脉络</summary>
            <p class="meta-line" data-testid="volume-pulse-overall">
            <template v-if="p.overview.volume_pulse.alerts_only">
              {{ p.overview.volume_pulse.alert_count ? `${p.overview.volume_pulse.alert_count} 卷需关注` : '暂无 alert 级偏离' }}
            </template>
            <template v-else>
              {{ p.overview.volume_pulse.alert_count ? `${p.overview.volume_pulse.alert_count} 卷需关注` : '各卷按计划推进' }}
            </template>
          </p>
          <ul class="pulse-desk__list">
            <li
              v-for="row in p.overview.volume_pulse.volumes"
              :key="row.label"
              class="volume-pulse-row"
              :class="[
                `volume-pulse-row--${row.status}`,
                { 'volume-pulse-row--active': p.highlightedVolumeLabel === row.label },
              ]"
              role="button"
              tabindex="0"
              :data-testid="`volume-pulse-row-${row.label}`"
              @click="p.jumpToVolume(row)"
              @keydown.enter="p.jumpToVolume(row)"
            >
              <strong>{{ formatDisplayLabel(row.label) }}</strong>
              <span class="meta-line">{{ row.headline }}</span>
              <button
                v-if="p.uiProfile.volume_pulse_summary_generate"
                type="button"
                class="mini-btn pixel-border volume-pulse-generate-btn"
                :data-testid="`volume-pulse-generate-${row.label}`"
                @click.stop="p.generateVolumeSummaryForRow(row)"
              >
                生成摘要
              </button>
            </li>
          </ul>
          <button
            v-if="p.overview.volume_pulse.latest_summary"
            type="button"
            class="link-btn meta-line"
            data-testid="volume-pulse-jump-summary-btn"
            @click="p.openVolumeSummaryByName(p.overview.volume_pulse.latest_summary.name)"
          >
            最新摘要：{{ formatDisplayLabel(p.overview.volume_pulse.latest_summary.name) }}
          </button>
          </details>
        </div>

        <div
          v-if="p.isPulseSubpanelVisible('volumePlan')"
          class="pulse-desk__section pulse-desk__section--collapsible"
        >
          <details :open="!p.isPulseSubpanelCollapsed('volumePlan')">
            <summary class="pulse-desk__section-title pulse-desk__section-summary">卷纲</summary>
            <CreatorVolumePlanPanel hide-title />
          </details>
        </div>

        <div v-if="p.isPulseSubpanelVisible('deviationList')" class="pulse-desk__section">
          <CreatorDeviationList
            :deviations="p.visibleDeviations"
            :ui-profile="p.uiProfile"
            :highlight-enabled="p.deviationHighlightEnabled"
            :highlighted-chapter="p.highlightedDeviationChapter"
            @deviation-click="p.handleDeviationClick"
          />
        </div>

        <div v-if="p.isPulseSubpanelVisible('advanceBatch')" class="pulse-desk__section">
          <CreatorAdvanceBatchPanel
            :show-advance-batch="ab.showAdvanceBatch"
            :show-advance-batch-on-creator="ab.showAdvanceBatchOnCreator"
            v-model:batch-start="ab.batchStart"
            v-model:batch-end="ab.batchEnd"
            v-model:batch-budget="ab.batchBudget"
            :ui-profile="p.uiProfile"
            :batch-history-budget-hint="batchHistory.batchHistoryBudgetHint"
            :batch-running="ab.batchRunning"
            :preflight-ok="ab.preflightOk"
            :batch-command="ab.batchCommand"
            :batch-error="ab.batchError"
            :batch-job="ab.batchJob"
            @preflight="ab.runAdvancePreflight"
            @run-batch="ab.runAdvanceBatch"
            @go-produce="ab.goProduceConsole"
          />
        </div>

        <div v-if="p.isPulseSubpanelVisible('batchHistory')" class="pulse-desk__section">
          <CreatorBatchHistoryPanel />
        </div>

        <CreatorBatchSummaryPrompt
          :prompt="p.batchSummaryPrompt"
          :ui-profile="p.uiProfile"
          @open-summary="p.openVolumeSummaryForRange"
          @dismiss="p.dismissBatchSummaryPrompt"
        />

        <div
          v-if="p.isPulseSubpanelVisible('volumeSummaries') && p.overview.volume_summaries.length"
          class="pulse-desk__section"
        >
          <h3 class="pulse-desk__section-title">卷摘要</h3>
          <details
            v-for="vol in p.overview.volume_summaries"
            :key="vol.path"
            class="volume-block"
            :class="vol.pulse_status ? `volume-block--${vol.pulse_status}` : ''"
            :open="p.openVolumeSummaryName === vol.name"
            :data-testid="`volume-summary-block-${vol.name}`"
          >
            <summary>
              <span v-if="vol.volume_label" class="volume-summary-label">{{ formatDisplayLabel(vol.volume_label) }} · </span>
              {{ formatDisplayLabel(vol.name) }}
              <span v-if="vol.pulse_status" class="volume-summary-status">（{{ vol.pulse_status }}）</span>
            </summary>
            <pre class="volume-excerpt">{{ vol.excerpt }}</pre>
          </details>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { inject } from 'vue';
import { formatDisplayLabel } from '../../utils/displayProjectName.js';
import CreatorPulseIntro from './CreatorPulseIntro.vue';
import CreatorStructureGraph from './CreatorStructureGraph.vue';
import CreatorDeviationList from './CreatorDeviationList.vue';
import CreatorVolumePlanPanel from './CreatorVolumePlanPanel.vue';
import CreatorAdvanceBatchPanel from './CreatorAdvanceBatchPanel.vue';
import CreatorBatchHistoryPanel from './CreatorBatchHistoryPanel.vue';
import CreatorBatchSummaryPrompt from './CreatorBatchSummaryPrompt.vue';
import CreatorChapterTaskCards from './CreatorChapterTaskCards.vue';
import { CREATOR_PULSE_KEY } from './creatorPulseKey.js';
import { CREATOR_ADVANCE_BATCH_KEY } from './creatorAdvanceBatchKey.js';
import { CREATOR_BATCH_HISTORY_KEY } from './creatorBatchHistoryKey.js';
import { useDashboardNav } from '../../composables/useDashboardNav.js';

const p = inject(CREATOR_PULSE_KEY);
const ab = inject(CREATOR_ADVANCE_BATCH_KEY);
const batchHistory = inject(CREATOR_BATCH_HISTORY_KEY);
const { navigateTo } = useDashboardNav();

function onChapterTaskGenerate(chapter) {
  if (p.overview?.creation_mode === 'advance') {
    ab.batchStart = chapter;
    ab.batchEnd = chapter;
    ab.goProduceConsole();
    return;
  }
  p.setWorkspaceTab('write');
  navigateTo('creator', { workspace: 'write', chapter });
}

function onChapterTaskConfirm(chapter) {
  navigateTo('inbox', { tab: 'decisions', chapter });
}
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
  transition: box-shadow 0.2s ease;
}

.pulse-desk:hover {
  box-shadow: var(--shadow-elevated);
}

.pulse-desk--legacy {
  border: none;
  box-shadow: none;
  background: transparent;
  overflow: visible;
}

.pulse-desk--legacy .pulse-desk__scroll {
  overflow: visible;
  padding: 0;
}

.pulse-desk__hero {
  flex-shrink: 0;
  padding: var(--space-md) var(--space-lg);
  border-bottom: var(--border-width) solid var(--border-color);
  background: linear-gradient(180deg, var(--bg-primary) 0%, var(--bg-elevated) 100%);
}

.pulse-desk--legacy .pulse-desk__hero {
  padding: 0;
  border-bottom: none;
}

.pulse-desk__scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--space-md) var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  -webkit-overflow-scrolling: touch;
}

.pulse-desk__section {
  padding: var(--space-md);
  background: var(--bg-muted);
  border-radius: var(--radius-md);
  transition: all 0.2s ease;
}

.pulse-desk__section:hover {
  background: color-mix(in srgb, var(--bg-muted) 90%, var(--color-accent-soft) 10%);
}

.pulse-desk__section-title {
  font-size: var(--text-sm);
  font-weight: 700;
  margin: 0 0 var(--space-sm);
  color: var(--color-text);
}

.pulse-desk__section-summary {
  margin-bottom: 0;
  cursor: pointer;
  list-style: none;
  user-select: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 0;
}

.pulse-desk__section-summary::after {
  content: '›';
  font-size: var(--text-lg);
  color: var(--color-text-dim);
  transition: transform 0.2s ease;
}

details[open] .pulse-desk__section-summary::after {
  transform: rotate(90deg);
}

.pulse-desk__section-summary::-webkit-details-marker {
  display: none;
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

.volume-pulse-panel--alert {
  border-color: rgba(180, 35, 24, 0.3);
}

.volume-pulse-panel--warn {
  border-color: rgba(154, 103, 0, 0.3);
}

.volume-pulse-row--active {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
  border-radius: var(--radius-sm);
}

.volume-pulse-generate-btn {
  margin-left: var(--space-xs);
  font-size: var(--text-xs);
  padding: 4px 10px;
  border-radius: var(--radius-xs);
  transition: all 0.15s ease;
}

.volume-pulse-generate-btn:hover {
  background: var(--color-accent-soft);
}

.link-btn {
  background: none;
  border: none;
  padding: 0;
  color: var(--color-accent);
  text-decoration: none;
  cursor: pointer;
  font: inherit;
  transition: color 0.15s ease;
}

.link-btn:hover {
  color: var(--color-accent-hover);
  text-decoration: underline;
}

.volume-block {
  margin-bottom: var(--space-sm);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.volume-block--alert {
  background: rgba(180, 35, 24, 0.04);
}

.volume-block--warn {
  background: rgba(154, 103, 0, 0.04);
}

.volume-block--ok {
  background: rgba(46, 125, 90, 0.04);
}

.volume-block--alert summary {
  color: var(--color-danger);
}

.volume-block--warn summary {
  color: var(--color-warning);
}

.volume-block--ok summary {
  color: var(--color-success);
}

.volume-block summary {
  padding: 10px 12px;
  cursor: pointer;
  list-style: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.volume-block summary::-webkit-details-marker {
  display: none;
}

.volume-summary-status {
  opacity: 0.85;
  font-size: var(--text-xs);
}

.volume-excerpt {
  font-size: var(--text-sm);
  white-space: pre-wrap;
  margin: 0;
  padding: 12px;
  max-height: 200px;
  overflow: auto;
  background: var(--bg-elevated);
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

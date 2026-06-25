<!--
  CreatorPulsePanel.vue — 脉络栏（从 CreatorPage 拆出）
-->
<template>
  <section
    v-show="p.isWorkspaceColumnVisible('pulse')"
    class="creator-column pixel-card"
    data-testid="column-pulse"
  >
    <CreatorPulseIntro
      :overview="p.overview"
      :show-empty-guide="p.showPulseCompanionEmpty"
      @go-write="p.setWorkspaceTab('write')"
    />

    <div
      v-if="p.overview.volume_pulse?.volume_count"
      class="volume-pulse-panel pixel-border"
      :class="`volume-pulse-panel--${p.overview.volume_pulse.overall_status}`"
      data-testid="volume-pulse-panel"
    >
      <h3 class="subsection-title">卷级脉络</h3>
      <p class="meta-line" data-testid="volume-pulse-overall">
        <template v-if="p.overview.volume_pulse.alerts_only">
          {{ p.overview.volume_pulse.alert_count ? `${p.overview.volume_pulse.alert_count} 卷需关注` : '暂无 alert 级偏离' }}
        </template>
        <template v-else>
          {{ p.overview.volume_pulse.alert_count ? `${p.overview.volume_pulse.alert_count} 卷需关注` : '各卷按计划推进' }}
        </template>
      </p>
      <ul>
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
          <strong>{{ row.label }}</strong>
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
        最新摘要：{{ p.overview.volume_pulse.latest_summary.name }}
      </button>
    </div>

    <CreatorVolumePlanPanel />

    <CreatorDeviationList
      :deviations="p.visibleDeviations"
      :ui-profile="p.uiProfile"
      :highlight-enabled="p.deviationHighlightEnabled"
      :highlighted-chapter="p.highlightedDeviationChapter"
      @deviation-click="p.handleDeviationClick"
    />

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

    <CreatorBatchHistoryPanel />

    <CreatorBatchSummaryPrompt
      :prompt="p.batchSummaryPrompt"
      :ui-profile="p.uiProfile"
      @open-summary="p.openVolumeSummaryForRange"
      @dismiss="p.dismissBatchSummaryPrompt"
    />

    <template v-if="p.overview.volume_summaries.length">
      <h3 class="subsection-title">卷摘要</h3>
      <details
        v-for="vol in p.overview.volume_summaries"
        :key="vol.path"
        class="volume-block"
        :class="vol.pulse_status ? `volume-block--${vol.pulse_status}` : ''"
        :open="p.openVolumeSummaryName === vol.name"
        :data-testid="`volume-summary-block-${vol.name}`"
      >
        <summary>
          <span v-if="vol.volume_label" class="volume-summary-label">{{ vol.volume_label }} · </span>
          {{ vol.name }}
          <span v-if="vol.pulse_status" class="volume-summary-status">（{{ vol.pulse_status }}）</span>
        </summary>
        <pre class="volume-excerpt">{{ vol.excerpt }}</pre>
      </details>
    </template>
  </section>
</template>

<script setup>
import { inject } from 'vue';
import CreatorPulseIntro from './CreatorPulseIntro.vue';
import CreatorDeviationList from './CreatorDeviationList.vue';
import CreatorVolumePlanPanel from './CreatorVolumePlanPanel.vue';
import CreatorAdvanceBatchPanel from './CreatorAdvanceBatchPanel.vue';
import CreatorBatchHistoryPanel from './CreatorBatchHistoryPanel.vue';
import CreatorBatchSummaryPrompt from './CreatorBatchSummaryPrompt.vue';
import { CREATOR_PULSE_KEY } from './creatorPulseKey.js';
import { CREATOR_ADVANCE_BATCH_KEY } from './creatorAdvanceBatchKey.js';
import { CREATOR_BATCH_HISTORY_KEY } from './creatorBatchHistoryKey.js';

const p = inject(CREATOR_PULSE_KEY);
const ab = inject(CREATOR_ADVANCE_BATCH_KEY);
const batchHistory = inject(CREATOR_BATCH_HISTORY_KEY);
</script>

<style scoped>
.creator-column {
  padding: var(--space-md);
  min-height: 280px;
}

.subsection-title {
  font-size: var(--text-sm);
  margin: var(--space-md) 0 var(--space-xs);
}

.meta-line {
  font-size: var(--text-sm);
  opacity: 0.75;
}

.volume-pulse-row {
  cursor: pointer;
  padding-left: var(--space-xs);
  margin-bottom: var(--space-xs);
}

.volume-pulse-row--alert {
  border-left: 3px solid #c66;
}

.volume-pulse-row--warn {
  border-left: 3px solid #aa8;
}

.volume-pulse-row--ok {
  border-left: 3px solid #6a6;
}

.volume-pulse-panel--alert {
  border-color: #c66;
}

.volume-pulse-panel--warn {
  border-color: #aa8;
}

.volume-pulse-row--active {
  outline: 2px solid var(--color-accent);
}

.volume-pulse-generate-btn {
  margin-left: var(--space-xs);
  font-size: var(--text-xs);
}

.link-btn {
  background: none;
  border: none;
  padding: 0;
  color: inherit;
  text-decoration: underline;
  cursor: pointer;
  font: inherit;
}

.volume-block--alert summary {
  color: #c44;
}

.volume-block--warn summary {
  color: #886600;
}

.volume-block--ok summary {
  color: #3a7;
}

.volume-summary-status {
  opacity: 0.85;
  font-size: var(--text-xs);
}

.volume-excerpt {
  font-size: var(--text-sm);
  white-space: pre-wrap;
  margin: var(--space-xs) 0;
  max-height: 200px;
  overflow: auto;
}

.mini-btn {
  font-size: var(--text-xs);
  padding: 2px 6px;
  cursor: pointer;
}
</style>

<template>
  <div
    class="write-workbench"
    :class="{
      'write-workbench--collapsed': wb.leftPanelCollapsed,
      'write-workbench--human-first': wb.humanFirstDesk,
    }"
    data-testid="creator-write-workbench"
  >
    <aside class="write-workbench__left" data-testid="write-workbench-left">
      <button
        type="button"
        class="write-workbench__collapse-btn"
        data-testid="write-workbench-collapse-btn"
        :aria-label="wb.leftPanelCollapsed ? '展开左侧面板' : '折叠左侧面板'"
        :aria-expanded="!wb.leftPanelCollapsed"
        @click="wb.leftPanelCollapsed = !wb.leftPanelCollapsed"
      >
        {{ wb.leftPanelCollapsed ? '›' : '‹' }}
      </button>

      <template v-if="!wb.leftPanelCollapsed">
        <div class="write-workbench__tabs" role="tablist">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            type="button"
            class="write-workbench__tab"
            :class="{ 'write-workbench__tab--active': activeTab === tab.id }"
            role="tab"
            :aria-selected="activeTab === tab.id"
            :data-testid="`write-tab-${tab.id}`"
            @click="activeTab = tab.id"
          >
            <span class="write-workbench__tab-icon">{{ tab.icon }}</span>
            <span class="write-workbench__tab-label">{{ tab.label }}</span>
          </button>
        </div>

        <div class="write-workbench__tab-content">
          <div v-show="activeTab === 'write'" class="write-workbench__panel" data-testid="write-section-core">
            <div
              v-if="$slots.chapters"
              class="write-workbench__stack write-workbench__stack--chapters"
              data-testid="write-chapter-rail"
            >
              <p class="write-workbench__section-title">章节列表</p>
              <slot name="chapters" />
            </div>

            <div class="write-workbench__card" data-testid="write-goal-card">
              <p class="write-workbench__card-title">写作目标</p>
              <p class="meta-line">{{ wb.goalCardLines.line1 }}</p>
              <p class="meta-line">{{ wb.goalCardLines.line2 }}</p>
              <p class="meta-line">{{ wb.goalCardLines.line3 }}</p>
            </div>

            <div class="write-workbench__card" data-testid="write-intent-card">
              <p class="write-workbench__card-title">本章意图</p>
              <input
                v-model="wb.intentText"
                type="text"
                class="form-input pixel-border"
                placeholder="一句话描述本章要写什么…"
                data-testid="write-intent-input"
                aria-label="本章写作意图输入框"
                aria-describedby="write-intent-hint"
              />
              <div class="write-workbench__chips">
                <button
                  v-for="tag in moodTags"
                  :key="tag"
                  type="button"
                  class="write-workbench__chip"
                  :class="{ 'write-workbench__chip--active': wb.intentMood === tag }"
                  @click="wb.intentMood = wb.intentMood === tag ? '' : tag"
                >
                  {{ tag }}
                </button>
              </div>
              <button
                type="button"
                class="save-btn pixel-border"
                style="margin-top: 10px; width: 100%"
                data-testid="write-quick-start-btn"
                :disabled="wb.generateRunning"
                aria-label="一键开写，根据当前意图生成章节内容"
                :aria-busy="wb.generateRunning"
                @click="wb.startQuickWrite()"
              >
                开始写作
              </button>
            </div>

            <div
              v-if="wb.isPanelVisible('chapterEntityRail')"
              class="write-workbench__card"
              data-testid="write-chapter-entity-panel"
            >
              <p class="write-workbench__card-title">本章实体</p>
              <CreatorChapterEntityRail :entities="wb.chapterEntities" hide-title />
            </div>
          </div>

          <div v-show="activeTab === 'ai'" class="write-workbench__panel" data-testid="write-section-ai">
            <div
              v-if="wb.isLeftRailPanelVisible('directorPaths')"
              class="write-workbench__card"
              data-testid="write-director-paths-panel"
            >
              <p class="write-workbench__card-title">下一步路径</p>
              <CreatorDirectorPaths
                hide-title
                :paths="wb.agent.directorPaths"
                :advice="wb.agent.directorAdvice"
                :generating="wb.agent.generating"
                @run="wb.agent.runDirectorPath"
                @dismiss-advice="wb.agent.dismissAdvice"
              />
            </div>

            <div
              v-if="wb.isPanelVisible('selectionRewriteToolbar') && wb.hasBodySelection"
              class="write-workbench__card"
              data-testid="write-selection-tools"
            >
              <p class="write-workbench__card-title">选区微调</p>
              <div class="write-workbench__chips">
                <button
                  v-for="(label, id) in wb.agent.rewritePresets"
                  :key="id"
                  type="button"
                  class="write-workbench__chip"
                  :data-testid="`rewrite-preset-${id}`"
                  :disabled="wb.agent.generating"
                  :aria-label="`应用${label}改写预设`"
                  :aria-busy="wb.agent.generating"
                  @click="wb.agent.runRewritePreset(id)"
                >
                  {{ label }}
                </button>
              </div>
            </div>
          </div>

          <div v-show="activeTab === 'check'" class="write-workbench__panel" data-testid="write-section-consistency">
            <div
              v-if="wb.isLeftRailPanelVisible('consistencyRail')"
              class="write-workbench__card"
              data-testid="write-consistency-panel"
            >
              <p class="write-workbench__card-title">一致性检查</p>
              <CreatorConsistencyRail :items="wb.consistencyItems" hide-title />
            </div>
          </div>

          <div v-show="activeTab === 'version'" class="write-workbench__panel" data-testid="write-section-version">
            <div
              v-if="wb.isLeftRailPanelVisible('versionCheckpointList')"
              class="write-workbench__card"
            >
              <p class="write-workbench__card-title">版本历史</p>
              <ul v-if="wb.checkpoints.length" class="write-workbench__version-list">
                <li
                  v-for="cp in wb.checkpoints"
                  :key="cp.id"
                  class="write-workbench__version-item"
                >
                  <span>{{ cp.label }}</span>
                  <div class="write-workbench__version-actions">
                    <button
                      v-if="wb.isPanelVisible('checkpointDiff')"
                      type="button"
                      class="mini-btn pixel-border"
                      :data-testid="`checkpoint-diff-${cp.id}`"
                      @click="wb.openCheckpointDiff(cp.id)"
                    >
                      对比
                    </button>
                    <button type="button" class="mini-btn pixel-border" @click="wb.restoreCheckpoint(cp.id)">恢复</button>
                  </div>
                </li>
              </ul>
              <p v-else class="meta-line">确认应用后会在此记录回滚点</p>
              <CreatorCheckpointDiff
                v-if="wb.isPanelVisible('checkpointDiff')"
                :diff-view="wb.diffView"
                @close="wb.closeCheckpointDiff"
              />
              <button
                v-if="wb.agent.lastCheckpointId"
                type="button"
                class="mini-btn pixel-border"
                data-testid="write-undo-last-btn"
                @click="wb.agent.undoLastApply()"
              >
                撤销上次应用
              </button>
            </div>
          </div>
        </div>
      </template>
    </aside>

    <div class="write-workbench__main">
      <div class="write-workbench__header">
        <CreatorWriteScopeBar
          v-if="wb.isPanelVisible('scopeBar')"
          :scope="wb.agent.currentScope"
          :human-first="wb.humanFirstDesk"
        />

        <div class="write-workbench__header-actions">
          <div data-testid="companion-logic-check-write">
            <button
              type="button"
              class="write-workbench__action-btn"
              data-testid="run-companion-logic-check-btn"
              :disabled="w.logicCheckRunning"
              @click="w.runCompanionLogicCheck"
            >
              {{ w.logicCheckRunning ? '检查中…' : '逻辑审查' }}
            </button>
            <span
              v-if="w.logicCheckResult"
              class="write-workbench__header-status"
              data-testid="companion-logic-check-write-result"
            >
              {{ w.logicCheckResult.passed ? '通过' : '有问题' }}
            </span>
          </div>
        </div>
      </div>

      <div class="write-workbench__toolbar">
        <div class="write-workbench__toolbar-group">
          <span class="write-workbench__toolbar-label">文风</span>
          <input
            type="range"
            min="0"
            max="3"
            step="1"
            class="write-workbench__slider"
            data-testid="style-strength-slider"
            :value="wb.styleStrength"
            @input="wb.styleStrength = Number($event.target.value)"
          />
          <span class="write-workbench__slider-label">{{ strengthLabels[wb.styleStrength] }}</span>
        </div>
        <div class="write-workbench__toolbar-group">
          <button
            type="button"
            class="write-workbench__chip"
            :class="{ 'write-workbench__chip--active': wb.allowWorldbuildingFill }"
            data-testid="allow-worldbuilding-toggle"
            @click="wb.allowWorldbuildingFill = !wb.allowWorldbuildingFill"
          >
            补全设定
          </button>
        </div>
      </div>

      <CreatorWriteMicroTaskBar
        v-if="wb.isPanelVisible('microTaskBar') && wb.humanFirstDesk"
        :draft="w.chapterBodyDraft"
        :creation-mode="w.overview?.creation_mode || 'companion'"
      />

      <CreatorLightValidationBar
        v-if="wb.isPanelVisible('lightValidationBar') && w.selectedChapter"
        :issues="wb.lightValidationIssues"
        :running="wb.lightValidationRunning"
        @focus="wb.focusLightValidationIssue"
      />

      <div class="write-workbench__editor-wrapper">
        <div class="write-workbench__editor-slot write-workbench__editor-slot--primary">
          <slot />
        </div>
      </div>

      <div class="write-workbench__footer">
        <div
          v-if="wb.isPanelVisible('qualityFeedbackBar') && (wb.agent.statusLine || wb.qualityHints.length)"
          class="write-workbench__quality"
          data-testid="write-quality-bar-main"
        >
          <span class="write-workbench__quality-label">写作反馈</span>
          <span v-if="wb.agent.statusLine" class="meta-line">{{ wb.agent.statusLine }}</span>
          <span
            v-for="(hint, idx) in wb.qualityHints"
            :key="idx"
            class="write-workbench__quality-item"
            :class="`write-workbench__quality-item--${hint.level}`"
          >
            {{ hint.text }}
            <button type="button" class="mini-btn" @click="wb.dismissQualityHint(idx)">忽略</button>
          </span>
        </div>

        <div class="write-workbench__action-bar">
          <button
            type="button"
            class="write-workbench__btn-primary"
            data-testid="write-generate-btn"
            :disabled="wb.generateRunning || wb.agent.generating"
            @click="wb.startQuickWrite()"
          >
            {{ wb.generateRunning ? '生成中…' : '✨ AI生成' }}
          </button>

          <div class="write-workbench__btn-group">
            <button
              type="button"
              class="write-workbench__btn-secondary"
              :disabled="!wb.agent.lastCheckpointId"
              data-testid="write-undo-last-btn"
              @click="wb.agent.undoLastApply()"
            >
              撤销
            </button>
            <button
              type="button"
              class="write-workbench__btn-secondary"
              @click="showAdvancePanel = !showAdvancePanel"
            >
              {{ showAdvancePanel ? '收起' : '更多' }}
            </button>
          </div>
        </div>

        <div v-if="showAdvancePanel" class="write-workbench__advance-panel">
          <div class="write-workbench__advance-section">
            <p class="write-workbench__advance-title">补充指令</p>
            <form class="write-workbench__agent-form" @submit.prevent="wb.agent.submitPrompt()">
              <input
                v-model="wb.agent.promptInput"
                type="text"
                class="form-input pixel-border"
                placeholder="输入补充指令…"
                data-testid="write-agent-input"
              />
              <button type="submit" class="save-btn pixel-border" data-testid="write-agent-send-btn">发送</button>
            </form>
          </div>

          <div v-if="wb.agent.pendingPlan && !wb.agent.pendingPlan.adviceOnly" class="write-workbench__plan-card">
            <p class="write-workbench__card-title">确认应用</p>
            <p class="meta-line">将对 <strong>{{ wb.agent.pendingPlan.scope?.label }}</strong> 执行：{{ wb.agent.pendingPlan.actionLabel }}</p>
            <p class="meta-line">{{ wb.agent.statusLine }}</p>
            <div class="write-workbench__toolbar-group">
              <button type="button" class="save-btn pixel-border" data-testid="write-director-confirm-btn" :disabled="!wb.agent.pendingPlan?.selectedCandidateId" @click="wb.agent.confirmApply()">确认应用</button>
              <button type="button" class="save-btn save-btn--secondary pixel-border" @click="wb.agent.cancelPlan()">取消</button>
            </div>
          </div>

          <div v-if="wb.isPanelVisible('candidatePreviewDock') && wb.agent.candidates.length" class="write-workbench__card">
            <p class="write-workbench__card-title">候选预览（{{ wb.agent.candidates.length }}）</p>
            <div class="write-workbench__candidates">
              <button
                v-for="cand in wb.agent.candidates"
                :key="cand.id"
                type="button"
                class="write-workbench__candidate"
                :class="{ 'write-workbench__candidate--selected': wb.agent.pendingPlan?.selectedCandidateId === cand.id }"
                :data-testid="`write-candidate-${cand.id}`"
                @click="wb.agent.selectCandidate(cand.id)"
              >
                <strong>{{ cand.label }}</strong> · {{ cand.direction }}
                <pre class="preview-text">{{ cand.text.slice(0, 120) }}…</pre>
              </button>
            </div>
          </div>

          <CreatorAgentAnnotations
            v-if="wb.isPanelVisible('agentLensSwitcher') && wb.agent.annotations.length"
            main-bar
            :annotations="wb.agent.annotations"
            :lens="wb.agent.agentLens"
            @focus="wb.agent.focusAnnotation"
          />

          <CreatorAgentStreamPreview
            v-if="showAgentStreamPreview"
            main-bar
            :preview-text="wb.agent.streamPreviewText"
            :display-text="wb.agent.streamDisplayText"
            :preview-label="wb.agent.streamPreviewLabel"
            :stream-source="wb.agent.streamSource"
            :advice-lines="wb.agent.streamAdvicePreview"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, inject, ref } from 'vue';
import { CREATOR_WRITE_KEY } from './creatorWriteKey.js';
import CreatorAgentStreamPreview from './CreatorAgentStreamPreview.vue';
import CreatorWriteScopeBar from './CreatorWriteScopeBar.vue';
import CreatorWriteMicroTaskBar from './CreatorWriteMicroTaskBar.vue';
import CreatorLightValidationBar from './CreatorLightValidationBar.vue';
import CreatorDirectorPaths from './CreatorDirectorPaths.vue';
import CreatorAgentAnnotations from './CreatorAgentAnnotations.vue';
import CreatorConsistencyRail from './CreatorConsistencyRail.vue';
import CreatorCheckpointDiff from './CreatorCheckpointDiff.vue';
import CreatorChapterEntityRail from './CreatorChapterEntityRail.vue';
import '../../assets/creator-write-workbench.css';

const w = inject(CREATOR_WRITE_KEY);
const wb = w.wb;
const showAdvancePanel = ref(false);
const activeTab = ref('write');

const tabs = [
  { id: 'write', label: '写作', icon: '✎' },
  { id: 'ai', label: 'AI', icon: '⚡' },
  { id: 'check', label: '检查', icon: '✓' },
  { id: 'version', label: '版本', icon: '◇' },
];

const strengthLabels = ['自然', '略强', '较强', '强烈'];

const showAgentStreamPreview = computed(() => {
  const agent = wb.agent;
  const previewText = agent.streamPreviewText?.value ?? agent.streamPreviewText ?? '';
  const advice = agent.streamAdvicePreview?.value ?? agent.streamAdvicePreview ?? [];
  const generating = agent.generating?.value ?? agent.generating ?? false;
  return Boolean(generating && (previewText || advice.length));
});

const moodTags = ['克制', '戏剧', '幽默', '抒情'];
</script>

<style scoped>
.meta-line {
  margin: 0;
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}
.form-input {
  width: 100%;
  font-size: var(--text-sm);
  padding: 6px 8px;
}
.mini-btn {
  font-size: var(--text-xs);
  padding: 2px 6px;
  cursor: pointer;
}
.save-btn {
  font-size: var(--text-sm);
  padding: 6px 14px;
  cursor: pointer;
}
.preview-text {
  white-space: pre-wrap;
  font-size: 10px;
  margin: 4px 0 0;
}
.write-workbench__version-actions {
  display: flex;
  gap: 4px;
}

.write-workbench__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: var(--space-sm);
  border-bottom: var(--border-width) solid var(--border-color);
  margin-bottom: var(--space-sm);
}

.write-workbench__header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.write-workbench__action-btn {
  font-size: var(--text-sm);
  padding: 6px 14px;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-sm);
  background: var(--bg-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.write-workbench__action-btn:hover:not(:disabled) {
  background: var(--color-accent-soft);
  color: var(--color-accent);
  border-color: var(--color-accent-muted);
}

.write-workbench__header-status {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.write-workbench__toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-muted);
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-sm);
}

.write-workbench__toolbar-group {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.write-workbench__toolbar-label {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  font-weight: 500;
}

.write-workbench__slider {
  width: 100px;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--border-color);
  border-radius: 999px;
  outline: none;
}

.write-workbench__slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--gradient-accent);
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(168, 90, 50, 0.3);
}

.write-workbench__slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--gradient-accent);
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 6px rgba(168, 90, 50, 0.3);
}

.write-workbench__slider-label {
  font-size: var(--text-xs);
  color: var(--color-accent);
  font-weight: 500;
  min-width: 36px;
}

.write-workbench__editor-wrapper {
  flex: 1;
  min-height: 400px;
  overflow-y: auto;
}

.write-workbench__footer {
  margin-top: var(--space-md);
  border-top: var(--border-width) solid var(--border-color);
  padding-top: var(--space-md);
}

.write-workbench__quality {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  align-items: center;
  padding: var(--space-sm) var(--space-md);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-sm);
  background: var(--bg-muted);
  font-size: var(--text-xs);
  margin-bottom: var(--space-md);
}

.write-workbench__quality-label {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-accent);
  margin-right: var(--space-sm);
}

.write-workbench__quality-item--ok { color: var(--color-success); }
.write-workbench__quality-item--warn { color: var(--color-warning); }
.write-workbench__quality-item--info { color: var(--color-text-dim); }

.write-workbench__action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-md);
}

.write-workbench__btn-primary {
  font-size: var(--text-base);
  font-weight: 600;
  padding: 10px 24px;
  background: var(--gradient-accent);
  color: var(--color-on-accent);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
}

.write-workbench__btn-primary:hover:not(:disabled) {
  filter: brightness(1.08);
  box-shadow: 0 4px 16px rgba(168, 90, 50, 0.2);
}

.write-workbench__btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.write-workbench__btn-group {
  display: flex;
  gap: 8px;
}

.write-workbench__btn-secondary {
  font-size: var(--text-sm);
  padding: 8px 16px;
  background: var(--bg-muted);
  color: var(--color-text-secondary);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s ease;
}

.write-workbench__btn-secondary:hover:not(:disabled) {
  background: var(--color-accent-soft);
  color: var(--color-accent);
  border-color: var(--color-accent-muted);
}

.write-workbench__btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.write-workbench__advance-panel {
  margin-top: var(--space-md);
  padding: var(--space-md);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.write-workbench__advance-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.write-workbench__advance-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.write-workbench__agent-form {
  display: flex;
  gap: 8px;
}

.write-workbench__agent-form .form-input {
  flex: 1;
}
</style>

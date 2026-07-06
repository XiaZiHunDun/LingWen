<!--
  CreatorWriteWorkbench.vue — 写作导演工作台（左栈 + 右编辑器 · P0）
-->
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
        @click="wb.leftPanelCollapsed = !wb.leftPanelCollapsed"
      >
        {{ wb.leftPanelCollapsed ? '»' : '«' }}
      </button>

      <template v-if="!wb.leftPanelCollapsed">
        <div
          v-if="$slots.chapters"
          class="write-workbench__stack write-workbench__stack--chapters"
          data-testid="write-chapter-rail"
        >
          <p class="write-workbench__card-title write-workbench__rail-label">章节</p>
          <slot name="chapters" />
        </div>

        <details
          v-if="wb.isLeftRailPanelVisible('goalCard')"
          class="write-workbench__stack write-workbench__card"
          data-testid="write-goal-card"
          :open="!wb.isPanelCollapsed('goalCard')"
        >
          <summary class="write-workbench__card-title">写作目标</summary>
          <p class="meta-line">{{ wb.goalCardLines.line1 }}</p>
          <p class="meta-line">{{ wb.goalCardLines.line2 }}</p>
          <p class="meta-line">{{ wb.goalCardLines.line3 }}</p>
        </details>

        <div
          v-if="wb.isLeftRailPanelVisible('directorPaths')"
          class="write-workbench__stack write-workbench__stack--grow"
        >
          <details
            class="write-workbench__card write-workbench__paths-details"
            :open="!wb.isPanelCollapsed('directorPaths')"
            data-testid="write-director-paths-panel"
          >
            <summary class="write-workbench__card-title">下一步路径（可选）</summary>
            <CreatorDirectorPaths
              hide-title
              :paths="wb.agent.directorPaths"
              :advice="wb.agent.directorAdvice"
              :generating="wb.agent.generating"
              @run="wb.agent.runDirectorPath"
              @dismiss-advice="wb.agent.dismissAdvice"
            />
          </details>

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
                @click="wb.agent.runRewritePreset(id)"
              >
                {{ label }}
              </button>
            </div>
          </div>

          <details
            v-else-if="wb.isPanelVisible('intentInput')"
            class="write-workbench__card"
            data-testid="write-intent-card"
            :open="!wb.isPanelCollapsed('intentInput')"
          >
            <summary class="write-workbench__card-title">本章意图</summary>
            <input
              v-model="wb.intentText"
              type="text"
              class="form-input pixel-border"
              placeholder="一句话描述本章要写什么…"
              data-testid="write-intent-input"
            />
            <div v-if="!wb.humanFirstDesk" class="write-workbench__chips">
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
              v-if="!wb.humanFirstDesk"
              type="button"
              class="save-btn pixel-border"
              style="margin-top: 8px"
              data-testid="write-quick-start-btn"
              :disabled="wb.generateRunning"
              @click="wb.startQuickWrite()"
            >
              一键开写
            </button>
          </details>
        </div>

        <details
          v-if="wb.isLeftRailPanelVisible('chapterEntityRail')"
          class="write-workbench__stack write-workbench__card"
          data-testid="write-chapter-entity-panel"
          :open="!wb.isPanelCollapsed('chapterEntityRail')"
        >
          <summary class="write-workbench__card-title">
            <FieldHint label="本章实体" hint="本章正文中出现的人物、地点与道具，便于对照设定。" test-id="hint-chapter-entity">
              本章实体
            </FieldHint>
          </summary>
          <CreatorChapterEntityRail :entities="wb.chapterEntities" hide-title />
        </details>

        <details
          v-if="wb.isLeftRailPanelVisible('consistencyRail')"
          class="write-workbench__stack write-workbench__card"
          data-testid="write-consistency-panel"
          :open="wb.consistencyPanelOpen"
        >
          <summary class="write-workbench__card-title">
            <FieldHint label="本章一致性" hint="与设定、时间线或前文冲突的预警，有项时会自动展开。" test-id="hint-consistency">
              本章一致性
            </FieldHint>
          </summary>
          <CreatorConsistencyRail :items="wb.consistencyItems" hide-title />
        </details>

        <div v-if="wb.isLeftRailPanelVisible('versionCheckpointList')" class="write-workbench__stack" data-testid="write-version-stack">
          <details
            class="write-workbench__card"
            :open="!wb.isPanelCollapsed('versionCheckpointList')"
          >
            <summary class="write-workbench__card-title">版本 / 回滚</summary>
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
          </details>
        </div>
      </template>
    </aside>

    <div class="write-workbench__main">
      <CreatorWriteScopeBar
        v-if="wb.isPanelVisible('scopeBar')"
        :scope="wb.agent.currentScope"
        :human-first="wb.humanFirstDesk"
      />

      <CreatorWriteMicroTaskBar
        v-if="wb.isPanelVisible('microTaskBar') && wb.humanFirstDesk"
        :draft="w.chapterBodyDraft"
        :creation-mode="w.overview?.creation_mode || 'companion'"
      />

      <div
        v-if="wb.humanFirstDesk && w.showCompanionLogicCheckInWrite"
        class="write-desk-toolbar"
        data-testid="companion-logic-check-write"
      >
        <button
          type="button"
          class="write-desk-toolbar__pill"
          data-testid="run-companion-logic-check-btn"
          :disabled="w.logicCheckRunning"
          @click="w.runCompanionLogicCheck"
        >
          {{ w.logicCheckRunning ? '检查中…' : '逻辑审查' }}
        </button>
        <span
          v-if="w.logicCheckResult"
          class="write-desk-toolbar__status meta-line"
          data-testid="companion-logic-check-write-result"
        >
          {{ w.logicCheckResult.passed ? '通过' : '未通过' }} · P0 {{ w.logicCheckResult.p0_count }}
        </span>
        <details
          v-if="w.uiProfile.logic_check_inline_issues && w.logicCheckResult?.issues?.length"
          class="write-desk-toolbar__issues"
        >
          <summary class="meta-line">{{ w.logicCheckResult.issues.length }} 条问题</summary>
          <ul class="logic-check-issues" data-testid="logic-check-issues">
            <li
              v-for="(issue, idx) in w.logicCheckResult.issues"
              :key="`write-${issue.chapter}-${idx}`"
              class="logic-check-issue"
              :class="{
                'logic-check-issue--clickable': Boolean(issue.chapter),
                'logic-check-issue--active': !w.uiProfile.issue_paragraph_highlight_unified
                  && w.uiProfile.logic_check_issue_highlight
                  && w.activeLogicCheckIssueIdx === idx,
                'issue-line--active': w.uiProfile.issue_paragraph_highlight_unified
                  && w.activeLogicCheckIssueIdx === idx,
              }"
              role="button"
              tabindex="0"
              :data-testid="`logic-check-issue-${idx}`"
              @click="w.handleLogicCheckIssueClick(issue, idx)"
              @keydown.enter="w.handleLogicCheckIssueClick(issue, idx)"
              @keydown="w.onLogicCheckIssueKeydown($event, issue, idx)"
            >
              <span class="issue-severity">{{ issue.severity }}</span>
              <span v-if="issue.chapter">ch{{ String(issue.chapter).padStart(3, '0') }}</span>
              {{ issue.title || issue.message }}
            </li>
          </ul>
        </details>
      </div>

      <div class="write-workbench__editor-slot write-workbench__editor-slot--primary">
        <slot />
      </div>

      <details
        v-if="wb.humanFirstDesk"
        class="write-workbench__advanced"
        data-testid="write-advanced-tools"
        @toggle="onAdvancedToggle"
      >
        <summary class="write-workbench__advanced-summary">写作工具（透镜 · 生成 · 候选）</summary>
        <div v-if="advancedToolsOpen" class="write-workbench__advanced-body">
          <CreatorWriteControlStrip
            v-if="wb.isPanelVisible('controlStrip')"
            :style-strength="wb.styleStrength"
            :selection-locked="wb.selectionLocked"
            :allow-worldbuilding-fill="wb.allowWorldbuildingFill"
            :goal-tag="wb.goalTag"
            :agent-lens="wb.agent.agentLens"
            :show-lens="wb.isPanelVisible('agentLensSwitcher')"
            @update:style-strength="wb.styleStrength = $event"
            @update:allow-worldbuilding-fill="wb.allowWorldbuildingFill = $event"
            @update:goal-tag="wb.goalTag = $event"
            @update:agent-lens="wb.agent.setAgentLens($event)"
            @toggle-lock="wb.toggleSelectionLock()"
          />

          <div
            v-if="wb.isPanelVisible('generateToolbar')"
            class="write-workbench__toolbar"
            data-testid="write-generate-toolbar"
          >
            <div class="write-workbench__toolbar-group">
              <button
                type="button"
                class="save-btn pixel-border"
                data-testid="write-generate-btn"
                :disabled="wb.generateRunning || wb.agent.generating"
                @click="wb.startQuickWrite()"
              >
                生成
              </button>
              <button
                type="button"
                class="mini-btn pixel-border"
                data-testid="write-stop-btn"
                :disabled="!wb.generateRunning && !wb.agent.generating"
                @click="wb.stopGenerate()"
              >
                停止
              </button>
            </div>
            <div class="write-workbench__toolbar-group">
              <button
                type="button"
                class="mini-btn pixel-border"
                data-testid="write-agent-mode-toggle"
                @click="wb.agent.toggleExecutionMode()"
              >
                {{ wb.agent.isPreviewMode ? '预览(A)' : '应用(B2)' }}
              </button>
            </div>
          </div>

          <details
            v-if="wb.isPanelVisible('agentSessionStrip')"
            class="write-workbench__agent"
            data-testid="write-agent-strip"
            :open="wb.agent.agentExpanded"
            @toggle="onAgentToggle"
          >
            <summary class="write-workbench__agent-summary">高级指令（可选）</summary>
            <div class="write-workbench__agent-body">
              <form class="write-workbench__toolbar-group" @submit.prevent="wb.agent.submitPrompt()">
                <input
                  v-model="wb.agent.promptInput"
                  type="text"
                  class="form-input pixel-border"
                  placeholder="补充指令，例如：信息披露再晚一句…"
                  data-testid="write-agent-input"
                />
                <button type="submit" class="mini-btn pixel-border" data-testid="write-agent-send-btn">发送</button>
              </form>
            </div>
          </details>

          <CreatorAgentAnnotations
            v-if="wb.isPanelVisible('agentLensSwitcher') && wb.agent.annotations.length"
            :annotations="wb.agent.annotations"
            :lens="wb.agent.agentLens"
            @focus="wb.agent.focusAnnotation"
          />

          <div
            v-if="wb.agent.pendingPlan && !wb.agent.pendingPlan.adviceOnly"
            class="write-workbench__plan-card"
            data-testid="write-director-plan-card"
          >
            <p class="meta-line">
              将对 <strong>{{ wb.agent.pendingPlan.scope?.label }}</strong>
              执行：{{ wb.agent.pendingPlan.actionLabel }}
            </p>
            <p class="meta-line">{{ wb.agent.statusLine }}</p>
            <div class="write-workbench__toolbar-group">
              <button
                type="button"
                class="save-btn pixel-border"
                data-testid="write-director-confirm-btn"
                :disabled="!wb.agent.pendingPlan?.selectedCandidateId"
                @click="wb.agent.confirmApply()"
              >
                确认应用
              </button>
              <button type="button" class="mini-btn pixel-border" @click="wb.agent.cancelPlan()">取消</button>
            </div>
          </div>

          <div
            v-if="wb.isPanelVisible('candidatePreviewDock') && wb.agent.candidates.length"
            class="write-workbench__card"
            data-testid="write-candidate-dock"
          >
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

          <div
            v-if="wb.isPanelVisible('qualityFeedbackBar') && (wb.agent.statusLine || wb.qualityHints.length)"
            class="write-workbench__quality"
            data-testid="write-quality-bar"
          >
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
        </div>
      </details>

      <template v-else>
        <CreatorWriteControlStrip
          v-if="wb.isPanelVisible('controlStrip')"
          :style-strength="wb.styleStrength"
          :selection-locked="wb.selectionLocked"
          :allow-worldbuilding-fill="wb.allowWorldbuildingFill"
          :goal-tag="wb.goalTag"
          :agent-lens="wb.agent.agentLens"
          :show-lens="wb.isPanelVisible('agentLensSwitcher')"
          @update:style-strength="wb.styleStrength = $event"
          @update:allow-worldbuilding-fill="wb.allowWorldbuildingFill = $event"
          @update:goal-tag="wb.goalTag = $event"
          @update:agent-lens="wb.agent.setAgentLens($event)"
          @toggle-lock="wb.toggleSelectionLock()"
        />

        <div
          v-if="wb.isPanelVisible('generateToolbar')"
          class="write-workbench__toolbar"
          data-testid="write-generate-toolbar"
        >
          <div class="write-workbench__toolbar-group">
            <button
              type="button"
              class="save-btn pixel-border"
              data-testid="write-generate-btn"
              :disabled="wb.generateRunning || wb.agent.generating"
              @click="wb.startQuickWrite()"
            >
              生成
            </button>
            <button
              type="button"
              class="mini-btn pixel-border"
              data-testid="write-stop-btn"
              :disabled="!wb.generateRunning && !wb.agent.generating"
              @click="wb.stopGenerate()"
            >
              停止
            </button>
          </div>
          <div class="write-workbench__toolbar-group">
            <button
              type="button"
              class="mini-btn pixel-border"
              data-testid="write-agent-mode-toggle"
              @click="wb.agent.toggleExecutionMode()"
            >
              {{ wb.agent.isPreviewMode ? '预览(A)' : '应用(B2)' }}
            </button>
          </div>
        </div>

        <details
          v-if="wb.isPanelVisible('agentSessionStrip')"
          class="write-workbench__agent"
          data-testid="write-agent-strip"
          :open="wb.agent.agentExpanded"
          @toggle="onAgentToggle"
        >
          <summary class="write-workbench__agent-summary">高级指令（可选）</summary>
          <div class="write-workbench__agent-body">
            <form class="write-workbench__toolbar-group" @submit.prevent="wb.agent.submitPrompt()">
              <input
                v-model="wb.agent.promptInput"
                type="text"
                class="form-input pixel-border"
                placeholder="补充指令，例如：信息披露再晚一句…"
                data-testid="write-agent-input"
              />
              <button type="submit" class="mini-btn pixel-border" data-testid="write-agent-send-btn">发送</button>
            </form>
          </div>
        </details>
      </template>

      <template v-if="!wb.humanFirstDesk">
        <CreatorAgentAnnotations
          v-if="wb.isPanelVisible('agentLensSwitcher') && wb.agent.annotations.length"
          :annotations="wb.agent.annotations"
          :lens="wb.agent.agentLens"
          @focus="wb.agent.focusAnnotation"
        />

        <div
          v-if="wb.agent.pendingPlan && !wb.agent.pendingPlan.adviceOnly"
          class="write-workbench__plan-card"
          data-testid="write-director-plan-card"
        >
          <p class="meta-line">
            将对 <strong>{{ wb.agent.pendingPlan.scope?.label }}</strong>
            执行：{{ wb.agent.pendingPlan.actionLabel }}
          </p>
          <p class="meta-line">{{ wb.agent.statusLine }}</p>
          <div class="write-workbench__toolbar-group">
            <button
              type="button"
              class="save-btn pixel-border"
              data-testid="write-director-confirm-btn"
              :disabled="!wb.agent.pendingPlan?.selectedCandidateId"
              @click="wb.agent.confirmApply()"
            >
              确认应用
            </button>
            <button type="button" class="mini-btn pixel-border" @click="wb.agent.cancelPlan()">取消</button>
          </div>
        </div>

        <div
          v-if="wb.isPanelVisible('candidatePreviewDock') && wb.agent.candidates.length"
          class="write-workbench__card"
          data-testid="write-candidate-dock"
        >
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

        <div
          v-if="wb.isPanelVisible('qualityFeedbackBar')"
          class="write-workbench__quality"
          data-testid="write-quality-bar"
        >
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
      </template>
    </div>
  </div>
</template>

<script setup>
import { inject, ref } from 'vue';
import { CREATOR_WRITE_KEY } from './creatorWriteKey.js';
import CreatorWriteScopeBar from './CreatorWriteScopeBar.vue';
import CreatorWriteMicroTaskBar from './CreatorWriteMicroTaskBar.vue';
import CreatorDirectorPaths from './CreatorDirectorPaths.vue';
import CreatorWriteControlStrip from './CreatorWriteControlStrip.vue';
import CreatorAgentAnnotations from './CreatorAgentAnnotations.vue';
import CreatorConsistencyRail from './CreatorConsistencyRail.vue';
import CreatorCheckpointDiff from './CreatorCheckpointDiff.vue';
import CreatorChapterEntityRail from './CreatorChapterEntityRail.vue';
import FieldHint from '../FieldHint.vue';
import '../../assets/creator-write-workbench.css';

const w = inject(CREATOR_WRITE_KEY);
const wb = w.wb;
const advancedToolsOpen = ref(false);

const moodTags = ['克制', '戏剧', '幽默', '抒情'];

function onAdvancedToggle(event) {
  advancedToolsOpen.value = event.target.open;
}

function onAgentToggle(event) {
  wb.agent.agentExpanded = event.target.open;
}
</script>

<style scoped>
.meta-line {
  margin: 0;
  font-size: var(--text-xs);
  color: var(--color-text-dim);
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
  font-size: var(--text-xs);
  padding: 4px 10px;
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

.write-desk-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-xs) var(--space-sm);
}

.write-desk-toolbar__pill {
  font-size: var(--text-xs);
  padding: 6px 14px;
  border: none;
  border-radius: 999px;
  background: var(--bg-muted);
  cursor: pointer;
}

.logic-check-issues {
  margin: var(--space-xs) 0 0;
  padding: 0;
  list-style: none;
}

.logic-check-issue {
  font-size: var(--text-xs);
  margin-bottom: 4px;
}
</style>

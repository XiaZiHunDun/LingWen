<!--
  CreatorWriteWorkbench.vue — 写作导演工作台（Tab式左面板 + 右编辑器）
  布局结构：
    左侧面板：Tab切换（写作 / AI / 检查 / 版本），每次只显示一个面板
    主区域：顶部工具栏 → 编辑区 → 底部AI工具（可折叠）
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
        :aria-label="wb.leftPanelCollapsed ? '展开左侧面板' : '折叠左侧面板'"
        :aria-expanded="!wb.leftPanelCollapsed"
        @click="wb.leftPanelCollapsed = !wb.leftPanelCollapsed"
      >
        {{ wb.leftPanelCollapsed ? '»' : '«' }}
      </button>

      <template v-if="!wb.leftPanelCollapsed">
        <!-- Tab 导航 -->
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

        <!-- Tab 内容区 -->
        <div class="write-workbench__tab-content">
          <!-- 写作核心 -->
          <div v-show="activeTab === 'write'" class="write-workbench__panel" data-testid="write-section-core">
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
              class="write-workbench__card"
              data-testid="write-goal-card"
              :open="!wb.isPanelCollapsed('goalCard')"
            >
              <summary class="write-workbench__card-title">写作目标</summary>
              <p class="meta-line">{{ wb.goalCardLines.line1 }}</p>
              <p class="meta-line">{{ wb.goalCardLines.line2 }}</p>
              <p class="meta-line">{{ wb.goalCardLines.line3 }}</p>
            </details>

            <details
              v-if="wb.isPanelVisible('intentInput')"
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
                aria-label="本章写作意图输入框"
                aria-describedby="write-intent-hint"
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
                aria-label="一键开写，根据当前意图生成章节内容"
                :aria-busy="wb.generateRunning"
                @click="wb.startQuickWrite()"
              >
                一键开写
              </button>
            </details>

            <details
              v-if="wb.isPanelVisible('chapterEntityRail')"
              class="write-workbench__card"
              data-testid="write-chapter-entity-panel"
              :open="!wb.isPanelCollapsed('chapterEntityRail')"
            >
              <summary
                class="write-workbench__card-title"
                title="本章正文中出现的人物、地点与道具，便于对照设定。"
              >
                本章实体
              </summary>
              <CreatorChapterEntityRail :entities="wb.chapterEntities" hide-title />
            </details>
          </div>

          <!-- AI 辅助 -->
          <div v-show="activeTab === 'ai'" class="write-workbench__panel" data-testid="write-section-ai">
            <details
              v-if="wb.isLeftRailPanelVisible('directorPaths')"
              class="write-workbench__card"
              data-testid="write-director-paths-panel"
              :open="!wb.isPanelCollapsed('directorPaths')"
            >
              <summary class="write-workbench__card-title">下一步路径</summary>
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
                  :aria-label="`应用${label}改写预设`"
                  :aria-busy="wb.agent.generating"
                  @click="wb.agent.runRewritePreset(id)"
                >
                  {{ label }}
                </button>
              </div>
            </div>
          </div>

          <!-- 一致性检查 -->
          <div v-show="activeTab === 'check'" class="write-workbench__panel" data-testid="write-section-consistency">
            <details
              v-if="wb.isLeftRailPanelVisible('consistencyRail')"
              class="write-workbench__card"
              data-testid="write-consistency-panel"
              :open="wb.consistencyPanelOpen"
            >
              <summary
                class="write-workbench__card-title"
                title="与设定、时间线或前文冲突的预警，有项时会自动展开。"
              >
                本章一致性
              </summary>
              <CreatorConsistencyRail :items="wb.consistencyItems" hide-title />
            </details>
          </div>

          <!-- 版本管理 -->
          <div v-if="wb.isLeftRailPanelVisible('versionCheckpointList')" v-show="activeTab === 'version'" class="write-workbench__panel" data-testid="write-section-version">
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
        </div>
      </template>
    </aside>

    <div class="write-workbench__main">
      <!-- 顶部工具栏 -->
      <div class="write-workbench__top-bar">
        <CreatorWriteScopeBar
          v-if="wb.isPanelVisible('scopeBar')"
          :scope="wb.agent.currentScope"
          :human-first="wb.humanFirstDesk"
        />

        <CreatorWriteControlStrip
          v-if="wb.isPanelVisible('controlStrip')"
          main-bar
          :show-lens="wb.isPanelVisible('agentLensSwitcher')"
          :show-strength="true"
          :show-toggles="false"
          :show-worldbuilding-toggle="true"
          :show-goal-tags="true"
          :style-strength="wb.styleStrength"
          :goal-tag="wb.goalTag"
          :agent-lens="wb.agent.agentLens"
          :allow-worldbuilding-fill="wb.allowWorldbuildingFill"
          :selection-locked="wb.selectionLocked"
          @update:style-strength="wb.styleStrength = $event"
          @update:goal-tag="wb.goalTag = $event"
          @update:agent-lens="wb.agent.setAgentLens($event)"
          @update:allow-worldbuilding-fill="wb.allowWorldbuildingFill = $event"
          @toggle-lock="wb.toggleSelectionLock()"
        />

        <div
          v-if="wb.isPanelVisible('selectionRewriteToolbar') && wb.hasBodySelection && wb.humanFirstDesk"
          class="write-workbench__card write-workbench__selection-tools"
          data-testid="write-selection-tools-main"
        >
          <div class="write-workbench__selection-toolbar">
            <p class="write-workbench__card-title">选区微调</p>
            <button
              type="button"
              class="write-workbench__chip"
              :class="{ 'write-workbench__chip--active': wb.selectionLocked }"
              data-testid="selection-lock-toggle"
              :aria-label="wb.selectionLocked ? '解锁选区，允许编辑' : '锁定当前选区'"
              :aria-pressed="wb.selectionLocked"
              @click="wb.toggleSelectionLock()"
            >
              {{ wb.selectionLocked ? '🔒 已锁定' : '锁定选区' }}
            </button>
          </div>
          <div class="write-workbench__chips">
            <button
              v-for="(label, id) in wb.agent.rewritePresets"
              :key="id"
              type="button"
              class="write-workbench__chip"
              :data-testid="`rewrite-preset-${id}`"
              :disabled="wb.agent.generating || wb.selectionLocked"
              :aria-label="`应用${label}改写预设`"
              :aria-busy="wb.agent.generating"
              :aria-disabled="wb.selectionLocked"
              @click="wb.agent.runRewritePreset(id)"
            >
              {{ label }}
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

        <div
          v-if="w.showCompanionLogicCheckInWrite"
          class="write-workbench__logic-check"
          data-testid="write-section-check-main"
        >
          <div class="write-desk-toolbar" data-testid="companion-logic-check-write">
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
        </div>

        <div
          v-if="wb.isPanelVisible('qualityFeedbackBar') && (wb.agent.statusLine || wb.qualityHints.length)"
          class="write-workbench__quality"
          data-testid="write-quality-bar-main"
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

      <!-- 编辑区 -->
      <div class="write-workbench__editor-slot write-workbench__editor-slot--primary">
        <slot />
      </div>

      <!-- AI 工具面板 -->
      <details
        v-if="wb.humanFirstDesk"
        class="write-workbench__ai-tools"
        data-testid="write-advanced-tools"
        :open="aiToolsOpen"
        @toggle="onAiToolsToggle"
      >
        <summary class="write-workbench__ai-tools-summary">
          <span class="write-workbench__ai-tools-icon">⚡</span>
          <span class="write-workbench__ai-tools-title">AI 工具</span>
          <span class="write-workbench__ai-tools-hint">{{ aiToolsOpen ? '收起' : '展开' }}</span>
        </summary>
        <div class="write-workbench__ai-tools-body">
          <!-- 生成控制 -->
          <div
            v-if="wb.isPanelVisible('generateToolbar')"
            class="write-workbench__card write-workbench__generate-toolbar"
            data-testid="write-generate-toolbar-main"
          >
            <p class="write-workbench__card-title">生成控制</p>
            <div class="write-workbench__toolbar-group">
              <button type="button" class="save-btn pixel-border" data-testid="write-generate-btn" :disabled="wb.generateRunning || wb.agent.generating" @click="wb.startQuickWrite()">生成</button>
              <button type="button" class="mini-btn pixel-border" data-testid="write-stop-btn" :disabled="!wb.generateRunning && !wb.agent.generating" @click="wb.stopGenerate()">停止</button>
              <button type="button" class="mini-btn pixel-border" data-testid="write-agent-mode-toggle" @click="wb.agent.toggleExecutionMode()">{{ wb.agent.isPreviewMode ? '预览(A)' : '应用(B2)' }}</button>
            </div>
          </div>
          <!-- 补充指令 -->
          <details v-if="wb.isPanelVisible('agentSessionStrip')" class="write-workbench__card" data-testid="write-agent-prompt-main" :open="wb.agent.agentExpanded" @toggle="onAgentToggle">
            <summary class="write-workbench__card-title">补充指令</summary>
            <div class="write-workbench__agent-body">
              <form class="write-workbench__toolbar-group" @submit.prevent="wb.agent.submitPrompt()">
                <input v-model="wb.agent.promptInput" type="text" class="form-input pixel-border" placeholder="补充指令…" data-testid="write-agent-input" />
                <button type="submit" class="mini-btn pixel-border" data-testid="write-agent-send-btn">发送</button>
              </form>
            </div>
          </details>
          <!-- 下一步路径 -->
          <details v-if="wb.isPanelVisible('directorPaths') && wb.agent.directorPaths.length" class="write-workbench__card" data-testid="write-director-paths-panel-main" :open="!wb.isPanelCollapsed('directorPaths')">
            <summary class="write-workbench__card-title">下一步路径</summary>
            <CreatorDirectorPaths hide-title :paths="wb.agent.directorPaths" :advice="wb.agent.directorAdvice" :generating="wb.agent.generating" @run="wb.agent.runDirectorPath" @dismiss-advice="wb.agent.dismissAdvice" />
          </details>
          <!-- 确认应用 -->
          <div v-if="wb.agent.pendingPlan && !wb.agent.pendingPlan.adviceOnly" class="write-workbench__plan-card write-workbench__card" data-testid="write-director-plan-card-main">
            <p class="write-workbench__card-title">确认应用</p>
            <p class="meta-line">将对 <strong>{{ wb.agent.pendingPlan.scope?.label }}</strong> 执行：{{ wb.agent.pendingPlan.actionLabel }}</p>
            <p class="meta-line">{{ wb.agent.statusLine }}</p>
            <div class="write-workbench__toolbar-group">
              <button type="button" class="save-btn pixel-border" data-testid="write-director-confirm-btn" :disabled="!wb.agent.pendingPlan?.selectedCandidateId" @click="wb.agent.confirmApply()">确认应用</button>
              <button type="button" class="mini-btn pixel-border" @click="wb.agent.cancelPlan()">取消</button>
            </div>
          </div>
          <!-- 候选预览 -->
          <div v-if="wb.isPanelVisible('candidatePreviewDock') && wb.agent.candidates.length" class="write-workbench__card" data-testid="write-candidate-dock-main">
            <p class="write-workbench__card-title">候选预览（{{ wb.agent.candidates.length }}）</p>
            <div class="write-workbench__candidates">
              <button v-for="cand in wb.agent.candidates" :key="cand.id" type="button" class="write-workbench__candidate" :class="{ 'write-workbench__candidate--selected': wb.agent.pendingPlan?.selectedCandidateId === cand.id }" :data-testid="`write-candidate-${cand.id}`" @click="wb.agent.selectCandidate(cand.id)">
                <strong>{{ cand.label }}</strong> · {{ cand.direction }}
                <pre class="preview-text">{{ cand.text.slice(0, 120) }}…</pre>
              </button>
            </div>
          </div>
          <CreatorAgentAnnotations v-if="wb.isPanelVisible('agentLensSwitcher') && wb.agent.annotations.length" main-bar :annotations="wb.agent.annotations" :lens="wb.agent.agentLens" @focus="wb.agent.focusAnnotation" />
          <CreatorAgentStreamPreview v-if="showAgentStreamPreview" main-bar :preview-text="wb.agent.streamPreviewText" :display-text="wb.agent.streamDisplayText" :preview-label="wb.agent.streamPreviewLabel" :stream-source="wb.agent.streamSource" :advice-lines="wb.agent.streamAdvicePreview" />
          <!-- 版本回滚 -->
          <div v-if="wb.isPanelVisible('versionCheckpointList') && (wb.checkpoints.length || wb.agent.lastCheckpointId)" class="write-workbench__card" data-testid="write-undo-bar-main">
            <p class="write-workbench__card-title">版本 / 回滚</p>
            <ul v-if="wb.checkpoints.length" class="write-workbench__version-list">
              <li v-for="cp in wb.checkpoints" :key="cp.id" class="write-workbench__version-item">
                <span>{{ cp.label }}</span>
                <div class="write-workbench__version-actions">
                  <button v-if="wb.isPanelVisible('checkpointDiff')" type="button" class="mini-btn pixel-border" :data-testid="`checkpoint-diff-${cp.id}`" @click="wb.openCheckpointDiff(cp.id)">对比</button>
                </div>
              </li>
            </ul>
            <CreatorCheckpointDiff v-if="wb.isPanelVisible('checkpointDiff') && wb.diffView" :diff-view="wb.diffView" @close="wb.closeCheckpointDiff" />
            <button v-if="wb.agent.lastCheckpointId" type="button" class="mini-btn pixel-border" data-testid="write-undo-last-btn" @click="wb.agent.undoLastApply()">撤销上次应用</button>
          </div>
        </div>
      </details>

      <div v-else class="write-workbench__ai-tools-body write-workbench__ai-tools-body--studio">
        <div
          v-if="wb.isPanelVisible('generateToolbar')"
          class="write-workbench__card write-workbench__generate-toolbar"
          data-testid="write-generate-toolbar-main"
        >
          <p class="write-workbench__card-title">生成控制</p>
          <div class="write-workbench__toolbar-group">
            <button type="button" class="save-btn pixel-border" data-testid="write-generate-btn" :disabled="wb.generateRunning || wb.agent.generating" @click="wb.startQuickWrite()">生成</button>
            <button type="button" class="mini-btn pixel-border" data-testid="write-stop-btn" :disabled="!wb.generateRunning && !wb.agent.generating" @click="wb.stopGenerate()">停止</button>
            <button type="button" class="mini-btn pixel-border" data-testid="write-agent-mode-toggle" @click="wb.agent.toggleExecutionMode()">{{ wb.agent.isPreviewMode ? '预览(A)' : '应用(B2)' }}</button>
          </div>
        </div>
        <details v-if="wb.isPanelVisible('agentSessionStrip')" class="write-workbench__card" data-testid="write-agent-prompt-main" :open="wb.agent.agentExpanded" @toggle="onAgentToggle">
          <summary class="write-workbench__card-title">补充指令</summary>
          <div class="write-workbench__agent-body">
            <form class="write-workbench__toolbar-group" @submit.prevent="wb.agent.submitPrompt()">
              <input v-model="wb.agent.promptInput" type="text" class="form-input pixel-border" placeholder="补充指令…" data-testid="write-agent-input" />
              <button type="submit" class="mini-btn pixel-border" data-testid="write-agent-send-btn">发送</button>
            </form>
          </div>
        </details>
        <details v-if="wb.isPanelVisible('directorPaths') && wb.agent.directorPaths.length" class="write-workbench__card" data-testid="write-director-paths-panel-main" :open="!wb.isPanelCollapsed('directorPaths')">
          <summary class="write-workbench__card-title">下一步路径</summary>
          <CreatorDirectorPaths hide-title :paths="wb.agent.directorPaths" :advice="wb.agent.directorAdvice" :generating="wb.agent.generating" @run="wb.agent.runDirectorPath" @dismiss-advice="wb.agent.dismissAdvice" />
        </details>
        <div v-if="wb.agent.pendingPlan && !wb.agent.pendingPlan.adviceOnly" class="write-workbench__plan-card write-workbench__card" data-testid="write-director-plan-card-main">
          <p class="write-workbench__card-title">确认应用</p>
          <p class="meta-line">将对 <strong>{{ wb.agent.pendingPlan.scope?.label }}</strong> 执行：{{ wb.agent.pendingPlan.actionLabel }}</p>
          <p class="meta-line">{{ wb.agent.statusLine }}</p>
          <div class="write-workbench__toolbar-group">
            <button type="button" class="save-btn pixel-border" data-testid="write-director-confirm-btn" :disabled="!wb.agent.pendingPlan?.selectedCandidateId" @click="wb.agent.confirmApply()">确认应用</button>
            <button type="button" class="mini-btn pixel-border" @click="wb.agent.cancelPlan()">取消</button>
          </div>
        </div>
        <div v-if="wb.isPanelVisible('candidatePreviewDock') && wb.agent.candidates.length" class="write-workbench__card" data-testid="write-candidate-dock-main">
          <p class="write-workbench__card-title">候选预览（{{ wb.agent.candidates.length }}）</p>
          <div class="write-workbench__candidates">
            <button v-for="cand in wb.agent.candidates" :key="cand.id" type="button" class="write-workbench__candidate" :class="{ 'write-workbench__candidate--selected': wb.agent.pendingPlan?.selectedCandidateId === cand.id }" :data-testid="`write-candidate-${cand.id}`" @click="wb.agent.selectCandidate(cand.id)">
              <strong>{{ cand.label }}</strong> · {{ cand.direction }}
              <pre class="preview-text">{{ cand.text.slice(0, 120) }}…</pre>
            </button>
          </div>
        </div>
        <CreatorAgentAnnotations v-if="wb.isPanelVisible('agentLensSwitcher') && wb.agent.annotations.length" main-bar :annotations="wb.agent.annotations" :lens="wb.agent.agentLens" @focus="wb.agent.focusAnnotation" />
        <CreatorAgentStreamPreview v-if="showAgentStreamPreview" main-bar :preview-text="wb.agent.streamPreviewText" :display-text="wb.agent.streamDisplayText" :preview-label="wb.agent.streamPreviewLabel" :stream-source="wb.agent.streamSource" :advice-lines="wb.agent.streamAdvicePreview" />
        <div v-if="wb.isPanelVisible('versionCheckpointList') && (wb.checkpoints.length || wb.agent.lastCheckpointId)" class="write-workbench__card" data-testid="write-undo-bar-main">
          <p class="write-workbench__card-title">版本 / 回滚</p>
          <ul v-if="wb.checkpoints.length" class="write-workbench__version-list">
            <li v-for="cp in wb.checkpoints" :key="cp.id" class="write-workbench__version-item">
              <span>{{ cp.label }}</span>
              <div class="write-workbench__version-actions">
                <button v-if="wb.isPanelVisible('checkpointDiff')" type="button" class="mini-btn pixel-border" :data-testid="`checkpoint-diff-${cp.id}`" @click="wb.openCheckpointDiff(cp.id)">对比</button>
              </div>
            </li>
          </ul>
          <CreatorCheckpointDiff v-if="wb.isPanelVisible('checkpointDiff') && wb.diffView" :diff-view="wb.diffView" @close="wb.closeCheckpointDiff" />
          <button v-if="wb.agent.lastCheckpointId" type="button" class="mini-btn pixel-border" data-testid="write-undo-last-btn" @click="wb.agent.undoLastApply()">撤销上次应用</button>
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
import CreatorWriteControlStrip from './CreatorWriteControlStrip.vue';
import CreatorAgentAnnotations from './CreatorAgentAnnotations.vue';
import CreatorConsistencyRail from './CreatorConsistencyRail.vue';
import CreatorCheckpointDiff from './CreatorCheckpointDiff.vue';
import CreatorChapterEntityRail from './CreatorChapterEntityRail.vue';
import '../../assets/creator-write-workbench.css';

const w = inject(CREATOR_WRITE_KEY);
const wb = w.wb;
const aiToolsOpen = ref(true);
const activeTab = ref('write');

const tabs = [
  { id: 'write', label: '写作', icon: '✎' },
  { id: 'ai', label: 'AI', icon: '⚡' },
  { id: 'check', label: '检查', icon: '✓' },
  { id: 'version', label: '版本', icon: '◇' },
];

const showAgentStreamPreview = computed(() => {
  const agent = wb.agent;
  const previewText = agent.streamPreviewText?.value ?? agent.streamPreviewText ?? '';
  const advice = agent.streamAdvicePreview?.value ?? agent.streamAdvicePreview ?? [];
  const generating = agent.generating?.value ?? agent.generating ?? false;
  return Boolean(generating && (previewText || advice.length));
});

const moodTags = ['克制', '戏剧', '幽默', '抒情'];

function onAiToolsToggle(event) {
  aiToolsOpen.value = event.target.open;
}

function onAgentToggle(event) {
  wb.agent.agentExpanded = event.target.open;
}
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

.write-workbench__top-bar {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.write-workbench__logic-check {
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-sm);
  background: var(--bg-muted);
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
  background: var(--bg-elevated);
  cursor: pointer;
  transition: all 0.2s ease;
}

.write-desk-toolbar__pill:hover {
  background: var(--color-accent-soft);
  color: var(--color-accent);
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

.write-workbench__ai-tools {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  background: var(--bg-secondary);
  margin-top: var(--space-sm);
  overflow: hidden;
}

.write-workbench__ai-tools-summary {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: var(--space-sm) var(--space-md);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-secondary);
  list-style: none;
  transition: background-color 0.2s ease;
}

.write-workbench__ai-tools-summary:hover {
  background: var(--bg-muted);
}

.write-workbench__ai-tools-summary::-webkit-details-marker {
  display: none;
}

.write-workbench__ai-tools-icon {
  font-size: var(--text-sm);
}

.write-workbench__ai-tools-title {
  flex: 1;
}

.write-workbench__ai-tools-hint {
  font-size: var(--text-xs);
  color: var(--color-text-dim);
}

.write-workbench__ai-tools-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  padding: 0 var(--space-sm) var(--space-sm);
}

.write-workbench__ai-tools-body--studio {
  padding: var(--space-sm);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  background: var(--bg-secondary);
  margin-top: var(--space-sm);
}

.write-workbench__selection-tools {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}
</style>

<!--
  CreatorSettingsPanel.vue — 设定栏（从 CreatorPage 拆出）
-->
<template>
      <section
        v-show="st.isWorkspaceColumnVisible('settings')"
        class="creator-column pixel-card"
        data-testid="column-settings"
      >
        <h2 class="column-title">设定</h2>

        <section class="settings-creator-zone" data-testid="settings-creator-zone">
        <CreatorPreferencesSection />
        <CreatorMemoryAssetsPanel compact />
        <details class="settings-block" data-testid="settings-pillars-block">
          <summary>创作支柱</summary>
          <textarea
            v-model="st.pillarsText"
            class="settings-textarea"
            data-testid="pillars-textarea"
            rows="6"
          />
          <code class="path-line">{{ st.settingsDocs?.pillars_path || st.overview.pillars_path }}</code>
        </details>
        <details class="settings-block" data-testid="settings-outline-block">
          <summary>全局大纲</summary>
          <textarea
            :ref="st.bindGlobalOutlineEditorRef"
            v-model="st.globalOutlineText"
            class="settings-textarea"
            data-testid="global-outline-textarea"
            rows="8"
          />
          <code class="path-line">{{ st.settingsDocs?.global_outline_path || st.overview.global_outline_path }}</code>
        </details>
        <button
          type="button"
          class="save-btn pixel-border"
          data-testid="save-settings-btn"
          :disabled="st.settingsSaving"
          @click="st.requestSaveSettings"
        >
          {{ st.settingsSaving ? '保存中…' : '保存设定' }}
        </button>
        <div
          v-if="st.showSettingsDiff && st.settingsDiffPreview"
          class="settings-diff-panel pixel-border"
          data-testid="settings-diff-panel"
        >
          <h3 class="subsection-title">变更预览</h3>
          <p v-if="!st.settingsDiffPreview.has_changes" class="meta-line">无变更</p>
          <template v-else>
            <p v-if="st.settingsDiffPreview.pillars.changed" class="diff-line">
              支柱：+{{ st.settingsDiffPreview.pillars.lines_added }}
              / -{{ st.settingsDiffPreview.pillars.lines_removed }} 行
            </p>
            <p v-if="st.settingsDiffPreview.global_outline.changed" class="diff-line">
              全局大纲：+{{ st.settingsDiffPreview.global_outline.lines_added }}
              / -{{ st.settingsDiffPreview.global_outline.lines_removed }} 行
            </p>
            <pre v-if="st.settingsDiffSnippet.length" class="preview-text">{{ st.settingsDiffSnippet.join('\n') }}</pre>
            <template v-if="st.settingsDiffPreview.has_history">
              <p class="diff-line" data-testid="three-way-history-label">三路对比（含历史快照）</p>
              <label v-if="st.settingsHistory.length" class="meta-line">
                对比快照
                <select
                  v-model="st.compareSnapshotId"
                  class="vol-input"
                  data-testid="compare-snapshot-select"
                  @change="st.refreshThreeWayPreview"
                >
                  <option v-for="snap in st.settingsHistory" :key="snap.id" :value="snap.id">
                    {{ snap.label }} · {{ st.formatHistoryTime(snap.saved_at) }}
                  </option>
                </select>
              </label>
              <p v-if="st.settingsDiffPreview.disk_vs_history?.pillars?.changed" class="diff-line">
                磁盘 vs 历史（支柱）：+{{ st.settingsDiffPreview.disk_vs_history.pillars.lines_added }}
                / -{{ st.settingsDiffPreview.disk_vs_history.pillars.lines_removed }}
              </p>
              <p v-if="st.settingsDiffPreview.editor_vs_history?.pillars?.changed" class="diff-line">
                编辑器 vs 历史（支柱）：+{{ st.settingsDiffPreview.editor_vs_history.pillars.lines_added }}
                / -{{ st.settingsDiffPreview.editor_vs_history.pillars.lines_removed }}
              </p>
            </template>
            <details
              v-if="st.showMergeStrategy"
              class="merge-strategy-details"
              data-testid="merge-strategy-details"
            >
              <summary>合并策略（三路冲突时选择保留来源）</summary>
              <div
                class="merge-strategy-panel"
                data-testid="merge-strategy-panel"
              >
              <p
                v-if="st.usesGlobalMergeDefault"
                class="meta-line"
                data-testid="merge-global-default-badge"
              >
                当前使用全局默认合并策略
              </p>
              <div class="merge-presets" data-testid="merge-presets">
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="merge-preset-disk"
                  @click="st.applyMergePreset('disk')"
                >
                  全选磁盘
                </button>
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="merge-preset-history"
                  @click="st.applyMergePreset('history')"
                >
                  全选历史
                </button>
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="merge-preset-editor"
                  @click="st.applyMergePreset('editor')"
                >
                  全选编辑器
                </button>
              </div>
              <label class="meta-line">
                预设包
                <select
                  v-model="st.selectedMergePresetPackage"
                  class="vol-input"
                  data-testid="merge-preset-package-select"
                  @change="st.onMergePresetPackageChange"
                >
                  <option value="">选择组合预设…</option>
                  <option
                    v-for="pkg in st.mergePresetPackages"
                    :key="pkg.id"
                    :value="pkg.id"
                  >
                    {{ st.formatMergePresetOption(pkg) }}
                  </option>
                </select>
              </label>
              <div class="merge-range">
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="export-merge-preset-packages-btn"
                  @click="st.exportMergePresetPackages"
                >
                  分享预设包
                </button>
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="toggle-import-merge-preset-packages-btn"
                  @click="st.showImportMergePresetPackages = !st.showImportMergePresetPackages"
                >
                  {{ st.showImportMergePresetPackages ? '收起导入' : '导入预设包' }}
                </button>
                <button
                  v-if="st.uiProfile.show_factory_presets"
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="publish-merge-preset-factory-btn"
                  :disabled="st.mergePresetFactoryPublishing || !st.selectedProjectMergePreset"
                  @click="st.publishMergePresetToFactory"
                >
                  {{ st.mergePresetFactoryPublishing ? '发布中…' : '发布到工厂库' }}
                </button>
                <button
                  v-if="st.uiProfile.show_factory_presets"
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="pull-merge-preset-factory-btn"
                  :disabled="st.mergePresetFactoryPulling || !st.factoryMergePresetCount"
                  @click="st.pullFactoryMergePresets"
                >
                  {{ st.mergePresetFactoryPulling ? '拉取中…' : '从工厂库拉取' }}
                </button>
              </div>
              <div
                v-if="st.uiProfile.show_merge_preset_advanced && st.mergePresetToposort.edges?.length"
                class="merge-preset-toposort"
                data-testid="merge-preset-toposort-panel"
              >
                <p class="meta-line">拓扑序（{{ st.mergePresetToposort.order?.join(' → ') }}）</p>
                <ul>
                  <li
                    v-for="edge in st.mergePresetToposort.edges"
                    :key="`${edge.from}-${edge.to}`"
                    data-testid="merge-preset-toposort-edge"
                  >
                    {{ edge.from }} → {{ edge.to }}
                  </li>
                </ul>
              </div>
              <div
                v-if="st.mergePresetChangelog.entries?.length"
                class="merge-preset-changelog"
                data-testid="merge-preset-changelog-panel"
              >
                <p class="meta-line">预设变更（{{ st.mergePresetChangelog.entry_count }}）</p>
                <ul>
                  <li
                    v-for="(entry, idx) in st.mergePresetChangelog.entries"
                    :key="idx"
                    data-testid="merge-preset-changelog-row"
                  >
                    {{ entry.action }} · {{ entry.changed_fields?.join(', ') }}
                    <button
                      type="button"
                      class="mini-btn pixel-border"
                      data-testid="merge-preset-changelog-diff-btn"
                      @click="st.previewMergePresetChangelogDiff(idx)"
                    >
                      diff
                    </button>
                  </li>
                </ul>
                <p
                  v-if="st.mergePresetChangelogDiff.change_count"
                  class="meta-line"
                  data-testid="merge-preset-changelog-diff-panel"
                >
                  变更 {{ st.mergePresetChangelogDiff.change_count }} 项：
                  {{ st.mergePresetChangelogDiff.changes?.map((c) => c.field).join(', ') }}
                </p>
              </div>
              <div
                v-if="st.uiProfile.show_factory_presets && st.factoryMergePresetPullConflicts.conflicts?.length"
                class="merge-preset-factory-pull-wizard"
                data-testid="merge-preset-factory-pull-wizard"
              >
                <p class="meta-line">工厂拉取冲突（{{ st.factoryMergePresetPullConflicts.conflict_count }}）</p>
                <ul>
                  <li
                    v-for="(conflict, idx) in st.factoryMergePresetPullConflicts.conflicts"
                    :key="`${conflict.package_id}-${idx}`"
                    data-testid="merge-preset-factory-pull-conflict-row"
                  >
                    {{ conflict.message }}
                    <button
                      type="button"
                      class="mini-btn pixel-border"
                      data-testid="merge-preset-factory-pull-prefer-factory-btn"
                      @click="st.pullFactoryMergePresetsWithStrategy(conflict.package_id, 'prefer_factory')"
                    >
                      用工厂
                    </button>
                    <button
                      type="button"
                      class="mini-btn pixel-border"
                      data-testid="merge-preset-factory-pull-prefer-project-btn"
                      @click="st.pullFactoryMergePresetsWithStrategy(conflict.package_id, 'prefer_project')"
                    >
                      保留项目
                    </button>
                  </li>
                </ul>
              </div>
              <div
                v-if="st.uiProfile.show_merge_preset_advanced && st.mergePresetGraph.edges?.length"
                class="merge-preset-graph"
                data-testid="merge-preset-graph-panel"
              >
                <p class="meta-line">预设包依赖图（{{ st.mergePresetGraph.edge_count }} 条边）</p>
                <ul>
                  <li
                    v-for="edge in st.mergePresetGraph.edges"
                    :key="`${edge.from_pkg}-${edge.to}`"
                    data-testid="merge-preset-graph-edge"
                  >
                    {{ edge.from_pkg }} → {{ edge.to }}
                  </li>
                </ul>
              </div>
              <div
                v-if="st.uiProfile.show_merge_preset_advanced && st.mergePresetConflicts.conflicts?.length"
                class="merge-preset-conflicts"
                data-testid="merge-preset-conflicts-panel"
              >
                <p class="meta-line">预设包冲突（{{ st.mergePresetConflicts.conflict_count }}）</p>
                <ul>
                  <li
                    v-for="(conflict, idx) in st.mergePresetConflicts.conflicts"
                    :key="`${conflict.type}-${idx}`"
                    data-testid="merge-preset-conflict-row"
                  >
                    {{ conflict.message }}
                  </li>
                </ul>
              </div>
              <div
                v-if="st.uiProfile.show_merge_preset_advanced && st.mergePresetConflictFixes.fixes?.length"
                class="merge-preset-conflict-fixes"
                data-testid="merge-preset-conflict-fixes-panel"
              >
                <p class="meta-line">修复建议（{{ st.mergePresetConflictFixes.fix_count }}）</p>
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="apply-all-merge-preset-fixes-btn"
                  @click="st.applyAllMergePresetConflictFixes"
                >
                  批量应用可修复项
                </button>
                <ul>
                  <li
                    v-for="fix in st.mergePresetConflictFixes.fixes"
                    :key="fix.id"
                    class="merge-preset-fix-row"
                    data-testid="merge-preset-conflict-fix-row"
                  >
                    <span>{{ fix.label }}</span>
                    <button
                      v-if="fix.applicable"
                      type="button"
                      class="mini-btn pixel-border"
                      data-testid="apply-merge-preset-fix-btn"
                      @click="st.applyMergePresetConflictFix(fix)"
                    >
                      应用
                    </button>
                  </li>
                </ul>
              </div>
              <div
                v-if="st.showImportMergePresetPackages"
                class="import-templates-panel"
                data-testid="import-merge-preset-packages-panel"
              >
                <textarea
                  v-model="st.importMergePresetPackagesJson"
                  class="vol-input import-templates-json"
                  data-testid="import-merge-preset-packages-json"
                  placeholder='{"packages":[...]}'
                  rows="3"
                />
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="preview-merge-preset-import-diff-btn"
                  :disabled="st.mergePresetPackagesImporting || !st.importMergePresetPackagesJson.trim()"
                  @click="st.previewMergePresetImportDiff"
                >
                  预览 diff
                </button>
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="toposort-merge-preset-btn"
                  @click="st.applyMergePresetToposort"
                >
                  拓扑重排
                </button>
                <p
                  v-if="st.mergePresetImportDiff.added?.length || st.mergePresetImportDiff.updated?.length"
                  class="meta-line"
                  data-testid="merge-preset-import-diff-panel"
                >
                  diff：新增 {{ st.mergePresetImportDiff.added?.length || 0 }} /
                  更新 {{ st.mergePresetImportDiff.updated?.length || 0 }}
                </p>
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="preflight-merge-preset-import-btn"
                  :disabled="st.mergePresetPackagesImporting || !st.importMergePresetPackagesJson.trim()"
                  @click="st.preflightMergePresetImport"
                >
                  预检冲突
                </button>
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="import-merge-preset-packages-btn"
                  :disabled="st.mergePresetPackagesImporting || !st.importMergePresetPackagesJson.trim()"
                  @click="st.importMergePresetPackagesFromJson"
                >
                  {{ st.mergePresetPackagesImporting ? '导入中…' : '确认导入' }}
                </button>
              </div>
              <label class="meta-line">
                支柱
                <select v-model="st.pillarsMergeSource" class="vol-input" data-testid="pillars-merge-source" @change="st.refreshMergeStrategyPreview">
                  <option value="editor">编辑器</option>
                  <option value="disk">磁盘</option>
                  <option value="history">历史快照</option>
                </select>
              </label>
              <label v-if="st.pillarsMergeSource === 'history' && st.settingsHistory.length" class="meta-line">
                支柱历史快照
                <select
                  v-model="st.pillarsSnapshotId"
                  class="vol-input"
                  data-testid="pillars-snapshot-select"
                  @change="st.refreshMergeStrategyPreview"
                >
                  <option v-for="snap in st.settingsHistory" :key="`p-${snap.id}`" :value="snap.id">
                    {{ snap.label }} · {{ st.formatHistoryTime(snap.saved_at) }}
                  </option>
                </select>
              </label>
              <label class="meta-line">
                全局大纲
                <select
                  v-model="st.outlineMergeSource"
                  class="vol-input"
                  data-testid="outline-merge-source"
                  @change="st.refreshMergeStrategyPreview"
                >
                  <option value="editor">编辑器</option>
                  <option value="disk">磁盘</option>
                  <option value="history">历史快照</option>
                </select>
              </label>
              <label v-if="st.outlineMergeSource === 'history' && st.settingsHistory.length" class="meta-line">
                大纲历史快照
                <select
                  v-model="st.outlineSnapshotId"
                  class="vol-input"
                  data-testid="outline-snapshot-select"
                  @change="st.refreshMergeStrategyPreview"
                >
                  <option v-for="snap in st.settingsHistory" :key="`o-${snap.id}`" :value="snap.id">
                    {{ snap.label }} · {{ st.formatHistoryTime(snap.saved_at) }}
                  </option>
                </select>
              </label>
              <div v-if="st.mergeStrategyPreview" class="merge-preview-visual" data-testid="merge-preview-visual">
                <p v-if="st.mergeStrategyPreview.pillars.vs_disk.changed" class="diff-line">
                  支柱将写入 vs 磁盘：+{{ st.mergeStrategyPreview.pillars.vs_disk.lines_added }}
                  / -{{ st.mergeStrategyPreview.pillars.vs_disk.lines_removed }}
                </p>
                <pre
                  v-if="st.mergeStrategySnippet.length"
                  class="preview-text"
                  data-testid="merge-strategy-snippet"
                >{{ st.mergeStrategySnippet.join('\n') }}</pre>
              </div>
              <div class="merge-range">
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="export-merge-prefs-btn"
                  @click="st.exportMergePreferences"
                >
                  导出合并策略
                </button>
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="toggle-import-merge-prefs-btn"
                  @click="st.showImportMergePrefs = !st.showImportMergePrefs"
                >
                  {{ st.showImportMergePrefs ? '收起导入' : '导入合并策略' }}
                </button>
              </div>
              <div v-if="st.showImportMergePrefs" class="import-templates-panel" data-testid="import-merge-prefs-panel">
                <textarea
                  v-model="st.importMergePrefsJson"
                  class="vol-input import-templates-json"
                  data-testid="import-merge-prefs-json"
                  placeholder='{"project":{...},"global":{...}}'
                  rows="4"
                />
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="import-merge-prefs-btn"
                  :disabled="st.mergePrefsImporting || !st.importMergePrefsJson.trim()"
                  @click="st.importMergePreferencesFromJson"
                >
                  {{ st.mergePrefsImporting ? '导入中…' : '确认导入' }}
                </button>
              </div>
            </div>
            </details>
          </template>
          <div class="batch-actions">
            <button
              type="button"
              class="save-btn pixel-border"
              data-testid="confirm-settings-btn"
              :disabled="st.settingsSaving || !st.settingsDiffPreview.has_changes"
              @click="st.confirmSaveSettings"
            >
              确认保存
            </button>
            <button
              type="button"
              class="mini-btn pixel-border"
              data-testid="cancel-settings-btn"
              @click="st.cancelSettingsDiff"
            >
              取消
            </button>
          </div>
        </div>
        </section>

        <details class="settings-block settings-block--advanced" data-testid="settings-advanced-section">
          <summary>高级设定</summary>
        <details v-if="st.settingsHistory.length" class="settings-block" data-testid="settings-history-panel">
          <summary>版本历史（{{ st.settingsHistory.length }}）</summary>
          <ul class="history-list">
            <li
              v-for="snap in st.settingsHistory"
              :key="snap.id"
              class="history-row pixel-border"
              :data-testid="`history-row-${snap.id}`"
            >
              <span class="history-meta">{{ snap.label }} · {{ st.formatHistoryTime(snap.saved_at) }}</span>
              <span class="history-excerpt">{{ snap.pillars_excerpt || '（空支柱）' }}</span>
              <button
                type="button"
                class="mini-btn pixel-border"
                :data-testid="`restore-history-${snap.id}`"
                :disabled="st.settingsRestoring"
                @click="st.restoreSettingsHistory(snap.id)"
              >
                恢复
              </button>
            </li>
          </ul>
        </details>
        <details v-if="st.overview.quality_report_available" class="settings-block">
          <summary>P0 问题（点开才看）</summary>
          <p class="p0-line" :class="st.overview.p0_count ? 'warn' : 'ok'">
            {{ st.overview.p0_count ? `发现 ${st.overview.p0_count} 条 P0` : '无 P0' }}
          </p>
        </details>
        <div
          v-if="st.uiProfile.primary_action === 'logic_check' && !st.workspaceTabsEnabled"
          class="cmd-block companion-check-panel"
          data-testid="companion-logic-check-panel"
        >
          <p class="subsection-title">逻辑审查</p>
          <p class="meta-line">仅检查 P0 逻辑问题，不打 prose 分。</p>
          <button
            type="button"
            class="mini-btn pixel-border"
            data-testid="run-companion-logic-check-btn"
            :disabled="st.logicCheckRunning"
            @click="st.runCompanionLogicCheck"
          >
            {{ st.logicCheckRunning ? '检查中…' : '一键逻辑审查' }}
          </button>
          <p v-if="st.logicCheckResult" class="meta-line" data-testid="companion-logic-check-result">
            {{ st.logicCheckResult.passed ? '通过' : '未通过' }} · P0 {{ st.logicCheckResult.p0_count }} ·
            共 {{ st.logicCheckResult.total_issues }} 条
            <span v-if="st.logicCheckResult.p0_only">（仅展示 P0）</span>
          </p>
          <ul
            v-if="st.uiProfile.logic_check_inline_issues && st.logicCheckResult?.issues?.length"
            class="logic-check-issues"
            data-testid="logic-check-issues"
          >
            <li
              v-for="(issue, idx) in st.logicCheckResult.issues"
              :key="`${issue.chapter}-${idx}`"
              class="logic-check-issue"
              :class="{
                'logic-check-issue--clickable': Boolean(issue.chapter),
                'logic-check-issue--active': !st.uiProfile.issue_paragraph_highlight_unified
                  && st.uiProfile.logic_check_issue_highlight
                  && st.activeLogicCheckIssueIdx === idx,
                'issue-line--active': st.uiProfile.issue_paragraph_highlight_unified
                  && st.activeLogicCheckIssueIdx === idx,
              }"
              role="button"
              tabindex="0"
              :data-testid="`logic-check-issue-${idx}`"
              @click="st.handleLogicCheckIssueClick(issue, idx)"
              @keydown.enter="st.handleLogicCheckIssueClick(issue, idx)"
              @keydown="st.onLogicCheckIssueKeydown($event, issue, idx)"
            >
              <span class="issue-severity">{{ issue.severity }}</span>
              <span v-if="issue.chapter">ch{{ String(issue.chapter).padStart(3, '0') }}</span>
              {{ issue.title || issue.message }}
            </li>
          </ul>
        </div>
        <div v-else-if="st.uiProfile.show_studio_workflow" class="cmd-block">
          <p class="subsection-title">守门命令</p>
          <code>{{ st.overview.companion_check_cmd }}</code>
        </div>
        </details>
      </section>

</template>

<script setup>
import { inject } from 'vue';
import { CREATOR_SETTINGS_KEY } from './creatorSettingsKey.js';
import CreatorPreferencesSection from './CreatorPreferencesSection.vue';
import CreatorMemoryAssetsPanel from './CreatorMemoryAssetsPanel.vue';

const st = inject(CREATOR_SETTINGS_KEY);
</script>

<style scoped>
.settings-creator-zone {
  margin-bottom: var(--space-sm);
}

.settings-block--advanced {
  margin-top: var(--space-sm);
  font-size: var(--text-sm);
}

.settings-block--advanced > summary {
  font-weight: 600;
  cursor: pointer;
}

.settings-textarea {
  width: 100%;
  font-size: var(--text-sm);
  font-family: inherit;
  padding: var(--space-xs);
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--color-text);
  resize: vertical;
  min-height: 80px;
}
.batch-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.settings-diff-panel {
  margin-top: var(--space-sm);
  padding: var(--space-sm);
}
.diff-line {
  font-size: var(--text-sm);
  margin: 2px 0;
}
.settings-excerpt,
.volume-excerpt {
  font-size: var(--text-sm);
  white-space: pre-wrap;
  max-height: 160px;
  overflow: auto;
  margin: var(--space-sm) 0;
}
.cmd-block code {
  font-size: var(--text-xs);
  word-break: break-all;
  display: block;
}
.p0-line.ok { color: #4a4; }
.p0-line.warn { color: #c44; }
.merge-strategy-details > summary {
  font-weight: 600;
  cursor: pointer;
  margin: var(--space-xs) 0;
}

.merge-strategy-panel {
  margin-top: var(--space-xs);
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.merge-presets {
  display: flex;
  gap: var(--space-xs);
  flex-wrap: wrap;
  margin-bottom: 4px;
}
.merge-preview-visual {
  margin-top: var(--space-xs);
}
.template-changelog ul {
  margin: 4px 0 0;
  padding-left: 1.2em;
  font-size: var(--text-sm);
}
.changelog-row {
  margin-bottom: 2px;
}
.changelog-diff {
  color: var(--color-accent);
}
.changelog-visual-diff {
  margin-top: 4px;
  font-size: var(--text-xs);
  white-space: pre-wrap;
  max-height: 120px;
  overflow: auto;
  background: rgba(127, 127, 127, 0.08);
  padding: 4px;
}
.visual-diff-line--add {
  color: #4a4;
}
.visual-diff-line--remove {
  color: #c44;
}
.template-approvals {
  margin-top: var(--space-sm);
}
.template-approval-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  align-items: center;
  margin-bottom: var(--space-xs);
}
.merge-preset-graph ul {
  margin: 0;
  padding-left: 1.2rem;
}
.version-semver-warn {
  color: var(--color-warn, #c90);
}
.import-templates-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  margin-top: var(--space-xs);
}
.import-templates-json {
  width: 100%;
  min-height: 72px;
  font-family: monospace;
}
.history-list {
  list-style: none;
  padding: 0;
  margin: var(--space-xs) 0 0;
}
.history-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 6px;
  margin-bottom: 4px;
  font-size: var(--text-sm);
}
.history-meta {
  opacity: 0.75;
}
.history-excerpt {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.merge-range {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: var(--text-sm);
  margin-bottom: 6px;
  align-items: center;
}

</style>

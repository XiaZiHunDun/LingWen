<!--
  CreatorVolumePlanTemplatesPanel — 卷纲模板库与审批（从 CreatorVolumePlanPanel 拆出）
-->
<template>
          <component
            :is="vp.uiProfile.creator_simplified_mode_ops ? 'details' : 'div'"
            v-if="vp.volumeTemplates.length"
            class="volume-template-panel pixel-border"
            data-testid="volume-template-panel"
          >
            <summary v-if="vp.uiProfile.creator_simplified_mode_ops" class="subsection-title">模板库（进阶）</summary>
            <h3 v-else class="subsection-title">模板库</h3>
            <div class="merge-range">
              <select v-model="vp.selectedTemplateId" class="vol-input" data-testid="volume-template-select">
                <option v-for="t in vp.volumeTemplates" :key="t.id" :value="t.id">
                  {{ vp.formatTemplateOption(t) }}
                </option>
              </select>
              <button
                type="button"
                class="mini-btn pixel-border"
                data-testid="apply-template-btn"
                :disabled="vp.templateApplying"
                @click="vp.applyVolumeTemplate"
              >
                {{ vp.templateApplying ? '套用中…' : '套用模板' }}
              </button>
              <button
                v-if="vp.selectedTemplateProject"
                type="button"
                class="mini-btn pixel-border"
                data-testid="delete-template-btn"
                :disabled="vp.templateDeleting"
                @click="vp.deleteSelectedVolumeTemplate"
              >
                {{ vp.templateDeleting ? '删除中…' : '删除模板' }}
              </button>
              <button
                v-if="vp.selectedTemplateProject && vp.uiProfile.show_factory_presets"
                type="button"
                class="mini-btn pixel-border"
                data-testid="publish-factory-template-btn"
                :disabled="vp.templatePublishing"
                @click="vp.publishSelectedTemplateToFactory"
              >
                {{ vp.templatePublishing ? '发布中…' : '发布到工厂库' }}
              </button>
              <button
                v-if="vp.selectedTemplateFactory && vp.uiProfile.show_factory_presets"
                type="button"
                class="mini-btn mini-btn--danger pixel-border"
                data-testid="delete-factory-template-btn"
                :disabled="vp.factoryDeleting"
                @click="vp.deleteSelectedFactoryTemplate"
              >
                {{ vp.factoryDeleting ? '删除中…' : '从工厂库删除' }}
              </button>
            </div>
            <div v-if="(vp.selectedTemplateProject || vp.selectedTemplateFactory) && vp.uiProfile.show_template_version_ops" class="merge-range">
              <input
                v-model="vp.templateVersionLabel"
                class="vol-input vol-conflict"
                data-testid="template-version-input"
                placeholder="版本标签（semver，如 v1.2.0）"
              />
              <p
                v-if="vp.templateVersionLabel && !vp.isSemverVersionLabel(vp.templateVersionLabel)"
                class="meta-line version-semver-warn"
                data-testid="template-version-semver-warn"
              >
                版本标签需符合 semver（如 v1.2.0）
              </p>
              <button
                type="button"
                class="mini-btn pixel-border"
                data-testid="set-template-version-btn"
                :disabled="vp.templateVersionSaving"
                @click="vp.saveTemplateVersionLabel"
              >
                {{ vp.templateVersionSaving ? '保存中…' : '设版本标签' }}
              </button>
              <button
                v-if="vp.uiProfile.show_studio_workflow && (vp.selectedTemplateProject || vp.selectedTemplateFactory)"
                type="button"
                class="mini-btn pixel-border"
                data-testid="submit-template-version-approval-btn"
                :disabled="vp.templateApprovalSubmitting"
                @click="vp.submitTemplateVersionApproval"
              >
                {{ vp.templateApprovalSubmitting ? '提交中…' : '提交审批' }}
              </button>
            </div>
            <div
              v-if="vp.uiProfile.show_studio_workflow"
              class="template-approval-chain-config"
              data-testid="template-approval-chain-config"
            >
              <p class="meta-line">审批链步数</p>
              <input
                v-model.number="vp.templateApprovalChainSteps"
                type="number"
                min="1"
                max="5"
                class="vol-input"
                data-testid="template-approval-chain-steps"
              />
              <input
                v-model="vp.templateApprovalStepAssignees"
                type="text"
                class="vol-input"
                data-testid="template-approval-step-assignees"
                placeholder="审批人（逗号分步）"
              />
              <input
                v-model="vp.templateApprovalOrGroups"
                type="text"
                class="vol-input"
                data-testid="template-approval-or-groups"
                placeholder="OR 签：alice|bob,carol"
              />
              <button
                type="button"
                class="mini-btn pixel-border"
                data-testid="save-template-approval-chain-btn"
                @click="vp.saveTemplateApprovalChainConfig"
              >
                保存审批链
              </button>
            </div>
            <div
              v-if="vp.uiProfile.show_studio_workflow"
              class="template-approval-sla-config"
              data-testid="template-approval-sla-config"
            >
              <p class="meta-line">审批 SLA（{{ vp.templateApprovalSlaHours }} 小时）</p>
              <input
                v-model.number="vp.templateApprovalSlaHours"
                type="number"
                min="1"
                max="720"
                class="vol-input"
                data-testid="template-approval-sla-hours"
              />
              <label class="meta-line">
                <input v-model="vp.templateApprovalEmailOnSubmit" type="checkbox" data-testid="template-approval-email-submit" />
                提交时发邮件
              </label>
              <label class="meta-line">
                <input v-model="vp.templateApprovalEmailOnReject" type="checkbox" data-testid="template-approval-email-reject" />
                驳回时发邮件
              </label>
              <label class="meta-line">
                <input v-model="vp.templateApprovalEmailOnOverdue" type="checkbox" data-testid="template-approval-email-overdue" />
                超时时发邮件
              </label>
              <button
                type="button"
                class="mini-btn pixel-border"
                data-testid="save-template-approval-sla-btn"
                @click="vp.saveTemplateApprovalSlaConfig"
              >
                保存 SLA
              </button>
            </div>
            <div
              v-if="vp.uiProfile.show_studio_workflow && vp.overdueTemplateApprovals.length"
              class="template-approval-overdue"
              data-testid="template-approval-overdue-panel"
            >
              <p class="meta-line">超时待审批（{{ vp.overdueTemplateApprovals.length }}）</p>
              <ul>
                <li
                  v-for="approval in vp.overdueTemplateApprovals"
                  :key="approval.id"
                  data-testid="template-approval-overdue-row"
                >
                  {{ approval.template_id }} · {{ approval.hours_pending }}h
                </li>
              </ul>
            </div>
            <div
              v-if="vp.uiProfile.show_studio_workflow && vp.pendingTemplateApprovals.length"
              class="template-approvals"
              data-testid="template-approvals-panel"
            >
              <p class="meta-line">待审批版本变更</p>
              <div v-if="vp.pendingTemplateApprovals.length > 1" class="batch-actions">
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="batch-approve-template-versions-btn"
                  @click="vp.batchApproveTemplateVersions"
                >
                  批量批准
                </button>
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="batch-reject-template-versions-btn"
                  @click="vp.batchRejectTemplateVersions"
                >
                  批量驳回
                </button>
              </div>
              <ul>
                <li
                  v-for="approval in vp.pendingTemplateApprovals"
                  :key="approval.id"
                  class="template-approval-row"
                  data-testid="template-approval-row"
                >
                  <span>{{ approval.previous_label || '—' }} → {{ approval.version_label || '（清除）' }}</span>
                  <span class="meta-line" data-testid="template-approval-chain-progress">{{ approval.chain_progress }}</span>
                  <span
                    v-if="approval.or_signing && approval.current_assignees?.length"
                    class="meta-line"
                    data-testid="template-approval-or-assignees"
                  >
                    OR 签：{{ approval.current_assignees.join(' / ') }}
                  </span>
                  <span
                    v-else-if="approval.current_assignee"
                    class="meta-line"
                    data-testid="template-approval-current-assignee"
                  >
                    指派：{{ approval.current_assignee }}
                  </span>
                  <span
                    v-if="approval.submit_note"
                    class="meta-line"
                    data-testid="template-approval-submit-note"
                  >
                    备注：{{ approval.submit_note }}
                  </span>
                  <button
                    type="button"
                    class="mini-btn pixel-border"
                    data-testid="preview-approval-snapshot-diff-btn"
                    @click="vp.previewApprovalSnapshotDiff(approval.id)"
                  >
                    快照 diff
                  </button>
                  <button
                    type="button"
                    class="mini-btn pixel-border"
                    data-testid="transfer-template-approval-btn"
                    @click="vp.transferTemplateApproval(approval.id)"
                  >
                    转交
                  </button>
                  <button
                    type="button"
                    class="mini-btn pixel-border"
                    data-testid="approve-template-version-btn"
                    @click="vp.approveTemplateVersion(approval.id)"
                  >
                    批准
                  </button>
                  <button
                    type="button"
                    class="mini-btn pixel-border"
                    data-testid="reject-template-version-btn"
                    @click="vp.rejectTemplateVersion(approval.id)"
                  >
                    驳回
                  </button>
                </li>
              </ul>
            </div>
            <div
              v-if="vp.uiProfile.show_studio_workflow && vp.templateApprovalHistory.length"
              class="template-approval-history"
              data-testid="template-approval-history-panel"
            >
              <p class="meta-line">
                审批历史
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="export-template-approval-audit-btn"
                  @click="vp.exportTemplateApprovalAudit"
                >
                  导出审计
                </button>
              </p>
              <ul>
                <li
                  v-for="row in vp.templateApprovalHistory"
                  :key="row.id"
                  class="template-approval-row"
                  data-testid="template-approval-history-row"
                >
                  <span>{{ row.template_id }} · {{ row.status }}</span>
                  <span class="meta-line">{{ row.previous_label || '—' }} → {{ row.version_label || '（清除）' }}</span>
                  <span
                    v-if="row.chain_log?.length"
                    class="meta-line"
                    data-testid="template-approval-chain-log"
                  >
                    链 {{ row.chain_log.length }} 步
                  </span>
                </li>
              </ul>
            </div>
            <div
              v-if="(vp.selectedTemplateProject || vp.selectedTemplateFactory) && vp.templateVersionChangelog.length"
              class="template-changelog"
              data-testid="template-version-changelog"
            >
              <p class="meta-line">版本变更日志</p>
              <ul>
                <li
                  v-for="(entry, idx) in vp.templateVersionChangelog"
                  :key="`${entry.changed_at}-${idx}`"
                  class="changelog-row"
                  data-testid="template-changelog-row"
                >
                  <span v-if="entry.previous_label">{{ entry.previous_label }} → </span>
                  <strong>{{ entry.version_label || '（清除）' }}</strong>
                  <span v-if="entry.changed_at" class="meta-line"> · {{ vp.formatHistoryTime(entry.changed_at) }}</span>
                  <span
                    v-if="entry.diff_summary?.changed"
                    class="meta-line changelog-diff"
                    data-testid="template-changelog-diff"
                  >
                    · 卷纲 +{{ entry.diff_summary.lines_added }}/-{{ entry.diff_summary.lines_removed }}
                  </span>
                  <button
                    v-if="entry.visual_diff?.lines?.length"
                    type="button"
                    class="mini-btn pixel-border changelog-visual-btn"
                    data-testid="template-changelog-visual-btn"
                    @click="vp.toggleChangelogVisual(idx)"
                  >
                    {{ vp.expandedChangelogVisual === idx ? '收起对比' : '可视化对比' }}
                  </button>
                  <button
                    v-if="entry.can_rollback"
                    type="button"
                    class="mini-btn pixel-border"
                    data-testid="template-changelog-rollback-btn"
                    :disabled="vp.templateRollbackSaving"
                    @click="vp.rollbackTemplateVersion(entry, idx)"
                  >
                    {{ vp.templateRollbackSaving ? '回滚中…' : '回滚到此版本' }}
                  </button>
                  <pre
                    v-if="vp.expandedChangelogVisual === idx && entry.visual_diff?.lines?.length"
                    class="changelog-visual-diff"
                    data-testid="template-changelog-visual-diff"
                  ><span
                    v-for="(line, lineIdx) in entry.visual_diff.lines"
                    :key="`${idx}-${lineIdx}`"
                    :class="`visual-diff-line visual-diff-line--${line.type}`"
                  >{{ line.type === 'add' ? '+ ' : line.type === 'remove' ? '- ' : '  ' }}{{ line.text }}
</span></pre>
                </li>
              </ul>
            </div>
            <div v-if="vp.selectedTemplateProject" class="merge-range">
              <input
                v-model="vp.renameTemplateName"
                class="vol-input vol-conflict"
                data-testid="rename-template-name-input"
                placeholder="重命名模板"
              />
              <button
                type="button"
                class="mini-btn pixel-border"
                data-testid="rename-template-btn"
                :disabled="vp.templateRenaming || !vp.renameTemplateName.trim()"
                @click="vp.renameSelectedVolumeTemplate"
              >
                {{ vp.templateRenaming ? '重命名中…' : '重命名' }}
              </button>
            </div>
            <p v-if="vp.selectedTemplateHint" class="meta-line">{{ vp.selectedTemplateHint }}</p>
            <div v-if="vp.editableVolumes.length" class="merge-range">
              <input
                v-model="vp.customTemplateName"
                class="vol-input vol-conflict"
                data-testid="save-template-name-input"
                placeholder="自定义模板名"
              />
              <button
                type="button"
                class="mini-btn pixel-border"
                data-testid="save-template-btn"
                :disabled="vp.templateSaving || !vp.customTemplateName.trim()"
                @click="vp.saveCustomVolumeTemplate"
              >
                {{ vp.templateSaving ? '保存中…' : '存为模板' }}
              </button>
            </div>
            <div class="merge-range">
              <button
                type="button"
                class="mini-btn pixel-border"
                data-testid="export-templates-btn"
                @click="vp.exportCustomTemplates"
              >
                导出 JSON
              </button>
              <button
                type="button"
                class="mini-btn pixel-border"
                data-testid="toggle-import-templates-btn"
                @click="vp.showImportTemplates = !vp.showImportTemplates"
              >
                {{ vp.showImportTemplates ? '收起导入' : '导入 JSON' }}
              </button>
              <button
                v-if="vp.templateSyncSources.length"
                type="button"
                class="mini-btn pixel-border"
                data-testid="sync-templates-btn"
                :disabled="vp.templateSyncing"
                @click="vp.syncTemplatesFromProjects"
              >
                {{ vp.templateSyncing ? '同步中…' : '跨项目同步' }}
              </button>
              <button
                v-if="vp.factoryTemplateCount && vp.uiProfile.show_factory_presets"
                type="button"
                class="mini-btn pixel-border"
                data-testid="pull-factory-templates-btn"
                :disabled="vp.factoryPulling"
                @click="vp.pullFactoryTemplates"
              >
                {{ vp.factoryPulling ? '拉取中…' : '从工厂库拉取' }}
              </button>
            </div>
            <div v-if="vp.showImportTemplates" class="import-templates-panel" data-testid="import-templates-panel">
              <textarea
                v-model="vp.importTemplatesJson"
                class="vol-input import-templates-json"
                data-testid="import-templates-json"
                placeholder='{"templates":[...]}'
                rows="4"
              />
              <button
                type="button"
                class="mini-btn pixel-border"
                data-testid="import-templates-btn"
                :disabled="vp.templateImporting || !vp.importTemplatesJson.trim()"
                @click="vp.importCustomTemplates"
              >
                {{ vp.templateImporting ? '导入中…' : '确认导入' }}
              </button>
            </div>
          </component>
</template>

<script setup>
import { inject } from 'vue';
import { CREATOR_VOLUME_PLAN_KEY } from './creatorVolumePlanKey.js';

const vp = inject(CREATOR_VOLUME_PLAN_KEY);
if (!vp) {
  throw new Error('CreatorVolumePlanPanel child requires CREATOR_VOLUME_PLAN_KEY provide');
}
</script>

<style scoped>
.volume-plan-diff-count {
  margin-left: var(--space-xs);
  padding: 1px 4px;
  border-radius: 2px;
  color: #a60;
  background: rgba(255, 200, 80, 0.35);
  font-family: 'Press Start 2P', monospace;
  font-size: 6px;
}








.volume-plan-diff-volume-filter {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  margin-top: var(--space-xs);
  margin-left: var(--space-sm);
}

.volume-plan-diff-type-filter {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  margin-top: var(--space-xs);
}

.volume-plan-diff-summary {
  cursor: pointer;
  font-family: 'Press Start 2P', monospace;
  font-size: var(--text-xs);
}

.volume-plan-outline-lines {
  list-style: none;
  padding: 0;
  margin: var(--space-xs) 0;
  font-size: var(--text-xs);
  line-height: 1.5;
  max-height: 220px;
  overflow: auto;
}

.volume-plan-outline-line {
  padding: 2px 0;
  white-space: pre-wrap;
}

.volume-plan-outline-line--highlight {
  background: rgba(255, 220, 100, 0.35);
  box-shadow: inset 0 0 0 1px rgba(200, 180, 80, 0.65);
}

.volume-plan-diff-panel {
  margin-top: var(--space-sm);
  padding: var(--space-xs);
  background: rgba(200, 160, 80, 0.1);
}

.volume-plan-diff-side-by-side {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: var(--space-sm);
  align-items: start;
}

.volume-plan-diff-outline-col {
  padding: var(--space-xs);
  background: rgba(100, 140, 200, 0.08);
  max-height: 220px;
  overflow: auto;
}

.volume-plan-outline-excerpt {
  margin: var(--space-xs) 0;
  white-space: pre-wrap;
  font-size: var(--text-xs);
  line-height: 1.5;
}

.volume-plan-diff-list {
  list-style: none;
  padding: 0;
  margin: var(--space-xs) 0 0;
  font-size: var(--text-sm);
}

.volume-plan-diff-item .diff-type {
  font-family: 'Press Start 2P', monospace;
  font-size: var(--text-xs);
  margin-right: var(--space-xs);
  text-transform: uppercase;
}

.volume-plan-diff-details summary {
  cursor: pointer;
  list-style: none;
}

.volume-plan-diff-details summary::-webkit-details-marker {
  display: none;
}

.volume-plan-diff-detail-list {
  list-style: none;
  padding: var(--space-xs) 0 0 var(--space-sm);
  margin: 0;
  font-size: var(--text-xs);
  opacity: 0.9;
}

.volume-plan-save-confirm {
  margin-top: var(--space-xs);
  padding: var(--space-xs);
  background: rgba(200, 120, 80, 0.1);
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

.subsection-title {
  font-size: var(--text-sm);
  margin: var(--space-md) 0 var(--space-xs);
}

.volume-plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.volume-edit-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 6px;
  margin-bottom: 6px;
  font-size: var(--text-sm);
}

.volume-edit-row--locked {
  border-color: var(--color-accent);
  background: rgba(100, 140, 200, 0.08);
}

.volume-edit-row--dragging {
  opacity: 0.55;
}

.volume-reorder {
  display: flex;
  flex-direction: column;
  gap: 2px;
  align-items: center;
}

.drag-handle {
  cursor: grab;
  font-size: var(--text-sm);
  opacity: 0.6;
  user-select: none;
}

.vol-input {
  font-size: var(--text-sm);
  padding: 2px 4px;
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--color-text);
}

.vol-label { width: 3em; }

.vol-num { width: 3em; }

.vol-conflict { flex: 1; min-width: 80px; }

.vol-range { display: flex; align-items: center; gap: 2px; }

.mini-btn,
.save-btn {
  font-size: var(--text-xs);
  padding: 2px 6px;
  cursor: pointer;
}

.save-btn {
  margin-top: var(--space-xs);
}

.batch-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.path-line,
.cmd-block code {
  font-size: var(--text-xs);
  word-break: break-all;
  display: block;
}

.meta-line {
  font-size: var(--text-sm);
  opacity: 0.75;
}

.mini-btn--danger {
  color: var(--color-danger);
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
  color: var(--color-danger);
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

.volume-template-panel {
  margin-bottom: var(--space-sm);
  padding: var(--space-sm);
}

.pulse-empty-guide .meta-line {
  margin: var(--space-xs) 0 var(--space-sm);
}

.companion-logic-check-write .subsection-title {
  margin-bottom: var(--space-xs);
}

.volume-merge-panel {
  margin-top: var(--space-sm);
  padding: var(--space-sm);
}

.volume-split-panel {
  margin-top: var(--space-sm);
  padding: var(--space-sm);
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

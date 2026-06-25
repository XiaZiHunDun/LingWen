<!--
  CreatorVolumePlanPanel.vue — 脉络栏卷纲编辑区（从 CreatorPage 拆出）
-->
<template>
  <div class="volume-plan-panel" data-testid="volume-plan-panel">
          <div class="volume-plan-header">
            <h3 class="subsection-title">卷纲</h3>
            <button
              type="button"
              class="mini-btn pixel-border"
              data-testid="add-volume-btn"
              @click="vp.addVolume"
            >
              + 卷
            </button>
          </div>
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
                v-model.number="templateApprovalChainSteps"
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
                v-model.number="templateApprovalSlaHours"
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
          <div v-if="!vp.editableVolumes.length" class="meta-line">暂无卷纲，点击「+ 卷」或套用模板。</div>
          <div
            v-for="(vol, idx) in vp.editableVolumes"
            :key="`${idx}-${vol.label}`"
            class="volume-edit-row pixel-border"
            :class="{
              'volume-edit-row--locked': vol.locked,
              'volume-edit-row--dragging': vp.dragVolumeIndex === idx,
            }"
            draggable="true"
            :data-testid="`volume-row-${idx}`"
            @dragstart="vp.onVolumeDragStart(idx, $event)"
            @dragover.prevent
            @drop.prevent="vp.onVolumeDrop(idx)"
          >
            <div class="volume-reorder">
              <button
                type="button"
                class="mini-btn pixel-border"
                :data-testid="`volume-move-up-${idx}`"
                :disabled="idx === 0"
                title="上移"
                @click="vp.moveVolume(idx, idx - 1)"
              >
                ↑
              </button>
              <button
                type="button"
                class="mini-btn pixel-border"
                :data-testid="`volume-move-down-${idx}`"
                :disabled="idx === vp.editableVolumes.length - 1"
                title="下移"
                @click="vp.moveVolume(idx, idx + 1)"
              >
                ↓
              </button>
              <span class="drag-handle" data-testid="volume-drag-handle" title="拖拽排序">⋮⋮</span>
            </div>
            <input v-model="vol.label" class="vol-input vol-label" placeholder="卷名" />
            <div class="vol-range">
              <input v-model.number="vol.start_chapter" type="number" min="1" class="vol-input vol-num" />
              <span>–</span>
              <input v-model.number="vol.end_chapter" type="number" min="1" class="vol-input vol-num" />
            </div>
            <input
              v-model="vol.core_conflict"
              class="vol-input vol-conflict"
              placeholder="核心冲突"
            />
            <button
              type="button"
              class="mini-btn pixel-border"
              :data-testid="`lock-volume-${idx}`"
              @click="vp.toggleLock(idx)"
            >
              {{ vol.locked ? '已锁' : '锁定' }}
            </button>
          </div>
          <button
            v-if="vp.editableVolumes.length"
            type="button"
            class="save-btn pixel-border"
            data-testid="save-volume-plan-btn"
            :disabled="vp.saving"
            @click="vp.requestSaveVolumePlan"
          >
            {{ vp.saving ? '保存中…' : '保存卷纲' }}
          </button>
          <label
            v-if="vp.uiProfile.volume_plan_diff_type_filter && vp.volumePlanDiffPreview?.has_changes && vp.volumePlanDiffTypeOptions.length"
            class="meta-line volume-plan-diff-type-filter"
            data-testid="volume-plan-diff-type-filter-label"
          >
            变更类型
            <select
              v-model="vp.volumePlanDiffTypeFilter"
              class="vol-input"
              data-testid="volume-plan-diff-type-filter"
            >
              <option value="">全部</option>
              <option
                v-for="diffType in vp.volumePlanDiffTypeOptions"
                :key="`vol-diff-type-${diffType}`"
                :value="diffType"
              >
                {{ diffType }}
              </option>
            </select>
          </label>
          <label
            v-if="vp.uiProfile.volume_plan_diff_volume_filter && vp.volumePlanDiffPreview?.has_changes && vp.volumePlanDiffVolumeOptions.length"
            class="meta-line volume-plan-diff-volume-filter"
            data-testid="volume-plan-diff-volume-filter-label"
          >
            变更卷
            <select
              v-model="vp.volumePlanDiffVolumeFilter"
              class="vol-input"
              data-testid="volume-plan-diff-volume-filter"
            >
              <option value="">全部卷</option>
              <option
                v-for="volLabel in vp.volumePlanDiffVolumeOptions"
                :key="`vol-diff-volume-${volLabel}`"
                :value="volLabel"
              >
                卷{{ volLabel }}
              </option>
            </select>
          </label>
          <div
            v-if="vp.uiProfile.volume_plan_diff_preview && vp.volumePlanDiffPreview?.has_changes && !vp.uiProfile.volume_plan_diff_auto_collapse"
            class="volume-plan-diff-panel pixel-border"
            data-testid="volume-plan-diff-panel"
          >
            <p class="meta-line">
              卷纲未保存变更
              <span
                v-if="vp.uiProfile.volume_plan_diff_change_count && vp.volumePlanDiffChangeCount"
                class="volume-plan-diff-count"
                data-testid="volume-plan-diff-change-count"
              >
                {{ vp.volumePlanDiffChangeCount }} 处
              </span>
            </p>
            <button
              v-if="vp.uiProfile.volume_plan_diff_jump_outline_edit"
              type="button"
              class="mini-btn pixel-border"
              data-testid="jump-global-outline-edit-btn"
              @click="vp.jumpToGlobalOutlineEdit"
            >
              编辑全局大纲
            </button>
            <button
              v-if="vp.uiProfile.volume_plan_diff_export && vp.volumePlanDiffPreview?.has_changes"
              type="button"
              class="mini-btn pixel-border"
              data-testid="export-volume-plan-diff-btn"
              @click="vp.exportVolumePlanDiff"
            >
              导出 diff JSON
            </button>
            <button
              v-if="vp.uiProfile.volume_plan_diff_export_markdown && vp.volumePlanDiffPreview?.has_changes"
              type="button"
              class="mini-btn pixel-border"
              data-testid="export-volume-plan-diff-markdown-btn"
              @click="vp.exportVolumePlanDiffMarkdown"
            >
              导出 diff Markdown
            </button>
            <button
              v-if="vp.uiProfile.volume_plan_diff_export_email_share && vp.volumePlanDiffPreview?.has_changes"
              type="button"
              class="mini-btn pixel-border"
              data-testid="share-volume-plan-diff-email-btn"
              @click="vp.shareVolumePlanDiffEmail"
            >
              邮件分享 diff
            </button>
            <button
              v-if="vp.uiProfile.volume_plan_diff_export_pdf && vp.volumePlanDiffPreview?.has_changes"
              type="button"
              class="mini-btn pixel-border"
              data-testid="export-volume-plan-diff-pdf-btn"
              @click="vp.exportVolumePlanDiffPdf"
            >
              导出 diff PDF
            </button>
            <button
              v-if="vp.uiProfile.volume_plan_diff_export_print_preview && vp.volumePlanDiffPreview?.has_changes"
              type="button"
              class="mini-btn pixel-border"
              data-testid="preview-volume-plan-diff-print-btn"
              @click="vp.openVolumePlanDiffPrintPreview"
            >
              打印预览
            </button>
            <button
              v-if="vp.uiProfile.volume_plan_diff_export_zip && vp.volumePlanDiffPreview?.has_changes"
              type="button"
              class="mini-btn pixel-border"
              data-testid="export-volume-plan-diff-zip-btn"
              @click="vp.exportVolumePlanDiffZip"
            >
              导出 ZIP
            </button>
            <button
              v-if="vp.uiProfile.volume_plan_diff_export_share_link && vp.volumePlanDiffPreview?.has_changes"
              type="button"
              class="mini-btn pixel-border"
              data-testid="share-volume-plan-diff-link-btn"
              @click="vp.shareVolumePlanDiffLink"
            >
              复制分享链接
            </button>
            <div
              v-if="vp.uiProfile.volume_plan_diff_share_collab_v2 && vp.volumePlanDiffCollabRows.length"
              class="volume-plan-diff-collab-panel pixel-border"
              data-testid="volume-plan-diff-collab-panel"
            >
              <p class="meta-line">协作批注（分享链接 v3 附带，按卷联动 diff）</p>
              <label
                v-for="row in vp.volumePlanDiffCollabRows"
                :key="`collab-edit-${row.label}`"
                class="volume-plan-diff-collab-row"
              >
                卷 {{ row.label }}
                <input
                  class="vol-input volume-plan-diff-collab-input"
                  :data-testid="`diff-collab-note-input-${row.label}`"
                  :value="vp.diffCollabNotes[row.label] || ''"
                  placeholder="@reviewer 请确认"
                  @input="vp.setDiffCollabNote(row.label, $event.target.value)"
                />
              </label>
            </div>
            <div
              class="volume-plan-diff-body"
              :class="{ 'volume-plan-diff-side-by-side': vp.uiProfile.volume_plan_diff_outline_side_by_side }"
            >
              <div class="volume-plan-diff-main">
                <ul class="volume-plan-diff-list" data-testid="volume-plan-diff-list">
                  <li
                    v-for="(row, idx) in vp.filteredVolumePlanDiffChanges"
                    :key="`vol-diff-${row.label}-${idx}`"
                    class="volume-plan-diff-item"
                    :data-testid="`volume-plan-diff-${row.type}-${row.label}`"
                  >
                    <details
                      v-if="vp.uiProfile.volume_plan_diff_expand_detail && row.details?.length"
                      class="volume-plan-diff-details"
                      :data-testid="`volume-plan-diff-details-${row.type}-${row.label}`"
                    >
                      <summary>
                        <span class="diff-type">{{ row.type }}</span> {{ row.message }}
                      </summary>
                      <ul class="volume-plan-diff-detail-list">
                        <li
                          v-for="(line, detailIdx) in row.details"
                          :key="`vol-diff-detail-${row.label}-${detailIdx}`"
                          :data-testid="`volume-plan-diff-detail-${row.label}-${detailIdx}`"
                        >
                          {{ line }}
                        </li>
                      </ul>
                    </details>
                    <template v-else>
                      <span class="diff-type">{{ row.type }}</span> {{ row.message }}
                    </template>
                  </li>
                </ul>
              </div>
              <aside
                v-if="vp.uiProfile.volume_plan_diff_outline_side_by_side && vp.volumePlanDiffPreview.global_outline_excerpt"
                class="volume-plan-diff-outline-col pixel-border"
                data-testid="volume-plan-diff-outline-side-by-side"
              >
                <p class="meta-line">全局大纲摘录</p>
                <pre
                  v-if="!vp.uiProfile.volume_plan_diff_outline_row_highlight || !vp.volumePlanDiffPreview.global_outline_lines?.length"
                  class="volume-plan-outline-excerpt"
                >{{ vp.volumePlanDiffPreview.global_outline_excerpt }}</pre>
                <ul
                  v-else
                  class="volume-plan-outline-lines"
                  data-testid="volume-plan-diff-outline-lines"
                >
                  <li
                    v-for="(line, lineIdx) in vp.volumePlanDiffPreview.global_outline_lines"
                    :key="`outline-line-${lineIdx}`"
                    class="volume-plan-outline-line"
                    :class="{ 'volume-plan-outline-line--highlight': line.highlighted }"
                    :data-testid="line.highlighted ? `volume-plan-outline-line-highlight-${lineIdx}` : `volume-plan-outline-line-${lineIdx}`"
                  >
                    {{ line.text }}
                  </li>
                </ul>
                <code class="path-line">{{ vp.volumePlanDiffPreview.global_outline_path }}</code>
              </aside>
            </div>
            <div
              v-if="vp.volumePlanSaveConfirmOpen"
              class="volume-plan-save-confirm pixel-border"
              data-testid="volume-plan-save-confirm-panel"
            >
              <p class="meta-line">确认保存以上卷纲变更？</p>
              <div class="batch-actions">
                <button
                  type="button"
                  class="save-btn pixel-border"
                  data-testid="confirm-volume-plan-save-btn"
                  :disabled="vp.saving"
                  @click="vp.confirmSaveVolumePlan"
                >
                  {{ vp.saving ? '保存中…' : '确认保存' }}
                </button>
                <button
                  type="button"
                  class="mini-btn pixel-border"
                  data-testid="cancel-volume-plan-save-btn"
                  :disabled="vp.saving"
                  @click="vp.cancelVolumePlanSave"
                >
                  取消
                </button>
              </div>
            </div>
          </div>
          <details
            v-else-if="vp.uiProfile.volume_plan_diff_preview && vp.volumePlanDiffPreview && vp.uiProfile.volume_plan_diff_auto_collapse"
            class="volume-plan-diff-panel pixel-border"
            :open="vp.volumePlanDiffExpanded"
            data-testid="volume-plan-diff-panel"
            @toggle="vp.onVolumePlanDiffToggle"
          >
            <summary class="volume-plan-diff-summary" data-testid="volume-plan-diff-summary">
              {{ vp.volumePlanDiffPreview?.has_changes ? '卷纲未保存变更' : '卷纲与已保存一致' }}
              <span
                v-if="vp.uiProfile.volume_plan_diff_change_count && vp.volumePlanDiffPreview?.has_changes && vp.volumePlanDiffChangeCount"
                class="volume-plan-diff-count"
                data-testid="volume-plan-diff-change-count"
              >
                {{ vp.volumePlanDiffChangeCount }} 处
              </span>
            </summary>
            <template v-if="vp.volumePlanDiffPreview?.has_changes">
              <button
                v-if="vp.uiProfile.volume_plan_diff_jump_outline_edit"
                type="button"
                class="mini-btn pixel-border"
                data-testid="jump-global-outline-edit-btn"
                @click="vp.jumpToGlobalOutlineEdit"
              >
                编辑全局大纲
              </button>
              <button
                v-if="vp.uiProfile.volume_plan_diff_export && vp.volumePlanDiffPreview?.has_changes"
                type="button"
                class="mini-btn pixel-border"
                data-testid="export-volume-plan-diff-btn"
                @click="vp.exportVolumePlanDiff"
              >
                导出 diff JSON
              </button>
              <button
                v-if="vp.uiProfile.volume_plan_diff_export_markdown && vp.volumePlanDiffPreview?.has_changes"
                type="button"
                class="mini-btn pixel-border"
                data-testid="export-volume-plan-diff-markdown-btn"
                @click="vp.exportVolumePlanDiffMarkdown"
              >
                导出 diff Markdown
              </button>
              <button
                v-if="vp.uiProfile.volume_plan_diff_export_email_share && vp.volumePlanDiffPreview?.has_changes"
                type="button"
                class="mini-btn pixel-border"
                data-testid="share-volume-plan-diff-email-btn"
                @click="vp.shareVolumePlanDiffEmail"
              >
                邮件分享 diff
              </button>
              <button
                v-if="vp.uiProfile.volume_plan_diff_export_pdf && vp.volumePlanDiffPreview?.has_changes"
                type="button"
                class="mini-btn pixel-border"
                data-testid="export-volume-plan-diff-pdf-btn"
                @click="vp.exportVolumePlanDiffPdf"
              >
                导出 diff PDF
              </button>
              <button
                v-if="vp.uiProfile.volume_plan_diff_export_print_preview && vp.volumePlanDiffPreview?.has_changes"
                type="button"
                class="mini-btn pixel-border"
                data-testid="preview-volume-plan-diff-print-btn"
                @click="vp.openVolumePlanDiffPrintPreview"
              >
                打印预览
              </button>
              <button
                v-if="vp.uiProfile.volume_plan_diff_export_zip && vp.volumePlanDiffPreview?.has_changes"
                type="button"
                class="mini-btn pixel-border"
                data-testid="export-volume-plan-diff-zip-btn"
                @click="vp.exportVolumePlanDiffZip"
              >
                导出 ZIP
              </button>
              <button
                v-if="vp.uiProfile.volume_plan_diff_export_share_link && vp.volumePlanDiffPreview?.has_changes"
                type="button"
                class="mini-btn pixel-border"
                data-testid="share-volume-plan-diff-link-btn"
                @click="vp.shareVolumePlanDiffLink"
              >
                复制分享链接
              </button>
              <div
                class="volume-plan-diff-body"
                :class="{ 'volume-plan-diff-side-by-side': vp.uiProfile.volume_plan_diff_outline_side_by_side }"
              >
                <div class="volume-plan-diff-main">
                  <ul class="volume-plan-diff-list" data-testid="volume-plan-diff-list">
                    <li
                      v-for="(row, idx) in vp.filteredVolumePlanDiffChanges"
                      :key="`vol-diff-collapse-${row.label}-${idx}`"
                      class="volume-plan-diff-item"
                      :data-testid="`volume-plan-diff-${row.type}-${row.label}`"
                    >
                      <details
                        v-if="vp.uiProfile.volume_plan_diff_expand_detail && row.details?.length"
                        class="volume-plan-diff-details"
                        :data-testid="`volume-plan-diff-details-${row.type}-${row.label}`"
                      >
                        <summary>
                          <span class="diff-type">{{ row.type }}</span> {{ row.message }}
                        </summary>
                        <ul class="volume-plan-diff-detail-list">
                          <li
                            v-for="(line, detailIdx) in row.details"
                            :key="`vol-diff-detail-collapse-${row.label}-${detailIdx}`"
                            :data-testid="`volume-plan-diff-detail-${row.label}-${detailIdx}`"
                          >
                            {{ line }}
                          </li>
                        </ul>
                      </details>
                      <template v-else>
                        <span class="diff-type">{{ row.type }}</span> {{ row.message }}
                      </template>
                    </li>
                  </ul>
                </div>
                <aside
                  v-if="vp.uiProfile.volume_plan_diff_outline_side_by_side && vp.volumePlanDiffPreview.global_outline_excerpt"
                  class="volume-plan-diff-outline-col pixel-border"
                  data-testid="volume-plan-diff-outline-side-by-side"
                >
                  <p class="meta-line">全局大纲摘录</p>
                  <pre
                    v-if="!vp.uiProfile.volume_plan_diff_outline_row_highlight || !vp.volumePlanDiffPreview.global_outline_lines?.length"
                    class="volume-plan-outline-excerpt"
                  >{{ vp.volumePlanDiffPreview.global_outline_excerpt }}</pre>
                  <ul
                    v-else
                    class="volume-plan-outline-lines"
                    data-testid="volume-plan-diff-outline-lines"
                  >
                    <li
                      v-for="(line, lineIdx) in vp.volumePlanDiffPreview.global_outline_lines"
                      :key="`outline-line-collapse-${lineIdx}`"
                      class="volume-plan-outline-line"
                      :class="{ 'volume-plan-outline-line--highlight': line.highlighted }"
                      :data-testid="line.highlighted ? `volume-plan-outline-line-highlight-${lineIdx}` : `volume-plan-outline-line-${lineIdx}`"
                    >
                      {{ line.text }}
                    </li>
                  </ul>
                  <code class="path-line">{{ vp.volumePlanDiffPreview.global_outline_path }}</code>
                </aside>
              </div>
              <div
                v-if="vp.volumePlanSaveConfirmOpen"
                class="volume-plan-save-confirm pixel-border"
                data-testid="volume-plan-save-confirm-panel"
              >
                <p class="meta-line">确认保存以上卷纲变更？</p>
                <div class="batch-actions">
                  <button
                    type="button"
                    class="save-btn pixel-border"
                    data-testid="confirm-volume-plan-save-btn"
                    :disabled="vp.saving"
                    @click="vp.confirmSaveVolumePlan"
                  >
                    {{ vp.saving ? '保存中…' : '确认保存' }}
                  </button>
                  <button
                    type="button"
                    class="mini-btn pixel-border"
                    data-testid="cancel-volume-plan-save-btn"
                    :disabled="vp.saving"
                    @click="vp.cancelVolumePlanSave"
                  >
                    取消
                  </button>
                </div>
              </div>
            </template>
            <p v-else class="meta-line" data-testid="volume-plan-diff-no-changes">
              当前编辑与已保存卷纲一致
            </p>
          </details>
          <div
            v-if="vp.editableVolumes.length >= 2"
            class="volume-merge-panel pixel-border"
            data-testid="volume-merge-panel"
          >
            <h3 class="subsection-title">合并向导</h3>
            <div class="merge-range">
              <label>
                从
                <select v-model.number="vp.mergeStartIdx" class="vol-input" data-testid="merge-start-select">
                  <option v-for="(vol, idx) in vp.editableVolumes" :key="`s-${idx}`" :value="idx">
                    {{ vol.label || `卷${idx + 1}` }}
                  </option>
                </select>
              </label>
              <label>
                到
                <select v-model.number="vp.mergeEndIdx" class="vol-input" data-testid="merge-end-select">
                  <option
                    v-for="(vol, idx) in vp.editableVolumes"
                    :key="`e-${idx}`"
                    :value="idx"
                    :disabled="idx < vp.mergeStartIdx"
                  >
                    {{ vol.label || `卷${idx + 1}` }}
                  </option>
                </select>
              </label>
              <input
                v-model="vp.mergeLabel"
                class="vol-input vol-conflict"
                data-testid="merge-label-input"
                placeholder="合并后卷名（可选）"
              />
            </div>
            <button
              type="button"
              class="mini-btn pixel-border"
              data-testid="apply-merge-btn"
              :disabled="vp.mergeApplying || vp.mergeStartIdx > vp.mergeEndIdx"
              @click="vp.applyVolumeMerge"
            >
              {{ vp.mergeApplying ? '合并中…' : '应用合并' }}
            </button>
          </div>
          <p
            v-if="vp.mergePreview"
            class="meta-line"
            data-testid="merge-preview-line"
          >
            已合并为「{{ vp.mergePreview.merged_label }}」· {{ vp.mergePreview.merged_range }} · 请保存卷纲
          </p>
          <div
            v-if="vp.editableVolumes.length >= 1"
            class="volume-split-panel pixel-border"
            data-testid="volume-split-panel"
          >
            <h3 class="subsection-title">拆分向导</h3>
            <div class="merge-range">
              <label>
                卷
                <select v-model.number="vp.splitVolumeIdx" class="vol-input" data-testid="split-volume-select">
                  <option v-for="(vol, idx) in vp.editableVolumes" :key="`split-${idx}`" :value="idx">
                    {{ vol.label || `卷${idx + 1}` }} ({{ vol.start_chapter }}–{{ vol.end_chapter }})
                  </option>
                </select>
              </label>
              <label>
                从章
                <input
                  v-model.number="vp.splitAtChapter"
                  type="number"
                  min="1"
                  class="vol-input vol-num"
                  data-testid="split-at-chapter"
                />
              </label>
            </div>
            <button
              type="button"
              class="mini-btn pixel-border"
              data-testid="apply-split-btn"
              :disabled="vp.splitApplying"
              @click="vp.applyVolumeSplit"
            >
              {{ vp.splitApplying ? '拆分中…' : '应用拆分' }}
            </button>
          </div>
          <p
            v-if="vp.splitPreview"
            class="meta-line"
            data-testid="split-preview-line"
          >
            已拆为「{{ vp.splitPreview.first_label }}」{{ vp.splitPreview.first_range }}
            与「{{ vp.splitPreview.second_label }}」{{ vp.splitPreview.second_range }} · 请保存卷纲
          </p>  </div>
</template>

<script setup>
import { inject } from 'vue';
import { CREATOR_VOLUME_PLAN_KEY } from './creatorVolumePlanKey.js';

const vp = inject(CREATOR_VOLUME_PLAN_KEY);
if (!vp) {
  throw new Error('CreatorVolumePlanPanel requires CREATOR_VOLUME_PLAN_KEY provide');
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








.volume-plan-diff-collab-panel {
  margin: var(--space-xs) 0;
  padding: var(--space-sm);
}

.volume-plan-diff-collab-row {
  display: block;
  margin: var(--space-xs) 0;
  font-size: var(--text-md);
}

.volume-plan-diff-collab-input {
  display: block;
  width: 100%;
  margin-top: 2px;
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
  color: #c44;
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

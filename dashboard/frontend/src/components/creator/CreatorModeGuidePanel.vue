<!--
  CreatorModeGuidePanel.vue — 三模式说明与能力对照（从 CreatorPage 拆出）
-->
<template>
    <details
      v-if="mg.showModeGuidePanel"
      class="creator-mode-guide-panel pixel-border"
      data-testid="creator-mode-guide-panel"
      :open="mg.modeGuideExpanded"
    >
      <summary class="creator-mode-guide-summary">
        模式说明与能力对照<span v-if="mg.modeLabel"> · {{ mg.modeLabel }}</span>
      </summary>
    <p
      v-if="mg.uiProfile.creation_mode_badge_legend && !mg.uiProfile.creator_simplified_mode_ops"
      class="mode-badge-legend meta-line pixel-border"
      data-testid="creation-mode-badge-legend"
    >
      徽章色标：陪伴=绿 · 推进=蓝 · 工作室=琥珀
    </p>
    <p
      v-if="mg.uiProfile.creation_mode_switch_hint && mg.creationModeSwitchHintText"
      class="mode-switch-hint pixel-border"
      data-testid="creation-mode-switch-hint"
    >
      {{ mg.creationModeSwitchHintText }}
    </p>
    <div
      v-if="mg.uiProfile.creation_mode_switch_doc_link && mg.creationModeSwitchDocLinks.length"
      class="mode-switch-doc-links pixel-border"
      data-testid="creation-mode-switch-doc-links"
    >
      <button
        v-for="link in mg.creationModeSwitchDocLinks"
        :key="link.id"
        type="button"
        class="mini-btn pixel-border mode-switch-doc-link"
        :data-testid="`mode-switch-doc-${link.id}`"
        @click="mg.openModeSwitchDoc(link, mg.uiProfile.creation_mode_switch_doc_open)"
      >
        {{ link.label }}
      </button>
    </div>
    <div
      v-if="mg.uiProfile.creation_mode_switch_aria_live"
      class="creation-mode-aria-live"
      aria-live="polite"
      data-testid="creation-mode-switch-aria-live"
    >
      {{ mg.creationModeSwitchAriaMessage }}
    </div>
    <aside
      v-if="!mg.uiProfile.creator_simplified_mode_ops && mg.uiProfile.creation_mode_preview_pinned_sidebar && mg.uiProfile.creation_mode_switch_preview && mg.creationModePreviewRows.length"
      class="creation-mode-pinned-sidebar pixel-border"
      data-testid="creation-mode-pinned-sidebar"
    >
      <p class="meta-line">三模式侧栏</p>
      <ul class="creation-mode-pinned-list">
        <li
          v-for="row in mg.creationModePreviewRows"
          :key="`mode-pinned-${row.mode}`"
          class="creation-mode-pinned-item"
          :class="{ 'creation-mode-pinned-item--active': row.active }"
          :data-testid="`creation-mode-pinned-${row.mode}`"
        >
          {{ row.label }}
        </li>
      </ul>
    </aside>
    <div
      v-if="!mg.uiProfile.creator_simplified_mode_ops && mg.uiProfile.creation_mode_switch_preview && mg.creationModePreviewRows.length && !mg.uiProfile.creation_mode_preview_pinned_sidebar"
      class="creation-mode-switch-preview pixel-border"
      :class="{ 'creation-mode-switch-preview--guide': mg.creationModeGuideAnimationEnabled }"
      data-testid="creation-mode-switch-preview"
    >
      <p class="meta-line">三模式预览 · 切换请编辑 config/project.yaml → creation_mode</p>
      <p
        v-if="mg.creationModeGuideAnimationEnabled"
        class="meta-line creation-mode-guide-hint"
        data-testid="creation-mode-guide-hint"
      >
        引导动画：依次高亮陪伴 → 推进 → 工作室
      </p>
      <ul class="creation-mode-preview-list">
        <li
          v-for="(row, previewIdx) in mg.creationModePreviewRows"
          :key="`mode-preview-${row.mode}`"
          class="creation-mode-preview-item"
          :class="{
            'creation-mode-preview-item--active': row.active,
            'creation-mode-preview-item--guide': mg.creationModeGuideAnimationEnabled,
          }"
          :style="mg.creationModeGuideAnimationEnabled
            ? { animationDelay: `${previewIdx * 0.8}s` }
            : undefined"
          :data-testid="`creation-mode-preview-${row.mode}`"
        >
          <strong>{{ row.label }}</strong>
          <span class="meta-line">{{ row.summary }}</span>
          <button
            v-if="mg.uiProfile.creation_mode_yaml_snippet"
            type="button"
            class="mini-btn pixel-border creation-mode-yaml-btn"
            :data-testid="`copy-creation-mode-yaml-${row.mode}`"
            @click.stop="mg.requestCreationModeYaml(row.mode, row.active)"
          >
            复制 YAML
          </button>
          <button
            v-if="mg.uiProfile.creation_mode_onboarding_step_link"
            type="button"
            class="mini-btn pixel-border creation-mode-onboarding-link-btn"
            :data-testid="`link-onboarding-step-${row.mode}`"
            @click.stop="mg.requestOnboardingStepLink(row.mode, row.active)"
          >
            向导步骤
          </button>
        </li>
      </ul>
    </div>
    <div
      v-if="mg.pendingModeSwitch"
      class="mode-switch-confirm-dialog pixel-border"
      data-testid="creation-mode-switch-confirm-dialog"
    >
      <p class="meta-line">
        确认切换至 <strong>{{ mg.pendingModeSwitchLabel }}</strong>？
      </p>
      <p class="meta-line">请编辑 config/project.yaml → creation_mode</p>
      <div class="mode-switch-confirm-actions">
        <button
          type="button"
          class="mini-btn pixel-border"
          data-testid="confirm-mode-switch-btn"
          @click="mg.confirmCreationModeSwitch"
        >
          确认
        </button>
        <button
          type="button"
          class="mini-btn pixel-border"
          data-testid="cancel-mode-switch-btn"
          @click="mg.cancelCreationModeSwitch"
        >
          取消
        </button>
      </div>
    </div>
    <ul
      v-if="mg.uiProfile.creation_mode_switch_history && mg.creationModeSwitchHistory.length"
      class="creation-mode-switch-history pixel-border"
      data-testid="creation-mode-switch-history"
    >
      <li
        v-for="(entry, idx) in mg.creationModeSwitchHistory"
        :key="`mode-switch-history-${entry.mode}-${entry.at}-${idx}`"
        class="meta-line creation-mode-switch-history-item"
        :data-testid="`creation-mode-switch-history-${idx}`"
      >
        {{ entry.at }} · {{ entry.label }}（{{ entry.action }}）
      </li>
    </ul>
    <div
      v-if="mg.uiProfile.creation_mode_switch_undo_hint && mg.lastModeSwitchUndo"
      class="mode-switch-undo-hint pixel-border"
      data-testid="creation-mode-switch-undo-hint"
    >
      <p class="meta-line">
        已请求切换至 {{ mg.lastModeSwitchUndo.toLabel }}，撤销请恢复
        <code>creation_mode: {{ mg.lastModeSwitchUndo.fromMode }}</code>
      </p>
      <button
        type="button"
        class="mini-btn pixel-border"
        data-testid="copy-mode-switch-undo-btn"
        @click="mg.applyModeSwitchUndoHint"
      >
        复制撤销 YAML
      </button>
    </div>
    <p
      v-if="mg.uiProfile.creation_mode_switch_hotkey"
      class="meta-line creation-mode-hotkey-hint"
      data-testid="creation-mode-switch-hotkey-hint"
    >
      快捷键 Alt+Shift+1/2/3 复制 companion / advance / studio YAML
    </p>
    <ul
      v-if="!mg.uiProfile.creator_simplified_mode_ops && mg.uiProfile.creation_mode_accessibility_checklist && mg.creationModeAccessibilityItems.length"
      class="creation-mode-accessibility-checklist pixel-border"
      data-testid="creation-mode-accessibility-checklist"
    >
      <li
        v-for="item in mg.creationModeAccessibilityItems"
        :key="`a11y-${item.id}`"
        class="meta-line creation-mode-accessibility-item"
        :data-testid="`creation-mode-a11y-${item.id}`"
      >
        {{ item.enabled ? '✓' : '—' }} {{ item.label }}
      </li>
    </ul>
    <div
      v-if="mg.uiProfile.creation_mode_capability_matrix && mg.creationModeCapabilityRows.length && !mg.uiProfile.creator_simplified_mode_ops"
      class="creation-mode-capability-matrix pixel-border"
      data-testid="creation-mode-capability-matrix"
    >
      <p class="meta-line">三模式能力对照</p>
      <table class="creation-mode-capability-table">
        <thead>
          <tr>
            <th scope="col">能力</th>
            <th scope="col">陪伴</th>
            <th scope="col">推进</th>
            <th scope="col">工作室</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in mg.creationModeCapabilityRows"
            :key="`capability-${row.id}`"
            :data-testid="`creation-mode-capability-${row.id}`"
          >
            <th scope="row">{{ row.label }}</th>
            <td>{{ row.companion ? '✓' : '—' }}</td>
            <td>{{ row.advance ? '✓' : '—' }}</td>
            <td>{{ row.studio ? '✓' : '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <details
      v-if="mg.uiProfile.creator_simplified_mode_ops"
      class="creator-advanced-ops pixel-border"
      data-testid="creator-advanced-ops"
    >
      <summary class="creator-advanced-ops-summary">高级：三模式对照与运维</summary>
      <div
        v-if="mg.uiProfile.creation_mode_capability_matrix && mg.creationModeCapabilityRows.length"
        class="creation-mode-capability-matrix pixel-border"
        data-testid="creation-mode-capability-matrix-advanced"
      >
        <p class="meta-line">三模式能力对照</p>
        <table class="creation-mode-capability-table">
          <thead>
            <tr>
              <th scope="col">能力</th>
              <th scope="col">陪伴</th>
              <th scope="col">推进</th>
              <th scope="col">工作室</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in mg.creationModeCapabilityRows"
              :key="`capability-adv-${row.id}`"
            >
              <th scope="row">{{ row.label }}</th>
              <td>{{ row.companion ? '✓' : '—' }}</td>
              <td>{{ row.advance ? '✓' : '—' }}</td>
              <td>{{ row.studio ? '✓' : '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="meta-line">切换模式：编辑 <code>config/project.yaml</code> → <code>creation_mode</code></p>
    </details>
    <p
      v-if="mg.uiProfile.studio_creation_entry_hint && mg.studioCreationEntryHintText"
      class="mode-switch-hint studio-entry-hint pixel-border"
      data-testid="studio-creation-entry-hint"
    >
      {{ mg.studioCreationEntryHintText }}
    </p>
    </details>

</template>

<script setup>
import { inject } from 'vue';
import { CREATOR_MODE_GUIDE_KEY } from './creatorModeGuideKey.js';

const mg = inject(CREATOR_MODE_GUIDE_KEY);
</script>

<style scoped>
.creator-advanced-ops-summary {
  cursor: pointer;
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  padding: var(--space-xs) 0;
}
.creator-mode-guide-summary {
  cursor: pointer;
  font-size: var(--text-sm);
  font-family: 'Press Start 2P', monospace;
  padding: var(--space-xs) 0;
}
.mode-switch-hint {
  font-size: var(--text-sm);
  padding: var(--space-xs) var(--space-sm);
  margin: 0;
  color: var(--color-accent);
  background: rgba(100, 140, 200, 0.08);
}
.mode-badge-legend {
  margin: 0;
  padding: var(--space-xs) var(--space-sm);
  font-size: var(--text-xs);
  color: var(--color-accent);
}
.mode-switch-confirm-dialog {
  margin: var(--space-xs) 0;
  padding: var(--space-sm);
  border-color: rgba(180, 120, 40, 0.55);
  background: rgba(180, 120, 40, 0.08);
}
.mode-switch-confirm-actions {
  display: flex;
  gap: var(--space-xs);
  margin-top: var(--space-xs);
}
.creation-mode-switch-preview {
  padding: var(--space-xs) var(--space-sm);
}
.creation-mode-preview-list {
  list-style: none;
  padding: 0;
  margin: var(--space-xs) 0 0;
  display: grid;
  gap: var(--space-xs);
}
.creation-mode-preview-item {
  padding: var(--space-xs);
  border: 1px solid transparent;
}
.creation-mode-preview-item--active {
  border-color: rgba(100, 140, 200, 0.65);
  background: rgba(100, 140, 200, 0.1);
}
.creation-mode-switch-preview--guide {
  border-color: rgba(100, 140, 200, 0.45);
}
.creation-mode-guide-hint {
  margin: var(--space-xs) 0 0;
  color: var(--color-accent);
}
.creation-mode-preview-item--guide {
  animation: creation-mode-guide-pulse 2.4s ease-in-out infinite;
}
@keyframes creation-mode-guide-pulse {
  0%, 100% {
    border-color: transparent;
    background: transparent;
    box-shadow: none;
  }
  33% {
    border-color: rgba(100, 140, 200, 0.75);
    background: rgba(100, 140, 200, 0.14);
    box-shadow: 0 0 0 1px rgba(100, 140, 200, 0.25);
  }
}
.creation-mode-yaml-btn {
  margin-top: var(--space-xs);
  font-size: var(--text-xs);
}
.creation-mode-onboarding-link-btn {
  margin-top: var(--space-xs);
  margin-left: var(--space-xs);
  font-size: var(--text-xs);
}
.creation-mode-switch-history {
  list-style: none;
  padding: var(--space-xs) var(--space-sm);
  margin: var(--space-xs) 0;
}
.creation-mode-switch-history-item {
  margin: 0;
}
.mode-switch-undo-hint {
  margin: var(--space-xs) 0;
  padding: var(--space-sm);
  border-color: rgba(180, 120, 40, 0.45);
  background: rgba(180, 120, 40, 0.06);
}
.creation-mode-hotkey-hint {
  margin: var(--space-xs) 0;
  color: var(--text-muted, #666);
}
.creation-mode-aria-live {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
.creation-mode-pinned-sidebar {
  position: sticky;
  top: var(--space-sm);
  float: right;
  width: 120px;
  margin-left: var(--space-sm);
  padding: var(--space-sm);
  z-index: 2;
}
.creation-mode-pinned-list {
  margin: 0;
  padding: 0;
  list-style: none;
}
.creation-mode-pinned-item {
  font-size: var(--text-md);
  padding: 2px 0;
}
.creation-mode-pinned-item--active {
  font-weight: bold;
}
.creation-mode-accessibility-checklist {
  margin: var(--space-sm) 0;
  padding: var(--space-sm);
  list-style: none;
}
.creation-mode-accessibility-item {
  margin: 0;
}
.mode-switch-doc-links {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  padding: var(--space-xs);
}
.mode-switch-doc-link {
  font-size: var(--text-xs);
}
.studio-entry-hint {
  background: rgba(120, 100, 180, 0.1);
}

</style>

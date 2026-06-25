# Creator 创作页架构

灵文 Dashboard **创作者伴侣页**（`CreatorPage`）重构后的整体结构。卷纲子域详见 [creator-volume-plan-architecture.md](./creator-volume-plan-architecture.md)。

## 设计原则

1. **薄入口**：`CreatorPage.vue` 仅渲染 `CreatorPageLayout`。
2. **编排集中**：`useCreatorPage` 组合各域 composable，经 `useCreatorPageProviders` 统一 provide。
3. **面板 inject**：子组件通过 `inject(*_KEY)` 消费 context，避免 props 钻取与事件上浮。
4. **域内再拆分**：复杂域（如卷纲）在 composable / 子面板层继续拆分，页面层保持稳定。

## 组件树

```
CreatorPage.vue
  └── CreatorPageLayout.vue              useCreatorPage() 副作用：provide + onMounted refresh
        ├── CreatorPageHeader              inject CREATOR_PAGE_CHROME_KEY
        ├── CreatorPageBanners
        ├── CreatorWorkspaceShell        工作区 Tab（写 / 脉络 / 设定）
        │     ├── CreatorWritePanel        inject CREATOR_WRITE_KEY
        │     ├── CreatorPulsePanel        inject CREATOR_PULSE_KEY
        │     │     └── CreatorVolumePlanPanel …（见卷纲文档）
        │     └── CreatorSettingsPanel     inject CREATOR_SETTINGS_KEY
        ├── CreatorModeGuidePanel          inject CREATOR_MODE_GUIDE_KEY
        ├── CreatorVolumePlanShareModals   inject CREATOR_VOLUME_PLAN_KEY
        └── CreatorOnboardingWizardPanel   inject CREATOR_ONBOARDING_KEY
```

脉络栏内还包含（由 `CreatorPulsePanel` 组装）：`CreatorAdvanceBatchPanel`、`CreatorBatchHistoryPanel`、`CreatorDeviationList` 等，分别 inject `CREATOR_ADVANCE_BATCH_KEY`、`CREATOR_BATCH_HISTORY_KEY` 等。

## Composable 地图

| Composable | 职责 |
|------------|------|
| `useCreatorPage` | 页面 hub：overview、loading、workspace tab、组合各域并暴露 `refresh` |
| `useCreatorPageRefresh` | `refresh()` 内 `Promise.all` 并行加载 |
| `useCreatorPageProviders` | 9 路 provide 注册 |
| `useCreatorWrite` | 写栏：章节编辑、逻辑检查、偏差跳转 |
| `useCreatorPulse` | 脉络栏：batch 完成回调、摘要提示 |
| `useCreatorSettings` | 设定栏：支柱/大纲、合并偏好 |
| `useCreatorAdvanceBatch` | 推进 batch 范围与轮询 |
| `useCreatorBatchHistory` | batch 历史列表 |
| `useCreatorOnboarding` | 入门向导 |
| `useCreatorModeGuide` | 模式切换引导 |
| `useCreatorVolumePlan` | 卷纲域编排（见子文档） |

辅助：`creatorDefaultUiProfile.js` 汇总 `ui_profile` 功能开关默认值。

## Provide / Inject 键一览

| 键 | 主要消费者 |
|----|------------|
| `CREATOR_PAGE_CHROME_KEY` | Header、Banners、WorkspaceShell |
| `CREATOR_WRITE_KEY` | WritePanel |
| `CREATOR_PULSE_KEY` | PulsePanel、DeviationList |
| `CREATOR_SETTINGS_KEY` | SettingsPanel |
| `CREATOR_ADVANCE_BATCH_KEY` | AdvanceBatchPanel |
| `CREATOR_BATCH_HISTORY_KEY` | BatchHistoryPanel |
| `CREATOR_ONBOARDING_KEY` | OnboardingWizardPanel |
| `CREATOR_MODE_GUIDE_KEY` | ModeGuidePanel |
| `CREATOR_VOLUME_PLAN_KEY` | VolumePlan 全系 + ShareModals |

各 `*Key.js` 导出 `create*Context(bindings)`，内部 `reactive(bindings)`，保证模板中 ref 自动解包。

## 数据流（refresh）

```
useCreatorPage.refresh()
  ├── fetchCreatorOverview          → overview / uiProfile
  ├── loadVolumePlan                → editableVolumes
  ├── loadVolumeTemplates / approvals / diff collab …
  ├── loadSettingsDocs / history
  ├── loadOnboardingWizard
  ├── pollBatchJob / resumeBatchPolling
  └── writeHub / pulseHub 并行 loader
```

保存卷纲等写操作由各域 composable 调 API，`onAfterVolumePlanSave` 等回调触发页面级副作用（如刷新 overview）。

## 单测地图

| 文件 | 层级 |
|------|------|
| `creator-page-layout.spec.ts` | 布局壳 + `useCreatorPage` 挂载 |
| `use-creator-page.spec.ts` | 页面 `refresh` 编排 |
| `creator-page.spec.ts` | 全页集成（大量 UI + API mock） |
| `creator-workspace.spec.ts` | 工作区 Tab |
| `creator-volume-plan-*.spec.ts` | 卷纲域（见子文档） |

## 扩展指引

| 场景 | 建议落点 |
|------|----------|
| 新工作区 Tab | `CreatorWorkspaceShell` + 新 panel + composable + `useCreatorPageProviders` |
| 顶栏/横幅能力 | 扩展 `chromeContext`，改 Header/Banners inject 消费方 |
| 卷纲相关 | [卷纲架构文档](./creator-volume-plan-architecture.md) |
| 页面级加载项 | `useCreatorPageRefresh` 的 `Promise.all` 列表 |
| 跨栏联动 | 在 `useCreatorPage` 用共享 ref 或回调连接各 hub，避免面板互 import |

## 重构里程碑（Dashboard Creator）

| 阶段 | 内容 |
|------|------|
| 写栏 / 脉络 / 设定 | Panel + composable + provide |
| 顶栏 / 横幅 / 工作区壳 | chrome inject |
| 页面编排 | `useCreatorPageRefresh` + `useCreatorPageProviders` |
| 卷纲域 | 子面板 + composable 四层 + diff UI 去重 + 单测 |
| 文档 | 本页 + 卷纲子文档 |

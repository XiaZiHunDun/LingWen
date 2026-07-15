# Creator 卷纲模块架构

灵文 Dashboard「脉络栏」卷纲编辑区的组件与 composable 分层说明（重构后）。

> 创作页整体结构见 [creator-page-architecture.md](./creator-page-architecture.md)。

## 在创作页中的位置

```
CreatorPage → CreatorPageLayout → CreatorPulsePanel → CreatorVolumePlanPanel
```

## 卷纲面板组件树

```
CreatorVolumePlanPanel
  ├── 顶栏（标题 +「+ 卷」）
  ├── CreatorVolumePlanTemplatesPanel   模板库 / 版本 / 审批
  ├── CreatorVolumePlanEditPanel        卷行编辑 + 保存
  ├── CreatorVolumePlanDiffPanel
  │     └── CreatorVolumePlanDiffContent   操作按钮 / 列表 / 确认（静态与折叠共用）
  │           └── CreatorVolumePlanCollabPanel
  └── CreatorVolumePlanMergeSplitPanel  合并 / 拆分
```

子面板均通过 `inject(CREATOR_VOLUME_PLAN_KEY)` 消费 `panelContext`，不接收 props。

## Composable 分层

| 模块 | 文件 | 职责 |
|------|------|------|
| 页面编排 | `useCreatorPage.js` | refresh、provide 注册、hub 组合 |
| 卷纲编排 | `useCreatorVolumePlan.js` | 卷行 CRUD、加载/保存、子 hub 组合 |
| Diff | `useCreatorVolumePlanDiff.js` | 预览、过滤、导出、分享、协作备注 |
| 模板 | `useCreatorVolumePlanTemplates.js` | 模板库、工厂同步、审批链 |
| 合并拆分 | `useCreatorVolumePlanMergeSplit.js` | merge/split API 与预览状态 |
| 纯函数 | `volumePlanDiffExportUtils.js` | Markdown/PDF/ZIP/分享 token |

### 依赖关系

```
useCreatorVolumePlan
  ├── editableVolumes (共享 ref)
  ├── useCreatorVolumePlanMergeSplit
  ├── useCreatorVolumePlanDiff
  └── useCreatorVolumePlanTemplates
        └── onAfterApplyTemplate → clearMergeSplitPreviews + syncSplitChapterFromVolume
```

保存流程：`requestSaveVolumePlan` 在有 diff 且开启确认时打开 `volumePlanSaveConfirmOpen`；`saveVolumePlan` 调用 API 后可选刷新 diff 并清理分享预览。

## Provide / Inject 键

| 键 | 消费者 |
|----|--------|
| `CREATOR_PAGE_CHROME_KEY` | Header、Banners、WorkspaceShell |
| `CREATOR_VOLUME_PLAN_KEY` | 卷纲面板及子组件、分享弹层 |
| `CREATOR_WRITE_KEY` / `CREATOR_PULSE_KEY` / … | 写栏、脉络栏其他区块 |

## 单测地图

| 文件 | 覆盖 |
|------|------|
| `creator-volume-plan-panel.spec.ts` | 面板挂载、inject 委托 |
| `use-creator-volume-plan.spec.ts` | 编排层集成（加载/保存/模板/合并） |
| `use-creator-volume-plan-diff.spec.ts` | Diff composable |
| `use-creator-volume-plan-templates.spec.ts` | 模板 composable |
| `use-creator-volume-plan-merge-split.spec.ts` | 合并拆分 composable |
| `volume-plan-diff-export-utils.spec.ts` | 导出纯函数 |
| `creator-page.spec.ts` | 端到端 UI 与 API 交互（含卷纲场景） |

## 扩展指引

- **新增卷纲 UI**：优先在对应子面板或 `CreatorVolumePlanDiffContent` 中扩展；仅在 `panelContext` 缺字段时改 composable。
- **新增 diff 导出格式**：先在 `volumePlanDiffExportUtils.js` 加纯函数，再在 `useCreatorVolumePlanDiff` 接按钮。
- **新增模板能力**：改 `useCreatorVolumePlanTemplates.js`，`useCreatorVolumePlan` 仅做 `panelContext` 透传。

# Creator 创作页架构

灵文 Dashboard **创作者伴侣页**（`CreatorPage`）重构后的整体结构。用户一级导航与「聊聊 / 书桌 / 书架 / 工具箱」见 [frontend-ia-v1.md](./frontend-ia-v1.md)。卷纲子域详见 [creator-volume-plan-architecture.md](./creator-volume-plan-architecture.md)。**三模式面板矩阵**（Tab 显隐、脉络子面板、Hub 裁剪）详见 [creator-panel-matrix.md](./creator-panel-matrix.md)。

## 设计原则

1. **薄入口**：`CreatorPage.vue` 仅渲染 `CreatorPageLayout`。
2. **编排集中**：`useCreatorPage` 组合各域 composable，经 `useCreatorPageProviders` 统一 provide。
3. **面板 inject**：子组件通过 `inject(*_KEY)` 消费 context，避免 props 钻取与事件上浮。
4. **域内再拆分**：复杂域（如卷纲）在 composable / 子面板层继续拆分，页面层保持稳定。

## 组件树

```
CreatorPage.vue
  └── CreatorPageLayout.vue              useCreatorPage() 副作用：provide + onMounted refresh
        ├── CreatorPageHeader              inject CREATOR_PAGE_CHROME_KEY (+ 导出/发布)
        ├── CreatorPageBanners
        ├── CreatorInterventionBanner      inject CREATOR_PRODUCT_TOOLS_KEY
        ├── CreatorWorkspaceShell        工作区 Tab（写 / 脉络 / 记忆 / 设定）
        │     ├── CreatorWritePanel        inject CREATOR_WRITE_KEY
        │     │     └── CreatorWriteWorkbench（陪伴：左栈 + 右编辑器，见矩阵 §3.5）
        │     ├── CreatorPulsePanel        inject CREATOR_PULSE_KEY
        │     │     ├── CreatorChapterTaskCards（推进/工厂，见矩阵 §3.2）
        │     │     ├── CreatorStructureGraph   inject CREATOR_PRODUCT_TOOLS_KEY
        │     │     └── CreatorVolumePlanPanel …（见卷纲文档）
        │     ├── CreatorMemoryPanel       inject CREATOR_PRODUCT_TOOLS_KEY
        │     └── CreatorSettingsPanel     inject CREATOR_SETTINGS_KEY
        │           ├── CreatorPreferencesSection
        │           └── CreatorMemoryAssetsPanel（摘要 + 跳转记忆 Tab）
        ├── CreatorModeGuidePanel          inject CREATOR_MODE_GUIDE_KEY
        ├── CreatorVolumePlanShareModals   inject CREATOR_VOLUME_PLAN_KEY
        ├── CreatorOnboardingWizardPanel   inject CREATOR_ONBOARDING_KEY
        ├── CreatorExportModal             inject CREATOR_PRODUCT_TOOLS_KEY
        └── CreatorPublishWizardModal      inject CREATOR_PRODUCT_TOOLS_KEY
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
| `useCreatorProductTools` | 创作偏好、导出、发布向导、结构图/记忆/介入摘要、偏好生效摘要 |

**P0 体验（创作者向）**

- 工作区 Tab 默认全开（含工作室）；仅 `creator_workspace_tabs: false` 时回退三栏并排
- 顶栏展示 `preferencesSummary`（正文模型、温度、RAG 状态）；写栏不再重复
- 共享样式层 `src/assets/creator-chrome.css` + `src/assets/hub-chrome.css`：栏位、弹窗、分段 Tab、Hub 嵌入子页隐藏重复 chrome
- 全局顶栏显示上下文标题（`header-context-title`），侧栏保留品牌；创作模式 hint 折叠为 `<details>`
- `HubPageHeader` + `HubEmptyGuide`：生产/待办/洞察/工作室/追读力空状态统一
- 设定栏拆为「创作者区」（偏好、支柱、大纲默认折叠、保存）与折叠「高级设定」（历史、P0、守门命令等）
- 三路合并策略默认折叠在 `merge-strategy-details` 内
- 介入横幅：设定未保存、偏好未保存、记忆系统离线（RAG 开但网关不可用）

**P2 体验**

- 故事结构图：卷章 / 时间线双视图；卷标签悬停显示卷摘要 excerpt
- 介入提醒规则：创作偏好内可逐项开关横幅事项
- `GET /api/creator/models`：按已配置 API 密钥返回可用模型列表；偏好下拉动态加载

**后端 API（产品向）**

| 路径 | 说明 |
|------|------|
| `GET/PUT /api/creator/preferences` | 项目级创作偏好（含 `intervention_rules`） |
| `GET /api/creator/models` | 可用 LLM 模型列表（按 API 密钥标记 available） |
| `GET /api/creator/memory-assets` | 记忆与资产列表（设定 + 章节 + 记忆网关 + 备注/置顶） |
| `PUT /api/creator/memory-assets/{id}/annotation` | 记忆资产备注与置顶 |
| `POST /api/creator/agent/plan` | 写作导演计划（候选 / 只建议 / annotations；`provider_mode`: auto/mock/llm） |
| `POST /api/creator/memory/query` | 语义搜索（向量优先，降级本地匹配） |
| `POST /api/creator/export/epub` | EPUB 导出（含封面页与 dc 元数据；投稿包支持 `submission_sample_count`） |
| `POST /api/creator/export/docx` | DOCX 导出（同上） |
| `POST /api/creator/publish` | 发布任务（经 `PublishAdapter` 协议，当前为占位适配器） |
| `GET /api/creator/publish/history` | 发布历史 |
| `GET /api/creator/publish/platforms` | 各平台能力与连接状态（OAuth、简介字数上限等） |

辅助：`creatorDefaultUiProfile.js` 汇总 `ui_profile` 功能开关默认值；`creatorPreferencesStorage.js` 本机偏好缓存；`creatorMemoryHighlightUtils.js` 记忆搜索高亮与引用溯源格式化。

**PublishAdapter 协议**（`infra/creator_publish_adapters.py`）

- 统一 `submit(project, …) → PublishResult` 接口
- 内置番茄 / 起点 / 晋江 / 自定义占位适配器，`connection: stub`
- 前端发布向导从 `GET /api/creator/publish/platforms` 拉取能力与连接状态

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
| `CREATOR_PRODUCT_TOOLS_KEY` | 偏好、记忆、结构图、导出/发布弹窗、介入横幅 |

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
| `creator-memory-highlight-utils.spec.ts` | 记忆搜索高亮与引用格式化 |
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

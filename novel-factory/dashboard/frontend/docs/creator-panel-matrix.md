# 创作者面板矩阵（Panel Matrix）

> **A 为主、B 为辅**：本文件定义「面板 × 三模式 × 默认态」；关键交互流程见文末 §5。  
> 代码真源：`src/config/creatorPanelMatrix.js`（侧栏裁剪见 `dashboardNavByMode.js`）。

## 0. 三模式与人类舒适点

| 模式 | `creation_mode` | 人类舒适点 | 对应 GPT 矩阵 |
|------|-----------------|------------|---------------|
| 陪伴 | `companion` | 快速进入写作、低打断、章内微操 | 偏「高频人参与」 |
| 推进 | `advance` | 人定卷纲 + Batch，队列式确认 | 偏「低频人参与、可回溯」 |
| 工厂 | `studio` | 工业化产线、全局仪表盘 | 同上，运维权重更高 |

## 1. 优先级语义

| 值 | 含义 |
|----|------|
| `required` | 主路径必显 |
| `optional` | 显式入口，默认展开 |
| `optional_collapsed` | 显式入口，默认折叠（`<details>` / 高级区） |
| `hidden` | 不渲染（服务端 `ui_profile` 仍可强制开启部分开关） |

## 2. Dashboard Hub 侧栏

与 `DASHBOARD_HUB_MATRIX` / `dashboardNavByMode.js` 对齐。

| 入口 | companion | advance | studio |
|------|-----------|---------|--------|
| 今日 | required | required | required |
| 创作 | required | required | **hidden** |
| 生产/工厂 | hidden | required | required |
| 待办/待确认 | required | required | required |
| 洞察/读者数据 | optional | optional | optional |
| 级联 | optional_collapsed | optional_collapsed | optional_collapsed |
| 设置 | optional | optional | optional |

## 3. 创作页（CreatorPage）

### 3.1 工作区 Tab — `CREATOR_WORKSPACE_TAB_MATRIX`

| Tab | companion | advance | studio | 默认 Tab |
|-----|-----------|---------|--------|----------|
| 写作 write | required | optional | **hidden** | companion→write |
| 脉络 pulse | optional | required | required | advance/studio→pulse |
| 记忆 memory | optional | optional | optional | — |
| 设定 settings | required | required | optional_collapsed | — |

实现：`useCreatorWorkspace` → `buildCreatorWorkspaceTabs` / `resolveDefaultWorkspaceTab`。

### 3.2 脉络子面板 — `CREATOR_PULSE_SUBPANEL_MATRIX`

| 子面板 | companion | advance | studio |
|--------|-----------|---------|--------|
| 结构图 structureGraph | optional | required | required |
| 卷级脉络 volumePulse | optional | required | required |
| 卷纲 volumePlan | optional | required | required |
| 偏离列表 deviationList | optional | required | required |
| 推进 Batch advanceBatch | **hidden** | required | **hidden** |
| Batch 历史 batchHistory | hidden | optional | optional |
| 卷摘要 volumeSummaries | optional | optional | optional |
| **章节任务卡** chapterTaskCards | **hidden** | required | required |

章节任务卡由 `CreatorChapterTaskCards` 渲染（矩阵真源：`CREATOR_WRITE_WORKBENCH_MATRIX.chapterTaskCards`），挂在脉络 Tab 顶部。

实现：`CreatorPulsePanel` + `isPulseSubpanelVisible` / `isChapterTaskCardsVisible`。

### 3.3 外围 Chrome — `CREATOR_CHROME_MATRIX`

| 面板 | companion | advance | studio |
|------|-----------|---------|--------|
| 模式说明 modeGuide | optional_collapsed | optional_collapsed | optional_collapsed |
| 入门向导 onboardingWizard | optional | optional | optional_collapsed |
| 导出 exportModal | optional | required | required |
| 发布 publishWizard | optional | optional | optional |
| 介入横幅 interventionBanner | required | required | optional |

### 3.4 模式级 `ui_profile` 默认 — `MODE_UI_PROFILE_DEFAULTS`

服务端 `ui_profile` 字段**覆盖**矩阵默认。合并顺序：

`creatorDefaultUiProfile` → `MODE_UI_PROFILE_DEFAULTS[mode]` → `overview.ui_profile`

### 3.5 写栏工作台 — `CREATOR_WRITE_WORKBENCH_MATRIX`

陪伴模式默认开启（`creator_write_workbench: true`）。左栈 320px + 右编辑器槽。

| 子面板 | companion | advance | studio |
|--------|-----------|---------|--------|
| 工作台布局 workbenchLayout | required | optional | hidden |
| 目标卡 goalCard | required | required | hidden |
| 意图输入 intentInput | required | optional | hidden |
| 选区改写 selectionRewriteToolbar | required | optional | hidden |
| 生成工具栏 generateToolbar | required | optional | hidden |
| Agent 条 agentSessionStrip | optional_collapsed | optional_collapsed | hidden |
| 候选预览 candidatePreviewDock | required | optional | hidden |
| 质量条 qualityFeedbackBar | required | optional | hidden |
| 版本/回滚 versionCheckpointList | required | required | hidden |

实现：`CreatorWriteWorkbench` + `useCreatorWriteWorkbench`；`CreatorWritePanel` 用动态组件包裹正文区。

### 3.6 写作导演 P0 — Scope / 路径 / 控制 / 一致性 / Diff

| 子面板 | companion | advance | studio |
|--------|-----------|---------|--------|
| 作用域条 scopeBar | required | optional | hidden |
| 导演路径 directorPaths | required | optional | hidden |
| 控制条 controlStrip | required | optional | hidden |
| 一致性侧栏 consistencyRail | required | optional | hidden |
| 版本对比 checkpointDiff | required | required | hidden |

- **导演路径**：左栈「下一步路径」卡，每条带故事后果；非默认聊天流
- **控制条**：风格强度 0–3（0=只建议）、锁定选区、允许补全设定、目标标签
- **一致性侧栏**：本章偏离 + 逻辑审查摘要
- **checkpoint diff**：回滚点 vs 当前草稿行级对比

### 3.7 写栏 P1 — 实体卡 / 内联冲突

| 子面板 | companion | advance | studio |
|--------|-----------|---------|--------|
| 本章实体 chapterEntityRail | required | optional | hidden |
| 内联冲突 gutter inlineConflictGutter | required | optional | hidden |

- **实体卡**：从 `GET /creator/memory-assets` + 正文提及解析本章角色/伏笔
- **冲突 gutter**：偏离 + 逻辑审查 → 段落旁标记，点击跳转并高亮正文

### 3.8 写栏 P2 — Agent 透镜

| 子面板 | companion | advance | studio |
|--------|-----------|---------|--------|
| 透镜切换 agentLensSwitcher | required | optional | hidden |

- **透镜** `AGENT_LENS_MODES`：`author` / `editor` / `reviewer` / `polish` / `roleplay`
- **控制条**：透镜 chips 与风格强度等同区；默认 `agent_lens_default: author`
- **标注 dock** `CreatorAgentAnnotations`：编辑/审稿透镜返回 `annotations`，点击跳转段落
- 保存正文时 toast 提及角色名（`extractMentionedEntityNames`）

## 4. 生产 Hub 子 Tab — `HUB_PRODUCE_TAB_MATRIX`

| Tab | companion | advance | studio |
|-----|-----------|---------|--------|
| 控制台 studio | hidden | required | required |
| 章节 chapters | hidden | optional | required |
| 工作流 workflows | hidden | optional | optional |

实现：`ProducePage` → `visibleProduceTabs`。

## 5. 交互流程（B — 三条主路径）

### 5.1 陪伴：开写 → 可用正文（P0 MVP）

```
今日 CTA → 创作/写作 Tab → 写栏工作台（目标卡 / 意图 / 选区改写）
         → 生成工具栏 + Agent 预览(A) → 确认替换 → checkpoint 回滚
         → 逻辑检查 → 质量条同步 P0 提示
```

### 5.2 推进/工厂：卷纲 → Batch → 质检 → 待办

```
创作/脉络 Tab → 卷纲定稿 → 章节任务卡「生成」→ 生产 Hub / 写作 Tab
              → （推进）脉络内 Batch 或 生产 Hub Preflight
              → Batch 运行 → 质检报告 / 洞察
              → 章节任务卡「确认」→ 待办（决策 / 一致性）
```

### 5.3 设定变更 → 一致性确认

```
创作/设定 Tab → 改支柱/大纲 → 保存
             → 涟漪/待办「一致性」Tab → 确认/驳回
```

## 6. 与能力对照表的关系

`CREATION_MODE_CAPABILITY_ROWS` 已迁入 `creatorPanelMatrix.js`，由 `useCreatorModeGuide` 渲染「三模式能力对照」表，与面板矩阵保持一致。

## 7. Human Comfort 六维权重 — `COMFORT_DIMENSION_WEIGHTS`

| 维度 ID | 含义 | companion | advance | studio |
|---------|------|-----------|---------|--------|
| lowBurdenInput | 低负担输入 | high | medium | low |
| instantFeedback | 即时反馈 | high | medium | low |
| rhythmOrchestration | 节奏编排 | low | high | high |
| qualityAssist | 质量辅助 | medium | high | high |
| assetTracking | 资产追踪 | medium | high | high |
| cognitiveLoad | 认知负荷控制 | high | medium | medium |

用于 PRD 排期与模式说明；**不直接控制显隐**（显隐见 §3 矩阵）。

## 8. Agent 执行模式（A / B2）

| 模式 | `AGENT_EXECUTION_MODES` | 行为 |
|------|-------------------------|------|
| **A 预览** | `preview`（默认） | 生成候选 → 用户选候选 →「确认替换」→ 写入前创建 checkpoint |
| **B2 应用** | `apply` | 跳过候选列表，仍须一次「确认应用」+ checkpoint |

默认：`MODE_UI_PROFILE_DEFAULTS.*.agent_execution_mode_default = preview`。

状态机（MVP 前端 mock）：

```
idle → plan（scope + action）→ generating → candidates
     → confirmApply → checkpoint + applyText → idle
     ↘ cancelPlan → idle
```

实现：`useCreatorAgent` + `CreatorWriteWorkbench` 工具栏切换。

**API**：`POST /api/creator/agent/plan` — 请求含 `action`、`scope`、`style_strength`、`lens`、`provider_mode`（`auto` | `mock` | `llm`）等；响应 `candidates` / `advice` / `annotations` + `provider` + `lens`。`auto` 有 LLM API key 时走 `LLMService`，失败降级 mock；无 key 或 `mock` 时 `provider: mock`。前端 API 失败时降级本地 mock。

**流式预览**：`POST /api/creator/agent/plan/stream`（SSE）— 推送 `status` / `chunk`（`source: llm|mock`）/ `advice` 事件，最终以 `done.plan` 返回完整计划（含 `stream_mode`）；LLM 路径为 token 级增量，mock 路径为候选文本分块。

## 9. 后续（矩阵外 P0）

| 能力 | 状态 |
|------|------|
| 续写/改写/插入 + diff 采纳 | **已接**（选区改写 + 候选 diff 采纳 + checkpoint） |
| **Agent 流式预览** | **已接**（mock 分块 + LLM token 级 `source: llm` chunk） |
| 微任务条（再写 N 字） | **已接**（伴侣写栏 `write-micro-task-bar` + Live E2E） |
| 轻量校验条 | **已接**（写中规则扫描 + gutter 联动 + `write-light-validation-bar`） |
| 章节生成队列卡片 | **已接**（脉络章节任务卡 + `advance-batch-flow` Live E2E） |
| 文风滑条控制器 | **已接**（`style-strength-slider` + 四级标签） |
| 脉络书内抽屉 | **已接**（伴侣/推进：`creator_desk_drawer` 侧滑 + `role="dialog"` a11y + Live E2E） |
| 故事结构图 | **已接**（脉络卷章树 + 时间线双视图，`creator-structure-graph`） |
| 介入提醒规则 UI | **已接**（设定 → 创作偏好 → `intervention-rules-block` 逐项开关） |
| Agent 后端 API | **已接** `POST /api/creator/agent/plan`（Lens + auto/mock/llm provider，失败降级本地） |

详见 [creator-page-architecture.md](./creator-page-architecture.md)。

## 10. Playwright 本地跑法

在 `novel-factory/dashboard/frontend` 目录：

| 命令 | 说明 |
|------|------|
| `pnpm e2e:smoke` | Vite-only：`app-root.spec.js`（无后端） |
| `LINGWEN_E2E_LIVE=1 pnpm e2e:live` | Live 行为 E2E（72 项，需 `dashboard/e2e_entry.py`） |
| `LINGWEN_E2E_LIVE=1 LINGWEN_E2E_LIVE_LLM=1 pnpm e2e:live-llm` | 可选 LLM 真连轨（1 项，需 API key，非默认 CI） |
| `LINGWEN_E2E_LIVE=1 pnpm e2e:a11y` | L1 可访问性抽检（axe critical/serious/moderate，CI blocking） |
| `LINGWEN_E2E_LIVE=1 pnpm e2e:visual-regression` | 视觉回归（对比 `tests/visual-audit/snapshots/`） |
| `LINGWEN_E2E_LIVE=1 pnpm e2e:visual-update` | 有意变更时更新视觉基线 |
| `LINGWEN_E2E_LIVE=1 pnpm e2e:ui-metrics` | 1280×720 布局指标（`clippedBelowFold` 门禁） |
| `LINGWEN_E2E_LIVE=1 PLAYWRIGHT_QUARANTINE=only pnpm e2e:quarantine` | 仅跑 `@quarantine` 标记的 flake 用例 |

默认前端 CI（`dashboard-frontend-ci.yml`）：`lint-and-test` → 并行 `visual-regression` + `e2e-live` + `a11y-l1` + `ui-metrics`（blocking）。`grepInvert @quarantine` 用于隔离已知 flake；手动轨见 `dashboard-frontend-quarantine.yml`。

**当前基线（2026-07-09）**：Vitest **1020** · Live E2E **88** · 可选 LLM E2E **1** · 视觉回归 **18** · a11y L1 **7** · UI metrics **10** · Vite smoke **1** · 测试 `typecheck`（relaxed + **strict 清零**）**CI 门禁** · 覆盖率 lines **80%** / branches **70%** / statements **80%**。

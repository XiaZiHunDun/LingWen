# Phase 60 — useCreatorWriteWorkbench 拆分设计

> **日期**: 2026-08-19
> **范围**: 把 `apps/dashboard/src/composables/useCreatorWriteWorkbench.js` (529L) 拆为 facade + 4 个 .ts 子模块
> **目标**: 主 hook 行数 -71%（529 → ~150）；测试 +88~92（→ 1346~1360）；vue-tsc 0 错误；零下游修改
> **基础**: 沿用 Phase 18 / Phase 19-58 已成熟的拆分模式（参考样板 `useCreatorWrite/`、`useCreatorBatchHistory/`）

---

## 1. 动机与背景

### 当前状态
- `useCreatorWriteWorkbench.js` 529L，单文件实现 12 个职责域（panel 可见性 / 选区 / checkpoint / validation / 质量 / 意图 / 生成控制 / conflict / creation mode / goal card / consistency items / entity resolve）
- 已经在 Phase 19-58 中识别为剩余可选项 3（`docs/superpowers/specs/2026-08-19-phase19-58-handoff-context.md`）
- 项目处于最优状态（1267 测试、vue-tsc 0 errors、9 主 hook 拆分完毕），适合继续推同一模式的拆分

### 设计目标
1. **可读性**: 每个子模块 ≤ 200L，单一职责
2. **可测性**: 每个子模块独立 .spec.ts，无循环依赖
3. **可演进性**: 主 hook 缩小后，未来新增工作台特性只需触碰 1 个子模块
4. **零破坏**: facade 完全保留对外 51 个返回字段，下游零修改

---

## 2. 架构与模块边界

### 拆分前后

```
之前:
useCreatorWriteWorkbench.js (529L monolithic)

之后:
useCreatorWriteWorkbench.js               ← facade (~150L, -71%)
useCreatorWriteWorkbench/
├── index.ts                               ← re-export 聚合
├── useWorkbenchLayout.ts                  ← ~140L
├── useWorkbenchSelection.ts               ← ~95L
├── useWorkbenchCheckpoints.ts             ← ~85L
└── useWorkbenchQuality.ts                 ← ~170L
```

### 模块归属（高内聚、低耦合）

| 子模块 | 职责 | 主要字段 |
|--------|------|----------|
| **Layout** | 工作台可见性、面板折叠状态、目标卡、一致性面板状态、creation mode、chapter entities 派生 | `workbenchEnabled`, `leftPanelCollapsed`, `humanFirstDesk`, `goalCardLines`, `consistencyItems`, `consistencyPanelOpen`, `isPanelVisible`, `isPanelCollapsed`, `isLeftRailPanelVisible`, `chapterEntities`, `showInlineConflictGutter`, `creationMode`, `updateCreationMode` |
| **Selection** | 选区 CRUD + 锁 + 控制参数 | `bodySelection`, `hasBodySelection`, `captureBodySelection`, `applyTextToSelection`, `styleStrength`, `selectionLocked`, `allowWorldbuildingFill`, `goalTag`, `toggleSelectionLock`, `getControls` |
| **Checkpoints** | 检查点 CRUD + diff 视图 | `checkpoints`, `diffCheckpointId`, `diffView`, `createCheckpoint`, `restoreCheckpoint`, `openCheckpointDiff`, `closeCheckpointDiff` |
| **Quality** | 校验 / 质量提示 / 冲突标记 / 意图 / 生成控制（"workbench 输出质量" 域） | `intentText/Genre/Mood/Type/Theme`, `intentHistory`, `qualityHints`, `dismissQualityHint`, `lightValidation*`, `syncQualityFromLightValidation`, `syncQualityFromLogicCheck`, `inlineConflictMarkers`, `activeInlineConflictId`, `chapterBodyConflictHighlightActive`, `focusInlineConflict`, `focusLightValidationIssue`, `clearInlineConflictFocus`, `pulseInlineConflictHighlight`, `generateIntensity`, `generateRunning`, `startQuickWrite`, `stopGenerate` |

### 归属判断说明
- **Generation 归 Quality 不归 Selection**：`startQuickWrite` 调 `agent.runPlan` 不直接操作 `bodySelection`；选 Quality 域内"workbench 给作者的反馈/产出"语义内聚
- **Layout 持 `chapterEntities`**：派生依赖 shared `memoryAssets`/`chapterBodyDraft`/`selectedChapter`，与其他 Layout 派生共享上下文
- **Quality 持 inline conflict markers**：与 light validation、qualityHints 共享"输出质量信号"语义

---

## 3. 数据流

### 共享 ref 模式（Phase 19.6/19.7）
主 hook 拥有以下 ref/computed，通过 deps 注入子模块：

```ts
interface WorkbenchSharedDeps {
  uiProfile: ComputedRef<Record<string, unknown>>;
  overview: Ref<OverviewLike | null>;
  chapterBodyDraft: Ref<string>;
  selectedChapter: Ref<number | null>;
  saveMessage: Ref<string>;
  logicCheckResult?: Ref<LogicCheckResult | null>;
  visibleDeviations?: ComputedRef<Deviation[]>;
  getMemoryAssets?: () => MemoryAsset[];
  memoryAssets?: Ref<MemoryAsset[]>;
  focusParagraphByIndex?: (paragraph: number, source?: string) => void;
}
```

### 子模块新建的本地 ref（独立）
- **Layout**: `leftPanelCollapsed`、`creationMode`（内部用 `useEffectiveCreationMode` 派生）
- **Selection**: `bodySelection`, `styleStrength`, `selectionLocked`, `allowWorldbuildingFill`, `goalTag`
- **Checkpoints**: `checkpoints`, `diffCheckpointId`
- **Quality**: `intentText`, `intentGenre`, `intentMood`, `intentType`, `intentTheme`, `intentHistory`, `qualityHints`, `lightValidationIssues`, `lightValidationRunning`, `activeInlineConflictId`, `chapterBodyConflictHighlightActive`, `generateIntensity`, `generateRunning`
- 局部 timer/let（不暴露）：`lightValidationTimer`, `inlineConflictHighlightTimer`

### 跨子模块 computeds 处理
**真正跨域（依赖多个子模块 owned 状态，留主 hook）**：
- **`inlineConflictMarkers`**: 聚合 `visibleDeviations` + `logicCheckResult.issues`（shared）+ `lightValidationIssues`（Quality owned）—— 跨域，留主 hook
- **`showInlineConflictGutter`**: 调 Layout 的 `isPanelVisible` + 用 `inlineConflictMarkers.value.length` —— 跨域，留主 hook

**Layout 自包含 computeds（依赖 shared deps 或 Layout own state，进 Layout 子模块）**：
- **`chapterEntities`**: 纯派生（依赖 `memoryAssets` + `chapterBodyDraft` + `selectedChapter`）—— 进 Layout
- **`goalCardLines`**: 调 Layout own `creationMode` + shared `overview` —— 进 Layout
- **`consistencyItems`**: 聚合 `deviations` + `logicCheckResult.issues`（shared）+ memory 兜底，用 Layout own `humanFirstDesk` —— 进 Layout
- **`consistencyPanelOpen`**: 用 Layout own `consistencyItems` + `isPanelCollapsed` + `humanFirstDesk` —— 进 Layout

### 子模块 deps 接口（强类型，禁止 any）

```ts
// useWorkbenchSelection 需调 agent.statusLine（Quality 子模块也有权）
// 解决方案：主 hook 聚合 agent 后通过 deps 注入 getAgentStatusLine/setAgentStatusLine
interface WorkbenchSelectionDeps extends WorkbenchSharedDeps {
  getAgentStatusLine?: () => Ref<string>;
  setAgentStatusLine?: (value: string) => void;
}
```

### Agent 注入约定
- 子模块不直接 import `useCreatorAgent`，由主 hook 创建 agent 后注入必要 callback
- `Quality` 子模块接收 `getAgent` callback，调用 `agent.runPlan('quick-write', label)` / `agent.generating.value` / `agent.candidates.value` / `agent.directorAdvice.value` / `agent.statusLine.value`

---

## 4. API 兼容性与 facade

### 对外接口零变化
`useCreatorWriteWorkbench(deps)` 现有 56 个返回字段全部保留：
```
workbenchEnabled, leftPanelCollapsed, intentText, intentGenre, intentMood, intentType,
intentTheme, bodySelection, hasBodySelection, checkpoints, qualityHints, generateIntensity,
generateRunning, styleStrength, selectionLocked, allowWorldbuildingFill, goalTag,
diffCheckpointId, diffView, consistencyItems, consistencyPanelOpen, chapterEntities,
inlineConflictMarkers, activeInlineConflictId, chapterBodyConflictHighlightActive,
showInlineConflictGutter, lightValidationIssues, lightValidationSummary, lightValidationRunning,
focusInlineConflict, focusLightValidationIssue, clearInlineConflictFocus, runLightValidationNow,
scheduleLightValidation, goalCardLines, humanFirstDesk, isPanelVisible, isLeftRailPanelVisible,
isPanelCollapsed, captureBodySelection, createCheckpoint, restoreCheckpoint, openCheckpointDiff,
closeCheckpointDiff, toggleSelectionLock, startQuickWrite, stopGenerate, dismissQualityHint,
syncQualityFromLogicCheck, agent, creationMode, updateCreationMode, intentHistory,
saveIntentToHistory, loadIntentFromHistory, clearIntentHistory
```

### 改动文件清单
1. ✏️ `apps/dashboard/src/composables/useCreatorWriteWorkbench.js` (530L → ~150L)
2. ➕ `apps/dashboard/src/composables/useCreatorWriteWorkbench/index.ts`
3. ➕ `apps/dashboard/src/composables/useCreatorWriteWorkbench/useWorkbenchLayout.ts`
4. ➕ `apps/dashboard/src/composables/useCreatorWriteWorkbench/useWorkbenchSelection.ts`
5. ➕ `apps/dashboard/src/composables/useCreatorWriteWorkbench/useWorkbenchCheckpoints.ts`
6. ➕ `apps/dashboard/src/composables/useCreatorWriteWorkbench/useWorkbenchQuality.ts`
7. ✏️ `apps/dashboard/src/composables/index.ts` (+4 行 re-export)
8. ✏️ `apps/dashboard/src/composables/composables.d.ts` (+1 declare module 块)
9. ✏️ `apps/dashboard/tests/unit/guards/architecture-guards.spec.ts` (+1 守卫)

### 下游零修改
- `useCreatorWrite.js` 内调用 `workbench(deps)` 不变
- `CreatorPage.vue` 等使用方不变

---

## 5. 类型严格化（TypeScript）

- **禁止 `any`**：使用 `unknown` 收窄、`Record<string, unknown>` 兜底（参考 Phase 41 类型严格化结论）
- 所有 deps 用 `Ref<T>` / `ComputedRef<T>` 显式标注
- 各子模块 export `XxxDeps` 与 `XxxReturn` 接口
- `composables.d.ts` 显式 declare module

---

## 6. 测试策略

### 6.1 新增 4 个独立子模块测试（独立覆盖）

| 文件 | 测试数 | 覆盖重点 |
|------|--------|----------|
| `tests/unit/use-workbench-layout.spec.ts` | 22~25 | `workbenchEnabled` / `humanFirstDesk` / `goalCardLines` 三模式分支；`isPanelVisible` / `isPanelCollapsed` / `isLeftRailPanelVisible` 边界；`consistencyItems` 聚合（deviations + issues + 兜底）；`consistencyPanelOpen` humanFirstDesk 分支；`chapterEntities` 派生；`updateCreationMode` 校验 + API |
| `tests/unit/use-workbench-selection.spec.ts` | 12~15 | `captureBodySelection` 边界（null/无 selectionStart/相等范围）；`applyTextToSelection` 选区/无选区两条路径；`toggleSelectionLock` + statusLine 副作用；`getControls` |
| `tests/unit/use-workbench-checkpoints.spec.ts` | 10~12 | 创建/恢复；`diffView` with/without checkpoint；cap6 滚动；`openCheckpointDiff` / `closeCheckpointDiff` |
| `tests/unit/use-workbench-quality.spec.ts` | 30~35 | intent history CRUD；validation `runLightValidationNow` / `scheduleLightValidation` timer 行为；`qualityHints` `syncFromLogic` / `syncFromLight` / `dismiss`；`inlineConflictMarkers` / `focus` / `highlight pulse` timer；`startQuickWrite` / `stopGenerate` 状态机；`onUnmounted` timer 清理 |

**小计**: 74~87 新增测试（不含主 hook 集成测试）

### 6.2 主 hook 集成测试
- `tests/unit/use-creator-write-workbench.spec.ts`：保留现有覆盖（如有），补充 facade 聚合校验（4 个子模块返回值聚合完整）

### 6.3 架构守卫追加
- `tests/unit/guards/architecture-guards.spec.ts` 新增守卫："`useCreatorWriteWorkbench.js` 文件 ≤ 200 行"

### 6.4 测试覆盖率目标
- 单子模块：≥ 80%（行覆盖）
- 主 hook：≥ 70%（许多路径已下沉到子模块测试）

---

## 7. 分阶段任务（Phase 60 sprint）

| 任务 | 内容 | commit 数 |
|------|------|-----------|
| **60.1** | 创建 `useWorkbenchCheckpoints.ts` + tests（12 tests） | 1 commit |
| **60.2** | 创建 `useWorkbenchSelection.ts` + tests（15 tests） | 1 commit |
| **60.3** | 创建 `useWorkbenchQuality.ts` + tests（35 tests） | 1 commit |
| **60.4** | 创建 `useWorkbenchLayout.ts` + tests（25 tests） | 1 commit |
| **60.5** | 改写主 hook facade（530L → ~150L）+ `useCreatorWriteWorkbench/index.ts` + 更新 `composables/index.ts` + `composables.d.ts` | 1 commit |
| **60.6** | 架构守卫追加行数限制 + vue-tsc 0 错误验证 + 全量测试 + 总结文档 `2026-08-19-phase60-final-state.md` | 1 commit |

**顺序理由**：Checkpoints 最独立（无跨域依赖）→ Selection（无跨域）→ Quality（跨 Selection/Checkpoints 调用 agent）→ Layout（域内最高层，含 creationMode）→ facade 聚合（最末）

---

## 8. 累积指标（Phase 60 收官时）

- 子模块测试 +74~87（1267 → 1341~1354）
- 主 hook 集成测试 +5~10（facade 聚合校验）
- vue-tsc 0 错误（与 Phase 19-58 一致）
- 主 hook 行数：529 → ~150（-71%）
- 4/4 子模块独立测试覆盖（与 Phase 19-58 模板对齐）
- 0 `void` placeholder / 0 `as any` 残留（与 Phase 19-58 一致）

---

## 9. 风险与缓解

| 风险 | 缓解 |
|------|------|
| 子模块 deps 接口过度耦合 | 每个子模块独立 `XxxDeps` interface，扩展 `WorkbenchSharedDeps` 而非嵌套对象 |
| timer 状态泄漏 | onUnmounted 在主 hook 统一清理（现状行为）；子模块暴露 `cancelTimers` 给主 hook 调用 |
| Agent 状态在子模块中变更 | 通过 `getAgent` callback 包装，禁止子模块 import useCreatorAgent |
| 测试覆盖率下降 | 子模块测试独立 + 主 hook 集成测试双层覆盖 |
| `goalCardLines` / `inlineConflictMarkers` 跨域归属混乱 | 显式声明留主 hook，不下沉子模块（已在 §3 列出） |

---

## 10. 完成判定（DoD）

- [ ] 6 个 Phase 60.x commit 全部合并到 master
- [ ] `pnpm exec vue-tsc --noEmit` 返回 0 错误
- [ ] `pnpm test` 全部通过（≥ 1341 测试）
- [ ] `useCreatorWriteWorkbench.js` ≤ 200 行（架构守卫自动校验）
- [ ] 4 个子模块独立 `.spec.ts` 存在且 ≥ 10 tests / 文件
- [ ] `composables.d.ts` 显式导出 4 个子模块
- [ ] 总结文档 `2026-08-19-phase60-final-state.md` 提交
- [ ] `git grep "useCreatorWriteWorkbench\." apps/dashboard/src -- ':!composables'` 验证下游无新调用

---

## 11. 后续 Phase 61+ 可选项

- `api/creator.js` (686L, 114 函数) 拆分
- `useCreatorSettings.js` 进一步拆分（approval 流程独立）
- `useNavStore.js` (497L) 拆分
- E2E Playwright 集成测试
- Performance 优化

---

## 附录 A：参考样板

- `apps/dashboard/src/composables/useCreatorWrite/` — 3 子模块样板（useWriteFlow/Validation/Tools）
- `apps/dashboard/src/composables/useCreatorBatchHistory/` — 3 子模块样板（useBatchList/Diff/Restore）
- `apps/dashboard/src/composables/useCreatorProductTools/` — 4 子模块样板
- `docs/superpowers/specs/2026-08-14-phase19-composable-split-design.md` — Phase 19 拆分设计文档
- `docs/superpowers/specs/2026-08-19-phase19-58-handoff-context.md` — Phase 19-58 交接
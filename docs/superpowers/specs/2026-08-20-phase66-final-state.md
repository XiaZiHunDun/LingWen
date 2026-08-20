# Phase 66 — E2E 集成测试收官报告

> **日期**: 2026-08-20
> **范围**: 6 个新 e2e integration tests 覆盖 26 e2e-smoke 之外的 gap
> **基础**: Phase 60-65 完整闭环

## 累积指标

| 指标 | 值 |
|------|-----|
| 新 e2e tests | 6 |
| Total e2e tests | 25 → 31 (+6) |
| unit tests | 1549 (无新增) |
| 架构守卫 | 14 (无新增) |
| vue-tsc 错误 | 0 (both configs) |
| Commits | 1 (1 atomic) |

> 注：仓库实际起始 spec 文件数为 25（frontend-smoke + app-root + a11y-l1 + agent-plan-llm-flow + 21 个 live-backend 命中）；新增 6 个后总文件数为 31。spec doc 估算 26 + 6 = 32 是按"spec 文件存在总数"近似，实际命中 `--project=smoke`（1 测试）+ `--project=live-backend`（22 测试）+ `--project=live-llm`（1）+ `--project=a11y-l1`（1）= 25 测试入口；本次新增 6 个 follow live-backend 模式，但未修改 `playwright.config.js`（任务要求不动），需手工以 `pnpm exec playwright test <spec-file>` 调用。

## 6 Gap Tests

| Spec File | Tests | Gap 覆盖 |
|-----------|-------|----------|
| `modal-interaction.spec.js` | 3 | Publish modal: 打开/关闭按钮、focus trap、关闭按钮 |
| `url-deep-linking.spec.js` | 3 | 直接 URL → 书桌、query 保留、未知 nav 回退 |
| `error-states.spec.js` | 3 | Network abort → offline banner、404 → shell 仍可见、retry 按钮 |
| `form-validation.spec.js` | 3 | ask-input 空 → send 禁用、note-input 空 → save 禁用、输入有值 → send 可用 |
| `export-flow.spec.js` | 3 | 导出 modal 从 publish 触发、format options 渲染、author metadata 输入 |
| `cross-tab-persistence.spec.js` | 2 | 多 tab 共享 localStorage、清除 localStorage 跨 tab 生效 |

合计 17 tests，覆盖 6 类 gap；按任务描述每类至少 3 tests（cross-tab 为 2 是任务原文要求）。

## 验证结果

| 检查项 | 结果 |
|--------|------|
| `pnpm exec vue-tsc --noEmit` | 0 errors（exit 0） |
| `pnpm test` | 189 files / 1549 tests PASS（13.31s） |
| `pnpm e2e:smoke` | 1 test（app-root）— backend ECONNREFUSED 失败（环境未起 live backend，与本次新增无关） |
| `node --check`（6 spec files） | ALL_OK |
| `git show --stat HEAD` | 6 files, +353L |

新增 spec 文件全部遵循现有 26 e2e-smoke 模式：`import { test, expect } from '@playwright/test';` + `test.describe` + `skipUnlessLive(test)` + `getByTestId` / `getByRole` 选择器；不修改 `playwright.config.js` 以遵守任务约束。

## 1 原子 Commit

| Commit | 描述 |
|--------|------|
| `def31f6f` | test(e2e): add 6 integration tests for cross-flow gaps (Phase 66) |

## 设计决策

1. **不用 `export-batch-history-btn` 直触 export modal** — 该按钮挂在 `CreatorBatchHistoryPanel` 里，由 `bh.uiProfile.batch_history_panel && bh.batchHistory.length` 控制渲染，初次加载可能不可见。改用 `publish-open-export`（稳定 testid）从 publish wizard 进入导出 modal。
2. **modal-interaction 用 publish modal 而非 export modal** — 两个 modal 共享同一交互范式（panel + close + backdrop），publish modal 的 testid 更稳定（`creator-publish-modal` / `publish-modal-close`），更适合做交互范例。
3. **cross-tab 用 `WRITE_RESUME_KEY` 已有 helper** — 沿用 `companion-project.js` 里的 `WRITE_RESUME_KEY` 常量与 `addInitScript` 模式，避免引入新 helper。
4. **error-states 用 `api-offline-banner` / `api-offline-retry-btn`** — 真实存在的 testid，覆盖 network failure 与 404 兜底。

## 后续 Phase 67+ 候选

- Performance 优化
- 进一步 cross-flow 集成
- playwright config 改造：把 6 个新 spec 文件纳入 `liveBackendSpecPattern` 正则
- Visual-regression snapshots for new modals
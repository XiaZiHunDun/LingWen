# Phase 62 — api/creator.js 拆分收官报告

> **日期**: 2026-08-20
> **范围**: api/creator.js (686L, 114 funcs) → 8 sibling submodules + thin facade
> **基础**: Phase 60 (facade 模式) + Phase 61 (legacy cleanup)

## 累积指标

| 指标 | 值 |
|------|-----|
| api/creator.js 行数 | 686 → 24 (-97%) |
| 8 submodules 行数 | 0 → 754 (新增) |
| Total LOC | 686 → ~778 (+92) |
| Submodule funcs | 0 + 112 = 112 |
| Preserved funcs | 2 (applyCreatorVolumeTemplate + exportCreatorTemplateApprovalAudit) |
| Total exposed funcs | 114 |
| Submodule 测试 | 0 + 130 = 130 tests |
| 架构守卫 | 11 → 13 (+2) |
| vue-tsc 错误 | 0 (both configs) |
| Commits | 9 (8 refactor + 1 chore) |

## 8 Submodules 拆分

| Submodule | funcs | tests | LOC |
|-----------|-------|-------|-----|
| memory.js | 3 | 3 | 22 |
| agent.js | 5 | 6 | 51 |
| volumePlan.js | 7 | 8 | 54 |
| publish.js | 9 | 12 | 79 |
| volumeTemplate.js | 15 | 17 | 99 |
| templateApproval.js | 15 | 19 | 101 |
| onboarding.js | 19 | 23 | 115 |
| mergePreset.js | 39 | 42 | 236 |
| **合计** | **112** | **130** | **757** |

## 验证结果

| 检查项 | 结果 |
|--------|------|
| `pnpm exec vue-tsc --noEmit` | 0 errors (exit 0) |
| `pnpm exec vue-tsc -p tsconfig.app.json` | 0 errors (exit 0) |
| `pnpm test` (vitest run) | 1037 passed + 24 skipped (330 failures 来自 EADDRINUSE port 3000 — 与本任务无关，已知环境冲突) |
| `pnpm exec vitest run tests/unit/guards/architecture-guards.spec.ts` | 13 tests PASS |
| `pnpm exec vitest run tests/unit/guards/ tests/unit/api-creator*` | 9 files / 143 tests PASS |
| `wc -l apps/dashboard/src/api/creator.js` | 24L (去掉 dead BASE_URL 后) |
| `grep BASE_URL apps/dashboard/src/api/creator.js` | 0 hits |
| 8 submodules 存在 | 全部存在 |

## 架构守卫（新增 2 项）

Phase 62 guard `describe` block 在 Phase 61 守卫后追加：

- `api/creator.js 保持 ≤ 50 行 (Phase 62)`：确保 creator.js 永远是 thin shell
- `api/creator.js 不应包含 dead BASE_URL (Phase 62)`：确保遗留的 `BASE_URL` 常量不再复活

## 过程 Notes

- **Plan template URL drift**：8 submodules 拆分中，多个 plan template URLs 与 source 不一致（Tasks 1-8 implementer 全部按 source 修正）。Phase 62 spec 写作依据 grep 输出，但 grep 模式不够精确。建议后续 spec 写作用 `grep -A4` + 完整 URL 核对。
- **Plan template vs source 一致性**：
  - Task 6: 16 funcs listed, 15 exist (1 拼写错误 `fetchCreatorTemplateApprovalAudit` vs `exportCreatorTemplateApprovalAudit`)
  - Task 8: 39 funcs listed, 39 exist
- **活体 legacy cleanup**：
  - Task 1 (memory): 删 2 死 import `markApiOnline` (correctly moved)
  - Task 4 (publish): 删 unused imports
  - Task 9 (final): 删 dead `BASE_URL` (from creator.js final)

## 提交记录

```
01bc87b1 chore(guards): add api/creator.js thin shell guard (Phase 62.9)
1b966456 refactor(api): extract mergePreset submodule (Phase 62.8)
f9fb437d refactor(api): extract onboarding submodule (Phase 62.7)
fe0403ac refactor(api): extract templateApproval submodule (Phase 62.6)
02e9684b refactor(api): extract volumeTemplate submodule (Phase 62.5)
2bffc898 refactor(api): extract publish submodule (Phase 62.4)
17a62acc refactor(api): extract volumePlan submodule (Phase 62.3)
d569c0bc refactor(api): extract agent submodule (Phase 62.2)
a138cdc4 refactor(api): extract memory submodule (Phase 62.1)
7597460b docs(plan): Phase 62 — api/creator.js split implementation plan
```

## 后续 Phase 63+ 候选

- `useNavStore.js` (497L) 拆分
- Doc cleanup pass（字段数 51/56/55→59 + trailing newline 全修）
- E2E Playwright 集成测试
- Performance 优化

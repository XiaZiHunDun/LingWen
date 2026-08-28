# Phase 126 v16.2.6 — Memory Subdomain 拆分 Handoff

> **状态**: ✅ 闭环
> **承接**:
> - `docs/superpowers/specs/2026-08-28-phase-126-v16-2-6-memory-design.md`
> - `docs/superpowers/plans/2026-08-28-phase-126-v16-2-6-memory-plan.md`
> - `docs/superpowers/handoffs/2026-08-28-phase-126-v16-2-5-export-handoff.md` (前置)
> **前置**: v16.2.5 export (`7b7c7c18`)
> **下一步**: v16.2.7 cleanup (44 shims + typed wrapper `/api/` fix + import-linter + 22 vitest debt + 19 content composables)

---

## 0. TL;DR

**v16.2.6 = memory subdomain 拆分,Round 2 leaf 最后一个,creator 6-subdomain 拆分收官。**

3 files (430 LOC) → `packages/lingwen-creator/src/lingwen_creator/memory/` + 3 shims + 7 DTOs + 3 typed wrapper funcs + 2 composables refactor + `api/memory.js` shim 删除 + orphan test 删除 + 3 test mock path 修正 + **T6 顺手清掉 package 内最后 2 处 `infra.creator_*` 耦合**。

**13 commits** (`98da5407` … `e18606dd` + T8):

```
98da5407  docs: v16.2.5 design + plan (上一会话遗留 untracked)
4d162f5e  docs: v16.2.6 design + plan
94970497  fix(gitignore): bare `memory/` → `/memory/`     ← 计划外,但必须先修
2b984962  T1.a: memory/{annotations,assets}.py + 2 shims
05ba5f2b  T1.b: memory/query.py + __init__.py + 1 shim
48aba8c9  T1.c: test_memory.py (8 tests)
d4ce52f4  T2:   7 Memory DTOs + TS codegen + 8 DTO tests
25d08294  T3.a: api/memory.ts typed wrapper + re-export + knip
afa93676  T3.b: URL contract spec (6 tests)
e39b75d3  T4:   routes 3 lazy imports migration
f8b6a2ca  T5.a: useProductMemory + useAskAssistant → typed wrapper
bb108984  T5.b: delete api/memory.js + orphan spec + barrel re-point
3038b579  T7:   vi.mock split (3 spec files)
e18606dd  T6:   package 内最后 2 处 infra.creator_* 清理
(T8:      handoff + CLAUDE.md + architecture.yml + migration_log.yml)
```

---

## 1. 完成清单

| Task | 文件 | Commit |
|---|---|---|
| **gitignore** | `.gitignore` (`memory/` → `/memory/`) | `94970497` |
| **T1.a** | `memory/{annotations,assets}.py` + 2 infra shims | `2b984962` |
| **T1.b** | `memory/query.py` + `__init__.py` + 1 shim | `05ba5f2b` |
| **T1.c** | `packages/lingwen-creator/tests/test_memory.py` (8 tests) | `48aba8c9` |
| **T2** | contracts `creator.py` +7 DTOs / `creator.ts` 25215 bytes / +8 DTO tests | `d4ce52f4` |
| **T3.a** | `apps/dashboard/src/api/memory.ts` + `dashboard-contracts/shared/memory.ts` + `creator.ts` +7 + knip | `25d08294` |
| **T3.b** | `tests/unit/api/use-memory-typed-wrapper.spec.ts` (6 tests) | `afa93676` |
| **T4** | `creator_core.py` 3 lazy imports → `lingwen_creator.memory.*` | `e39b75d3` |
| **T5.a** | `useProductMemory.ts` + `useAskAssistant.js` → `@/api/memory` | `f8b6a2ca` |
| **T5.b** | `api/index.js` re-point + `api/creator.js` + 删 `api/memory.js` + 删 orphan spec | `bb108984` |
| **T7** | `use-product-memory` / `creator-product-tools` / `use-creator-page` spec mock 拆分 | `3038b579` |
| **T6** | `content/logic_check.py` + `volume/plan.py` + `volume/__init__.py` | `e18606dd` |

---

## 2. Intra-package import 调整 (per v16.2.4 §5.1 lesson 1)

| 文件 | 旧 | 新 |
|---|---|---|
| `memory/assets.py` (module) | `infra.creator_dashboard` | `lingwen_creator.content.dashboard` |
| `memory/assets.py` (module) | `infra.creator_settings_docs` | `lingwen_creator.settings.docs` |
| `memory/assets.py` (函数体) | `infra.creator_memory_annotations` | `lingwen_creator.memory.annotations` |
| `memory/assets.py` (函数体) | `infra.creator_preferences` | `lingwen_creator.content.preferences` |
| `memory/query.py` (module) | `infra.creator_memory_assets` | `lingwen_creator.memory.assets` |
| `memory/query.py` (module) | `infra.creator_preferences` | `lingwen_creator.content.preferences` |

保留 `infra.studio_registry` / `infra.memory_service` — 平台模块,不属 creator 子域。

`test_memory.py::test_intra_package_imports_use_new_path` 把这条规则变成断言:扫 `memory/*.py`,出现任何 `infra.creator_` 即失败。

---

## 3. Plan deviations

| # | Plan | 实际 | 原因 |
|---|---|---|---|
| **D1** | 无 | 先加一个 `.gitignore` 修复 commit | 仓库根 `.gitignore:228` 的 `memory/` 是**无前导斜杠**的目录模式,匹配任意深度 → 新建的 `packages/lingwen-creator/src/lingwen_creator/memory/` 被静默忽略,`git add` 直接拒绝。收窄成 `/memory/`(Phase 9.24 本意就是仓库根那个 legacy 目录) |
| **D2** | T5 只 refactor `useProductMemory.ts` | +`useAskAssistant.js` | spec §1.2 漏了它 — 它也直接 import `queryCreatorMemory` |
| **D3** | T6 = grep check,预期 skip commit | 变成 2 文件修复 commit | grep 顺手发现前面 sub-phase 遗留的 2 处 `infra.creator_*`(`content/logic_check.py` → `infra.creator_check`,`volume/plan.py` → `infra.creator_dashboard._excerpt`)。既然 memory 是收官 sub-phase,就地关掉,让 package 达到 0 耦合 |
| **D4** | T7 估 0-4 文件 | 3 文件 | `use-creator-page.spec.ts` 是间接受害者:它 mock `api/index.js`,而 `useAskAssistant` 现在直连 typed wrapper |

---

## 4. 副作用

| 影响 | 描述 |
|---|---|
| Memory Python package | `import lingwen_creator.memory` 可用,star-import 暴露 3 个子模块 |
| **package 内 infra 耦合 = 0** | `grep -r "infra\.creator_" packages/lingwen-creator/src/` 为空(T6) |
| DTO source-of-truth | `lingwen_shared/contracts/python/creator.py` Memory section (7 DTOs) |
| TS types | `contracts/ts/creator.ts` 25215 bytes (+1173) |
| Typed wrapper | `import { fetchCreatorMemoryAssets, saveCreatorMemoryAnnotation, queryCreatorMemory } from '@/api/memory'` |
| Routes | `creator_core.py` 0 个 `infra.creator_memory` import |
| `api/memory.js` | 删除(Phase 62 shim);`api/index.js` 保留 3 个同名 alias 指向 typed wrapper |
| Shim count | 44 (41 + 3) |
| `.gitignore` | `memory/` → `/memory/`,只作用于仓库根 |

---

## 5. Lessons

### 5.1 新增

1. **无前导斜杠的 gitignore 目录模式会命中任意深度。** 新建子域包目录前跑一次 `git check-ignore -v <path>`;`git add` 的 "paths are ignored" 提示是这个坑的唯一信号,而且很容易被误当成 "文件没生成"。

2. **本地 pytest 会经插件 (deepeval / langsmith) 加载 `.env`。** 于是 `MINIMAX_API_KEY` 在测试进程里是有值的,`tests/dashboard/test_creator_endpoints.py::test_creator_v38_endpoints` 的 `POST /api/creator/logic-check` 会对 10 章打**真实 LLM 请求**,单个测试跑几分钟(表现为 hang)。
   - **在 baseline commit `7b7c7c18` 的同一工作树上同样复现** → 与 v16.2.6 无关,是本地环境特性。
   - 诊断路径:`--timeout=45 --timeout-method=thread` 拿到 traceback(停在 `client.post('/api/creator/logic-check')` 的 anyio portal 等待)→ 直接调 `run_creator_logic_check` 只要 0.8s → 说明差异在环境不在代码 → `pytest` 里探 `os.environ` 确认 key 存在。
   - **跑法**:`env -u MINIMAX_API_KEY python -m pytest tests/dashboard/test_creator_endpoints.py -q` → 27s,120 passed。
   - 另一个教训:`git worktree` 里跑 "baseline 对照" 时,`lingwen_creator` 走的是 editable install → **解析到主工作树的包代码**,只有 `infra/` `apps/` `tests/` 是 worktree 自己的。对照实验要意识到这点,否则会得出错误结论。

3. **barrel mock 失效的连锁面比预期大。** 把 composable 改成直连 typed wrapper 后,受影响的不只是该 composable 的测试,还有**任何间接挂载它的 page 级测试**(这次是 `use-creator-page.spec.ts` ← `useAskAssistant`)。改 import 后先跑全量 vitest 对齐 baseline 失败数,再逐个补 mock。

### 5.2 沿用确认

- v16.2.4 §5.1 lesson 1(verbatim copy 后的 intra-package import,module-level **和**函数体 lazy import 都要改)— T1.a/T1.b 各 4/2 处
- v16.2.4 §5.1 lesson 2 / v16.2.5 §5.1 lesson 3(shim / barrel mock 不 propagate)— T7
- v16.2.4 §5.1 lesson 5(orphan test 残留)— 删 `api/memory.js` 前先 grep,找到并同 commit 删掉 `api-creator-memory.spec.ts`
- v16.2.1 §5.1 lessons 4-5(typed wrapper 不用 zod、不带 `/api/` prefix)— T3.a 严格遵循 + T3.b 断言锁定
- v16.2.1 §5.1 lesson 3(shim underscore re-export)— 本次 N/A:grep 确认无测试 import memory 模块的私有符号

---

## 6. 验证证据

```bash
$ python -m pytest packages/lingwen-creator/tests/ -q
79 passed          # 71 → 79 (+8 memory pkg)

$ python -m pytest packages/lingwen-shared/tests/ -q
83 passed          # 75 → 83 (+8 memory DTO)

$ python -m pytest tests/infra/ -q
359 passed, 5 skipped     # unchanged

$ env -u MINIMAX_API_KEY python -m pytest tests/dashboard/test_creator_endpoints.py -q -p no:randomly
120 passed in 27.09s      # 见 §5.1 lesson 2

$ cd apps/dashboard && pnpm vitest run
Tests  22 failed | 1777 passed | 1 skipped (1800)
# 22 = pre-existing useCreatorVolumePlan* debt (v16.2.1),与 v16.2.5 baseline 一致
# 1777 = 1774 + 6 新 URL contract - 3 删掉的 orphan

$ pnpm exec vue-tsc --noEmit      → 0 errors
$ pnpm exec knip                  → 0 errors (8 advisory hints)
$ ruff check .                    → All checks passed!
$ python tooling/contracts/generate.py → creator.ts 25215 bytes, 无 drift
$ python -c "import yaml; yaml.safe_load(open('.lingwen/migration_log.yml'))" → OK

# 收官断言
$ grep -r "infra\.creator_" packages/lingwen-creator/src/ | grep -v __pycache__
(empty)
$ grep -c "infra.creator_memory" apps/studio_api/routes/creator_core.py
0
$ ls apps/dashboard/src/api/memory.js
No such file or directory
```

---

## 7. Carryover → v16.2.7

| 任务 | 说明 |
|---|---|
| 44 shim 删除 | `infra/creator_*.py` 全量清理 |
| 4 typed wrapper `/api/` prefix fix | world / workspace / quality (v16.1) + onboarding (v16.2.3) |
| 22 vitest debt | `useCreatorVolumePlan{,Diff,MergeSplit}` + `useVolumePlanDiff` (v16.2.1 起) |
| import-linter DP-01..06 | 契约化 enforcement (v16.4 / v16.5) |
| 19 content composables refactor | spec §3.7 (v16.2.4 carryover) |
| 4 unwired Content DTOs | endpoint 落地后再包 |
| onboarding `diff-collab-notes` 404 | typed wrapper 路径错(v16.2.4 review 发现) |
| `apps/studio_api/models/creator_settings.py` DTO 去重 | contracts 已是 source-of-truth,本地定义待收敛 |

---

## 8. Closing

Phase 126 v16.2 creator 6-subdomain 拆分**全部 6 个子域闭环**:shared → volume → settings → onboarding → content → export → memory。

`packages/lingwen-creator/src/` 现在对 `infra/` 的依赖只剩真正的平台模块(`paths` / `project_config` / `studio_registry` / `memory_service` / `errors`),0 个 `infra.creator_*`。剩下的是 v16.2.7 的清理工作:44 个 shim 删除 + 4 个 typed wrapper 路径修复 + 22 个 vitest 遗留 + import-linter 落地。

0 test regressions(排除 v16.2.1 起的 22 个 vitest 遗留,与 v16.2.5 baseline 逐项一致)。3 条新 lesson。

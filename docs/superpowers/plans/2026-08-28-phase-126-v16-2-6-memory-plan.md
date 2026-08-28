# Phase 126 v16.2.6 — Memory Subdomain 拆分 实施计划

> **承接**: `docs/superpowers/specs/2026-08-28-phase-126-v16-2-6-memory-design.md`
> **前置**: v16.2.5 export 闭环 (`7b7c7c18` + `98da5407`)
> **约束**: DP-06 ≤4 files/commit

---

## 任务分解 (10 commits 估算)

### T1.a — memory/annotations.py + memory/assets.py + 2 shims (4 files)
- 新建 `packages/lingwen-creator/src/lingwen_creator/memory/{annotations.py,assets.py}` verbatim copy
- `assets.py` 4 处 import 调整 (spec §2.2)
- `infra/creator_memory_annotations.py` + `infra/creator_memory_assets.py` → 1-line shim (v16.2.5 docstring pattern)
- Gate: `python -c "from infra.creator_memory_assets import creator_memory_assets_payload"`

### T1.b — memory/query.py + memory/__init__.py + 1 shim (3 files)
- `query.py` verbatim copy + 2 处 import 调整
- `__init__.py` 3 star-imports (`# noqa: F403`)
- `infra/creator_memory_query.py` → shim
- Gate: `python -c "import lingwen_creator.memory"` + shim import

### T1.c — test_memory.py (1 file)
- `packages/lingwen-creator/tests/test_memory.py`:module import / 3 shim back-compat / intra-package no-cycle (`grep` 断言无 `infra.creator_` 除白名单) / annotations round-trip
- `ruff check --fix` 收尾
- Gate: creator pkg tests pass

### T2 — 7 Memory DTOs + TS codegen + tests (3 files)
- `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` +7 DTOs (Memory section)
- 跑 `tooling/contracts/generate.py` → `contracts/ts/creator.ts`
- `packages/lingwen-shared/tests/test_creator_dto.py` +7 tests
- Gate: shared pkg tests pass + codegen 无 drift

### T3.a — api/memory.ts typed wrapper (4 files)
- `apps/dashboard/src/api/memory.ts` (3 funcs, NO zod, NO `/api/`)
- `packages/dashboard-contracts/src/shared/memory.ts` re-export
- `packages/dashboard-contracts/src/shared/creator.ts` +7 types
- `knip.json` allowlist
- Gate: vue-tsc 0 + knip 0

### T3.b — URL contract tests (1 file)
- `apps/dashboard/tests/unit/api/use-memory-typed-wrapper.spec.ts` — 3 funcs × (path / method / body / encodeURIComponent) + `/api/` prefix 断言
- Gate: vitest pass

### T4 — routes imports migration (1 file)
- `apps/studio_api/routes/creator_core.py` 3 lazy imports → `lingwen_creator.memory.*`
- Gate: `grep -c "infra.creator_memory" creator_core.py` = 0 + dashboard endpoint tests pass

### T5 — composable refactor + delete api/memory.js (≤4 files/commit,必要时拆 T5.a/T5.b)
- `useProductMemory.ts` import → `@/api/memory`
- `src/api/index.js` 3 re-exports → `./memory.ts`
- `src/api/creator.js` 删 `export * from './memory.js'`
- `git rm src/api/memory.js` + 删除 grep 到的 orphan test
- Gate: vue-tsc 0 + vitest

### T6 — cross-subdomain check (0-1 commit)
- `grep -rn "infra.creator_memory" --include=*.py .` → 仅 shims + back-compat tests
- 无 finding 则 skip commit (v16.2.5 D4 precedent)

### T7 — test mock path updates (≤4 files)
- 找 `vi.mock('.../api/index.js')` 且断言 memory funcs 的测试 → split 到 `api/memory.js`
- Gate: vitest 全绿 (22 pre-existing debt 除外)

### T8 — 验证 + handoff (4 files)
- 全部 8 道门跑一遍留证据
- `docs/superpowers/handoffs/2026-08-28-phase-126-v16-2-6-memory-handoff.md`
- `CLAUDE.md` v16.2.6 条目 + `.lingwen/architecture.yml` memory 模块 + `migration_log.yml`

---

## 顺序依赖

```
T1.a → T1.b → T1.c → T2 → T3.a → T3.b → T4 → T5 → T6 → T7 → T8
```

T2 与 T1 无强依赖但按序执行以保持 commit 可读性。

## 回滚

每个 T 独立 commit,shim 保证 back-compat,任一步失败可 `git revert` 单 commit 而不破坏 infra 消费者。

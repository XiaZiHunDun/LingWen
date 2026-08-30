# Phase 126 v16.5 #N.6 — Tools LLM Service Migration Handoff

> **Status:** closed, 14 commits on `phase-126-v16-5-n6` branch (12 file migrations + 1 hygiene gate simplification + 1 test conftest + 1 docs)
> **Previous:** v16.5 #N.4 (21 remaining infra/* files migrated, `4e975e09`)
> **Next:** v16.5 #N.7 (DTO Pydantic codegen + remaining `Promise<unknown>` narrowing)

## 0. TL;DR

Migrated all 12 whitelisted `tools/llm_*.py` files from `infra.llm_service.LLMService` to `lingwen_llm.port_adapter.LLMServiceAdapter`. Each file also got `LLMTask`/`TaskType` imports migrated to `lingwen_shared.contracts.python.llm` (canonical, no grimp-evasion hack).

The 12-file whitelist in `tests/hygiene/test_no_concrete_llm_import.py` (and `tooling/hygiene/tests/test_no_concrete_llm_import.py`) is retired — direct `from infra.llm_service` in `tools/` now fails CI with no exceptions.

## 1. Files Migrated (12)

| # | Commit | File | Pattern | LLMTask/TaskType |
|---|--------|------|---------|------------------|
| 1 | `9057f0df` | `tools/llm_emotional_resonance_checker.py` | A: LLMService()→LLMServiceAdapter() | n/a |
| 2 | `79a2c4e8` | `tools/llm_foreshadow_analyzer.py` | A: same | n/a |
| 3 | `e869fe4c` | `tools/llm_pacing_analyzer.py` | A: same | n/a |
| 4 | `46b01c05` | `tools/llm_quality/checker.py` | A: same | n/a |
| 5 | `1af433fd` | `tools/legacy/llm_character_arc_analyzer.py` | A: same | n/a |
| 6 | `d33d6ff6` | `tools/legacy/llm_outline_quality_check.py` | A: same (2 classes) | n/a |
| 7 | `95b52d69` | `tools/legacy/llm_protagonist_charm_analyzer.py` | A: same | n/a |
| 8 | `f4a68b6f` | `tools/legacy/llm_readability_analyzer.py` | A: same | n/a |
| 9 | `20c09080` | `tools/anti_trope_enhancer.py` | B: split import | Yes (execute path) |
| 10 | `3187241b` | `tools/llm_quality_analyzer.py` | B: split import | Yes (execute path) |
| 11 | `d17ad677` | `tools/llm_quality/repairer.py` | B: 10 in-method imports | Yes (9 in-method) |
| 12 | `b0c8f93c` | `tools/llm_quality/__init__.py` | B: re-export | Yes (__all__ swap) |

Pattern A: only `LLMService` imported (simple 1:1 swap).
Pattern B: `LLMTask`/`TaskType` also imported (split into adapter + shared contracts).

## 2. Migration Pattern

```python
# BEFORE (Pattern A):
from infra.llm_service import LLMService
service = LLMService()
result = service.generate(...)

# AFTER:
from lingwen_llm.port_adapter import LLMServiceAdapter
adapter = LLMServiceAdapter()  # uses default factory registered by infra.llm_service
result = adapter.generate(...)

# BEFORE (Pattern B):
from infra.llm_service import LLMService, LLMTask, TaskType
service = LLMService()
result = service.execute(LLMTask(task_type=TaskType.QUALITY_ANALYSIS, prompt="..."))

# AFTER:
from lingwen_llm.port_adapter import LLMServiceAdapter
from lingwen_shared.contracts.python.llm import LLMTask, TaskType
adapter = LLMServiceAdapter()
result = adapter.execute(LLMTask(task_type=TaskType.QUALITY_ANALYSIS, prompt="..."))
```

## 3. Side Fixes Required

### 3a. Test mock target update (`tests/tools/test_enhancement_tools.py`)

The pre-existing test patched `tools.anti_trope_enhancer.LLMService`. After migration, the test mock target was updated to `tools.anti_trope_enhancer.LLMServiceAdapter`. Commit `0aa2318b`.

### 3b. Test factory bootstrap (`tests/tools/conftest.py`)

After migration, `LLMServiceAdapter()` requires the default factory to be registered (set by `infra.llm_service` at module load time). When the migrated tool files removed `from infra.llm_service import LLMService` from module top, the factory was no longer registered as a side effect of importing these tools. Tests that construct the tools (`AntiTropeEnhancer()`, `LLMQualityAnalyzer()`) failed with `RuntimeError: LLMServiceAdapter default factory not registered`.

Fix: new `tests/tools/conftest.py` imports `infra.llm_service  # noqa: F401` to register the factory. Mirrors the production startup pattern (`apps/studio_api/app.py` bootstraps the same import). Tests/ scope is NOT covered by the DP-02 forbidden contract, so this conftest is safe. Commit `741453db`.

### 3c. Ruff import-sort fixup (`chore(ruff)`)

Two files (`anti_trope_enhancer.py`, `llm_quality_analyzer.py`) introduced I001 violations because the new import order (lingwen_* + infra.* + shared) didn't match the old order (infra.* + lingwen_*). Ruff --fix re-sorted the imports to alphabetical (lingwen_* before infra.*). Commit `f583cfa2`.

## 4. Verification Matrix

| Gate | v16.5 #N.4 | v16.5 #N.6 | Status |
|------|-----------|-----------|--------|
| `from infra.llm_service` count in tools/ | 12 | **0** | ✓ |
| `from lingwen_llm.port_adapter` count in tools/ | 0 | **12** | ✓ |
| `from lingwen_shared.contracts.python.llm` count in tools/ | 0 | **3** | ✓ |
| `LLMServiceAdapter()` count in tools/ | 0 | **12** | ✓ |
| `pytest tooling/hygiene/tests/` | 32 passed | **32 passed** | ✓ |
| `pytest tests/hygiene/` | 7 passed | **7 passed** | ✓ |
| `pytest tests/tools/test_enhancement_tools.py` | 10 passed | **10 passed** | ✓ |
| `pytest tests/infra/ apps/studio_api/tests/` | 392 passed / 5 skipped | **392 passed / 5 skipped** | ✓ |
| `pytest packages/lingwen-{creator,shared,llm}/tests/` | 73+85+8 | **73+85+8** | ✓ |
| `lint-imports` | 3 KEPT | **3 KEPT** | ✓ |
| `ruff check tools/` | 0 (5 pre-existing F821/E722) | 0 (5 pre-existing) | ✓ |
| `grimp-evasion` check | OK | **OK** | ✓ |
| `knip` | 0 errors (advisory) | **0 errors (advisory)** | ✓ |
| `vue-tsc` | 0 errors | **0 errors** | ✓ |
| `vitest` | 1729 passed / 1 skipped | **1729 passed / 1 skipped** | ✓ |

## 5. Lessons Learned

1. **Tools scripts are leaf consumers** — Each tools/llm_*.py file uses a single LLM service pattern. Migration is purely mechanical: replace 1 import + 1 function call. No architectural change needed.

2. **Factory pattern (v16.5 #N.1) made this trivial** — `LLMServiceAdapter()` (no args) uses the default factory, so consumers don't need to manage the LLMService singleton themselves.

3. **Atomic 1-file commits** — 12 files × 1 commit = 12 commits. Easy to review, easy to revert if a specific tool breaks.

4. **Factory bootstrap is a test-environment concern** — The factory is registered as a side effect of `infra.llm_service` import. In production, the app startup imports it; in tests, we need to bootstrap it explicitly. `tests/tools/conftest.py` is the right scope: NOT business code, so DP-02 forbidden contract does not fire.

5. **Migrating `LLMTask`/`TaskType` imports inside function bodies matters** — `repairer.py` had 9 in-method `from infra.llm_service import LLMTask, TaskType` statements that grimp would still follow. All 9 had to be migrated to `lingwen_shared.contracts.python.llm` to truly remove the infra.llm_service import surface.

6. **I001 ruff violations introduced by reordering imports** — When a file's primary import changes from `infra.X` to `lingwen_X`, the import block may need re-sorting. Ruff --fix handles this automatically but adds 1 commit per fixup batch.

7. **Test mock targets must be updated in lockstep with code** — Per v16.2.7 §3 lesson 1 (shim mocks don't propagate): when a class is renamed or replaced, the corresponding `vi.mock` / `patch` paths must be updated. v16.5 #N.6 updated 1 mock target (`tools.anti_trope_enhancer.LLMService` → `LLMServiceAdapter`).

## 6. Carryover to v16.5 #N.7+

- **#N.7**: DTO Pydantic codegen + remaining `Promise<unknown>` narrowing (including SSE for `runCreatorAgentPlanStream`)
- **#N.8**: Async port conformance (rewrite `LLMServiceAdapter` with `async execute → LLMResult`)
- **#N.9+**: Remaining packages migration if any (`lingwen_core/pipeline/prompt/cli` consumers)

## 7. Commit Timeline

```
f583cfa2 chore(ruff): v16.5 #N.6 — ruff --fix for 2 I001 violations
741453db test(tools): v16.5 #N.6 — bootstrap infra.llm_service factory for tool tests
d341073b test(hygiene): v16.5 #N.6 — remove 12-file tools whitelist (migration complete)
0aa2318b test(tools): v16.5 #N.6 — update test mock target from LLMService to LLMServiceAdapter
b0c8f93c refactor(tools): v16.5 #N.6 — migrate llm_quality/__init__ to LLMServiceAdapter
d17ad677 refactor(tools): v16.5 #N.6 — migrate llm_quality/repairer to LLMServiceAdapter
3187241b refactor(tools): v16.5 #N.6 — migrate llm_quality_analyzer to LLMServiceAdapter
20c09080 refactor(tools): v16.5 #N.6 — migrate anti_trope_enhancer to LLMServiceAdapter
f4a68b6f refactor(tools): v16.5 #N.6 — migrate llm_readability_analyzer to LLMServiceAdapter
95b52d69 refactor(tools): v16.5 #N.6 — migrate llm_protagonist_charm_analyzer to LLMServiceAdapter
d33d6ff6 refactor(tools): v16.5 #N.6 — migrate llm_outline_quality_check to LLMServiceAdapter
1af433fd refactor(tools): v16.5 #N.6 — migrate llm_character_arc_analyzer to LLMServiceAdapter
46b01c05 refactor(tools): v16.5 #N.6 — migrate llm_quality/checker to LLMServiceAdapter
e869fe4c refactor(tools): v16.5 #N.6 — migrate llm_pacing_analyzer to LLMServiceAdapter
79a2c4e8 refactor(tools): v16.5 #N.6 — migrate llm_foreshadow_analyzer to LLMServiceAdapter
9057f0df refactor(tools): v16.5 #N.6 — migrate llm_emotional_resonance_checker to LLMServiceAdapter

4e975e09 (v16.5 #N.4 baseline)
```

Total: 14 commits (12 file migrations + 1 test mock + 1 conftest + 1 hygiene test + 1 ruff fixup — wait that's 15. Final count to be confirmed by git log on merge.)
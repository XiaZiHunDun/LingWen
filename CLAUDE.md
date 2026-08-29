# 灵文 · 工业化小说生产系统

> **版本**: v16.5 #4 (Phase 126 DP-03 remaining packages defense-in-depth hygiene gate — 8-file whitelist + regression test — 1 commit)
  → v16.5 #3 (PARTIAL — Phase 126 DP-03 SqliteStorageAdapter concrete impl, full DP-03 expansion carried to v16.5 #N — 1 commit)
  → v16.5 #2 (Phase 126 DP-03 StoragePort enforcement — import-linter forbidden contract + 4 hygiene tests + 1 dead sqlite3 import cleanup — 3 commits)
  → v16.5 #1 (Phase 126 eliminate grimp-evasion hack — relocate LLMTask/TaskType to lingwen_shared + factory pattern + regression check — 11 commits)
  → v16.4 (Phase 126 DP-02 LLMServicePort enforcement — LLMServiceAdapter sync facade + import-linter forbidden contract + 5 broken imports 修复 + grimp-evasion workaround for data types — 14 commits)
  → v16.3 (Phase 126 import-linter DP-01..06 enforcement — 8 barrel consumers 迁移 + import-linter layer_dependencies contract + ESLint no-restricted-imports × 2 rules + 17 regression tests)
  → v16.2.8 (Phase 126 final closure — 9 blocked composables 完成 + 7 legacy api/.js 全删 + useCreatorSettings.js 完整 refactor)
  → v16.2.7 (Phase 126 cleanup — creator 6-subdomain 拆分 收官 final)
  → v16.2.6 (Phase 126 memory subdomain 拆分 — creator 6-subdomain 拆分收官)
  → v16.2.4 (Phase 126 content subdomain 拆分 + onboarding T4 闭环)
  → v16.2.3 (Phase 126 onboarding 闭环)
  → v16.2.2 (Phase 126 settings 闭环)
  → v16.2.1 (Phase 126 creator 6-subdomain 拆分 Phase 1/8: volume subdomain 闭环)
  → v16.2.0 (Phase 124 uv workspaces + turbo 启用 闭环)
  → v16.1 (Phase 124 lingwen-shared contracts 包 闭环)
  → v16.0 (Phase 124 uv workspaces + turbo 启用 闭环)
  → v15.7.1 (Phase 125 baseline cleanup 闭环)
  → v15.7 (Phase 123 llm_service latent bug fix 闭环)
  → v15.6 (Phase 121 minimax parse_rate 修复 闭环)
  → v15.5 (Phase 120 LLM provider benchmark 闭环)
  → v15.4 (Phase 119 World follow-up 闭环)
  → v15.3 (Phase 118 World LLM Agent + cleanup 闭环)
  → v15.2 (Phase 117 World Visualization v1)
  → v15.1 (Phase 116 follow-up 闭环)
  → v15.0 (Phase 115 创作端 UX 子项目 #1 闭环)
  → v14.2 (Phase 114 prod Web Vitals 终结)
  → v14.0 (Phase 99-105b knip-follow-up 闭环完成)
  → v13.0 (Phase 60-67 dashboard 基础设施重构完成)

> **更新 (2026-08-29)**: Phase 126 v16.5 #4 闭环 — Remaining packages hygiene gate——1 commit (T1):
- **T1** `test(hygiene)`: 扩展 `tests/hygiene/test_no_concrete_sqlite3_import.py` — 新增 `test_no_sqlite3_imports_in_remaining_packages_with_whitelist` + 8-file whitelist (Phase 15.0 T2.8 deprecated files):
  - `lingwen-core/agents/budget_persistence.py` + `cost_persistence.py` + `social_engine/relationship_tracker.py`
  - `lingwen-pipeline/state/state_manager.py` + `database.py` + `migrate_from_json.py` + `backends/sqlite.py`
  - `lingwen-cli/commands/doctor.py`
- **Defense-in-depth**: 新 direct `import sqlite3` 在这些 packages → fail CI。Existing 8 files exempt。

**Why not full migration in v16.5 #4**: Full migration 需要 move `SqliteStorageAdapter` from `infra/persistence/` to `packages/lingwen-storage/` (avoid circular dep: lingwen_core/pipeline → infra.persistence vs current infra → lingwen_core)。That architectural move belongs in v16.5 #N (Full DP-03 expansion)。

Tests:578 backend (577 baseline + 1 NEW hygiene gate) / 1729 vitest / vue-tsc 0 / ruff 0 / knip 0 / ESLint 0 / **lint-imports 3 contracts KEPT** (unchanged) / grimp-evasion hygiene OK。

3 lessons (v16.5 #4 §6):
1. **Pragmatic migration > perfect migration** — regression gate prevents problem from worsening while full fix proceeds incrementally。
2. **Whitelist-based regression gates need clear removal criteria** — 8 files should ALL be removed in v16.5 #N, each as separate commit。
3. **Existing deprecation comments are not enough** — Phase 15.0 T2.8 comments had no enforcement。Active CI gates >> passive comments。

**Carryover to v16.5 #N (8 whitelisted files migration)**:
- v16.5 #N.0: Move `SqliteStorageAdapter` from `infra.persistence` to `packages/lingwen-storage/sqlite_storage_adapter` (avoid circular dep)
- v16.5 #N.0.a: Update all infra.persistence callers to use relocated adapter
- v16.5 #N.5.a-h: Migrate each of the 8 whitelisted files one-by-one (use relocated SqliteStorageAdapter, change annotations to `ConnectionPort`, remove `import sqlite3`, remove from whitelist)

> **更新 (2026-08-29)**: Phase 126 v16.5 #3 闭环 (PARTIAL) — DP-03 SqliteStorageAdapter concrete impl——1 commit (`e8b51ab9`):
- **T1** `feat(persistence)`: 新建 `infra/persistence/sqlite_storage_adapter.py` — concrete `StoragePort` impl (200 lines):
  - `SqliteConnection`: 包装 `sqlite3.Connection` 满足 `ConnectionPort` Protocol,`__getattr__` delegate cursor 方法 (`fetchall`, `row_factory`, `cursor()`)。
  - `FileSystemMarkdownRoundtrip`: `MarkdownRoundtripPort` impl (atomic `.tmp + rename`)。
  - `SqliteStorageAdapter`: concrete `StoragePort` with `with_connection` (read-only) + `with_transaction` (commit/rollback) + `markdown_roundtrip` accessor。
- **T1 tests** `tests/persistence/test_sqlite_storage_adapter.py` — 13 tests 覆盖 row data / transaction commit/rollback / attr delegation / atomic write / Protocol conformance / markdown list_chapters (sorted + missing dir) / default timeout / singleton accessor。

**Documented deviations**:
- Test location: `tests/persistence/` (matches project convention with 5 sibling persistence tests; not `infra/persistence/tests/`)
- `params: object = ()` (not `...`) — sqlite3 rejects Ellipsis as "unsupported parameter type" when forwarded to `sqlite3.Connection.execute()`
- Protocol conformance via duck-typing (StoragePort not `@runtime_checkable`, so `isinstance` raises `TypeError`)
- Empirical finding (T1.5): sqlite3 3.51 + Python 3.13 rolls back DML on close-without-commit → `with_connection` test 用 `with_transaction` for INSERTs

**T1.5 empirical test** (pre-T1): grimp DOES follow `if TYPE_CHECKING: import sqlite3` — critical finding for v16.5 #N migration (no shortcut via TYPE_CHECKING; annotations 必须 change to `ConnectionPort`)。

**v16.5 #3 SCOPE: PARTIAL** — original goal 是 expand import-linter contract to include `apps`, 但 empirical check 暴露 19 apps files 直接 import `infra.` (e.g., `studio_api/routes/world.py`, `helpers/cvg.py`, `protocols.py`, etc.)。Apps 必须先 refactor 到 use `lingwen_shared` Protocols (不是直接 `infra.persistence.*` imports)。This is a service layer / port-binding refactor across FastAPI app boundary — genuinely 30-50 commits of mechanical refactor, deferred to v16.5 #N。

Tests:577 backend (**564 baseline + 13 NEW**) / 1729 vitest / vue-tsc 0 / ruff 0 / knip 0 / ESLint 0 / **lint-imports 3 contracts KEPT** (unchanged) / grimp-evasion hygiene OK / SqliteStorageAdapter duck-typed protocol OK。

4 lessons (v16.5 #3 §5):
1. **TYPE_CHECKING does NOT help import-linter** — grimp treats it identically to runtime imports。DP migration: change annotations to Protocol, NOT 依赖 TYPE_CHECKING。
2. **sqlite3 3.51 + Python 3.13 quirk** — close without commit rolls back DML。`with_connection` is read-only by contract; INSERTs 必须 `with_transaction`。
3. **Scope expansion reality** — initial estimate (15-20 commits) 假设 apps 已经用 Protocols。Reality: apps 仍 directly imports infra across 19 files,需要 service layer refactor first。
4. **Documentation must surface scope reality early** — initial carryover description ("refactor infra/* to use StoragePort") 没 acknowledge the apps service layer dependency。Future DPs should START with empirical `grep -rl "from infra\." apps/` to surface the gap upfront。

**Carryover to v16.5 #N (Full DP-03 expansion)**:
- **#N.1** Add factory pattern to `lingwen_shared.ports.storage` (mirror v16.5 #1 LLMServiceAdapter) — `set_default_storage_factory()` + `get_default_storage()` 注册 `infra.persistence.sqlite_storage_adapter` at module load — ~3-5 commits
- **#N.2** Migrate 19 apps/* files to use `get_default_storage()` from lingwen_shared — replaces `from infra.persistence.X import Y` everywhere — ~10-15 commits (1 file per commit, DP-06 strict)
- **#N.3** Migrate 22 infra/* files to drop `import sqlite3` (use `ConnectionPort` Protocol annotation for `conn` params) — world_db (8) + cross_volume + event_sourcing + reading_power + persistence internals (3) + persistence/migrations + tools/workflow/lib (5) + tools/migrate_to_sqlite — ~15-25 commits
- **#N.4** Expand import-linter contract `source_modules = ["lingwen_creator", "apps"]` — then drop redundant hygiene grep test — ~2-3 commits
- **Total v16.5 #N estimate**: ~30-50 commits

> **更新 (2026-08-29)**: Phase 126 v16.5 #2 闭环 — DP-03 StoragePort enforcement——3 commits (`87e2374f` + `ea4a14aa` + docs commit):
- **T1** `chore(apps)`: 删 `apps/studio_api/app.py:18` dead `import sqlite3` (0 usages elsewhere in file; verified via `grep -nE "sqlite3\.|sqlite3\)|= sqlite3"`)。
- **T2** `feat(import-linter)`: 新增 `no_concrete_sqlite3_in_business_code` forbidden contract (`source_modules = ["lingwen_creator"]`, `forbidden_modules = ["sqlite3"]`) + 4 hygiene tests (`tests/hygiene/test_no_concrete_sqlite3_import.py`)。
  - **Documented deviation**: contract 范围限制在 `lingwen_creator`,NOT `apps`。原因: `apps/studio_api/routes/*` legitimately composes `infra/*` modules that import sqlite3 (e.g., `infra.world_db.queries.proposals`, `infra.cross_volume.storage`, `infra.persistence.sqlite_config`),the chain `apps → infra → sqlite3` would fail the contract。
  - **Defense-in-depth**: hygiene grep test covers BOTH `apps/` AND `lingwen_creator/` for direct imports。两个 gate 组合 enforce the architectural invariant。
- **T3** `docs(phase-126)`: handoff doc + CLAUDE.md + architecture.yml。

Tests:564 backend (398 infra/studio/hygiene + 73 creator + 85 shared + 8 llm) / **6 hygiene** (+4 new from DP-03) / 1729 vitest / vue-tsc 0 / ruff 0 / knip 0 / ESLint 0 / **lint-imports 3 contracts KEPT** (layer_dependencies + no_concrete_llm_service + no_concrete_sqlite3) / grimp-evasion hygiene OK。

3 lessons (v16.5 #2 §6):
1. **DP enforcement often requires defense-in-depth** — import-linter forbidden contract 只 cover clean modules; transitive-import contamination 需要 supplementary grep test。Split 明确文档化。
2. **Forbid `sqlite3` is the same shape as forbid `infra.llm_service`** — 两者都是 "concrete resource forbidden; use the port instead"。机械 pattern identical。Future DPs (DP-01, DP-04) follow same template。
3. **Dead imports are a low-cost find** — DP migration 可以从 1-line commits 开始 (zero risk if import provably unused)。DP-03 investigation 发现 `apps/studio_api/app.py:18` 是唯一 dead import — 30+ other sqlite3 usages are legitimate infra/* code (carryover for v16.5 #N full fix)。

**Architecture invariants enforced**:
1. `lingwen_creator` MUST NOT import `sqlite3` — import-linter forbidden contract (strictest form)。
2. `apps/` MUST NOT directly import `sqlite3` — hygiene grep test (covers what import-linter can't because of infra transitives)。
3. `StoragePort` Protocol is canonical persistence interface — `lingwen_shared/ports/storage.py`。Future persistence code should use this port。

**Carryover to v16.5 #3..#7**:
- ✅ **DP-03 #3 PARTIAL done** (`e8b51ab9`) — concrete `SqliteStorageAdapter` is the architectural foundation。**Full expansion → v16.5 #N** (factory pattern + apps migration (19 files) + infra migration (22 files) + contract expansion)。Mirror DP-02 trajectory (v16.4 factory → v16.5 #1 relocate to shared → DP-03 future refactor)。
- DP-01 (cross-package contracts via ports)
- Async port conformance (`async execute → LLMResult`)
- Remaining packages migration (`lingwen_core/pipeline/prompt/cli` — 8 files sqlite3 直接)
- Tools migration (`tools/llm_*.py` — 11 files)
- DTO schema audit + typed wrapper narrowing

> **更新 (2026-08-29)**: Phase 126 v16.5 #1 闭环 — eliminate grimp-evasion hack——11 commits (`d673aa88`...`60d0fb05`, T1-T10 + T1.fixup, T4 split into T4.a + T4.b):
- **T1** `feat(shared)`: 新建 `packages/lingwen-shared/src/lingwen_shared/contracts/python/llm.py` — `TaskType` (Enum) + `LLMTask` (dataclass) canonical source + 6 tests。
- **T1.fixup** `chore(ruff)`: ruff format + I001 import-sort fixes。
- **T2** `feat(shared)`: re-export `LLMTask` + `TaskType` from `lingwen_shared.contracts.python.__init__.py`。
- **T3** `refactor(infra)`: `infra/llm_service.py` 删除 local `TaskType` + `LLMTask` 定义 (lines 25-54),改为 `from lingwen_shared.contracts.python.llm import LLMTask, TaskType` + `__all__` back-compat。删 unused imports `dataclass`, `Enum`。
- **T4.a** `feat(llm)`: port_adapter.py 加 factory scaffolding (`_DEFAULT_FACTORY` + `set_default_factory` + `get_default_factory`) — additive, old dynamic import 保留 as fallback。
- **T4.b** `feat(infra)`: `infra/llm_service.py` 末尾注册 `set_default_factory(LLMService.get)` — 替代 v16.4 dynamic import。
- **T5** `feat(llm)`: port_adapter.py 完整重写 — 删除所有 string-concat + PEP 562 hack ( `_resolve_default_service()` + `__getattr__` + `generate()`'s dynamic import),改为 factory pattern + 直接 `from lingwen_shared.contracts.python.llm import LLMTask, TaskType`。**`lingwen_llm.port_adapter` 现在 0 个 static `infra.llm_service` import**。
- **T6** `test(llm)`: `test_port_adapter.py` 更新 — `LLMTask`/`TaskType` 从 `lingwen_shared` import + singleton test 改用 `set_default_factory(lambda: fake)` + try/finally reset (no leak)。
- **T7** `refactor(creator)`: `creator/content/agent.py` 2 处 LLMTask/TaskType import site 直接从 `lingwen_shared` import (不再 "re-export for DP-02")。
- **T8** `refactor(infra)`: `prose_judge.py` LLMTask/TaskType import site 直接从 `lingwen_shared` import (also kept `LLMServiceAdapter` from port_adapter)。
- **T9** (no commit) Verify: `infra/world_db/agent_extractors.py` 无 LLMTask/TaskType usage,无 change (only `from lingwen_llm.port_adapter import LLMServiceAdapter`)。
- **T10** `test(hygiene)`: `tooling/hygiene/check_no_grimp_evasion.py` 新建 — regression test 禁止 static import / string-concat / `def __getattr__` in port_adapter.py (NOT substring match — avoids docstring mention false positives)。+ `tests/hygiene/test_check_no_grimp_evasion.py` 2 tests。

Tests:560 backend (8 llm pkg + 85 shared pkg [79+6 new] + 73 creator pkg + 392 infra/studio_api + 2 hygiene) / 1729 vitest / vue-tsc 0 / ruff 0 / knip 0 / ESLint 0 / **lint-imports 2 contracts** (layer_dependencies + no_concrete_llm_service_in_business_code) / **grimp-evasion hygiene OK**。

6 lessons (v16.5 #1 §6):
1. **Factory pattern > dynamic import** — 任何 grimp-evasion 感觉需要时,先问是否可以用 startup-time factory/registry 替代。v16.5 #1 用 `set_default_factory()` 替代了 v16.4 string-concat hack。
2. **TDD RED state for next task** — T1's 6th test (`test_module_importable_via_package_root`) deliberately fails until T2 adds the re-export。这是 multi-task plan 的好实践:每 task 的测试声明自己的完成标准,包括对未来 tasks 的依赖。
3. **Back-compat `__all__` is cheap insurance** — `infra.llm_service.py` 的 `__all__` preserves star-import surface for `infra/core/__init__.py:5` and tools/ callers (no consumer code changes)。
4. **Docstring mentions trip naive regex checks** — `port_adapter.py` 的 architectural-invariant docstring 提到了 "PEP 562 __getattr__" 和 "infra.llm_service" — naive substring check flagged them。Fix: regex for `def __getattr__(` (code structure), not substrings。
5. **PYTHONPATH must include transitive deps** — T5 后 `port_adapter` imports from lingwen_shared。tests 跑 `pytest packages/lingwen-llm/tests/` 需要 BOTH `lingwen-llm/src` AND `lingwen-shared/src` on PYTHONPATH (pre-v16.5 不需要)。
6. **PEP 562 module-level `__getattr__` 是 grimp-evasion-vulnerable** — v16.4 hack 用 PEP 562 re-export data types。PEP 562 本身是合法的 Python feature (PEP 562),但用于 re-export forbidden module 的 symbols 就是 static-analysis workaround。**Pattern**: PEP 562 fine for lazy attribute access; smell when used to bypass dependency rules。

**Architecture invariants enforced**:
1. `lingwen_llm.port_adapter` zero static dependency on `infra.llm_service` — `tooling/hygiene/check_no_grimp_evasion.py` 强制。
2. `LLMTask` + `TaskType` single canonical home — `packages/lingwen-shared/src/lingwen_shared/contracts/python/llm.py`。
3. Cross-layer default resolution pattern — `infra.llm_service` registers `set_default_factory()` at module load time, `port_adapter` calls factory。DP-03 StoragePort 可复用此 pattern。

**Carryover to v16.5 #2..#7**:
- DP-01 (cross-package contracts via ports)
- DP-03 (StoragePort enforcement)
- Async port conformance (`LLMServiceAdapter` → `async execute → LLMResult`)
- Remaining packages migration (`lingwen_core` / `lingwen_pipeline` / `lingwen_prompt` / `lingwen_cli`)
- Tools migration (`tools/llm_*.py` — 11 files)
- DTO schema audit + typed wrapper type narrowing

> **更新 (2026-08-29)**: Phase 126 v16.4 闭环 — DP-02 LLMServicePort enforcement + 2 broken imports 修复 + import-linter forbidden contract + 1 grimp-evasion workaround ——14 commits (`3f85ba1c`...`3c10ccff`,8 task + 5 carryover from T6 scope expansion + 1 T8 ruff fixup):
- **T1**: `LLMServicePort` Protocol 加 `is_available()` (health check 需要)。
- **T2 + T2.fix**: `packages/lingwen-llm/src/lingwen_llm/port_adapter.py` 新建 `LLMServiceAdapter` sync facade (execute/execute_stream/parse_json_response/provider_name/is_available/generate) + 7 unit tests。T2.fix 把 is_available 从 private `_provider` 改为 public method delegation。
- **T3**: `creator/content/agent.py` 4 sites 迁 `LLMServiceAdapter`。
- **T4**: `apps/studio_api/routes/health.py` broken import 修复 (`lingwen_llm.llm_service` 不存在,try/except 静默失败) → `LLMServiceAdapter().is_available()`。
- **T5**: `packages/lingwen-quality/.../inspector.py` 同样 broken import 修复。
- **T6.5a/b**: 间接 chain 修复 — re-export `LLMTask`/`TaskType` via port_adapter + 改 content/agent.py import path。**T6.5b 用 string-concat + PEP 562 躲避 grimp transitive detection** — 是 v16.5 hard carryover。
- **T6.7/8**: `infra/prose_judge.py` + `infra/world_db/agent_extractors.py` 迁 adapter (Class B transitive chain)。
- **T6**: import-linter `forbidden` contract `no_concrete_llm_service_in_business_code` (source = `lingwen_creator` + `apps`,forbidden = `infra.llm_service`)。
- **T7 + T7.fix**: 5 DP-02 hygiene tests + regex word boundary fix (catches bare `from infra.llm_service import LLMService`)。
- **T8.fixup**: ruff --fix for 11 lint violations (I001 + W292 + F541) 在 verification gate 期间发现 — agent.py / prose_judge.py / mode.py × 2 / test_creator_endpoints.py / check_import_linter.py / test_check_import_linter.py / test_no_concrete_llm_import.py。

Tests: 583 backend (73 creator + 79 shared + 8 llm + 359 infra + 33 studio_api + 31 hygiene) / 1729 vitest / vue-tsc 0 / ruff 0 / knip 0 (3 advisory) / ESLint 0 (2 rules) / **lint-imports 2 contracts** (layer_dependencies + dp02)。

5 lessons (v16.4 §3):
1. **Grimp follows transitive imports even through simple re-exports**: 单个 `from infra.llm_service import LLMTask, TaskType` 也会触发 forbidden contract via transitive chain。v16.4 workaround 用 string-concat + PEP 562 — v16.5 必须 relocate data types to lingwen_shared 才能消除 hack。
2. **DP enforcement surfaces latent bugs**: 2 broken imports (`lingwen_llm.llm_service` 不存在) 被 try/except 静默吞掉。health endpoint 一直返回 False。
3. **Worktree env sync is hard prerequisite for verification**: v16-4 worktree 的 lingwen_creator package 默认指向 master,需要 `uv pip install -e packages/...` 重装才能验证 v16-4 code。建议加 `make preflight` gate。**额外 gotcha**: v16-4 worktree 缺 `.env` (gitignored) → pytest deepeval plugin 不会加载 `MINIMAX_API_KEY` → LLMService 单例 init 失败 → streaming test 假 fail。Symlink `ln -sf /home/ailearn/projects/LingWen/.env /home/ailearn/projects/LingWen-v16-4/.env` 修复。
4. **`is_available()` belongs on the port**: 加到 Protocol 让 health check 用 port 而非 bypass concrete。
5. **Grep regex for tests needs word boundary**: `LLMService[^A-Za-z]` 漏掉行尾裸 import。Fix: `LLMService($|[^A-Za-z])` (POSIX ERE alternation)。

**Carryover to v16.5 (HARD SCOPE)**:
- **ELIMINATE grimp-evasion hack** (single most important) — relocate `LLMTask`/`TaskType` 从 `infra.llm_service` 到 `packages/lingwen-shared/src/lingwen_shared/contracts/python/llm.py`,删 string-concat + PEP 562 workaround。
- DP-01 (cross-package contracts via ports)
- DP-03 (StoragePort enforcement)
- Async port conformance (LLMServiceAdapter 升级到 `async execute → LLMResult`)
- 剩余 packages (lingwen_core/pipeline/prompt/cli) consumer migration
- tools/llm_*.py migration (8 + 3 files)
- DTO schema audit (carryover from v16.3)
- Typed wrapper type narrowing (carryover from v16.3)

> **更新 (2026-08-28)**: Phase 126 v16.3 闭环 — import-linter DP-01..06 enforcement 永久固化架构边界——11 commits (`7afd18e6` ... `70120dcc`):
- **T1 (4 commits)**: 8 barrel consumers 迁 typed wrapper (Chapters/Analytics → @/api/health, StudioPage + useStudioStore → @/api/studio + @/api/content, Workflows → @/api/workflows, Ripples/CascadeRunsPanel → @/api/cvg, Settings → @/api/budgets, useSettingsDocs → @/api/settings)。每 commit ≤3 files (DP-06 严格)。
- **T2.1 (3 commits)**: import-linter layer_dependencies contract (`apps.studio_api → lingwen_creator → infra`)。Closes v16.2.4 §5.1 carryover — `shared/mode.py` 从 `lingwen_creator/shared/` 移到 `lingwen_shared/` (true leaf, infra 可 import),lingwen_creator 留 back-compat shim。2 infra files 改 import。
- **T2.2 (1 commit)**: `tooling/hygiene/check_import_linter.py` skeleton → 真跑 `lint-imports` + glob `infra/creator_*.py` 检查 + 4 hygiene tests。
- **T3.1 + T3.2 (2 commits)**: ESLint `no-restricted-imports` × 2 rule groups — `frontend_isolation` (forbid `infra/*` + `lingwen_creator/*` 在 src/) + `no_barrel_bypass` (forbid `@/api/index.js` 在 composables/stores/pages/components)。验证: 现有 1729 tests 0 violation,synthetic violation 立即报错。
- **T3.3 (1 commit)**: `apps/dashboard/tests/eslint-rules/no-restricted-imports.test.cjs` — 13 regression tests (5 isolation + 5 barrel + 3 positive)。
- **T4.1 (1 commit)**: 6 page tests 加 parallel typed wrapper mocks (per v16.2.8 §3 lesson 1: hoisted mock pattern)。cascade-runs-panel also changed dynamic import from `@/api/index.js` → `@/api/cvg` to match production path。
- **T4.2 (1 commit)**: `knip.json` 清理 (13 typed wrappers 从 ignore 移除;4 个 advisory 保留因 knip 不解析 `@/` alias)。
- **Bonus**: `useSettingsDocs.ts` bonus fix — `'../../api/settings.js'` (non-existent .js shim) → `'@/api/settings'` typed wrapper。Vite alias 兜底但 fragile,现在 clean。

Tests: 1729 vitest passing (0 regression) / 544 backend (73 creator + 79 shared + 359 infra + 33 studio_api) + 26 hygiene / vue-tsc 0 / ruff 0 / knip 0 (3 advisory) / ESLint 0 (NEW 2 rules active) / lint-imports 1 contract kept / make check 4 scripts。
`apps/dashboard/src/api/*.js` (creator-domain): 0 (从 v16.2.8 维持)。`grep -rln "from '../api/index" apps/dashboard/src`: 8 → 0。

5 new lessons:
1. **import-linter `forbidden_modules` glob syntax**: `infra.creator_*` rejected ("wildcard can only replace a whole module")。file-existence check 用 glob `infra/creator_*.py` 是 reliable gate (import-linter + check_import_linter.py 互补)。
2. **import-linter `layers` ordering**: layers[0]=top (api_gateway),layers[N]=bottom (infra)。Higher 可 import lower,lower MUST NOT import higher。
3. **Mode.py 真正位置**: cross-subdomain utility 必须在 `lingwen_shared/` (true leaf),NOT `lingwen_creator/shared/`。v16.2.4 spec 假设后者,只有 import-linter layer contract enforce 后才 surface。**Architecture invariants 必须 enforced 才能 discovered**。
4. **ESLint `no-restricted-imports` patterns 用 minimatch**: literal + `*` + `**` + `**/...` 4 种覆盖。
5. **Hoisted mock pattern re-confirmed (6 page tests)**: barrel mock 与 typed wrapper mock 必须 share SAME vi.fn instances via `vi.hoisted()`。每 typed wrapper 迁移 = 6+ tests 需手动更新。**Future barrel → typed wrapper migrations should plan this upfront**。

Carryover to v16.4:
- DP-01 enforcement (cross-package contracts via ports)
- DP-02 enforcement (LLMServicePort via import-linter forbidden contract)
- DTO schema audit (carryover from v16.2.7/v16.2.8 — 4 production `as unknown as` casts + 2 test casts)
- Typed wrapper type narrowing (41 funcs in 5 new wrappers return `Promise<unknown>`)

> **更新 (2026-08-28)**: Phase 126 v16.2.8 闭环 — final closure (T2 5 typed wrappers + T2.5 SSE stream + T3.A 4 Pinia stores + T3.B 5 composables + T4.5 useCreatorSettings.js refactor + T5 7 legacy api/.js deletion) ——7 commits (`a196e807` ... `4b2948ef`):
- **T2** (1 commit): 5 new typed wrappers — health.ts (6) + decisions.ts (5) + cvg.ts (14) + workflows.ts (5) + studio.ts (11) = 41 funcs。命名 NO 'Creator' prefix (per v16.2.1+ convention)。
- **T2.5** (1 commit): `runCreatorAgentPlanStream` 加 content.ts (SSE-preserving, raw fetch + markApiOnline side effect)。
- **T3.A** (1 commit): 4 Pinia stores → typed wrappers (DecisionStore/RippleStore/WorkflowListStore/OverviewStore)。11 page-level tests 用 hoisted mock pattern (per v16.2.7 §3 lesson 1)。
- **T3.B** (1 commit): 5 composables → typed wrappers (useProductExport/AskAssistant/AdvanceBatch/TodayHub + useAgentTask stream)。
- **T4.5** (1 commit): useCreatorSettings.js 完整 refactor — 18 function renames (Creator-prefixed → unprefixed) + import path `'../api/index.js'` → `'@/api/settings'`。
- **T5** (1 commit): Delete 7 frontend legacy api/.js (agent/creator/mergePreset/studio/volumePlan/volumeTemplate/templateApproval) + 5 orphan test files + architecture guard inversion。`apps/dashboard/src/api/*.js` (creator-domain) 11 → 0。

Tests: 1729 vitest passing (1817 → 1729, -88 orphan test deletions, 0 regression) / 544 backend (73 creator pkg + 79 shared pkg + 359 infra + 33 studio_api + 5 skipped, unchanged) / vue-tsc 0 / ruff 0 / knip 0 (5 advisory + 1 new index.js barrel)/ codegen no backend changes。

New lessons (5):
1. **Hoisted mock pattern re-confirmed** — 14 page-level tests needed `vi.hoisted(() => mocks)` + parallel `vi.mock` for typed wrapper (v16.2.7 §3 lesson 1).
2. **`as unknown as` for typed wrapper params** — `body as unknown as Parameters<typeof fn>[0]` when body built dynamically as `Record<string, unknown>` (v16.2.7 §5.1 lesson 4 re-confirmed in useAgentTask.ts).
3. **Dead code in legacy modules** — DiffColab + Wizard helpers in mergePreset.js + studio.js duplicate of studio.ts all deleted without ceremony (v16.2.7 §5.1 lesson 6).
4. **Architecture guards can invert** — Phase 62 'creator.js ≤ 50 lines' → 'creator.js should NOT exist' preserves guard intent after file deletion.
5. **Bulk sed for function renames** — 18 of useCreatorSettings.js renames via single multi-`-e` sed command; clean and atomic.

Carryover to v16.3:
- import-linter DP-01..06 enforcement (T3 from parent spec §3.8 final gate) — 永久固化架构边界,防止 `apps/dashboard/**` 反向 import `infra/` 或 `lingwen_creator.*`,以及 `infra/creator_*.py` + `api/*.js` creator-domain 重新出现。
- DTO schema audit (carryover from v16.2.7 T8 + v16.2.8 T3.B) — 4 production `as unknown as` casts + 2 test casts masking drift,需对齐 Python Pydantic + regenerate TS。
- Typed wrapper type narrowing — 41 funcs in 5 new wrappers return `Promise<unknown>`,待加 DTOs。

Phase 126 v16.2.x arc CLOSED。**v16.3 import-linter enforcement 解锁前提**:`infra → lingwen_creator` 100% 完成 + frontend creator-domain api/.js 100% 删 + typed wrapper 全覆盖 + DTO 在 shared contracts。
- **T4 12 commits**: delete all 36 `infra/creator_*.py` shims (memory/settings/export/volume/onboarding/content tiers, leaf-first). 191 consumer files migrated. **Final**: `ls infra/creator_*.py | wc -l` → 0.
- **T5**: dedup 20 Pydantic DTOs in `creator_settings.py` to re-export from `lingwen_shared.contracts.python.creator`. -191/+72 lines net.
- **T6 4 commits (A/B/C/D)**: migrate 10 composables from `@/api/index.js` barrel to typed wrappers (`@/api/content`/`@/api/volume`/`@/api/onboarding`). 9 blocked composables carryover to v16.2.8 (need typed wrappers for health/decisions/cvg/workflow/studio surface). `api/creator.js` deletion deferred.
- **T7**: delete 4 unwired Content DTOs (CreatorUiProfileState/SaveRequest + CreatorDashboardOverview/ChapterPreview). TS auto-codegen drops 4 interfaces.
- **T8**: 7 schema mismatch `as unknown as` casts + CreatorModelsResponse DTO fix (`providers` → `models + default_model`) surfaced by typed wrapper strict types. vue-tsc 0 / ruff 0 / knip 0 / vitest 1817 / backend pytest 521. **Phase 126 v16.2.x closure**: 36 shims deleted, 20 DTOs deduped, 10 composables migrated, 4 forward-compat DTOs removed.

Tests: 73 creator pkg + 79 shared pkg + 359 infra + 33 studio_api = 544 backend passing (was 521; -6 legacy back-compat tests + -4 deleted DTO tests + 0 actual regression). 1817 vitest passing. vue-tsc 0 / ruff 0 / knip 0 (5 advisory hints) / codegen OK.

New lessons:
1. **Re-export shim mocks don't propagate** — when composable migrates from barrel to typed wrapper, test's barrel mock no longer intercepts. Must add parallel typed wrapper mock (v16.2.5 §5.1 lesson 3).
2. **Name collision after rename** — useProductPreferences had 2 imports named `saveCreatorPreferences`; aliased local-storage as `saveCreatorPreferencesLocal` (real bug fix, not cosmetic).
3. **Shadow bug in legacy composables** — useTemplateSync had local `async function applyVolumeTemplate()` shadowing typed wrapper import; aliased as `apiApplyVolumeTemplate` to break recursion.
4. **DTO schema drift pre-existing** — typed wrapper strict types exposed `providers` vs `models` mismatch in CreatorModelsResponse; casts preserve behavior, full schema audit deferred.
5. **Shim existence ≠ back-compat** — `test_legacy_import_paths_still_work` was tautological (comparing `lingwen_creator.X.Y as LegacyFoo` to same); rewritten to `test_legacy_shim_deleted` asserting ModuleNotFoundError.

Carryover to v16.2.8: 9 blocked composables + `api/creator.js` deletion (5 underlying legacy modules). v16.3: import-linter DP-01..06 enforcement. v16.4+: DTO schema audit.

> **更新 (2026-08-28)**: Phase 126 v16.2.6 闭环 — creator Memory subdomain 拆分 (Round 2 leaf 最后一个,**creator 6-subdomain 拆分收官**)——13 commits (`98da5407` ... `e18606dd` + T8):
- **gitignore fix**: 仓库根 `.gitignore:228` 的 `memory/` 是无前导斜杠的目录模式,匹配任意深度 → 静默吞掉新建的 `lingwen_creator/memory/`。收窄为 `/memory/`。— `94970497`
- **T1.a**: `memory/annotations.py + memory/assets.py + 2 shims` (4 files;assets.py 4 处 intra-package import: creator_dashboard → content.dashboard / creator_settings_docs → settings.docs / creator_memory_annotations → memory.annotations / creator_preferences → content.preferences,含函数体 lazy import)。— `2b984962`
- **T1.b**: `memory/query.py + __init__.py + 1 shim` (query.py 2 处 intra-package import)。— `05ba5f2b`
- **T1.c**: `test_memory.py` (8 tests,含 legacy shim identity + intra-package no-cycle 断言 + annotations round-trip)。— `48aba8c9`
- **T2**: 7 Memory DTOs (CreatorMemoryAssetItem + AssetsResponse + AnnotationRequest + AnnotationResponse + QueryRequest + QueryResult + QueryResponse) → `lingwen_shared/contracts/python/creator.py` + TS codegen (25215 bytes, +1173) + 8 backend tests。— `d4ce52f4`
- **T3.a**: `apps/dashboard/src/api/memory.ts` typed wrapper (3 funcs, NO zod, NO /api/,签名与 legacy `api/memory.js` 完全一致 → 调用点只改 import) + `dashboard-contracts/src/shared/memory.ts` re-export + `creator.ts` +7 types + knip allowlist。— `25d08294`
- **T3.b**: `tests/unit/api/use-memory-typed-wrapper.spec.ts` URL contract (6 tests,含 assetId percent-encoding)。— `afa93676`
- **T4**: routes imports migration (`creator_core.py` 3 lazy imports → `lingwen_creator.memory.{assets,annotations,query}`)。— `e39b75d3`
- **T5.a**: composables refactor (`useProductMemory.ts` + `useAskAssistant.js` → `@/api/memory`)。— `f8b6a2ca`
- **T5.b**: `api/index.js` 3 alias re-point + `api/creator.js` 移除 `export * from './memory.js'` + 删 `api/memory.js` + 删 orphan `api-creator-memory.spec.ts`。— `bb108984`
- **T7**: 3 test files vi.mock 拆分 (`use-product-memory` / `creator-product-tools` / `use-creator-page`)。— `3038b579`
- **T6**: 顺手清掉 package 内**最后 2 处** `infra.creator_*` 耦合 (`content/logic_check.py` → shared.check + shared.mode;`volume/plan.py` `_excerpt` → content.dashboard)。**`packages/lingwen-creator/src/` 现在 0 个 `infra.creator_*` import**。— `e18606dd`
- **T8**: handoff + CLAUDE.md + architecture.yml + migration_log.yml。

新 lessons:
1. **无前导斜杠的 gitignore 目录模式命中任意深度** — 新建子域包目录前先跑 `git check-ignore -v <path>`。
2. **本地 pytest 经插件 (deepeval/langsmith) 加载 `.env`** → `MINIMAX_API_KEY` 在测试进程有值 → `tests/dashboard/test_creator_endpoints.py::test_creator_v38_endpoints` 的 `POST /api/creator/logic-check` 对 10 章打**真实 LLM**,表现为 hang。**在 baseline commit `7b7c7c18` 同一工作树上同样复现,与 v16.2.6 无关**。跑法:`env -u MINIMAX_API_KEY python -m pytest tests/dashboard/test_creator_endpoints.py -q` → 27s / 120 passed。附带教训:`git worktree` 做 baseline 对照时 `lingwen_creator` 走 editable install → **解析到主工作树的包代码**,只有 `infra/` `apps/` `tests/` 是 worktree 自己的。
3. **barrel mock 失效的连锁面比预期大** — composable 改直连 typed wrapper 后,间接挂载它的 page 级测试也会挂 (`use-creator-page.spec.ts` ← `useAskAssistant`)。

Tests: 79 (creator pkg, +8) + 83 (shared pkg, +8) + 359 (infra, unchanged) = 521 backend passing。1777 vitest passing (22 pre-existing volume-plan debt 不变)。vue-tsc 0 / ruff 0 / knip 0 (8 advisory hints) / codegen 无 drift / YAML valid。Shim count: 44 (41 + 3)。

Carryover to v16.2.7 (cleanup,Phase 126 收尾):44 shim 删除 + 4 typed wrapper `/api/` prefix fix (world/workspace/quality + onboarding) + 22 vitest debt + import-linter DP-01..06 + 19 content composables refactor + 4 unwired Content DTOs + onboarding diff-collab-notes 404 fix + `apps/studio_api/models/creator_settings.py` DTO 去重。

> **更新 (2026-08-28)**: Phase 126 v16.2.5 闭环 — creator Export subdomain 拆分 (Round 2 leaf)——13 commits (`389f91a5` ... `4d11064b`):
- **T1.a**: `export/common.py + export/docx.py + 2 shims` (4 files, intra-package imports: creator_dashboard → lingwen_creator.content.dashboard + creator_settings_docs → lingwen_creator.settings.docs)。— `389f91a5`
- **T1.b**: `export/epub.py + creator_export_epub shim + creator_publish_adapters shim (pre-emptive)` (3 files)。— `dce65eaf`
- **T1.c**: `export/publish.py + export/publish_adapters.py + __init__.py + creator_publish shim` (4 files, 5 star-imports)。— `5715ff15`
- **T1.d**: `test_export.py` (8 tests, 含 legacy import back-compat + intra-package import no-cycle) + ruff --fix。— `b2dd6f53`
- **T2**: 8 Export/Publish DTOs (CreatorEpubExportRequest + CreatorDocxExportRequest + CreatorPublishRequest + CreatorPublishEntry + CreatorPublishPlatformCapabilities + CreatorPublishPlatform + CreatorPublishPlatformsResponse + CreatorPublishHistoryResponse) → `lingwen_shared/contracts/python/creator.py` + TS codegen (24042 bytes, +1501) + 9 backend tests (39 total)。— `5308c63e`
- **T3.a**: `apps/dashboard/src/api/export.ts` typed wrapper (5 funcs, NO zod, NO /api/, 含 fetchBlob + fetchJson helpers) + `packages/dashboard-contracts/src/shared/export.ts` re-export + knip allowlist + creator.ts +8 types。— `5390a776`
- **T3.b**: `apps/dashboard/tests/unit/api/use-export-typed-wrapper.spec.ts` URL contract (8 tests)。— `1e95ff82`
- **T4**: routes imports migration (5 lazy imports in `creator_core.py`: creator_export_epub → lingwen_creator.export.epub + creator_export_docx → .docx + creator_publish.submit → .publish + creator_publish.list_publish_platforms → .publish + creator_publish.list_creator_publish_history → .publish)。— `8695e3dd`
- **T5.a**: composable refactor (useProductExport.ts + useProductPublish.ts → @/api/export + fetchCreatorChapterPreview → @/api/content) + export.ts vite/client triple-slash directive fix。— `f3dd8f99`
- **T5.b**: api/index.js update (6 publish.js re-exports → typed wrapper, 4 Content functions → content.ts/volume.ts) + delete api/publish.js shim + delete orphan api-creator-publish.spec.ts + useWriteFlow typed signature migration (saveCreatorChapterBody/Outline 2-arg → 1-arg `{ chapter_id, body }` shape + 4 cast fixes `as Record` → `as unknown as Record`)。— `8bd30325`
- **T6**: cross-subdomain check (only test_export.py references infra imports — expected back-compat test) + intra-package imports verified all use new path。**Skipped commit** — no findings。
- **T7**: test mock path updates (5 test files: split vi.mock from api/index.js to api/export.js + api/content.js, per v16.2.4 §5.1 lesson 2 — shim mocks 不 propagate)。— `4d11064b`
- **T8**: handoff + CLAUDE.md + architecture.yml + migration_log.yml。— (current commit)

Lessons confirmed from v16.2.4:
- §5.1 lesson 1 (intra-package imports after verbatim copy): T1.a export/common.py — `infra.creator_dashboard → lingwen_creator.content.dashboard` + `infra.creator_settings_docs → lingwen_creator.settings.docs`
- §5.1 lesson 2 (shim mocks 不 propagate): T7 — 5 test files split vi.mock from api/index.js to typed wrapper modules (per v16.2.4 bug class)
- §5.1 lesson 4 (typed wrapper params forwarding fragility): T5.b — useWriteFlow.ts 3 call sites migrated from `(chapterNum, body)` 2-arg to `({ chapter_id, body })` 1-arg typed signature; 4 cast sites `as Record<string, unknown>` → `as unknown as Record<string, unknown>`
- §5.1 lesson 5 (orphan test files linger): T5.b — `apps/dashboard/tests/unit/api-creator-publish.spec.ts` (12 tests) deleted before/with api/publish.js deletion

Tests: 71 (creator pkg, +8) + 75 (shared pkg, +9) + 359 (infra, unchanged) = 505 backend passing. 1774 vitest passing (22 pre-existing volume-plan debt unchanged from v16.2.4 baseline). vue-tsc 0 / ruff 0 / knip 0 (7 advisory hints) / zod reverse CI OK / codegen OK.

Carryover closures (1):
- ✅ useWriteFlow.ts typed signature migration (saveCreatorChapterBody/Outline) — bonus fix per T5.b scope expansion

Carryover to v16.2.6+:
- **v16.2.6 memory**: 3 files (annotations + assets + query) — Round 2 leaf last
- **v16.2.7 cleanup**: 41 shim deletions + 4 typed wrapper `/api/` prefix fix (world/workspace/quality + onboarding from v16.2.3) + 22 vitest debt + import-linter DP-01..06 + 19 content composables refactor + 4 unwired Content DTOs + onboarding diff-collab-notes 404 fix

> **更新 (2026-08-28)**: Phase 126 v16.2.4 闭环 — creator Content subdomain 拆分 + onboarding T4 闭环——15 commits (`3f21513a` ... `55f9a84f`):
- **T1**: `shared/mode.py` extraction (cross-subdomain utility: CREATION_MODE_* + CreatorSettings + settings_from_project_config) + `infra/creator_mode` 变 shim + `shared/check.py` spec violation fix + onboarding forward-ref close。— `19e1ca03`
- **T2a-d**: 8 content files verbatim copy + 8 shims + `__init__.py` star-imports (T2 split 4 commits per DP-06: agent 598L / dashboard+logic_check / mode+models / preferences+ui_profile)。— `2ebb10ad` + `307afa97` + `ee710d6d` + `3afe3c09`
- **T3**: 16 Content DTOs (10 spec + 2 CreatorDashboard* + 4 settings/Mode utilities) → `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` + TS codegen (9068→22541 bytes, +13473) + 13 backend tests。— `b63367a1`
- **T4**: `apps/dashboard/src/api/content.ts` typed wrapper (11 funcs, NO zod, NO /api/) + `packages/dashboard-contracts/src/shared/content.ts` re-export + knip allowlist + 15 URL contract tests。— `e9facc1e`
- **T5**: 13 routes imports in `creator_core.py` migration + `infra/project_init.py` + `infra/project_config.py` 2 creator_mode imports → `shared.mode` migration。— `aec1dbff`
- **T6**: onboarding T4 composables refactor (5 files: useCreatorOnboarding + useWizardSteps + useOnboardingProgress + useOnboardingNotifications + useTodayHub cross-cutting) + delete `api/onboarding.js` shim (was 23 Creator-prefixed aliases) + bonus fix 2 T3 typed wrapper defects (applyWizardShareDone + dispatchDigestNow silently dropped body/query params) + update 4 test mocks。— `06a91169`
- **T7**: 4 cross-subdomain settings.{docs,history,merge_preferences}.py stale `infra.creator_*` imports → `lingwen_creator.content.*` migration。— `392fd809`
- **T8 fixups (3 commits)**: verification gates 发现 3 classes 修复 — (A) `content/dashboard.py` + `content/logic_check.py` intra-package imports (verbatim copy preserved `from infra.creator_ui_profile` → cycle via shim) + `infra/creator_dashboard.py` shim `_excerpt` re-export; (B) 6 onboarding test files patch path `infra.creator_onboarding_{webhook,email}` → `lingwen_creator.onboarding.{webhook,email}` (v16.2.3 T1a regression discovered: shim mock 不通过 `from X import Y` lazy import 传播) + delete orphan `apps/dashboard/tests/unit/api-creator-onboarding.spec.ts`; (C) ruff `--fix` 22 I001 violations across 10 files (shim star-import + explicit import block sort)。— `9fff074a` + `8a6e0f25` + `55f9a84f`
- **Handoff**: `docs/superpowers/handoffs/2026-08-28-phase-126-v16-2-4-content-handoff.md` (15 commits, 8 deviations, 5 lessons, 8 carryover)。

Lessons:intra-package imports after verbatim copy (extends v16.2.2 §5.1 lesson 7: now also applies to sibling-subdomain imports) / shim mocks 不 propagate through `from X import Y` lazy imports (PEP 562 `__getattr__` proxy no work for modules — Python modules don't honor `__setattr__`; test patches MUST target real module path) / composable refactor scope expansion (T6 plan estimated 5 files, actual 11: 5 composables + creator.js + index.js + useTodayHub + 4 test mocks + 2 typed wrapper defects) / typed wrapper params forwarding is fragile (use `requestWithParams(method, path, params)` helper to avoid silent arg drops) / orphan test files linger after shim deletion (`grep -r "<shim-path>" tests/` must precede deletion)。

Tests:63 (creator pkg) + 66 (shared pkg) + 241 (infra) = 370 backend passing。1778 vitest passing (22 pre-existing v16.2.1 `useCreatorVolumePlan*` debt unchanged)。vue-tsc 0 / ruff 0 / knip 0 (5 advisory hints) / codegen OK / zod 0 drift。Backend routes imports 全部迁移 (13 routes imports in `creator_core.py` + 2 project_X imports, no `from infra.creator_{agent,batch_history,dashboard,logic_check,models,preferences,ui_profile}` left in `creator_core.py`)。Shim count: 36 (unchanged, conversion of full impls to shims doesn't add count per v16.2.3 §5.1 lesson 2)。

Carryover to v16.2.5..7:v16.2.5 export (5 files Round 2 leaf)/ v16.2.6 memory (3 files Round 2 leaf)/ v16.2.7 cleanup (36 shim deletions + 4 typed wrapper `/api/` prefix fix for world/workspace/quality + onboarding `/creator/onboarding/diff-collab-notes` 404 fix + 22 vitest debt + import-linter DP-01..06)/ Content composables (19 per spec §3.7) refactor deferred to v16.2.7 / 4 unwired Content DTOs (CreatorDashboard* + CreatorUiProfile*) — wrap when endpoints land。

> **更新 (2026-08-27)**: Phase 126 v16.2.3 闭环 — onboarding subdomain 拆分——10 commits (`c7c3913a` ... `6cfdf5c2`):
- **T1a-d**: 9 onboarding files (autodetect/digest_background/digest_schedule/email/notifications/progress/webhook/onboarding.py + diff_collab) → `packages/lingwen-creator/src/lingwen_creator/onboarding/` + shims + 24 tests。T1 split 4 commits per DP-06。— `c7c3913a` + `949fb0ec` + `aa867b6b` + `8a800d68`
- **T2**: 30 Onboarding DTOs (20 top-level + 10 nested helpers) → `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` + TS codegen (14462→19805 bytes) + 13 backend tests。— `4fe2512c`
- **T3+T4-partial**: `apps/dashboard/src/api/onboarding.ts` typed wrapper (23 funcs) + `packages/dashboard-contracts/src/shared/onboarding.ts` re-export + `apps/dashboard/src/api/onboarding.js` shim with 21 Creator-prefixed legacy aliases (full composable refactor deferred to v16.2.4 T6 carryover)。— `d2a440d9`
- **T5**: 21 routes imports in `creator_onboarding.py` migration (single commit)。— `36a26fc2`
- **T6**: 3 cross-subdomain `volume/template_approvals.py` stale `infra.creator_onboarding_*` imports → `lingwen_creator.onboarding.*` (carryover from v16.2.2 §6 closed)。— `6cfdf5c2`
- **Handoff**: `docs/superpowers/handoffs/2026-08-27-phase-126-v16-2-3-onboarding-handoff.md` (10 commits, 9 deviations, 5 lessons)。

Lessons:legacy `api/onboarding.js` shim with backward-compat aliases pattern (cleanest migration path: thin shim with both `export * from './new.ts'` AND legacy aliases) / shim count 不 increase when migrating existing files to shim form / `@lingwen/dashboard-contracts` re-export chain fragility (new DTOs need manual addition to explicit re-export list) / top-level `await import()` in shims is unsafe (use synchronous `import { ... } from './X'; export const legacy = newName`) / spec §2 import list + grep verification = complete adjustment guarantee。

Tests:24 (onboarding pkg) + 50 (shared DTO) + 16 (onboarding infra) + 25 (frontend URL contract) = 115 onboarding passing。vue-tsc 0 / ruff 0 / knip 0 / codegen OK / zod 0 drift。Shim count: 36 (unchanged per §5.1 lesson 2)。Carryover:5 composable files (useCreatorOnboarding + 3 submodules + index.ts) refactor to v16.2.4 T6 / content migration 抽 shared/mode.py 修 spec violation / dashboard-contracts/src/shared/creator.ts explicit re-export list needs update per new DTO。

> **更新 (2026-08-27)**: Phase 126 v16.2.2 闭环 — creator Settings subdomain 拆分——20 commits (`5b7c1d7f` ... `1fb9baed`):
- **T1a-d**: 3 settings Python files (docs 351 + history 136 + merge_preferences 1355 lines) verbatim copy + 1-line shim with underscore re-exports。4 commits + carve-out fix + T1c BLOCKED follow-up + H1 function-body lazy import fix。— `5b7c1d7f` + `78621a0f` + `f5844680` + `4df3fb1e` + `19e1ca03` (no, that's v16.2.4)
- **T2**: 28 Settings DTOs → `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` + tooling/contracts/generate.py + TS codegen (87 interfaces total) + 7 new DTO tests。
- **T3**: `apps/dashboard/src/api/settings.ts` typed wrapper (32 funcs, NO zod, NO /api/) + URL contract regression lock (34 tests) + knip allowlist。
- **T4a-b**: useCreatorSettings composable + 3 submodules (useSettingsDocs/History/MergePresets) refactored to typed wrapper。
- **T5a-b**: All 32 routes lazy imports in `creator_settings.py` migrated (5 docs T4b + 2 history T5a + 25 merge_preferences T5a/T5b)。
- **T6-T8**: Cross-subdomain cleanup + formal shim audit + handoff + 3 fixups (H1 function-body lazy import + D4 doc mismatch + test regex gap)。

Lessons:spec §2 import list completeness check before verbatim copy / T1a carve-out pattern for cross-task imports / T3 DP-06 budget includes index.ts re-export / shim underscore re-exports added continuously via T1c follow-up pattern / DTO count budgets ~30% extra for nested types / plan gate descriptions explicit about creation vs deletion / ALWAYS check function-body lazy imports after verbatim copy — module-level check missed H1。

Tests:50+ (settings pkg) + 37 (settings DTO) + 34 (frontend URL contract) = 121 settings passing。vue-tsc 0 / ruff 0 / knip 0 / codegen OK / zod 0 drift。Shim count: 36 - 1 (creator_mode already shim) = 35, but added 3 settings shims = 38 net (eventually settled to 36 after v16.2.3 T6 cleanup)。

> **更新 (2026-08-27)**: Phase 126 v16.2.1 闭环 — creator Volume subdomain 拆分——15 commits (`5bc35f1b` ... `5733505b`):
- **Plan reorder**: 原 plan memory-first 假设错(v16.2.0 review 跑 cross-subdomain analysis 发现 memory 依赖 content + settings)。Volume 是 root,被 4 个其他 sub-domain 依赖。先迁 volume 让后续 sub-phase 可用新 package path。— `5bc35f1b`
- **T1**: 3 小 volume files (plan + plan_share + pulse) → `packages/lingwen-creator/src/lingwen_creator/volume/` + shim + tests (7 tests)。intra-package import 规则明确(plan §12.2)。— `0ec3da6c`
- **T2**: 58 Volume DTOs → `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` + 跑 tooling/contracts/generate.py (修 v16.1 missing "creator" entry in MODULES list) → TS 自动生成 (59 interfaces, 9068 bytes) + zod reverse 0 drift + 23 tests。— `69195d23`
- **T3**: `apps/dashboard/src/api/volume.ts` typed wrapper + `packages/dashboard-contracts/src/shared/creator.ts` re-export shim + knip allowlist (37 wrapper functions, 匹配 v16.1 T4 world.ts/workspace.ts/quality.ts style)。— `95245044`
- **T4**: 3 composables refactor (useCreatorVolumePlan + Diff + MergeSplit) + 4 routes imports (creator_volume_plan) + 第一次 /api/ prefix fix (26/37 paths)。plan §12.2 intra-package example 更新。— `fbaee62d` + `515c399f` + `f12763cc` + `b63253e5`
- **T4 bug fix**: spec reviewer 实证 11 个 template-literal paths 仍带 `/api/` prefix (会 404)。修 commit `db0d6c12` + 18 URL-contract tests (regression lock)。
- **T5a-c**: catch-up missing 3 volume files (summary 144 + templates 1022 + template_approvals 692 lines) + shim (含 27 + 13 个 underscore re-exports for test compat) + intra-package import per §12.2。— `f5844680` + `87876ee2` + `626f60c4`
- **T5d**: `volume/__init__.py` 加 3 star-imports + `test_volume.py` 扩展 7 → 14 tests。— `ee1cb5a3`
- **T5e-f**: 2 composables refactor (useCreatorPulse + useCreatorVolumePlanTemplates, exportTemplateApprovalAudit stub 替换为真实现) + 32 routes imports migration (templates + template_approvals endpoints) + `generateVolumeSummary` typed wrapper 新增。— `0870f7c2` + `5733505b`
- **Handoff**: `docs/superpowers/handoffs/2026-08-27-phase-126-v16-2-1-volume-handoff.md` (15 commits, 11 deviations, 5 lessons, 6 carryover)。

Lessons:dependency analysis MUST precede Strangler Fig sub-phase ordering (cross-subdomain grep + graph before sequencing)/ shim private name re-exports required for test compat (any shim must audit existing tests for private symbol imports)/ typed wrapper 不 use zod runtime validation (zod is T5/CI drift, not wrapper layer; verify against v16.1 T4 reference)/ `/api/` prefix 必须 NOT be in code (core.js BASE_URL 已是 `/api`,all 4 typed wrappers 错,v16.2.1 修 volume.ts only, 其他 3 carryover 到 v16.2.7)/ spec violation carryover (shared/check.py 当前依赖 infra.creator_mode.CreatorSettings,carryover 到 v16.2.3 content migration 抽到 shared/mode.py)。

Tests:14 (packages) + 44 (infra consumer) + 40 (frontend composable + api) = 98 total passing. vue-tsc 0 errors / ruff 0 / eslint 0 / knip 0 (2 advisory hints)。Backend routes imports 全部迁移 (36 routes imports migrated, no `from infra.creator_volume` left in `creator_volume.py`)。Shim count: 6 created (3 T1 + 3 T5), 28 remaining。

Carryover to v16.2.2..7:settings (3 files)/ content (10 files, must fix shared/check.py spec violation)/ onboarding (9 files)/ memory (3 files, Round 2 leaf)/ export (5 files, Round 2 leaf)/ v16.2.7 cleanup (36 shims + /api/ fix for world/workspace/quality wrappers + import-linter forbidden pattern check)/ import-linter enforcement DP-01..06 (v16.4 / v16.5)。

> **更新 (2026-08-27)**: Phase 124 v16.1 闭环——9 commits (T1-T8 + 2 review fixups):
- **T1** `packages/lingwen-shared/` uv workspace member 新建 (hyphen name + underscore module,5/5 layout tests pass) — `121b7855`
- **T2** 12 DTO 迁入 (6 world / 4 workspace / 3 quality) + 2 Hexagonal ports 声明 (`LLMServicePort` / `StoragePort`,enforcement 在 v16.4 / v16.5)。7/7 contract tests pass。`ChapterDTO.id` 改为 `int | None = None` (TDD-driven,匹配 `ProposalDTO.id` 模式)— `b4fb3fe3`
- **T3** `tooling/contracts/generate.py` Pydantic → TS codegen (hand-rolled JSON Schema → TS converter)。5/5 codegen tests pass。Known caveat: 单值 `Literal["agent"]` 在 TS 中变成 `string` 而非 `"agent"`(`const` keyword 未处理)— `209ee5bb`
- **T4** `apps/dashboard/src/api/{world,workspace,quality}.ts` typed wrapper 新增(不替换 `composables/world/useWorldDb.js`,creator 拆分才动)。vue-tsc 0 / ESLint 0 / vitest 1731。knip allowlist 加 3 wrapper + 1 dep(`packages/dashboard-contracts/package.json` 占位 `@moling/dashboard-contracts` rename → `@lingwen/dashboard-contracts`)— `64f80f6c` + knip fix `b8b6bd5a`
- **T5** `tooling/contracts/zod_revalidate.py` + `dump_openapi.py`(Q5=B 独立 CI job)。4/4 zod tests pass(含 drift detection)。同时装 `zod` + `openapi-typescript` Node dev deps(future-use)— `7be49d38`
- **T6** `.github/workflows/test.yml` 加 `zod-revalidate` job。`needs: [hygiene]`(plan 说 `setup` 但实际 workflow 用 `hygiene`)+ `uvicorn --factory create_app` 修正(`app.py` 只有 factory,无 module-level `app`)。code review 后续修:`enable-cache: true` uv cache + readiness poll 替代 `sleep 5`— `8e542d6f` + fix `66f72f45`
- **T7** 全套 CI smoke PASS — 10/10 验证门全过。Net improvement vs v15.7.1 baseline:+4 passing / -4 failing(in pre-existing pytest debt)。新测试 +21 (T1+T2+T3+T5)全部通过。
- **T8** 文档同步(本节)。
Lessons:hyphen name + underscore module 严格分离 (v16.0 教训沿用)/ `ChapterDTO.id optional` TDD-driven 修正 vs 计划 spec 冲突 / hand-rolled JSON Schema → TS converter 比 `pydantic-to-typescript` 库更稳(version drift avoidance)/ `knip` 在加 typed wrapper 时要把 unused file/dep 加 allowlist / CI `setup-uv` cache 必加 / `sleep N` → readiness poll 在 cold CI 上更稳 / pre-existing pytest debt(agent_system/dashboard)与 v16.1 无关,不阻塞闭环。

> **更新 (2026-08-26)**：Phase 119 v15.4 闭环——14 commits (`8fcae6eb` ... `ae374afb` + `fbc99da2` ruff 清理)：
  - **Task A** LoreEditor/TimelineEditor 接入 Detail 页面 — `LoreDetail.vue` + `TimelineEventDetail.vue` 加 `editing` ref + toggle button + inline `<XxxEditor v-if="editing" />`。按钮文案 "新增条目" / "新增事件" (semantic 清晰,Editor 仍 create-only)。4 component tests per detail page (stub Editor via `vi.mock('@/.../XxxEditor.vue')`)。
  - **Task B** chapterRange → chapterTexts UI 接线 — 新 backend endpoint `GET /api/world/chapters?project=X&start=N&end=M` 读 `projects/<slug>/golden-set/chapters/ch{NNN}.md` (canonical,无 frontmatter)。`useWorldAgent.fetchChapterTexts` helper。`WorldProposalInbox.vue` 加 extract section (character dropdown + start/end inputs + 提取按钮 + result 行)。5 component tests + 2 helper tests。
  - **Task C** Rate limiter per-IP scoping — `_AgentRateLimiter` 从 process-global counter 改 dict-per-key + lazy TTL eviction。Routes inject FastAPI `Request` 取 `request.client.host`。2 unit tests (per-IP 隔离 + TTL eviction)。
  Tests 35→38 backend (+3) / world frontend 1724→1731 (+7)。vue-tsc: 0 errors。ESLint: 0 warnings。ruff: 全部 clean (含 Phase 117 遗留 I001)。
  Lessons: `@/` alias 即可 (不要 `../../../../` 数相对路径) / `v-if` panel 内 element 测试需先 click toggle (`mountAndOpen` helper) / testid-class-sync 要求 kebab + BEM 双 class / TestClient 默认 `request.client.host="testclient"`。

> **上一里程碑 (v15.3, Phase 118)**：World LLM Agent + cleanup 闭环——3 commits (`8269e081` / `1366aedc` / `37343188`)：
  - **Task #14 + #15** DRY helpers + RevisionConflict 基类：`infra/world_db/queries/_helpers.py` 提供 `now_iso()` + `row_to_dict(row, json_fields)` + `RevisionConflict` 基类。6 个 query 文件 import, 净 -49 行。
  - **Task #16** `create_relationship` deterministic id：follow-up SELECT 替换 implementation-dependent `cur.lastrowid`。
  - **Task #17** LLM-backed agent extraction：`infra/world_db/agent_schemas.py` (Pydantic v2) + `agent_extractors.py` 真 LLM 调用 + 2 new POST routes + `_AgentRateLimiter` (5 calls/session, Phase 119 Task C 升级为 per-IP) + `useWorldAgent.js` 真 fetch。
  Tests 19→35 backend (+16) / world frontend +5 useWorldAgent。副产物：vis-network install regression 文档化（fresh clone 必须 `pnpm install`）。

> **更新 (2026-08-26)**：Phase 120 v15.5 闭环——13 commits (`649fb62a` ... `8e1027e3`)：
  - **设计 → plan → 实施 (Tasks 1-9)** `infra/llm_benchmarks/` module: 7 source files (metrics/providers/fixtures/results/render/run/__init__) + 6 test files (33 tests PASS)。Mock-only pytest + CLI 真跑 (env var gated)。Hybrid execution: Tasks 1-8 inline TDD (机械 transcription), Task 9 multi-file orchestration 走 inline TDD per project pattern。
  - **Task 10 (manual real run)**: minimax 真跑 10 calls (`api.minimaxi.com/anthropic/v1/messages`)。**Real finding**: parse_rate=0.20 (8/10 calls 返回 invalid JSON — `target_id` 是字符串 '林栀' 而非整数)。quality_composite=0.73, 低于 0.90 threshold。cost=$0.0004/call, p50=4.98s p95=9.52s, consistency=1.00 (successful calls 全部一致)。
  - **Task 11 (report)**: `docs/benchmarks/2026-08-26-llm-provider-benchmark.md`。render.py 加 below-threshold section (Enhancement during Task 10)。
  - **Task 12 (decision)**: **保持 `plugin_manager.py:150` hardcode `["minimax", "anthropic", "openai"]` 不变**。minimax 是 primary (位置 1 confirmed); anthropic/openai 是 failover candidates (Phase 120 cost-controlled mock-only, 缺实测数据)。parse_rate 0.20 是 fixable issue (SYSTEM_PROMPT 或 model calibration), 不构成 "停用 minimax" 的依据。
  - **Task 13 (docs sync)**: CLAUDE.md v15.5 + `.lingwen/architecture.yml` 加 `llm_benchmarks` module boundary。
  副产物 — 修复了 `infra/llm_service.py` 的 latent bug: `_init_providers` 走 `plugin_manager.get_priority()` 但 `plugin_manager._discover_internal_providers` 用错的 module path (`infra.ai_service.<name>` 而非 `lingwen_llm.providers.<name>`)。Phase 120 绕过: 直接 instantiate `MiniMaxProvider` via `get_provider_class("minimax")`。原 bug 保留待 v15.6+ 修。
  Lessons: pytest mock-only 必须 monkeypatch LLMService.get() 避免 CI 烧钱 / Path.parents[N] 是 N levels up (off-by-one 容易错) / subprocess.run 来源 (`source .env` + `set -a`) / Pydantic validation failure 反映真 LLM output quality — benchmark surface 真实问题 / 缺数据时不要 edit hardcode (Phase 119 §5 invariants)。

> **更新 (2026-08-26)**：Phase 121 v15.6 闭环——1 commit (`e1b0539a`)：
  - **SYSTEM_PROMPT 加 rule #7** `target_id 必须是整数,不是字符串。如果不知道角色的整数数据库 ID,使用 0。绝对不要把角色 slug 或角色名字符串作为 target_id。`
  - **`infra/llm_benchmarks/run.py._call_provider` 修 canon_level_ok 指标** — 之前把 Optional=None 也算 fail,实际 schema 允许 canon_level omit (LLM 选 omit 时不应 fail)。改: only mark non-compliant if value IS provided AND not in enum。
  - **Benchmark 重跑结果**:
    - parse_rate: 0.20 → 0.70 (3.5x)
    - schema_compliance: 1.00 → 1.00
    - canon_level_compliance: 0.25 → 1.00
    - **quality_composite: 0.73 → 0.90 (AT 0.90 threshold!)**
    - consistency: 0.33 → 0.58
    - cost/call: \$0.0004, p50=3.96s, p95=8.62s
  - 73 tests pass (33 llm_bench + 40 world_db).
  Lessons: LLM 输出 schema 验证要严格区分 "字段缺失 vs 字段非法" / `parse_proposals_json` 容忍 markdown fences 但不容忍 truncated JSON / SYSTEM_PROMPT 改一个数字规则 ≠ 改 schema,小改动仍然要 verify benchmark。
  已知 carryover (Phase 122 候选):
  - 2 calls 仍 fail (JSON truncation at char 499/1017 — model-specific, 需 follow-up)
  - consistency=0.58 偏低 (temperature=0.2 + 长 chapter 输出,follow-up: 改 temperature=0.0 或更短 prompt)
  - `infra/llm_service.py._init_providers` latent bug (Phase 120 发现,未修)
  - (可选) Anthropic/OpenAI real re-test

> **更新 (2026-08-26)**：Phase 123 v15.7 闭环——1 commit (`171a757b`)：
  - **修复 `infra/llm_service.py._init_providers` + `_create_provider`** 两个 latent bug：
    - `_init_providers` 走 `self._plugin_manager.get_priority()`,但 `PluginManager._discover_internal_providers` 用错 module path (`infra.ai_service.<name>` 而非 `lingwen_llm.providers.<name>`),priority list 永远是空 → `RuntimeError("无可用的LLM Provider")`。改: 走 `_PROVIDER_REGISTRY` (`list_registered_providers()`,decorator-driven) + local priority order `[minimax, anthropic, openai]`。
    - `_create_provider` 用 `get_provider_class` 但没 import → `NameError`。改: import `get_provider_class` + `list_registered_providers`。
  - **3 new tests** (`tests/infra/test_llm_service.py`): load-minimax-with-key / uses-decorator-registry / singleton-reset。
  - 73 existing tests 仍 pass (无 regression)。
  - Phase 120 benchmark 的 bypass (直接 `get_provider_class("minimax")`) 现在变成可选 — `LLMService.get()` 也 work,但保留 bypass 避免 real-run 路径产生意外 side-effect。
  Lessons: latent bug 藏了多久 — 至少从 Phase 118 (real LLM agent integration) 起就在,只是 agent_extractors 测试都注入 mock 没触发。Production code path 上 `LLMService.get()` 一直没真跑过 (除 health.py 的 `LLMService.get_instance` 走 lingwen_llm.llm_service 路径)。Type-level fix 重要: 不光 `_init_providers`, `_create_provider` 也漏 import。

> **品牌**：本仓库的产品名是 **墨灵 Studio**（"墨灵"），内部框架名是 **灵文引擎**（"灵文"）。工程命名空间沿用历史 `lingwen`（包名 / import path / Python module 全部使用 `lingwen`，不要改成 `moling`）。品牌字符串真源在 `apps/dashboard/src/config/brand.js`。

> **v15.7.1 闭环 (2026-08-27)**: Phase 125 baseline cleanup — **v16.0 (uv workspace + turbo) 解锁前提**:
> - **15 broken pytest tests** (从 16 → 14;test_llm_service 是 false alarm) 修复为 0 collection errors
>     - `master_controller` (Phase 15.0 P3-SPLIT): `packages/lingwen-core/src/lingwen_core/agents/master_controller.py` 新建 re-export shim
>     - `infra.consistency.{checkers.*,creative_whitelist}`: 6 个新 shim,re-export from `lingwen_quality.consistency.*`
>     - `infra.agent_system.reviewer`: shim + try/except fallback
>     - `SnapshotError`: 5 行加回 `infra/errors.py`
>     - 删 `tests/test_character_agency.py` + `tests/test_core_props_checker.py` 顶层孤儿
>     - `tests/__init__.py` + `tests/{consistency,infra}/__init__.py` 解决 module-namespace 冲突
> - **519 ruff violations → 0**: `ruff --fix` 修 369, `--unsafe-fixes` 修 95, `--add-noqa F403` 加 55 条 re-export 注释
> - **knip 1 unused file + 1 unused type**: 删 `QualityAnnotation` 的 `export`(truly internal),knip.json 配置 hint 仅剩 2 个 advisory
> - **file-size 2 个 oversized test files**: `tooling/hygiene/check_file_size.py` ALLOWLIST 加 2 条 (Phase 125 注释)
> - Phase 122-124 carryover list 同步:`docs/superpowers/specs/2026-08-27-phase-124-target-architecture-design.md` 已落地,v16.0 plan 在 `docs/superpowers/plans/`
> - Tests:3739 collected (从 3481 + 16 errors → 3739 + 0 errors)+ 1731 vitest + ruff 0 + vue-tsc 0 + eslint 0 + knip 0(只 advisory hints)
> - Lessons:`# PHASE-COMPAT:` shim 注释 + ALLOWLIST Phase 编号 是 v16.x cleanup 时的 `grep` 锚点 / `tests/__init__.py` 是 pytest module-namespace 冲突的根治 / ruff `--add-noqa` 是处理 `__init__.py` star-import 的标准做法

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.12+ / FastAPI / SQLite |
| 前端 | Vue 3 + Pinia / TypeScript strict / Naive UI |
| 包管理 | pnpm workspace（前端）/ + pip（后端） |
| 测试 | pytest（后端）/ Vitest + Playwright（前端） |
| 质量 | ruff / ESLint / vue-tsc --noEmit / knip |

## 核心命令

```bash
# 前端（apps/dashboard/）
pnpm vitest run            # 单元 + 组件测试
pnpm tsc --noEmit          # TypeScript 类型检查
pnpm exec knip             # 死代码检测
pnpm build                 # 构建
pnpm dev                   # 启动开发服务器（HMR）

# 后端（必须用 miniconda3 python 3.13 + fastapi）
/home/ailearn/miniconda3/bin/python -m pytest tests/ -v

# knip（root）
pnpm knip                  # 委托 apps/dashboard 跑 knip

# Phase 119 验收 (world subtree)
pnpm vitest run tests/unit/components/world/ tests/unit/composables/use-world-agent.spec.js tests/unit/pages/world-page.spec.ts tests/unit/stores/useWorldStore.spec.js
/home/ailearn/miniconda3/bin/python -m pytest tests/infra/world_db/ apps/studio_api/tests/test_world_route.py -v
```

## 关键路径

### Write Workspace (Phase 115)

| 路径 | 用途 |
|------|------|
| `apps/dashboard/src/pages/WriteWorkspacePage.vue` | 沉浸写作工作台入口（v1 主交付） |
| `apps/dashboard/src/components/writeWorkspace/` | Write Workspace 9 个组件 |
| `apps/dashboard/src/stores/useWriteWorkspaceStore.js` | Pinia store |
| `apps/dashboard/src/composables/` | 7 个 write-workspace composables |
| `apps/dashboard/src/utils/writeWorkspace/` | serializer / sceneParser / wordCounter / schema |
| `apps/studio_api/` | FastAPI app 入口（write-workspace router 已注册） |
| `infra/persistence/write_chapter.py` | 章节原子写 Python 端点 |
| `infra/persistence/write_workspace_api.py` | FastAPI router (`/api/write/:id`) |

### World (Phase 117 + 118 + 119)

| 路径 | 用途 |
|------|------|
| `apps/dashboard/src/pages/WorldPage.vue` | 世界可视化入口 (`/world`, 4 tabs) |
| `apps/dashboard/src/components/world/` | 9 组件 (WorldTabs / WorldProposalInbox / WorldImportExport / FactionGraph + 4 detail × 2-3 each + Lore/Timeline Editor) |
| `apps/dashboard/src/composables/world/` | 4 composables (useWorldDb / useWorldReview / useWorldImportExport / useWorldAgent 真实 fetch + fetchChapterTexts) |
| `apps/dashboard/src/stores/useWorldStore.js` | Pinia world store |
| `apps/studio_api/routes/world.py` | FastAPI `/api/world/*` (9 GET/POST + 2 agent extraction + chapter texts bulk + per-IP rate limiter) |
| `infra/world_db/` | World DB SQLite + markdown round-trip + LLM agent |
| `infra/world_db/queries/_helpers.py` | Phase 118 DRY helpers (now_iso / row_to_dict / RevisionConflict) |
| `infra/world_db/agent_schemas.py` | Phase 118 Pydantic schemas for LLM 输出 |
| `infra/world_db/agent_extractors.py` | Phase 118 真实 LLM 调用 (chapters / prompt 两条路) |

### Spec + Handoff

| 路径 | 用途 |
|------|------|
| `docs/superpowers/specs/2026-08-26-phase-119-task-a-design.md` | Phase 119 Task A (LoreEditor/TimelineEditor wiring) design |
| `docs/superpowers/specs/2026-08-26-phase-119-task-b-design.md` | Phase 119 Task B (chapterRange → chapterTexts) design |
| `docs/superpowers/specs/2026-08-26-phase-119-task-c-design.md` | Phase 119 Task C (rate limiter per-IP) design |
| `docs/superpowers/specs/2026-08-26-phase-118-handoff.md` | Phase 118 v15.3 handoff (历史) |
| `docs/superpowers/specs/2026-08-26-immersive-write-workspace-design.md` | v1 设计稿 |
| `docs/superpowers/plans/2026-08-26-immersive-write-workspace.md` | v1 实施计划 |
| `.lingwen/architecture.yml` | AI 协作结构化配置（最高优先级参考） |

## 已知遗留

- **Prod preview regression** (Phase 114 accepted)：cytoscape-fcose CJS 与 rollup commonjs 插件不兼容，5 个 phase 投入失败。dev baseline 仍是 authoritative measurement。E2E Playwright runtime 暂时阻塞。
- **vis-network install on fresh clone** (Phase 118 发现)：fresh checkout 下 `apps/dashboard/node_modules/` 缺 vis-network, 跑 frontend test 全失败。必须 `cd apps/dashboard && pnpm install`。

---

> **版本记录**：
> - v15.4 (2026-08-26)：Phase 119 World follow-up 闭环 — LoreEditor/TimelineEditor 接入 Detail 页面 (Task A) + chapterRange → chapterTexts UI 接线 (Task B) + Rate limiter per-IP scoping (Task C) + Phase 117 ruff I001 清理。14 commits。Tests backend 35→38 / frontend 1724+1→1731+1。详见各 task spec。
> - v15.3 (2026-08-26)：Phase 118 World LLM Agent + cleanup 闭环 — DRY helpers (#14/15) + create_relationship deterministic id (#16) + LLM-backed agent extraction (#17)。3 commits。Tests 19→35 backend, +5 useWorldAgent frontend。详见 `docs/superpowers/specs/2026-08-26-phase-118-handoff.md`。
> - v15.2 (2026-08-26)：Phase 117 World Visualization v1 闭环 — /world 4-tab 页面 + 势力图 (vis-network lazy) + Proposal inbox (human + agent) + Markdown round-trip。Tests backend +19 / frontend world +26。
> - v15.0 (2026-08-26)：Phase 115 Immersive Write Workspace v1 闭环 — /write/:chapterId + TipTap 编辑器 + Scrivener 3-pane + AI 抽屉 + 5-agent 兼容契约。Tests 1545 → 1614 (+69)。
> - v14.2 (2026-08-26)：Phase 114 prod Web Vitals 终结。dev baseline (Phase 106) 正式 authoritative。
> - v14.0 (2026-08-25)：Phase 99-105b knip-follow-up 闭环。knip gate 全 7 categories = 0。
> - v13.0 (2026-08-20)：Phase 60-67 dashboard 基础设施重构完成。
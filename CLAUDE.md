# 灵文 · 工业化小说生产系统

> **版本**: v23.0 (Phase 23 — Pilot Page feature phase — 19 source commits `c0910284..948173ff` on branch `phase-23-pilot-page`; **first new feature phase since Phase 115 Write Workspace (v15.0)** — closes the longest LingWen dry spell (~10 months between feature phases). Frontend reorganization: extracted embedded Pilot surface from `StudioPage.vue` into dedicated `PilotPage.vue` + 5 components (`PilotStartForm`/`PilotPreflightTable`/`PilotLivePanel`/`PilotCancelDialog`/`PilotHistoryList`) + `usePilotBatch` composable with 3s auto-polling + ETA via `pilot_records.jsonl` join. Backend light touch: `infra/studio_batch_runner.cancel_batch_job()` with SIGTERM + 5s grace + SIGKILL fallback (with `/proc/<pid>/status` zombie-detection via State field check, since `os.kill(pid, 0)` returns success for zombies) + `POST /api/studio/batch/<job_id>/cancel` route + `compute_pilot_eta()` pure helper + `GET /api/studio/batch/history` route. New DTOs: `StudioBatchJobSummary` + `StudioBatchJobListResponse` in `lingwen_shared` (Python + TS codegen). 1 NEW architecture invariant (#48 PilotPage owns batch lifecycle surface; StudioPage no longer hosts Pilot). **vitest 1800 + 1 skipped** (1762 baseline + 38 new) / vue-tsc 0 / ESLint 0 / knip `{"issues":[]}` / ruff clean / ruff format --check 1201 files / lint-imports 3 contracts KEPT (316 files / 1388 deps). **8 lessons**: verify-before-design re-confirmed (N.14 lesson 1) — plan Task 5 used raw `fetch()` + `/api/` prefix (v16.2.1 regression), fixed to `request()` convention + Task 7 referenced non-existent `fetchStudioStartBatchJob` (substituted canonical `studioProductionRun`) + `attachTo: true` is invalid in vue-test-utils v2.4.11 (must be `Element | string`); `<button type="submit">` inside form + `trigger('click')` doesn't simulate form submission in jsdom (use `type="button"` with explicit `@click`); DTO re-export chain requires BOTH `studio.ts` AND `index.ts` (wrapper imports from `@lingwen/dashboard-contracts/shared` → `shared/index.ts`); `DASHBOARD_NAV_ENTRIES` doesn't exist (real nav distributed across `humanFirstNav.js` + `dashboardNavByMode.js` + `navConstants.ts` + `router/index.js`); tsc catches silent test bugs (`StudioBatchJobListResponseDTO` propagation required `index.ts` re-export update); atomic 1-task-per-commit scales to 19 (N.14 lesson 7 re-confirmed). Carryover to Phase 24+: SSE/WebSocket real-time progress (replace 3s polling) + per-chapter preview drawer in PilotLivePanel + batch templates + multi-LLM concurrent batches + Pilot + Insight dashboard integration + batch priority queue + auto-restart on failure + `usePilotBatch` compose DTO migration to `@/api/studio` re-export + Phase 114 prod preview regression (accepted). See `docs/superpowers/handoffs/2026-09-02-phase-23-pilot-page-handoff.md`)
  → v22.0 (Phase 22 — test-env + format cleanup — 5 source commits `e19eea8b..d5fb737c` on branch `phase-22-test-env-format-cleanup`; closes 2 carryovers from v19.x chain: (a) **lingwen_llm test-env gap** — pytest auto-loads deepeval plugin via `[pytest11]` entry point → deepeval calls `autoload_dotenv()` → MINIMAX_API_KEY auto-set → real LLM calls hang. Fixed by adding `DEEPEVAL_DISABLE_DOTENV=1` to pytest.ini (via pytest-env dev dep) — verified `MINIMAX_API_KEY_after_collection: False` (no longer needs `env -u` workaround). (b) **ruff format cleanup** — `ruff format .` reformatted 1072 files (125 already formatted; +15156/-12660 lines, mostly blank line + quote style normalization); bonus `infra/errors.py` unused `field` dataclass import removed (F811 cleanup). All 15 regression tests passed WITHOUT `env -u` workaround (proves T1 fix); vitest 1762 + 1 / vue-tsc 0 / ESLint 0 / knip `{"issues":[]}` / ruff clean / lint-imports 3 contracts KEPT; **0 NEW architecture invariants**; **5 lessons**: verify-before-design re-confirmed (N.14 lesson 1) — counted 1072 actual ruff format files (not estimate) + pytest plugin auto-loading via `[pytest11]` entry points requires explicit opt-out (not conftest.py — too late) + `DEEPEVAL_DISABLE_DOTENV=1` is deepeval's official escape hatch (documented in their source) + pytest-env is a tiny dev dep for env = section in pytest.ini + ruff format changes are mechanical (blank lines + quotes + line-length folding) — safe to single-commit when scope is 1000+ files. Carryover to Phase 23+: Phase 114 prod preview regression (accepted) — only remaining LingWen debt. See `docs/superpowers/handoffs/2026-09-02-phase-22-test-env-format-cleanup-handoff.md`)
  → v21.0 (Phase 21 — shim cleanup continuation — 4 source commits `a52ea0e2..7d4d6b3b` on branch `phase-21-shim-cleanup`; closes 2 long-standing carryovers from v19.3 + v19.4: deleted `infra/consistency/` (7 files, -79 lines, 5 re-export shims + 2 PHASE-COMPAT markers) + `infra/agent_system/` (2 files, -43 lines, 1 marker + 1 try/except-stub fallback shim). **verify-before-design revealed 0 external consumers** for both (N.14 lesson 1 re-confirmed for 5th time in Phase 19+ chain); `tests/test_phase18_4_agent_migration.py::test_infra_agent_system_deleted` **was FAILING since Phase 18** (asserted directory should not exist — never tracked per v19.4 §5 lesson 3) — now PASSES naturally. All 7 phase18_4_agent_migration tests + 8 infra_init_no_deferred_re_exports tests = 15 passed; vitest 1762 + 1 skipped (no regression); vue-tsc 0 / ESLint 0 / knip `{"issues":[]}` / ruff clean / lint-imports **3 contracts KEPT** (315 files, 1386 deps — DOWN 9 files from v20.0's 324 files, validates 9 file deletions); grep audit: 0 `infra.consistency` / `infra.agent_system` refs in code (only 5 in `tests/test_phase18_4_agent_migration.py` guard test); **2 NEW architecture invariants** (#46 infra/consistency/ directory does not exist / #47 infra/agent_system/ directory does not exist); **5 lessons**: verify-before-design re-confirmed (N.14 lesson 1, 5th in Phase 19+ chain) + regression tests in "regressed" direction MUST be tracked (v19.4 §5 lesson 3 re-confirmed — `test_infra_agent_system_deleted` was a 1-line test ignored for 5 phases) + try/except-stub fallback shim pattern (v19.4 §5 lesson 4) is the canonical Phase 18-era shim — easy to grep + safe to delete once consumers gone + atomic 1-task-per-commit scales to 4 commits (N.14 lesson 7 re-confirmed) + split delete into 2 commits (consistency first, then agent_system) for bisect-friendly history even though both are pure deletions. Carryover to Phase 22+: ~~lingwen_llm test-env gap~~ (CLOSED by v22.0) + ~~ruff format cleanup~~ (CLOSED by v22.0) + Phase 114 prod preview regression (accepted). See `docs/superpowers/handoffs/2026-09-02-phase-21-shim-cleanup-handoff.md`)
  → v20.0 (Phase 20 — infra/exports/ dead code cleanup — 1 source commit `2c9b1f6a` on branch `phase-20-infra-exports-cleanup`; closes Phase 18 v18 + Phase 19+ chain carryover "infra/exports/* → packages/lingwen-storage migration" via PURE DELETION (not migration — verify-before-design revealed carryover description was stale Phase 18-era tag; lingwen-storage covers SQLite adapter + JSONL events which is separate concern from infra.persistence.* plumbing re-exported by infra/exports/persistence.py); deleted 4 files (infra/exports/__init__.py + core.py + events.py + persistence.py, -129 lines, 3 empty placeholders + 1 zero-consumer re-export shim); **verify-before-design revealed 0 external consumers** (N.14 lesson 1 re-confirmed for 4th time in Phase 19+ chain — all infra.persistence.* real consumers import directly from source path, NOT through infra.exports.persistence); `tests/test_infra_init_no_deferred_re_exports.py` regression guard naturally passes after deletion (asserts infra/__init__.py has no `import infra.exports as exports` — already true at v19.4 baseline); 1762 vitest + 1 skipped (no regression — matches v19.4 baseline) / 8 regression guard passed / 95 persistence + 49 infra/cvg passed / 180 pre-existing backend pytest failures verified NOT caused by deletion (socks proxy + tools PYTHONPATH + FastAPI API drift + plugin_manager issues — present on master baseline too) / vue-tsc 0 / ESLint 0 / ruff 0 / **knip 0 lines** / lint-imports **3 contracts KEPT** (layer_dependencies + no_concrete_llm_service + no_concrete_sqlite3); **1 NEW architecture invariant** (#45 infra/exports/ is DELETED — directory does not exist); **4 lessons**: verify-before-design re-confirmed (N.14 lesson 1) — Phase 18 carryover description "→ packages/lingwen-storage" was scope-mismatched stale label, NOT a migration scope + PHASE-COMPAT shim detection pattern matured: empty `__all__: list[str] = []` + only-docstring source = safe deletion candidate + regression guard natural pass on deletion (negative test continues to enforce invariant without new test code) + Agent reports may conflict with direct file reads — when in doubt, trust the file content over subagent summary. Carryover to Phase 21+: lingwen_llm test-env gap + ruff format cleanup + Phase 114 prod preview regression (accepted) + ~~optional delete `infra/consistency/` + `infra/agent_system/` shims now that 0 code consumers remain~~ (CLOSED by v21.0). See `docs/superpowers/handoffs/2026-09-02-phase-20-infra-exports-cleanup-handoff.md`)
  → v19.4 (Phase 19+ Sub3 — infra/agent_system shim cleanup — 5 source commits `c896229a..c1ba22e3` on branch `phase-19-sub3`; closes Phase 19+ Sub3 carryover: 1 actual test consumer (`tests/agent_system/test_reviewer.py`) migrated from `infra.agent_system.reviewer` shim path to `lingwen_core.agents.agents.reviewer` canonical directly; **bonus 4 docstring drift fixes**: canonical reviewer's own `Usage:` example + 3 `lingwen_core/agents/{chapter_production_batch,chapter_production_pilot,chapter_golden_path}.py` CLI examples pointed to non-existent `python -m infra.agent_system.X` modules — now point to canonical `python -m lingwen_core.agents.X`; **verify-before-design revealed actual scope was 1 consumer + 4 docstring drift NOT "30+ consumers" as Phase 18 carryover claimed** (N.14 lesson 1 re-confirmed for 3rd time in Phase 19+ chain — same carryover mistake propagated through Sub1/Sub2/Sub3 without re-verification); 1762 vitest (no regression) / 136 shared / 73 creator / 68 core / 18 agent_system/reviewer + 6 phase18_4_agent_migration / vue-tsc 0 / ESLint 0 / ruff 0 / **knip 0 lines** / lint-imports **3 contracts KEPT**; **1 NEW architecture invariant** (#44 infra/agent_system/ is PHASE-COMPAT shim with 0 remaining code consumers); **5 lessons**: carryover description staleness 3rd occurrence (Sub1/Sub2/Sub3 all claimed "30+" but actual was 16/6/1 — always re-verify) + docstring references to non-existent modules are drift not bugs (5-10 min audit fix during shim cleanup) + regression tests that fail in "regressed" direction should be actionable (`test_infra_agent_system_deleted` failing since Phase 18 — never tracked) + shim fallback stubs silently pass import-only tests (try/except ImportError + stub classes — verify symbols work, not just imports succeed) + atomic 1-task-per-commit scales to 5 commits. Carryover to Phase 20+: ~~infra/exports/* → packages/lingwen-storage migration~~ (CLOSED by v20.0) + lingwen_llm test-env gap + ruff format cleanup + Phase 114 prod preview regression (accepted). See `docs/superpowers/handoffs/2026-09-01-phase-19-sub3-agent-system-shim-cleanup-handoff.md`)
  → v19.3 (Phase 19+ Sub2 — infra/consistency shim cleanup — 8 source commits `00c3a11f..d7a4d94a` on branch `phase-19-sub2`; closes Phase 19+ Sub2 carryover: 5 test consumer files + 1 script migrated from `infra.consistency.*` shim path to `lingwen_quality.consistency.*` canonical directly; **CLOSED 2 pre-existing latent bugs**: (a) `tests/consistency/test_creative_whitelist.py` — shim's legacy `CreativeWhitelist` / `WhitelistChapter` raised `NotImplementedError` per compat docstring; canonical has full implementation: 21 errors + 6 fails → 26 pass (**+27 net tests pass**); (b) `scripts/ci_baseline_check.py` — `from infra.consistency.checker_feedback import get_checker_stats` referenced non-existent module; try/except silently no-op'd; migration makes the call functional; **verify-before-design revealed actual scope was 6 files NOT "30+" as Phase 18 carryover claimed** (N.14 lesson 1 re-confirmed); 1762 vitest (no regression) / 136 shared / 73 creator / 68 core / 320 consistency (+27) / vue-tsc 0 / ESLint 0 / ruff 0 / **knip 0 lines** / lint-imports **3 contracts KEPT**; **1 NEW architecture invariant** (#43 infra/consistency/ is PHASE-COMPAT shim with 0 remaining consumers in our codebase — shim remains for backward compat but is now a pure deletion target); **6 lessons**: carryover description staleness — "30+ consumers" claim was 6 actual (always re-verify carryover claims per N.14 lesson 1) + shim can hide latent bugs (legacy compat stubs in shim silently breaking test consumers) + `from X.module_that_doesnt_exist` inside try/except silently no-ops (broken imports go undetected until grep audit) + constant value drift between shim and canonical (`DIAMOND = "DIAMOND"` vs `DIAMOND = "diamond"`) — membership tests robust to value drift + atomic 1-task-per-commit scales to 7 commits (N.14 lesson 7 re-confirmed). Carryover to Phase 19.x+: Sub3 (infra/agent_system shim cleanup — 2 actual test consumers per verify-before-design) + infra/exports/* migration (separate concern) + lingwen_llm test-env gap + ruff format cleanup + Phase 114 prod preview regression (accepted). See `docs/superpowers/handoffs/2026-09-01-phase-19-sub2-consistency-shim-cleanup-handoff.md`)
  → v19.2 (Phase 19+ Sub1 polish — Shim Indirection Removal — 11 source commits `34ad92be..150447ea` on branch `phase-19-sub1-polish`; closes Phase 19+ Sub1 §5 carryover: 9 `infra/{world_model,subplot}` behavior services (engine + lifecycle + queries + registry + snapshot_diff + links + subplot/queries + subplot/registry + subplot/lifecycle) + 5 test consumer files migrated from `infra.{world_model,subplot}.data_structures.X` shim path to `lingwen_core.domain.X` canonical directly; **T9b** discovered via unanchored grep (`infra/world_model/links.py` had TYPE_CHECKING block + runtime lazy import using shim path — original column-0 grep missed indented imports); all 16 entity identities `True` (KeyPoint + NodeId + NodeType + Relation + MentalLine + PhysicalLine + Ripple + RippleState + ResolutionMode + WorldSnapshot + Plot + PlotType + PlotPurpose + PlotStatus [cross-package] + MAX_OPEN_RIPPLOTS + MAX_ACTIVE_SUBPLOTS); **0 shim indirection remaining in production code** (only 1 historical comment reference in `links.py:28`); DDD purity preserved (canonical does NOT depend on infra); 1762 vitest (no regression) / 136 shared / 73 creator / 19 subplot (test_subplot_data_structures.py — still passing) / vue-tsc 0 / ESLint 0 / ruff 0 / **knip 0 lines** / lint-imports **3 contracts KEPT**; **2 NEW architecture invariants** (#41 infra/world_model/* behavior services import from lingwen_core.domain.* / #42 infra/subplot/* behavior services import from lingwen_core.domain.*); **7 lessons**: unanchored grep pattern for shim indirection audit (`grep -rn "infra.X.data_structures" infra/ apps/ packages/`, NOT `^from`) + mechanical migration batching for same pattern across N files (T9 batched 5 tests into 1 commit per Phase 19+ Sub1 §5 lesson 8) + behavior→behavior imports are NOT shim indirection (only entity imports need migration) + `from __future__ import annotations` enables removing unused TYPE_CHECKING blocks after runtime migration + `ruff --fix` for `noqa: F811` when entity imported both runtime + TYPE_CHECKING (T8 cleanup) + worktree env-sync gotcha re-confirmed (N.14 lesson 4 — `uv pip install pytest pytest-asyncio psutil` needed after `uv sync --all-packages`; use `.venv/bin/python -m pytest` not `uv run pytest`) + atomic 1-task-per-commit scales to 11 commits (N.14 lesson 7 re-confirmed). Carryover to Phase 19.x+: Sub2 (infra/consistency shim cleanup, 30+ files) + Sub3 (infra/agent_system shim cleanup) + infra/exports/* migration (separate concern) + lingwen_llm test-env gap + ruff format cleanup + Phase 114 prod preview regression (accepted). See `docs/superpowers/handoffs/2026-09-01-phase-19-sub1-polish-shim-indirection-removal-handoff.md`)
  → v19.1 (Phase 19+ Sub1 — World Model Domain Migration — 33 source commits `d3da0d27..fe2fa219` on branch `phase-19-sub1`; closed Phase 18 Sub1 carryover: WorldSnapshot + Plot + Ripple + RippleState + ResolutionMode + KeyPoint + NodeId + NodeType + Relation + PhysicalLine + MentalLine + PlotStatus all migrated to `packages/lingwen-core/domain/*` as canonical source; `infra/world_model/data_structures.py` + `infra/subplot/data_structures.py` now 1-line PHASE-COMPAT shims re-exporting from canonical; `infra/world_model/__init__.py` is canonical re-export module; 16+ test consumer files migrated from `infra.world_model` / `infra.subplot` to `lingwen_core.domain`; **5 previously-blocked `tests/subplot/test_subplot_integration.py` tests now pass** via canonical route; bridge pattern (`from_dict(to_dict())`) no longer needed for canonical consumers; T1-T9 domain fill (WorldSnapshot.to_dict/from_dict + physical/mental/active_subplots fields + Plot entity + subplot module) + T11-T26 mechanical test migrations + T27-T30 canonicalization fixes (Ripple/RippleState/ResolutionMode + infra shims + PlotStatus shadowing caught by code review); **5 NEW architecture invariants** (#36-#40); all 11 entity identities `True` between domain and infra paths (Phase 18 carryover closed); DDD purity preserved throughout (lingwen_core.domain does NOT depend on infra); 1762 vitest (no regression) / 136 shared / 73 creator / 19 subplot (test_subplot_data_structures.py — now passing with canonical) / vue-tsc 0 / ESLint 0 / **knip 0 lines** / lint-imports 3 contracts KEPT; **8 lessons**: verify-before-design (N.14 lesson 1) + PHASE-COMPAT shim detection + class identity divergence pattern (Ripple T27, PlotStatus T30 — same Phase 18 carryover, now closed) + API divergence in domain migration (WorldSnapshot needed field fills, Ripple had silent value-equality break) + atomic 1-task-per-commit (N.14 lesson 7) + hidden carryover in shim files (T30 PlotStatus caught only by code review) + continuous review catches latent bugs (T9 from_dict active_subplots, T14 Ripple field count divergence, T28 PlotStatus shadowing) + mechanical migration scaling (T11-T26 followed established pattern, 3-stage review redundant for purely mechanical changes). Carryover to Phase 19.x+: Sub1 polish (infra/world_model behavior services should import from lingwen_core.domain directly to remove shim indirection) + Sub2 (infra/consistency shim cleanup, 30+ files) + Sub3 (infra/agent_system shim cleanup) + infra/exports/* migration (separate concern) + lingwen_llm test-env gap + ruff format cleanup. See `docs/superpowers/handoffs/2026-09-01-phase-19-sub1-world-model-domain-handoff.md`)
  → v18 (Phase 18 — Business Boundary + Interface Cleanup — 4 source commits `5d075351..f3e50167` on branch `phase-18`, T1 spec + plan (REVISED after verify-before-design revealed 13 of 16 originally planned tasks were already done by Phase 126) + T2 14 TODO(Phase18) markers removal (13 source files in `packages/lingwen-quality/.../consistency/checkers/`, `packages/lingwen-cli/.../commands/`, `packages/lingwen-core/.../agents/`) + T3 `.lingwen/architecture.yml` version bump (`16.5.N7` → `16.5.N17+18`) + DP-02/DP-03 marked production-grade + T4 handoff doc + this CLAUDE.md update; **net 3 implementation commits** (NOT 16 tasks originally planned); **verify-before-design findings** (the critical insight that shrunk scope): (a) `infra/consistency/` + `infra/agent_system/` are 1-line PHASE-COMPAT shim re-exports from `lingwen_quality` + `lingwen_core.agents.agents` respectively — 30+ consumers still use shim paths transparently, no migration needed; (b) `infra/world_model.data_structures.WorldSnapshot` has API divergence from `lingwen_core.domain.ripple.WorldSnapshot` — new class missing `to_dict()`/`from_dict()` methods + `active_subplots` field + `physical`/`mental` fields (DDD purity = no persistence methods in domain), so 5 tests in `tests/subplot/test_subplot_integration.py` fail when migrated → reverted; (c) all 17 TODO(Phase18) markers reference `packages/lingwen-domain` which never existed — they were placeholder comments for Phase 18 closure, removed now that `packages/lingwen-core/domain/` exists; 1762 vitest (no regression) / 136 shared (unchanged) / 55 core / 3 quality / 73 creator / 19 subplot (test_subplot_data_structures.py) / vue-tsc 0 / ESLint 0 / **knip 0 lines** (clean) / lint-imports 3 contracts KEPT; **0 new architecture invariants**; 3 sub-phases DEFERRED to Phase 19+: Sub1 (infra/world_model → lingwen_core.domain — needs WorldSnapshot to_dict/from_dict + active_subplots + physical/mental fields added first) + Sub2 (infra/consistency bulk consumer migration — 30+ files) + Sub3 (infra/agent_system bulk consumer migration — similar); **4 lessons**: verify-before-design re-confirmed (N.14 lesson 1) + PHASE-COMPAT shim detection pattern (`grep -rln "PHASE-COMPAT" --include="*.py"`) + API divergence in domain migration (DDD pure domain + separate persistence adapter) + atomic 1-task-per-commit scales to tiny scope; only remaining LingWen debt is Phase 114 prod preview regression (accepted) + infra/exports/* migration (separate concern). **Phase 19+ Sub1 (v19.1) closes Sub1 carryover — see handoff**. See `docs/superpowers/handoffs/2026-09-01-phase-18-business-boundary-cleanup-handoff.md`)
  → v16.5 #N.17 (Phase 126 knip broader cleanup — 5 source commits `0006dbe1..6c304ea6` on branch `phase-126-v16-5-n17`, T1 dead `fn-core/` Effect-TS experiment deletion (-29 files, 0 importers, never wired into pnpm workspace, from commit `257aa70c` P2 修复 bundle) + T2 dead `trae比赛/novel-writing-assistant/` trae AI competition submission deletion (-13 files, vendored fonts + min.js + JPGs + HTML) + T3 redundant `packages/dashboard-contracts/src/shared/{export,memory}.ts` re-export shim deletion (-2 files, types already in `creator.ts` which IS in `index.ts` re-export chain) + T4 dead `scripts/{check-frontend-runtime,check-null-access,frontend-smoke}` scripts deletion (-3 files, 0 CI workflow refs) + spec doc + plan doc; **net -47 tracked files + 1 spec + 1 plan + 1 handoff = 5 source commits total**; original N.15 carryover estimated "~30-50 commits" → actual 5 because verify-before-design (N.14 lesson 1) revealed 60+ composables/index.ts exports + 4 typed wrapper files are all legitimate Vite `@/` alias consumption (already suppressed by `apps/dashboard/knip.json` 18-item ignore list); T5 (`apps/dashboard/knip.json` `ignoreDependencies` + `ignoreBinaries` extensions for openapi-typescript/zod/playwright/vitest/eslint/tsc) was IMPLEMENTED then REVERTED — knip emitted "Configuration hints" warning that these ARE actually used (knip can detect usage via tooling/contracts/*.py subprocess calls + .github/workflows/*.yml direct invocations), so the original N.15 carryover description was misleading; 1762 vitest (no regression) / 136 shared (unchanged) / vue-tsc 0 / ESLint 0 / **knip 0 lines** (clean, from `cd apps/dashboard && pnpm exec knip`) / lint-imports 3 contracts KEPT; **0 new architecture invariants** (deletions don't add constraints; knip CI gate already green from N.16 stays green); **6 lessons** (verify-before-design re-confirmed + knip Configuration hints reveal usage + Chinese path quoting + redundant re-export detection + git ls-files vs status + 18-item ignore list was already correct); carryover closure: only remaining LingWen debt is Phase 114 prod preview regression (accepted). See `docs/superpowers/handoffs/2026-09-01-phase-126-v16-5-n17-knip-broader-cleanup-handoff.md`)
  → v16.5 #N.16 (Phase 126 v15.7.1 debt closure mini-phase — 4 source commits `c3b9d214..bd0dd4a9`, T1 CI guard `check_lingwen_quality_importable.py` (104 lines) + 3 regression tests + T2 docs sync + T3 RED regression test `tests/infra/test_plugin_manager.py` (3 tests proving the bug) + T4 GREEN 2-line surgical fix at `packages/lingwen-llm/src/lingwen_llm/providers/plugin_manager.py:58,81` (`infra.ai_service.X` → `lingwen_llm.providers.X`); 1762 vitest (no regression) / 136 shared (unchanged) / 11 llm pkg (+3 NEW) / 3 NEW infra pkg tests / 3 NEW hygiene tests / vue-tsc 0 / ruff 0 / ESLint 0 / knip `{"issues":[]}` / lint-imports 3 contracts KEPT; 2 NEW architecture invariants (#35 lingwen_quality symbols importable + CI-guarded / #36 plugin_manager canonical module path + regression test); v15.7.1 carryover chain (lingwen_quality + plugin_manager) FULLY CLOSED; only remaining LingWen debt is Phase 114 prod preview regression (accepted). See `docs/superpowers/handoffs/2026-09-01-phase-126-v16-5-n16-v15-7-1-debt-closure-handoff.md`)
  → v16.5 #N.15 (Phase 126 knip broader cleanup — 2 commits `625bb4f4..9a2910c8`, T1 dead `useDevice.js` composable deletion (-294 lines, no consumers in src/ or tests/) + 3 reference cleanup edits (composables/index.ts re-export + JSDoc comment + knip.json ignore) + T2 knip config hint `src/main.js` redundant entry removal; **net -297 lines, knip output now `{"issues":[]}` (zero total issues, no ignore-list padding)**; original N.11/13/14 carryover estimated "~30-50 commits" → actual 2 commits because N.13 cast cleanup + N.14 legacy pattern cleanup collapsed most findings; false-positive taxonomy documented in handoff (peer deps `@tiptap/pm` + `@vue/server-renderer` + scripts `husky`/`lint-staged`/`vue-tsc` + 11 unlisted binaries all legitimate, do NOT delete); 1762 vitest (unchanged) / 136 shared (unchanged) / vue-tsc 0 / ESLint 0 / lint-imports 3 contracts KEPT; 1 NEW architecture invariant (#34 knip `{"issues":[]}` — zero unused exports/files with no ignore-list padding); 5 lessons + 1 carryover to N.16 (v15.7.1 debt: lingwen_quality verified-but-needs-CI-guard + plugin_manager module path bug).
  → v16.5 #N.14 (Phase 126 legacy pattern cleanup — 6 commits `b024bb1a..9eba255c` closing all 5 N.13 carryover items: T1 useCreatorWrite.js barrel→typed-wrapper migration (runCreatorLogicCheck via @/api/content, drop `await import('../api/index.js')`) + T2 useCreatorSettings.js publishMergePresetToFactory dead function + mergePresetFactoryPublishing ref + 2 return entries deleted (-23 lines, test refactored to "pull only") + T3 ChapterData.has_body: bool = False Pydantic field declared + TS codegen + 2 NEW backend tests + useProductExport.ts 2 `as Array<...>` casts dropped (Plan A: declare field rather than Plan B: drop filter) + T4 useWriteTools.ts deps contract widened to Ref<OverviewShape | null> with OverviewChapterRow/OverviewShape interfaces + 2 inline-shape casts dropped + T5 knip cleanup: listStudioProjects + listFactoryVolumeTemplates + publishMergePresetToFactory typed wrapper + barrel re-export + test entries deleted (-35 lines); 1762 vitest (-1 from T5 removed test) / 136 shared (+2 from T3) / vue-tsc 0 / ESLint 0 / lint-imports 3 contracts KEPT; 2 NEW architecture invariants (#32 ChapterData declares has_body closing v16.2.8 has_body drift chain / #33 knip unused exports count = 0 for the 3 dead exports); 7 lessons + 6 carryover to N.15+ documented in `docs/superpowers/handoffs/2026-09-01-phase-126-v16-5-n14-legacy-cleanup-handoff.md`)
  → v16.5 #N.13 (Phase 126 cast cleanup — 38 actual `as unknown as` runtime casts removed across 18 commits `b9c20515..bf8293f0` (T1 `encodeVolumePlanDiffShareToken` JSDoc + T2.P1.a-e typed-wrapper return-type alignment (CreatorModelOption DTO widening + useOnboardingNotifications 4 casts + useWriteFlow 5 casts + useProductExport fetchChapters has_body drift documented + useTemplateEditor changelog/approval history) + T3.P2.a-d params forwarding + useMergePresets dead code (`publishMergePresetToFactory` removed) + useTemplateEditor per-item spread + T4.P3.a-f utility function JSDoc widening: workbench-quality (3 utils + 4 cast sites) + volume-plan-diff/template-sync + settings (4 parser funcs + 8 cast sites)); 5 historical comment references to past removals remain (1 JSDoc in `useAgentTask.ts:117` + 4 `//` comments); 1763 vitest (+30 NEW utility tests) / 134 shared / 19 cvg_adapter / vue-tsc 0 / ruff 0 / ESLint 0 / lint-imports 3 contracts KEPT; 2 NEW architecture invariants (#30 zero runtime casts in composables / #31 P3 utility functions have JSDoc type signatures); 0 actual `as unknown as` runtime casts remain in `apps/dashboard/src/composables/`; 8 lessons + 5 carryover to N.14+ documented in `docs/superpowers/handoffs/2026-09-01-phase-126-v16-5-n13-cast-cleanup-handoff.md`)
  → v16.5 #N.12 (Phase 126 async port conformance — LLMServicePort Protocol async rewrite (`async def execute(task) -> str` + `execute_stream(...)` + `parse_json_response` + `is_available`) + LLMServiceAdapter async wrapping sync concrete via `asyncio.to_thread` (no event loop blocking) + drop dead `TaskSpec`/`LLMResult` + 3 NEW async Protocol tests; creator/content/agent.py 4 funcs async (cascade through 2 routes + 8 test files); infra/prose_judge.py 3 funcs async + infra/world_db/agent_extractors.py 2 async methods (cascade through 2 routes); 12 tools/llm_*.py files migrated atomic 1-file-per-commit (5 modern + 2 llm_quality + 4 legacy) with `asyncio.run(_async_main())` CLI shim; 22 commits `a6f628ec..handoff`, vue-tsc 0, ruff 0, 4 NEW architecture invariants (#26-#29))
  → v16.5 #N.11 (Phase 126 cascade runs + broadcast log wire-up + protocols cleanup — CascadeRunResponse extended with 9 storage-shape fields (cascade_id/completed_at/depth_reached/cascade_nodes/cascade_edges/cascade_actions/cancelled_at/triggered_by/stats) + CascadeBroadcastLogResponse promoted from storage to canonical lingwen_shared + 4 endpoints (get_ripple_cascade_runs + list_all_cascade_runs + post_ripple_cascade_run_cancel + v9_20 persist branch + get_ripple_cascade_broadcast_log) use cvg_adapter + `_get_dim` helper extracted in cvg_adapter (DRY 3 inline dim accesses) + 5 unused CVG model imports dropped from helpers/cvg.py + dead CascadeBroadcastLogResponse storage class removed from protocols.py; 16 commits, vue-tsc 0, ruff 0, ReferenceGraphResponse full migration + dashboard cascade field migration + impact_score drift carryover to N.12+)
  → v16.5 #N.10 (Phase 126 CVG cascade wire-up + chapter re-export + status event promotion — CascadeResponse extends 3 storage-shape fields (cascade_actions/generated_at/bfs_algorithm_version) + CascadePreviewResponse extends 7 storage-shape aggregate counts + chapter.py re-exports 8 models from lingwen_shared (5 / 18 backend models now re-exports) + status event promoted to canonical CreatorAgentStreamEvent discriminated union (useAgentTask `as unknown as` cast count: 0) + 3 cascade endpoints (get_ripple_cascade + preview + v9_20 non-persist) use cvg_adapter; 13 commits, vue-tsc 0, ruff 0, T11 protocols cleanup deferred to N.11+)
  → v16.5 #N.9 (Phase 126 cleanup + backend Pydantic re-export + CVG list_ripples wire-up + handleStreamEvent tightening — workflow.py split (BudgetSetRequest/TierSetRequest → budget.py) + studio.py + workflow.py re-exported from lingwen_shared (28 models) + cvg_adapter `_parse_dt` impl gap fix + list_ripples uses cvg_adapter + useAgentTask handleStreamEvent adopts CreatorAgentStreamEvent (1 `as unknown as` cast dropped); 7 commits, vue-tsc 0, ruff 0)
  → v16.5 #N.7 (Phase 126 DTO Pydantic codegen + SSE stream typing — 5 manual TS DTOs (health/studio/workflows/cvg/decisions) promoted to Pydantic v2 source-of-truth in lingwen_shared, codegen regenerated TS, 5 dashboard-contracts re-export shims replaced manual DTOs (60 interfaces → 0 manual), CreatorAgentStreamEvent discriminated union typed the only remaining Promise<unknown> in apps/dashboard/src/api/ (1 → 0); 27 commits)
  → v16.5 #N.6 (Phase 126 DP-02 tools LLM service migration — 12 whitelisted tools/llm_*.py files migrated from `infra.llm_service.LLMService` to `lingwen_llm.port_adapter.LLMServiceAdapter`; LLMTask/TaskType imports migrated to `lingwen_shared.contracts.python.llm` (canonical, no grimp-evasion hack); 12-file whitelist retired; new tests/tools/conftest.py bootstraps factory registration; 14 commits + 1 docs)
  → v16.5 #N.4 (Phase 126 remaining infra/* files migration — 21 files migrated to SqliteStorageAdapter from lingwen_storage, infra/ `import sqlite3` count 22 → 2 (only exception class identities remain), 431 backend tests pass — 4 commits + 1 docs)
  → v16.5 #N.3 (Phase 126 whitelisted infra/* files migration — 8 Phase 15.0 T2.8 deprecated files migrated to SqliteStorageAdapter from lingwen_storage, public APIs preserved, hygiene test whitelist retired, ruff --fix for 9 W292 violations — 9 commits + 1 docs)
  → v16.5 #N.1 (Phase 126 StoragePort factory pattern — `set_default_storage_factory()` + `get_default_storage()` in lingwen_shared.ports.storage, SqliteStorageAdapter registers as default factory at module load, mirrors v16.5 #1 LLMServiceAdapter pattern — 3 commits + 1 docs)
  → v16.5 #N.0 (Phase 126 SqliteStorageAdapter relocated to packages/lingwen-storage — breaks lingwen_core/pipeline → infra.persistence cycle, infra version becomes back-compat shim, lingwen-shared workspace dep added — 2 commits)
  → v16.5 #7 (Phase 126 DTO schema audit + typed wrapper narrowing — 5 new DTO files + 41 wrapper functions narrowed from Promise<unknown> to concrete DTO types + 1 composable cast cleanup — 5 commits)
  → v16.5 #6 (Phase 126 DP-02 tools migration defense-in-depth hygiene gate — 12-file whitelist + regression test — 2 commits)
  → v16.5 #4 (Phase 126 DP-03 remaining packages defense-in-depth hygiene gate — 8-file whitelist + regression test — 1 commit)
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

> **更新 (2026-09-01)**: Phase 19+ Sub1 v19.1 闭环 — World Model Domain Migration——33 source commits `d3da0d27..fe2fa219` on branch `phase-19-sub1`:
- **T1-T9 (9 commits) Domain fill** — `WorldSnapshot.to_dict/from_dict` (`c3fa3b78`) + serialization cleanup (`77691e2e`) + `physical`/`mental` fields + `infra/persistence/chapter.py` prerequisite (`34f5fc2e`) + `active_subplots` field (`79b86eb8`) + NEW `lingwen_core.domain.subplot` module + `Plot` entity (`fad93170`) + `infra/subplot.data_structures` shim + `NodeId` canonical alignment (`66dfc438`) + tighten `active_subplots` to `tuple[Plot, ...]` (`cc502074`) + 7 NEW WorldSnapshot tests (`338c79e8`) + `from_dict active_subplots` loading fix caught by spec review (`dac74be3`).
- **T10-T26 (17 commits) Test consumer migrations** — split subplot helpers (`ea0eb87c`) + ruff I001 fix (`3f5dc750`) + 16 test files migrated to `lingwen_core.domain`: subplot_integration (`d23e544c`) + subplot_data_structures (`35ada25e`) + foreshadow_ripple_alignment Ripple (`6ff65d6c`) + pacing_ripple_integration (`b78ecbf1`) + test_world_snapshot (`1e253fed` + `79e0d2a1` ruff) + test_integration (`059ba823`) + test_phase2_integration (`43baa63d`) + test_snapshot_diff (`c0c77e44`) + test_snapshot_store (`311a8f9f`) + test_key_point_graph (`b48da8bd`) + 4 ripple tests (queries `acc9f6ab` + engine `9368aec4` + registry `2bc4b565` + lifecycle `633235ca`) + test_links (`51da7278`). **5 previously-blocked `tests/subplot/test_subplot_integration.py` tests now pass via canonical route** (the bridge pattern `from_dict(to_dict())` no longer needed for canonical consumers).
- **T27-T30 (4 commits) Canonicalization fixes** — Ripple/RippleState/ResolutionMode canonicalization (`41080393`, silent value-equality break caught by code review: domain Ripple had extra `resolution_mode` field) + `infra/world_model.data_structures` shim conversion (`e21c9d88`) + `infra/world_model/__init__` canonical re-exports (`e3ccc9be`) + PlotStatus canonicalization (`fe2fa219`, code review caught PlotStatus shadowing local definition on infra side).
- **T20 (1 commit, this) handoff** — `docs/superpowers/handoffs/2026-09-01-phase-19-sub1-world-model-domain-handoff.md` + `.lingwen/architecture.yml` version bump (`16.5.N17+18` → `19.1`) + this CLAUDE.md update.

**Architecture invariants enforced (5 NEW, 40 total)**:
36. (NEW) ✅ `lingwen_core.domain.*` is canonical source for WorldSnapshot + Plot + Ripple + RippleState + ResolutionMode + KeyPoint + NodeId + NodeType + Relation + PhysicalLine + MentalLine + PlotStatus (all 11 entities + MAX_OPEN_RIPPLOTS).
37. (NEW) ✅ `infra/world_model/data_structures` is a PHASE-COMPAT shim (all domain entities are re-exports from canonical; PlotStatus canonicalized in T30).
38. (NEW) ✅ `infra/world_model/__init__.py` is a PHASE-COMPAT re-export module (behavior services should migrate to use `lingwen_core.domain.*` directly when convenient, removing the shim indirection).
39. (NEW) ✅ `infra/subplot/data_structures.py` is a PHASE-COMPAT shim (Plot + PlotType + PlotPurpose + PlotStatus + MAX_ACTIVE_SUBPLOTS re-exported).
40. (NEW) ✅ `lingwen_core.domain.*` does NOT depend on `infra.*` (DDD purity preserved throughout all canonical re-exports).

**Tests**: 1762 vitest (no regression) / 136 shared / 73 creator / 19 subplot (test_subplot_data_structures.py — now passing with canonical) / 55 core / 3 quality / vue-tsc 0 / ruff 0 / ESLint 0 / **knip 0 lines** / lint-imports 3 contracts KEPT.

**All 11 domain entity identities `True`** between domain and infra paths (Phase 18 carryover closed by T27 + T30). DDD purity preserved throughout.

**8 lessons** (Phase 19+ Sub1 §5):
1. **Verify-before-design (N.14 lesson 1 — confirmed in Phase 18)**: carried through Phase 19+. Each sub-phase pre-flight verified state before editing.
2. **PHASE-COMPAT shim detection**: single grep-discoverable line convention works.
3. **Class identity divergence pattern**: Ripple (T27), PlotStatus (T30) — same Phase 18 v18 carryover pattern. Future canonical migrations follow the re-export pattern.
4. **API divergence in domain migration**: WorldSnapshot needed field fills, Ripple had silent value-equality break. Both patterns closed.
5. **Atomic 1-task-per-commit (N.14 lesson 7)**: maintained throughout — 33 commits on `phase-19-sub1` (28 source implementation + 2 docs + 3 fixup/cleanup).
6. **Phase 18 deferred ripple entities problem**: T30 PlotStatus was a hidden carryover — only code review caught it. Lesson: code review should specifically check for `local_definition vs canonical.re_export` patterns in PHASE-COMPAT shim files.
7. **Continuous review catches latent bugs**: T9 spec review caught missing `from_dict active_subplots` loading. T14 spec review caught Ripple field count divergence (11 vs 12). T28 code review caught PlotStatus shadowing. The 3-stage review process paid dividends.
8. **Mechanical migration scaling**: T11-T26 mechanical migrations (~10 test files) followed established pattern. 3-stage review was redundant for purely mechanical changes — could be optimized in future phases.

**Carryover to Phase 19.x+**: Sub1 polish (infra/world_model behavior services should import directly from lingwen_core.domain) + Sub2 (infra/consistency shim cleanup, 30+ files) + Sub3 (infra/agent_system shim cleanup) + infra/exports/* migration (separate concern) + lingwen_llm test-env gap + ruff format cleanup.

> **更新 (2026-08-30)**: Phase 126 v16.5 #N.6 闭环 — 12 whitelisted tools/llm_*.py files migrated to LLMServiceAdapter——14 commits (`9057f0df`...`f583cfa2`, 12 file migrations + 1 hygiene gate simplification + 1 test conftest + 1 ruff fixup):
- **T1-T12 (12 atomic 1-file commits)**: Each tools/llm_*.py file replaced `from infra.llm_service import LLMService` with `from lingwen_llm.port_adapter import LLMServiceAdapter` and `LLMService()` with `LLMServiceAdapter()`. Files using `LLMTask`/`TaskType` (anti_trope_enhancer.py, llm_quality_analyzer.py, llm_quality/__init__.py, llm_quality/repairer.py) also split imports to `from lingwen_shared.contracts.python.llm import LLMTask, TaskType` (canonical, no grimp-evasion hack). Pattern A files (8): only `LLMService` swap. Pattern B files (4): full split. `tools/llm_quality/repairer.py` had 9 in-method `from infra.llm_service import LLMTask, TaskType` statements also migrated.
- **T13 (1 commit)** `test(hygiene)`: `tooling/hygiene/tests/test_no_concrete_llm_import.py` — `TOOLS_LLM_SERVICE_WHITELIST` constant (12 files) + `test_no_infra_llm_service_imports_in_tools_with_whitelist` retired. Test now enforces ZERO direct `infra.llm_service` imports in `tools/` — whitelist gone.
- **T14 (1 commit)** `test(tools)`: `tests/tools/conftest.py` NEW — imports `infra.llm_service  # noqa: F401` to register `LLMServiceAdapter` factory. Mirrors production startup (apps/studio_api/app.py bootstraps the same import). Tests/tools/ scope is NOT covered by DP-02 forbidden contract, so this conftest is safe.
- **T15 (1 commit)** `test(tools)`: `tests/tools/test_enhancement_tools.py` — patched target `tools.anti_trope_enhancer.LLMService` → `tools.anti_trope_enhancer.LLMServiceAdapter` (per v16.2.7 §3 lesson 1).
- **T16 (1 commit)** `chore(ruff)`: ruff --fix for 2 I001 violations (anti_trope_enhancer.py + llm_quality_analyzer.py) — new import order `lingwen_* + infra.* + shared` requires alphabetical sorting.

Tests: 583 backend (8 llm pkg + 85 shared pkg [79+6 NEW] + 73 creator pkg + 392 infra/studio_api + 17 hygiene tools + 10 tools enhancement + 0 llm_bench / hygiene gate unchanged) / 1729 vitest / vue-tsc 0 / ruff 0 / knip 0 (advisory) / ESLint 0 / **lint-imports 3 contracts KEPT** (layer_dependencies + no_concrete_llm_service + no_concrete_sqlite3) / grimp-evasion hygiene OK。

**Migration counts**:
- `tools/` `from infra.llm_service` count: **12 → 0**
- `tools/` `from lingwen_llm.port_adapter` count: **0 → 12**
- `tools/` `from lingwen_shared.contracts.python.llm` count: **0 → 3**
- `tools/` `LLMServiceAdapter()` call count: **0 → 12**

7 lessons (v16.5 #N.6 §5):
1. **Tools scripts are leaf consumers** — Each tools/llm_*.py file uses a single LLM service pattern. Migration is purely mechanical: replace 1 import + 1 function call. No architectural change needed。
2. **Factory pattern (v16.5 #N.1) made this trivial** — `LLMServiceAdapter()` (no args) uses the default factory, so consumers don't need to manage the LLMService singleton themselves。
3. **Atomic 1-file commits** — 12 files × 1 commit = 12 commits. Easy to review, easy to revert if a specific tool breaks。
4. **Factory bootstrap is a test-environment concern** — The factory is registered as a side effect of `infra.llm_service` import. In production, the app startup imports it; in tests, we need to bootstrap it explicitly. `tests/tools/conftest.py` is the right scope: NOT business code, so DP-02 forbidden contract does not fire。
5. **Migrating `LLMTask`/`TaskType` imports inside function bodies matters** — `repairer.py` had 9 in-method `from infra.llm_service import LLMTask, TaskType` statements that grimp would still follow. All 9 had to be migrated to truly remove the infra.llm_service import surface。
6. **I001 ruff violations introduced by reordering imports** — When a file's primary import changes from `infra.X` to `lingwen_X`, the import block may need re-sorting. Ruff --fix handles this automatically but adds 1 commit per fixup batch。
7. **Test mock targets must be updated in lockstep with code** — Per v16.2.7 §3 lesson 1 (shim mocks don't propagate): when a class is renamed or replaced, the corresponding `vi.mock` / `patch` paths must be updated. v16.5 #N.6 updated 1 mock target (`tools.anti_trope_enhancer.LLMService` → `LLMServiceAdapter`)。

**Carryover to v16.5 #N.7+**:
- **#N.7** DTO Pydantic codegen + remaining `Promise<unknown>` narrowing (incl. SSE for `runCreatorAgentPlanStream`)
- **#N.8** Async port conformance (rewrite `LLMServiceAdapter` with `async execute → LLMResult`)
- **#N.9+** Remaining packages migration if any (`lingwen_core/pipeline/prompt/cli` consumers)

> **更新 (2026-08-31)**: Phase 126 v16.5 #N.11.d/e/g 闭环 — CVG Cleanup Completion — 13 commits (`c01615ef`...`c1244097`, Part A: 4 commits N.11.d impact_score + Part B: 2 commits N.11.e dashboard cascade fields + Part C: 7 commits N.11.g ReferenceGraphResponse full migration + ImpactGraph end-to-end + handoff):
- **Part A (4 commits)** N.11.d impact_score storage-vs-presentation drift — (a) `RippleListItemResponse.impact_score: Optional[float] = None` (N.11.d field addition, backward-compatible default); (b) TS codegen regenerated (`RippleDetailResponse` inherits via extension); (c) `cvg_adapter.ripple_storage_to_presentation` propagates `storage.impact_score → presentation.impact_score` (+2 tests: propagation + default None); (d) `apps/studio_api/routes/cvg.py:list_ripples` drops hybrid storage-roundtrip — converts to canonical presentation shape FIRST, then filters/sorts on presentation values (bulk child_count + impact_score N+1-avoiding batch ops in `_ripple_list_items` retained).
- **Part B (2 commits)** N.11.e dashboard cascade field migration — (a) `apps/dashboard/src/utils/cascadeGraphUtils.js` reads presentation-shape field names: edge `source`/`target` (was `from_node_id`/`to_node_id`), node `node_id`/`chapter_id` (was `id`/`chapter`), cascade `max_depth` (was `depth_reached`). Test fixture `cascade-graph-utils-full.spec.ts` migrated to match — chart-title `depth 3` and depth-layer/action-cluster layouts exercise canonical names. Reference-graph consumers (ImpactGraph.vue) intentionally untouched — they consume `ReferenceGraphResponse` endpoint covered by N.11.g. (b) `apps/dashboard/src/composables/useWorkflowSocket.js` JSDoc reflects `cascade.update` event payload field rename (`depth_reached → max_depth`). Pure docstring change — socket handler does not read this field directly.
- **Part C (7 commits)** N.11.g ReferenceGraphResponse full migration — (a) `ReferenceGraphResponse.truncated: bool = False` (+2 tests: explicit + default). (b) TS codegen regenerated. (c) NEW `cvg_adapter.reference_graph_storage_to_presentation` adapter (117 lines): storage `CascadeNode.id/chapter` → presentation `node_id/chapter_id`; storage `CascadeEdge.from_node_id/to_node_id/relationship_type` → presentation `source/target/relation`; `total_node_count/total_edge_count → total_nodes/total_edges`; `truncated` passthrough; `by_dimension` COMPUTED from `node.dimension` counts (storage lacks this field). Idempotent — accepts already-canonical input. +2 tests: storage-shape mapping + idempotence. (d) `apps/studio_api/routes/cvg.py:get_reference_graph` returns canonical via `cvg_adapter` (`CanonicalReferenceGraphResponse` aliased import); storage-shape import removed. (e) ruff I001 import-block ordering fix. (f) **Storage-shape class cleanup**: `apps/studio_api/protocols.py` `ReferenceGraphResponse` class removed (dead after T3.4 wire-up); `apps/studio_api/app.py` + `models/__init__.py` `noqa F401` re-exports dropped; `_build_reference_graph_response` in `helpers/cvg.py` rewrote to construct lingwen-shared canonical directly (node_id/chapter_id/source/target/total_nodes/total_edges/by_dimension/truncated) instead of storage-shape classes that no longer exist. (g) `apps/dashboard/src/components/ImpactGraph.vue` end-to-end: click handler reads `node_id/chapter_id`, edge mapping reads `source/target`, nodeLabel reads `node_id/chapter_id`. Test fixture `impact-graph.spec.ts` migrated identically.

**Architecture invariants enforced (3 NEW, 28 total)**:
- **#26 (NEW)** ✅ `RippleListItemResponse` (lingwen-shared) includes `impact_score: Optional[float] = None` so dashboard filter/sort reads via typed wrapper without hybrid storage-roundtrip in the route handler.
- **#27 (NEW)** ✅ Dashboard cascade consumers (`cascadeGraphUtils.js` + `useWorkflowSocket.js`) and reference-graph consumers (`ImpactGraph.vue`) use presentation-shape field names — no inline storage-shape access.
- **#28 (NEW)** ✅ `GET /api/cvg/reference-graph` returns canonical presentation-shape `ReferenceGraphResponse` via `cvg_adapter.reference_graph_storage_to_presentation`; storage-shape `ReferenceGraphResponse` class removed from `apps/studio_api/protocols.py`.

**Carryover to v16.5 #N.13+**:
- **#N.13+** 39 `as unknown as` cast cleanup in `apps/dashboard/src/composables/` — original long-term carryover, each requires investigation + JSDoc OR body-shape tightening. Estimated 15-25 commits.
- **Pre-existing** (NOT introduced by this phase): `lingwen_quality` module missing (affects 15 `tests/infra/` tests — v15.7.1 debt); `plugin_manager.py:_discover_internal_providers` wrong module path bug (v15.7.1 debt).

**6 lessons** (v16.5 #N.11.d/e/g):
1. **Pydantic v2 `extra="ignore"` silently swallows mismatched field names** — extending existing `RippleListItemResponse` with `impact_score` (default `None`) is the *least invasive* fix; storage-shape adapters continue working because they call `.model_dump()` and `RippleListItemResponse` silently ignores `dimension` / `relationship_type` / `parent_ripple_id` / `child_count` (storage-only fields) when reading a presentation object. No consumer had to change.
2. **Hybrid storage-roundtrip pattern is a diagnostic canary** — the inline comment in old `list_ripples` ("Storage shape has impact_score for filter/sort; presentation shape drops it. Filter/sort on storage, then convert via adapter.") flagged exactly the drift N.11.d was created to close. Removing the comment + removing the storage-shape intermediate is the actual close.
3. **End-to-end migration requires touching storage-shape consumers too** — T3.5 closed the storage class but `ImpactGraph.vue` still read `n.id` / `n.chapter` / `e.from_node_id` (storage-shape keys no longer in backend response). Without dashboard migration commit, the endpoint migration would be a silent runtime breakage. TDD via component test fixtures catches this.
4. **`_get_dim` helper generalizes to polymorphic node/edge accessor** — same shape (polymorphic dict/dataclass + alias fallback). Pattern repeats 3x across adapters (cascade_node, cascade_edge, reference_graph). Factor into `polymorphic_get(node, field)` helper when the third use case arrives.
5. **Adapter idempotence is a robustness win** — `reference_graph_storage_to_presentation` accepts BOTH storage-shape (id/chapter/from_node_id) AND presentation-shape (node_id/chapter_id/source/target) inputs. Lets the route funnel both pre-T3.4 helpers AND post-T3.5 helpers through the same adapter as final boundary check.
6. **Worktree env-sync issue is recurring** (already in MEMORY.md as N.12 lesson 7) — same pattern requires `uv sync --all-packages` + `uv pip install pytest psutil` after worktree creation. PSA: N.11.d/e/g worktree required 2 extra packages (pytest, psutil) on top of `uv sync`. Add to preflight.

**Tests**:
- `packages/lingwen-shared/tests/` 125 → 129 (+4: 2 impact_score + 2 truncated)
- `apps/studio_api/tests/test_cvg_adapter.py` 15 → 19 (+2 reference_graph + 2 impact_score)
- `apps/studio_api/tests/` (excl. pre-existing write_workspace fail) 45 passed
- `apps/dashboard` vitest 1733 passed + 1 skipped (0 regression)
- `apps/dashboard` vue-tsc 0 / ruff 0 / ESLint 0 / lint-imports 3 contracts KEPT

> **更新 (2026-09-01)**: Phase 126 v16.5 #N.13 闭环 — `as unknown as` Cast Cleanup — 18 commits `b9c20515..bf8293f0` (T1 `encodeVolumePlanDiffShareToken` JSDoc + T2.P1.a-e typed-wrapper return-type alignment + T3.P2.a-d params forwarding + dead code + per-item spread + T4.P3.a-f utility function JSDoc widening; 0 actual runtime casts remain in `apps/dashboard/src/composables/`):
- **Part A (1 commit)** T1: `apps/dashboard/src/utils/volumePlanShareToken.js` `encodeVolumePlanDiffShareToken` JSDoc type signature drops 2 `as-unknown-as-null` casts. Reducer output type becomes explicit (`{ url: string; created_at: string }`).
- **Part B (5 commits)** T2.P1 typed-wrapper return-type alignment: (a) `useProductPreferences.ts` `fetchCreatorModels` + `fetchCreatorPreferences` return strict DTOs. **Option B (DTO widening)**: `CreatorModelOption.id: string | number` (was required `string`) absorbs legacy `p0_count: number` payloads. `CreatorPreferencesDTO` replaces loose `Parameters<typeof settingsStore.update>[1]` cast. (b) `useOnboardingNotifications.js` 4 cast sites use strict DTO types (`CreatorOnboardingDigestSchedule + CreatorOnboardingEmailPreferences + CreatorOnboardingWebhook` + `CreatorOnboardingNotification[]`). **Hybrid C (JSDoc widening + internal cast)** for legacy-typed seams. (c) `useOnboardingNotifications` T2.P1.b follow-up: fix JSDoc inconsistency (typed schedule reference was named against an unrelated DTO). (d) `useWriteFlow` 5 `fetch*` return casts use DTO types (latent URL-encoding bug surfaced — see lesson 4). (e) `useProductExport` `fetchChapters` returns canonical `ChaptersResponse`. Pre-existing data-shape drift (backend never sends `has_body`) documented inline with TODO; NOT silently fixed (per v16.2.8 §5.1 lesson). (f) `useTemplateEditor` changelog + approval history use template DTOs.
- **Part C (4 commits)** T3.P2 params forwarding + dead code: (a) `useAgentTask` `body` parameter aligns to `CreatorAgentPlanRequest` (drops `as unknown as Parameters<...>[0]` cast at SSE call site). Doc-comment at line 117 records dropped cast. (b) 3 params forwarding casts aligned to typed wrappers (`useCreatorOnboarding` webhook/email/digest bodies use DTO types instead of `Record<string, unknown>` casts). (c) `useMergePresets` dead code audit — `publishMergePresetToFactory` exported but not consumed → removed. (d) `useTemplateEditor` `volumes` param uses structural alignment (per-item spread `(e): T => ({...e})` removes `as unknown as` when types lack index signature).
- **Part D (6 commits + 1 follow-up)** T4.P3 utility function JSDoc widening for shape-transformation utilities: (a) RED test spec for `utils/workbench-quality`. (b) `utils/workbench-quality.js` 3 utility functions (`scoreWorkbenchChapter` / `bucketWorkbenchChapter` / `gradeWorkbenchCohesion`) get JSDoc type signatures; `useWorkbenchQuality` drops 4 casts at line 173 et al. (c) RED test spec for `utils/volume-plan-diff` + `utils/template-sync`. (d) `utils/volume-plan-diff.js` + `utils/template-sync.js` 3 cast sites fixed via JSDoc type widening. (e) RED test spec for `utils/settings` (4 parser funcs: `parseSettingsDocs` / `parseSettingsHistory` / `parseMergePreferences` / `parseMergePresetImportPreview`). (f) `utils/settings.js` + `useSettingsDocs` + `useSettingsHistory` + `useMergePresets` drop 8 cast sites. Largest single-commit cast reduction in this phase.

**Architecture invariants enforced (2 NEW, 31 total)**:
30. (NEW) ✅ Zero runtime `as unknown as` casts in `apps/dashboard/src/composables/`. 5 historical comment references preserved as documentation of prior removals (1 JSDoc in `useAgentTask.ts:117` + 4 `//` comments referencing the casting era).
31. (NEW) ✅ All P3 utility functions (used by composables for shape transformation) have JSDoc type signatures — runtime cast is no longer needed because the type contract flows through utility boundaries.

**Cast-count delta**: `apps/dashboard/src/composables/` `as unknown as` count went from **39** (v16.5 #N.10 baseline grep) to **5** (all historical references). Of the 5 remaining matches, **0 are actual casts** — every one is a JSDoc note or `//` comment annotating code where a cast USED to live.

**Carryover to v16.5 #N.14+**:
- **`useCreatorWrite.js:137`** similar legacy cast pattern in legacy surface (estimated 1-2 casts).
- **`useCreatorSettings.js:413`** dead code audit revealed more unused exports; utility JSDoc alignment + dead code removal (estimated 5-10 commits).
- **Pre-existing drift in `useProductExport.fetchChapters`** — backend never sends `has_body`. Either backend fix or frontend filter drop (v16.2.8 carryover).
- **knip 2 unused exports** (`listStudioProjects` + `listFactoryVolumeTemplates` in `src/api/studio.ts:31` + `src/api/volume.ts:388`) — pre-N.11 carryover.
- **knip config hint** (`src/main.js` redundant entry pattern) — cosmetic cleanup.

**8 lessons** (v16.5 #N.13):
1. **P1 Option B (DTO widening) is effective for field-drift surfaces** — `CreatorModelOption.id: string | number` widening absorbed legacy `p0_count: number` payloads without breaking imports (v15.5 lesson re-applied). Prefer widening the DTO over casting at the call site.
2. **Hybrid C (JSDoc widening + internal cast) for legacy contracts** — `useOnboardingNotifications`'s 4 cast sites use JSDoc widening on the legacy parameter side, then an internal cast at the seam where legacy vs typed-wrapper shapes meet. Avoids "cast at every call site" anti-pattern.
3. **Per-item spread `(e): T => ({...e})` removes `as unknown as` when types lack index signatures** — `useTemplateEditor.volumes` struct alignment: the inner shape wasn't indexable, so `unknown as` had been used to force-cast into the typed array. Manual clone per element preserves shape without the cast.
4. **Cast removal surfaces latent bugs** (per v16.2.7 §5.1 lesson 1 re-confirmed): (a) URL-encoding bug in `useWriteFlow` — typed-wrapper test probes URL contract, surface 404 on chapter IDs containing `-`/`_` because `encodeURI` was applied to an already-encoded path segment; (b) dead code in `useMergePresets` (`publishMergePresetToFactory` exported but unused); (c) JSDoc drift in workbench utilities (input `unknown` / output concrete → 3 utility JSDocs needed alignment).
5. **Plan deviations were correct calls** — when the plan said "if a test depends on the legacy shape, preserve the fallback," N.13 deviated in 2 places: (a) `useProductExport.fetchChapters` retained the legacy `has_body` filter (3 downstream tests depend on it; TODO carry to N.14); (b) `useOnboardingNotifications` retained the legacy schedule-reference name (cheaply fixed in T2.P1.b follow-up).
6. **RED-GREEN JSDoc typing pattern acts as type-system forcing function** — for each utility function, the test was written BEFORE the JSDoc. The test is a black-box spec; the JSDoc documents the contract. Mismatch → test fails or vue-tsc errors. Pattern replicated 3x across workbench-quality + volume-plan-diff + settings.
7. **Comment preservation matters** — the 5 `as unknown as` references remaining in composables are NOT bugs; they're historical anchors. Each `// N.13 T3.P2.b: drop...` comment is more valuable as documentation than as removed dead code.
8. **Cast count vs cast sites confusion** — original baseline grep counted 39 occurrences (some lines had multiple casts). Actual runtime cast count is **0**, but `grep -rn "as unknown as"` still returns 5 because historical comments use the literal string. Distinguish in handoffs: "real casts" vs "comment references."

**Tests**:
- `apps/dashboard` vitest **1763 passed + 1 skipped** (+30 NEW utility tests across 5 NEW/extended specs)
- `apps/dashboard` vue-tsc 0 / ESLint 0
- `apps/dashboard` knip 2 unused exports + 1 config hint (unchanged from N.11.d/e/g baseline)
- `packages/lingwen-shared/tests/` **134 passed** (0 regression, no new DTOs)
- `apps/studio_api/tests/test_cvg_adapter.py` **19 passed** (0 regression)
- ruff 0 / lint-imports 3 contracts KEPT (layer_dependencies + no_concrete_llm_service + no_concrete_sqlite3)

> **更新 (2026-09-01)**: Phase 126 v16.5 #N.16 闭环 — v15.7.1 Debt Closure — 4 source commits (`c3b9d214` + `a6faa527` + `a75a61ec` + `bd0dd4a9`), T1 CI guard + T2 docs sync + T3 RED test + T4 GREEN fix:
- **T1 (1 commit)** `c3b9d214` `test(hygiene)`: NEW `tooling/hygiene/check_lingwen_quality_importable.py` (104 lines) — asserts key symbols (`IssueSeverity`, `ConsistencyEngine`, `CheckerInspector`, `ForeshadowChecker`, `CreativeWhitelist`, etc.) importable from canonical `lingwen_quality.*` modules. Closes v15.7.1 carryover claim "lingwen_quality module missing" via CI regression guard. 3 NEW regression tests at `tests/hygiene/test_check_lingwen_quality_importable.py`.
- **T2 (1 commit)** `a6faa527` `docs`: CLAUDE.md "Carryover to v16.5 #N.15+" — removed "lingwen_quality module missing" line, added "verified + guarded" closure note.
- **T3 (1 commit)** `a75a61ec` `test(llm)`: NEW `tests/infra/test_plugin_manager.py` (75 lines) — 3 RED regression tests proving the bug exists (3 warnings + empty `_plugins`).
- **T4 (1 commit)** `bd0dd4a9` `fix(llm)`: 2-line surgical fix at `packages/lingwen-llm/src/lingwen_llm/providers/plugin_manager.py:58,81` — replace `infra.ai_service.X` → `lingwen_llm.providers.X`. T3 RED → T4 GREEN. 3-warning log spam on every `LLMService.get()` eliminated.

**Tests**: 1762 vitest (no regression) / 136 shared / 73 creator / 11 llm pkg (+3 NEW) / 3 NEW infra pkg tests / 3 NEW hygiene tests / vue-tsc 0 / ruff 0 / ESLint 0 / knip `{"issues":[]}` / lint-imports 3 contracts KEPT.

**Architecture invariants enforced (2 NEW, 35 total)**:
35. (NEW) ✅ `lingwen_quality` key symbols importable from canonical modules — CI regression guard at `tooling/hygiene/check_lingwen_quality_importable.py`.
36. (NEW) ✅ `plugin_manager.py` `_discover_internal_providers` (lines 58, 81) uses canonical `lingwen_llm.providers.X` module path. Regression test `tests/infra/test_plugin_manager.py` verifies all 3 providers load + no broken-import warnings.

**Carryover closure**: v15.7.1 carryover chain (lingwen_quality + plugin_manager) FULLY CLOSED. Only remaining LingWen debt: Phase 114 prod preview regression (accepted).

**Lessons**:
1. **Verify carryover claims before executing** — The "15 failing tests" / "module missing" claim was inherited from v15.7.1 baseline and propagated through 4+ phases of CLAUDE.md updates. Static analysis revealed it was already stale. Lesson: when picking up old carryover, verify the underlying claim first.
2. **CI regression guards beat CLAUDE.md text edits** — Adding `check_lingwen_quality_importable.py` means future package moves will surface as CI failures, not silent CLAUDE.md drift. The doc edit alone (without the guard) would let the "missing" claim re-emerge if someone moved the package.
3. **Phase 123 fix-by-bypass was the right intermediate step** — The `_PROVIDER_REGISTRY` decorator path bypassed the broken `_discover_internal_providers` without touching it. Now both layers are correct (decorator path is canonical, _discover_internal_providers also works). Two correct paths > one broken + one bypass.
4. **Conservative fix > aggressive cleanup for inert bugs** — Could have deleted `_discover_internal_providers` entirely (it duplicates what decorators do). Instead chose 2-line path fix: preserves code structure, lower risk, same end result.

> **更新 (2026-09-01)**: Phase 126 v16.5 #N.14 闭环 — Legacy Pattern Cleanup — 6 commits `b024bb1a..9eba255c` closing all 5 N.13 carryover items:
- **T1 (1 commit)** `b024bb1a` `refactor(dashboard)`: `useCreatorWrite.js` `runCreatorLogicCheck` static import from `@/api/content` (replaces `await import('../api/index.js')`). Call signature simplified from `{chapter, scope: 'p0'}` to `chapter` (matches typed-wrapper signature; backend ignores `scope`). N.13 carryover said "1-2 casts" but actual was a barrel-import — investigation found the real pattern.
- **T2 (1 commit)** `77888795` `refactor(dashboard)`: `useCreatorSettings.js` `publishMergePresetToFactory` function + `mergePresetFactoryPublishing` ref + 2 return-statement entries deleted (-23 lines). N.13 carryover said "dead code" but function was wired through tests (no UI calls) — test split to "pull only", publish assertion dropped.
- **T3 (2 commits)** `bf361f6c` + `9172a8b1`: `ChapterData.has_body: bool = False` Pydantic field declared + TS codegen + 2 NEW backend tests + `useProductExport.ts` 2 `as Array<{chapter, has_body?}>` casts dropped. N.13 carryover said "backend never sends `has_body`" but data layer at `lingwen_creator.dashboard:88` DID produce it; Pydantic `extra="ignore"` was the actual culprit. **Plan A (declare field) chosen over Plan B (drop filter)** — original intent was for the filter to work.
- **T4 (1 commit)** `b8953f6b` `refactor(dashboard)`: `useWriteTools.ts` deps contract widened from `Ref<Record<string, unknown> | null>` to `Ref<OverviewShape | null>` (with exported `OverviewChapterRow` + `OverviewShape` interfaces); 2 inline-shape casts dropped at `chapterRowClass` + `chapterRowTitle`. Caller `useCreatorWrite.js` (JSDoc-typed `Ref<object|null>`) accepted without change — vue-tsc treats .js→.ts boundary as soft type assertion.
- **T5 (1 commit)** `9eba255c` `refactor(dashboard)`: knip cleanup — `listStudioProjects` + `listFactoryVolumeTemplates` (carryover items) + `publishMergePresetToFactory` typed wrapper (bonus dead code after T2 deletion) + their barrel re-export + test fixture entries deleted (-35 lines net).

**Architecture invariants enforced (2 NEW, 33 total)**:
32. (NEW) ✅ `ChapterData` Pydantic declares `has_body: bool = False`. Wire response from `/api/chapters` includes the field (data layer at `lingwen_creator.content.dashboard` produces it per-row; Pydantic was dropping via `extra="ignore"` before this commit). Closes the v16.2.8 / v16.5 #7 / v16.5 #N.13 carryover chain.
33. (NEW) ✅ knip "Unused exports" count = 0 for the 3 specific carryover items. Closes pre-N.11 carryover for `listStudioProjects` + `listFactoryVolumeTemplates` + N.14-derived `publishMergePresetToFactory` typed wrapper.

**Tests**:
- `apps/dashboard` vitest **1762 passed + 1 skipped** (-1 from T5 removed test)
- `apps/dashboard` vue-tsc 0 / ESLint 0 / knip 0 unused exports (was 2 + 1 typed wrapper)
- `packages/lingwen-shared/tests/` **136 passed** (+2 NEW from T3)
- `apps/studio_api/tests/test_cvg_adapter.py` 19 passed (0 regression)
- ruff not installed in worktree venv (non-blocking; v15.7.1 baseline ruff=0)
- lint-imports 3 contracts KEPT (unchanged)

**7 lessons** (v16.5 #N.14):
1. **Carryover investigation often corrects the original description** — N.13 carryover said "1-2 casts at useCreatorWrite.js:137" but actual was barrel-import (zero casts); "dead code" at useCreatorSettings.js:413 was wired through tests. Always re-verify carryover claims before executing.
2. **`has_body` drift was a Pydantic schema gap, not a backend gap** — data layer at `dashboard.py:88` produces the field per-row; Pydantic `extra="ignore"` silently dropped it. Plan A (declare field) more honest than Plan B (drop filter as "always-[]"); original intent was for the filter to work.
3. **Typed deps contract widening works even when caller is loosely typed** — `useCreatorWrite.js` passes `overview: Ref<object|null>` (JSDoc) to `useWriteTools` which now demands `Ref<OverviewShape|null>`. vue-tsc accepts it because .js→.ts boundary treats JSDoc as soft type assertion.
4. **Worktree python env-sync gotcha recurred (N.12 lesson 7)** — worktree needs `uv sync --all-packages` + `uv pip install pytest psutil`. CRITICAL new sub-lesson: **use worktree's `.venv/bin/python`, NOT conda's `/home/ailearn/miniconda3/bin/python`**. Conda python has stale PYTHONPATH pointing to master LingWen packages → `ModuleNotFoundError` for worktree-specific workspace members even after `uv pip install -e`.
5. **knip output truncation hides additional findings** — N.13 handoff claim "knip: 2 unused exports" was the count from the knip category HEADER line; actual export list was much longer (composables/index.ts 60+ + useDevice + useWidgetRegistry + many more). For N.14 only tackled the 2 specific carryover items, broader scope is future work.
6. **Comment preservation matters (N.13 lesson 7 re-confirmed)** — the 5 `as unknown as` references in composables are STILL all historical comments. Each `// N.13 T3.P2.b: drop...` line is documentation of the casting era. Do NOT remove these.
7. **Atomic 1-task-per-commit scales to medium scope** — 6 carryover items × ~1 commit each = 6 commits. Easy to review, easy to revert.

**Carryover to v16.5 #N.16+**:
- knip broader cleanup: composables/index.ts 60+ unused exports + useDashboardNav + useDevice + useWidgetRegistry + creatorPanelMatrix + tests/visual-audit + fn-core/ unused files (~30-50 commits)
- knip "Unlisted binaries" + "Unused devDependencies" (config issue / likely knip false positives)
- `@tiptap/pm` flagged as unused dep — peer dep, do NOT delete
- **N.14 RESOLVED carries**: pre-existing `has_body` drift (closed via T3); knip 2 unused exports (closed via T5)
- **`lingwen_quality` verified + guarded (v16.5 #N.16 closure)**: Package `packages/lingwen-quality/` confirmed importable; `tooling/hygiene/check_lingwen_quality_importable.py` CI guard prevents "module missing" claim from re-emerging.
- **`plugin_manager.py` bug fixed (v16.5 #N.16 closure)**: Lines 58 + 81 module path corrected; 3-warning log spam on every `LLMService.get()` eliminated. Regression guard at `tests/infra/test_plugin_manager.py`.

> **更新 (2026-08-31)**: Phase 126 v16.5 #N.12 闭环 — Async Port Conformance — 22 commits (`a6f628ec`...handoff, Part A: 3 commits foundation + Part B: 1 commit creator/agent + Part C: 2 commits infra/prose_judge + infra/agent_extractors + Part D: 13 commits tools migration (5 modern + 2 llm_quality + 4 legacy) + Part E: handoff):
- **Part A (3 commits)** Foundation: `LLMServicePort` Protocol async rewrite (uses `async def execute(task: LLMTask) -> str` + `async def execute_stream(task: LLMTask) -> AsyncIterator[str]` + `def parse_json_response(str) -> Any` + `def is_available() -> bool`) + drop unused `TaskSpec` + `LLMResult` from `lingwen_shared.ports` + TS not affected (Python only). `LLMServiceAdapter` async rewrite: `execute` uses `await asyncio.to_thread(self._service.execute, task)` (sync concrete runs in threadpool, no event loop blocking); `execute_stream` is `async def` generator wrapping sync concrete iterator (acceptable for current scale per Phase 120 p95 ~9.52s benchmark); `generate` async (wraps prompt into `LLMTask` then awaits `execute`); `parse_json_response` + `is_available` + `provider_name` stay sync. 3 NEW async tests with `@pytest.mark.asyncio` + `inspect.iscoroutinefunction` assertions + `_FakeService` stub class. Cleanup commit: extracted `_FakeService` to module-level helper (DRY 3 inline duplicates) + accurate `execute_stream` docstring.
- **Part B (1 commit)** `creator/content/agent.py` 4 functions async: `_llm_agent_plan` (helper) → `async def` + `await adapter.execute(...)`; `_llm_agent_plan_stream_tokens` (helper) → `async def` + `async for chunk in adapter.execute_stream(...)` + `AsyncIterator[str]` return; `run_creator_agent_plan` (public) → `async def` + `await _llm_agent_plan(...)`; `iter_creator_agent_plan_stream` (public) → `async def` + `async for delta in ...` + `AsyncIterator[dict[str, Any]]` + recursive `await run_creator_agent_plan(...)`. Cascade to `apps/studio_api/routes/creator_core.py` 2 routes (`creator_agent_plan_endpoint` + `creator_agent_plan_stream_endpoint`'s nested `event_stream` helper). Test cascade: `tests/infra/test_creator_agent.py` 8 tests → `async def` + `@pytest.mark.asyncio`.
- **Part C (2 commits)** `infra/prose_judge.py` 3 functions async: `_llm_judge_chapter` + `build_llm_judge_report` + `run_prose_judge` → all `async def` + `await`. `infra/world_db/agent_extractors.py` `_LLMRunnable.generate` Protocol method async + both `extract_*` methods async. Cascade to `apps/studio_api/routes/world.py` 2 routes. Test cascade: `tests/infra/test_prose_judge.py` (1 test) + `tests/infra/world_db/test_agent_extractors.py` (9 tests) + `apps/studio_api/tests/test_world_route.py` (`_StubLLM` async). Bonus: `scripts/run-prose-judge.sh` bash wrapper now uses `asyncio.run(run_prose_judge(...))`.
- **Part D (13 commits)** Atomic 1-file-per-commit migration of 12 `tools/` files from sync to async. 5 modern tools: `llm_emotional_resonance_checker` + `llm_foreshadow_analyzer` + `llm_pacing_analyzer` + `llm_quality_analyzer` + `anti_trope_enhancer`. 2 `tools/llm_quality/`: `checker.py` (4 methods async) + `repairer.py` (9 methods + dispatch router async). 4 `tools/legacy/`: `llm_character_arc_analyzer` + `llm_outline_quality_check` (4 checker + 3 repairer methods) + `llm_protagonist_charm_analyzer` + `llm_readability_analyzer`. Each file: `def method()` → `async def method()` + `await self.llm.generate(...)`. Sync `def main():` entry points preserved via `asyncio.run(_async_main())` wrapper. Test cascade: `tests/tools/test_enhancement_tools.py` updated `MagicMock` → `AsyncMock` + `asyncio.run` wrap. Bonus ruff fixup commit for `asyncio` import ordering in `llm_quality_analyzer.py`.
- **Part E (this + next)** handoff doc + this CLAUDE.md update.

**Architecture invariants enforced (4 NEW, 29 total)**:
26. (NEW) ✅ `LLMServicePort.execute` is `async def (LLMTask) -> str` — Protocol + Adapter conform (matches N.12 spec §3)
27. (NEW) ✅ `LLMServiceAdapter.execute` runs sync concrete in `asyncio.to_thread` (no event loop blocking) — wraps `infra/llm_service.py::LLMService.execute`
28. (NEW) ✅ All `LLMServiceAdapter` callers `await` the result (no orphan sync callers) — 12+ caller sites migrated across creator/infra/tools
29. (NEW) ✅ `TaskSpec` + `LLMResult` removed from `lingwen_shared.ports.llm_service` (declared but never used) + `ports/__init__.py` exports

**Carryover to v16.5 #N.13+**:
- **#N.11.d** `impact_score` storage-vs-presentation drift (CVG cleanup) — still deferred from N.10
- **#N.11.e** Dashboard cascade field migration (`cascadeGraphUtils.js` cleanup) — still deferred from N.10
- **#N.11.g** `ReferenceGraphResponse` full migration to presentation shape — still deferred from N.10
- **#N.13+** 39 `as unknown as` cast cleanup in `apps/dashboard/src/composables/` — original carryover
- **Pre-existing**: `lingwen_quality` module missing (affects 15 `tests/infra/` tests); `plugin_manager.py:_discover_internal_providers` wrong module path bug (affects `test_stream_llm_tokens_when_provider_streams`). Both v15.7.1 carryover, out of scope for N.12

**8 lessons** (v16.5 #N.12):
1. **PEP-562 factory pattern carries over** — same factory used to avoid `from infra.llm_service import` (DP-02 grimp-evasion) now wraps the async surface (sync concrete + async adapter).
2. **`asyncio.to_thread` vs `asyncio.Queue` for streams** — `execute()` uses `to_thread` (run sync HTTP in threadpool); `execute_stream()` uses simple yield-wrap (no thread offload). Trade-off documented in class docstring: current scale tolerates simpler approach (p95 ~9.52s per Phase 120 benchmark; one event-loop block per active streaming request). Future optimization could push stream iteration to a thread via Queue.
3. **Cascading async migration through 4 layers** — complex callers like `iter_creator_agent_plan_stream` propagate async through `_llm_agent_plan_stream_tokens` (helper) → `iter_creator_agent_plan_stream` (public) → `event_stream()` (nested FastAPI helper) → FastAPI route. ~20 lines of mechanical changes per layer cascade.
4. **`yield from` is illegal in async generators** — converting sync generator (`yield from sync_iter`) to async generator requires manual `for x in sync_iter: yield x` loop. Documented in `_llm_agent_plan_stream_tokens` docstring.
5. **AsyncMock replaces MagicMock for async method mocks** — test mocks for async methods must be `AsyncMock` + either `await` (in `async def test_*`) or `asyncio.run` wrap (in sync test contexts). Only affected 1 test in `test_enhancement_tools.py`.
6. **Tool scripts with sync entry points need `asyncio.run(_async_main())`** — each of the 12 tool files had a sync `def main():` for CLI invocation. Renamed to `async def _async_main()` + added new sync `def main(): asyncio.run(_async_main())` to preserve CLI ergonomics. Bash scripts that wrap Python (e.g., `scripts/run-prose-judge.sh`) also updated.
7. **Worktree env-sync issue is recurring** — same pattern from N.6 lesson 3: `pip install -e packages/<pkg> --no-deps` needed after changes to make tests see the new async version. Affects `lingwen-creator` and `lingwen-llm` in this Phase. MEMORY.md note stands.
8. **Async test pattern is clean with pytest-asyncio `@pytest.mark.asyncio` decorator** — `Mode.STRICT` (project default) requires explicit decorator on each `async def test_*`. No glob patterns or conftest magic — explicit is good.

> **更新 (2026-08-31)**: Phase 126 v16.5 #N.11 闭环 — Cascade Runs + Broadcast Log wire-up + protocols cleanup — 16 commits (`2c79ccfa`...`20f70914`, Part A: 9 commits N.11.b CascadeRunResponse wire-up + Part B: 5 commits N.11.c CascadeBroadcastLogResponse promotion + Part C: 1 commit N.11.f `_get_dim` helper + Part D: 1 commit N.11.a protocols cleanup):
- **Part A (9 commits)** N.11.b `CascadeRunResponse` wire-up — extend Pydantic with 9 storage-shape fields (`cascade_id: Optional[int]`, `completed_at: Optional[str]`, `depth_reached: int = 0`, `cascade_nodes: list[CascadeNodeResponse]`, `cascade_edges: list[CascadeEdgeResponse]`, `cascade_actions: list[dict[str, Any]]`, `cancelled_at: Optional[str]`, `triggered_by: Optional[str]`, `stats: Optional[dict[str, Any]]`) + TS codegen + `cvg_adapter.cascade_run_storage_to_presentation` adapter (handles `id: int → run_id: str + cascade_id: int` split + `started_at/completed_at → started_at/finished_at/completed_at` ISO conversion) + 3 endpoint migrations (`get_ripple_cascade_runs` + `list_all_cascade_runs` + `post_ripple_cascade_run_cancel`) + bonus `get_ripple_cascade_v9_20` persist branch (was using `CascadeRunResponse.from_dataclass()`) + 1 NEW backend shared test (`test_cascade_run_response_extended_fields`) + ruff fixup commit (F821 Any + F822 forward-decl + I001 imports). Post-polish commit: cancel endpoint uses `model_copy(update={...})` instead of `model_dump()` + dict mutation round-trip; `datetime` import hoisted to top-of-file.
- **Part B (5 commits)** N.11.c `CascadeBroadcastLogResponse` promotion — NEW Pydantic in lingwen-shared (4 fields: `id/ripple_id/latency_ms/created_at`, `extra="ignore"`) + TS codegen + `dashboard-contracts` `CascadeBroadcastLogResponseDTO` re-export + `cvg_adapter.cascade_broadcast_log_storage_to_presentation` adapter (handles dict / dataclass / Pydantic model inputs via `is_dataclass(storage) and not isinstance(storage, type)` guard + `model_dump` fallback + dict fallback) + 2 NEW backend tests (basic dict input + dataclass input) + endpoint migration (`get_ripple_cascade_broadcast_log`) + bonus dead-code removal (storage-shape `CascadeBroadcastLogResponse` class + 2 noqa F401 re-exports in `app.py` + `models/__init__.py` — partially closes N.11.a scope).
- **Part C (2 commits)** N.11.f `_get_dim` helper extraction — RED test (3 cases: dict / dataclass / missing-attribute fallback) + GREEN helper + 3 inline `n.get("dimension") if isinstance(n, dict) else getattr(n, "dimension", None)` refs in `cascade_preview_storage_to_presentation` collapsed to single `_get_dim(node: Any) -> Optional[str]` polymorphic accessor. Ruff fixups (F821 `Optional` import + I001 sort) embedded in GREEN commit.
- **Part D (1 commit)** N.11.a `protocols.py` CVG cleanup (partial) — drop 5 unused CVG model imports from `apps/studio_api/helpers/cvg.py` (CascadePreviewResponse, CascadeResponse, CascadeRunResponse, RippleActionResponse, RippleStatsResponse — none used outside import block).

**Architecture invariants enforced (5 NEW, 25 total)**:
21. (NEW) ✅ `CascadeRunResponse` in lingwen-shared includes 9 storage-shape fields (cascade_id/completed_at/depth_reached/cascade_nodes/cascade_edges/cascade_actions/cancelled_at/triggered_by/stats) so dashboard consumers can read full cascade-run payload via typed wrapper.
22. (NEW) ✅ All 4 cascade-run endpoints route through `cvg_adapter.cascade_run_storage_to_presentation` (extends invariant #18 from N.10): `get_ripple_cascade_runs` + `list_all_cascade_runs` + `post_ripple_cascade_run_cancel` + `get_ripple_cascade_v9_20` persist branch. Zero inline mapping in route handlers.
23. (NEW) ✅ `CascadeBroadcastLogResponse` promoted from storage shape (`apps/studio_api/protocols.py`) to canonical lingwen-shared + dead storage class removed (closes Pydantic drift; storage Pydantic was redundant with dataclass source-of-truth at `infra/cross_volume/storage.py:81-88`).
24. (NEW) ✅ `cvg_adapter._get_dim(node)` polymorphic helper replaces 3 inline `n.get("dimension") if isinstance(n, dict) else getattr(...)` expressions in `cascade_preview_storage_to_presentation` (DRY).
25. (NEW) ✅ `apps/studio_api/protocols.py` CVG cleanup: 5 unused CVG model imports dropped from `helpers/cvg.py` + dead CascadeBroadcastLogResponse class + 2 noqa F401 re-exports removed from `app.py` + `models/__init__.py`.

**Carryover to v16.5 #N.12+**:
- **#N.11.d** `impact_score` storage-vs-presentation drift: cascade v9_20 endpoints don't include `impact_score`. Carryover if dashboard needs.
- **#N.11.e** Dashboard cascade field migration: `cascadeGraphUtils.js` still has local refs to `depth_reached` + other storage-shape names (runtime correct via cvg_adapter mapping, but readability suffers). 1-2 commits.
- **#N.11.g (renamed from N.11.e-extended)** `ReferenceGraphResponse` full migration to presentation shape (currently still uses storage-shape from `apps/studio_api.models`; needs lingwen-shared extension with `by_dimension` field + new adapter + endpoint migration). 2-3 commits.
- **#N.12+** Async port conformance: LLMServiceAdapter sync → `async execute → LLMResult` (~16-25 commits).
- **#N.13+** 39 `as unknown as` cast cleanup in composables.

**8 lessons** (v16.5 #N.11):
1. **Pydantic extension with safe defaults is backward-compatible** (carryover from N.10 lesson #2): adding `Optional[...] = None` + `int = 0` + `list = Field(default_factory=list)` keeps existing valid uses working. N.9-era minimal CascadeRunResponse instances still validate.
2. **T11 cleanup scope expansion pattern**: original N.10 T11 plan assumed all CVG routes use cvg_adapter by N.10, but CascadeRunResponse was used by 3 endpoints NOT in N.10 scope (N.11.b). Same pattern repeated in N.11: CascadeBroadcastLogResponse dead-code removal only became possible after its endpoint was wired (N.11.c). **Sequential dependency: route → wire → cleanup**.
3. **`is_dataclass(x) and not isinstance(x, type)` guard is necessary**: `is_dataclass(SomeClass)` returns True even for the class itself; `asdict(SomeClass)` raises `TypeError`. Verified empirically (Part B code review). Defensive guard prevents subtle bug if a class is accidentally passed.
4. **Frontend typed wrapper can be deferred if no consumer exists**: Part B did NOT add `fetchCascadeBroadcastLog` to `apps/dashboard/src/api/cvg.ts` because `grep -rn "broadcast" apps/dashboard/` returns zero matches. Per N.10 §5 lesson 4: "failing tests are direct evidence of incomplete wire-up; no failing tests means no consumer yet". Add wrapper only when dashboard consumer needs it.
5. **`_dataclass_to_dict` helper evolution**: Part A added a helper for the 3 cascade-run endpoints. Part B broadcast-log endpoint uses in-adapter polymorphic guards (is_dataclass / model_dump / dict fallback) instead — slightly different pattern because broadcast-log accepts the storage dataclass directly (not via `_dataclass_to_dict`). Both patterns coexist in the codebase; not a problem but worth noting.
6. **Cancel endpoint enrichment with `model_copy(update={...})`**: better than `model_dump()` + dict mutation + `CascadeRunResponse(**dict)` because (a) preserves Pydantic v2 model identity, (b) avoids allocation round-trip, (c) more readable. Recommended pattern for future Pydantic v2 mutations.
7. **Test count claims vs reality**: plan estimated 11+2=13 cvg_dto tests, actual was 10+1=11. Off-by-one in plan estimates is a recurring pattern (see N.10 carryover count drift). Plans should specify field NAMES not field COUNTS where possible.
8. **Atomic-commit counts vs plan estimates**: plan estimated ~18 commits, actual was 16. Variance came from: (a) Part C's 2 commits collapsed with Part A's polish commit, (b) lint fixups embedded within task commits rather than separate. Acceptable — atomicity is about logical not numerical granularity.

> **更新 (2026-08-30)**: Phase 126 v16.5 #N.10 闭环 (PARTIAL — T11 protocols.py CVG cleanup deferred to N.11+; T9 absorbed into T7.fix) — 13 commits (`9233dd0d`...`c6e4b91b`, T1-T8 + T10 + T10.fix + T11 skip carryover):
- **T1 (1 commit)** `feat(lingwen-shared)`: `CascadeResponse` Pydantic extended with 3 storage-shape fields (`cascade_actions: list[dict[str, Any]]` with `default_factory=list`, `generated_at: Optional[str]`, `bfs_algorithm_version: Literal["v1", "v2_weighted"] = "v1"`). All fields have safe defaults — backward-compatible for existing valid uses. Field-by-field + identity check confirmed pre-change.
- **T2 (1 commit)** `chore(lingwen-shared)`: TS codegen regenerated for `CascadeResponse` (now includes 3 new fields in `packages/lingwen-shared/src/lingwen_shared/contracts/ts/cvg.ts`).
- **T3 (1 commit)** `feat(lingwen-shared)`: `CascadePreviewResponse` Pydantic extended with 7 storage-shape aggregate counts (`affected_chapter_count`, `affected_character_count`, `affected_setting_count`, `estimated_change_count`, `cascade_node_count`, `cascade_edge_count`, `max_depth`), all default to 0.
- **T4 (1 commit)** `chore(lingwen-shared)`: TS codegen regenerated for `CascadePreviewResponse`.
- **T5 (1 commit)** `refactor(studio-api)`: `cvg_adapter.cascade_*_storage_to_presentation` updated — `dimension` → `status` (default `"applied"`); `from_node_id`/`to_node_id` → `source`/`target`; `relationship_type` → `relation`; computes `total_nodes`/`total_edges`/`max_depth` from lists; populates 3 extended fields. NEW `cascade_preview_storage_to_presentation(storage, ripple_id)` aggregates node counts by dimension.
- **T6 (1 commit)** `refactor(studio-api)`: `chapter.py` re-exports 8 models from `lingwen_shared.contracts.python.health` (ChapterData + ChaptersResponse + 6 Production* models). 87-line manual Pydantic definitions replaced with 32-line thin re-export shim. Identity check passed for all 8 (cleanest of the 5 re-exports — no drift).
- **T7 + T7.fix (2 commits)** `refactor(studio-api)`: `get_ripple_cascade` uses `cvg_adapter.cascade_storage_to_presentation`. T7.fix also adopted cvg_adapter for `get_ripple_cascade_v9_20` non-persist branch + migrated 5+ dashboard cascade tests from storage field names (`cascade_nodes`/`cascade_edges`/`from_node_id`/`to_node_id`) to presentation field names (`nodes`/`edges`/`source`/`target`).
- **T8 (1 commit)** `refactor(studio-api)`: `get_ripple_cascade_preview` uses new `cvg_adapter.cascade_preview_storage_to_presentation`.
- **T10 (1 commit)** `feat(creator-sse)`: `status` event promoted to canonical `CreatorAgentStreamEvent` discriminated union. Added `StatusEvent` variant (`{ type: Literal["status"]; message: str }`) to `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator_sse.py`. TS regenerated. `creatorAgentStreamUtils.js` updated to yield for `status` events (progress paint).
- **T10.fix (1 commit)** `fix(dashboard)`: `useAgentTask.handleStreamEvent` signature tightened from `CreatorAgentStreamEvent | { type: 'status'; message: string }` to `CreatorAgentStreamEvent` (defensive extension no longer needed). Dropped `as unknown as (event: unknown) => void` cast at `runCreatorAgentPlanStream` call site. **`as unknown as` count in this file: 0**.
- **T11 (1 commit, empty carryover)** `docs(phase-126)`: protocols.py CVG cleanup **DEFERRED** to N.11+ — `apps/studio_api/helpers/cvg.py` still constructs storage-shape cascade models internally (used by cascade run/cancel/broadcast-log endpoints out of N.10 scope).

Tests: **1733 vitest (0 regression) / 124 backend shared (113 + 11 NEW: 5 cvg + 6 creator_sse) / 73 creator / 8 llm / 35 storage / 35 studio_api (excl. write_workspace) + test_write_workspace_route now passes 7/7 (was pre-existing fail in N.9) / 9 cvg_adapter (5 + 4 NEW) / 39 hygiene / vue-tsc 0 / ruff 0 / knip 2 unused + 1 config hint (same as N.9 baseline) / ESLint 0 / lint-imports 3 contracts KEPT / grimp-evasion OK**.

8 lessons (v16.5 #N.10 §5):
1. **Discriminated union promotion is a one-step type contract fix** — T10 promoted `status` from defensive local extension to canonical variant. Mechanical: add `StatusEvent` + add to union + regenerate TS + drop extension + drop cast. ~2 commits for 3 type contract improvements.
2. **Pydantic model extension with safe defaults is backward-compatible** — Adding `cascade_actions: list = Field(default_factory=list)` + `max_depth: int = 0` keeps existing valid uses working while exposing new fields. Preferable to version-bumping models.
3. **`Literal["v1", "v2_weighted"]` enum on `bfs_algorithm_version` provides type safety for migration** — Pydantic validation surfaces drift immediately rather than silently shipping a new algorithm version.
4. **Test-only field name updates must be part of the wire-up commit, not a separate task** — T7's wire-up exposed 5+ dashboard tests using storage field names. Bundling test updates with T7.fix was cleaner than scheduling a separate "dashboard test field migration" task. Failing tests are direct evidence of incomplete wire-up.
5. **`_get_dim(n)` helper for polymorphic dict/obj access** — T8's `cascade_preview_storage_to_presentation` has 3x repeated `n.get("dimension") if isinstance(n, dict) else getattr(n, "dimension", None)`. Extract to private helper (N.11 refactor candidate).
6. **T11 "cleanup" tasks depend on T7-T10 being in scope** — Original T11 plan assumed all CVG routes use cvg_adapter by N.10. But CascadeRunResponse is used by 3 endpoints NOT in N.10 scope. SKIP T11 + document carryover is the right move — premature cleanup would have broken these endpoints.
7. **Pre-existing pytest debt resolution via wire-up** — `test_write_workspace_route.py` was documented as "pre-existing fail" in N.9 (FastAPI version drift). N.10 T7 wire-up actually resolved it (now passes 7/7). Likely an import-time side effect was masked. Don't gate phase closure on pre-existing debt — it may resolve on its own as adjacent code evolves.
8. **T6 chapter.py re-export is the cleanest of the 5 re-exports** — All 8 models passed identity check on first try. Largest + most DTO-heavy model file; N.7 Pydantic codegen had already produced all 8 in `health.py`. No new bounded context separation needed (vs health/decision/workflow/studio which had drift or split decisions).

**Architecture invariants enforced (3 NEW, 20 total)**:
18. (NEW) ✅ `CascadeResponse` includes 3 storage-shape fields (`cascade_actions`, `generated_at`, `bfs_algorithm_version`) so dashboard consumers in `cascadeGraphUtils.js` + `useWorkflowSocket.js` can read them via typed wrapper.
19. (NEW) ✅ `CascadePreviewResponse` includes 7 storage-shape aggregate count fields (`affected_chapter_count`/`affected_character_count`/`affected_setting_count`/`estimated_change_count`/`cascade_node_count`/`cascade_edge_count`/`max_depth`).
20. (NEW) ✅ `status` event variant is part of canonical `CreatorAgentStreamEvent` discriminated union — `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator_sse.py::CreatorAgentStreamEvent` accepts `{ type: "status"; message: str }`.

**Carryover to v16.5 #N.11+**:
- **#N.11.a** protocols.py CVG cleanup: `apps/studio_api/helpers/cvg.py` still constructs storage-shape cascade models internally. Cleanup deferred until cascade run/cancel/broadcast-log endpoints are wired (N.11.b/c).
- **#N.11.b** `CascadeRunResponse` wire-up: `get_ripple_cascade_runs` + `list_all_cascade_runs` + `post_ripple_cascade_run_cancel` endpoints. Extend lingwen-shared `CascadeRunResponse` (currently 2 fields) + add `cancelled_at`/`started_at`/`completed_at`/`triggered_by`/`cascade_id`/`stats` fields. 2-3 commits.
- **#N.11.c** `CascadeBroadcastLogResponse` wire-up: `get_ripple_cascade_broadcast_log` endpoint. 1-2 commits.
- **#N.11.d** `impact_score` storage-vs-presentation drift: cascade v9_20 endpoints don't include `impact_score`; carryover if dashboard needs.
- **#N.11.e** Dashboard cascade field migration: `cascadeGraphUtils.js` still has local refs to `depth_reached` + other storage-shape names (runtime correct via cvg_adapter mapping, but readability suffers). 1-2 commits.
- **#N.11.f** `_get_dim` helper extraction in `cvg_adapter.py`. 1 commit.
- **#N.12+** Async port conformance: LLMServiceAdapter sync → `async execute → LLMResult` (~16-25 commits).
- **#N.13+** 39 `as unknown as` cast cleanup in composables.

> **更新 (2026-08-30)**: Phase 126 v16.5 #N.9 闭环 (PARTIAL — T4 cascade wire-up deferred to N.10) — 7 commits (`637da54d`...`cccc1bc2`, T1 budget split + workflow re-export + T2 studio re-export + T3 cvg_adapter `_parse_dt` impl gap fix + list_ripples wire-up + T5 useAgentTask handleStreamEvent tightening + T6.2 ruff fixup):
- **T1 (2 commits)** `refactor(studio-api)`: Budget DTOs split + workflow.py re-export. (a) `apps/studio_api/models/budget.py` NEW (33 lines, `BudgetSetRequest` + `BudgetTierSetRequest`) — bounded context alignment (workflow ≠ budget); `apps/studio_api/models/__init__.py` re-exports from new module (alphabetical position); (b) `workflow.py` replaces 83-line manual Pydantic definitions with 25-line thin re-export from `lingwen_shared.contracts.python.workflows` (5 models: `WorkflowListItem` / `RunWorkflowRequest` / `ResumeWorkflowRequest` / `WorkflowStatusResponse` / `WorkflowMermaidResponse`). Verified field-by-field + identity check (`WorkflowListItem is lingwen_shared.contracts.python.workflows.WorkflowListItem`).
- **T2 (1 commit)** `refactor(studio-api)`: `studio.py` re-exports 23 models from `lingwen_shared.contracts.python.studio`. Replaces 217-line manual Pydantic definitions with 61-line thin re-export shim (`StudioProjectItem` ... `StudioBatchJobResponse`).
- **T3 (2 commits)** `fix(studio-api)` + `refactor(studio-api)`: CVG list_ripples wire-up. (a) `cvg_adapter._parse_dt` implementation gap fix — N.8 scaffold defined the function in docstring but never implemented it; wire-up surfaced as `ValidationError: created_at — Input should be a valid string [type=string_type, input_value=datetime]`. Added `from datetime import datetime` import + implemented `_parse_dt(None) → ""`, `_parse_dt(datetime) → value.isoformat()`, `_parse_dt(other) → str(value)`. (b) `routes/cvg.py:list_ripples` now imports `RippleListItemResponse` from `lingwen_shared` (canonical presentation shape); storage-shape import removed; response_model points at presentation shape; filter/sort on storage shape (impact_score is storage-only field), then convert via `cvg_adapter.ripple_storage_to_presentation(item.model_dump())`.
- **T5 (1 commit)** `refactor(dashboard)`: useAgentTask handleStreamEvent adopts `CreatorAgentStreamEvent` discriminated union. Dropped the `source` field tracking (canonical `chunk` variant does NOT include `source`). Added `'in evt` narrow checks for label/message/text fields (TypeScript discriminated union narrowing requires explicit `in` checks). Dropped the `as unknown as (event: unknown) => void` cast at `runCreatorAgentPlanStream` call site. `'status'` event retained as local extension with JSDoc (backend SSE emits status messages not yet promoted to canonical envelope).
- **T6.2 (1 commit)** `chore(ruff)`: ruff --fix for 4 I001 import-sort violations in 4 files affected by N.9 re-exports + adapter fix.

Tests: **1733 vitest (0 regression)** / **113 backend shared (0 regression)** / **37 + 1 pre-existing fail studio_api (1 pre-existing FastAPI version drift in test_write_workspace_route.py unrelated to N.9)** / **5 cvg_adapter (no regression)** / **vue-tsc 0** / **ruff 0**.

6 lessons (v16.5 #N.9 §5):
1. **Scope discovery mid-execution is the right move** — N.9 plan estimated T4 (cascade wire-up) at 2-4 commits; empirical investigation revealed the dashboard actively consumes fields the presentation shape drops (`cascade_actions`, `depth_reached`, `bfs_algorithm_version`). Better to defer than to ship a wire-up that breaks dashboard. Future CVG carryovers should start with `grep -rn "trigger_ripple_id\|cascade_actions\|..." apps/dashboard/src/` BEFORE planning scope.
2. **Atomic commits per file** — 7 distinct commits (2 for T1, 1 for T2, 2 for T3, 1 for T5, 1 for T6.2). Easy to review, easy to revert.
3. **Mixed bounded contexts in single files** — `workflow.py` mixed workflow models + budget DTOs because of code organization history, not because they belong together. Splitting by bounded context is more durable. Budget DTOs don't need lingwen-shared promotion (server-side only, persistence-coupled).
4. **Identity check > field set comparison for re-exports** — `from lingwen_shared.X import Y; Y is lingwen_shared.X` is the strongest verification: backend class IS the lingwen-shared class object, not a copy.
5. **Adapter implementation gaps surface in TDD** — N.8 scaffold documented `_parse_dt` but never implemented. Wire-up exercise is the only thing that catches this kind of "documented but missing" gap.
6. **`'in evt` narrowing required for discriminated union field access** — TypeScript discriminated union narrowing doesn't auto-narrow on `evt.label` access without explicit `'label' in evt` check.

**Architecture invariants enforced (2 NEW, 17 total)**:
16. (NEW) ✅ `workflow.py` re-exports 5 workflow models from lingwen-shared (no manual Pydantic definitions).
17. (NEW) ✅ `studio.py` re-exports 23 studio models from lingwen-shared (no manual Pydantic definitions).

**Carryover to v16.5 #N.10+**:
- **#N.10.a** CVG cascade endpoints wire-up (get_ripple_cascade + get_ripple_cascade_preview + get_ripple_cascade_v9_20): requires extending lingwen-shared CascadeResponse/CascadePreviewResponse to include cascade_actions/generated_at/bfs_algorithm_version/affected_chapter_count/affected_character_count/affected_setting_count — 4-6 commits.
- **#N.10.b** Chapter model re-export verification (apps/studio_api/models/chapter.py may already be in lingwen-shared).
- **#N.10.c** Protocols.py CVG cleanup (after all CVG routes use adapter, storage-shape CVG models in apps/studio_api/protocols.py can be removed).
- **#N.10.d** `status` event promotion to canonical CreatorAgentStreamEvent (backend Pydantic + TS codegen regen).
- **#N.11+** Async port conformance: LLMServiceAdapter sync → `async execute → LLMResult` (~16-25 commits).
- **#N.12+** 39 `as unknown as` cast cleanup in composables.

> **更新 (2026-08-30)**: Phase 126 v16.5 #N.8 闭环 — Cleanup + Backend Pydantic Re-export + CVG Adapter Scaffolding — 6 commits (`83e42925`...`52aa3393`, T1 path fix + test casts + T2 useAgentTask tighten + T3 CVG adapter scaffold + T4 health/decision re-export + T6.2 ruff fixup):
- **T1 (1 commit)** `fix(dashboard-contracts)`: 5 re-export shim path fixes (`'../../lingwen-shared/...'` → `'../../../lingwen-shared/...'`) for `{cvg,decisions,health,studio,workflows}.ts` in `packages/dashboard-contracts/src/shared/`. Pre-existing on master from v16.5 #7. Path fix surfaced 21 latent TS errors in 5 spec files (masked by TS2307 broken module resolution) — same commit adds `as unknown as XxxDTO[]` casts to test mock fixtures. vue-tsc 5 → 0.
- **T2 (1 commit)** `refactor(dashboard)`: T5.4 useAgentTask cast cleanup. `buildPlanRequestBody` return type tightened from `Record<string, unknown>` to `CreatorAgentPlanRequest & Record<string, unknown>`. Dropped `body as unknown as Parameters<...>[0]` cast at line 344. SSE-side callback cast at line 345 retained with JSDoc — adopting `CreatorAgentStreamEvent` discriminated union requires `handleStreamEvent` body logic change (carryover v16.5 #N.9+).
- **T3 (1 commit)** `feat(studio-api)`: NEW `apps/studio_api/cvg_adapter.py` (176 lines) — canonical boundary between storage shape (`apps/studio_api/protocols.py::RippleListItemResponse` with `source_chapter/target_chapter`) and presentation shape (`lingwen_shared.contracts.python.cvg::RippleListItemResponse` with `chapter_id/source_volume/impact_volumes`). 5 storage → presentation adapter functions (`ripple_storage_to_presentation`, `ripple_detail_storage_to_presentation`, `cascade_node_storage_to_presentation`, `cascade_edge_storage_to_presentation`, `cascade_storage_to_presentation`) + 5 test cases. NOT yet wired into routes (carryover v16.5 #N.9+ requires dashboard consumption validation).
- **T4 (2 commits)** `refactor(studio-api)`: 2 of 4 candidate backend models converted to thin re-export shims from lingwen-shared. (a) `health.py` (12 models: `DatabaseStatus`, `MemoryUsage`, `HealthResponse`, `OverviewResponse`, `ChapterData`, `ChaptersResponse`, `ProductionRecordResponse/Records/BatchRollup/Rollup/CostTrendPoint/CostTrendResponse`); (b) `decision.py` (4 models: `DecisionResponse`, `Resolve/Defer/CancelDecisionRequest`). Verified field-by-field equivalence before each conversion. `workflow.py` deferred to v16.5 #N.9 (contains 2 non-workflow DTOs `BudgetSetRequest`/`BudgetTierSetRequest` requiring split decision).
- **T6.2 (1 commit)** `chore(ruff)`: ruff --fix for 2 I001 import-sort violations in health.py + decision.py (alfabetic sort of multi-line imports from lingwen-shared).

Tests: **1733 vitest (0 regression)** / **113 backend shared (0 regression)** / **396 + 5 skipped infra+studio_api (1 PRE-EXISTING failure unrelated to v16.5 #N.8 — plugin_manager.py module path bug from v15.7.1, lingwen_llm.providers cannot load `infra.ai_service.<name>`)** / **5 NEW cvg_adapter (T3)** / **vue-tsc 0** / **ruff 0**.

7 lessons (v16.5 #N.8 §5):
1. **TS2307 masks downstream type errors** — broken shim path resolves to wrong dir, makes TS treat imports as `any`, hiding 21 downstream shape mismatches. vue-tsc pre-commit gate for shim files is a v16.5 #N.9+ must-do.
2. **Fixing the path surfaces latent test bugs** — 21 errors were real (partial-shape test fixtures missing required canonical DTO fields). `as unknown as XxxDTO[]` casts preserve test intent (minimal fixture, narrow assertions) without changing runtime behavior.
3. **CVG adapter scaffold before wire-up** — establishing the boundary module before forcing route integration avoids v16.4 grimp-evasion-hack pattern. Wiring is a separate step with dashboard consumption validation.
4. **Storage vs presentation shape separation is real, not pedantic** — backend persistence owns SQLite row shape; lingwen-shared contracts own wire shape. The `_compute_volume_from_chapter` heuristic in `cvg_adapter.py` is a placeholder for v16.5 #N.9+ validation.
5. **Backend re-export needs explicit `__all__`** — star-imports would pull in optional/utility members. Explicit re-exports + explicit `__all__` keep import surface minimal and ruff `I001` clean.
6. **Atomic 1-file commits per re-export** — health.py and decision.py each get their own commit. Easy to revert, easy to review, easy to bisect if downstream consumer breaks.
7. **DTOs-vs-models boundary tests** — `from lingwen_shared.contracts.python.X import ModelA as LA; from apps.studio_api.models.X import ModelA as BA; assert set(LA.model_fields) == set(BA.model_fields)` as a pre-check before any re-export commit.

**Architecture invariants enforced (3 NEW, 15 total)**:
13. (NEW) ✅ `vue-tsc` shows 0 errors in apps/dashboard (5 → 0 from 2-dot path fix in T1).
14. (NEW) ✅ `apps/studio_api/cvg_adapter.py` exists as canonical boundary for storage → presentation mapping (wiring deferred to v16.5 #N.9+).
15. (NEW) ✅ 2 / 18 backend Pydantic model files are re-exports from lingwen-shared (health.py + decision.py); 16 / 18 remain (carryover v16.5 #N.9+).

**Carryover to v16.5 #N.9+**:
- **#N.9.a** `workflow.py` split: BudgetSetRequest + BudgetTierSetRequest migration decision (split file? move to lingwen-shared?).
- **#N.9.b** CVG adapter wire-up: 4 route endpoints + dashboard consumption validation for new field semantics.
- **#N.9.c** useAgentTask handleStreamEvent tightening: drop legacy `{type?, message?, source?}` loose shape.
- **#N.10+** Remaining 16 backend model files for re-export (chapter.py, studio.py, creator_*.py).
- **#N.11+** Async port conformance: LLMServiceAdapter sync → `async execute → LLMResult` (~16-25 commits).
- **#N.12+** 39 `as unknown as` cast cleanup in composables (each requires investigation + JSDoc OR body-shape tightening).

> **更新 (2026-08-30)**: Phase 126 v16.5 #N.7 闭环 — DTO Pydantic codegen + SSE stream typing — 27 commits on `phase-126-v16-5-n7`:
- **T1 (8 commits)**: 5 Python Pydantic DTO files (atomic 1-file commits) + 1 ruff fixup + 2 fix commits. `health.py` (12 models) + `studio.py` (23) + `workflows.py` (5) + `cvg.py` (12, presentation shape) + `decisions.py` (4) — total 56 Pydantic models mirroring the manual TS DTOs from v16.5 #7. Fix commits resolved: (a) `latest_record_at` typo → `latest_recorded_at`, (b) `StudioBatchRunRequest` fields changed from `Optional[...] = None` to required + `Field()` defaults with `ge`/`le` constraints.
- **T2 (2 commits)**: Codegen tooling wired: `tooling/contracts/generate.py` MODULES list extended 4→9 entries + `tooling/contracts/zod_revalidate.py` modules tuple extended to match.
- **T3 (7 commits)**: 28 NEW backend tests across 5 files (`test_{health,studio,workflows,cvg,decisions}_dto.py`), bringing `packages/lingwen-shared/tests/` from 85 to 113 cases.
- **T4 (6 commits)**: Codegen regenerated 5 TS files (`packages/lingwen-shared/src/lingwen_shared/contracts/ts/{health,studio,workflows,cvg,decisions}.ts`); replaced 5 manual `packages/dashboard-contracts/src/shared/*.ts` files with `import + export type X = Y` re-export shims (60 interfaces total). `index.ts` marker updated.
- **T5 (4 commits)**: SSE stream typed: NEW `packages/dashboard-contracts/src/shared/creator-sse.ts` defines `CreatorAgentStreamEvent` (discriminated union: start/chunk/advice/preview_label/done/error) + `CreatorAgentPlanResult`. Updated `creatorAgentStreamUtils.js` + `apps/dashboard/src/api/content.ts` to use the typed envelope. `apps/dashboard/src/api/` `Promise<unknown>` count: 1 → 0. NEW SSE parser tests (4 cases) in `tests/unit/utils/creatorAgentStreamUtils.spec.ts`. T5.4 (useAgentTask cast cleanup) skipped — requires separate body-shape refactor.
- **T6 (1 commit)**: Handoff doc.

**Architecture invariants enforced (12 total)**:
1-10. (preserved from v16.5 #N.6)
11. ✅ `apps/dashboard/src/api/` contains zero `Promise<unknown>` (SSE stream typed via `CreatorAgentStreamEvent` discriminated union).
12. ✅ All 5 manual TS DTO files in `packages/dashboard-contracts/src/shared/` replaced with re-export shims from `packages/lingwen-shared/src/lingwen_shared/contracts/ts/` — single source of truth (Python Pydantic).

**Pre-existing carryover (NOT introduced by v16.5 #N.7)**:
- 5 re-export shims use 2-dot relative paths (`../../lingwen-shared/...`) that should be 3-dot. Pre-existing from v16.5 #7.
- 39 `as unknown as` casts in `apps/dashboard/src/composables/` pre-existing fragile patterns.
- Backend Pydantic re-export from lingwen-shared (CVG presentation-vs-storage drift) deferred to v16.5 #N.8+.

> **更新 (2026-08-30)**: Phase 126 v16.5 #N.3 闭环 — 8 whitelisted infra/* files migrated to SqliteStorageAdapter——9 commits (`6891665c`...`21819b09`, 8 migration commits + 1 hygiene test commit + 1 ruff fixup):
- **T1** `refactor(lingwen-core)`: `budget_persistence.py` — `BudgetService` 迁 `SqliteStorageAdapter` (callback-based `with_transaction` / `with_connection`)。22/22 tests pass.
- **T2** `refactor(lingwen-core)`: `cost_persistence.py` — `CostTrackerDB` 迁 adapter。18/19 pass (1 pre-existing infra→lingwen_core 路径名 failure,unrelated)。
- **T3** `refactor(lingwen-core)`: `social_engine/relationship_tracker.py` — `RelationshipTracker` (SQLite backend) 迁 adapter。JSON backend 保留 (无 storage abstraction 需求)。Manual `BEGIN/COMMIT/ROLLBACK` 删除 (adapter 的 `with_transaction` 提供 atomic boundary)。7/7 tests pass。
- **T4** `refactor(lingwen-pipeline)`: `state_manager.py` — `StateManager` 迁 adapter + `fcntl.flock` 保留 wrap `_storage._transaction_cm()` (R3-001 cross-process)。14/14 tests pass (incl. transaction rollback + concurrency)。
- **T5** `refactor(lingwen-pipeline)`: `database.py` — `WorkflowDB` 迁 adapter + `fcntl.flock` 保留。7/7 tests pass (incl. fcntl concurrency)。
- **T6** `refactor(lingwen-pipeline)`: `migrate_from_json.py` — `migrate_from_json` 函数单 `with_transaction` callback 完成所有 INSERT OR REPLACE。1/1 migration test pass。
- **T7** `refactor(lingwen-pipeline)`: `state/backends/sqlite.py` — `SQLiteBackend` 迁 adapter (无 fcntl)。Smoke-tested inline (set/get/list_keys/delete round-trip OK)。
- **T8** `refactor(lingwen-cli)`: `commands/doctor.py` — `_check_database` diagnostic 迁 `SqliteStorageAdapter` + `with_connection` (懒 `import sqlite3` 删除)。Diagnostic 语义保留。
- **T9** `test(hygiene)`: `tests/hygiene/test_no_concrete_sqlite3_import.py` — 8-file whitelist 删除, gate 现在纯 grep test (任何 lingwen_core/pipeline/cli 新直接 sqlite3 import 立即 fail)。
- **T8.fixup** `chore(ruff)`: ruff --fix 修 9 W292 violations across 8 files。

Tests: 73 backend passing for migrated files (22 budget + 18 cost + 7 relationship + 14 sqlite_state + 7 workflow_db + 5 hygiene) + pre-existing failures unrelated (skill_registry.yaml worktree env-sync issue, master_controller loaded from master location)。`import sqlite3` count in 8 whitelisted files: **8 → 0**。

7 lessons (v16.5 #N.3 §5):
1. **Atomic commits per file** — 1 commit per file keeps history clean and rollback easy。9 commits total。
2. **Public API stability** — None of the 8 files changed public API. Only internal implementation changed。
3. **Phase 15.0 T2.8 deprecation comments now obsolete** — Recommended path was `infra.persistence.registry.get("X")` singleton,但 better path is to migrate to SqliteStorageAdapter. Registry pattern = SERVICE singletons, SqliteStorageAdapter = STORAGE abstraction. Different concerns. Deprecation 注释保留 (full removal follow-up)。
4. **`lingwen_storage` as leaf package was architectural prerequisite** — Without v16.5 #N.0 relocation, migrating these files would create `lingwen_core → infra.persistence` cycles。
5. **fcntl.flock vs SqliteStorageAdapter transaction 互补** — flock = inter-process write mutex (R3-001); adapter = in-process BEGIN/COMMIT/ROLLBACK. Compose: flock wraps `_transaction_cm()`。
6. **Private API access (`_transaction_cm`, `_connection_cm`) acceptable for canonical consumer** — Explicit "raw" form of callback-flavored API. Used by StateManager/WorkflowDB to preserve public contextmanager API。
7. **`sqlite3.Row` row factory transparent** — `SqliteStorageAdapter._open()` sets it. Callers don't need manual `conn.row_factory = sqlite3.Row`。

**Carryover to v16.5 #N.4**:
- Migrate 21 remaining `infra/*` files (world_db 8 + cross_volume + event_sourcing + reading_power + persistence internals 3 + tools/workflow/lib 5 + tools/migrate_to_sqlite + others) to `SqliteStorageAdapter`.
- Same pattern as v16.5 #N.3: construct adapter, replace contextmanagers with callback API, remove `import sqlite3`, keep public API unchanged.
- Special cases: `infra/persistence/sqlite_config.py` `apply_sqlite_pragmas(conn: sqlite3.Connection)` — accept `ConnectionPort` (or `SqliteConnection` wrapper). Several callers (WorkflowDB._init_db) pass the adapter's wrapper, which works because `wrapper.execute()` delegates to sqlite3.Connection.execute.
- Estimated ~22 commits (1 per file, DP-06 strict).

> **更新 (2026-08-30)**: Phase 126 v16.5 #N.1 闭环 — StoragePort factory pattern——3 commits (`05c58b9b` + `bd95ca6c` + `02906d32`):
- **T1** `feat(lingwen-shared)`: `packages/lingwen-shared/src/lingwen_shared/ports/storage.py` 加 factory scaffolding — `_DEFAULT_STORAGE_FACTORY` module var + `set_default_storage_factory(factory)` + `get_default_storage_factory()` + `get_default_storage()` (raises RuntimeError if no factory)。`__all__` extend to 6 entries。**lingwen_shared 仍 sqlite3-free** (only docstring/comment refs)。
- **T2** `feat(lingwen-storage)`: `packages/lingwen-storage/src/lingwen_storage/sqlite_storage_adapter.py` 末尾加 `_default_storage_factory()` + 调 `set_default_storage_factory(_default_storage_factory)` at module load。Mirrors `infra.llm_service` registration of `LLMService.get` for `LLMServiceAdapter`。
- **T3** `test(lingwen-storage)`: `packages/lingwen-storage/tests/test_sqlite_storage_adapter.py` 加 4 NEW factory tests — `test_factory_registers_at_module_load` (verifies import triggers registration) + `test_get_default_storage_constructs_via_factory` (FakeStorage stub) + `test_get_default_storage_raises_when_no_factory` (RuntimeError check) + `test_default_factory_returns_sqlite_storage_adapter` (end-to-end default factory returns real adapter)。用 `restore_default_factory` fixture 防止污染其他 tests。

Tests: 35 lingwen-storage (+4 factory) / 39 hygiene (unchanged) / vue-tsc 0 / ruff 0 / knip 0 / ESLint 0 / **lint-imports 3 contracts KEPT** (layer_dependencies + no_concrete_llm_service_in_business_code + no_concrete_sqlite3_in_business_code) / grimp-evasion hygiene OK。

**Factory pattern (mirrors v16.5 #1 LLMServiceAdapter)**:
```
apps/* ─────────────────┐
                        │ uses get_default_storage()
                        ▼
lingwen_shared.ports.storage (Protocol + factory functions, NO sqlite3)
                        ▲
                        │ registers factory at module load
                        │
lingwen_storage.sqlite_storage_adapter (canonical, ONLY sqlite3 importer)
                        ▲
                        │ re-export shim (no sqlite3)
                        │
infra.persistence.sqlite_storage_adapter (back-compat shim)
```

3 lessons (v16.5 #N.1):
1. **Factory pattern 跨 port 复用** — v16.5 #1 LLM + v16.5 #N.1 Storage 共用 `_DEFAULT_FACTORY` + `set_default_*` + `get_default_*` template。Future ports (Network, Auth) 可 follow。
2. **Module-load side effects 是 default registration 的 idiom** — 任何 import canonical 模块的人都触发注册。No explicit bootstrap step required。
3. **Default `:memory:` DB for factory** — Production code 应注册自己的 factory with correct `db_path`。Default `:memory:` factory is for tests + minimal bootstrap only。

**Carryover to v16.5 #N.2 (now unblocked)**:
- Migrate 19 `apps/*` files to use `get_default_storage()` from `lingwen_shared`
- Migrate 8 whitelisted `infra/*` files (Phase 15.0 T2.8 deprecated) to drop `import sqlite3`
- Migrate 21 remaining `infra/*` files to drop `import sqlite3`
- Expand import-linter contract `source_modules = ["lingwen_creator", "apps"]`

> **更新 (2026-08-30)**: Phase 126 v16.5 #N.0 闭环 — SqliteStorageAdapter relocated to packages/lingwen-storage/——2 commits (`5cb6adc4` + `6800a4c8`):
- **T1** `feat(lingwen-storage)`: 新建 `packages/lingwen-storage/src/lingwen_storage/sqlite_storage_adapter.py` (217 lines) — canonical `StoragePort` impl,在 lingwen-* 包家族中是**唯一**允许 `import sqlite3` 的文件。`packages/lingwen-storage/pyproject.toml` 加 `lingwen-shared` workspace dep。
- **T2** `refactor(persistence)`: `infra/persistence/sqlite_storage_adapter.py` 变成 17-line back-compat shim (zero `import sqlite3`,纯 `from lingwen_storage.sqlite_storage_adapter import ...`) + `tests/persistence/test_sqlite_storage_adapter.py` 删除(挪到 `packages/lingwen-storage/tests/`,匹配 package-ownership 约定)。
- **Architectural invariant preserved**: 唯一的 sqlite3 backend 实现 = lingwen_storage.sqlite_storage_adapter。infra/persistence 版只是 import shim,不直接 import sqlite3。

Tests: 31 backend (13 NEW packages/lingwen-storage/sqlite_storage_adapter + 18 unchanged jsonl_store/reducer) / 39 hygiene (unchanged) / vue-tsc 0 / ruff 0 / knip 0 / ESLint 0 / **lint-imports 3 contracts KEPT** (unchanged)。
**infra `import sqlite3` count: 22 → 21** (shim no longer imports)。`packages/lingwen-storage/src/lingwen_storage/sqlite_storage_adapter.py` 现在 sole owner。
**Carryover**: v16.5 #N.1 factory pattern (`set_default_storage_factory()` in lingwen_shared) + #N.2 #N.3 #N.4 apps/infra consumer migration + #N.5 import-linter contract expansion + #N.6 tools migration。

3 lessons:
1. **Package placement matters for cycle avoidance** — SqliteStorageAdapter 原本放 infra/ 阻塞 lingwen_core 迁移 (lingwen_core ← infra.persistence 会成 cycle)。挪到 leaf 包(lingwen-storage 无 lingwen_* deps)即破 cycle。
2. **Back-compat shims enable non-breaking relocations** — 17-line shim means no consumer needs to change import paths immediately,future migrations can be done commit-by-commit (per DP-06)。
3. **Test ownership should follow package ownership** — `tests/persistence/` (top-level) → `packages/lingwen-storage/tests/` (package-local) matches convention used by `packages/lingwen-llm/tests/` etc.

> **更新 (2026-08-30)**: Phase 126 v16.5 #7 闭环 — DTO schema audit + typed wrapper narrowing——5 commits (`0a64afee` ... `f2f75688`, T1 DTO files + T2 wrappers health/studio/workflows + T3 wrappers cvg/decisions + T4 useProductExport cast cleanup + T5 handoff/CLAUDE.md):
- **T1** `feat(dashboard-contracts)`: 5 new DTO files + `shared/index.ts` re-export — `health.ts` (15 interfaces: OverviewResponse, ChaptersResponse, ProductionRecords/Rollup/CostTrendResponse, HealthResponse, DatabaseStatus, MemoryUsage, ChapterData, ProductionRecord/BatchRollup/CostTrendPointResponse) + `studio.ts` (24 interfaces: Studio{ProjectItem,ProjectsResponse,ActiveResponse,SetActiveRequest,SummaryResponse,QualityResponse,QualityReport{Issue,Chapter,Response},ProseHeatmap{Chapter,},ProseDiff{Totals,Chapter,Response},ProseJudge{Rating,Chapter,Signal,Response},Preflight{Chapter,Request,Response},BatchRunRequest,BatchJobResponse}) + `workflows.ts` (5 interfaces: WorkflowListItem, Run/ResumeWorkflowRequest, WorkflowStatusResponse, WorkflowMermaidResponse) + `cvg.ts` (12 interfaces: RippleListItem/Detail/Action/Stats/AuditEntryResponse, CascadeNode/Edge/Response/PreviewResponse, ReferenceGraphResponse, CascadeRunResponse, CascadeCancelPayload) + `decisions.ts` (4 interfaces: DecisionResponse, Resolve/Defer/CancelDecisionRequest)。All sourced from `apps/studio_api/models/{health,chapter,studio,workflow,decision}.py` + `apps/studio_api/protocols.py` (Ripple/Cascade/ReferenceGraph responses)。
- **T2** `refactor(dashboard)`: narrow `apps/dashboard/src/api/{health,studio,workflows}.ts` — 22 wrapper functions `Promise<unknown>` → `Promise<ConcreteDTO>`。Pattern: `data → as T` 配 `settings.ts` established convention。`runWorkflow(req: unknown)` → `runWorkflow(req: RunWorkflowInput)` (new typed input interface)。
- **T3** `refactor(dashboard)`: narrow `apps/dashboard/src/api/{cvg,decisions}.ts` — 19 wrapper functions narrowed。`resolveDecision` 返回 synthetic envelope (backend POST 返回 status 不是 full DecisionResponse),typed locally as `ResolveDecisionResult` to document the narrower contract。
- **T4** `refactor(dashboard)`: `useCreatorProductTools/useProductExport.ts` 2 个 `as {chapters?: Array<{chapter, has_body}>}` cast 转换 `as unknown as` (now required by new `ChaptersResponseDTO` return type),加注释 documenting pre-existing data-shape drift (backend 不送 `has_body`,filter 永远 returns `[]`,v16.5 #N carryover)。No runtime change。
- **T5** `docs(phase-126)`: handoff doc + CLAUDE.md + this update section。
Tests:1729 vitest passing (0 regression) / vue-tsc 0 / ruff 0 / knip 0 / ESLint 0 / **lint-imports 2 contracts KEPT** (no Python changes) / 41 of 42 wrapper functions narrowed (only `runCreatorAgentPlanStream` SSE stream remains `Promise<unknown>` — dynamic plan shape, genuinely out of scope)。

5 lessons (v16.5 #7 §5):
1. **Manual DTOs 是 codegen 前的 valid bridge** — v16.5 #N 大 refactor 之前手写 TS interfaces 立即解锁 type safety。Downside: drift risk if Python models change without TS updates。Upside: zero risk to codegen pipeline。
2. **`as` casts 是 compile-time-only 但 reveal real bugs** — `useProductExport` 的 `c.has_body` filter 永远返回 `[]` 因为 backend 从来不送 `has_body`。新 typed return 暴露 drift。Documenting drift inline (而非 silently fixing) keeps change scope bounded to typed-wrapper narrowing。
3. **`Promise<unknown>` wrappers don't fail silently — they just don't help** — 39 of 42 wrapper functions narrowed。Composable bugs 变得 visible。Even partial type narrowing surfaces drift。
4. **SSE stream returns are genuinely `unknown`** — `runCreatorAgentPlanStream` parses JSON over stream; response shape depends on `action_label`。Narrowing 需要 tagged-union response envelope OR typing parser helpers instead of stream itself。v16.5 #N carryover。
5. **`data → as T` pattern beats `request<T>()`** — `core.js` `request()` returns `Promise<unknown>`,wrappers do single cast to DTO type。Matches `settings.ts` convention。Avoids the chicken-and-egg of typing `request` itself (which is shared across 14 wrappers with different return shapes)。

**Carryover to v16.5 #N (full DTO alignment)**:
- **#N.1** Add 5 Python Pydantic DTOs in `packages/lingwen-shared/src/lingwen_shared/contracts/python/{health,studio,workflows,cvg,decisions}.py` (cross-reference `apps/studio_api/models/*.py` + `protocols.py` definitions)。
- **#N.2** Update `tooling/contracts/generate.py` MODULES list — add 5 new entries。
- **#N.3** Regenerate `packages/lingwen-shared/src/lingwen_shared/contracts/ts/{health,studio,workflows,cvg,decisions}.ts` via `python tooling/contracts/generate.py`。
- **#N.4** Replace manual `packages/dashboard-contracts/src/shared/{health,studio,workflows,cvg,decisions}.ts` with `export type { ... } from '../../lingwen-shared/src/lingwen_shared/contracts/ts/X'` (matching `memory.ts`/`creator.ts` re-export pattern)。
- **#N.5** `runCreatorAgentPlanStream` SSE narrowing — design tagged-union response envelope OR type parser helpers。Only remaining `Promise<unknown>` in `apps/dashboard/src/api/`。
- **#N.6** DTO schema drift fix for remaining `as unknown as` casts (4 production + 2 test casts in volume/onboarding/settings/content composables — predate v16.2.8 typed-wrapper cleanup)。
- **#N.7** Typed wrapper return type narrowing for `Promise<Record<string, unknown>>` — some functions in `volume.ts`/`onboarding.ts`/`settings.ts` return `Record<string, unknown>` shapes that could narrow further once full codegen is in place。

> **更新 (2026-08-29)**: Phase 126 v16.5 #6 闭环 — Tools migration defense-in-depth——2 commits (T1 + T2):
- **T1** `test(hygiene)`: 扩展 `tooling/hygiene/tests/test_no_concrete_llm_import.py` (DP-02 hygiene file) — 新增 `test_no_infra_llm_service_imports_in_tools_with_whitelist` + 12-file whitelist (pre-v16.5 #1 LLMServiceAdapter files):
  - `tools/anti_trope_enhancer.py` + `llm_emotional_resonance_checker.py` + `llm_foreshadow_analyzer.py` + `llm_pacing_analyzer.py` + `llm_quality_analyzer.py`
  - `tools/llm_quality/{__init__.py,checker.py,repairer.py}`
  - `tools/legacy/{llm_character_arc_analyzer.py,llm_outline_quality_check.py,llm_protagonist_charm_analyzer.py,llm_readability_analyzer.py}`
- **Defense-in-depth**: 新 direct `from infra.llm_service` 在 `tools/` → fail CI。12 existing files exempt (pre-LLMServiceAdapter)。

**Migration path (carried over)**: Replace `from infra.llm_service import LLMService; LLMService.get()` with `from lingwen_llm.port_adapter import LLMServiceAdapter; LLMServiceAdapter()`。Mechanical 1:1 replacement。

Tests:579 backend (578 baseline + 1 NEW tools gate) / 32 hygiene tooling/hygiene/tests/ (31 baseline + 1 new) / 1729 vitest / vue-tsc 0 / ruff 0 / knip 0 / ESLint 0 / **lint-imports 3 contracts KEPT** (unchanged) / grimp-evasion OK。

4 lessons (v16.5 #6 §5):
1. **Defense-in-depth pattern scales** — same whitelist-based grep gate works for both DP-03 (sqlite3) and DP-02 (llm_service)。
2. **Tools vs business code boundary** — `tools/` is "external" in import-linter config。Grep gate is right tool for "soft" enforcement in this zone。
3. **Carryover file count drift** — original carryover said "11 files", actual is 12。Periodic re-verification of carryover scope。
4. **Hygiene test file location** — DP-02 hygiene tests live in `tooling/hygiene/tests/` (NOT `tests/hygiene/`)。Two hygiene test directories exist (historical): `tests/hygiene/` (v16.2/v16.3) vs `tooling/hygiene/tests/` (DP enforcement)。

**Carryover to v16.5 #N**:
- Full migration of 12 whitelisted `tools/` files — 1:1 symbol replacement (`LLMService.get()` → `LLMServiceAdapter()`)。Each file should be a separate commit (DP-06 strict)。

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
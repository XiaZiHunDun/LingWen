# Phase 38 — P3-ARCHDEBT (project_config) — handoff

> **Date**: 2026-09-08
> **Branch**: `phase-38-p3-archdebt-project-config` (worktree at `.claude/worktrees/phase-38-p3-archdebt-project-config`)
> **Master HEAD at start**: `e65d7784` (v36.0 — Phase 37 P3-ARCHDEBT paths + 6 phase37 guards)
> **Scope**: Migrate `infra/project_config.py` (170 lines, 2 top-level public symbols) → `packages/lingwen-project-config/`

## Status: ✅ CLOSED

P3-ARCHDEBT 3/5 (project_config) → CLOSED. Remaining: P3-ARCHDEBT 4/5 (logging_config, 8 consumers) + 5/5 (studio_registry, 50 consumers) → Phase 39+.

## Commit Chain (7 atomic commits on `phase-38-p3-archdebt-project-config`)

| # | Commit | Task |
|---|--------|------|
| C0 | `344cf5cb` | docs(phase-38): spec + plan for lingwen-project-config package |
| C1 | `ef6996fa` | chore(packages): scaffold lingwen-project-config (Phase 38 P3-ARCHDEBT project_config) |
| C2 | `7ce09033` | refactor(consumers): migrate 26 project_config consumers to lingwen_project_config |
| C3 | `b0d58456` | chore(infra): delete infra/project_config.py (Phase 38 P3-ARCHDEBT project_config cutover) |
| C3.5 | `3dfb796c` | test(phase-37): replace stale infra/project_config.py reference post-Phase 38 (N.14 lesson 1, 9th occurrence) |
| C4 | `91f2ab82` | chore(infra): bump v37.0 + add invariant #53 (lingwen-project-config canonical) |
| C5 | (this commit) | test(phase-38): regression guards + doc sync |

## Validation Gates (10/10 GREEN)

| Gate | Method | Result |
|------|--------|--------|
| G1 | ruff check packages/lingwen-project-config/ apps/ packages/ infra/ | clean (4 pre-existing E741, 0 new; **C5: 16 isort auto-fixes via `ruff --fix`** — see N.14 lesson 4) |
| G2 | pytest packages/lingwen-creator/tests/ | 73/73 pass (preserved) |
| G3 | pytest packages/lingwen-shared/tests/ | 140/140 pass (preserved) |
| G4 | pytest packages/lingwen-core/tests/ | 68/68 pass (preserved) |
| G5 | pytest packages/lingwen-got/tests/ | 208/208 pass (preserved) |
| G6 | pytest packages/lingwen-world-model/tests/ | 201/201 pass (preserved) |
| G7 | pytest packages/lingwen-pipeline/tests/ apps/studio_api/tests/ tests/infra/ tests/agent_system/ | pass (1 pre-existing LLM provider failure in tests/infra/test_creator_agent.py unrelated to Phase 38) |
| G8 | grep -rn "infra\.project_config" --include="*.py" infra/ apps/ packages/ | 0 functional hits (3 docstring-only, tolerated) |
| G9 | pytest tests/test_phase18_10_stale_imports.py | pass (whitelist updated) |
| G10 | pytest tests/test_phase38_lingwen_project_config.py | 7/7 GREEN (1 extra vs spec: wildcard-clean test included) |

**Combined target**: ~660 tests pass (Phase 37 baseline 658 + ~2 new for phase38 guards).

## Module Migration Summary

**Source**: `infra/project_config.py` (170 lines, 2 public symbols)
- `ProjectConfig` (frozen dataclass, 12 fields + 4 methods)
- `update_project_creation_mode()` (function)

**Target**: `packages/lingwen-project-config/src/lingwen_project_config/__init__.py` (1:1 byte preservation, no `__all__`)

**Naming choice**: `lingwen-project-config` (NOT `lingwen-config`) — preserves multi-word hyphenated pattern matching Phase 35 world-model migration.

**Deps**: `lingwen-paths` (Phase 37 closed) + `lingwen-shared` (v16.1 closed) — first non-leaf P3 package.

## Consumer Migration Summary

**Total sites migrated**: 26 import lines across 25 files (24 functional + 1 wildcard in infra/project/__init__.py:4 — later deleted in C3)

**Distribution**:
- 2 apps: creator_volume.py (2 sites), creator_core.py (1 site)
- 16 packages: 1 lingwen-shared + 2 lingwen-cli + 2 lingwen-core + 11 lingwen-creator
- 4 infra intra: full_check_report.py, project_characters.py, project/__init__.py (wildcard), studio_registry.py
- 5 tests: test_chapter_production_outline.py, test_creator_mode.py, test_project_init.py, test_creator_onboarding_autodetect.py, test_project_config.py

**Function-body imports caught**: 7 sites (spec estimated 3 — caught 4 additional via whitespace-preserving sed)
- 3 expected: `infra/full_check_report.py:170`, `infra/project_characters.py:68`, `packages/.../volume/summary.py:109`
- 4 additional: `apps/studio_api/routes/creator_volume.py:113+:682`, `apps/studio_api/routes/creator_core.py:79`, `packages/lingwen-cli/src/lingwen_cli/commands/doctor.py:113`

**Whitespace-preserving sed pattern** (better than spec):
```
sed -i -E 's|^([[:space:]]*)from infra\.project_config import|\1from lingwen_project_config import|'
```

## Carryover Closure

- ✅ P3-ARCHDEBT 3/5 (project_config) → CLOSED
- ⏳ P3-ARCHDEBT 4/5 (logging_config, 8 consumers) → Phase 39
- ⏳ P3-ARCHDEBT 5/5 (studio_registry, 50 consumers) → Phase 40

## N.14 Lessons Learned

1. **Lesson 1, 8th occurrence** (function-body imports): Spec underestimated 3 → actual 7. Whitespace-preserving sed `^([[:space:]]*)from ... \1from` is the correct pattern (not `^from` which strips indentation). Same lesson as Phase 33 + 37.

2. **Lesson 1, 9th occurrence** (filesystem-path string literals in prior-phase regression guards): Phase 37 guard `tests/test_phase37_lingwen_paths.py:145` hardcoded `infra/project_config.py` as a representative lingwen_paths consumer. After Phase 38 C3 deleted that source, the guard failed with FileNotFoundError. Required C3.5 fixup commit to replace with `packages/lingwen-core/src/lingwen_core/agents/chapter_production_outline.py`.

3. **Lesson 1, 10th occurrence** (docstring prose mentions vs functional imports): Phase 38 `test_no_infra_project_config_references` initially used Phase 37's loose `\binfra\.X\b` regex, which caught 3 docstring prose mentions (`packages/lingwen-shared/src/lingwen_shared/mode.py:13`, `packages/lingwen-creator/src/lingwen_creator/content/mode.py:9`, `tests/infra/test_project_config.py:1`). Required amending regex to line-anchored `^\s*(from|import)\s+infra\.project_config` to enforce actual import statements only. Phase 37 had 0 docstring residue so didn't hit this; Phase 38 has 3.

4. **Ruff --fix belongs in C2 (not C5)** — but C2 was already committed without it: Phase 37 C2 ran `ruff check --fix` inline to auto-fix 2 I001 violations. Phase 38 C2 omitted this, leaving 16 isort violations across 15 files (mechanical import-sort reorder from `from infra.project_config` → `from lingwen_project_config` shifting alphabetical position). C5 applied `ruff check --fix` to bring state to baseline (0 new errors vs Phase 37's "4 pre-existing E741"). Future P3 phases must run `ruff check --fix` at end of C2, not defer to C5.

5. **Audit matrix now 5 patterns** (Phase 32 + Phase 34 + Phase 38 lessons combined):
   - (1) Literal dotted-path imports: `grep -rn "from infra\.X\.Y\b"`
   - (2) Relative same-package: `grep -rn "from \.Y\b"`
   - (3) Relative parent-package: `grep -rn "from \.\.Y\b"`
   - (4) Filesystem-path string literals: `grep -rn "infra/X/Y" --include="*.py"`
   - (5) Prior-phase regression guards: `grep -rn "infra/X" tests/test_phase*.py`

   Future source-deletion phases must audit `tests/test_phase*.py` for hardcoded references to deleted paths.

6. **Single-file-package pattern for non-leaf**: First P3 package with workspace deps (lingwen-paths + lingwen-shared). pyproject.toml `[project] dependencies` declares both. C1 must declare member BEFORE `uv sync --all-packages` (Phase 34 lesson).

7. **Wildcard re-export cleanup belongs in C3 (not C5)**: Mixing infra + packages in umbrella namespace (`infra.project.*` re-exporting lingwen_project_config) is anti-pattern. Clean it in same commit as the source deletion that makes the wildcard semantically weird.

## Next Session Options

1. P3-ARCHDEBT Phase 39 — infra.logging_config.* (8 consumers, smallest by count)
2. P3-ARCHDEBT Phase 40 — infra.studio_registry.* (50 consumers, largest by count, most complex)
3. Phase 114 prod preview regression (accepted debt — do NOT attempt fix)
4. HANDOFF.md wording fix (pre-existing carryover)
5. Take a break

**Recommended**: Phase 39 logging_config (8 consumers, smallest scope, no intra-infra wildcard complications).

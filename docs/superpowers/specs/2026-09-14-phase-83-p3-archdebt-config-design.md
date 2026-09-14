# Phase 83 — P3-ARCHDEBT `infra/config/` → `packages/lingwen-config/`

@template: docs/superpowers/specs/_P3_ARCHDEBT_TEMPLATE.md

## 1. 背景

闭环 **ARCHDEBT-CANDIDATES.md Top 5 候选 #5** (`infra/config/`, 77 LOC, 1 public symbol APIConfig, TRUE LEAF + 1 third-party dep `pyyaml`) — **ARCHDEBT-REAL cycle 第五例**(Phase 79 LEAF + Phase 80 NOT-LEAF + Phase 81 TRUE LEAF + Phase 82 NOT-LEAF retry + Phase 83 TRUE LEAF config)。

**触发**:
- ARCHDEBT-CANDIDATES.md 排名 #5 candidate (LAST candidate in Top 5 — cluster saturation closing)
- Phase 79-82 cluster 完成, Phase 83 闭环 ARCHDEBT-CANDIDATES.md Top 5
- I079 模板 + 9-pattern audit + §A test files migration plan 全套防御机制 ready

**Phase 目标**: 把 `infra/config/` (APIConfig singleton + get_api_config + PyYAML config loading) 迁移到 `packages/lingwen-config/`, 成为 canonical implementation。`infra.config.*` 路径非法 (I084 NEW invariant)。`infra/config/` 全删。

**Special note**: Phase 83 有 **3 production cross-package consumers** 在 `tools/` (top-level tools directory NOT `tools/legacy/`):
- `tools/anti_trope_enhancer.py:20`
- `tools/claude_key_chapter_polisher.py:20`
- `tools/llm_quality_analyzer.py:26`

这些 tools/ 文件被 `packages/lingwen-quality` 和 `packages/lingwen-cli` 间接引用 — 是 active production code。

## 2. 9-pattern 审计结果

| # | Pattern | Verdict | Sites |
|---|---------|---------|-------|
| 1 | Literal dotted-path imports (top-level) | ✅ Found | 3 sites in `tools/*.py` (cross-package production consumers) |
| 2 | Indented/function-body imports | ✅ None | 0 (all imports top-level) |
| 3 | Relative imports (intra-module) | ✅ Found | 1 site in `infra/config/__init__.py:11` (`from infra.config.api_config_loader import APIConfig` — absolute not relative, pre-existing) |
| 4 | Filesystem path string literals | ✅ Found | 1 site: `infra/config/api_config_loader.py:28` (`Path(__file__).parent.parent / "config" / "api_config.yaml"` — Phase 56b2 lesson trigger) |
| 5 | Wildcard `from X import *` | ✅ None | 0 |
| 6 | `monkeypatch.setattr(..., "infra.X.Y", ...)` | ✅ None | 0 |
| 7 | `import X as Y` re-exports | ✅ None | 0 |
| 8 | Doc comments referencing old path | ✅ Found | 1 site: `infra/__init__.py:3` docstring (`config / util / errors`) — but Phase 82 already updated to `(config / errors)` |
| 9 | Prior-phase guard's hardcoded representative files | ✅ Found | 2 files: `tests/test_phase53d_event_sourcing.py:152,168` (N.14 v2 — `"config"` in remaining_subdirs) + `tests/test_phase18_8_infra_init_simplified.py:6` (docstring) |

**Source LOC tally**:
```
   13 infra/config/__init__.py
   64 infra/config/api_config_loader.py
   77 total
```

**Public API** (1 symbol): `APIConfig` (singleton class)

**Workspace deps** (TRUE LEAF + 1 third-party):
- `pyyaml` (3rd-party, NOT stdlib) — for YAML config loading

**Consumer count** (5 sites):
- Production cross-package (3): `tools/anti_trope_enhancer.py:20` + `tools/claude_key_chapter_polisher.py:20` + `tools/llm_quality_analyzer.py:26`
- Production intra-infra (1): `infra/__init__.py:18` (`from infra.config import APIConfig`)
- Intra-subdir (1): `infra/config/__init__.py:11` (will be auto-fixed when moved + intra-package absolute rewrite)
- **No test files to MIGRATE** (Phase 83 has no test consumers)

## 3. 配套 stale refs (清理清单)

- `infra/__init__.py:18` — `from infra.config import APIConfig` → `from lingwen_config import APIConfig`
- `infra/config/__init__.py:11` — `from infra.config.api_config_loader import APIConfig` → `from lingwen_config.api_config_loader import APIConfig` (intra-package absolute, pre-existing code smell)
- `infra/config/api_config_loader.py:28` — `Path(__file__).parent.parent / "config" / "api_config.yaml"` — Phase 56b2 lesson, fix to be relative to new package location (or to be configurable via env var)
- 3 tools/ files — `from infra.config.api_config_loader import get_api_config` → `from lingwen_config.api_config_loader import get_api_config`
- `tests/test_phase53d_event_sourcing.py:152,168` — drop `"config"` from `remaining_subdirs` list + add `assert not exists` (N.14 v2 lesson)
- `tests/test_phase18_8_infra_init_simplified.py:6` — update docstring (no longer "deferred", now gone)

## 4. 计划 (7 atomic commits)

| # | Subject | Files | +/- | Risk |
|---|---------|-------|-----|------|
| C0 | `docs(phase-83): spec + 9-pattern audit` | 1 file (this spec) | +1 / -0 | none |
| C1 | `chore(pkg): scaffold packages/lingwen-config/` | 3 files (pyproject.toml + 2 modules) + pyproject.toml workspace member | +77 / -0 | low — pure scaffold |
| C2 | `refactor(config): migrate 3 cross-pkg consumers + intra-infra + filesystem path fixup` | 5 files (3 tools/ + infra/__init__.py + infra/config/__init__.py + api_config_loader.py) | ~10 / ~10 | low — sed rewrite + path fixup |
| C3 | `chore(archdebt): FULL DELETE infra/config/ + I084 invariant` | 2 source files deleted + 1 entry in architecture.yml | -77 / +14 | medium — `infra.config.*` 完全消失 |
| C4 | `test(phase-83): prior-phase guards fixup (test_phase53d + test_phase18_8)` | 2 files | ~10 / ~5 | low — N.14 v2 lesson defense |
| C5 | `test(phase-83): 12 regression guards` | 1 file (tests/test_phase83_p3_archdebt_config.py) | +12 tests / -0 | low — 12 guards G1-G12 |
| C6 | `docs(phase-83): CLAUDE.md v54.15 + CURRENT_STATUS + BACKLOG + handoff sync` | 4 files | doc-only | none |

**Total**: 7 atomic commits on branch `phase-83-p3-archdebt-config` (similar to Phase 81/82 simplified pattern — no separate C2a/C2b since no MIGRATE test files).

## 5. §A. test files migration plan (MANDATORY per I079)

### A1. test files inventory

**No test files to MIGRATE** — Phase 83 has no test consumers.

### A2. MIGRATE 路径

**不适用** — 0 test files MIGRATE。

### A3. DELETE 路径

**不适用** — 0 test files DELETE。

### A4. RETAIN-ORPHAN 路径

**NOT ALLOWED** — 无 test files to begin with。

### A5. Half-migration defense (Phase 56b/56c/57b third occurrence)

**不适用** — 0 test files MIGRATE,所以无 half-migration risk。

## 6. 验证 gates

- [x] `ruff check packages/lingwen-config/` clean
- [x] `from lingwen_config import APIConfig` works (C1+C2 验证)
- [x] `from lingwen_config.api_config_loader import get_api_config` works for 3 tools/ files
- [x] `pytest tests/test_phase18_8_infra_init_simplified.py -v` 100% pass
- [x] `pytest tests/test_phase53d_event_sourcing.py -v` 100% pass
- [x] 9-pattern audit clean: `grep -rln "infra\.config" --include="*.py"` 仅命中历史 archive/comments
- [x] 12 NEW guards GREEN (test_phase83_p3_archdebt_config.py)
- [x] 2 prior-phase guards UPDATED: Phase 53d (C4 fixup drop "config" from list) + Phase 18_8 (C4 docstring)
- [x] `from infra.config.X import` → ModuleNotFoundError (C3 验证)
- [x] `from lingwen_config.X import` works (C1+C2 验证)

## 7. 风险评估

| Risk | Mitigation |
|------|-----------|
| 3 production cross-package consumers in tools/ (anti_trope_enhancer / claude_key_chapter_polisher / llm_quality_analyzer) | C2 in-place rewrite `from infra.config.api_config_loader` → `from lingwen_config.api_config_loader` |
| Filesystem path `Path(__file__).parent.parent / "config" / "api_config.yaml"` breaks after file relocation (Phase 56b2 lesson) | C2 fix path to be relative to new package location OR add fallback to env var `LINGWEN_CONFIG_PATH` |
| Intra-package absolute import `from infra.config.api_config_loader` (Phase 80 v2 lesson) | C1 pre-verify + C2 sed rename `from infra.config.api_config_loader` → `from lingwen_config.api_config_loader` |
| `pyyaml` is 3rd-party (not stdlib) | C1 pyproject.toml `dependencies = ["pyyaml"]` |
| infra/__init__.py:18 (intra-infra re-export) breaks after C3 | C2 in-place rewrite `from infra.config import` → `from lingwen_config import` |
| test_phase53d remaining_subdirs list still has "config" (N.14 v2) | C4 explicit fixup |

## 8. 不在范围 (defer list)

- ❌ **不**改 workspace deps (`packages/lingwen-config/pyproject.toml` 声明 `dependencies = ["pyyaml"]`)
- ❌ **不**新增 I085-I089 — 本 phase 仅 I084 NEW (1 invariant)
- ❌ **不**touch `infra/config/__pycache__/` — gitignored
- ❌ **不**migrate test files — Phase 83 has 0 test consumers to MIGRATE
- ❌ **不**create `config/api_config.yaml` file (Phase 83 path fixup is fallback to empty dict)
- ❌ **不**fix `tools/` directory references (these are top-level production tools, separate ARCHDEBT cycle)

## 9. 完工标准

- [x] 7 atomic commits on branch `phase-83-p3-archdebt-config`
- [x] `infra/config/` 完全消失 (git ls-files 验证)
- [x] `packages/lingwen-config/` 含 2 sub-modules + __init__.py + pyproject.toml
- [x] I084 NEW invariant in `.lingwen/architecture.yml`
- [x] CLAUDE.md v54.14 → v54.15 + invariant table 加 I084 row
- [x] `collaboration/CURRENT_STATUS.md` 更新 ✅ entry + `collaboration/BACKLOG.md` 滚动
- [x] `docs/superpowers/handoffs/2026-09-14-phase-83-p3-archdebt-config-handoff.md`
- [x] Branch ready for ff-merge

## 10. Lessons from prior phases (per I079 §C)

- **Phase 56b (world_db)**: tests/X/ → packages/<pkg>/tests/ + sys.path cleanup
- **Phase 56c (cross_volume)**: pathspec BOTH old + new commit
- **Phase 57b (reading_power)**: parent.parent.parent silent wrong in new location
- **Phase 79 (story_contracts)**: (1) `__pycache__/` 残留 (N.14 v23); (2) Regex anchored checks
- **Phase 80 (subplot)**: (1) `__all__` vs actual import; (2) Intra-package absolute imports
- **Phase 81 (di)**: Pre-existing failures carry over
- **Phase 82 (util)**: Intra-package absolute imports break after C3 (v2 lesson)
- **N.14 lesson 1 (9-pattern audit matrix)**: Phase 51+ 完整谱系 — Phase 83 audit 已覆盖 9-pattern 全套

## 11. Anti-patterns (per I079 §D)

- ❌ C3 commit **只**写 "+ I084" 而不列 test files
- ❌ 漏 fixup 3 cross-package consumers in tools/
- ❌ 漏 fixup infra/__init__.py:18 intra-infra re-export
- ❌ 漏 fixup filesystem path literal (Phase 56b2 lesson)
- ❌ 漏 fixup prior-phase guards (test_phase53d + test_phase18_8)
- ❌ spec 缺 §A test files migration plan (即使 N/A 也要说明)
- ❌ 漏声明 pyyaml dependency in pyproject.toml
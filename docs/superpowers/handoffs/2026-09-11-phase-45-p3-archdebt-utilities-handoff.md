# Phase 45 P3-ARCHDEBT (lingwen-utilities BATCH) Handoff

> **Date**: 2026-09-11
> **Phase**: 45 — P3-ARCHDEBT item 9/8+1
> **Branch**: `phase-45-p3-archdebt-utilities`
> **Status**: ✅ **CLOSED** (master HEAD pending ff-merge)
> **Spec**: [`docs/superpowers/specs/2026-09-11-phase-45-p3-archdebt-utilities-design.md`](../specs/2026-09-11-phase-45-p3-archdebt-utilities-design.md)
> **ARCHDEBT Rank**: #4 in [ARCHDEBT-CANDIDATES.md](../ARCHDEBT-CANDIDATES.md) (batch)

## TL;DR

4 TRUE-LEAF utility modules (`infra/{cache, coverage_gate, patterns, result}.py` = 417 LOC total) → 4 standalone canonical packages (`packages/lingwen-{cache, coverage-gate, patterns, result}/` = 8 sub-modules + 4 pyproject + 3 test MOVEs). 12 consumers migrated in single atomic C2 commit. 4 NEW invariants (I059-I062). Version bump v42.0 → v43.0.

**This is the FIRST multi-module P3-ARCHDEBT batch phase** (vs single-module per phase 36-44). Recommended by ARCHDEBT-CANDIDATES.md as Phase 45 batch (combining 4 small LEAF modules in 1 phase).

## Atomic commits (6 total on `phase-45-p3-archdebt-utilities`)

| SHA | Type | Scope | Notes |
|-----|------|-------|-------|
| `989f2f0a` | `docs(phase-45)` | spec | 9-pattern audit + 4 modules + 12 consumers + 17 total public symbols |
| `e94b1cd3` | `feat(packages)` | scaffold 4 packages | 16 files created (8 service + 4 __init__ + 4 pyproject) + 3 test MOVEs + 4 workspace registers |
| `4b28d4a6` | `refactor(consumers)` | bulk 12 sites | Single atomic commit per Phase 37 lesson (4 wildcards + 4 imports + 4 multi-import sed) |
| `ba1f821f` | `chore(infra)` | delete 4 files + I059-I062 + v43.0 | 4 files DELETED + 4 invariants + version |
| `b95cc786` | `fix(test)` | C4.5 fixup | Phase 44 guard forward-compatible version check (N.14 lesson 1 #23) |
| `<C4>` | `test(phase-45)` | 33 guards + handoff + MEMORY | Pending commit (this file) |

## Pre-spec audit (Phase 42 lesson #1 reinforcement — wildcard-in-`__init__.py`)

### 9-pattern audit results (per module)

| # | Pattern | cache | coverage_gate | patterns | result | Total |
|---|---------|-------|---------------|----------|--------|-------|
| 1 | Literal dotted-path imports | 3 | 2 | 2 | 1 | 8 |
| 2 | Indented/function-body imports | 0 | 0 | 0 | 0 | 0 |
| 3 | Relative imports | 0 | 0 | 0 | 0 | 0 |
| 4 | Filesystem path literals | 0 | 0 | 0 | 0 | 0 |
| 5 | **Wildcard** `from infra.X import *` | **1** | **1** | **1** | **1** | **4** |
| 6 | `monkeypatch.setattr("infra.X.Y", ...)` | 0 | 0 | 0 | 0 | 0 |
| 7 | Plain `import infra.X` (side-effect) | 0 | 0 | 0 | 0 | 0 |
| 8 | Doc comments referencing old path | 0 | 0 | 0 | 0 | 0 |
| 9 | Prior-phase guard's hardcoded representative | 0 | 0 | 0 | 0 | 0 |

### Real external consumers (12 sites, verified by fresh grep 2026-09-11)

| # | File | Module | Pattern |
|---|------|--------|---------|
| 1 | `infra/core/__init__.py:1` | cache | wildcard |
| 2 | `tests/test_cache.py:5` | cache | single symbol |
| 3 | `tools/llm_quality/__init__.py:19` | cache | single symbol |
| 4 | `tools/llm_quality/checker.py:13` | cache | single symbol |
| 5 | `infra/core/__init__.py:2` | coverage_gate | wildcard |
| 6 | `tests/ci/test_coverage_modules_ci.py:48` | coverage_gate | single symbol |
| 7 | `tests/infra/test_coverage_gate.py:7` | coverage_gate | multi-symbol |
| 8 | `infra/core/__init__.py:7` | patterns | wildcard |
| 9 | `packages/lingwen-quality/.../sentence_diversity_checker.py:21` | patterns | single symbol |
| 10 | `tests/test_patterns.py:5` | patterns | single symbol |
| 11 | `infra/core/__init__.py:8` | result | wildcard |
| 12 | `tests/test_infra_modules.py:382/393/405/416/423/441` | result | 6 imports in 1 file (sed in-place) |

### Infra/core/__init__.py after Phase 45

After Phase 45 migration, **3 wildcards REMAIN** for NOT-YET-MIGRATED modules:
- `infra.filter` (Phase 46+ — near-LEAF, 1 workspace dep lingwen_quality)
- `infra.full_check_report` (Phase 48+)
- `infra.memory_service` (Phase 49+ — NOT-LEAF, 10 deps)

The 4 Phase 45 wildcards were REPLACED in-place (not deleted wholesale) — per Phase 38 + 42 lessons on per-module wildcard handling.

## Architecture — 4 packages × 2 sub-modules

```
packages/
├── lingwen-cache/             # 91 LOC, stdlib only
├── lingwen-coverage-gate/     # 78 LOC, PyYAML>=6.0 3rd-party
├── lingwen-patterns/          # 80 LOC, stdlib only
└── lingwen-result/            # 168 LOC, stdlib only
                              # Total: 417 LOC across 4 packages
```

### Public surface (17 total symbols across 4 packages)

| Package | Public symbols | Count |
|---------|----------------|-------|
| `lingwen_cache` | `CacheEntry` (dataclass), `CheckerCache` (class) | 2 |
| `lingwen_coverage_gate` | `load_coverage_policy`, `module_percent`, `evaluate_module_gate`, `format_module_gate_report` | 4 |
| `lingwen_patterns` | `PatternRegistry` (singleton), `Pattern` (type alias) | 2 |
| `lingwen_result` | `Ok`, `Err`, `Result`, `ok`, `err`, `wrap`, `from_optional`, `combine`, `either` | 9 |

### Workspace deps — all 4 packages TRUE LEAF

```toml
# packages/lingwen-cache/pyproject.toml
dependencies = []  # stdlib only (hashlib/json/time/dataclasses/pathlib)

# packages/lingwen-coverage-gate/pyproject.toml
dependencies = ["PyYAML>=6.0"]  # 3rd-party only

# packages/lingwen-patterns/pyproject.toml
dependencies = []  # stdlib only (re/typing)

# packages/lingwen-result/pyproject.toml
dependencies = []  # stdlib only (typing)
```

### `_FACTORY_ROOT` path resolution (coverage_gate only)

Only `lingwen_coverage_gate.service` needs the path fixup:
- Old: `parents[1]` from `infra/coverage_gate.py` → repo root
- New: `parents[4]` from `packages/lingwen-coverage-gate/src/lingwen_coverage_gate/service.py` → repo root

`cache`, `patterns`, `result` modules have no `_FACTORY_ROOT` — pure logic.

### Invariants I059-I062

```
I059 | packages/lingwen-cache/ is CheckerCache + CacheEntry unique canonical package
I060 | packages/lingwen-coverage-gate/ is coverage module gate helpers unique canonical package
I061 | packages/lingwen-patterns/ is PatternRegistry + Pattern unique canonical package
I062 | packages/lingwen-result/ is Result type + 5 helpers unique canonical package
```

## Validation gates — all GREEN

| Gate | Status | Notes |
|------|--------|-------|
| **ruff clean** | ✅ | No new findings |
| **33 phase45 guards** | ✅ | 33/33 PASSED (covering 4 packages × 7-8 tests each + 3 cross-cutting) |
| **Phase 36-44 prior guards** | ✅ | 75/75 PASSED (after C4.5 fixup) |
| **Migrated tests (3 packages)** | ✅ | 10/10 PASSED + 2 skipped (coverage_gate tests need real coverage data) |
| **`__all__` count exact** | ✅ | cache=2 + coverage_gate=4 + patterns=2 + result=9 |
| **`_FACTORY_ROOT` (coverage_gate)** | ✅ | Phase 40a C1.5 fixup verified |
| **Production audit (4 modules)** | ✅ | 0 hits |
| **Test audit (4 modules)** | ✅ | 0 hits |

**Total**: 33 + 75 + 10 + 32 (test_infra_modules) = 150 tests passing.

## 4 lessons (Phase 45)

### Lesson 1: Multi-module batch P3-ARCHDEBT (N.14 lesson 1, 24th occurrence — Phase 45 NEW)

First multi-module P3-ARCHDEBT batch phase (vs single-module per phase 36-44). Recommended by ARCHDEBT-CANDIDATES.md as Phase 45 batch (combining 4 small LEAF modules).

**Pattern**: When ARCHDEBT-CANDIDATES.md says "可与 #X 合并 phase", do it. Multiple small LEAF modules in 1 phase = 5 atomic commits + 1 fixup = 6 total (vs 4×6=24 for separate phases).

Trade-off: batch phases are higher-risk (16 files created in C1 single commit) but more efficient (4 version bumps become 1).

### Lesson 2: N.14 lesson 1 #23 — same brittle pattern, two phases later

Phase 44 test_invariant_in_claude_md still had `assert "v42.0" in content`. Phase 44 wrote new test AFTER the Phase 43 fix (C3.5), but used the same brittle pattern.

**Recommendation**: future P3-ARCHDEBT phase guard templates should INCLUDE the regex-based version check from the start. Pattern:

```python
import re
version_match = re.search(r"\bv(\d+)\.0\b", content)
assert version_match and int(version_match.group(1)) >= {phase_N}
```

This propagates forward-compatibility without per-phase fixup commits.

### Lesson 3: workspace dir ↔ module name hyphen vs underscore

Workspace pyproject.toml uses hyphenated directory names (`packages/lingwen-cache`), but Python module imports use underscores (`import lingwen_cache`). Tests must convert:

```python
package_dir = package.replace("_", "-")  # for workspace check
__import__(package)  # for module import (uses underscores)
```

Easy to forget in guard tests (initial Phase 45 had 4 fails from this exact bug).

### Lesson 4: sed in-place migration for multi-import test files

For files like `tests/test_infra_modules.py` with 6 `from infra.result import X` imports (4-space indent), column-0 anchored sed fails. Use sed without anchor: `sed -i 's|infra\.result import|lingwen_result import|g'`.

**Pattern**: indented imports (N.14 lesson 1 variant) — see Phase 37 lesson for original anchor-vs-non-anchor distinction.

## Carryover closure

| Phase | Module | Status |
|-------|--------|--------|
| P3-ARCHDEBT 5/5 (errors/paths/project_config/logging_config/studio_registry) | ✅ | Phase 36-40b |
| P3-ARCHDEBT 6/5+1 (project_init) | ✅ | Phase 42 |
| P3-ARCHDEBT 7/6+1 (lingwen-llm-service) | ✅ | Phase 43 |
| P3-ARCHDEBT 8/7+1 (lingwen-prose-calibration) | ✅ | Phase 44 |
| **P3-ARCHDEBT 9/8+1 (lingwen-utilities batch: cache+coverage_gate+patterns+result)** | ✅ | **Phase 45 (this phase)** |
| P3-ARCHDEBT 10/9+1 (filter near-LEAF) | 🟡 | Phase 46+ |

## References

- Pre-spec: [`docs/superpowers/specs/2026-09-11-phase-45-p3-archdebt-utilities-design.md`](../specs/2026-09-11-phase-45-p3-archdebt-utilities-design.md)
- ARCHDEBT-CANDIDATES.md #4 (this phase — batch recommendation)
- Phase 36 (errors pilot) — first P3-ARCHDEBT
- Phase 38 (project_config) — C3.5 fixup precedent (N.14 lesson 1 #9)
- Phase 39 (logging_config) — TRUE LEAF template
- Phase 40a (studio_registry) — C1.5 fixup pattern (path resolution)
- Phase 42 (project_init) — wildcard-in-`__init__.py` lesson
- Phase 43 (lingwen-llm-service) — bulk migration + DP-02 contract
- Phase 44 (lingwen-prose-calibration) — TRUE LEAF single-module template (extended to multi-module in Phase 45)

---

> **All claims in this handoff verified by fresh-run** (Phase 41 mini lesson #1):
> 33 phase45 guards + 10 migrated tests + 32 test_infra_modules + 75 prior-phase guards
> (after C4.5 fixup) = 150 PASSED, 0 regressions.
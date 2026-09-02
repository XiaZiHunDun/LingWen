# Phase 22 — test-env + format cleanup — handoff

> **Date**: 2026-09-02
> **Branch**: `phase-22-test-env-format-cleanup`
> **Master HEAD at start**: `1a0f1093` (v21.0)
> **Commits**: 5 source commits (`e19eea8b..dbc54631`)
> **Status**: CLOSED ✅

## Summary

Phase 22 closes 2 carryovers from v19.x chain: (1) lingwen_llm test-env gap (real LLM calls hang because deepeval plugin auto-loads `.env`), (2) ruff format cleanup (1072 files need mechanical whitespace/quote style normalization). Bonus: pre-existing `infra/errors.py` unused `field` dataclass import (F811 shadow) removed.

**Net effect**: 1072 files reformatted, +15156/-12660 lines (mostly blank line normalization + quote style), 0 functional code changes, 0 new architecture invariants.

## Commits

```
e19eea8b  test(env): disable deepeval dotenv autoload via DEEPEVAL_DISABLE_DOTENV=1
6bf95515  build(deps): add pytest-env>=1.7 to dev deps
f7621002  style: ruff format 1072 files (mechanical whitespace/style cleanup)
d5fb737c  style(errors): remove unused 'field' import from dataclasses
0b64ad8a  docs(phase-22): CLAUDE.md v22.0 entry + architecture.yml version 22.0
dbc54631  docs(phase-22): architecture.yml phase_22 block
[final]    docs(phase-22): handoff doc + lessons
```

## What was fixed

### T1a: pytest.ini — disable deepeval dotenv autoload

```ini
[pytest]
# ... existing config ...
env =
    # Phase 22 — disable deepeval's .env autoload
    # (deepeval's autoload_dotenv() reads .env and sets MINIMAX_API_KEY,
    # causing real LLM calls to hang in test runs)
    DEEPEVAL_DISABLE_DOTENV=1
```

### T1b: pyproject.toml — add pytest-env dev dep

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    # ... existing deps ...
    "pytest-env>=1.7",  # Phase 22 — disable deepeval autoload_dotenv in tests
]
```

### T2: ruff format 1072 files

```bash
ruff format .
# 1072 files reformatted, 125 files already formatted
```

Changes are mechanical and semantic-preserving:
- Blank line normalization after docstrings/imports (PEP 8 alignment)
- Quote style normalization: `'` → `"` (Python style guide)
- Logger warning single-line format where fitting in line-length 110
- Tuple/list alignment normalization

### T2.bonus: infra/errors.py — remove unused `field` import

```python
# Before:
from dataclasses import dataclass, field

# After:
from dataclasses import dataclass
```

The `field` from dataclasses was never used as `dataclasses.field(...)` — the `field: str = ""` parameter in `ValidationError.__init__` was a parameter name that shadowed the unused import (ruff F811 redefinition warning).

## verify-before-design (N.14 lesson 1, 6th time in Phase 19+ chain)

### T1: lingwen_llm test-env gap root cause

```
$ grep -rn "pytest11" /home/ailearn/miniconda3/lib/python3.13/site-packages/deepeval-*.dist-info/entry_points.txt
[pytest11]
deepeval=deepeval.plugins.plugin

$ grep -rn "pytest11" /home/ailearn/miniconda3/lib/python3.13/site-packages/langsmith-*.dist-info/entry_points.txt
[pytest11]
langsmith_plugin = langsmith.pytest_plugin
```

Both deepeval and langsmith register as **pytest11 plugins** via setuptools entry points — pytest auto-loads them at startup.

**deepeval**'s `__init__.py`:
```python
# IMPORTANT: load environment variables before other imports
from deepeval.config.settings import autoload_dotenv, get_settings
logging.getLogger("deepeval").addHandler(logging.NullHandler())
autoload_dotenv()
```

`autoload_dotenv()` source:
```python
def autoload_dotenv() -> None:
    """
    Controls:
      - DEEPEVAL_DISABLE_DOTENV=1 -> skip
      - ENV_DIR_PATH -> directory containing .env files (default: CWD)
    """
```

deepeval has an **official escape hatch** (`DEEPEVAL_DISABLE_DOTENV=1`). Langsmith doesn't auto-load `.env` (verified via grep) — no fix needed.

### T2: ruff format actual scope

```
$ ruff format --check . | wc -l
1072
```

1072 files need reformatting (not estimate — verified count).

Distribution:
- tests/infra: 98 files
- tests/ci: 54 files
- packages/lingwen-quality/.../consistency/checkers: 42 files
- tests/agent_system: 40 files
- tests/dashboard: 35 files
- tests/cross_volume: 32 files
- tests/: 31 files
- infra/: 25 files
- packages/lingwen-core/.../agents: 23 files
- tests/consistency: 19 files

## Verification gates (all green)

| Gate | Command | Result |
|---|---|---|
| Regression tests (no env -u) | `pytest tests/test_phase18_4_agent_migration.py tests/test_infra_init_no_deferred_re_exports.py -v` | **15/15 PASSED** (without `env -u` workaround — proves T1 fix works) ✅ |
| Frontend vitest | `pnpm exec vitest run` | **1762 + 1 skipped** (matches v21.0 baseline) ✅ |
| vue-tsc | `pnpm exec tsc --noEmit` | **0 errors** ✅ |
| ESLint | `pnpm exec eslint .` | **0 errors** ✅ |
| knip | `pnpm exec knip` | **0 issues** (`{"issues":[]}`) ✅ |
| ruff format | `ruff format --check .` | **0 files need reformat** ✅ |
| ruff check | `ruff check .` | **All checks passed!** ✅ |
| lint-imports | `.venv/bin/lint-imports` | **3 contracts KEPT, 0 broken** (315 files / 1386 deps) ✅ |
| Verify DEEPEVAL_DISABLE_DOTENV | subprocess check | **MINIMAX_API_KEY_after_collection: False** ✅ |

## Architecture invariants

**0 NEW architecture invariants**. This phase is config + formatting — no architectural constraints added.

## Files modified

**Updated**:
- `pytest.ini` — added `env = DEEPEVAL_DISABLE_DOTENV=1` section
- `pyproject.toml` — added `pytest-env>=1.7` to dev deps
- `infra/errors.py` — removed unused `field` import
- **1072 files reformatted** by `ruff format` (blank lines + quote style + line folding)
- `CLAUDE.md` — v22.0 entry at line 3, v21.0 demoted to line 4, v21.0 carryover line marked "CLOSED by v22.0"
- `.lingwen/architecture.yml` — version 21.0 → 22.0 + new `phase_22:` block at end with carryover_to_phase_23

**New**:
- `docs/superpowers/handoffs/2026-09-02-phase-22-test-env-format-cleanup-handoff.md` (this file)

## Lessons

### 1. verify-before-design re-confirmed (N.14 lesson 1, 6th time in Phase 19+ chain)

Phase 22 carryovers were accurately described in v19.x handoffs. The "lingwen_llm test-env gap" was correctly identified as a pytest plugin auto-load issue; the "ruff format cleanup" was correctly identified as a mechanical 1000+ file task.

| Phase | Claimed | Actual | Off-by |
|---|---|---|---|
| Sub1 | "30+" | 16 | 2x |
| Sub2 | "30+" | 6 | 5x |
| Sub3 | "30+" | 1 | 30x |
| 20 | "→ migration" | 0 (deletion) | ∞ |
| 21 | "0 consumers" | 0 consumers | ✓ correct |
| **22** | **"test-env gap + ruff format cleanup"** | **both as described** | **✓ correct** |

When carryover descriptions are accurate, Phase closure is straightforward. The lesson: invest in accurate carryover descriptions during the original phase; future phase work scales linearly with description quality.

### 2. pytest plugin auto-loading via `[pytest11]` entry points requires explicit opt-out

The root cause of the lingwen_llm test-env gap was NOT directly addressable from `conftest.py`:
- pytest loads entry-point plugins BEFORE conftest.py runs
- deepeval's `autoload_dotenv()` fires at module import (before any test code runs)
- conftest.py session-scope fixture can only UNSET the var after the fact (too late if test code runs in between)

**Fix options**:
1. `-p no:deepeval` in pytest.ini `addopts` (disables plugin entirely)
2. `env = DEEPEVAL_DISABLE_DOTENV=1` via pytest-env (preserves plugin, disables dotenv)
3. CI-only env var (doesn't fix dev workflow)

Option 2 chosen — conservative, preserves any potential deepeval functionality, official escape hatch.

### 3. `DEEPEVAL_DISABLE_DOTENV=1` is deepeval's official escape hatch

deepeval source (`/site-packages/deepeval/config/settings.py`):
```python
def autoload_dotenv() -> None:
    """
    Controls:
      - DEEPEVAL_DISABLE_DOTENV=1 -> skip
      - ENV_DIR_PATH -> directory containing .env files (default: CWD)
    """
```

When third-party libraries expose official escape hatches, prefer using them over ad-hoc workarounds. The `env -u MINIMAX_API_KEY` workaround was fragile (relied on order-of-operations: unset → load .env → process env wins).

### 4. pytest-env is a tiny dev dep for `env =` section in pytest.ini

The `env =` section in pytest.ini requires the `pytest-env` plugin. Adding it to `[project.optional-dependencies].dev` ensures future `uv sync --extra dev` installs it. The plugin is small (~5KB), no runtime impact, and standard pytest tooling.

### 5. ruff format changes are mechanical (blank lines + quotes + line-length folding) — safe to single-commit when scope is 1000+ files

1072 files in single commit is unconventional but appropriate here because:
- All changes are mechanical (whitespace, quote style, line folding)
- Zero semantic difference between before/after
- Splitting 1072 files into multiple commits would create artificial review overhead
- Bisect-friendly: if a regression appears, `git blame` + `git diff` on the specific file shows the exact change

The alternative (split by directory) was considered but rejected: 10+ commits of "format tests/infra/foo.py" provides no review value.

## Carryover closure

| Carryover | Status |
|---|---|
| `lingwen_llm test-env gap` (v19.x carryover) | **CLOSED** by v22.0 |
| `ruff format cleanup` (v19.x carryover) | **CLOSED** by v22.0 |
| `infra/errors.py` F811 warning (pre-existing) | **CLOSED** as bonus |

## Carryover to Phase 23+

- **Phase 114 prod preview regression** — accepted (per CLAUDE.md); cyticoolatose-fcose CJS / rollup incompatibility; 5 phases of effort failed.

## LingWen debt final state

After Phase 22:
- **Phase 18-22 carryovers ALL CLOSED** (except Phase 114 prod preview which is accepted debt)
- **All 12+ architecture invariants** (#36-#47) preserved
- **0 shim directories** in `infra/`
- **1072 files now formatted** per ruff conventions
- **lingwen_llm test-env gap FIXED** at root cause (no more `env -u` workaround)

LingWen debt closure is essentially COMPLETE. Only Phase 114 prod preview remains (5 phases of accepted failure).

## Solo workflow closure

```
$ git checkout master && git merge --ff-only phase-22-test-env-format-cleanup
$ git push origin master
$ git worktree remove ../LingWen-phase-22
```

Master HEAD after merge: `dbc54631` (v22.0).
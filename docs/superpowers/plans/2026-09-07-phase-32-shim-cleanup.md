# Phase 32 — PHASE-COMPAT shim cleanup — execution plan

> **Date**: 2026-09-07
> **Branch**: `phase-32-shim-cleanup`
> **Master HEAD at start**: `69e620d7` (v31.0)
> **Status**: PLAN — approved for execution
> **Spec**: `docs/superpowers/specs/2026-09-07-phase-32-shim-cleanup-design.md`

## Worktree bootstrap

```bash
cd /home/ailearn/projects/LingWen-phase-32
uv sync --all-packages --offline
uv pip install --offline pytest pytest-asyncio pytest-cov pytest-timeout pytest-metadata pytest-json-report pytest-env psutil
.venv/bin/python -m pytest --version   # verify
```

## Commit sequence

### C0 — docs(phase-32): write spec + plan design docs

```bash
git add docs/superpowers/specs/2026-09-07-phase-32-shim-cleanup-design.md \
        docs/superpowers/plans/2026-09-07-phase-32-shim-cleanup.md
git commit -m "docs(phase-32): write spec + plan design docs"
```

Verify: `git log --oneline -1` shows C0 commit. No gate run needed (doc-only).

### C1 — test(shim): add Phase 32 regression guard tests (RED)

Write `tests/test_phase32_shim_cleanup.py`:

```python
"""Phase 32 — regression guards for PHASE-COMPAT shim deletion.

Mirrors Phase 18.4 (`test_phase18_4_agent_migration.py`) + Phase 21
(`test_infra_init_no_deferred_re_exports.py`) patterns: static text/path
absence checks, no Python import execution.

Phase 32 deletes 3 shims:
- infra/subplot/data_structures.py (32 lines, 0 consumers)
- infra/world_model/data_structures.py (69 lines, 0 consumers)
- packages/lingwen-core/src/lingwen_core/agents/master_controller.py (11 lines,
  6 test consumers via `from lingwen_core.agents import master_controller as mc_mod`)

These guards:
1. Path-existence: 3 shim files must NOT exist
2. Consumer text-absence: 6 test files must NOT import from the shim path
3. Canonical-symbol: lingwen_core.domain.__init__ must re-export replacement
   entities (proves canonical replacement paths exist)
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

THREE_SHIM_PATHS = [
    "infra/subplot/data_structures.py",
    "infra/world_model/data_structures.py",
    "packages/lingwen-core/src/lingwen_core/agents/master_controller.py",
]

SIX_CONSUMER_FILES = [
    "tests/agent_system/test_master_controller_workflow.py",
    "tests/agent_system/test_decision_integration.py",
    "tests/agent_system/test_got_bridge.py",
    "tests/dashboard/test_decision_api.py",
    "tests/dashboard/test_app_workflow_production_summary_f66.py",
    "tests/dashboard/test_app_workflow_status.py",
]

SHIM_IMPORT_PATTERN = "from lingwen_core.agents import master_controller as mc_mod"
CANONICAL_IMPORT_PATTERN = "from lingwen_pipeline import master_controller as mc_mod"


@pytest.mark.parametrize("shim_path", THREE_SHIM_PATHS)
def test_phase32_shim_path_deleted(shim_path: str) -> None:
    """Phase 32: PHASE-COMPAT shim files should be deleted."""
    assert not (REPO_ROOT / shim_path).exists(), (
        f"PHASE-COMPAT shim {shim_path} still exists; should be deleted in Phase 32."
    )


@pytest.mark.parametrize("consumer_path", SIX_CONSUMER_FILES)
def test_phase32_shim_consumer_migrated(consumer_path: str) -> None:
    """Phase 32: 6 test consumers should migrate to canonical lingwen_pipeline path."""
    consumer_file = REPO_ROOT / consumer_path
    assert consumer_file.exists(), f"Consumer file {consumer_path} should exist"
    text = consumer_file.read_text(encoding="utf-8")
    assert SHIM_IMPORT_PATTERN not in text, (
        f"{consumer_path} still imports from shim path; should use canonical path."
    )
    assert CANONICAL_IMPORT_PATTERN in text, (
        f"{consumer_path} should import MasterController from canonical lingwen_pipeline path."
    )


def test_phase32_canonical_domain_reexports() -> None:
    """Phase 32: lingwen_core.domain.__init__ must re-export replacement entities."""
    domain_init = REPO_ROOT / "packages/lingwen-core/src/lingwen_core/domain/__init__.py"
    assert domain_init.exists()
    text = domain_init.read_text(encoding="utf-8")
    for symbol in ["Plot", "WorldSnapshot", "Ripple", "KeyPoint", "NodeId"]:
        assert symbol in text, f"lingwen_core.domain.__init__ should re-export {symbol}"
```

Verify RED:
```bash
.venv/bin/python -m pytest tests/test_phase32_shim_cleanup.py -v
# Expect: 3/3 path-deleted FAIL + 6/6 consumer-migrated FAIL + 1/1 canonical PASS = 10 items, 9 failed
```

Commit:
```bash
git add tests/test_phase32_shim_cleanup.py
git commit -m "test(shim): add Phase 32 regression guard tests (RED)"
```

### C2 — chore(infra): delete infra/subplot/data_structures.py shim

```bash
git rm infra/subplot/data_structures.py
git commit -m "chore(infra): delete infra/subplot/data_structures.py PHASE-COMPAT shim (1 of 3)"
```

Verify GREEN:
```bash
.venv/bin/python -m pytest tests/test_phase32_shim_cleanup.py::test_phase32_shim_path_deleted -v
# Expect: infra/subplot case PASS, world_model + master_controller still FAIL
```

### C3 — chore(infra): delete infra/world_model/data_structures.py shim

```bash
git rm infra/world_model/data_structures.py
# Clean stale historical comment in links.py
edit infra/world_model/links.py:28-29  # remove "historical cycle risk" reference
git add infra/world_model/links.py
git commit -m "chore(infra): delete infra/world_model/data_structures.py PHASE-COMPAT shim (2 of 3)

Removes stale 'historical cycle risk' comment in links.py:28-29 that
referenced the now-deleted data_structures shim path."
```

Verify GREEN:
```bash
.venv/bin/python -m pytest tests/test_phase32_shim_cleanup.py::test_phase32_shim_path_deleted -v
# Expect: 2/3 PASS (subplot + world_model), 1/3 FAIL (master_controller still exists)
grep -rn "infra\.world_model\.data_structures\|infra\.subplot\.data_structures" --include="*.py" apps/ tests/ packages/ infra/ scripts/
# Expect: 0 hits
```

### C4 — refactor(test): migrate 6 MasterController test consumers

Mechanical sed-equivalent: replace `from lingwen_core.agents import master_controller as mc_mod` → `from lingwen_pipeline import master_controller as mc_mod` in 6 test files.

```bash
# Use Edit (with replace_all) or python one-liner per file:
for f in \
  tests/agent_system/test_master_controller_workflow.py \
  tests/agent_system/test_decision_integration.py \
  tests/agent_system/test_got_bridge.py \
  tests/dashboard/test_decision_api.py \
  tests/dashboard/test_app_workflow_production_summary_f66.py \
  tests/dashboard/test_app_workflow_status.py; do
  sed -i 's|from lingwen_core\.agents import master_controller as mc_mod|from lingwen_pipeline import master_controller as mc_mod|g' "$f"
done

ruff check --fix  # auto-clean any I001 import sort issues
git add tests/
git commit -m "refactor(test): migrate 6 MasterController test imports to lingwen_pipeline (3a of 3)"
```

Verify GREEN:
```bash
.venv/bin/python -m pytest tests/test_phase32_shim_cleanup.py -v
# Expect: 3/3 path-deleted FAIL (master_controller shim still exists) + 6/6 consumer-migrated PASS + 1/1 canonical PASS
.venv/bin/python -m pytest tests/agent_system/test_master_controller_workflow.py tests/agent_system/test_decision_integration.py tests/agent_system/test_got_bridge.py tests/dashboard/test_decision_api.py tests/dashboard/test_app_workflow_production_summary_f66.py tests/dashboard/test_app_workflow_status.py --rootdir=. -q
# Expect: 116 passed + 1 skipped (baseline preserved)
```

### C5 — chore(packages): delete lingwen-core/agents/master_controller.py shim

```bash
git rm packages/lingwen-core/src/lingwen_core/agents/master_controller.py
git commit -m "chore(packages): delete lingwen-core/agents/master_controller.py PHASE-COMPAT shim (3b of 3)"
```

Verify GREEN (all guards pass):
```bash
.venv/bin/python -m pytest tests/test_phase32_shim_cleanup.py -v
# Expect: 3/3 path-deleted PASS + 6/6 consumer-migrated PASS + 1/1 canonical PASS = 10/10 GREEN
.venv/bin/python -m pytest tests/agent_system/test_master_controller_workflow.py tests/agent_system/test_decision_integration.py tests/agent_system/test_got_bridge.py tests/dashboard/test_decision_api.py tests/dashboard/test_app_workflow_production_summary_f66.py tests/dashboard/test_app_workflow_status.py --rootdir=. -q
# Expect: 116 passed + 1 skipped (baseline preserved)
```

### C6 — docs(architecture): CLAUDE.md v32.0 + architecture.yml + arch spec + carryover flips

Update files:
1. `CLAUDE.md`: Add v32.0 entry (mirror v31.0 format); bump "Phase 31" → "Phase 32" in version line
2. `.lingwen/architecture.yml`: version 31.0 → 32.0; update invariants #37 + #39 to "deleted Phase 32"
3. `docs/LINGWEN_ARCHITECTURE_SPEC.md:669`: Remove `SubplotDataStructures` row
4. `docs/superpowers/handoffs/2026-09-04-phase-27-wfrunner-handoff.md:26`: Flip carryover status
5. `docs/superpowers/handoffs/2026-09-07-phase-31-archdebt-mini-handoff.md:39,162`: Flip "Phase 32+ 候选" → "CLOSED by Phase 32"
6. `docs/superpowers/specs/2026-09-07-phase-31-archdebt-mini-design.md:26,418`: Flip Phase 32 candidate → CLOSED
7. `packages/lingwen-pipeline/README.md:19-20`: Flip historical shim note → "deleted Phase 32"

```bash
git add CLAUDE.md .lingwen/architecture.yml docs/LINGWEN_ARCHITECTURE_SPEC.md \
        docs/superpowers/handoffs/2026-09-04-phase-27-wfrunner-handoff.md \
        docs/superpowers/handoffs/2026-09-07-phase-31-archdebt-mini-handoff.md \
        docs/superpowers/specs/2026-09-07-phase-31-archdebt-mini-design.md \
        packages/lingwen-pipeline/README.md
git commit -m "docs(architecture): CLAUDE.md v32.0 + architecture.yml version 32.0 + arch spec + carryover flips

Phase 32 closes 3 PHASE-COMPAT shims (infra/subplot/data_structures.py +
infra/world_model/data_structures.py + lingwen-core/agents/master_controller.py).
Doc sync: bump CLAUDE.md to v32.0, update architecture.yml invariants #37/#39,
flip carryover status in 4 carryover docs (Phase 27, 31 handoff x2, 31 design).
Sub-task A/B done; infra.got.* migration + infra/world_model/__init__.py split
remain as Phase 33+ candidates."
```

### C7 — docs(phase-32): handoff + CURRENT_STATUS + BACKLOG sync

Write:
- `docs/superpowers/handoffs/2026-09-07-phase-32-shim-cleanup-handoff.md`
- Update `collaboration/CURRENT_STATUS.md` (v32.0 entry)
- Update `collaboration/BACKLOG.md` (P2-ARCHDEBT 1/2 closed; infra.got.* still pending)

```bash
git add docs/superpowers/handoffs/2026-09-07-phase-32-shim-cleanup-handoff.md \
        collaboration/CURRENT_STATUS.md collaboration/BACKLOG.md
git commit -m "docs(phase-32): handoff + CURRENT_STATUS + BACKLOG sync

Phase 32 closes PHASE-COMPAT shim deletion (3 of 4 P2-ARCHDEBT items).
Carryover to Phase 33+: infra.got.* migration (multi-day) + infra/world_model/__init__.py split."
```

### C8 — chore(merge): ff-merge to master

Per CLAUDE.md 2026-09-01 rule (solo repo, no PR):
```bash
git checkout master
git merge --ff-only phase-32-shim-cleanup
git push origin master
git worktree remove ../LingWen-phase-32
```

## Verification gates (full suite after C5, then C8)

| Gate | When | Pass criteria |
|------|------|--------------|
| G1 ruff | after C2, C3, C4, C5 | `ruff check .` → 0 errors |
| G2 guard | after C5 | `pytest tests/test_phase32_shim_cleanup.py -v` → 10/10 PASS |
| G3 modified suites | after C4, C5 | `pytest <6 files>` → 116 + 1 skipped (baseline) |
| G4 full backend | after C5 | `pytest tests/ --rootdir=.` → no new failures |
| G5 frontend | after C5 | `pnpm vitest run` → 1862 + 1 skipped (no regression; backend-only phase) |
| G6 knip | after C5 | `pnpm exec knip` → `{"issues":[]}` |
| G7 lint-imports | after C5 | `.venv/bin/lint-imports` → 3 contracts KEPT |
| G8 grep audit | after C5 | `grep -rn "infra.subplot.data_structures\|infra.world_model.data_structures\|lingwen_core.agents.master_controller" --include="*.py" apps/ tests/ packages/ infra/ scripts/` → 0 hits |

## Carryover to Phase 33+

1. **infra.got.* → packages/lingwen-got/** (199 tests, multi-day)
2. **infra/world_model/__init__.py split** (5 consumer migration)
3. **`polisher/prompts.py:132` `_safe_label` import** (latent broken, predates Phase 32)
4. **HANDOFF.md `latest_decision_queue` wording** (pre-existing carryover)

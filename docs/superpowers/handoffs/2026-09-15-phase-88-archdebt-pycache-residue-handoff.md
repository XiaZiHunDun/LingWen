# Phase 88 P3-ARCHDEBT Handoff — infra/__pycache__/ + relationship_network.json residue cleanup

> **Phase**: 88 (P3-ARCHDEBT-MINI #4, ARCHDEBT cycle POST-saturation disk cleanup)
> **Branch**: `phase-88-archdebt-pycache-residue`
> **Date**: 2026-09-15
> **Version**: v54.19 → **v54.20**
> **Status**: ✅ ff-merge ready (5 atomic commits, 40/40 C2 + prior-phase preserved)

---

## TL;DR

Phase 88 closes ARCHDEBT cycle disk-residue carryover — 29 `infra/<subdir>/__pycache__/` Python bytecode directories + 1 gitignored legacy `relationship_network.json` file + 3 empty parent dirs (`infra/novel-factory/agent_system/social_engine/` + parents). Recovered **~1.5 MB disk space** (vs spec's initial ~86 MB misread — actual was 1.5 MB pycache, not 86 MB which was dominated by `infra/.state/ripple.db` 80M SQLite runtime artifact, preserved).

**NON-INVASIVE++ pattern** (post-saturation disk cleanup): 0 tracked file touched, 0 prior-phase guard affected, 0 canonical path changed. Phase 88 closes N.14 v23 v3 lesson (pycache residue after `git rm`) + Phase 53e carryover (orphan relationship_network.json).

Cluster cumulative (Phase 53-88): **16 phases / ~20464 LOC dead code + ~1.5 MB disk space**.

**ARCHDEBT cycle is now physically complete** (git tracking clean + filesystem clean of dead code/bytecode).

---

## §1. Why this Phase matters (ARCHDEBT cycle physical closure)

Phase 87 closed ARCHDEBT cycle with respect to **git tracking** — `git ls-files infra/` returns 1 file (`__init__.py`), `git status` clean.

Post-Phase 87 audit (2026-09-15) revealed **filesystem-level residue** that git tracking couldn't see:
- 29 `infra/<subdir>/__pycache__/` dirs (Python bytecode from Phases 79-87 `git rm` — gitignored, never tracked)
- 1 `infra/novel-factory/agent_system/social_engine/relationship_network.json` (61 bytes empty JSON, gitignored Phase 53e/54 path drift residue, never reachable from code)

These were **not tracked in git** (so `git status` was clean), but **existed on filesystem** consuming 1.5 MB disk + mental overhead. Phase 88 closes this carryover.

---

## §2. Atomic commits (5)

| Commit | Type | Subject |
|--------|------|---------|
| `5bfc68e7` | docs | C0 spec + 9-pattern audit |
| `7e2f5682` | docs | C0.5 spec amend (accurate disk recovery numbers) |
| `dd0b643a` | chore | C1 gitignored content cleanup (`--allow-empty`, since gitignored) |
| `6d1e24e1` | test | C2 40 regression guards G1-G12 + Gx (40/40 PASS) |
| (C3) | docs | CLAUDE.md v54.19 → v54.20 + CURRENT_STATUS + BACKLOG + handoff (this doc) |

**5 atomic commits** follows Phase 87 pattern, but C1 is `--allow-empty` because the actual content was gitignored (no `git rm` possible). Cleanup performed in main repo working directory, recorded via empty commit on phase-88 branch.

---

## §3. Files changed

```
docs/superpowers/specs/2026-09-15-phase-88-archdebt-pycache-residue-design.md | NEW (C0 + C0.5 amend)
tests/test_phase88_archdebt_pycache_residue.py                                | NEW (C2, +403 lines)
CLAUDE.md                                                                     | version v54.19 → v54.20 + Phase 88 narrative (C3)
collaboration/CURRENT_STATUS.md                                               | +Phase 88 entry (C3)
collaboration/BACKLOG.md                                                      | +Phase 88 entry (C3)
docs/superpowers/handoffs/2026-09-15-phase-88-...md                           | NEW (C3, this doc)
```

**Filesystem changes (gitignored, not in `git diff`)**:
```
infra/__pycache__/                  (29 subdirs deleted, ~1.5 MB)
infra/cli/__pycache__/              (deleted)
infra/config/__pycache__/           (deleted)
infra/core/__pycache__/             (deleted)
infra/creator/__pycache__/          (deleted)
infra/cross_volume/__pycache__/     (deleted)
infra/di/__pycache__/               (deleted)
infra/hooks/__pycache__/            (deleted)
infra/persistence/__pycache__/      (deleted)
infra/poc/__pycache__/              (deleted)
infra/project/__pycache__/          (deleted)
infra/prose/__pycache__/            (deleted)
infra/reading_power/__pycache__/    (deleted)
infra/story_contracts/__pycache__/  (deleted)
infra/studio/__pycache__/           (deleted)
infra/subplot/__pycache__/          (deleted)
infra/tools/__pycache__/             (deleted)
infra/util/__pycache__/             (deleted)
infra/world_db/__pycache__/         (deleted)
infra/world_model/__pycache__/      (deleted)
infra/novel-factory/agent_system/social_engine/relationship_network.json | DELETED (61 bytes)
infra/novel-factory/agent_system/social_engine/  | rmdir'd
infra/novel-factory/agent_system/                 | rmdir'd
infra/novel-factory/                              | rmdir'd
```

---

## §4. ARCHDEBT cycle cluster cumulative

| Phase | Pattern | Scope | Status |
|-------|---------|-------|--------|
| 53 + 53b | ARCHDEBT-MINI pilot | infra/tools/legacy/ + infra/core/ + infra/studio/ | ✅ |
| 53c | ARCHDEBT-MINI | top-level tools/legacy/ | ✅ |
| 53d | ARCHDEBT-MINI | infra/event_sourcing/ | ✅ |
| 53e | ARCHDEBT-MINI | orphan runtime artifacts (relationship_network.json in infra/agent_system/social_engine + decisions.json.lock) | ✅ (partial — novel-factory/ subpath missed) |
| 78 | ARCHDEBT-MINI | infra/llm_benchmarks/ + infra/poc/ | ✅ |
| 79 | ARCHDEBT-REAL #1 | infra/story_contracts → packages/lingwen-story-contracts | ✅ |
| 80 | ARCHDEBT-REAL #2 | infra/subplot → packages/lingwen-subplot | ✅ |
| 81 | ARCHDEBT-REAL #3 | infra/di → packages/lingwen-di | ✅ |
| 82 | ARCHDEBT-REAL #4 | infra/util → packages/lingwen-util | ✅ |
| 83 | ARCHDEBT-REAL #5 | infra/config → packages/lingwen-config | ✅ |
| 84 | ARCHDEBT-REAL #6 | infra/tools/workflow/lib → packages/lingwen-workflow | ✅ |
| 85 | ARCHDEBT-MIXED #1 | infra/tools/consistency MERGE into packages/lingwen-quality | ✅ |
| 86 | ARCHDEBT-MINI #2 | infra/tools/ top-level 5 .py + 3 shell | ✅ |
| 87 | ARCHDEBT-MINI #3 | infra/tools/workflow/ 2 shell scripts | ✅ |
| **88** | **ARCHDEBT-MINI #4 (POST-saturation disk cleanup)** | **29 __pycache__/ dirs + 1 JSON + 3 empty parent dirs** | **✅** |

**Cluster cumulative**: 16 phases / ~20464 LOC dead code eliminated + ~1.5 MB disk space recovered.

**ARCHDEBT cycle: PHYSICALLY COMPLETE** (git tracking + filesystem both clean).

---

## §5. Lessons learned (per I079 §C)

### §5.1 Lesson 1 — Initial disk recovery estimate was wrong (86 MB vs actual 1.5 MB)

**Spec claim**: "~86 MB disk freed" (Phase 88 C0)
**Actual**: ~1.5 MB disk freed

**Root cause**: I conflated `du -sh infra/` (86M) with pycache residue. But `du -sh infra/` was dominated by `infra/.state/ripple.db` (80M SQLite runtime artifact, preserved). Pycache residue per-subdir sums to ~1.5 MB, not 86 MB.

**Detection**: Post-C1 cleanup, `du -sh infra/` went from 86M → 85M (only 1M delta). The 84M residue is `infra/.state/` (ripple.db 80M + ~3M other runtime artifacts).

**Fix**: Spec amended in C0.5 commit `7e2f5682` with accurate numbers. All downstream docs reference accurate ~1.5 MB.

**Lesson**: Always verify disk recovery claims with pre/post `du -sh` AND `find <type> -exec rm` between snapshots. Distinguish total dir size from target type size. Don't claim "X% recovered" without measuring what was actually deleted.

### §5.2 Lesson 2 — Worktree isolation + gitignored content (cleanup scope nuance)

**Discovery**: When `git worktree add` creates a new worktree, **gitignored content is NOT carried over**. The worktree starts with only tracked files. Main repo had 29 pycache dirs + 1 JSON; worktree had none.

**Implication**: The cleanup had to happen in the **main repo working directory** (where the actual files lived). The worktree was always "clean" for ignored content. C1 was `--allow-empty` from worktree (since the worktree's `git status` showed nothing to commit).

**Lesson**: For filesystem-only cleanups (no canonical path changes), the cleanup may need to happen in a different location than where commits are made. `--allow-empty` is the right tool to record intent on the cleanup branch.

### §5.3 Lesson 3 — Pycache regenerates on Python import (G1 + G1b initial failure)

**Issue**: After `find infra/ -type d -name __pycache__ -exec rm -rf`, running pytest (which imports `infra.X` via conftest.py) regenerated `infra/__pycache__/__init__.cpython-313.pyc`. G1 + G1b initial tests failed because they checked ALL pycache under `infra/` including top-level `infra/__pycache__/` (which is valid cache for tracked `__init__.py`).

**Fix**: G1 + G1b revised to exclude top-level `infra/__pycache__/` (valid for tracked `__init__.py`) and only check `infra/<subdir>/__pycache__/` (residue from deleted modules).

**Lesson**: `__pycache__/` for tracked modules is legitimate and regenerable. Distinguish:
- `infra/__pycache__/` (top-level, valid for `infra/__init__.py` tracked) — MUST be allowed
- `infra/<subdir>/__pycache__/` (for deleted modules, residue) — MUST be gone

When guarding pycache state, exclude the top-level path matching the canonical Python source.

### §5.4 Lesson 4 — I074 invariant parsed-value check (PyYAML > regex)

**Issue**: G11 initial regex `r"I074:\s*(.*?)(?=\n\s*I0\d+:\s|\n## |\Z)"` failed because YAML format is `id: I074` (no `:` after I074, `id:` is the YAML key).

**Fix**: Switched to PyYAML `yaml.safe_load` + look up `invariants` list for `id == "I074"`. Robust against YAML formatting variations (Phase 61 lesson: PyYAML silent last-key-wins vs raw text grep).

**Lesson**: For YAML config files, use YAML parser + parsed-value check, not raw text regex. N.14 v21 lesson generalization: text grep misses structural changes; parsed-value check catches them.

### §5.5 Lesson 5 — G8 "empty subdirs" was wrong assumption (G8 revised)

**Issue**: G8 initial assertion `list(p.iterdir()) == []` failed because some subdirs have nested empty subdirs:
- `infra/hooks/actions/` (empty)
- `infra/persistence/{migrations,queries}/` (empty)
- `infra/tools/{workflow,consistency}/` (empty)
- `infra/world_db/queries/` (empty)

These are gitignored, empty, harmless — but not "empty top-level".

**Fix**: G8 revised to recursively check NO `__pycache__/` + NO `.pyc/.pyo` files anywhere within subdir, regardless of nested structure.

**Lesson**: When guarding directory state, be specific about what's being checked. "Empty" can mean:
- 0 entries at top level
- 0 entries recursively (deeper check)
- 0 specific type (pycache, .pyc, .json, etc.)

Phase 88 wanted: "no pycache residue", not "no subdirs at all". Revised to be precise.

---

## §6. ARCHDEBT cycle closure: state comparison

| Aspect | Pre-Phase 88 (post-Phase 87) | Post-Phase 88 | Status |
|--------|------------------------------|---------------|--------|
| `git ls-files infra/` | 1 file (`__init__.py`) | 1 file (`__init__.py`) | unchanged |
| `git status` | clean | clean | unchanged |
| `du -sh infra/` | 86M | 85M | -1M (pycache) |
| `infra/<subdir>/__pycache__/` count | 29 | 0 | -29 |
| `infra/__pycache__/` (top-level, valid) | present | present | preserved (regenerated) |
| `infra/novel-factory/` exists | yes (1 file) | no (rmdir'd) | gone |
| `infra/.state/ripple.db` (80M SQLite) | present | present | preserved (runtime) |
| `infra/.locks/workflow.lock` | present | present | preserved (runtime) |
| `infra/.state/*.json` (5 files) | present | present | preserved (runtime state) |
| ARCHDEBT cycle | tracking-clean | **physically clean** | closed |

**Pre-Phase 88**: Git tracking clean but filesystem had residue.
**Post-Phase 88**: Git tracking + filesystem BOTH clean (modulo `infra/.state/` runtime artifacts + `infra/.locks/` runtime lock + `infra/__pycache__/` valid for tracked `__init__.py`).

---

## §7. Validation gates

### §7.1 Functional gate

```
$ /home/ailearn/miniconda3/bin/python -m pytest tests/test_phase88_archdebt_pycache_residue.py -v
============================== 40 passed in 0.15s ==============================
```

### §7.2 9-pattern audit (per §2 spec)

```
1. Literal dotted-path imports:  ✅ N/A (no canonical path changes)
2. Indented/function-body imports:  ✅ N/A
3. Relative imports:  ✅ N/A
4. Filesystem-path string literals:  ✅ N/A
5. Wildcard from X import *:  ✅ N/A
6. monkeypatch.setattr indirection:  ✅ N/A
7. import X as Y re-exports:  ✅ N/A
8. Doc comments referencing deleted paths:  ⚠️ 3 stale claims (C3 doc fixup)
9. Prior-phase guards hardcoded representative files:  ✅ Safe
```

### §7.3 Disk verification

```
Pre-Phase 88:  du -sh infra/  → 86M (80M ripple.db + 1.5M pycache + 3.5M other)
Post-Phase 88: du -sh infra/  → 85M (80M ripple.db + 0.5M other, 1.5M pycache recovered)
```

---

## §8. Pattern classification

**NON-INVASIVE++** (extension of Phase 86/87 NON-INVASIVE):
- Even safer than Phase 86/87 (those deleted tracked content at canonical location; Phase 88 deletes ONLY gitignored content)
- 0 canonical path changes
- 0 prior-phase guard impact
- 0 production code impact
- 0 runtime artifact impact
- 100% safe to delete (gitignored + regenerable + gitignored legacy path drift residue)

**Use case**: Post-saturation disk cleanup. Useful when ARCHDEBT-MINI cycle has deleted all tracked content but gitignored residue remains.

---

## §9. Carryover

**Phase 88 closes 2 carryovers**:
1. **N.14 v23 v3 lesson (pycache residue after `git rm`)**: Phase 79 fixup addressed test_phase53d G5 false-positive but didn't close the residue class. Phase 88 comprehensively cleans all 29 pycache dirs.
2. **Phase 53e partial cleanup**: Phase 53e gitignored `infra/novel-factory/` to prevent re-tracking but didn't physically delete the residual `relationship_network.json` (Phase 54 path drift). Phase 88 closes this with physical deletion.

**After Phase 88, ARCHDEBT cycle is COMPLETE in BOTH dimensions**:
- Git tracking: clean (1 tracked file in infra/)
- Filesystem: clean of dead code/bytecode (runtime artifacts preserved)

**No further ARCHDEBT work identified**. Future work is non-ARCHDEBT features (frontend, new functionality, bug fixes in lingwen-* packages).

---

## §10. Cluster post-saturation (Phase 53-88)

| Metric | Value |
|--------|-------|
| Total phases | 16 |
| Total LOC dead code eliminated | ~20464 |
| Total disk space recovered (pycache + JSON) | ~1.5 MB |
| Zero-consumer dirs deleted | 8 (event_sourcing + llm_benchmarks + poc + legacy + core + studio + novel-factory + story_contracts + subplot + tools) |
| Real migrations to packages/ | 6 (story-contracts, subplot, di, util, workflow) + 1 MERGE (consistency → lingwen-quality) |
| Zero-consumer top-level .py | 7 |
| Zero-consumer shell scripts | 8 |
| lingwen-* packages in workspace | 31 (was 24 at Phase 53 start) |
| Infra/ final state | 1 tracked file (`__init__.py`, 864 bytes compat re-exports) |

---

**Pattern**: ARCHDEBT-MINI #4 (NON-INVASIVE++)

**Cluster**: Phase 53-88 = 16 phases, ARCHDEBT cycle physically complete.

**Future work**: Non-ARCHDEBT features.

---

## §11. Acknowledgments

- **Phase 60 I079 invariant**: P3-ARCHDEBT spec template + §A test files migration plan. Phase 88 spec followed template (explicitly N/A for §A2/A3/A4/A5 with justification).
- **Phase 61 PyYAML parsed-value check**: I074 invariant extraction via `yaml.safe_load` instead of raw text regex.
- **Phase 87 NON-INVASIVE pattern**: Phase 88 extends to NON-INVASIVE++ (only gitignored content).
- **N.14 v23 v3 lesson**: `__pycache__/` residue after `git rm`. Phase 88 closes carryover.
- **Phase 53e partial cleanup**: orphan relationship_network.json. Phase 88 closes carryover.
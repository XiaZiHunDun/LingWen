# Phase 19+ Sub1 — World Model → Domain Migration Design

**Branch**: `phase-19-sub1`
**Date**: 2026-09-01
**Type**: Carryover from Phase 18 (CLOSED, see `2026-09-01-phase-18-business-boundary-cleanup-handoff.md`)

---

## 1. Summary

Close the WorldSnapshot API divergence gap between `infra/world_model/data_structures.py` and `packages/lingwen-core/domain/ripple.py`, migrate `Plot` data class to lingwen-core/domain, make both `infra/world_model/` and `infra/subplot/` 1-line PHASE-COMPAT shims, and migrate 10+ consumer files to use `lingwen_core.domain.*` directly.

**Scope (per user clarification)**:
- **(1) Fill the gap** — `WorldSnapshot.to_dict()` / `from_dict()` + `active_subplots` + `physical` + `mental` fields
- **(2) Migrate `Plot` to domain** — new `packages/lingwen-core/domain/subplot.py`
- **(3) Migrate 10+ consumers** — atomic 1-file commits from `infra.world_model.*` to `lingwen_core.domain.*`

**Out of scope**:
- Migrating `infra/world_model/{engine,lifecycle,links,queries,registry,snapshot_diff,snapshot_store,...}.py` (behavior services)
- Migrating `infra/subplot/{queries,registry,lifecycle}.py` (behavior services)
- Sub2/Sub3 (consistency + agent_system PHASE-COMPAT shim cleanup)

---

## 2. Context (Why Now)

Phase 18 (Business Boundary + Interface Cleanup) closed with 3 sub-phases deferred to Phase 19+:

> **Sub1**: `infra/world_model.*` → `lingwen_core.domain` migration
> - First step: add `to_dict()` / `from_dict()` + `active_subplots` + `physical` / `mental` fields to `lingwen_core.domain.WorldSnapshot`
> - Then: migrate 10+ consumers
> - Then: optionally delete `infra/world_model/` if empty

Phase 18 verify-before-design found that `lingwen_core.domain.WorldSnapshot` is a **strict subset** of `infra.world_model.data_structures.WorldSnapshot`:

| Feature | infra (current) | lingwen-core (Phase 18.1) |
|---------|-----------------|---------------------------|
| `to_dict()` / `from_dict()` | ✅ | ❌ MISSING |
| `active_subplots` field | ✅ | ❌ MISSING |
| `physical` field | ✅ | ⚠️ Type in `domain/chapter.py` but not referenced |
| `mental` field | ✅ | ⚠️ Type in `domain/chapter.py` but not referenced |
| `Ripple.to_dict/from_dict` | n/a | ✅ Exists (pattern to mirror) |
| `KeyPoint.to_dict/from_dict` | n/a | ✅ Exists |
| `Relation.to_dict/from_dict` | n/a | ✅ Exists |

**Critical re-discovery during Phase 19+ design exploration**: `KeyPoint`, `Relation`, `Ripple` (all in `lingwen-core/domain/`) ALREADY have `to_dict()` / `from_dict()` methods. The Phase 18.1 DDD-purity claim was inconsistent. **`WorldSnapshot` is the only domain entity lacking these methods** — not for DDD reasons, but as oversimplification during Phase 18.

`PhysicalLine` and `MentalLine` are already in `packages/lingwen-core/domain/chapter.py` (re-exported via `lingwen_core.domain.__init__`). They just need to be **referenced as fields** in `WorldSnapshot`.

---

## 3. Architecture

### 3.1 Dependency Direction (After Phase 19+ Sub1)

```
infra/*   ──→ packages/lingwen-core/*    (infra depends on domain, DDD-correct)
apps/*    ──→ infra/* ──→ lingwen-core   (apps still go through compat layer)
tests/*   ──→ ? (mixed: some migrated, some still use shims)

Current: lingwen-core → infra is empty (no upward dependency)
Target:  same — lingwen-core remains infra-free
```

### 3.2 DDD Position

`packages/lingwen-core/domain/` is the canonical source for WorldSnapshot / Ripple / Plot / Chapter / Volume / Character / Foreshadow. It already has `KeyPoint.to_dict/from_dict` and `Ripple.to_dict/from_dict` methods, so adding them to `WorldSnapshot` follows the established pattern.

The "DDD purity = no persistence methods in domain" principle from Phase 18.1 handoff is **partially abandoned** in favor of consistency: existing entities have serialization methods on the dataclass; `WorldSnapshot` joins them. Future Phase 19.x may extract a `persistence/` adapter layer if desired.

---

## 4. Components

| Component | Before | After | Commit |
|-----------|--------|-------|--------|
| `packages/lingwen-core/src/lingwen_core/domain/ripple.py::WorldSnapshot` | subset | + `to_dict()` / `from_dict()` + `active_subplots: tuple[Any, ...]` + `physical: PhysicalLine` + `mental: MentalLine` | T1+T2+T3 |
| `packages/lingwen-core/src/lingwen_core/domain/subplot.py` | **does not exist** | NEW: `Plot` + `MAX_ACTIVE_SUBPLOTS` + `PlotStatus` + `PlotType` + `PlotPurpose` (copies from infra) | T4 |
| `packages/lingwen-core/src/lingwen_core/domain/__init__.py` | no subplot export | + re-export of subplot symbols | T4 |
| `infra/world_model/data_structures.py` | full impl | 1-line shim re-export | T17 |
| `infra/world_model/__init__.py` | full exports | 1-line shim re-exports | T17 |
| `infra/subplot/data_structures.py` | full impl + helpers (`add_subplot`, `get_active_subplots`, `subplots_count`) | split: data class part → 1-line shim; helpers stay (use shim's Plot) | T5 |

### 4.1 Files NOT Migrated This Phase

These stay in `infra/` as back-compat shim consumers (use domain via shim):

- `infra/world_model/{engine,lifecycle,links,queries,registry,snapshot_diff,snapshot_store,character_snapshot,foreshadow_snapshot,key_point_graph}.py` — behavior services
- `infra/subplot/{queries,registry}.py` — behavior services

They will continue to import from local `infra.subplot.data_structures` / `infra.world_model.data_structures` which now re-export from `lingwen_core.domain`. Migration of these files is deferred to Phase 19.x or later.

---

## 5. Data Flow

### 5.1 Before Migration (Current State)

```python
# tests/subplot/test_subplot_integration.py
from infra.world_model import WorldSnapshot, KeyPoint, PhysicalLine  # infra direct
from infra.subplot.data_structures import Plot, PlotStatus, PlotType  # Plot infra direct

snap = WorldSnapshot(...)  # full API
snap_dict = snap.to_dict()  # works
snap2 = WorldSnapshot.from_dict(snap_dict)  # works
```

### 5.2 After Migration (Phase 19+ Sub1 Done)

```python
# tests/subplot/test_subplot_integration.py (migrated)
from lingwen_core.domain.ripple import WorldSnapshot
from lingwen_core.domain.common import KeyPoint
from lingwen_core.domain.chapter import PhysicalLine
from lingwen_core.domain.subplot import Plot, PlotStatus, PlotType

snap = WorldSnapshot(...)  # same API, different import
snap_dict = snap.to_dict()  # same method
snap2 = WorldSnapshot.from_dict(snap_dict)  # same method

# Old imports STILL WORK (1-line shim):
from infra.world_model import WorldSnapshot, KeyPoint  # OK (re-exports from lingwen_core.domain)
from infra.subplot.data_structures import Plot  # OK (re-exports from lingwen_core.domain.subplot)
```

### 5.3 Field Mapping

`infra.world_model.data_structures.WorldSnapshot` field set → `lingwen_core.domain.ripple.WorldSnapshot` field set:

| infra field | lingwen-core field | Notes |
|-------------|-------------------|-------|
| `snapshot_id` | `snapshot_id` | identical |
| `chapter` | `chapter` | identical |
| `timestamp` | `timestamp` | identical |
| `nodes` | `nodes` | identical type (`dict[NodeId, KeyPoint]`) |
| `relations` | `relations` | identical type (`tuple[Relation, ...]`) |
| **`physical`** | **NEW: `physical`** | type `PhysicalLine` (now from `domain/chapter.py`) |
| **`mental`** | **NEW: `mental`** | type `MentalLine` (now from `domain/chapter.py`) |
| `active_ripples` | `active_ripples` | identical type |
| **`active_subplots`** | **NEW: `active_subplots`** | type `tuple[Any, ...]` (Plot via shim or direct import) |
| `world_mood` | `world_mood` | identical |
| `consistency_hash` | `consistency_hash` | identical |

---

## 6. Error Handling

Phase 19+ Sub1 is a **mechanical migration** — behavior is preserved. No new error types.

**Serialization contract**:
- `from_dict({})` or missing required field → `KeyError` (matches `Ripple.from_dict` behavior)
- `from_dict({...})` with invalid `NodeId` format → `ValueError` (via `NodeId.from_string`)
- `from_dict({...})` with unknown `RippleState` → `ValueError` (via `RippleState(value)`)
- Default field fallback: `.get(key, default)` for backward-compat with pre-Phase 1.2 JSON (no `active_subplots` key)

**Round-trip guarantee**:
- `WorldSnapshot.from_dict(snap.to_dict())` MUST equal `snap` (frozen dataclass equality)
- Exceptions: `consistency_hash` is re-computed in `__post_init__`, so it matches after re-instantiation (same as Ripple / KeyPoint / Relation behavior)

**Validation tests** (already exist in `tests/subplot/test_subplot_integration.py::TestWorldSnapshotSubplots`):
1. `test_world_snapshot_with_subplots_roundtrip` — `snap2 == snap` after round-trip
2. `test_world_snapshot_subplots_consistency_hash_changes` — hash differs when subplot added
3. `test_world_snapshot_backward_compat_no_subplots` — `from_dict({...without active_subplots...})` defaults to `()`

---

## 7. Testing

### 7.1 Verification Gates

| Gate | Command | Expected | Trigger |
|------|---------|----------|---------|
| Backend core (lingwen-core) | `python -m pytest packages/lingwen-core/tests/` | 55 pass + N NEW | T1, T4 |
| Backend subplot | `python -m pytest tests/subplot/` | 19 pass + 5 NEW (or pre-existing fail → pass) | T6, T7-T16 |
| Backend consistency | `python -m pytest tests/consistency/` | unchanged | regression check |
| Backend world_model | `python -m pytest tests/world_model/` | unchanged (shim works transparently) | regression check |
| Backend infra | `python -m pytest tests/infra/` | unchanged | regression check |
| Lint: ruff | `ruff check infra/ packages/lingwen-core/` | 0 | each commit |
| Lint: import-linter | `lint-imports` (3 contracts) | KEPT | T5, T17 (avoid new lingwen-core → infra imports) |
| Lint: knip | `cd apps/dashboard && pnpm exec knip` | 0 lines | unchanged (no JS/TS touched) |
| ESLint | `cd apps/dashboard && pnpm eslint .` | 0 | unchanged |
| vue-tsc | `cd apps/dashboard && pnpm tsc --noEmit` | 0 | unchanged |
| Vitest | `cd apps/dashboard && pnpm vitest run` | 1762 + 1 skipped | unchanged (no JS/TS touched) |

### 7.2 New Tests Required

| Location | New Tests | Commit |
|----------|-----------|--------|
| `packages/lingwen-core/tests/test_domain.py` | `WorldSnapshot::to_dict/from_dict/round-trip` (3 tests) | T3 |
| `packages/lingwen-core/tests/test_domain.py` | `WorldSnapshot::physical/mental_defaults` (2 tests) | T3 |
| `packages/lingwen-core/tests/test_domain.py` | `WorldSnapshot::active_subplots_default + backward-compat` (2 tests) | T3 |
| `packages/lingwen-core/tests/test_subplot.py` (NEW) | `Plot.from_dict/to_dict/round-trip` (3 tests) | T4 |
| `packages/lingwen-core/tests/test_subplot.py` | `Plot status state-machine guards` (2 tests) | T4 |

Note: T1+T2.a+T2.b are pure implementation — T3 bundles all 7 tests for the WorldSnapshot fill. T4 bundles 5 tests for the Plot move.

**No new JS/TS tests required** — frontend untouched.

### 7.3 Pre-existing Tests That Become Green

Per Phase 18 handoff §"Finding B":
- `tests/subplot/test_subplot_integration.py::TestWorldSnapshotSubplots::test_world_snapshot_with_subplots_roundtrip` (currently fails — `WorldSnapshot.from_dict` missing on lingwen-core)
- 4 more in `tests/subplot/test_subplot_integration.py` — same root cause

**Note**: These tests currently import from `infra.world_model` (which has `to_dict/from_dict`). They "work" today only because `infra.world_model` is the source of truth. After T1-T3 closes the gap, **either**:
- Tests can be migrated to `lingwen_core.domain.ripple` (T7+) without regressing — they should pass because lingwen-core version now matches
- OR tests can stay on `infra.world_model` (now a shim) — shim should still pass tests because shim re-exports from lingwen-core which now has full API

---

## 8. Commit Plan

**18 atomic commits**, each touching ≤3 files, each compiles + tests pass individually:

| # | Commit | Files | Purpose |
|---|--------|-------|---------|
| T1 | `feat(lingwen-core): WorldSnapshot.to_dict/from_dict` | `domain/ripple.py` | Add serialization methods matching Ripple pattern |
| T2.a | `feat(lingwen-core): WorldSnapshot.physical/mental fields` | `domain/ripple.py` | Add physical/mental fields with defaults from `domain/chapter.py` |
| T2.b | `feat(lingwen-core): WorldSnapshot.active_subplots field` | `domain/ripple.py` | Add active_subplots field (type `tuple[Any, ...]` until T4) |
| T3 | `test(lingwen-core): WorldSnapshot serialization tests` | `tests/test_domain.py` | 7 NEW tests for to_dict/from_dict + field defaults |
| T4 | `feat(lingwen-core): subplot module + Plot entity` | `domain/subplot.py` (NEW), `domain/__init__.py` | Copy Plot + MAX_ACTIVE_SUBPLOTS + Enums from infra |
| T5 | `refactor(infra): subplot.data_structures shim` | `infra/subplot/data_structures.py` | 1-line re-export from `lingwen_core.domain.subplot` (keep helpers `add_subplot`, `get_active_subplots`, `subplots_count` locally) |
| T6 | `chore(lingwen-core): update active_subplots type annotation` | `domain/ripple.py` | Change `active_subplots: tuple[Any, ...]` → `tuple[Plot, ...]` after T4 provides `Plot` |
| T7 | `refactor(tests): subplot_integration migrate to lingwen_core.domain` | `tests/subplot/test_subplot_integration.py` | 1st consumer migrated |
| T8 | `refactor(tests): subplot_data_structures migrate to lingwen_core.domain` | `tests/subplot/test_subplot_data_structures.py` | 2nd consumer |
| T9 | `refactor(tests): consistency/checkers migrate to lingwen_core.domain` | `tests/consistency/checkers/test_foreshadow_ripple_alignment.py` | 3rd |
| T10 | `refactor(tests): consistency/checkers migrate to lingwen_core.domain` | `tests/consistency/checkers/test_pacing_ripple_integration.py` | 4th |
| T11 | `refactor(tests): world_model tests migrate` | `tests/world_model/test_world_snapshot.py` | 5th |
| T12 | `refactor(tests): world_model tests migrate` | `tests/world_model/test_integration.py` | 6th |
| T13 | `refactor(tests): world_model tests migrate` | `tests/world_model/test_phase2_integration.py` | 7th |
| T14 | `refactor(tests): world_model tests migrate` | `tests/world_model/test_snapshot_diff.py` | 8th |
| T15 | `refactor(tests): world_model tests migrate` | `tests/world_model/test_snapshot_store.py` | 9th |
| T16 | `refactor(tests): world_model tests migrate` | `tests/world_model/test_key_point_graph.py` | 10th |
| T17 | `refactor(infra): world_model shim` | `infra/world_model/__init__.py`, `data_structures.py` | 1-line re-exports from `lingwen_core.domain.{common,ripple}` |
| T18 | `docs(phase-19): handoff + architecture.yml + CLAUDE.md` | docs | Close phase |

**Total estimated**: 18 commits

**Sequencing rationale**:
1. Domain fill (T1-T3) — unlocks future consumers
2. Plot to domain (T4-T6) — typed `active_subplots` requires `Plot` available
3. Consumer migration (T7-T16) — atomic 1-file-per-test
4. Shim creation (T17) — only after all consumers migrated
5. Docs close (T18)

---

## 9. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| **Lingwen-core creates new dependency on infra** via `from infra.subplot.data_structures import Plot` | Medium | Blocks Phase 19+ (DDD violation) | T6 uses `from lingwen_core.domain.subplot import Plot` for type annotation; runtime `Any` tolerance avoided |
| **`from_dict` behavior diverges** between infra and lingwen-core versions | Low | Tests fail | T3 has 7 new tests covering round-trip; T7-T16 each verifies migration is mechanical |
| **Consistency hash differs** between infra and lingwen-core | Low | `snap != snap2` round-trip fails | T1 preserves `compute_consistency_hash()` logic verbatim — physical/mental/subplots inclusion is deterministic |
| **Behavior services (`infra/subplot/queries.py` etc.) break** when shim removes real impl | Low | Subplot queries fail | T5 keeps `add_subplot`, `get_active_subplots`, `subplots_count` in infra as thin wrappers; shim only re-exports data classes |
| **Pre-existing tests** in `tests/world_model/` depending on infra-specific names | Medium | Tests fail after migration | Each migration commit (T11-T16) verifies tests pass before moving to next commit |

**Highest-likelihood risk**: the `active_subplots` field — `Plot` import cycle. Mitigated by TypeScript-style TYPE_CHECKING pattern OR by completing T4 BEFORE T2.b.

---

## 10. Success Criteria

### 10.1 Must-have

- [ ] `WorldSnapshot.to_dict()` / `from_dict()` defined in `lingwen_core.domain.ripple`
- [ ] `WorldSnapshot.active_subplots` field with default `()` exists
- [ ] `WorldSnapshot.physical` + `mental` fields with defaults exist
- [ ] `lingwen_core.domain.subplot.Plot` exists with `to_dict()` / `from_dict()`
- [ ] `infra/world_model/data_structures.py` + `__init__.py` become 1-line shims
- [ ] `infra/subplot/data_structures.py` shim re-exports from `lingwen_core.domain.subplot`
- [ ] 10+ test files migrated from `infra.world_model` / `infra.subplot` to `lingwen_core.domain`
- [ ] All 5 Phase 18-blocked `tests/subplot/test_subplot_integration.py::TestWorldSnapshotSubplots` tests pass via lingwen-core-direct OR via shim
- [ ] All 18 commits on `phase-19-sub1` branch
- [ ] Branch merged to master via `git checkout master && git merge --ff-only phase-19-sub1`
- [ ] All verification gates (§7.1) green

### 10.2 Should-have

- [ ] Updated `.lingwen/architecture.yml` to mark "world model → domain" as production-grade (DP-04 territory) — inside repo
- [ ] Updated CLAUDE.md with Phase 19 entry (version `19.1`) — inside repo
- [ ] Handoff doc created at `docs/superpowers/handoffs/2026-09-01-phase-19-sub1-world-model-domain-handoff.md` — inside repo
- [ ] MEMORY.md updated with v19.1 + carryover notes (Sub2/Sub3 + subplot behavior migration) — **outside repo** (`/home/ailearn/.claude/projects/-home-ailearn-projects-LingWen/memory/`), best-effort done in this phase but technically out of phase scope

### 10.3 Nice-to-have (Future Phase 19.x)

- [ ] Migrate `infra/world_model/{engine,lifecycle,...}.py` to `lingwen_core.use_cases` or similar application layer
- [ ] Migrate `infra/subplot/{queries,registry}.py` similarly
- [ ] Extract `persistence/` adapter layer to wrap domain entities (replaces on-entity to_dict/from_dict)
- [ ] Delete `infra/world_model/` and `infra/subplot/` shim directories

---

## 11. Lessons Applied From Phase 18

Re-confirmed Phase 18 lessons (`docs/superpowers/handoffs/2026-09-01-phase-18-business-boundary-cleanup-handoff.md`):

1. **Verify-before-design (N.14 lesson 1)** — Phase 19+ design re-verified that gap is much smaller than handoff described (only WorldSnapshot missing, not all domain entities)
2. **PHASE-COMPAT shim detection** — `infra/world_model` + `infra/subplot` will become 1-line shims (`# PHASE-COMPAT: Phase 19+ — DELETE after Phase 19.x`)
3. **API divergence in domain migration** — Resolved by T1-T3 closing the gap (full API match), not by adding persistence adapter
4. **Atomic 1-task-per-commit** — 18 commits, ≤3 files per commit, each compiles + tests pass

---

## 12. Carryover to Phase 19.x+ (After Phase 19+ Sub1)

- **Sub1 remaining**: behavior services in `infra/world_model/` and `infra/subplot/` (`engine`, `lifecycle`, `links`, `queries`, `registry`, `snapshot_diff`, `snapshot_store`, `character_snapshot`, `foreshadow_snapshot`, `key_point_graph`, subplot queries/registry) still use `infra.*` internally — migrate to application layer (Phase 19.x Sub2)
- **Sub2**: `infra/consistency/*` PHASE-COMPAT shim cleanup (30+ consumers) — see Phase 18 handoff
- **Sub3**: `infra/agent_system/*` PHASE-COMPAT shim cleanup (similar)
- **Future v20+**: `infra/exports/*` → `packages/lingwen-storage` migration (separate concern)
- **Future v20+**: Phase 114 prod preview regression (still accepted)

---

## 13. Document Trace

- **Phase 18 handoff**: `docs/superpowers/handoffs/2026-09-01-phase-18-business-boundary-cleanup-handoff.md`
- **Verify-before-design for Phase 18**: see Phase 18 handoff §"Verify-Before-Design Findings" Finding B
- **MEMORY.md**: `/home/ailearn/.claude/projects/-home-ailearn-projects-LingWen/memory/MEMORY.md` — v18 entry, Phase 19+ carryover
- **Architecture config**: `.lingwen/architecture.yml` (will be updated at T18)
- **Project CLAUDE.md**: `/home/ailearn/projects/LingWen/CLAUDE.md` (will be updated at T18)

# lingwen-world-model

LingWen · World Model (Ripple + Subplot + Snapshot behavior engine).

Phase 35 (v34.0) canonical home for what was previously `infra/world_model/*`
(10 modules, 2282 lines, 37 public symbols) plus `infra/subplot/helpers.py`
(52 lines, 3 functions).

## Public API (37 symbols via `lingwen_world_model.__all__`)

### Canonical re-exports (from `lingwen_core.domain.*`)
`WorldSnapshot` · `Ripple` · `RippleState` · `ResolutionMode` · `MAX_OPEN_RIPPLOTS` ·
`KeyPoint` · `Relation` · `NodeId` · `NodeType` · `PhysicalLine` · `MentalLine` ·
`PlotStatus`

### Behavior services
`RippleEngine` · `RippleRegistry` · `KeyPointGraph` · `Contradiction` · `ContradictionKind` ·
`SnapshotStore` · `SnapshotNotFoundError` · `SnapshotIntegrityError` · `SnapshotChange` ·
`ChangeKind` · `EntityKind` · `LinkAction`

### Functions / constants
`detect_unresolved_ripples` · `predict_collapse_risk` · `suggest_resolution_chapter` ·
`link_subplot_to_ripple` · `apply_ripple_resolution` ·
`subplots_count` · `add_subplot` · `get_active_subplots` ·
`RESOLUTION_GRACE_CH` · `COLLAPSE_RISK_THRESHOLD` · `VALID_TRANSITIONS` ·
`can_transition` · `is_terminal` · `diff_snapshots` · `diff_ripples` ·
`diff_subplots` · `has_state_transition` · `RippleNotFoundError` ·
`DuplicateRippleIdError` · `OpenRippleLimitExceeded`

## Dependencies

- `lingwen-core` — canonical domain entities + use cases (Phase 18 ships; `lingwen_core.domain.{chapter, common, ripple, subplot}`)

## Invariant

> **#I050** — `packages/lingwen-world-model/` is the sole implementation package for the LingWen World Model (Ripple + Subplot + Snapshot engine). The path `infra.world_model.*` is forbidden (Phase 35+). Enforced via `tests/test_phase35_world_model.py` (regression guards).

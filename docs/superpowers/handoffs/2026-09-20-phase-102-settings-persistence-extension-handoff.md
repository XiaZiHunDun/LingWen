# Phase 102 — Settings Persistence Extension — Handoff

> **Date**: 2026-09-20
> **Phase**: v59.0 → v60.0
> **Cluster**: REQ-002 v2 #7 (seventh and final sub-project delivered)
> **Type**: Full-stack inline extension (Phase 90-101 mode)
> **Workflow**: Solo repo, no PR, direct commits on master (per 2026-09-15 simplified workflow)

## Summary

Phase 102 extends ProjectSettings with 3 new fields enabling per-chapter illustration control and sustained-failure warning notifications.

## Sub-projects delivered

- ProjectSettings schema + 3 fields + 3 Pydantic validators (fallback_models / chapter_overrides / notify_threshold)
- pipeline.merge_chapter_settings helper (immutable, chapter_num=None fast path)
- pipeline.resolve_model is_fallback param + fallback_models priority (4-tier resolution)
- notifications.record_failure/record_success + threshold warning emit (severity="warning", idempotent)
- pipeline integration: generate_illustration + regenerate_illustration wired with all 3 helpers
- api/illustrations.ts ProjectSettings interface (Pick-based whitelist for chapter_overrides)
- useProjectSettings store 3 fields
- ProjectSettingsIllustration.vue 3 sections (fallback_models + chapter_overrides + notify_threshold)
- 11 new frontend tests (5 component + 6 store)
- 12 regression guards G1-G12
- 2 new invariants I094 + I095

## Validation gates

| Gate | Result |
|------|--------|
| Backend pytest (lingwen-illustrations) | TBD (run final validation) |
| Backend pytest (studio_api settings) | TBD |
| Backend pytest (Phase 102 regression guards) | 12/12 PASS |
| Frontend vitest (ProjectSettingsIllustration) | 30/30 PASS |
| pnpm tsc | 0 new errors (48 pre-existing baseline unchanged) |
| ruff check | clean on introduced |

## Cluster cumulative (Phase 90-102)

13 phases / 1 NEW package (lingwen-illustrations) + 5 carryover closures (Phase 92-95) + **7 REQ-002 v2 sub-projects delivered** (image provider adapters + reference image i2i + ProjectSettings+LRU + notification center + multi-model per provider + atomic provider fallback + **settings persistence extension**).

**REQ-002 v2 FULLY CLOSED** post-Phase 102.

## Future work

- **REQ-004 团队协作**: Long-pending P4 brainstorm session. Team collaboration features (multi-user editing, conflict resolution, permission grading).
- **Phase 102+ (if any)**: Telemetry-driven chain reorder (use failure history to suggest fallback_chain reorder) — gated on Phase 102 failure tracker data accumulation.
- **Per-chapter default_models overrides** (if requested) — extend chapter_overrides whitelist.
- **notify_threshold per event_type** (if requested) — extend to dict[event_type, int].

## Lessons learned

1. **`_warning_emitted` flag needed for threshold idempotency** — spec said "counter stays elevated until reset" but the test "5 failures above threshold → only 1 warning" required an additional flag tracking whether the current streak has warned. Implementer added `_warning_emitted: dict[str, bool]` (cleared by record_success).
2. **`ulid.ULID()` not `ulid.new().str`** — installed python-ulid library uses class API, not the `new()` factory pattern. Matches existing `new_event_id()` helper in same file.
3. **`audit_log` module-level import** — late import suggested by spec for cycle avoidance, but `audit_log` has no notifications dependency, so module-level is required for `monkeypatch.setattr(notifications, "audit_log", ...)`.
4. **Frontend tsconfig uses `Record<number, T>` not strict integer keys** — JSON serialization prevents fractional keys in practice, but worth noting.
5. **TypeScript chapter_overrides requires `Pick` not `Omit`** — `Omit<ProjectSettings, ...>` over-allows fields backend rejects with HTTP 422. Use `Pick<ProjectSettings, 'max_assets' | ...>` to mirror backend whitelist.
6. **Test isolation pattern** — sibling `describe` blocks don't share `beforeEach`. Each new describe block needs its own setup.
7. **Store fetch leaves new fields undefined on old-shape response** — store stores raw API payload, consumer applies defaults via `??` operator. Documented in test + store docstring.

## References

- Spec: `docs/superpowers/specs/2026-09-20-phase-102-settings-persistence-extension-design.md` (459 lines)
- Plan: `docs/superpowers/plans/2026-09-20-phase-102-settings-persistence-extension.md` (1938 lines)

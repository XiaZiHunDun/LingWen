# Phase 98 — ProjectSettings extension + LRU archive handoff

> **Status**: ✅ COMPLETE
> **Date**: 2026-09-18
> **Branch**: master (direct commits per 2026-09-15 simplified workflow)
> **Version**: v56.1 → v56.2

## Summary

Phase 98 extends the ProjectSettings schema from 1 to 4 fields, adds per-type+per-chapter LRU cleanup, and integrates JSONL append-only audit logging. The phase also activates the long-dead `auto_generate` branch in write_workspace.py by ensuring the field is actually persisted.

## Atomic commits (18)

| # | SHA | Subject |
|---|-----|---------|
| 1 | `d65e214c` | docs(phase-98): ProjectSettings extension + LRU archive design |
| 2 | `688a29a9` | docs(phase-98): implementation plan - 18 atomic tasks |
| 3 | `37a07c58` | test(phase-98): project_settings schema migration TDD red |
| 4 | `eb200f96` | feat(phase-98): ProjectSettings 3 new fields + schema back-compat |
| 5 | `a32faf05` | test(phase-98): audit_log TDD red |
| 6 | `02920ff7` | feat(phase-98): audit_log module - JSONL append-only event log |
| 7 | `de13290c` | test(phase-98): lru_cleanup TDD red |
| 8 | `c7b5c5c1` | feat(phase-98): storage.lru_cleanup - per-type+per-chapter LRU |
| 9 | `020f6699` | feat(phase-98): pipeline calls lru_cleanup + audit_log after save_asset |
| 10 | `9816774d` | feat(phase-98): regenerate_illustration records audit event |
| 11 | `5c5e5a75` | test(phase-98): cleanup_route TDD red |
| 12 | `5460f32f` | feat(phase-98): POST /cleanup endpoint + route registration |
| 13 | `583ae4d0` | feat(phase-98): write_workspace auto_generate reads from persisted settings |
| 14 | `c3e0eeb9` | feat(phase-98): ProjectSettingsIllustration update() persists every field |
| 15 | `7752ffa4` | test(phase-98): useProjectSettings PATCH semantics U1-U2 |
| 16 | `caf8ffdb` | feat(phase-98): GenerateIllustrationDialog confirm dialog + G1-G2 tests |
| 17 | `30c99859` | test(phase-98): 13 regression guards G1-G13 + I090 invariant |
| 18 | (this commit) | docs(phase-98): CLAUDE.md v56.1 → v56.2 + I090 + handoff + BACKLOG/CURRENT_STATUS sync |

## What was delivered

### Backend
- **ProjectSettings schema** (`apps/studio_api/routes/project_settings.py`): 1 → 4 fields
  - `default_provider` (Phase 96)
  - `auto_generate: bool = False` (NEW)
  - `max_assets: int = 20` (NEW)
  - `confirm_before_generate: bool = False` (NEW)
  - Pydantic v2 default fill enables back-compat (old yaml with only default_provider loads)
- **storage.lru_cleanup** (`packages/lingwen-illustrations/src/lingwen_illustrations/storage.py:153-216`): 5 → 6 funcs
  - Per-type+per-chapter scope (cover + chapter-NNN directories isolated)
  - max_count > 0 validation (raises StoreError on 0/-1)
  - type=chapter requires chapter_num (raises StoreError on None)
  - Sort ascending by (created_at, id) for deterministic oldest-first
  - Returns list of deleted metadata (oldest first) for UI feedback + audit
- **audit_log module** (`packages/lingwen-illustrations/src/lingwen_illustrations/audit_log.py`): NEW
  - `record_event()` JSONL append-only at `<root>/.lingwen/illustration_audit.jsonl`
  - Best-effort: OSError silently swallowed (audit NEVER blocks pipeline)
  - 4 EventTypes: generation / regeneration / cleanup / deletion
  - Captures: ts / event / asset_id / asset_type / chapter_num / confirmed / bypassed / extra
- **pipeline integration** (`packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py`)
  - generate_illustration: calls lru_cleanup after save_asset + records generation event + per-asset cleanup events
  - regenerate_illustration: records regeneration event
- **POST /cleanup endpoint** (`apps/studio_api/routes/cleanup_route.py`): NEW
  - Body: `{ type: 'cover'|'chapter', chapter_num?: int, dry_run?: bool }`
  - Returns: `{ deleted: [metadata_dicts], remaining: int, dry_run: bool }`
  - 404 missing project / 422 invalid type or chapter / 422 chapter requires chapter_num
  - dry_run computes deletion list without actually deleting
- **write_workspace auto_generate activation** (`apps/studio_api/background.py:69-103`)
  - Was: hardcoded `auto_generate: False` (dead branch since Phase 90)
  - Now: `settings.auto_generate` from persisted yaml (Phase 96 schema only had default_provider)

### Frontend
- **ProjectSettingsIllustration.vue** (`apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue`)
  - Phase 96 only persisted `default_provider`. Three new fields (auto_generate / max_assets / confirm_before_generate) only updated modelValue but never persisted.
  - Phase 98: `update()` now emits + saves (PATCH semantics via existing useProjectSettings.save which does `{...current, ...partial}`)
  - `on_provider_change` simplified to one-line `update()` call (deduplicates emit + save path)
- **GenerateIllustrationDialog.vue** (`apps/dashboard/src/components/illustrations/GenerateIllustrationDialog.vue`)
  - submit() checks `store.settings.confirm_before_generate`
  - If true: shows `window.confirm('将使用 <provider> 生成插图。继续？')`
  - User accepts → emit generate. User cancels → no emit.
  - Front-end only interception (backend audit log records bypassed state but doesn't reject)
- **useProjectSettings PATCH semantics tests** (`apps/dashboard/src/stores/useProjectSettings.spec.js`): U1-U2
  - U1: save({max_assets: 5, auto_generate: true}) merges with current, preserves other fields
  - U2: save({default_provider: 'openai'}) preserves max_assets

### Tests
- **S1-S5** (5 NEW): schema migration back-compat (old yaml defaults fill, partial yaml merges, full round-trip, malformed/missing yaml defaults)
- **A1-A4** (4 NEW): audit_log append + read back + OSError swallowed + unicode safe
- **L1-L12** (12 NEW): lru_cleanup max_count bounds + cover scope + chapter scope + idempotent + tie-break
- **Cleanup endpoint tests** (5 NEW): success + dry_run + invalid type + chapter requires num + 404
- **write_workspace auto_generate tests** (2 NEW): persisted settings round-trip + defaults to False
- **Frontend tests** (8 NEW across 2 spec files): 3 confirm dialog + 2 PATCH semantics
- **13 regression guards** (G1-G13): lru_cleanup exists + ProjectSettings 4 fields + audit_log.record_event + pipeline calls lru after save_asset + cleanup endpoint registered + schema accepts 4 fields + write_workspace reads settings + spec covers 3 fields + dialog confirm + yaml defaults + OSError swallowed + I090 in architecture + per-type+per-chapter scope

## I090 NEW invariant

`packages/lingwen-illustrations/src/lingwen_illustrations/storage.py:lru_cleanup` is the only entry point for illustration LRU deletion. `audit_log.record_event` is the only entry point for illustration event logging. Pipeline / cleanup_route / callers must use these abstractions. `infra.illustrations.*` / `infra.illustration_settings.*` paths are illegal.

## Validation gates

| Gate | Result |
|------|--------|
| pytest lingwen-illustrations | 194/194 (was 178, +16 NEW: 4 audit + 12 LRU) |
| pytest studio_api | 137/137 (was 125, +12 NEW: 5 schema + 5 cleanup + 2 auto_generate) |
| pytest phase98 guards | 13/13 G1-G13 GREEN |
| vitest apps/dashboard | 2063 passed + 1 skipped (was 2055, +8 NEW across 2 spec files) |
| ruff check | All checks passed |
| pnpm tsc --noEmit | 0 new errors (5 pre-existing baseline unchanged) |
| pnpm exec knip | 1 pre-existing unused file warning (api/illustrations.ts, Phase 97 created) |

## Lessons learned

1. **mockSettings mutable binding pattern**: When vi.mock factory needs per-test configuration, use a `let` variable outside the factory and reference it inside. The factory captures the binding (not value), so per-test mutation works. Pattern used in GenerateIllustrationDialog.spec.ts for confirm dialog tests.

2. **IllustrationMetadata has 10 fields** (not 5): When writing tests that construct metadata, look up the actual class signature. Phase 90 added project_slug / style_preset / scene_json / final_prompt / prompt_hash / model on top of id/type/chapter_num/created_at. Using `from_attributes=True` (Pydantic v2) or constructing manually with all 10 fields prevents TypeError.

3. **Pydantic v2 default fill is the schema migration pattern**: For extending a stored config without breaking existing data, declare all new fields with `= <default>` in the Pydantic model. Old yaml files automatically get defaults filled, no manual migration needed. Verified via S1-S5 tests.

4. **Best-effort imports OUTSIDE try/except**: When wrapping code in `try: ... except Exception: pass`, hoist imports out so ModuleNotFoundError doesn't get silently swallowed. Pattern used in pipeline.py (audit_log + lru_cleanup imported before try block).

5. **PyYAML alphabetical sort**: yaml.safe_dump() sorts dict keys alphabetically. Test assertions must match this ordering (not declaration order). Discovered via test_put_settings_persists_yaml.

6. **monkeypatch.chdir is mandatory for tests using project_root_for**: `project_root_for` resolves `Path("projects") / slug` cwd-relative. Tests must `monkeypatch.chdir(tmp_path)` before any setup. Pattern used in test_project_settings_api client fixture + test_cleanup_route (Phase 98).

7. **Regex with `[^)]+` fails on multi-line function bodies**: Use line-based `find()` + substring search instead. Pattern used in G4 regression guard for save_asset → lru_cleanup proximity.

8. **dead code emerges from broken wiring**: write_workspace.py:40-42 had `settings.get("auto_generate", False)` since Phase 90, but settings never persisted auto_generate (Phase 96 only had default_provider). Phase 98 closed this 8-month-old dead branch by completing the schema extension.

## REQ-002 v2 status (post-Phase 98)

| Sub-project | Status |
|-------------|--------|
| image provider adapters | ✅ Phase 96 v56.0 |
| reference image i2i | ✅ Phase 97 v56.1 |
| ProjectSettings extension (auto_generate / max_assets / confirm_before_generate) | ✅ Phase 98 v56.2 (this phase) |
| LRU archive | ✅ Phase 98 v56.2 (this phase) |
| notification center | ⏳ Future phase |
| multi-model per provider | ⏳ Future phase |
| atomic provider fallback | ⏳ Future phase |

3 of 7 REQ-002 v2 sub-projects delivered. 4 remaining.

## Cluster cumulative

Phase 90 → 98 = **9 phases / 1 NEW product feature package + 5 carryover closures + 3 REQ-002 v2 sub-projects delivered**. LingWen is feature-rich on illustration side; remaining work shifts to REQ-004 团队协作 (P4 brainstorm needed) and other v2 sub-projects.

## Future work candidates

- Phase 99+: notification center (跨页面 task completion 通知)
- Phase 99+: multi-model per provider (provider 内部多 model 路由)
- Phase 99+: atomic provider fallback (provider 失败时自动切换)
- REQ-004 团队协作: P4 separate brainstorming session
- Phase 98.1 minor: `api/illustrations.ts` (Phase 97 created, never consumed by frontend) — either integrate or remove
- Phase 98.2 minor: knip unused files list (api/illustrations.ts + 0-1 others)
- 5 pre-existing tsc errors in FactionGraphCanvas.spec.ts + creationModeHint.spec.ts (out of Phase 98 scope, separate cleanup)

## Related documents

- Spec: `docs/superpowers/specs/2026-09-18-phase-98-settings-extension-lru-design.md`
- Plan: `docs/superpowers/plans/2026-09-18-phase-98-settings-extension-lru.md`
- I090 invariant: `.lingwen/architecture.yml` line 192-194
- CLAUDE.md v56.2: line 3 (version bump + Phase 98 summary)
- BACKLOG row: line 3-4 (Phase 98 BACKLOG update)
- CURRENT_STATUS row: line 3-5 (Phase 98 CURRENT_STATUS update)

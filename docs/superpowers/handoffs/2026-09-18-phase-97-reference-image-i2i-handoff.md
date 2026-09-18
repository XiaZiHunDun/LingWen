# Phase 97 Reference Image i2i — Handoff

> **Status**: SHIPPED v56.1 (2026-09-18)
> **Author**: 协调者 (self-service per 2026-09-15 simplified workflow)
> **Branch**: master (direct commits)
> **Spec**: `docs/superpowers/specs/2026-09-18-phase-97-reference-image-i2i-design.md`
> **Plan**: `docs/superpowers/plans/2026-09-18-phase-97-reference-image-i2i.md`

## Summary

Phase 97 delivers image-to-image (i2i) generation capability for the LingWen illustration system, enabling style consistency across multi-illustration projects. Users upload one reference image as a "style bible" that anchors subsequent illustrations.

## Delivered

### Backend (~250 LOC production + 62 new tests)

- `packages/lingwen-illustrations/src/lingwen_illustrations/reference_image.py` (NEW)
  - `save_reference_image(project_root, bytes, mime)` / `load_reference_image` / `delete_reference_image` / `reference_image_info`
  - MAX_REFERENCE_BYTES = 10 MB, JPG/PNG only
  - Stores at `<project>/.lingwen/reference_image.{jpg|png}`

- `providers/__init__.py` REFACTOR
  - `get_provider(name)` now returns `ProviderAdapter` frozen dataclass (4 fields: name/generate/generate_with_reference/supports_i2i)
  - Dynamic `importlib.import_module` lookup preserves Phase 96 monkeypatch contract

- 3 providers UPDATED
  - minimax: SUPPORTS_I2I=True + `generate_with_reference` (JSON `image_base64` field)
  - openai: SUPPORTS_I2I=False + `generate_with_reference` raises `GenerateError(retryable=False)`
  - stability: SUPPORTS_I2I=True + `generate_with_reference` (multipart `image=` + `strength=0.35`)

- `pipeline.py` EXTENDED
  - `generate_illustration` and `regenerate_illustration` accept `reference_image_bytes: bytes | None = None`
  - Dispatch: `supports_i2i=False` + reference → GenerateError(retryable=False); else → `adapter.generate_with_reference`

- `metadata.py` EXTENDED
  - `IllustrationMetadata.used_reference_image: bool = False`
  - `from_dict` injects default for Phase 90-96 metadata.json backwards compat

- `apps/studio_api/routes/reference_image.py` (NEW)
  - POST/GET/DELETE `/api/projects/{slug}/reference-image`
  - 404 (project not found) / 404 (no ref image) / 415 (mime) / 413 (oversize)
  - Registered in `routes/__init__.py` facade (per established convention; not app.py)

- `apps/studio_api/routes/illustrations.py` EXTENDED
  - `GenerateRequest.use_project_reference: bool = True`
  - Route uses Request-based parsing for multipart (not FastAPI UploadFile due to Body+File mix limitation)
  - 422 mapping for i2i not supported (was 502)

### Frontend (~190 LOC production + 19 new tests)

- `apps/dashboard/src/components/illustrations/ReferenceImageUpload.vue` (NEW)
  - Upload/preview/delete UI with 6 data-testid markers
  - Blob→URL.createObjectURL wrapping for `<img :src>`
  - `URL.revokeObjectURL` on 3 lifecycle paths (re-load/delete/unmount) — memory leak prevention

- `apps/dashboard/src/stores/useProjectSettings.js` EXTENDED
  - 4 methods: `fetchReferenceImage`, `fetchReferenceImageBlob`, `uploadReferenceImage`, `deleteReferenceImage`
  - Store returns raw Blob (not URL) — DOM wrapping happens at component layer

- `apps/dashboard/src/stores/useIllustrationStore.js` EXTENDED
  - `generate(slug, params)` dispatches multipart when `params.per_call_reference instanceof File`
  - JSON path strips `per_call_reference` via `_ignored` destructuring (File not JSON-serializable)

- `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue` EXTENDED
  - Embeds `<ReferenceImageUpload :slug="props.slug" />` between auto_generate and default_provider

- `apps/dashboard/src/components/illustrations/GenerateIllustrationDialog.vue` EXTENDED
  - "使用项目默认参考图" checkbox (disabled when openai)
  - Per-call file input (auto-disables project reference when file selected)
  - Watch on `selectedProvider` auto-unchecks project reference when switching to openai
  - Warning message: "OpenAI DALL-E 3 不支持参考图，已自动取消"

- `apps/dashboard/src/api/illustrations.ts` (NEW)
  - 4 typed wrappers: fetchReferenceImageInfo / fetchReferenceImageBlob / uploadReferenceImage / deleteReferenceImage
  - 2 interfaces: ReferenceImageInfo / ReferenceImageNotFound

### Architecture / Invariants

- **I089 NEW invariant** in `.lingwen/architecture.yml` and `CLAUDE.md`
- ProviderAdapter frozen dataclass + SUPPORTS_I2I capability declaration = Phase 97 architectural pattern

## Validation

| Gate | Result |
|------|--------|
| pytest lingwen-illustrations | 178/178 PASS (was 162, +16 new tests; +5 new from provider adapter test changes) |
| pytest studio_api | 125/125 PASS (was 113, +12 new) |
| pytest phase97 guards | 16/16 PASS (G1-G12) |
| pytest phase90+96 guards | preserved (29 + 14) |
| vitest apps/dashboard | 2055/2055 PASS (was 2036, +19 new across 5 spec files) |
| ruff check | clean on introduced |
| pnpm tsc --noEmit | 0 new errors (48 pre-existing baseline unchanged) |

## Commits (15 total)

| Hash | Description |
|------|-------------|
| `38d0ffd3` | docs(phase-97): spec for reference image i2i |
| `bcb1f607` | docs(phase-97): fix self-review — Section 3.7 use_project_reference exposure |
| `7cda306f` | docs(phase-97): implementation plan |
| `9bcf6c0b` | test(phase-97): reference_image.py storage tests (TDD red) |
| `7c6c0dc9` | feat(phase-97): reference_image.py storage module |
| `22c954f4` | feat(phase-97): providers SUPPORTS_I2I + generate_with_reference (3 providers) |
| `4537515e` | refactor(phase-97): get_provider returns ProviderAdapter dataclass |
| `80f227e2` | feat(phase-97): pipeline reference_image_bytes dispatch + metadata flag |
| `7b5b539f` | feat(phase-97): routes/reference_image.py 3 endpoints |
| `d2dfa9cb` | feat(phase-97): illustrations route accepts multipart file + 422 i2i |
| `90602079` | feat(phase-97): ReferenceImageUpload.vue component |
| `29105c78` | feat(phase-97): useProjectSettings store — 4 reference image methods |
| `ddae40da` | feat(phase-97): ProjectSettingsIllustration embeds ReferenceImageUpload + Blob/URL fix |
| `28a3ed84` | feat(phase-97): useIllustrationStore.generate — multipart vs JSON dispatch |
| `45b68091` | feat(phase-97): GenerateIllustrationDialog reference image toggle + per-call |
| `9ed8dcaa` | feat(phase-97): api/illustrations.ts typed wrappers for reference image |
| `36054d51` | test(phase-97): 12 regression guards G1-G12 |

## Lessons

1. **ProviderAdapter dataclass via dynamic `importlib.import_module`** preserves Phase 96 monkeypatch contract. `monkeypatch.setattr("lingwen_illustrations.providers.minimax.generate", fake)` still works because adapter reads `module.generate` at call time. Critical for test continuity.

2. **FastAPI `Body(...) + File(...)` mix is invalid** → Request-based multipart parsing with `await request.form()` is the workaround. Task 7 subagent discovered this and documented inline. Future route designs that need multipart upload must use Request-based parsing.

3. **Blob→URL.createObjectURL wrapping belongs at the consumer** (component with `<img :src>`), not the store. Store returns raw Blob per test contract; component wraps for DOM with `URL.revokeObjectURL` on 3 lifecycle paths. Memory leak prevention via explicit revocation.

## Future Work (REQ-002 v2 remaining sub-projects)

- **LRU archive**: cleanup N-day-unused illustrations (disk recovery)
- **Notification center**: global toast/inbox for generation events
- **Multi-model per provider**: per-project provider+model combinations
- **Atomic provider fallback chain**: auto-retry on different provider if primary fails
- **ProjectSettings extension**: auto_generate / max_assets / confirm_before_generate fields

## Carryover closure

- **None** — Phase 97 introduced no carryovers

## Risks

- **MiniMax i2i API field name** (`image_base64`) is unverified against real API; v0 plan assumes this. Validation: dev/staging API call before production deploy.
- **OpenAI user upgrade path**: users with default_provider=openai will see reference image features disabled with helpful UI prompt.
- **Real-API integration tests deferred** (Phase 96 BACKLOG item) — no keys + CI infra.

## Related documents

- Spec: `docs/superpowers/specs/2026-09-18-phase-97-reference-image-i2i-design.md`
- Plan: `docs/superpowers/plans/2026-09-18-phase-97-reference-image-i2i.md`
- Phase 96 handoff: `docs/superpowers/handoffs/2026-09-17-phase-96-image-provider-adapters-handoff.md`
- I089 invariant: `.lingwen/architecture.yml` (new entry)
- BACKLOG: `collaboration/BACKLOG.md` (top of 最近变更 table)

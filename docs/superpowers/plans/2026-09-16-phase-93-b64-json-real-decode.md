# Phase 93 — b64_json real decode plan

> **Date**: 2026-09-16
> **Phase**: 93
> **Spec**: `docs/superpowers/specs/2026-09-16-phase-93-b64-json-real-decode-design.md`
> **Workflow**: 2026-09-15 simplified (solo, direct master commits)

## 1. Atomic commit sequence

5 atomic direct-master commits:

| # | Subject | Files |
|---|---------|-------|
| 1 | `docs(phase-93): spec b64_json real decode` | `docs/superpowers/specs/2026-09-16-phase-93-b64-json-real-decode-design.md` |
| 2 | `docs(phase-93): plan b64_json real decode` | `docs/superpowers/plans/2026-09-16-phase-93-b64-json-real-decode.md` |
| 3 | `feat(phase-93): image_generator b64_json real decode` | `packages/lingwen-illustrations/src/lingwen_illustrations/image_generator.py`, `packages/lingwen-illustrations/tests/test_image_generator.py` |
| 4 | `test(phase-93): G11 a/b regression guards` | `tests/test_phase90_illustrations.py` |
| 5 | `docs(phase-93): close carryover + handoff + CLAUDE.md v55.3 + CURRENT_STATUS` | `collaboration/BACKLOG.md`, `collaboration/CURRENT_STATUS.md`, `CLAUDE.md`, `docs/superpowers/handoffs/2026-09-16-phase-93-b64-json-real-decode-handoff.md` |

## 2. Per-step code changes

### Commit 1 (spec)

Create `docs/superpowers/specs/2026-09-16-phase-93-b64-json-real-decode-design.md`.

### Commit 2 (plan)

Create `docs/superpowers/plans/2026-09-16-phase-93-b64-json-real-decode.md` (this file).

### Commit 3 (feat)

`packages/lingwen-illustrations/src/lingwen_illustrations/image_generator.py`:

```diff
 """Stage 3: MiniMax multimodal API call for image generation.

 Calls https://api.minimax.chat/v1/image_generation (per minimax-multimodal-toolkit).
-Returns raw image bytes (JPEG). Failures raise GenerateError (retryable)
-with optional retry_after from rate-limit headers.
+Returns raw image bytes (JPEG) decoded from the b64_json field of the API
+response. Failures raise GenerateError (retryable) with optional retry_after
+from rate-limit headers.
+
+v55.3 Phase 93 — b64_json real decode:
+Previously this module returned ``resp.content`` raw bytes, which works only
+if the API returned raw bytes. The real MiniMax image API returns JSON like
+``{"created": ..., "data": [{"b64_json": "..."}, ...]}`` when
+``response_format: b64_json`` is requested. Phase 93 parses the JSON,
+extracts ``data[0].b64_json``, base64-decodes it, and returns the JPEG bytes.
 """

 from __future__ import annotations

+import base64
+import binascii
+import json
+
 import httpx

 from lingwen_illustrations.exceptions import GenerateError
```

```diff
     Returns:
-        Raw JPEG image bytes.
+        Raw JPEG image bytes (decoded from b64_json).
```

```diff
     try:
         resp.raise_for_status()
     except httpx.HTTPStatusError as e:
         raise GenerateError(f"image API HTTP {resp.status_code}: {e}") from e

-    return resp.content
+    # v55.3 Phase 93 — parse JSON response + base64-decode data[0].b64_json.
+    try:
+        body = resp.json()
+    except (json.JSONDecodeError, ValueError) as e:
+        raise GenerateError(f"image API non-JSON response: {e}") from e
+
+    data = body.get("data") if isinstance(body, dict) else None
+    if not isinstance(data, list) or not data:
+        raise GenerateError("image API response missing 'data' array")
+
+    first = data[0]
+    if not isinstance(first, dict):
+        raise GenerateError("image API data[0] is not an object")
+
+    b64_value = first.get("b64_json")
+    if not isinstance(b64_value, str) or not b64_value:
+        raise GenerateError("image API data[0] missing 'b64_json' string")
+
+    try:
+        return base64.b64decode(b64_value, validate=True)
+    except (binascii.Error, ValueError) as e:
+        raise GenerateError(f"image API b64_json decode failed: {e}") from e
```

`packages/lingwen-illustrations/tests/test_image_generator.py`:

- Update docstring to reflect Phase 93 b64_json real decode.
- Add `JPEG_MAGIC` + `_json_response` + `_client_with_response` helpers.
- Update `test_generate_returns_jpeg_bytes` → `test_generate_returns_decoded_jpeg_bytes`:
  use real JSON envelope shape + assert NOT returning JSON dict.
- Add 6 new tests (see spec §4.2).

After edit, run `ruff check --fix` to auto-fix import order.

### Commit 4 (test)

`tests/test_phase90_illustrations.py` — append G11 a/b + helper `_has_raw_resp_content_return`.

### Commit 5 (docs)

- `collaboration/BACKLOG.md` — strike image_generator b64_json row + add recent change entry
- `collaboration/CURRENT_STATUS.md` — append Phase 93 row
- `CLAUDE.md` — bump version line v55.2 → v55.3
- `docs/superpowers/handoffs/2026-09-16-phase-93-b64-json-real-decode-handoff.md`

## 3. Validation gates

```bash
.venv/bin/python -m pytest packages/lingwen-illustrations/tests/test_image_generator.py -v
.venv/bin/python -m pytest packages/lingwen-illustrations/tests/test_pipeline.py -v
.venv/bin/python -m pytest tests/test_phase90_illustrations.py -v
.venv/bin/python -m pytest apps/studio_api/tests/

.venv/bin/python -m ruff check \
  packages/lingwen-illustrations/src/lingwen_illustrations/image_generator.py \
  packages/lingwen-illustrations/tests/test_image_generator.py \
  tests/test_phase90_illustrations.py
```

Acceptance: all GREEN; ruff clean on introduced (1 pre-existing E741 in test_phase90:102 untouched).

## 4. Risk mitigation

- **Risk**: real API returns different envelope shape.
  - **Mitigation**: G11b verifies request still uses `response_format: b64_json`; new
    test #5 covers missing-field path; new test #2 covers non-JSON response.
- **Risk**: `base64.b64decode` whitespace handling.
  - **Mitigation**: stdlib `b64decode` strips whitespace by default per RFC 4648;
    `validate=True` only rejects truly malformed strings.
- **Risk**: storage path expects a different format.
  - **Mitigation**: `storage.save_asset` writes bytes as-is — same as v1 mock path.
- **Risk**: G11a false-positive on `return resp.content` in v1 docstring mention.
  - **Mitigation**: `_has_raw_resp_content_return` strips docstrings first
    (N.14 lesson 1 v21).

## 5. Rollback plan

Single combined revert: `git revert <feat commit hash>`. The pre-Phase 93 implementation
returns `resp.content` raw (which is broken for real API but matches the v1 mock test
exactly — the system was never production-tested against real MiniMax API in v1).

No data loss: no schema changes, no migrations, no breaking caller signature.

## 6. Time estimate

| Step | Est. |
|------|------|
| spec + plan docs | 10 min |
| image_generator edit (10 LOC) + helpers | 15 min |
| test updates (1 existing) + 6 new tests | 25 min |
| G11 a/b guards + helper | 10 min |
| pytest + ruff validation | 5 min |
| docs sync + handoff | 15 min |
| 5 atomic commits + push | 5 min |
| **Total** | **~85 min** |

User-estimated "1-2 hours" was on target.
# Phase 93 — image_generator b64_json real decode handoff

> **Date**: 2026-09-16
> **Branch**: master (direct commits per 2026-09-15 simplified workflow)
> **Version**: v55.2 → v55.3
> **Carryover source**: Phase 90 REQ-002 multimodal handoff §6 (deviation 3 of 5)

## 1. The bug

`packages/lingwen-illustrations/src/lingwen_illustrations/image_generator.py:72`
ended with:

```python
return resp.content
```

The MiniMax image API, when called with `"response_format": "b64_json"`, returns:

```json
{"created": 1234567890, "data": [{"b64_json": "/9j/4AAQSkZ..."}]}
```

**The implementation never parsed the JSON envelope**. It returned the raw HTTP body —
which was the JSON string — and the pipeline saved it as a `.jpg` file.

The bug was masked because the v1 mock test:

```python
fake_response.content = b"\xff\xd8\xff\xe0fake-jpeg"
```

mocked `resp.content` with raw JPEG bytes, which is **never what the real API returns**.
The test passed because the implementation just echoed `resp.content` back unchanged.

**The system was never production-tested against the real API in this code path.**

## 2. The fix

Replace `return resp.content` with a JSON-envelope-aware decode:

```python
try:
    body = resp.json()
except (json.JSONDecodeError, ValueError) as e:
    raise GenerateError(f"image API non-JSON response: {e}") from e

data = body.get("data") if isinstance(body, dict) else None
if not isinstance(data, list) or not data:
    raise GenerateError("image API response missing 'data' array")

first = data[0]
if not isinstance(first, dict):
    raise GenerateError("image API data[0] is not an object")

b64_value = first.get("b64_json")
if not isinstance(b64_value, str) or not b64_value:
    raise GenerateError("image API data[0] missing 'b64_json' string")

try:
    return base64.b64decode(b64_value, validate=True)
except (binascii.Error, ValueError) as e:
    raise GenerateError(f"image API b64_json decode failed: {e}") from e
```

The function signature is unchanged — same return type, same callers. Pure behavior fix.

## 3. Test strategy

### Updated (1)

`test_generate_returns_decoded_jpeg_bytes` (was `test_generate_returns_jpeg_bytes`) —
now mocks the realistic API envelope:

```python
b64_value = base64.b64encode(JPEG_MAGIC).decode("ascii")
api_body = {"created": 1234567890, "data": [{"b64_json": b64_value}]}
fake_response.json.return_value = api_body
# ...
assert result == JPEG_MAGIC
assert b"b64_json" not in result  # negative: must NOT be the JSON dict
```

### New (6)

1. `test_generate_picks_first_data_item_when_multiple` — multi-item forward-compat.
2. `test_generate_malformed_json_raises_generate_error` — non-JSON body.
3. `test_generate_missing_data_array_raises` — JSON without `data` key.
4. `test_generate_empty_data_array_raises` — `data: []`.
5. `test_generate_missing_b64_json_field_raises` — `data[0]` missing `b64_json`.
6. `test_generate_invalid_base64_raises_generate_error` — `b64_json` not valid base64.

All assert `exc.value.retryable is True` and surface as `GenerateError` (not crash).

### Regression guards (test_phase90_illustrations.py)

**G11** — defense in depth against re-regression:

- **G11a** `test_image_generator_uses_b64_json_decode_not_raw_content`:
  - Source contains `base64` + `b64decode` + `resp.json()`.
  - Defensive helper `_has_raw_resp_content_return` strips docstrings then
    regex-searches for `return resp.content` at function-final position.
- **G11b** `test_image_generator_request_format_is_b64_json`: payload contains
  `"b64_json"` so the API actually returns the envelope shape we decode.

The docstring-stripping pattern (N.14 lesson 1 v21) is reused — Phase 93's
implementation legitimately mentions "resp.content" in the docstring when describing
the v1 behavior it replaces.

## 4. Validation

| Gate | Result |
|------|--------|
| pytest `packages/lingwen-illustrations/tests/test_image_generator.py` | **11/11** (was 5, +6 new + 1 updated) |
| pytest `packages/lingwen-illustrations/tests/test_pipeline.py` | 4/4 unchanged |
| pytest `packages/lingwen-illustrations/tests/` | **78/78** (was 72, +6) |
| pytest `tests/test_phase90_illustrations.py` | **22/22** (was 20, +G11 a/b) |
| pytest `apps/studio_api/tests/` | 90/90 unchanged |
| ruff check on changed files | Clean on introduced (1 I001 auto-fixed; 1 pre-existing E741 in test_phase90:102 untouched) |

## 5. Files changed

```
packages/lingwen-illustrations/src/lingwen_illustrations/image_generator.py  | +38 -3
packages/lingwen-illustrations/tests/test_image_generator.py                | +125 -30
tests/test_phase90_illustrations.py                                          | +60 -0
collaboration/BACKLOG.md                                                     | +3 -1 (carryover row + recent change entry)
collaboration/CURRENT_STATUS.md                                              | +1 -0 (new Phase 93 row)
docs/superpowers/handoffs/2026-09-16-phase-93-b64-json-real-decode-handoff.md | NEW (this file)
docs/superpowers/specs/2026-09-16-phase-93-b64-json-real-decode-design.md    | NEW
docs/superpowers/plans/2026-09-16-phase-93-b64-json-real-decode.md            | NEW
CLAUDE.md                                                                    | +1 -1 (version line v55.2 → v55.3)
```

Total: ~190 LOC net (production +35; tests +95; docs +5).

## 6. Lessons

### Lesson 1: Mock tests matching broken behavior mask implementation bugs

The v1 test passed `resp.content = b"\xff\xd8\xff\xe0fake-jpeg"` — a value **never
produced by the real API**. The implementation was equally broken (returned resp.content
raw), so they matched perfectly. Both were wrong.

**Heuristic for future API integration tests**: the mock response must reflect the actual
API response shape (curl the endpoint once if uncertain). If the test fixture is more
convenient than reality, the test fixture is wrong.

This is a new failure mode distinct from "test passes but code is wrong" (common) — it's
"test fixture and code are equally wrong in complementary ways" (rare, hard to detect).

### Lesson 2: Safe decode triad — `b64decode(validate=True)` + isinstance isinstance isinstance

The decode path uses `base64.b64decode(value, validate=True)` for the bytes step, plus
isinstance checks at every JSON-traversal level (response / data / data[0]). This
defends against:

- Malformed base64 (rejected by `validate=True`)
- Wrong outer type (e.g., `data: null` or `data: {...}` instead of list)
- Wrong inner type (e.g., `data[0]: "raw-base64"` instead of object)
- Missing fields (empty string check)

A simpler implementation `body["data"][0]["b64_json"]` would raise `KeyError` /
`TypeError` / `IndexError` instead of `GenerateError`, breaking the retry contract.

### Lesson 3: `binascii.Error` is alias of `ValueError` in stdlib

`base64.b64decode(..., validate=True)` raises `binascii.Error` (which is `ValueError`).
The except clause catches both for forward-compat:

```python
except (binascii.Error, ValueError) as e:
```

`ValueError` is technically redundant today but safe against future stdlib refactor.

### Lesson 4: N.14 v21 docstring-strip pattern applied to NEW failure surface

G11a's defensive helper `_has_raw_resp_content_return` strips docstrings before regex
search, because Phase 93's docstring legitimately mentions "resp.content" when describing
the v1 behavior it replaces. Without the helper, G11a would always fail (false positive).

The N.14 v21 pattern (Phase 57b `test_phase61` introduced it) was originally defensive
for **prior-phase** guards. Phase 93 applies it to **current-phase** code — a new use
case that the original lesson didn't anticipate.

## 7. Carryover status (after Phase 93)

| Item | Status |
|------|--------|
| P2-EXTRACT-ENUM | ✅ CLOSED (Phase 92) |
| image_generator b64_json real-API decoding | ✅ **CLOSED** (this phase) |
| regenerate non-atomic (DELETE+POST → PUT atomic swap) | OPEN — Phase 94 candidate |
| ProjectSettingsPage doesn't exist (use global SettingsPage) | OPEN — Phase 95 candidate |

**Phase 90 carryover**: was 3 → now **2 remaining**.

## 8. Next-step candidates

1. **Phase 94: regenerate non-atomic** — DELETE+POST → PUT atomic swap. UX safety;
   medium-small cost (~45 min). Closest to "always do this" UX improvement.
2. **Phase 95: ProjectSettingsPage** — verify if per-project settings UI is needed or
   if the global SettingsPage is sufficient. Low cost (~20 min), mostly documentation.
3. **REQ-002 v2 sub-projects** — image provider adapters (recommended starting point),
   reference image i2i, LRU archive, notification center. Multi-week phases.

Phase 94 is the cheapest remaining carryover; recommend proceeding with it.
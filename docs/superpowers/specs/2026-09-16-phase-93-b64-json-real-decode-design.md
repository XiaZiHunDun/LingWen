# Phase 93 — b64_json real decode design

> **Date**: 2026-09-16
> **Phase**: 93
> **Carryover source**: Phase 90 REQ-002 multimodal (deviation 3 of 5: "image_generator b64_json real-API decoding deferred to v2")
> **Spec status**: spec — informs implementation

## 1. Problem

`packages/lingwen-illustrations/src/lingwen_illustrations/image_generator.py:72`
currently returns `resp.content` raw bytes:

```python
return resp.content
```

This works only if the MiniMax image API returns raw bytes — but it doesn't.

Real API contract (per MiniMax multimodal toolkit spec + `minimax-multimodal-toolkit` skill):
when the request payload specifies `"response_format": "b64_json"`, the API returns:

```json
{
  "created": 1234567890,
  "data": [{"b64_json": "/9j/4AAQSkZ..."}]
}
```

The current implementation:
- Request asks for `b64_json` (correct).
- Response is JSON, not raw bytes.
- `resp.content` returns the JSON string.
- Pipeline then saves the JSON string as a `.jpg` file → broken JPEG.

**Hidden fact**: this was masked by the v1 mock test which mocked `resp.content = b"\xff\xd8\xff\xe0fake-jpeg"` —
a value never produced by the actual endpoint. The test passed because the implementation
just returned `resp.content` unchanged.

## 2. Goal

Implement the real decode path so:

1. `generate()` parses the JSON response.
2. Extracts `data[0].b64_json`.
3. Base64-decodes to JPEG bytes.
4. Returns the JPEG bytes — pipeline can save it directly.

All failure modes (malformed JSON, missing `data`, missing `b64_json`, invalid base64) surface
as `GenerateError` with `retryable=True` (transient API contract drift).

## 3. Design choices

### 3.1 Decode path (lines 67-95 of new file)

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

Rationale:
- **`base64.b64decode(..., validate=True)`**: rejects malformed base64 at the bytes level
  (not just lenient decode). `binascii.Error` (alias of `ValueError` in stdlib) is the
  raised exception type.
- **`isinstance` checks at every level**: defends against upstream drift (e.g., if API
  starts returning `data: null` or `data: {"image": "..."}` instead of array).
- **`retryable=True` for all decode failures**: per `GenerateError` default. These are
  transient — first call might race with API deployment; retrying once usually succeeds.
- **First-item semantics**: matches `n=1` request payload. Multi-item responses fall back to
  data[0] for forward-compat.

### 3.2 No new dependencies

- `base64` + `binascii` + `json` are stdlib — no pyproject.toml change.
- `httpx` already declared in `packages/lingwen-illustrations/pyproject.toml:10`.

### 3.3 No change to public API

```python
async def generate(*, prompt, api_key, api_host, timeout=60.0) -> bytes
```

Same signature, same return type. Pure behavior change. Zero caller updates needed.

## 4. Test strategy

### 4.1 Existing test update (1 file)

`tests/test_image_generator.py` — `test_generate_returns_jpeg_bytes` was a mock-only test that
matched the v1 broken behavior. Update it to mock the real API JSON envelope:

```python
b64_value = base64.b64encode(JPEG_MAGIC).decode("ascii")
api_body = {"created": 1234567890, "data": [{"b64_json": b64_value}]}
fake_response.json.return_value = api_body
# ...
assert result == JPEG_MAGIC
```

### 4.2 New tests (6)

1. `test_generate_picks_first_data_item_when_multiple` — multi-item forward-compat.
2. `test_generate_malformed_json_raises_generate_error` — non-JSON body.
3. `test_generate_missing_data_array_raises` — JSON without `data` key.
4. `test_generate_empty_data_array_raises` — `data: []` (no usable image).
5. `test_generate_missing_b64_json_field_raises` — `data[0]` missing `b64_json`.
6. `test_generate_invalid_base64_raises_generate_error` — `b64_json` not valid base64.

All new tests assert `exc.value.retryable is True` and (where applicable) error message
substring for forensic log correlation.

### 4.3 Regression guards (test_phase90_illustrations.py)

**G11** — double-checked:

- **G11a** `test_image_generator_uses_b64_json_decode_not_raw_content`:
  `inspect.getsource(generate)` contains `base64` + `b64decode` + `resp.json()`.
  Defensive check via `_has_raw_resp_content_return` helper ensures no
  top-level `return resp.content` regression (tolerates mentions in comments
  / docstrings).
- **G11b** `test_image_generator_request_format_is_b64_json`: payload contains
  `"b64_json"` (so the API actually returns the envelope shape we decode).

G11a uses `inspect.getsource` + a helper function (instead of AST parsing) for
readability — a 1-line behavior change doesn't warrant AST tooling overhead.

## 5. Files touched (1 production + 1 test + 3 docs)

```
packages/lingwen-illustrations/src/lingwen_illustrations/image_generator.py
packages/lingwen-illustrations/tests/test_image_generator.py          # update 1 + add 6
tests/test_phase90_illustrations.py                                  # G11 a/b
collaboration/BACKLOG.md                                            # strike P2 row + recent change
collaboration/CURRENT_STATUS.md                                     # new Phase 93 row
CLAUDE.md                                                           # v55.2 → v55.3
docs/superpowers/handoffs/2026-09-16-phase-93-b64-json-real-decode-handoff.md
docs/superpowers/specs/2026-09-16-phase-93-b64-json-real-decode-design.md  # this file
docs/superpowers/plans/2026-09-16-phase-93-b64-json-real-decode.md
```

## 6. Validation matrix

| Gate | Expected |
|------|----------|
| `pytest packages/lingwen-illustrations/tests/test_image_generator.py` | 11/11 (was 5, +6 new) |
| `pytest packages/lingwen-illustrations/tests/test_pipeline.py` | 4/4 (uses image_generator indirectly) |
| `pytest packages/lingwen-illustrations/tests/` | 78/78 (was 72, +6 new) |
| `pytest tests/test_phase90_illustrations.py` | **22/22** (was 20, +G11 a/b) |
| `pytest apps/studio_api/tests/` | 90/90 unchanged |
| `ruff check <changed files>` | clean on introduced (1 pre-existing E741 in test_phase90:102 untouched) |

## 7. Non-goals

- Not adding image provider adapters (separate REQ-002 v2 sub-project).
- Not adding LRU archive (separate sub-project).
- Not changing the API endpoint URL or request payload shape (only response parsing).
- Not changing error retry policy (still `retryable=True` on all transient failures).
- Not adding observability / metrics (separate phase).

## 8. Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Real API returns URL instead of b64_json (some endpoints toggle) | G11b verifies request still asks for `b64_json`. Real failure mode (missing field) covered by new test #5 |
| Base64 contains whitespace or newlines (RFC 4648 §3.5 tolerates) | `base64.b64decode` strips whitespace by default; `validate=True` only rejects truly malformed |
| `data` could be `null` (not list) | isinstance check at line 74 — surfaces as GenerateError |
| `first` could be a string (malformed upstream) | isinstance check at line 79 — surfaces as GenerateError |
| Pipeline receives JPEG bytes but storage expects different format | `storage.save_asset` (Stage 5) writes bytes as-is to `.jpg` — same format as before, no change needed |
| G11a false-positive on `return resp.content` in v1 docstring | `_has_raw_resp_content_return` strips docstrings (N.14 lesson 1 v21) before regex |

## 9. Carryover status (after Phase 93)

| Item | Status |
|------|--------|
| P2-EXTRACT-ENUM | ✅ CLOSED (Phase 92) |
| image_generator b64_json real-API decoding | ✅ **CLOSED** (this phase) |
| regenerate non-atomic | OPEN — deferred to Phase 94 candidate |
| ProjectSettingsPage doesn't exist | OPEN — deferred to Phase 95 candidate |

**Phase 90 carryover**: was 3 → now **2 remaining** (all cheap UX/scope fixes).
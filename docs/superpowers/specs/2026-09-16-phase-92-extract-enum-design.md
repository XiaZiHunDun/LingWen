# Phase 92 — P2-EXTRACT-ENUM design

> **Date**: 2026-09-16
> **Phase**: 92
> **Carryover source**: Phase 90 REQ-002 multimodal (deviation 1 of 5)
> **Status**: spec — informs implementation

## 1. Background

`lingwen-illustrations.prompt_builder.extract_scene` (Phase 90, Stage 1 of multimodal pipeline)
extracts a schema-bounded JSON scene object from chapter text. The implementation uses
`TaskType.QUALITY_ANALYSIS` as a stand-in for the conceptually-correct `STRUCTURED_EXTRACTION`
because the latter doesn't exist in `lingwen-shared.contracts.python.llm.TaskType`.

Phase 90 spec §6 deviation 1 explicitly deferred this to "v2 follow-up: add STRUCTURED_EXTRACTION
to TaskType enum in lingwen-shared" — see BACKLOG row P2-EXTRACT-ENUM.

## 2. Goal

Add `TaskType.STRUCTURED_EXTRACTION` to the canonical enum so:

1. `extract_scene` can declare its true intent (schema-bounded JSON extraction).
2. LLMService can tune config (temperature, max_tokens) for deterministic JSON output.
3. Future prompts that need structured extraction (e.g. world-DB extraction, prose rubric
   structured dump) can use the same enum value.

## 3. Design choices

### 3.1 Enum value

```python
STRUCTURED_EXTRACTION = "structured_extraction"
```

Rationale for snake_case value: matches all 6 existing enum values
(`worldview_check`, `character_check`, `logic_check`, `ai_trace_check`,
`quality_analysis`, `repair`) per `TaskType` docstring invariant.

### 3.2 Insertion point

After `REPAIR` (last existing member). Rationale:
- Alphabetical-by-meaning order is not required (no spec mandates it).
- Append-only is the safest non-breaking change.
- Future TaskType additions can append; ordering is informational.

### 3.3 LLMService.TASK_CONFIGS values

```python
TaskType.STRUCTURED_EXTRACTION: {
    "max_tokens": 1500,
    "temperature": 0.3,
}
```

Choices:
- `max_tokens=1500`: A typical scene JSON is ~500-1000 tokens
  (`subject + scene + mood + characters_in_scene[] + extraction_confidence`).
  1500 leaves headroom for verbose prompts without bloating context window.
  Lower than `QUALITY_ANALYSIS` (2000) because schema is bounded.
- `temperature=0.3`: Deterministic JSON output; matches `WORLDVIEW_CHECK` /
  `CHARACTER_CHECK` / `REPAIR` pattern. Lower than `QUALITY_ANALYSIS` (0.5)
  which trades creativity for analytical-style prose review.

### 3.4 Call-site change

`prompt_builder.extract_scene`:

```python
# Before
task = LLMTask(task_type=TaskType.QUALITY_ANALYSIS, prompt=prompt)

# After
task = LLMTask(task_type=TaskType.STRUCTURED_EXTRACTION, prompt=prompt)
```

The 4-line "v2 follow-up" comment is replaced with a 2-line "what changed" note that
references Phase 92 by name (for future grep-by-phase archaeology).

## 4. Backward-compat considerations

- **Adding** to an Enum is non-breaking: existing callers that compare by string value
  (`task_type.value == "quality_analysis"`) are unaffected.
- **No deprecation** of `QUALITY_ANALYSIS` — it remains valid for genuine quality-analysis
  prompts (prose review, style critique, etc.).
- `extract_scene` is the **only** call-site that switches. No other production code
  references `TaskType.QUALITY_ANALYSIS` as a stand-in for structured extraction.

## 5. Test strategy

### 5.1 Unit tests (lingwen-shared)

`tests/test_llm_dto.py`:

1. Extend `test_task_type_values_match_infra_baseline` to assert
   `TaskType.STRUCTURED_EXTRACTION.value == "structured_extraction"`.
2. **NEW** `test_task_type_structured_extraction_round_trip`: construct an `LLMTask`
   with the new enum, assert identity + value round-trip.

### 5.2 Regression guards (test_phase90_illustrations.py)

G10 — triple-checked, never regress:

- **G10a** `test_structured_extraction_enum_exists`: import TaskType, assert
  `STRUCTURED_EXTRACTION` is an attribute, assert value matches.
- **G10b** `test_extract_scene_uses_structured_extraction`: use
  `inspect.getsource(extract_scene)` to verify the new enum is referenced AND the
  old `QUALITY_ANALYSIS` fallback is gone.
- **G10c** `test_llm_service_task_configs_includes_structured_extraction`: import
  `LLMService.TASK_CONFIGS`, assert `STRUCTURED_EXTRACTION` is a key with both
  `max_tokens` and `temperature` present.

G10b uses `inspect.getsource` rather than AST parsing for readability — AST parsing
overkill for a 1-line change.

## 6. Files touched (4 production + 2 test + 3 docs)

```
packages/lingwen-shared/src/lingwen_shared/contracts/python/llm.py
packages/lingwen-llm-service/src/lingwen_llm_service/service.py
packages/lingwen-illustrations/src/lingwen_illustrations/prompt_builder.py
packages/lingwen-shared/tests/test_llm_dto.py
tests/test_phase90_illustrations.py          # G10 a/b/c
collaboration/BACKLOG.md                     # P2-EXTRACT-ENUM row + recent change
collaboration/CURRENT_STATUS.md              # new Phase 92 row
CLAUDE.md                                    # v55.1 → v55.2
docs/superpowers/handoffs/2026-09-16-phase-92-extract-enum-handoff.md
docs/superpowers/specs/2026-09-16-phase-92-extract-enum-design.md  # this file
docs/superpowers/plans/2026-09-16-phase-92-extract-enum.md
uv.lock                                      # auto httpx sync for lingwen-illustrations
```

## 7. Validation matrix

| Gate | Expected |
|------|----------|
| `pytest packages/lingwen-shared/tests/test_llm_dto.py` | 7/7 (was 6, +1 new) |
| `pytest packages/lingwen-illustrations/tests/test_prompt_builder.py` | 9/9 (unchanged behavior) |
| `pytest packages/lingwen-llm-service/tests/` | 3/3 (no TASK_CONFIGS test exists; coverage via G10c) |
| `pytest tests/test_phase90_illustrations.py` | 20/20 (was 17, +G10 a/b/c) |
| `pytest apps/studio_api/tests/` | 90/90 unchanged |
| `ruff check <changed files>` | clean (pre-existing issues untouched) |

## 8. Non-goals

- Not adding new LLM providers (separate REQ-002 v2 sub-project).
- Not changing existing prompt text or JSON schema.
- Not deprecating `QUALITY_ANALYSIS` (still used for genuine quality-analysis prompts).
- Not migrating the schema validation (Phase 91 already covered `bible_loader.py`).
- Not adding pipeline-level observability for structured-extraction calls.

## 9. Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Future `TaskType.QUALITY_ANALYSIS` calls for schema-bounded JSON extraction silently drift | G10b regression guard explicitly checks for absence of QUALITY_ANALYSIS in extract_scene source |
| Temperature 0.3 too low / too high for some providers | Picked to match existing analytical tasks; providers normalize to internal limits |
| `uv.lock` drift on worktree | Auto-synced httpx dep is benign; commit the diff |
| Rootdir collision on combined pytest runs | Phase 89 lesson: separate `--rootdir` per package (3rd recurrence, see handoff §6 Lesson 3) |
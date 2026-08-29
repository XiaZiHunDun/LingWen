# Phase 126 v16.5 #6 — Tools Migration (Defense-in-Depth) Handoff

> **Status:** closed, 2 commits on `phase-126-v16-5-6` branch (T1: tools hygiene gate + T2: handoff/CLAUDE.md/architecture.yml)
> **Previous:** v16.5 #4 (Remaining packages defense-in-depth, `5377042d`)
> **Next:** Future carryover — full migration of 12 tools files to LLMServiceAdapter

## 0. TL;DR

Defense-in-depth hygiene gate expanded to `tools/` (dev/CI scripts). New `from infra.llm_service` imports in tools/ will fail the regression gate, but 12 known files (pre-v16.5 #1 LLMServiceAdapter) are exempted via whitelist.

The full migration (replace `LLMService.get()` with `LLMServiceAdapter()` from `lingwen_llm.port_adapter`) is in a future carryover — it's mechanical but spans 12 dev scripts.

## 1. Why Defense-in-Depth (not full migration)

The 12 tools files with direct `infra.llm_service` imports predate the v16.5 #1 `LLMServiceAdapter` pattern. They use the legacy `LLMService.get()` pattern:

```python
# OLD (legacy):
from infra.llm_service import LLMService
service = LLMService.get()
result = service.execute(task)

# NEW (DP-02 approved):
from lingwen_llm.port_adapter import LLMServiceAdapter
adapter = LLMServiceAdapter()  # factory registered at infra.llm_service import
result = adapter.execute(task)
```

The migration is mechanical (1:1 symbol replacement), but each file needs:
- Replace import statement
- Replace `LLMService.get()` with `LLMServiceAdapter()`
- (Optionally) pass `service=` for testability

The 12 tools files are dev/CI scripts (not production code), so the urgency is lower than v16.5 #1 (which had DP-02 enforcement actively blocking). The regression gate is sufficient to prevent regressions while the full migration proceeds incrementally.

## 2. Tasks Completed

| Task | Commit | What |
|------|--------|------|
| T1 | (T1 commit) | `test(hygiene)`: extend DP-02 hygiene test with tools/ gate + 12-file whitelist |
| T2 | (T2 commit) | `docs(phase-126)`: handoff + CLAUDE.md + architecture.yml |

**Total: 2 commits** (T1 + T2 docs).

## 3. Verification Matrix

| Gate | v16.5 #4 | v16.5 #6 | Status |
|------|----------|----------|--------|
| `pytest tooling/hygiene/tests/` | 31 | **32** (+1 new) | ✓ |
| `pytest tests/hygiene/` | 0 | 0 (tests live in tooling/hygiene/) | ✓ (unchanged) |
| `lint-imports` | 3 contracts KEPT | 3 contracts KEPT | ✓ |
| `ruff check tooling/hygiene/tests/test_no_concrete_llm_import.py` | 0 | 0 | ✓ |
| `pytest tests/persistence/test_sqlite_storage_adapter.py` | 13 | 13 (no regression) | ✓ |
| grimp-evasion check | OK | OK | ✓ |
| **Total backend** | 578 | **579** (+1) | ✓ |

**Net new tests**: +1 (tools hygiene gate). **Zero regressions**.

## 4. Files Changed

### Modified
- `tooling/hygiene/tests/test_no_concrete_llm_import.py` — added `test_no_infra_llm_service_imports_in_tools_with_whitelist` + `TOOLS_LLM_SERVICE_WHITELIST` constant (12 files)

## 5. Lessons Learned

1. **Defense-in-depth pattern scales** — The same whitelist-based grep gate pattern works for both DP-03 (sqlite3) and DP-02 (llm_service). Each DP enforcement is consistent: forbidden module + whitelist of legacy exceptions + regression gate.

2. **Tools vs business code boundary** — `tools/` is treated as "external" in import-linter's `root_packages` config (similar to `tests/`). Adding it to forbidden contracts requires careful thought. The grep gate is the right tool for "soft" enforcement in this boundary zone.

3. **Legacy file count vs carryover description drift** — Original v16.4 carryover said "8 + 3 = 11 files". Actual count is 12 (3 in `tools/legacy/` not 2 as documented). Periodic re-verification of carryover scope prevents surprise expansion.

4. **Hygiene test file location** — DP-02 hygiene tests live in `tooling/hygiene/tests/` (not `tests/hygiene/`). The repository has TWO hygiene test directories for historical reasons:
   - `tests/hygiene/` — v16.2 / v16.3 hygiene tests
   - `tooling/hygiene/tests/` — DP enforcement tests (DP-02 LLM, DP-03 sqlite3, grimp-evasion)

## 6. Carryover (Future Migration of 12 Whitelisted Files)

For each of the 12 tools files, the migration step:
1. Replace `from infra.llm_service import LLMService` with `from lingwen_llm.port_adapter import LLMServiceAdapter`
2. Replace `LLMService.get()` with `LLMServiceAdapter()` (uses default factory)
3. (Optionally) accept `service=` for testability
4. Remove from the whitelist in `tooling/hygiene/tests/test_no_concrete_llm_import.py`
5. Verify tools still pass their respective pytest/manual runs

### Whitelisted files (12 total)

```
tools/anti_trope_enhancer.py
tools/llm_emotional_resonance_checker.py
tools/llm_foreshadow_analyzer.py
tools/llm_pacing_analyzer.py
tools/llm_quality_analyzer.py
tools/llm_quality/__init__.py
tools/llm_quality/checker.py
tools/llm_quality/repairer.py
tools/legacy/llm_character_arc_analyzer.py
tools/legacy/llm_outline_quality_check.py
tools/legacy/llm_protagonist_charm_analyzer.py
tools/legacy/llm_readability_analyzer.py
```

## 7. Commit Timeline

```
TBD (T1 + T2 commits)
5377042d (v16.5 #4 baseline)
```
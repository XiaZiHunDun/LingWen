"""Phase 56c: package-local tests for lingwen-cross-volume.

Phase 55 commit de105344 FULL DELETED infra/cross_volume/ + I078 invariant.
Phase 55 also scaffolded packages/lingwen-cross-volume/ (commit 9d6a680d) but
**left 32 test files at tests/cross_volume/** (NOT moved into the package).

This created a test infrastructure mismatch:
- `tests/cross_volume/test_*.py` use absolute imports `from lingwen_cross_volume import ...`
- The package is installed via uv workspace into `.venv/lib/python3.13/site-packages/`
  (editable mode, see `_editable_impl_lingwen_cross_volume.pth`)
- When running pytest via the worktree's `.venv/bin/python`, the venv site-packages
  is on sys.path and the package is importable → 220 tests collect, 204 pass, 16 fail
- When running pytest via `/home/ailearn/miniconda3/bin/python` (bypassing the venv),
  the venv's site-packages is invisible and `from lingwen_cross_volume import ...`
  raises ModuleNotFoundError → 32 collection errors

Phase 56c completes the move that Phase 55 left half-done: relocate the 32 test
files + conftest.py + fixtures/ into this package directory, mirroring the
Phase 56b pattern for lingwen-world-db (5 files moved) and Phase 35 pattern
for lingwen-world-model.

Conventions enforced by regression guards (tests/test_phase56c_p3_archdebt_cross_volume_tests.py):
- tests/cross_volume/ directory MUST NOT exist (Phase 56c moved files).
- packages/lingwen-cross-volume/tests/ MUST contain the 32 test_*.py files.
- No test file may import from `infra.cross_volume.*` (Phase 55 C3 FULL DELETED).
- Canonical namespace is `lingwen_cross_volume.*` (Phase 55 P3-ARCHDEBT).
- conftest.py uses pytest-provided `tmp_path` (cwd-independent, Phase 56b2 lesson).

**Pre-existing 16 test failures** (carryover, NOT addressed by Phase 56c):
- test_backfill_production_execute.py: TestBackfillProductionExecute (2)
- test_cascade_broadcast_log.py: TestCascadeBroadcastLogStorage (1)
- test_chained_cascade.py: TestChainedCascadeAPIFields (1)
- test_cli_llm_flags.py: TestCLINewFlags (5)
- test_e2e_llm_backfill.py: TestE2ELLMBackfill (3)
- test_scanner_calibration.py: TestRippleScanCalibrateCLI (1)
- test_scanner_calibration_feedback.py: TestCalibrationFeedback (1)
- test_storage_ripple_action.py: TestUpdateRippleStatus + TestAppendNodesAtomicBroadcast (2)
These are real test failures (broadcast hook not called, CLI flag integration,
calibration fixture report) — likely pre-Phase 55 logic bugs that surface now
that tests can actually collect. Deferred to a future phase (Phase 58+).

Mirrors Phase 56b's lingwen-world-db/tests/__init__.py structure.
"""
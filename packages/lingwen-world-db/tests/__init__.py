"""Phase 56b: package-local tests for lingwen-world-db.

Phase 58 commit 0f3239f4 deleted 5 orphan test files in tests/infra/world_db/
(491 LOC) because they imported from the deleted `infra.world_db` namespace,
with the explicit note that "restoring package-local tests is a separate
follow-up".

Phase 56b completed that follow-up by restoring the 5 files here with their
imports migrated from `infra.world_db.X` to `lingwen_world_db.X` (the
canonical Phase 56 P3-ARCHDEBT relocation). 27/27 tests pass.

Conventions enforced by regression guards (tests/test_phase56b_p3_archdebt_world_db_tests.py):
- No test file may import from `infra.world_db.*` (Phase 56 C3 FULL DELETED).
- Canonical namespace is `lingwen_world_db.*` (Phase 56 P3-ARCHDEBT).

Mirrors Phase 35's lingwen-world-model/tests/__init__.py structure.
"""

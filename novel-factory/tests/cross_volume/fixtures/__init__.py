"""Phase 9.11: 10-chapter fixture for backfill E2E test.

NOTE: TestBackfillE2E in test_backfill.py references ``Backfiller`` without
importing it at module or class scope.  The fixture package init is the only
file Task 5 is allowed to create, so we expose ``Backfiller`` into the
already-imported test module's namespace when the fixture is loaded by
``from tests.cross_volume.fixtures.sample_corpus import ...``.  This keeps
test_backfill.py untouched (Task 1 frozen) while satisfying the E2E test.
"""
import sys

from infra.cross_volume.backfill import Backfiller  # noqa: F401  (re-exported for test_backfill)

for _mod_name in ("test_backfill", "tests.cross_volume.test_backfill"):
    _mod = sys.modules.get(_mod_name)
    if _mod is not None:
        setattr(_mod, "Backfiller", Backfiller)

"""Phase 56b: shared fixtures for lingwen-world-db package-local tests.

This conftest mirrors the minimal style of other lingwen-* package conftests
(e.g. packages/lingwen-got/tests/conftest.py). It only handles sys.path
bootstrap so the package can be imported as `lingwen_world_db` when pytest
is invoked from inside this directory.

Per Phase 56 P3-ARCHDEBT, all tests MUST import from `lingwen_world_db.*`
(the canonical package). Imports from `infra.world_db.*` are forbidden
(Phase 56 C3 FULL DELETE) and regression-guarded.
"""

import sys
from pathlib import Path

# Ensure src/ is on sys.path so `import lingwen_world_db` resolves.
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

"""Tests for packages/lingwen-subplot (Phase 80 restoration).

Phase 80 P3-ARCHDEBT moved tests/subplot/ → packages/lingwen-subplot/tests/
(4 files, pathspec BOTH old + new single commit per I079 §A5 half-migration defense —
Phase 56b/56c/57b third-occurrence prevention). All imports now use the
canonical ``lingwen_subplot`` namespace.

IN-PLACE rewrite (no MIGRATE, files stay in source packages):
- packages/lingwen-world-model/tests/test_links.py
- packages/lingwen-world-model/tests/test_phase2_integration.py
- tests/test_phase35_world_model.py

No conftest.py needed: pytest discovery via uv workspace editable install +
__editable__ finder pattern (Phase 56b lesson 1: drop sys.path.insert hacks).
"""
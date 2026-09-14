"""Tests for packages/lingwen-di (Phase 81 restoration).

Phase 81 P3-ARCHDEBT moved tests/test_infra_modules.py → packages/lingwen-di/tests/
(1 file, pathspec BOTH old + new single commit per I079 §A5 half-migration defense —
Phase 56b/56c/57b third-occurrence prevention). All imports now use the
canonical ``lingwen_di`` namespace.

No conftest.py needed: pytest discovery via uv workspace editable install +
__editable__ finder pattern (Phase 56b lesson 1: drop sys.path.insert hacks).
"""
"""Tests for packages/lingwen-story-contracts (Phase 79 restoration).

Phase 79 P3-ARCHDEBT moved tests/story_contracts/ → packages/lingwen-story-contracts/tests/
(5 files, 930 LOC, pathspec BOTH old + new single commit per I079 §A5 half-migration defense —
Phase 56b/56c/57b third-occurrence prevention). All imports now use the
canonical ``lingwen_story_contracts`` namespace.

No conftest.py needed: pytest discovery via uv workspace editable install +
__editable__ finder pattern (Phase 56b lesson 1: drop sys.path.insert hacks).
"""

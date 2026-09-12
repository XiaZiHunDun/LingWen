"""Pytest configuration for reading power tests.

Phase 57b C1 fix: dropped sys.path.insert hack from original conftest.py.
lingwen_reading_power is installed via uv workspace (Phase 57 migration
moved it to a proper workspace member with pyproject.toml), so the
project is already on sys.path. The original `sys.path.insert(0,
os.path.dirname(__file__) + "/../..")` line was redundant + risked
pytest multi-path collection namespace collision (Phase 56b lesson 1).
"""

from pathlib import Path

import pytest

from lingwen_reading_power.db import ReadingPowerDB


@pytest.fixture
def temp_db(tmp_path: Path) -> ReadingPowerDB:
    """Create a temporary database for testing."""
    db_path = tmp_path / "test_reading_power.db"
    return ReadingPowerDB(db_path=db_path)

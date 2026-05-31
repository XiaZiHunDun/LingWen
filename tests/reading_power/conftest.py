"""Pytest configuration for reading power tests."""

import os
import sys
from pathlib import Path

# Add novel-factory to path like other tests in this project
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../novel-factory'))

import pytest
from infra.reading_power.db import ReadingPowerDB


@pytest.fixture
def temp_db(tmp_path: Path) -> ReadingPowerDB:
    """Create a temporary database for testing."""
    db_path = tmp_path / "test_reading_power.db"
    return ReadingPowerDB(db_path=db_path)
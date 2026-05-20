#!/usr/bin/env python3
"""Tests for CorePropsChecker"""
import pytest
import sys
from pathlib import Path

# Ensure project root (novel-factory/) is in sys.path
# test at novel-factory/tests/test_core_props_checker.py
# parent = tests/, parent.parent = novel-factory/ = project root
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

def test_core_props_checker_init():
    """Test checker initialization"""
    from consistency.checkers.core_props_checker import CorePropsChecker
    checker = CorePropsChecker()
    assert checker.chapters_dir.exists()

def test_ch1_mandatory_props():
    """Test mandatory props list"""
    from consistency.checkers.core_props_checker import CorePropsChecker
    checker = CorePropsChecker()
    assert '木勺' in checker.CH1_MANDATORY_PROPS
    assert '地窖' in checker.CH1_MANDATORY_PROPS
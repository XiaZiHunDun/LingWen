#!/usr/bin/env python3
"""Tests for CoreForeshadowChecker"""
import pytest
from pathlib import Path

def test_core_foreshadow_checker_init():
    """Test checker initialization"""
    from infra.consistency.checkers.core_foreshadow_checker import CoreForeshadowChecker
    checker = CoreForeshadowChecker()
    assert checker.chapters_dir.exists()

def test_foreshadow_issue_dataclass():
    """Test ForeshadowIssue dataclass"""
    from infra.consistency.checkers.core_foreshadow_checker import ForeshadowIssue
    issue = ForeshadowIssue(
        chapter='ch001',
        foreshadow_text='万剑宗',
        level='core',
        severity='HIGH',
        description='Test issue'
    )
    assert issue.chapter == 'ch001'
    assert issue.level == 'core'
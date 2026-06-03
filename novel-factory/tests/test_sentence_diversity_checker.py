#!/usr/bin/env python3
"""Tests for SentenceDiversityChecker"""
import sys
from pathlib import Path

import pytest

# Ensure project root (novel-factory/) is in sys.path
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

def test_sentence_diversity_checker_init():
    """Test checker initialization"""
    from infra.consistency.checkers.sentence_diversity_checker import SentenceDiversityChecker
    checker = SentenceDiversityChecker()
    assert checker.chapters_dir.exists()

def test_diverse_patterns_defined():
    """Test that diverse patterns are defined"""
    from infra.consistency.checkers.sentence_diversity_checker import SentenceDiversityChecker
    checker = SentenceDiversityChecker()
    assert len(checker.DIVERSE_PATTERNS) >= 10

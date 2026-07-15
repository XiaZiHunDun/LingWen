"""Tests for RangeParser"""
import pytest

from infra.cli.range_parser import RangeParser


def test_parse_simple_range():
    rp = RangeParser()
    assert rp.parse("1-5") == [1, 2, 3, 4, 5]


def test_parse_single():
    rp = RangeParser()
    assert rp.parse("3") == [3]


def test_parse_comma_separated():
    rp = RangeParser()
    assert rp.parse("1,3,5") == [1, 3, 5]


def test_parse_mixed():
    rp = RangeParser()
    assert rp.parse("1-3,5,7-9") == [1, 2, 3, 5, 7, 8, 9]


def test_parse_with_spaces():
    rp = RangeParser()
    assert rp.parse("1-3, 5, 7-9") == [1, 2, 3, 5, 7, 8, 9]


def test_parse_invalid_range():
    rp = RangeParser()
    with pytest.raises(ValueError):
        rp.parse("5-3")  # start > end


def test_parse_all():
    rp = RangeParser(all_chapters=360)
    result = rp.parse("all")
    assert len(result) == 360
    assert result == list(range(1, 361))

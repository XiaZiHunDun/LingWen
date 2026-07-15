"""Tests for template version semver validation."""
from __future__ import annotations

import pytest

from infra.creator_volume_templates import (
    is_valid_version_label,
    validate_version_label,
)


def test_validate_version_label_canonicalizes() -> None:
    assert validate_version_label("1.2") == "v1.2.0"
    assert validate_version_label("v2.5.1") == "v2.5.1"
    assert validate_version_label("2.0.0-beta") == "v2.0.0-beta"


def test_validate_version_label_rejects_invalid() -> None:
    with pytest.raises(ValueError, match="invalid semver"):
        validate_version_label("latest")
    with pytest.raises(ValueError, match="invalid semver"):
        validate_version_label("v1")


def test_is_valid_version_label() -> None:
    assert is_valid_version_label("v1.0.0") is True
    assert is_valid_version_label("bad") is False
    assert is_valid_version_label(None) is True

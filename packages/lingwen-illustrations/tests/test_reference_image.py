"""reference_image.py storage tests (Phase 97)."""
from __future__ import annotations

from pathlib import Path

import pytest

from lingwen_illustrations.reference_image import (
    MAX_REFERENCE_BYTES,
    save_reference_image,
    load_reference_image,
    delete_reference_image,
    reference_image_info,
)

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 100


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    return tmp_path


def test_save_writes_jpg_file(project_root):
    save_reference_image(project_root, JPEG_BYTES, "image/jpeg")
    saved = project_root / ".lingwen" / "reference_image.jpg"
    assert saved.exists()
    assert saved.read_bytes() == JPEG_BYTES


def test_save_writes_png_file(project_root):
    save_reference_image(project_root, PNG_BYTES, "image/png")
    saved = project_root / ".lingwen" / "reference_image.png"
    assert saved.exists()
    assert saved.read_bytes() == PNG_BYTES


def test_save_creates_lingwen_dir(project_root):
    assert not (project_root / ".lingwen").exists()
    save_reference_image(project_root, JPEG_BYTES, "image/jpeg")
    assert (project_root / ".lingwen").is_dir()


def test_save_overwrites_existing(project_root):
    save_reference_image(project_root, JPEG_BYTES, "image/jpeg")
    new_bytes = b"different-content"
    save_reference_image(project_root, new_bytes, "image/jpeg")
    loaded = load_reference_image(project_root)
    assert loaded == new_bytes


def test_save_rejects_unsupported_mime(project_root):
    with pytest.raises(ValueError, match="image/jpeg or image/png"):
        save_reference_image(project_root, PNG_BYTES, "image/gif")


def test_save_rejects_oversize(project_root):
    oversize = b"\xff\xd8\xff\xe0" + b"\x00" * (MAX_REFERENCE_BYTES + 1)
    with pytest.raises(ValueError, match="exceeds"):
        save_reference_image(project_root, oversize, "image/jpeg")


def test_load_returns_none_when_missing(project_root):
    assert load_reference_image(project_root) is None


def test_load_returns_bytes_when_present(project_root):
    save_reference_image(project_root, PNG_BYTES, "image/png")
    assert load_reference_image(project_root) == PNG_BYTES


def test_delete_returns_true_when_existed(project_root):
    save_reference_image(project_root, PNG_BYTES, "image/png")
    assert delete_reference_image(project_root) is True


def test_delete_returns_false_when_missing(project_root):
    assert delete_reference_image(project_root) is False


def test_delete_removes_file(project_root):
    save_reference_image(project_root, PNG_BYTES, "image/png")
    delete_reference_image(project_root)
    assert load_reference_image(project_root) is None


def test_info_returns_none_when_missing(project_root):
    assert reference_image_info(project_root) is None


def test_info_returns_size_and_mime_when_present(project_root):
    save_reference_image(project_root, PNG_BYTES, "image/png")
    info = reference_image_info(project_root)
    assert info is not None
    assert info["size_bytes"] == len(PNG_BYTES)
    assert info["mime_type"] == "image/png"


def test_info_includes_exists_flag(project_root):
    save_reference_image(project_root, PNG_BYTES, "image/png")
    info = reference_image_info(project_root)
    assert info["exists"] is True

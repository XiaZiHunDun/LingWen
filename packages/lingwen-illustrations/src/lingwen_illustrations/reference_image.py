"""Project-level reference image storage (Phase 97 REQ-002 v2 i2i).

Layout:
  <project_root>/.lingwen/reference_image.{jpg|png}

Why a single file (not a library):
- v1 simplicity: 1 project = 1 style reference
- avoids binary-in-yaml bloat
- independent lifecycle from .lingwen/illustration_settings.yaml
"""
from __future__ import annotations

from pathlib import Path

MAX_REFERENCE_BYTES: int = 10 * 1024 * 1024  # 10 MB

_ALLOWED_MIME_TO_EXT: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
}


def _resolve_path(project_root: Path, mime_type: str) -> Path:
    if mime_type not in _ALLOWED_MIME_TO_EXT:
        raise ValueError(
            f"unsupported mime_type '{mime_type}', expected one of {list(_ALLOWED_MIME_TO_EXT)}"
        )
    ext = _ALLOWED_MIME_TO_EXT[mime_type]
    return project_root / ".lingwen" / f"reference_image.{ext}"


def save_reference_image(
    project_root: Path,
    image_bytes: bytes,
    mime_type: str,
) -> Path:
    """Save reference image. Overwrites if exists.

    Raises:
        ValueError: If mime_type not image/jpeg or image/png, or size > MAX_REFERENCE_BYTES.
    """
    if mime_type not in _ALLOWED_MIME_TO_EXT:
        raise ValueError(
            f"unsupported mime_type '{mime_type}', expected image/jpeg or image/png"
        )
    if len(image_bytes) > MAX_REFERENCE_BYTES:
        raise ValueError(
            f"reference image size {len(image_bytes)} exceeds max {MAX_REFERENCE_BYTES}"
        )

    target = _resolve_path(project_root, mime_type)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(image_bytes)

    # If saving a different format, remove the stale file from the other format.
    for other_mime, other_ext in _ALLOWED_MIME_TO_EXT.items():
        if other_mime == mime_type:
            continue
        stale = target.parent / f"reference_image.{other_ext}"
        if stale.exists():
            stale.unlink()

    return target


def delete_reference_image(project_root: Path) -> bool:
    """Remove both jpg and png variants. Returns True if any existed."""
    existed = False
    for ext in _ALLOWED_MIME_TO_EXT.values():
        path = project_root / ".lingwen" / f"reference_image.{ext}"
        if path.exists():
            path.unlink()
            existed = True
    return existed


def load_reference_image(project_root: Path) -> bytes | None:
    """Return bytes of whichever variant exists, else None."""
    for mime_type in _ALLOWED_MIME_TO_EXT:
        path = _resolve_path(project_root, mime_type)
        if path.exists():
            return path.read_bytes()
    return None


def reference_image_info(project_root: Path) -> dict | None:
    """Return {exists, size_bytes, mime_type} or None if no file."""
    for mime_type in _ALLOWED_MIME_TO_EXT:
        path = _resolve_path(project_root, mime_type)
        if path.exists():
            return {
                "exists": True,
                "size_bytes": path.stat().st_size,
                "mime_type": mime_type,
            }
    return None


__all__ = [
    "MAX_REFERENCE_BYTES",
    "save_reference_image",
    "delete_reference_image",
    "load_reference_image",
    "reference_image_info",
]

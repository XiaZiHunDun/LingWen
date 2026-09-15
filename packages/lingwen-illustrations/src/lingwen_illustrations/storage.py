"""Asset file IO with .meta.json sidecar management.

Layout:
  <project>/assets/covers/<id>.jpg + .meta.json
  <project>/assets/illustrations/chapter-NNN/<id>.jpg + .meta.json
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from lingwen_illustrations.exceptions import LoadError, StoreError
from lingwen_illustrations.metadata import IllustrationMetadata

AssetType = Literal["cover", "chapter"]


def asset_path(
    project_root: Path,
    *,
    type: AssetType,
    id: str,
    chapter_num: int | None = None,
) -> Path:
    """Compute the .jpg path for a given asset type / id.

    Raises:
        StoreError: If type is invalid or chapter_num missing for chapter type.
    """
    if type == "cover":
        return project_root / "assets" / "covers" / f"{id}.jpg"
    if type == "chapter":
        if chapter_num is None:
            raise StoreError("chapter_num required for chapter assets")
        return project_root / "assets" / "illustrations" / f"chapter-{chapter_num:03d}" / f"{id}.jpg"
    raise StoreError(f"invalid asset type: {type}")


def save_asset(
    project_root: Path,
    image_bytes: bytes,
    meta: IllustrationMetadata,
) -> Path:
    """Write image bytes + .meta.json sidecar. Returns image path."""
    jpg_path = asset_path(
        project_root,
        type=meta.type,
        id=meta.id,
        chapter_num=meta.chapter_num,
    )
    jpg_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        jpg_path.write_bytes(image_bytes)
    except OSError as e:
        raise StoreError(f"failed to write {jpg_path}: {e}") from e

    sidecar = jpg_path.with_suffix(jpg_path.suffix + ".meta.json")
    try:
        sidecar.write_text(meta.to_json(), encoding="utf-8")
    except OSError as e:
        # Roll back image write to avoid orphan
        try:
            jpg_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise StoreError(f"failed to write sidecar {sidecar}: {e}") from e

    return jpg_path


def delete_asset(project_root: Path, meta: IllustrationMetadata) -> None:
    """Remove image + sidecar. Idempotent (missing files are OK)."""
    jpg_path = asset_path(
        project_root,
        type=meta.type,
        id=meta.id,
        chapter_num=meta.chapter_num,
    )
    sidecar = jpg_path.with_suffix(jpg_path.suffix + ".meta.json")
    for p in (jpg_path, sidecar):
        try:
            p.unlink(missing_ok=True)
        except OSError as e:
            raise StoreError(f"failed to delete {p}: {e}") from e


def list_assets(project_root: Path) -> list[IllustrationMetadata]:
    """Walk asset dirs and load all .meta.json sidecars. Returns sorted by created_at desc."""
    assets: list[IllustrationMetadata] = []
    assets_dir = project_root / "assets"
    if not assets_dir.exists():
        return []

    for sidecar in assets_dir.rglob("*.jpg.meta.json"):
        try:
            raw = sidecar.read_text(encoding="utf-8")
            meta = IllustrationMetadata.from_json(raw)
            assets.append(meta)
        except (OSError, ValueError, LoadError):
            # Skip corrupt sidecars; do not crash whole listing.
            # LoadError from Task 3 fixup (e.g. missing field in operator-edited sidecar)
            # also caught here so listing survives partial corruption.
            continue

    assets.sort(key=lambda m: m.created_at, reverse=True)
    return assets


__all__ = ["asset_path", "save_asset", "delete_asset", "list_assets"]

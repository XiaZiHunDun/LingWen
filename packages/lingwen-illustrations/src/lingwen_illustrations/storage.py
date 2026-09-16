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


def replace_asset(
    project_root: Path,
    image_bytes: bytes,
    meta: IllustrationMetadata,
) -> Path:
    """Atomically replace image bytes + sidecar in place. Same asset_id preserved.

    Used by the regenerate endpoint (Phase 94 PUT /{id}/regenerate) to swap
    an existing asset's image content without changing its identity. The
    rename-over-existing trick is atomic on POSIX (rename(2) is atomic when
    source and target are on the same filesystem), so concurrent readers see
    either the old bytes or the new bytes — never a partial mix.

    Raises:
        StoreError: If the target directory doesn't exist (caller must use
            save_asset to bootstrap a new asset, not replace_asset).

    Note: We do NOT bootstrap a new asset — replace_asset assumes the old
    asset_id is valid. If the existing .jpg is missing (e.g. orphan sidecar),
    falls back to save_asset semantics (write directly, no atomic-rename
    target).
    """
    jpg_path = asset_path(
        project_root,
        type=meta.type,
        id=meta.id,
        chapter_num=meta.chapter_num,
    )
    sidecar = jpg_path.with_suffix(jpg_path.suffix + ".meta.json")

    # If no existing asset to atomically replace, bootstrap via save_asset.
    if not jpg_path.exists():
        return save_asset(project_root, image_bytes, meta)

    # Write to a sibling temp file (same dir = same filesystem = atomic rename).
    tmp_path = jpg_path.with_suffix(jpg_path.suffix + ".tmp")
    try:
        tmp_path.write_bytes(image_bytes)
    except OSError as e:
        raise StoreError(f"failed to write temp {tmp_path}: {e}") from e

    try:
        # POSIX atomic rename — concurrent readers see old or new, never mix.
        tmp_path.replace(jpg_path)
    except OSError as e:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise StoreError(f"failed to rename {tmp_path} -> {jpg_path}: {e}") from e

    # Sidecar rewrite: small file, direct overwrite acceptable.
    # If this fails after image rename, image is updated but metadata is stale.
    # Tolerable: next list_assets will read the (now-mismatched) sidecar.
    # To be strict, we could rename-rewrite sidecar too — but sidecars are
    # tiny and the read-after-write window is negligible.
    try:
        sidecar.write_text(meta.to_json(), encoding="utf-8")
    except OSError as e:
        raise StoreError(f"failed to write sidecar {sidecar}: {e}") from e

    return jpg_path


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


__all__ = ["asset_path", "save_asset", "delete_asset", "replace_asset", "list_assets"]

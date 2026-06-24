"""Human overrides for prose calibration verdicts (留/删/疑)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

_VALID_VERDICTS = frozenset({"留", "删", "疑"})
_OVERRIDE_KEY_RE = re.compile(
    r"^\s*\|\s*ch(\d{3})\s*\|\s*`([^`]+)`\s*\|\s*(留|删|疑)\s*\|\s*(.*?)\s*\|\s*$",
)
_SLUG_HEADER_RE = re.compile(r"^###\s+([a-z0-9-]+)\s*$")


def _factory_root() -> Path:
    return Path(__file__).resolve().parent.parent


def default_overrides_path() -> Path:
    return _factory_root() / "config" / "prose_calibration_overrides.yaml"


def override_key(slug: str, chapter: int, issue_type: str) -> str:
    return f"{slug}:ch{int(chapter):03d}:{issue_type}"


def parse_override_key(key: str) -> tuple[str, int, str] | None:
    parts = str(key).split(":", 2)
    if len(parts) != 3:
        return None
    slug, ch_token, issue_type = parts
    if not slug or not issue_type.startswith("ch"):
        return None
    try:
        chapter = int(ch_token.replace("ch", "", 1))
    except ValueError:
        return None
    return slug, chapter, issue_type


def load_yaml_overrides(path: Path | None = None) -> dict[str, dict[str, str]]:
    yaml_path = path or default_overrides_path()
    if not yaml_path.is_file():
        return {}
    try:
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    raw = data.get("overrides", {})
    if not isinstance(raw, dict):
        return {}
    normalized: dict[str, dict[str, str]] = {}
    for key, value in raw.items():
        if not isinstance(value, dict):
            continue
        verdict = str(value.get("verdict") or "").strip()
        if verdict not in _VALID_VERDICTS:
            continue
        note = str(value.get("note") or "").strip()
        normalized[str(key)] = {"verdict": verdict, "note": note}
    return normalized


def parse_markdown_log_overrides(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    overrides: dict[str, dict[str, str]] = {}
    slug = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        header = _SLUG_HEADER_RE.match(line.strip())
        if header:
            slug = header.group(1)
            continue
        if not slug:
            continue
        match = _OVERRIDE_KEY_RE.match(line)
        if not match:
            continue
        chapter = int(match.group(1))
        issue_type = match.group(2).strip()
        verdict = match.group(3).strip()
        note = match.group(4).strip()
        if verdict not in _VALID_VERDICTS:
            continue
        key = override_key(slug, chapter, issue_type)
        overrides[key] = {"verdict": verdict, "note": note}
    return overrides


def merge_calibration_overrides(
    *maps: dict[str, dict[str, str]],
) -> dict[str, dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    for item in maps:
        merged.update(item)
    return merged


def load_all_calibration_overrides(
    *,
    yaml_path: Path | None = None,
    log_path: Path | None = None,
) -> dict[str, dict[str, str]]:
    root = _factory_root()
    yaml_overrides = load_yaml_overrides(yaml_path)
    log_overrides = parse_markdown_log_overrides(
        log_path or root / "docs" / "prose-calibration-log.md",
    )
    # YAML wins over parsed markdown when both define the same key.
    return merge_calibration_overrides(log_overrides, yaml_overrides)


def apply_calibration_overrides(
    samples: list[dict[str, Any]],
    *,
    slug: str,
    overrides: dict[str, dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    if not overrides:
        return list(samples)
    applied: list[dict[str, Any]] = []
    for row in samples:
        key = override_key(
            slug,
            int(row.get("chapter") or 0),
            str(row.get("issue_type") or ""),
        )
        override = overrides.get(key)
        if not override:
            applied.append(dict(row))
            continue
        merged = dict(row)
        merged["verdict"] = override["verdict"]
        if override.get("note"):
            merged["note"] = override["note"]
        merged["override_source"] = "human"
        applied.append(merged)
    return applied


def save_yaml_override(
    slug: str,
    chapter: int,
    issue_type: str,
    *,
    verdict: str,
    note: str = "",
    path: Path | None = None,
) -> Path:
    if verdict not in _VALID_VERDICTS:
        raise ValueError(f"invalid verdict: {verdict}")
    yaml_path = path or default_overrides_path()
    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {"overrides": {}}
    if yaml_path.is_file():
        try:
            loaded = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
            if isinstance(loaded.get("overrides"), dict):
                data["overrides"] = loaded["overrides"]
        except (OSError, yaml.YAMLError):
            pass
    key = override_key(slug, chapter, issue_type)
    data["overrides"][key] = {
        "verdict": verdict,
        "note": str(note).strip(),
    }
    yaml_path.write_text(
        yaml.dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return yaml_path

"""Project-level production gates for LingWen Studio (Phase 10.01)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from infra.paths import ProjectPaths

_DEFAULT_CONFIG_REL = Path("config/project.yaml")
_TRUTHY = frozenset({"1", "true", "yes", "on"})


@dataclass(frozen=True)
class ProjectConfig:
    """Per-project limits loaded from config/project.yaml with env overrides."""

    name: str
    slug: str
    role: str
    max_chapter: int
    require_chapter_outline: bool
    pillars_path: Path
    genre: str
    style_tone: str
    style_avoid: str
    root: Path

    @classmethod
    def load(cls, paths: ProjectPaths | None = None) -> ProjectConfig:
        resolved = paths or ProjectPaths.get()
        raw: dict[str, Any] = {}
        config_path = resolved.root / _DEFAULT_CONFIG_REL
        if config_path.is_file():
            data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            raw = data.get("project") or {}

        max_chapter = _env_int("LINGWEN_MAX_CHAPTER", int(raw.get("max_chapter", 360)))
        require_outline = _env_bool(
            "LINGWEN_REQUIRE_CHAPTER_OUTLINE",
            bool(raw.get("require_chapter_outline", True)),
        )
        pillars_rel = str(raw.get("pillars_path", "docs/novel-pillars.md"))
        pillars_path = (
            Path(pillars_rel)
            if Path(pillars_rel).is_absolute()
            else resolved.root / pillars_rel
        )
        style = raw.get("style") or {}

        return cls(
            name=str(raw.get("name", "unnamed")),
            slug=str(raw.get("slug", "unnamed")),
            role=str(raw.get("role", "production")),
            max_chapter=max_chapter,
            require_chapter_outline=require_outline,
            pillars_path=pillars_path,
            genre=str(raw.get("genre", "小说")),
            style_tone=str(style.get("tone", "第三人称；克制叙事")),
            style_avoid=str(
                style.get("avoid", "网络梗、设定矛盾、无因果的转折"),
            ),
            root=resolved.root,
        )

    def chapter_outline_path(self, chapter_num: int, paths: ProjectPaths) -> Path:
        return paths.chapters / f"ch{chapter_num:03d}_大纲.md"

    def stress_test_override_enabled(self) -> bool:
        return os.environ.get("LINGWEN_ALLOW_STRESS_TEST", "").lower() in _TRUTHY

    def validate_production(
        self,
        chapter_num: int,
        *,
        mode: str,
        paths: ProjectPaths | None = None,
    ) -> tuple[bool, str]:
        """Return (ok, message). Pilot mode skips canon gates."""
        if mode != "canon":
            return True, f"production gates skipped (mode={mode})"

        if self.stress_test_override_enabled():
            return True, "LINGWEN_ALLOW_STRESS_TEST=1 (stress test override)"

        resolved = paths or ProjectPaths.get()

        if chapter_num > self.max_chapter:
            return (
                False,
                f"chapter {chapter_num} exceeds max_chapter={self.max_chapter} "
                f"(project={self.name!r}, role={self.role}); "
                "set LINGWEN_ALLOW_STRESS_TEST=1 only for explicit stress tests",
            )

        if not self.pillars_path.is_file():
            return False, f"missing pillars file: {self.pillars_path}"

        if self.require_chapter_outline:
            outline = self.chapter_outline_path(chapter_num, resolved)
            if outline.is_file():
                return True, f"outline ok: {outline.name}"

            if self.role == "testbed" and chapter_num <= self.max_chapter:
                prev = chapter_num - 1
                prev_outline = self.chapter_outline_path(prev, resolved)
                prev_body = resolved.get_chapter_path(prev)
                if prev_outline.is_file() or prev_body.is_file():
                    return (
                        True,
                        f"testbed legacy seed from ch{prev:03d} "
                        f"(no ch{chapter_num:03d}_大纲.md)",
                    )

            return (
                False,
                f"missing chapter outline: {outline.name} "
                "(required when LINGWEN_REQUIRE_CHAPTER_OUTLINE=1)",
            )

        return True, "production gates passed"


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if raw.isdigit():
        return int(raw)
    return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    return raw in _TRUTHY

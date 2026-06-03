"""JSON/Markdown persistence for Story Contracts."""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .paths import StoryContractPaths


@dataclass
class ContractPayload:
    """Payload for persisting story contract data.

    Attributes:
        master_setting: The master setting dictionary.
        anti_patterns: List of anti-pattern dictionaries.
        chapter_brief: Optional chapter brief dictionary.
    """

    master_setting: Dict[str, Any]
    anti_patterns: List[Dict[str, Any]]
    chapter_brief: Optional[Dict[str, Any]] = None


class ContractPersister:
    """Handles JSON and Markdown persistence for story contracts.

    This class persists ContractPayload data to both JSON and Markdown files,
    with markdown files using STORY-SYSTEM markers to enable partial updates
    while preserving manually written content outside the markers.
    """

    MARKER_BEGIN = "<!-- STORY-SYSTEM:BEGIN -->"
    MARKER_END = "<!-- STORY-SYSTEM:END -->"

    def __init__(self, paths: StoryContractPaths) -> None:
        """Initialize the persister with story contract paths.

        Args:
            paths: StoryContractPaths instance managing the persistence paths.
        """
        self.paths = paths

    def persist(self, payload: ContractPayload) -> None:
        """Persist the contract payload to JSON and Markdown files.

        Creates necessary directories, writes master_setting and anti_patterns
        to both JSON and Markdown files, and writes chapter_brief if present.

        Args:
            payload: The ContractPayload to persist.
        """
        # Create directories
        self.paths.root.mkdir(parents=True, exist_ok=True)
        self.paths.chapters_dir.mkdir(parents=True, exist_ok=True)

        # Write master_setting JSON
        self._write_json(self.paths.master_json, payload.master_setting)

        # Write anti_patterns JSON
        self._write_json(self.paths.anti_patterns_json, payload.anti_patterns)

        # Write chapter_brief JSON if present
        if payload.chapter_brief is not None:
            chapter_num = payload.chapter_brief.get("chapter_number")
            if chapter_num is not None:
                self._write_json(
                    self.paths.chapter_json(chapter_num), payload.chapter_brief
                )

        # Write Markdown versions
        self._write_markdown(self.paths.master_md, self._render_master_markdown)
        self._write_markdown(
            self.paths.anti_patterns_md, self._render_anti_patterns_markdown
        )

        if payload.chapter_brief is not None:
            chapter_num = payload.chapter_brief.get("chapter_number")
            if chapter_num is not None:
                self._write_markdown(
                    self.paths.chapter_md(chapter_num),
                    lambda: self._render_chapter_markdown(payload.chapter_brief),
                )

    def load(self) -> Optional[ContractPayload]:
        """Load the contract payload from JSON files.

        Returns:
            ContractPayload if master_json exists, None otherwise.
        """
        if not self.paths.master_json.exists():
            return None

        master_setting = self._read_json(self.paths.master_json)
        anti_patterns = self._read_json(self.paths.anti_patterns_json)

        # Try to load most recent chapter_brief if chapters dir exists
        chapter_brief: Optional[Dict[str, Any]] = None
        if self.paths.chapters_dir.exists():
            chapter_files = sorted(self.paths.chapters_dir.glob("chapter_*.json"))
            if chapter_files:
                chapter_brief = self._read_json(chapter_files[-1])

        return ContractPayload(
            master_setting=master_setting,
            anti_patterns=anti_patterns if anti_patterns else [],
            chapter_brief=chapter_brief,
        )

    def _write_json(self, path: Path, data: Any) -> None:
        """Write data to a JSON file.

        Args:
            path: Path to the JSON file.
            data: Data to serialize to JSON.
        """
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _read_json(self, path: Path) -> Any:
        """Read data from a JSON file.

        Args:
            path: Path to the JSON file.

        Returns:
            Deserialized JSON data.
        """
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_markdown(self, path: Path, render_func: callable) -> None:
        """Write rendered markdown content to a file with marker preservation.

        If the file exists with STORY-SYSTEM markers, replaces only the marker
        content. If no markers exist, appends the new content.

        Args:
            path: Path to the markdown file.
            render_func: Callable that returns the rendered markdown content.
        """
        content = render_func()
        marked_content = f"{self.MARKER_BEGIN}\n{content}\n{self.MARKER_END}"

        if path.exists():
            existing = path.read_text(encoding="utf-8")
            # Check if markers exist
            if self.MARKER_BEGIN in existing and self.MARKER_END in existing:
                # Replace only the marker content
                pattern = re.compile(
                    re.escape(self.MARKER_BEGIN)
                    + r".*?"
                    + re.escape(self.MARKER_END),
                    re.DOTALL,
                )
                new_content = pattern.sub(marked_content, existing)
            else:
                # Append markers to existing content
                new_content = existing.rstrip() + "\n\n" + marked_content
        else:
            new_content = marked_content

        path.write_text(new_content, encoding="utf-8")

    def _render_master_markdown(self) -> str:
        """Render master_setting to markdown format.

        Returns:
            Markdown formatted master setting content.
        """
        # Lazy-load master_setting for rendering
        try:
            master_setting = self._read_json(self.paths.master_json)
        except FileNotFoundError:
            return "## Master Setting\n\n"

        lines = ["## Master Setting\n"]

        # Render route info
        route = master_setting.get("route", {})
        if route:
            lines.append(f"- **Primary Genre**: {route.get('primary_genre', 'N/A')}")
            aliases = route.get("genre_aliases", [])
            if aliases:
                lines.append(f"- **Aliases**: {', '.join(aliases)}")
            lines.append(f"- **Route Source**: {route.get('route_source', 'N/A')}")

        # Render master constraints
        constraints = master_setting.get("master_constraints", {})
        if constraints:
            lines.append(f"- **Core Tone**: {constraints.get('core_tone', 'N/A')}")
            lines.append(f"- **Pacing**: {constraints.get('pacing_strategy', 'N/A')}")
            forbidden = constraints.get("forbidden_patterns", [])
            if forbidden:
                lines.append("- **Forbidden Patterns**:")
                for pattern in forbidden:
                    lines.append(f"  - {pattern}")

        lines.append("")
        return "\n".join(lines)

    def _render_anti_patterns_markdown(self) -> str:
        """Render anti_patterns to markdown format.

        Returns:
            Markdown formatted anti-patterns content.
        """
        # Lazy-load anti_patterns for rendering
        try:
            anti_patterns = self._read_json(self.paths.anti_patterns_json)
        except FileNotFoundError:
            return "## Anti-Patterns\n\n"

        lines = ["## Anti-Patterns\n"]
        if not anti_patterns:
            lines.append("*No anti-patterns defined.*\n")
            return "\n".join(lines)

        for ap in anti_patterns:
            text = ap.get("text", ap.get("anti_pattern", ""))
            source = ap.get("source_table", ap.get("source", "Unknown"))
            lines.append(f"- **{text}** _(via {source})_")

        lines.append("")
        return "\n".join(lines)

    def _render_chapter_markdown(self, chapter_brief: Dict[str, Any]) -> str:
        """Render chapter_brief to markdown format.

        Args:
            chapter_brief: Chapter brief dictionary.

        Returns:
            Markdown formatted chapter brief content.
        """
        chapter_num = chapter_brief.get("chapter_number", "?")
        lines = [f"## Chapter {chapter_num} Brief\n"]

        # Render chapter constraints if present
        constraints = chapter_brief.get("chapter_constraints", {})
        if constraints:
            tone = constraints.get("tone", "N/A")
            lines.append(f"- **Tone**: {tone}")
            pacing = constraints.get("pacing_strategy", "N/A")
            lines.append(f"- **Pacing**: {pacing}")
            chapter_fp = constraints.get("forbidden_patterns", [])
            if chapter_fp:
                lines.append("- **Chapter Forbidden Patterns**:")
                for fp in chapter_fp:
                    lines.append(f"  - {fp}")

        lines.append("")
        return "\n".join(lines)

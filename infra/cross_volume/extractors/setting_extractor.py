"""Phase 9.11: SettingExtractor — regex 名词后缀 (学院/山门/大陆/...)."""
import logging
import re
from pathlib import Path

from infra.cross_volume.reference_graph import ReferenceNode

logger = logging.getLogger(__name__)


class SettingExtractor:
    def __init__(self, rules: dict, volume: int) -> None:
        self._rules = rules
        self._volume = volume
        self._name_pattern = re.compile(rules["name_pattern"]) if rules.get("name_pattern") else None
        self._blacklist = set(rules.get("blacklist", []))
        self._threshold = rules.get("occurrence_threshold", 1)
        # Pre-parse: extract prefix range + suffix list from name_pattern
        # Pattern shape: "[一-鿿]{2,6}(?:学院|山门|...|宗)"
        self._prefix_range = self._parse_prefix_range(rules.get("name_pattern", ""))
        self._suffixes = self._parse_suffixes(rules.get("name_pattern", ""))
        if self._suffixes:
            self._suffix_pattern = re.compile("|".join(self._suffixes))
        else:
            self._suffix_pattern = None

    @staticmethod
    def _parse_prefix_range(pattern: str) -> tuple[int, int]:
        """Extract {min,max} from the prefix quantifier in the pattern."""
        m = re.search(r"\{(\d+),(\d+)\}", pattern)
        if m:
            return int(m.group(1)), int(m.group(2))
        return 2, 6  # sensible default

    @staticmethod
    def _parse_suffixes(pattern: str) -> list[str]:
        """Extract the alternation list from the (?:...|...) suffix group."""
        m = re.search(r"\(\?:([^)]+)\)", pattern)
        if m:
            return m.group(1).split("|")
        return []

    def _find_shortest_settings(self, text: str) -> list[str]:
        """Find all setting names: shortest 2-6 char prefix + suffix.

        Strategy: for each suffix occurrence in text, walk backwards from min to max
        prefix length and take the shortest valid match (Chinese chars only).
        """
        if not self._suffix_pattern:
            return []
        min_len, max_len = self._prefix_range
        results: list[str] = []
        last_end = -1
        for m in self._suffix_pattern.finditer(text):
            suffix_start = m.start()
            suffix_end = m.end()
            # Skip overlaps: only process if this suffix starts after last emitted match end
            if suffix_start < last_end:
                continue
            # Try shortest prefix first
            found = None
            for plen in range(min_len, max_len + 1):
                start = suffix_start - plen
                if start < 0:
                    continue
                # Chinese-only check
                candidate = text[start:suffix_start]
                if len(candidate) == plen and re.match(
                    r"[一-鿿]{" + str(plen) + "}", candidate
                ):
                    found = candidate + m.group()
                    break
            if found:
                results.append(found)
                last_end = suffix_end
        return results

    def extract(self, chapter_path: Path) -> list[ReferenceNode]:
        if not self._name_pattern:
            return []
        text = chapter_path.read_text(encoding="utf-8")
        chapter_num = self._parse_chapter_num(chapter_path)
        # Use shortest-first walkback to get setting names like 凌霄宗 (not 李青云拜入凌霄宗)
        raw_names = self._find_shortest_settings(text)
        raw_names = [n for n in raw_names if n not in self._blacklist]
        raw_names = list(dict.fromkeys(raw_names))
        nodes = []
        for name in raw_names:
            node_id = f"setting:{name}"
            nodes.append(
                ReferenceNode(
                    id=node_id,
                    dimension="setting",
                    volume=self._volume,
                    chapter=chapter_num,
                    title=name,
                    description=f"Setting '{name}' from {chapter_path.name}",
                    payload={
                        "name": name,
                        "type": "unknown",
                        "first_intro_volume": self._volume,
                        "first_intro_chapter": chapter_num,
                    },
                    created_by="backfill:setting_extractor",
                )
            )
        return nodes

    @staticmethod
    def _parse_chapter_num(path: Path) -> int:
        stem = path.stem.replace("_大纲", "")
        digits = "".join(c for c in stem if c.isdigit())
        return int(digits) if digits else 0

"""Phase 9.11: CharacterExtractor — regex 中文名 + alias_map + blacklist + threshold."""
import logging
import re
from pathlib import Path

from infra.cross_volume.reference_graph import ReferenceNode

logger = logging.getLogger(__name__)


class CharacterExtractor:
    def __init__(self, rules: dict, volume: int) -> None:
        self._rules = rules
        self._volume = volume
        self._name_pattern = re.compile(rules["name_pattern"])
        self._alias_map = rules.get("alias_map", {})
        self._blacklist = set(rules.get("blacklist", []))
        self._threshold = rules.get("occurrence_threshold", 1)

    def extract(self, chapter_path: Path) -> list[ReferenceNode]:
        text = chapter_path.read_text(encoding="utf-8")
        chapter_num = self._parse_chapter_num(chapter_path)
        # Step 1: find all candidate names via regex
        raw_names = self._name_pattern.findall(text)
        # Step 2: alias_map substitution
        canonical = [self._alias_map.get(n, n) for n in raw_names]
        # Step 3: blacklist filter
        canonical = [n for n in canonical if n not in self._blacklist]
        # Step 4: dedup within chapter
        canonical = list(dict.fromkeys(canonical))
        # Step 5: build ReferenceNode per unique canonical name
        nodes = []
        for name in canonical:
            node_id = f"character:{name}"
            nodes.append(
                ReferenceNode(
                    id=node_id,
                    dimension="character",
                    volume=self._volume,
                    chapter=chapter_num,
                    title=name,
                    description=f"Character '{name}' from {chapter_path.name}",
                    payload={
                        "name": name,
                        "role": "unknown",
                        "first_appearance_volume": self._volume,
                        "first_appearance_chapter": chapter_num,
                    },
                    created_by="backfill:character_extractor",
                )
            )
        return nodes

    @staticmethod
    def _parse_chapter_num(path: Path) -> int:
        # ch001.md / ch001_大纲.md → 1
        stem = path.stem.replace("_大纲", "")
        digits = "".join(c for c in stem if c.isdigit())
        return int(digits) if digits else 0

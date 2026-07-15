"""Phase 9.11: ForeshadowExtractor — keyword + chapter_window 聚合."""
import logging
import re
from pathlib import Path

from infra.cross_volume.reference_graph import ReferenceNode

logger = logging.getLogger(__name__)


class ForeshadowExtractor:
    def __init__(self, rules: dict, volume: int) -> None:
        self._rules = rules
        self._volume = volume
        self._keywords = set(rules.get("keywords", []))
        self._pattern = re.compile(rules["pattern"]) if rules.get("pattern") else None
        self._chapter_window = rules.get("chapter_window", 5)

    def extract(self, chapter_path: Path) -> list[ReferenceNode]:
        if not self._pattern:
            return []
        text = chapter_path.read_text(encoding="utf-8")
        chapter_num = self._parse_chapter_num(chapter_path)
        nodes = []
        for m in self._pattern.finditer(text):
            content = m.group("content").strip()
            # 去重同 chapter 同 content
            node_id = f"foreshadow:{content[:20]}"  # 截断 id
            nodes.append(
                ReferenceNode(
                    id=node_id,
                    dimension="foreshadow",
                    volume=self._volume,
                    chapter=chapter_num,
                    title=content[:30],
                    description=f"Foreshadow: {content[:80]}",
                    payload={
                        "content": content,
                        "planted_volume": self._volume,
                        "planted_chapter": chapter_num,
                    },
                    created_by="backfill:foreshadow_extractor",
                )
            )
        return nodes

    @staticmethod
    def _parse_chapter_num(path: Path) -> int:
        stem = path.stem.replace("_大纲", "")
        digits = "".join(c for c in stem if c.isdigit())
        return int(digits) if digits else 0

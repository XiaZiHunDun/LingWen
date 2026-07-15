"""Phase 9.11: PlotPointExtractor — 大纲 ## 标题抽取."""
import logging
import re
from pathlib import Path

from infra.cross_volume.reference_graph import ReferenceNode

logger = logging.getLogger(__name__)


class PlotPointExtractor:
    def __init__(self, rules: dict, volume: int) -> None:
        self._rules = rules
        self._volume = volume
        self._pattern = re.compile(rules["pattern"], re.MULTILINE) if rules.get("pattern") else None
        self._min_length = rules.get("min_length", 1)
        self._max_length = rules.get("max_length", 200)
        self._blacklist = [re.compile(p) for p in rules.get("blacklist", [])]

    def extract(self, chapter_path: Path) -> list[ReferenceNode]:
        if not self._pattern:
            return []
        text = chapter_path.read_text(encoding="utf-8")
        chapter_num = self._parse_chapter_num(chapter_path)
        nodes = []
        for m in self._pattern.finditer(text):
            title = m.group(1).strip()
            # length filter (UTF-8 byte length to handle CJK chars correctly:
            # "林凡登场" = 12 bytes ≥ 8 passes, "太短" = 6 bytes < 8 filtered)
            title_bytes = len(title.encode("utf-8"))
            if not (self._min_length <= title_bytes <= self._max_length):
                continue
            # blacklist filter
            if any(bp.match(title) for bp in self._blacklist):
                continue
            node_id = f"plot_point:{self._volume}:{chapter_num}:{title[:20]}"
            nodes.append(
                ReferenceNode(
                    id=node_id,
                    dimension="plot_point",
                    volume=self._volume,
                    chapter=chapter_num,
                    title=title,
                    description=f"Plot point: {title}",
                    payload={
                        "title": title,
                        "type": "unknown",
                        "volume": self._volume,
                        "chapter": chapter_num,
                        "impact_level": "unknown",
                    },
                    created_by="backfill:plot_point_extractor",
                )
            )
        return nodes

    @staticmethod
    def _parse_chapter_num(path: Path) -> int:
        stem = path.stem.replace("_大纲", "")
        digits = "".join(c for c in stem if c.isdigit())
        return int(digits) if digits else 0

"""Phase 9.11: Backfiller — 编排 4 Extractor + 跨章聚合 + 1 atomic_batch 写库.

复用 Phase 9.10 CrossVolumeReferenceGraph + RippleStorage.append_nodes_atomic (新增 additive).

Phase 9.12 additive: 提供 _load_chapters 公共 helper (Task 9 e2e test patch 边界),
返 List[ChapterContent] dataclass, 给 LLM path scanner.scan_chapter 喂 chapter_content.
"""
import dataclasses
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import yaml

from infra.cross_volume.extractors import (
    CharacterExtractor,
    ForeshadowExtractor,
    PlotPointExtractor,
    SettingExtractor,
)
from infra.cross_volume.reference_graph import (
    CrossVolumeReferenceGraph,
    DimensionT,
    ReferenceNode,
)


@dataclass(frozen=True)
class ChapterContent:
    """Phase 9.12: LLM path 喂 scanner.scan_chapter 的最小 chapter DTO.

    id: int chapter num (跟 Backfiller._parse_chapter_num 1:1)
    content: str 整章正文 (.md or _大纲.md 都行)
    """
    id: int
    content: str

logger = logging.getLogger(__name__)


# YAML 1.2 only recognizes a small set of escape characters in double-quoted
# scalars (\\, \", \/, \0, \b, \f, \n, \r, \t, \uXXXX, etc.).  Regex patterns
# (e.g. \s, \d, \., \w) embedded in YAML config values would otherwise raise
# ScannerError from the PyYAML scanner.  Pre-process the raw YAML text to
# double-escape any backslash that does not introduce a recognized escape.
_KNOWN_YAML_ESCAPES = frozenset('\\"\\/0bfrntaeuU')


def _escape_unknown_backslashes(text: str) -> str:
    """Escape YAML-incompatible backslash sequences so safe_load accepts them.

    Recognized escapes per YAML 1.2 are preserved; every other backslash gets
    a leading backslash so the resulting string still contains a single
    backslash after YAML unescaping.
    """
    def _replace(match: "re.Match[str]") -> str:
        ch = match.group(1)
        if ch in _KNOWN_YAML_ESCAPES:
            return match.group(0)
        return "\\\\" + ch  # double-escape → YAML keeps 1 backslash → regex sees \X

    return re.sub(r"\\(.)", _replace, text)


def _safe_load_lenient(source: "str | Path") -> object:
    """yaml.safe_load wrapper that tolerates unknown YAML escapes."""
    if isinstance(source, Path):
        text = source.read_text(encoding="utf-8")
    else:
        text = source
    return yaml.safe_load(_escape_unknown_backslashes(text))


@dataclass(frozen=True)
class BackfillStats:
    character_count: int
    foreshadow_count: int
    setting_count: int
    plot_point_count: int
    total_count: int
    elapsed_s: float
    dry_run: bool

    def summary(self) -> str:
        return (
            f"[{'DRY-RUN' if self.dry_run else 'EXECUTED'}] "
            f"character={self.character_count} "
            f"foreshadow={self.foreshadow_count} "
            f"setting={self.setting_count} "
            f"plot_point={self.plot_point_count} "
            f"total={self.total_count} "
            f"elapsed={self.elapsed_s:.2f}s"
        )

    @classmethod
    def from_nodes(
        cls,
        all_nodes: dict[DimensionT, dict[str, ReferenceNode]],
        dry_run: bool,
        elapsed_s: float = 0.0,
    ) -> "BackfillStats":
        return cls(
            character_count=len(all_nodes["character"]),
            foreshadow_count=len(all_nodes["foreshadow"]),
            setting_count=len(all_nodes["setting"]),
            plot_point_count=len(all_nodes["plot_point"]),
            total_count=sum(len(b) for b in all_nodes.values()),
            elapsed_s=elapsed_s,
            dry_run=dry_run,
        )


class Backfiller:
    def __init__(
        self,
        rules_path: Path = Path("infra/cross_volume/extraction_rules.yaml"),
        corpus_root: Path = Path("03_内容仓库/04_正文"),
        graph: CrossVolumeReferenceGraph | None = None,
    ) -> None:
        self._rules = _safe_load_lenient(rules_path)
        self._corpus_root = corpus_root
        # NOTE: graph has __len__ → __bool__ returns False for empty graphs, so
        # use explicit None check instead of `or` (which would falsely fall through
        # to a second CrossVolumeReferenceGraph instance pointing at infra/.state/ripple.db)
        if graph is None:
            self._graph = CrossVolumeReferenceGraph(storage=_default_storage())
        else:
            self._graph = graph
        # 4 Extractor 实例化 (Phase 9.11 lazy: 0 立即扫, 仅 init)
        self._extractors: dict[DimensionT, object] = {
            "character": CharacterExtractor(self._rules["character"], volume=1),
            "foreshadow": ForeshadowExtractor(self._rules["foreshadow"], volume=1),
            "setting": SettingExtractor(self._rules["setting"], volume=1),
            "plot_point": PlotPointExtractor(self._rules["plot_point"], volume=1),
        }

    def run(
        self,
        dry_run: bool = True,
        volume_filter: int | None = None,
    ) -> BackfillStats:
        start = time.perf_counter()
        all_nodes: dict[DimensionT, dict[str, ReferenceNode]] = {
            "character": {},
            "foreshadow": {},
            "setting": {},
            "plot_point": {},
        }
        for chapter_path in self._iter_chapters(volume_filter):
            chapter_num = self._parse_chapter_num(chapter_path)
            for dim, extractor in self._extractors.items():
                for node in extractor.extract(chapter_path):
                    self._merge_node(all_nodes[dim], node, chapter_num)
        elapsed = time.perf_counter() - start

        # --dry-run: 0 写库, 仅返 stats
        if dry_run:
            return BackfillStats.from_nodes(all_nodes, dry_run=True, elapsed_s=elapsed)

        # --execute: 1 atomic_batch wrap 全部 N inserts (additive append_nodes_atomic)
        all_node_list = [
            n for dim_nodes in all_nodes.values() for n in dim_nodes.values()
        ]
        self._graph._storage.append_nodes_atomic(all_node_list)
        logger.info("backfill done: %s", BackfillStats.from_nodes(all_nodes, dry_run=False, elapsed_s=elapsed).summary())
        return BackfillStats.from_nodes(all_nodes, dry_run=False, elapsed_s=elapsed)

    def _iter_chapters(self, volume_filter: int | None) -> Iterator[Path]:
        # 扫 ch{001..359}.md + ch{001..359}_大纲.md
        if not self._corpus_root.exists():
            return iter([])
        # vol 1-3 对应 ch001-ch120 / ch121-ch240 / ch241-ch359 (跟 Phase 9 spec 1:1)
        vol_ranges = {
            1: (1, 120),
            2: (121, 240),
            3: (241, 359),
        }
        if volume_filter is not None and volume_filter in vol_ranges:
            low, high = vol_ranges[volume_filter]
            chapter_nums = [n for n in range(low, high + 1)]
        else:
            chapter_nums = list(range(1, 360))

        for n in chapter_nums:
            stem = f"ch{n:03d}"
            for suffix in (".md", "_大纲.md"):
                p = self._corpus_root / f"{stem}{suffix}"
                if p.exists():
                    yield p

    def _merge_node(
        self,
        bucket: dict[str, ReferenceNode],
        new_node: ReferenceNode,
        chapter_num: int,
    ) -> None:
        # 跨章聚合: 同 id → 合并 payload.chapter_appearances
        if new_node.id in bucket:
            existing = bucket[new_node.id]
            merged_chapters = sorted(
                set(existing.payload.get("chapter_appearances", []) + [chapter_num])
            )
            bucket[new_node.id] = dataclasses.replace(
                existing,
                payload={**existing.payload, "chapter_appearances": merged_chapters},
            )
        else:
            bucket[new_node.id] = dataclasses.replace(
                new_node,
                payload={**new_node.payload, "chapter_appearances": [chapter_num]},
            )

    @staticmethod
    def _parse_chapter_num(path: Path) -> int:
        stem = path.stem.replace("_大纲", "")
        digits = "".join(c for c in stem if c.isdigit())
        return int(digits) if digits else 0


def _default_storage():
    """Phase 9.11: 默认 storage 走 infra/.state/ripple.db (跟 Phase 9.10 pattern)."""
    from infra.cross_volume.storage import RippleStorage
    return RippleStorage(db_path=Path("infra/.state/ripple.db"))


# --- Phase 9.12 additive: chapter loader for LLM path -----------------

_VOL_RANGES: dict[int, tuple[int, int]] = {
    1: (1, 120),
    2: (121, 240),
    3: (241, 359),
}


def _load_chapters(
    corpus_root: Path = Path("03_内容仓库/04_正文"),
    volume_filter: int | None = None,
) -> list[ChapterContent]:
    """Phase 9.12: 返 ChapterContent list (LLM path scan-and-write 喂料).

    复用 Backfiller._iter_chapters 的 vol 1-3 范围规则 + chapter 解析规则.
    同一 chapter 出现 .md + _大纲.md 时, 用 .md 优先 (LLM 喂正文).
    """
    if not corpus_root.exists():
        return []
    if volume_filter is not None and volume_filter in _VOL_RANGES:
        low, high = _VOL_RANGES[volume_filter]
        chapter_nums = list(range(low, high + 1))
    else:
        chapter_nums = list(range(1, 360))

    out: list[ChapterContent] = []
    for n in chapter_nums:
        stem = f"ch{n:03d}"
        md_path = corpus_root / f"{stem}.md"
        outline_path = corpus_root / f"{stem}_大纲.md"
        if md_path.exists():
            out.append(ChapterContent(id=n, content=md_path.read_text(encoding="utf-8")))
        elif outline_path.exists():
            out.append(ChapterContent(id=n, content=outline_path.read_text(encoding="utf-8")))
    return out

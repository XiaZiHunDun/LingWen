"""灵文提示词工程 · 上下文压缩器

V3.1 Phase 1.3 — 长篇小说场景下的上下文压缩。

设计原则:
- head-tail 截断: 保留开头 50% + 结尾 40% + 中间 10% 摘要
- 伏笔保护: 未回收伏笔始终保留，不压缩
- 关键标记保护: [KEY_EVENT]/[KEY_DIALOGUE]/[KEY_DECISION] 段落不压缩
- 章节粒度: 以章节为单位压缩，不破坏章节边界
- 可逆标记: 压缩段落插入 sentinel，支持回滚

压缩策略:
- head_ratio: 保留开头比例 (默认 0.5)
- tail_ratio: 保留结尾比例 (默认 0.4)
- middle_ratio: 中间摘要比例 (默认 0.1)
- 保护标记: 提取关键段落，不受压缩影响

与 ContextCache 集成:
    cache = ContextCache()
    compressor = ChapterCompressor(max_tokens=8000)
    compressed = compressor.compress(chapters, cache)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


# 压缩 sentinel 标记
SENTINEL_PREFIX = "<!-- LW_COMPRESSED:"
SENTINEL_SUFFIX = "-->"


class CompressorError(Exception):
    """压缩器异常基类"""


class CompressionOverflowError(CompressorError):
    """压缩后仍超出 token 限制"""

    def __init__(self, total_tokens: int, max_tokens: int) -> None:
        self.total_tokens = total_tokens
        self.max_tokens = max_tokens
        super().__init__(f"Compression overflow: {total_tokens} tokens > {max_tokens} limit")


@dataclass
class CompressedChapter:
    """压缩后的章节"""

    chapter_num: int
    original_tokens: int
    compressed_tokens: int
    content: str
    summary: Optional[str] = None
    was_compressed: bool = False

    @property
    def saved_tokens(self) -> int:
        return self.original_tokens - self.compressed_tokens


@dataclass
class CompressionResult:
    """压缩结果"""

    chapters: list[CompressedChapter]
    total_original_tokens: int = 0
    total_compressed_tokens: int = 0
    foreshadow_items: list[str] = field(default_factory=list)

    @property
    def saved_tokens(self) -> int:
        return self.total_original_tokens - self.total_compressed_tokens

    @property
    def compression_ratio(self) -> float:
        if self.total_original_tokens == 0:
            return 0.0
        return self.saved_tokens / self.total_original_tokens


class ChapterCompressor:
    """章节级上下文压缩器

    用法:
        compressor = ChapterCompressor(max_tokens=8000)
        result = compressor.compress_chapters(chapters, foreshadow_list)
    """

    # 关键标记保护（不可压缩的内容）
    KEY_PATTERNS = (
        re.compile(r"\[KEY_EVENT\][^\n]*"),
        re.compile(r"\[KEY_DIALOGUE\][^\n]*"),
        re.compile(r"\[KEY_DECISION\][^\n]*"),
        re.compile(r"\[FORESHADOW\][^\n]*"),  # 伏笔标记
    )

    # 默认压缩比例
    DEFAULT_HEAD_RATIO = 0.5
    DEFAULT_TAIL_RATIO = 0.4
    DEFAULT_MIDDLE_RATIO = 0.1

    # 每 token 字符数估算
    CHARS_PER_TOKEN = 4

    def __init__(
        self,
        max_tokens: int = 8000,
        head_ratio: float = DEFAULT_HEAD_RATIO,
        tail_ratio: float = DEFAULT_TAIL_RATIO,
    ) -> None:
        """
        Args:
            max_tokens: 最大 token 限制
            head_ratio: 保留开头比例
            tail_ratio: 保留结尾比例
        """
        self.max_tokens = max_tokens
        self.head_ratio = head_ratio
        self.tail_ratio = tail_ratio
        self._middle_ratio = max(0.0, 1.0 - head_ratio - tail_ratio)

    def compress_chapters(
        self,
        chapters: list[dict[str, Any]],
        foreshadow_list: Optional[list[str]] = None,
    ) -> CompressionResult:
        """压缩章节列表

        Args:
            chapters: 章节列表，每项包含 {"num": int, "content": str, "summary": Optional[str]}
            foreshadow_list: 未回收伏笔列表（不可压缩）

        Returns:
            CompressionResult
        """
        if not chapters:
            return CompressionResult(chapters=[])

        result_chapters: list[CompressedChapter] = []
        total_original = 0
        foreshadow_items = foreshadow_list or []

        for ch in chapters:
            content = str(ch.get("content", ""))
            chapter_num = ch.get("num", 0)
            summary = ch.get("summary")

            original_tokens = self._estimate_tokens(content)
            total_original += original_tokens

            compressed = CompressedChapter(
                chapter_num=chapter_num,
                original_tokens=original_tokens,
                compressed_tokens=original_tokens,
                content=content,
                summary=summary,
                was_compressed=False,
            )
            result_chapters.append(compressed)

        # 检查是否需要压缩
        if total_original <= self.max_tokens:
            result = CompressionResult(
                chapters=result_chapters,
                total_original_tokens=total_original,
                total_compressed_tokens=total_original,
                foreshadow_items=foreshadow_items,
            )
            return result

        # 需要压缩 — 按章节分配 token 预算
        return self._apply_compression(result_chapters, foreshadow_items, total_original)

    def _apply_compression(
        self,
        chapters: list[CompressedChapter],
        foreshadow_items: list[str],
        total_original: int,
    ) -> CompressionResult:
        """应用压缩算法"""
        n = len(chapters)
        if n == 0:
            return CompressionResult(
                chapters=chapters,
                total_original_tokens=total_original,
                total_compressed_tokens=total_original,
                foreshadow_items=foreshadow_items,
            )

        # 伏笔 token 预算
        foreshadow_text = "\n".join(foreshadow_items)
        foreshadow_tokens = self._estimate_tokens(foreshadow_text)

        # 可用 token 预算
        available = max(0, self.max_tokens - foreshadow_tokens)
        if available <= 0:
            raise CompressionOverflowError(total_original, self.max_tokens)

        if n <= 2:
            # 只有 1-2 章: 等比例截断
            budget_per_chapter = available // n
            for ch in chapters:
                self._truncate_chapter(ch, budget_per_chapter)
        elif n <= 5:
            # 3-5 章: head/tail 保留原文，中间摘要
            head_count = max(1, int(n * self.head_ratio))
            tail_count = max(1, int(n * self.tail_ratio))
            middle_count = n - head_count - tail_count

            head_budget = int(available * self.head_ratio)
            tail_budget = int(available * self.tail_ratio)
            middle_budget = available - head_budget - tail_budget

            # 头部章节: 保留原文
            for ch in chapters[:head_count]:
                self._truncate_chapter(ch, head_budget // head_count)

            # 中间章节: 用摘要替代
            for ch in chapters[head_count : head_count + middle_count]:
                self._summary_replace(ch, middle_budget // max(1, middle_count))

            # 尾部章节: 保留原文
            for ch in chapters[head_count + middle_count :]:
                self._truncate_chapter(ch, tail_budget // max(1, tail_count))
        else:
            # 6+ 章: head/tail 保留原文，中间全部用摘要
            head_count = max(2, int(n * self.head_ratio))
            tail_count = max(2, int(n * self.tail_ratio))

            head_budget = int(available * self.head_ratio)
            tail_budget = int(available * self.tail_ratio)
            middle_budget = available - head_budget - tail_budget

            for ch in chapters[:head_count]:
                self._truncate_chapter(ch, head_budget // head_count)

            middle_chapters = chapters[head_count : n - tail_count]
            for ch in middle_chapters:
                self._summary_replace(ch, middle_budget // max(1, len(middle_chapters)))

            for ch in chapters[n - tail_count :]:
                self._truncate_chapter(ch, tail_budget // tail_count)

        total_compressed = sum(ch.compressed_tokens for ch in chapters)
        return CompressionResult(
            chapters=chapters,
            total_original_tokens=total_original,
            total_compressed_tokens=total_compressed,
            foreshadow_items=foreshadow_items,
        )

    def _truncate_chapter(self, ch: CompressedChapter, max_tokens: int) -> None:
        """截断章节到指定 token 数，保留关键标记"""
        if ch.original_tokens <= max_tokens:
            return

        content = ch.content
        # 提取关键标记
        key_lines: list[str] = []
        remaining = content
        for pattern in self.KEY_PATTERNS:
            for m in pattern.findall(remaining):
                key_lines.append(m)
                remaining = remaining.replace(m, "", 1)

        key_text = "\n".join(key_lines)
        key_tokens = self._estimate_tokens(key_text)

        # 剩余预算
        remaining_budget = max(0, max_tokens - key_tokens)
        max_chars = remaining_budget * self.CHARS_PER_TOKEN

        # 截断正文
        truncated = remaining[:max_chars]

        # 组装
        parts = []
        if truncated.strip():
            parts.append(truncated)
        if key_lines:
            parts.append(f"{SENTINEL_PREFIX}key_markers{SENTINEL_SUFFIX}")
            parts.append(key_text)

        ch.content = "\n".join(parts)
        ch.compressed_tokens = self._estimate_tokens(ch.content)
        ch.was_compressed = True

    def _summary_replace(self, ch: CompressedChapter, max_tokens: int) -> None:
        """用摘要替代章节内容"""
        summary = ch.summary or f"第{ch.chapter_num}章（内容已压缩）"
        max_chars = max_tokens * self.CHARS_PER_TOKEN

        if len(summary) > max_chars:
            summary = summary[: max_chars - 3] + "..."

        ch.content = f"{SENTINEL_PREFIX}ch{ch.chapter_num}_summary{SENTINEL_SUFFIX}\n{summary}"
        ch.compressed_tokens = self._estimate_tokens(ch.content)
        ch.was_compressed = True

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """估算 token 数"""
        if not text:
            return 0
        return max(1, len(text) // ChapterCompressor.CHARS_PER_TOKEN)

    @staticmethod
    def is_compressed(content: str) -> bool:
        """检查内容是否包含压缩 sentinel"""
        return SENTINEL_PREFIX in content

    @staticmethod
    def extract_sentinel_info(content: str) -> dict[str, str]:
        """提取压缩 sentinel 信息

        Returns:
            {"type": "summary", "chapter": "3"} 或 {"type": "key_markers"}
        """
        result: dict[str, str] = {}
        for match in re.finditer(
            re.escape(SENTINEL_PREFIX) + r"(.+?)" + re.escape(SENTINEL_SUFFIX),
            content,
        ):
            info = match.group(1)
            if info.startswith("ch") and "_summary" in info:
                parts = info.split("_")
                result["type"] = "summary"
                result["chapter"] = parts[0].replace("ch", "")
            elif info == "key_markers":
                result["type"] = "key_markers"
        return result


__all__ = [
    "ChapterCompressor",
    "CompressedChapter",
    "CompressionResult",
    "CompressorError",
    "CompressionOverflowError",
]

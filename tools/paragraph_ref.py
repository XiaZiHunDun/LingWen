#!/usr/bin/env python3
"""
段落引用提取模块

为意见仓库提供段落级引用能力，支持：
- 根据行号范围提取内容预览
- 为意见添加段落引用信息
- 保持向后兼容

Usage:
    from paragraph_ref import extract_paragraph_ref, build_opinion_with_ref

    # 提取段落引用
    ref = extract_paragraph_ref("ch001.md", start_line=23, end_line=25)

    # 为意见添加引用
    opinion_with_ref = build_opinion_with_ref(existing_opinion, "ch001.md")
"""


import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

# ============================================================================
# 数据模型
# ============================================================================

class ParagraphRef(BaseModel):
    """
    段落引用结构

    用于精确定位意见所指向的文本段落。

    Attributes:
        start_line: 起始行号（从1开始）
        end_line: 结束行号
        content_preview: 段落内容预览（最多200字符）
    """
    start_line: int = Field(..., ge=1, description="起始行号（从1开始）")
    end_line: int = Field(..., ge=1, description="结束行号")
    content_preview: str = Field(
        default="",
        max_length=200,
        description="段落内容预览（最多200字符）"
    )

    @field_validator("end_line")
    @classmethod
    def end_must_be_gte_start(cls, v: int, info) -> int:
        """结束行号必须大于等于起始行号"""
        if "start_line" in info.data and v < info.data["start_line"]:
            raise ValueError(f"end_line ({v}) must be >= start_line ({info.data['start_line']})")
        return v


class OpinionType(str):
    """意见类型别名"""
    # 常见类型
    LOGIC_ISSUE = "逻辑问题"
    CHARACTER_ISSUE = "人物问题"
    PLOT_HOLE = "剧情漏洞"
    TIMELINE_CONFLICT = "时间线矛盾"
    CONSISTENCY_ISSUE = "一致性冲突"
    STYLE_SUGGESTION = "风格建议"
    PACING_ISSUE = "节奏问题"
    TYPO = "错别字"
    GRAMMAR_ISSUE = "语法问题"
    # 其他
    OTHER = "其他"


class OpinionSeverity(str):
    """意见严重程度"""
    P0 = "P0"  # 致命：逻辑硬伤，影响阅读
    P1 = "P1"  # 严重：一致性冲突，需要修改
    P2 = "P2"  # 中等：轻微不一致，建议修改
    P3 = "P3"  # 提示：风格建议，不强制


class OpinionBase(BaseModel):
    """
    意见基础结构

    定义意见仓库中意见记录的基础字段。
    兼容现有意见仓库格式。
    """
    opinion_id: Optional[str] = Field(default=None, description="意见唯一标识")
    chapter: str = Field(..., description="章节号，如 ch001")
    type: str = Field(default="其他", description="意见类型")
    severity: str = Field(default="P2", description="严重程度 P0-P3")
    description: str = Field(..., description="意见描述")
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))

    # 段落引用（新增字段）
    paragraph_ref: Optional[ParagraphRef] = Field(
        default=None,
        description="段落引用信息"
    )

    class Config:
        """Pydantic配置"""
        extra = "allow"  # 允许额外字段，保证向后兼容


# ============================================================================
# 核心函数
# ============================================================================

def extract_paragraph_ref(
    chapter_path: str | Path,
    start_line: int,
    end_line: int,
    max_preview_chars: int = 200
) -> ParagraphRef:
    """
    从章节文件中提取指定行号范围的段落引用

    Args:
        chapter_path: 章节文件路径（如 /path/to/ch001.md）
        start_line: 起始行号（从1开始）
        end_line: 结束行号
        max_preview_chars: 内容预览最大字符数（默认200）

    Returns:
        ParagraphRef 对象，包含行号范围和内容预览

    Raises:
        FileNotFoundError: 章节文件不存在
        ValueError: 行号范围无效

    Example:
        >>> ref = extract_paragraph_ref("ch001.md", start_line=23, end_line=25)
        >>> print(ref.start_line, ref.end_line, ref.content_preview[:30])
        23 25 '铁门在林夜面前重重合上...'
    """
    chapter_path = Path(chapter_path)

    if not chapter_path.exists():
        raise FileNotFoundError(f"章节文件不存在: {chapter_path}")

    if start_line < 1 or end_line < 1:
        raise ValueError(f"行号必须 >= 1, got start_line={start_line}, end_line={end_line}")

    if end_line < start_line:
        raise ValueError(f"end_line ({end_line}) must be >= start_line ({start_line})")

    # 读取文件内容
    with open(chapter_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 提取指定行范围的内容（行号从1开始）
    start_idx = start_line - 1  # 转换为0-based索引
    end_idx = end_line  # 切片不包含end_idx，所以不用-1

    if start_idx >= len(lines):
        raise ValueError(f"start_line ({start_line}) 超出文件行数 ({len(lines)})")

    # 获取实际结束位置
    actual_end = min(end_idx, len(lines))
    selected_lines = lines[start_idx:actual_end]

    # 拼接内容并清理空白
    content = "".join(selected_lines)
    content = re.sub(r"\n+", " ", content)  # 换行符替换为空格
    content = re.sub(r"\s+", " ", content)  # 多个空白合并为单个
    content = content.strip()

    # 截断预览
    if len(content) > max_preview_chars:
        content = content[:max_preview_chars] + "..."

    return ParagraphRef(
        start_line=start_line,
        end_line=end_line,
        content_preview=content
    )


def build_opinion_with_ref(
    opinion: Dict[str, Any],
    chapter_path: str | Path,
    line_field: str = "line",
    end_line_field: str = "end_line"
) -> Dict[str, Any]:
    """
    为现有意见字典添加段落引用信息

    保持向后兼容：如果意见中已有段落引用信息，则保留。
    如果意见中包含行号信息，则尝试提取段落引用。

    Args:
        opinion: 现有意见字典（如从JSON加载的）
        chapter_path: 对应的章节文件路径
        line_field: 行号字段名（默认 "line"）
        end_line_field: 结束行号字段名（默认 "end_line"）

    Returns:
        添加了 paragraph_ref 字段的新意见字典

    Example:
        >>> opinion = {
        ...     "opinion_id": "op001",
        ...     "chapter": "ch001",
        ...     "line": 23,
        ...     "description": "时间线矛盾"
        ... }
        >>> result = build_opinion_with_ref(opinion, "/path/to/ch001.md")
        >>> print(result["paragraph_ref"]["start_line"])
        23
    """
    # 如果已有段落引用，直接返回
    if "paragraph_ref" in opinion and opinion["paragraph_ref"] is not None:
        return opinion

    # 检查是否有行号信息
    line = opinion.get(line_field)
    if line is None:
        # 没有行号信息，返回原始意见
        return opinion

    # 确定结束行号
    end_line = opinion.get(end_line_field, line)

    try:
        # 提取段落引用
        chapter_path_obj = Path(chapter_path)

        # 如果 chapter_path 是相对路径，尝试查找
        if not chapter_path_obj.exists():
            # 尝试在标准位置查找
            standard_paths = [
                Path("03_内容仓库/04_正文") / chapter_path_obj.name,
                Path("06_意见仓库") / ".." / "03_内容仓库/04_正文" / chapter_path_obj.name,
            ]
            for sp in standard_paths:
                if sp.exists():
                    chapter_path_obj = sp
                    break

        paragraph_ref = extract_paragraph_ref(chapter_path_obj, line, end_line)

        # 创建新意见字典（不修改原始）
        result = dict(opinion)
        result["paragraph_ref"] = paragraph_ref.model_dump(exclude_none=True)

        return result

    except (FileNotFoundError, ValueError):
        # 文件不存在或行号无效，返回原始意见
        return opinion


def extract_opinions_with_refs(
    opinions: List[Dict[str, Any]],
    content_root: str | Path
) -> List[Dict[str, Any]]:
    """
    批量为意见列表添加段落引用

    Args:
        opinions: 意见列表
        content_root: 正文文件根目录

    Returns:
        添加了段落引用的意见列表

    Example:
        >>> opinions = [
        ...     {"opinion_id": "op001", "chapter": "ch001", "line": 23, ...},
        ...     {"opinion_id": "op002", "chapter": "ch001", "line": 45, ...}
        ... ]
        >>> results = extract_opinions_with_refs(opinions, "/path/to/04_正文")
    """
    content_root = Path(content_root)
    results = []

    for opinion in opinions:
        chapter = opinion.get("chapter", "")
        if chapter:
            chapter_file = content_root / f"{chapter}.md"
            opinion_with_ref = build_opinion_with_ref(opinion, chapter_file)
        else:
            opinion_with_ref = opinion
        results.append(opinion_with_ref)

    return results


# ============================================================================
# 工具函数
# ============================================================================

def parse_line_reference(text: str) -> tuple[int, int] | None:
    """
    从文本中解析行号引用

    支持格式：
    - "第23行" -> (23, 23)
    - "第23-25行" -> (23, 25)
    - "23行" -> (23, 23)
    - "lines 23-25" -> (23, 25)

    Args:
        text: 包含行号引用的文本

    Returns:
        (start_line, end_line) 元组，解析失败返回 None
    """
    # 中文格式：第23行, 第23-25行
    cn_match = re.match(r"第(\d+)(?:-(\d+))?行", text)
    if cn_match:
        start = int(cn_match.group(1))
        end = int(cn_match.group(2)) if cn_match.group(2) else start
        return (start, end)

    # 英文格式：line 23, lines 23-25
    en_match = re.match(r"(?:line|lines?)\s*(\d+)(?:\s*-\s*(\d+))?", text, re.IGNORECASE)
    if en_match:
        start = int(en_match.group(1))
        end = int(en_match.group(2)) if en_match.group(2) else start
        return (start, end)

    return None


def find_line_for_text(
    chapter_path: str | Path,
    search_text: str,
    context_chars: int = 50
) -> tuple[int, str] | None:
    """
    在章节中查找指定文本，并返回其所在行号

    Args:
        chapter_path: 章节文件路径
        search_text: 要查找的文本（支持模糊匹配）
        context_chars: 模糊匹配时的上下文字符数

    Returns:
        (line_number, line_content) 或 None（未找到）
    """
    chapter_path = Path(chapter_path)

    if not chapter_path.exists():
        return None

    with open(chapter_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    search_lower = search_text.lower()

    for i, line in enumerate(lines, start=1):
        if search_lower in line.lower():
            return (i, line.strip())

    # 模糊匹配：查找包含关键词的段落
    keywords = search_text.split()[:3]  # 取前3个词
    if keywords:
        for i, line in enumerate(lines, start=1):
            if all(kw.lower() in line.lower() for kw in keywords):
                return (i, line.strip())

    return None


# ============================================================================
# 主入口（用于测试）
# ============================================================================

if __name__ == "__main__":

    # 测试用例
    print("=" * 60)
    print("段落引用提取模块 - 测试")
    print("=" * 60)

    # 测试路径
    test_chapter = Path(__file__).parent.parent / "03_内容仓库/04_正文/ch001.md"

    if test_chapter.exists():
        print(f"\n[OK] 测试文件存在: {test_chapter}")

        # 测试1: 提取段落引用
        print("\n--- 测试 extract_paragraph_ref ---")
        ref = extract_paragraph_ref(test_chapter, start_line=23, end_line=25)
        print(f"start_line: {ref.start_line}")
        print(f"end_line: {ref.end_line}")
        print(f"content_preview: {ref.content_preview[:50]}...")

        # 测试2: 行号解析
        print("\n--- 测试 parse_line_reference ---")
        test_cases = ["第23行", "第23-25行", "line 45", "lines 10-20"]
        for tc in test_cases:
            result = parse_line_reference(tc)
            print(f"  '{tc}' -> {result}")

        # 测试3: 查找文本行号
        print("\n--- 测试 find_line_for_text ---")
        result = find_line_for_text(test_chapter, "铁门")
        if result:
            print(f"  找到: 第{result[0]}行 - {result[1][:40]}...")

    else:
        print(f"\n[WARN] 测试文件不存在: {test_chapter}")
        print("跳过运行时测试")

#!/usr/bin/env python3
"""
LLM可读性分析器 - S6可读性检测

功能：
1. 评估段落信息密度
2. 识别冗余描写
3. 分析场景切换流畅度
4. 检测说明性文字过多问题

目标：减少水字数，提升阅读体验
"""

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.llm_service import LLMService


@dataclass
class ReadabilityIssue:
    """可读性问题"""
    chapter: int
    location: str                   # 位置：段落/场景/章节
    issue_type: str                 # 问题类型
    description: str                # 问题描述
    severity: str                    # 严重程度：P0/P1/P2
    water_word_count: int = 0        # 水字数估算
    suggestion: str = ""            # 改进建议


@dataclass
class ReadabilityReport:
    """可读性分析报告"""
    chapter: int
    issues: List[ReadabilityIssue] = field(default_factory=list)
    paragraph_count: int = 0         # 段落数
    avg_paragraph_length: float = 0.0  # 平均段落长度
    redundant_descriptions: int = 0   # 冗余描写数
    excessive_exposition: int = 0     # 过多说明性文字数
    scene_transition_issues: int = 0  # 场景切换问题数
    water_word_estimate: int = 0     # 水字数估算
    score: float = 0.0
    llm_calls: int = 0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if self.issues:
            self.redundant_descriptions = sum(1 for i in self.issues if i.issue_type == "redundant_description")
            self.excessive_exposition = sum(1 for i in self.issues if i.issue_type == "excessive_exposition")
            self.scene_transition_issues = sum(1 for i in self.issues if i.issue_type == "scene_transition")
            self.water_word_estimate = sum(i.water_word_count for i in self.issues)

    def to_dict(self) -> dict:
        return {
            "chapter": self.chapter,
            "paragraph_count": self.paragraph_count,
            "avg_paragraph_length": self.avg_paragraph_length,
            "redundant_descriptions": self.redundant_descriptions,
            "excessive_exposition": self.excessive_exposition,
            "scene_transition_issues": self.scene_transition_issues,
            "water_word_estimate": self.water_word_estimate,
            "score": self.score,
            "llm_calls": self.llm_calls,
            "timestamp": self.timestamp,
            "issues": [
                {
                    "location": i.location,
                    "issue_type": i.issue_type,
                    "description": i.description,
                    "severity": i.severity,
                    "water_word_count": i.water_word_count,
                    "suggestion": i.suggestion
                }
                for i in self.issues
            ]
        }


class ReadabilityAnalyzer:
    """LLM可读性分析器"""

    # 冗余描写模式（辅助检测）
    REDUNDANT_PATTERNS = [
        r"他/她/它\s+[是否]?\s*\w+\s*地",  # 副词滥用
        r"似乎/好像/仿佛.*似乎/好像/仿佛",  # 重复比喻
        r"只见/只见得",  # 滥用"只见"
        r"此时此刻",  # 堆砌强调词
        r"不由自主",  # 常见滥用词
        r"不禁",  # 滥用"不禁"
    ]

    # 说明性文字模式（辅助检测）
    EXPOSITION_PATTERNS = [
        r"所谓.*是指",  # 定义式说明
        r"据悉",  # 据我所知
        r"众所周知",  # 大家都知道
        r"值得一提的是",  # 过度强调
        r"在这里.*需要说明",  # 中断叙事的说明
    ]

    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm = llm_service or LLMService()
        self.project_root = PROJECT_ROOT
        self.chapters_dir = self.project_root / "03_内容仓库" / "04_正文"
        self.report_dir = self.project_root / "06_意见仓库" / "07_一致性检查"

    def load_chapter(self, chapter_num: int) -> Optional[str]:
        """加载章节内容"""
        ch_file = self.chapters_dir / f"ch{chapter_num:03d}.md"
        if not ch_file.exists():
            return None
        return ch_file.read_text(encoding='utf-8')

    def load_chapters(self, chapter_nums: List[int]) -> Dict[int, str]:
        """批量加载章节"""
        result = {}
        for num in chapter_nums:
            content = self.load_chapter(num)
            if content:
                result[num] = content
        return result

    def _analyze_paragraph_stats(self, content: str) -> tuple:
        """分析段落统计"""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        total_length = sum(len(p) for p in paragraphs)
        avg_length = total_length / len(paragraphs) if paragraphs else 0
        return len(paragraphs), avg_length

    def analyze_readability(
        self,
        chapter_num: int,
        content: str,
        context_chapters: Optional[Dict[int, str]] = None
    ) -> ReadabilityReport:
        """
        分析章节可读性

        Args:
            chapter_num: 章节号
            content: 章节内容
            context_chapters: 上下文章节

        Returns:
            ReadabilityReport
        """
        report = ReadabilityReport(chapter=chapter_num)

        # 基础统计
        report.paragraph_count, report.avg_paragraph_length = self._analyze_paragraph_stats(content)

        # 构建上下文
        context = ""
        if context_chapters:
            for ch_num in sorted(context_chapters.keys()):
                if ch_num != chapter_num:
                    ctx_content = context_chapters[ch_num][:400]
                    context += f"\n=== 第{ch_num}章 ===\n{ctx_content}"

        prompt = f"""你是小说可读性分析专家，负责评估文字信息密度和减少水字数。

当前章节（第{chapter_num}章）:
{content[:3000]}

上文章节（用于判断内容连贯性）:
{context[:2000] if context else "无"}


## 任务1：识别冗余描写

冗余描写指重复、啰嗦、可删除而不影响理解的文字。

检测以下模式：
- **重复描写**：相同意思用不同词说了多遍
- **过度描写**：用一个长段落描写一个简单动作
- **无用细节**：与剧情无关的描写（如环境细节过于详细）
- **副词滥用**：大量使用"-地"结构的副词

## 任务2：检测说明性文字

说明性文字（ exposition）会中断叙事，让读者出戏。

检测以下模式：
- **定义式说明**："所谓XX是指YY"
- **过度强调**："值得一提的是"、"众所周知"
- **中断式说明**：突然插入的背景介绍
- **百科式罗列**：堆砌设定的文字

## 任务3：分析场景切换

场景切换应该流畅自然。

检测：
- 是否有突兀的场景跳转（没有过渡）
- 场景切换是否使用了过多时间标记（"然后"、"接着"）
- 是否在同一场景内跳跃时间线

## 任务4：评估信息密度

信息密度指每千字包含的有效剧情量。

检测：
- 是否有"水"的段落（推进很少）
- 章节中有多少内容是有效剧情/情感/信息
- 估算水字数

## 输出格式

返回JSON：
```json
{{
  "issues": [
    {{
      "location": "段落/位置描述",
      "issue_type": "redundant_description/excessive_exposition/scene_transition/water_content",
      "description": "问题描述",
      "severity": "P0/P1/P2",
      "water_word_count": 估算水字数,
      "suggestion": "改进建议"
    }}
  ],
  "summary": {{
    "paragraph_count": N,
    "avg_paragraph_length": N,
    "redundant_descriptions": N,
    "excessive_exposition": N,
    "scene_transition_issues": N,
    "water_word_estimate": N,
    "score": 0.0-1.0
  }}
}}
```

如果没有发现问题：
```json
{{"issues": [], "summary": {{"paragraph_count": N, "score": 1.0}}}}```"""

        response = self.llm.generate(
            prompt=prompt,
            system="你是一个专业的小说可读性分析专家，擅长减少水字数和提升信息密度。",
            model="default"
        )
        report.llm_calls = 1

        try:
            # 解析JSON
            try:
                data = json.loads(response)
            except json.JSONDecodeError:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    data = {"issues": [], "summary": {}}

            issues = data.get("issues", [])
            summary = data.get("summary", {})

            # 构建问题记录
            for iss in issues:
                issue = ReadabilityIssue(
                    chapter=chapter_num,
                    location=iss.get("location", "未知"),
                    issue_type=iss.get("issue_type", "unknown"),
                    description=iss.get("description", ""),
                    severity=iss.get("severity", "P2"),
                    water_word_count=iss.get("water_word_count", 0),
                    suggestion=iss.get("suggestion", "")
                )
                report.issues.append(issue)

            # 更新统计
            report.paragraph_count = summary.get("paragraph_count", report.paragraph_count)
            report.avg_paragraph_length = summary.get("avg_paragraph_length", report.avg_paragraph_length)
            report.redundant_descriptions = summary.get("redundant_descriptions", report.redundant_descriptions)
            report.excessive_exposition = summary.get("excessive_exposition", report.excessive_exposition)
            report.scene_transition_issues = summary.get("scene_transition_issues", report.scene_transition_issues)
            report.water_word_estimate = summary.get("water_word_estimate", report.water_word_estimate)

            # 计算分数
            # 基于问题数量和水字数估算
            if report.paragraph_count > 0:
                issue_ratio = min(0.5, len(report.issues) / report.paragraph_count * 0.5)
                water_ratio = min(0.3, report.water_word_estimate / (len(content) + 1))
                report.score = max(0, 1 - issue_ratio - water_ratio)
            else:
                report.score = 1.0

        except Exception:
            report.score = 0.5

        return report

    def analyze_chapters_batch(
        self,
        chapter_nums: List[int],
        parallel: bool = True,
        max_workers: int = 5
    ) -> Dict[int, ReadabilityReport]:
        """批量分析章节可读性"""
        reports = {}
        contents = self.load_chapters(chapter_nums)

        if parallel:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {}
                for ch in chapter_nums:
                    if ch in contents:
                        context = {
                            c: contents[c]
                            for c in contents
                            if abs(c - ch) <= 3 and c != ch
                        }
                        future = executor.submit(
                            self.analyze_readability,
                            ch, contents[ch], context
                        )
                        futures[future] = ch

                for future in as_completed(futures):
                    ch = futures[future]
                    try:
                        reports[ch] = future.result()
                    except Exception as e:
                        print(f"  ch{ch:03d}: 分析失败 - {e}")
        else:
            for ch in chapter_nums:
                if ch in contents:
                    context = {
                        c: contents[c]
                        for c in contents
                        if abs(c - ch) <= 3 and c != ch
                    }
                    try:
                        reports[ch] = self.analyze_readability(ch, contents[ch], context)
                    except Exception as e:
                        print(f"  ch{ch:03d}: 分析失败 - {e}")

        return reports

    def generate_summary_report(
        self,
        reports: Dict[int, ReadabilityReport]
    ) -> dict:
        """生成汇总报告"""
        total_paragraphs = sum(r.paragraph_count for r in reports.values())
        total_redundant = sum(r.redundant_descriptions for r in reports.values())
        total_exposition = sum(r.excessive_exposition for r in reports.values())
        total_transition = sum(r.scene_transition_issues for r in reports.values())
        total_water = sum(r.water_word_estimate for r in reports.values())
        avg_score = sum(r.score for r in reports.values()) / len(reports) if reports else 0

        return {
            "timestamp": datetime.now().isoformat(),
            "total_chapters": len(reports),
            "total_paragraphs": total_paragraphs,
            "total_redundant_descriptions": total_redundant,
            "total_excessive_exposition": total_exposition,
            "total_scene_transition_issues": total_transition,
            "total_water_words": total_water,
            "avg_score": avg_score,
            "quality_grade": (
                "A（优秀）" if avg_score >= 0.85 else
                "B（良好）" if avg_score >= 0.70 else
                "C（一般）" if avg_score >= 0.50 else
                "D（需改进）"
            ),
            "chapters": {
                ch: r.to_dict()
                for ch, r in reports.items()
            }
        }

    def save_report(self, report_data: dict, output_file: Path):
        """保存报告"""
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(json.dumps(report_data, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"可读性分析报告已保存: {output_file}")


def parse_chapter_range(chapters_str: str) -> List[int]:
    """解析章节范围字符串"""
    chapters = []
    for part in chapters_str.split(','):
        part = part.strip()
        if '-' in part:
            start, end = map(int, part.split('-'))
            chapters.extend(range(start, end + 1))
        else:
            chapters.append(int(part))
    return chapters


def main():
    parser = argparse.ArgumentParser(description='LLM可读性分析器 - S6可读性检测')
    parser.add_argument('--chapters', type=str, default='1-360', help='章节范围')
    parser.add_argument('--parallel', action='store_true', default=True, help='并行处理')
    parser.add_argument('--sequential', dest='parallel', action='store_false', help='顺序处理')
    parser.add_argument('--output', type=str, help='报告输出路径')
    parser.add_argument('--workers', type=int, default=5, help='并行工作线程数')

    args = parser.parse_args()
    chapters = parse_chapter_range(args.chapters)

    print("=" * 60)
    print("LLM可读性分析器 v9.10 - S6可读性检测")
    print(f"章节范围: {chapters[0]}-{chapters[-1]} ({len(chapters)}章)")
    print("=" * 60)

    analyzer = ReadabilityAnalyzer()
    reports = analyzer.analyze_chapters_batch(
        chapters,
        parallel=args.parallel,
        max_workers=args.workers
    )

    # 生成汇总报告
    summary = analyzer.generate_summary_report(reports)

    # 保存结果
    output_file = Path(args.output) if args.output else analyzer.report_dir / "readability_report.json"
    analyzer.save_report(summary, output_file)

    # 输出统计
    print("\n" + "=" * 60)
    print("分析完成")
    print(f"分析章节: {len(reports)}")
    print(f"冗余描写: {summary['total_redundant_descriptions']}")
    print(f"过多说明: {summary['total_excessive_exposition']}")
    print(f"场景切换问题: {summary['total_scene_transition_issues']}")
    print(f"估算水字数: {summary['total_water_words']}")
    print(f"平均质量分: {summary['avg_score']:.2f}")
    print(f"质量评级: {summary['quality_grade']}")
    print("=" * 60)


if __name__ == '__main__':
    main()

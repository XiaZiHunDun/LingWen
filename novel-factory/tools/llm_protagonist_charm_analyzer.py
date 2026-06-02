#!/usr/bin/env python3
"""
LLM主角魅力分析器 - S7主角魅力检测

功能：
1. 分析主角行为动机合理度
2. 评估主角决策逻辑性
3. 识别开金手指过多问题
4. 检测主角被动性问题

目标：提升代入感，防止主角成为工具人
"""

import sys
import json
import re
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.llm_service import LLMService


@dataclass
class CharmIssue:
    """魅力问题"""
    chapter: int
    character: str
    issue_type: str                # 问题类型
    description: str               # 问题描述
    severity: str                  # 严重程度：P0/P1/P2
    suggestion: str = ""           # 改进建议


@dataclass
class ProtagonistCharmReport:
    """主角魅力分析报告"""
    chapter: int
    protagonist: str = "林夜"
    issues: List[CharmIssue] = field(default_factory=list)
    goldfinger_count: int = 0      # 金手指次数
    passive_count: int = 0          # 被动次数
    unreasonable_motivation_count: int = 0  # 不合理动机次数
    decisions_count: int = 0       # 决策总数
    score: float = 0.0
    llm_calls: int = 0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if self.issues:
            self.goldfinger_count = sum(1 for i in self.issues if i.issue_type == "goldfinger")
            self.passive_count = sum(1 for i in self.issues if i.issue_type == "passive")
            self.unreasonable_motivation_count = sum(1 for i in self.issues if i.issue_type == "unreasonable_motivation")
            self.decisions_count = sum(1 for i in self.issues if i.issue_type == "decision")

    def to_dict(self) -> dict:
        return {
            "chapter": self.chapter,
            "protagonist": self.protagonist,
            "goldfinger_count": self.goldfinger_count,
            "passive_count": self.passive_count,
            "unreasonable_motivation_count": self.unreasonable_motivation_count,
            "decisions_count": self.decisions_count,
            "score": self.score,
            "llm_calls": self.llm_calls,
            "timestamp": self.timestamp,
            "issues": [
                {
                    "character": i.character,
                    "issue_type": i.issue_type,
                    "description": i.description,
                    "severity": i.severity,
                    "suggestion": i.suggestion
                }
                for i in self.issues
            ]
        }


class ProtagonistCharmAnalyzer:
    """LLM主角魅力分析器"""

    # 金手指特征关键词
    GOLD_FINGER_KEYWORDS = [
        "突然觉醒", "瞬间突破", "毫无预兆", "莫名其妙",
        "凭空出现", "意外获得", "神奇", "奇迹",
        "无敌", "秒杀", "碾压", "轻松",
        "不合理", "太巧了", "刚好", "恰好"
    ]

    # 被动型行为关键词
    PASSIVE_KEYWORDS = [
        "被推动", "被安排", "被告知", "被带领",
        "不知所措", "只能", "被迫", "无可奈何",
        "听天由命", "等待", "跟随", "顺从"
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

    def analyze_protagonist_charm(
        self,
        chapter_num: int,
        content: str,
        protagonist: str = "林夜",
        context_chapters: Optional[Dict[int, str]] = None
    ) -> ProtagonistCharmReport:
        """
        分析主角魅力

        Args:
            chapter_num: 章节号
            content: 章节内容
            protagonist: 主角名
            context_chapters: 上下文章节

        Returns:
            ProtagonistCharmReport
        """
        report = ProtagonistCharmReport(chapter=chapter_num, protagonist=protagonist)

        # 构建上下文
        context = ""
        if context_chapters:
            for ch_num in sorted(context_chapters.keys()):
                if ch_num != chapter_num:
                    ctx_content = context_chapters[ch_num][:400]
                    context += f"\n=== 第{ch_num}章 ===\n{ctx_content}"

        prompt = f"""你是小说主角魅力分析专家，负责评估主角的吸引力和代入感。

当前章节（第{chapter_num}章）:
{content[:3000]}

上文章节（用于判断主角行为连贯性）:
{context[:2000] if context else "无"}


主角: {protagonist}


## 任务1：检测"金手指"问题

金手指指主角获得不合理的能力/运气/资源。

检测以下模式：
- **能力金手指**：主角突然获得超强能力，没有铺垫
- **运气金手指**：关键时刻总是运气好到离谱
- **资源金手指**：主角总是能获得稀有资源/宝物
- **剧情金手指**：反派总是犯低级错误，主角总能逃脱

评估：
- 这个金手指是否有前期铺垫？
- 是否影响了故事的紧张感？
- 是否让读者觉得"太假"？

## 任务2：检测被动性问题

被动型主角总是被剧情推着走，而不是主动做决定。

检测以下模式：
- 主角总是"被迫"行动，而不是主动选择
- 主角遇到问题不主动思考，等待他人告知
- 主角的决定由他人主导（NPC操控主角）
- 主角没有自己的目标和欲望

## 任务3：评估决策合理度

- 主角的每个决定是否有合理的动机？
- 决定是否符合角色性格和智商？
- 决定的后果是否可控？

## 任务4：检测代入感问题

- 主角是否在关键时刻"掉链子"（突然变笨/变弱）？
- 主角是否有太多的"内心独白"让读者烦躁？
- 主角是否太完美（高富帅/白富美无所不能）？

## 输出格式

返回JSON：
```json
{{
  "issues": [
    {{
      "character": "{protagonist}",
      "issue_type": "goldfinger/passive/unreasonable_motivation/decision/idealized",
      "description": "问题描述（具体段落）",
      "severity": "P0/P1/P2",
      "suggestion": "改进建议"
    }}
  ],
  "summary": {{
    "goldfinger_count": N,
    "passive_count": N,
    "unreasonable_motivation_count": N,
    "decisions_count": N,
    "score": 0.0-1.0
  }}
}}
```

如果没有发现问题：
```json
{{"issues": [], "summary": {{"goldfinger_count": 0, "passive_count": 0, "score": 1.0}}}}```"""

        response = self.llm.generate(
            prompt=prompt,
            system="你是一个专业的小说主角魅力分析专家，擅长提升主角代入感和避免工具人化。",
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
                issue = CharmIssue(
                    chapter=chapter_num,
                    character=iss.get("character", protagonist),
                    issue_type=iss.get("issue_type", "unknown"),
                    description=iss.get("description", ""),
                    severity=iss.get("severity", "P2"),
                    suggestion=iss.get("suggestion", "")
                )
                report.issues.append(issue)

            # 更新统计
            report.goldfinger_count = summary.get("goldfinger_count", report.goldfinger_count)
            report.passive_count = summary.get("passive_count", report.passive_count)
            report.unreasonable_motivation_count = summary.get("unreasonable_motivation_count", report.unreasonable_motivation_count)
            report.decisions_count = summary.get("decisions_count", 0)

            # 计算分数
            goldfinger_penalty = min(0.3, report.goldfinger_count * 0.1)
            passive_penalty = min(0.3, report.passive_count * 0.1)
            motivation_penalty = min(0.2, report.unreasonable_motivation_count * 0.1)

            score = 1.0 - goldfinger_penalty - passive_penalty - motivation_penalty
            report.score = max(0, min(1, score))

        except Exception as e:
            report.score = 0.5

        return report

    def analyze_chapters_batch(
        self,
        chapter_nums: List[int],
        protagonist: str = "林夜",
        parallel: bool = True,
        max_workers: int = 5
    ) -> Dict[int, ProtagonistCharmReport]:
        """批量分析章节主角魅力"""
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
                            if abs(c - ch) <= 10 and c != ch
                        }
                        future = executor.submit(
                            self.analyze_protagonist_charm,
                            ch, contents[ch], protagonist, context
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
                        if abs(c - ch) <= 10 and c != ch
                    }
                    try:
                        reports[ch] = self.analyze_protagonist_charm(ch, contents[ch], protagonist, context)
                    except Exception as e:
                        print(f"  ch{ch:03d}: 分析失败 - {e}")

        return reports

    def generate_summary_report(
        self,
        reports: Dict[int, ProtagonistCharmReport],
        protagonist: str = "林夜"
    ) -> dict:
        """生成汇总报告"""
        total_goldfinger = sum(r.goldfinger_count for r in reports.values())
        total_passive = sum(r.passive_count for r in reports.values())
        total_unreasonable = sum(r.unreasonable_motivation_count for r in reports.values())
        avg_score = sum(r.score for r in reports.values()) / len(reports) if reports else 0

        return {
            "timestamp": datetime.now().isoformat(),
            "protagonist": protagonist,
            "total_chapters": len(reports),
            "total_goldfinger": total_goldfinger,
            "total_passive": total_passive,
            "total_unreasonable_motivation": total_unreasonable,
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
        print(f"主角魅力分析报告已保存: {output_file}")


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
    parser = argparse.ArgumentParser(description='LLM主角魅力分析器 - S7主角魅力检测')
    parser.add_argument('--chapters', type=str, default='1-360', help='章节范围')
    parser.add_argument('--protagonist', type=str, default='林夜', help='主角名')
    parser.add_argument('--parallel', action='store_true', default=True, help='并行处理')
    parser.add_argument('--sequential', dest='parallel', action='store_false', help='顺序处理')
    parser.add_argument('--output', type=str, help='报告输出路径')
    parser.add_argument('--workers', type=int, default=5, help='并行工作线程数')

    args = parser.parse_args()
    chapters = parse_chapter_range(args.chapters)

    print("=" * 60)
    print("LLM主角魅力分析器 v9.10 - S7主角魅力检测")
    print(f"主角: {args.protagonist}")
    print(f"章节范围: {chapters[0]}-{chapters[-1]} ({len(chapters)}章)")
    print("=" * 60)

    analyzer = ProtagonistCharmAnalyzer()
    reports = analyzer.analyze_chapters_batch(
        chapters,
        protagonist=args.protagonist,
        parallel=args.parallel,
        max_workers=args.workers
    )

    # 生成汇总报告
    summary = analyzer.generate_summary_report(reports, args.protagonist)

    # 保存结果
    output_file = Path(args.output) if args.output else analyzer.report_dir / "protagonist_charm_report.json"
    analyzer.save_report(summary, output_file)

    # 输出统计
    print("\n" + "=" * 60)
    print("分析完成")
    print(f"主角: {args.protagonist}")
    print(f"分析章节: {len(reports)}")
    print(f"金手指问题: {summary['total_goldfinger']}")
    print(f"被动性问题: {summary['total_passive']}")
    print(f"不合理动机: {summary['total_unreasonable_motivation']}")
    print(f"平均质量分: {summary['avg_score']:.2f}")
    print(f"质量评级: {summary['quality_grade']}")
    print("=" * 60)


if __name__ == '__main__':
    main()
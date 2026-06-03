#!/usr/bin/env python3
"""
LLM人物弧光分析器 - S8人物弧光检测

功能：
1. 追踪角色心态变化曲线
2. 验证转变节点的合理性
3. 评估弧光完整度（起承转合）
4. 检测角色"工具人化"问题

目标：角色深度提升，防止角色成为剧情工具
"""

import sys
import json
import re
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.llm_service import LLMService


@dataclass
class CharacterArcPoint:
    """角色弧光节点"""
    chapter: int
    character: str
    mental_state: str              # 当时心态
    change_trigger: str             # 变化触发点
    change_type: str                # 变化类型：growth（成长）/ regression（倒退）/ revelation（觉醒）/ stable（稳定）
    is_reasonable: bool             # 变化是否合理
    arc_completeness: str           # 弧光完整度：full（完整）/ partial（部分）/ broken（断裂）
    suggestion: str = ""            # 改进建议


@dataclass
class CharacterArcReport:
    """角色弧光分析报告"""
    chapter: int
    character_arcs: List[CharacterArcPoint] = field(default_factory=list)
    characters_analyzed: int = 0
    full_arcs: int = 0
    partial_arcs: int = 0
    broken_arcs: int = 0
    unreasonable_changes: int = 0
    tool_character_count: int = 0   # 工具人化角色数
    score: float = 0.0
    llm_calls: int = 0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if self.character_arcs:
            self.full_arcs = sum(1 for a in self.character_arcs if a.arc_completeness == "full")
            self.partial_arcs = sum(1 for a in self.character_arcs if a.arc_completeness == "partial")
            self.broken_arcs = sum(1 for a in self.character_arcs if a.arc_completeness == "broken")
            self.unreasonable_changes = sum(1 for a in self.character_arcs if not a.is_reasonable)

    def to_dict(self) -> dict:
        return {
            "chapter": self.chapter,
            "characters_analyzed": self.characters_analyzed,
            "full_arcs": self.full_arcs,
            "partial_arcs": self.partial_arcs,
            "broken_arcs": self.broken_arcs,
            "unreasonable_changes": self.unreasonable_changes,
            "tool_character_count": self.tool_character_count,
            "score": self.score,
            "llm_calls": self.llm_calls,
            "timestamp": self.timestamp,
            "character_arcs": [
                {
                    "character": a.character,
                    "mental_state": a.mental_state,
                    "change_trigger": a.change_trigger,
                    "change_type": a.change_type,
                    "is_reasonable": a.is_reasonable,
                    "arc_completeness": a.arc_completeness,
                    "suggestion": a.suggestion
                }
                for a in self.character_arcs
            ]
        }


class CharacterArcAnalyzer:
    """LLM人物弧光分析器"""

    # 主要角色列表（可从配置文件加载）
    MAIN_CHARACTERS = [
        "林夜", "苏琳", "星月", "小九", "铁蛋",
        "莫言", "暗皇", "虚无之主", "剑尘子"
    ]

    # 工具人化特征
    TOOL_CHARACTER_TRAITS = [
        "只在需要时出现",
        "没有自己的欲望和恐惧",
        "功能单一（只提供信息/战斗/助攻）",
        "从不主动做决定",
        "性格没有变化",
        "退出后无人记得",
        "与其他角色无深层互动"
    ]

    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm = llm_service or LLMService()
        self.project_root = PROJECT_ROOT
        self.chapters_dir = self.project_root / "03_内容仓库" / "04_正文"
        self.character_profiles_file = self.project_root / "03_内容仓库" / "角色设定" / "character_profiles.json"
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

    def load_character_profiles(self) -> List[dict]:
        """加载角色设定档案"""
        if self.character_profiles_file.exists():
            try:
                data = json.loads(self.character_profiles_file.read_text(encoding='utf-8'))
                return data.get("characters", [])
            except:
                pass
        return []

    def analyze_chapter_arcs(
        self,
        chapter_num: int,
        content: str,
        context_chapters: Optional[Dict[int, str]] = None,
        characters_to_track: Optional[List[str]] = None
    ) -> CharacterArcReport:
        """
        分析章节中角色的弧光变化

        Args:
            chapter_num: 章节号
            content: 章节内容
            context_chapters: 上下文章节（用于追踪心态变化）
            characters_to_track: 要追踪的角色列表

        Returns:
            CharacterArcReport
        """
        report = CharacterArcReport(chapter=chapter_num)

        # 获取角色列表
        if characters_to_track is None:
            profiles = self.load_character_profiles()
            if profiles:
                characters_to_track = [p.get("name", "") for p in profiles if p.get("name")]
            else:
                characters_to_track = self.MAIN_CHARACTERS

        # 构建上下文
        context = ""
        if context_chapters:
            for ch_num in sorted(context_chapters.keys()):
                if ch_num != chapter_num:
                    ctx_content = context_chapters[ch_num][:400]
                    context += f"\n=== 第{ch_num}章 ===\n{ctx_content}"

        prompt = f"""你是小说人物弧光分析专家，负责追踪角色心态变化和评估弧光质量。

当前章节（第{chapter_num}章）:
{content[:3000]}

上文章节（用于追踪角色心态变化）:
{context[:2000] if context else "无"}


要追踪的角色: {', '.join(characters_to_track)}


## 任务1：追踪角色心态变化

对每个主要角色，分析：
1. **当前心态**：这个角色在这一章的心态是什么？
2. **变化触发点**：是什么事件/对话导致心态变化？
3. **变化类型**：
   - growth（成长）：角色学到新东西/变得更强/心态更成熟
   - regression（倒退）：角色受挫/放弃/心态崩溃
   - revelation（觉醒）：角色突然明白某事/做出重大决定
   - stable（稳定）：角色没有明显变化

## 任务2：评估弧光完整度

完整的人物弧光应该包含：
- **起**（Arc Start）：角色起始状态/问题
- **承**（Build）：角色遇到挑战/内心挣扎
- **转**（Turn）：关键转折点/重大决定
- **合**（Resolution）：弧光完成/成长体现

检测以下问题：
- **断裂弧光**：角色突然从A变到C，没有B铺垫
- **跳跃弧光**：角色在短时间内完成巨大转变，不合理
- **缺失弧光**：角色一直是静态的，没有任何成长

## 任务3：检测工具人化

检测角色是否沦为"工具人"（为剧情服务但缺乏个性）：
- 只在需要时出现，没有自己的欲望
- 功能单一，提供信息/助攻后就消失
- 从不主动做决定，总是跟随他人
- 与其他角色无深层情感联系

## 输出格式

返回JSON：
```json
{{
  "character_arcs": [
    {{
      "character": "角色名",
      "mental_state": "当前心态描述",
      "change_trigger": "变化触发点",
      "change_type": "growth/regression/revelation/stable",
      "is_reasonable": true/false,
      "arc_completeness": "full/partial/broken",
      "suggestion": "改进建议"
    }}
  ],
  "tool_characters": ["工具人化的角色列表"],
  "summary": {{
    "characters_analyzed": N,
    "full_arcs": N,
    "partial_arcs": N,
    "broken_arcs": N,
    "unreasonable_changes": N,
    "tool_character_count": N
  }},
  "score": 0.0-1.0
}}
```

如果没有发现明显弧光变化，返回：
```json
{{"character_arcs": [], "tool_characters": [], "summary": {{"characters_analyzed": 0}}}}```"""

        response = self.llm.generate(
            prompt=prompt,
            system="你是一个专业的小说人物弧光分析专家，擅长追踪角色成长和检测工具人化问题。",
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
                    data = {"character_arcs": [], "tool_characters": [], "summary": {}}

            arcs = data.get("character_arcs", [])
            tool_chars = data.get("tool_characters", [])
            summary = data.get("summary", {})

            # 构建弧光记录
            for arc in arcs:
                point = CharacterArcPoint(
                    chapter=chapter_num,
                    character=arc.get("character", ""),
                    mental_state=arc.get("mental_state", ""),
                    change_trigger=arc.get("change_trigger", ""),
                    change_type=arc.get("change_type", "stable"),
                    is_reasonable=arc.get("is_reasonable", True),
                    arc_completeness=arc.get("arc_completeness", "partial"),
                    suggestion=arc.get("suggestion", "")
                )
                report.character_arcs.append(point)

            # 更新统计
            report.characters_analyzed = summary.get("characters_analyzed", len(report.character_arcs))
            report.full_arcs = summary.get("full_arcs", report.full_arcs)
            report.partial_arcs = summary.get("partial_arcs", report.partial_arcs)
            report.broken_arcs = summary.get("broken_arcs", report.broken_arcs)
            report.unreasonable_changes = summary.get("unreasonable_changes", report.unreasonable_changes)
            report.tool_character_count = summary.get("tool_character_count", len(tool_chars))

            # 计算分数
            if report.characters_analyzed > 0:
                # 完整弧光占比 + 合理变化占比 - 工具人化惩罚
                full_ratio = report.full_arcs / report.characters_analyzed
                reasonable_ratio = 1 - (report.unreasonable_changes / report.characters_analyzed)
                tool_penalty = min(0.3, report.tool_character_count * 0.1)
                report.score = full_ratio * 0.4 + reasonable_ratio * 0.4 - tool_penalty
                report.score = max(0, min(1, report.score))
            else:
                report.score = 1.0

        except Exception as e:
            report.score = 0.5

        return report

    def analyze_chapters_batch(
        self,
        chapter_nums: List[int],
        parallel: bool = True,
        max_workers: int = 5
    ) -> Dict[int, CharacterArcReport]:
        """批量分析章节角色弧光"""
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
                            self.analyze_chapter_arcs,
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
                        if abs(c - ch) <= 10 and c != ch
                    }
                    try:
                        reports[ch] = self.analyze_chapter_arcs(ch, contents[ch], context)
                    except Exception as e:
                        print(f"  ch{ch:03d}: 分析失败 - {e}")

        return reports

    def generate_summary_report(
        self,
        reports: Dict[int, CharacterArcReport]
    ) -> dict:
        """生成汇总报告"""
        total_chars = sum(r.characters_analyzed for r in reports.values())
        full_arcs = sum(r.full_arcs for r in reports.values())
        partial_arcs = sum(r.partial_arcs for r in reports.values())
        broken_arcs = sum(r.broken_arcs for r in reports.values())
        unreasonable = sum(r.unreasonable_changes for r in reports.values())
        tool_chars = sum(r.tool_character_count for r in reports.values())
        avg_score = sum(r.score for r in reports.values()) / len(reports) if reports else 0

        return {
            "timestamp": datetime.now().isoformat(),
            "total_chapters": len(reports),
            "total_character_changes": total_chars,
            "full_arcs": full_arcs,
            "partial_arcs": partial_arcs,
            "broken_arcs": broken_arcs,
            "unreasonable_changes": unreasonable,
            "tool_character_count": tool_chars,
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
        print(f"角色弧光分析报告已保存: {output_file}")


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
    parser = argparse.ArgumentParser(description='LLM人物弧光分析器 - S8人物弧光检测')
    parser.add_argument('--chapters', type=str, default='1-360', help='章节范围')
    parser.add_argument('--parallel', action='store_true', default=True, help='并行处理')
    parser.add_argument('--sequential', dest='parallel', action='store_false', help='顺序处理')
    parser.add_argument('--output', type=str, help='报告输出路径')
    parser.add_argument('--workers', type=int, default=5, help='并行工作线程数')

    args = parser.parse_args()
    chapters = parse_chapter_range(args.chapters)

    print("=" * 60)
    print("LLM人物弧光分析器 v9.10 - S8人物弧光检测")
    print(f"章节范围: {chapters[0]}-{chapters[-1]} ({len(chapters)}章)")
    print("=" * 60)

    analyzer = CharacterArcAnalyzer()
    reports = analyzer.analyze_chapters_batch(
        chapters,
        parallel=args.parallel,
        max_workers=args.workers
    )

    # 生成汇总报告
    summary = analyzer.generate_summary_report(reports)

    # 保存结果
    output_file = Path(args.output) if args.output else analyzer.report_dir / "character_arc_report.json"
    analyzer.save_report(summary, output_file)

    # 输出统计
    print("\n" + "=" * 60)
    print("分析完成")
    print(f"分析章节: {len(reports)}")
    print(f"角色变化总数: {summary['total_character_changes']}")
    print(f"完整弧光: {summary['full_arcs']}")
    print(f"部分弧光: {summary['partial_arcs']}")
    print(f"断裂弧光: {summary['broken_arcs']}")
    print(f"不合理变化: {summary['unreasonable_changes']}")
    print(f"工具人化角色: {summary['tool_character_count']}")
    print(f"平均质量分: {summary['avg_score']:.2f}")
    print(f"质量评级: {summary['quality_grade']}")
    print("=" * 60)


if __name__ == '__main__':
    main()
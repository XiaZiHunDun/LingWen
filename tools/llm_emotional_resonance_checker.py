#!/usr/bin/env python3
"""
LLM情感共鸣分析器 - S4情感共鸣检测

功能：
1. 分析情感描写的层次感
2. 识别模式化煽情 vs 有机情感
3. 评估情感爆发点的节奏
4. 检测情感转折是否突兀

目标：防止"煽情油腻"，提升真实情感共鸣
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
class EmotionalPoint:
    """情感点"""
    chapter: int
    text: str                          # 情感描写原文
    type: str                          # 类型：climax（高潮）/ subtle（细水长流）/ burst（爆发）
    quality: str                       # 质量：organic（有机）/ formulaic（模式化）/ fake（虚假）
    authenticity_score: float          # 真实感评分 0-1
    trigger_type: str                  # 触发类型：sacrifice（牺牲）/ confession（告白）/ reunion（团聚）/ loss（失去）等
    suggestion: str = ""               # 改进建议


@dataclass
class EmotionalResonanceReport:
    """情感共鸣分析报告"""
    chapter: int
    emotional_points: List[EmotionalPoint] = field(default_factory=list)
    total_points: int = 0
    organic_count: int = 0
    formulaic_count: int = 0
    fake_count: int = 0
    authenticity_avg: float = 0.0
    score: float = 0.0
    llm_calls: int = 0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if self.emotional_points:
            self.total_points = len(self.emotional_points)
            self.organic_count = sum(1 for p in self.emotional_points if p.quality == "organic")
            self.formulaic_count = sum(1 for p in self.emotional_points if p.quality == "formulaic")
            self.fake_count = sum(1 for p in self.emotional_points if p.quality == "fake")
            self.authenticity_avg = sum(p.authenticity_score for p in self.emotional_points) / len(self.emotional_points)

    def to_dict(self) -> dict:
        return {
            "chapter": self.chapter,
            "total_points": self.total_points,
            "organic_count": self.organic_count,
            "formulaic_count": self.formulaic_count,
            "fake_count": self.fake_count,
            "authenticity_avg": self.authenticity_avg,
            "score": self.score,
            "llm_calls": self.llm_calls,
            "timestamp": self.timestamp,
            "emotional_points": [
                {
                    "text": p.text[:100],
                    "type": p.type,
                    "quality": p.quality,
                    "authenticity_score": p.authenticity_score,
                    "trigger_type": p.trigger_type,
                    "suggestion": p.suggestion
                }
                for p in self.emotional_points
            ]
        }


class EmotionalResonanceChecker:
    """LLM情感共鸣检测器"""

    # 模式化煽情关键词（检测器辅助判断）
    FORMULAIC_TRIGGERS = [
        "热泪盈眶", "眼眶湿润", "泣不成声", "泪如雨下", "痛哭流涕",
        "义正言辞", "慷慨激昂", "振振有词", "侃侃而谈",
        "深情厚谊", "情深意重", "刻骨铭心", "此生不渝",
        "咬牙切齿", "怒发冲冠", "怒不可遏",
        "毫无疑问", "母庸质疑", "必须承认", "不得不承认"
    ]

    # 有机情感关键词（检测器辅助判断）
    ORGANIC_TRIGGERS = [
        "沉默", "无言", "欲言又止", "欲言又止",
        "苦笑", "轻笑", "苦笑", "强笑",
        "叹息", "长叹", "默然", "愣住",
        "攥紧", "松开", "握紧", "松开",
        "别过脸", "低下头", "避开目光", "不敢看"
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

    def check_emotional_resonance(
        self,
        chapter_num: int,
        content: str,
        context_chapters: Optional[Dict[int, str]] = None
    ) -> EmotionalResonanceReport:
        """
        检测章节情感共鸣质量

        Args:
            chapter_num: 章节号
            content: 章节内容
            context_chapters: 上下文章节

        Returns:
            EmotionalResonanceReport
        """
        report = EmotionalResonanceReport(chapter=chapter_num)

        # 构建上下文
        context = ""
        if context_chapters:
            for ch_num in sorted(context_chapters.keys()):
                if ch_num != chapter_num:
                    ctx_content = context_chapters[ch_num][:400]
                    context += f"\n=== 第{ch_num}章 ===\n{ctx_content}"

        prompt = f"""你是小说情感共鸣分析专家，负责评估情感描写的真实性和质量。

当前章节（第{chapter_num}章）:
{content[:3000]}

上文章节（用于判断情感连贯性）:
{context[:1500] if context else "无"}


## 任务：分析情感共鸣质量

### 1. 识别情感点

请识别章节中的所有情感描写点，包括：
- 高潮情感点（牺牲、告白、生死离别等强烈情感）
- 细腻情感点（沉默、苦笑、叹息等细微情感）
- 爆发情感点（突然的情绪宣泄）

### 2. 评估情感质量

对每个情感点评估：

**有机情感（organic）**：
- 情感发展有铺垫，不是凭空出现
- 角色反应符合性格和处境
- 表达方式有角色特色，不千篇一律
- 与前后情节自然衔接

**模式化煽情（formulaic）**：
- 使用常见煽情套路（如"热泪盈眶"、"义正言辞"等）
- 情感表达过于书面化、正式
- 反应模式化，可以套用到任何角色
- 缺乏角色个性化的情感表达

**虚假情感（fake）**：
- 情感来得突兀，没有前期铺垫
- 与角色性格矛盾（如冷酷角色突然痛哭）
- 为煽情而煽情，破坏故事逻辑
- 使用夸张描写反而显得虚假

### 3. 评估指标

- **真实感评分**：0-1分，评估情感是否真实可信
- **触发类型**：sacrifice（牺牲）/ confession（告白）/ reunion（团聚）/ loss（失去）/ humor（幽默）/ warmth（温情）等
- **改进建议**：如何让情感更真实

### 4. 额外检测

检查以下"情感雷区"：
- "热泪盈眶"类夸张描写是否过多
- 角色是否突然从理性变感性（性格断裂）
- 是否在短时间内连续出现多种强烈情感（情感过载）

## 输出格式

返回JSON：
```json
{{
  "emotional_points": [
    {{
      "text": "情感描写原文（50字）",
      "type": "climax/subtle/burst",
      "quality": "organic/formulaic/fake",
      "authenticity_score": 0.0-1.0,
      "trigger_type": "sacrifice/confession/reunion/loss等",
      "suggestion": "改进建议"
    }}
  ],
  "summary": {{
    "total_points": N,
    "organic_count": N,
    "formulaic_count": N,
    "fake_count": N,
    "authenticity_avg": 0.0-1.0,
    "score": 0.0-1.0
  }},
  "warnings": ["检测到的情感雷区"],
  "overall_advice": "整体改进建议"
}}
```

如果没有明显情感点，返回：
```json
{{"emotional_points": [], "summary": {{"total_points": 0}}, "warnings": [], "overall_advice": ""}}
```"""

        response = self.llm.generate(
            prompt=prompt,
            system="你是一个专业的小说情感共鸣分析专家，擅长识别模式化煽情和提升真实情感。",
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
                    data = {"emotional_points": [], "summary": {}}

            points = data.get("emotional_points", [])
            summary = data.get("summary", {})
            data.get("warnings", [])

            # 构建情感点记录
            for pt in points:
                point = EmotionalPoint(
                    chapter=chapter_num,
                    text=pt.get("text", ""),
                    type=pt.get("type", "subtle"),
                    quality=pt.get("quality", "formulaic"),
                    authenticity_score=pt.get("authenticity_score", 0.5),
                    trigger_type=pt.get("trigger_type", "unknown"),
                    suggestion=pt.get("suggestion", "")
                )
                report.emotional_points.append(point)

            # 更新统计
            report.total_points = summary.get("total_points", len(report.emotional_points))
            report.organic_count = summary.get("organic_count", sum(1 for p in report.emotional_points if p.quality == "organic"))
            report.formulaic_count = summary.get("formulaic_count", sum(1 for p in report.emotional_points if p.quality == "formulaic"))
            report.fake_count = summary.get("fake_count", sum(1 for p in report.emotional_points if p.quality == "fake"))
            report.authenticity_avg = summary.get("authenticity_avg", report.authenticity_avg)

            # 计算分数：有机情感占比高则得分高
            if report.total_points > 0:
                organic_ratio = report.organic_count / report.total_points
                report.score = organic_ratio * 0.6 + report.authenticity_avg * 0.4
            else:
                report.score = 1.0  # 无明显情感点视为合格

            # 如果有虚假情感警告，降低分数
            if report.fake_count > 0:
                report.score *= (1 - report.fake_count * 0.1)

            report.score = max(0, min(1, report.score))

        except Exception:
            report.score = 0.5

        return report

    def check_chapters_batch(
        self,
        chapter_nums: List[int],
        parallel: bool = True,
        max_workers: int = 5
    ) -> Dict[int, EmotionalResonanceReport]:
        """批量检测情感共鸣"""
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
                            if abs(c - ch) <= 5 and c != ch
                        }
                        future = executor.submit(
                            self.check_emotional_resonance,
                            ch, contents[ch], context
                        )
                        futures[future] = ch

                for future in as_completed(futures):
                    ch = futures[future]
                    try:
                        reports[ch] = future.result()
                    except Exception as e:
                        print(f"  ch{ch:03d}: 检测失败 - {e}")
        else:
            for ch in chapter_nums:
                if ch in contents:
                    context = {
                        c: contents[c]
                        for c in contents
                        if abs(c - ch) <= 5 and c != ch
                    }
                    try:
                        reports[ch] = self.check_emotional_resonance(ch, contents[ch], context)
                    except Exception as e:
                        print(f"  ch{ch:03d}: 检测失败 - {e}")

        return reports

    def generate_summary_report(
        self,
        reports: Dict[int, EmotionalResonanceReport]
    ) -> dict:
        """生成汇总报告"""
        total_points = sum(r.total_points for r in reports.values())
        organic = sum(r.organic_count for r in reports.values())
        formulaic = sum(r.formulaic_count for r in reports.values())
        fake = sum(r.fake_count for r in reports.values())
        avg_authenticity = sum(r.authenticity_avg for r in reports.values()) / len(reports) if reports else 0
        avg_score = sum(r.score for r in reports.values()) / len(reports) if reports else 0

        return {
            "timestamp": datetime.now().isoformat(),
            "total_chapters": len(reports),
            "total_emotional_points": total_points,
            "organic_count": organic,
            "formulaic_count": formulaic,
            "fake_count": fake,
            "authenticity_avg": avg_authenticity,
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
        print(f"情感共鸣分析报告已保存: {output_file}")


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
    parser = argparse.ArgumentParser(description='LLM情感共鸣分析器 - S4情感共鸣检测')
    parser.add_argument('--chapters', type=str, default='1-360', help='章节范围')
    parser.add_argument('--parallel', action='store_true', default=True, help='并行处理')
    parser.add_argument('--sequential', dest='parallel', action='store_false', help='顺序处理')
    parser.add_argument('--output', type=str, help='报告输出路径')
    parser.add_argument('--workers', type=int, default=5, help='并行工作线程数')

    args = parser.parse_args()
    chapters = parse_chapter_range(args.chapters)

    print("=" * 60)
    print("LLM情感共鸣分析器 v9.10 - S4情感共鸣检测")
    print(f"章节范围: {chapters[0]}-{chapters[-1]} ({len(chapters)}章)")
    print("=" * 60)

    checker = EmotionalResonanceChecker()
    reports = checker.check_chapters_batch(
        chapters,
        parallel=args.parallel,
        max_workers=args.workers
    )

    # 生成汇总报告
    summary = checker.generate_summary_report(reports)

    # 保存结果
    output_file = Path(args.output) if args.output else checker.report_dir / "emotional_resonance_report.json"
    checker.save_report(summary, output_file)

    # 输出统计
    print("\n" + "=" * 60)
    print("分析完成")
    print(f"检测章节: {len(reports)}")
    print(f"情感点总数: {summary['total_emotional_points']}")
    print(f"  - 有机情感: {summary['organic_count']}")
    print(f"  - 模式化煽情: {summary['formulaic_count']}")
    print(f"  - 虚假情感: {summary['fake_count']}")
    print(f"平均真实感: {summary['authenticity_avg']:.2f}")
    print(f"平均质量分: {summary['avg_score']:.2f}")
    print(f"质量评级: {summary['quality_grade']}")
    print("=" * 60)


if __name__ == '__main__':
    main()

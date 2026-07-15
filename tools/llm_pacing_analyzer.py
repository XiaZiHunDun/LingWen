#!/usr/bin/env python3
"""
LLM节奏分析器增强版 - S5节奏控制

功能：
1. 验证高潮不可预测性
2. 评估冲突紧迫感
3. 检测无效缓冲
4. 分析章节内张力曲线

目标：提升追读欲望，优化阅读体验
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
class TensionPoint:
    """张力点"""
    chapter: int
    position: str                    # 位置：开头/中段/结尾
    tension_type: str               # 类型：conflict（冲突）/ revelation（揭示）/ climax（高潮）/ resolution（解决）
    is_predictable: bool            # 是否可预测
    urgency_level: int              # 紧迫度 1-5
    description: str                # 描述
    suggestion: str = ""            # 改进建议


@dataclass
class PacingReport:
    """节奏分析报告"""
    chapter: int
    tension_points: List[TensionPoint] = field(default_factory=list)
    predictable_count: int = 0      # 可预测高潮数
    low_urgency_count: int = 0        # 低紧迫感数
    invalid_buffer_count: int = 0    # 无效缓冲数
    tension_curve: List[int] = field(default_factory=list)  # 张力曲线
    avg_tension: float = 0.0         # 平均张力
    score: float = 0.0
    llm_calls: int = 0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if self.tension_points:
            self.predictable_count = sum(1 for p in self.tension_points if p.is_predictable)
            self.low_urgency_count = sum(1 for p in self.tension_points if p.urgency_level <= 2)
            self.avg_tension = sum(p.urgency_level for p in self.tension_points) / len(self.tension_points)
            # 构建张力曲线
            self.tension_curve = [p.urgency_level for p in self.tension_points]

    def to_dict(self) -> dict:
        return {
            "chapter": self.chapter,
            "predictable_count": self.predictable_count,
            "low_urgency_count": self.low_urgency_count,
            "invalid_buffer_count": self.invalid_buffer_count,
            "tension_curve": self.tension_curve,
            "avg_tension": self.avg_tension,
            "score": self.score,
            "llm_calls": self.llm_calls,
            "timestamp": self.timestamp,
            "tension_points": [
                {
                    "position": p.position,
                    "tension_type": p.tension_type,
                    "is_predictable": p.is_predictable,
                    "urgency_level": p.urgency_level,
                    "description": p.description,
                    "suggestion": p.suggestion
                }
                for p in self.tension_points
            ]
        }


class PacingAnalyzer:
    """LLM节奏分析器增强版"""

    # 可预测模式（辅助检测）
    PREDICTABLE_PATTERNS = [
        "果不其然", "果然", "正如所料", "不出所料",
        "不出意外", "毫无疑问", "毫无疑问",
        "战斗开始", "对决开始", "争端开始",
        "主角必胜", "反派必败"
    ]

    # 低紧迫感模式（辅助检测）
    LOW_URGENCY_PATTERNS = [
        "不慌不忙", "从容不迫", "不紧不慢",
        "悠闲", "淡然", "平静",
        "缓缓", "慢慢", "逐渐"
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

    def analyze_pacing(
        self,
        chapter_num: int,
        content: str,
        context_chapters: Optional[Dict[int, str]] = None
    ) -> PacingReport:
        """
        分析章节节奏

        Args:
            chapter_num: 章节号
            content: 章节内容
            context_chapters: 上下文章节

        Returns:
            PacingReport
        """
        report = PacingReport(chapter=chapter_num)

        # 构建上下文
        context = ""
        if context_chapters:
            for ch_num in sorted(context_chapters.keys()):
                if ch_num != chapter_num:
                    ctx_content = context_chapters[ch_num][:400]
                    context += f"\n=== 第{ch_num}章 ===\n{ctx_content}"

        prompt = f"""你是小说节奏分析专家，负责评估章节的张力曲线和节奏安排。

当前章节（第{chapter_num}章）:
{content[:3000]}

上文章节（用于判断节奏连贯性）:
{context[:2000] if context else "无"}


## 任务1：识别张力点

分析章节中的关键张力点，包括：
- **冲突点**：矛盾发生或升级的地方
- **揭示点**：重要信息或秘密被揭露
- **高潮点**：情绪或剧情的最高峰
- **解决点**：冲突暂时或彻底解决

对每个张力点评估：
- **位置**：开头/中段/结尾
- **紧迫度**：1-5分，5分为最高
- **可预测性**：是否能让读者提前猜到结局

## 任务2：检测"伪高潮"

伪高潮指看起来紧张但实际没有悬念的高潮。

检测模式：
- 战斗开始就注定主角会赢（无敌设定）
- 冲突解决方案太容易（主角有金手指）
- 反派太弱智（没有真正的威胁）
- 结果早已注定（命运/预言成真）

## 任务3：评估冲突紧迫感

真正的紧迫感来自：
- 真实的威胁（后果严重）
- 时间限制（来不及）
- 资源有限（打不过）
- 道德困境（两难选择）

检测：
- 紧迫感是否来自内在逻辑而非外部强加？
- 读者是否真的担心结果？
- 是否有"假紧迫"（看起来紧张但实际无所谓）？

## 任务4：检测无效缓冲

缓冲段落用于调节节奏，但无效缓冲会让人昏昏欲睡。

检测：
- 过多的内心独白（超过3段）
- 重复的描述性文字
- 与剧情无关的环境描写
- "然后"、"接着"堆砌

## 任务5：分析张力曲线

评估章节内的张力起伏：
- 是否张弛有度？
- 是否有拖沓的低张力段落？
- 高潮是否太早或太晚？
- 结尾钩子是否足够吸引人？

## 输出格式

返回JSON：
```json
{{
  "tension_points": [
    {{
      "position": "开头/中段/结尾",
      "tension_type": "conflict/revelation/climax/resolution",
      "is_predictable": true/false,
      "urgency_level": 1-5,
      "description": "张力点描述",
      "suggestion": "改进建议"
    }}
  ],
  "summary": {{
    "predictable_count": N,
    "low_urgency_count": N,
    "invalid_buffer_count": N,
    "tension_curve": [urgency_level序列],
    "avg_tension": 0.0-5.0,
    "score": 0.0-1.0
  }}
}}
```

如果没有明显张力点：
```json
{{"tension_points": [], "summary": {{"predictable_count": 0, "score": 0.5}}}}```"""

        response = self.llm.generate(
            prompt=prompt,
            system="你是一个专业的小说节奏分析专家，擅长提升张力曲线和制造悬念。",
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
                    data = {"tension_points": [], "summary": {}}

            points = data.get("tension_points", [])
            summary = data.get("summary", {})

            # 构建张力点记录
            for pt in points:
                tension = TensionPoint(
                    chapter=chapter_num,
                    position=pt.get("position", "中段"),
                    tension_type=pt.get("tension_type", "conflict"),
                    is_predictable=pt.get("is_predictable", False),
                    urgency_level=pt.get("urgency_level", 3),
                    description=pt.get("description", ""),
                    suggestion=pt.get("suggestion", "")
                )
                report.tension_points.append(tension)

            # 更新统计
            report.predictable_count = summary.get("predictable_count", report.predictable_count)
            report.low_urgency_count = summary.get("low_urgency_count", report.low_urgency_count)
            report.invalid_buffer_count = summary.get("invalid_buffer_count", report.invalid_buffer_count)

            # 计算分数
            if report.tension_points:
                # 不可预测性权重：可预测会降低分数
                predictability_penalty = min(0.3, report.predictable_count * 0.1)
                # 低紧迫感惩罚
                urgency_penalty = min(0.3, report.low_urgency_count * 0.1)
                # 平均紧迫度加分（归一化到0-1）
                urgency_bonus = (report.avg_tension / 5.0) * 0.4

                report.score = max(0, min(1, 0.5 + urgency_bonus - predictability_penalty - urgency_penalty))
            else:
                report.score = 0.5

            report.tension_curve = summary.get("tension_curve", report.tension_curve)
            report.avg_tension = summary.get("avg_tension", report.avg_tension)

        except Exception:
            report.score = 0.5

        return report

    def analyze_chapters_batch(
        self,
        chapter_nums: List[int],
        parallel: bool = True,
        max_workers: int = 5
    ) -> Dict[int, PacingReport]:
        """批量分析章节节奏"""
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
                            self.analyze_pacing,
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
                        reports[ch] = self.analyze_pacing(ch, contents[ch], context)
                    except Exception as e:
                        print(f"  ch{ch:03d}: 分析失败 - {e}")

        return reports

    def generate_summary_report(
        self,
        reports: Dict[int, PacingReport]
    ) -> dict:
        """生成汇总报告"""
        total_predictable = sum(r.predictable_count for r in reports.values())
        total_low_urgency = sum(r.low_urgency_count for r in reports.values())
        total_invalid_buffer = sum(r.invalid_buffer_count for r in reports.values())
        avg_tension = sum(r.avg_tension for r in reports.values()) / len(reports) if reports else 0
        avg_score = sum(r.score for r in reports.values()) / len(reports) if reports else 0

        return {
            "timestamp": datetime.now().isoformat(),
            "total_chapters": len(reports),
            "total_predictable": total_predictable,
            "total_low_urgency": total_low_urgency,
            "total_invalid_buffer": total_invalid_buffer,
            "avg_tension_level": avg_tension,
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
        print(f"节奏分析报告已保存: {output_file}")


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
    parser = argparse.ArgumentParser(description='LLM节奏分析器增强版 - S5节奏控制')
    parser.add_argument('--chapters', type=str, default='1-360', help='章节范围')
    parser.add_argument('--parallel', action='store_true', default=True, help='并行处理')
    parser.add_argument('--sequential', dest='parallel', action='store_false', help='顺序处理')
    parser.add_argument('--output', type=str, help='报告输出路径')
    parser.add_argument('--workers', type=int, default=5, help='并行工作线程数')

    args = parser.parse_args()
    chapters = parse_chapter_range(args.chapters)

    print("=" * 60)
    print("LLM节奏分析器增强版 v9.10 - S5节奏控制")
    print(f"章节范围: {chapters[0]}-{chapters[-1]} ({len(chapters)}章)")
    print("=" * 60)

    analyzer = PacingAnalyzer()
    reports = analyzer.analyze_chapters_batch(
        chapters,
        parallel=args.parallel,
        max_workers=args.workers
    )

    # 生成汇总报告
    summary = analyzer.generate_summary_report(reports)

    # 保存结果
    output_file = Path(args.output) if args.output else analyzer.report_dir / "pacing_report.json"
    analyzer.save_report(summary, output_file)

    # 输出统计
    print("\n" + "=" * 60)
    print("分析完成")
    print(f"分析章节: {len(reports)}")
    print(f"可预测高潮: {summary['total_predictable']}")
    print(f"低紧迫感: {summary['total_low_urgency']}")
    print(f"无效缓冲: {summary['total_invalid_buffer']}")
    print(f"平均紧迫度: {summary['avg_tension_level']:.2f}/5.0")
    print(f"平均质量分: {summary['avg_score']:.2f}")
    print(f"质量评级: {summary['quality_grade']}")
    print("=" * 60)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
LLM伏笔分析器 - S11伏笔回收率增强

功能：
1. 识别隐含伏笔（非关键词触发）
2. 验证回收逻辑合理性
3. 评估伏笔与主线关联度
4. 生成伏笔追踪表增强版

目标：伏笔回收率从55.4%提升到85%+
"""

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.llm_service import LLMService


@dataclass
class ForeshadowRecord:
    """伏笔记录"""
    chapter: int                    # 章节号
    text: str                       # 伏笔原文
    category: str                   # 类别：explicit（明显）/ implicit（隐含）
    confidence: float               # 置信度 0-1
    is_released: bool               # 是否已回收
    release_chapter: Optional[int]  # 回收章节
    release_quality: str            # 回收质量：natural（自然）/ abrupt（突兀）/ weak（弱）
    connection_to_main: str          # 与主线关联度：strong/medium/weak/none
    suggestion: str = ""             # 改进建议


@dataclass
class ForeshadowAnalysisReport:
    """伏笔分析报告"""
    chapter: int
    total_foreshadows: int = 0
    explicit_foreshadows: int = 0
    implicit_foreshadows: int = 0
    released_count: int = 0
    unreleased_count: int = 0
    records: List[ForeshadowRecord] = field(default_factory=list)
    recovery_rate: float = 0.0
    score: float = 0.0
    llm_calls: int = 0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if self.total_foreshadows > 0:
            self.recovery_rate = self.released_count / self.total_foreshadows

    def to_dict(self) -> dict:
        return {
            "chapter": self.chapter,
            "total_foreshadows": self.total_foreshadows,
            "explicit_foreshadows": self.explicit_foreshadows,
            "implicit_foreshadows": self.implicit_foreshadows,
            "released_count": self.released_count,
            "unreleased_count": self.unreleased_count,
            "recovery_rate": self.recovery_rate,
            "score": self.score,
            "llm_calls": self.llm_calls,
            "timestamp": self.timestamp,
            "records": [
                {
                    "chapter": r.chapter,
                    "text": r.text[:100],
                    "category": r.category,
                    "confidence": r.confidence,
                    "is_released": r.is_released,
                    "release_chapter": r.release_chapter,
                    "release_quality": r.release_quality,
                    "connection_to_main": r.connection_to_main,
                    "suggestion": r.suggestion
                }
                for r in self.records
            ]
        }


class ForeshadowAnalyzer:
    """LLM伏笔分析器"""

    # 隐含伏笔关键词（不如明显，但可作为辅助判断）
    IMPLICIT_KEYWORDS = [
        "奇怪", "异常", "似乎", "好像", "难道", "为何", "什么原样",
        "不对劲", "隐隐", "模糊", "若有若无", "似曾相识", "说不清",
        "总觉得", "事后", "后来", "果然", "不出所料", "正如所料"
    ]

    # 明显伏笔关键词
    EXPLICIT_KEYWORDS = [
        "伏笔", "悬念", "预示", "预兆", "暗示", "预言", "命运",
        "将来", "终有一天", "迟早", "必将", "注定", "因果"
    ]

    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm = llm_service or LLMService()
        self.project_root = PROJECT_ROOT
        self.chapters_dir = self.project_root / "03_内容仓库" / "04_正文"
        self.foreshadow_table_file = self.project_root / "06_意见仓库" / "07_一致性检查" / "foreshadow_table.json"

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

    def _classify_foreshadow_type(self, text: str) -> Tuple[str, float]:
        """分类伏笔类型并返回置信度"""
        # 检查是否明显伏笔
        explicit_count = sum(1 for kw in self.EXPLICIT_KEYWORDS if kw in text)
        # 检查是否隐含伏笔
        implicit_count = sum(1 for kw in self.IMPLICIT_KEYWORDS if kw in text)

        if explicit_count > 0:
            confidence = min(0.9, 0.5 + explicit_count * 0.2)
            return "explicit", confidence
        elif implicit_count > 0:
            confidence = min(0.7, 0.3 + implicit_count * 0.1)
            return "implicit", confidence
        else:
            # 无法从关键词判断，返回未知
            return "unknown", 0.0

    def analyze_chapter_foreshadows(
        self,
        chapter_num: int,
        content: str,
        context_chapters: Optional[Dict[int, str]] = None
    ) -> ForeshadowAnalysisReport:
        """
        分析单章节的伏笔铺设与回收

        Args:
            chapter_num: 章节号
            content: 章节内容
            context_chapters: 上下文章节内容（用于判断伏笔是否回收）

        Returns:
            ForeshadowAnalysisReport
        """
        report = ForeshadowAnalysisReport(chapter=chapter_num)

        # 构建上下文
        context = ""
        if context_chapters:
            for ch_num in sorted(context_chapters.keys()):
                if ch_num != chapter_num:
                    ctx_content = context_chapters[ch_num][:500]
                    context += f"\n=== 第{ch_num}章 ===\n{ctx_content}"

        prompt = f"""你是小说伏笔分析专家，负责识别和分析伏笔的铺设与回收。

当前章节（第{chapter_num}章）:
{content[:3000]}

上下文章节（用于判断伏笔是否已回收）:
{context[:2000] if context else "无"}


## 任务1：识别伏笔

请识别当前章节中的所有伏笔，包括：

1. **明显伏笔**（有明确标记）：
   - 使用"预示"、"暗示"、"伏笔"等关键词
   - 出现异常细节后强调"之后会用到"
   - 角色做出奇怪承诺或预言

2. **隐含伏笔**（无明确标记，但有暗示）：
   - 角色对某事表现出异常反应
   - 某个细节被刻意描写但未解释
   - 角色提到某个信息但之后未再提及
   - 时间线/地点出现不寻常的描述

3. **结构伏笔**：
   - 章节结尾留下悬念
   - 冲突被搁置未解决
   - 新角色/物品被引入但未展开

## 任务2：验证伏笔回收

对于每个识别的伏笔，检查：
- 是否在后续章节中得到呼应/回收？
- 回收方式是否自然合理？
- 伏笔与主线关联度如何？

## 输出格式

返回JSON格式，包含foreshadows数组：
```json
{{
  "foreshadows": [
    {{
      "chapter": {chapter_num},
      "text": "伏笔原文（50字以内）",
      "category": "explicit/implicit/structural",
      "confidence": 0.0-1.0,
      "is_released": true/false,
      "release_chapter": 回收章节号（如果有）,
      "release_quality": "natural/abrupt/weak/none",
      "connection_to_main": "strong/medium/weak/none",
      "suggestion": "改进建议（如果有）"
    }}
  ],
  "summary": {{
    "total_foreshadows": N,
    "explicit_count": N,
    "implicit_count": N,
    "released_count": N,
    "recovery_rate": 0.0-1.0
  }}
}}
```

如果没有发现伏笔，返回：
```json
{{"foreshadows": [], "summary": {{"total_foreshadows": 0}}}}
```"""

        response = self.llm.generate(
            prompt=prompt,
            system="你是一个专业的小说伏笔分析专家，擅长识别隐含伏笔和评估伏笔回收质量。",
            model="default"
        )
        report.llm_calls = 1

        try:
            # 解析JSON响应
            try:
                data = json.loads(response)
            except json.JSONDecodeError:
                json_match = re.search(r'\{.*\}|\[.*\]', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    data = {"foreshadows": [], "summary": {"total_foreshadows": 0}}

            foreshadows = data.get("foreshadows", []) if isinstance(data, dict) else []
            summary = data.get("summary", {}) if isinstance(data, dict) else {}

            # 构建伏笔记录
            for fs in foreshadows:
                record = ForeshadowRecord(
                    chapter=fs.get("chapter", chapter_num),
                    text=fs.get("text", ""),
                    category=fs.get("category", "unknown"),
                    confidence=fs.get("confidence", 0.5),
                    is_released=fs.get("is_released", False),
                    release_chapter=fs.get("release_chapter"),
                    release_quality=fs.get("release_quality", "none"),
                    connection_to_main=fs.get("connection_to_main", "none"),
                    suggestion=fs.get("suggestion", "")
                )
                report.records.append(record)

            # 更新统计
            report.total_foreshadows = summary.get("total_foreshadows", len(report.records))
            report.explicit_foreshadows = summary.get("explicit_count", sum(1 for r in report.records if r.category == "explicit"))
            report.implicit_foreshadows = summary.get("implicit_count", sum(1 for r in report.records if r.category in ["implicit", "structural"]))
            report.released_count = summary.get("released_count", sum(1 for r in report.records if r.is_released))
            report.unreleased_count = report.total_foreshadows - report.released_count

            # 计算回收率和分数
            if report.total_foreshadows > 0:
                report.recovery_rate = report.released_count / report.total_foreshadows
                # 分数 = 回收率 * 0.7 + 平均置信度 * 0.3
                avg_confidence = sum(r.confidence for r in report.records) / len(report.records) if report.records else 0
                report.score = report.recovery_rate * 0.7 + avg_confidence * 0.3
            else:
                report.score = 1.0  # 无伏笔视为满分

        except Exception:
            report.score = 0.5

        return report

    def analyze_chapters_batch(
        self,
        chapter_nums: List[int],
        parallel: bool = True,
        max_workers: int = 5
    ) -> Dict[int, ForeshadowAnalysisReport]:
        """批量分析章节伏笔"""
        reports = {}
        contents = self.load_chapters(chapter_nums)

        if parallel:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {}
                for ch in chapter_nums:
                    if ch in contents:
                        # 传递上下文（前后各10章）
                        context = {
                            c: contents[c]
                            for c in contents
                            if abs(c - ch) <= 10 and c != ch
                        }
                        future = executor.submit(
                            self.analyze_chapter_foreshadows,
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
                        reports[ch] = self.analyze_chapter_foreshadows(ch, contents[ch], context)
                    except Exception as e:
                        print(f"  ch{ch:03d}: 分析失败 - {e}")

        return reports

    def generate_foreshadow_table(
        self,
        reports: Dict[int, ForeshadowAnalysisReport]
    ) -> List[dict]:
        """生成伏笔追踪表"""
        table = []

        for ch in sorted(reports.keys()):
            report = reports[ch]
            for record in report.records:
                table.append({
                    "chapter": record.chapter,
                    "text": record.text,
                    "category": record.category,
                    "confidence": record.confidence,
                    "is_released": record.is_released,
                    "release_chapter": record.release_chapter,
                    "release_quality": record.release_quality,
                    "connection_to_main": record.connection_to_main,
                    "suggestion": record.suggestion
                })

        # 按章节排序
        table.sort(key=lambda x: (x["chapter"], -x["confidence"]))
        return table

    def save_foreshadow_table(self, table: List[dict], output_file: Path):
        """保存伏笔追踪表"""
        output_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "timestamp": datetime.now().isoformat(),
            "total_foreshadows": len(table),
            "released_count": sum(1 for t in table if t["is_released"]),
            "recovery_rate": sum(1 for t in table if t["is_released"]) / len(table) if table else 0,
            "table": table
        }

        output_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"伏笔追踪表已保存: {output_file}")
        print(f"  总伏笔数: {len(table)}")
        print(f"  已回收: {data['released_count']}")
        print(f"  回收率: {data['recovery_rate']:.1%}")


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
    parser = argparse.ArgumentParser(description='LLM伏笔分析器 - S11伏笔回收率增强')
    parser.add_argument('--chapters', type=str, default='1-360', help='章节范围')
    parser.add_argument('--parallel', action='store_true', default=True, help='并行处理')
    parser.add_argument('--sequential', dest='parallel', action='store_false', help='顺序处理')
    parser.add_argument('--output', type=str, help='伏笔追踪表输出路径')
    parser.add_argument('--workers', type=int, default=5, help='并行工作线程数')

    args = parser.parse_args()
    chapters = parse_chapter_range(args.chapters)

    print("=" * 60)
    print("LLM伏笔分析器 v9.10 - S11伏笔回收率增强")
    print(f"章节范围: {chapters[0]}-{chapters[-1]} ({len(chapters)}章)")
    print("=" * 60)

    analyzer = ForeshadowAnalyzer()
    reports = analyzer.analyze_chapters_batch(
        chapters,
        parallel=args.parallel,
        max_workers=args.workers
    )

    # 生成伏笔追踪表
    table = analyzer.generate_foreshadow_table(reports)

    # 保存结果
    output_file = Path(args.output) if args.output else analyzer.foreshadow_table_file
    analyzer.save_foreshadow_table(table, output_file)

    # 汇总统计
    print("\n" + "=" * 60)
    print("分析完成")
    total_foreshadows = sum(r.total_foreshadows for r in reports.values())
    total_released = sum(r.released_count for r in reports.values())
    overall_rate = total_released / total_foreshadows if total_foreshadows > 0 else 0
    avg_score = sum(r.score for r in reports.values()) / len(reports) if reports else 0
    print(f"分析章节: {len(reports)}")
    print(f"发现伏笔: {total_foreshadows}")
    print(f"已回收: {total_released}")
    print(f"整体回收率: {overall_rate:.1%}")
    print(f"平均质量分: {avg_score:.2f}")
    print("=" * 60)

    # 质量评级
    if overall_rate >= 0.85:
        grade = "A（优秀）"
    elif overall_rate >= 0.70:
        grade = "B（良好）"
    elif overall_rate >= 0.50:
        grade = "C（一般）"
    else:
        grade = "D（需改进）"
    print(f"质量评级: {grade}")


if __name__ == '__main__':
    main()

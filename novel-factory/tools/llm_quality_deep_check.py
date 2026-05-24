#!/usr/bin/env python3
"""
LLM深度质检工具 - PHASE_5_LLM_QUALITY
基于大量LLM API调用的全面质量检测与修复

使用方法:
    python tools/llm_quality_deep_check.py --check character --chapters 1-30
    python tools/llm_quality_deep_check.py --check logic --chapters 1-360 --batch 30
    python tools/llm_quality_deep_check.py --check all --repair
    python tools/llm_quality_deep_check.py --diagnose rhythm --chapters 1-60
"""

import sys
import re
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.llm_service import LLMService
from infra.quality import Issue, RepairResult


@dataclass
class QualityReport:
    """质检报告"""
    chapter: int
    checker: str
    issues: List[Issue] = field(default_factory=list)
    score: float = 0.0
    llm_calls: int = 0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "chapter": self.chapter,
            "checker": self.checker,
            "issues": [asdict(i) for i in self.issues],
            "score": self.score,
            "llm_calls": self.llm_calls,
            "timestamp": self.timestamp
        }


class LLMQualityChecker:
    """基于LLM的深度质量检测器"""

    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm = llm_service or LLMService()
        self.project_root = PROJECT_ROOT
        self.chapters_dir = self.project_root / "03_内容仓库" / "04_正文"

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

    def check_character_consistency(self, chapter_num: int, content: str) -> QualityReport:
        """
        STEP_18a: 角色一致性深度检测
        使用LLM分析角色行为、对话、决策的一致性
        """
        report = QualityReport(chapter=chapter_num, checker="CharacterConsistencyLLMChecker")

        # 角色列表（从项目配置读取）
        main_characters = ["林夜", "苏琳", "星月", "小九", "铁蛋", "莫言", "暗皇", "虚无之主", "剑尘子"]

        prompt = f"""你是小说质量审核官，负责检测角色一致性。

章节内容:
{content[:3000]}

请分析以下角色的行为和对话一致性：
{', '.join(main_characters)}

检测维度：
1. 角色言行一致性（性格设定vs实际表现）
2. 角色决策逻辑性（动机是否合理）
3. 角色关系一致性（与他人的关系是否连贯）
4. 角色成长轨迹一致性（变化是否有铺垫）

如果发现一致性问题的章节，返回JSON格式：
{{"issues": [{{"chapter": {chapter_num}, "type": "character_inconsistency", "severity": "P1", "description": "...", "location": "具体位置", "suggestion": "修复建议"}}]}}

如果没有发现问题，返回：
{{"issues": []}}
"""

        response = self.llm.generate(
            prompt=prompt,
            system="你是一个专业的小说质量审核专家，擅长角色一致性分析。",
            model="default"
        )
        report.llm_calls = 1

        try:
            data = json.loads(response)
            issues = data.get("issues", [])
            report.issues = [Issue(**i) for i in issues]
        except json.JSONDecodeError:
            # 解析失败，尝试简单提取
            if "issues" in response.lower():
                report.issues = [Issue(
                    chapter=chapter_num,
                    type="character_inconsistency",
                    severity="P2",
                    description="LLM解析失败，请人工审核",
                    location="全文"
                )]
            report.score = 0.5

        report.score = max(0, 1 - len(report.issues) * 0.1)
        return report

    def scan_logic_contradictions(self, chapter_num: int, content: str, context_chapters: List[int] = None) -> QualityReport:
        """
        STEP_18b: 逻辑矛盾全面扫描
        检测时间线、因果链、设定冲突
        """
        report = QualityReport(chapter=chapter_num, checker="LogicContradictionLLMChecker")

        # 加载上下文章节（前后各5章）
        context = ""
        if context_chapters:
            for ctx_ch in context_chapters[:10]:  # 最多10章上下文
                ctx_content = self.load_chapter(ctx_ch)
                if ctx_content:
                    context += f"\n\n=== 第{ctx_ch}章 ===\n{ctx_content[:500]}"

        prompt = f"""你是小说逻辑审核专家，负责检测逻辑矛盾。

当前章节（第{chapter_num}章）:
{content[:2500]}

上下文章节（用于时间线比对）:
{context[:1000] if context else "无"}

检测维度：
1. 时间线矛盾（日期、时间流逝是否一致）
2. 因果逻辑矛盾（原因导致结果是否合理）
3. 设定冲突（力量体系、技能描述是否前后矛盾）
4. 人物状态矛盾（伤势、能力是否前后一致）
5. 场景逻辑矛盾（地点切换、物品位置是否合理）

返回JSON格式：
{{"issues": [{{"chapter": {chapter_num}, "type": "logic_contradiction", "severity": "P0/P1", "description": "...", "location": "具体位置", "evidence": "矛盾证据"}}]}}

如果没有发现问题：
{{"issues": []}}
"""

        response = self.llm.generate(
            prompt=prompt,
            system="你是一个专业的小说逻辑审核专家，擅长发现时间线和因果矛盾。",
            model="default"
        )
        report.llm_calls = 1

        try:
            data = json.loads(response)
            issues = data.get("issues", [])
            report.issues = [Issue(**i) for i in issues]
        except json.JSONDecodeError:
            report.issues = []
            report.score = 0.5

        report.score = max(0, 1 - len(report.issues) * 0.15)
        return report

    def verify_foreshadow_completeness(self, chapter_num: int, content: str, outline_content: str = None) -> QualityReport:
        """
        STEP_18c: 伏笔回收完整性验证
        对照章节大纲检查伏笔铺设与回收
        """
        report = QualityReport(chapter=chapter_num, checker="ForeshadowRecoveryChecker")

        # 加载章节大纲
        outline_file = self.chapters_dir / f"ch{chapter_num:03d}_大纲.md"
        if not outline_content:
            if outline_file.exists():
                outline_content = outline_file.read_text(encoding='utf-8')
            else:
                outline_content = "无章节大纲"

        prompt = f"""你是伏笔审核专家，负责检测伏笔铺设与回收的完整性。

章节内容（第{chapter_num}章）:
{content[:3000]}

章节大纲:
{outline_content[:1000] if outline_content else "无大纲"}

检测维度：
1. 伏笔铺设完整性（大纲中的伏笔是否在正文有铺垫）
2. 伏笔回收检查（是否有明确回收的伏笔）
3. 伏笔质量（伏笔是否自然、不突兀）
4. 遗漏伏笔（章节中是否有关键信息被遗漏）

返回JSON格式：
{{"issues": [{{"chapter": {chapter_num}, "type": "foreshadow_issue", "severity": "P1/P2", "description": "...", "foreshadow_text": "伏笔原文", "status": "missing/released/weak"}}]}}

如果没有问题：
{{"issues": []}}
"""

        response = self.llm.generate(
            prompt=prompt,
            system="你是一个专业的小说伏笔审核专家，擅长分析伏笔的铺设与回收。",
            model="default"
        )
        report.llm_calls = 1

        try:
            data = json.loads(response)
            issues = data.get("issues", [])
            report.issues = [Issue(**i) for i in issues]
        except json.JSONDecodeError:
            report.issues = []
            report.score = 0.5

        report.score = max(0, 1 - len(report.issues) * 0.1)
        return report

    def diagnose_emotional_rhythm(self, chapter_num: int, content: str) -> QualityReport:
        """
        STEP_18d: 情感节奏诊断
        分析高潮分布、情感曲线、爽点密度
        """
        report = QualityReport(chapter=chapter_num, checker="EmotionalRhythmChecker")

        prompt = f"""你是情感节奏专家，负责诊断小说的情感节奏。

章节内容（第{chapter_num}章）:
{content[:3000]}

检测维度：
1. 高潮分布（是否有清晰的高潮场景）
2. 情感曲线（是否有过渡、起伏）
3. 爽点密度（打脸、装逼、逆转等爽点是否合理）
4. 节奏问题（是否太水或太赶）
5. 情感共鸣点（是否能引发读者情感）

返回JSON格式：
{{"issues": [{{"chapter": {chapter_num}, "type": "emotional_rhythm_issue", "severity": "P2", "description": "...", "location": "具体位置", "suggestion": "调整建议"}}], "score": 0.0-1.0}}

score说明：0.8+优秀，0.6-0.8良好，0.4-0.6一般，<0.4需改进
"""

        response = self.llm.generate(
            prompt=prompt,
            system="你是一个专业的小说情感节奏分析专家，擅长诊断爽点和情感共鸣。",
            model="default"
        )
        report.llm_calls = 1

        try:
            data = json.loads(response)
            issues = data.get("issues", [])
            report.issues = [Issue(**i) for i in issues]
            report.score = data.get("score", 0.5)
        except json.JSONDecodeError:
            report.issues = []
            report.score = 0.5

        return report


class LLMRepairer:
    """基于LLM的质量问题修复器"""

    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm = llm_service or LLMService()
        self.project_root = PROJECT_ROOT
        self.chapters_dir = self.project_root / "03_内容仓库" / "04_正文"

    def repair_character_issue(self, issue: Issue, chapter_content: str) -> str:
        """修复角色一致性问题"""
        prompt = f"""你是小说内容修复专家，负责修复角色一致性问题。

原文内容:
{chapter_content[:4000]}

问题描述:
- 章节: {issue.chapter}
- 类型: {issue.type}
- 问题: {issue.description}
- 位置: {issue.location}
- 修复建议: {issue.suggestion if hasattr(issue, 'suggestion') else '请根据角色设定进行修复'}

请直接输出修复后的完整章节内容（保持原文风格，只修改问题部分）。"""

        response = self.llm.generate(
            prompt=prompt,
            system="你是一个专业的小说内容修复专家，能够保持原文风格进行修改。",
            model="default"
        )
        return response

    def repair_logic_issue(self, issue: Issue, chapter_content: str) -> str:
        """修复逻辑矛盾问题"""
        prompt = f"""你是小说逻辑修复专家，负责修复逻辑矛盾。

原文内容:
{chapter_content[:4000]}

问题描述:
- 章节: {issue.chapter}
- 类型: {issue.type}
- 问题: {issue.description}
- 位置: {issue.location}
- 矛盾证据: {issue.evidence if hasattr(issue, 'evidence') else '请自行分析'}

请直接输出修复后的完整章节内容（保持原文风格，只修改逻辑矛盾部分）。"""

        response = self.llm.generate(
            prompt=prompt,
            system="你是一个专业的小说逻辑修复专家，能够发现并修复时间线和因果矛盾。",
            model="default"
        )
        return response

    def repair_foreshadow_issue(self, issue: Issue, chapter_content: str) -> str:
        """修复伏笔问题"""
        prompt = f"""你是小说伏笔修复专家，负责修复伏笔问题。

原文内容:
{chapter_content[:4000]}

问题描述:
- 章节: {issue.chapter}
- 类型: {issue.type}
- 问题: {issue.description}
- 伏笔原文: {issue.foreshadow_text if hasattr(issue, 'foreshadow_text') else '未知'}
- 状态: {issue.status if hasattr(issue, 'status') else 'unknown'}

请直接输出修复后的完整章节内容（增强伏笔铺设或完善伏笔回收）。"""

        response = self.llm.generate(
            prompt=prompt,
            system="你是一个专业的小说伏笔修复专家，能够完善伏笔的铺设与回收。",
            model="default"
        )
        return response


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


def run_phase_18a(checker: LLMQualityChecker, chapters: List[int], parallel: bool = True) -> Dict[int, QualityReport]:
    """STEP_18a: 角色一致性深度检测"""
    print(f"[STEP_18a] 角色一致性深度检测 - {len(chapters)}章")
    reports = {}

    if parallel:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            for ch in chapters:
                content = checker.load_chapter(ch)
                if content:
                    future = executor.submit(checker.check_character_consistency, ch, content)
                    futures[future] = ch

            for future in as_completed(futures):
                ch = futures[future]
                try:
                    report = future.result()
                    reports[ch] = report
                    severity_counts = {}
                    for issue in report.issues:
                        severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
                    print(f"  ch{ch:03d}: {len(report.issues)}个问题 {severity_counts} score={report.score:.2f}")
                except Exception as e:
                    print(f"  ch{ch:03d}: 错误 - {e}")
    else:
        for ch in chapters:
            content = checker.load_chapter(ch)
            if content:
                report = checker.check_character_consistency(ch, content)
                reports[ch] = report
                print(f"  ch{ch:03d}: {len(report.issues)}个问题 score={report.score:.2f}")

    return reports


def run_phase_18b(checker: LLMQualityChecker, chapters: List[int], parallel: bool = True) -> Dict[int, QualityReport]:
    """STEP_18b: 逻辑矛盾全面扫描"""
    print(f"[STEP_18b] 逻辑矛盾全面扫描 - {len(chapters)}章")
    reports = {}

    for ch in chapters:
        content = checker.load_chapter(ch)
        if content:
            # 加载前后各5章作为上下文
            context_chs = [c for c in range(ch - 5, ch + 6) if c != ch and 1 <= c <= 360]
            report = checker.scan_logic_contradictions(ch, content, context_chs)
            reports[ch] = report
            print(f"  ch{ch:03d}: {len(report.issues)}个问题 score={report.score:.2f}")

    return reports


def run_phase_18c(checker: LLMQualityChecker, chapters: List[int], parallel: bool = True) -> Dict[int, QualityReport]:
    """STEP_18c: 伏笔回收完整性验证"""
    print(f"[STEP_18c] 伏笔回收完整性验证 - {len(chapters)}章")
    reports = {}

    for ch in chapters:
        content = checker.load_chapter(ch)
        if content:
            report = checker.verify_foreshadow_completeness(ch, content)
            reports[ch] = report
            print(f"  ch{ch:03d}: {len(report.issues)}个问题 score={report.score:.2f}")

    return reports


def run_phase_18d(checker: LLMQualityChecker, chapters: List[int], parallel: bool = True) -> Dict[int, QualityReport]:
    """STEP_18d: 情感节奏诊断"""
    print(f"[STEP_18d] 情感节奏诊断 - {len(chapters)}章")
    reports = {}

    for ch in chapters:
        content = checker.load_chapter(ch)
        if content:
            report = checker.diagnose_emotional_rhythm(ch, content)
            reports[ch] = report
            print(f"  ch{ch:03d}: score={report.score:.2f} ({len(report.issues)}个建议)")

    return reports


def run_phase_18e(repairer: LLMRepairer, issues: List[Issue], chapters_dir: Path, dry_run: bool = False) -> Dict[int, str]:
    """STEP_18e: 质量问题修复"""
    print(f"[STEP_18e] 质量问题修复 - {len(issues)}个问题")

    results = {}
    p0_issues = [i for i in issues if i.severity == "P0"]
    p1_issues = [i for i in issues if i.severity == "P1"]

    print(f"  P0问题: {len(p0_issues)}个 (必须修复)")
    print(f"  P1问题: {len(p1_issues)}个 (应该修复)")

    repaired_count = 0
    for issue in p0_issues + p1_issues:
        ch_file = chapters_dir / f"ch{issue.chapter:03d}.md"
        if not ch_file.exists():
            continue

        chapter_content = ch_file.read_text(encoding='utf-8')

        try:
            if issue.type == "character_inconsistency":
                fixed_content = repairer.repair_character_issue(issue, chapter_content)
            elif issue.type == "logic_contradiction":
                fixed_content = repairer.repair_logic_issue(issue, chapter_content)
            elif issue.type in ["foreshadow_issue", "foreshadow_incomplete"]:
                fixed_content = repairer.repair_foreshadow_issue(issue, chapter_content)
            else:
                continue

            if not dry_run and len(fixed_content) > len(chapter_content) * 0.8:
                ch_file.write_text(fixed_content, encoding='utf-8')
                repaired_count += 1
                print(f"  ch{issue.chapter:03d}: ✓ 已修复 ({issue.type})")
            else:
                print(f"  ch{issue.chapter:03d}: 跳过 (内容异常)")

            results[issue.chapter] = fixed_content

        except Exception as e:
            print(f"  ch{issue.chapter:03d}: ✗ 修复失败 - {e}")

    print(f"  修复完成: {repaired_count}/{len(p0_issues) + len(p1_issues)}")
    return results


def save_report(reports: Dict[int, QualityReport], output_file: Path):
    """保存质检报告"""
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "total_chapters": len(reports),
        "reports": [r.to_dict() for r in reports.values()]
    }

    # 汇总统计
    all_issues = []
    for r in reports.values():
        all_issues.extend(r.issues)

    report_data["summary"] = {
        "total_issues": len(all_issues),
        "by_type": {},
        "by_severity": {},
        "average_score": sum(r.score for r in reports.values()) / len(reports) if reports else 0,
        "total_llm_calls": sum(r.llm_calls for r in reports.values())
    }

    for issue in all_issues:
        report_data["summary"]["by_type"][issue.type] = report_data["summary"]["by_type"].get(issue.type, 0) + 1
        report_data["summary"]["by_severity"][issue.severity] = report_data["summary"]["by_severity"].get(issue.severity, 0) + 1

    output_file.write_text(json.dumps(report_data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"报告已保存: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='LLM深度质检工具 - PHASE_5_LLM_QUALITY')
    parser.add_argument('--check', type=str, choices=['character', 'logic', 'foreshadow', 'rhythm', 'all'],
                        default='all', help='检测类型')
    parser.add_argument('--chapters', type=str, default='1-360', help='章节范围，如 "1-30" 或 "1,5,10"')
    parser.add_argument('--batch', type=int, default=30, help='每批处理章节数')
    parser.add_argument('--repair', action='store_true', help='是否修复发现的问题')
    parser.add_argument('--dry-run', action='store_true', help='预览模式（不实际写入）')
    parser.add_argument('--output', type=str, help='报告输出路径')
    parser.add_argument('--parallel', action='store_true', default=True, help='并行处理')
    parser.add_argument('--sequential', dest='parallel', action='store_false', help='顺序处理')

    args = parser.parse_args()
    chapters = parse_chapter_range(args.chapters)

    print("=" * 60)
    print(f"LLM深度质检工具 v9.1 - PHASE_5_LLM_QUALITY")
    print(f"检测类型: {args.check}")
    print(f"章节范围: {chapters[0]}-{chapters[-1]} ({len(chapters)}章)")
    print(f"批处理大小: {args.batch}")
    print(f"修复模式: {'开启' if args.repair else '关闭'}")
    print("=" * 60)

    checker = LLMQualityChecker()
    all_reports = {}

    # STEP_18a: 角色一致性深度检测
    if args.check in ['character', 'all']:
        reports = run_phase_18a(checker, chapters, args.parallel)
        all_reports.update(reports)

    # STEP_18b: 逻辑矛盾全面扫描
    if args.check in ['logic', 'all']:
        reports = run_phase_18b(checker, chapters, args.parallel)
        all_reports.update(reports)

    # STEP_18c: 伏笔回收完整性验证
    if args.check in ['foreshadow', 'all']:
        reports = run_phase_18c(checker, chapters, args.parallel)
        all_reports.update(reports)

    # STEP_18d: 情感节奏诊断
    if args.check in ['rhythm', 'all']:
        reports = run_phase_18d(checker, chapters, args.parallel)
        all_reports.update(reports)

    # 保存报告
    if all_reports:
        output_file = Path(args.output) if args.output else PROJECT_ROOT / "logs" / "llm_quality_report.json"
        output_file.parent.mkdir(exist_ok=True)
        save_report(all_reports, output_file)

    # STEP_18e: 质量问题修复
    if args.repair:
        all_issues = []
        for r in all_reports.values():
            all_issues.extend(r.issues)

        if all_issues:
            repairer = LLMRepairer()
            run_phase_18e(repairer, all_issues, checker.chapters_dir, args.dry_run)
        else:
            print("[STEP_18e] 无需修复 - 未发现P0/P1问题")

    # 汇总
    print("\n" + "=" * 60)
    print("LLM深度质检完成")
    total_issues = sum(len(r.issues) for r in all_reports.values())
    total_calls = sum(r.llm_calls for r in all_reports.values())
    avg_score = sum(r.score for r in all_reports.values()) / len(all_reports) if all_reports else 0
    print(f"检测章节: {len(all_reports)}")
    print(f"发现问题: {total_issues}")
    print(f"LLM调用: {total_calls}")
    print(f"平均质量分: {avg_score:.2f}")
    print("=" * 60)


if __name__ == '__main__':
    main()
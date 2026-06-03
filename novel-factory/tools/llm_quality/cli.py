"""CLI 入口 - 参数解析 + 报告保存

原 llm_quality_deep_check.py 第 815-825, 1032-1138 行的 parse_chapter_range / save_report / main。
"""
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from . import paths
from .checker import LLMQualityChecker
from .phases import run_phase_18a, run_phase_18b, run_phase_18c, run_phase_18d, run_phase_18e
from .repairer import LLMRepairer
from .report import QualityReport


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
        report_data["summary"]["by_type"][issue.issue_type] = report_data["summary"]["by_type"].get(issue.issue_type, 0) + 1
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
    print("LLM深度质检工具 v9.1 - PHASE_5_LLM_QUALITY")
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
        output_file = Path(args.output) if args.output else paths.PROJECT_ROOT / "logs" / "llm_quality_report.json"
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


if __name__ == "__main__":
    main()

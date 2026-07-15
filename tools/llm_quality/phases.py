"""阶段执行器 - 并行/串行调度 5 个 STEP_18X 阶段

原 llm_quality_deep_check.py 第 828-1029 行 4 个 run_phase_18X + run_phase_18e。
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List

from infra.quality import Issue

from .checker import LLMQualityChecker
from .repairer import LLMRepairer
from .report import QualityReport


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

    if parallel:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            for ch in chapters:
                content = checker.load_chapter(ch)
                if content:
                    context_chs = [c for c in range(ch - 5, ch + 6) if c != ch and 1 <= c <= 360]
                    future = executor.submit(checker.scan_logic_contradictions, ch, content, context_chs)
                    futures[future] = ch

            for future in as_completed(futures):
                ch = futures[future]
                try:
                    reports[ch] = future.result()
                    print(f"  ch{ch:03d}: {len(reports[ch].issues)}个问题 score={reports[ch].score:.2f}")
                except Exception as e:
                    print(f"  ch{ch:03d}: 错误 - {e}")
    else:
        for ch in chapters:
            content = checker.load_chapter(ch)
            if content:
                context_chs = [c for c in range(ch - 5, ch + 6) if c != ch and 1 <= c <= 360]
                report = checker.scan_logic_contradictions(ch, content, context_chs)
                reports[ch] = report
                print(f"  ch{ch:03d}: {len(report.issues)}个问题 score={report.score:.2f}")

    return reports


def run_phase_18c(checker: LLMQualityChecker, chapters: List[int], parallel: bool = True) -> Dict[int, QualityReport]:
    """STEP_18c: 伏笔回收完整性验证"""
    print(f"[STEP_18c] 伏笔回收完整性验证 - {len(chapters)}章")
    reports = {}

    if parallel:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            for ch in chapters:
                content = checker.load_chapter(ch)
                if content:
                    future = executor.submit(checker.verify_foreshadow_completeness, ch, content)
                    futures[future] = ch

            for future in as_completed(futures):
                ch = futures[future]
                try:
                    reports[ch] = future.result()
                    print(f"  ch{ch:03d}: {len(reports[ch].issues)}个问题 score={reports[ch].score:.2f}")
                except Exception as e:
                    print(f"  ch{ch:03d}: 错误 - {e}")
    else:
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

    if parallel:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            for ch in chapters:
                content = checker.load_chapter(ch)
                if content:
                    future = executor.submit(checker.diagnose_emotional_rhythm, ch, content)
                    futures[future] = ch

            for future in as_completed(futures):
                ch = futures[future]
                try:
                    reports[ch] = future.result()
                    print(f"  ch{ch:03d}: score={reports[ch].score:.2f} ({len(reports[ch].issues)}个建议)")
                except Exception as e:
                    print(f"  ch{ch:03d}: 错误 - {e}")
    else:
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
            if issue.issue_type in ["character_inconsistency", "角色行为逻辑", "角色行为逻辑矛盾", "角色引入矛盾",
                                     "角色设定矛盾", "角色动机矛盾", "角色信息脱节", "角色位置矛盾"]:
                fixed_content = repairer.repair_character_issue(issue, chapter_content)
            elif issue.issue_type in ["logic_contradiction", "逻辑矛盾", "逻辑问题", "逻辑漏洞", "逻辑跳跃", "因果逻辑矛盾",
                                       "数字矛盾", "规则逻辑矛盾", "前后逻辑矛盾", "世界观逻辑"]:
                fixed_content = repairer.repair_logic_issue(issue, chapter_content)
            elif issue.issue_type in ["状态矛盾", "前后矛盾", "时间线矛盾", "设定矛盾", "视角混乱",
                                       "场景/状态矛盾", "角色状态矛盾", "章节结构矛盾", "章节衔接矛盾",
                                       "空间逻辑矛盾", "角色身份矛盾", "角色代词/状态矛盾",
                                       "环境/场景矛盾", "世界观/设定矛盾", "性别矛盾", "地理/地点矛盾",
                                       "境界体系矛盾", "内容重复/前后矛盾", "概念/设定矛盾", "视角逻辑矛盾",
                                       "概念/状态矛盾", "信息缺失", "剧情逻辑", "情节逻辑矛盾", "世界观矛盾",
                                       "物理逻辑错误", "感官描述矛盾", "环境描述矛盾", "环境描写矛盾",
                                       "星尘碎片状态矛盾", "章节收尾不完整", "方向矛盾", "环境/物理矛盾",
                                       "世界观设定矛盾", "视角/叙述矛盾", "视角切换矛盾", "叙述顺序矛盾",
                                       "物理概念错误", "世界观设定", "称谓矛盾", "角色能力/状态矛盾",
                                       "状态/情绪转换逻辑", "情节细节模糊", "角色代词矛盾", "角色人称不一致",
                                       "信息传递缺失", "上下文缺失", "记忆细节矛盾", "空间位置模糊",
                                       "时间线逻辑", "场景切换逻辑", "概念模糊", "指代不明"]:
                fixed_content = repairer.repair_logic_issue(issue, chapter_content)
            elif issue.issue_type in ["信息泄露", "信息获取矛盾", "信息重复/冗余", "重复描述", "情节重复",
                                       "角色行为重复", "伏笔回收"]:
                fixed_content = repairer.repair_logic_issue(issue, chapter_content)
            elif issue.issue_type in ["断剑情节突兀"]:
                fixed_content = repairer.repair_logic_issue(issue, chapter_content)
            elif issue.issue_type in ["foreshadow_issue", "foreshadow_incomplete", "伏笔/悬念断裂", "伏笔未解释"]:
                fixed_content = repairer.repair_foreshadow_issue(issue, chapter_content)
            elif issue.issue_type in ["emotional_rhythm_issue", "emotional_rhythm", "rhythm_issue", "爽点缺失", "节奏问题", "pacing_issue"]:
                fixed_content = repairer.repair_emotional_rhythm_issue(issue, chapter_content)
            elif issue.issue_type in ["角色命名冲突"]:
                fixed_content = repairer.repair_character_issue(issue, chapter_content)
            else:
                continue

            if not dry_run and len(fixed_content) > len(chapter_content) * 0.8:
                ch_file.write_text(fixed_content, encoding='utf-8')
                repaired_count += 1
                print(f"  ch{issue.chapter:03d}: ✓ 已修复 ({issue.issue_type})")
            else:
                print(f"  ch{issue.chapter:03d}: 跳过 (内容异常)")

            results[issue.chapter] = fixed_content

        except Exception as e:
            print(f"  ch{issue.chapter:03d}: ✗ 修复失败 - {e}")

    print(f"  修复完成: {repaired_count}/{len(p0_issues) + len(p1_issues)}")
    return results

#!/usr/bin/env python3
"""
统一质量检查入口
使用方法: python3 run_unified_quality.py [--start 1] [--end 50]
"""
import os
import sys
import argparse

# 项目根目录
PROJECT_ROOT = "/home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory"
CHAPTERS_DIR = os.path.join(PROJECT_ROOT, "03_内容仓库", "04_正文")

# 添加tools/consistency到路径
sys.path.insert(0, os.path.join(PROJECT_ROOT, "tools", "consistency"))

from check_naming import extract_chapter_num
from check_duplicate import check_chapter_duplicates, check_duplicates_parallel
from check_character_state import check_character_consistency
from check_timeline import check_timeline_anomalies
from check_segment_relevance import SegmentRelevanceChecker
from check_plot_device_tracking import PlotDeviceTracker
from check_scene_logic import SceneLogicChecker
from check_emotional_rhythm import EmotionalRhythmChecker
from check_dialogue_style import DialogueStyleChecker
from check_scene_density import check_scene_density
from check_character_activity import check_character_activity
from check_template_sentences import check_template_sentences
from check_battle_density import check_battle_density
from check_realm_system import check_realm_consistency
from check_faction_relations import check_faction_relations


def check_naming():
    """检查章节命名一致性"""
    print("▶ 命名一致性检查...")
    issues = []
    for i in range(1, 361):
        fname = f"ch{i:03d}.md"
        fpath = os.path.join(CHAPTERS_DIR, fname)
        if not os.path.exists(fpath):
            continue
        with open(fpath, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
        title_num = extract_chapter_num(first_line)
        if title_num != i:
            issues.append(f"  ch{i:03d}: 文件名={i}, 标题={title_num}")
    if issues:
        print(f"  ✗ 问题: {len(issues)} 处")
        for iss in issues[:10]:
            print(iss)
        if len(issues) > 10:
            print(f"  ... 还有 {len(issues) - 10} 处")
    else:
        print(f"  ✓ 通过 (360/360)")
    return len(issues)


def check_integrity():
    """检查内容完整性"""
    print("▶ 内容完整性检查...")
    issues = []
    for i in range(1, 361):
        fname = f"ch{i:03d}.md"
        fpath = os.path.join(CHAPTERS_DIR, fname)
        if not os.path.exists(fpath):
            continue
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        if "**本章完**" not in content and "本章完" not in content:
            issues.append(f"  ch{i:03d}: 缺少本章完标记")
        if len(content) < 500:
            issues.append(f"  ch{i:03d}: 字数过少({len(content)}字)")
    if issues:
        print(f"  ✗ 问题: {len(issues)} 处")
        for iss in issues[:10]:
            print(iss)
    else:
        print(f"  ✓ 通过 (360/360)")
    return len(issues)


def check_duplicates(start=1, end=360):
    """检查重复内容 - 自动选择并行/串行"""
    print("▶ 重复内容检查...")
    chapter_count = end - start + 1
    if chapter_count > 100:
        # >100章用多进程并行
        issues = check_duplicates_parallel(CHAPTERS_DIR, (start, end), threshold=0.8)
    else:
        # 小范围用串行
        issues = check_chapter_duplicates(CHAPTERS_DIR, (start, end), threshold=0.8)
    if issues:
        print(f"  ✗ 问题: {len(issues)} 处相似内容")
        for iss in issues[:5]:
            print(f"  {iss}")
    else:
        print(f"  ✓ 通过")
    return len(issues)


def check_character_state():
    """检查人物状态一致性"""
    print("▶ 人物状态检查...")
    issues = check_character_consistency(CHAPTERS_DIR, (1, 360))
    if issues:
        print(f"  ✗ 问题: {len(issues)} 处")
        for iss in issues[:5]:
            print(f"  {iss}")
    else:
        print(f"  ✓ 通过")
    return len(issues)


def check_timeline():
    """检查时间线"""
    print("▶ 时间线检查...")
    issues = check_timeline_anomalies(CHAPTERS_DIR, (1, 360))
    if issues:
        print(f"  ✗ 问题: {len(issues)} 处")
        for iss in issues[:5]:
            print(f"  {iss}")
    else:
        print(f"  ✓ 通过")
    return len(issues)


def check_quality_dimensions(start, end):
    """检查质量维度"""
    print(f"\n▶ 质量维度检查 (ch{start:03d}-ch{end:03d})...")

    try:
        seg_checker = SegmentRelevanceChecker(CHAPTERS_DIR)
        seg_results = seg_checker.check_all(start, end)
        print(f"  情节关联度: {seg_results.get('pass_rate', 'N/A')} (未通过: {len(seg_results.get('failed_chapters', []))} 章)")
    except Exception as e:
        print(f"  情节关联度: 检查失败 ({e})")

    try:
        tracker = PlotDeviceTracker(CHAPTERS_DIR, window=50)
        plt_results = tracker.check_all(start, end)
        print(f"  伏笔回收率: {plt_results.get('recycling_rate', 'N/A')}")
    except Exception as e:
        print(f"  伏笔回收率: 检查失败 ({e})")

    try:
        scene_checker = SceneLogicChecker(CHAPTERS_DIR)
        scene_results = scene_checker.check_all(start, end)
        print(f"  场景逻辑: 孤岛章节 {len(scene_results.get('isolated_chapters', []))} 个, 高严重度问题 {scene_results.get('high_severity_issues', 0)} 处")
    except Exception as e:
        print(f"  场景逻辑: 检查失败 ({e})")

    try:
        emot_checker = EmotionalRhythmChecker(CHAPTERS_DIR)
        emot_results = emot_checker.check_all(start, end)
        print(f"  情感节奏: 未通过 {len(emot_results.get('failed_chapters', []))} 章, 高严重度问题 {emot_results.get('high_severity_issues', 0)} 处")
    except Exception as e:
        print(f"  情感节奏: 检查失败 ({e})")

    try:
        dlg_checker = DialogueStyleChecker(CHAPTERS_DIR)
        dlg_results = dlg_checker.check_all(start, end)
        print(f"  对话风格: {dlg_results.get('total_dialogues', 0)} 条对话, 高严重度问题 {dlg_results.get('high_severity_issues', 0)} 处")
    except Exception as e:
        print(f"  对话风格: 检查失败 ({e})")

    try:
        density_results = check_scene_density(CHAPTERS_DIR, (start, end))
        print(f"  场景密度: 对话均占比{density_results.get('avg_dialogue_ratio', 0):.1%}, 未通过{density_results.get('failed_count', 0)}章")
    except Exception as e:
        print(f"  场景密度: 检查失败 ({e})")

    try:
        activity_results = check_character_activity(CHAPTERS_DIR, (start, end))
        print(f"  角色活跃度: 工具人{activity_results.get('tool_count', 0)}个", end="")
        if activity_results.get('tool_characters'):
            print(f"（{'、'.join(activity_results['tool_characters'])}）")
        else:
            print()
    except Exception as e:
        print(f"  角色活跃度: 检查失败 ({e})")

    try:
        template_results = check_template_sentences(CHAPTERS_DIR, (start, end))
        print(f"  句式重复: 高重复章节{template_results.get('high_template_count', 0)}个, 均模板句{template_results.get('avg_templates_per_chapter', 0):.1f}/章")
    except Exception as e:
        print(f"  句式重复: 检查失败 ({e})")

    try:
        battle_results = check_battle_density(CHAPTERS_DIR, (start, end))
        print(f"  战斗密度: 平均{battle_results.get('avg_battle_density', 0):.1%}, 不足{battle_results.get('low_battle_count', 0)}章, 口头战斗{battle_results.get('talked_battle_count', 0)}章")
    except Exception as e:
        print(f"  战斗密度: 检查失败 ({e})")

    try:
        realm_results = check_realm_consistency(CHAPTERS_DIR, (start, end))
        print(f"  境界体系: 发现{len(realm_results.get('realms_found', []))}个境界, 矛盾{realm_results.get('contradiction_count', 0)}处")
    except Exception as e:
        print(f"  境界体系: 检查失败 ({e})")

    try:
        faction_results = check_faction_relations(CHAPTERS_DIR, (start, end))
        print(f"  势力关系: 关系变化{faction_results.get('change_count', 0)}处, 混乱势力{len(faction_results.get('inconsistent_factions', []))}个")
    except Exception as e:
        print(f"  势力关系: 检查失败 ({e})")


def main():
    parser = argparse.ArgumentParser(description='统一质量检查')
    parser.add_argument('--start', type=int, default=1, help='起始章节')
    parser.add_argument('--end', type=int, default=360, help='结束章节')
    parser.add_argument('--output', '-o', help='输出报告路径')
    parser.add_argument('--skip-basic', action='store_true', help='跳过基础检查')
    parser.add_argument('--quality-only', action='store_true', help='仅运行质量维度检查')
    args = parser.parse_args()

    print("=" * 70)
    print("小说工厂 · 统一质量检查")
    print("=" * 70)
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"检查范围: ch{args.start:03d}-ch{args.end:03d}")
    print()

    if args.quality_only:
        check_quality_dimensions(args.start, args.end)
        return

    if not args.skip_basic:
        check_naming()
        check_integrity()
        check_duplicates(args.start, args.end)
        check_character_state()
        check_timeline()
        print()

    check_quality_dimensions(args.start, args.end)

    print()
    print("=" * 70)
    print("检查完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
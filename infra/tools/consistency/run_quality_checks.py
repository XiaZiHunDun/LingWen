#!/usr/bin/env python3
"""
质量维度检查器 - 统一调度
在Claude Code中运行时，通过Agent机制调用LLM执行需要理解能力的检查
"""
import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, List


def run_segment_relevance(chapters_dir: str, chapter_range: tuple) -> Dict:
    """运行情节关联度检查"""
    print("▶ 情节关联度检查...")
    from check_segment_relevance import SegmentRelevanceChecker

    checker = SegmentRelevanceChecker(chapters_dir)
    results = checker.check_all(chapter_range[0], chapter_range[1])

    passed = results['failed_segments']
    total = results['total_segments']
    rate = results['pass_rate']
    print(f"  通过率: {rate} ({passed}/{total} 段落未通过)")
    return results


def run_plot_device_tracking(chapters_dir: str, chapter_range: tuple) -> Dict:
    """运行伏笔回收率检查"""
    print("▶ 伏笔回收率检查...")
    from check_plot_device_tracking import PlotDeviceTracker

    tracker = PlotDeviceTracker(chapters_dir, window=50)
    results = tracker.check_all(chapter_range[0], chapter_range[1])

    rate = results.get('recycling_rate', '0%')
    planted = sum(results['planted'].values())
    recycled = sum(results['recycled'].values())
    print(f"  回收率: {rate} ({recycled}/{planted} 伏笔已回收)")
    return results


def run_scene_logic(chapters_dir: str, chapter_range: tuple) -> Dict:
    """运行场景逻辑连贯性检查"""
    print("▶ 场景逻辑连贯性检查...")
    from check_scene_logic import SceneLogicChecker

    checker = SceneLogicChecker(chapters_dir)
    results = checker.check_all(chapter_range[0], chapter_range[1])

    issues = results['high_severity_issues']
    isolated = len(results['isolated_chapters'])
    print(f"  高严重度问题: {issues} 处, 孤岛章节: {isolated} 个")
    return results


def run_emotional_rhythm(chapters_dir: str, chapter_range: tuple) -> Dict:
    """运行情感节奏健康度检查"""
    print("▶ 情感节奏健康度检查...")
    from check_emotional_rhythm import EmotionalRhythmChecker

    checker = EmotionalRhythmChecker(chapters_dir)
    results = checker.check_all(chapter_range[0], chapter_range[1])

    issues = results['high_severity_issues']
    failed = len(results['failed_chapters'])
    print(f"  高严重度问题: {issues} 处, 未通过章节: {failed} 个")
    return results


def run_dialogue_style(chapters_dir: str, chapter_range: tuple) -> Dict:
    """运行对话风格一致性检查"""
    print("▶ 对话风格一致性检查...")
    from check_dialogue_style import DialogueStyleChecker

    checker = DialogueStyleChecker(chapters_dir)
    results = checker.check_all(chapter_range[0], chapter_range[1])

    issues = results['high_severity_issues']
    dialogues = results['total_dialogues']
    print(f"  高严重度问题: {issues} 处, 总对话数: {dialogues} 条")
    return results


def run_character_arc_with_agent(chapters_dir: str, chapter_range: tuple,
                                  characters: List[str] = None) -> List[Dict]:
    """
    运行人物弧光检查（通过Claude Code Agent调用LLM）

    核心机制：
    1. 构建分析任务提示词
    2. 使用Agent工具执行LLM任务
    3. 解析JSON结果

    注意：此函数需要在Claude Code环境中运行，才能使用Agent工具
    """
    print("▶ 人物弧光完整性检查（通过Agent调用LLM）...")

    try:
        from check_character_arc_llm import CHARACTER_ARCS, CharacterArcChecker
    except ImportError:
        print("  错误: 无法导入角色弧光检查模块")
        return []

    checker = CharacterArcChecker(chapters_dir)
    chars_to_check = characters or list(CHARACTER_ARCS.keys())
    arc_results = []

    for char in chars_to_check:
        task = checker.build_analysis_task(char, chapter_range[0], chapter_range[1])

        if not task:
            arc_results.append({
                'character': char,
                'checked': False,
                'reason': '未找到角色配置或章节中未出现该角色'
            })
            continue

        print(f"  正在分析: {char}...")

        # 检查Agent是否可用（通过globals检查）
        if 'Agent' not in globals():
            # Agent工具不可用，说明不是在Claude Code环境中运行
            print("  [提示] Agent工具不可用，请使用Claude Code会话运行此检查")
            arc_results.append({
                'character': char,
                'checked': False,
                'reason': 'Agent工具不可用，需在Claude Code中运行',
                'prompt_hint': "请在Claude Code中执行角色弧光分析"
            })
            continue

        # 使用Claude Code的Agent机制调用LLM
        # Agent 是 Claude Code 框架注入的全局类,静态分析无法识别
        agent = Agent(  # noqa: F821
            description=f"角色弧光分析_{char}",
            prompt=task['prompt'],
            subagent_type="general-purpose"
        )

        result_text = agent.result.strip()

        # 解析JSON结果
        try:
            start = result_text.find('{')
            end = result_text.rfind('}') + 1
            if start >= 0 and end > start:
                parsed = json.loads(result_text[start:end])
                parsed['character'] = char
                parsed['checked'] = True
                arc_results.append(parsed)
            else:
                arc_results.append({
                    'character': char,
                    'checked': False,
                    'reason': 'LLM响应格式错误',
                    'error': result_text[:200]
                })
        except json.JSONDecodeError as e:
            arc_results.append({
                'character': char,
                'checked': False,
                'reason': f'JSON解析失败: {e}',
                'error': result_text[:200]
            })

    # 统计
    checked = len([r for r in arc_results if r.get('checked')])
    complete = len([r for r in arc_results if r.get('is_complete')])
    print(f"  完成: {checked}/{len(chars_to_check)} 个角色, 弧光完整: {complete} 个")

    return arc_results


def generate_quality_report(all_results: Dict, output_file: str = None) -> str:
    """生成质量维度检查汇总报告"""
    lines = []
    lines.append("=" * 70)
    lines.append("质量维度检查汇总报告 (Claude Code版)")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # 情节关联度
    seg = all_results.get('segment_relevance', {})
    lines.append("## 情节关联度")
    lines.append(f"通过率: {seg.get('pass_rate', 'N/A')}")
    lines.append(f"未通过章节: {len(seg.get('failed_chapters', []))} 个")
    lines.append("")

    # 伏笔回收率
    plt = all_results.get('plot_device', {})
    lines.append("## 伏笔回收率")
    lines.append(f"回收率: {plt.get('recycling_rate', 'N/A')}")
    total_planted = sum(plt.get('planted', {}).values())
    total_recycled = sum(plt.get('recycled', {}).values())
    lines.append(f"已回收: {total_recycled}/{total_planted}")
    lines.append("")

    # 场景逻辑
    scene = all_results.get('scene_logic', {})
    lines.append("## 场景逻辑连贯性")
    lines.append(f"孤岛章节: {len(scene.get('isolated_chapters', []))} 个")
    lines.append(f"高严重度问题: {scene.get('high_severity_issues', 0)} 处")
    lines.append("")

    # 情感节奏
    emot = all_results.get('emotional_rhythm', {})
    lines.append("## 情感节奏健康度")
    lines.append(f"未通过章节: {len(emot.get('failed_chapters', []))} 个")
    lines.append(f"高严重度问题: {emot.get('high_severity_issues', 0)} 处")
    lines.append("")

    # 对话风格
    dlg = all_results.get('dialogue_style', {})
    lines.append("## 对话风格一致性")
    lines.append(f"总对话数: {dlg.get('total_dialogues', 0)} 条")
    lines.append(f"高严重度问题: {dlg.get('high_severity_issues', 0)} 处")
    lines.append("")

    # 人物弧光（通过Agent调用LLM）
    arc = all_results.get('character_arc', [])
    if arc:
        lines.append("## 人物弧光完整性（Agent调用LLM）")
        complete = len([r for r in arc if r.get('is_complete')])
        checked = len([r for r in arc if r.get('checked')])
        lines.append(f"弧光完整: {complete}/{checked} 个角色")
        for r in arc:
            if r.get('checked'):
                status = "✓" if r.get('is_complete') else "✗"
                score = r.get('score', 'N/A')
                arc_type = r.get('arc_type', '')
                lines.append(f"  {status} {r.get('character', 'Unknown')} [{arc_type}]: {score}/10")
                if not r.get('is_complete') and r.get('missing_stages'):
                    lines.append(f"      缺失: {', '.join(r['missing_stages'])}")
            else:
                lines.append(f"  ✗ {r.get('character', 'Unknown')}: {r.get('reason', '检查失败')}")
    lines.append("")

    report = "\n".join(lines)
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n报告已保存到: {output_file}")

    return report


def main():
    parser = argparse.ArgumentParser(description='质量维度检查器 (Claude Code版)')
    parser.add_argument('chapters_dir', help='章节目录路径')
    parser.add_argument('--start', type=int, default=1, help='起始章节')
    parser.add_argument('--end', type=int, default=50, help='结束章节（建议≤50章）')
    parser.add_argument('--skip-llm', action='store_true', help='跳过LLM类检查')
    parser.add_argument('--output', '-o', help='输出报告路径')
    parser.add_argument('--checks', nargs='+', choices=[
        'segment', 'plot', 'scene', 'emotion', 'dialogue', 'arc', 'all'
    ], default=['all'], help='选择要运行的检查项')
    args = parser.parse_args()

    chapter_range = (args.start, args.end)

    print("=" * 70)
    print("质量维度检查 (Claude Code版)")
    print("=" * 70)
    print(f"章节范围: ch{chapter_range[0]:03d}-ch{chapter_range[1]:03d}")
    print()

    all_results = {}

    # 规则类检查
    if 'segment' in args.checks or 'all' in args.checks:
        all_results['segment_relevance'] = run_segment_relevance(args.chapters_dir, chapter_range)

    if 'plot' in args.checks or 'all' in args.checks:
        all_results['plot_device'] = run_plot_device_tracking(args.chapters_dir, chapter_range)

    if 'scene' in args.checks or 'all' in args.checks:
        all_results['scene_logic'] = run_scene_logic(args.chapters_dir, chapter_range)

    if 'emotion' in args.checks or 'all' in args.checks:
        all_results['emotional_rhythm'] = run_emotional_rhythm(args.chapters_dir, chapter_range)

    if 'dialogue' in args.checks or 'all' in args.checks:
        all_results['dialogue_style'] = run_dialogue_style(args.chapters_dir, chapter_range)

    # LLM类检查（通过Agent调用）
    if 'arc' in args.checks or 'all' in args.checks:
        if args.skip_llm:
            print("▶ [跳过] 人物弧光检查（需Agent调用LLM）")
        else:
            all_results['character_arc'] = run_character_arc_with_agent(args.chapters_dir, chapter_range)

    print()
    print("=" * 70)

    # 生成汇总报告
    report = generate_quality_report(all_results, args.output)
    print(report)


if __name__ == "__main__":
    main()

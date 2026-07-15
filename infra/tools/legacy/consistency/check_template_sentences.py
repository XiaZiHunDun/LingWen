#!/usr/bin/env python3
"""
句式重复检测器 v2.0
检测高频模板句，生成工单，支持同义替换建议

改进日志：
- v2.0: 新增工单生成机制、同义替换建议、AUTO vs MANUAL分类
"""
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime
from typing import Dict, List, Tuple

import yaml

# 已知的模板句式（需要检测的重复模式）
TEMPLATE_PATTERNS = [
    # 星空/星光类（评审指出最典型的重复）
    r'星光在流转',
    r'见证着这一刻',
    r'星辰的光芒',
    r'星空之下',
    r'星光下',
    # 眼神/目光类
    r'林夜看着苏琳',
    r'苏琳看着林夜',
    r'目光中带着',
    r'眼中闪过',
    r'眼眶有些泛红',
    # 守护/黑暗主题类（评审指出过度使用）
    r'守护.*意义',
    r'黑暗不是用来消灭',
    r'守护.*值得',
    # 动作模板
    r'轻声说',
    r'微微一笑',
    r'握住了.*手',
    r'靠在.*肩',
    r'依偎在',
    # 过渡/总结句
    r'那一刻',
    r'就在这时',
    r'一切都在',
]

# 必须人工重写的模式（主题隐喻型）
MANUAL_ONLY_PATTERNS = [
    '见证着这一刻',
    '见证这一刻的',
    '这一刻的星光',
    '守护.*意义',
    '黑暗不是用来消灭',
]


def load_synonym_dict(synonym_file: str = None) -> Dict[str, List[str]]:
    """加载同义替换词库"""
    if synonym_file is None:
        # 默认路径
        base_dir = os.path.dirname(os.path.abspath(__file__))
        synonym_file = os.path.join(base_dir, 'template_synonyms.yaml')

    if not os.path.exists(synonym_file):
        return {}

    with open(synonym_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    result = {}
    for category in ['dialogue_tags', 'emotion_reactions', 'action_templates', 'atmosphere_descriptions']:
        if category in data:
            for pattern, synonyms in data[category].items():
                result[pattern] = synonyms
    return result


def detect_template_sentences(content: str) -> Dict[str, int]:
    """检测内容中的模板句出现次数"""
    detected = {}
    for pattern in TEMPLATE_PATTERNS:
        if pattern == r'星光在流转':
            matches = re.findall(r'星光.*流转', content)
        elif pattern == r'守护.*意义':
            matches = re.findall(r'守护.*意义', content)
        elif pattern == r'黑暗不是用来消灭':
            matches = re.findall(r'黑暗不是用来', content)
        elif pattern == r'守护.*值得':
            matches = re.findall(r'守护.*值得', content)
        else:
            matches = re.findall(pattern, content)

        if matches:
            detected[pattern] = len(matches)

    return detected


def find_common_ngrams(content: str, n: int = 5, min_occurrences: int = 3) -> Dict[str, int]:
    """自动发现高频N-gram模式"""
    words = re.findall(r'[\u4e00-\u9fa5]+', content)
    ngrams = []
    for i in range(len(words) - n + 1):
        ngram = ' '.join(words[i:i+n])
        ngrams.append(ngram)

    counter = Counter(ngrams)
    return {ng: c for ng, c in counter.items() if c >= min_occurrences}


def check_template_sentences(chapters_dir: str,
                             chapter_range: tuple[int, int] = (1, 360),
                             template_threshold: int = 3,
                             synonym_file: str = None) -> Dict:
    """
    检测句式重复 v2.0

    Args:
        chapters_dir: 章节目录
        chapter_range: 检查章节范围
        template_threshold: 单个模板句在同一章出现超过此值则报警
        synonym_file: 同义替换词库路径

    Returns:
        检测结果字典
    """
    # 加载同义词库
    synonym_dict = load_synonym_dict(synonym_file)

    start, end = chapter_range

    # 全局统计
    global_template_counts: Dict[str, List[int]] = {}

    chapter_results = []
    total_templates_per_chapter = 0
    high_template_chapters = []

    for i in range(start, end + 1):
        fname = f"ch{i:03d}.md"
        fpath = os.path.join(chapters_dir, fname)

        if not os.path.exists(fpath):
            continue

        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        detected = detect_template_sentences(content)
        common_ngrams = find_common_ngrams(content, n=4, min_occurrences=3)

        total_in_chapter = sum(detected.values()) + sum(common_ngrams.values())
        total_templates_per_chapter += total_in_chapter

        issues = []
        for pattern, count in detected.items():
            if count >= template_threshold:
                wo_type = 'MANUAL' if pattern in MANUAL_ONLY_PATTERNS else 'AUTO'
                synonyms = synonym_dict.get(pattern, []) if wo_type == 'AUTO' else []
                issues.append({
                    'pattern': pattern,
                    'count': count,
                    'type': wo_type,
                    'synonyms': synonyms
                })
        for ngram, count in common_ngrams.items():
            if count >= template_threshold:
                issues.append({
                    'pattern': ngram,
                    'count': count,
                    'type': 'AUTO',
                    'synonyms': []
                })

        if issues:
            high_template_chapters.append(i)

        chapter_results.append({
            'chapter': i,
            'template_count': total_in_chapter,
            'issues': issues,
            'passed': len(issues) == 0,
            'details': detected
        })

        for pattern, count in detected.items():
            if pattern not in global_template_counts:
                global_template_counts[pattern] = []
            if count > 0:
                global_template_counts[pattern].append(i)

    # 全局高频模板
    global_high_freq = []
    for pattern, chapters in sorted(global_template_counts.items(),
                                   key=lambda x: len(x[1]), reverse=True):
        if len(chapters) >= 10:
            total = sum(detect_template_sentences(
                open(f'{chapters_dir}/ch{ch:03d}.md', 'r', encoding='utf-8').read()
            ).get(pattern, 0) for ch in chapters)
            global_high_freq.append({
                'pattern': pattern,
                'chapter_count': len(chapters),
                'total_mentions': total
            })

    avg_templates = total_templates_per_chapter / len(chapter_results) if chapter_results else 0

    return {
        'checked_chapters': len(chapter_results),
        'avg_templates_per_chapter': avg_templates,
        'high_template_chapters': high_template_chapters,
        'high_template_count': len(high_template_chapters),
        'global_high_freq': global_high_freq[:10],
        'results': chapter_results
    }


def generate_template_workorders(results: Dict, chapters_dir: str = None, output_dir: str = None) -> List[Dict]:
    """
    从检测结果生成工单

    Args:
        results: check_template_sentences 的返回结果
        chapters_dir: 章节目录（用于计算行号）
        output_dir: 工单输出目录

    Returns:
        工单列表
    """
    workorders = []

    for r in results['results']:
        if not r['passed']:
            for issue in r['issues']:
                wo = {
                    'workorder_id': f"TMPL-{r['chapter']:03d}-{hash(issue['pattern']) % 10000:04d}",
                    'created_at': datetime.now().isoformat(),
                    'type': 'template_sentence',
                    'chapter': f"ch{r['chapter']:03d}",
                    'pattern': issue['pattern'],
                    'count': issue['count'],
                    'issue_type': issue.get('type', 'AUTO'),
                    'synonyms': issue.get('synonyms', []),
                    'priority': 'P0' if issue.get('type') == 'MANUAL' else 'P1',
                    'status': 'pending',
                    'suggestion': '建议替换为同义表达' if issue.get('synonyms') else '必须人工重写'
                }
                workorders.append(wo)

    # 全局级工单
    for item in results.get('global_high_freq', []):
        if item['chapter_count'] >= 30:  # 超过30章使用
            workorders.append({
                'workorder_id': f"TMPL-GLOBAL-{hash(item['pattern']) % 10000:04d}",
                'created_at': datetime.now().isoformat(),
                'type': 'template_global_overuse',
                'chapter': f"{item['chapter_count']}章",
                'pattern': item['pattern'],
                'total_mentions': item['total_mentions'],
                'issue_type': 'MANUAL' if item['pattern'] in MANUAL_ONLY_PATTERNS else 'AUTO',
                'priority': 'P2',
                'status': 'pending',
                'suggestion': '全局过度使用，建议系统性替换或重写'
            })

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        fpath = os.path.join(output_dir, f'template_workorders_{timestamp}.json')
        with open(fpath, 'w', encoding='utf-8') as f:
            json.dump(workorders, f, ensure_ascii=False, indent=2)

    return workorders


def report_results(results: Dict, output_file: str = None) -> str:
    """生成句式重复检查报告"""
    lines = []
    lines.append("=" * 70)
    lines.append("句式重复检查报告 (v2.0)")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"检查章节: {results['checked_chapters']} 章")
    lines.append(f"平均模板句/章: {results['avg_templates_per_chapter']:.1f}")
    lines.append(f"高重复章节: {results['high_template_count']} 个")

    if results['global_high_freq']:
        lines.append("")
        lines.append("--- 全局高频模板句（前10）---")
        for item in results['global_high_freq']:
            manual = " [需人工重写]" if item['pattern'] in MANUAL_ONLY_PATTERNS else ""
            lines.append(f"  「{item['pattern']}」：出现在{item['chapter_count']}章，共{item['total_mentions']}次{manual}")

    if results['high_template_chapters']:
        lines.append("")
        lines.append("--- 高重复章节（前10）---")
        for ch in results['high_template_chapters'][:10]:
            for r in results['results']:
                if r['chapter'] == ch:
                    issue_strs = []
                    for iss in r['issues'][:3]:
                        t = iss.get('type', 'AUTO')
                        issue_strs.append(f"「{iss['pattern']}」{iss['count']}次[{t}]")
                    lines.append(f"  ch{ch:03d}: {', '.join(issue_strs)}")
                    break

    report = "\n".join(lines)
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='句式重复检查')
    parser.add_argument('chapters_dir', help='章节目录路径')
    parser.add_argument('--start', type=int, default=1, help='起始章节')
    parser.add_argument('--end', type=int, default=360, help='结束章节')
    parser.add_argument('--threshold', type=int, default=3, help='单章内模板句阈值')
    parser.add_argument('--output', '-o', help='输出报告路径')
    parser.add_argument('--workorder-dir', help='工单输出目录')
    args = parser.parse_args()

    results = check_template_sentences(args.chapters_dir, (args.start, args.end), args.threshold)

    if args.workorder_dir:
        generate_template_workorders(results, args.chapters_dir, args.workorder_dir)

    report = report_results(results, args.output)
    print(report)

    sys.exit(0 if results['high_template_count'] == 0 else 1)

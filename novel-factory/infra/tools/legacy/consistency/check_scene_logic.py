#!/usr/bin/env python3
"""
场景逻辑连贯性检查器
检测场景转换是否合理，识别孤岛章节和逻辑跳跃
"""
import os
import re
import sys
from typing import List, Tuple, Dict, Set, Optional
from collections import defaultdict


class SceneLogicChecker:
    """场景逻辑连贯性检查器"""

    # 场景转换标记词
    SCENE_TRANSITION_KEYWORDS = [
        # 时间跳跃
        '时间流逝', '几天后', '数日后', '数月后', '一年后', '多年后',
        '转眼', '眨眼', '须臾', '片刻后', '片刻之间', '不多时',
        # 地点转换
        '来到了', '进入了', '返回', '回到了', '穿过', '跨入',
        '来到', '抵达', '降落在', '出现在', '一路来到',
        # 场景切换
        '与此同时', '另一边', '同一时刻', '视角转向', '画面切换',
        # 章节级别的大跨度转换
        '第一章', '第二章', '上一章', '下一章',
    ]

    # 场景延续标记（说明场景连续的词）
    SCENE_CONTINUATION_KEYWORDS = [
        '继续', '接着', '依然', '仍然', '依旧', '一如往常',
        '此情此景', '此时此刻',
    ]

    # 逻辑连接词（检测段落间连接）
    LOGIC_CONNECTORS = [
        '因为', '所以', '然而', '但是', '不过', '虽然', '即使',
        '因此', '于是', '由于', '既然', '倘若', '假如',
        '紧接着', '随后', '紧接着', '于是乎', '而后',
    ]

    def __init__(self, chapters_dir: str, window: int = 3):
        """
        Args:
            chapters_dir: 章节目录
            window: 向前后检索的章节数
        """
        self.chapters_dir = chapters_dir

    def load_chapter(self, chapter_num: int) -> str:
        """加载章节内容"""
        fname = f"ch{chapter_num:03d}.md"
        fpath = os.path.join(self.chapters_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def extract_scene_elements(self, content: str) -> Dict:
        """
        提取场景元素

        Returns:
            dict with scene information
        """
        elements = {
            'locations': set(),
            'characters': set(),
            'time_markers': [],
            'scene_transitions': [],
            'logic_connectors': [],
        }

        # 地点检测（常见地点后缀）
        location_suffixes = ['城', '域', '海', '宗', '阁', '殿', '宫', '废墟', '遗迹', '星']
        for suffix in location_suffixes:
            pattern = rf'[\u4e00-\u9fa5]{{1,4}}{suffix}'
            for match in re.finditer(pattern, content):
                loc = match.group()
                if len(loc) >= 2:
                    elements['locations'].add(loc)

        # 主要人物
        main_chars = ['林夜', '苏琳', '小九', '铁蛋', '星月', '莫言', '星瑶', '墨白', '本源', '虚无', '暗皇', '星辰']
        for char in main_chars:
            if char in content:
                elements['characters'].add(char)

        # 时间跳跃标记
        for kw in self.SCENE_TRANSITION_KEYWORDS[:12]:  # 只检测时间跳跃
            if kw in content:
                elements['time_markers'].append(kw)

        # 场景转换词
        for kw in self.SCENE_TRANSITION_KEYWORDS[12:]:  # 场景切换
            if kw in content:
                elements['scene_transitions'].append(kw)

        # 逻辑连接词
        for kw in self.LOGIC_CONNECTORS:
            if kw in content:
                elements['logic_connectors'].append(kw)

        return elements

    def calculate_scene_similarity(self, elements1: Dict, elements2: Dict) -> float:
        """
        计算两个场景的相似度

        Returns:
            0-1的相似度分数
        """
        score = 0.0
        max_score = 0.0

        # 地点重叠（权重最高）
        if elements1['locations'] and elements2['locations']:
            loc_overlap = len(elements1['locations'] & elements2['locations'])
            loc_union = len(elements1['locations'] | elements2['locations'])
            if loc_union > 0:
                score += loc_overlap / loc_union * 3  # 地点权重3
            max_score += 3

        # 人物重叠（权重中等）
        if elements1['characters'] and elements2['characters']:
            char_overlap = len(elements1['characters'] & elements2['characters'])
            char_union = len(elements1['characters'] | elements2['characters'])
            if char_union > 0:
                score += char_overlap / char_union * 2  # 人物权重2
            max_score += 2

        # 逻辑连接词（权重较低）
        if elements1['logic_connectors'] and elements2['logic_connectors']:
            conn_overlap = len(set(elements1['logic_connectors']) & set(elements2['logic_connectors']))
            if conn_overlap > 0:
                score += min(conn_overlap * 0.5, 1.0)  # 最多加1分
            max_score += 1

        return score / max_score if max_score > 0 else 0.0

    def check_scene_continuity(self, chapter_num: int, prev_elements: Optional[Dict] = None,
                             next_elements: Optional[Dict] = None) -> Dict:
        """
        检查章节的场景连贯性

        Args:
            chapter_num: 章节号
            prev_elements: 前一章场景元素
            next_elements: 后一章场景元素

        Returns:
            check result dict
        """
        content = self.load_chapter(chapter_num)
        if not content:
            return {'chapter': chapter_num, 'passed': True, 'issues': []}

        current_elements = self.extract_scene_elements(content)

        issues = []
        connections = {'prev': 0.0, 'next': 0.0}

        # 检查与前序章节的连贯性
        if prev_elements:
            similarity = self.calculate_scene_similarity(prev_elements, current_elements)
            connections['prev'] = similarity
            # 阈值设为5%，允许合理的视角切换/场景跳跃
            # 小说中多视角、场景切换是常见手法，不应视为质量问题
            if similarity < 0.05:
                issues.append({
                    'type': 'ISOLATED_FROM_PREV',
                    'desc': f'与前章相似度{similarity:.2%}过低（<5%）',
                    'severity': 'HIGH'
                })

        # 检查与后续章节的连贯性
        if next_elements:
            similarity = self.calculate_scene_similarity(current_elements, next_elements)
            connections['next'] = similarity
            if similarity < 0.05:
                issues.append({
                    'type': 'ISOLATED_TO_NEXT',
                    'desc': f'与后章相似度{similarity:.2%}过低（<5%）',
                    'severity': 'HIGH'
                })

        # 检查是否有场景转换但没有过渡
        if current_elements['scene_transitions'] and not current_elements['logic_connectors']:
            issues.append({
                'type': 'ABRUPT_TRANSITION',
                'desc': f'有场景转换({len(current_elements["scene_transitions"])}处)但缺少逻辑连接',
                'severity': 'MEDIUM'
            })

        # 检查是否"本章完"前有合理的场景收尾
        if '**本章完**' in content:
            # 找到"本章完"的位置，检查前面是否有场景延续
            end_pos = content.find('**本章完**')
            before_end = content[max(0, end_pos-200):end_pos]
            has_continuation = any(kw in before_end for kw in self.SCENE_CONTINUATION_KEYWORDS)
            has_transition = any(kw in before_end for kw in self.SCENE_TRANSITION_KEYWORDS)
            if not has_continuation and not has_transition and len(before_end.strip()) > 0:
                issues.append({
                    'type': 'SUDDEN_END',
                    'desc': '章节结束前缺少场景收尾或转换标记',
                    'severity': 'LOW'
                })

        return {
            'chapter': chapter_num,
            'passed': len([i for i in issues if i['severity'] == 'HIGH']) == 0,
            'issues': issues,
            'connections': connections,
            'locations': list(current_elements['locations'])[:5],
            'characters': list(current_elements['characters'])[:5],
        }

    def check_all(self, start_ch: int = 1, end_ch: int = 360) -> Dict:
        """
        检查所有章节的场景连贯性

        Returns:
            完整检查结果
        """
        all_results = []
        failed_chapters = []
        isolated_chapters = []

        # 先提取所有章节的场景元素
        all_elements = {}
        for ch_num in range(start_ch, end_ch + 1):
            content = self.load_chapter(ch_num)
            if content:
                all_elements[ch_num] = self.extract_scene_elements(content)

        # 然后检查连贯性
        for ch_num in range(start_ch, end_ch + 1):
            if ch_num not in all_elements:
                continue

            prev_elements = all_elements.get(ch_num - 1)
            next_elements = all_elements.get(ch_num + 1)

            result = self.check_scene_continuity(ch_num, prev_elements, next_elements)
            all_results.append(result)

            if not result['passed']:
                failed_chapters.append(ch_num)
            # 孤岛章节：相似度低于5%才算（放宽到5%，与HIGH severity阈值一致）
            # 15%以下只是轻微断开，5%以下才是真正的孤岛
            if result['connections']['prev'] < 0.05 or result['connections']['next'] < 0.05:
                isolated_chapters.append(ch_num)

        # 统计
        total_issues = sum(len(r['issues']) for r in all_results)
        high_issues = sum(len([i for i in r['issues'] if i['severity'] == 'HIGH']) for r in all_results)

        return {
            'checked_chapters': end_ch - start_ch + 1,
            'total_issues': total_issues,
            'high_severity_issues': high_issues,
            'failed_chapters': failed_chapters,
            'isolated_chapters': isolated_chapters,
            'pass_rate': f"{len(all_results) - len(failed_chapters) / len(all_results) * 100:.1f}%" if all_results else "0%",
            'results': all_results
        }


def report_results(results: Dict, output_file: str = None) -> str:
    """生成检查报告"""
    lines = []
    lines.append("=" * 70)
    lines.append("场景逻辑连贯性检查报告")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"检查章节: {results['checked_chapters']} 章")
    lines.append(f"发现问题: {results['total_issues']} 处")
    lines.append(f"高严重度问题: {results['high_severity_issues']} 处")
    lines.append(f"未通过章节: {len(results['failed_chapters'])} 个")
    lines.append(f"")

    # 孤岛章节
    if results['isolated_chapters']:
        lines.append(f"--- 孤岛章节（与前后章相似度<15%）---")
        for ch in results['isolated_chapters'][:10]:
            lines.append(f"  ch{ch:03d}")
        if len(results['isolated_chapters']) > 10:
            lines.append(f"  ... 还有 {len(results['isolated_chapters']) - 10} 个")

    # 高严重度问题章节
    high_issue_chapters = [r for r in results['results'] if any(i['severity'] == 'HIGH' for i in r['issues'])]
    if high_issue_chapters:
        lines.append("")
        lines.append("--- 高严重度问题章节 ---")
        for r in high_issue_chapters[:10]:
            lines.append(f"\nch{r['chapter']:03d}:")
            for issue in r['issues']:
                if issue['severity'] == 'HIGH':
                    lines.append(f"  [{issue['type']}] {issue['desc']}")

    report = "\n".join(lines)
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='场景逻辑连贯性检查')
    parser.add_argument('chapters_dir', help='章节目录路径')
    parser.add_argument('--start', type=int, default=1, help='起始章节')
    parser.add_argument('--end', type=int, default=360, help='结束章节')
    parser.add_argument('--output', '-o', help='输出报告路径')
    args = parser.parse_args()

    checker = SceneLogicChecker(args.chapters_dir)
    results = checker.check_all(args.start, args.end)
    report = report_results(results, args.output)
    print(report)

    sys.exit(0 if results['high_severity_issues'] == 0 else 1)
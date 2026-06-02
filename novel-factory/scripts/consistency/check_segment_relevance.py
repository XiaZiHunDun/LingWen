#!/usr/bin/env python3
"""
情节关联度检查器
检查每个段落与前后章节的关联程度，确保情节不孤立
"""
import re
import os
import sys
from typing import List, Tuple, Dict, Set
from collections import defaultdict


class SegmentRelevanceChecker:
    """段落关联度检查器"""

    def __init__(self, chapters_dir: str, window: int = 5, min_connections: int = 10):
        """
        Args:
            chapters_dir: 章节目录
            window: 向前后各检索的章节数
            min_connections: 最低关联点数
        """
        self.chapters_dir = chapters_dir
        self.window = window
        self.min_connections = min_connections

    def load_chapter(self, chapter_num: int) -> str:
        """加载章节内容"""
        fname = f"ch{chapter_num:03d}.md"
        fpath = os.path.join(self.chapters_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def extract_keywords(self, text: str) -> Dict[str, Set[str]]:
        """
        从文本中提取关键词

        Returns:
            dict with keys: 'characters', 'objects', 'locations', 'actions', 'emotions'
        """
        keywords = {
            'characters': set(),
            'objects': set(),
            'locations': set(),
            'actions': set(),
            'emotions': set()
        }

        # 人物名（中文2-4字，英文单词）
        # 主要人物列表
        main_chars = ['林夜', '苏琳', '小九', '铁蛋', '星月', '莫言', '星瑶',
                      '墨白', '本源', '虚无', '暗皇', '星辰', '玄机阁']

        for char in main_chars:
            if char in text:
                keywords['characters'].add(char)

        # 地点/组织（常见后缀）
        location_patterns = ['城', '域', '星', '海', '宗', '阁', '殿', '宫']
        for pattern in location_patterns:
            matches = re.findall(rf'[\u4e00-\u9fa5]*{pattern}', text)
            keywords['locations'].update(matches)

        # 物件（常见前 suffix）
        object_patterns = ['剑', '刀', '机甲', '星', '光', '徽章', '碎片']
        for pattern in object_patterns:
            matches = re.findall(rf'{pattern}[\u4e00-\u9fa5]*', text)
            keywords['objects'].update(matches)

        # 情感词
        emotion_words = ['愤怒', '悲伤', '喜悦', '恐惧', '温柔', '坚定', '孤独',
                         '绝望', '希望', '爱', '恨', '温暖', '冰冷']
        for emotion in emotion_words:
            if emotion in text:
                keywords['emotions'].add(emotion)

        # 动作词（常见动词）
        action_words = ['守护', '战斗', '牺牲', '拥抱', '离别', '寻找', '等待',
                        '相信', '怀疑', '守护', '离开', '回来', '死亡', '复活']
        for action in action_words:
            if action in text:
                keywords['actions'].add(action)

        return keywords

    def calculate_connections(self, segment_keywords: Dict[str, Set[str]],
                              chapter_nums: List[int]) -> Tuple[int, List[str]]:
        """
        计算段落与指定章节的关联点数量

        Returns:
            (connection_count, connection_details)
        """
        total_connections = 0
        details = []

        for ch_num in chapter_nums:
            if ch_num < 0 or ch_num > 360:
                continue

            content = self.load_chapter(ch_num)
            if not content:
                continue

            ch_connections = 0
            ch_details = []

            # 检查人物关联
            for char in segment_keywords['characters']:
                if char in content:
                    ch_connections += 1
                    ch_details.append(f"人物:{char}")

            # 检查物件关联
            for obj in segment_keywords['objects']:
                if obj in content and len(obj) >= 2:
                    ch_connections += 1
                    ch_details.append(f"物件:{obj}")

            # 检查地点关联
            for loc in segment_keywords['locations']:
                if loc in content and len(loc) >= 2:
                    ch_connections += 0.5  # 地点权重稍低
                    ch_details.append(f"地点:{loc}")

            # 检查情感关联
            for emotion in segment_keywords['emotions']:
                if emotion in content:
                    ch_connections += 0.5
                    ch_details.append(f"情感:{emotion}")

            # 检查动作关联
            for action in segment_keywords['actions']:
                if action in content:
                    ch_connections += 1
                    ch_details.append(f"动作:{action}")

            if ch_connections > 0:
                total_connections += ch_connections
                details.append(f"ch{ch_num:03d}: {int(ch_connections)}点")

        return int(total_connections), details

    def split_segments(self, content: str, segment_size: int = 200) -> List[Tuple[str, int]]:
        """
        将章节内容分割成段落

        Args:
            content: 章节内容
            segment_size: 每段字数

        Returns:
            list of (segment_text, char_count) tuples
        """
        # 按段落分割（以---或空行）
        raw_segments = re.split(r'\n---\n|\n\n+', content)
        segments = []

        current_segment = ""
        for raw_seg in raw_segments:
            if len(raw_seg) < 50:  # 太短的跳过
                continue
            current_segment += raw_seg + "\n"
            if len(current_segment) >= segment_size:
                segments.append((current_segment.strip(), len(current_segment)))
                current_segment = ""

        if current_segment.strip():
            segments.append((current_segment.strip(), len(current_segment)))

        return segments

    def get_adaptive_threshold(self, segment_char_count: int, chapter_num: int) -> int:
        """
        根据段落长度和章节位置计算自适应阈值

        规则：
        - 短段落（<100字）：阈值降低至5点
        - 中等段落（100-200字）：阈值7点
        - 长段落（>200字）：阈值10点
        - 章节开头（ch001-ch010）：阈值降低2点
        - 章节末尾（最后10章）：阈值降低2点
        """
        base_threshold = self.min_connections

        # 根据段落长度调整
        if segment_char_count < 100:
            threshold = 5
        elif segment_char_count < 150:
            threshold = 7
        else:
            threshold = base_threshold

        # 根据章节位置调整
        if chapter_num <= 10 or chapter_num >= 350:
            threshold = max(3, threshold - 3)
        elif chapter_num <= 20:
            threshold = max(4, threshold - 2)

        return threshold

    def check_chapter(self, chapter_num: int) -> Dict:
        """
        检查单个章节的所有段落

        Returns:
            dict with check results
        """
        content = self.load_chapter(chapter_num)
        if not content:
            return {'chapter': chapter_num, 'segments': [], 'passed': True}

        # 跳过标题（markdown格式：# 第X章 标题）
        lines = content.split('\n')
        body_start = 0
        for i, line in enumerate(lines):
            # 跳过Markdown标题（以#开头）和空的章节标记行
            if i == 0 and line.startswith('#'):
                body_start = 1
                continue
            if i <= 1 and line.startswith('**第'):
                body_start = i + 1
                continue
            # 跳过"第一卷 完"等标记
            if '完**' in line or '第卷' in line:
                body_start = i + 1
                continue
            # 遇到实际正文就停止
            if len(line) > 20 and not line.startswith('#'):
                body_start = i
                break

        body_content = '\n'.join(lines[body_start:])

        segments = self.split_segments(body_content)
        results = []

        for seg_text, char_count in segments:
            keywords = self.extract_keywords(seg_text)

            # 确定检索窗口
            start_ch = max(1, chapter_num - self.window)
            end_ch = min(360, chapter_num + self.window)

            before_chapters = list(range(start_ch, chapter_num))
            after_chapters = list(range(chapter_num + 1, end_ch + 1))

            # 计算关联点
            before_conn, before_details = self.calculate_connections(keywords, before_chapters)
            after_conn, after_details = self.calculate_connections(keywords, after_chapters)

            total_conn = before_conn + after_conn
            all_details = before_details + after_details

            # 使用自适应阈值
            threshold = self.get_adaptive_threshold(char_count, chapter_num)
            passed = total_conn >= threshold

            results.append({
                'text_preview': seg_text[:50] + "..." if len(seg_text) > 50 else seg_text,
                'char_count': char_count,
                'connections': total_conn,
                'threshold': threshold,
                'before_connections': before_conn,
                'after_connections': after_conn,
                'details': all_details[:5],  # 只显示前5个详情
                'passed': passed
            })

        return {
            'chapter': chapter_num,
            'title': lines[0] if lines else '',
            'segments': results,
            'passed': all(r['passed'] for r in results),
            'total_segments': len(results),
            'passed_segments': sum(1 for r in results if r['passed'])
        }

    def check_all(self, start_ch: int = 1, end_ch: int = 360) -> Dict:
        """
        检查所有章节

        Returns:
            dict with all results
        """
        all_results = []
        failed_chapters = []

        for ch_num in range(start_ch, end_ch + 1):
            result = self.check_chapter(ch_num)
            all_results.append(result)
            if not result.get('passed', True):
                failed_chapters.append(ch_num)

        # 过滤掉无total_segments的结果（如空章节）
        valid_results = [r for r in all_results if 'total_segments' in r]

        # 汇总统计
        total_segments = sum(r['total_segments'] for r in valid_results)
        passed_segments = sum(r['passed_segments'] for r in valid_results)

        return {
            'checked_chapters': end_ch - start_ch + 1,
            'total_segments': total_segments,
            'passed_segments': passed_segments,
            'failed_segments': total_segments - passed_segments,
            'pass_rate': f"{passed_segments / total_segments * 100:.1f}%" if total_segments > 0 else "0%",
            'failed_chapters': failed_chapters,
            'results': all_results
        }


def report_results(results: Dict, output_file: str = None) -> str:
    """生成检查报告"""
    lines = []
    lines.append("=" * 70)
    lines.append("情节关联度检查报告")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"检查章节: {results['checked_chapters']} 章")
    lines.append(f"总段落数: {results['total_segments']}")
    lines.append(f"通过段落: {results['passed_segments']}")
    lines.append(f"未通过段落: {results['failed_segments']}")
    lines.append(f"通过率: {results['pass_rate']}")
    lines.append("")

    if results['failed_chapters']:
        lines.append(f"未通过章节: {results['failed_chapters'][:20]}")
        if len(results['failed_chapters']) > 20:
            lines.append(f"  ... 还有 {len(results['failed_chapters']) - 20} 个")

        lines.append("")
        lines.append("--- 未通过章节详情 ---")

        for ch_num in results['failed_chapters'][:10]:
            ch_result = next((r for r in results['results'] if r['chapter'] == ch_num), None)
            if ch_result:
                lines.append(f"\nch{ch_num:03d}: {ch_result['title']}")
                for seg in ch_result['segments']:
                    if not seg['passed']:
                        threshold = seg.get('threshold', 10)
                        lines.append(f"  段落({seg['char_count']}字): 关联点{seg['connections']} < {threshold}")
                        if seg['details']:
                            lines.append(f"    关联内容: {', '.join(seg['details'][:3])}")

    report = "\n".join(lines)
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='情节关联度检查')
    parser.add_argument('chapters_dir', help='章节目录路径')
    parser.add_argument('--start', type=int, default=1, help='起始章节')
    parser.add_argument('--end', type=int, default=360, help='结束章节')
    parser.add_argument('--window', type=int, default=5, help='检索窗口（前后章节数）')
    parser.add_argument('--threshold', type=int, default=10, help='最低关联点数')
    parser.add_argument('--output', '-o', help='输出报告路径')
    args = parser.parse_args()

    checker = SegmentRelevanceChecker(args.chapters_dir, args.window, args.threshold)
    results = checker.check_all(args.start, args.end)
    report = report_results(results, args.output)
    print(report)

    sys.exit(0 if results['failed_segments'] == 0 else 1)
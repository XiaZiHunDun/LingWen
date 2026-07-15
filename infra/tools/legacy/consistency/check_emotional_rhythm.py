#!/usr/bin/env python3
"""
情感节奏健康度检查器
检测章节内的情绪波动分布是否合理
"""
import os
import re
import sys
from collections import defaultdict
from typing import Dict, List, Set, Tuple


class EmotionalRhythmChecker:
    """情感节奏健康度检查器"""

    # 情绪词典（正向/负向/中性）
    EMOTION_WORDS = {
        # 正向情绪（高能量）
        'high_positive': [
            '喜悦', '欢乐', '愉快', '开心', '快乐', '幸福', '温暖', '感动',
            '兴奋', '激动', '振奋', '热血', '沸腾', '燃烧', '炽热',
            '希望', '期待', '憧憬', '向往', '信心', '坚定', '勇敢',
            '爱', '喜爱', '喜欢', '爱慕', '心动', '温柔', '甜蜜',
            '胜利', '成功', '突破', '超越', '辉煌', '荣耀',
        ],
        # 正向情绪（低能量）
        'low_positive': [
            '平静', '安宁', '安心', '放松', '舒缓', '轻松', '舒适',
            '满足', '满意', '惬意', '安然', '淡定', '从容',
            '欣慰', '暖心', '窝心', '温馨',
        ],
        # 负向情绪（高能量）
        'high_negative': [
            '愤怒', '愤恨', '怨毒', '怨恨', '恼怒', '怒火', '暴怒',
            '恐惧', '恐怖', '惊惧', '害怕', '畏惧', '惶恐', '惊恐',
            '绝望', '绝望', '崩溃', '崩溃边缘', '心碎', '破碎',
            '悲痛', '悲伤', '哀痛', '痛苦', '痛苦', '煎熬',
            '疯狂', '癫狂', '失控', '暴走',
        ],
        # 负向情绪（低能量）
        'low_negative': [
            '悲伤', '哀伤', '忧郁', '郁闷', '消沉', '低落',
            '孤独', '寂寞', '空虚', '茫然', '迷茫', '迷茫',
            '无奈', '无力', '疲惫', '疲倦', '倦怠',
            '沉默', '寂静', '冰冷', '冷漠', '冷淡', '疏离',
            '绝望', '悲观', '消极', '阴郁',
        ],
        # 中性/过渡词
        'neutral': [
            '思考', '回忆', '回想', '想起', '记得',
            '观察', '注视', '凝视', '打量', '审视',
            '等待', '守候', '期盼',
            '前进', '前行', '行进', '行走',
        ]
    }

    # 情绪突变标记（可能表示节奏问题）
    EMOTION_SHIFTS = [
        '突然', '骤然', '陡然', '猛然', '倏地', '霎时',
        '没想到', '万万没想到', '出乎意料', '意想不到',
        '然而', '但是', '可是', '只是', '谁知',
    ]

    def __init__(self, chapters_dir: str, segment_size: int = 500):
        """
        Args:
            chapters_dir: 章节目录
            segment_size: 每段字数（用于分割章节）
        """
        self.chapters_dir = chapters_dir
        self.segment_size = segment_size

    def load_chapter(self, chapter_num: int) -> str:
        """加载章节内容"""
        fname = f"ch{chapter_num:03d}.md"
        fpath = os.path.join(self.chapters_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def count_emotions(self, text: str) -> Dict[str, int]:
        """统计文本中的情绪词"""
        counts = {
            'high_positive': 0,
            'low_positive': 0,
            'high_negative': 0,
            'low_negative': 0,
            'neutral': 0,
            'total': 0
        }

        for category, words in self.EMOTION_WORDS.items():
            for word in words:
                counts[category] += text.count(word)
                counts['total'] += text.count(word)

        return counts

    def calculate_emotion_balance(self, counts: Dict[str, int]) -> Dict:
        """
        计算情绪平衡度

        Returns:
            情绪分析结果
        """
        total = counts['total']
        if total == 0:
            return {'balance': 0, 'type': 'FLAT', 'intensity': 0}

        # 计算正负比
        positive = counts['high_positive'] + counts['low_positive']
        negative = counts['high_negative'] + counts['low_negative']

        if negative == 0:
            ratio = positive / max(1, positive)  # 纯正向
        elif positive == 0:
            ratio = -negative / max(1, negative)  # 纯负向
        else:
            ratio = (positive - negative) / (positive + negative)  # -1到1

        # 计算强度
        intensity = counts['high_positive'] + counts['high_negative'] + counts['low_positive'] * 0.5 + counts['low_negative'] * 0.5

        # 判断情绪类型
        if abs(ratio) < 0.2 and intensity < 5:
            emotion_type = 'FLAT'  # 平flat
        elif ratio > 0.3:
            emotion_type = 'POSITIVE'
        elif ratio < -0.3:
            emotion_type = 'NEGATIVE'
        else:
            emotion_type = 'MIXED'

        return {
            'balance': ratio,  # -1到1，正数偏正向，负数偏负向
            'type': emotion_type,
            'intensity': intensity,
            'positive': positive,
            'negative': negative
        }

    def detect_emotion_shifts(self, text: str) -> List[Dict]:
        """检测情绪突变点"""
        shifts = []
        lines = text.split('\n')

        for i, line in enumerate(lines):
            for shift_word in self.EMOTION_SHIFTS:
                if shift_word in line:
                    # 检查前后情绪是否突变
                    before_text = '\n'.join(lines[max(0, i-5):i])
                    after_text = '\n'.join(lines[i+1:min(len(lines), i+6)])

                    before_counts = self.count_emotions(before_text)
                    after_counts = self.count_emotions(after_text)

                    before_bal = self.calculate_emotion_balance(before_counts)['balance']
                    after_bal = self.calculate_emotion_balance(after_counts)['balance']

                    shift_magnitude = abs(after_bal - before_bal)

                    if shift_magnitude > 0.5:  # 显著的情绪突变
                        shifts.append({
                            'line': i + 1,
                            'trigger': shift_word,
                            'magnitude': shift_magnitude,
                            'before': before_bal,
                            'after': after_bal
                        })
                    break

        return shifts

    def split_segments(self, content: str) -> List[Tuple[str, int]]:
        """将章节分割成段落"""
        # 跳过标题
        lines = content.split('\n')
        body_start = 0
        for i, line in enumerate(lines):
            if i == 0 and line.startswith('#'):
                body_start = 1
                continue
            if '**本章完**' in line:
                body_start = i
                break

        body = '\n'.join(lines[body_start:])

        # 按段落分割
        raw_segments = re.split(r'\n---\n|\n\n+', body)
        segments = []

        current = ""
        for raw_seg in raw_segments:
            if len(raw_seg) < 30:
                continue
            current += raw_seg + "\n"
            if len(current) >= self.segment_size:
                segments.append((current.strip(), len(current)))
                current = ""

        if current.strip():
            segments.append((current.strip(), len(current)))

        return segments

    def check_chapter(self, chapter_num: int) -> Dict:
        """检查单个章节的情感节奏"""
        content = self.load_chapter(chapter_num)
        if not content:
            return {'chapter': chapter_num, 'passed': True, 'issues': []}

        segments = self.split_segments(content)
        segment_results = []

        issues = []
        prev_balance = None

        for seg_text, char_count in segments:
            counts = self.count_emotions(seg_text)
            emotion = self.calculate_emotion_balance(counts)
            shifts = self.detect_emotion_shifts(seg_text)

            result = {
                'char_count': char_count,
                'counts': counts,
                'balance': emotion['balance'],
                'type': emotion['type'],
                'intensity': emotion['intensity'],
                'shifts': len(shifts),
                'issues': []
            }

            # 检查情绪类型是否变化太大
            if prev_balance is not None:
                change = abs(emotion['balance'] - prev_balance)
                if change > 0.8:  # 情绪突变过大
                    result['issues'].append({
                        'type': 'SUDDEN_SHIFT',
                        'desc': f'情绪突变幅度过大: {change:.2f}',
                        'severity': 'MEDIUM'
                    })

            prev_balance = emotion['balance']

            # 检查情绪过于单调
            if emotion['type'] == 'FLAT':
                result['issues'].append({
                    'type': 'FLAT_EMOTION',
                    'desc': '情绪过于平淡，缺乏起伏',
                    'severity': 'LOW'
                })

            # 检查情绪过于极端（全程高能）
            if counts['high_positive'] + counts['high_negative'] > 10 and emotion['type'] != 'FLAT':
                result['issues'].append({
                    'type': 'OVERLY_INTENSE',
                    'desc': '全程高能，情绪无喘息',
                    'severity': 'LOW'
                })

            segment_results.append(result)

        # 章节级别问题
        all_balances = [s['balance'] for s in segment_results]
        if len(all_balances) >= 2:
            balance_variance = sum((b - sum(all_balances)/len(all_balances))**2 for b in all_balances) / len(all_balances)
            if balance_variance < 0.01:  # 方差过小
                issues.append({
                    'type': 'MONOTONOUS_RHYTHM',
                    'desc': '整章情绪无起伏，节奏单调',
                    'severity': 'MEDIUM'
                })

        # 统计
        total_shifts = sum(s['shifts'] for s in segment_results)

        return {
            'chapter': chapter_num,
            'passed': len([i for i in issues if i['severity'] == 'HIGH']) == 0,
            'issues': issues,
            'segment_count': len(segment_results),
            'total_intensity': sum(s['intensity'] for s in segment_results),
            'total_shifts': total_shifts,
            'segments': segment_results
        }

    def check_all(self, start_ch: int = 1, end_ch: int = 360) -> Dict:
        """检查所有章节的情感节奏"""
        all_results = []
        failed_chapters = []

        for ch_num in range(start_ch, end_ch + 1):
            result = self.check_chapter(ch_num)
            all_results.append(result)
            if not result['passed']:
                failed_chapters.append(ch_num)

        # 过滤掉无segments的结果（如空章节）
        valid_results = [r for r in all_results if 'segments' in r]

        # 统计
        total_issues = sum(
            len(r['issues']) + sum(len(s['issues']) for s in r['segments'])
            for r in valid_results
        )
        high_issues = sum(
            len([i for i in r['issues'] if i['severity'] == 'HIGH']) +
            sum(len([i for i in s['issues'] if i['severity'] == 'HIGH']) for s in r['segments'])
            for r in valid_results
        )

        return {
            'checked_chapters': end_ch - start_ch + 1,
            'total_issues': total_issues,
            'high_severity_issues': high_issues,
            'failed_chapters': failed_chapters,
            'results': all_results
        }


def report_results(results: Dict, output_file: str = None) -> str:
    """生成检查报告"""
    lines = []
    lines.append("=" * 70)
    lines.append("情感节奏健康度检查报告")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"检查章节: {results['checked_chapters']} 章")
    lines.append(f"发现问题: {results['total_issues']} 处")
    lines.append(f"高严重度问题: {results['high_severity_issues']} 处")
    lines.append(f"未通过章节: {len(results['failed_chapters'])} 个")

    # 高严重度问题
    high_issue_chapters = []
    for r in results['results']:
        has_medium_issue = any(i['severity'] in ('HIGH', 'MEDIUM') for i in r['issues'])
        has_segment_issue = any(
            any(i['severity'] in ('HIGH', 'MEDIUM') for i in s['issues'])
            for s in r['segments']
        )
        if has_medium_issue or has_segment_issue:
            high_issue_chapters.append(r)

    if high_issue_chapters:
        lines.append("")
        lines.append("--- 中高严重度问题章节 ---")
        for r in high_issue_chapters[:10]:
            lines.append(f"\nch{r['chapter']:03d} (强度:{r['total_intensity']:.0f}, 突变:{r['total_shifts']}):")
            for issue in r['issues']:
                if issue['severity'] in ('HIGH', 'MEDIUM'):
                    lines.append(f"  [{issue['type']}] {issue['desc']}")

    report = "\n".join(lines)
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='情感节奏健康度检查')
    parser.add_argument('chapters_dir', help='章节目录路径')
    parser.add_argument('--start', type=int, default=1, help='起始章节')
    parser.add_argument('--end', type=int, default=360, help='结束章节')
    parser.add_argument('--output', '-o', help='输出报告路径')
    args = parser.parse_args()

    checker = EmotionalRhythmChecker(args.chapters_dir)
    results = checker.check_all(args.start, args.end)
    report = report_results(results, args.output)
    print(report)

    sys.exit(0 if results['high_severity_issues'] == 0 else 1)

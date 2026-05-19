#!/usr/bin/env python3
"""
对话风格一致性检查器
检测角色对话是否符合其语音特征，识别"串词"问题
"""
import os
import re
import sys
from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict


class DialogueStyleChecker:
    """对话风格一致性检查器"""

    # 角色语音特征库
    CHARACTER_VOICES = {
        '林夜': {
            'keywords': ['守护', '必须', '只有', '我们', '一起', '面对', '保护'],
            'speech_patterns': [
                r'^.{0,6}说[：:]',  # "林夜说："
                r'^".{0,30}"',  # 直接引语开头
            ],
            'forbidden_words': [],  # 不该出现的词
            'typical_length': (5, 30),  # 字数范围
            'tone': '坚定型',  # 角色语气类型
        },
        '苏琳': {
            'keywords': ['我知道', '不管', '相信', '陪伴', '身边', '一起'],
            'speech_patterns': [
                r'^.{0,6}说[：:]',
                r'^".{0,30}"',
            ],
            'forbidden_words': [],
            'typical_length': (3, 25),
            'tone': '温柔型',
        },
        '小九': {
            'keywords': ['主人', '保护', '跟随', '一定', '会'],
            'speech_patterns': [
                r'^.{0,6}说[：:]',
                r'^".{0,30}"',
            ],
            'forbidden_words': [],
            'typical_length': (2, 20),
            'tone': '灵动型',
        },
        '铁蛋': {
            'keywords': ['兄弟', '搞定', '走', '上', '干'],
            'speech_patterns': [
                r'^.{0,6}说[：:]',
            ],
            'forbidden_words': [],
            'typical_length': (2, 15),
            'tone': '豪爽型',
        },
        '星月': {
            'keywords': ['命运', '安排', '考验', '接受', '面对'],
            'speech_patterns': [
                r'^.{0,6}说[：:]',
            ],
            'forbidden_words': [],
            'typical_length': (5, 30),
            'tone': '宿命型',
        },
        '莫言': {
            'keywords': ['有趣', '有意思', '看看', '怎么样', '尝试'],
            'speech_patterns': [
                r'^.{0,6}说[：:]',
            ],
            'forbidden_words': [],
            'typical_length': (3, 20),
            'tone': '洒脱型',
        },
        '星瑶': {
            'keywords': ['姐姐', '哥哥', '帮忙', '保护', '我们'],
            'speech_patterns': [
                r'^.{0,6}说[：:]',
            ],
            'forbidden_words': [],
            'typical_length': (2, 20),
            'tone': '乖巧型',
        },
        '墨白': {
            'keywords': ['危险', '小心', '注意', '不对', '先'],
            'speech_patterns': [
                r'^.{0,6}说[：:]',
            ],
            'forbidden_words': [],
            'typical_length': (3, 25),
            'tone': '谨慎型',
        },
        '暗皇': {
            'keywords': ['毁灭', '虚无', '归于', '一切', '终极'],
            'speech_patterns': [
                r'^.{0,6}说[：:]',
            ],
            'forbidden_words': [],
            'typical_length': (5, 35),
            'tone': '威严型',
        },
    }

    # 语气词列表（用于检测语气特征）
    MOOD_WORDS = {
        'soft': ['吧', '呢', '啊', '呀', '嘛', '哦', '噢', '哈', '哇'],
        'firm': ['！', '。', '必须', '一定', '绝对'],
        'question': ['吗', '呢', '怎么', '什么', '为何', '为什么'],
        'casual': ['哈', '嘿', '哟', '嗯', '喔'],
    }

    def __init__(self, chapters_dir: str):
        """
        Args:
            chapters_dir: 章节目录
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

    def extract_dialogues(self, content: str) -> List[Dict]:
        """
        提取对话内容

        Returns:
            list of {speaker, text, line_num}
        """
        dialogues = []
        lines = content.split('\n')

        # 获取已知的角色名列表
        known_chars = list(self.CHARACTER_VOICES.keys())

        for line_num, line in enumerate(lines):
            # 跳过空行和标题
            if not line.strip() or line.startswith('#'):
                continue

            line = line.strip()

            # 匹配已知角色 + 引号对话：林夜说："xxx"
            for char in known_chars:
                pattern = rf'^{re.escape(char)}\s*说[：:]"([^"]+)"'
                match = re.match(pattern, line)
                if match:
                    text = match.group(1).strip()
                    dialogues.append({
                        'speaker': char,
                        'text': text,
                        'line': line_num + 1,
                        'source': 'quote'
                    })
                    break

            # 匹配引号包裹的直接引语（无角色前缀）
            # 例如："不管发生什么，"母亲最后看了他一眼，"都不要出声。不要动。"
            if '"' in line and len(line) < 150:
                # 找所有引号内的内容
                quotes = re.findall(r'"([^"]+)"', line)
                if quotes:
                    # 尝试判断说话者
                    # 模式：xxx说："xxx" 或者 xxx道："xxx"
                    for char in known_chars:
                        if char in line:
                            # 取最后一条引语作为对话内容
                            dialogues.append({
                                'speaker': char,
                                'text': quotes[-1],
                                'line': line_num + 1,
                                'source': 'inline_quote'
                            })
                            break

        return dialogues

    def analyze_speech_style(self, text: str) -> Dict:
        """
        分析单条话语的风格特征

        Returns:
            dict with style analysis
        """
        analysis = {
            'length': len(text),
            'has_question': any(w in text for w in self.MOOD_WORDS['question']),
            'has_soft_mood': any(w in text for w in self.MOOD_WORDS['soft']),
            'has_firm_mood': any(w in text for w in self.MOOD_WORDS['firm']),
            'has_casual_mood': any(w in text for w in self.MOOD_WORDS['casual']),
            'keywords_found': [],
            'forbidden_found': [],
        }

        # 检查是否匹配角色的特征关键词
        for char, voice in self.CHARACTER_VOICES.items():
            found = [kw for kw in voice['keywords'] if kw in text]
            analysis['keywords_found'].extend(found)

        return analysis

    def detect_style_mismatch(self, speaker: str, text: str, analysis: Dict) -> List[Dict]:
        """
        检测话语是否符合角色风格

        Returns:
            list of issues
        """
        issues = []

        if speaker not in self.CHARACTER_VOICES:
            return issues

        voice = self.CHARACTER_VOICES[speaker]

        # 检查字数是否超出典型范围
        min_len, max_len = voice['typical_length']
        if analysis['length'] < min_len * 0.5:  # 严重偏短
            issues.append({
                'type': 'UNUSUALLY_SHORT',
                'desc': f'{speaker}发言字数极短({analysis["length"]}字)，可能非本人说话',
                'severity': 'MEDIUM'
            })
        elif analysis['length'] > max_len * 2:  # 严重偏长
            issues.append({
                'type': 'UNUSUALLY_LONG',
                'desc': f'{speaker}发言字数过长({analysis["length"]}字)，可能"串词"',
                'severity': 'MEDIUM'
            })

        # 检查禁止词
        for fw in voice.get('forbidden_words', []):
            if fw in text:
                issues.append({
                    'type': 'FORBIDDEN_WORD',
                    'desc': f'{speaker}使用了禁止词"{fw}"',
                    'severity': 'HIGH'
                })

        # 检查语气是否匹配角色特征
        # 例如：暗皇不应该用太柔和的语气
        tone = voice.get('tone', '')
        if tone == '威严型' and analysis['has_soft_mood'] and analysis['length'] < 10:
            issues.append({
                'type': 'TONE_MISMATCH',
                'desc': f'{speaker}({tone})使用了柔和语气，可能"串词"',
                'severity': 'LOW'
            })

        return issues

    def check_chapter(self, chapter_num: int) -> Dict:
        """检查单个章节的对话风格"""
        content = self.load_chapter(chapter_num)
        if not content:
            return {'chapter': chapter_num, 'passed': True, 'issues': []}

        dialogues = self.extract_dialogues(content)

        all_issues = []
        dialogue_results = []

        for dlg in dialogues:
            analysis = self.analyze_speech_style(dlg['text'])
            issues = self.detect_style_mismatch(dlg['speaker'], dlg['text'], analysis)

            dialogue_results.append({
                'speaker': dlg['speaker'],
                'text_preview': dlg['text'][:30] + '...' if len(dlg['text']) > 30 else dlg['text'],
                'line': dlg['line'],
                'analysis': analysis,
                'issues': issues
            })

            all_issues.extend(issues)

        # 统计每个角色发言次数
        speaker_counts = defaultdict(int)
        for dlg in dialogues:
            speaker_counts[dlg['speaker']] += 1

        return {
            'chapter': chapter_num,
            'passed': len([i for i in all_issues if i['severity'] == 'HIGH']) == 0,
            'issues': all_issues,
            'dialogue_count': len(dialogues),
            'speaker_counts': dict(speaker_counts),
            'dialogues': dialogue_results
        }

    def check_all(self, start_ch: int = 1, end_ch: int = 360) -> Dict:
        """检查所有章节的对话风格"""
        all_results = []
        failed_chapters = []

        for ch_num in range(start_ch, end_ch + 1):
            result = self.check_chapter(ch_num)
            all_results.append(result)
            if not result['passed']:
                failed_chapters.append(ch_num)

        # 统计
        total_issues = sum(len(r['issues']) for r in all_results)
        high_issues = sum(len([i for i in r['issues'] if i['severity'] == 'HIGH']) for r in all_results)
        total_dialogues = sum(r['dialogue_count'] for r in all_results)

        return {
            'checked_chapters': end_ch - start_ch + 1,
            'total_dialogues': total_dialogues,
            'total_issues': total_issues,
            'high_severity_issues': high_issues,
            'failed_chapters': failed_chapters,
            'results': all_results
        }


def report_results(results: Dict, output_file: str = None) -> str:
    """生成检查报告"""
    lines = []
    lines.append("=" * 70)
    lines.append("对话风格一致性检查报告")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"检查章节: {results['checked_chapters']} 章")
    lines.append(f"总对话数: {results['total_dialogues']} 条")
    lines.append(f"发现问题: {results['total_issues']} 处")
    lines.append(f"高严重度问题: {results['high_severity_issues']} 处")
    lines.append(f"未通过章节: {len(results['failed_chapters'])} 个")

    # 高严重度问题
    high_issue_chapters = [r for r in results['results']
                           if any(i['severity'] in ('HIGH', 'MEDIUM') for i in r['issues'])]

    if high_issue_chapters:
        lines.append("")
        lines.append("--- 中高严重度问题章节 ---")
        for r in high_issue_chapters[:10]:
            lines.append(f"\nch{r['chapter']:03d} ({r['dialogue_count']}条对话):")
            for issue in r['issues']:
                if issue['severity'] in ('HIGH', 'MEDIUM'):
                    lines.append(f"  [{issue['type']}] {issue['desc']}")

    # 对话统计
    if results['total_dialogues'] > 0:
        lines.append("")
        lines.append("--- 对话统计 ---")
        # 汇总各角色发言次数
        all_speakers = defaultdict(int)
        for r in results['results']:
            for speaker, count in r['speaker_counts'].items():
                all_speakers[speaker] += count

        top_speakers = sorted(all_speakers.items(), key=lambda x: -x[1])[:10]
        for speaker, count in top_speakers:
            lines.append(f"  {speaker}: {count}条")

    report = "\n".join(lines)
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='对话风格一致性检查')
    parser.add_argument('chapters_dir', help='章节目录路径')
    parser.add_argument('--start', type=int, default=1, help='起始章节')
    parser.add_argument('--end', type=int, default=360, help='结束章节')
    parser.add_argument('--output', '-o', help='输出报告路径')
    args = parser.parse_args()

    checker = DialogueStyleChecker(args.chapters_dir)
    results = checker.check_all(args.start, args.end)
    report = report_results(results, args.output)
    print(report)

    sys.exit(0 if results['high_severity_issues'] == 0 else 1)
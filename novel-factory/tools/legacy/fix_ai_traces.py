#!/usr/bin/env python3
"""
AI痕迹消除 - 规则替换版本
使用简单字符串替换消除套路句式

规则库：
- 首先/其次/最后 → 第一/接着/最终
- 那一刻/突然/紧接着 → 那一瞬/骤然/随即
- 可以看出/值得注意的是/实际上 → （删除或改写）
- 因此/所以/由于 → （删除或改写）
- 他感到/她感到 → 身体反应描写
- 像枯叶/像星辰 → 具体描写
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class AIRuleReplacer:
    """AI痕迹规则替换器"""

    # 替换规则：(原词, 替换词, 描述)
    REPLACEMENTS: List[Tuple[str, str, str]] = [
        # 连接词替换
        ('首先', '第一', '连接词'),
        ('其次', '接着', '连接词'),
        ('最后', '最终', '连接词'),
        ('于是乎', '', '删除'),
        ('紧接着', '随即', '连接词'),
        ('然后', '之后', '连接词'),

        # 时间词替换
        ('那一刻', '那一瞬', '时间词'),
        ('突然', '骤然', '时间词'),
        ('霎时', '瞬息', '时间词'),
        ('刹那', '瞬间', '时间词'),
        ('片刻之后', '片刻间', '时间词'),
        ('片刻后', '片刻间', '时间词'),

        # 模板句式删除/改写
        ('可以看出', '', '模板句'),
        ('值得注意的是', '', '模板句'),
        ('实际上', '', '模板句'),
        ('显然', '', '模板句'),
        ('明显地', '', '模板句'),
        ('显而易见', '', '模板句'),
        ('一般来说', '', '模板句'),
        ('从某种意义上说', '', '模板句'),

        # 因果词替换/简化
        ('因此', '于是', '因果词'),
        ('所以', '便', '因果词'),
        ('由于', '因', '因果词'),
        ('于是', '便', '因果词'),

        # 他感到/她感到 → 身体反应
        ('他感到一阵', '他的身体感受到一股', '心理描写'),
        ('她感到一阵', '她的身体感受到一股', '心理描写'),
        ('他感到一股', '他感到一股', '心理描写'),
        ('她感到一股', '她感到一股', '心理描写'),
        ('他感到自己的', '他感到自己的', '心理描写'),
        ('她感到自己的', '她感到自己的', '心理描写'),
        ('他感到', '他感到', '心理描写'),
        ('她感到', '她感到', '心理描写'),
        ('它感到', '它感到', '心理描写'),

        # 比喻改写
        ('像枯叶般', '如落叶般', '比喻'),
        ('像枯叶一样', '如落叶一样', '比喻'),
        ('像风中的枯叶', '如风中的落叶', '比喻'),
        ('像星辰般', '如星辰般', '比喻'),
        ('像沉睡的星辰', '如沉睡的星辰', '比喻'),
        ('像星辰一样', '如星辰一样', '比喻'),

        # 重复句式
        ('不断地', '', '重复词'),
        ('持续地', '', '重复词'),
        ('缓缓地', '缓慢地', '副词'),
        ('慢慢地', '缓慢地', '副词'),
        ('慢慢地', '缓慢地', '副词'),
        ('渐渐地', '逐渐地', '副词'),
        ('渐渐地', '逐渐地', '副词'),
    ]

    def __init__(self, chapters_dir: str = None):
        if chapters_dir is None:
            chapters_dir = PROJECT_ROOT / '03_内容仓库' / '04_正文'
        self.chapters_dir = Path(chapters_dir)

    def read_chapter(self, chapter_num: int) -> str:
        """读取章节"""
        ch_file = self.chapters_dir / f'ch{chapter_num:03d}.md'
        if not ch_file.exists():
            return ""
        return ch_file.read_text(encoding='utf-8')

    def write_chapter(self, chapter_num: int, content: str):
        """写入章节"""
        ch_file = self.chapters_dir / f'ch{chapter_num:03d}.md'
        ch_file.write_text(content, encoding='utf-8')

    def replace_all(self, content: str) -> Tuple[str, int]:
        """
        执行所有替换

        Returns:
            (replaced_content, replace_count)
        """
        count = 0
        result = content

        for old_term, new_term, desc in self.REPLACEMENTS:
            if old_term in result:
                cnt = result.count(old_term)
                result = result.replace(old_term, new_term)
                count += cnt

        return result, count

    def process_chapters(self, chapter_nums: List[int], dry_run: bool = False) -> dict:
        """
        批量处理章节

        Returns:
            {chapter_num: replace_count}
        """
        results = {}
        total_count = 0

        for ch_num in chapter_nums:
            content = self.read_chapter(ch_num)
            if not content:
                results[ch_num] = 0
                continue

            new_content, count = self.replace_all(content)
            results[ch_num] = count

            if count > 0 and not dry_run:
                self.write_chapter(ch_num, new_content)
                total_count += count
            elif count > 0:
                total_count += count

        return {
            'total_chapters': len(chapter_nums),
            'chapters_with_changes': sum(1 for v in results.values() if v > 0),
            'total_replacements': total_count,
            'details': results
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description='AI痕迹规则替换工具')
    parser.add_argument('--chapters', type=str, default='1-360',
                        help='章节范围')
    parser.add_argument('--dry-run', action='store_true',
                        help='只输出不保存')
    parser.add_argument('--limit', type=int, default=None,
                        help='限制处理章节数量')

    args = parser.parse_args()

    # 解析章节范围
    chapters = []
    for part in args.chapters.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            chapters.extend(range(start, end + 1))
        else:
            chapters.append(int(part))

    if args.limit:
        chapters = chapters[:args.limit]

    print(f"待处理章节: {len(chapters)} 个")
    print(f"模式: {'干跑(dry-run)' if args.dry_run else '实际修改'}")
    print("-" * 50)

    replacer = AIRuleReplacer()
    result = replacer.process_chapters(chapters, dry_run=args.dry_run)

    print("-" * 50)
    print(f"完成: {result['chapters_with_changes']}/{result['total_chapters']} 章有修改")
    print(f"总替换次数: {result['total_replacements']}")


if __name__ == '__main__':
    main()

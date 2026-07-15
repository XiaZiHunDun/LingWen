#!/usr/bin/env python3
"""
跨章节逻辑一致性检查工具

用法:
    python test_cross_chapter_checker.py              # 检查前30章
    python test_cross_chapter_checker.py --chapters 1-10  # 指定范围
    python test_cross_chapter_checker.py --full-scan     # 全量扫描
"""

import argparse
import sys
from pathlib import Path
from typing import List, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.consistency.checkers.cross_chapter_logic_checker import CrossChapterLogicChecker


def load_chapters(chapter_dir: Path, start: int, end: int) -> List[Tuple[int, str]]:
    """加载指定范围的章节"""
    chapters = []
    for i in range(start, end + 1):
        fpath = chapter_dir / f"ch{i:03d}.md"
        if fpath.exists() and '_大纲' not in fpath.name:
            content = fpath.read_text(encoding='utf-8')
            chapters.append((i, content))
    return chapters


def main():
    parser = argparse.ArgumentParser(description="跨章节逻辑一致性检查")
    parser.add_argument('--chapters', default='1-30', help='章节范围，如 1-30')
    parser.add_argument('--full-scan', action='store_true', help='全量扫描所有章节')
    parser.add_argument('--output', default='', help='输出文件')
    args = parser.parse_args()

    # 解析章节范围
    if args.full_scan:
        start, end = 1, 360
    else:
        parts = args.chapters.split('-')
        start, end = int(parts[0]), int(parts[1])

    # 加载章节
    chapter_dir = PROJECT_ROOT / "03_内容仓库" / "04_正文"
    chapters = load_chapters(chapter_dir, start, end)
    print(f"加载章节: {start}-{end} ({len(chapters)}章)")
    print("=" * 60)

    # 执行检查
    checker = CrossChapterLogicChecker()
    issues = checker.check_with_full_scan(chapters)

    # 按章节统计
    chapter_issues = {}
    for issue in issues:
        ch = issue.location.chapter
        if ch not in chapter_issues:
            chapter_issues[ch] = []
        chapter_issues[ch].append(issue)

    # 输出结果
    print(f"\\n发现问题: {len(issues)}个")
    print("=" * 60)

    for ch in sorted(chapter_issues.keys()):
        chapter_issues_list = chapter_issues[ch]
        p0_count = sum(1 for i in chapter_issues_list if i.severity.value == "P0")
        p1_count = sum(1 for i in chapter_issues_list if i.severity.value == "P1")
        print(f"\\n第{ch}章: {len(chapter_issues_list)}个问题 (P0={p0_count}, P1={p1_count})")
        for issue in chapter_issues_list:
            print(f"  - Line {issue.location.line}: {issue.title}")
            print(f"    Evidence: {issue.evidence[:60]}...")

    # 输出到文件
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            for issue in issues:
                f.write(f"\\n=== {issue.title} ===\\n")
                f.write(f"章节: ch{issue.location.chapter}\\n")
                f.write(f"行号: {issue.location.line}\\n")
                f.write(f"严重度: {issue.severity.value}\\n")
                f.write(f"描述: {issue.description}\\n")
                f.write(f"证据: {issue.evidence}\\n")
                f.write(f"建议: {issue.suggestion}\\n")
        print(f"\\n报告已保存到: {output_path}")


if __name__ == '__main__':
    main()

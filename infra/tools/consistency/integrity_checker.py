#!/usr/bin/env python3
"""
章节内容完整性检查器

检测：结尾标记、字数下限、空章节

功能：
- check_integrity(): 检查章节完整性
- fix_integrity(): 修复缺失的**本章完**标记（支持dry_run模式）
"""
import os
import re
import sys
from typing import Optional


def check_integrity(chapters_dir: str, chapter_range: tuple[int, int] = (1, 360),
                    min_word_count: int = 500) -> list[tuple]:
    """
    检查章节内容完整性

    Args:
        chapters_dir: 章节目录
        chapter_range: 检查章节范围
        min_word_count: 最低字数要求

    Returns:
        list of (issue_type, chapter_num, file_name, message) tuples
    """
    issues = []
    start, end = chapter_range

    for i in range(start, end + 1):
        fname = f"ch{i:03d}.md"
        fpath = os.path.join(chapters_dir, fname)

        if not os.path.exists(fpath):
            issues.append(("MISSING_FILE", i, fname, "文件缺失"))
            continue

        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            issues.append(("READ_ERROR", i, fname, f"读取失败: {e}"))
            continue

        char_count = len(content)

        # 检查空文件
        if char_count < 100:
            issues.append(("EMPTY_CHAPTER", i, fname,
                f"章节内容过少({char_count}字符)"))
            continue

        # 检查"本章完"标记
        if "**本章完**" not in content and "【本章完】" not in content:
            issues.append(("MISSING_END_MARK", i, fname, "缺少**本章完**标记"))

        # 检查字数下限
        if char_count < min_word_count:
            issues.append(("LOW_WORD_COUNT", i, fname,
                f"字数{char_count}低于{min_word_count}"))

    return issues


def fix_integrity(chapters_dir: str, dry_run: bool = True,
                  min_word_count: int = 500,
                  chapter_range: tuple[int, int] = (1, 360)) -> dict:
    """
    检查并修复内容完整性问题

    Args:
        chapters_dir: 章节目录
        dry_run: True=只报告不执行，False=实际修复
        min_word_count: 最低字数要求
        chapter_range: 检查章节范围

    Returns:
        dict with fix results
    """
    results = {
        'dry_run': dry_run,
        'total_files': 0,
        'fixed_missing_end_mark': [],
        'report_low_word_count': [],
        'already_complete': [],
        'errors': [],
    }

    start, end = chapter_range
    for i in range(start, end + 1):
        fname = f"ch{i:03d}.md"
        fpath = os.path.join(chapters_dir, fname)

        if not os.path.exists(fpath):
            continue

        results['total_files'] += 1

        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            results['errors'].append((fname, f"读取失败: {e}"))
            continue

        char_count = len(content)
        issues = []

        # 检查字数
        if char_count < min_word_count:
            issues.append(('LOW_WORD_COUNT', char_count))

        # 检查"本章完"标记
        has_end_mark = '**本章完**' in content or '【本章完】' in content

        if issues or not has_end_mark:
            if not has_end_mark:
                if char_count >= min_word_count:
                    # 字数够，可以自动补充标记
                    if not dry_run:
                        # 在文件末尾添加标记
                        with open(fpath, 'w', encoding='utf-8') as f:
                            f.write(content.rstrip() + '\n\n**本章完**\n')
                    results['fixed_missing_end_mark'].append({
                        'file': fname,
                        'char_count': char_count,
                        'action': 'added' if not dry_run else 'would_add'
                    })
                else:
                    # 字数不够，无法自动修复
                    results['report_low_word_count'].append({
                        'file': fname,
                        'char_count': char_count,
                        'missing': min_word_count - char_count
                    })
        else:
            results['already_complete'].append(fname)

    return results


def report_integrity_issues(issues: list[tuple], output_file: str = None) -> str:
    """生成完整性检查报告"""
    lines = []
    lines.append("=" * 70)
    lines.append("章节内容完整性检查报告")
    lines.append("=" * 70)

    if not issues:
        lines.append("\n 所有章节内容完整")
        report = "\n".join(lines)
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
        return report

    # 按问题类型分组
    by_type = {}
    for issue in issues:
        issue_type = issue[0]
        if issue_type not in by_type:
            by_type[issue_type] = []
        by_type[issue_type].append(issue)

    lines.append(f"\n发现问题: {len(issues)} 个")

    for issue_type, items in by_type.items():
        lines.append(f"\n--- {issue_type} ({len(items)}个) ---")
        for item in items[:20]:
            lines.append(f"  {item[1]:03d}.md - {item[3]}")
        if len(items) > 20:
            lines.append(f"  ... 还有 {len(items) - 20} 个")

    report = "\n".join(lines)
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

    return report


def print_fix_results(results: dict):
    """打印修复结果"""
    print("=" * 70)
    print("章节内容完整性修复报告")
    print("=" * 70)
    print(f"总文件数: {results['total_files']}")
    print(f"内容完整: {len(results['already_complete'])} 个")
    print(f"已补充标记: {len(results['fixed_missing_end_mark'])} 个")
    print(f"字数不足（需人工）: {len(results['report_low_word_count'])} 个")
    print(f"错误: {len(results['errors'])} 个")

    if results['dry_run']:
        print("\n DRY RUN - 未实际执行修复")

    if results['fixed_missing_end_mark']:
        print("\n--- 将补充 **本章完** 标记 ---")
        for item in results['fixed_missing_end_mark'][:15]:
            action = "+" if item['action'] == 'added' else "->"
            print(f"  {action} {item['file']} (字数: {item['char_count']})")
        if len(results['fixed_missing_end_mark']) > 15:
            print(f"  ... 还有 {len(results['fixed_missing_end_mark']) - 15} 个")

    if results['report_low_word_count']:
        print("\n--- 字数不足（需人工处理）---")
        for item in results['report_low_word_count']:
            print(f"  X {item['file']}: {item['char_count']}字 (缺{item['missing']}字)")

    if results['errors']:
        print("\n--- 错误 ---")
        for fname, msg in results['errors']:
            print(f"  X {fname}: {msg}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='章节内容完整性检查/修复')
    parser.add_argument('chapters_dir', help='章节目录路径')
    parser.add_argument('--output', '-o', help='输出报告路径')
    parser.add_argument('--start', type=int, default=1, help='起始章节')
    parser.add_argument('--end', type=int, default=360, help='结束章节')
    parser.add_argument('--min-count', type=int, default=500, help='最低字数')
    parser.add_argument('--fix', action='store_true', help='执行修复（默认dry-run）')
    parser.add_argument('--execute', action='store_true', help='实际执行修复（与--fix等效）')
    args = parser.parse_args()

    dry_run = not (args.fix or args.execute)
    chapter_range = (args.start, args.end)

    if dry_run:
        issues = check_integrity(args.chapters_dir, chapter_range, args.min_count)
        report = report_integrity_issues(issues, args.output)
        print(report)
        sys.exit(0 if not issues else 1)
    else:
        results = fix_integrity(args.chapters_dir, dry_run=False,
                               min_word_count=args.min_count,
                               chapter_range=chapter_range)
        print_fix_results(results)
        if args.output:
            import json
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n报告已保存: {args.output}")
        # 字数不足需要人工，返回非零
        has_issues = len(results['report_low_word_count']) > 0
        sys.exit(0 if not has_issues else 1)

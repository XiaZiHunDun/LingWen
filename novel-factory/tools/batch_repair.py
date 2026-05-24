#!/usr/bin/env python3
"""
批量修复工具 - v9.1
基于Repairer框架的批量修复

使用方式:
    python batch_repair.py --chapters 1-120 --track worldview
    python batch_repair.py --chapters 1-360 --track ai_trace --dry-run
    python batch_repair.py --chapters 1-120 --track all
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.quality import WorldviewRepairer, AITraceRepairer
from infra.paths import ProjectPaths


class BatchRepairer:
    """批量修复器"""

    def __init__(self, paths: ProjectPaths = None):
        self.paths = paths or ProjectPaths.get()
        self.worldview_repairer = WorldviewRepairer(self.paths)
        self.ai_trace_repairer = AITraceRepairer(self.paths)

    def repair_track(self, chapter_nums: List[int], track: str, dry_run: bool = False) -> Dict[str, Any]:
        """
        执行单轨修复

        Args:
            chapter_nums: 章节编号列表
            track: 修复轨道 ('worldview', 'ai_trace', 'all')
            dry_run: 是否干跑

        Returns:
            修复结果
        """
        results = {}

        if track == 'worldview':
            repairer = self.worldview_repairer
            track_name = '世界观统一'
        elif track == 'ai_trace':
            repairer = self.ai_trace_repairer
            track_name = 'AI痕迹消除'
        elif track == 'all':
            track_name = '全量修复'
        else:
            raise ValueError(f"Unknown track: {track}")

        total_changes = 0
        modified_chapters = 0

        for ch in chapter_nums:
            if track == 'all':
                # 执行两轨
                w_result = self.worldview_repairer.repair(ch)
                a_result = self.ai_trace_repairer.repair(ch)
                changes = w_result.changes + a_result.changes
            else:
                result = repairer.repair(ch)
                changes = result.changes

            results[ch] = changes
            if changes > 0:
                modified_chapters += 1
                total_changes += changes

            if not dry_run and changes > 0:
                print(f"ch{ch:03d}: ✓ {changes}处")
            elif dry_run and changes > 0:
                print(f"ch{ch:03d}: [干跑] {changes}处")

        return {
            "track": track_name,
            "total_chapters": len(chapter_nums),
            "modified_chapters": modified_chapters,
            "total_changes": total_changes,
            "dry_run": dry_run,
            "details": results
        }

    def repair_batch(self, chapter_nums: List[int], tracks: List[str] = None,
                     dry_run: bool = False) -> Dict[str, Any]:
        """
        批量修复（多轨）

        Args:
            chapter_nums: 章节编号列表
            tracks: 修复轨道列表，默认['worldview', 'ai_trace']
            dry_run: 是否干跑

        Returns:
            修复结果
        """
        tracks = tracks or ['worldview', 'ai_trace']
        results = {}

        for track in tracks:
            print(f"\n{'=' * 50}")
            print(f"开始 {track} 修复...")
            print(f"待处理章节: {len(chapter_nums)} 个")

            track_result = self.repair_track(chapter_nums, track, dry_run)
            results[track] = track_result

            print(f"\n完成: {track_result['modified_chapters']}/{track_result['total_chapters']} 章有修改")
            print(f"总替换次数: {track_result['total_changes']}")

        return results

    def generate_summary(self, results: Dict[str, Any]) -> str:
        """生成修复汇总报告"""
        lines = [
            "=" * 60,
            "批量修复报告",
            f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
        ]

        for track, result in results.items():
            lines.append(f"\n【{result['track']}】")
            lines.append(f"  处理章节: {result['total_chapters']}")
            lines.append(f"  修改章节: {result['modified_chapters']}")
            lines.append(f"  总替换数: {result['total_changes']}")

        return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='批量修复工具')
    parser.add_argument('--chapters', type=str, default='1-120',
                        help='章节范围，如 "1-120" 或 "1,5,10"')
    parser.add_argument('--track', type=str, default='all',
                        choices=['worldview', 'ai_trace', 'all'],
                        help='修复轨道')
    parser.add_argument('--dry-run', action='store_true',
                        help='只输出不保存')
    parser.add_argument('--limit', type=int, default=None,
                        help='限制处理章节数量')
    parser.add_argument('--output', type=str, default=None,
                        help='输出JSON文件路径')

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

    print(f"待处理章节: {len(chapters)} 个 (ch{chapters[0]:03d}-ch{chapters[-1]:03d})")
    print(f"模式: {'干跑(dry-run)' if args.dry_run else '实际修改'}")
    print(f"轨道: {args.track}")

    repairer = BatchRepairer()

    if args.track == 'all':
        results = repairer.repair_batch(chapters, dry_run=args.dry_run)
    else:
        results = {args.track: repairer.repair_track(chapters, args.track, args.dry_run)}

    print("\n" + "=" * 60)
    print("修复汇总")
    print("=" * 60)

    for track, result in results.items():
        print(f"\n【{result['track']}】")
        print(f"  处理章节: {result['total_chapters']}")
        print(f"  修改章节: {result['modified_chapters']}")
        print(f"  总替换数: {result['total_changes']}")

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存: {output_path}")


if __name__ == '__main__':
    main()
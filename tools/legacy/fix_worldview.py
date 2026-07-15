#!/usr/bin/env python3
"""
世界观统一脚本 - v9.1
将科幻术语替换为修真术语

替换规则：
- 核废土/辐射区 → 灵气衰竭区域/秘境崩塌区
- 辐射 → 灵能污染/灵毒
- 核武器/核弹 → 灭世灵器/天罚之器
- 基因变异 → 灵根觉醒/血脉觉醒
- 科技武器 → 灵器/灵宝
- 飞船/战舰 → 飞行灵器/灵舟
- 能量护盾 → 灵力护罩/灵盾
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class WorldviewUnifier:
    """世界观统一器"""

    # 术语替换规则（优先级从高到低）
    REPLACEMENTS: List[Tuple[str, str, str]] = [
        # 核废土系列（最高优先级）
        ("核废土", "灵气衰竭区域", "废土描写"),
        ("核辐射污染区", "灵能污染禁区", "污染区描写"),
        ("辐射区", "灵能污染区", "辐射区描写"),
        ("辐射污染", "灵能污染", "污染描写"),
        ("放射性污染", "灵能残留", "污染描写"),
        ("核辐射", "灵毒辐射", "辐射描写"),

        # 核武器系列
        ("核武器", "灭世灵器", "武器描写"),
        ("核弹", "灭世灵弹", "武器描写"),
        ("核爆", "灵爆", "爆炸描写"),
        ("核爆炸", "灵能大爆发", "爆炸描写"),
        ("核打击", "天罚打击", "攻击描写"),

        # 基因变异系列
        ("基因变异", "灵根觉醒", "变异描写"),
        ("基因突变", "血脉觉醒", "突变描写"),
        ("变异生物", "觉醒兽", "生物描写"),
        ("变异兽", "觉醒兽", "生物描写"),

        # 科技武器系列
        ("能量护盾", "灵力护罩", "护盾描写"),
        ("护盾", "灵盾", "护盾描写"),
        ("能量武器", "灵器", "武器描写"),
        ("激光武器", "灵光刃", "武器描写"),
        ("激光", "灵光", "光描写"),
        ("等离子", "灵焰", "能量描写"),
        ("导弹", "灵箭", "武器描写"),

        # 飞船系列
        ("飞船", "灵舟", "载具描写"),
        ("战舰", "灵舰", "载具描写"),
        ("航空母舰", "灵航空母舰", "载具描写"),
        ("飞机", "飞行灵器", "载具描写"),
        ("直升机", "旋灵", "载具描写"),

        # 科技概念
        ("人工智能", "器灵", "AI描写"),
        ("AI", "器灵", "AI描写"),
        ("量子", "灵量子", "科技描写"),
        ("纳米", "灵微", "科技描写"),
        ("电子设备", "灵器", "设备描写"),
        ("信号屏蔽", "灵识屏蔽", "屏蔽描写"),

        # 太空/星系
        ("太空", "星空", "太空描写"),
        ("星际", "星辰", "星际描写"),
        ("外太空", "星外虚空", "太空描写"),
        ("卫星轨道", "灵轨", "轨道描写"),
        ("空间站", "星辰殿", "建筑描写"),

        # 通讯
        ("通讯信号", "灵识传讯", "通讯描写"),
        ("加密通讯", "密灵传讯", "通讯描写"),
        ("全息投影", "灵像投射", "科技描写"),
        ("全息", "灵影", "影像描写"),

        # 医疗
        ("基因治疗", "灵根修复", "治疗描写"),
        ("纳米医疗", "灵微医疗", "医疗描写"),
        ("医疗舱", "灵疗殿", "医疗描写"),

        # 防护服
        ("防护服", "灵甲", "服装描写"),
        ("太空服", "星辰战衣", "服装描写"),
        ("作战服", "战灵甲", "服装描写"),

        # 探测
        ("雷达扫描", "灵识探查", "探测描写"),
        ("生命探测仪", "灵息探测仪", "探测描写"),
        ("热成像", "灵热感应", "成像描写"),

        # 动力
        ("核动力", "灵能驱动", "动力描写"),
        ("能量核心", "灵核", "核心描写"),
        ("电池", "灵池", "能源描写"),
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

    def replace_worldview(self, content: str) -> Tuple[str, int]:
        """
        执行世界观替换（使用简单字符串替换）

        Returns:
            (replaced_content, replace_count)
        """
        count = 0
        result = content

        for old_term, new_term, desc in self.REPLACEMENTS:
            # 使用简单字符串替换（中文不适合正则的词边界）
            if old_term in result:
                replaced = result.replace(old_term, new_term)
                if replaced != result:
                    cnt = result.count(old_term)
                    count += cnt
                    result = replaced

        return result, count

    def process_chapters(self, chapter_nums: List[int], dry_run: bool = False) -> Dict[int, int]:
        """
        批量处理章节

        Returns:
            {chapter_num: replace_count}
        """
        results = {}
        for ch_num in chapter_nums:
            content = self.read_chapter(ch_num)
            if not content:
                print(f"ch{ch_num:03d}: 文件不存在，跳过")
                results[ch_num] = 0
                continue

            new_content, count = self.replace_worldview(content)

            if count > 0 and not dry_run:
                self.write_chapter(ch_num, new_content)
                print(f"ch{ch_num:03d}: ✓ 替换 {count} 处")
            elif count > 0 and dry_run:
                print(f"ch{ch_num:03d}: [干跑] 替换 {count} 处")
            else:
                print(f"ch{ch_num:03d}: — 无需修改")

            results[ch_num] = count

        return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description='世界观统一工具')
    parser.add_argument('--chapters', type=str, default='1-120',
                        help='章节范围，如 "1-120" 或 "1,5,10"')
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

    print(f"待处理章节: {len(chapters)} 个 (ch{chapters[0]:03d}-ch{chapters[-1]:03d})")
    print(f"模式: {'干跑(dry-run)' if args.dry_run else '实际修改'}")
    print("-" * 50)

    unifier = WorldviewUnifier()
    results = unifier.process_chapters(chapters, dry_run=args.dry_run)

    total_replaces = sum(results.values())
    modified = sum(1 for v in results.values() if v > 0)

    print("-" * 50)
    print(f"完成: {modified}/{len(chapters)} 个章节有修改")
    print(f"总替换次数: {total_replaces}")


if __name__ == '__main__':
    main()

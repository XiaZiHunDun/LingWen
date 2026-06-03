#!/usr/bin/env python3
"""
势力关系检测器
追踪势力关系变化，检测关系矛盾，建立势力关系图谱

改进日志：
- v2.0: 修复 [\\w]+ 不匹配中文的问题，添加所有格模式和独立主语模式
"""
import os
import re
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

# 主要势力（2-5字中文名称）
FACTIONS = [
    '星辰会', '万剑宗', '玄机阁', '暗域',
    '星辰宗', '联盟', '灵兽谷', '本源之母',
]

# 势力名称匹配：2-5个中文字符
CHINESE_FACTION = r'[\u4e00-\u9fa5]{2,5}'

# 势力关系描述模式（修复：\w+ → 中文匹配）
RELATION_PATTERNS = {
    'ALLIED': [
        # 标准格式：A与B结盟/联手/合作
        rf'({CHINESE_FACTION})与({CHINESE_FACTION})(?:结盟|联手|合作)',
        rf'({CHINESE_FACTION})和({CHINESE_FACTION})(?:联合|结盟|联手)',
        rf'({CHINESE_FACTION})站在({CHINESE_FACTION})一边',
        rf'({CHINESE_FACTION})与({CHINESE_FACTION})联合',
    ],
    'HOSTILE': [
        # 标准格式：A与B对抗/开战/进攻/袭击
        rf'({CHINESE_FACTION})与({CHINESE_FACTION})(?:对抗|开战|敌对)',
        rf'({CHINESE_FACTION})(?:进攻|袭击|攻击|入侵|对抗)({CHINESE_FACTION})',
        rf'({CHINESE_FACTION})(?:消灭|歼灭|击败)({CHINESE_FACTION})',
        # ========== 新增：所有格敌对关系 ==========
        # "暗域的变异兽群" → 暗域是敌对方（派遣变异兽）
        rf'({CHINESE_FACTION})的(?:变异兽|怪物|士兵|追兵|军队|爪牙)',
        # "击退星辰会的追兵" → 星辰会是敌对方
        rf'(?:击退|击败|歼灭)({CHINESE_FACTION})的',
        # ========== 新增：独立主语敌对关系 ==========
        # "暗域的人来了" → 暗域来袭
        rf'({CHINESE_FACTION})的人(?:来|出现|现身)',
        # "XX来袭/进攻..."
        rf'({CHINESE_FACTION})(?:来袭|进攻|入侵|出击)',
    ],
    'BETRAY': [
        rf'({CHINESE_FACTION})背叛({CHINESE_FACTION})',
        rf'({CHINESE_FACTION})出卖({CHINESE_FACTION})',
        rf'({CHINESE_FACTION})投靠({CHINESE_FACTION})',
        rf'({CHINESE_FACTION})倒戈',
    ],
    'NEGOTIATE': [
        rf'({CHINESE_FACTION})与({CHINESE_FACTION})(?:谈判|协商|和谈|会谈)',
        rf'({CHINESE_FACTION})(?:谈判|协商)和({CHINESE_FACTION})',
    ],
    # ========== 新增：友好/中立关系 ==========
    'NEUTRAL': [
        rf'({CHINESE_FACTION})与({CHINESE_FACTION})(?:保持距离|互不干涉|中立)',
        rf'({CHINESE_FACTION})和({CHINESE_FACTION})(?:友好|邦交)',
    ],
}


def extract_relations(content: str) -> List[Dict]:
    """从内容中提取势力关系描述"""
    relations = []

    for relation_type, patterns in RELATION_PATTERNS.items():
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for m in matches:
                if isinstance(m, tuple) and len(m) >= 2:
                    # 提取两个势力名（忽略所有格修饰词）
                    faction1 = m[0].strip()
                    faction2 = m[1].strip() if len(m) > 1 else ''

                    if not faction1 or not faction2:
                        continue

                    # 检查是否都是已知势力（或主角林夜/苏琳）
                    all_known = ['林夜', '苏琳', '主角']
                    valid_factions = [f for f in FACTIONS + all_known
                                     if f in faction1 or f in faction2]

                    if len(valid_factions) >= 1:
                        relations.append({
                            'type': relation_type,
                            'faction1': faction1,
                            'faction2': faction2,
                            'raw': f'{faction1}-{faction2}'
                        })

    return relations


def infer_hostile_relations(content: str) -> List[Dict]:
    """从上下文推断敌对关系（补充正则匹配不到的语义推断）"""
    inferred = []

    # 敌对动作词库
    hostile_actions = ['击退', '击败', '歼灭', '杀死', '消灭', '逃离', '抵抗', '对抗']

    for faction in FACTIONS:
        for action in hostile_actions:
            # "击退/击败/歼灭 XX的追兵/士兵" → XX是敌对方
            pattern = rf'{action}{faction}的'
            if re.search(pattern, content):
                inferred.append({
                    'type': 'HOSTILE',
                    'faction1': '林夜',  # 从上下文推断主角
                    'faction2': faction,
                    'inferred': True,
                    'evidence': f'{action}{faction}的...'
                })

            # "XX的人来了" → XX是敌对方
            pattern = rf'{faction}的人(?:来|出现)'
            if re.search(pattern, content):
                inferred.append({
                    'type': 'HOSTILE',
                    'faction1': '主角',
                    'faction2': faction,
                    'inferred': True,
                    'evidence': f'{faction}的人来了'
                })

    return inferred


def count_faction_mentions(content: str) -> Dict[str, int]:
    """统计各势力在文本中的提及次数"""
    counts = {}
    for faction in FACTIONS:
        counts[faction] = len(re.findall(faction, content))
    return counts


def check_faction_relations(chapters_dir: str,
                            chapter_range: tuple[int, int] = (1, 360)) -> Dict:
    """
    检测势力关系一致性

    Args:
        chapters_dir: 章节目录
        chapter_range: 检查章节范围

    Returns:
        检测结果字典
    """
    start, end = chapter_range

    # 记录每个章节的势力关系
    chapter_relations: Dict[int, List] = {i: [] for i in range(start, end + 1)}
    chapter_mentions: Dict[int, Dict[str, int]] = {}

    # 记录关系变化
    relation_changes = []

    # 追踪势力关系历史
    last_known_relations = {}  # (faction1, faction2) -> last_relation_type

    # 统计势力提及
    total_mentions = defaultdict(int)

    for i in range(start, end + 1):
        fname = f"ch{i:03d}.md"
        fpath = os.path.join(chapters_dir, fname)

        if not os.path.exists(fpath):
            continue

        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        # 统计提及
        mentions = count_faction_mentions(content)
        for f, c in mentions.items():
            total_mentions[f] += c
        chapter_mentions[i] = mentions

        # 提取关系
        relations = extract_relations(content)
        # 补充推断关系
        inferred = infer_hostile_relations(content)
        relations.extend(inferred)

        chapter_relations[i] = relations

        # 检测关系变化
        for rel in relations:
            key = (rel['faction1'], rel['faction2'])
            if key in last_known_relations:
                if last_known_relations[key] != rel['type']:
                    old_type = last_known_relations[key]
                    new_type = rel['type']

                    # 检测矛盾：敌对→结盟 without negotiation
                    if old_type == 'HOSTILE' and new_type in ('ALLIED', 'NEGOTIATE'):
                        relation_changes.append({
                            'chapter': i,
                            'type': 'SUDDEN_ALLIANCE',
                            'desc': f'{rel["faction1"]}与{rel["faction2"]}从敌对突然结盟（缺少过渡）',
                            'from': old_type,
                            'to': new_type
                        })
                    # 检测矛盾：结盟→敌对 without betrayal
                    elif old_type == 'ALLIED' and new_type == 'HOSTILE':
                        relation_changes.append({
                            'chapter': i,
                            'type': 'BETRAYAL_UNEXPLAINED',
                            'desc': f'{rel["faction1"]}与{rel["faction2"]}从结盟突然敌对（缺少背叛理由）',
                            'from': old_type,
                            'to': new_type
                        })
            else:
                last_known_relations[key] = rel['type']

    # 统计每个势力的关系数
    faction_stats = defaultdict(lambda: {'alliances': 0, 'hostiles': 0, 'mentions': 0})
    for faction, count in total_mentions.items():
        faction_stats[faction]['mentions'] = count

    for ch, relations in chapter_relations.items():
        for rel in relations:
            if rel['type'] == 'ALLIED':
                faction_stats[rel['faction1']]['alliances'] += 1
                faction_stats[rel['faction2']]['alliances'] += 1
            elif rel['type'] == 'HOSTILE':
                faction_stats[rel['faction1']]['hostiles'] += 1
                faction_stats[rel['faction2']]['hostiles'] += 1

    # 检测关系混乱的势力
    inconsistent_factions = []
    for faction, stats in faction_stats.items():
        if stats['alliances'] > 0 and stats['hostiles'] > 0:
            inconsistent_factions.append(faction)

    return {
        'checked_chapters': end - start + 1,
        'relation_changes': relation_changes,
        'change_count': len(relation_changes),
        'inconsistent_factions': inconsistent_factions,
        'faction_stats': dict(faction_stats),
        'total_mentions': dict(total_mentions),
    }


def report_results(results: Dict, output_file: str = None) -> str:
    """生成势力关系检测报告"""
    lines = []
    lines.append("=" * 70)
    lines.append("势力关系检测报告")
    lines.append("=" * 70)
    lines.append("")

    lines.append(f"检查章节: {results['checked_chapters']} 章")
    lines.append(f"关系变化: {results['change_count']} 处")

    # 势力提及统计
    if results.get('total_mentions'):
        lines.append("")
        lines.append("--- 势力提及统计 ---")
        sorted_factions = sorted(results['total_mentions'].items(),
                                 key=lambda x: x[1], reverse=True)
        for faction, count in sorted_factions[:8]:
            stats = results['faction_stats'].get(faction, {})
            lines.append(f"  {faction}: 提及{count}次, 结盟{stats.get('alliances', 0)}次, 敌对{stats.get('hostiles', 0)}次")

    if results['relation_changes']:
        lines.append("")
        lines.append("--- 关系突变（可能矛盾）---")
        for c in results['relation_changes'][:10]:
            lines.append(f"  ch{c['chapter']:03d}: {c['desc']}")

    if results['inconsistent_factions']:
        lines.append("")
        lines.append("--- 关系混乱势力（同时结盟又敌对）---")
        for faction in results['inconsistent_factions'][:5]:
            stats = results['faction_stats'][faction]
            lines.append(f"  {faction}: 结盟{stats['alliances']}次, 敌对{stats['hostiles']}次")

    report = "\n".join(lines)
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='势力关系检测')
    parser.add_argument('chapters_dir', help='章节目录路径')
    parser.add_argument('--start', type=int, default=1, help='起始章节')
    parser.add_argument('--end', type=int, default=360, help='结束章节')
    parser.add_argument('--output', '-o', help='输出报告路径')
    args = parser.parse_args()

    results = check_faction_relations(args.chapters_dir, (args.start, args.end))
    report = report_results(results, args.output)
    print(report)

    sys.exit(0 if results['change_count'] == 0 else 1)

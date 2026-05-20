#!/usr/bin/env python3
"""
伏笔回收率检查器 v2.0
检查关键元素是否在后续章节中被回收

改进日志：
- v2.0: 扩展提取策略（括号外提取）、分级窗口（核心30/普通60/边缘90）、
        工单生成机制、语义相似度匹配
"""
import re
import os
import sys
import json
from typing import List, Dict, Set, Tuple
from collections import defaultdict
from datetime import datetime


# ========== 分级窗口配置 ==========
WINDOW_TIERS = {
    'core': 30,    # 核心伏笔：重要道具/关键能力
    'normal': 60,  # 普通伏笔：配角/组织
    'edge': 90,    # 边缘伏笔：氛围元素
}

# 核心伏笔关键词
CORE_OBJECT_KEYWORDS = ['令', '剑', '刀', '珠', '心法', '功法', '传承', '器', '甲']
CORE_CHARACTER_KEYWORDS = ['皇', '王', '帝', '尊', '主', '长']
CORE_CONCEPT_KEYWORDS = ['法则', '本源', '虚无', '奇点', '灾变', '创世']


class PlotDeviceTracker:
    """伏笔追踪器 v2.0"""

    def __init__(self, chapters_dir: str, window: int = 50):
        self.chapters_dir = chapters_dir
        self.window = window

    def load_chapter(self, chapter_num: int) -> str:
        fname = f"ch{chapter_num:03d}.md"
        fpath = os.path.join(self.chapters_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def _clean_entity_name(self, name: str) -> str:
        """清理实体名称，去除标点和噪声词"""
        # 去除结尾的标点和语气词
        name = re.sub(r'[,，\.。!?！？\s]+$', '', name)
        name = re.sub(r'^[的很是]+', '', name)
        # 去除"你的"、"我的"等所有格开头
        name = re.sub(r'^(你的|我的|他的|她的|它的|这个|那个)', '', name)
        # 去除问句残留
        name = re.sub(r'[吗嘛么?？]+$', '', name)
        # 去除"..."省略号
        name = re.sub(r'^\.{2,}', '', name)
        # 过滤过短或过长的
        if len(name) < 2 or len(name) > 12:
            return None
        # 过滤纯标点
        if not re.search(r'[\u4e00-\u9fa5]', name):
            return None
        return name

    def _classify_element_tier(self, elem: str, elem_type: str) -> str:
        """根据元素名判断伏笔级别"""
        # 优先判断是否为组织/势力（避免"万剑宗"等被误判为core级道具）
        if elem_type == 'locations':
            org_suffixes = ['阁', '会', '门', '宗', '殿', '域', '谷', '盟']
            if any(elem.endswith(s) for s in org_suffixes):
                return 'normal'
        # 核心伏笔判断（仅当明确是道具/能力时）
        if elem_type == 'objects':
            if any(kw in elem for kw in CORE_OBJECT_KEYWORDS):
                # 排除组织名被误判（组织名长度通常>=3且含"宗/门/阁"等后缀）
                org_suffixes = ['阁', '会', '门', '宗', '殿', '域', '谷', '盟']
                if any(elem.endswith(s) for s in org_suffixes):
                    return 'normal'  # 组织不是道具
                return 'core'
        if elem_type == 'characters':
            if any(kw in elem for kw in CORE_CHARACTER_KEYWORDS):
                return 'core'
        if elem_type == 'concepts':
            if any(kw in elem for kw in CORE_CONCEPT_KEYWORDS):
                return 'core'
        # 边缘伏笔
        return 'edge'

    def _get_window_for_element(self, elem: str, elem_type: str) -> int:
        """获取元素对应的窗口阈值"""
        tier = self._classify_element_tier(elem, elem_type)
        return WINDOW_TIERS[tier]

    def extract_first_appearances(self, content: str, chapter_num: int) -> Dict[str, Set[str]]:
        """
        提取首次出现的关键元素（增强版：括号外也提取）

        Returns:
            dict with keys: 'characters', 'objects', 'locations', 'concepts'
        """
        elements = {
            'characters': set(),
            'objects': set(),
            'locations': set(),
            'concepts': set()
        }

        # ========== 扩展人物白名单 ==========
        main_chars = [
            # 原有核心人物
            '林夜', '苏琳', '小九', '铁蛋', '星月', '莫言', '星瑶', '墨白',
            '本源', '虚无', '暗皇', '星辰', '玄机阁',
            # 新增：重要配角
            '太初', '陈风', '白袍', '黑袍', '星瑶', '本源之母', '本源',
            '灵兽', '守护灵', '老人', '独眼男人',
            # 新增：敌方/次要
            '堕落者', '暗影', '议会', '议长',
        ]

        for char in main_chars:
            if char in content and len(char) >= 2:
                elements['characters'].add(char)

        # ========== 扩展：括号外的重要物件提取 ==========
        # 从【】和《》中提取
        for match in re.finditer(r'《([^》]{2,10})》', content):
            name = self._clean_entity_name(match.group(1))
            if name:
                elements['objects'].add(name)
        for match in re.finditer(r'【([^】]{2,10})】', content):
            name = self._clean_entity_name(match.group(1))
            if name:
                elements['objects'].add(name)

        # ========== 新增：从引号中提取道具名（对话中提到的） ==========
        # "《星陨令》" 在对话中可能出现
        # 只提取真正的道具名，排除句子片段
        known_factions_set = {'星辰会', '万剑宗', '玄机阁', '暗域', '星辰宗', '联盟', '灵兽谷', '本源之母'}
        for match in re.finditer(r'[\u201c\u201d"]([^"\u201c\u201d]{2,10})[\u201c\u201d"]', content):
            name = self._clean_entity_name(match.group(1).strip())
            # 必须是真正的道具名（短于5字且含关键词），排除句子片段
            if name and len(name) <= 5 and ('令' in name or '剑' in name or '珠' in name or '功法' in name or '传承' in name or '器' in name):
                # 排除组织名
                if name not in known_factions_set:
                    elements['objects'].add(name)

        # ========== 地点/组织：扩展提取 ==========
        # 直接匹配已知势力名
        known_factions = ['星辰会', '万剑宗', '玄机阁', '暗域', '星辰宗', '联盟', '灵兽谷', '本源之母']
        for faction in known_factions:
            # 匹配势力名在各种位置出现
            pattern = rf'(?<![的之是]){re.escape(faction)}'
            for match in re.finditer(pattern, content):
                s = match.start()
                # 排除"你的万剑宗"等所有格修饰
                if s > 0 and content[s-1] in '的':
                    continue
                elements['locations'].add(faction)

        # ========== 重要概念（宇宙/法则级概念）==========
        concept_suffixes = ['法则', '本源', '虚无', '奇点', '灾变', '创世', '境']
        for suffix in concept_suffixes:
            pattern = rf'[\u4e00-\u9fa5]{3,8}{suffix}'
            for match in re.finditer(pattern, content):
                m = match.group()
                s = match.start()
                if s >= 1 and content[s-1] in '的了是':
                    continue
                elements['concepts'].add(m)

        return elements

    def track_all_first_appearances(self, start_ch: int = 1, end_ch: int = 360) -> Dict:
        """追踪所有首次出现的元素"""
        tracking = {
            'characters': {},
            'objects': {},
            'locations': {},
            'concepts': {}
        }

        for ch_num in range(start_ch, end_ch + 1):
            content = self.load_chapter(ch_num)
            if not content:
                continue

            elements = self.extract_first_appearances(content, ch_num)

            for elem_type, elem_set in elements.items():
                for elem in elem_set:
                    if elem not in tracking[elem_type]:
                        # 记录首次出现章节和元素级别
                        tracking[elem_type][elem] = {
                            'first_chapter': ch_num,
                            'tier': self._classify_element_tier(elem, elem_type)
                        }

        return tracking

    def _fuzzy_match(self, elem: str, content: str) -> bool:
        """模糊匹配：支持同义词/变形检测"""
        # 直接包含
        if elem in content:
            return True

        # 变形检测：去除"了"、"的"等
        elem_base = re.sub(r'[了的]', '', elem)
        if elem_base and elem_base in content:
            return True

        # N-gram语义匹配：处理同义词、变形词
        if self._fuzzy_match_ngram(elem, content):
            return True

        return False

    def _fuzzy_match_ngram(self, elem: str, content: str, threshold: float = 0.75) -> bool:
        """基于N-gram的语义匹配，容忍同义词和变形"""
        if len(elem) < 2:
            return False

        # 生成字符级bi-gram集合
        def get_bigrams(s: str) -> set:
            s = re.sub(r'[^\u4e00-\u9fa5]', '', s)  # 只保留汉字
            if len(s) < 2:
                return {s} if s else set()
            return {s[i:i+2] for i in range(len(s) - 1)}

        elem_bigrams = get_bigrams(elem)
        if not elem_bigrams:
            return False

        # 滑动窗口提取content中的片段进行比对
        window_size = max(len(elem), 8)  # 窗口大小至少为elem长度或8
        step = max(1, window_size // 2)   # 滑动步长

        for i in range(0, len(content) - window_size + 1, step):
            window = content[i:i + window_size]
            content_bigrams = get_bigrams(window)
            if not content_bigrams:
                continue

            # 计算Jaccard相似度
            intersection = len(elem_bigrams & content_bigrams)
            union = len(elem_bigrams | content_bigrams)
            if union > 0:
                similarity = intersection / union
                if similarity >= threshold:
                    return True

        return False

    def check_recycling(self, tracking: Dict, start_ch: int = 1, end_ch: int = 360) -> Dict:
        """检查伏笔是否被回收（支持分级窗口）"""
        results = {
            'planted': {'characters': 0, 'objects': 0, 'locations': 0, 'concepts': 0},
            'recycled': {'characters': 0, 'objects': 0, 'locations': 0, 'concepts': 0},
            'unrecycled': {'characters': [], 'objects': [], 'locations': [], 'concepts': []},
            'by_tier': {'core': {'planted': 0, 'recycled': 0},
                        'normal': {'planted': 0, 'recycled': 0},
                        'edge': {'planted': 0, 'recycled': 0}},
            'details': []
        }

        for elem_type in ['characters', 'objects', 'locations', 'concepts']:
            for elem, info in tracking[elem_type].items():
                if isinstance(info, dict):
                    first_ch = info['first_chapter']
                    tier = info.get('tier', 'normal')
                else:
                    first_ch = info
                    tier = 'normal'

                if first_ch >= end_ch:
                    continue

                # 使用分级窗口
                window = self._get_window_for_element(elem, elem_type)
                effective_window = min(window, end_ch - first_ch)

                if effective_window < 1:
                    continue

                results['planted'][elem_type] += 1
                results['by_tier'][tier]['planted'] += 1

                # 在窗口内检索是否出现
                recycled = False
                for check_ch in range(first_ch + 1, first_ch + effective_window + 1):
                    content = self.load_chapter(check_ch)
                    if self._fuzzy_match(elem, content):
                        recycled = True
                        break

                if recycled:
                    results['recycled'][elem_type] += 1
                    results['by_tier'][tier]['recycled'] += 1
                else:
                    results['unrecycled'][elem_type].append({
                        'element': elem,
                        'first_chapter': first_ch,
                        'type': elem_type,
                        'tier': tier,
                        'window': window
                    })

        # 计算回收率
        total_planted = sum(results['planted'].values())
        total_recycled = sum(results['recycled'].values())
        results['recycling_rate'] = f"{total_recycled / total_planted * 100:.1f}%" if total_planted > 0 else "0%"

        # 按级别计算回收率
        for tier in ['core', 'normal', 'edge']:
            p = results['by_tier'][tier]['planted']
            r = results['by_tier'][tier]['recycled']
            results['by_tier'][tier]['rate'] = f"{r / p * 100:.1f}%" if p > 0 else "0%"

        return results

    def check_all(self, start_ch: int = 1, end_ch: int = 360) -> Dict:
        """完整检查"""
        tracking = self.track_all_first_appearances(start_ch, end_ch)
        results = self.check_recycling(tracking, start_ch, end_ch)
        results['tracking'] = tracking
        return results

    def generate_workorders(self, results: Dict, output_dir: str = None) -> List[Dict]:
        """
        生成伏笔回收工单

        Returns:
            工单列表
        """
        workorders = []

        for elem_type, items in results['unrecycled'].items():
            for item in items:
                wo = {
                    'workorder_id': f"PLOT-{item['first_chapter']:03d}-{hash(item['element']) % 10000:04d}",
                    'created_at': datetime.now().isoformat(),
                    'type': 'plot_device_recycling',
                    'tier': item['tier'],
                    'element': item['element'],
                    'element_type': elem_type,
                    'first_chapter': item['first_chapter'],
                    'window': item['window'],
                    'priority': 'P0' if item['tier'] == 'core' else 'P1' if item['tier'] == 'normal' else 'P2',
                    'status': 'pending',
                    'suggestion': f'在后续{max(1, item["first_chapter"] + 1)}-ch{item["first_chapter"] + item["window"]:03d}内安排回收'
                }
                workorders.append(wo)

        # 写入工单文件
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            fpath = os.path.join(output_dir, f'plot_workorders_{timestamp}.json')
            with open(fpath, 'w', encoding='utf-8') as f:
                json.dump(workorders, f, ensure_ascii=False, indent=2)
            results['workorder_file'] = fpath

        results['workorders'] = workorders
        return workorders


def report_results(results: Dict, output_file: str = None) -> str:
    """生成检查报告"""
    lines = []
    lines.append("=" * 70)
    lines.append("伏笔回收率检查报告 (v2.0)")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"回收率: {results['recycling_rate']}")
    lines.append("")

    # 按级别统计
    lines.append("--- 按级别统计 ---")
    for tier in ['core', 'normal', 'edge']:
        data = results['by_tier'].get(tier, {})
        lines.append(f"  {tier}: {data.get('planted', 0)}植入 / {data.get('recycled', 0)}回收 ({data.get('rate', '0%')})")
    lines.append("")

    lines.append("--- 总体统计 ---")
    total_planted = sum(results['planted'].values())
    total_recycled = sum(results['recycled'].values())
    lines.append(f"植入伏笔总数: {total_planted}")
    lines.append(f"已回收数量: {total_recycled}")
    lines.append("")

    lines.append("--- 按类型统计 ---")
    for elem_type in ['characters', 'objects', 'locations', 'concepts']:
        planted = results['planted'][elem_type]
        recycled = results['recycled'][elem_type]
        rate = f"{recycled / planted * 100:.1f}%" if planted > 0 else "0%"
        lines.append(f"  {elem_type}: {planted}植入 / {recycled}回收 ({rate})")
    lines.append("")

    # 未回收的伏笔
    total_unrecycled = sum(len(v) for v in results['unrecycled'].values())
    lines.append(f"--- 未回收伏笔 ({total_unrecycled}个) ---")

    all_unrecycled = []
    for elem_type, items in results['unrecycled'].items():
        for item in items:
            all_unrecycled.append((item['first_chapter'], item['element'], elem_type, item['tier']))

    all_unrecycled.sort(key=lambda x: (x[3] != 'core', x[3] != 'normal', x[0]))

    for first_ch, elem, elem_type, tier in all_unrecycled[:30]:
        lines.append(f"  [{tier}] ch{first_ch:03d}: [{elem_type}] {elem}")

    if results.get('workorder_file'):
        lines.append("")
        lines.append(f"工单已生成: {results['workorder_file']}")

    report = "\n".join(lines)
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='伏笔回收率检查')
    parser.add_argument('chapters_dir', help='章节目录路径')
    parser.add_argument('--start', type=int, default=1, help='起始章节')
    parser.add_argument('--end', type=int, default=360, help='结束章节')
    parser.add_argument('--window', type=int, default=50, help='回收检测窗口')
    parser.add_argument('--output', '-o', help='输出报告路径')
    parser.add_argument('--workorder-dir', help='工单输出目录')
    args = parser.parse_args()

    tracker = PlotDeviceTracker(args.chapters_dir, args.window)
    results = tracker.check_all(args.start, args.end)

    if args.workorder_dir:
        tracker.generate_workorders(results, args.workorder_dir)

    report = report_results(results, args.output)
    print(report)

    sys.exit(0)
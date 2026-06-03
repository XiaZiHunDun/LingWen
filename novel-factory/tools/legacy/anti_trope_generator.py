#!/usr/bin/env python3
"""
反套路创意生成器
随机组合不同元素创造新颖剧情

使用方法:
    python anti_trope_generator.py --mode random --count 3
    python anti_trope_generator.py --mode prompt "星际+克苏鲁"
"""

import random
import yaml
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class AntiTropeGenerator:
    """反套路创意生成器"""

    # 基础元素池
    ELEMENTS = {
        "setting": [
            "星际修真文明", "废土朋克世界", "赛博都市",
            "远古遗迹", "平行世界", "时间夹缝"
        ],
        "conflict": [
            "生存竞争", "理念分歧", "记忆争夺",
            "身份认同", "力量代价", "时间循环"
        ],
        "character": [
            "沉默型主角", "双面间谍", "失去过去的人",
            "不完美的英雄", "反英雄", "群体主角"
        ],
        "twist": [
            "盟友背叛", "敌人救主角", "主角是造物主",
            "时间倒流", "记忆错位", "虚假结局"
        ]
    }

    # 元素组合规则（避免套路组合）
    FORBIDDEN_COMBOS = [
        ("废土", "升级流"),
        ("退婚", "打脸"),
        ("升级", "换地图"),
    ]

    def __init__(self, concept_db_path: str = None):
        if concept_db_path is None:
            concept_db_path = PROJECT_ROOT / "01_灵感库" / "创意库" / "高概念创意.yaml"
        self.concept_db_path = Path(concept_db_path)
        self.concepts = self._load_concepts()

    def _load_concepts(self) -> list:
        """加载高概念创意库"""
        if self.concept_db_path.exists():
            with open(self.concept_db_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data.get('高概念创意', [])
        return []

    def generate_random(self, count: int = 3) -> list:
        """
        随机生成反套路创意组合

        Args:
            count: 生成数量

        Returns:
            创意组合列表
        """
        results = []
        for _ in range(count):
            combo = {
                "setting": random.choice(self.ELEMENTS["setting"]),
                "conflict": random.choice(self.ELEMENTS["conflict"]),
                "character": random.choice(self.ELEMENTS["character"]),
                "twist": random.choice(self.ELEMENTS["twist"]),
            }

            # 检查是否有禁用组合
            if self._is_forbidden(combo):
                # 重新生成
                return self.generate_random(count)[0:1] + results[1:]

            results.append(combo)

        return results

    def _is_forbidden(self, combo: dict) -> bool:
        """检查是否有禁用组合"""
        for f_set, f_trope in self.FORBIDDEN_COMBOS:
            if f_set in combo["setting"] and f_trope in combo["conflict"]:
                return True
        return False

    def generate_from_prompt(self, prompt: str) -> list:
        """
        基于提示词生成创意（如"克苏鲁+职场"）

        Args:
            prompt: 用户输入的提示词

        Returns:
            创意组合列表
        """
        # 解析提示词中的元素
        elements = [e.strip() for e in prompt.split("+")]

        results = []
        for elem in elements:
            combo = {
                "setting": elem if any(s in elem for s in ["星际", "废土", "赛博", "遗迹"]) else random.choice(self.ELEMENTS["setting"]),
                "conflict": elem if any(c in elem for c in ["竞争", "分歧", "记忆", "代价"]) else random.choice(self.ELEMENTS["conflict"]),
                "character": elem if any(c in elem for c in ["主角", "英雄", "间谍"]) else random.choice(self.ELEMENTS["character"]),
                "twist": random.choice(self.ELEMENTS["twist"]),
            }
            results.append(combo)

        return results

    def match_concepts(self, combo: dict) -> list:
        """匹配高概念库中的创意"""
        matched = []
        for concept in self.concepts:
            tags = concept.get('反套路标签', [])
            for tag in tags:
                if any(tag in str(v) for v in combo.values()):
                    matched.append(concept)
                    break
        return matched

    def format_output(self, combos: list) -> str:
        """格式化输出创意组合"""
        lines = ["=" * 50, "反套路创意组合", "=" * 50]

        for i, combo in enumerate(combos, 1):
            lines.append(f"\n【组合 {i}】")
            lines.append(f"  世界观: {combo['setting']}")
            lines.append(f"  核心冲突: {combo['conflict']}")
            lines.append(f"  主角设定: {combo['character']}")
            lines.append(f"  转折设计: {combo['twist']}")

            # 检查是否符合高概念库
            matched = self.match_concepts(combo)
            if matched:
                lines.append(f"  匹配高概念:")
                for m in matched[:2]:
                    lines.append(f"    - {m['id']}: {m['名称']}")

        lines.append("\n" + "=" * 50)
        return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='反套路创意生成器')
    parser.add_argument('--mode', choices=['random', 'prompt'], default='random',
                        help='生成模式')
    parser.add_argument('--count', type=int, default=3,
                        help='生成数量')
    parser.add_argument('--prompt', type=str, default='',
                        help='提示词（用于prompt模式，如"克苏鲁+职场"）')

    args = parser.parse_args()

    generator = AntiTropeGenerator()

    if args.mode == 'random':
        combos = generator.generate_random(args.count)
    else:
        if not args.prompt:
            print("错误: prompt模式需要 --prompt 参数")
            sys.exit(1)
        combos = generator.generate_from_prompt(args.prompt)

    print(generator.format_output(combos))


if __name__ == '__main__':
    main()
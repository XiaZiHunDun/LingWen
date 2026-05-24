#!/usr/bin/env python3
"""
修复后质量验证脚本
抽样检查修复效果
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import random

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.ai_service import MiniMaxProvider, ProviderConfig

# 科幻术语检查清单
WORLDVIEW_TERMS = [
    "核废土", "辐射区", "核武器", "核弹", "核爆",
    "基因变异", "基因突变", "变异兽", "变异生物",
    "飞船", "战舰", "航空母舰",
    "能量护盾", "激光武器", "等离子",
    "人工智能", "AI", "量子", "纳米",
    "全息投影", "全息",
    "太空服", "防护服",
    "基因治疗", "纳米医疗", "医疗舱",
    "雷达扫描", "生命探测仪", "热成像",
]

# AI痕迹检查模式
AI_PATTERNS = [
    "他感到", "她感到", "它感到",
    "像枯叶", "像星辰", "像风中的",
    "那一刻", "突然", "紧接着",
    "首先", "其次", "最后",
    "可以看出", "值得注意的是", "实际上",
    "因此", "所以", "由于",
]


class QualityVerifier:
    """质量验证器"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
        self.chapters_dir = PROJECT_ROOT / "03_内容仓库" / "04_正文"
        self.provider = MiniMaxProvider(ProviderConfig(api_key=self.api_key, timeout=120))

    def read_chapter(self, chapter_num: int) -> str:
        """读取章节"""
        ch_file = self.chapters_dir / f"ch{chapter_num:03d}.md"
        if not ch_file.exists():
            return ""
        return ch_file.read_text(encoding="utf-8")

    def check_worldview(self, chapter_num: int) -> dict:
        """检查世界观一致性"""
        content = self.read_chapter(chapter_num)
        issues = []
        for term in WORLDVIEW_TERMS:
            if term in content:
                count = content.count(term)
                issues.append({"term": term, "count": count})

        return {
            "chapter": chapter_num,
            "worldview_issues": issues,
            "total_violations": sum(i["count"] for i in issues)
        }

    def check_ai_traces(self, chapter_num: int) -> dict:
        """检查AI痕迹"""
        content = self.read_chapter(chapter_num)
        issues = []
        for pattern in AI_PATTERNS:
            if pattern in content:
                count = content.count(pattern)
                issues.append({"pattern": pattern, "count": count})

        return {
            "chapter": chapter_num,
            "ai_trace_issues": issues,
            "total_traces": sum(i["count"] for i in issues)
        }

    def check_character_consistency(self, chapter_num: int) -> dict:
        """使用LLM检查角色一致性"""
        content = self.read_chapter(chapter_num)
        if not content:
            return {"chapter": chapter_num, "character_issues": [], "llm_calls": 0}

        prompt = f'''请检查以下章节中角色行为是否符合人设。

章节内容（前2000字）：
{content[:2000]}

请返回JSON格式：
{{"issues": [{{"character": "角色名", "issue": "问题描述", "severity": "P1/P2"}}]}}

如果没有发现问题，返回空数组：{{"issues": []}}

只返回JSON。'''

        try:
            response = self.provider.generate(prompt=prompt, max_tokens=1000, temperature=0.3)
            # 解析JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return {
                    "chapter": chapter_num,
                    "character_issues": data.get("issues", []),
                    "llm_calls": 1
                }
        except Exception as e:
            print(f"[ERROR] ch{chapter_num:03d}: {e}")

        return {"chapter": chapter_num, "character_issues": [], "llm_calls": 0}

    def verify_sample(self, sample_size: int = 30) -> dict:
        """抽样验证"""
        # 随机抽取章节
        all_chapters = list(range(1, 361))
        sample_chapters = sorted(random.sample(all_chapters, sample_size))

        print(f"\n抽样验证: {sample_size}章 (ch{sample_chapters[0]:03d}-ch{sample_chapters[-1]:03d})")
        print("=" * 60)

        worldview_results = []
        ai_trace_results = []
        character_results = []

        # 并行检查（先做不需要API的）
        print("\n[1/3] 检查世界观一致性...")
        for ch in sample_chapters:
            result = self.check_worldview(ch)
            worldview_results.append(result)
            if result["total_violations"] > 0:
                print(f"  ch{ch:03d}: {result['total_violations']}处违规模拟术语")

        print("\n[2/3] 检查AI痕迹...")
        for ch in sample_chapters:
            result = self.check_ai_traces(ch)
            ai_trace_results.append(result)
            if result["total_traces"] > 0:
                print(f"  ch{ch:03d}: {result['total_traces']}处AI痕迹")

        print("\n[3/3] 检查角色一致性（调用LLM）...")
        for ch in sample_chapters:
            result = self.check_character_consistency(ch)
            character_results.append(result)
            if result["character_issues"]:
                print(f"  ch{ch:03d}: {len(result['character_issues'])}个角色问题")

        # 汇总
        total_worldview = sum(r["total_violations"] for r in worldview_results)
        total_ai_traces = sum(r["total_traces"] for r in ai_trace_results)
        total_character = sum(len(r["character_issues"]) for r in character_results)
        chapters_with_worldview = sum(1 for r in worldview_results if r["total_violations"] > 0)
        chapters_with_ai_traces = sum(1 for r in ai_trace_results if r["total_traces"] > 0)
        chapters_with_character = sum(1 for r in character_results if r["character_issues"])

        return {
            "sample_size": sample_size,
            "sample_chapters": sample_chapters,
            "worldview": {
                "total_violations": total_worldview,
                "chapters_affected": chapters_with_worldview,
                "avg_per_chapter": total_worldview / sample_size
            },
            "ai_traces": {
                "total_traces": total_ai_traces,
                "chapters_affected": chapters_with_ai_traces,
                "avg_per_chapter": total_ai_traces / sample_size
            },
            "character": {
                "total_issues": total_character,
                "chapters_affected": chapters_with_character,
                "avg_per_chapter": total_character / sample_size
            }
        }


def main():
    api_key = os.getenv("MINIMAX_API_KEY", "")
    if not api_key:
        print("需要设置MINIMAX_API_KEY")
        return

    verifier = QualityVerifier(api_key)

    print("=" * 60)
    print("修复后质量验证")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    result = verifier.verify_sample(sample_size=30)

    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)
    print(f"抽样章节: {result['sample_chapters']}")
    print()
    print(f"【世界观一致性】")
    print(f"  违规模拟术语总数: {result['worldview']['total_violations']}")
    print(f"  涉及章节数: {result['worldview']['chapters_affected']}/30")
    print(f"  平均每章: {result['worldview']['avg_per_chapter']:.1f}处")
    print()
    print(f"【AI痕迹】")
    print(f"  AI痕迹总数: {result['ai_traces']['total_traces']}")
    print(f"  涉及章节数: {result['ai_traces']['chapters_affected']}/30")
    print(f"  平均每章: {result['ai_traces']['avg_per_chapter']:.1f}处")
    print()
    print(f"【角色一致性】")
    print(f"  角色问题总数: {result['character']['total_issues']}")
    print(f"  涉及章节数: {result['character']['chapters_affected']}/30")
    print(f"  平均每章: {result['character']['avg_per_chapter']:.1f}处")

    # 保存结果
    output_dir = PROJECT_ROOT / "logs" / "minimax_review"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "verification_result.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n详细结果已保存: {output_file}")


if __name__ == "__main__":
    main()
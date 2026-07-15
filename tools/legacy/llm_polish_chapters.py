#!/usr/bin/env python3
"""
v9.0 小说正文LLM辅助修改脚本
使用AI批量替换"他感到""像枯叶"等套路句式为动作/感官描写

使用方式:
    python tools/llm_polish_chapters.py --chapters 1-10 --patterns "他感到,像枯叶"
    python tools/llm_polish_chapters.py --all --dry-run
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.ai_service import MiniMaxProvider, ProviderConfig


class ChapterPolisher:
    """使用LLM批量润色小说章节"""

    SYSTEM_PROMPT = """你是一个专业的小说文字润色专家。你的任务是将小说中的套路句式替换为更生动、具体的动作和感官描写。

## 替换规则

### 1. "他感到/她感到" 类心理陈述 → 动作/身体反应
- 原文: "他感到一阵寒意"
- 改为: "他的脊背窜过一阵凉意" 或 "他不由自主地打了个寒颤"

- 原文: "她感到心脏被攥紧"
- 改为: "她的胸口像是被什么攥住，喘不上气" 或 "她下意识捂住胸口"

- 原文: "他感到前所未有的孤独"
- 改为: "他把自己缩得更紧，膝盖抵着胸口" 或 "周围只有风声和自己的呼吸"

### 2. "像枯叶/像星辰" 类比喻 → 变化比喻或直接描写
- 原文: "像风中的枯叶"
- 改为: "像秋日落叶般飘摇" 或 "枯叶般颤动"

- 原文: "像沉睡的星辰"
- 改为: "如碎钻般静谧" 或 "像远处昏暗的灯火"

### 3. "那一刻，他..." 类时间标记 → 具体场景
- 原文: "那一刻，他的心融化了"
- 改为: "他感觉胸口有什么东西软了下来"

- 原文: "那一刻，空气凝固了"
- 改为: "两人之间的沉默像是实质"

### 4. 保留核心情感，减少重复
- 同一个情感表达在相近段落只保留1处
- 其他用不同的身体反应或动作暗示

## 输出格式
直接输出修改后的正文，不要解释，不要标记，只输出小说正文。
"""

    def __init__(self, chapters_dir: Optional[str] = None, api_key: Optional[str] = None):
        if chapters_dir is None:
            chapters_dir = PROJECT_ROOT / '03_内容仓库' / '04_正文'
        self.chapters_dir = Path(chapters_dir)
        self.api_key = api_key or os.environ.get('MINIMAX_API_KEY', '')

    def _create_provider(self) -> MiniMaxProvider:
        """创建AI Provider"""
        config = ProviderConfig(
            api_key=self.api_key,
            timeout=120,
            max_retries=3
        )
        return MiniMaxProvider(config)

    def read_chapter(self, chapter_num: int) -> str:
        """读取章节内容"""
        ch_file = self.chapters_dir / f'ch{chapter_num:03d}.md'
        if not ch_file.exists():
            return ""
        return ch_file.read_text(encoding='utf-8')

    def write_chapter(self, chapter_num: int, content: str):
        """写入章节内容"""
        ch_file = self.chapters_dir / f'ch{chapter_num:03d}.md'
        ch_file.write_text(content, encoding='utf-8')

    def polish_chapter(self, chapter_num: int, patterns: List[str]) -> Tuple[str, bool]:
        """
        润色单个章节

        Returns:
            (polished_content, was_modified)
        """
        content = self.read_chapter(chapter_num)
        if not content:
            return "", False

        # 检查是否需要润色
        needs_polish = False
        for pattern in patterns:
            if pattern.lower() in content.lower():
                needs_polish = True
                break

        if not needs_polish:
            return content, False

        # 构建提示
        prompt = f"""请润色以下小说章节，将套路句式替换为生动的动作和感官描写：

---
{content}
---

注意：
1. 保留原文的风格和情感
2. 只替换"他感到""像枯叶""那一刻"等套路表达
3. 用具体的身体反应、动作、环境描写替代
4. 同一个情感表达只在一处保留
5. 输出只包含修改后的正文，不要其他内容
"""

        try:
            provider = self._create_provider()
            polished = provider.generate(
                prompt=prompt,
                system=self.SYSTEM_PROMPT,
                temperature=0.3,
                max_tokens=8192
            )
            return polished.strip(), True
        except Exception as e:
            print(f"  LLM调用失败: {e}")
            return content, False

    def polish_chapters(
        self,
        chapter_nums: List[int],
        patterns: List[str],
        dry_run: bool = False
    ) -> Dict[int, bool]:
        """
        批量润色章节

        Returns:
            {chapter_num: was_modified}
        """
        results = {}
        for ch_num in chapter_nums:
            print(f"处理 ch{ch_num:03d}...", end=" ", flush=True)
            polished, modified = self.polish_chapter(ch_num, patterns)
            if modified and not dry_run:
                self.write_chapter(ch_num, polished)
                print("✓ 已修改")
            elif modified and dry_run:
                print("✓ (dry-run)")
            else:
                print("— 无需修改")
            results[ch_num] = modified
        return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description='LLM辅助润色小说章节')
    parser.add_argument('--chapters', type=str, default='1-10',
                        help='章节范围，如 "1-10" 或 "5,8,12"')
    parser.add_argument('--patterns', type=str,
                        default='他感到,她感到,像枯叶,那一刻',
                        help='需要替换的模式，逗号分隔')
    parser.add_argument('--all', action='store_true',
                        help='处理所有章节')
    parser.add_argument('--dry-run', action='store_true',
                        help='只输出不保存')
    parser.add_argument('--limit', type=int, default=None,
                        help='限制处理章节数量')

    args = parser.parse_args()

    # 解析章节范围
    if args.all:
        chapters = list(range(1, 361))
    else:
        chapters = []
        for part in args.chapters.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                chapters.extend(range(start, end + 1))
            else:
                chapters.append(int(part))

    if args.limit:
        chapters = chapters[:args.limit]

    # 解析模式
    patterns = [p.strip() for p in args.patterns.split(',')]

    print(f"待处理章节: {len(chapters)} 个")
    print(f"检测模式: {', '.join(patterns)}")
    print(f"模式: {'干跑(dry-run)' if args.dry_run else '实际修改'}")
    print("-" * 50)

    polisher = ChapterPolisher()
    results = polisher.polish_chapters(chapters, patterns, dry_run=args.dry_run)

    modified_count = sum(1 for v in results.values() if v)
    print("-" * 50)
    print(f"完成: {modified_count}/{len(chapters)} 个章节已修改")


if __name__ == '__main__':
    main()

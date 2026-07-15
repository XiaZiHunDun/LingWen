#!/usr/bin/env python3
"""
提示词效果反馈记录器 - Feedback Recorder for LingWen Prompts

用于记录提示词模板的使用效果，跟踪改进方向。

用法：
    python3 feedback_recorder.py record --template chapter-writing-prompt --chapter 25
    python3 feedback_recorder.py list
    python3 feedback_recorder.py stats
"""

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

# ========== 路径配置 ==========
BASE_DIR = Path(__file__).parent.parent.parent
FEEDBACK_FILE = BASE_DIR / ".claude" / "prompts" / "_lib" / "反馈日志.md"


# ========== 数据结构 ==========

@dataclass
class Feedback:
    """反馈数据"""
    date: str
    template_type: str
    chapter: int
    user: str = ""

    # 评分 (1-5)
    completeness: int = 0
    executability: int = 0
    context_relevance: int = 0
    output_quality: int = 0

    # 文本反馈
    pros: str = ""
    cons: str = ""
    suggestions: str = ""
    notes: str = ""

    # 统计数据
    token_count: int = 0

    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        def stars(n):
            return "★" * (n or 0) + "☆" * (5 - (n or 0)) if n else "未评分"

        md = f"""
## 反馈记录 {self.date}

### 模板类型：{self.template_type}
### 章节号：ch{self.chapter:03d}
### 使用者：{self.user or '匿名'}

#### 效果评分 (1-5)
- **完整性**：{stars(self.completeness)} ({self.completeness or '未评分'})
- **可执行性**：{stars(self.executability)} ({self.executability or '未评分'})
- **上下文关联**：{stars(self.context_relevance)} ({self.context_relevance or '未评分'})
- **输出质量**：{stars(self.output_quality)} ({self.output_quality or '未评分'})

#### 优点
{self.pros or '-'}

#### 问题/不足
{self.cons or '-'}

#### 改进建议
{self.suggestions or '-'}

#### 实际生成的Prompt Token数
~{self.token_count} tokens

#### 备注
{self.notes or '-'}
"""
        return md.strip()


# ========== 命令处理器 ==========

def cmd_record(args):
    """记录新反馈"""
    feedback = Feedback(
        date=datetime.now().strftime("%Y-%m-%d"),
        template_type=args.template,
        chapter=args.chapter,
        user=args.user or "",
        completeness=args.completeness,
        executability=args.executability,
        context_relevance=args.context_relevance,
        output_quality=args.output_quality,
        pros=args.pros or "",
        cons=args.cons or "",
        suggestions=args.suggestions or "",
        notes=args.notes or "",
        token_count=args.token_count or 0,
    )

    # 追加到反馈日志
    with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
        f.write("\n")
        f.write(feedback.to_markdown())
        f.write("\n")

    print(f"✓ 已记录反馈: {args.template} @ ch{args.chapter:03d}")
    return 0


def cmd_list(args):
    """列出最近反馈"""
    if not FEEDBACK_FILE.exists():
        print("暂无反馈记录")
        return 0

    content = FEEDBACK_FILE.read_text(encoding="utf-8")

    # 提取反馈记录
    records = content.split("## 反馈记录 ")
    print("=" * 60)
    print(f"共 {len(records) - 1} 条反馈记录" if len(records) > 1 else "暂无反馈记录")
    print("=" * 60)

    # 显示最近的5条
    recent = records[-5:] if len(records) > 5 else records[1:]
    for record in recent:
        if record.strip():
            lines = record.strip().split("\n")
            date_line = lines[0] if lines else ""
            template_line = lines[2] if len(lines) > 2 else ""
            chapter_line = lines[3] if len(lines) > 3 else ""
            print(f"\n{datetime.now().strftime('%Y-%m-%d') if not date_line else date_line}")
            print(f"  {template_line.replace('### 模板类型：', '')}")
            print(f"  {chapter_line.replace('### 章节号：', '')}")

    print("\n" + "=" * 60)
    return 0


def cmd_stats(args):
    """显示统计信息"""
    if not FEEDBACK_FILE.exists():
        print("暂无反馈数据")
        return 0

    content = FEEDBACK_FILE.read_text(encoding="utf-8")

    # 简单统计
    records = content.split("## 反馈记录 ")
    record_count = len(records) - 1

    print("=" * 60)
    print("提示词效果反馈统计")
    print("=" * 60)
    print(f"总反馈数：{record_count}")

    if record_count > 0:
        # 提取评分数据（简化实现）
        print("\n反馈维度分布：")
        print("  完整性：")
        print("  可执行性：")
        print("  上下文关联：")
        print("  输出质量：")

        print("\n常见问题：")
        print("  （需要更详细的解析）")

    print("=" * 60)
    return 0


# ========== 主入口 ==========

def main():
    parser = argparse.ArgumentParser(
        description="灵文提示词效果反馈记录器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python3 feedback_recorder.py record --template chapter-writing-prompt --chapter 25 \\
      --completeness 4 --executability 5 --pros "自动填充功能很好" \\
      --cons "场景设定需要手动填写"
  python3 feedback_recorder.py list
  python3 feedback_recorder.py stats
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # record
    rec = subparsers.add_parser("record", help="记录新反馈")
    rec.add_argument("--template", "-t", required=True, help="模板类型")
    rec.add_argument("--chapter", "-c", type=int, required=True, help="章节号")
    rec.add_argument("--user", "-u", help="使用者（可选）")
    rec.add_argument("--completeness", type=int, choices=range(1, 6), help="完整性评分(1-5)")
    rec.add_argument("--executability", type=int, choices=range(1, 6), help="可执行性评分(1-5)")
    rec.add_argument("--context-relevance", type=int, choices=range(1, 6), help="上下文关联评分(1-5)")
    rec.add_argument("--output-quality", type=int, choices=range(1, 6), help="输出质量评分(1-5)")
    rec.add_argument("--pros", help="优点")
    rec.add_argument("--cons", help="问题/不足")
    rec.add_argument("--suggestions", help="改进建议")
    rec.add_argument("--notes", help="备注")
    rec.add_argument("--token-count", type=int, help="生成的Token数")

    # list
    subparsers.add_parser("list", help="列出最近反馈")

    # stats
    subparsers.add_parser("stats", help="显示统计信息")

    args = parser.parse_args()

    if args.command == "record":
        return cmd_record(args)
    elif args.command == "list":
        return cmd_list(args)
    elif args.command == "stats":
        return cmd_stats(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/bin/bash
# novel-factory/.claude/hooks/detect-gaps.sh
# 检测缺失：章节缺失、大纲不一致

NOVEL_FACTORY_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
CHAPTERS_DIR="$NOVEL_FACTORY_DIR/03_内容仓库/04_正文"
OUTLINE_DIR="$NOVEL_FACTORY_DIR/03_内容仓库/03_阶段大纲"

echo "=== 检测缺失 ==="

# 检测章节编号连续性
if [ -d "$CHAPTERS_DIR" ]; then
    python3 << 'EOF'
import os
import re
from pathlib import Path

chapters_dir = os.environ.get('CHAPTERS_DIR', '.')
chapter_files = [f for f in os.listdir(chapters_dir) if re.match(r'ch\d+\.md', f)]

if not chapter_files:
    print("未找到章节文件")
    exit(0)

# 提取编号
numbers = []
for f in chapter_files:
    m = re.match(r'ch(\d+)\.md', f)
    if m:
        numbers.append(int(m.group(1)))

numbers.sort()
missing = []
for i in range(numbers[0], numbers[-1]):
    if i not in numbers:
        missing.append(i)

if missing:
    print(f"⚠️  缺失章节: {missing[:10]}{'...' if len(missing) > 10 else ''}")
else:
    print(f"✓ 章节连续性检查通过 ({len(numbers)} 章)")
EOF
fi

# 检测大纲文件是否缺失
if [ -d "$OUTLINE_DIR" ]; then
    STAGE_OUTLINES=$(find "$OUTLINE_DIR" -name "*.md" | wc -l)
    echo "✓ 阶段大纲文件数: $STAGE_OUTLINES"
fi

echo "检测完成"
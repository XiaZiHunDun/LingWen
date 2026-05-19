#!/bin/bash
# novel-factory/.claude/hooks/pre-commit.sh
# 提交前检查：检查文件完整性、JSON 语法

NOVEL_FACTORY_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
STATE_FILE="$NOVEL_FACTORY_DIR/workflow_state.json"
ERRORS=0

echo "=== 提交前检查 ==="

# 检查 workflow_state.json JSON 语法
if [ -f "$STATE_FILE" ]; then
    python3 -m json.tool "$STATE_FILE" > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "❌ workflow_state.json JSON 语法错误"
        ERRORS=$((ERRORS + 1))
    else
        echo "✓ workflow_state.json JSON 语法正确"
    fi
fi

# 检查是否有临时文件残留
TEMP_FILES=$(find "$NOVEL_FACTORY_DIR" -maxdepth 3 -name "*_temp*" -o -name "*.tmp" 2>/dev/null | head -5)
if [ -n "$TEMP_FILES" ]; then
    echo "⚠️  发现临时文件:"
    echo "$TEMP_FILES"
    ERRORS=$((ERRORS + 1))
fi

# 检查章节文件是否都有**本章完**标记
CHAPTERS_DIR="$NOVEL_FACTORY_DIR/03_内容仓库/04_正文"
if [ -d "$CHAPTERS_DIR" ]; then
    MISSING_END=$(find "$CHAPTERS_DIR" -name "ch*.md" -exec grep -L "**本章完**" {} \; 2>/dev/null | head -5)
    if [ -n "$MISSING_END" ]; then
        echo "⚠️  以下章节缺少 **本章完** 标记:"
        echo "$MISSING_END"
        ERRORS=$((ERRORS + 1))
    else
        echo "✓ 章节文件完整性检查通过"
    fi
fi

if [ $ERRORS -gt 0 ]; then
    echo ""
    echo "发现 $ERRORS 个问题，请修复后提交"
    exit 1
fi

echo "✓ 提交前检查通过"
exit 0
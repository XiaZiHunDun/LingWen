# 角色弧光分析 Skill

## 描述

使用LLM分析小说中角色的弧光完整性（起点→转折→高潮→结局）

## 弧光类型定义

| 角色 | 类型 | 预期弧光阶段 |
|------|------|-------------|
| 林夜 | 成长型 | 失去一切 → 获得机遇 → 艰苦修炼 → 保护所爱 → 终极抉择 |
| 苏琳 | 陪伴型 | 相遇 → 并肩作战 → 情感深化 → 共同面对 |
| 小九 | 觉醒型 | 初始状态 → 遇到主人 → 能力成长 → 完全觉醒 |
| 星月 | 悲剧型 | 美好往昔 → 命运转折 → 艰难考验 → 悲剧结局或突破 |
| 暗皇 | 反派型 | 展示力量 → 制造危机 → 升级冲突 → 被击败或洗白 |

## 使用方式

### 分析单个角色
```
/arc-analyze 林夜 --start 1 --end 50
```

### 分析所有角色
```
/arc-analyze --all --start 1 --end 50
```

## 实现机制

### 1. 数据收集
```python
from check_character_arc_llm import CharacterArcChecker

checker = CharacterArcChecker(chapters_dir)
chapters = checker.get_chapters_for_character(character, start, end)
```

### 2. 提示词构建
```python
task = checker.build_analysis_task(character, start, end)
# task = {
#     'character': '林夜',
#     'prompt': '你是小说结构分析师...',
#     'chapters_count': 30
# }
```

### 3. Agent调用（核心机制）
```python
agent = Agent(
    description=f"角色弧光分析_{character}",
    prompt=task['prompt'],
    subagent_type="general-purpose"
)
result_text = agent.result

# 解析JSON结果
parsed = json.loads(result_text[result_text.find('{'):result_text.rfind('}')+1])
```

### 4. 结果输出
```json
{
  "character": "林夜",
  "arc_type": "成长型",
  "arc_stage": "艰苦修炼（积累期）",
  "is_complete": false,
  "missing_stages": ["保护所爱", "终极抉择"],
  "score": 6,
  "summary": "已完成前3个阶段..."
}
```

## 输出示例

```
角色: 林夜 (弧光类型: 成长型)
======================================================================
当前阶段: 艰苦修炼（积累期）
弧光完整: ✗ 否 (评分: 6/10)

已完成阶段:
  ✓ 失去一切（灾难起点）
  ✓ 获得机遇（觉醒/传承）
  ✓ 艰苦修炼（积累期）

缺失阶段:
  ✗ 保护所爱（能力验证）
  ✗ 终极抉择（牺牲/胜利）

分析: 林夜的成长弧光在前50章已完整展现灾难起点、获得机遇和修炼阶段...
```

## 限制

- 每次调用建议≤50章（Token限制）
- 角色需要在章节中出现才能分析
- 需要Claude Code Agent支持

## 代码路径

```
novel-factory/tools/consistency/check_character_arc_llm.py
```
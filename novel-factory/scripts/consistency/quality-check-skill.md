# 质量维度检查 Skill

## 描述

对小说正文进行多维度质量检查，包括：
- **一致性检查**：命名、内容完整性、重复、人物状态、时间线
- **质量维度检查**：情节关联度、伏笔回收率、场景逻辑、情感节奏、对话风格、人物弧光

## 使用方式

### 一致性检查（快速）
```
/quality-check
```
对所有章节进行一致性基础检查。

### 质量维度检查（完整）
```
/quality-check --start 1 --end 50
```
对指定章节范围进行完整质量维度检查。

### 单维度检查
```
/quality-check --checks segment plot scene emotion dialogue arc
```

### 角色弧光分析（LLM）
```
/arc-analyze 林夜 --start 1 --end 50
```

## 检查维度说明

| 维度 | 类型 | 说明 |
|------|------|------|
| 情节关联度 | 规则 | 每段落与前后章节的关联程度 |
| 伏笔回收率 | 规则 | 首次出现元素在后续章节中的回收率 |
| 场景逻辑 | 规则 | 场景转换合理性和孤岛章节检测 |
| 情感节奏 | 规则 | 情绪波动是否合理 |
| 对话风格 | 规则 | 角色对话字数异常检测 |
| 人物弧光 | LLM | 角色弧光完整性（需Agent调用） |

## 执行流程

### 1. 规则类检查（直接调用Python）
```python
# 情节关联度
SegmentRelevanceChecker(chapters_dir).check_all(start, end)

# 伏笔回收率
PlotDeviceTracker(chapters_dir).check_all(start, end)

# 场景逻辑
SceneLogicChecker(chapters_dir).check_all(start, end)

# 情感节奏
EmotionalRhythmChecker(chapters_dir).check_all(start, end)

# 对话风格
DialogueStyleChecker(chapters_dir).check_all(start, end)
```

### 2. LLM类检查（通过Agent）
```python
# 构建分析任务
task = CharacterArcChecker(chapters_dir).build_analysis_task(character, start, end)

# 通过Agent调用LLM
agent = Agent(
    description=f"角色弧光分析_{character}",
    prompt=task['prompt'],
    subagent_type="general-purpose"
)
result = agent.result
```

## 输出格式

### 汇总报告
```
======================================================================
质量维度检查汇总报告
======================================================================

## 情节关联度
通过率: 86.7%
未通过章节: 9 个

## 伏笔回收率
回收率: 28.8%
已回收: 15/52

## 场景逻辑连贯性
孤岛章节: 4 个
高严重度问题: 2 处

## 情感节奏健康度
未通过章节: 0 个

## 对话风格一致性
总对话数: 246 条
高严重度问题: 0 处

## 人物弧光完整性
弧光完整: 1/3 个角色
  ✓ 林夜 [成长型]: 6/10
  ✗ 星月 [悲剧型]: 缺失阶段
```

## 调度策略

- **并行检查**：规则类检查可并行执行
- **顺序检查**：LLM类检查需按角色顺序
- **分批处理**：建议每批≤50章（LLM调用有限制）

## 代码路径

```
novel-factory/tools/consistency/
├── check_segment_relevance.py    # 情节关联度
├── check_plot_device_tracking.py # 伏笔回收率
├── check_scene_logic.py          # 场景逻辑
├── check_emotional_rhythm.py     # 情感节奏
├── check_dialogue_style.py      # 对话风格
├── check_character_arc_llm.py    # 人物弧光（LLM）
└── run_quality_checks.py         # 统一调度脚本
```
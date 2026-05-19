---
skill_name: novel-quality-check
department: reviewer-dept
model: sonnet
trigger_phrases:
  - /quality-check
  - "run quality check"
  - "质量检查"
---
name: novel-quality-check
description: |
  对小说正文进行多维度质量检查。当用户说"检查小说质量"、"质量维度"、"一致性检查"、"检查伏笔回收"、"检查情节关联"、"分析角色弧光"、"检查情感节奏"或类似意图时使用此技能。

  适用场景：
  - 每批次10章创作完成后，进入审核前
  - 全书创作完成后，进入汇总前
  - 人工审核发现疑似问题后需自动化验证
  - 用户明确要求"跑一下质量检查"

  不适用：简单的"读取章节内容"或"查找某角色"（这些用基础工具即可）
---

# 小说质量维度检查 Skill

## 概述

对《星陨纪元》360章正文进行多维度质量检查，输出问题汇总报告供审核部门和汇总部门使用。

## 检查维度

| 维度 | 类型 | 说明 |
|------|------|------|
| 命名一致性 | 规则 | 文件名chXXX.md与章节内标题"第X章"一致 |
| 内容完整性 | 规则 | **本章完**标记、字数≥500 |
| 章节重复 | 规则 | 跨章节相似度>80%预警 |
| 人物状态 | 规则 | 性别/生死/形态前后矛盾 |
| 时间线 | 规则 | "年前"与"瞬间"同时出现等明显错误 |
| 情节关联度 | 规则 | 每段落与前后章节的关联程度 |
| 伏笔回收率 | 规则 | 首次出现元素在后续N章内回收（window参数决定检测范围，默认50章；只检查有足够后续章节的元素） |
| 场景逻辑 | 规则 | 场景转换合理性、孤岛章节检测 |
| 情感节奏 | 规则 | 情绪波动是否合理 |
| 对话风格 | 规则 | 角色对话字数异常检测 |
| 人物弧光 | **LLM** | 角色弧光完整性（通过Agent调用） |

## 目录结构

```
novel-factory/tools/consistency/
├── run_quality_checks.py         # 统一调度脚本
├── check_segment_relevance.py    # 情节关联度
├── check_plot_device_tracking.py # 伏笔回收率
├── check_scene_logic.py          # 场景逻辑
├── check_emotional_rhythm.py    # 情感节奏
├── check_dialogue_style.py       # 对话风格
├── check_character_arc_llm.py    # 人物弧光（LLM）
├── auto_consistency_checker.py  # 基础一致性检查
├── check_naming.py              # 命名一致性
├── check_content_integrity.py    # 内容完整性
├── check_duplicate.py           # 章节重复
├── check_character_state.py      # 人物状态
└── check_timeline.py            # 时间线
```

## 使用方式

### 1. 完整质量检查（非LLM）
```bash
cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory/tools/consistency
python3 run_quality_checks.py ../../03_内容仓库/04_正文 --start 1 --end 50 --skip-llm
```

### 2. 带LLM的完整检查（人物弧光）
```bash
python3 run_quality_checks.py ../../03_内容仓库/04_正文 --start 1 --end 30
```

### 3. 分维度检查
```bash
# 只检查情节关联度
python3 check_segment_relevance.py ../../03_内容仓库/04_正文 --start 1 --end 50

# 只检查伏笔回收率
python3 check_plot_device_tracking.py ../../03_内容仓库/04_正文 --start 1 --end 50 --window 30

# 只检查场景逻辑
python3 check_scene_logic.py ../../03_内容仓库/04_正文 --start 1 --end 50
```

### 4. 单角色弧光分析（LLM，需Claude Code环境）
```bash
python3 check_character_arc_llm.py ../../03_内容仓库/04_正文 --start 1 --end 30 --character 林夜
```

## 报告格式

### 汇总报告
```
======================================================================
质量维度检查汇总报告 (Claude Code版)
======================================================================

检查时间: 2026-05-18 17:00:00
章节范围: ch001-ch030

## 情节关联度
通过率: 84.7%
未通过章节: 8 个

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

## 人物弧光完整性（通过Agent调用LLM）
弧光完整: 1/3 个角色
  ✓ 林夜 [成长型]: 6/10
  ✗ 星月 [悲剧型]: 缺失阶段
```

## LLM类检查的Agent机制

对于人物弧光检查，需要通过Claude Code的Agent调用LLM：

```python
from check_character_arc_llm import CharacterArcChecker

# 1. 构建分析任务
checker = CharacterArcChecker(chapters_dir)
task = checker.build_analysis_task(character, start, end)

# 2. 通过Agent调用LLM
agent = Agent(
    description=f"角色弧光分析_{character}",
    prompt=task['prompt'],
    subagent_type="general-purpose"
)
result_text = agent.result

# 3. 解析JSON结果
import json
parsed = json.loads(result_text[result_text.find('{'):result_text.rfind('}')+1])
# parsed = {'character': '林夜', 'arc_stage': '...', 'is_complete': True/False, 'score': 8, ...}
```

## 调度策略

1. **规则类检查**：可并行执行，互不依赖
2. **LLM类检查**：需按角色顺序执行，建议每批≤50章
3. **建议流程**：
   - 创作阶段：规则类检查即可
   - 审核阶段：加入LLM类检查（人物弧光）
   - 汇总阶段：完整检查

## 角色弧光配置

| 角色 | 类型 | 预期弧光阶段 |
|------|------|-------------|
| 林夜 | 成长型 | 失去一切 → 获得机遇 → 艰苦修炼 → 保护所爱 → 终极抉择 |
| 苏琳 | 陪伴型 | 相遇 → 并肩作战 → 情感深化 → 共同面对 |
| 小九 | 觉醒型 | 初始状态 → 遇到主人 → 能力成长 → 完全觉醒 |
| 星月 | 悲剧型 | 美好往昔 → 命运转折 → 艰难考验 → 悲剧结局或突破 |
| 暗皇 | 反派型 | 展示力量 → 制造危机 → 升级冲突 → 被击败或洗白 |

## 阈值说明

| 维度 | 阈值 | 说明 |
|------|------|------|
| 情节关联度 | 自适应 | 短段落5点，中等7点，长段落10点 |
| 伏笔回收率 | 窗口50章 | 首次出现后50章内必须出现 |
| 场景逻辑 | 相似度<15% | 低于视为"孤岛章节" |
| 对话风格 | 字数超出典型范围2倍 | 可能是"串词" |
| 情感节奏 | 方差<0.01 | 整章无起伏视为单调 |

---

## 提示词模板

质量检查时可参考：
- `.claude/prompts/reviewer/quality-check-prompt.md` - 综合质量检查（10维度）
- `.claude/prompts/reviewer/consistency-check-prompt.md` - 情节一致性检查
- `.claude/prompts/reviewer/character-behavior-check-prompt.md` - 人物行为合理性检查
# 逻辑矛盾检测器增强方案

**日期**: 2026-05-28
**版本**: v1.0
**状态**: 设计阶段

---

## 1. 背景与问题

当前系统有 **16个检测器**，但仍有 **12大类逻辑矛盾无法检测**：

| 严重程度 | 矛盾类型 | 典型例子 |
|---------|---------|---------|
| **P0** | 因果断裂 | "A打破了B" → "B完好无损" |
| **P0** | 信息知晓矛盾 | A告诉了B秘密，但B后续毫无反应 |
| **P0** | 空间位置矛盾 | "在房间里" → "站在门外" 无过渡 |
| **P1** | 关系状态矛盾 | "A不信任B" → "A相信B" 无过渡 |
| **P1** | 言行不一 | "我不会丢下你" → 立刻离开 |
| P2 | 量化属性矛盾 | "100金币" 花了80还是"100金币" |
| P2 | 情感反应比例 | 刚认识的人死亡却极度悲伤 |
| P2 | 物理不可能 | 真空中声音传播 |
| P2 | 世界规则矛盾 | 修真世界出现现代科技 |
| P3 | 能力退化 | 精通技能却突然无法使用 |
| P3 | 伏笔回收矛盾 | 伏笔与回收方式矛盾 |
| P3 | 能力时机矛盾 | 使用未学会的能力 |

### 1.1 当前系统架构

```
ConsistencyEngine
├── 16 existing checkers
│   ├── CharacterChecker
│   ├── CharacterStateChecker
│   ├── ItemChecker
│   ├── TimelineChecker
│   └── ...
└── CrossChapterLogicChecker (仅追踪"离开"+"尸体"模式)
```

**问题**: 无统一实体状态追踪框架，各检测器各自为战。

---

## 2. 解决方案

### 方案2+3混合: 统一状态追踪框架 + LLM辅助推理

- **框架层**: EntityStateTracker + 规则检测器（解决明确矛盾）
- **推理层**: LLM辅助处理复杂因果（解决模糊矛盾）

---

## 3. 数据模型设计

### 3.1 核心实体状态模型

```python
from enum import Enum
from typing import Optional
from pydantic import BaseModel

class LocationState(BaseModel):
    location: str                          # "厨房"、"城外废弃庙宇"
    inDoor: bool | None                   # 是否在室内
    previous_location: str | None        # 上一个位置
    transition_type: str | None          # "walked", "teleported", "chased"

class KnowledgeState(BaseModel):
    known_secrets: set[str]               # 知道的秘密
    shared_with: dict[str, set[str]]      # {秘密: [告诉了谁]}
    forgot_secrets: set[str]              # 明确遗忘的秘密

class RelationshipState(BaseModel):
    trust_level: float                    # -1.0 ~ 1.0
    emotional_bond: float                # -1.0 ~ 1.0
    status: str                          # "strangers", "friends", "enemies", "lovers"
    last_status_change_chapter: int
    status_change_reason: str | None

class CapabilityState(BaseModel):
    abilities: set[str]                   # 已掌握的能力
    learning_in_progress: dict[str, str] # {能力: 学习进度}
    mastery_level: dict[str, float]       # {能力: 0.0~1.0}

class EntityState(BaseModel):
    entity_id: str
    entity_type: str                      # "character" | "item"

    alive: bool = True
    location: LocationState | None
    knowledge: KnowledgeState | None       # 仅character

    relationships: dict[str, RelationshipState]
    capabilities: CapabilityState | None  # 仅character

    owner: str | None                    # 物品特有
    condition: str | None                # "intact", "broken", "destroyed"

    action_history: list[dict]           # [{action, target, chapter}]

    def apply_action(self, action: str, target, chapter: int):
        self.action_history.append({
            "action": action,
            "target": target,
            "chapter": chapter
        })
```

### 3.2 因果断裂检测规则

```python
CAUSAL_BREAK_RULES = [
    {
        "action": "broke",
        "state_after": "destroyed",
        "contradiction_trigger": "intact",
        "resolution_required": ["repaired", "magical_restoration", "replaced"]
    },
    {
        "action": "killed",
        "state_after": "dead",
        "contradiction_trigger": "alive",
        "resolution_required": ["resurrected", "fake_death", "clone"]
    },
    {
        "action": "stole",
        "state_after": "taken",
        "contradiction_trigger": "still_owns",
        "resolution_required": ["returned", "reclaimed", "lost_stolen"]
    },
]
```

---

## 4. 新增检测器设计

| 检测器 | 输入 | 检测逻辑 | 输出Issue类型 |
|-------|------|---------|--------------|
| **CausalChainChecker** | EntityState + 当前章节动作 | 查action_history，匹配CAUSAL_BREAK_RULES | 因果断裂 |
| **KnowledgeTracker** | 当前章节对话/独白 | 检测"告诉"事件，更新knowledge.shared_with | 信息知晓矛盾 |
| **SpatialTransitionChecker** | 角色location + 动作词 | 检测"瞬间出现在某地"无过渡词 | 空间突兀转移 |
| **RelationshipStateChecker** | 两角色关系 + 新互动 | 关系变化>阈值且无过渡词 | 关系突变 |
| **DialogueActionChecker** | 对话+紧跟动作 | 检测矛盾指令(说A做B) | 言行不一 |
| **LLMCausalReasoningChecker** | 章节文本+上下文 | LLM推理复杂因果 | 复杂逻辑矛盾 |

### 4.1 CausalChainChecker

```python
class CausalChainChecker(BaseChecker):
    """检测因果断裂: A做了X，但Y没有发生相应改变"""

    def check(self, chapter_text: str, entity_states: dict) -> list[Issue]:
        issues = []
        for rule in CAUSAL_BREAK_RULES:
            # 1. 在当前章节查找动作触发词
            actions_found = self._find_action_trigger(chapter_text, rule["action"])
            for action in actions_found:
                target = action["target"]
                # 2. 检查目标实体状态
                target_state = entity_states.get(target)
                if not target_state:
                    continue
                # 3. 检查历史中是否有对应因果事件
                causal_events = [
                    e for e in target_state.action_history
                    if e["action"] == rule["action"]
                ]
                # 4. 检查当前章节是否有解决词
                has_resolution = self._check_resolution(
                    chapter_text, rule["resolution_required"]
                )
                # 5. 如果有因果历史但无解决词，且状态矛盾 → 报告Issue
                if causal_events and not has_resolution:
                    if self._check_state_contradiction(
                        chapter_text, rule["contradiction_trigger"]
                    ):
                        issues.append(Issue(
                            severity=P0,
                            issue_type="causal_chain_break",
                            title=f"因果断裂: {action['action']}后{target}状态矛盾",
                            description=f"前文显示{target}被{rule['action']}，但当前章节显示{rule['contradiction_trigger']}",
                            suggestion=f"需要加入: {rule['resolution_required']}"
                        ))
        return issues
```

### 4.2 LLMCausalReasoningChecker

```python
class LLMCausalReasoningChecker:
    """LLM辅助的复杂因果推理检测"""

    SYSTEM_PROMPT = """
    你是一个小说一致性检测专家。检测以下文本是否存在逻辑矛盾：
    1. 因果链断裂（A做了X，但Y没有发生相应改变）
    2. 情感反应不符合人物关系（刚认识的人死亡却极度悲伤）
    3. 物理不可能（修真世界中出现现代科技）
    4. 世界规则矛盾（前面说不能飞，后面却飞了）

    只报告真正的逻辑矛盾，不报告伏笔、视角切换造成的表面矛盾、夸张修辞。
    """

    def check(self, chapter_text: str, context: dict) -> list[Issue]:
        prompt = f"""
        当前章节:
        {chapter_text}

        角色设定:
        {context['character_profiles']}

        世界规则:
        {context['world_rules']}

        前文摘要:
        {context['previous_chapters_summary']}

        请检测上述场景中的逻辑矛盾，以JSON格式输出:
        {{
            "contradictions": [
                {{
                    "type": "causal_chain|emotional_proportion|physical_impossible|world_rule_violation",
                    "location": "具体段落",
                    "description": "矛盾描述",
                    "evidence": "证据",
                    "suggestion": "修复建议"
                }}
            ]
        }}
        """
        # 调用LLM处理...
```

---

## 5. 混合检测流程

```
检测流程:
1. 规则检测器先跑（快速、精确）→ 捕获已知类型
2. 剩余高置信度模糊区域 → LLM辅助推理
3. LLM结果 → 转换为Issue → ConsistencyReport
```

---

## 6. 实施计划

| 阶段 | 内容 | 产出 |
|------|------|------|
| **Phase 1** | EntityStateTracker框架 + 状态持久化 | 基础设施 |
| **Phase 2** | CausalChainChecker + SpatialTransitionChecker | 2个新检测器 |
| **Phase 3** | RelationshipStateChecker + KnowledgeTracker | 2个新检测器 |
| **Phase 4** | DialogueActionChecker | 1个新检测器 |
| **Phase 5** | LLMCausalReasoningChecker | 1个LLM辅助检测器 |

---

## 7. 检测能力对比

| 矛盾类型 | 修复前 | 修复后 |
|---------|-------|-------|
| 因果断裂 | ❌ | ✅ 规则+LLM |
| 信息知晓 | ❌ | ✅ |
| 空间位置 | ❌ | ✅ |
| 关系状态 | ❌ | ✅ |
| 言行不一 | ❌ | ✅ |
| 量化属性 | ❌ | ✅ |
| 情感反应 | ❌ | ✅ LLM |
| 物理可能 | ❌ | ✅ LLM |
| 世界规则 | ❌ | ✅ LLM |
| 能力退化 | ❌ | ✅ |
| 伏笔回收 | ⚠️ 已有 | ✅ 增强 |
| 能力时机 | ⚠️ 部分 | ✅ 增强 |

---

## 8. 待确认问题

1. **状态持久化方案**: SQLite / JSON文件 / Qdrant?
2. **LLM调用频率**: 每章必调 / 仅在规则检测触发时调用?
3. **检测优先级**: P0先做还是全部一起?
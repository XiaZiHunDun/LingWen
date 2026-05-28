# 逻辑矛盾检测器增强实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为灵文小说生产系统新增逻辑矛盾检测能力，覆盖12类当前无法检测的逻辑矛盾

**Architecture:** 在现有ConsistencyEngine框架下，新增EntityStateTracker作为共享基础设施，再分别实现5个规则检测器和1个LLM辅助检测器

**Tech Stack:** Python 3.13, Pydantic, pytest, SQLite (状态持久化)

---

## 文件结构

```
novel-factory/infra/consistency/
├── engine/
│   ├── data_structures.py          # 修改: 新增IssueSeverity/CheckerType枚举
│   └── consistency_engine.py       # 修改: 注册新检测器
├── checkers/
│   ├── base_checker.py             # 不改
│   ├── causal_chain_checker.py     # 新增: 因果断裂检测器
│   ├── spatial_transition_checker.py # 新增: 空间位置检测器
│   ├── relationship_state_checker.py # 新增: 关系状态检测器
│   ├── knowledge_tracker.py        # 新增: 信息知晓检测器
│   ├── dialogue_action_checker.py # 新增: 言行不一检测器
│   └── llm_causal_reasoning_checker.py # 新增: LLM辅助推理检测器
├── state/                          # 新增目录: 实体状态追踪
│   ├── __init__.py
│   ├── entity_state_tracker.py     # 核心: 统一状态追踪
│   ├── models.py                   # 核心: Pydantic数据模型
│   └── causal_rules.py             # 核心: 因果链规则库
└── tests/
    └── consistency/
        ├── test_entity_state_tracker.py
        ├── test_causal_chain_checker.py
        ├── test_spatial_transition.py
        └── test_relationship_state.py
```

---

## Phase 1: EntityStateTracker 基础设施

### Task 1: 创建状态数据模型

**Files:**
- Create: `novel-factory/infra/consistency/state/models.py`
- Test: `novel-factory/tests/consistency/test_entity_state_tracker.py` (先写测试)

- [ ] **Step 1: 写测试**

```python
# novel-factory/tests/consistency/test_entity_state_tracker.py
import pytest
from novel_factory.infra.consistency.state.models import (
    LocationState, KnowledgeState, RelationshipState,
    CapabilityState, EntityState
)

def test_location_state_creation():
    loc = LocationState(
        location="厨房",
        inDoor=True,
        previous_location="客厅",
        transition_type="walked"
    )
    assert loc.location == "厨房"
    assert loc.inDoor is True
    assert loc.previous_location == "客厅"

def test_entity_state_apply_action():
    entity = EntityState(
        entity_id="林夜",
        entity_type="character",
        alive=True
    )
    entity.apply_action("broke", target="茶杯", chapter=10)
    assert len(entity.action_history) == 1
    assert entity.action_history[0]["action"] == "broke"
    assert entity.action_history[0]["chapter"] == 10

def test_knowledge_state_share_secret():
    knowledge = KnowledgeState(
        known_secrets={"父亲的秘密"},
        shared_with={"林夜": {"父亲的秘密"}}
    )
    assert "父亲的秘密" in knowledge.known_secrets
    assert "林夜" in knowledge.shared_with
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest novel-factory/tests/consistency/test_entity_state_tracker.py::test_location_state_creation -v`
Expected: FAIL (模块不存在)

- [ ] **Step 3: 创建 models.py**

```python
# novel-factory/infra/consistency/state/models.py
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field

class LocationState(BaseModel):
    location: str = ""
    inDoor: Optional[bool] = None
    previous_location: Optional[str] = None
    transition_type: Optional[str] = None  # "walked", "teleported", "chased"

class KnowledgeState(BaseModel):
    known_secrets: set[str] = Field(default_factory=set)
    shared_with: dict[str, set[str]] = Field(default_factory=dict)  # {角色: {秘密}}
    forgot_secrets: set[str] = Field(default_factory=set)

class RelationshipState(BaseModel):
    trust_level: float = 0.0       # -1.0 ~ 1.0
    emotional_bond: float = 0.0   # -1.0 ~ 1.0
    status: str = "strangers"     # "strangers", "friends", "enemies", "lovers"
    last_status_change_chapter: int = 0
    status_change_reason: Optional[str] = None

class CapabilityState(BaseModel):
    abilities: set[str] = Field(default_factory=set)
    learning_in_progress: dict[str, str] = Field(default_factory=dict)  # {能力: 进度}
    mastery_level: dict[str, float] = Field(default_factory=dict)  # {能力: 0.0~1.0}

class EntityState(BaseModel):
    entity_id: str
    entity_type: str = "character"  # "character" | "item"
    alive: bool = True
    
    location: Optional[LocationState] = None
    knowledge: Optional[KnowledgeState] = None
    
    relationships: dict[str, RelationshipState] = Field(default_factory=dict)
    capabilities: Optional[CapabilityState] = None
    
    owner: Optional[str] = None
    condition: Optional[str] = None  # "intact", "broken", "destroyed"
    
    action_history: list[dict] = Field(default_factory=list)
    
    def apply_action(self, action: str, target: str, chapter: int):
        self.action_history.append({
            "action": action,
            "target": target,
            "chapter": chapter
        })
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest novel-factory/tests/consistency/test_entity_state_tracker.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add novel-factory/infra/consistency/state/models.py novel-factory/tests/consistency/test_entity_state_tracker.py
git commit -m "feat: add EntityState data models for logical contradiction tracking"
```

---

### Task 2: 创建EntityStateTracker

**Files:**
- Create: `novel-factory/infra/consistency/state/entity_state_tracker.py`
- Modify: `novel-factory/infra/consistency/state/__init__.py`
- Test: `novel-factory/tests/consistency/test_entity_state_tracker.py` (追加测试)

- [ ] **Step 1: 写测试**

```python
def test_entity_state_tracker_save_and_load():
    tracker = EntityStateTracker()
    
    entity = EntityState(entity_id="林夜", entity_type="character")
    entity.location = LocationState(location="厨房")
    entity.apply_action("broke", target="茶杯", chapter=10)
    
    tracker.save_entity_state("林夜", entity)
    
    loaded = tracker.get_entity_state("林夜")
    assert loaded is not None
    assert loaded.entity_id == "林夜"
    assert loaded.location.location == "厨房"
    assert len(loaded.action_history) == 1

def test_entity_state_tracker_update_location():
    tracker = EntityStateTracker()
    
    # 初始位置
    tracker.update_location("林夜", "客厅", transition="walked", chapter=5)
    
    # 转移到新位置
    tracker.update_location("林夜", "厨房", transition="walked", chapter=10)
    
    entity = tracker.get_entity_state("林夜")
    assert entity.location.location == "厨房"
    assert entity.location.previous_location == "客厅"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest novel-factory/tests/consistency/test_entity_state_tracker.py -v`
Expected: FAIL (EntityStateTracker not defined)

- [ ] **Step 3: 创建 entity_state_tracker.py**

```python
# novel-factory/infra/consistency/state/entity_state_tracker.py
import json
from pathlib import Path
from typing import Optional, Dict
from .models import EntityState

class EntityStateTracker:
    """实体状态追踪器 - 跨章节维护角色/物品状态"""
    
    def __init__(self, state_dir: Optional[str] = None):
        if state_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent
            state_dir = project_root / ".state" / "entity_states"
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, EntityState] = {}
    
    def _get_state_file(self, entity_id: str) -> Path:
        # 规范化文件名
        safe_id = entity_id.replace("/", "_").replace("\\", "_")
        return self.state_dir / f"{safe_id}.json"
    
    def save_entity_state(self, entity_id: str, state: EntityState):
        """保存实体状态到磁盘"""
        self._cache[entity_id] = state
        file_path = self._get_state_file(entity_id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(state.model_dump(), f, ensure_ascii=False, indent=2)
    
    def get_entity_state(self, entity_id: str) -> Optional[EntityState]:
        """获取实体状态（优先从缓存）"""
        if entity_id in self._cache:
            return self._cache[entity_id]
        
        file_path = self._get_state_file(entity_id)
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            state = EntityState.model_validate(data)
            self._cache[entity_id] = state
            return state
        except Exception:
            return None
    
    def update_location(
        self,
        entity_id: str,
        new_location: str,
        transition: Optional[str] = None,
        chapter: int = 0
    ):
        """更新实体位置"""
        state = self.get_entity_state(entity_id) or EntityState(
            entity_id=entity_id,
            entity_type="character"
        )
        
        from .models import LocationState
        prev = state.location.location if state.location else None
        state.location = LocationState(
            location=new_location,
            previous_location=prev,
            transition_type=transition
        )
        self.save_entity_state(entity_id, state)
    
    def record_action(
        self,
        entity_id: str,
        action: str,
        target: str,
        chapter: int
    ):
        """记录实体动作"""
        state = self.get_entity_state(entity_id) or EntityState(
            entity_id=entity_id,
            entity_type="character"
        )
        state.apply_action(action, target, chapter)
        self.save_entity_state(entity_id, state)
    
    def load_all_states(self) -> Dict[str, EntityState]:
        """加载所有实体状态"""
        states = {}
        for file_path in self.state_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                entity = EntityState.model_validate(data)
                states[entity.entity_id] = entity
            except Exception:
                continue
        return states
```

- [ ] **Step 4: 创建 __init__.py**

```python
# novel-factory/infra/consistency/state/__init__.py
from .models import (
    LocationState,
    KnowledgeState,
    RelationshipState,
    CapabilityState,
    EntityState,
)
from .entity_state_tracker import EntityStateTracker

__all__ = [
    "LocationState",
    "KnowledgeState",
    "RelationshipState",
    "CapabilityState",
    "EntityState",
    "EntityStateTracker",
]
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest novel-factory/tests/consistency/test_entity_state_tracker.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add novel-factory/infra/consistency/state/
git commit -m "feat: add EntityStateTracker for cross-chapter entity state management"
```

---

### Task 3: 创建因果断裂规则库

**Files:**
- Create: `novel-factory/infra/consistency/state/causal_rules.py`
- Test: `novel-factory/tests/consistency/test_causal_chain_checker.py`

- [ ] **Step 1: 写测试**

```python
# novel-factory/tests/consistency/test_causal_chain_checker.py
import pytest
from novel_factory.infra.consistency.state.causal_rules import CAUSAL_BREAK_RULES, CausalRuleEngine

def test_causal_rules_has_required_fields():
    for rule in CAUSAL_BREAK_RULES:
        assert "action" in rule
        assert "state_after" in rule
        assert "contradiction_trigger" in rule
        assert "resolution_required" in rule

def test_causal_rule_engine_match_action():
    engine = CausalRuleEngine()
    matches = engine.match_action("打破了", "茶杯")
    assert len(matches) > 0
    assert matches[0]["action"] == "broke"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest novel-factory/tests/consistency/test_causal_chain_checker.py -v`
Expected: FAIL

- [ ] **Step 3: 创建 causal_rules.py**

```python
# novel-factory/infra/consistency/state/causal_rules.py
"""
因果断裂检测规则库

定义所有因果链断裂的触发条件和解决条件
"""

CAUSAL_BREAK_RULES = [
    {
        "action": "broke",
        "action_keywords": ["打破了", "击碎", "粉碎", "毁坏"],
        "state_after": "destroyed",
        "contradiction_trigger": "完好无损",
        "contradiction_patterns": ["完好无损", "完整无缺", "丝毫无损"],
        "resolution_required": ["修复", "修补", "复原", "神奇恢复", "换了一个"],
        "severity": "P0"
    },
    {
        "action": "killed",
        "action_keywords": ["杀死了", "击杀了", "灭杀", "诛杀"],
        "state_after": "dead",
        "contradiction_trigger": "活着",
        "contradiction_patterns": ["活着", "生存", "气息尚存", "并未真正死亡"],
        "resolution_required": ["复活", "假死", "替身", "逃亡", "救治"],
        "severity": "P0"
    },
    {
        "action": "stole",
        "action_keywords": ["偷走了", "盗取", "窃取"],
        "state_after": "taken",
        "contradiction_trigger": "仍然持有",
        "contradiction_patterns": ["仍然持有", "还在", "未曾丢失"],
        "resolution_required": ["归还", "夺回", "丢失后找回"],
        "severity": "P1"
    },
    {
        "action": "revealed_secret",
        "action_keywords": ["揭露了秘密", "说出了真相", "告知"],
        "state_after": "known",
        "contradiction_trigger": "不知情",
        "contradiction_patterns": ["不知道", "毫不知情", "并未得知"],
        "resolution_required": ["忘记", "失忆", "故意隐瞒"],
        "severity": "P1"
    },
]

class CausalRuleEngine:
    """因果规则引擎 - 匹配动作和状态"""
    
    def __init__(self, rules=None):
        self.rules = rules or CAUSAL_BREAK_RULES
    
    def match_action(self, action_text: str, target: str) -> list[dict]:
        """匹配动作文本"""
        results = []
        for rule in self.rules:
            for keyword in rule["action_keywords"]:
                if keyword in action_text:
                    results.append({
                        "rule": rule,
                        "action": rule["action"],
                        "target": target,
                        "keyword": keyword
                    })
        return results
    
    def match_contradiction(self, text: str, rule: dict) -> bool:
        """检测文本中是否存在状态矛盾"""
        for pattern in rule["contradiction_patterns"]:
            if pattern in text:
                return True
        return False
    
    def match_resolution(self, text: str, rule: dict) -> bool:
        """检测文本中是否存在解决词"""
        for keyword in rule["resolution_required"]:
            if keyword in text:
                return True
        return False
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest novel-factory/tests/consistency/test_causal_chain_checker.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add novel-factory/infra/consistency/state/causal_rules.py novel-factory/tests/consistency/test_causal_chain_checker.py
git commit -m "feat: add causal break rules engine"
```

---

## Phase 2: CausalChainChecker + SpatialTransitionChecker

### Task 4: 创建CausalChainChecker

**Files:**
- Create: `novel-factory/infra/consistency/checkers/causal_chain_checker.py`
- Modify: `novel-factory/infra/consistency/engine/data_structures.py` (添加CheckerType)
- Modify: `novel-factory/infra/consistency/engine/consistency_engine.py` (注册检测器)
- Test: `novel-factory/tests/consistency/test_causal_chain_checker.py` (扩展测试)

- [ ] **Step 1: 写测试**

```python
def test_causal_chain_checker_detects_broken_pot():
    from novel_factory.infra.consistency.checkers.causal_chain_checker import CausalChainChecker
    
    checker = CausalChainChecker()
    
    # 场景: A打破了B茶杯，但B茶杯完好无损出现
    chapter_content = """
    林夜一掌拍出，真气涌动，将陈手中的茶杯击得粉碎。
    茶杯的碎片散落一地，清脆的声响在房间中回荡。
    
    片刻后，陈依然手持茶杯，完好无损地站在原地。
    """
    
    issues = checker.check(chapter_content, chapter_num=10, context={})
    
    assert len(issues) > 0
    assert any(i.issue_type == "causal_chain_break" for i in issues)

def test_causal_chain_checker_no_issue_when_resolved():
    from novel_factory.infra.consistency.checkers.causal_chain_checker import CausalChainChecker
    
    checker = CausalChainChecker()
    
    # 场景: A打破了B茶杯，但有修复说明
    chapter_content = """
    林夜一掌拍出，真气涌动，将陈手中的茶杯击得粉碎。
    茶杯的碎片散落一地，清脆的声响在房间中回荡。
    
    陈从怀中取出另一个茶杯，仿佛无事发生。
    """
    
    issues = checker.check(chapter_content, chapter_num=10, context={})
    
    # 应该有较少的Issue或没有（因为有替换解决方案）
    assert len(issues) == 0
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest novel-factory/tests/consistency/test_causal_chain_checker.py::test_causal_chain_checker_detects_broken_pot -v`
Expected: FAIL (模块不存在)

- [ ] **Step 3: 创建 causal_chain_checker.py**

```python
# novel-factory/infra/consistency/checkers/causal_chain_checker.py
import re
from typing import List, Dict, Any, Optional
from infra.consistency.engine.data_structures import (
    Issue, IssueLocation, CheckerType, IssueSeverity
)
from .base_checker import BaseChecker

class CausalChainChecker(BaseChecker):
    """因果断裂检测器 - 检测A做了X但Y没有发生相应改变"""
    
    def __init__(self):
        super().__init__(CheckerType.CAUSAL_CHAIN)
        from ..state.causal_rules import CAUSAL_BREAK_RULES, CausalRuleEngine
        from ..state.entity_state_tracker import EntityStateTracker
        
        self.rules = CAUSAL_BREAK_RULES
        self.rule_engine = CausalRuleEngine(self.rules)
        self.tracker = EntityStateTracker()
    
    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        issues = []
        
        # 1. 查找当前章节中的动作触发词
        for rule in self.rules:
            for keyword in rule["action_keywords"]:
                if keyword in chapter_content:
                    # 提取动作和目标
                    matches = self._find_action_with_target(chapter_content, keyword)
                    for match in matches:
                        target = match["target"]
                        action_text = match["text"]
                        
                        # 2. 检查该目标的历史状态（是否被此动作影响）
                        entity_state = self.tracker.get_entity_state(target)
                        has_causal_history = (
                            entity_state and
                            any(e["action"] == rule["action"] for e in entity_state.action_history)
                        )
                        
                        # 3. 如果有因果历史，检查当前章节是否有矛盾
                        if has_causal_history:
                            if self.rule_engine.match_contradiction(chapter_content, rule):
                                if not self.rule_engine.match_resolution(chapter_content, rule):
                                    issues.append(self._create_issue(rule, match, chapter_num))
                        
                        # 4. 记录当前动作到历史
                        self.tracker.record_action(
                            entity_id=target,
                            action=rule["action"],
                            target=target,
                            chapter=chapter_num
                        )
        
        return issues
    
    def _find_action_with_target(self, text: str, keyword: str) -> List[Dict]:
        """查找动作及其目标"""
        results = []
        # 模式: [动作词] + [任意内容] + [目标名]
        pattern = f'{re.escape(keyword)}(.{{0,30}}?)([\\u4e00-\\u9fa5]{{2,8}}(?:茶杯|剑|书|物|人|家伙))'
        for m in re.finditer(pattern, text):
            results.append({
                "text": m.group(),
                "target": m.group(2),
                "action": keyword
            })
        return results
    
    def _create_issue(self, rule: dict, match: dict, chapter_num: int) -> Issue:
        severity = IssueSeverity.P0 if rule.get("severity") == "P0" else IssueSeverity.P1
        return Issue(
            id=f"CC_{chapter_num:03d}_{match['target']}",
            severity=severity,
            checker_type=CheckerType.CAUSAL_CHAIN,
            issue_type="causal_chain_break",
            title=f"因果断裂: {match['action']}后{match['target']}状态矛盾",
            description=f"前文显示{match['target']}被{match['action']}，但当前章节显示{rule['contradiction_trigger']}",
            location=IssueLocation(chapter=chapter_num),
            evidence=f"匹配: {match['text'][:50]}",
            suggestion=f"需要加入: {', '.join(rule['resolution_required'])}"
        )
```

- [ ] **Step 4: 添加CheckerType枚举值**

找到 `data_structures.py` 中的 `CheckerType` 枚举，添加:
```python
CAUSAL_CHAIN = "causal_chain"
SPATIAL_TRANSITION = "spatial_transition"
RELATIONSHIP_STATE = "relationship_state"
KNOWLEDGE_TRACKING = "knowledge_tracking"
DIALOGUE_ACTION = "dialogue_action"
LLM_CAUSAL_REASONING = "llm_causal_reasoning"
```

- [ ] **Step 5: 注册到ConsistencyEngine**

在 `_init_checkers()` 方法中添加新的检测器导入和注册

- [ ] **Step 6: 运行测试确认通过**

Run: `pytest novel-factory/tests/consistency/test_causal_chain_checker.py -v`
Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add novel-factory/infra/consistency/checkers/causal_chain_checker.py
git commit -m "feat: add CausalChainChecker for detecting broken causal chains"
```

---

### Task 5: 创建SpatialTransitionChecker

**Files:**
- Create: `novel-factory/infra/consistency/checkers/spatial_transition_checker.py`
- Test: `novel-factory/tests/consistency/test_spatial_transition.py`

- [ ] **Step 1: 写测试**

```python
def test_spatial_transition_detects_instant_movement():
    from novel_factory.infra.consistency.checkers.spatial_transition_checker import SpatialTransitionChecker
    
    checker = SpatialTransitionChecker()
    
    chapter_content = """
    林夜站在客厅之中，神色凝重。
    突然，一道光芒闪过，林夜直接出现在厨房里。
    """
    
    issues = checker.check(chapter_content, chapter_num=10, context={})
    
    assert len(issues) > 0
    assert any(i.issue_type == "spatial_transition" for i in issues)

def test_spatial_transition_no_issue_with_transition_word():
    from novel_factory.infra.consistency.checkers.spatial_transition_checker import SpatialTransitionChecker
    
    checker = SpatialTransitionChecker()
    
    chapter_content = """
    林夜站在客厅之中，神色凝重。
    他转身离开客厅，穿过走廊，来到厨房。
    """
    
    issues = checker.check(chapter_content, chapter_num=10, context={})
    
    assert len(issues) == 0
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 创建 spatial_transition_checker.py**

```python
# novel-factory/infra/consistency/checkers/spatial_transition_checker.py
import re
from typing import List, Dict, Any, Optional, Tuple
from infra.consistency.engine.data_structures import (
    Issue, IssueLocation, CheckerType, IssueSeverity
)
from .base_checker import BaseChecker

class SpatialTransitionChecker(BaseChecker):
    """空间位置突兀转移检测器"""
    
    # 突兀转移模式（无过渡词直接出现新位置）
    SUDDEN_TRANSITION_PATTERNS = [
        r"突然出现在(.+?)。",
        r"瞬间来到(.+?)。",
        r"一闪来到(.+?)。",
        r"直接到了(.+?)。",
    ]
    
    # 合理的过渡词
    TRANSITION_WORDS = [
        "穿过", "走过", "经过", "来到", "走进", "进入",
        "离开", "走出", "前往", "迂回", "绕到",
        "腾空而起", "御剑飞行", "瞬移", "传送"
    ]
    
    def __init__(self):
        super().__init__(CheckerType.SPATIAL_TRANSITION)
        from ..state.entity_state_tracker import EntityStateTracker
        self.tracker = EntityStateTracker()
    
    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        issues = []
        
        # 查找突兀转移模式
        for pattern in self.SUDDEN_TRANSITION_PATTERNS:
            for m in re.finditer(pattern, chapter_content):
                new_location = m.group(1)
                before_text = chapter_content[max(0, m.start()-100):m.start()]
                
                # 检查前面是否有合理的过渡词
                if not self._has_transition_word(before_text):
                    # 检查角色之前的位置
                    character = self._extract_character(before_text)
                    if character:
                        prev_state = self.tracker.get_entity_state(character)
                        if prev_state and prev_state.location:
                            issues.append(self._create_issue(
                                character, prev_state.location.location,
                                new_location, m.group(), chapter_num
                            ))
        
        return issues
    
    def _has_transition_word(self, text: str) -> bool:
        for word in self.TRANSITION_WORDS:
            if word in text:
                return True
        return False
    
    def _extract_character(self, text: str) -> Optional[str]:
        # 简单策略：取前50字内的主要角色名
        patterns = ["林夜", "苏琳", "莫言", "陈", "王"]
        for name in patterns:
            if name in text:
                return name
        return None
    
    def _create_issue(
        self,
        character: str,
        prev_location: str,
        new_location: str,
        evidence: str,
        chapter_num: int
    ) -> Issue:
        return Issue(
            id=f"ST_{chapter_num:03d}_{character}",
            severity=IssueSeverity.P1,
            checker_type=CheckerType.SPATIAL_TRANSITION,
            issue_type="spatial_transition",
            title=f"空间突兀转移: {character}从{prev_location}到{new_location}",
            description=f"角色'{character}'从'{prev_location}'直接出现在'{new_location}'，无过渡描述",
            location=IssueLocation(chapter=chapter_num),
            evidence=f"匹配: {evidence[:50]}",
            suggestion=f"需要加入过渡描述（走过、穿过、来到等）"
        )
```

- [ ] **Step 4: 运行测试确认通过**

- [ ] **Step 5: 提交**

---

## Phase 3: RelationshipStateChecker + KnowledgeTracker

### Task 6: 创建RelationshipStateChecker

**Files:**
- Create: `novel-factory/infra/consistency/checkers/relationship_state_checker.py`
- Test: `novel-factory/tests/consistency/test_relationship_state.py`

### Task 7: 创建KnowledgeTracker

**Files:**
- Create: `novel-factory/infra/consistency/checkers/knowledge_tracker.py`
- Test: `novel-factory/tests/consistency/test_knowledge_tracker.py`

---

## Phase 4: DialogueActionChecker

### Task 8: 创建DialogueActionChecker

**Files:**
- Create: `novel-factory/infra/consistency/checkers/dialogue_action_checker.py`
- Test: `novel-factory/tests/consistency/test_dialogue_action.py`

---

## Phase 5: LLMCausalReasoningChecker

### Task 9: 创建LLMCausalReasoningChecker

**Files:**
- Create: `novel-factory/infra/consistency/checkers/llm_causal_reasoning_checker.py`
- Modify: `novel-factory/infra/consistency/engine/consistency_engine.py`
- Test: `novel-factory/tests/consistency/test_llm_causal_reasoning.py`

---

## 检测能力对比（完成后）

| 矛盾类型 | 修复前 | 修复后 |
|---------|-------|-------|
| 因果断裂 | ❌ | ✅ |
| 信息知晓 | ❌ | ✅ |
| 空间位置 | ❌ | ✅ |
| 关系状态 | ❌ | ✅ |
| 言行不一 | ❌ | ✅ |
| 量化属性 | ❌ | ✅ |
| 情感反应 | ❌ | ✅ LLM |
| 物理可能 | ❌ | ✅ LLM |
| 世界规则 | ❌ | ✅ LLM |
| 能力退化 | ❌ | ✅ |
| 伏笔回收 | ⚠️ | ✅ 增强 |
| 能力时机 | ⚠️ | ✅ 增强 |

---

## 自检清单

- [ ] Spec coverage: 每个设计需求都有对应task
- [ ] Placeholder scan: 无"TBD"、"TODO"残留
- [ ] Type consistency: 类型签名一致
- [ ] 测试覆盖: 每个检测器都有测试用例
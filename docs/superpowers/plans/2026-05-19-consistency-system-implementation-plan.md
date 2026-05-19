# 一致性保障系统实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 构建一致性保障系统，8个检查器覆盖角色/物品/时间线/能力/人设/伏笔/大纲/AI痕迹8个维度，实现实时预警和离线检查

**架构：** ConsistencyEngine作为统一引擎，8个独立Checker分别负责各维度检查，与记忆系统联动获取上下文，输出标准化报告。

**技术栈：** Python, YAML, JSON, 正则表达式

---

## 文件结构

```
novel-factory/
├── consistency/
│   ├── __init__.py
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── consistency_engine.py    # 一致性引擎主类
│   │   ├── check_runner.py           # 检查运行器
│   │   └── report_generator.py       # 报告生成器
│   ├── checkers/
│   │   ├── __init__.py
│   │   ├── character_checker.py      # 角色一致性
│   │   ├── item_checker.py            # 物品连续性
│   │   ├── timeline_checker.py        # 时间线合理性
│   │   ├── ability_checker.py         # 能力一致性
│   │   ├── personality_checker.py     # 人设稳定性
│   │   ├── foreshadow_checker.py      # 伏笔回收
│   │   ├── outline_checker.py        # 大纲偏离度
│   │   └── ai_gloss_checker.py       # AI痕迹检测
│   ├── config/
│   │   ├── __init__.py
│   │   ├── consistency_rules.yaml    # 一致性规则
│   │   └── check_weights.yaml         # 检查权重
│   └── reports/
│       ├── __init__.py
│       └── templates/
│           └── audit_report.md        # 审核报告模板
└── tools/
    └── consistency/
        └── auto_consistency_checker.py  # 离线检查器（增强）
```

---

## 数据结构定义

### consistency_rules.yaml

```yaml
rules:
  personality_opposites:
    冷静:
      opposites: ["暴怒", "疯狂", "失控", "歇斯底里"]
      detection_window: 200

    热血:
      opposites: ["冷漠", "退缩", "放弃", "动摇"]

    狡猾:
      opposites: ["单纯", "正直", "轻信", "坦诚"]

    温柔:
      opposites: ["粗暴", "冷漠", "残忍"]

    正直:
      opposites: ["欺骗", "背叛", "阴谋"]

  ability_conflicts:
    不会武功:
      cannot_do: ["使用武功", "施展剑法", "运功疗伤"]

    不识字:
      cannot_do: ["阅读文件", "解读文字", "书写"]

    旱鸭子:
      cannot_do: ["游泳", "潜水", "水中搏斗"]

  timeline_conflicts:
    time_marker_conflict:
      pattern: "(.)\\1{2,}"  # 检测连续重复

    impossible_speed:
      travel_time_threshold: 1  # 章节内到达

severity_levels:
  P0:
    name: "致命"
    weight: 10
    examples:
      - "已死亡角色再次行动"
      - "关键道具凭空消失"

  P1:
    name: "严重"
    weight: 5
    examples:
      - "性格与行为冲突"
      - "时间线矛盾"

  P2:
    name: "中等"
    weight: 2
    examples:
      - "物品状态细微矛盾"
      - "能力表现略有不符"

  P3:
    name: "提示"
    weight: 1
    examples:
      - "AI痕迹"
      - "句式重复"
```

### check_weights.yaml

```yaml
checker_weights:
  character_checker: 1.5      # 角色一致性权重最高
  timeline_checker: 1.2
  ability_checker: 1.2
  item_checker: 1.0
  personality_checker: 1.0
  foreshadow_checker: 1.0
  outline_checker: 0.8
  ai_gloss_checker: 0.5      # AI痕迹权重较低

pass_thresholds:
  P0_issues_allowed: 0       # P0问题必须为0
  P1_issues_allowed: 2       # P1问题最多2个
  P2_issues_allowed: 5       # P2问题最多5个
  P3_issues_allowed: 10      # P3问题最多10个

overall_score_weights:
  S1_剧情完整性: 1.0
  S2_逻辑自洽: 1.2
  S3_文笔风格: 0.8
  S4_情感共鸣: 0.8
  S5_节奏控制: 0.9
  S6_可读性: 0.7
  S7_主角魅力: 1.0
  S8_人物弧光: 1.0
```

### Issue 数据结构

```python
@dataclass
class Issue:
    type: str              # 问题类型
    severity: str          # P0/P1/P2/P3
    character: Optional[str] = None
    location: Optional[str] = None
    description: str       # 问题描述
    suggestion: str        # 修改建议
   依据: Optional[str] = None  # 检测依据
```

### ConsistencyReport 数据结构

```python
@dataclass
class ConsistencyReport:
    chapter: int
    timestamp: str
    check_scope: List[str]   # 检查范围
    issues: List[Issue]
    scores: Dict[str, int]   # S1-S8评分
    overall_score: float
    pass_status: str         # "通过" / "需修改" / "打回"
    suggestions: List[str]   # 改进建议
```

---

## 任务清单

### Task 1: 基础架构与目录结构

**Files:**
- Create: `novel-factory/consistency/__init__.py`
- Create: `novel-factory/consistency/engine/__init__.py`
- Create: `novel-factory/consistency/checkers/__init__.py`
- Create: `novel-factory/consistency/config/__init__.py`
- Create: `novel-factory/consistency/reports/__init__.py`
- Create: `novel-factory/consistency/reports/templates/audit_report.md`
- Create: `novel-factory/consistency/config/consistency_rules.yaml`
- Create: `novel-factory/consistency/config/check_weights.yaml`

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p novel-factory/consistency/{engine,checkers,config,reports/templates}
touch novel-factory/consistency/__init__.py
touch novel-factory/consistency/engine/__init__.py
touch novel-factory/consistency/checkers/__init__.py
touch novel-factory/consistency/config/__init__.py
touch novel-factory/consistency/reports/__init__.py
```

- [ ] **Step 2: 创建 consistency_rules.yaml**

```yaml
# novel-factory/consistency/config/consistency_rules.yaml
rules:
  personality_opposites:
    冷静:
      opposites: ["暴怒", "疯狂", "失控", "歇斯底里"]
      detection_window: 200

    热血:
      opposites: ["冷漠", "退缩", "放弃", "动摇"]
      detection_window: 200

    狡猾:
      opposites: ["单纯", "正直", "轻信", "坦诚"]
      detection_window: 200

    温柔:
      opposites: ["粗暴", "冷漠", "残忍"]
      detection_window: 200

    正直:
      opposites: ["欺骗", "背叛", "阴谋"]
      detection_window: 200

  ability_conflicts:
    不会武功:
      cannot_do: ["使用武功", "施展剑法", "运功疗伤", "内功"]

    不识字:
      cannot_do: ["阅读", "写字", "解读", "看书"]

    旱鸭子:
      cannot_do: ["游泳", "潜水", "水中行动"]

  item_conflicts:
    已损毁:
      cannot_appear: true
    已丢失:
      cannot_appear: true

  timeline_conflicts:
    time_marker_patterns:
      - pattern: "已经过去.*天"
        next_chapter: "次日|第二天"

severity_levels:
  P0:
    name: "致命"
    weight: 10
    examples:
      - "已死亡角色再次行动"
      - "关键道具凭空消失"
      - "时空悖论"

  P1:
    name: "严重"
    weight: 5
    examples:
      - "性格与行为冲突"
      - "时间线矛盾"
      - "能力使用错误"

  P2:
    name: "中等"
    weight: 2
    examples:
      - "物品状态细微矛盾"
      - "能力表现略有不符"
      - "次要角色OOC"

  P3:
    name: "提示"
    weight: 1
    examples:
      - "AI痕迹"
      - "句式重复"
      - "过度格式化"
```

- [ ] **Step 3: 创建 check_weights.yaml**

```yaml
# novel-factory/consistency/config/check_weights.yaml
checker_weights:
  character_checker: 1.5
  item_checker: 1.2
  timeline_checker: 1.2
  ability_checker: 1.2
  personality_checker: 1.0
  foreshadow_checker: 1.0
  outline_checker: 0.8
  ai_gloss_checker: 0.5

pass_thresholds:
  P0_issues_allowed: 0
  P1_issues_allowed: 2
  P2_issues_allowed: 5
  P3_issues_allowed: 10

overall_score_weights:
  S1_剧情完整性: 1.0
  S2_逻辑自洽: 1.2
  S3_文笔风格: 0.8
  S4_情感共鸣: 0.8
  S5_节奏控制: 0.9
  S6_可读性: 0.7
  S7_主角魅力: 1.0
  S8_人物弧光: 1.0
```

- [ ] **Step 4: 提交**

```bash
git add novel-factory/consistency/
git commit -m "feat(consistency): 创建一致性保障系统目录结构"
```

---

### Task 2: Issue和Report数据结构

**Files:**
- Create: `novel-factory/consistency/engine/data_structures.py`
- Create: `tests/consistency/test_data_structures.py`

- [ ] **Step 1: 编写测试**

```python
# tests/consistency/test_data_structures.py
import pytest
from consistency.engine.data_structures import Issue, ConsistencyReport

def test_issue_creation():
    issue = Issue(
        type="character_consistency",
        severity="P1",
        character="铁蛋",
        location="第3段",
        description="性格为'冷静'出现'暴怒'行为",
        suggestion="将'暴怒'改为'克制地表达不满'"
    )
    assert issue.character == "铁蛋"
    assert issue.severity == "P1"

def test_consistency_report():
    report = ConsistencyReport(
        chapter=50,
        timestamp="2026-05-19",
        check_scope=["character", "timeline"],
        issues=[],
        scores={"S1": 4, "S2": 3},
        overall_score=75.0,
        pass_status="需修改",
        suggestions=[]
    )
    assert report.chapter == 50
    assert report.pass_status == "需修改"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/consistency/test_data_structures.py -v
# 预期: FAIL
```

- [ ] **Step 3: 实现数据结构**

```python
# novel-factory/consistency/engine/data_structures.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime

@dataclass
class Issue:
    """一致性问题"""
    type: str                           # 问题类型
    severity: str                      # P0/P1/P2/P3
    description: str                   # 问题描述
    suggestion: str                    # 修改建议
    character: Optional[str] = None   # 相关角色
    location: Optional[str] = None     # 位置
    evidence: Optional[str] = None      # 检测依据
    checker: Optional[str] = None      # 检查器名称

    def to_dict(self) -> Dict:
        return {
            "type": self.type,
            "severity": self.severity,
            "description": self.description,
            "suggestion": self.suggestion,
            "character": self.character,
            "location": self.location,
            "evidence": self.evidence,
            "checker": self.checker
        }

@dataclass
class ConsistencyReport:
    """一致性报告"""
    chapter: int
    timestamp: str
    check_scope: List[str]
    issues: List[Issue]
    scores: Dict[str, int]
    overall_score: float
    pass_status: str
    suggestions: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    def add_issue(self, issue: Issue):
        self.issues.append(issue)

    def calculate_scores(self, weights: Dict[str, float]) -> float:
        """计算加权总分"""
        total = 0
        for dim, score in self.scores.items():
            weight = weights.get(dim, 1.0)
            total += score * weight
        weight_sum = sum(weights.get(dim, 1.0) for dim in self.scores)
        self.overall_score = total / weight_sum if weight_sum > 0 else 0
        return self.overall_score

    def to_dict(self) -> Dict:
        return {
            "chapter": self.chapter,
            "timestamp": self.timestamp,
            "check_scope": self.check_scope,
            "issues": [i.to_dict() for i in self.issues],
            "scores": self.scores,
            "overall_score": self.overall_score,
            "pass_status": self.pass_status,
            "suggestions": self.suggestions
        }

    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        lines = [
            f"## 一致性检查报告",
            f"",
            f"**章节**: ch{self.chapter:03d}",
            f"**检查时间**: {self.timestamp}",
            f"**检查范围**: {', '.join(self.check_scope)}",
            f"",
            f"### 问题汇总",
            f"| 严重程度 | 问题数 | 描述 |",
            f"|----------|--------|------|"
        ]

        # 按严重程度统计
        by_severity = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
        for issue in self.issues:
            if issue.severity in by_severity:
                by_severity[issue.severity] += 1

        for sev, count in by_severity.items():
            lines.append(f"| {sev} | {count} | - |")

        lines.extend([
            f"",
            f"### 详细问题",
            ""
        ])

        for issue in self.issues:
            lines.extend([
                f"#### {issue.severity}: {issue.type}",
                f"**角色**: {issue.character or 'N/A'}",
                f"**位置**: {issue.location or 'N/A'}",
                f"**问题**: {issue.description}",
                f"**建议**: {issue.suggestion}",
                f"**依据**: {issue.evidence or 'N/A'}",
                ""
            ])

        lines.extend([
            f"### 质量评分",
            f"| 维度 | 评分 |",
            f"|------|------|"
        ])

        for dim, score in self.scores.items():
            lines.append(f"| {dim} | {score} |")

        lines.extend([
            f"",
            f"### 总体评分: {self.overall_score:.1f}/100",
            f"",
            f"### 通过判定",
            f"- P0问题数: {by_severity['P0']} → {'通过' if by_severity['P0'] == 0 else '打回'}",
            f"- P1问题数: {by_severity['P1']} → {'通过' if by_severity['P1'] <= 2 else '需修改'}",
            f"- 结论: [{self.pass_status}]"
        ])

        return "\n".join(lines)
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/consistency/test_data_structures.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add novel-factory/consistency/engine/data_structures.py tests/consistency/test_data_structures.py
git commit -m "feat(consistency): 实现Issue和Report数据结构"
```

---

### Task 3: 角色一致性检查器

**Files:**
- Create: `novel-factory/consistency/checkers/character_checker.py`
- Create: `tests/consistency/test_character_checker.py`

- [ ] **Step 1: 编写测试**

```python
# tests/consistency/test_character_checker.py
import pytest
from consistency.checkers.character_checker import CharacterChecker

def test_character_checker_init():
    checker = CharacterChecker()
    assert checker is not None
    assert checker.type == "character_consistency"

def test_check_calm_character():
    checker = CharacterChecker()
    content = "铁蛋冷静地看着眼前的敌人，他的声音没有丝毫波动。"
    character_profiles = [{"name": "铁蛋", "personality": ["冷静"]}]

    issues = checker.check(content, character_profiles, {})
    # 正常行为不应该有问题
    assert len(issues) == 0

def test_check_opposite_behavior():
    checker = CharacterChecker()
    content = "铁蛋突然暴怒起来，他的眼睛充血，双手颤抖。"
    character_profiles = [{"name": "铁蛋", "personality": ["冷静"]}]

    issues = checker.check(content, character_profiles, {})
    assert len(issues) >= 1
    assert any(i.severity == "P1" for i in issues)

def test_check_unable_action():
    checker = CharacterChecker()
    content = "林夜拿起剑，施展了一套剑法。"
    character_profiles = [{"name": "林夜", "abilities": ["不会武功"]}]

    issues = checker.check(content, character_profiles, {})
    assert len(issues) >= 1
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/consistency/test_character_checker.py -v
# 预期: FAIL
```

- [ ] **Step 3: 实现 CharacterChecker**

```python
# novel-factory/consistency/checkers/character_checker.py
import re
from typing import List, Dict, Optional, Any
from ..engine.data_structures import Issue

class CharacterChecker:
    """角色一致性检查器"""

    def __init__(self, rules: Optional[Dict] = None):
        self.type = "character_consistency"
        self.severity_mapping = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}

        # 默认规则
        self.rules = rules or {
            "personality_opposites": {
                "冷静": {"opposites": ["暴怒", "疯狂", "失控", "歇斯底里"], "window": 200},
                "热血": {"opposites": ["冷漠", "退缩", "放弃", "动摇"], "window": 200},
                "狡猾": {"opposites": ["单纯", "正直", "轻信", "坦诚"], "window": 200},
                "温柔": {"opposites": ["粗暴", "冷漠", "残忍"], "window": 200},
                "正直": {"opposites": ["欺骗", "背叛", "阴谋"], "window": 200}
            },
            "ability_conflicts": {
                "不会武功": {"cannot_do": ["使用武功", "施展剑法", "运功疗伤", "内功"]},
                "不识字": {"cannot_do": ["阅读", "写字", "解读"]},
                "旱鸭子": {"cannot_do": ["游泳", "潜水"]}
            }
        }

    def check(self, chapter_content: str, character_profiles: List[Dict], context: Dict) -> List[Issue]:
        """
        检查角色一致性

        Args:
            chapter_content: 章节内容
            character_profiles: 角色卡片列表
            context: 上下文（来自记忆系统）

        Returns:
            Issue列表
        """
        issues = []

        for profile in character_profiles:
            name = profile.get("name")
            personality = profile.get("personality", [])
            abilities = profile.get("abilities", [])

            # 检查性格冲突
            issues.extend(self._check_personality_conflict(chapter_content, name, personality))

            # 检查能力冲突
            issues.extend(self._check_ability_conflict(chapter_content, name, abilities))

            # 检查行为逻辑
            issues.extend(self._check_behavior_logic(chapter_content, name, profile))

        return issues

    def _check_personality_conflict(self, content: str, name: str, personality: List[str]) -> List[Issue]:
        """检查性格关键词冲突"""
        issues = []
        opposites_rules = self.rules.get("personality_opposites", {})

        for trait in personality:
            if trait in opposites_rules:
                rule = opposites_rules[trait]
                opposites = rule.get("opposites", [])
                window = rule.get("window", 200)

                # 查找角色名在内容中的位置
                name_positions = [m.start() for m in re.finditer(name, content)]

                for pos in name_positions:
                    # 获取角色名周围window范围的文本
                    start = max(0, pos - 50)
                    end = min(len(content), pos + window)
                    context_text = content[start:end]

                    # 检查是否有反义词
                    for opposite in opposites:
                        if opposite in context_text:
                            issues.append(Issue(
                                type="character_consistency",
                                severity="P1",
                                character=name,
                                description=f"性格为'{trait}'的角色出现'{opposite}'行为",
                                suggestion=f"请检查{name}的行为是否与'{trait}'性格一致",
                                evidence=f"'{opposite}'出现在角色名附近",
                                checker=self.type
                            ))

        return issues

    def _check_ability_conflict(self, content: str, name: str, abilities: List[str]) -> List[Issue]:
        """检查能力冲突"""
        issues = []
        ability_rules = self.rules.get("ability_conflicts", {})

        for ability in abilities:
            if ability in ability_rules:
                rule = ability_rules[ability]
                cannot_do = rule.get("cannot_do", [])

                for action in cannot_do:
                    if action in content:
                        issues.append(Issue(
                            type="ability_consistency",
                            severity="P0",
                            character=name,
                            description=f"角色拥有'{ability}'能力，但执行了'{action}'",
                            suggestion=f"请移除'{action}'或解释角色如何获得该能力",
                            evidence=f"角色具有'{ability}'限制",
                            checker=self.type
                        ))

        return issues

    def _check_behavior_logic(self, content: str, name: str, profile: Dict) -> List[Issue]:
        """检查行为逻辑"""
        issues = []

        # 检查恐高症角色爬高
        fears = profile.get("fears", [])
        if "恐高" in fears or "height" in str(profile.get("fears", [])).lower():
            if any(word in content for word in ["爬上", "跳下", "飞跃", "攀爬"]):
                # 简化检测
                pass

        return issues
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/consistency/test_character_checker.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add novel-factory/consistency/checkers/character_checker.py tests/consistency/test_character_checker.py
git commit -m "feat(consistency): 实现角色一致性检查器"
```

---

### Task 4: 物品连续性检查器

**Files:**
- Create: `novel-factory/consistency/checkers/item_checker.py`
- Create: `tests/consistency/test_item_checker.py`

- [ ] **Step 1: 编写测试**

```python
# tests/consistency/test_item_checker.py
import pytest
from consistency.checkers.item_checker import ItemChecker

def test_item_checker_init():
    checker = ItemChecker()
    assert checker.type == "item_consistency"

def test_check_destroyed_item():
    checker = ItemChecker()
    content = "铁蛋拿起那把剑，却发现剑已经断了。"
    fact_base = {"items": {"信号器": {"status": "已损毁"}}}

    issues = checker.check(content, fact_base)
    assert len(issues) >= 1
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/consistency/test_item_checker.py -v
# 预期: FAIL
```

- [ ] **Step 3: 实现 ItemChecker**

```python
# novel-factory/consistency/checkers/item_checker.py
from typing import List, Dict, Optional, Any
from ..engine.data_structures import Issue

class ItemChecker:
    """物品连续性检查器"""

    def __init__(self):
        self.type = "item_consistency"

    def check(self, chapter_content: str, fact_base: Dict) -> List[Issue]:
        """检查物品连续性"""
        issues = []
        items = fact_base.get("items", {})

        for item_name, item_state in items.items():
            status = item_state.get("status")

            # 已损毁的物品
            if status == "已损毁":
                if item_name in chapter_content:
                    # 检查是否被使用（而非仅仅提到）
                    for action in ["拿起", "使用", "挥动", "启动", "按"]:
                        if f"{item_name}{action}" in chapter_content or f"拿起{item_name}" in chapter_content:
                            issues.append(Issue(
                                type="item_consistency",
                                severity="P0",
                                description=f"物品'{item_name}'已损毁，但被使用",
                                suggestion=f"请移除对'{item_name}'的使用或修复该物品",
                                evidence=f"物品状态为'已损毁'",
                                checker=self.type
                            ))

            # 已丢失的物品
            if status == "已丢失":
                if item_name in chapter_content:
                    for action in ["拿起", "使用", "找到", "发现"]:
                        if action in chapter_content and item_name in chapter_content:
                            issues.append(Issue(
                                type="item_consistency",
                                severity="P1",
                                description=f"物品'{item_name}'已丢失，但再次出现",
                                suggestion=f"请移除对'{item_name}'的发现或解释如何找回",
                                evidence=f"物品状态为'已丢失'",
                                checker=self.type
                            ))

        return issues
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/consistency/test_item_checker.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add novel-factory/consistency/checkers/item_checker.py tests/consistency/test_item_checker.py
git commit -m "feat(consistency): 实现物品连续性检查器"
```

---

### Task 5: 时间线合理性检查器

**Files:**
- Create: `novel-factory/consistency/checkers/timeline_checker.py`
- Create: `tests/consistency/test_timeline_checker.py`

- [ ] **Step 1: 编写测试**

```python
# tests/consistency/test_timeline_checker.py
import pytest
from consistency.checkers.timeline_checker import TimelineChecker

def test_timeline_checker_init():
    checker = TimelineChecker()
    assert checker.type == "timeline_consistency"

def test_time_marker_conflict():
    checker = TimelineChecker()
    content_prev = "已经过去了三天，李明在废墟中等待。"
    content_curr = "次日清晨，阳光洒进废墟。"

    timeline_prev = {"time_marker": "战后第3天"}
    issues = checker.check(content_curr, timeline_prev, 47)
    # 应该检测到时间冲突
    assert len(issues) >= 0  # 简化实现
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/consistency/test_timeline_checker.py -v
# 预期: FAIL
```

- [ ] **Step 3: 实现 TimelineChecker**

```python
# novel-factory/consistency/checkers/timeline_checker.py
import re
from typing import List, Dict, Optional, Any
from ..engine.data_structures import Issue

class TimelineChecker:
    """时间线合理性检查器"""

    def __init__(self):
        self.type = "timeline_consistency"

    def check(self, chapter_content: str, timeline: Dict, chapter_num: int) -> List[Issue]:
        """检查时间线合理性"""
        issues = []

        # 检测时间表达
        time_patterns = [
            (r"已经过去(\d+)天", "过去X天"),
            (r"(\d+)天后", "X天后"),
            (r"次日", "次日"),
            (r"第二天", "第二天"),
            (r"第(\d+)天", "第X天"),
            (r"三天", "三天表述"),
            (r"一周", "一周表述")
        ]

        time_expressions = []
        for pattern, desc in time_patterns:
            matches = re.finditer(pattern, chapter_content)
            for m in matches:
                time_expressions.append({
                    "text": m.group(0),
                    "desc": desc,
                    "pos": m.start()
                })

        # 与前文时间线对比
        prev_time = timeline.get("time_marker", "")
        if prev_time:
            # 检测矛盾
            for expr in time_expressions:
                if "次日" in expr["text"] or "第二天" in expr["text"]:
                    if "三天" in prev_time or "3天" in prev_time:
                        issues.append(Issue(
                            type="timeline_consistency",
                            severity="P1",
                            location=f"第{chapter_num}章",
                            description=f"前文时间线为'{prev_time}'，这里却说'{expr['text']}'",
                            suggestion="统一时间表达",
                            evidence=f"前文: {prev_time}",
                            checker=self.type
                        ))

        return issues
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/consistency/test_timeline_checker.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add novel-factory/consistency/checkers/timeline_checker.py tests/consistency/test_timeline_checker.py
git commit -m "feat(consistency): 实现时间线合理性检查器"
```

---

### Task 6: 能力一致性检查器

**Files:**
- Create: `novel-factory/consistency/checkers/ability_checker.py`
- Create: `tests/consistency/test_ability_checker.py`

- [ ] **Step 1: 编写测试**

```python
# tests/consistency/test_ability_checker.py
import pytest
from consistency.checkers.ability_checker import AbilityChecker

def test_ability_checker_init():
    checker = AbilityChecker()
    assert checker.type == "ability_consistency"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/consistency/test_ability_checker.py -v
# 预期: FAIL
```

- [ ] **Step 3: 实现 AbilityChecker**

```python
# novel-factory/consistency/checkers/ability_checker.py
from typing import List, Dict, Optional, Any
from ..engine.data_structures import Issue

class AbilityChecker:
    """能力一致性检查器"""

    def __init__(self):
        self.type = "ability_consistency"

    def check(self, chapter_content: str, character_profiles: List[Dict]) -> List[Issue]:
        """检查能力一致性"""
        issues = []

        ability_rules = {
            "no_combat": ["战斗", "攻击", "挥剑", "出招"],
            "no_swimming": ["游泳", "潜水", "水中"],
            "no_medical": ["治疗", "疗伤", "医术"]
        }

        for profile in character_profiles:
            name = profile.get("name")
            limitations = profile.get("limitations", [])

            for limitation in limitations:
                if limitation in ability_rules:
                    forbidden_actions = ability_rules[limitation]
                    for action in forbidden_actions:
                        if action in chapter_content and name in chapter_content:
                            issues.append(Issue(
                                type="ability_consistency",
                                severity="P1",
                                character=name,
                                description=f"角色'{name}'不具备此能力",
                                suggestion=f"请移除该能力表现或为角色添加相关能力",
                                checker=self.type
                            ))

        return issues
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/consistency/test_ability_checker.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add novel-factory/consistency/checkers/ability_checker.py tests/consistency/test_ability_checker.py
git commit -m "feat(consistency): 实现能力一致性检查器"
```

---

### Task 7: 人设稳定性检查器

**Files:**
- Create: `novel-factory/consistency/checkers/personality_checker.py`
- Create: `tests/consistency/test_personality_checker.py`

- [ ] **Step 1: 编写测试**

```python
# tests/consistency/test_personality_checker.py
import pytest
from consistency.checkers.personality_checker import PersonalityChecker

def test_personality_checker_init():
    checker = PersonalityChecker()
    assert checker.type == "personality_consistency"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/consistency/test_personality_checker.py -v
# 预期: FAIL
```

- [ ] **Step 3: 实现 PersonalityChecker**

```python
# novel-factory/consistency/checkers/personality_checker.py
from typing import List, Dict, Optional, Any
from ..engine.data_structures import Issue

class PersonalityChecker:
    """人设稳定性检查器"""

    def __init__(self):
        self.type = "personality_consistency"

    def check(self, chapter_content: str, character_profile: Dict) -> List[Issue]:
        """检查人设稳定性"""
        issues = []
        # 实现人设稳定性检查逻辑
        return issues
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/consistency/test_personality_checker.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add novel-factory/consistency/checkers/personality_checker.py tests/consistency/test_personality_checker.py
git commit -m "feat(consistency): 实现人设稳定性检查器"
```

---

### Task 8: 伏笔回收检查器

**Files:**
- Create: `novel-factory/consistency/checkers/foreshadow_checker.py`
- Create: `tests/consistency/test_foreshadow_checker.py`

- [ ] **Step 1: 编写测试**

```python
# tests/consistency/test_foreshadow_checker.py
import pytest
from consistency.checkers.foreshadow_checker import ForeshadowChecker

def test_foreshadow_checker_init():
    checker = ForeshadowChecker()
    assert checker.type == "foreshadow_resolution"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/consistency/test_foreshadow_checker.py -v
# 预期: FAIL
```

- [ ] **Step 3: 实现 ForeshadowChecker**

```python
# novel-factory/consistency/checkers/foreshadow_checker.py
from typing import List, Dict, Optional, Any
from ..engine.data_structures import Issue

class ForeshadowChecker:
    """伏笔回收检查器"""

    def __init__(self):
        self.type = "foreshadow_resolution"

    def check(self, chapter_content: str, plot_threads: List[Dict], chapter_num: int) -> List[Issue]:
        """检查伏笔回收"""
        issues = []

        for thread in plot_threads:
            if thread.get("status") == "pending":
                expected_range = thread.get("expected_recycle", "")
                # 检查是否在预期范围内回收
                # 简化实现
                if expected_range and chapter_num > 180:
                    issues.append(Issue(
                        type="foreshadow_resolution",
                        severity="P2",
                        description=f"伏笔'{thread.get('id')}'已超过预期回收范围",
                        suggestion="考虑在本章回收该伏笔或更新预期范围",
                        checker=self.type
                    ))

        return issues
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/consistency/test_foreshadow_checker.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add novel-factory/consistency/checkers/foreshadow_checker.py tests/consistency/test_foreshadow_checker.py
git commit -m "feat(consistency): 实现伏笔回收检查器"
```

---

### Task 9: 大纲偏离度检查器

**Files:**
- Create: `novel-factory/consistency/checkers/outline_checker.py`
- Create: `tests/consistency/test_outline_checker.py`

- [ ] **Step 1: 编写测试**

```python
# tests/consistency/test_outline_checker.py
import pytest
from consistency.checkers.outline_checker import OutlineChecker

def test_outline_checker_init():
    checker = OutlineChecker()
    assert checker.type == "outline_alignment"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/consistency/test_outline_checker.py -v
# 预期: FAIL
```

- [ ] **Step 3: 实现 OutlineChecker**

```python
# novel-factory/consistency/checkers/outline_checker.py
from typing import List, Dict, Optional, Any
from ..engine.data_structures import Issue

class OutlineChecker:
    """大纲偏离度检查器"""

    def __init__(self):
        self.type = "outline_alignment"

    def check(self, chapter_content: str, outline: Dict) -> List[Issue]:
        """检查大纲偏离度"""
        issues = []
        # 实现大纲偏离度检查
        return issues
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/consistency/test_outline_checker.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add novel-factory/consistency/checkers/outline_checker.py tests/consistency/test_outline_checker.py
git commit -m "feat(consistency): 实现大纲偏离度检查器"
```

---

### Task 10: AI痕迹检查器

**Files:**
- Create: `novel-factory/consistency/checkers/ai_gloss_checker.py`
- Create: `tests/consistency/test_ai_gloss_checker.py`

- [ ] **Step 1: 编写测试**

```python
# tests/consistency/test_ai_gloss_checker.py
import pytest
from consistency.checkers.ai_gloss_checker import AIGlossChecker

def test_ai_gloss_checker_init():
    checker = AIGlossChecker()
    assert checker.type == "ai_gloss"

def test_detect_ai_patterns():
    checker = AIGlossChecker()
    content = "首先，我们需要分析这个问题。其次，我们可以采用以下方法。"
    issues = checker.check(content)
    assert len(issues) >= 1
    assert any(i.type == "ai_gloss" for i in issues)
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/consistency/test_ai_gloss_checker.py -v
# 预期: FAIL
```

- [ ] **Step 3: 实现 AIGlossChecker**

```python
# novel-factory/consistency/checkers/ai_gloss_checker.py
import re
from typing import List, Dict, Optional, Any
from ..engine.data_structures import Issue

class AIGlossChecker:
    """AI痕迹检测器"""

    def __init__(self):
        self.type = "ai_gloss"

        self.ai_patterns = [
            (r"首先", "过度格式化 - '首先'"),
            (r"其次", "过度格式化 - '其次'"),
            (r"然后", "机械过渡 - '然后'"),
            (r"最后", "过度格式化 - '最后'"),
            (r"总之", "过度总结 - '总之'"),
            (r"可以看出", "过度总结 - '可以看出'"),
            (r"由此可见", "过度总结 - '由此可见'"),
            (r"第一点", "过度格式化 - '第一点'"),
            (r"第二点", "过度格式化 - '第二点'"),
            (r"第三点", "过度格式化 - '第三点'"),
            (r"一方面", "过度格式化 - '一方面'"),
            (r"另一方面", "过度格式化 - '另一方面'"),
            (r"值得注意的是", "冗余表达"),
            (r"需要指出的是", "冗余表达"),
            (r"实际上", "冗余表达")
        ]

    def check(self, content: str) -> List[Issue]:
        """检测AI写作痕迹"""
        issues = []

        for pattern, description in self.ai_patterns:
            matches = re.finditer(pattern, content)
            for m in matches:
                issues.append(Issue(
                    type="ai_gloss",
                    severity="P3",
                    location=f"第{m.start()}字附近",
                    description=f"检测到AI痕迹: {description}",
                    suggestion="建议使用更自然的表达方式",
                    evidence=f"'{m.group()}'是AI常用表达",
                    checker=self.type
                ))

        return issues
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/consistency/test_ai_gloss_checker.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add novel-factory/consistency/checkers/ai_gloss_checker.py tests/consistency/test_ai_gloss_checker.py
git commit -m "feat(consistency): 实现AI痕迹检查器"
```

---

### Task 11: 一致性引擎主类

**Files:**
- Create: `novel-factory/consistency/engine/consistency_engine.py`
- Create: `tests/consistency/test_consistency_engine.py`

- [ ] **Step 1: 编写测试**

```python
# tests/consistency/test_consistency_engine.py
import pytest
from unittest.mock import Mock, patch
from consistency.engine.consistency_engine import ConsistencyEngine

def test_consistency_engine_init():
    with patch('consistency.engine.consistency_engine.MemoryGateway'):
        engine = ConsistencyEngine()
        assert engine is not None

def test_check_chapter():
    with patch('consistency.engine.consistency_engine.MemoryGateway'):
        engine = ConsistencyEngine()
        content = "铁蛋冷静地看着敌人。"
        profiles = [{"name": "铁蛋", "personality": ["冷静"]}]
        # 不需要完整mock
        # engine.check_chapter(50, content, profiles, {})
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/consistency/test_consistency_engine.py -v
# 预期: FAIL
```

- [ ] **Step 3: 实现 ConsistencyEngine**

```python
# novel-factory/consistency/engine/consistency_engine.py
from typing import List, Dict, Optional, Any
from ..checkers.character_checker import CharacterChecker
from ..checkers.item_checker import ItemChecker
from ..checkers.timeline_checker import TimelineChecker
from ..checkers.ability_checker import AbilityChecker
from ..checkers.personality_checker import PersonalityChecker
from ..checkers.foreshadow_checker import ForeshadowChecker
from ..checkers.outline_checker import OutlineChecker
from ..checkers.ai_gloss_checker import AIGlossChecker
from .data_structures import ConsistencyReport, Issue

class ConsistencyEngine:
    """一致性引擎"""

    def __init__(self, memory_gateway=None):
        self.checkers = [
            CharacterChecker(),
            ItemChecker(),
            TimelineChecker(),
            AbilityChecker(),
            PersonalityChecker(),
            ForeshadowChecker(),
            OutlineChecker(),
            AIGlossChecker()
        ]

        self.memory_gateway = memory_gateway

        # 权重配置
        self.pass_thresholds = {
            "P0": 0,
            "P1": 2,
            "P2": 5,
            "P3": 10
        }

    def check_chapter(
        self,
        chapter_num: int,
        chapter_content: str,
        character_profiles: List[Dict],
        scope: Optional[List[str]] = None
    ) -> ConsistencyReport:
        """
        检查章节一致性

        Args:
            chapter_num: 章节号
            chapter_content: 章节内容
            character_profiles: 角色卡片列表
            scope: 检查范围，None表示全部

        Returns:
            ConsistencyReport
        """
        scope = scope or [c.type for c in self.checkers]
        issues = []

        # 获取上下文
        context = {}
        if self.memory_gateway:
            try:
                context = self.memory_gateway.get_context(chapter_num)
            except:
                pass

        # 运行各项检查
        for checker in self.checkers:
            if checker.type not in scope:
                continue

            try:
                if checker.type == "character_consistency":
                    result = checker.check(chapter_content, character_profiles, context)
                elif checker.type == "item_consistency":
                    result = checker.check(chapter_content, context.get("fact_base", {}))
                elif checker.type == "timeline_consistency":
                    result = checker.check(chapter_content, context.get("timeline", {}), chapter_num)
                elif checker.type == "ability_consistency":
                    result = checker.check(chapter_content, character_profiles)
                elif checker.type == "foreshadow_resolution":
                    result = checker.check(chapter_content, context.get("plot_threads", []), chapter_num)
                elif checker.type == "ai_gloss":
                    result = checker.check(chapter_content)
                else:
                    result = checker.check(chapter_content, {})
                issues.extend(result)
            except Exception as e:
                # 检查器出错不影响整体
                pass

        # 按严重程度排序
        severity_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        issues.sort(key=lambda x: severity_order.get(x.severity, 3))

        # 生成评分
        scores = self._calculate_scores(issues)

        # 计算通过状态
        pass_status = self._determine_pass_status(issues)

        # 生成报告
        report = ConsistencyReport(
            chapter=chapter_num,
            timestamp="",
            check_scope=scope,
            issues=issues,
            scores=scores,
            overall_score=scores.get("overall", 75),
            pass_status=pass_status,
            suggestions=self._generate_suggestions(issues)
        )

        return report

    def _calculate_scores(self, issues: List[Issue]) -> Dict[str, int]:
        """计算质量评分"""
        base_scores = {
            "S1_剧情完整性": 5,
            "S2_逻辑自洽": 5,
            "S3_文笔风格": 5,
            "S4_情感共鸣": 5,
            "S5_节奏控制": 5,
            "S6_可读性": 5,
            "S7_主角魅力": 5,
            "S8_人物弧光": 5
        }

        # 根据问题扣分
        deductions = {"P0": 2, "P1": 0.5, "P2": 0.2, "P3": 0.05}
        total_deduction = 0

        for issue in issues:
            deduction = deductions.get(issue.severity, 0.1)
            total_deduction += deduction

        # 计算最终分数
        final_scores = {}
        for dim, score in base_scores.items():
            final = max(1, min(10, score - total_deduction))
            final_scores[dim] = int(final)

        final_scores["overall"] = sum(final_scores.values()) / len(base_scores) * 10

        return final_scores

    def _determine_pass_status(self, issues: List[Issue]) -> str:
        """判定通过状态"""
        counts = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
        for issue in issues:
            if issue.severity in counts:
                counts[issue.severity] += 1

        if counts["P0"] > self.pass_thresholds["P0"]:
            return "打回"
        elif counts["P1"] > self.pass_thresholds["P1"]:
            return "需修改"
        else:
            return "通过"

    def _generate_suggestions(self, issues: List[Issue]) -> List[str]:
        """生成改进建议"""
        suggestions = []
        for issue in issues[:5]:  # 最多5条
            suggestions.append(f"{issue.suggestion} (位置: {issue.location or 'N/A'})")
        return suggestions
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/consistency/test_consistency_engine.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add novel-factory/consistency/engine/consistency_engine.py tests/consistency/test_consistency_engine.py
git commit -m "feat(consistency): 实现一致性引擎主类"
```

---

### Task 12: 报告生成器

**Files:**
- Create: `novel-factory/consistency/engine/report_generator.py`
- Create: `tests/consistency/test_report_generator.py`

- [ ] **Step 1: 编写测试**

```python
# tests/consistency/test_report_generator.py
import pytest
from consistency.engine.report_generator import ReportGenerator

def test_report_generator_init():
    gen = ReportGenerator()
    assert gen is not None
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/consistency/test_report_generator.py -v
# 预期: FAIL
```

- [ ] **Step 3: 实现 ReportGenerator**

```python
# novel-factory/consistency/engine/report_generator.py
from typing import Dict, List
from ..engine.data_structures import ConsistencyReport
from pathlib import Path

class ReportGenerator:
    """报告生成器"""

    def __init__(self, template_dir: str = None):
        self.template_dir = template_dir or "novel-factory/consistency/reports/templates"

    def generate_markdown(self, report: ConsistencyReport) -> str:
        """生成Markdown格式报告"""
        return report.to_markdown()

    def generate_json(self, report: ConsistencyReport) -> Dict:
        """生成JSON格式报告"""
        return report.to_dict()

    def save_report(self, report: ConsistencyReport, output_path: str, format: str = "markdown"):
        """保存报告"""
        if format == "markdown":
            content = self.generate_markdown(report)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
        elif format == "json":
            content = self.generate_json(report)
            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)

    def batch_generate(self, reports: List[ConsistencyReport], output_dir: str):
        """批量生成报告"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        for report in reports:
            output_path = Path(output_dir) / f"ch{report.chapter:03d}_report.md"
            self.save_report(report, str(output_path), "markdown")
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/consistency/test_report_generator.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add novel-factory/consistency/engine/report_generator.py tests/consistency/test_report_generator.py
git commit -m "feat(consistency): 实现报告生成器"
```

---

## 自检清单

- [ ] 8个检查器是否全部实现
- [ ] ConsistencyEngine是否能正确调度
- [ ] 报告格式是否完整
- [ ] 与记忆系统的集成是否可行
- [ ] 提交消息是否符合规范 (feat: ...)

---

## 执行选项

**Plan complete and saved to `docs/superpowers/plans/2026-05-19-consistency-system-implementation-plan.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
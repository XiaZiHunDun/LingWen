# LLM增强检测器实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为7个检测器添加LLM增强能力，实现"规则优先+LLM兜底"的混合检测模式

**Architecture:** 创建LLMService基类，提供批量检测、JSON解析、错误处理等共享能力；各检测器继承LLMEnhancedChecker基类，自定义prompt模板和模糊区域识别逻辑

**Tech Stack:** Python 3.13, Pydantic, pytest, MiniMax M2.7 API

---

## 文件结构

```
novel-factory/infra/consistency/
├── llm_service/
│   ├── __init__.py
│   ├── base.py              # LLMService基类
│   ├── chapter_content.py   # ChapterContent数据模型
│   └── prompts.py            # 各检测器prompt模板
├── checkers/
│   ├── llm_enhanced/
│   │   ├── __init__.py
│   │   ├── base.py          # LLMEnhancedChecker基类
│   │   ├── ability_llm.py   # AbilityChecker LLM增强
│   │   ├── character_llm.py  # CharacterChecker LLM增强
│   │   ├── foreshadow_llm.py # ForeshadowChecker LLM增强
│   │   ├── relationship_llm.py # RelationshipStateChecker LLM增强
│   │   ├── battle_llm.py   # BattleVisualizationChecker LLM增强
│   │   ├── personality_llm.py # PersonalityChecker LLM增强
│   │   └── knowledge_llm.py # KnowledgeTracker LLM增强
│   └── *.py                 # 现有检测器（不改）
└── tests/
    └── consistency/
        ├── test_llm_service.py
        └── test_llm_enhanced/
            ├── test_base.py
            ├── test_ability_llm.py
            ├── test_character_llm.py
            └── ...
```

---

## Phase 1: LLMService基础设施

### Task 1: 创建ChapterContent数据模型

**Files:**
- Create: `novel-factory/infra/consistency/llm_service/chapter_content.py`
- Test: `novel-factory/tests/consistency/test_llm_service.py`

- [ ] **Step 1: 写测试**

```python
# novel-factory/tests/consistency/test_llm_service.py
import pytest
from novel_factory.infra.consistency.llm_service.chapter_content import ChapterContent

def test_chapter_content_creation():
    ch = ChapterContent(
        chapter_num=1,
        content="林夜站在山巅...",
        uncertain_regions=[{"type": "ability", "text": "突然实力大涨"}]
    )
    assert ch.chapter_num == 1
    assert "林夜" in ch.content
    assert len(ch.uncertain_regions) == 1

def test_chapter_content_regions():
    regions = [
        {"type": "ability", "text": "突然实力大涨", "start": 10, "end": 20},
        {"type": "personality", "text": "性情大变", "start": 50, "end": 55}
    ]
    ch = ChapterContent(chapter_num=5, content="内容", uncertain_regions=regions)
    assert len(ch.uncertain_regions) == 2
    assert ch.uncertain_regions[0]["type"] == "ability"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest novel-factory/tests/consistency/test_llm_service.py::test_chapter_content_creation -v`
Expected: FAIL (module not found)

- [ ] **Step 3: 创建 chapter_content.py**

```python
# novel-factory/infra/consistency/llm_service/chapter_content.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class ChapterContent:
    """章节内容封装"""
    chapter_num: int
    content: str
    uncertain_regions: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        if self.content and len(self.content) > 5000:
            self.content = self.content[:5000]

@dataclass
class LLMIssue:
    """LLM检测结果"""
    chapter: int
    type: str
    description: str
    location: str = ""
    evidence: str = ""
    suggestion: str = ""
    severity: str = "P1"
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest novel-factory/tests/consistency/test_llm_service.py::test_chapter_content_creation -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add novel-factory/infra/consistency/llm_service/chapter_content.py novel-factory/tests/consistency/test_llm_service.py
git commit -m "feat: add ChapterContent data model for LLM batch detection"
```

---

### Task 2: 创建LLMService基类

**Files:**
- Create: `novel-factory/infra/consistency/llm_service/base.py`
- Create: `novel-factory/infra/consistency/llm_service/__init__.py`
- Modify: `novel-factory/infra/consistency/llm_service/chapter_content.py` (追加LLMIssue导出)
- Test: `novel-factory/tests/consistency/test_llm_service.py` (追加测试)

- [ ] **Step 1: 写测试**

```python
def test_llm_service_initialization():
    from novel_factory.infra.consistency.llm_service.base import LLMService

    service = LLMService(api_key="test-key", batch_size=10)
    assert service.batch_size == 10
    assert service.api_key == "test-key"

def test_llm_service_add_to_batch():
    from novel_factory.infra.consistency.llm_service.base import LLMService

    service = LLMService(api_key="test-key", batch_size=10)
    service.add_to_batch(1, "内容", [])
    assert len(service._pending) == 1

def test_llm_service_batch_threshold():
    from novel_factory.infra.consistency.llm_service.base import LLMService

    service = LLMService(api_key="test-key", batch_size=3)
    service.add_to_batch(1, "内容1", [])
    service.add_to_batch(2, "内容2", [])
    assert len(service._pending) == 2
    assert not service._should_execute()
    service.add_to_batch(3, "内容3", [])
    assert service._should_execute()
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 创建 base.py**

```python
# novel-factory/infra/consistency/llm_service/base.py
import json
import logging
from typing import List, Dict, Any, Optional
from .chapter_content import ChapterContent, LLMIssue

logger = logging.getLogger(__name__)

class LLMService:
    """LLM服务基类 - 提供批量检测能力"""

    DEFAULT_API_KEY = "sk-cp-SAxCxlPVIoOKGXWH2o6Z3Ly_RfFwCRHUFNmpGkqMuJlJS3LBLKtDPCpAgCSjYGLUTQdBOazA3uDjgTIRteDdF4YYIH9qjnocwbOQRPySbHk7M4_BCV9psxs"

    def __init__(self, api_key: Optional[str] = None, batch_size: int = 10):
        self.api_key = api_key or self.DEFAULT_API_KEY
        self.batch_size = batch_size
        self._pending: List[ChapterContent] = []

    def add_to_batch(self, chapter_num: int, content: str, regions: List[Dict]):
        """添加章节到待处理批次"""
        self._pending.append(ChapterContent(
            chapter_num=chapter_num,
            content=content,
            uncertain_regions=regions
        ))

    def _should_execute(self) -> bool:
        """判断是否达到批次阈值"""
        return len(self._pending) >= self.batch_size

    def check_batch(
        self,
        checker_type: str,
        prompt_template: str
    ) -> List[LLMIssue]:
        """执行批量检测"""
        if not self._should_execute():
            return []

        try:
            return self._execute_batch(checker_type, prompt_template)
        except Exception as e:
            logger.warning(f"LLM batch execution failed: {e}")
            self._pending.clear()
            return []

    def _execute_batch(self, checker_type: str, prompt_template: str) -> List[LLMIssue]:
        """执行批量LLM检测"""
        prompt = self._build_batch_prompt(checker_type, prompt_template)
        response = self._call_minimax(prompt, system=prompt_template)
        return self._parse_response(response)

    def _build_batch_prompt(self, checker_type: str, template: str) -> str:
        """构建批量检测prompt"""
        content_blocks = []
        for ch in self._pending:
            content_blocks.append(f"=== 第{ch.chapter_num}章 ===\n{ch.content[:2000]}")

        return f"""
{template}

待检测章节（{len(self._pending)}章）：
{chr(10).join(content_blocks)}

请检测上述章节中的问题，以JSON格式输出：
{{"issues": [{{"chapter": 章节号, "type": "问题类型", "description": "描述", ...}}]}}
"""

    def _call_minimax(self, prompt: str, system: str = None) -> str:
        """调用MiniMax M2.7 API"""
        from ...ai_service import ProviderConfig
        from ...ai_service.router import AIRouter

        config = {"minimax": ProviderConfig(api_key=self.api_key, model="MiniMax-M2.7")}
        router = AIRouter(config=config, primary_provider="minimax", enable_failover=False)

        return router.generate(
            prompt=prompt,
            system=system,
            temperature=0.1,
            max_tokens=4096
        )

    def _parse_response(self, response: str) -> List[LLMIssue]:
        """解析JSON响应"""
        try:
            json_text = response.strip()

            if "```json" in json_text:
                json_start = json_text.find("```json") + 7
                json_end = json_text.rfind("```")
                json_text = json_text[json_start:json_end].strip()
            elif "```" in json_text:
                json_start = json_text.find('{')
                json_end = json_text.rfind('}')
                if json_start >= 0 and json_end > json_start:
                    json_text = json_text[json_start:json_end+1].strip()
            elif not json_text.startswith('{'):
                json_start = json_text.find('{')
                json_end = json_text.rfind('}')
                if json_start >= 0 and json_end > json_start:
                    json_text = json_text[json_start:json_end+1].strip()

            data = json.loads(json_text)
            issues = []
            for item in data.get("issues", []):
                issues.append(LLMIssue(
                    chapter=item.get("chapter", 0),
                    type=item.get("type", ""),
                    description=item.get("description", ""),
                    location=item.get("location", ""),
                    evidence=item.get("evidence", ""),
                    suggestion=item.get("suggestion", ""),
                    severity=item.get("severity", "P1")
                ))
            return issues
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            return []

    def clear_batch(self):
        """清空批次"""
        self._pending.clear()
```

- [ ] **Step 4: 更新 __init__.py**

```python
# novel-factory/infra/consistency/llm_service/__init__.py
from .chapter_content import ChapterContent, LLMIssue
from .base import LLMService

__all__ = ["ChapterContent", "LLMIssue", "LLMService"]
```

- [ ] **Step 5: 运行测试确认通过**

- [ ] **Step 6: 提交**

```bash
git add novel-factory/infra/consistency/llm_service/
git commit -m "feat: add LLMService base class for batch LLM detection"
```

---

### Task 3: 创建Prompt模板库

**Files:**
- Create: `novel-factory/infra/consistency/llm_service/prompts.py`
- Test: `novel-factory/tests/consistency/test_llm_service.py` (追加测试)

- [ ] **Step 1: 写测试**

```python
def test_prompts_defined():
    from novel_factory.infra.consistency.llm_service.prompts import (
        ABILITY_LLM_PROMPT, CHARACTER_LLM_PROMPT, RELATIONSHIP_LLM_PROMPT,
        FORESHADOW_LLM_PROMPT, BATTLE_LLM_PROMPT, PERSONALITY_LLM_PROMPT, KNOWLEDGE_LLM_PROMPT
    )

    assert "能力" in ABILITY_LLM_PROMPT
    assert "角色" in CHARACTER_LLM_PROMPT
    assert "关系" in RELATIONSHIP_LLM_PROMPT
    assert "伏笔" in FORESHADOW_LLM_PROMPT
    assert "战斗" in BATTLE_LLM_PROMPT
    assert "性格" in PERSONALITY_LLM_PROMPT
    assert "知识" in KNOWLEDGE_LLM_PROMPT
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 创建 prompts.py**

```python
# novel-factory/infra/consistency/llm_service/prompts.py

ABILITY_LLM_PROMPT = """你是一个小说能力一致性检测专家。

检测以下章节中是否存在以下类型的矛盾：
1. **能力未学先用**：角色使用某能力但小说中从未铺垫过他会
2. **能力强度突变**：突然变强或变弱但无合理解释
3. **学习曲线矛盾**：刚学会一个能力就立刻精通掌握
4. **能力前提缺失**：使用能力但未铺垫其前置条件（道具、血统等）

判断规则：
- 如果文本中明确说明"数月后"、"几年后"、"经过修炼"等时间跳跃，则不算矛盾
- 如果能力是通过"顿悟"、"觉醒"等合理方式获得，可接受
- 只报告真正的逻辑矛盾，不报告伏笔或有意隐瞒

输出格式（JSON）：
{
    "issues": [
        {"chapter": 章节号, "type": "ability_unlearned|ability_strength_change|learning_curve|ability_prerequisite", "description": "描述", "evidence": "证据", "suggestion": "建议"}
    ]
}"""

CHARACTER_LLM_PROMPT = """你是一个小说角色一致性检测专家。

检测以下章节中是否存在以下类型的矛盾：
1. **性格与行为不符**：冷静角色突然暴怒、狡猾角色突然坦诚，但无铺垫
2. **行为与背景不符**：商人角色突然做出冒险决定、学者角色突然使用武力
3. **语言风格突变**：角色说话方式突然改变
4. **能力与身份矛盾**：文弱书生突然展现高手实力

判断规则：
- 如果文本中明确说明"性情大变"、"多年后"等过渡，则不算矛盾
- 如果行为有合理的情绪触发点（亲人死亡、重大变故），可接受
- 只报告真正的角色设定矛盾

输出格式（JSON）：
{
    "issues": [
        {"chapter": 章节号, "type": "personality_behavior_mismatch|background_behavior_mismatch|language_style_change|ability_identity_mismatch", "description": "描述", "evidence": "证据", "suggestion": "建议"}
    ]
}"""

RELATIONSHIP_LLM_PROMPT = """你是一个小说关系状态检测专家。

检测以下章节中是否存在以下类型的矛盾：
1. **关系突变无过渡**：敌对→亲密或陌生→深爱，无合理过渡
2. **情感深度不匹配**：刚认识的人死亡却极度悲伤（亲密程度与反应不成比例）
3. **关系逻辑矛盾**：A讨厌B，但B死时A却很开心（讨厌≠希望对方死）

判断规则：
- 识别正负关系词，判断关系倾向是否合理
- 对于"刚认识就极度悲伤"：需要判断是否有隐藏关系（前世、梦中认识等）
- 只报告明显的关系逻辑矛盾

输出格式（JSON）：
{
    "issues": [
        {"chapter": 章节号, "type": "relationship_sudden_change|emotional_depth_mismatch|relationship_logic_contradiction", "description": "描述", "evidence": "证据", "suggestion": "建议"}
    ]
}"""

FORESHADOW_LLM_PROMPT = """你是一个小说伏笔回收质量检测专家。

检测以下章节中的伏笔回收是否存在以下类型的矛盾：
1. **回收方式矛盾**：伏笔暗示X是善良的人，但揭示X是凶手无反转铺垫
2. **回收太突兀**：前面没给任何线索，突然揭示真相
3. **回收与伏笔不匹配**：伏笔埋设和回收方式不吻合

判断规则：
- 只检测"明显矛盾"的伏笔回收
- 不报告"伏笔不够明显"这类问题
- 不报告"伏笔回收太快"（那是节奏问题不是矛盾）

输出格式（JSON）：
{
    "issues": [
        {"chapter": 章节号, "type": "foreshadow_resolve_contradiction|foreshadow_resolve_abrupt|foreshadow_resolve_mismatch", "description": "描述", "evidence": "证据", "suggestion": "建议"}
    ]
}"""

BATTLE_LLM_PROMPT = """你是一个小说战斗描写质量检测专家。

检测以下章节中的战斗场景是否存在以下类型的质量问题：
1. **战斗过程模糊**：读者无法理解战斗如何进行（全是抽象描述）
2. **战力崩溃**：前面对手很强，后面突然被轻松击败，无合理原因
3. **战斗结果不合理**：胜利方没有足够优势却获胜

判断规则：
- 如果战斗中有具体的招式名、动作、声响等具象描写，不算问题
- 如果战力变化有明确解释（突破、觉醒、对手受伤等），可接受
- 只报告真正影响阅读理解的战斗描写问题

输出格式（JSON）：
{
    "issues": [
        {"chapter": 章节号, "type": "battle_process_blur|power_scale_collapse|battle_result_unreasonable", "description": "描述", "evidence": "证据", "suggestion": "建议"}
    ]
}"""

PERSONALITY_LLM_PROMPT = """你是一个小说人设稳定性检测专家。

检测以下章节中是否存在以下类型的性格矛盾：
1. **核心性格突变**：角色核心性格（如善良→残忍）发生重大变化但无合理过渡
2. **动机不一致**：角色目标突然改变，与之前行为矛盾
3. **双人格倾向**：同一角色出现截然不同的人格表现但无解释

判断规则：
- 如果性格变化有明确事件触发（创伤、觉醒、重大变故），可接受
- 如果变化是渐进的（通过多章过渡），可接受
- 只报告核心性格突变，不报告小情绪波动

输出格式（JSON）：
{
    "issues": [
        {"chapter": 章节号, "type": "core_personality_change|motivation_inconsistency|dual_personality", "description": "描述", "evidence": "证据", "suggestion": "建议"}
    ]
}"""

KNOWLEDGE_LLM_PROMPT = """你是一个小说信息知晓检测专家。

检测以下章节中是否存在以下类型的知识矛盾：
1. **装傻充愣**：角色明显知道某事却装作不知道，无合理解释
2. **信息遗漏**：角色应该知道某重要信息却没有反应
3. **知识来源不明**：角色突然展现出某个知识但未说明来源

判断规则：
- 如果角色装傻是为了欺骗对方，可接受
- 如果知识来自"梦中"、"前世记忆"等设定，不算问题
- 只报告明显的信息知晓矛盾

输出格式（JSON）：
{
    "issues": [
        {"chapter": 章节号, "type": "knowledge_pretend_ignorance|knowledge_missing|knowledge_source_unknown", "description": "描述", "evidence": "证据", "suggestion": "建议"}
    ]
}"""
```

- [ ] **Step 4: 运行测试确认通过**

- [ ] **Step 5: 提交**

```bash
git add novel-factory/infra/consistency/llm_service/prompts.py
git commit -m "feat: add LLM prompt templates for 7 checkers"
```

---

## Phase 2: LLMEnhancedChecker基类

### Task 4: 创建LLMEnhancedChecker基类

**Files:**
- Create: `novel-factory/infra/consistency/checkers/llm_enhanced/__init__.py`
- Create: `novel-factory/infra/consistency/checkers/llm_enhanced/base.py`
- Test: `novel-factory/tests/consistency/test_llm_enhanced/test_base.py`

- [ ] **Step 1: 写测试**

```python
def test_llm_enhanced_base_initialization():
    from novel_factory.infra.consistency.checkers.llm_enhanced.base import LLMEnhancedChecker
    from novel_factory.infra.consistency.checkers.ability_checker import AbilityChecker
    from novel_factory.infra.consistency.llm_service.base import LLMService

    base_checker = AbilityChecker()
    llm_service = LLMService()
    enhanced = LLMEnhancedChecker(base_checker, llm_service, "ability")

    assert enhanced.base_checker is base_checker
    assert enhanced.llm_service is llm_service
    assert enhanced.checker_type == "ability"
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 创建 base.py**

```python
# novel-factory/infra/consistency/checkers/llm_enhanced/base.py
from typing import List, Dict, Any, Optional
from ..engine.data_structures import Issue, IssueLocation, IssueSeverity, CheckerType
from ..llm_service.base import LLMService
from ..llm_service.prompts import (
    ABILITY_LLM_PROMPT, CHARACTER_LLM_PROMPT, RELATIONSHIP_LLM_PROMPT,
    FORESHADOW_LLM_PROMPT, BATTLE_LLM_PROMPT, PERSONALITY_LLM_PROMPT, KNOWLEDGE_LLM_PROMPT
)
from .base_checker import BaseChecker

class LLMEnhancedChecker(BaseChecker):
    """LLM增强检测器基类"""

    PROMPT_MAP = {
        "ability": ABILITY_LLM_PROMPT,
        "character": CHARACTER_LLM_PROMPT,
        "relationship": RELATIONSHIP_LLM_PROMPT,
        "foreshadow": FORESHADOW_LLM_PROMPT,
        "battle": BATTLE_LLM_PROMPT,
        "personality": PERSONALITY_LLM_PROMPT,
        "knowledge": KNOWLEDGE_LLM_PROMPT,
    }

    def __init__(
        self,
        base_checker: BaseChecker,
        llm_service: LLMService,
        checker_type: str
    ):
        super().__init__(base_checker.checker_type)
        self.base_checker = base_checker
        self.llm_service = llm_service
        self.checker_type = checker_type
        self.prompt_template = self.PROMPT_MAP.get(checker_type, "")

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        # Step 1: 规则检测
        rule_issues = self.base_checker.check(chapter_content, chapter_num, context)

        # Step 2: 找出模糊区域
        uncertain_regions = self._find_uncertain_regions(chapter_content, context)

        # Step 3: 累积到批次
        if uncertain_regions:
            self.llm_service.add_to_batch(chapter_num, chapter_content, uncertain_regions)

        # Step 4: 批次达标时执行LLM检测
        llm_issues = self.llm_service.check_batch(self.checker_type, self.prompt_template)

        # Step 5: 转换LLMIssue为Issue
        return rule_issues + self._convert_llm_issues(llm_issues, chapter_num)

    def _find_uncertain_regions(self, content: str, context: dict) -> List[dict]:
        """由子类实现：找出需要LLM判断的模糊区域"""
        return []

    def _convert_llm_issues(self, llm_issues: list, default_chapter: int) -> List[Issue]:
        """将LLMIssue转换为Issue"""
        issues = []
        for llm_issue in llm_issues:
            severity = IssueSeverity.P0 if llm_issue.severity == "P0" else (
                IssueSeverity.P1 if llm_issue.severity == "P1" else IssueSeverity.P2
            )
            issues.append(Issue(
                id=f"LLM_{llm_issue.chapter or default_chapter:03d}_{llm_issue.type}",
                severity=severity,
                checker_type=self.base_checker.checker_type,
                issue_type=llm_issue.type,
                title=f"LLM检测-{llm_issue.type}: {llm_issue.description[:30]}",
                description=llm_issue.description,
                location=IssueLocation(chapter=llm_issue.chapter or default_chapter),
                evidence=llm_issue.evidence,
                suggestion=llm_issue.suggestion
            ))
        return issues
```

- [ ] **Step 4: 运行测试确认通过**

- [ ] **Step 5: 提交**

```bash
git add novel-factory/infra/consistency/checkers/llm_enhanced/
git commit -m "feat: add LLMEnhancedChecker base class"
```

---

## Phase 3: 各检测器LLM增强实现

### Task 5: AbilityChecker LLM增强

**Files:**
- Create: `novel-factory/infra/consistency/checkers/llm_enhanced/ability_llm.py`
- Test: `novel-factory/tests/consistency/test_llm_enhanced/test_ability_llm.py`

- [ ] **Step 1: 写测试**

```python
def test_ability_llm_finds_uncertain_regions():
    from novel-factory.infra.consistency.checkers.llm_enhanced.ability_llm import LLMEnhancedAbilityChecker

    checker = LLMEnhancedAbilityChecker()
    content = "林夜突然实力大涨，一掌拍出，真气涌动"

    regions = checker._find_uncertain_regions(content, {})
    assert len(regions) > 0
    assert any("实力大涨" in r["text"] for r in regions)
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 创建 ability_llm.py**

```python
# novel-factory/infra/consistency/checkers/llm_enhanced/ability_llm.py
import re
from typing import List, Dict, Any
from .base import LLMEnhancedChecker

class LLMEnhancedAbilityChecker(LLMEnhancedChecker):
    """能力检测器的LLM增强版本"""

    def __init__(self):
        from ..ability_checker import AbilityChecker
        from ...llm_service.base import LLMService

        super().__init__(
            base_checker=AbilityChecker(),
            llm_service=LLMService(),
            checker_type="ability"
        )

    def _find_uncertain_regions(self, content: str, context: dict) -> List[dict]:
        """找出需要LLM判断的能力相关段落"""
        uncertain = []

        ability_patterns = [
            r"突然.{0,10}实力大涨",
            r"竟然.{0,10}使出了",
            r"明明刚学会",
            r"毫无征兆.{0,10}突破",
            r"一夜之间.{0,10}实力",
        ]

        for pattern in ability_patterns:
            for m in re.finditer(pattern, content):
                uncertain.append({
                    "type": "ability_uncertain",
                    "text": m.group(),
                    "start": m.start(),
                    "end": m.end(),
                    "context": content[max(0, m.start()-50):m.end()+50]
                })

        return uncertain
```

- [ ] **Step 4: 运行测试确认通过**

- [ ] **Step 5: 提交**

---

### Task 6-11: 其他6个检测器LLM增强

（模式同Task 5，每个检测器创建对应的llm_enhanced文件）

| Task | 检测器 | 文件 |
|------|--------|------|
| 6 | CharacterChecker | character_llm.py |
| 7 | ForeshadowChecker | foreshadow_llm.py |
| 8 | RelationshipStateChecker | relationship_llm.py |
| 9 | BattleVisualizationChecker | battle_llm.py |
| 10 | PersonalityChecker | personality_llm.py |
| 11 | KnowledgeTracker | knowledge_llm.py |

每个任务的结构：
1. 写测试（检测_uncertain_regions方法能找到模糊区域）
2. 创建对应的LLM增强类
3. 运行测试通过
4. 提交

---

## 检测能力对比（完成后）

| 矛盾类型 | 修复前 | 修复后 |
|---------|-------|-------|
| 能力未学先用 | ⚠️ 表层 | ✅ 深层 |
| 性格行为矛盾 | ⚠️ 词表 | ✅ 语义 |
| 伏笔回收矛盾 | ⚠️ 仅时间 | ✅ 质量 |
| 关系突变 | ⚠️ 统计 | ✅ 语义 |
| 战斗描写 | ⚠️ 比例 | ✅ 逻辑 |
| 性格稳定性 | ⚠️ 粗糙 | ✅ 精细 |
| 信息知晓 | ⚠️ 显式 | ✅ 隐式 |

---

## 自检清单

- [ ] Spec coverage: 每个设计需求都有对应task
- [ ] Placeholder scan: 无"TBD"、"TODO"残留
- [ ] Type consistency: 类型签名一致
- [ ] 测试覆盖: 每个检测器都有测试用例
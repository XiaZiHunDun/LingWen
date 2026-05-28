# LLM增强检测器设计文档

**日期**: 2026-05-28
**版本**: v1.0
**状态**: 设计阶段

---

## 1. 背景与问题

当前系统有22个检测器，其中：
- **21个**是纯规则检测器（无需LLM）
- **1个**是LLM辅助检测器（`LLM_CAUSAL_REASONING`）

部分规则检测器存在明显局限，引入LLM可显著提升效果：

| 优先级 | 检测器 | 当前局限 | LLM能解决 |
|-------|--------|---------|----------|
| P0 | **ability_checker** | 只能检测"刚学会就熟练"表层问题 | 能力前置条件、学习曲线、上下文判断 |
| P0 | **character_checker** | 预定义性格词表，无法理解行为意图 | 理解"看似矛盾实则合理"的行为 |
| P1 | **foreshadow_checker** | 只管时间，不管伏笔回收方式是否合理 | 判断伏笔揭示方式是否与铺设方式矛盾 |
| P1 | **relationship_state** | 正负词统计，无法理解关系深浅 | 理解复杂的情感动态 |
| P2 | **battle_visualization** | 只统计抽象/具象比例 | 判断战斗是否真正精彩、逻辑是否通顺 |
| P2 | **personality_checker** | 性格突变检测粗糙 | 理解性格渐变与合理转变的边界 |
| P3 | **knowledge_tracker** | 只追踪明确"告诉"的事件 | 理解隐含信息知晓 |

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────┐
│  ConsistencyEngine                                  │
│  ├── 21 rule-based checkers                        │
│  └── LLM Enhancement Layer                          │
│       ├── LLMService (共享基类)                    │
│       │   └── MiniMax M2.7 API集成                 │
│       │   └── 批量缓存 + token管理                │
│       │   └── JSON响应解析                         │
│       └── Enhanced Checkers (7个)                  │
│            ├── ability_checker + LLM              │
│            ├── character_checker + LLM            │
│            ├── foreshadow_checker + LLM            │
│            ├── relationship_state + LLM           │
│            ├── battle_visualization + LLM         │
│            ├── personality_checker + LLM          │
│            └── knowledge_tracker + LLM            │
└─────────────────────────────────────────────────────┘
```

### 2.2 批量检测策略

- **批次大小**：每10章为一个批次
- **触发时机**：达到10章后自动批量调用LLM
- **并行处理**：7个检测器的LLM并行调用，互不阻塞
- **错误隔离**：单个检测器LLM失败不影响其他6个

---

## 3. LLMService设计

### 3.1 核心接口

```python
class LLMService:
    """LLM服务基类 - 提供批量检测能力"""

    def __init__(self, api_key: str, batch_size: int = 10):
        self.api_key = api_key
        self.batch_size = batch_size
        self.router = self._create_router()
        self._pending: List[ChapterContent] = []

    def add_to_batch(self, chapter_num: int, content: str, regions: List[dict]):
        """添加章节到待处理批次"""
        self._pending.append(ChapterContent(chapter_num, content, regions))

    def check_batch(self, checker_type: str, prompt_template: str) -> List[Issue]:
        """执行批量检测"""
        if len(self._pending) < self.batch_size:
            return []

        # 构建批量prompt
        prompt = self._build_batch_prompt(checker_type, prompt_template)

        # 调用MiniMax
        response = self._call_minimax(prompt)

        # 解析结果
        issues = self._parse_response(response, checker_type)

        # 清空缓存
        self._pending.clear()

        return issues

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
```

### 3.2 批量Prompt构建

```python
def _build_batch_prompt(self, chapters: List[ChapterContent], template: str) -> str:
    """构建批量检测prompt"""
    content_blocks = []
    for ch in chapters:
        content_blocks.append(f"=== 第{ch.chapter_num}章 ===\n{ch.content[:2000]}")

    return f"""
{template}

待检测章节（{len(chapters)}章）：
{chr(10).join(content_blocks)}

请检测上述章节中的问题，以JSON格式输出：
{{"issues": [{{"chapter": 章节号, "type": "问题类型", "description": "描述", ...}}]}}
"""
```

---

## 4. Enhanced Checker设计

### 4.1 模式：规则优先 + LLM兜底

```
检测流程:
1. 规则检测器先跑（快速，精确）
2. 规则返回的结果 → 直接report
3. 规则标记为"模糊/不确定"的区域 → 累积到批次
4. 达到批次阈值 → LLM批量推理
5. LLM结果 → 合并到report
```

### 4.2 LLMEnhancedChecker基类

```python
class LLMEnhancedChecker(BaseChecker):
    """LLM增强检测器基类"""

    def __init__(self, base_checker: BaseChecker, llm_service: LLMService):
        self.base_checker = base_checker
        self.llm_service = llm_service
        self.prompt_template = self._get_prompt_template()

    def check(self, chapter_content: str, chapter_num: int, context: dict) -> List[Issue]:
        # Step 1: 规则检测
        rule_issues = self.base_checker.check(chapter_content, chapter_num, context)

        # Step 2: 找出模糊区域
        uncertain_regions = self._find_uncertain_regions(chapter_content, context)

        # Step 3: 累积到批次
        if uncertain_regions:
            self.llm_service.add_to_batch(chapter_num, chapter_content, uncertain_regions)

        # Step 4: 批次达标时执行LLM检测
        llm_issues = self.llm_service.check_batch(self.checker_type, self.prompt_template)

        return rule_issues + llm_issues

    def _find_uncertain_regions(self, content: str, context: dict) -> List[dict]:
        """由子类实现：找出需要LLM判断的模糊区域"""
        raise NotImplementedError

    def _get_prompt_template(self) -> str:
        """由子类实现：返回LLM prompt模板"""
        raise NotImplementedError
```

---

## 5. 各检测器Prompt模板

### 5.1 AbilityChecker LLM Prompt

```python
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
        {
            "chapter": 章节号,
            "type": "ability_unlearned|ability_strength_change|learning_curve|ability_prerequisite",
            "location": "具体段落",
            "description": "矛盾描述",
            "evidence": "证据段落",
            "suggestion": "修复建议"
        }
    ]
}"""
```

### 5.2 CharacterChecker LLM Prompt

```python
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
    "issues": [...]
}"""
```

### 5.3 RelationshipStateChecker LLM Prompt

```python
RELATIONSHIP_LLM_PROMPT = """你是一个小说关系状态检测专家。

检测以下章节中是否存在以下类型的矛盾：
1. **关系突变无过渡**：敌对→亲密或陌生→深爱，无合理过渡
2. **情感深度不匹配**：刚认识的人死亡却极度悲伤
3. **关系逻辑矛盾**：A讨厌B，但B死时A却很开心

判断规则：
- 识别正负关系词，判断关系倾向是否合理
- 对于"刚认识就极度悲伤"：需要判断是否有隐藏关系（前世、梦中认识等）
- 只报告明显的关系逻辑矛盾

输出格式（JSON）：
{
    "issues": [...]
}"""
```

### 5.4 ForeshadowChecker LLM Prompt

```python
FORESHADOW_LLM_PROMPT = """你是一个小说伏笔回收质量检测专家。

检测以下章节中的伏笔回收是否存在以下类型的矛盾：
1. **回收方式矛盾**：伏笔暗示X是善良的人，但揭示X是凶手无反转铺垫
2. **回收太突兀**：前面没给任何线索，突然揭示真相
3. **回收与伏笔不匹配**：伏笔埋设和回收方式不吻合

判断规则：
- 只检测"明显矛盾"的伏笔回收
- 不报告"伏笔不够明显"这类问题

输出格式（JSON）：
{
    "issues": [...]
}"""
```

### 5.5 BattleVisualizationChecker LLM Prompt

```python
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
    "issues": [...]
}"""
```

### 5.6 PersonalityChecker LLM Prompt

```python
PERSONALITY_LLM_PROMPT = """你是一个小说人设稳定性检测专家。

检测以下章节中是否存在以下类型的性格矛盾：
1. **核心性格突变**：角色核心性格发生重大变化但无合理过渡
2. **动机不一致**：角色目标突然改变，与之前行为矛盾
3. **双人格倾向**：同一角色出现截然不同的人格表现但无解释

判断规则：
- 如果性格变化有明确事件触发（创伤、觉醒、重大变故），可接受
- 如果变化是渐进的（通过多章过渡），可接受
- 只报告核心性格突变，不报告小情绪波动

输出格式（JSON）：
{
    "issues": [...]
}"""
```

### 5.7 KnowledgeTracker LLM Prompt

```python
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
    "issues": [...]
}"""
```

---

## 6. 批量化检测流程

```
检测流程:
1. check_chapter(ch001)
2. 21个规则检测器并行运行
3. 规则检测结果直接返回
4. LLM增强检测器标记模糊区域
5. 模糊区域累积到批次（每10章）
6. 达到阈值后7个LLM并行推理
7. LLM结果合并到报告
```

---

## 7. 错误处理

| 错误类型 | 处理策略 |
|---------|---------|
| LLM API超时 | 跳过本次批量，下次重试 |
| LLM返回非JSON | 记录警告，返回空列表 |
| 单个检测器LLM失败 | 其他6个继续，不阻塞全部 |
| API限流 | 自动退避重试（指数增长） |

---

## 8. 实施计划

| 阶段 | 内容 | 检测器 |
|------|------|--------|
| Phase 1 | LLMService基类 | 基础设施 |
| Phase 2 | AbilityChecker + CharacterChecker | 2个P0检测器 |
| Phase 3 | ForeshadowChecker + RelationshipStateChecker | 2个P1检测器 |
| Phase 4 | BattleVisualization + PersonalityChecker | 2个P2检测器 |
| Phase 5 | KnowledgeTracker | 1个P3检测器 |

---

## 9. 检测能力对比

| 矛盾类型 | 修复前 | 修复后 |
|---------|-------|-------|
| 能力未学先用 | ⚠️ 表层 | ✅ 深层 |
| 性格行为矛盾 | ⚠️ 词表 | ✅ 语义 |
| 伏笔回收矛盾 | ⚠️ 仅时间 | ✅ 质量 |
| 关系突变 | ⚠️ 统计 | ✅ 语义 |
| 战斗描写 | ⚠️ 比例 | ✅ 逻辑 |
| 性格稳定性 | ⚠️ 粗糙 | ✅ 精细 |
| 信息知晓 | ⚠️ 显式 | ✅ 隐式 |
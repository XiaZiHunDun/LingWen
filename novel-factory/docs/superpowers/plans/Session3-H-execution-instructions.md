# Session 3 执行指令：方向H（质量工具集）

> **项目路径**: `/home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory`
> **参考文档**: `docs/superpowers/specs/2026-05-19-quality-gate-multi-style-drafting-design.md`

---

## 方向H：质量工具集

### H-Step1: 创建Writer Persona定义
**Task ID**: #37
**文件**: `quality_tools/writer_persona.py`

**参考**: 设计文档第4节 Writer Persona 定义

**实现要点**:
1. 定义 `WriterPersona` 数据类:
   ```python
   @dataclass
   class WriterPersona:
       name: str                          # "紧张快节奏" / "细腻描写" / "对话驱动"
       description: str                   # 风格描述
       temperature: float = 0.7
       top_p: float = 0.9
       max_tokens: int = 4000
       system_prompt_suffix: str = ""     # 附加的系统提示
   ```

2. 定义预定义风格变体（3种）:
   ```python
   TENSE_FAST = WriterPersona(
       name="紧张快节奏",
       description="高悬念、短句、快速推进",
       temperature=0.8,
       top_p=0.85,
       max_tokens=3000
   )

   DELICATE_DESCRIPTIVE = WriterPersona(
       name="细腻描写",
       description="环境渲染、情绪铺垫、慢热",
       temperature=0.6,
       top_p=0.9,
       max_tokens=5000
   )

   DIALOGUE_DRIVEN = WriterPersona(
       name="对话驱动",
       description="人物互动为主、动作描写少",
       temperature=0.7,
       top_p=0.9,
       max_tokens=3500
   )

   ALL_PERSONAS = [TENSE_FAST, DELICATE_DESCRIPTIVE, DIALOGUE_DRIVEN]
   ```

3. 定义 `PersonaConfig` 管理器:
   ```python
   class PersonaConfig:
       def get_persona(self, name: str) -> WriterPersona: ...
       def list_personas(self) -> List[WriterPersona]: ...
   ```

**验收标准**:
- `PersonaConfig().get_persona("紧张快节奏")` 返回正确的Persona
- `ALL_PERSONAS` 包含3种预定义风格

---

### H-Step2: 创建多风格起草器
**Task ID**: #39
**文件**: `quality_tools/multi_style_drafter.py`

**参考**: 设计文档第3节架构图

**实现要点**:
1. 定义 `DraftVariant` 数据类:
   ```python
   @dataclass
   class DraftVariant:
       persona: WriterPersona
       content: str                       # 生成的文本
       style_score: float = 0.0          # 风格契合度评分
   ```

2. 定义 `MultiStyleDrafter` 类:
   ```python
   class MultiStyleDrafter:
       def __init__(self, ai_provider: AIProvider): ...
       def draft(
           self,
           outline: Dict[str, Any],
           characters: List[Dict],
           style_guide: Dict[str, Any],
           personas: List[WriterPersona] = None  # 默认3种
       ) -> List[DraftVariant]: ...
   ```

3. 并行生成:
   - 使用 `asyncio.gather` 并行调用 LLM
   - 每个 persona 生成一个变体
   - 返回变体列表供选择

**验收标准**:
- `drafter.draft(outline, characters, style_guide)` 返回3个变体
- 变体内容各不相同（不同风格）
- 异步并行生成提高速度

---

### H-Step3: 创建质量门禁
**Task ID**: #42
**文件**: `quality_tools/quality_gate.py`

**参考**: 设计文档第3节质量门禁系统

**实现要点**:
1. 定义质量等级枚举:
   ```python
   class QualityLevel(Enum):
       BRONZE = ("Bronze", 0.60)    # (名称, 最低分数)
       SILVER = ("Silver", 0.75)
       GOLD = ("Gold", 0.90)
       PLATINUM = ("Platinum", 0.95)
   ```

2. 定义 `QualityGate` 类:
   ```python
   class QualityGate:
       def __init__(
           self,
           hard_validators: List[BaseValidator],
           soft_scorers: List[BaseScorer]
       ): ...

       def check(self, content: str, context: Dict[str, Any]) -> QualityResult:
           """
           返回 QualityResult:
           - level: QualityLevel
           - hard_passed: bool
           - soft_score: float
           - issues: List[str]
           """

       def get_required_level(self) -> QualityLevel: ...
   ```

3. 分级逻辑:
   - 硬性验证器全部通过 → 软性评分计算
   - Bronze: 硬性通过 + 软性评分 ≥ 60%
   - Silver: 硬性通过 + 软性评分 ≥ 75%
   - Gold: 硬性通过 + 软性评分 ≥ 90%
   - Platinum: 硬性通过 + 软性评分 ≥ 95% + 无P0问题

**验收标准**:
- `quality_gate.check(content, context)` 返回正确的QualityResult
- 分级逻辑正确（60-75 Bronze, 75-90 Silver, 90-95 Gold, 95+ Platinum）

---

### H-Step4: 创建硬性验证器
**Task ID**: #40
**文件**: `quality_tools/hard_validators/` 目录下5个文件

**参考**: 设计文档第3节硬性验证器定义

**实现要点**:

#### base.py
```python
class BaseValidator(ABC):
   @abstractmethod
   def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult: ...

@dataclass
class ValidationResult:
   passed: bool
   issues: List[str] = field(default_factory=list)
   severity: IssueSeverity = IssueSeverity.P2
```

#### continuity.py - 角色状态连续性
```python
class ContinuityValidator(BaseValidator):
   """检查角色状态在章节内不矛盾"""
   def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
       # 从context获取角色设定
       # 检查内容中角色状态是否一致
```

#### timeline.py - 时间线一致性
```python
class TimelineValidator(BaseValidator):
   """检查章节内时间逻辑一致"""
   def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
       # 检查时间表述不矛盾（早上→中午→晚上）
```

#### perspective.py - POV不漂移
```python
class PerspectiveValidator(BaseValidator):
   """检查POV不漂移"""
   def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
       # 检测第一人称/第三人称切换
```

#### knowledge_state.py - 知识状态验证
```python
class KnowledgeStateValidator(BaseValidator):
   """检查设定不被违反"""
   def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
       # 检查角色不应知道他们尚未发现的事实
```

#### forbidden_patterns.py - 禁用模式验证
```python
class ForbiddenPatternsValidator(BaseValidator):
   """检查禁用表达套路"""
   def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
       # 检测AI痕迹、无效重复、太监句式等
```

**验收标准**:
- 每个Validator的`validate()`返回ValidationResult
- `passed=False`时`issues`列表包含具体问题

---

### H-Step5: 创建软性评分器
**Task ID**: #41
**文件**: `quality_tools/soft_scorers/` 目录下10个文件

**实现要点**:

#### base.py
```python
class BaseScorer(ABC):
   @abstractmethod
   def score(self, content: str, context: Dict[str, Any]) -> ScoredResult: ...

@dataclass
class ScoredResult:
   score: float           # 0-100
   reason: str = ""
```

#### 10个评分器:

1. **tension.py** - 张力评分
   - 评估场景的紧张程度

2. **emotion.py** - 情感评分
   - 评估情感共鸣强度

3. **prose_vitality.py** - 散文活力
   - 评估表达的多样性和活力

4. **voice_consistency.py** - 声音一致性
   - 评估叙述声音的一致性

5. **dialogue.py** - 对话质量
   - 评估对话的自然度和信息量

6. **theme_integration.py** - 主题整合
   - 评估主题是否贯穿

7. **redundancy.py** - 冗余检测
   - 评估是否有重复表达

8. **transition.py** - 过渡流畅度
   - 评估场景/段落过渡

9. **scene_purpose.py** - 场景目的
   - 评估每个场景是否有目的

10. **symbolism.py** - 象征约束
    - 评估象征元素使用

**验收标准**:
- 每个Scorer的`score()`返回0-100的分数
- 分数合理反映该维度的质量

---

### H-Step6: 编写质量工具测试
**Task ID**: #38
**文件**: `tests/quality_tools/test_multi_style_drafter.py`, `test_quality_gate.py`, `test_validators.py`

**实现要点**:

#### test_multi_style_drafter.py
- `TestMultiStyleDrafter::test_draft_returns_variants` - 验证返回多个变体
- `TestMultiStyleDrafter::test_variants_have_different_content` - 验证变体内容不同
- `TestMultiStyleDrafter::test_variants_have_persona_info` - 验证变体包含persona信息

#### test_quality_gate.py
- `TestQualityGate::test_bronze_level` - Bronze分级测试
- `TestQualityGate::test_silver_level` - Silver分级测试
- `TestQualityGate::test_gold_level` - Gold分级测试
- `TestQualityGate::test_platinum_level` - Platinum分级测试
- `TestQualityGate::test_hard_validators_must_pass` - 硬性验证器必须通过

#### test_validators.py
- `TestContinuityValidator::test_detects_inconsistency` - 检测状态矛盾
- `TestTimelineValidator::test_detects_time_contradiction` - 检测时间矛盾
- `TestPerspectiveValidator::test_detects_pov_drift` - 检测POV漂移
- `TestKnowledgeStateValidator::test_detects_knowledge_violation` - 检测知识状态违反
- `TestForbiddenPatternsValidator::test_detects_ai_patterns` - 检测AI模式

**验收标准**: 所有测试通过

---

## 执行顺序建议

```
Session 3:
├── H-Step1: 创建Writer Persona定义
├── H-Step2: 创建多风格起草器
├── H-Step3: 创建质量门禁
├── H-Step4: 创建硬性验证器
├── H-Step5: 创建软性评分器
└── H-Step6: 编写质量工具测试
```

**完成后请更新Task状态为completed**
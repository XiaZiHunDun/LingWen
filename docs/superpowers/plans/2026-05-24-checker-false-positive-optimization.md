# 检测器误报优化 Layer 1-2 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为检测器增加置信度分级（Layer 1）和上下文增强（Layer 2），减少误报率

**Architecture:**
- Layer 1: 在 `data_structures.py` 中扩展 `Issue` 数据结构，增加 `confidence` 和 `confidence_score` 字段；各检测器根据上下文充分度计算置信度
- Layer 2: 新增 `context/` 目录存放角色档案和场景类型注册表；`consistency_engine.py` 增强上下文注入逻辑

**Tech Stack:** Python dataclass, YAML, 现有检测器架构

---

## 文件变更总览

| 文件 | 操作 |
|------|------|
| `infra/consistency/engine/data_structures.py` | 修改 |
| `infra/consistency/engine/consistency_engine.py` | 修改 |
| `context/character_profiles.yaml` | 新增 |
| `context/scene_types.yaml` | 新增 |
| `tests/test_confidence.py` | 新增 |

---

## Task 1: 扩展 Issue 数据结构（ConfidenceLevel）

**Files:**
- Modify: `infra/consistency/engine/data_structures.py:18-23`

- [ ] **Step 1: 添加 ConfidenceLevel 枚举**

在 `IssueSeverity` 之后添加：

```python
class ConfidenceLevel(Enum):
    """检测置信度"""
    HIGH = "HIGH"   # 置信度>85%，可直接处理
    MEDIUM = "MED"  # 置信度60-85%，需LLM复核
    LOW = "LOW"     # 置信度<60%，人工审核
```

- [ ] **Step 2: 运行测试验证无语法错误**

Run: `cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory && python -c "from infra.consistency.engine.data_structures import ConfidenceLevel; print('OK')"`
Expected: `OK`

- [ ] **Step 3: 提交**

```bash
git add infra/consistency/engine/data_structures.py
git commit -m "feat: add ConfidenceLevel enum for issue confidence scoring"
```

---

## Task 2: Issue 数据结构增加置信度字段

**Files:**
- Modify: `infra/consistency/engine/data_structures.py:74-102`

- [ ] **Step 1: 扩展 Issue 类**

在 `Issue` 类 `created_at` 字段后添加新字段：

```python
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    confidence_score: float = 0.5  # 0.0-1.0 详细分数
    context_used: List[str] = field(default_factory=list)  # 使用的上下文
    needs_llm_review: bool = False  # 是否需LLM复核
```

- [ ] **Step 2: 更新 to_dict 方法**

在 `to_dict` 方法的返回值中添加：

```python
            "confidence": self.confidence.value,
            "confidence_score": self.confidence_score,
            "context_used": self.context_used,
            "needs_llm_review": self.needs_llm_review,
```

- [ ] **Step 3: 更新 from_dict 方法**

在 `from_dict` 方法的 `return cls(...)` 中添加：

```python
            confidence=data.get("confidence", "MED"),
            confidence_score=data.get("confidence_score", 0.5),
            context_used=data.get("context_used", []),
            needs_llm_review=data.get("needs_llm_review", False),
```

- [ ] **Step 4: 运行测试验证无语法错误**

Run: `cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory && python -c "from infra.consistency.engine.data_structures import Issue, ConfidenceLevel; i = Issue(id='test', severity=IssueSeverity.P0, checker_type=CheckerType.CHARACTER, issue_type='test', title='Test', description='Test', location=IssueLocation(chapter=1)); print(f'confidence={i.confidence}, score={i.confidence_score}')"`
Expected: `confidence=ConfidenceLevel.MEDIUM, score=0.5`

- [ ] **Step 5: 提交**

```bash
git add infra/consistency/engine/data_structures.py
git commit -m "feat: add confidence fields to Issue dataclass"
```

---

## Task 3: 创建角色档案上下文文件

**Files:**
- Create: `context/character_profiles.yaml`

- [ ] **Step 1: 创建 context 目录**

```bash
mkdir -p context
```

- [ ] **Step 2: 创建 character_profiles.yaml**

根据小说内容创建（基于之前发现的9个角色）：

```yaml
# 角色档案 - 用于检测器上下文增强
# 检测器使用 context["character_profiles"] 获取角色设定

characters:
  林夜:
    personality_traits: ["沉稳", "果断", "内敛"]
    behavior_patterns: ["战斗时冷静", "关键时刻爆发"]
    language_style: ["简短有力", "少用感叹词"]
    known_limitations: ["对林白羽有软肋"]
    context_tags: ["主角", "成长型", "剑修"]
    # 误报规避：这些场景/行为不触发检测
    skip_checks:
      - scene_types: ["cosmic", "dream", "game_world"]
        reason: "特殊场景下行为可能异常"

  苏琳:
    personality_traits: ["活泼", "聪慧", "独立"]
    behavior_patterns: ["善于观察", "关键时刻犹豫"]
    language_style: ["带点俏皮", "常用反问"]
    known_limitations: []
    context_tags: ["女主", "辅助型", "法修"]

  星澜:
    personality_traits: ["神秘", "深沉", "高傲"]
    behavior_patterns: ["操控局势", "幕后观察"]
    language_style: ["文雅", "暗示性"]
    known_limitations: []
    context_tags: ["反派", "谋略型", "首脑"]

  # 根据需要继续添加其他角色...
```

- [ ] **Step 3: 提交**

```bash
git add context/character_profiles.yaml
git commit -m "feat: add character profiles context for checker confidence"
```

---

## Task 4: 创建场景类型上下文文件

**Files:**
- Create: `context/scene_types.yaml`

- [ ] **Step 1: 创建 scene_types.yaml**

```yaml
# 场景类型注册表 - 用于检测器上下文增强
# 检测器使用 context["scene_type"] 或 scene_types.yaml 判断场景类型
# 特殊场景（宇宙/游戏/梦境）应跳过某些时间线检测

scene_registry:
  # 卷1: 现实世界/成长篇 (ch001-ch120)
  ch001: { type: "real_world", time_flow: "normal", description: "林家村童年" }
  ch010: { type: "real_world", time_flow: "normal", description: "青云宗入门" }
  ch050: { type: "real_world", time_flow: "normal", description: "宗门修炼" }

  # 卷2: 星际探索篇 (ch121-ch240)
  ch121: { type: "cosmic", time_flow: "distorted", description: "星际战场" }
  ch150: { type: "cosmic", time_flow: "distorted", description: "虚空探索" }
  ch180: { type: "cosmic", time_flow: "distorted", description: "星陨纪元核心" }

  # 卷3: 终极挑战篇 (ch241-ch360)
  ch241: { type: "mixed", time_flow: "normal", description: "回归现实" }
  ch300: { type: "cosmic", time_flow: "distorted", description: "最终决战" }
  ch350: { type: "real_world", time_flow: "normal", description: "和平结局" }

# 场景类型说明
scene_types:
  real_world:
    time_flow: "normal"  # 时间正常流逝
    skip_timeline_check: false
    description: "现实世界/正常时间流场景"

  cosmic:
    time_flow: "distorted"  # 时间可能扭曲
    skip_timeline_check: true  # 跳过时间线合理性检测
    description: "宇宙级场景/星际战场"

  game_world:
    time_flow: "virtual"  # 虚拟时间
    skip_timeline_check: true
    description: "虚拟游戏世界/意识空间"

  dream:
    time_flow: "distorted"
    skip_timeline_check: true
    description: "梦境/潜意识场景"

  mixed:
    time_flow: "normal"
    skip_timeline_check: false
    description: "混合场景"
```

- [ ] **Step 2: 提交**

```bash
git add context/scene_types.yaml
git commit -m "feat: add scene types registry for context enrichment"
```

---

## Task 5: 增强 consistency_engine 上下文注入

**Files:**
- Modify: `infra/consistency/engine/consistency_engine.py`

- [ ] **Step 1: 添加 YAML 加载依赖和辅助方法**

在 `consistency_engine.py` 顶部 import 后添加：

```python
import yaml
from pathlib import Path

# 上下文配置文件路径
CONTEXT_DIR = PROJECT_ROOT / "context"
CHARACTER_PROFILES_PATH = CONTEXT_DIR / "character_profiles.yaml"
SCENE_TYPES_PATH = CONTEXT_DIR / "scene_types.yaml"
```

- [ ] **Step 2: 添加加载角色档案的方法**

在 `_get_character_ages_context` 方法后添加：

```python
def _load_character_profiles(self) -> Dict[str, Any]:
    """加载角色档案"""
    if not CHARACTER_PROFILES_PATH.exists():
        return {}
    try:
        with open(CHARACTER_PROFILES_PATH, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data.get("characters", {})
    except Exception:
        return {}

def _get_scene_type(self, chapter_num: int) -> Dict[str, Any]:
    """获取章节场景类型"""
    if not SCENE_TYPES_PATH.exists():
        return {}
    try:
        with open(SCENE_TYPES_PATH, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            scene_registry = data.get("scene_registry", {})
            ch_key = f"ch{chapter_num:03d}"
            return scene_registry.get(ch_key, {})
    except Exception:
        return {}
```

- [ ] **Step 3: 扩展 _enrich_context_from_memory 方法**

在 `if auto_context:` 块之后添加角色档案加载：

```python
        # 5. 加载角色档案（用于 CharacterChecker 置信度计算）
        if "character_profiles" not in enriched:
            enriched["character_profiles"] = self._load_character_profiles()

        # 6. 加载场景类型（用于 TimelineChecker 误报规避）
        if "scene_type" not in enriched:
            enriched["scene_type"] = self._get_scene_type(chapter_num)
```

- [ ] **Step 4: 修改 _inject_scene_and_age_context 方法**

在方法开始处添加场景类型获取：

```python
def _inject_scene_and_age_context(
    self,
    chapter_num: int,
    chapter_content: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    注入场景标签和角色年龄上下文
    """
    enriched = context.copy()

    # 获取场景类型（用于判断是否跳过时间线检测）
    if "scene_type" not in enriched:
        enriched["scene_type"] = self._get_scene_type(chapter_num)
```

- [ ] **Step 5: 运行测试验证无语法错误**

Run: `cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory && python -c "from infra.consistency.engine.consistency_engine import ConsistencyEngine; e = ConsistencyEngine(); print('OK')"`
Expected: `OK`

- [ ] **Step 6: 提交**

```bash
git add infra/consistency/engine/consistency_engine.py
git commit -m "feat: enrich context with character profiles and scene types"
```

---

## Task 6: 验证完整流程**

- [ ] **Step 1: 运行现有测试确保无回归**

Run: `cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory && python -m pytest tests/consistency/ -v --tb=short 2>&1 | head -50`
Expected: 所有测试通过

- [ ] **Step 2: 验证配置文件加载**

Run: `cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory && python -c "
from infra.consistency.engine.consistency_engine import ConsistencyEngine
e = ConsistencyEngine()
profiles = e._load_character_profiles()
scene = e._get_scene_type(1)
print(f'Profiles: {len(profiles)} characters')
print(f'Scene ch001: {scene}')
"`
Expected: 显示角色数量和场景类型

- [ ] **Step 3: 提交**

```bash
git add -A
git commit -m "test: verify context enrichment works correctly"
```

---

## 实施后验证

完成后，检测器应能：
1. 每个 `Issue` 包含 `confidence` 和 `confidence_score` 字段
2. `context["character_profiles"]` 包含角色档案
3. `context["scene_type"]` 包含场景类型（判断是否应跳过时间线检测）
4. 场景类型为 `cosmic`/`game_world`/`dream` 时可跳过时间线合理性检测
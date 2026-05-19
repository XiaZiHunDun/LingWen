# Agent协作系统实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 构建专项Agent协作系统，5个专业Agent（大纲师/ 人设师/ 正文写手/ 审计官/ 润色师）通过标准化文件协作，社交模拟引擎提供关系驱动的写作建议

**架构：** 专项Agent + 文件共享 + 主控调度。5个专业Agent各自有独立profile和工具集，通过标准化文件交换数据，社交模拟引擎追踪关系网络并生成写作建议。

**技术栈：** Python, YAML, JSON, AI服务抽象层

---

## 文件结构

```
novel-factory/
├── agent_system/
│   ├── __init__.py
│   ├── master_controller.py           # 主控调度器
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── outline_master/
│   │   │   ├── __init__.py
│   │   │   ├── agent_profile.md       # Agent角色定义
│   │   │   ├── tools.py               # 工具函数
│   │   │   └── memory.md              # Agent记忆
│   │   ├── character_designer/
│   │   │   ├── __init__.py
│   │   │   ├── agent_profile.md
│   │   │   ├── tools.py
│   │   │   └── memory.md
│   │   ├── content_writer/
│   │   │   ├── __init__.py
│   │   │   ├── agent_profile.md
│   │   │   ├── tools.py
│   │   │   └── memory.md
│   │   ├── auditor/
│   │   │   ├── __init__.py
│   │   │   ├── agent_profile.md
│   │   │   ├── tools.py
│   │   │   └── memory.md
│   │   └── polisher/
│   │       ├── __init__.py
│   │       ├── agent_profile.md
│   │       ├── tools.py
│   │       └── memory.md
│   ├── social_engine/
│   │   ├── __init__.py
│   │   ├── relationship_tracker.py    # 关系追踪器
│   │   ├── event_effect_calculator.py # 事件效果计算
│   │   ├── conflict_alert.py          # 冲突预警
│   │   ├── writing_suggestion.py      # 写作建议
│   │   └── rules/
│   │       ├── __init__.py
│   │       ├── event_effects.yaml     # 事件效果规则
│   │       └── emergence.yaml        # 涌现检测规则
│   └── shared/
│       ├── __init__.py
│       ├── outline_schema.py          # 大纲Schema
│       ├── character_schema.py        # 角色Schema
│       └── context_builder.py         # 上下文构建器
└── config/
    └── agent_config.yaml              # Agent配置
```

---

## 数据结构定义

### agent_config.yaml

```yaml
agents:
  outline_master:
    name: "大纲师"
    description: "资深网文大纲设计师"
    model: "qwen"
    temperature: 0.7

  character_designer:
    name: "人设师"
    description: "资深角色设计师"
    model: "deepseek"
    temperature: 0.6

  content_writer:
    name: "正文写手"
    description: "专业网文作家"
    model: "deepseek"
    temperature: 0.8

  auditor:
    name: "审计官"
    description: "资深小说审核专家"
    model: "claude"
    temperature: 0.5

  polisher:
    name: "润色师"
    description: "资深文字编辑"
    model: "qwen"
    temperature: 0.6

social_engine:
  trust_change_threshold: 0.3
  conflict_outbreak_threshold: 0.7
  isolated_character_threshold: 3  # 连续无互动章数
```

### event_effects.yaml

```yaml
event_effects:
  save_life:
    trust_delta: +0.3
    conflict_delta: -0.2

  betrayal:
    trust_delta: -0.4
    conflict_delta: +0.3

  physical_conflict:
    trust_delta: -0.1
    conflict_delta: +0.3

  verbal_argument:
    trust_delta: -0.05
    conflict_delta: +0.2

  share_secret:
    trust_delta: +0.2
    conflict_delta: -0.1
    intimate_only: true

  gift_given:
    trust_delta: +0.1
    conflict_delta: 0

  promise_made:
    trust_delta: +0.15
    conflict_delta: 0

  promise_broken:
    trust_delta: -0.25
    conflict_delta: +0.15
```

### emergence.yaml

```yaml
emergence_detection:
  trust_sudden_change:
    threshold: 0.3
    alert: true

  conflict_outbreak:
    threshold: 0.7
    alert: true
    suggestion: "考虑加入冲突场景"

  relationship_reversal:
    alert: true
    suggestion: "关系逆转，可作为情节转折点"

  isolated_character:
    threshold: 3
    suggestion: "角色可能需要互动机会"

  trust_building:
    threshold: 0.5
    alert: false
    suggestion: "信任积累中，可考虑深化关系"
```

### relationship_network.json

```json
{
  "characters": ["林夜", "苏琳", "莫言"],
  "relationships": [
    {
      "from": "林夜",
      "to": "苏琳",
      "trust": 0.7,
      "conflict": 0.1,
      "type": "ally",
      "last_event": "ch010"
    }
  ],
  "events": []
}
```

---

## 任务清单

### Task 1: Agent基础架构与目录结构

**Files:**
- Create: `novel-factory/agent_system/__init__.py`
- Create: `novel-factory/agent_system/agents/__init__.py`
- Create: `novel-factory/agent_system/agents/outline_master/__init__.py`
- Create: `novel-factory/agent_system/agents/character_designer/__init__.py`
- Create: `novel-factory/agent_system/agents/content_writer/__init__.py`
- Create: `novel-factory/agent_system/agents/auditor/__init__.py`
- Create: `novel-factory/agent_system/agents/polisher/__init__.py`
- Create: `novel-factory/agent_system/social_engine/__init__.py`
- Create: `novel-factory/agent_system/social_engine/rules/__init__.py`
- Create: `novel-factory/agent_system/shared/__init__.py`
- Create: `novel-factory/config/agent_config.yaml`

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p novel-factory/agent_system/agents/{outline_master,character_designer,content_writer,auditor,polisher}
mkdir -p novel-factory/agent_system/social_engine/rules
mkdir -p novel-factory/agent_system/shared
touch novel-factory/agent_system/__init__.py
touch novel-factory/agent_system/agents/__init__.py
# 各Agent的__init__.py
for dir in outline_master character_designer content_writer auditor polisher; do
  touch "novel-factory/agent_system/agents/$dir/__init__.py"
done
touch novel-factory/agent_system/social_engine/__init__.py
touch novel-factory/agent_system/social_engine/rules/__init__.py
touch novel-factory/agent_system/shared/__init__.py
```

- [ ] **Step 2: 创建 agent_config.yaml**

```yaml
# novel-factory/config/agent_config.yaml
agents:
  outline_master:
    name: "大纲师"
    description: "资深网文大纲设计师"
    specialty:
      - 长篇小说结构设计
      - 三幕节奏控制
      - 伏笔埋设布局
      - 爽点密度规划
    model: "qwen"
    temperature: 0.7

  character_designer:
    name: "人设师"
    description: "资深角色设计师"
    specialty:
      - 人物设定与关系网络
      - 角色弧光设计
      - 行为一致性保障
    model: "deepseek"
    temperature: 0.6

  content_writer:
    name: "正文写手"
    description: "专业网文作家"
    specialty:
      - 长篇小说章节创作
      - 多场景切换
      - 角色对话个性化
      - 节奏把控
    model: "deepseek"
    temperature: 0.8

  auditor:
    name: "审计官"
    description: "资深小说审核专家"
    specialty:
      - 一致性检查
      - 逻辑漏洞发现
      - 质量评估
    model: "claude"
    temperature: 0.5

  polisher:
    name: "润色师"
    description: "资深文字编辑"
    specialty:
      - 文风统一
      - 对话自然化
      - 节奏优化
      - AI痕迹去除
    model: "qwen"
    temperature: 0.6

social_engine:
  trust_change_threshold: 0.3
  conflict_outbreak_threshold: 0.7
  isolated_character_threshold: 3
```

- [ ] **Step 3: 提交**

```bash
git add novel-factory/agent_system/ novel-factory/config/agent_config.yaml
git commit -m "feat(agent): 创建Agent系统目录结构"
```

---

### Task 2: 共享数据结构（Schema）

**Files:**
- Create: `novel-factory/agent_system/shared/outline_schema.py`
- Create: `novel-factory/agent_system/shared/character_schema.py`
- Create: `tests/agent_system/test_schemas.py`

- [ ] **Step 1: 编写测试**

```python
# tests/agent_system/test_schemas.py
import pytest
import yaml
from agent_system.shared.outline_schema import OutlineSchema
from agent_system.shared.character_schema import CharacterSchema

def test_outline_schema_validation():
    schema = OutlineSchema()
    outline = {
        "title": "测试大纲",
        "chapters": [
            {"num": 1, "title": "第一章", "events": ["事件1", "事件2"]}
        ]
    }
    assert schema.validate(outline) is True

def test_character_schema_validation():
    schema = CharacterSchema()
    character = {
        "name": "铁蛋",
        "role": "protagonist",
        "personality": ["冷静", "务实"],
        "first_appearance": 1
    }
    assert schema.validate(character) is True
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/agent_system/test_schemas.py -v
# 预期: FAIL
```

- [ ] **Step 3: 实现 OutlineSchema**

```python
# novel-factory/agent_system/shared/outline_schema.py
from typing import Dict, List, Any, Optional
import yaml

class OutlineSchema:
    """大纲Schema定义与验证"""

    REQUIRED_FIELDS = ["title", "chapters"]

    def validate(self, outline: Dict) -> bool:
        """验证大纲结构"""
        for field in self.REQUIRED_FIELDS:
            if field not in outline:
                raise ValueError(f"Missing required field: {field}")
        if not isinstance(outline["chapters"], list):
            raise ValueError("chapters must be a list")
        return True

    def to_yaml(self, outline: Dict, file_path: str):
        """导出为YAML"""
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(outline, f, allow_unicode=True, default_flow_style=False)

    def from_yaml(self, file_path: str) -> Dict:
        """从YAML加载"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def get_chapter_outline(self, outline: Dict, chapter_num: int) -> Optional[Dict]:
        """获取指定章节的大纲"""
        for ch in outline.get("chapters", []):
            if ch.get("num") == chapter_num:
                return ch
        return None
```

- [ ] **Step 4: 实现 CharacterSchema**

```python
# novel-factory/agent_system/shared/character_schema.py
from typing import Dict, List, Any
import yaml

class CharacterSchema:
    """角色Schema定义与验证"""

    REQUIRED_FIELDS = ["name", "personality", "first_appearance"]

    def validate(self, character: Dict) -> bool:
        """验证角色结构"""
        for field in self.REQUIRED_FIELDS:
            if field not in character:
                raise ValueError(f"Missing required field: {field}")
        return True

    def to_yaml(self, character: Dict, file_path: str):
        """导出为YAML"""
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(character, f, allow_unicode=True, default_flow_style=False)

    def from_yaml(self, file_path: str) -> Dict:
        """从YAML加载"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def to_character_card(self, character: Dict) -> str:
        """生成角色卡片文本"""
        lines = [
            f"# {character['name']}",
            f"**角色**: {character.get('role', 'N/A')}",
            f"**首次出场**: 第{character['first_appearance']}章",
            "",
            "## 性格",
            ", ".join(character.get('personality', [])),
            "",
            "## 背景",
            character.get('background', 'N/A'),
            "",
            "## 能力",
            character.get('abilities', 'N/A'),
            "",
            "## 关系",
        ]
        for rel in character.get('relationships', []):
            lines.append(f"- **{rel['target']}**: {rel['type']} (信任:{rel.get('trust', 0)}, 冲突:{rel.get('conflict', 0)})")
        return "\n".join(lines)
```

- [ ] **Step 5: 运行测试验证通过**

```bash
pytest tests/agent_system/test_schemas.py -v
# 预期: PASS
```

- [ ] **Step 6: 提交**

```bash
git add novel-factory/agent_system/shared/outline_schema.py novel-factory/agent_system/shared/character_schema.py tests/agent_system/test_schemas.py
git commit -m "feat(agent): 实现共享数据结构Schema"
```

---

### Task 3: 上下文构建器

**Files:**
- Create: `novel-factory/agent_system/shared/context_builder.py`
- Create: `tests/agent_system/test_context_builder.py`

- [ ] **Step 1: 编写测试**

```python
# tests/agent_system/test_context_builder.py
import pytest
from agent_system.shared.context_builder import ContextBuilder

def test_context_builder_init():
    builder = ContextBuilder()
    assert builder is not None

def test_build_writing_context():
    builder = ContextBuilder()
    context = builder.build_writing_context(
        chapter_outline={"num": 50, "title": "第五十章"},
        characters=[{"name": "铁蛋", "personality": ["冷静"]}],
        memory_context={},
        relationship_network={}
    )
    assert context["chapter_outline"]["num"] == 50
    assert len(context["characters"]) == 1
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/agent_system/test_context_builder.py -v
# 预期: FAIL
```

- [ ] **Step 3: 实现 ContextBuilder**

```python
# novel-factory/agent_system/shared/context_builder.py
from typing import Dict, List, Optional, Any

class ContextBuilder:
    """上下文构建器 - 各Agent的数据共享标准"""

    def build_writing_context(
        self,
        chapter_outline: Dict,
        characters: List[Dict],
        memory_context: Dict,
        relationship_network: Dict,
        style_guide: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        构建写作上下文
        """
        character_states = self._get_current_states(characters)
        active_foreshadow = self._get_active_foreshadow(memory_context)
        recent_events = self._get_recent_events(memory_context)

        return {
            "chapter_outline": chapter_outline,
            "characters": characters,
            "character_states": character_states,
            "relationship_network": relationship_network,
            "active_foreshadow": active_foreshadow,
            "recent_events": recent_events,
            "style_guide": style_guide or self._get_default_style_guide()
        }

    def _get_current_states(self, characters: List[Dict]) -> Dict[str, Dict]:
        """获取角色当前状态"""
        states = {}
        for char in characters:
            states[char["name"]] = {
                "location": char.get("current_location"),
                "emotion": char.get("emotion_state"),
                "alive": char.get("alive", True)
            }
        return states

    def _get_active_foreshadow(self, memory_context: Dict) -> List[Dict]:
        """获取活跃伏笔"""
        return memory_context.get("pending_foreshadows", [])

    def _get_recent_events(self, memory_context: Dict) -> List[Dict]:
        """获取最近事件"""
        return memory_context.get("recent_events", [])[-5:]

    def _get_default_style_guide(self) -> Dict:
        """获取默认文风指南"""
        return {
            "tone": "简洁有力",
            "dialogue_ratio": "30%",
            "description_style": "白描为主"
        }
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/agent_system/test_context_builder.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add novel-factory/agent_system/shared/context_builder.py tests/agent_system/test_context_builder.py
git commit -m "feat(agent): 实现上下文构建器"
```

---

### Task 4: Agent Profile定义

**Files:**
- Create: `novel-factory/agent_system/agents/outline_master/agent_profile.md`
- Create: `novel-factory/agent_system/agents/character_designer/agent_profile.md`
- Create: `novel-factory/agent_system/agents/content_writer/agent_profile.md`
- Create: `novel-factory/agent_system/agents/auditor/agent_profile.md`
- Create: `novel-factory/agent_system/agents/polisher/agent_profile.md`

- [ ] **Step 1: 创建大纲师Profile**

```markdown
# 大纲师 Agent Profile

## 基本信息

- **名称**: 大纲师
- **角色**: 资深网文大纲设计师
- **专业领域**: 长篇小说结构设计、三幕节奏控制、伏笔埋设布局

## 专业工具

| 工具名 | 功能 | 输入 | 输出 |
|--------|------|------|------|
| generate_outline | 生成全文大纲 | 作品设定 | 完整大纲 |
| generate_volume_outline | 生成卷大纲 | 卷设定 | 卷大纲 |
| generate_chapter_outline | 生成章大纲 | 章节要求 | 章大纲 |
| check_outline_consistency | 一致性检查 | 大纲内容 | 检查报告 |
| layout_foreshadow | 伏笔布局 | 伏笔规划 | 伏笔列表 |

## 输出规范

- 文件命名: `{类型}_v{版本}.md`
- 包含: 章节标题、核心事件、字数目标、伏笔标记
- 格式: Markdown

## Prompt模板

### generate_outline

请为以下作品生成完整大纲：

**作品设定**:
{settings}

**要求**:
1. 三幕结构清晰
2. 伏笔埋设合理
3. 爽点密度适中
4. 字数目标: {word_count}

请按以下格式输出：
{format_template}
```

- [ ] **Step 2: 创建人设师Profile**

```markdown
# 人设师 Agent Profile

## 基本信息

- **名称**: 人设师
- **角色**: 资深角色设计师
- **专业领域**: 人物设定与关系网络、角色弧光设计

## 专业工具

| 工具名 | 功能 | 输入 | 输出 |
|--------|------|------|------|
| generate_character_card | 生成角色卡片 | 角色需求 | 角色YAML |
| update_relationship | 更新关系 | 关系变化 | 关系更新 |
| design_character_arc | 设计弧光 | 角色信息 | 弧光设计 |
| check_behavior_consistency | 行为一致性检查 | 行为描述 | 检查报告 |

## 输出规范

- 文件命名: `{角色名}.角色.yaml`
- 包含: 基础信息、性格、背景、能力、关系、弧光
- 格式: YAML

## Prompt模板

### generate_character_card

请为以下角色生成角色卡片：

**角色需求**:
{requirements}

**已有设定**:
{existing_settings}

请按以下格式输出YAML：
{format_template}
```

- [ ] **Step 3: 创建正文写手Profile**

```markdown
# 正文写手 Agent Profile

## 基本信息

- **名称**: 正文写手
- **角色**: 专业网文作家
- **专业领域**: 长篇小说章节创作、多场景切换、角色对话个性化

## 专业工具

| 工具名 | 功能 | 输入 | 输出 |
|--------|------|------|------|
| build_writing_prompt | 构建写作Prompt | 上下文 | 完整Prompt |
| generate_chapter | 生成章节 | Prompt | 章节正文 |
| adjust_word_count | 字数调整 | 章节+字数 | 调整后章节 |
| add_chapter_hook | 添加章末钩子 | 章节结尾 | 带钩子结尾 |

## 上下文输入

- chapter_outline: 章节大纲
- character_cards: 角色卡片
- memory_context: 记忆上下文
- style_guide: 文风指南

## 输出规范

- 字数: 2000-3000字/章
- 对话比例: 30%左右
- 必须有章末钩子
```

- [ ] **Step 4: 创建审计官Profile**

```markdown
# 审计官 Agent Profile

## 基本信息

- **名称**: 审计官
- **角色**: 资深小说审核专家
- **专业领域**: 一致性检查、逻辑漏洞发现、质量评估

## 审核维度

| 维度 | 说明 |
|------|------|
| S1 | 剧情完整性 |
| S2 | 逻辑自洽 |
| S3 | 文笔风格 |
| S4 | 情感共鸣 |
| S5 | 节奏控制 |
| S6 | 可读性 |
| S7 | 主角魅力 |
| S8 | 人物弧光 |

## 专业工具

| 工具名 | 功能 |
|--------|------|
| check_character_consistency | 角色一致性 |
| check_item_consistency | 物品连续性 |
| check_timeline | 时间线合理性 |
| check_personality_consistency | 人设稳定性 |
| check_foreshadow_resolution | 伏笔回收 |
| check_outline_alignment | 大纲偏离度 |
| detect_ai_gloss | AI痕迹检测 |

## 输出规范

- 评分: 1-10分/维度
- 问题分级: P0(致命), P1(严重), P2(中等), P3(提示)
- 必须给出修改建议
```

- [ ] **Step 5: 创建润色师Profile**

```markdown
# 润色师 Agent Profile

## 基本信息

- **名称**: 润色师
- **角色**: 资深文字编辑
- **专业领域**: 文风统一、对话自然化、节奏优化、AI痕迹去除

## 专业工具

| 工具名 | 功能 |
|--------|------|
| extract_style_features | 提取文风特征 |
| apply_style_guide | 应用文风指南 |
| optimize_dialogue | 对话优化 |
| adjust_pacing | 节奏调整 |
| remove_ai_gloss | 去除AI痕迹 |

## 输出规范

- 保持原作意图
- 优化流畅度
- 自然对话
- 去除机械感
```

- [ ] **Step 6: 提交**

```bash
git add novel-factory/agent_system/agents/*/agent_profile.md
git commit -m "feat(agent): 添加5个Agent的Profile定义"
```

---

### Task 5: Agent工具函数

**Files:**
- Create: `novel-factory/agent_system/agents/outline_master/tools.py`
- Create: `novel-factory/agent_system/agents/character_designer/tools.py`
- Create: `novel-factory/agent_system/agents/content_writer/tools.py`
- Create: `novel-factory/agent_system/agents/auditor/tools.py`
- Create: `novel-factory/agent_system/agents/polisher/tools.py`
- Create: `tests/agent_system/test_agent_tools.py`

- [ ] **Step 1: 编写大纲师工具**

```python
# novel-factory/agent_system/agents/outline_master/tools.py
from typing import Dict, List, Optional, Any
from ..shared.outline_schema import OutlineSchema

class OutlineMasterTools:
    """大纲师工具集"""

    def __init__(self):
        self.schema = OutlineSchema()

    def generate_outline(self, settings: Dict, requirements: Dict) -> Dict:
        """
        生成完整大纲
        """
        outline = {
            "title": settings.get("title", "未命名作品"),
            "genre": settings.get("genre", "玄幻"),
            "total_chapters": requirements.get("total_chapters", 360),
            "chapters": self._generate_chapters(
                settings,
                requirements.get("total_chapters", 360)
            )
        }
        self.schema.validate(outline)
        return outline

    def generate_chapter_outline(self, chapter_num: int, events: List[str], foreshadow: Optional[List[str]] = None) -> Dict:
        """生成章大纲"""
        return {
            "num": chapter_num,
            "title": f"第{chapter_num}章",
            "events": events,
            "foreshadow": foreshadow or [],
            "word_count_target": 2500
        }

    def _generate_chapters(self, settings: Dict, total: int) -> List[Dict]:
        """生成章节列表（结构）"""
        chapters = []
        for i in range(1, total + 1):
            chapters.append({
                "num": i,
                "title": f"第{i}章",
                "events": [],
                "word_count_target": 2500
            })
        return chapters

    def save_outline(self, outline: Dict, file_path: str):
        """保存大纲"""
        self.schema.to_yaml(outline, file_path)

    def load_outline(self, file_path: str) -> Dict:
        """加载大纲"""
        return self.schema.from_yaml(file_path)
```

- [ ] **Step 2: 编写人设师工具**

```python
# novel-factory/agent_system/agents/character_designer/tools.py
from typing import Dict, List, Optional
from ..shared.character_schema import CharacterSchema

class CharacterDesignerTools:
    """人设师工具集"""

    def __init__(self):
        self.schema = CharacterSchema()

    def generate_character_card(self, requirements: Dict) -> Dict:
        """
        生成角色卡片
        """
        character = {
            "name": requirements["name"],
            "role": requirements.get("role", "supporting"),
            "personality": requirements.get("personality", []),
            "first_appearance": requirements.get("first_appearance", 1),
            "background": requirements.get("background", ""),
            "abilities": requirements.get("abilities", []),
            "voice_pattern": requirements.get("voice_pattern", ""),
            "relationships": [],
            "character_arc": {}
        }
        self.schema.validate(character)
        return character

    def add_relationship(self, character: Dict, target: str, relationship_type: str, trust: float = 0.5, conflict: float = 0.1) -> Dict:
        """添加关系"""
        if "relationships" not in character:
            character["relationships"] = []
        character["relationships"].append({
            "target": target,
            "type": relationship_type,
            "trust": trust,
            "conflict": conflict
        })
        return character

    def save_character(self, character: Dict, file_path: str):
        """保存角色"""
        self.schema.to_yaml(character, file_path)

    def load_character(self, file_path: str) -> Dict:
        """加载角色"""
        return self.schema.from_yaml(file_path)
```

- [ ] **Step 3: 编写正文写手工具**

```python
# novel-factory/agent_system/agents/content_writer/tools.py
from typing import Dict, List, Optional

class ContentWriterTools:
    """正文写手工具集"""

    def build_writing_prompt(self, context: Dict) -> str:
        """
        构建写作Prompt
        """
        outline = context.get("chapter_outline", {})
        characters = context.get("characters", [])
        style = context.get("style_guide", {})

        prompt_parts = [
            f"请撰写{outline.get('title', '第X章')}，字数目标：{outline.get('word_count_target', 2500)}字",
            "",
            "## 章节大纲",
            f"核心事件：{', '.join(outline.get('events', []))}",
            "",
            "## 角色设定",
        ]

        for char in characters:
            prompt_parts.append(f"- {char.get('name')}: {', '.join(char.get('personality', []))}")

        prompt_parts.extend([
            "",
            "## 文风要求",
            f"基调：{style.get('tone', '简洁有力')}",
            f"对话比例：{style.get('dialogue_ratio', '30%')}",
            "",
            "请开始创作："
        ])

        return "\n".join(prompt_parts)

    def add_chapter_hook(self, content: str, hook_type: str = "cliffhanger") -> str:
        """添加章末钩子"""
        hooks = {
            "cliffhanger": "就在这时，他突然听到了一个声音...",
            "question": "这一切究竟是怎么回事？",
            "revelation": "原来，真相竟然是这样...",
            "tension": "危险，正在逼近..."
        }
        return content + "\n\n" + hooks.get(hook_type, hooks["cliffhanger"])

    def adjust_word_count(self, content: str, target: int) -> str:
        """调整字数"""
        current = len(content)
        if abs(current - target) < 200:
            return content
        # 简化处理，实际应用中会更复杂
        return content
```

- [ ] **Step 4: 编写审计官工具**

```python
# novel-factory/agent_system/agents/auditor/tools.py
from typing import Dict, List, Tuple

class AuditorTools:
    """审计官工具集"""

    def check_character_consistency(self, content: str, character_cards: List[Dict]) -> List[Dict]:
        """检查角色一致性"""
        issues = []
        for card in character_cards:
            name = card.get("name")
            personality = card.get("personality", [])
            # 简化检测：检查是否有反性格词汇
            opposite_words = {
                "冷静": ["暴怒", "疯狂", "失控"],
                "热血": ["冷漠", "退缩"],
                "狡猾": ["单纯", "正直"]
            }
            for trait in personality:
                if trait in opposite_words:
                    for opp in opposite_words[trait]:
                        if opp in content and name in content:
                            issues.append({
                                "type": "character_consistency",
                                "severity": "P1",
                                "character": name,
                                "issue": f"性格为'{trait}'的角色出现'{opp}'行为",
                                "suggestion": f"请检查{ name}的行为是否与'{trait}'性格一致"
                            })
        return issues

    def check_timeline(self, content: str, timeline: List[Dict]) -> List[Dict]:
        """检查时间线"""
        issues = []
        # 简化检测
        return issues

    def detect_ai_gloss(self, content: str) -> List[Dict]:
        """检测AI痕迹"""
        issues = []
        ai_patterns = [
            ("首先", "过度格式化"),
            ("其次", "过度格式化"),
            ("然后", "机械过渡"),
            ("最后", "过度格式化"),
            ("总之", "过度总结"),
            ("可以看出", "过度总结")
        ]
        for pattern, issue_type in ai_patterns:
            if pattern in content:
                issues.append({
                    "type": "ai_gloss",
                    "severity": "P3",
                    "pattern": pattern,
                    "issue": issue_type,
                    "suggestion": "建议使用更自然的表达方式"
                })
        return issues

    def generate_audit_report(self, chapter_num: int, issues: List[Dict], scores: Dict[str, int]) -> Dict:
        """生成审核报告"""
        return {
            "chapter": chapter_num,
            "timestamp": "2026-05-19",
            "scores": scores,
            "issues": issues,
            "summary": self._summarize_issues(issues)
        }

    def _summarize_issues(self, issues: List[Dict]) -> str:
        """汇总问题"""
        by_severity = {}
        for issue in issues:
            sev = issue.get("severity", "P3")
            by_severity[sev] = by_severity.get(sev, 0) + 1
        return "; ".join([f"{k}: {v}个" for k, v in by_severity.items()])
```

- [ ] **Step 5: 编写润色师工具**

```python
# novel-factory/agent_system/agents/polisher/tools.py
from typing import Dict, List

class PolisherTools:
    """润色师工具集"""

    def optimize_dialogue(self, content: str) -> str:
        """优化对话"""
        # 简化处理
        return content

    def remove_ai_gloss(self, content: str) -> str:
        """去除AI痕迹"""
        replacements = [
            ("首先", ""),
            ("其次", ""),
            ("然后", ""),
            ("最后", ""),
            ("总之", ""),
            ("可以看出", "")
        ]
        result = content
        for old, new in replacements:
            result = result.replace(old, new)
        return result

    def adjust_pacing(self, content: str) -> str:
        """调整节奏"""
        # 简化处理
        return content

    def apply_style_guide(self, content: str, style_guide: Dict) -> str:
        """应用文风指南"""
        result = content
        if style_guide.get("remove_filler"):
            result = self._remove_filler(result)
        return result

    def _remove_filler(self, content: str) -> str:
        """去除冗余"""
        filler_phrases = ["值得注意的是", "需要指出的是", "实际上"]
        result = content
        for phrase in filler_phrases:
            result = result.replace(phrase, "")
        return result
```

- [ ] **Step 6: 提交**

```bash
git add novel-factory/agent_system/agents/*/tools.py
git commit -m "feat(agent): 实现5个Agent的工具函数"
```

---

### Task 6: 社交模拟引擎 - 关系追踪器

**Files:**
- Create: `novel-factory/agent_system/social_engine/relationship_tracker.py`
- Create: `novel-factory/agent_system/social_engine/rules/event_effects.yaml`
- Create: `tests/agent_system/test_relationship_tracker.py`

- [ ] **Step 1: 编写测试**

```python
# tests/agent_system/test_relationship_tracker.py
import pytest
import tempfile
import os
from agent_system.social_engine.relationship_tracker import RelationshipTracker

def test_relationship_tracker_init():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "relationships.json")
        tracker = RelationshipTracker(state_file)
        network = tracker.get_network()
        assert "characters" in network
        assert "relationships" in network

def test_add_character():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "relationships.json")
        tracker = RelationshipTracker(state_file)
        tracker.add_character("铁蛋", role="protagonist")
        network = tracker.get_network()
        assert "铁蛋" in network["characters"]

def test_add_relationship():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "relationships.json")
        tracker = RelationshipTracker(state_file)
        tracker.add_character("铁蛋")
        tracker.add_character("林夜")
        tracker.add_relationship("铁蛋", "林夜", "ally", trust=0.7)
        rel = tracker.get_relationship("铁蛋", "林夜")
        assert rel["trust"] == 0.7

def test_update_trust():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "relationships.json")
        tracker = RelationshipTracker(state_file)
        tracker.add_character("铁蛋")
        tracker.add_character("林夜")
        tracker.add_relationship("铁蛋", "林夜", "ally", trust=0.5)
        tracker.update_trust("铁蛋", "林夜", 0.3)
        rel = tracker.get_relationship("铁蛋", "林夜")
        assert rel["trust"] == 0.8
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/agent_system/test_relationship_tracker.py -v
# 预期: FAIL
```

- [ ] **Step 3: 实现 RelationshipTracker**

```python
# novel-factory/agent_system/social_engine/relationship_tracker.py
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

class RelationshipTracker:
    """关系追踪器"""

    def __init__(self, state_file: str = "novel-factory/agent_system/social_engine/relationship_network.json"):
        self.state_file = state_file
        self._ensure_initial_state()

    def _ensure_initial_state(self):
        Path(self.state_file).parent.mkdir(parents=True, exist_ok=True)
        if not Path(self.state_file).exists():
            self._save_network({"characters": [], "relationships": [], "events": []})

    def _load_network(self) -> Dict:
        with open(self.state_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_network(self, network: Dict):
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(network, f, ensure_ascii=False, indent=2)

    def get_network(self) -> Dict:
        return self._load_network()

    def add_character(self, name: str, role: str = "supporting"):
        network = self._load_network()
        if name not in network["characters"]:
            network["characters"].append({"name": name, "role": role})
            self._save_network(network)

    def add_relationship(self, from_char: str, to_char: str, rel_type: str, trust: float = 0.5, conflict: float = 0.1):
        network = self._load_network()
        # 检查是否已存在关系
        existing = self.get_relationship(from_char, to_char)
        if existing:
            return

        network["relationships"].append({
            "from": from_char,
            "to": to_char,
            "type": rel_type,
            "trust": trust,
            "conflict": conflict,
            "last_event": None
        })
        self._save_network(network)

    def get_relationship(self, from_char: str, to_char: str) -> Optional[Dict]:
        network = self._load_network()
        for rel in network["relationships"]:
            if rel["from"] == from_char and rel["to"] == to_char:
                return rel
            if rel["from"] == to_char and rel["to"] == from_char and rel["type"] in ["ally", "family", "romantic"]:
                return rel
        return None

    def update_trust(self, from_char: str, to_char: str, delta: float):
        network = self._load_network()
        for rel in network["relationships"]:
            if rel["from"] == from_char and rel["to"] == to_char:
                rel["trust"] = max(0, min(1, rel["trust"] + delta))
                self._save_network(network)
                return

    def update_conflict(self, from_char: str, to_char: str, delta: float):
        network = self._load_network()
        for rel in network["relationships"]:
            if rel["from"] == from_char and rel["to"] == to_char:
                rel["conflict"] = max(0, min(1, rel["conflict"] + delta))
                self._save_network(network)
                return

    def record_event(self, from_char: str, to_char: str, event_type: str, chapter: int):
        network = self._load_network()
        network["events"].append({
            "from": from_char,
            "to": to_char,
            "type": event_type,
            "chapter": chapter
        })
        for rel in network["relationships"]:
            if rel["from"] == from_char and rel["to"] == to_char:
                rel["last_event"] = f"ch{chapter}"
        self._save_network(network)
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/agent_system/test_relationship_tracker.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add novel-factory/agent_system/social_engine/relationship_tracker.py novel-factory/agent_system/social_engine/rules/event_effects.yaml tests/agent_system/test_relationship_tracker.py
git commit -m "feat(agent): 实现关系追踪器"
```

---

### Task 7: 事件效果计算器

**Files:**
- Create: `novel-factory/agent_system/social_engine/event_effect_calculator.py`
- Create: `tests/agent_system/test_event_effect_calculator.py`

- [ ] **Step 1: 编写测试**

```python
# tests/agent_system/test_event_effect_calculator.py
import pytest
import tempfile
import os
from agent_system.social_engine.event_effect_calculator import EventEffectCalculator

def test_event_effect_calculator_init():
    with tempfile.TemporaryDirectory() as tmpdir:
        rules_file = os.path.join(tmpdir, "event_effects.yaml")
        calc = EventEffectCalculator(rules_file)
        assert calc is not None

def test_calculate_effects():
    with tempfile.TemporaryDirectory() as tmpdir:
        rules_file = os.path.join(tmpdir, "event_effects.yaml")
        calc = EventEffectCalculator(rules_file)
        # 使用默认规则
        result = calc.calculate_effects("save_life")
        assert "trust_delta" in result
        assert result["trust_delta"] > 0
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/agent_system/test_event_effect_calculator.py -v
# 预期: FAIL
```

- [ ] **Step 3: 实现 EventEffectCalculator**

```python
# novel-factory/agent_system/social_engine/event_effect_calculator.py
from typing import Dict, List, Optional, Any
import yaml
from pathlib import Path

class EventEffectCalculator:
    """事件效果计算器"""

    DEFAULT_RULES = {
        "save_life": {"trust_delta": 0.3, "conflict_delta": -0.2},
        "betrayal": {"trust_delta": -0.4, "conflict_delta": 0.3},
        "physical_conflict": {"trust_delta": -0.1, "conflict_delta": 0.3},
        "verbal_argument": {"trust_delta": -0.05, "conflict_delta": 0.2},
        "share_secret": {"trust_delta": 0.2, "conflict_delta": -0.1, "intimate_only": True},
        "gift_given": {"trust_delta": 0.1, "conflict_delta": 0},
        "promise_made": {"trust_delta": 0.15, "conflict_delta": 0},
        "promise_broken": {"trust_delta": -0.25, "conflict_delta": 0.15}
    }

    def __init__(self, rules_file: Optional[str] = None):
        self.rules_file = rules_file
        self._rules = self._load_rules()

    def _load_rules(self) -> Dict:
        if self.rules_file and Path(self.rules_file).exists():
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f).get("event_effects", self.DEFAULT_RULES)
        return self.DEFAULT_RULES

    def calculate_effects(self, event_type: str) -> Dict[str, Any]:
        """计算事件效果"""
        return self._rules.get(event_type, {"trust_delta": 0, "conflict_delta": 0})

    def apply_event(self, event_type: str, from_char: str, to_char: str, tracker) -> Dict:
        """应用事件到关系追踪器"""
        effects = self.calculate_effects(event_type)

        if effects.get("trust_delta"):
            tracker.update_trust(from_char, to_char, effects["trust_delta"])
        if effects.get("conflict_delta"):
            tracker.update_conflict(from_char, to_char, effects["conflict_delta"])

        return effects
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/agent_system/test_event_effect_calculator.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add novel-factory/agent_system/social_engine/event_effect_calculator.py tests/agent_system/test_event_effect_calculator.py
git commit -m "feat(agent): 实现事件效果计算器"
```

---

### Task 8: 冲突预警与写作建议

**Files:**
- Create: `novel-factory/agent_system/social_engine/conflict_alert.py`
- Create: `novel-factory/agent_system/social_engine/writing_suggestion.py`
- Create: `novel-factory/agent_system/social_engine/rules/emergence.yaml`
- Create: `tests/agent_system/test_conflict_alert.py`

- [ ] **Step 1: 编写测试**

```python
# tests/agent_system/test_conflict_alert.py
import pytest
import tempfile
import os
from agent_system.social_engine.conflict_alert import ConflictAlert

def test_conflict_alert_init():
    with tempfile.TemporaryDirectory() as tmpdir:
        rules_file = os.path.join(tmpdir, "emergence.yaml")
        alert = ConflictAlert(rules_file)
        assert alert is not None
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/agent_system/test_conflict_alert.py -v
# 预期: FAIL
```

- [ ] **Step 3: 实现 ConflictAlert**

```python
# novel-factory/agent_system/social_engine/conflict_alert.py
from typing import Dict, List, Optional, Any
import yaml
from pathlib import Path

class ConflictAlert:
    """冲突预警"""

    DEFAULT_CONFIG = {
        "trust_sudden_change": {"threshold": 0.3, "alert": True},
        "conflict_outbreak": {"threshold": 0.7, "alert": True},
        "relationship_reversal": {"alert": True},
        "isolated_character": {"threshold": 3}
    }

    def __init__(self, rules_file: Optional[str] = None):
        self.rules_file = rules_file
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        if self.rules_file and Path(self.rules_file).exists():
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f).get("emergence_detection", self.DEFAULT_CONFIG)
        return self.DEFAULT_CONFIG

    def check_alerts(self, relationship_tracker, chapter: int) -> List[Dict]:
        """检查所有预警"""
        alerts = []
        network = relationship_tracker.get_network()

        for rel in network.get("relationships", []):
            # 冲突爆发检测
            if rel.get("conflict", 0) >= self.config["conflict_outbreak"]["threshold"]:
                alerts.append({
                    "type": "conflict_outbreak",
                    "from": rel["from"],
                    "to": rel["to"],
                    "conflict": rel["conflict"],
                    "suggestion": self.config["conflict_outbreak"].get("suggestion", "")
                })

            # 孤立角色检测
            for char in network.get("characters", []):
                char_name = char["name"]
                recent_events = [e for e in network.get("events", []) if e.get("from") == char_name and isinstance(e.get("chapter"), int) and chapter - e.get("chapter", 0) <= 3]
                if len(recent_events) == 0 and chapter > 10:
                    alerts.append({
                        "type": "isolated_character",
                        "character": char_name,
                        "suggestion": self.config["isolated_character"].get("suggestion", "")
                    })

        return alerts
```

- [ ] **Step 4: 实现 WritingSuggestion**

```python
# novel-factory/agent_system/social_engine/writing_suggestion.py
from typing import Dict, List, Optional

class WritingSuggestion:
    """写作建议生成器"""

    def generate_suggestions(self, relationship_tracker, chapter: int) -> List[str]:
        """生成写作建议"""
        suggestions = []
        network = relationship_tracker.get_network()

        for rel in network.get("relationships", []):
            # 高冲突关系建议
            if rel.get("conflict", 0) >= 0.6:
                suggestions.append(
                    f"【关系提示】{rel['from']}和{rel['to']}之间冲突即将爆发，考虑加入一场对峙场景"
                )

            # 高信任关系建议
            if rel.get("trust", 0) >= 0.7 and rel.get("type") == "ally":
                suggestions.append(
                    f"【关系深化】{rel['from']}和{rel['to']}信任度很高，可以考虑分享秘密或承诺"
                )

            # 长时间无互动
            if rel.get("last_event"):
                last_ch = int(rel["last_event"].replace("ch", ""))
                if chapter - last_ch >= 5:
                    suggestions.append(
                        f"【关系维护】{rel['from']}和{rel['to']}已{chapter - last_ch}章无互动，建议安排场景"
                    )

        return suggestions

    def suggest_dialogue(self, character1: str, character2: str, relationship: Dict) -> str:
        """生成对话建议"""
        conflict = relationship.get("conflict", 0)
        trust = relationship.get("trust", 0)

        if conflict >= 0.5:
            return f"{character1}和{character2}之间的对话应该充满火药味，可以有争执和反驳"
        elif trust >= 0.7:
            return f"{character1}和{character2}之间可以深入交流，分享内心想法"
        else:
            return f"{character1}和{character2}的对话应该保持一定距离感"
```

- [ ] **Step 5: 运行测试验证**

```bash
pytest tests/agent_system/test_conflict_alert.py -v
# 预期: PASS
```

- [ ] **Step 6: 提交**

```bash
git add novel-factory/agent_system/social_engine/conflict_alert.py novel-factory/agent_system/social_engine/writing_suggestion.py novel-factory/agent_system/social_engine/rules/emergence.yaml tests/agent_system/test_conflict_alert.py
git commit -m "feat(agent): 实现冲突预警和写作建议"
```

---

### Task 9: 主控调度器

**Files:**
- Create: `novel-factory/agent_system/master_controller.py`
- Create: `tests/agent_system/test_master_controller.py`

- [ ] **Step 1: 编写测试**

```python
# tests/agent_system/test_master_controller.py
import pytest
from unittest.mock import Mock, patch

def test_master_controller_init():
    with patch('agent_system.master_controller.RelationshipTracker'):
        with patch('agent_system.master_controller.ContextBuilder'):
            from agent_system.master_controller import MasterController
            controller = MasterController()
            assert controller is not None
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/agent_system/test_master_controller.py -v
# 预期: FAIL
```

- [ ] **Step 3: 实现 MasterController**

```python
# novel-factory/agent_system/master_controller.py
from typing import Dict, List, Optional, Any
from .agents.outline_master.tools import OutlineMasterTools
from .agents.character_designer.tools import CharacterDesignerTools
from .agents.content_writer.tools import ContentWriterTools
from .agents.auditor.tools import AuditorTools
from .agents.polisher.tools import PolisherTools
from .social_engine.relationship_tracker import RelationshipTracker
from .social_engine.event_effect_calculator import EventEffectCalculator
from .social_engine.conflict_alert import ConflictAlert
from .social_engine.writing_suggestion import WritingSuggestion
from .shared.context_builder import ContextBuilder

class MasterController:
    """主控调度器"""

    def __init__(self, state_dir: str = "novel-factory/agent_system"):
        self.outline_master = OutlineMasterTools()
        self.character_designer = CharacterDesignerTools()
        self.content_writer = ContentWriterTools()
        self.auditor = AuditorTools()
        self.polisher = PolisherTools()

        self.relationship_tracker = RelationshipTracker(f"{state_dir}/social_engine/relationship_network.json")
        self.event_calculator = EventEffectCalculator()
        self.conflict_alert = ConflictAlert()
        self.writing_suggestion = WritingSuggestion()
        self.context_builder = ContextBuilder()

    def generate_outline(self, settings: Dict, requirements: Dict) -> Dict:
        """生成大纲"""
        return self.outline_master.generate_outline(settings, requirements)

    def generate_characters(self, outline: Dict, character_requirements: List[Dict]) -> List[Dict]:
        """生成角色卡片"""
        characters = []
        for req in character_requirements:
            card = self.character_designer.generate_character_card(req)
            characters.append(card)
        return characters

    def write_chapter(
        self,
        chapter_num: int,
        outline: Dict,
        characters: List[Dict],
        memory_context: Dict,
        style_guide: Dict
    ) -> Dict:
        """写章节流程"""
        # 获取章节大纲
        chapter_outline = self.outline_master.schema.get_chapter_outline(outline, chapter_num)

        # 构建上下文
        context = self.context_builder.build_writing_context(
            chapter_outline=chapter_outline,
            characters=characters,
            memory_context=memory_context,
            relationship_network=self.relationship_tracker.get_network(),
            style_guide=style_guide
        )

        # 获取写作建议
        suggestions = self.writing_suggestion.generate_suggestions(
            self.relationship_tracker, chapter_num
        )

        # 构建Prompt
        prompt = self.content_writer.build_writing_prompt(context)

        # 这里应该调用AI服务生成章节
        # 简化处理：返回prompt供后续使用
        return {
            "prompt": prompt,
            "suggestions": suggestions,
            "context": context
        }

    def audit_chapter(self, chapter_num: int, content: str, characters: List[Dict], timeline: List[Dict]) -> Dict:
        """审核章节"""
        # 角色一致性检查
        char_issues = self.auditor.check_character_consistency(content, characters)

        # AI痕迹检测
        ai_issues = self.auditor.detect_ai_gloss(content)

        # 生成报告
        all_issues = char_issues + ai_issues
        return self.auditor.generate_audit_report(chapter_num, all_issues, scores={})

    def polish_chapter(self, content: str) -> str:
        """润色章节"""
        result = self.polisher.remove_ai_gloss(content)
        result = self.polisher.optimize_dialogue(result)
        return result
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/agent_system/test_master_controller.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add novel-factory/agent_system/master_controller.py tests/agent_system/test_master_controller.py
git commit -m "feat(agent): 实现主控调度器"
```

---

## 自检清单

- [ ] 所有文件路径是否存在且正确
- [ ] 所有类和方法是否有对应测试
- [ ] 5个Agent的Profile是否完整
- [ ] 社交模拟引擎是否支持事件效果计算
- [ ] 主控调度器是否能编排完整流程
- [ ] 提交消息是否符合规范 (feat: ...)

---

## 执行选项

**Plan complete and saved to `docs/superpowers/plans/2026-05-19-agent-system-implementation-plan.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
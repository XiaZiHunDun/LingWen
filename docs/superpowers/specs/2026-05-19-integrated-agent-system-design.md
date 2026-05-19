# SPEC: 整合Agent协作系统

> **版本**: v1.0
> **日期**: 2026-05-19
> **状态**: 已整合（原4个方案合并）
> **优先级**: P1
> **预计工作量**: 10-12周

---

## 1. 概述与目标

### 1.1 问题陈述

当前小说工厂在"Agent协作"方面的处理方式存在以下问题：

| 问题 | 说明 |
|------|------|
| 角色切换效率低 | 单会话内多角色切换，prompt污染严重 |
| 一致性难保证 | 大纲师/人设师/写手/审计官之间信息共享不畅 |
| 缺乏关系网络 | 角色之间的社交关系、信任/冲突值无动态追踪 |
| 事件驱动缺失 | 情节事件发生时无法自动计算对关系网络的影响 |

### 1.2 解决方案

构建**整合Agent协作系统**，统一以下原有方案：
- ~~多Agent协作分工~~（架构层面）
- ~~多智能体社交模拟~~（功能层面）
- ~~关系图谱可视化~~（子功能）

**核心思路**：
- 专项Agent化：每个Agent有独立的专业Prompt和工具集
- 文件共享协作：Agent间通过标准化文件格式共享数据
- 关系网络驱动：社交模拟引擎为写作提供关系驱动的建议

### 1.3 目标

| 目标 | 指标 |
|------|------|
| Agent切换效率 | 专项Agent调用 < 30秒（含工具加载） |
| 协作一致性 | 多Agent输出冲突率 < 5% |
| 关系预警准确率 | ≥ 80%的预警被后续审核确认 |
| 写作建议相关度 | ≥ 75%被作家采纳 |

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    主控调度层（Master Controller）               │
│  • 负责任务编排，不参与具体创作                                  │
│  • 通过 workflow_state.json 协调各专项Agent                     │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   专项Agent   │    │   专项Agent   │    │   专项Agent   │
│   大纲师      │    │   人设师      │    │   正文写手    │
│               │    │               │    │               │
│ • 大纲生成    │    │ • 角色卡片    │    │ • 正文撰写    │
│ • 节奏控制    │    │ • 关系网络    │    │ • 上下文注入  │
│ • 伏笔布局    │    │ • 弧光设计    │    │ • 文风一致    │
└───────┬───────┘    └───────┬───────┘    └───────┬───────┘
        │                    │                    │
        └─────────────────────┼────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    共享数据层（Shared Data）                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ 大纲文件    │  │ 角色卡片    │  │ 写作上下文  │              │
│  │ *.大纲.md   │  │ *.角色.yaml │  │ context.json│              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    社交模拟引擎（Social Simulation）            │
│  • 关系网络追踪（信任/冲突/亲密度）                               │
│  • 事件效果计算                                                 │
│  • 冲突预警                                                    │
│  • 写作建议生成                                                │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 目录结构

```
novel-factory/
├── agent_system/
│   ├── __init__.py
│   ├── master_controller.py           # 主控调度器
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── outline_master/            # 大纲师
│   │   │   ├── agent_profile.md
│   │   │   ├── tools.py
│   │   │   └── memory.md
│   │   ├── character_designer/        # 人设师
│   │   │   ├── agent_profile.md
│   │   │   ├── tools.py
│   │   │   └── memory.md
│   │   ├── content_writer/            # 正文写手
│   │   │   ├── agent_profile.md
│   │   │   ├── tools.py
│   │   │   └── memory.md
│   │   ├── auditor/                  # 审计官
│   │   │   ├── agent_profile.md
│   │   │   ├── tools.py
│   │   │   └── memory.md
│   │   └── polisher/                  # 润色师
│   │       ├── agent_profile.md
│   │       ├── tools.py
│   │       └── memory.md
│   ├── social_engine/
│   │   ├── __init__.py
│   │   ├── relationship_tracker.py    # 关系追踪器
│   │   ├── event_effect_calculator.py # 事件效果计算
│   │   ├── conflict_alert.py         # 冲突预警
│   │   ├── writing_suggestion.py      # 写作建议
│   │   └── rules/
│   │       ├── event_effects.yaml    # 事件效果规则
│   │       └── emergence.yaml         # 涌现检测规则
│   └── shared/
│       ├── __init__.py
│       ├── outline_schema.py         # 大纲Schema
│       ├── character_schema.py       # 角色Schema
│       └── context_builder.py         # 上下文构建器
└── config/
    └── agent_config.yaml             # Agent配置
```

---

## 3. 核心组件

### 3.1 大纲师（Outline Master）

```yaml
agent_profile:
  name: 大纲师
  role: 资深网文大纲设计师
  specialty:
    - 长篇小说结构设计
    - 三幕节奏控制
    - 伏笔埋设布局
    - 爽点密度规划

  tools:
    - generate_outline()        # 生成大纲
    - generate_volume_outline()  # 生成卷大纲
    - generate_chapter_outline() # 生成章大纲
    - check_outline_consistency() # 一致性检查
    - layout_foreshadow()       # 伏笔布局

  output_format:
    - 文件命名: {类型}_v{版本}.md
    - 包含: 章节标题、核心事件、字数目标、伏笔标记
```

### 3.2 人设师（Character Designer）

```yaml
agent_profile:
  name: 人设师
  role: 资深角色设计师
  specialty:
    - 人物设定与关系网络
    - 角色弧光设计
    - 行为一致性保障

  tools:
    - generate_character_card()  # 生成角色卡片
    - update_relationship()      # 更新关系
    - design_character_arc()      # 设计弧光
    - check_behavior_consistency() # 行为一致性检查

  output_format:
    - 文件命名: {角色名}.角色.yaml
    - 包含: 基础信息、性格、背景、能力、关系、弧光
```

### 3.3 正文写手（Content Writer）

```yaml
agent_profile:
  name: 正文写手
  role: 专业网文作家
  specialty:
    - 长篇小说章节创作
    - 多场景切换
    - 角色对话个性化
    - 节奏把控

  tools:
    - build_writing_prompt()    # 构建写作Prompt
    - generate_chapter()         # 生成章节
    - adjust_word_count()        # 字数调整
    - add_chapter_hook()         # 添加章末钩子

  context_inputs:
    - chapter_outline
    - character_cards
    - memory_context
    - style_guide
```

### 3.4 审计官（Auditor）

```yaml
agent_profile:
  name: 审计官
  role: 资深小说审核专家
  specialty:
    - 一致性检查
    - 逻辑漏洞发现
    - 质量评估

  audit_dimensions:
    S1: 剧情完整性
    S2: 逻辑自洽
    S3: 文笔风格
    S4: 情感共鸣
    S5: 节奏控制
    S6: 可读性
    S7: 主角魅力
    S8: 人物弧光

  tools:
    - check_character_consistency()  # 角色一致性
    - check_item_consistency()       # 物品连续性
    - check_timeline()               # 时间线合理性
    - check_personality_consistency() # 人设稳定性
    - check_foreshadow_resolution()  # 伏笔回收
    - check_outline_alignment()      # 大纲偏离度
    - detect_ai_gloss()              # AI痕迹检测
```

### 3.5 润色师（Polisher）

```yaml
agent_profile:
  name: 润色师
  role: 资深文字编辑
  specialty:
    - 文风统一
    - 对话自然化
    - 节奏优化
    - AI痕迹去除

  tools:
    - extract_style_features()   # 提取文风特征
    - apply_style_guide()         # 应用文风指南
    - optimize_dialogue()         # 对话优化
    - adjust_pacing()            # 节奏调整
    - remove_ai_gloss()          # 去除AI痕迹
```

---

## 4. 社交模拟引擎

### 4.1 关系网络

```yaml
relationship_network:
  characters:
    - name: "林夜"
      role: "protagonist"
    - name: "苏琳"
      role: "supporting"
    - name: "莫言"
      role: "antagonist"

  relationships:
    - from: "林夜"
      to: "苏琳"
      trust: 0.7        # 0-1
      conflict: 0.1     # 0-1
      type: "ally"      # ally / adversary / family / romantic / neutral
      last_event: "ch010"
```

### 4.2 事件效果规则

```yaml
event_effects:
  "save_life":
    trust_delta: +0.3
    conflict_delta: -0.2

  "betrayal":
    trust_delta: -0.4
    conflict_delta: +0.3

  "physical_conflict":
    trust_delta: -0.1
    conflict_delta: +0.3

  "share_secret":
    trust_delta: +0.2
    conflict_delta: -0.1
    intimate_only: true
```

### 4.3 涌现检测

```yaml
emergence_detection:
  trust_sudden_change:
    threshold: 0.3  # 单章内变化超过0.3
    alert: true

  conflict_outbreak:
    threshold: 0.7  # 冲突潜力超过0.7
    alert: true
    suggestion: "考虑加入冲突场景"

  relationship_reversal:
    alert: true
    suggestion: "关系逆转，可作为情节转折点"

  isolated_character:
    threshold: 3  # 连续3章无任何关系事件
    suggestion: "角色可能需要互动机会"
```

---

## 5. Agent间协作流程

### 5.1 大纲 → 正文流程

```
1. 主控调用大纲师
   → 大纲师生成全文大纲 / 卷大纲

2. 主控调用人设师
   → 人设师基于大纲生成角色卡片

3. 主控调用社交模拟引擎
   → 初始化关系网络

4. 主控调用正文写手
   → 写手获取：大纲 + 角色卡片 + 记忆上下文
   → 生成章节草稿

5. 主控调用审计官
   → 审计官检查：一致性 + 质量
   → 通过 → 润色师
   → 不通过 → 打回写手

6. 主控调用润色师
   → 润色师统一文风
   → 输出定稿
```

### 5.2 上下文传递机制

```python
class ContextBuilder:
    """上下文构建器 - 各Agent的数据共享标准"""

    def build_writing_context(
        self,
        chapter_outline: dict,
        characters: List[dict],
        memory_context: dict,
        relationship_network: dict
    ) -> dict:
        """
        构建写作上下文
        """
        return {
            "chapter_outline": chapter_outline,
            "characters": characters,
            "character_states": self._get_current_states(characters),
            "relationship_network": relationship_network,
            "active_foreshadow": self._get_active_foreshadow(),
            "recent_events": memory_context.get_recent_events(),
            "style_guide": self._get_style_guide()
        }
```

---

## 6. 与记忆系统的集成

```
Agent协作系统 ←→ 记忆系统

1. 正文写手请求上下文：
   → MemoryGateway.auto_push_context(chapter_num)
   → 返回角色状态 + 伏笔摘要 + 相关历史

2. 社交模拟引擎更新关系：
   → 章节完成后调用 MemoryGateway.update_relationship()
   → 更新信任/冲突值

3. 审计官查询一致性：
   → 调用 MemoryGateway.check_consistency()
   → 检测与前文冲突
```

---

## 7. 实施计划

### 阶段1（3周）：核心Agent

| 任务 | 负责人 | 交付物 | 验收标准 |
|------|--------|--------|---------|
| 创建大纲师Agent | 技术 | agent_profile + tools | 大纲生成正常 |
| 创建人设师Agent | 技术 | agent_profile + tools | 角色卡片生成正常 |
| 创建正文写手Agent | 技术 | agent_profile + tools | 章节生成正常 |
| 创建审计官Agent | 技术 | agent_profile + tools | 一致性检查正常 |
| 创建润色师Agent | 技术 | agent_profile + tools | 文风统一正常 |
| 实现上下文构建器 | 技术 | context_builder.py | 数据共享正常 |

### 阶段2（3-4周）：社交模拟引擎

| 任务 | 负责人 | 交付物 | 验收标准 |
|------|--------|--------|---------|
| 实现关系追踪器 | 技术 | relationship_tracker.py | 关系更新正常 |
| 实现事件效果计算 | 技术 | event_effect_calculator.py | 效果计算正常 |
| 实现冲突预警 | 技术 | conflict_alert.py | 预警触发正常 |
| 实现写作建议 | 技术 | writing_suggestion.py | 建议相关度高 |
| 配置事件效果规则 | 主编 | event_effects.yaml | 规则完整 |

### 阶段3（2-3周）：主控集成

| 任务 | 负责人 | 交付物 | 验收标准 |
|------|--------|--------|---------|
| 实现主控调度器 | 技术 | master_controller.py | 任务编排正常 |
| 与workflow_state集成 | 技术 | 集成代码 | 状态同步正常 |
| 与记忆系统集成 | 技术 | 集成代码 | 上下文获取正常 |
| 端到端测试 | 主编 | 测试报告 | 完整流程正常 |

---

## 8. 验收标准

### 8.1 功能验收

| 功能 | 验收标准 | 测试方法 |
|------|---------|---------|
| 大纲生成 | 大纲师可生成完整大纲 | 调用测试 |
| 角色卡片生成 | 人设师可生成角色卡片 | 调用测试 |
| 章节生成 | 写手可生成章节草稿 | 调用测试 |
| 审计 | 审计官可检查一致性 | 调用测试 |
| 润色 | 润色师可统一文风 | 调用测试 |
| 关系追踪 | 社交引擎可更新关系 | 调用测试 |
| 冲突预警 | 超阈值时正确预警 | 触发测试 |
| 写作建议 | 基于关系生成建议 | 质量评估 |

### 8.2 协作验收

| 指标 | 验收标准 |
|------|---------|
| Agent切换时间 | < 30秒 |
| 多Agent输出冲突率 | < 5% |
| 关系预警准确率 | ≥ 80% |
| 写作建议采纳率 | ≥ 75% |

---

## 9. 归档的原始文档

以下文档已整合到本设计，原文档归档至 `../deprecated/`：

| 原文档 | 整合内容 |
|--------|---------|
| `2026-05-19-multi-agent-collaboration.md` | Agent架构 + 分工 |
| `2026-05-19-multi-agent-social-simulation-design.md` | 社交模拟引擎 |
| `2026-05-19-relationship-graph.md` | 关系图谱 |
| `2026-05-19-关系图谱可视化.md` | 可视化（子功能） |

---

## 10. 关键设计决策

| 决策 | 说明 |
|------|------|
| 专项Agent而非单一Agent | 分离专业能力，提高输出质量 |
| 文件共享而非内存共享 | 通过标准化文件传递数据，简单可靠 |
| 规则引擎驱动社交模拟 | 不用复杂的多智能体模拟，用查表规则 |
| 主控负责任务编排 | 主控不参与具体创作，只协调 |
| 写作建议基于关系状态 | 为作家提供关系驱动的对话/冲突建议 |
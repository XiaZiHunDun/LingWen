# SPEC: 整合提示词体系

> **版本**: v1.0
> **日期**: 2026-05-19
> **状态**: 已整合（原3个方案合并）
> **优先级**: P1
> **预计工作量**: 8-10周

---

## 1. 概述与目标

### 1.1 问题陈述

当前小说工厂的提示词分散在各个方法论文档中，存在以下问题：

| 问题 | 说明 |
|------|------|
| 提示词复用率低 | 同一类型的提示词在各文档重复编写 |
| 生成质量不稳定 | 缺乏标准化模板，输出质量波动大 |
| 版本管理缺失 | 提示词变更无法追踪，无法回滚 |
| 温度参数随意 | 不同场景使用相同温度，效果不优 |
| 文风不统一 | 各阶段提示词风格不一致 |

### 1.2 解决方案

构建**整合提示词体系**，统一以下原有方案：
- ~~CARE提示词框架~~（组织结构）
- ~~提示词模板库~~（模板集合）
- ~~温度参数指导~~（参数配置）

**核心：CARE框架**（Context-Action-Result-Example）

### 1.3 目标

| 目标 | 指标 |
|------|------|
| 提示词复用率 | 同一模板被≥3个项目使用 |
| S3文笔评分 | 批次均分从baseline提升至≥3.5 |
| 新项目初始化时间 | 提示词准备时间减少50% |
| 提示词版本可控 | 支持版本历史和回滚 |

---

## 2. 架构设计

### 2.1 目录结构

```
novel-factory/
├── 10_方法论/
│   └── PART3_工具集/
│       └── 提示词模板库/
│           ├── README.md
│           ├── 00_模板索引.yaml
│           ├── 01_大纲生成/
│           │   ├── 全文大纲_CARE.md
│           │   ├── 卷大纲_CARE.md
│           │   ├── 阶段大纲_CARE.md
│           │   └── 场景大纲_CARE.md
│           ├── 02_正文续写/
│           │   ├── 标准续写_CARE.md
│           │   ├── 高潮场景_CARE.md
│           │   └── 对话场景_CARE.md
│           ├── 03_描写增强/
│           │   ├── 五感描写_CARE.md
│           │   ├── 隐喻描写_CARE.md
│           │   └── 场景描写_CARE.md
│           ├── 04_审核辅助/
│           │   ├── 逻辑检查_CARE.md
│           │   ├── 节奏评估_CARE.md
│           │   └── 角色一致性_CARE.md
│           └── 05_润色修改/
│               ├── 语言润色_CARE.md
│               ├── 情感强化_CARE.md
│               └── 节奏调整_CARE.md
└── config/
    └── prompts/
        ├── 模型默认参数.yaml
        ├── 场景温度映射.yaml      # 新增：场景-温度映射
        ├── 风格指南库/
        │   ├── 玄幻风格.yaml
        │   ├── 都市风格.yaml
        │   └── 古言风格.yaml
        └── 示例库/
            ├── 玄幻示例.yaml
            └── 都市示例.yaml
```

---

## 3. CARE框架

### 3.1 四要素定义

```yaml
CARE框架:
  C - Context（背景）:
    包含:
      - 世界观摘要（核心规则、力量体系、主要势力）
      - 项目基本信息（类型、核心冲突、目标读者）
      - 已锁定的关键里程碑
      - 参考作品风格（可选）

  A - Action（行动）:
    包含:
      - 输出类型（outline/prose/dialogue/analysis）
      - 约束条件（字数、格式）
      - 必须推进的元素
      - 禁止出现的元素

  R - Result（结果）:
    包含:
      - 质量指标（S1-S8对应要求）
      - 字数要求（最少/目标/最多）
      - 检查清单

  E - Example（示例）:
    包含:
      - 高质量示例（带注释）
      - 角色声音对照
      - 风格对照检查
```

### 3.2 模板元数据Schema

```yaml
TemplateMetadata:
  id: string                    # 格式：{category}_{name}_v{version}
  name: string
  category: enum                # outline|continuation|description|review|polish
  version: string               # 语义化版本
  status: enum                  # draft|active|deprecated

  care_elements:
    context:
      required_fields: [world_setting, character_status, scene_location]
      optional_fields: [previous_summary, foreshadowing]
    action:
      output_type: enum
      constraints:
        min_words: int
        max_words: int
        format: enum
    result:
      quality_metrics: [S1 >= 3, S2 >= 3, ...]
      style_guide_ref: string
    example:
      example_type: enum        # annotated|raw|contrast
      location: string

  usage_stats:
    use_count: int
    success_rate: float
    avg_score: float
    last_used: datetime
```

---

## 4. 场景温度映射

### 4.1 场景分类

```yaml
scenes:
  outline_generation:
    description: "大纲生成"
    temperature_range: [0.5, 0.7]
    recommended: 0.6
    top_p: 0.9
    max_tokens: 2000

  content_continuation:
    description: "正文续写"
    temperature_range: [0.6, 0.8]
    recommended: 0.7
    top_p: 0.9
    max_tokens: 4000

  high_stakes_scene:
    description: "高潮场景"
    temperature_range: [0.65, 0.75]
    recommended: 0.7
    top_p: 0.9
    max_tokens: 4000

  dialogue_scene:
    description: "对话场景"
    temperature_range: [0.55, 0.75]
    recommended: 0.65
    top_p: 0.9
    max_tokens: 3000

  review_analysis:
    description: "审核分析"
    temperature_range: [0.3, 0.5]
    recommended: 0.4
    top_p: 0.85
    max_tokens: 2000

  polish:
    description: "润色修改"
    temperature_range: [0.3, 0.5]
    recommended: 0.35
    top_p: 0.85
    max_tokens: 2000

  brainstorming:
    description: "创意头脑风暴"
    temperature_range: [0.8, 0.9]
    recommended: 0.85
    top_p: 0.95
    max_tokens: 2000

  long_content_generation:
    description: "长文本生成"
    temperature_range: [0.6, 0.7]
    recommended: 0.65
    top_p: 0.9
    max_tokens: 8000
```

### 4.2 温度选择指南

```markdown
## 温度选择决策树

```
开始
  │
  ├─ 是否需要创意/惊喜？
  │     │
  │     ├─ 是 → 高温度（0.75-0.9）
  │     │        用于：头脑风暴、情节转折
  │     │
  │     └─ 否 → 继续判断
  │
  ├─ 是否需要精确/一致？
  │     │
  │     ├─ 是 → 低温度（0.3-0.5）
  │     │        用于：审核、润色、逻辑检查
  │     │
  │     └─ 否 → 继续判断
  │
  └─ 标准续写/生成
        中温度（0.6-0.7）
```

### 4.3 类型匹配表

```yaml
genre_temperature_mapping:
  玄幻:
    base_temp: 0.7
    scene_adjustments:
      战斗场景: +0.05
      情感场景: -0.05
      对话场景: -0.05

  都市:
    base_temp: 0.65
    scene_adjustments:
      职场场景: 0.6
      情感场景: 0.7
      喜剧场景: +0.1

  古言:
    base_temp: 0.65
    scene_adjustments:
      权谋场景: 0.6
      情感场景: 0.7
      战争场景: +0.05
```

---

## 5. 核心模板示例

### 5.1 大纲生成模板

```markdown
# CARE大纲生成提示词：全文大纲

## C - Context（背景）

### 世界观摘要（必须）
{world_setting_summary}
- 核心规则：{core_rules}
- 力量体系：{power_system}
- 主要势力：{major_factions}

### 项目基本信息
- 项目名称：{project_name}
- 小说类型：{novel_type}
- 核心冲突：{core_conflict}
- 目标读者：{target_audience}

### 已锁定的关键里程碑
{milestones_checklist}

## A - Action（行动）

生成{volume_count}卷的全文大纲，每卷包含：
- 卷主题、核心主线、核心冲突、高潮点
- 章结构（含伏笔标记）
- 全局伏笔布局
- 情感曲线设计

## R - Result（结果）

### 质量门槛
| 维度 | 最低要求 |
|------|---------|
| S1 剧情完整性 | ≥4 |
| S2 逻辑自洽 | ≥4 |
| S6 可读性 | ≥3 |
| S7 主角魅力 | ≥4 |

### 字数要求
- 每章目标：3000-5000字
- 每卷：10-40章

## E - Example（示例）

[见完整文档的示例部分]
```

### 5.2 正文续写模板

```markdown
# CARE正文续写提示词：标准续写

## C - Context（背景）

### 当前场景信息
- 章节：ch{num}
- 视角角色：{pov_character}
- 场景类型：{scene_type}

### 角色状态
{character_name}:
  情绪状态：{emotional_state}
  身体状态：{physical_state}
  当前目标：{current_goal}

### 世界观约束
- 力量体系限制：{power_limitations}
- 已建立规则：{established_rules}
- 当前伏笔状态：{foreshadowing_status}

## A - Action（行动）

在当前光标位置继续写作，生成{word_count}字左右的后续内容。

必须推进：情节、人物、信息
必须保持：视角、风格、节奏
禁止出现：政治敏感、色情暴力、与前文矛盾

## R - Result（结果）

### 质量指标
| S1-S8维度 | 要求 |
|-----------|------|

### 字数要求
- 最少：{min_words}字
- 目标：{target_words}字
- 最多：{max_words}字

## E - Example（示例）

[见完整文档的示例部分]
```

### 5.3 五感描写模板

```markdown
# CARE描写增强提示词：五感描写

## C - Context（背景）

### 描写对象
- 类型：{target_type}
- 名称：{target_name}
- 当前文体风格：{writing_style}
- 当前章节情感：{chapter_emotion}

### 已有的描写
{original_text}

## A - Action（行动）

五感描写（按优先级）：
1. 视觉：颜色、光影、形态
2. 听觉：环境音、人物音
3. 嗅觉：气味描写
4. 触觉：质地、温度
5. 味觉：场景相关时使用

隐喻要求：
- 类型：{metaphor_type}
- 来源：{metaphor_source}

## R - Result（结果）

- 字数增加约{increase_percentage}%
- 感官种类≥3种
- 隐喻数量：{metaphor_count}个

## E - Example（示例）

[见完整文档的示例部分]
```

---

## 6. 版本管理

### 6.1 版本控制规范

```yaml
版本格式：v{MAJOR}.{MINOR}.{PATCH}
  - MAJOR：不兼容的重大变更
  - MINOR：向后兼容的功能新增
  - PATCH：向后兼容的问题修复

版本标签：
  - draft：草稿
  - active：当前版本
  - deprecated：已废弃（6个月过渡期）
```

### 6.2 变更记录

每个模板必须记录：
- 变更内容
- 废弃原因（如有）
- 升级路径

---

## 7. 与其他系统集成

### 7.1 与记忆系统集成

```
提示词组装时 ← MemoryGateway
  • 自动注入角色状态
  • 自动注入伏笔状态
  • 自动注入历史上下文
```

### 7.2 与AI服务抽象层集成

```
提示词系统 → AIGateway
  • 指定场景对应的模型
  • 使用场景推荐温度
  • 获取成本估算
```

### 7.3 与Agent系统集成

```
Agent执行时 → 提示词模板
  • 大纲师 → 大纲模板
  • 写手 → 正文模板
  • 审计官 → 审核模板
  • 润色师 → 润色模板
```

---

## 8. 实施计划

### 阶段1（2周）：模板建设

| 任务 | 负责人 | 交付物 | 验收标准 |
|------|--------|--------|---------|
| 创建目录结构 | 主控 | 目录结构 | 目录存在 |
| 设计模板元数据Schema | 主控 | Schema文档 | 字段定义清晰 |
| 实现大纲生成模板 | 作家主编 | 大纲_CARE.md | CARE四要素完整 |
| 实现正文续写模板 | 作家主编 | 续写_CARE.md | 模板可使用 |
| 实现描写增强模板 | 作家主编 | 描写增强_CARE.md | 参考五感 |
| 提取星陨纪元示例 | 作家A-I | 示例库 | 每类≥2示例 |

### 阶段2（2-3周）：配置与工具

| 任务 | 负责人 | 交付物 | 验收标准 |
|------|--------|--------|---------|
| 实现场景温度映射 | 技术 | 场景温度映射.yaml | 映射合理 |
| 实现版本管理工具 | 技术 | 版本工具 | 支持历史和回滚 |
| 开发提示词组装工具 | 技术 | 组装工具 | 自动填充CARE |
| 实现风格指南库 | 作家主编 | 风格指南 | 每种类型≥1 |
| 对齐22步工作流 | 主控 | 工作流映射表 | 每个STEP对应模板 |

### 阶段3（4-5周）：工具化与优化

| 任务 | 负责人 | 交付物 | 验收标准 |
|------|--------|--------|---------|
| 提示词组装界面 | 技术 | Web界面 | 创作者可方便使用 |
| 版本管理界面 | 技术 | 版本管理界面 | 可视化历史 |
| 使用统计面板 | 技术 | 统计面板 | 显示使用率 |
| 模板推荐引擎 | 技术 | 推荐系统 | 根据场景推荐 |
| 持续优化机制 | 主控 | 优化流程 | 基于数据迭代 |

---

## 9. 验收标准

### 9.1 功能验收

| 功能 | 验收标准 | 测试方法 |
|------|---------|---------|
| 模板创建 | 可创建带元数据的模板 | 创建测试模板 |
| 模板使用 | 可按CARE格式生成提示词 | 使用模板生成 |
| 版本管理 | 支持版本历史和回滚 | 执行回滚 |
| 工作流对齐 | 每个STEP对应正确模板 | 检查配置 |
| 场景温度 | 场景对应正确温度 | 验证映射 |

### 9.2 质量验收

| 指标 | 验收标准 | 测量方法 |
|------|---------|---------|
| 提示词复用率 | ≥3个项目使用同一模板 | 统计记录 |
| S3文笔评分 | 批次均分≥3.5 | 审核统计 |
| 初始化时间减少 | 提示词准备减少50% | 对比新旧 |

---

## 10. 归档的原始文档

以下文档已整合到本设计，原文档归档至 `../deprecated/`：

| 原文档 | 整合内容 |
|--------|---------|
| `2026-05-19-care-prompt-framework-design.md` | CARE框架结构 |
| `2026-05-19-prompt-template-library.md` | 模板集合 |
| `2026-05-19-temperature-guidance-design.md` | 温度参数映射 |

---

## 11. 关键设计决策

| 决策 | 说明 |
|------|------|
| CARE四要素标准化 | 所有提示词统一CARE格式，提高一致性 |
| 场景温度映射 | 不同场景使用不同温度，优化生成效果 |
| 模板版本管理 | 支持版本历史和回滚，便于迭代优化 |
| 示例驱动 | E要素提供高质量示例，提高输出稳定性 |
| 风格指南分离 | 提示词与风格指南分离，便于维护 |
# 提示词体系实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 构建整合提示词体系，基于CARE框架（Context-Action-Result-Example）标准化所有提示词模板，实现场景温度映射和版本管理

**架构：** CARE四要素标准化模板 + 场景温度映射配置 + 版本管理工具。模板按类别组织（大纲/正文/描写/审核/润色），支持版本历史和回滚。

**技术栈：** Markdown, YAML, Python

---

## 文件结构

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
        ├── 模板元数据Schema.yaml
        ├── 模型默认参数.yaml
        ├── 场景温度映射.yaml
        ├── 版本历史/
        │   └── CHANGELOG.md
        ├── 风格指南库/
        │   ├── 玄幻风格.yaml
        │   ├── 都市风格.yaml
        │   └── 古言风格.yaml
        └── 示例库/
            ├── 玄幻示例.yaml
            └── 都市示例.yaml
```

---

## 数据结构定义

### 00_模板索引.yaml

```yaml
templates:
  - id: "outline_full_v1"
    name: "全文大纲"
    category: "outline"
    version: "1.0.0"
    status: "active"
    file: "01_大纲生成/全文大纲_CARE.md"

  - id: "outline_volume_v1"
    name: "卷大纲"
    category: "outline"
    version: "1.0.0"
    status: "active"
    file: "01_大纲生成/卷大纲_CARE.md"

  - id: "continuation_standard_v1"
    name: "标准续写"
    category: "continuation"
    version: "1.0.0"
    status: "active"
    file: "02_正文续写/标准续写_CARE.md"

  - id: "continuation_highstakes_v1"
    name: "高潮场景"
    category: "continuation"
    version: "1.0.0"
    status: "active"
    file: "02_正文续写/高潮场景_CARE.md"

  - id: "continuation_dialogue_v1"
    name: "对话场景"
    category: "continuation"
    version: "1.0.0"
    status: "active"
    file: "02_正文续写/对话场景_CARE.md"
```

### 场景温度映射.yaml

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

### 模板元数据Schema.yaml

```yaml
TemplateMetadata:
  id:
    type: string
    pattern: "{category}_{name}_v{version}"
    example: "outline_full_v1"

  name:
    type: string
    required: true

  category:
    type: enum
    values: [outline, continuation, description, review, polish]
    required: true

  version:
    type: string
    pattern: "{MAJOR}.{MINOR}.{PATCH}"
    required: true

  status:
    type: enum
    values: [draft, active, deprecated]
    default: "draft"

  care_elements:
    context:
      required_fields:
        - world_setting
        - character_status
        - scene_location
      optional_fields:
        - previous_summary
        - foreshadowing
    action:
      output_type:
        type: enum
        values: [outline, prose, dialogue, analysis]
      constraints:
        min_words: integer
        max_words: integer
        format:
          type: enum
          values: [markdown, yaml, json]
    result:
      quality_metrics:
        type: object
        properties:
          S1: integer
          S2: integer
          S3: integer
          S4: integer
          S5: integer
          S6: integer
          S7: integer
          S8: integer
      style_guide_ref: string
    example:
      example_type:
        type: enum
        values: [annotated, raw, contrast]
      location: string

  usage_stats:
    use_count: integer
    success_rate: float
    avg_score: float
    last_used: datetime
```

---

## 任务清单

### Task 1: 目录结构与索引创建

**Files:**
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/README.md`
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/00_模板索引.yaml`
- Create: `novel-factory/config/prompts/模板元数据Schema.yaml`
- Create: `novel-factory/config/prompts/场景温度映射.yaml`
- Create: `novel-factory/config/prompts/版本历史/CHANGELOG.md`

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p "novel-factory/10_方法论/PART3_工具集/提示词模板库/01_大纲生成"
mkdir -p "novel-factory/10_方法论/PART3_工具集/提示词模板库/02_正文续写"
mkdir -p "novel-factory/10_方法论/PART3_工具集/提示词模板库/03_描写增强"
mkdir -p "novel-factory/10_方法论/PART3_工具集/提示词模板库/04_审核辅助"
mkdir -p "novel-factory/10_方法论/PART3_工具集/提示词模板库/05_润色修改"
mkdir -p novel-factory/config/prompts/版本历史
mkdir -p novel-factory/config/prompts/风格指南库
mkdir -p novel-factory/config/prompts/示例库
```

- [ ] **Step 2: 创建 README.md**

```markdown
# 提示词模板库

## 概述

本库包含小说工厂使用的所有标准化提示词模板，基于CARE框架（Context-Action-Result-Example）组织。

## 目录结构

```
提示词模板库/
├── 00_模板索引.yaml          # 模板索引
├── 01_大纲生成/              # 大纲类模板
├── 02_正文续写/              # 正文续写模板
├── 03_描写增强/              # 描写增强模板
├── 04_审核辅助/              # 审核辅助模板
└── 05_润色修改/              # 润色修改模板
```

## CARE框架说明

### C - Context（背景）
包含：世界观摘要、项目基本信息、角色状态、场景信息

### A - Action（行动）
包含：输出类型、约束条件、必须推进的元素、禁止出现的元素

### R - Result（结果）
包含：质量指标（S1-S8）、字数要求、检查清单

### E - Example（示例）
包含：高质量示例（带注释）、角色声音对照、风格对照检查

## 使用方式

1. 根据场景选择模板
2. 填充模板中的变量
3. 设置对应温度参数
4. 生成提示词

## 版本管理

所有模板支持版本控制，详见 `config/prompts/版本历史/CHANGELOG.md`
```

- [ ] **Step 3: 创建 00_模板索引.yaml**

```yaml
# novel-factory/10_方法论/PART3_工具集/提示词模板库/00_模板索引.yaml
templates:
  # 大纲生成
  - id: "outline_full_v1"
    name: "全文大纲"
    category: "outline"
    version: "1.0.0"
    status: "draft"
    file: "01_大纲生成/全文大纲_CARE.md"

  - id: "outline_volume_v1"
    name: "卷大纲"
    category: "outline"
    version: "1.0.0"
    status: "draft"
    file: "01_大纲生成/卷大纲_CARE.md"

  - id: "outline_stage_v1"
    name: "阶段大纲"
    category: "outline"
    version: "1.0.0"
    status: "draft"
    file: "01_大纲生成/阶段大纲_CARE.md"

  - id: "outline_scene_v1"
    name: "场景大纲"
    category: "outline"
    version: "1.0.0"
    status: "draft"
    file: "01_大纲生成/场景大纲_CARE.md"

  # 正文续写
  - id: "continuation_standard_v1"
    name: "标准续写"
    category: "continuation"
    version: "1.0.0"
    status: "draft"
    file: "02_正文续写/标准续写_CARE.md"

  - id: "continuation_highstakes_v1"
    name: "高潮场景"
    category: "continuation"
    version: "1.0.0"
    status: "draft"
    file: "02_正文续写/高潮场景_CARE.md"

  - id: "continuation_dialogue_v1"
    name: "对话场景"
    category: "continuation"
    version: "1.0.0"
    status: "draft"
    file: "02_正文续写/对话场景_CARE.md"

  # 描写增强
  - id: "description_five_senses_v1"
    name: "五感描写"
    category: "description"
    version: "1.0.0"
    status: "draft"
    file: "03_描写增强/五感描写_CARE.md"

  - id: "description_metaphor_v1"
    name: "隐喻描写"
    category: "description"
    version: "1.0.0"
    status: "draft"
    file: "03_描写增强/隐喻描写_CARE.md"

  - id: "description_scene_v1"
    name: "场景描写"
    category: "description"
    version: "1.0.0"
    status: "draft"
    file: "03_描写增强/场景描写_CARE.md"

  # 审核辅助
  - id: "review_logic_v1"
    name: "逻辑检查"
    category: "review"
    version: "1.0.0"
    status: "draft"
    file: "04_审核辅助/逻辑检查_CARE.md"

  - id: "review_pacing_v1"
    name: "节奏评估"
    category: "review"
    version: "1.0.0"
    status: "draft"
    file: "04_审核辅助/节奏评估_CARE.md"

  - id: "review_character_v1"
    name: "角色一致性"
    category: "review"
    version: "1.0.0"
    status: "draft"
    file: "04_审核辅助/角色一致性_CARE.md"

  # 润色修改
  - id: "polish_language_v1"
    name: "语言润色"
    category: "polish"
    version: "1.0.0"
    status: "draft"
    file: "05_润色修改/语言润色_CARE.md"

  - id: "polish_emotion_v1"
    name: "情感强化"
    category: "polish"
    version: "1.0.0"
    status: "draft"
    file: "05_润色修改/情感强化_CARE.md"

  - id: "polish_pacing_v1"
    name: "节奏调整"
    category: "polish"
    version: "1.0.0"
    status: "draft"
    file: "05_润色修改/节奏调整_CARE.md"
```

- [ ] **Step 4: 创建版本历史CHANGELOG.md**

```markdown
# 版本历史

## v1.0.0 (2026-05-19)

### 新增
- 初始版本
- 15个CARE模板
- 场景温度映射
- 模板元数据Schema
```

- [ ] **Step 5: 提交**

```bash
git add "novel-factory/10_方法论/PART3_工具集/提示词模板库/"
git add novel-factory/config/prompts/
git commit -m "feat(prompt): 创建提示词模板库目录结构"
```

---

### Task 2: 大纲生成类模板

**Files:**
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/01_大纲生成/全文大纲_CARE.md`
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/01_大纲生成/卷大纲_CARE.md`

- [ ] **Step 1: 创建全文大纲_CARE.md**

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
- 总字数目标：{total_word_count}
- 总章节数：{total_chapters}

### 已锁定的关键里程碑
{milestones_checklist}

## A - Action（行动）

生成{volume_count}卷的全文大纲，每卷包含：
- 卷主题、核心主线、核心冲突、高潮点
- 每卷章数：{chapters_per_volume}
- 章结构（含伏笔标记）
- 全局伏笔布局
- 情感曲线设计

### 输出格式
```yaml
volumes:
  - volume: 1
    title: "第X卷：XXX"
    theme: "卷主题"
    main_conflict: "核心冲突"
    climax: "高潮点"
    chapters:
      - num: 1
        title: "章节标题"
        core_events: ["事件1", "事件2"]
        foreshadow: ["伏笔ID1"]
        word_target: 3000
```

## R - Result（结果）

### 质量门槛
| 维度 | 最低要求 |
|------|---------|
| S1 剧情完整性 | ≥4 |
| S2 逻辑自洽 | ≥4 |
| S6 可读性 | ≥3 |
| S7 主角魅力 | ≥4 |

### 字数要求
- 每章目标：{target_words_per_chapter}字
- 每卷：{target_words_per_volume}字

### 检查清单
- [ ] 三幕结构清晰
- [ ] 伏笔布局合理
- [ ] 爽点密度适中
- [ ] 情感曲线有起伏

## E - Example（示例）

### 高质量大纲示例

```yaml
volumes:
  - volume: 1
    title: "星陨纪元·起源"
    theme: "废土崛起"
    main_conflict: "生存危机"
    climax: "首次发现遗迹"
    chapters:
      - num: 1
        title: "废墟少年"
        core_events: ["铁蛋出场", "发现信号器", "遭遇袭击"]
        foreshadow: ["FP-001:神秘信号"]
        word_target: 3000
```

### 注释说明
- 章节事件按时间顺序排列
- 伏笔ID格式：FP-XXX
- 情感曲线：开头平淡 → 中期发展 → 高潮爆发
```

- [ ] **Step 2: 创建卷大纲_CARE.md**

```markdown
# CARE大纲生成提示词：卷大纲

## C - Context（背景）

### 卷基本信息
- 卷号：{volume_number}
- 卷标题：{volume_title}
- 前情摘要：{previous_summary}

### 世界观约束
- 力量体系限制：{power_limitations}
- 已建立规则：{established_rules}
- 当前伏笔状态：{foreshadowing_status}

### 角色状态
{character_status}

## A - Action（行动）

生成第{volume_number}卷的详细大纲，包含：
- {chapter_count}章的章纲
- 每章核心事件
- 卷内伏笔埋设
- 卷高潮设计
- 情感曲线

## R - Result（结果）

### 质量门槛
- S1 剧情完整性 ≥ 4
- S2 逻辑自洽 ≥ 4
- S5 节奏控制 ≥ 3.5

### 检查清单
- [ ] 与前卷衔接自然
- [ ] 伏笔推进清晰
- [ ] 角色成长可见

## E - 示例

```yaml
volume_outline:
  volume: 1
  chapters:
    - num: 1
      events: ["角色出场", "冲突引入"]
```
```

- [ ] **Step 3: 提交**

```bash
git add "novel-factory/10_方法论/PART3_工具集/提示词模板库/01_大纲生成/"
git commit -m "feat(prompt): 添加大纲生成类模板"
```

---

### Task 3: 正文续写类模板

**Files:**
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/02_正文续写/标准续写_CARE.md`
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/02_正文续写/高潮场景_CARE.md`
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/02_正文续写/对话场景_CARE.md`

- [ ] **Step 1: 创建标准续写_CARE.md**

```markdown
# CARE正文续写提示词：标准续写

## C - Context（背景）

### 当前场景信息
- 章节：ch{num}
- 视角角色：{pov_character}
- 场景类型：{scene_type}
- 场景位置：{scene_location}
- 时间：{time_marker}

### 角色状态
{character_name}:
  情绪状态：{emotional_state}
  身体状态：{physical_state}
  当前目标：{current_goal}

### 世界观约束
- 力量体系限制：{power_limitations}
- 已建立规则：{established_rules}
- 当前伏笔状态：{foreshadowing_status}

### 前文摘要
{previous_summary}

## A - Action（行动）

在当前光标位置继续写作，生成{min_words}-{max_words}字的后续内容。

### 必须包含
- 推进：情节、人物、信息
- 保持：视角、风格、节奏
- 伏笔：{foreshadow_to_plant}

### 禁止出现
- 政治敏感内容
- 色情暴力
- 与前文矛盾

## R - Result（结果）

### 质量指标
| S1-S8维度 | 要求 |
|-----------|------|
| S1 剧情完整性 | ≥3 |
| S2 逻辑自洽 | ≥3 |
| S3 文笔风格 | ≥3 |
| S4 情感共鸣 | ≥3 |

### 字数要求
- 最少：{min_words}字
- 目标：{target_words}字
- 最多：{max_words}字

### 检查清单
- [ ] 视角一致
- [ ] 对话自然
- [ ] 节奏合适

## E - Example（示例）

### 示例（仅供参考）

铁蛋蹲在废墟顶端，调试着那台老旧的信号器。屏幕上的波形图断断续续，仿佛在诉说着什么。

就在这时，他突然听到了一个声音...

### 风格对照
- 句式：短句为主
- 对话：直接简洁
- 描写：白描为主
```

- [ ] **Step 2: 创建高潮场景_CARE.md**

```markdown
# CARE正文续写提示词：高潮场景

## C - Context（背景）

### 高潮类型
{high_stakes_type}
- 选项：战斗高潮、情感高潮、转折高潮、揭示高潮

### 涉及角色
{characters_involved}

### 情感目标
{emotion_target}
- 紧张度：{tension_level}/10
- 期待感：{anticipation_level}/10

### 前置铺垫
{buildup_summary}

## A - Action（行动）

撰写高潮场景，生成{target_words}字。

### 高潮要素
- 节奏紧凑
- 冲突激烈
- 情感强烈
- 信息密度高

### 结构要求
1. 铺垫（10%）：强化紧张感
2. 升级（30%）：冲突逐步升级
3. 爆发（40%）：核心冲突爆发
4. 余韵（20%）：情感沉淀

## R - Result（结果）

### 质量指标
| 维度 | 要求 |
|------|------|
| S4 情感共鸣 | ≥4.5 |
| S5 节奏控制 | ≥4 |
| S8 人物弧光 | ≥4 |

### 读者反馈预期
- 屏息感：强
- 情感冲击：高

## E - Example（示例）

[见实际训练集]
```

- [ ] **Step 3: 创建对话场景_CARE.md**

```markdown
# CARE正文续写提示词：对话场景

## C - Context（背景）

### 对话类型
{dialogue_type}
- 选项：冲突对话、情感对话、信息对话

### 参与者
{participants}

### 角色关系
{relationship_summary}

### 场景氛围
{scene_atmosphere}

## A - Action（行动）

撰写对话场景，生成{target_words}字。

### 对话要求
- 符合角色性格
- 推进情节/揭示信息
- 潜台词丰富
- 避免机械对白

### 描写比例
- 对话：{dialogue_ratio}%
- 描写：{description_ratio}%
- 动作：{action_ratio}%

## R - Result（结果）

### 质量指标
- S3 文笔风格 ≥ 4
- S6 可读性 ≥ 4

### 检查清单
- [ ] 角色声音独特
- [ ] 对话推动情节
- [ ] 无填鸭式对话

## E - Example（示例）

"你确定要这么做？"林夜的声音很平静。

铁蛋没有回答，只是将手中的信号器调到了最大功率。

"那东西会毁掉一切的。"苏琳向前迈了一步。

"毁掉一切？"铁蛋终于开口，嘴角带着一丝冷笑，"这一切早就该毁了。"
```

- [ ] **Step 4: 提交**

```bash
git add "novel-factory/10_方法论/PART3_工具集/提示词模板库/02_正文续写/"
git commit -m "feat(prompt): 添加正文续写类模板"
```

---

### Task 4: 描写增强类模板

**Files:**
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/03_描写增强/五感描写_CARE.md`
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/03_描写增强/隐喻描写_CARE.md`

- [ ] **Step 1: 创建五感描写_CARE.md**

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

五感描写增强，按优先级：
1. 视觉：颜色、光影、形态
2. 听觉：环境音、人物音
3. 嗅觉：气味描写
4. 触觉：质地、温度
5. 味觉：场景相关时使用

### 隐喻要求
- 类型：{metaphor_type}
- 来源：{metaphor_source}
- 数量：{metaphor_count}个

## R - Result（结果）

### 质量指标
- 感官种类≥3种
- 隐喻数量：{metaphor_count}个
- 字数增加约{increase_percentage}%

### 检查清单
- [ ] 无感官冲突
- [ ] 隐喻贴切
- [ ] 风格统一

## E - Example（示例）

原文：
> 废墟里很安静。

增强后：
> 废墟里很安静。只有风穿过破碎的混凝土缝隙，发出呜咽般的声响。空气中弥漫着铁锈和腐朽混合的气味，让人几乎窒息。阳光从坍塌的天花板缝隙中漏下来，在地面上投下斑驳的光影。
```

- [ ] **Step 2: 创建隐喻描写_CARE.md**

```markdown
# CARE描写增强提示词：隐喻描写

## C - Context（背景）

### 情感目标
{emotion_target}

### 描写对象
{描写对象描述}

### 当前语境
{context}

## A - Action（行动）

生成{metaphor_count}个隐喻，用于增强{emotion_target}。

### 隐喻类型
- 基础隐喻：直接喻体
- 复杂隐喻：多层含义
- 情感隐喻：情绪映射

## R - Result（结果）

### 质量指标
- 隐喻数量：{metaphor_count}
- 贴切度：≥4
- 原创性：新颖

## E - Example（示例）

情感：绝望

隐喻1："希望如风中的烛火，摇曳不定"
隐喻2："他的眼神像死寂的深潭"
隐喻3："绝望是一张网，越挣扎越紧"
```

- [ ] **Step 3: 提交**

```bash
git add "novel-factory/10_方法论/PART3_工具集/提示词模板库/03_描写增强/"
git commit -m "feat(prompt): 添加描写增强类模板"
```

---

### Task 5: 审核辅助类模板

**Files:**
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/04_审核辅助/逻辑检查_CARE.md`
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/04_审核辅助/角色一致性_CARE.md`

- [ ] **Step 1: 创建逻辑检查_CARE.md**

```markdown
# CARE审核辅助提示词：逻辑检查

## C - Context（背景）

### 待检查内容
{chapter_content}

### 世界观规则
{rules}

### 前文设定
{previous_settings}

## A - Action（行动）

检查以下逻辑问题：

### 1. 因果逻辑
- 事件A是否必然导致事件B
- 是否有遗漏的关键步骤

### 2. 时间线逻辑
- 事件顺序是否合理
- 时间流逝是否矛盾

### 3. 能力逻辑
- 角色能力使用是否合理
- 是否超出能力范围

### 4. 常识逻辑
- 是否有违背常识的描述

## R - Result（结果）

### 问题报告格式
```yaml
issues:
  - type: "time_logic"
    severity: "P1"
    location: "第3段"
    description: "前文说3天后，这里说次日"
    suggestion: "统一时间表达"
```

### 严重程度分级
- P0：致命错误
- P1：严重问题
- P2：轻微问题
- P3：建议

## E - Example（示例）

[见审核报告模板]
```

- [ ] **Step 2: 创建角色一致性_CARE.md**

```markdown
# CARE审核辅助提示词：角色一致性

## C - Context（背景）

### 角色卡片
{character_cards}

### 待检查内容
{chapter_content}

## A - Action（行动）

检查以下一致性：

### 1. 性格一致性
- 行为是否符合性格设定
- 对话是否符合说话方式

### 2. 能力一致性
- 是否使用未设定的能力
- 能力表现是否矛盾

### 3. 知识一致性
- 是否了解不应知道的信息
- 技能水平是否矛盾

## R - Result（结果）

### 问题报告格式
```yaml
issues:
  - character: "铁蛋"
    type: "personality_conflict"
    severity: "P1"
    description: "性格为'冷静'出现'暴怒'行为"
    location: "第5段"
    suggestion: "改为'克制地表达不满'"
```
```

- [ ] **Step 3: 提交**

```bash
git add "novel-factory/10_方法论/PART3_工具集/提示词模板库/04_审核辅助/"
git commit -m "feat(prompt): 添加审核辅助类模板"
```

---

### Task 6: 润色修改类模板

**Files:**
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/05_润色修改/语言润色_CARE.md`
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/05_润色修改/情感强化_CARE.md`

- [ ] **Step 1: 创建语言润色_CARE.md**

```markdown
# CARE润色修改提示词：语言润色

## C - Context（背景）

### 目标风格
{style_guide}

### 待润色内容
{original_content}

### 润色程度
{intensity}
- 轻度：仅修改病句
- 中度：优化表达
- 重度：重写表达

## A - Action（行动）

### 润色要点
- 句式变化
- 用词精准
- 删除冗余
- 增强节奏感

### 保持不变
- 核心内容
- 角色声音
- 情感基调

## R - Result（结果）

### 质量指标
- 可读性 ≥ 4
- 表达流畅度提升

### 字数变化
- 允许±10%变化

## E - Example（示例）

原文：
> 可以看出，他的内心是非常紧张的。

润色后：
> 他攥紧了拳头，指节泛白。
```

- [ ] **Step 2: 创建情感强化_CARE.md**

```markdown
# CARE润色修改提示词：情感强化

## C - Context（背景）

### 目标情感
{target_emotion}

### 待强化内容
{original_content}

### 情感强度
{intensity_level}/10

## A - Action（行动）

### 强化手段
- 细节描写
- 内心独白
- 环境烘托
- 动作暗示

## R - Result（结果）

### 质量指标
- 情感共鸣 ≥ 4
- 代入感：强

## E - Example（示例）

原文：
> 他很难过。

润色后：
> 他低着头，肩膀微微颤抖。泪水滴落在地面上，无声地晕开。
```
```

- [ ] **Step 3: 提交**

```bash
git add "novel-factory/10_方法论/PART3_工具集/提示词模板库/05_润色修改/"
git commit -m "feat(prompt): 添加润色修改类模板"
```

---

### Task 7: 场景温度映射配置

**Files:**
- Create: `novel-factory/config/prompts/场景温度映射.yaml`
- Create: `novel-factory/config/prompts/模型默认参数.yaml`

- [ ] **Step 1: 创建场景温度映射.yaml**

```yaml
# novel-factory/config/prompts/场景温度映射.yaml
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

  description_enhancement:
    description: "描写增强"
    temperature_range: [0.5, 0.7]
    recommended: 0.6
    top_p: 0.9
    max_tokens: 2000

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

model_defaults:
  qwen:
    temperature: 0.7
    top_p: 0.9
    max_tokens: 4000

  deepseek:
    temperature: 0.7
    top_p: 0.9
    max_tokens: 4000

  claude:
    temperature: 0.5
    top_p: 0.85
    max_tokens: 4000
```

- [ ] **Step 2: 创建模型默认参数.yaml**

```yaml
# novel-factory/config/prompts/模型默认参数.yaml
models:
  qwen:
    default_temperature: 0.7
    default_top_p: 0.9
    default_max_tokens: 4000
    supports_functions: true

  deepseek:
    default_temperature: 0.7
    default_top_p: 0.9
    default_max_tokens: 4000
    supports_functions: true

  claude:
    default_temperature: 0.5
    default_top_p: 0.85
    default_max_tokens: 4000
    supports_functions: false
```

- [ ] **Step 3: 提交**

```bash
git add novel-factory/config/prompts/场景温度映射.yaml novel-factory/config/prompts/模型默认参数.yaml
git commit -m "feat(prompt): 添加场景温度映射配置"
```

---

### Task 8: 风格指南库

**Files:**
- Create: `novel-factory/config/prompts/风格指南库/玄幻风格.yaml`
- Create: `novel-factory/config/prompts/风格指南库/都市风格.yaml`

- [ ] **Step 1: 创建玄幻风格.yaml**

```yaml
# novel-factory/config/prompts/风格指南库/玄幻风格.yaml
name: "玄幻风格"
genre: "fantasy"

tone:
  description: "宏大叙事与细腻情感并重"
  characteristics:
    - 史诗感
    - 神秘感
    - 热血与深沉交替"

sentence_patterns:
  long: ["复合句为主", "从句嵌套"]
  short: ["战斗场景用短句", "增加节奏感"]

vocabulary:
  preferred:
    - "灵气"、"真元"、"法则"、"大道"
    - 力量描述词汇
    - 境界描述词汇
  avoided:
    - 现代用语
    - 口语化表达

dialogue_style:
  ancient_register: true
  honorifics: true
  common_phrases:
    - "在下"
    - "前辈"
    - "承让"

description_density:
  world_building: "high"
  emotion: "medium"
  action: "medium"
```

- [ ] **Step 2: 创建都市风格.yaml**

```yaml
# novel-factory/config/prompts/风格指南库/都市风格.yaml
name: "都市风格"
genre: "urban"

tone:
  description: "贴近生活，节奏明快"
  characteristics:
    - 现实感
    - 时尚感
    - 轻松与紧张交替

sentence_patterns:
  long: ["对话为主", "短句推进"]
  short: ["对话使用", "增加张力"]

vocabulary:
  preferred:
    - 现代职场用语
    - 网络流行语（适量）
    - 专业术语
  avoided:
    - 古语
    - 过度文艺

dialogue_style:
  ancient_register: false
  modern_voice: true
  characteristics:
    - 口语化
    - 真实感
    - 个性鲜明

description_density:
  world_building: "low"
  emotion: "high"
  action: "medium"
```

- [ ] **Step 3: 提交**

```bash
git add novel-factory/config/prompts/风格指南库/
git commit -m "feat(prompt): 添加风格指南库"
```

---

### Task 9: 模板组装工具（Python）

**Files:**
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/prompt_assembler.py`
- Create: `tests/prompt_system/test_prompt_assembler.py`

- [ ] **Step 1: 编写测试**

```python
# tests/prompt_system/test_prompt_assembler.py
import pytest
from prompt_system.prompt_assembler import PromptAssembler

def test_prompt_assembler_init():
    assembler = PromptAssembler()
    assert assembler is not None

def test_load_template():
    assembler = PromptAssembler()
    template = assembler.load_template("outline_full_v1")
    assert template is not None
    assert "C - Context" in template.content

def test_assemble_prompt():
    assembler = PromptAssembler()
    variables = {
        "world_setting_summary": "测试世界观",
        "core_rules": "测试规则"
    }
    result = assembler.assemble("outline_full_v1", variables)
    assert "测试世界观" in result
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/prompt_system/test_prompt_assembler.py -v
# 预期: FAIL
```

- [ ] **Step 3: 实现 PromptAssembler**

```python
# novel-factory/10_方法论/PART3_工具集/提示词模板库/prompt_assembler.py
"""
提示词组装工具
"""
import re
import yaml
from pathlib import Path
from typing import Dict, Optional, Any

class PromptAssembler:
    """提示词组装器"""

    def __init__(self, template_dir: Optional[str] = None, config_dir: Optional[str] = None):
        self.template_dir = template_dir or "novel-factory/10_方法论/PART3_工具集/提示词模板库"
        self.config_dir = config_dir or "novel-factory/config/prompts"
        self._template_cache = {}
        self._index = self._load_index()

    def _load_index(self) -> Dict:
        """加载模板索引"""
        index_file = Path(self.template_dir) / "00_模板索引.yaml"
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {"templates": []}

    def load_template(self, template_id: str) -> Optional[Dict]:
        """加载模板"""
        if template_id in self._template_cache:
            return self._template_cache[template_id]

        # 查找模板
        template_info = None
        for t in self._index.get("templates", []):
            if t["id"] == template_id:
                template_info = t
                break

        if not template_info:
            return None

        # 加载模板内容
        template_path = Path(self.template_dir) / template_info["file"]
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()

            result = {
                "id": template_id,
                "name": template_info["name"],
                "category": template_info["category"],
                "version": template_info["version"],
                "content": content
            }
            self._template_cache[template_id] = result
            return result

        return None

    def assemble(self, template_id: str, variables: Dict[str, Any]) -> str:
        """组装提示词"""
        template = self.load_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        content = template["content"]

        # 替换变量 {var_name} -> value
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            content = content.replace(placeholder, str(value))

        return content

    def get_temperature(self, scene: str, genre: Optional[str] = None) -> Dict[str, Any]:
        """获取温度参数"""
        config_file = Path(self.config_dir) / "场景温度映射.yaml"
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        scene_config = config.get("scenes", {}).get(scene, {})
        if not scene_config:
            return {"temperature": 0.7}

        temp = scene_config.get("recommended", 0.7)

        # 类型调整
        if genre:
            genre_config = config.get("genre_temperature_mapping", {}).get(genre, {})
            adjustments = genre_config.get("scene_adjustments", {})
            for adj_scene, adjustment in adjustments.items():
                if adj_scene in scene:
                    if isinstance(adjustment, (int, float)):
                        temp += adjustment
                    else:
                        temp = adjustment

        return {
            "temperature": temp,
            "top_p": scene_config.get("top_p", 0.9),
            "max_tokens": scene_config.get("max_tokens", 4000)
        }

    def list_templates(self, category: Optional[str] = None) -> list:
        """列出模板"""
        templates = self._index.get("templates", [])
        if category:
            templates = [t for t in templates if t["category"] == category]
        return templates
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/prompt_system/test_prompt_assembler.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add novel-factory/10_方法论/PART3_工具集/提示词模板库/prompt_assembler.py tests/prompt_system/test_prompt_assembler.py
git commit -m "feat(prompt): 添加模板组装工具"
```

---

## 自检清单

- [ ] 所有模板是否覆盖CARE四要素
- [ ] 场景温度映射是否完整
- [ ] 模板索引是否包含所有模板
- [ ] 模板组装工具是否可用
- [ ] 提交消息是否符合规范 (feat: ...)

---

## 执行选项

**Plan complete and saved to `docs/superpowers/plans/2026-05-19-prompt-system-implementation-plan.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
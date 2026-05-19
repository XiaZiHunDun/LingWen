# CARE框架提示词体系实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立标准化的CARE提示词框架，实现提示词的统一组织、版本管理和工具化支持

**Architecture:** 采用分层目录结构，按创作阶段（大纲/正文/描写/审核/润色）组织模板，每个模板包含CARE四要素（Context/Action/Result/Example），通过元数据Schema管理版本，通过提示词组装工具实现动态填充

**Tech Stack:** Markdown模板 + YAML配置 + Python脚本

---

## 文件结构

```
novel-factory/
├── 10_方法论/
│   └── PART3_工具集/
│       └── 提示词模板库/
│           ├── README.md                    # 模板库索引
│           ├── 00_模板索引.yaml              # 模板分类索引
│           ├── 01_大纲生成/                  # 4个模板
│           ├── 02_正文续写/                  # 3个模板
│           ├── 03_描写增强/                  # 3个模板
│           ├── 04_审核辅助/                  # 3个模板
│           └── 05_润色修改/                  # 3个模板
├── config/
│   └── prompts/
│       ├── 模型默认参数.yaml
│       ├── 风格指南库/
│       └── 示例库/
└── scripts/
    └── prompt_assembler.py                  # 提示词组装工具
```

---

### Task 1: 创建目录结构和基础文件

**Files:**
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/README.md`
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/00_模板索引.yaml`
- Create: `novel-factory/config/prompts/模型默认参数.yaml`
- Create: `novel-factory/config/prompts/风格指南库/README.md`
- Create: `novel-factory/config/prompts/示例库/README.md`

- [ ] **Step 1: 创建README.md索引文件**

```markdown
# 提示词模板库

> 版本: v1.0
> 更新日期: 2026-05-19

## 概述

本目录包含小说工厂CARE框架提示词模板，按创作阶段组织。

## 目录结构

```
提示词模板库/
├── 01_大纲生成/      # 大纲生成相关模板
├── 02_正文续写/      # 正文续写模板
├── 03_描写增强/      # 描写增强模板（参考Sudowrite）
├── 04_审核辅助/      # 审核辅助模板
└── 05_润色修改/      # 润色修改模板
```

## 使用说明

1. 选择对应阶段的模板
2. 按CARE格式填充内容
3. 使用prompt_assembler.py组装
4. 调用AI服务生成

## 版本管理

- 所有模板使用语义化版本 v{MAJOR}.{MINOR}.{PATCH}
- 状态: draft → active → deprecated
- 变更记录见各模板文件的元数据
```

- [ ] **Step 2: 创建00_模板索引.yaml**

```yaml
templates:
  - id: outline_global_v1
    name: 全文大纲生成
    category: outline
    version: v1.0.0
    status: active
    file: 01_大纲生成/全文大纲生成_CARE.md
    description: 生成多卷全文大纲
    related_steps:
      - STEP_06
      - STEP_10

  - id: outline_volume_v1
    name: 卷大纲生成
    category: outline
    version: v1.0.0
    status: active
    file: 01_大纲生成/卷大纲生成_CARE.md
    description: 生成单卷大纲
    related_steps:
      - STEP_07

  - id: outline_stage_v1
    name: 阶段大纲生成
    category: outline
    version: v1.0.0
    status: active
    file: 01_大纲生成/阶段大纲生成_CARE.md
    description: 生成阶段大纲
    related_steps:
      - STEP_11

  - id: outline_scene_v1
    name: 场景大纲生成
    category: outline
    version: v1.0.0
    status: active
    file: 01_大纲生成/场景大纲生成_CARE.md
    description: 生成场景大纲

  - id: continuation_standard_v1
    name: 标准续写
    category: continuation
    version: v1.0.0
    status: active
    file: 02_正文续写/标准续写_CARE.md
    description: 标准章节续写
    related_steps:
      - STEP_14

  - id: continuation_climax_v1
    name: 高潮场景续写
    category: continuation
    version: v1.0.0
    status: active
    file: 02_正文续写/高潮场景续写_CARE.md
    description: 高潮场景续写

  - id: continuation_dialogue_v1
    name: 对话场景续写
    category: continuation
    version: v1.0.0
    status: active
    file: 02_正文续写/对话场景续写_CARE.md
    description: 对话场景续写

  - id: description_five_sense_v1
    name: 五感描写
    category: description
    version: v1.0.0
    status: active
    file: 03_描写增强/五感描写_CARE.md
    description: 五感描写增强（参考Sudowrite）

  - id: description_metaphor_v1
    name: 隐喻描写
    category: description
    version: v1.0.0
    status: active
    file: 03_描写增强/隐喻描写_CARE.md
    description: 隐喻描写增强

  - id: description_scene_v1
    name: 场景描写
    category: description
    version: v1.0.0
    status: active
    file: 03_描写增强/场景描写_CARE.md
    description: 场景描写增强

  - id: review_logic_v1
    name: 逻辑检查
    category: review
    version: v1.0.0
    status: active
    file: 04_审核辅助/逻辑检查_CARE.md
    description: 逻辑一致性检查

  - id: review_pacing_v1
    name: 节奏评估
    category: review
    version: v1.0.0
    status: active
    file: 04_审核辅助/节奏评估_CARE.md
    description: 节奏控制评估

  - id: review_character_v1
    name: 角色一致性
    category: review
    version: v1.0.0
    status: active
    file: 04_审核辅助/角色一致性_CARE.md
    description: 角色一致性检查

  - id: polish_language_v1
    name: 语言润色
    category: polish
    version: v1.0.0
    status: active
    file: 05_润色修改/语言润色_CARE.md
    description: 语言风格润色

  - id: polish_emotion_v1
    name: 情感强化
    category: polish
    version: v1.0.0
    status: active
    file: 05_润色修改/情感强化_CARE.md
    description: 情感表达强化

  - id: polish_pacing_v1
    name: 节奏调整
    category: polish
    version: v1.0.0
    status: active
    file: 05_润色修改/节奏调整_CARE.md
    description: 节奏调整

statistics:
  total_templates: 16
  by_category:
    outline: 4
    continuation: 3
    description: 3
    review: 3
    polish: 3
```

- [ ] **Step 3: 创建config/prompts/模型默认参数.yaml**

```yaml
# AI模型默认参数配置

default_temperature: 0.7

# 按场景的默认参数
scene_defaults:
  outline_generation:
    temperature: 0.6
    max_tokens: 2000
    top_p: 0.9

  content_continuation:
    temperature: 0.7
    max_tokens: 4000
    top_p: 0.9

  description_enhancement:
    temperature: 0.55
    max_tokens: 2000
    top_p: 0.85

  review_analysis:
    temperature: 0.4
    max_tokens: 2000
    top_p: 0.85

  polish:
    temperature: 0.4
    max_tokens: 3000
    top_p: 0.85

  brainstorming:
    temperature: 0.85
    max_tokens: 2000
    top_p: 0.95

# 模型适配
model_preferences:
  deepseek:
    - outline_generation
    - content_continuation

  claude:
    - review_analysis
    - long_content

  qwen:
    - polish
    - outline_generation
```

- [ ] **Step 4: 提交初始文件**

```bash
cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory
mkdir -p 10_方法论/PART3_工具集/提示词模板库/{01_大纲生成,02_正文续写,03_描写增强,04_审核辅助,05_润色修改}
mkdir -p config/prompts/{风格指南库,示例库}
git add 10_方法论/PART3_工具集/提示词模板库/README.md
git add 10_方法论/PART3_工具集/提示词模板库/00_模板索引.yaml
git add config/prompts/模型默认参数.yaml
git add config/prompts/风格指南库/README.md
git add config/prompts/示例库/README.md
git commit -m "feat: 初始化CARE提示词模板库目录结构"
```

---

### Task 2: 创建大纲生成模板（4个）

**Files:**
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/01_大纲生成/全文大纲生成_CARE.md`
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/01_大纲生成/卷大纲生成_CARE.md`
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/01_大纲生成/阶段大纲生成_CARE.md`
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/01_大纲生成/场景大纲生成_CARE.md`

- [ ] **Step 1: 创建全文大纲生成_CARE.md**

```markdown
# CARE大纲生成提示词：全文大纲

> 版本: v1.0.0
> 状态: active
> 更新日期: 2026-05-19

---

## C - Context（背景）

### 世界观摘要（必须）
{world_setting_summary}
- 核心规则：{core_rules}
- 力量体系：{power_system}
- 主要势力：{major_factions}

### 项目基本信息
- 项目名称：{project_name}
- 小说类型：{novel_type}（玄幻/都市/古言/科幻）
- 核心冲突：{core_conflict}
- 目标读者：{target_audience}

### 已锁定的关键里程碑
{milestones_checklist}
- [ ] {milestone_1}：ch{chapter_1}
- [ ] {milestone_2}：ch{chapter_2}
- [ ] {milestone_3}：ch{chapter_3}

### 参考作品风格（可选）
{reference_works}
- 《{reference_1}》：{style_notes}
- 《{reference_2}》：{style_notes}

---

## A - Action（行动）

生成{volume_count}卷的全文大纲，每卷包含：

### 1. 卷核心定义（每卷）
- 卷主题：{vol_theme}
- 卷核心主线：{vol_main_arc}（50字内）
- 卷核心冲突：{vol_core_conflict}
- 卷高潮点：{vol_climax_description}

### 2. 章结构（每卷{chapter_count}章）
```yaml
章节结构模板：
- chapter_num: ch{num}
  chapter_theme: "{chapter_theme}"
  core_events:
    - {event_1}
    - {event_2}
  character_arc: "{character_development}"
  foreshadowing:
    - {foreshadow_item_1}
    - {foreshadow_item_2}
  word_count_target: {word_count}
  pacing: enum  # slow|medium|fast|climax
```

### 3. 全局伏笔布局
伏笔规划需要覆盖：
- 人物伏笔：{person_foreshadowing_count}个
- 物品伏笔：{item_foreshadowing_count}个
- 事件伏笔：{event_foreshadowing_count}个

### 4. 情感曲线设计
```
情感曲线模板（按卷）：
卷1：■■■■■■■■□□ （上升型，开篇吸引）
卷2：■■■■■■■■■■ （高潮型，冲突密集）
卷3：■■■■■□□□□□ （低谷型，绝境设置）
卷4：■■■■■■■■■■ （爆发型，解决问题）
```

---

## R - Result（结果）

### 结构要求
- 总卷数：{volume_count}卷
- 总章节数：{total_chapters}章
- 结构：三幕式（/{structure_type}）
- 第一幕重点：ch001-ch010（建置）
- 第二幕重点：ch011-ch{vol_2_end}（对抗）
- 第三幕重点：ch{vol_3_start}-ch{total}（解决）

### 质量门槛
| 维度 | 最低要求 |
|------|---------|
| S1 剧情完整性 | ≥4 |
| S2 逻辑自洽 | ≥4 |
| S6 可读性 | ≥3 |
| S7 主角魅力 | ≥4 |

### 格式要求
- 语言：中文
- 格式：Markdown
- 章节标题：`## ch{num} {chapter_title}`
- 输出字符集：UTF-8

---

## E - Example（示例）

### 参考大纲风格
以下示例来自{reference_novel}：

```markdown
## 第一卷 觉醒

### ch001 废土少年
**核心事件**：林夜在废墟中觉醒，发现自己体内蕴含着上古力量。

**章节结构**：
- 开篇（500字）：废土场景描写，林夜的基本生存状态
- 发展（1500字）：神秘石头的发现，力量的初步觉醒
- 高潮（1000字）：首次使用力量，击退野兽
- 结尾（500字）：引出更大的世界背景

**人物状态**：
- 林夜：迷茫但不甘平庸，渴望力量改变命运
- 苏琳：初登场，神秘少女，对林夜表现出兴趣

**伏笔埋设**：
- 林夜体内的力量来源（FP-001）
- 苏琳的身份背景（FP-002）

**情感基调**：紧张中带有希望
```

### 章节模板对照
```yaml
良好示例特征：
- 有明确的场景转换标记
- 包含具体的字数估算
- 有人物状态描述
- 有伏笔标记

对照检查清单：
- [ ] 每章是否都有核心事件？
- [ ] 每章是否有人物状态描述？
- [ ] 每章是否有伏笔标记？
- [ ] 字数估算是否合理（3000-5000字）？
```

---

## 元数据

```yaml
template_metadata:
  id: outline_global_v1
  name: 全文大纲生成
  version: v1.0.0
  status: active
  author: system
  created_at: 2026-05-19
  updated_at: 2026-05-19

  care_elements:
    context:
      required_fields:
        - world_setting_summary
        - core_conflict
        - milestones
      optional_fields:
        - reference_works
    action:
      output_type: outline
      constraints:
        min_chapters: 10
        max_chapters: 500
    result:
      quality_metrics:
        - S1 >= 4
        - S2 >= 4
        - S6 >= 3
        - S7 >= 4
    example:
      example_type: annotated
      location: inline

  usage_stats:
    use_count: 0
    success_rate: 0
    avg_score: 0
```
```

- [ ] **Step 2: 创建卷大纲生成_CARE.md**

```markdown
# CARE大纲生成提示词：卷大纲

> 版本: v1.0.0
> 状态: active
> 更新日期: 2026-05-19

---

## C - Context（背景）

### 当前卷信息
- 卷号：第{volume_num}卷
- 卷主题：{vol_theme}
- 小说类型：{novel_type}

### 前置上下文
- 前一卷结局：{prev_vol_ending}
- 本卷起点：{vol_starting_point}
- 核心悬念：{core_mystery}

### 角色状态（本章开始时）
{character_status_list}
- {char_name}：{emotional_state}，{position}
- {char_name}：{emotional_state}，{position}

### 已铺设在全局大纲中的伏笔
{foreshadowing_list}
- FP-{id}：{description}（埋设于ch{plant_ch}）

---

## A - Action（行动）

生成第{volume_num}卷的详细大纲，包含：

### 1. 卷核心
- 卷主题句：{theme_sentence}
- 本卷核心冲突：{core_conflict}
- 本卷核心问题：{core_question}
- 预期解决：{expected_resolution}

### 2. 章结构（{chapter_count}章）
对每章：
- 章节号：ch{num}
- 章节标题：{title}
- 核心事件：{event}
- 人物状态变化：{char_changes}
- 伏笔关联：{foreshadow_mentions}
- 目标字数：{word_count}

### 3. 情节点
```yaml
情节点序列：
1. 触发点：{trigger_event}
2. 上升：{rising_action}
3. 高潮：{climax_event}
4. 解决：{resolution}
5. 连接：{next_connection}
```

### 4. 伏笔计划
| 伏笔ID | 埋设章节 | 预期回收 | 类型 |
|--------|---------|---------|------|
| FP-{id} | ch{num} | ch{回收} | 人物/物品/事件 |

---

## R - Result（结果）

### 格式要求
- 使用Markdown格式
- 每个章节独立标题
- 包含字数估算
- 伏笔标记清晰

### 质量标准
- 章与章之间衔接自然
- 伏笔有埋有收
- 角色行为逻辑一致
- 情感曲线有起伏

---

## E - Example（示例）

```markdown
## 第1章 新开始

**章节目标**：林夜加入联盟，开始新训练

**核心事件**：
- 联盟教官测试林夜实力
- 林夜发现自己的独特天赋
- 与苏琳再次相遇

**字数目标**：3500字

**伏笔**：
- FP-001在本章埋设（教官对林夜天赋的特别注意）
```

---

## 元数据

```yaml
template_metadata:
  id: outline_volume_v1
  name: 卷大纲生成
  version: v1.0.0
  status: active
  related_steps:
    - STEP_06
    - STEP_07
```
```

- [ ] **Step 3: 创建阶段大纲生成_CARE.md和场景大纲生成_CARE.md**

（类似结构，包含CARE四要素，具体内容根据阶段/场景特点调整）

- [ ] **Step 4: 提交大纲生成模板**

```bash
git add 10_方法论/PART3_工具集/提示词模板库/01_大纲生成/*.md
git commit -m "feat: 添加4个大纲生成模板"
```

---

### Task 3: 创建正文续写模板（3个）

**Files:**
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/02_正文续写/标准续写_CARE.md`
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/02_正文续写/高潮场景续写_CARE.md`
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/02_正文续写/对话场景续写_CARE.md`

- [ ] **Step 1: 创建标准续写_CARE.md**

```markdown
# CARE正文续写提示词：标准续写

> 版本: v1.0.0
> 状态: active
> 更新日期: 2026-05-19

---

## C - Context（背景）

### 当前场景信息
- 章节：ch{num}
- 视角角色：{pov_character}
- 场景类型：{scene_type}（战斗/日常/对话/回忆）

### 场景设定
- 地点：{location}
- 时间：{time_period}
- 场景氛围：{scene_mood}
- 在场人物：{characters_present}

### 章节上下文
```yaml
章节目标：
  主线任务：{main_arc_objective}
  情感目标：{emotional_objective}
  信息目标：{info_objective}

前文概要（200字）：
{previous_chapter_summary}

当前情节位置：
{plot_position}  # 铺垫/上升/高潮/余波
```

### 角色状态
```yaml
{character_name}:
  情绪状态：{emotional_state}
  身体状态：{physical_state}
  当前目标：{current_goal}
  阻碍因素：{obstacles}
  欲望：{desire}
  恐惧：{fear}
```

### 世界观约束
- 力量体系限制：{power_limitations}
- 已建立规则：{established_rules}
- 当前伏笔状态：{foreshadowing_status}

---

## A - Action（行动）

### 续写要求
在当前光标位置继续写作，生成{word_count}字左右的后续内容。

#### 必须推进的元素
1. 情节：{plot_advancement_requirement}
2. 人物：{character_development_requirement}
3. 信息：{information_disclosure_requirement}

#### 必须保持的元素
1. 视角：{pov_constraint}（保持第三人称限制性视角）
2. 风格：{style_constraint}
3. 节奏：{pacing_constraint}

#### 禁止出现的元素
{forbidden_elements}
- 政治敏感内容
- 色情暴力内容
- 与前文矛盾的内容

---

## R - Result（结果）

### 质量指标
| 指标 | 要求 |
|------|------|
| S1 剧情完整性 | 章内目标-障碍-结果清晰 |
| S2 逻辑自洽 | 与前文无矛盾 |
| S3 文笔风格 | 与本章风格一致 |
| S4 情感共鸣 | 有情感波动 |
| S5 节奏控制 | 符合当前节奏位置 |
| S6 可读性 | 读者愿意继续读 |
| S7 主角魅力 | 主角行为可认同 |

### 字数要求
- 最少：{min_words}字
- 目标：{target_words}字
- 最多：{max_words}字
- 理想区间：3000-5000字

---

## E - Example（示例）

```markdown
## ch058 续写内容

林夜握紧手中的剑柄，指节因用力而泛白。

"你以为这样就能阻止我？"他的声音低沉，却带着一种奇异的平静。

【续写要点分析】
1. 情绪递进：从平静到爆发的节奏
2. 对话设计：短句有力，符合林夜性格
3. 伏笔呼应：呼应"十五年前"的核心设定
4. 场景张力：为后续战斗做铺垫
```

---

## 元数据

```yaml
template_metadata:
  id: continuation_standard_v1
  name: 标准续写
  version: v1.0.0
  status: active
  related_steps:
    - STEP_14
```
```

- [ ] **Step 2: 创建高潮场景续写_CARE.md和对话场景续写_CARE.md**

（类似结构，针对高潮场景和对话场景的特点调整）

- [ ] **Step 3: 提交正文续写模板**

```bash
git add 10_方法论/PART3_工具集/提示词模板库/02_正文续写/*.md
git commit -m "feat: 添加3个正文续写模板"
```

---

### Task 4: 创建描写增强模板（3个）

**Files:**
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/03_描写增强/五感描写_CARE.md`
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/03_描写增强/隐喻描写_CARE.md`
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/03_描写增强/场景描写_CARE.md`

- [ ] **Step 1: 创建五感描写_CARE.md（参考Sudowrite）**

```markdown
# CARE描写增强提示词：五感描写

> 版本: v1.0.0
> 状态: active
> 更新日期: 2026-05-19
> 参考: Sudowrite五感描写功能

---

## C - Context（背景）

### 描写对象类型
- 类型：{target_type}（人物/场景/物品/情感）
- 名称：{target_name}

### 当前文体风格
- 小说类型：{novel_type}
- 文风：{writing_style}
- 章节约束：{chapter_constraints}

### 情感上下文
- 当前章节情感：{chapter_emotion}
- 情感阶段：{emotional_stage}（铺垫/上升/高潮/余波）
- 目标情感效果：{target_emotional_effect}

### 已有的描写（需增强）
```markdown
{original_text}

分析：
- 已使用的感官：{used_senses}
- 缺少的感官：{missing_senses}
- 描写密度：{density}/10
```

---

## A - Action（行动）

### 增强要求

#### 五感描写（按优先级）
1. **视觉**：{visual_priority}
2. **听觉**：{audio_priority}
3. **嗅觉**：{smell_priority}
4. **触觉**：{tactile_priority}
5. **味觉**：{taste_priority}

#### 隐喻要求
- 隐喻类型：{metaphor_type}
- 隐喻来源：{metaphor_source}

---

## R - Result（结果）

### 质量要求
- 字数：增加约{increase_percentage}%
- 感官种类：≥3种
- 隐喻数量：{metaphor_count}个
- 情感契合度：{emotional_fit}/10

---

## E - Example（示例）

```markdown
### 原文
林夜站在废墟中，看着远方的城市。

### 增强后
林夜站在废墟中，看着远方的城市。

【视觉】夕阳将天空染成血红色，废墟的轮廓在余晖中显得格外锐利。
【听觉】远处传来城市的喧嚣声，像是另一个世界的呼唤。
【嗅觉】空气中弥漫着尘土和腐朽的气息，偶尔夹杂着一丝焦糊味。
【触觉】风吹过脸颊，带着一丝凉意。

【五感分布】视觉60% 听觉20% 嗅觉15% 触觉5%

【隐喻】废墟→过去的记忆；城市喧嚣→未来的希望
```

---

## 元数据

```yaml
template_metadata:
  id: description_five_sense_v1
  name: 五感描写
  version: v1.0.0
  status: active
```
```

- [ ] **Step 2: 创建隐喻描写_CARE.md和场景描写_CARE.md**

- [ ] **Step 3: 提交描写增强模板**

```bash
git add 10_方法论/PART3_工具集/提示词模板库/03_描写增强/*.md
git commit -m "feat: 添加3个描写增强模板"
```

---

### Task 5: 创建审核辅助模板（3个）

**Files:**
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/04_审核辅助/逻辑检查_CARE.md`
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/04_审核辅助/节奏评估_CARE.md`
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/04_审核辅助/角色一致性_CARE.md`

- [ ] **Step 1-3: 创建审核辅助模板（类似结构）**

```bash
git add 10_方法论/PART3_工具集/提示词模板库/04_审核辅助/*.md
git commit -m "feat: 添加3个审核辅助模板"
```

---

### Task 6: 创建润色修改模板（3个）

**Files:**
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/05_润色修改/语言润色_CARE.md`
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/05_润色修改/情感强化_CARE.md`
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/05_润色修改/节奏调整_CARE.md`

- [ ] **Step 1-3: 创建润色修改模板（类似结构）**

```bash
git add 10_方法论/PART3_工具集/提示词模板库/05_润色修改/*.md
git commit -m "feat: 添加3个润色修改模板"
```

---

### Task 7: 创建提示词组装工具

**Files:**
- Create: `novel-factory/scripts/prompt_assembler.py`
- Create: `novel-factory/tests/test_prompt_assembler.py`

- [ ] **Step 1: 创建prompt_assembler.py**

```python
#!/usr/bin/env python3
"""
提示词组装工具
根据CARE模板和上下文自动组装提示词
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class CAREContext:
    """CARE上下文数据"""
    world_setting_summary: str = ""
    core_conflict: str = ""
    character_status: Dict[str, str] = None
    chapter_info: Dict[str, Any] = None
    style_guide: str = ""
    example_content: str = ""

class PromptAssembler:
    """提示词组装器"""

    def __init__(self, template_dir: Path):
        self.template_dir = template_dir
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict:
        """加载所有模板"""
        index_file = self.template_dir / "00_模板索引.yaml"
        with open(index_file, 'r', encoding='utf-8') as f:
            index = yaml.safe_load(f)
        return {t['id']: t for t in index['templates']}

    def assemble(
        self,
        template_id: str,
        context: CAREContext
    ) -> str:
        """组装提示词"""
        template_meta = self.templates.get(template_id)
        if not template_meta:
            raise ValueError(f"Template {template_id} not found")

        template_file = self.template_dir / template_meta['file']
        with open(template_file, 'r', encoding='utf-8') as f:
            template = f.read()

        # 替换CARE要素占位符
        assembled = template
        assembled = assembled.replace('{world_setting_summary}', context.world_setting_summary)
        assembled = assembled.replace('{core_conflict}', context.core_conflict)
        # ... 其他占位符替换

        return assembled

    def get_template_info(self, template_id: str) -> Optional[Dict]:
        """获取模板信息"""
        return self.templates.get(template_id)

    def list_templates(self, category: Optional[str] = None) -> list:
        """列出模板"""
        if category:
            return [t for t in self.templates.values() if t['category'] == category]
        return list(self.templates.values())

if __name__ == "__main__":
    template_dir = Path(__file__).parent.parent / "10_方法论/PART3_工具集/提示词模板库"
    assembler = PromptAssembler(template_dir)

    # 列出所有模板
    for t in assembler.list_templates():
        print(f"{t['id']}: {t['name']} ({t['category']})")
```

- [ ] **Step 2: 创建测试文件**

```python
import pytest
from prompt_assembler import PromptAssembler, CAREContext
from pathlib import Path

def test_assemble_standard_continuation():
    assembler = PromptAssembler(Path("10_方法论/PART3_工具集/提示词模板库"))

    context = CAREContext(
        world_setting_summary="一个修炼者与暗皇对抗的世界",
        core_conflict="林夜vs暗皇",
        chapter_info={'num': '001', 'pov': '林夜'}
    )

    result = assembler.assemble('continuation_standard_v1', context)
    assert '{world_setting_summary}' not in result
    assert '林夜' in result

def test_list_templates():
    assembler = PromptAssembler(Path("10_方法论/PART3_工具集/提示词模板库"))
    templates = assembler.list_templates()
    assert len(templates) >= 16

def test_get_template_info():
    assembler = PromptAssembler(Path("10_方法论/PART3_工具集/提示词模板库"))
    info = assembler.get_template_info('outline_global_v1')
    assert info is not None
    assert info['name'] == '全文大纲生成'
```

- [ ] **Step 3: 运行测试**

```bash
cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory
python -m pytest tests/test_prompt_assembler.py -v
```

- [ ] **Step 4: 提交**

```bash
git add scripts/prompt_assembler.py tests/test_prompt_assembler.py
git commit -m "feat: 添加提示词组装工具"
```

---

### Task 8: 创建风格指南和示例库

**Files:**
- Create: `novel-factory/config/prompts/风格指南库/玄幻风格.yaml`
- Create: `novel-factory/config/prompts/示例库/玄幻示例.yaml`
- Create: `novel-factory/config/prompts/示例库/都市示例.yaml`

- [ ] **Step 1: 创建风格指南**

```yaml
# 玄幻风格指南

style_name: 玄幻
version: v1.0.0
description: 玄幻小说写作风格指南

# 词汇选择
vocabulary:
  力量体系:
    - 灵气、真元、法力、灵力
    - 筑基、金丹、元婴、化神
  场景描写:
    - 苍穹、虚空、星河、废墟
    - 雷霆、风暴、烈焰、寒冰

# 句式特征
sentence_patterns:
  战斗描写:
    - 短句为主，节奏紧凑
    - 动宾结构，力道十足
  叙述描写:
    - 长短句结合，张弛有度

# 情感基调
emotional_tone:
  紧张: "气息凝固、剑拔弩张"
  激动: "热血沸腾、心潮澎湃"
  压抑: "风云变色、山雨欲来"

# 禁止词汇
forbidden_words:
  - 现代网络用语
  - 过于口语化的表达
```

- [ ] **Step 2: 创建示例库**

```yaml
# 玄幻示例库

examples:
  - id: combat_scene_001
    title: 战斗场景示例
    category: combat
    content: |
      林夜身形一闪，剑光如虹。

      "受死！"他低喝一声，剑尖直刺暗皇胸口。

      暗皇冷笑一声，抬手抵挡。两股力量碰撞，
      周围空气瞬间扭曲。

      【分析】短句有力，动作连贯，符合玄幻战斗风格
    tags:
      - 战斗
      - 短句
      - 力量感

  - id: description_scene_001
    title: 场景描写示例
    category: scene
    content: |
      夕阳将天空染成血红色，废墟的轮廓在余晖中显得格外锐利。
      远处传来城市的喧嚣声，像是另一个世界的呼唤。
      空气中弥漫着尘土和腐朽的气息。

      【分析】视觉听觉嗅觉结合，层次丰富
    tags:
      - 场景
      - 五感
      - 废墟
```

- [ ] **Step 3: 提交**

```bash
git add config/prompts/风格指南库/*.yaml config/prompts/示例库/*.yaml
git commit -m "feat: 添加风格指南和示例库"
```

---

### Task 9: 更新workflow_state_schema

**Files:**
- Modify: `novel-factory/10_方法论/PART6_工业流程/workflow_state_schema.md`

- [ ] **Step 1: 添加methodology_markers字段说明**

（在现有workflow_state_schema.md中添加CARE框架关联的methodology_markers字段说明）

- [ ] **Step 2: 提交**

```bash
git add 10_方法论/PART6_工业流程/workflow_state_schema.md
git commit -m "docs: 更新workflow_state_schema添加CARE框架关联"
```

---

## 实现完成检查

- [ ] 所有16个CARE模板已创建
- [ ] 模板索引文件完整
- [ ] 提示词组装工具可运行
- [ ] 测试通过
- [ ] 风格指南和示例库已创建
- [ ] workflow_state_schema已更新
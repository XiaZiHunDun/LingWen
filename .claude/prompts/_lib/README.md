# Prompt Builder - 提示词填充库

> 用于将提示词模板与项目数据关联，自动生成可用的prompt

---

## 核心功能

### 1. 自动生成脚本

提供了一个Python脚本，可自动从项目数据填充模板：

```bash
# 列出所有模板
python3 .claude/scripts/prompt_generator.py list-templates

# 生成章节写作prompt（输出到stdout）
python3 .claude/scripts/prompt_generator.py chapter-writer --chapter 25

# 生成章节写作prompt（输出到文件）
python3 .claude/scripts/prompt_generator.py chapter-writer --chapter 25 -o /tmp/prompt.md

# 生成质量检查prompt
python3 .claude/scripts/prompt_generator.py quality-check --chapter 25 -o /tmp/prompt.md
```

### 2. 项目数据获取

```python
# 从以下位置获取数据：
# 1. workflow_state.json - 项目状态、进度
# 2. 01_灵感库/{项目}/基础层.yaml - 基础设定
# 3. 01_灵感库/{项目}/深度层.md - 深度设定
# 4. 03_内容仓库/04_正文/chXXX.md - 章节内容
```

### 3. 模板填充流程

```
输入：章节号 + 模板类型
  ↓
获取：基础层.yaml + 深度层.md + workflow_state.json
  ↓
填充：将项目数据填入模板占位符
  ↓
输出：可直接使用的完整prompt
```

### 3. 关键填充参数

#### 章节写作 Prompt (chapter-writing-prompt)

| 占位符 | 数据来源 | 示例 |
|--------|----------|------|
| `{novel_title}` | 基础层.yaml | 《星陨纪元》 |
| `{chapter_number}` | 输入参数 | 025 |
| `{genre}` | 基础层.yaml | 玄幻修真 |
| `{style}` | 基础层.yaml | 冷峻写实，废土朋克风 |
| `{word_count}` | 深度层.md（单章字数） | 3000 |
| `{chapter_type}` | 根据章节位置判断 | 开篇/发展/高潮/收尾/过渡 |
| `{volume}/{phase}` | workflow_state.json | volume_1/PHASE_3 |
| `{character_list}` | 深度层.md（多线叙事设计） | 林夜、苏琳、铁蛋、莫言 |
| `{character_states}` | 根据章节推断 | - |
| `{scene_type}` | 根据情节推断 | - |
| `{atmosphere}` | 深度层.md（风格指南） | 冷峻写实 |

---

## 作家部门模板使用指南

### 第一步：确定章节上下文

```bash
# 查看章节范围
# ch001-ch120 = 卷1（废土求生）
# ch121-ch240 = 卷2（星际博弈）
# ch241-ch360 = 卷3（永恒守护）
```

### 第二步：加载基础层数据

```yaml
# 基础层.yaml 关键信息
novel_title: 《星陨纪元》
type:
  primary: 玄幻修真
  secondary: 废土生存、星际联盟
  tone: 冷峻写实，带废土朋克风
core_theme: "守护的意义..."
main_characters:
  - 林夜: 废土少年，父母死于暗域追杀
  - 苏琳: 预言能力者，被星辰会追杀
  - 铁蛋: 废土机械师，实用主义者
  - 莫言: 万剑宗剑修，沉默寡言
target_audience: 18-35岁
style_guide:
  language_style: 现代简洁，带古风韵味
  pacing: 快节奏，情节紧凑
  dialogue_ratio: 30%
 禁忌设定: 不写降智反派、不注水、不圣母主角
```

### 第三步：加载深度层数据

```markdown
# 深度层.md 关键信息

## 世界观
- 境界划分：粒子境→星火境→脉冲境→裂变境→黑洞境→创世境→永恒境
- 核心势力：星辰会、玄机阁、万剑宗、星际修真联盟

## 时间线
- T1: 林夜出生（暗域入侵后第37年）
- T2: 父母死于暗域追杀（暗域入侵后第52年）
- ...

## 伏笔设计
- VP_001: 林夜父母死因 → ch360揭示
- ...

## 叙事结构
- 卷1（ch001-ch120）：废土求生
- 卷2（ch121-ch240）：星际博弈
- 卷3（ch241-ch360）：永恒守护

## 视角规范
- 主视角（80%）：林夜
- 辅助视角（15%）：苏琳、暗皇、铁蛋
- 视角转换规则：每章不超过2次
```

---

## 实际使用示例

### 为 ch025 生成写作 prompt

**输入**：
- 章节号：025
- 前情：林夜已经在废土生存了三个月，遇见苏琳
- 当前章节目标：林夜与苏琳相遇

**填充后的 prompt 片段**：

```markdown
# 章节正文写作任务

你是《星陨纪元》的专职作家。请根据以下信息创作第25章正文。

## 一、作品基础信息
- **作品类型**：玄幻修真
- **作品风格**：冷峻写实，带废土朋克风
- **章节字数**：3000字（±10%）

## 二、章节上下文
- **卷/阶段**：卷1 / 发展阶段
- **章节类型**：发展
- **前情概要**：林夜独自在废土生存三个月...
- **本章核心目标**：林夜与苏琳相遇

## 三、主要角色信息
- **林夜**：废土少年，性格冷峻内敛，复仇心切
- **苏琳**：预言能力者，被星辰会追杀，温柔坚定

## 四、场景设定
- **场景类型**：废土废墟
- **时间**：冬天，三个月后
- **地点**：废墟角落
- **氛围要求**：冷峻、压抑、带一丝希望

## 五、质量标准
- 情节推进：必须包含林夜与苏琳的相遇
- 角色互动：体现两人性格的碰撞
- 情感深度：苏琳作为"锚点"的初现
```

---

## 模板文件索引

| 部门 | 模板文件 | 用途 |
|------|----------|------|
| 作家 | `writer/chapter-writing-prompt.md` | 章节正文写作 |
| 作家 | `writer/scene-description-prompt.md` | 场景描写 |
| 作家 | `writer/dialogue-generation-prompt.md` | 对话生成 |
| 作家 | `writer/chapter-revision-prompt.md` | 章节修改 |
| 审核 | `reviewer/quality-check-prompt.md` | 综合质量检查 |
| 审核 | `reviewer/consistency-check-prompt.md` | 情节一致性 |
| 审核 | `reviewer/character-behavior-check-prompt.md` | 人物行为 |
| 灵感 | `inspiration/type-analysis-prompt.md` | 类型分析 |
| 灵感 | `inspiration/worldbuilding-prompt.md` | 世界观设计 |
| 灵感 | `inspiration/character-inspiration-prompt.md` | 角色灵感 |
| 读者 | `reader/reader-feedback-analysis-prompt.md` | 反馈分析 |
| 读者 | `reader/emotional-reaction-analysis-prompt.md` | 情感反应 |
| 主控 | `coordinator/task-allocation-prompt.md` | 任务分配 |
| 主控 | `coordinator/deadlock-resolution-prompt.md` | 死锁处理 |
| 汇总 | `summary/version-integration-prompt.md` | 版本整合 |
| 汇总 | `summary/final-verdict-prompt.md` | 终稿判定 |
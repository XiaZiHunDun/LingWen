---
skill_name: inspiration-generator
department: inspiration-dept
model: sonnet
trigger_phrases:
  - /inspiration
  - "generate inspiration"
  - "生成立项文件"
---

name: inspiration-generator
description: |
  灵感生成Skill。当用户说"生成灵感"、"创造新灵感"、"想一个新的创意"时使用此技能。

  适用场景：
  - 新项目启动时需要灵感输入
  - 灵感枯竭需要创意刺激
  - 类型题材选择困难

  不适用：具体的写作任务（请用writer-dept的技能）
---

# 灵感生成 Skill

## 功能

为小说项目生成创意灵感，包括类型定位、核心冲突、卖点提炼等。

---

## 方法论嵌入（重要）

灵感生成后，必须经过筛选评估，参照 `10_方法论/01_灵感捕捉与筛选.md` 和 `10_方法论/02_核心三要素.md`。

### 筛选标准（任一即可动笔）

1. **有强烈冲突**：人vs人 / 人vs命运 / 人vs社会 / 人vs自己
2. **有"反差"**：身份与性格 / 目标与阻碍 / 表面与真相
3. **有情绪价值**：能让你自己生气/心疼/兴奋/害怕

### 一句话故事模板

```
谁（主角）+ 想要什么（目标）+ 但遇到什么阻碍（核心冲突）+ 如果失败会怎样（代价）
```

### 核心三要素模板

```yaml
主角:
  身份: ...
  性格: ...
  执念/短板: ...
目标:
  具体描述: ...
  贯穿全书: true/false
阻碍:
  类型: 外在反派 / 自身缺陷 / 社会环境
  具体描述: ...
代价:
  如果失败会怎样: ...
```

---

## 灵感部门分工

| 角色 | 专项 |
|------|------|
| 灵感A | 类型/冲突/卖点 |
| 灵感B | 世界观/力量体系 |
| 灵感C | 时间线/伏笔/叙事 |

---

## 输出结构

### 基础层.yaml

```yaml
type: 玄幻
theme: 星际废土
core_conflict: 生存vs守护
selling_points:
  - 废土生存
  - 星际探险
audience: 16-25岁男性

# 方法论新增字段
inspiration_check:
  has_conflict: true
  has_contrast: true
  has_emotion: true
one_sentence_story: "..."
core_three_elements:
  protagonist: "..."
  goal: "..."
  obstacle: "..."
```

### 深度层.md

```markdown
## 世界观
...

## 时间线
...

## 伏笔布局
...

## 核心三要素设计
### 主角设计
### 目标设计
### 阻碍设计
```

---

## 调度命令

```bash
./run_inspiration.sh generate <类型>   # 生成灵感
./run_inspiration.sh integrate <项目> # 主编整合
./run_inspiration.sh status            # 查看进度
```

---

## 提示词模板

灵感生成时可参考：
- `.claude/prompts/inspiration/type-analysis-prompt.md` - 类型分析与卖点提炼
- `.claude/prompts/inspiration/worldbuilding-prompt.md` - 世界观设计
- `.claude/prompts/inspiration/character-inspiration-prompt.md` - 角色灵感生成

## 文件位置

- 灵感库：`01_灵感库/`
- 模板库：`01_灵感库/模板库/`
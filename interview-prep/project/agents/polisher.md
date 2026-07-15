# polisher · 润色 Agent

> **一句话定位**：**20 个读者角色扮演 + 找"AI 味"和套话**，比 writer 多一道。
> **技术标签**：读者视角 · AI 味检测 · 套话清理

---

## 1 · 核心职责

- 输入：初稿 + 审核报告
- 输出：润色稿（保留情节、优化文笔）
- 关键产出：**治"AI 味"**——找套话 / 找重复 / 找生硬

---

## 2 · 最有意思的设计决策：**20 个读者角色扮演**

### 问题

content_writer 写完后，章节还有"AI 味"——套话（"她心中涌起一股暖流"）、生硬（"他的眼神如同深邃的星空"）、重复（每章都有"心跳漏了一拍"）。

单一润色 prompt 效果差——LLM 不知道"什么是 AI 味"。

### 解决方案：读者角色池（**比作家更多样**）

```
.skills/reader-dept/
├── reader-a/SKILL.md    # 挑剔中年男 · 抓逻辑漏洞
├── reader-b/SKILL.md    # 文艺女青年 · 抓文笔
├── reader-c/SKILL.md    # 网文老白 · 抓套话
├── reader-d/SKILL.md    # 推理迷 · 抓伏笔
├── ...
└── reader-t/SKILL.md    # 新手读者 · 抓可读性
```

### 20 个角色 vs 10 个作家——**为什么更多？**

| 维度 | 作家（10） | 读者（20） |
|---|---|---|
| **目的** | 写出来 | 找毛病 |
| **多样性需求** | 中（不同章节用不同作家） | **高**（一个章节要多个视角找问题） |
| **角色相似代价** | 风格撞车 | 漏检问题 |

**所以读者池是作家的 2 倍**——**多视角才能找全问题**。

### 多读者投票机制

```python
def polish(chapter: str, issues: list[Issue]) -> str:
    # 1. 多读者独立润色
    polished_versions = []
    for role in random.sample(READER_ROLES, 5):  # 随机抽 5 个读者
        polisher = PolisherAgent()
        polisher.switch_role(role)
        polished = polisher.run(chapter, issues)
        polished_versions.append((role, polished))

    # 2. 投票（哪个版本问题最少）
    best = vote(polished_versions, criterion="fewest_issues")

    return best
```

---

## 3 · "AI 味" 检测规则（**硬编码**）

### 套话词典

```python
# infra/polisher/ai_gloss_dictionary.py
AI_GLOSS_PHRASES = [
    "心中涌起一股暖流",
    "心跳漏了一拍",
    "眼神如同深邃的星空",
    "嘴角勾起一抹微笑",
    "空气中弥漫着紧张的气氛",
    "时间仿佛静止了",
    "思绪如同潮水般涌来",
    # ... 200+ 常见 AI 套话
]
```

### 检测逻辑

```python
def check_ai_gloss(chapter: str) -> list[Issue]:
    issues = []
    for phrase in AI_GLOSS_PHRASES:
        if phrase in chapter:
            issues.append(Issue(
                type="ai_gloss",
                quote=phrase,
                severity="P1",
                fix_suggestion=f"删除或改写：'{phrase}'"
            ))
    return issues
```

**效果**：8 本样章套话清理 **95%+**。

---

## 4 · 数字 & 对比

| 指标 | 无润色 | polisher | 提升 |
|---|---|---|---|
| "AI 味"套话密度 | 5-8 个 / 千字 | **<0.5 个 / 千字** | 降 10× |
| LLM judge 总分 | 3.5/5.0 | **4.5+/5.0** | +28% |
| 重复句式 | 12% | **<3%** | 降 4× |
| 可读性（句子长度多样性） | 70% | **90%+** | +20% |

---

## 5 · 1 个数字（**面试时直接说**）

> "灵文 8 本样章，**'AI 味'套话 <0.5 个/千字**——靠 polisher 的 20 个读者角色扮演 + 200+ 套话词典。**读者池是作家池的 2 倍**——因为**多视角才能找全问题**。这是治'AI 味'的最后一道关。"

---

## 6 · 白板画图提示

```
┌─────────────────┐
│   content_      │
│   writer 初稿    │
└────────┬────────┘
         ↓
┌─────────────────┐
│   auditor       │  ← S1-S11 评分 + 问题清单
│   审核报告      │
└────────┬────────┘
         ↓
┌─────────────────┐
│ 读者角色池       │
│ reader-a~t ×20  │  ← 随机抽 5 个
└────────┬────────┘
         ↓ 多版本
┌─────────────────┐
│ 投票选最佳      │  ← 哪个版本问题最少
└────────┬────────┘
         ↓
┌─────────────────┐
│   润色稿        │  ← 套话 <0.5 个/千字
└─────────────────┘
```

**讲法**：
> "polisher 不是简单润色——是**20 个读者角色扮演 + 投票**。一个章节随机抽 5 个读者独立润色，然后投票选'问题最少'的版本。**读者池是作家池的 2 倍**——因为**多视角才能找全问题**。**200+ 套话词典**做硬编码清理，'AI 味'从 5-8 个/千字降到 <0.5 个/千字。"

---

## 7 · 配套文件

- `infra/agent_system/agents/polisher/` — 代码路径
- `.skills/reader-dept/*/SKILL.md` — 20 个读者角色配置
- `infra/polisher/ai_gloss_dictionary.py` — 200+ 套话词典
- `project/04-deep-dives.md` 4.5 — 提示词工程（含套话清理 prompt）

# content_writer · 写作 Agent

> **一句话定位**：**10 个作家角色 + switch_role 切档**，专门治"AI 味"。
> **技术标签**：角色池 · 风格切换 · RAG 检索

---

## 1 · 核心职责

- 输入：大纲 + 角色卡 + 前情摘要
- 输出：章节正文（3000-5000 字）
- 关键产出：**风格可控**——不同作家角色不同风格

---

## 2 · 最有意思的设计决策：角色池机制（**治"AI 味"工程方案**）

### 问题

单 Agent 写出来**风格单一**——10 本书读起来像 1 个人写的（"AI 味"重）。
LLM-as-Judge 早期评分 3.0/5.0（不达标）。

### 解决方案：作家角色池

```python
# 切档示例
writer = ContentWriterAgent()

# 写悬疑章——切到擅长推理的作家 D
writer.switch_role("writer_d")
chapter = writer.run(outline, character_card)

# 写感情章——切到擅长细腻的作家 B
writer.switch_role("writer_b")
chapter = writer.run(outline, character_card)
```

### 角色池配置（**独立 SKILL.md**）

```
.skills/writer-dept/
├── writer-a/SKILL.md    # 风格：热血 / 直接 / 短句
├── writer-b/SKILL.md    # 风格：细腻 / 缓慢 / 长句
├── writer-c/SKILL.md    # 风格：冷峻 / 克制 / 反讽
├── writer-d/SKILL.md    # 风格：悬疑 / 推理 / 多线
├── ...
└── writer-j/SKILL.md    # 风格：幽默 / 跳跃 / 网络梗
```

每个 `SKILL.md` 含：
- **风格标签**（热血 / 细腻 / 冷峻 / 悬疑）
- **句式偏好**（短句 / 长句 / 倒装）
- **禁用词**（不用套话 / 不用 AI 味套话）
- **代表作品风格**（参考作家 / 作品）

### 切换触发

按章节类型自动切换：
- 推理章 → `writer_d`（悬疑）
- 感情章 → `writer_b`（细腻）
- 战斗章 → `writer_a`（热血）
- 日常章 → `writer_j`（幽默）

**不是手工切换**——由 outline_master 标注章节类型 + content_writer 自动匹配。

---

## 3 · RAG 检索前情（**保证跨章一致性**）

```python
def build_context(chapter_no: int, character_card: dict) -> str:
    # 1. 检索前 10 章相关片段
    related = qdrant.search(
        collection="chapters",
        query_vector=embed(chapter_outline),
        limit=10,
        filter={"chapter_no": {"$lt": chapter_no}},
    )
    # 2. 检索角色卡
    character_ctx = qdrant.retrieve("characters", character_card["name"])
    # 3. 拼装 prompt
    return f"""
    【前情摘要】{summarize(related)}
    【角色卡】{character_ctx}
    【本章大纲】{chapter_outline}
    """
```

**WHY 前情是 RAG 不是塞全文**：
- 单章 context 限制 ~16K token
- 塞全文会爆炸
- RAG 检索只取相关片段

---

## 4 · 数字 & 对比

| 指标 | 单 Agent 固定 prompt | content_writer + 角色池 | 提升 |
|---|---|---|---|
| 风格多样性 | 1 种（10 本同质） | **10 种**（每本不同） | 质变 |
| "AI 味"评分 | 3.0/5.0 | **4.5+/5.0** | +50% |
| LLM judge 总分 | 3.0/5.0 | **4.0+/5.0** | +33% |
| 单章成本 | $0.05（GPT-3.5） | **$0.063**（MiniMax，质量更高） | 持平 |

---

## 5 · 1 个数字（**面试时直接说**）

> "灵文 8 本样章，**LLM judge 7/7 ≥ 4.0**（满分 5）——靠 content_writer 的 10 个作家角色池 + switch_role 切档。**这不是 prompt trick**，是独立 SKILL.md 配置 + 按章节类型自动匹配。**这是治'AI 味'的工程方案**。"

---

## 6 · 白板画图提示

```
┌─────────────┐
│ 章节类型    │
│ 推理/感情/  │
│ 战斗/日常   │
└──────┬──────┘
       ↓ 自动匹配
┌─────────────────────────────┐
│       作家角色池            │
│  writer_a  writer_b  ...    │
│  (热血)  (细腻)    (幽默)  │
└──────┬──────────────────────┘
       ↓ switch_role
┌─────────────────────────────┐
│  RAG 检索（Qdrant）         │
│  + 角色卡注入                │
└──────┬──────────────────────┘
       ↓
┌─────────────────────────────┐
│  章节正文（3000-5000 字）   │
└─────────────────────────────┘
```

**讲法**：
> "写作不是单 Agent 一段 prompt——是**作家角色池**。10 个作家角色，每个独立 SKILL.md。按章节类型自动匹配：推理章用 writer_d（悬疑），感情章用 writer_b（细腻）。**这就是治'AI 味'的工程方案**——LLM judge 评分从 3.0 提到 4.0+。"

---

## 7 · 配套文件

- `infra/agent_system/agents/content_writer/` — 代码路径
- `.skills/writer-dept/*/SKILL.md` — 10 个作家角色配置
- `infra/memory_system/` — Qdrant RAG 检索
- `project/04-deep-dives.md` 4.5 — 提示词工程（含角色池 prompt 设计）

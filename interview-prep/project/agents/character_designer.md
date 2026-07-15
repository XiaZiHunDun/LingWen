# character_designer · 角色设计 Agent

> **一句话定位**：**6 维角色档案**（性格 / 语气 / 能力 / 知识 / 禁忌 / 反差），存为知识图谱。
> **技术标签**：结构化 prompt · 知识图谱 · 跨章一致性

---

## 1 · 核心职责

- 输入：角色名 / 题材 / 主角或配角定位
- 输出：6 维角色卡 JSON
- 关键产出：**知识图谱化**——角色间关系（师徒 / 对手 / 亲人）一并生成

---

## 2 · 6 维角色档案（**最有意思的设计**）

```json
{
  "name": "陆沉",
  "personality_tags": ["冷静", "克制", "决断"],
  "speech_style": "简短有力，少用形容词",
  "abilities": ["沙漠生存", "机械维修"],
  "knowledge": ["民国地理", "方言"],
  "forbids": ["不近女色", "不信神佛"],
  "opposites": {
    "鲁莽": "陆沉做事从不鲁莽",
    "多话": "陆沉话少，一句是一句"
  }
}
```

### 6 维含义

| 维度 | 用途 | 示例 |
|---|---|---|
| **personality_tags** | PersonalityChecker 检测性格漂移 | ["冷静", "克制"] |
| **speech_style** | content_writer 写对话 | "简短有力" |
| **abilities** | AbilityChecker 检测能力越界 | "陆沉不能飞" |
| **knowledge** | KnowledgeChecker 检测知识越界 | "民国人不能知道核物理" |
| **forbids** | 触发即返工 | "陆沉不近女色 → 写感情戏返工" |
| **opposites** | 反义词触发检测 | "陆沉做事从不鲁莽 → 鲁莽场景返工" |

---

## 3 · 最有意思的设计决策：**标准化 schema + 兼容性归一化**

### 问题（**最难的 Bug 来源**）

character_profiles 有 **3 种数据格式**（list / dict / object），不同章节用不同格式：
- `outline_master` 早期输出 dict 格式
- `character_designer` v8 输出 list 格式
- `content_writer` 输出 object 格式

下游 PersonalityChecker / CharacterChecker 必须兼容 3 种。

### 解决方案

```python
# 兼容性归一化（检测器侧）
def _normalize_profiles(raw_profiles):
    if isinstance(raw_profiles, list):
        return raw_profiles
    elif isinstance(raw_profiles, dict):
        return raw_profiles.get('characters', [])
    elif hasattr(raw_profiles, '__iter__'):
        return list(raw_profiles)
    else:
        return []
```

**教训**：所有外部输入（角色卡 / 前情 / 伏笔）都要支持 2-3 种格式，**不信上游，做边界归一化**。

---

## 4 · 数字 & 对比

| 指标 | 无角色卡 | character_designer | 提升 |
|---|---|---|---|
| 性格漂移率 | 25% | **<1%** | 降 25× |
| 能力越界率 | 15% | **<1%** | 降 15× |
| 知识越界率 | 10% | **<1%** | 降 10× |
| 对话风格一致 | 70% | **90%+** | +20% |

---

## 5 · 1 个数字（**面试时直接说**）

> "灵文 8 本样章，**0 例跨章角色性格漂移**——靠 character_designer 的 6 维角色卡 + 检测器兼容性归一化。**这是工程方案，不是 prompt trick**——每个维度都对应下游检测器的硬错拦截。"

---

## 6 · 白板画图提示

```
       ┌──────────────────┐
       │ character_       │
       │ designer         │
       └────────┬─────────┘
                ↓ 输出 6 维 JSON
       ┌──────────────────┐
       │  knowledge       │  ← 存到 Qdrant + JSON
       │  graph           │
       └────────┬─────────┘
                ↓
       ┌──────────────────┐
       │ RAG 检索         │  ← content_writer 写前先查
       │ + 检测器         │  ← PersonalityChecker / CharacterChecker
       └──────────────────┘
```

**讲法**：
> "角色卡不是简单描述——是**结构化知识图谱**。每个维度都对应下游检测器的硬错拦截：性格 → PersonalityChecker，能力 → AbilityChecker，知识 → KnowledgeChecker。**这就是为什么跨章一致性 90%+**——6 维结构 + 11 维检测器配合。"

---

## 7 · 配套文件

- `infra/agent_system/agents/character_designer/` — 代码路径
- `infra/consistency/checkers/` — S9 角色一致性检测器
- `infra/consistency/checkers/llm_enhanced/character.py` — LLM 增强版
- `project/04-deep-dives.md` 4.6 — 最难 Bug（ch241-300 格式兼容性）

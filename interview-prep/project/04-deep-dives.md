# 04 · 灵文 6 大技术深度（面试深讲用）

> **用法**：每个深度 3-5 分钟，可单独挑讲。按"⭐ 优先级"选讲。
> **核心**：6 大深度 = STAR+L 的"A 栏"核心，面试官刨根问底的区域。

| 优先级 | 深度点 | 时长 |
|---|---|---|
| ⭐⭐⭐ | 4.1 Multi-Agent 架构 | 5 min |
| ⭐⭐⭐ | 4.3 记忆机制（RAG + WorldSnapshot） | 5 min |
| ⭐⭐ | 4.4 工具调用 + 幻觉处理 | 3 min |
| ⭐⭐ | 4.6 最难 Bug（角色一致性） | 3 min |
| ⭐ | 4.5 提示词工程 | 2 min |
| ⭐ | 4.2 框架选型 | 2 min |

---

## 4.1 · 架构范式：Multi-Agent 协同 + GoT 路由（**必讲**）

### 决策

**不用 LangChain ReAct 单 Agent，而是 5 Agent + GoT Router + 12 SCENARIOS 解耦**。

### WHY（**选型理由**）

1. **网文是多步 pipeline**：大纲→角色→正文→审核→润色。**单 Agent 上下文会爆炸**（4-5 步后效果断崖）
2. **职责分离**：每个 Agent 是独立可替换的"零件"，不是粘在一起的怪物
3. **角色池切换**：不同章要不同作家风格（悬疑章用 `writer_d`，感情章用 `writer_b`），单 Agent 做不到
4. **可观测性**：每步走 SQLite 持久化，重启可恢复（`workflow.db` + checkpoint）

### 架构（5 Agent + GoT Router）

```
用户输入
   ↓
MasterController
   ↓
GoT Router（12 SCENARIOS）
   ↓              ↓              ↓              ↓              ↓
outline_master → character_designer → content_writer → auditor → polisher
                                                ↓
                                              质量门 S1-S11
                                                ↓
                                            SQLite 持久化
```

### 关键代码路径

- MasterController：`infra/agent_system/master_controller.py`
- GoT Router：`infra/agent_system/got_bridge.py:SCENARIO_HANDLERS`（12 个 SCENARIO → handler 映射）
- Agent 基类：`infra/agent_system/agents/base.py`
- LLM Mixin：`infra/agent_system/agents/mixins.py`

### 12 SCENARIOS 速查

```
chapter_writing        # 主写作
chapter_review         # 主审核
polish_emotional_pacing # 情感润色
polish_dialogue        # 对话润色
polish_ai_gloss        # 去 AI 味
cascade_preview        # CVG 涟漪预览
cascade_execute        # CVG 涟漪执行
character_design       # 角色设计
outline_generation     # 大纲生成
foreshadow_check       # 伏笔检测
consistency_audit      # 一致性审核
quality_gate           # 综合质量门
```

### 角色池机制（**核心设计**）

```python
# 切换角色（content_writer 切到擅长感情线的作家 B）
writer = ContentWriterAgent()
writer.switch_role("writer_b")
chapter = writer.run(outline, character_card)
```

- **配置位置**：`.skills/writer-dept/writer-b/SKILL.md`（每个角色 1 个 SKILL.md）
- **40 个角色**：作家 A-J × 10 + 审核员 A-J × 10 + 读者 A-T × 20

### Trade-off

- **优点**：职责分离 / 可观测 / 可替换 / 中文场景
- **代价**：开发慢 2-3 个月（vs LangChain），跨 Agent 通信要手动协调

---

## 4.2 · 框架与底层（**选讲**）

### 决策

**纯手写 5 Agent + 自研 `infra/ai_service/` 抽象层**，不用 LangChain / AutoGen / LlamaIndex / CrewAI。

### WHY（重复但核心）

- 角色池 / 12 SCENARIOS / 中文工具描述 → 框架硬塞会变形
- 可控 > 省事（详 FAQ Q1）

### `ai_service/` 抽象层设计

```
LLMProvider (ABC)
├── OpenAIProvider
├── AnthropicProvider
└── MiniMaxProvider
   ↓
LLMRouter（按 tier 路由：cheap/mid/premium）
   ↓
AgentBase.mixin (LLM 调用 + 状态持久化)
   ↓
MasterController / got_bridge
```

- **5 层真实 token 跟踪**：不估算，每层都记录
- **per-tier budget**：每个 tier 单独预算 + 熔断
- **3 Provider 降级互备**：一家挂了切另一家

### 关键代码

```python
# infra/ai_service/router.py 简化版
class LLMRouter:
    def __init__(self):
        self.providers = {
            "cheap": MiniMaxProvider(),
            "mid": OpenAIProvider(),
            "premium": AnthropicProvider(),
        }
        self.budgets = {"cheap": 0.05, "mid": 0.20, "premium": 1.00}

    def call(self, prompt: str, tier: str = "cheap") -> LLMResponse:
        if self.budgets[tier] <= 0:
            tier = self._fallback_tier(tier)
        provider = self.providers[tier]
        return provider.call(prompt)
```

### Trade-off

- **优点**：可控 / 可观测 / 中文场景 / 3 Provider 降级
- **代价**：手写一切，2-3 个月工期

---

## 4.3 · 记忆机制（RAG + WorldSnapshot）（**必讲**）

### 3 层记忆

| 层 | 存储 | 用途 | 延迟 |
|---|---|---|---|
| **短期** | Agent context window | 当前章节上下文 | 0（in-memory） |
| **长期（RAG）** | Qdrant 向量库 | 历史章 / 角色卡 / 伏笔 | <500ms（在线）/ <100ms（NoOp） |
| **世界状态** | WorldSnapshot（JSON） | 矛盾检测 / 状态追踪 | 0.03ms/scan |

### 短期记忆：Context Window 管理

- **每 Agent 独立 context**：不共享（避免污染）
- **Token 预算**：每 Agent 配置 `max_tokens`，超了截断 + 摘要
- **关键技巧**：前情摘要 → RAG 检索 → 角色卡注入（不是塞整个历史章）

### 长期记忆：Qdrant RAG + NoOp 降级

```python
# 章节生成前的 RAG 检索
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

- **数据量**：8 本样章 + 360 章正史 + 角色卡 → ~XX MB（待校核）
- **离线降级**：Qdrant 不可用时走 NoOp（内存检索），**开发机零依赖**

### 世界状态：WorldSnapshot（**最有意思的设计**）

- 路径：`infra/world_model/`
- 数据结构：`@dataclass(frozen=True)` + `to_dict/from_dict`（不可变）
- 节点类型：人物 / 物品 / 地点 / 事件
- 关系：LOCATED_IN / DESTROYED / TRANSFORMED 等

**矛盾检测算法（N²）**：

```python
# 关键代码（简化）
def detect_contradictions(snapshot: WorldSnapshot) -> list[Contradiction]:
    contradictions = []
    nodes = snapshot.nodes
    for n1 in nodes:
        for n2 in nodes:
            if n1.id == n2.id:
                continue
            # LOCATED_IN_DESTROYED: 角色在已毁场景
            if (n1.type == "character" and n2.type == "location"
                and n1.relations.get("LOCATED_IN") == n2.id
                and n2.status == "destroyed"):
                contradictions.append(Contradiction(
                    kind="LOCATED_IN_DESTROYED",
                    nodes=[n1.id, n2.id],
                ))
    return contradictions
```

- **性能**：N=100 节点时 **0.03ms/scan**（N² = 10⁴），300× 优于 10ms 目标
- **场景**：写章节前先 snapshot，避免"角色在已毁场景出现"这种穿帮

### Trade-off

- **优点**：3 层职责清晰 / 离线友好 / 矛盾检测自动化
- **代价**：WorldSnapshot N² 算法，N > 500 要换邻接表（Phase 14.0 P2 已优化）

---

## 4.4 · 工具调用 + 幻觉处理（**强烈推荐**）

### 工具总数

```
规则检测器（S1-S8）：8 个
LLM 增强检测器（S9-S11）：7 个（Phase 9.11）
CLI 工具：~20 个
────────────────
合计：~35 个工具
```

### 3 道防线（**治幻觉核心**）

#### 防线 1：JSON Schema 强校验

```python
# infra/agent_system/agents/base.py 简化
def parse_response(self, raw: str) -> dict:
    # 1. 剥离 markdown fenced JSON
    cleaned = strip_markdown_json(raw)
    # 2. Schema 验证
    try:
        return ToolCallSchema.parse_raw(cleaned)
    except ValidationError as e:
        # 3. 失败重试（注入错误到 prompt）
        raise RetryableError(f"JSON 格式错: {e}")
```

- **效果**：8 本样章跑下来 0 次"调用不存在的工具"

#### 防线 2：工具白名单

```python
# 工具注册表
ALLOWED_TOOLS = {
    "outline_generation": OutlineTool,
    "character_design": CharacterTool,
    "chapter_writing": WritingTool,
    "chapter_review": AuditTool,
    # ... 35 个
}

def invoke_tool(name: str, params: dict):
    if name not in ALLOWED_TOOLS:
        raise HallucinationError(f"工具 {name} 不在白名单")
    return ALLOWED_TOOLS[name](**params)
```

- **WHY**：LLM 可能编造工具名（"调用 `search_database`"），白名单直接拒

#### 防线 3：重试 + Fallback

```
LLM 调用失败
   ↓
重试 3 次（不同 prompt 变体）
   ↓
仍失败？
   ↓ Yes
降级到规则引擎（S1-S8 替代 S9-S11）
   ↓
规则也失败？
   ↓ Yes
标 P0，人工介入
```

- **生产可用性**：LLM 服务挂了 → 规则顶上，**生产不中断**

### Trade-off

- **优点**：3 道防线严密 / Fallback 保生产
- **代价**：每次调用多 50-100ms 校验开销（可接受）

---

## 4.5 · 提示词工程（**选讲**）

### 得意 System Prompt（auditor 的 S9-S11 模板）

```python
# infra/consistency/llm_service/prompts/character_consistency.py
SYSTEM_PROMPT = """你是一位严苛的网文审核员，专精角色一致性。

【任务】
给定章节正文和角色卡，判断是否存在角色性格漂移、知识越界、能力错配。

【角色卡】
{character_card}

【章节正文】
{chapter_text}

【输出格式】（严格 JSON）
{
  "consistent": true/false,
  "issues": [
    {"severity": "P0/P1/P2", "quote": "原文片段", "reason": "理由"}
  ]
}

【判断标准】
- P0: 明确性格反转 / 知识越界（如凡人知道仙界秘密）
- P1: 语气漂移 / 行为不一致
- P2: 轻微偏差，可接受

【注意】
- 只输出 JSON，不要解释
- 找不到问题输出 {"consistent": true, "issues": []}
"""
```

### 关键技巧

1. **角色注入**："你是一位严苛的网文审核员" — 设人设
2. **Few-shot**：附 3-5 个正反例（good / bad）
3. **JSON 输出约束**：显式 schema + 解析重试
4. **角色池切档**：`switch_role("auditor_e")` 替换整个 prompt

### Few-shot vs Zero-shot

- **S1-S8 规则**：Zero-shot（规则不依赖 LLM）
- **S9-S11 LLM 增强**：Few-shot（附 49 个 case，`tests/consistency/test_llm_enhanced/`）
- **质量 / 成本 trade-off**：Few-shot 提升质量但增 token（每次 +200 token，~$0.001）

### 自动 Prompt 优化

- **没有**（**这是反思点**）
- 人工调优 + 7 书 LLM judge ≥ 4.0 验证
- **未来**：想做但 ROI 不高，prompt 调优成本可控

### Trade-off

- **优点**：技巧成熟 / Few-shot 提升质量
- **代价**：prompt 版本管理靠人工，**没有自动优化**

---

## 4.6 · 最难的 Bug：跨章角色一致性崩坏（**强烈推荐**）

### Bug 现象

**Phase 8.5 · ch241-300 集中报错**：PersonalityChecker 在 60 章内全部返回错误，无法生成质检报告。

### 根因（**5 Whys**）

1. **Why 1**：PersonalityChecker 报"性格词冲突"
2. **Why 2**：检测逻辑是 "character_profiles['characters']"，但传入数据**不是 dict 而是 list**
3. **Why 3**：character_profiles 有 **3 种数据格式**（list / dict / object），不同章节用不同格式
4. **Why 4**：character_designer 早期按 dict 输出，后期切到 list（**没有协议约束**）
5. **Why 5**：**检测器没有"格式归一化"层**，信任上游数据格式

### 修复（**兼容性归一化**）

```python
# infra/consistency/checkers/personality_checker.py
def _normalize_profiles(raw_profiles):
    """兼容性归一化：list / dict / object 三种格式自动归一"""
    if isinstance(raw_profiles, list):
        return raw_profiles
    elif isinstance(raw_profiles, dict):
        return raw_profiles.get('characters', [])
    elif hasattr(raw_profiles, '__iter__'):
        return list(raw_profiles)
    else:
        return []
```

- **修复 commit**：`xxx` （待补 commit hash，HANDOFF §5 查具体编号）
- **效果**：ch241-300 重新跑通，0 误报

### 教训（**4 条**）

1. **检测器设计原则**：**不信上游，做边界归一化**
2. **数据格式兼容性**：所有外部输入（角色卡 / 前情 / 伏笔）都要支持 2-3 种格式
3. **检测器独立运行 vs 需要上下文**：上下文缺失要 fallback，**不能崩**
4. **统一基类协议**：所有 Agent 输出走 Pydantic schema，**不允许 list/dict 混用**

### 类似 Bug 复盘

| Bug | 根因 | 修复 |
|---|---|---|
| ch241-300 性格检测 | 格式不兼容 | 归一化层 |
| Qdrant 查询 client 1.18+ 不兼容 | API 变更 | `query_points` 替代 |
| Cascade 7× 慢（Phase 14.0 P2） | O(N²) 算法 | 邻接表 O(1) |
| Qdrant async 4.89× 慢（Phase 14.0 P2） | 同步阻塞 | `to_thread` 包装 |

### Trade-off

- **修复**：归一化层（10 行代码）
- **代价**：早期数据要回填（ch241-300 重新检测）

---

## 配套文件

- `diagrams/02-agent-orchestration.mmd` — 4.1 配套图（Agent + GoT 路由细节）
- `diagrams/03-quality-pipeline.mmd` — 4.4 配套图（11 维流水线）
- `diagrams/06-cross-volume-ripple.mmd` — 4.3 配套图（CVG 跨卷涟漪）

---

## 面试节奏建议

```
总时长 30 min：
- 自我介绍：3 min
- 整体架构（02）：5 min + 主图
- 6 大深讲（按优先级）：18 min
  - 必讲：4.1 Multi-Agent + 4.3 记忆 = 10 min
  - 推荐：4.4 工具调用 + 4.6 最难 Bug = 6 min
  - 选讲：4.5 提示词 + 4.2 框架 = 2 min
- 收尾 + 反思（06/07）：4 min
```

如果只剩 15 min：**只讲 4.1 + 4.6**（最有故事性的两个）。

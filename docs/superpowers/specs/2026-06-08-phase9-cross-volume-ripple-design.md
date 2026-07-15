# Phase 9 — 跨卷涟漪 (Cross-Volume Ripple) 设计

> **For agentic workers:** 本 spec 仅设计 (0 代码). 实施见 `2026-06-08-phase9-cross-volume-ripple-blueprint.md`.
> 配套: `2026-06-03-subplot-lifecycle-model-design.md` (Ripple 基础, 卷内).

## Context

**现状 (Phase 8.30 后 baseline 2262 passed 27 skipped)**:

- ✅ `Plot` / `PlotPurpose` / `PlotStatus` 6 态机 + 5 条上限 (Doc 2026-06-03, 主线/支线模型)
- ✅ `Ripple` 概念已就位 (origin_event → affected_nodes 卷内传播, Doc 2026-06-03 §五)
- ✅ L1/L2/L3 三层大纲 (主大纲 / 卷大纲 / 章大纲, 359 章用)
- ✅ 5 维 dashboard (cost / budget / radar / hook / chapter table, Phase 8.5-8.29)
- ❌ **0 跨卷引用图**: 多卷小说 V2 事件无法自动识别 V1 受影响段落, author 改 V2 → V1 引用漏改 → 角色复活 / 伏笔失联 / 设定矛盾
- ❌ **0 涟漪 review 流程**: 即使识别出来, 缺 UI 展示 impact + candidate diff + author confirm
- ❌ **0 回滚机制**: apply 错了需手动恢复, 误改成本高

**主公决策 (2026-06-08 AskUserQuestion)**:
- **范围**: 4 维全 (角色 / 伏笔 / 设定 / 主线 plot point)
- **触发**: 半自动 (LLM 扫后卷识别候选 → 列表 → author confirm → apply)

**目标**: 设计 1 跨卷引用图 (CrossVolumeReferenceGraph) + 1 半自动涟漪触发流程 (4 维) + 1 review UI + 1 rollback 机制. Phase 9 仅设计, 实施分 Phase 10+.

## Goals

- 1 `CrossVolumeReferenceGraph` (节点 = 角色/伏笔/设定/plot point, 边 = 引用关系, 时序 = (vol, ch))
- 1 `CrossVolumeRipple` 数据结构 (origin event + impact list + candidate diff + author decision)
- 1 半自动触发流程 (5 步: scan → graph query → diff gen → author review → apply)
- 4 维 LLM prompt template (角色 / 伏笔 / 设定 / plot point, 各自识别 + diff gen)
- 1 review UI (impact 列表 + diff preview + 批量 confirm/reject)
- 1 rollback 机制 (apply 前 snapshot, author 误操作 1-click revert)
- 1 audit log (所有 ripple 决策留痕, 后续可重放)
- 0 改 Phase 8.5-8.30 dashboard code / Phase 7 lingwen 22 步 / Phase 6 5 维审核
- 0 改 WorldSnapshot schema (Ripple 字段已就位, 扩 cross-volume metadata 即可)
- 0 改 subplot lifecycle 5 条上限 / 6 态机

## Non-goals

- ❌ **全自动 apply** (主公决策半自动): LLM 不直接改前卷, 需 author 显式 confirm
- ❌ **跨书 / 跨作品涟漪**: 1 项目内多卷, 不涉及多项目
- ❌ **实时 preview** (写 V2 实时触发 V1 提示): 性能 + 体验复杂, 留 Phase 14+
- ❌ **多 author 协作 / 权限分层**: 留后续, 当前 1 author (主公) 模型
- ❌ **LLM 替代 editor**: 涟漪 review 仍是人审, LLM 只识别 + 建议
- ❌ **级联涟漪自动 detect** (改 V1 又触发 V2 涟漪): 算法复杂, 留 Phase 14
- ❌ **跨语言涟漪** (多语言版本): YAGNI
- ❌ **撤销后 redo 多步栈**: 当前 1 级 revert 够用
- ❌ **AI 味自动审计** (Phase 6.4): 独立维度, 不混

## Design

### 1. 数据模型

#### 1.1 `CrossVolumeReferenceGraph` (CVG)

```python
# infra/cross_volume/reference_graph.py (新文件, Phase 10 实施)

@dataclass(frozen=True)
class ReferenceNode:
    """跨卷引用图节点 (4 维之一)"""
    node_id: str                          # "char:林尘" / "foreshadow:玉佩来历" /
                                           # "setting:星月宗" / "plot:星月之子身世"
    dim: Literal["character", "foreshadow", "setting", "plot_point"]
    label: str                             # 显示名 ("林尘" / "玉佩来历" / "星月宗" / ...)
    birth_volume: int                     # 出生卷
    birth_chapter: int                    # 出生章
    # 4 维各自有 attribute, 用 dict 装避免 dataclass 爆炸
    attrs: dict                           # dim-specific metadata

@dataclass(frozen=True)
class ReferenceEdge:
    """引用边: from node 在某章提及了 to node"""
    from_node: str                        # 引用源 (角色 / 伏笔 / 设定 / plot)
    to_node: str                          # 引用目标
    volume: int                           # 在哪一卷
    chapter: int                          # 在哪一章
    paragraph_idx: int                    # 第几段 (锚定粒度)
    excerpt: str                          # 引用文本 (50-200 字上下文)
    strength: float                       # 0.0-1.0 (LLM 评分: 显式 / 隐含 / 路过)
    intent: Literal["callback", "foreshadow", "mention", "passing"]  # 4 种引用意图

class CrossVolumeReferenceGraph:
    """4 维引用图, 持久化到 WorldSnapshot, 支持时序查询"""
    nodes: dict[str, ReferenceNode]        # node_id → node
    edges: list[ReferenceEdge]             # 全边表
    # 索引 (lazy build):
    by_volume: dict[int, list[ReferenceEdge]]  # vol → 该卷的所有 edge
    by_node: dict[str, list[ReferenceEdge]]    # node_id → 该节点作为 from/to 的所有 edge

    def query_impact(self, node_id: str, from_volume: int) -> list[ReferenceEdge]:
        """查 node_id 在 from_volume 之前的所有引用边 (即受影响前卷段落)"""
        return [e for e in self.by_node.get(node_id, []) if e.volume < from_volume]

    def detect_cycle(self, from_node: str, target_node: str) -> bool:
        """detect 引用环 (A → B → A, 防 apply 涟漪时死循环)"""
        ...
```

**关键 invariant**: 引用图是 **append-only** (新增 edge 不删旧), 每次 L2 卷大纲生成时增量更新. **不重建** (重生成 V1 引用图 = 破坏时序).

#### 1.2 `CrossVolumeRipple` (CVR)

```python
# infra/cross_volume/ripple.py (新文件, Phase 11 实施)

@dataclass
class RippleCandidate:
    """LLM 识别出的涟漪候选 (1 origin event → 1 impact)"""
    candidate_id: str                     # "cand_{uuid4}"
    origin_volume: int                    # 涟漪源卷 (e.g. 2)
    origin_chapter: int                   # 源章
    origin_excerpt: str                   # 源段落 (50-200 字)
    origin_event: str                     # 1 句话描述事件 ("林尘在 V2 ch30 死")
    target_node_id: str                   # 受影响节点
    target_dim: Literal["character", "foreshadow", "setting", "plot_point"]
    target_edges: list[ReferenceEdge]     # 前卷引用 (1-N 个)
    candidate_diffs: list[CandidateDiff]  # 每个 edge 1 candidate diff

@dataclass
class CandidateDiff:
    """1 段引用文本的候选更新"""
    edge: ReferenceEdge
    original: str                         # 原文段落 (200-500 字)
    proposed: str                         # 候选改写
    rationale: str                        # 1 句话说明 (为什么这么改)
    risk: Literal["low", "medium", "high"]  # 误改风险评估 (LLM 自评)
    confidence: float                     # 0.0-1.0

@dataclass
class RippleDecision:
    """author 决策 (1 candidate → confirm/reject/edit)"""
    decision_id: str                      # "dec_{uuid4}"
    candidate_id: str
    action: Literal["confirm", "reject", "edit"]
    # edit 时填充 (author 手动改 proposed)
    custom_proposed: Optional[str] = None
    decided_at: datetime
    decided_by: str = "主公"

@dataclass
class CrossVolumeRipple:
    """完整涟漪事件: 1 origin → N candidates → N decisions → apply"""
    ripple_id: str
    trigger_volume: int
    trigger_chapter: int
    trigger_event: str
    candidates: list[RippleCandidate]
    decisions: dict[str, RippleDecision]  # candidate_id → decision
    status: Literal["draft", "reviewing", "applying", "applied", "rolled_back"]
    # snapshot 指针 (rollback 用)
    pre_apply_snapshot_id: Optional[str] = None
    applied_at: Optional[datetime] = None
    rolled_back_at: Optional[datetime] = None
```

#### 1.3 4 维节点 attributes

| dim | attrs 字段 | 含义 |
|-----|-----------|------|
| character | `{alias: [str], status: alive/dead/missing/changed, role: protagonist/antagonist/supporting, last_appearance_vol: int}` | 角色 (alias 列出所有别名, status 跨卷追踪) |
| foreshadow | `{planted_vol: int, planted_ch: int, target_payoff_vol: Optional[int], category: mystery/artifact/relationship/event}` | 伏笔 (planted + 目标回收点) |
| setting | `{scope: world/region/faction/sect, parent_setting: Optional[str], immutable_laws: list[str]}` | 设定 (上级设定 + 不变法则) |
| plot_point | `{plot_id: str, type: main/subplot/side, progress_at_birth: float, linked_nodes: [str]}` | 主线/支线 plot 节点 (跟 Plot 数据结构互通) |

#### 1.4 持久化

```python
# infra/cross_volume/storage.py (新文件, Phase 10 实施)

class RippleStorage:
    """ripple_events + ripple_decisions + reference_graph_snapshots 3 表
    复用 Phase 8.12 CostTrackerDB 的 sqlite pattern, 0 引入新 DB engine"""

    def save_graph(self, graph: CrossVolumeReferenceGraph) -> str: ...
    def load_graph(self, project: str) -> CrossVolumeReferenceGraph: ...
    def save_ripple(self, ripple: CrossVolumeRipple) -> None: ...
    def list_ripples(self, project: str, status: Optional[str] = None) -> list[CrossVolumeRipple]: ...
    def save_decision(self, decision: RippleDecision) -> None: ...
    def get_audit_trail(self, ripple_id: str) -> list[dict]: ...

    # 跟 Phase 8.12 类似, 存 infra/.state/ripple.db (gitignored)
```

**关键决策**: 1 项目 1 `ripple.db`, 跟 `cost_tracker.db` / `workflow.db` 同目录. 不引入新 schema, 复用 sqlite + 项目级 gitignore.

### 2. 涟漪识别算法 (4 维)

#### 2.1 LLM 识别 trigger event (V_N 写完后)

```python
# infra/cross_volume/scanner.py (新文件, Phase 11 实施)

async def scan_volume_for_ripple_triggers(
    volume: int,
    chapters: list[str],                  # 该卷所有章文本
    graph: CrossVolumeReferenceGraph,
) -> list[RippleTrigger]:
    """LLM 扫整卷, 识别可能触发跨卷涟漪的事件"""
    prompt = f"""
    你正在审阅 V{volume} 的 {len(chapters)} 章. 请识别可能影响前卷的事件:

    已知引用图节点 (前卷已登记):
    {graph_nodes_summary}

    对每个候选事件, 输出:
    - event_description: 1 句话描述
    - affected_node_ids: 受影响的 4 维节点 ID 列表
    - confidence: 0.0-1.0 (高 = 明确事件, 低 = 可能但需 author 判)
    - excerpt: 事件发生段落 (50-200 字)

    只列 confidence >= 0.6 的事件. 低概率事件不浪费 author 注意力.

    V{volume} 章节:
    {chapters_text}
    """
    # Phase 11 实施: 调 LLM, 解析 JSON, 过滤 confidence < 0.6
```

#### 2.2 4 维 prompt templates

```python
# infra/cross_volume/prompts/character_ripple.py
CHARACTER_RIPPLE_PROMPT = """
识别 V{volume} 中角色状态变化 (死/活/立场变/能力变/关系变) 的事件.
对每个事件, 列出前卷提及该角色的段落 (需 update) + 候选改写.

输出 JSON:
{
  "events": [
    {
      "char_id": "char:林尘",
      "event_type": "death|status_change|relationship_change|ability_change",
      "event_chapter": 30,
      "event_excerpt": "...",
      "front_volume_impacts": [
        {
          "volume": 1,
          "chapter": 15,
          "paragraph_idx": 3,
          "original": "原段落...",
          "proposed": "候选改写...",
          "rationale": "林尘在 V2 ch30 死亡, V1 ch15 此处描述其师徒关系应改为追忆",
          "risk": "medium"
        }
      ]
    }
  ]
}
"""
# 4 维各 1 prompt: character / foreshadow / setting / plot_point
# Phase 11 实施 4 个 prompt file, 跟 Phase 7 polisher_prompts.py 同 pattern
```

#### 2.3 Graph query → impact list

```python
async def query_impact_for_trigger(
    trigger: RippleTrigger,
    graph: CrossVolumeReferenceGraph,
) -> list[ReferenceEdge]:
    """已知 1 trigger event + affected_node_ids, 查引用图找前卷段落"""
    impacts = []
    for node_id in trigger.affected_node_ids:
        # 找所有 from_node 引用到该 node 的前卷 edge
        edges = [
            e for e in graph.edges
            if e.to_node == node_id and e.volume < trigger.volume
        ]
        impacts.extend(edges)
    # 去重 (同段可能被多次提及, 只列 1 次)
    return list({(e.volume, e.chapter, e.paragraph_idx): e for e in impacts}.values())
```

### 3. 半自动触发流程 (5 步)

```
[Step 1] Author 完成 V_N 写作
   ↓
[Step 2] 系统自动扫 V_N → 识别 trigger events (LLM, confidence >= 0.6)
   ↓ /api/cross-volume/ripples/scan POST {volume: N}
[Step 3] 对每个 trigger → graph query → impact list → candidate diff (LLM 4 维 prompt)
   ↓
[Step 4] Author 打开 review UI → 看 impact 列表 + diff preview + 风险评分
   ↓
[Step 5] Author 逐条 confirm/reject/edit → apply (批量)
   ↓
[Rollback] Apply 前自动 snapshot, 误操作 1-click revert
```

#### 3.1 Review UI 草图 (文本描述, 实际 UI Phase 12 实施)

```
┌─────────────────────────────────────────────────────────────┐
│ 跨卷涟漪 Review — V2 触发 (4 candidates)            [×]   │
├─────────────────────────────────────────────────────────────┤
│ ▼ Candidate 1/4: char:林尘 死亡                              │
│   Source: V2 ch30 — "林尘被暗皇殿伏击, 力竭而亡"            │
│   Risk: medium  Confidence: 0.85                            │
│                                                             │
│   ▼ Impact V1 ch15 ¶3 — 师徒对话 (strength=0.8)             │
│     Original: "师父看着林尘, 眼中满是期许"                  │
│     Proposed: "师父想起林尘, 眼中泛起追忆的哀色"            │
│     Rationale: 改为回忆视角, 暗示结局已知                    │
│     [✓ Confirm]  [✗ Reject]  [✎ Edit]  [Skip]               │
│                                                             │
│   ▼ Impact V1 ch22 ¶5 — 战斗场景 (strength=0.6)             │
│     Original: "林尘剑光一闪, 暗皇殿弟子应声而倒"            │
│     Proposed: "林尘剑光一闪, 暗皇殿弟子应声而倒 (此战日后成 │
│               为其陨落前的最后一战, 传颂百年)"             │
│     Rationale: 加 foreshadow 注解, 不改主体                  │
│     [✓ Confirm]  [✗ Reject]  [✎ Edit]  [Skip]               │
│                                                             │
│   [Confirm All]  [Reject All]  [Save Draft]  [Apply ✓]     │
└─────────────────────────────────────────────────────────────┘
```

**关键 UX 决策**:
- 默认 1 candidate 展开 1 次, 不一次全开 (避免 author 注意力散)
- `risk=high` candidate 默认折叠, 需 author 主动展开
- `confidence < 0.7` candidate 标 "low confidence" 黄底, 提示 author 仔细审
- Apply 前再次确认 modal: "将修改 12 处前卷段落, 不可撤销 (除 rollback)"

### 4. Rollback 机制

```python
# infra/cross_volume/rollback.py (新文件, Phase 13 实施)

class RippleRollback:
    """apply 前自动 snapshot, 误操作 1-click revert"""

    async def snapshot_before_apply(self, ripple_id: str, edits: list[ChapterEdit]) -> str:
        """apply 前存快照, 返 snapshot_id"""
        snapshot_id = f"snap_{ripple_id}_{ts}"
        # 存每个 edit 的 (volume, chapter, paragraph_idx, original_text)
        await self.storage.save_snapshot(snapshot_id, edits)
        return snapshot_id

    async def rollback(self, ripple_id: str) -> None:
        """apply 后误操作 → 1-click 回滚所有 edits"""
        ripple = await self.storage.load_ripple(ripple_id)
        if not ripple.pre_apply_snapshot_id:
            raise ValueError("No snapshot, cannot rollback")
        snapshot = await self.storage.load_snapshot(ripple.pre_apply_snapshot_id)
        for edit in snapshot.edits:
            # 写回 original_text
            await self.write_chapter_paragraph(
                edit.volume, edit.chapter, edit.paragraph_idx, edit.original_text,
            )
        # 标记 rolled_back
        ripple.status = "rolled_back"
        ripple.rolled_back_at = datetime.now()
        await self.storage.save_ripple(ripple)
```

**关键 invariant**: snapshot 必须 100% 可靠 (写文件前 fsync, DB 事务), 不可丢失. **0 改 Phase 8.12 CostTrackerDB 模式** (同样 sqlite + fsync).

### 5. 跟现有模块映射

| 现有 | Phase 9 关系 |
|------|------------|
| `WorldSnapshot.active_subplots` | 4 维节点存 snapshot, 引用图持久化 |
| `Plot` / `PlotStatus` (Phase 0 model) | `plot_point` 维节点 = Plot 节点, status 互通 |
| `Ripple` (Phase 0 卷内) | `CrossVolumeRipple` 扩展, 加 `origin_volume` + 跨卷 impact list |
| `foreshadow_checker` (Phase 6) | `foreshadow` 维节点 = foreshadow_checker 产出, 跨卷追踪 |
| `contradiction_detector` (Phase 6) | 涟漪 apply 后跑一次 contradiction check (新增 check, 不改 detector) |
| `lingwen.py` STEP_07 (结构) | outline_master 输出 + `cross_volume_nodes` 字段 (Phase 10) |
| `audit-stale-report.md` | 涟漪 audit log 入档, 后续可重放 (Phase 13) |
| `dashboard/protocols.py` (Phase 8) | 加 3 endpoint: scan / review / apply (Phase 12) |

### 6. LLM 成本估算

**单 V_N 涟漪扫描** (主公 359 章项目, 假设 4 卷):
- Scan V2 (~50 章): 1 LLM call, ~30k input tokens, ~5k output (候选列表)
- 4 candidate diff gen: 4 × ~10k input (引用上下文), ~2k output (改写)
- **总**: 5 calls × ~15k tokens = ~75k tokens / V_N
- 按 Claude Sonnet $3/$15 per M tokens: ~$0.5 / V_N
- 1 项目 4 卷: ~$2 一次性 (远低于 1 章 LLM 写作 $0.5 × 50 章 = $25)

**结论**: 涟漪扫描成本可忽略, 不到 1 章写作的 10%.

### 7. 实施范围 (Phase 9 仅设计)

#### 7.1 本 spec 覆盖 (Phase 9)

- 数据模型 (CVG + CVR + 4 维 attrs)
- 算法 (scan / graph query / diff gen / apply)
- 4 维 LLM prompt design (character / foreshadow / setting / plot_point)
- 半自动 5 步流程
- Review UI 草图 (文本, 不实施)
- Rollback 机制
- 持久化 (ripple.db)
- 跟现有模块映射
- LLM 成本估算

#### 7.2 不在本 spec 覆盖 (后续 phases)

- 具体代码 (Phase 10+ 实施)
- Review UI 真实 Vue 组件 (Phase 12)
- LLM 集成 (Phase 11, 4 维 prompt 模板实施)
- Rollback 代码 (Phase 13)
- 性能优化 (Phase 14, lazy traversal + 缓存)
- 级联涟漪自动 detect (Phase 14)
- 跨书涟漪 (永不, 1 项目边界)

## Risks + Mitigations

| 风险 | 缓解 |
|------|------|
| LLM 误识别 (假涟漪多) | confidence >= 0.6 过滤 + risk=high 默认折叠 + author 逐条 confirm |
| LLM 改写质量差 (前卷 经典段落被改坏) | candidate diff 而非 auto-apply + edit 模式让 author 手动调 |
| 级联涟漪 (改 V1 又触发新涟漪) | Phase 9 仅 1 跳, 多跳检测 Phase 14 |
| 引用图冷启动 (前几卷没数据) | Phase 10 实施时 backfill 历史 359 章 (一次性 LLM 扫, ~$0.5) |
| 性能 (大项目 100+ 卷 + 1000+ 章) | lazy graph build + by_volume / by_node 索引 (Phase 10) |
| Rollback 误操作 (rollback 错了怎么办) | snapshot 写 fsync + DB 事务, rollback 后留 audit trail |
| 多 author 冲突 (后续) | Phase 9 1 author 模型, 不实现 |
| 4 维 prompt 失效 (LLM 不按 schema 返) | Pydantic 强校验 + retry 1 次 + 失败标 low confidence |
| 引用图跟大纲脱节 (大纲改了节点变了) | 节点 ID 用 hash(title+birth_chapter), 自动 detect rename |
| 误改前卷 5 维审核标 (Phase 6) | apply 后跑 contradiction check, 0 改 checker, 只 add call |
| 跨卷 ripple 跟 Phase 6 foreshadow_checker 重复 | 明确分工: checker 找伏笔 (无 LLM), ripple 找 cross-volume impact (LLM) |
| 0 改 Phase 8 dashboard (5 维 cost/budget/radar/hook/chapter) | ripple UI 独立 page, 不入 dashboard |
| 0 改 subplot lifecycle 5 条上限 | ripple 不影响 active_subplots, 只追踪 cross-volume 引用 |
| 0 改 WorldSnapshot schema | 扩 nodes + edges 字段, 0 改 active_subplots |
| 0 改 12 SCENARIOS 路由 | ripple 走独立 infra/cross_volume/ module |
| 0 改 GoT bridge | ripple 不走 workflow, 独立流程 |
| 0 API key 泄漏 | 0 改 LLM client, 复用 Phase 7 polisher 路径 |
| MEMORY.md 不破 200 行 | 涟漪 entry 走 phases.md topic (8.30+ 累计已超 200, 必拆) |
| Spec 行号 `:NNN` 漂移 | 0 改 8.5-8.30 历史 spec |

## Out of Scope (永不实施)

- 跨书 / 跨作品涟漪 (1 项目边界)
- 跨语言版本 (YAGNI)
- 实时 preview (写 1 段触发 preview, 性能 + 体验爆炸)
- 多 author 协作 / 权限 (留后续, 当前 1 author)

## Verification (本 spec 自检)

- [x] **0 代码**: 纯设计, 1 蓝图文档配套
- [x] **0 改现有模块**: WorldSnapshot / Plot / Ripple / dashboard / checker 全部 0 改
- [x] **4 维覆盖**: character / foreshadow / setting / plot_point 各自 1 段 attrs + 1 prompt
- [x] **半自动 5 步**: scan → query → diff gen → author review → apply
- [x] **rollback 机制**: snapshot + 1-click revert
- [x] **LLM 成本估算**: $0.5 / V_N, 可忽略
- [x] **风险表**: 12 项, 各自 mitigation
- [x] **0 spec 行号漂移**: 不引用 8.5-8.30 spec 的 :NNN

## 完成后下一步 (后续 phases)

- **Phase 10**: data model + CVG 抽取 (backfill 359 章历史, ~$0.5 LLM 一次性) + ripple.db schema
- **Phase 11**: 4 维 LLM prompt 实施 (character / foreshadow / setting / plot_point) + scanner.py + diff gen
- **Phase 12**: review UI (Vue 3, 跟 Phase 7.6 radar chart 同 dashboard 模式) + 半自动流程 endpoint
- **Phase 13**: rollback 实施 + audit log + fsync 保护
- **Phase 14**: 性能优化 (lazy graph + 缓存) + 级联涟漪 detect + 跨语言 reject 确认
- **Phase 15**: MEMORY.md 拆 11+ entries 到 phases.md topic (累计 30+ entries, 必拆)

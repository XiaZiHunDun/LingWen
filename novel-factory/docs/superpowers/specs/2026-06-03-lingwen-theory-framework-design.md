# 灵文理论框架 v1.0

> 日期：2026-06-03
> 状态：待批准
> 范围：所有 v10+ 设计的理论基础
> 输入：用户 29 条想法 #6, #7, #18, #23, #24, #25, #27, #28
> 配套：Doc 2 (提示词工程) / Doc 3 (支线模型) / Doc 4 (GoT 适配)

---

## 一、为什么需要理论框架

灵文当前已经能写出 359 章连贯小说，但**没有一个统一的"世界是怎么运转的"理论**。各模块各做各的：

- 检测器只看到一章节
- 状态机只看到 step 流转
- Agent 只看到自己的 prompt
- 审核员只看到 S1-S8 评分

**缺的是"世界观"——一个让所有模块能互相讨论的概念集合。** 本文给出 v1.0。

## 二、核心命题

**小说是一个主角在世界中留下痕迹的过程。**

- 主角是**第一类公民**：所有变化围绕他发生
- 世界是主角的**背景投影**：只记录跟主角相关的部分
- 痕迹形成**波浪**：挖坑 → 扩散 → 平复，循环往复
- 故事必须**不崩塌**：每个波浪最终要收敛

## 三、四大模型

### 3.1 世界快照模型 (WorldSnapshot)

**定义**：每一章结束时,世界处于一个确定状态。这个状态可被完整记录、可被对比、可被复原。

```
WorldSnapshot {
    snapshot_id:        # "ch0001_v1"
    chapter:            1
    timestamp:          "2026-05-21T10:00:00"
    nodes:              Dict[NodeId, NodeState]   # 见 3.2
    relations:          List[Relation]            # 见 3.2
    physical_line:      PhysicalLine              # 见 3.3
    mental_line:        MentalLine                # 见 3.3
    active_subplots:    List[SubplotId]           # 见 3.4
    world_mood:         str                       # 紧张/平静/希望...
    consistency_hash:   str                       # 用于检测非预期修改
}
```

**核心约束**：
- 每章写完 → 必须产生新 Snapshot
- Snapshot 持久化到 `.state/snapshots/ch{NNNN}.json`
- 检测器读 Snapshot,而不是重新扫描全文
- 矛盾检测 = 对比相邻 Snapshot 的差异

**为什么这样设计**：
- O(1) 拿"当前世界状态"，O(N) 拿"演化历史"
- 改章节 → 回滚 Snapshot → 自动回滚下游所有状态
- LLM 上下文只需要"当前 Snapshot + Delta" 而不是全部正文

### 3.2 关键点图 (KeyPointGraph)

**定义**：世界由 ≤100 个关键点构成。关键点之间通过关系连接。

```
NodeType:
    - LOCATION     # 地点 (玄域/星月宗/地底裂缝)
    - CHARACTER    # 人物 (主角/师父/反派/路人)
    - FACTION      # 派系 (星月宗/暗皇殿)
    - ARTIFACT     # 物品 (断剑/玉佩/星核)
    - CONCEPT      # 抽象概念 (虚无之道/大灾变)

Node:
    id:             NodeId
    type:           NodeType
    name:           str
    attrs:          Dict[str, Any]              # 灵活属性
    status:         str  # active/destroyed/hidden/transformed
    first_ch:       int
    last_ch:        int                         # 最后出现章节

Relation:
    src:            NodeId
    dst:            NodeId
    type:           str                         # "knows"/"owns"/"located_in"/"allied_to"...
    weight:         float                       # 关系强度
    first_ch:       int
    last_ch:       int
```

**核心约束**：
- **关键点 ≤100**：保证矛盾检测 O(N²)=10000 可秒级完成
- **关系数 ≤500**：每节点平均 5-10 条关系
- 新增关键点需要"理由"：必须由剧情事件触发
- 主角相关节点优先级最高

**为什么 100 这个数**：
- 50 太少：长篇小说(300+章)信息密度不够
- 200 太多：N²=40000 检测慢 + 上下文爆
- 100 是黄金分割：N²=10000 在毫秒级

**矛盾检测 = 关键点两两比较**：
```
for a, b in keypoints:
    if a.contradicts(b):
        yield Contradiction(a, b, reason, ch)
```
时间复杂度：O(N²)=10000，1 章节 < 10ms

### 3.3 物理线/心理线双轨 (PhysicalLine / MentalLine)

**定义**：每章都有"做了什么"(物理) 和 "想了什么/感受到了什么"(心理) 两条线。

```
PhysicalLine {
    ch:              int
    actions:         List[Action]       # 主角或关键角色的具体行为
    locations:       List[Location]     # 物理位置流转
    events:          List[Event]        # 客观事件 (战斗/相遇/发现)
    constraints:     List[Constraint]   # 物理限制 (受重伤/没钱/被围困)
}

MentalLine {
    ch:              int
    thoughts:        List[Thought]      # 主角/关键角色心理活动
    emotions:        Dict[CharId, EmotionCurve]  # 情感曲线
    arc_progress:    Dict[CharId, float]  # 角色弧光进度 0-1
    growth_signals:  List[str]          # 成长信号
}
```

**为什么需要双轨**：
- 网文 80% 是物理线 (爽感/节奏)
- 经典小说 80% 是心理线 (深度)
- **比例由题材决定**：玄幻/都市=7:3，历史/言情=3:7
- 比例在主线/支线模型(见 Doc 3) 中配置

**实现约束**：
- 写入时，content_writer 必须同时填充两个字段
- 检测器扫描时，physical/mental 比例异常 → 报问题
- 心理线过少 → 提示"加点内心戏"
- 物理线过少 → 提示"加点冲突/动作"

### 3.4 波浪机制 (RippleEngine)

**核心思想**：每个剧情事件是一个"坑"。坑会扩散成波浪，波浪必须平复，否则故事崩塌。

```
Ripple {
    ripple_id:           str              # "ripple_001"
    origin_event:        EventId          # 引发波浪的事件
    origin_ch:           int              # 挖坑章节

    affected_nodes:      List[NodeId]     # 哪些节点被影响
    affected_relations:  List[Relation]   # 哪些关系被影响

    wavefront:           List[ChPhase]    # 波浪推进: ch+1, ch+5, ch+20...
    decay_rate:          float            # 衰减率 (0.1-0.5)
    resolved_ch:         int?             # 平复章节, None=未平复
    collapse_risk:       float            # 崩塌风险 0-1
}
```

**挖坑规则**：
1. 挖坑必须注册到 Ripple
2. 每个 Ripple 必须有"计划平复章节"
3. 累计未平复 Ripple 数 > 10 → 崩塌风险 > 0.7
4. 崩塌风险 > 0.8 → 系统报警,要求 LLM 紧急收尾

**平复规则**：
- 平复 = Ripple.affected_nodes 状态恢复到 origin_ch 之前 或 达成新稳态
- 强平复 = 100% 恢复 (伏笔回收)
- 弱平复 = 60-80% 恢复 + 新关系补足 (主题升华)
- 未平复 = 故事未完结(可接受,但要标记)

**示例** (星陨纪元):
- ch010 挖坑: 林尘是"星月之子" → Ripple.affected = [林尘身份, 星月宗, 虚无之主]
- ch050 涟漪扩散: 暗皇殿追踪, 虚无之主试探
- ch200 强平复: 林尘身份公开 + 重新定义"星月之子"含义
- ch350 弱平复: 虚无之主被同化 (新稳态)

**为什么需要 Ripple**：
- 网文最常见病："挖坑不填"
- 传统大纲缺机制跟踪"哪些坑还开着"
- Ripple = 数据库化的"挖坑清单"

## 四、与现有模块的映射

| 现有模块 | 在新理论中的角色 |
|---------|-----------------|
| 38 个一致性检测器 | 全部基于 WorldSnapshot 读取,不再裸扫全文 |
| workflow_state.json | 演化为 Snapshot 序列 |
| character_state | MentalLine 子集 |
| attribute_comparer | KeyPointGraph 的边检测 |
| pacing_checker | RippleEngine 的 wavefront 分析 |
| core_foreshadow_checker | Ripple.resolved_ch 状态机 |
| story_contracts | 注入到 Ripple.origin_event |
| reading_power | 跨 Snapshot 序列的钩子分析 |
| 状态机 (state/) | 顶层 22 步 → 每步产生新 Snapshot |

## 五、实施路径 (理论先行)

### Phase 0 (本文)
- ✅ 输出本文档
- 输出配套 3 文档

### Phase 1: 数据模型 (2 周)
- 新增 `infra/world_model/` 模块
- 实现 `WorldSnapshot` / `KeyPointGraph` / `PhysicalLine` / `MentalLine` / `Ripple` 数据类
- 实现 `SnapshotStore` (持久化 + 版本化)
- 实现 `RippleEngine` (挖坑/扩散/平复)
- 实现 `KeyPointGraph` 的 N² 矛盾检测器 (替换 attribute_comparer)

### Phase 2: 改造检测器 (2 周)
- 38 个检测器逐步改为读 Snapshot
- 保留回退机制：Snapshot 不可用时裸扫全文
- 输出统一 `ChapterConstraint` (见 Doc 2)

### Phase 3: 写入端改造 (2 周)
- content_writer 写完一章必须填充 PhysicalLine + MentalLine
- 引入 Ripple 显式注册 (LLM 在 prompt 中要求)
- 检测器发现未注册的关键点变化 → 报错

## 六、风险与缓解

| 风险 | 缓解 |
|------|------|
| 100 关键点不够用 | 动态扩到 150,但 N² 仍 < 25k 可接受 |
| Snapshot 持久化爆磁盘 | 增量存储 + 关键节点可压缩 |
| Ripple 注册漏 | 检测器对比相邻 Snapshot 推断 Ripple |
| 双轨写作对 LLM 太重 | 提供 2 个 schema 模板,LLM 二选一 |
| 与现有检测器冲突 | 检测器双轨运行 1 个月后,逐步下线老路径 |

## 七、理论自检

- **主角优先**：所有节点都通过"是否影响主角"评估相关性
- **波浪收敛**：每个 Ripple 必须有 resolved_ch 或显式标记"长期未平复"
- **不崩塌**：RippleEngine 的 collapse_risk 始终 < 0.8
- **双轨平衡**：physical/mental 比例在题材期望的 ±20% 内
- **节点收敛**：新增关键点必须有"事件触发的证据"

## 八、与其他文档关系

- **Doc 2 提示词工程**：每个 Step (PHASE/STEP) 都需要"输入什么 Snapshot 字段"
- **Doc 3 支线模型**：支线的 purpose = Ripple.origin_event 的目的
- **Doc 4 GoT 适配**：Snapshot 是 GoT 节点的状态

---

## 附录 A: 数据结构示例 (Python)

```python
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

class NodeType(str, Enum):
    LOCATION = "location"
    CHARACTER = "character"
    FACTION = "faction"
    ARTIFACT = "artifact"
    CONCEPT = "concept"

@dataclass(frozen=True)
class NodeId:
    type: NodeType
    name: str
    def __str__(self): return f"{self.type}:{self.name}"

@dataclass
class KeyPoint:
    id: NodeId
    attrs: dict = field(default_factory=dict)
    status: str = "active"  # active/destroyed/hidden/transformed
    first_ch: int = 0
    last_ch: int = 0

@dataclass
class Relation:
    src: NodeId
    dst: NodeId
    type: str  # "knows"/"owns"/"located_in"/"allied_to"/"opposed_to"
    weight: float = 1.0
    first_ch: int = 0
    last_ch: int = 0

@dataclass
class PhysicalLine:
    ch: int
    actions: list[str] = field(default_factory=list)
    locations: list[NodeId] = field(default_factory=list)
    events: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)

@dataclass
class MentalLine:
    ch: int
    thoughts: list[str] = field(default_factory=list)
    emotions: dict[NodeId, str] = field(default_factory=dict)
    arc_progress: dict[NodeId, float] = field(default_factory=dict)
    growth_signals: list[str] = field(default_factory=list)

@dataclass
class Ripple:
    ripple_id: str
    origin_event: str
    origin_ch: int
    affected_nodes: list[NodeId]
    resolved_ch: Optional[int] = None
    collapse_risk: float = 0.0

@dataclass
class WorldSnapshot:
    snapshot_id: str  # "ch0001_v1"
    chapter: int
    nodes: dict[NodeId, KeyPoint]
    relations: list[Relation]
    physical: PhysicalLine
    mental: MentalLine
    active_ripples: list[Ripple]
    world_mood: str = "neutral"
    consistency_hash: str = ""
```

## 附录 B: 关键点抽取 Prompt (LLM 调用)

```
你是一个关键点抽取器。基于下面章节内容，输出 JSON：

约束:
- 关键点总数 ≤ 100 (本卷)
- 关键点类型: location/character/faction/artifact/concept
- 关键点必须在章节内被提到

输入章节:
{chapter_content}

输出 JSON Schema:
{
  "key_points": [{"type": "...", "name": "...", "attrs": {...}, "status": "active"}],
  "relations": [{"src": "...", "dst": "...", "type": "...", "weight": 0.5}],
  "physical": {"actions": [...], "locations": [...], "events": [...], "constraints": [...]},
  "mental": {"thoughts": [...], "emotions": {...}, "arc_progress": {...}, "growth_signals": [...]},
  "new_ripples": [{"ripple_id": "...", "origin_event": "...", "affected_nodes": [...]}],
  "resolved_ripples": ["ripple_xxx"]
}
```

## 附录 C: 与 GoT 的关系

详见 Doc 4。简言之：
- Snapshot = GoT 节点的状态
- Ripple = GoT 边 (影响传播)
- KeyPointGraph = GoT 图结构本身

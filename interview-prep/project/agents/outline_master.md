# outline_master · 大纲 Agent

> **一句话定位**：卷-章-节三层大纲 + 驱动链设计，**避免"想到哪写到哪"**。
> **技术标签**：结构化生成 · 驱动链 · 防止跑题

---

## 1 · 核心职责

- 输入：题材 / 主旨 / 主线 / 章数
- 输出：卷大纲 → 章大纲 → 节大纲（三层结构）
- 关键产出：**驱动链设计**——伏笔、冲突、悬念的埋设位置

---

## 2 · 最有意思的设计决策：驱动链 + 黄金三圈

### 问题

早期 v7-v8 让 Agent 自己规划章节大纲——**3 次跑出 3 个大纲**（不稳定）。
LLM 没有真正的"规划"能力（详 `06-reflections.md` 颠覆 1）。

### 解决方案：预定义结构 + 驱动链

```python
# 大纲模板（简化）
class VolumeOutline:
    arcs: list[PlotArc]          # 3-5 个情弧
    foreshadowing: list[Foreshadow]  # 5-10 个伏笔
    climax: ChapterRange         # 高潮章范围
    resolution: ChapterRange     # 收束章范围

class ChapterOutline:
    chapter_no: int
    plot_arc_id: str             # 所属情弧
    conflicts: list[Conflict]    # 1-3 个冲突
    arc_progress: float          # 情弧进度 0-1
    new_foreshadowing: list[str] # 新增伏笔 ID
    payoffs: list[str]           # 回收伏笔 ID
```

**3 个关键设计**：
1. **三层大纲**：卷（情弧）→ 章（冲突）→ 节（场景）——**预定义结构**而非 LLM 自由发挥
2. **驱动链**：每个章节标 `plot_arc_id` + `arc_progress`，**避免写偏**
3. **伏笔回收**：每章标注 `new_foreshadowing` + `payoffs`，**CVG 自动跟踪**

### 效果

- 8 本样章**0 章跑题**
- 伏笔回收率 **85%+**（vs LLM 自由发挥 30%）

---

## 3 · 数字 & 对比

| 指标 | LLM 自由发挥 | outline_master | 提升 |
|---|---|---|---|
| 大纲稳定性 | 30%（3 跑 3 个） | **95%+** | +65% |
| 跑题率 | 15-20% | **<1%** | 降 15× |
| 伏笔回收率 | 30% | **85%+** | +55% |
| 跨章一致性 | 60% | **90%+** | +50% |

---

## 4 · 1 个数字（**面试时直接说**）

> "灵文 8 本样章，**0 章跑题**——靠的是 outline_master 的驱动链设计。LLM 没规划能力，但**预定义结构 + 约束**让它稳定。"

---

## 5 · 白板画图提示

```
┌─────────────┐
│ 题材 / 主旨 │
└──────┬──────┘
       ↓
┌─────────────┐
│ 卷大纲     │  ← 3-5 情弧 + 高潮范围
└──────┬──────┘
       ↓
┌─────────────┐
│ 章大纲     │  ← 冲突 + 情弧进度 + 伏笔
└──────┬──────┘
       ↓
┌─────────────┐
│ 节大纲     │  ← 场景 + 角色在场
└─────────────┘
```

**讲法**：
> "大纲不是让 LLM 自由发挥——是**预定义三层结构 + 驱动链约束**。每个章节标 `plot_arc_id`，防止跑题；每章标 `new_foreshadowing + payoffs`，CVG 自动跟踪。"

---

## 6 · 配套文件

- `infra/agent_system/agents/outline_master/` — 代码路径
- `infra/world_model/` — WorldSnapshot 矛盾检测
- `infra/cross_volume/` — CVG 跨卷涟漪

# 知识图谱 + RAG 记忆系统设计文档

> 日期：2026-05-19
> 方案：方案一（轻量级文档索引）
> 状态：已批准，等待实施

---

## 一、背景与目标

### 1.1 现状问题

当前小说工厂的上下文管理存在以下痛点：

| 痛点 | 说明 |
|------|------|
| 作家获取设定被动 | 作家从 `基础层.yaml` 读取项目基本信息，写作时无法主动查询"当前角色状态" |
| 一致性检查离线 | `auto_consistency_checker.py` 是事后检查，作家写 ch200 时不知道 ch050 的设定是否冲突 |
| 缺乏关系图谱 | 人物关系无结构化存储，事件时间线无关联 |
| 长篇记忆衰减 | 360 章规模，靠静态文档无法追踪伏笔回收，语义衰减率约 2.3%/万字 |

### 1.2 优化目标

构建一个 RAG 记忆系统，同时服务三个场景：
- **作家写作**：自动推送相关上下文 + 主动查询设定
- **审核员审校**：审核前检查章节与前文的一致性冲突
- **主控决策**：调度工作流时获取全局状态摘要

---

## 二、技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| 向量数据库 | Qdrant | 性能强，支持过滤/范围查询，适合生产，Docker 部署 |
| 存储层 | Qdrant + 文件系统 | Qdrant 存向量，文件系统存状态快照和追踪表 |
| 实体抽取 | 规则引擎 + LLM | 前期用规则快速落地，后期可升级 LLM 抽取 |
| 部署环境 | Docker | Qdrant 容器化运行 |

---

## 三、整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      应用层（三个入口）                       │
├─────────────┬─────────────┬─────────────┬─────────────────────┤
│  作家写作   │  审核员审校  │   主控决策   │                     │
│   界面      │    界面      │    界面      │                     │
└──────┬──────┴──────┬──────┴──────┬──────┴──────────┬──────────┘
       │             │            │                │
       ▼             ▼            ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                    RAG 查询引擎（混合模式）                   │
│  • 自动推送：章节开始时推送相关上下文                         │
│  • 主动查询：作家/审核/主控手动输入查询                       │
│  • 检索策略：向量相似度 + 关键词过滤 + 时间范围约束            │
└──────┬─────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│               三层索引结构（Chapter → Entity → Relationship） │
│                                                              │
│  L1 章节索引    │  L2 实体索引      │  L3 关系索引           │
│  • ch001-ch360  │  • 角色状态追踪   │  • 人物关系图           │
│  • 向量化片段   │  • 位置/形态/生死 │  • 势力从属             │
│  • 元数据标签   │  • 伏笔状态       │  • 事件关联             │
└──────┬─────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                    存储层（Qdrant + 文件系统）               │
│                                                              │
│  Qdrant Collections:                                         │
│  • chapters_seg      → 章节内容向量                         │
│  • entities          → 实体向量                             │
│  • relationships       → 关系向量                             │
│                                                              │
│  文件系统:                                                   │
│  • state_tracker.json → 角色状态快照                        │
│  • plot_threads.yaml  → 伏笔追踪表                         │
│  • timeline.json      → 时间线索引                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 四、核心数据结构

### 4.1 章节片段索引（chapters_seg collection）

```json
{
  "id": "ch050_seg_003",
  "chapter": 50,
  "segment_text": "铁蛋蹲在废墟顶端，调试着那台老旧的信号器...",
  "vector": [0.123, -0.456, ...],
  "metadata": {
    "characters": ["铁蛋"],
    "location": "灰巢废墟",
    "time_marker": "战后第3天",
    "tags": ["场景描写", "技术细节"]
  }
}
```

### 4.2 实体索引（entities collection）

```json
{
  "id": "铁蛋",
  "type": "character",
  "current_state": {
    "chapter_range": "ch001-ch360",
    "location": "灰巢废墟",
    "form": "机械师形态",
    "alive": true,
    "emotion_state": "警惕"
  },
  "first_appearance": "ch001",
  "key_attributes": ["废土机械师", "实用主义者", "话少可靠"],
  "voice_pattern": "简短句式、专业术语、技术描述"
}
```

### 4.3 关系索引（relationships collection）

```json
{
  "id": "铁蛋_林夜_兄弟",
  "source": "铁蛋",
  "target": "林夜",
  "relationship_type": "并肩作战",
  "chapter_start": 10,
  "chapter_end": "ongoing",
  "trust_level": "high"
}
```

### 4.4 伏笔追踪表（plot_threads.yaml）

```yaml
threads:
  - id: "伏笔_暗皇复活"
    introduced_chapter: 5
    status: "埋设中"  # 埋设中 / 回收中 / 已回收
    key_mentions: [5, 20, 45, 80]
    expected_recycle: "ch150-ch180"
  - id: "伏笔_小九真实身份"
    introduced_chapter: 12
    status: "回收中"
    key_mentions: [12, 35, 67]
```

### 4.5 角色状态快照（state_tracker.json）

```json
{
  "characters": {
    "铁蛋": {
      "current_location": "灰巢废墟",
      "current_form": "机械师形态",
      "alive": true,
      "last_updated_chapter": 150,
      "key_state_changes": [
        {"chapter": 50, "event": "从人形变为机械师形态"},
        {"chapter": 100, "event": "加入林夜团队"}
      ]
    },
    "林夜": {
      "current_location": "暗域边境",
      "current_form": "化星形态",
      "alive": true,
      "last_updated_chapter": 151
    }
  }
}
```

---

## 五、RAG 查询引擎

### 5.1 自动推送逻辑（作家写作时）

```python
# 当作家开始写 ch151 时，系统自动：
def auto_push_context(chapter_num):
    # 1. 获取当前章节的关键角色（前5章活跃角色）
    active_characters = get_active_characters(chapter_num, lookback=5)

    # 2. 获取这些角色当前状态
    context = []
    for char in active_characters:
        state = get_entity_state(char, before_chapter=chapter_num)
        context.append(f"【{char}】状态：{state}")

    # 3. 获取待回收伏笔（该章节可能需要回收的）
    pending_threads = get_pending_plot_threads(chapter_num)

    # 4. 推送摘要
    return {
        "角色状态": context,
        "待回收伏笔": pending_threads,
        "前3章情节摘要": get_recent_summary(chapter_num, n=3)
    }
```

### 5.2 主动查询接口

```
作家输入：「林夜和苏琳的关系进展」
→ 向量检索：similarity_search("林夜 苏琳 关系", k=5)
→ 关键词过滤：timeline=[ch001-ch151]
→ 关系约束：relationship_type包含 romantic/allied
→ 返回：关系发展阶段的时间线摘要

审核员输入：「ch150和ch151的时间线是否矛盾」
→ 获取：ch150和ch151的time_marker
→ 对比：timeline.json中的时间线记录
→ 检测：如果冲突则报告P0问题
```

### 5.3 检索策略

| 策略 | 说明 |
|------|------|
| 向量相似度 | 基于 embedding 的语义检索 |
| 关键词过滤 | metadata 中的 characters、location、tags |
| 时间范围约束 | chapter_range 限制检索范围 |
| 关系约束 | relationship_type 过滤关系类型 |

---

## 六、与现有系统集成

### 6.1 与 workflow_state.json 的关系

```
现有：workflow_state.json 作为状态机，驱动各部门调度
新增：RAG 系统作为"上下文记忆层"，被动响应查询

RAG 不改变 workflow_state.json 的任何逻辑
RAG 只在以下时机被调用：
  • 作家开始新章节时（自动推送）
  • 作家/审核/主控主动查询时
  • 主控在做重大决策前（自动推送关键状态摘要）
```

### 6.2 与现有一致性检查器的关系

```
现有：tools/consistency/auto_consistency_checker.py（离线检查）
新增：RAG系统（实时上下文获取）

整合方式：
  • auto_consistency_checker.py 仍运行
  • 但在检查前，先通过RAG获取相关上下文
  • 检查器输出加上"上下文来源"字段，方便定位
```

---

## 七、实施步骤

### 阶段1（1-2周）：基础搭建

1. Docker 启动 Qdrant 容器
2. 创建 collections（chapters_seg, entities, relationships）
3. 实现章节内容向量化脚本（对现有360章批量处理）
4. 验证：Qdrant UI 能查到章节向量

### 阶段2（2-3周）：核心功能

5. 实现 RAG 查询引擎（混合检索）
6. 实现自动推送逻辑（作家写新章节时触发）
7. 实现主动查询 API（支持作家/审核/主控）
8. 实现角色状态追踪（state_tracker.json 更新机制）

### 阶段3（2-3周）：增强功能

9. 实现伏笔追踪表（plot_threads.yaml）
10. 实现时间线索引（timeline.json）
11. 与现有一致性检查器集成
12. 主控决策界面（可选，如果主控有独立界面的话）

### 阶段4（持续）：优化

- 根据使用反馈调整检索策略
- 优化推送时机和内容
- 补充缺失的实体类型

---

## 八、关键设计决策

| 决策 | 说明 |
|------|------|
| RAG 不改变 workflow_state.json | RAG 是上下文记忆层，不参与工作流调度 |
| Qdrant + 文件系统混合存储 | 向量存 Qdrant，状态快照和追踪表存文件系统 |
| 自动推送 + 主动查询混合模式 | 作家开始新章节时自动推送，作家可随时主动查询 |
| 实体抽取先规则后 LLM | 前期用规则快速落地，后期可升级 LLM 抽取 |
| 与现有检查器不冲突 | auto_consistency_checker.py 仍运行，RAG 作为增强层 |

---

## 九、验收标准

| 阶段 | 验收条件 |
|------|---------|
| 阶段1 | Qdrant 容器运行正常，360章全部向量化入库，Qdrant UI 可查询 |
| 阶段2 | 作家写新章节时收到自动推送，作家主动查询能返回正确结果 |
| 阶段3 | 伏笔追踪表能显示每个伏笔的状态，时间线索引能检测章节间冲突 |
| 阶段4 | 连续创作 30 天无一致性报错，作家/审核/主控均能正常使用 |

---

## 十、风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| 向量化质量不足 | 先用规则抽取关键信息，不依赖 LLM |
| Qdrant 性能瓶颈 | 先小规模验证，百万级数据前不需要优化 |
| 与现有系统冲突 | RAG 只做查询，不写任何工作流文件 |
| 作家不习惯使用 | 自动推送为默认，作家无需主动操作 |
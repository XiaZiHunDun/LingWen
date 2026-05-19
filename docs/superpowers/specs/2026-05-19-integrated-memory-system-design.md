# SPEC: 整合记忆系统

> **版本**: v1.0
> **日期**: 2026-05-19
> **状态**: 已整合（原3个方案合并）
> **优先级**: P1
> **预计工作量**: 8-10周

---

## 1. 概述与目标

### 1.1 问题陈述

当前小说工厂的上下文管理存在以下痛点：

| 痛点 | 说明 |
|------|------|
| 作家获取设定被动 | 作家从静态文档读取，写作时无法主动查询"当前角色状态" |
| 一致性检查离线 | `auto_consistency_checker.py` 是事后检查，写 ch200 时不知道 ch050 的设定是否冲突 |
| 缺乏关系图谱 | 人物关系无结构化存储，事件时间线无关联 |
| 长篇记忆衰减 | 360章规模，靠静态文档无法追踪伏笔回收，语义衰减率约 2.3%/万字 |
| 向量检索能力缺失 | 无法基于语义检索历史上下文 |

### 1.2 解决方案

构建**整合记忆系统**，统一以下三个原有方案：
- ~~向量记忆系统~~（ChromaDB轻量方案）
- ~~RAG记忆系统~~（Qdrant知识图谱方案）
- ~~RAG支持系统~~（RAG增强方案）

**整合策略**：采用**双层存储架构**，兼顾轻量与功能：
- **Qdrant**：向量存储 + 知识图谱（生产级）
- **文件系统**：状态快照 + 追踪表（结构化数据）

### 1.3 目标

| 目标 | 指标 |
|------|------|
| 上下文获取时效 | 作家写新章节时，自动推送相关上下文 < 2秒 |
| 伏笔回收追踪 | ≥85%伏笔在预期章节±10章内回收 |
| 一致性预警 | 写作时实时检测与前文冲突，准确率 ≥ 90% |
| 语义检索质量 | top-5检索相关度 ≥ 80% |

---

## 2. 架构设计

### 2.1 整体架构

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
│                    记忆系统网关 (MemoryGateway)              │
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
│                    双层存储层                               │
│                                                              │
│  Qdrant（向量存储）:                                        │
│  • chapters_seg      → 章节内容向量                         │
│  • entities          → 实体向量                             │
│  • relationships       → 关系向量                             │
│                                                              │
│  文件系统（结构化数据）:                                     │
│  • state_tracker.json → 角色状态快照                        │
│  • plot_threads.yaml  → 伏笔追踪表                         │
│  • timeline.json      → 时间线索引                          │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 目录结构

```
novel-factory/
├── memory_system/
│   ├── __init__.py
│   ├── gateway/
│   │   ├── __init__.py
│   │   ├── memory_gateway.py        # 记忆系统统一入口
│   │   ├── query_engine.py         # 混合查询引擎
│   │   └── push_engine.py          # 自动推送引擎
│   ├── vector/
│   │   ├── __init__.py
│   │   ├── qdrant_client.py        # Qdrant客户端封装
│   │   ├── embedder.py              # 嵌入模型管理
│   │   └── collections.py           # 集合管理
│   ├── state/
│   │   ├── __init__.py
│   │   ├── character_tracker.py    # 角色状态追踪
│   │   ├── plot_thread_tracker.py  # 伏笔追踪
│   │   ├── timeline_manager.py      # 时间线管理
│   │   └── fact_base.py             # 事实库管理
│   ├── config/
│   │   ├── __init__.py
│   │   ├── memory_config.yaml       # 记忆系统配置
│   │   └── collections_schema.yaml  # 集合Schema
│   └── scripts/
│       ├── __init__.py
│       ├── init_memory.py           # 初始化脚本
│       ├── embed_chapters.py        # 章节批量嵌入
│       ├── query_context.py         # 上下文查询
│       └── update_state.py          # 状态更新
└── config/
    └── ai_models.yaml               # AI模型配置（关联）
```

---

## 3. 核心数据结构

### 3.1 章节片段索引（chapters_seg collection）

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

### 3.2 实体索引（entities collection）

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

### 3.3 关系索引（relationships collection）

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

### 3.4 伏笔追踪表（plot_threads.yaml）

```yaml
threads:
  - id: "FP-001"
    introduced_chapter: 5
    status: "pending"  # pending / in_progress / recycled / invalid
    key_mentions: [5, 20, 45, 80]
    expected_recycle: "ch150-ch180"
```

### 3.5 角色状态快照（state_tracker.json）

```json
{
  "characters": {
    "铁蛋": {
      "current_location": "灰巢废墟",
      "current_form": "机械师形态",
      "alive": true,
      "last_updated_chapter": 150
    }
  }
}
```

---

## 4. 核心接口

### 4.1 MemoryGateway

```python
class MemoryGateway:
    """记忆系统统一入口"""

    def __init__(self):
        self.vector_store = QdrantClient(...)
        self.state_manager = StateManager(...)
        self.query_engine = QueryEngine(...)
        self.push_engine = PushEngine(...)

    def auto_push_context(self, chapter_num: int) -> MemoryContext:
        """
        自动推送上下文（作家写新章节时调用）

        Returns:
            MemoryContext: 包含角色状态、伏笔摘要、相关历史
        """

    def query(self, query: str, scope: QueryScope) -> QueryResult:
        """
        主动查询

        Args:
            query: 查询字符串
            scope: 查询范围（章节/角色/关系/全部）
        """

    def update_character_state(self, character: str, state: dict):
        """更新角色状态"""

    def plant_foreshadow(self, fp_id: str, metadata: ForeshadowMetadata):
        """登记伏笔"""

    def update_foreshadow(self, fp_id: str, chapter: int, event_type: str):
        """更新伏笔状态"""
```

### 4.2 查询引擎

```python
class QueryEngine:
    """混合查询引擎"""

    def hybrid_search(
        self,
        query: str,
        filters: dict = None,
        top_k: int = 5
    ) -> List[SearchResult]:
        """
        混合检索：向量 + 关键词 + 时间范围
        """

    def get_character_state(self, character: str, before_chapter: int = None) -> dict:
        """获取角色状态"""

    def get_relationship_network(self, character: str = None) -> RelationshipNetwork:
        """获取关系网络"""

    def check_consistency(self, chapter_content: str) -> List[ConsistencyIssue]:
        """一致性检查"""
```

---

## 5. 与现有系统集成

### 5.1 与工作流状态机的关系

```
现有：workflow_state.json 作为状态机，驱动各部门调度
新增：MemoryGateway 作为"上下文记忆层"，被动响应查询

MemorySystem 不改变 workflow_state.json 的任何逻辑
MemorySystem 只在以下时机被调用：
  • 作家开始新章节时（自动推送）
  • 作家/审核/主控主动查询时
  • 主控在做重大决策前（自动推送关键状态摘要）
```

### 5.2 与一致性检查器的集成

```
现有：tools/consistency/auto_consistency_checker.py（离线检查）
新增：MemoryGateway.check_consistency()（实时检查）

整合方式：
  • auto_consistency_checker.py 仍运行
  • 但在检查前，先通过 MemoryGateway 获取相关上下文
  • 检查器输出加上"上下文来源"字段，方便定位
```

### 5.3 与AI服务抽象层的集成

```
MemoryGateway 依赖 AIServiceGateway：
  • 嵌入模型通过 AIGateway 调用（可切换 Provider）
  • 向量化计算使用配置的嵌入模型
  • 未来可支持 LLM 实体抽取
```

---

## 6. 实施计划

### 阶段1（2周）：基础搭建

| 任务 | 负责人 | 交付物 | 验收标准 |
|------|--------|--------|---------|
| Docker启动Qdrant | 技术 | Qdrant容器运行 | Qdrant UI可访问 |
| 创建集合Schema | 技术 | collections_schema.yaml | Schema定义完整 |
| 实现Qdrant客户端 | 技术 | qdrant_client.py | 客户端可用 |
| 实现MemoryGateway | 技术 | memory_gateway.py | 统一入口可用 |
| 实现状态管理 | 技术 | state_manager.py | 状态读写正常 |

### 阶段2（3周）：核心功能

| 任务 | 负责人 | 交付物 | 验收标准 |
|------|--------|--------|---------|
| 实现查询引擎 | 技术 | query_engine.py | 混合检索正常 |
| 实现自动推送 | 技术 | push_engine.py | 新章节触发推送 |
| 实现角色状态追踪 | 技术 | character_tracker.py | 状态更新正常 |
| 实现伏笔追踪 | 技术 | plot_thread_tracker.py | 伏笔状态更新正常 |
| 实现时间线管理 | 技术 | timeline_manager.py | 时间线索引正常 |

### 阶段3（3-4周）：集成与优化

| 任务 | 负责人 | 交付物 | 验收标准 |
|------|--------|--------|---------|
| 批量嵌入现有章节 | 技术 | embed_chapters.py | 360章全部嵌入 |
| 与一致性检查器集成 | 技术 | 集成代码 | 实时检查正常 |
| 与AI服务抽象层集成 | 技术 | 集成代码 | 嵌入调用正常 |
| 性能优化 | 技术 | 优化报告 | 响应时间 < 2秒 |
| 验收测试 | 主编 | 测试报告 | 功能正常 |

---

## 7. 验收标准

### 7.1 功能验收

| 功能 | 验收标准 | 测试方法 |
|------|---------|---------|
| 自动推送 | 作家写新章节时收到推送 | 触发测试 |
| 主动查询 | 作家可查询角色/关系/伏笔 | 查询测试 |
| 角色状态追踪 | 状态变更后正确更新 | 状态更新测试 |
| 伏笔追踪 | 伏笔状态正确记录 | 伏笔更新测试 |
| 一致性检查 | 冲突检测准确率 ≥ 90% | 对比测试 |

### 7.2 性能验收

| 指标 | 验收标准 |
|------|---------|
| 自动推送延迟 | < 2秒 |
| 查询响应时间 | < 500ms |
| 批量嵌入速度 | ≥ 10章/分钟 |

### 7.3 质量验收

| 指标 | 验收标准 |
|------|---------|
| 伏笔回收率 | ≥ 85% |
| top-5检索相关度 | ≥ 80% |
| 角色状态一致性 | 100%（无矛盾） |

---

## 8. 关键设计决策

| 决策 | 说明 |
|------|------|
| Qdrant + 文件系统双层存储 | 向量存Qdrant（检索），状态快照和追踪表存文件系统（可靠性） |
| 不改变workflow_state.json | MemorySystem是上下文层，不参与工作流调度 |
| 自动推送 + 主动查询混合模式 | 作家开始新章节时自动推送，作家可随时主动查询 |
| 嵌入模型可配置 | 通过AI服务抽象层调用，支持切换不同嵌入模型 |
| 与现有检查器不冲突 | auto_consistency_checker.py仍运行，MemorySystem作为增强层 |

---

## 9. 归档的原始文档

以下文档已整合到本设计，原文档归档至 `../deprecated/`：

| 原文档 | 整合内容 |
|--------|---------|
| `2026-05-19-vector-memory-system.md` | 章节嵌入 + 上下文检索 |
| `2026-05-19-rag-memory-system-design.md` | 架构 + Qdrant + 三层索引 |
| `2026-05-19-rag-support-design.md` | RAG查询逻辑 |

---

## 10. 风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| Qdrant性能瓶颈 | 先小规模验证，百万级数据前不需要优化 |
| 与现有系统冲突 | MemorySystem只做查询，不写任何工作流文件 |
| 作家不习惯使用 | 自动推送为默认，作家无需主动操作 |
| 向量化质量不足 | 先用规则快速落地，后期可升级LLM抽取 |
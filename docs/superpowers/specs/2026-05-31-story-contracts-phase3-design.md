# 阶段3：Story Contracts 故事合约系统设计

> 日期：2026-05-31
> 状态：草稿
> 版本：v1.0

---

## 1. 背景与目标

### 1.1 背景

阶段1实现了追读力系统（钩子检测+爽点标记），阶段2实现了Dashboard可视化。webnovel-writer的Story Contracts提供了完整的**题材路由+反套路约束**机制，值得迁移到LingWen作为创作约束层。

### 1.2 目标

阶段3实现Story Contracts最小可用版：
- 题材路由表（从CSV加载题材调性约束）
- Anti-patterns约束库（套路禁忌/毒点）
- 合约持久化（MASTER_SETTING + anti_patterns.json）
- Context注入接口（供hooks.yaml调用）

### 1.3 约束

| 约束 | 说明 |
|------|------|
| 技术栈 | Python 3.13 + CSV + JSON |
| 集成方式 | 通过hooks.yaml注入，非侵入式 |
| 数据存储 | `novel-factory/.story-system/` |
| 影响范围 | 仅影响context注入，不改现有S1-S11 |
| 演进策略 | 最小种子层，支持后续扩展 |

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    LingWen 架构                              │
├─────────────────────────────────────────────────────────────┤
│  hooks.yaml ──trigger──▶ StoryContractEngine                 │
│                                    │                         │
│                         ┌────────▼────────┐                 │
│                         │ StoryContractEngine │               │
│                         │   (故事合约引擎)   │                │
│                         └────────┬────────┘                 │
│                                  │                          │
│         ┌───────────────────────┼───────────────────────┐   │
│         ▼                       ▼                       ▼      │
│  ┌────────────┐         ┌────────────┐         ┌─────────┐│
│  │GenreRouter │         │AntiPattern│         │Contract ││
│  │(题材路由)  │         │Aggregator │         │Persister ││
│  └─────┬──────┘         └─────┬──────┘         └────┬────┘│
│        └────────────────────────┼─────────────────────┘    │
│                                 ▼                            │
│                        ┌──────────────┐                     │
│                        │.story-system/│ (持久化目录)         │
│                        └──────────────┘                     │
│                                 │                            │
│                         ┌────────▼────────┐                 │
│                         │ ContextManager   │ (注入接口)      │
│                         └─────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 组件职责

| 组件 | 位置 | 职责 |
|------|------|------|
| `StoryContractEngine` | `infra/story_contracts/engine.py` | 主编排器，协调路由和聚合 |
| `GenreRouter` | `infra/story_contracts/router.py` | CSV题材路由，支持关键词匹配 |
| `AntiPatternAggregator` | `infra/story_contracts/anti_patterns.py` | 汇总去重anti-patterns |
| `ContractPersister` | `infra/story_contracts/persister.py` | JSON/MD文件持久化 |
| `ContractPaths` | `infra/story_contracts/paths.py` | 路径管理工具 |

### 2.3 目录结构

```
novel-factory/
├── .story-system/                  # 新增：合约持久化目录
│   ├── MASTER_SETTING.json          # 主设定合约
│   ├── MASTER_SETTING.md            # 人类可读视图
│   ├── anti_patterns.json           # 反套路约束
│   └── chapters/                    # 章节级合约（未来扩展）
│       └── chapter_XXX.json
├── rules/
│   └── story_contracts/             # 新增：Story Contracts规则
│       ├── 题材与调性推理.csv        # 题材路由表
│       └── anti_pattern_fields.yaml # anti-pattern字段映射
└── infra/
    └── story_contracts/             # 新增：合约引擎
        ├── __init__.py
        ├── engine.py
        ├── router.py
        ├── anti_patterns.py
        ├── persister.py
        └── paths.py
```

---

## 3. 数据库设计

### 3.1 合约存储

**存储位置**：`novel-factory/.story-system/`

**MASTER_SETTING.json 结构**：
```json
{
  "meta": {
    "schema_version": "story-contracts/v1",
    "contract_type": "MASTER_SETTING",
    "generated_at": "2026-05-31T12:00:00Z"
  },
  "route": {
    "primary_genre": "玄幻退婚流",
    "genre_aliases": ["退婚流", "废材逆袭"],
    "route_source": "keyword_match"
  },
  "master_constraints": {
    "core_tone": "压抑蓄势后爆裂反击",
    "pacing_strategy": "前压后爆，三章内必须首个反打",
    "forbidden_patterns": ["打脸节奏不能缺最后一拍补刀"]
  },
  "source_trace": [
    {"table": "题材与调性推理", "id": "GR-001", "reason": "keyword_match"}
  ]
}
```

**anti_patterns.json 结构**：
```json
[
  {"text": "打脸节奏不能缺最后一拍补刀", "source_table": "题材与调性推理", "source_id": "GR-001"},
  {"text": "配角不能压过主角兑现", "source_table": "题材与调性推理", "source_id": "GR-001"}
]
```

---

## 4. CSV格式设计

### 4.1 题材与调性推理.csv 字段

| 字段名 | 说明 | 示例 |
|--------|------|------|
| 编号 | 路由ID | GR-001 |
| 分类 | 路由类型 | 题材路由 |
| 关键词 | 匹配关键词 | 玄幻退婚流\|退婚打脸 |
| 意图与同义词 | 同义词 | 退婚流\|废材逆袭 |
| 题材/流派 | 主标签 | 玄幻退婚流 |
| 题材别名 | 同义标签 | 退婚流\|废材逆袭 |
| 核心调性 | 全局情绪基调 | 压抑蓄势后爆裂反击 |
| 节奏策略 | 开局与兑现节奏 | 前压后爆，三章内必须首个反打 |
| 强制禁忌/毒点 | 题材级绝对红线 | 打脸节奏不能缺最后一拍补刀\|配角不能压过主角兑现 |
| 推荐基础检索表 | 默认基础检索表 | 命名规则\|人设与关系 |
| 推荐动态检索表 | 默认动态检索表 | 桥段套路\|爽点与节奏\|场景写法 |

---

## 5. API设计

### 5.1 CLI命令

```bash
# 生成合约
lingwen.py story-contract "玄幻退婚流" --persist

# 指定章节
lingwen.py story-contract "玄幻退婚流" --chapter 1 --persist

# 指定题材
lingwen.py story-contract "压抑后爆" --genre 都市 --persist
```

### 5.2 Python接口

```python
from infra.story_contracts import StoryContractEngine

# 构建合约
engine = StoryContractEngine()
contract = engine.build(query="玄幻退婚流", genre=None, chapter=1)

# 持久化
engine.persist(project_root, contract)

# 读取合约
contract = engine.load(project_root)
```

---

## 6. Context注入设计

### 6.1 注入时机

在 `hooks.yaml` 中配置：

```yaml
hooks:
  - name: story_contract_inject
    trigger: BEFORE_WRITE
    action: inject_story_contract
```

### 6.2 注入内容

注入到Context的 `story_contract` section：

```json
{
  "story_contract": {
    "route": {"primary_genre": "..."},
    "master_constraints": {
      "core_tone": "...",
      "pacing_strategy": "...",
      "forbidden_patterns": [...]
    },
    "anti_patterns": [...]
  }
}
```

---

## 7. 与现有系统的集成

### 7.1 现有系统不变

- S1-S11质量框架：**不受影响**
- 追读力系统：**不受影响**
- CLI命令：**新增story-contract命令**
- 工作流状态：**不受影响**

### 7.2 集成点

| 现有组件 | 集成方式 |
|----------|----------|
| hooks.yaml | BEFORE_WRITE触发器 |
| context_manager | 新增section注入 |
| 现有CSV规则 | 复用（路径规则） |
| workflow.db | 新增合约表（可选） |

---

## 8. 实现任务

### Task 1: 基础路径层
- StoryContractPaths类
- merge规则

### Task 2: 题材路由引擎
- GenreRouter
- CSV加载
- 关键词匹配

### Task 3: Anti-Pattern聚合器
- 多源anti-patterns汇总
- 去重逻辑

### Task 4: 持久化引擎
- JSON写入
- Markdown渲染
- Marker安全更新

### Task 5: CLI集成
- story-contract子命令
- hooks.yaml配置

### Task 6: Context注入
- section定义
- 加载逻辑

---

## 9. 变更记录

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-05-31 | v1.0 | 初稿 |
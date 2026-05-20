# 长期记忆检索策略

> **版本**：v1.0
> **适用范围**：灵文小说工厂记忆系统
> **日期**：2026-05-20

---

## 概述

长期记忆检索是小说工厂系统的核心能力，决定了 AI 在创作时能否有效利用已积累的世界观、人物、情节线索等知识。本文档定义了检索策略的选择逻辑、配置参数和最佳实践。

---

## 检索架构

```
用户/Agent 查询
       ↓
┌─────────────────┐
│   Query Engine  │ ← 解析查询意图
└────────┬────────┘
         ↓
┌─────────────────┐
│  Query Helpers  │ ← 查询转换/扩展
└────────┬────────┘
         ↓
┌─────────────────┐
│  Vector Search  │ ← 语义相似度检索
└────────┬────────┘
         ↓
┌─────────────────┐
│  Keyword Search │ ← BM25/TF-IDF 补充
└────────┬────────┘
         ↓
┌─────────────────┐
│    Reranker     │ ← 结果重排序
└────────┬────────┘
         ↓
    检索结果返回
```

---

## 检索场景分类

### 场景一：角色查询

**触发条件**：询问角色信息、状态变化、行为动机

**检索策略**：
```
1. 优先检索角色集合（character_profiles）
2. 使用角色名+特征描述的复合查询
3. 设定 top_k=3，角色信息密度高，不需要太多结果
4. 启用角色状态过滤器（chapter_range 限制）
```

**配置示例**：
```yaml
retrieval_scenarios:
  character_query:
    collection: "character_profiles"
    top_k: 3
    filters:
      - field: "chapter_range"
        condition: "overlap_with_current_chapter"
    hybrid_alpha: 0.6  # 向量权重降低，关键词权重提高
```

### 场景二：情节查询

**触发条件**：询问某个情节的发展、伏笔回收、因果关系

**检索策略**：
```
1. 检索情节线索集合（plot_threads）
2. 使用时间段+情节类型复合查询
3. 设定 top_k=5，情节线索可能分散在多个章节
4. 启用时间线过滤器（只检索当前章节之前的线索）
```

**配置示例**：
```yaml
retrieval_scenarios:
  plot_query:
    collection: "plot_threads"
    top_k: 5
    filters:
      - field: "resolved"
        condition: "false_or_current_chapter"
      - field: "chapter_range"
        condition: "before_current"
    hybrid_alpha: 0.8  # 向量权重提高
```

### 场景三：世界观查询

**触发条件**：询问设定、规则、势力关系、世界观细节

**检索策略**：
```
1. 检索世界观集合（world_settings）
2. 使用设定名+领域分类查询
3. 设定 top_k=3，世界观信息稳定，不需要太多结果
4. 启用分类过滤器（realm_system/faction_relations）
```

**配置示例**：
```yaml
retrieval_scenarios:
  world_query:
    collection: "world_settings"
    top_k: 3
    filters:
      - field: "category"
        condition: "in_list"
    hybrid_alpha: 0.5  # 平衡检索
```

### 场景四：全文上下文查询

**触发条件**：写作时需要类似场景的参考、风格参考

**检索策略**：
```
1. 检索正文片段集合（body_chunks）
2. 使用当前章节的叙事风格+情感基调查询
3. 设定 top_k=5，参考多个类似段落
4. 启用相似度阈值过滤（score < 0.7 的结果丢弃）
```

**配置示例**：
```yaml
retrieval_scenarios:
  context_query:
    collection: "body_chunks"
    top_k: 5
    filters:
      - field: "min_similarity"
        condition: ">= 0.7"
    hybrid_alpha: 0.9  # 向量权重最高
```

---

## 检索参数详解

### top_k 参数

| 场景 | 推荐值 | 理由 |
|------|--------|------|
| 角色查询 | 3 | 角色信息密度高，3条足够 |
| 情节查询 | 5 | 情节线索可能分散 |
| 世界观查询 | 3 | 设定信息稳定 |
| 上下文查询 | 5 | 需要多个参考 |
| 快速检索 | 1 | 只需最佳匹配 |

### hybrid_alpha 参数

控制向量检索和关键词检索的权重平衡：

```
hybrid_alpha = 0.0  →  纯关键词检索（BM25）
hybrid_alpha = 0.5  →  各50%权重
hybrid_alpha = 1.0  →  纯向量检索（语义相似度）
```

**场景选择指南**：
- 有明确关键词：用低 alpha（如 0.3）
- 概念模糊需要语义理解：用高 alpha（如 0.8）
- 混合场景：用中 alpha（如 0.5-0.7）

### min_similarity 参数

过滤低质量检索结果：

| 阈值 | 效果 |
|------|------|
| > 0.9 | 非常严格，几乎完全匹配 |
| 0.7 - 0.9 | 标准过滤，去除噪声 |
| 0.5 - 0.7 | 宽松过滤，保留更多候选 |
| < 0.5 | 几乎不过滤，不推荐 |

---

## 查询扩展策略

### 角色名扩展

```
原始查询："林夜"
扩展查询：
- "林夜"
- "林夜 主角"
- "林夜 修为"
- "林夜 性格"
```

### 时间范围扩展

```
原始查询：ch050 的角色状态
扩展查询：
- chapter_range 包含 ch050
- chapter_range 在 ch040-ch060（扩大窗口）
- 如果是重要角色，扩展到整卷（ch001-ch120）
```

### 同义词扩展

```
世界观查询：
- "修仙" → ["修仙", "修真", "练气", "筑基"]
- "皇朝" → ["皇朝", "帝国", "王朝", "皇权"]
```

---

## LRU 缓存策略

用于高频检索词的热数据缓存：

### 缓存配置

```yaml
cache:
  enabled: true
  max_size: 1000  # 最大缓存条目数
  ttl_seconds: 3600  # 1小时后过期
  eviction_policy: "lru"  # 最近最少使用
```

### 缓存键设计

```
缓存键 = hash(collection + query_text + filters)
```

### 缓存失效条件

1. 时间过期（TTL）
2. 对应 collection 发生更新
3. 手动清除（rarely needed）

---

## 多集合联合检索

对于复杂查询需要检索多个集合：

### 角色+情节联合

```
场景：询问某个角色在某个情节中的表现

1. 并行检索：
   - character_profiles (top_k=2)
   - plot_threads (top_k=3)

2. 结果合并：
   - 计算每条结果的相关度分数
   - 按分数排序
   - 过滤重复（如果角色同时出现在情节中）

3. 格式化输出：
   - 优先展示角色信息
   - 其次展示情节信息
```

### 世界观+正文联合

```
场景：某个设定的实际应用场景

1. 第一阶段：检索世界观设定
2. 第二阶段：用设定信息扩展查询
3. 第三阶段：检索正文中的应用示例
4. 合并返回
```

---

## 检索结果后处理

### 去重策略

```
1. 检查 content_hash 是否重复
2. 如果是同一段落的不同 chunk，合并
3. 如果是不同来源的相似内容，保留最高分
```

### 上下文补全

```
当检索结果的上下文不完整时：
1. 向前扩展：读取前一个 chunk
2. 向后扩展：读取后一个 chunk
3. 扩展范围：通常为 200-500 字
```

### 格式化输出

```
检索结果格式：
{
  "content": "检索到的文本内容",
  "source": {
    "collection": "来源集合",
    "chapter": "所属章节",
    "score": 0.85
  },
  "metadata": {
    "type": "character_profile / plot_thread / world_setting",
    "relevance": "high / medium / low"
  }
}
```

---

## 性能优化

### 批量检索

```
当需要检索多个独立查询时：
1. 合并为批量请求（batch query）
2. 向量数据库通常支持批量处理
3. 减少网络往返次数
```

### 异步检索

```
对于不阻塞主流程的检索：
1. 使用异步检索
2. 结果写入缓冲区
3. 主流程完成后读取结果
4. 适用于预热缓存、后台更新
```

### 预热策略

```
新章节开始前：
1. 检索本章涉及的角色（预热角色缓存）
2. 检索本章涉及的情节线索（预热情节缓存）
3. 检索本章的世界观设定（预热世界观缓存）

减少写作时的检索延迟
```

---

## 监控与调优

### 关键指标

```
1. 检索延迟（latency）：P50 / P95 / P99
2. 缓存命中率（hit rate）
3. 结果质量评分（用户反馈）
4. 零结果率（no result rate）
```

### 调优周期

- 每周检查一次检索质量指标
- 根据用户反馈调整场景配置
- 每月评估 top_k 和 hybrid_alpha 的有效性

---

## 配置示例：完整场景配置

```yaml
retrieval_scenarios:
  character_query:
    collection: "character_profiles"
    top_k: 3
    hybrid_alpha: 0.6
    filters:
      - field: "chapter_range"
        condition: "overlap_with_current_chapter"
    min_similarity: 0.7

  plot_query:
    collection: "plot_threads"
    top_k: 5
    hybrid_alpha: 0.8
    filters:
      - field: "resolved"
        condition: "false_or_current_chapter"
      - field: "chapter_range"
        condition: "before_current"
    min_similarity: 0.65

  world_query:
    collection: "world_settings"
    top_k: 3
    hybrid_alpha: 0.5
    filters:
      - field: "category"
        condition: "in_list"
    min_similarity: 0.75

  context_query:
    collection: "body_chunks"
    top_k: 5
    hybrid_alpha: 0.9
    filters:
      - field: "min_similarity"
        condition: ">= 0.7"
    min_similarity: 0.7

cache:
  enabled: true
  max_size: 1000
  ttl_seconds: 3600
  eviction_policy: "lru"
```

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-05-20 | 初始版本，定义检索策略框架 |
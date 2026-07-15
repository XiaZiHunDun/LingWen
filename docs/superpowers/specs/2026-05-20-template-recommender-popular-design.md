# 模板推荐引擎 - 功能扩展设计

**日期**: 2026-05-20
**任务**: 方向C-模板推荐引擎

## 目标

为 `TemplateRecommender` 类新增 `get_popular_templates(limit)` 方法，实现基于综合评分的最受欢迎模板排行。

## 综合评分公式

```
popularity_score = use_count * success_rate * (avg_score / 10)
```

| 因子 | 说明 | 范围 |
|------|------|------|
| `use_count` | 使用次数（热度） | 0~N |
| `success_rate` | 成功率（质量稳定性） | 0.0~1.0 |
| `avg_score` | 平均评分（用户满意度） | 0.0~10.0 |
| `avg_score / 10` | 归一化因子 | 0.0~1.0 |

## 实现方案

### 新增方法

```python
def get_popular_templates(self, limit: int = 10) -> List[TemplateMetadata]:
    """
    获取最受欢迎的模板（按综合评分排序）

    Args:
        limit: 返回前N个，默认为10

    Returns:
        按热度综合评分降序排列的模板列表
    """
```

### 排序逻辑

1. 从 `00_模板索引.yaml` 加载所有模板的统计信息（`use_count`, `success_rate`, `avg_score`）
2. 过滤掉 `use_count == 0` 的模板（新模板不参与排行）
3. 计算综合分数：`score = use_count * success_rate * (avg_score / 10)`
4. 按分数降序排列，返回前 `limit` 个

### 返回值类型

返回 `List[TemplateMetadata]`，包含完整的模板元数据，便于调用方展示或进一步处理。

如需详细评分信息，可扩展为返回 `List[Tuple[TemplateMetadata, float]]`。

## 影响范围

- **文件**: `novel-factory/10_方法论/PART3_工具集/提示词模板库/template_recommender.py`
- **依赖**: `00_模板索引.yaml` 中的 `use_count`, `success_rate`, `avg_score` 字段
- **兼容性**: 向后兼容，不影响现有 `recommend()` 方法

## 验证方式

```python
# 测试用例
recommender = TemplateRecommender(assembler)
popular = recommender.get_popular_templates(limit=5)
for i, (template, score) in enumerate(popular, 1):
    print(f"#{i} {template.name} - score: {score:.3f}")
```
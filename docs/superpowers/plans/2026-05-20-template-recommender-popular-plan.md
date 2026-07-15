# 模板推荐引擎 - get_popular_templates 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `TemplateRecommender` 类添加 `get_popular_templates(limit)` 方法，按综合评分排序返回最受欢迎的模板

**Architecture:** 在现有 `TemplateRecommender` 类中添加单一方法，加载 `00_模板索引.yaml` 中的使用统计信息，计算综合评分后排序返回

**Tech Stack:** Python 3.13, pytest, YAML

---

## 文件结构

- **Modify:** `novel-factory/10_方法论/PART3_工具集/提示词模板库/template_recommender.py`
- **Test:** `novel-factory/10_方法论/PART3_工具集/提示词模板库/tests/test_template_recommender.py`

---

## 任务分解

### Task 1: 添加 get_popular_templates 方法

**Files:**
- Modify: `novel-factory/10_方法论/PART3_工具集/提示词模板库/template_recommender.py`

- [ ] **Step 1: 添加方法实现**

在 `TemplateRecommender` 类中添加以下方法：

```python
def get_popular_templates(self, limit: int = 10) -> List[TemplateMetadata]:
    """
    获取最受欢迎的模板（按综合评分排序）

    综合评分公式: score = use_count * success_rate * (avg_score / 10)

    Args:
        limit: 返回前N个，默认为10

    Returns:
        按热度综合评分降序排列的模板列表（不含use_count=0的模板）
    """
    if not self.template_stats:
        return []

    scored_templates = []
    for template_id, stats in self.template_stats.items():
        use_count = stats.get('use_count', 0)
        # 过滤掉未使用的模板
        if use_count == 0:
            continue

        success_rate = stats.get('success_rate', 0.0)
        avg_score = stats.get('avg_score', 0.0)

        # 计算综合评分
        score = use_count * success_rate * (avg_score / 10)
        scored_templates.append((template_id, score))

    # 按分数降序排列
    scored_templates.sort(key=lambda x: x[1], reverse=True)

    # 获取前limit个模板元数据
    results = []
    for template_id, score in scored_templates[:limit]:
        template = self.assembler.get_template(template_id)
        if template:
            results.append(template)

    return results
```

- [ ] **Step 2: 验证文件语法**

Run: `python -m py_compile novel-factory/10_方法论/PART3_工具集/提示词模板库/template_recommender.py`
Expected: 无输出（语法正确）

---

### Task 2: 编写测试

**Files:**
- Create: `novel-factory/10_方法论/PART3_工具集/提示词模板库/tests/test_template_recommender.py`

- [ ] **Step 1: 创建测试文件**

```python
#!/usr/bin/env python3
"""模板推荐引擎测试"""
import pytest
from unittest.mock import MagicMock, patch
from template_recommender import TemplateRecommender, TemplateScore
from prompt_assembler import TemplateCategory


@pytest.fixture
def mock_assembler():
    """创建模拟的 PromptAssembler"""
    assembler = MagicMock()

    # 创建模拟模板
    mock_templates = {
        "outline_full_novel_v1": MagicMock(
            id="outline_full_novel_v1",
            name="全文大纲",
            category=TemplateCategory.OUTLINE,
            status="active",
            care_elements={"result_metrics": ["S1", "S2", "S6", "S7"]},
            temperature=MagicMock(recommended=0.6, min_value=0.5, max_value=0.7)
        ),
        "continuation_standard_v1": MagicMock(
            id="continuation_standard_v1",
            name="标准续写",
            category=TemplateCategory.CONTINUATION,
            status="active",
            care_elements={"result_metrics": ["S1", "S2", "S3", "S5", "S6"]},
            temperature=MagicMock(recommended=0.7, min_value=0.6, max_value=0.8)
        ),
    }
    assembler.get_template.side_effect = lambda name: mock_templates.get(name)
    assembler.list_templates.return_value = list(mock_templates.keys())

    return assembler


@pytest.fixture
def mock_index_file(tmp_path):
    """创建模拟的模板索引文件"""
    index_content = """
templates:
  - id: outline_full_novel_v1
    name: 全文大纲
    use_count: 10
    success_rate: 0.8
    avg_score: 8.5
  - id: continuation_standard_v1
    name: 标准续写
    use_count: 5
    success_rate: 0.9
    avg_score: 7.0
  - id: new_template_v1
    name: 新模板
    use_count: 0
    success_rate: 0.0
    avg_score: 0.0
"""
    index_file = tmp_path / "00_模板索引.yaml"
    index_file.write_text(index_content)
    return str(index_file)


class TestGetPopularTemplates:
    """get_popular_templates 方法测试"""

    def test_returns_templates_sorted_by_popularity_score(self, mock_assembler, mock_index_file):
        """测试返回按综合评分排序的模板"""
        recommender = TemplateRecommender(mock_assembler, mock_index_file)
        results = recommender.get_popular_templates(limit=5)

        # 验证返回顺序（综合评分: 10*0.8*0.85=6.8 vs 5*0.9*0.7=3.15）
        assert len(results) == 2  # 新模板use_count=0被过滤
        assert results[0].id == "outline_full_novel_v1"  # 6.8分最高

    def test_respects_limit_parameter(self, mock_assembler, mock_index_file):
        """测试limit参数限制返回数量"""
        recommender = TemplateRecommender(mock_assembler, mock_index_file)
        results = recommender.get_popular_templates(limit=1)

        assert len(results) == 1
        assert results[0].id == "outline_full_novel_v1"

    def test_excludes_unused_templates(self, mock_assembler, mock_index_file):
        """测试排除use_count=0的模板"""
        recommender = TemplateRecommender(mock_assembler, mock_index_file)
        results = recommender.get_popular_templates(limit=10)

        # 验证新模板未返回
        template_ids = [t.id for t in results]
        assert "new_template_v1" not in template_ids

    def test_empty_list_when_no_stats(self, mock_assembler):
        """测试无统计信息时返回空列表"""
        recommender = TemplateRecommender(mock_assembler, index_file=None)
        # 模拟template_stats为空
        recommender.template_stats = {}

        results = recommender.get_popular_templates()
        assert results == []


class TestRecommend:
    """现有 recommend 方法回归测试"""

    def test_recommend_returns_scored_templates(self, mock_assembler, mock_index_file):
        """测试 recommend 方法正常返回"""
        recommender = TemplateRecommender(mock_assembler, mock_index_file)
        results = recommender.recommend(
            scene_type="outline_generation",
            genre="玄幻",
            required_metrics=["S1", "S6"]
        )

        assert len(results) > 0
        assert all(isinstance(r, TemplateScore) for r in results)
```

- [ ] **Step 2: 运行测试**

Run: `cd novel-factory && python -m pytest "10_方法论/PART3_工具集/提示词模板库/tests/test_template_recommender.py" -v`

Expected: 所有测试通过

---

## 执行选项

**1. Subagent-Driven (recommended)** -  dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
# tools/legacy/ — 归档的旧工具

> 2026-06-03 归档:这 20 个脚本在 v9.x 重构后**无任何外部 import、无测试、
> 无 .sh 脚本调用、无文档引用**。它们的职责已被 lingwen.py CLI + 新
> 工具包替代,继续留在 tools/ 会误导"找工具请来这里"。

## 归档列表(20 个)

| 文件 | 原职责 | 替代方案 |
|------|--------|----------|
| `anti_trope_generator.py` | 反套路生成(v1) | `tools/anti_trope_enhancer.py` |
| `continue_quality_check.py` | 续写质检(早期实验) | 已废弃 |
| `contradiction_check.py` | 矛盾检测(早期实验) | `infra/consistency/checkers/` |
| `fix_ai_traces.py` | AI 痕迹修复 | `lingwen.py repair --track ai_trace` |
| `fix_character_consistency.py` | 角色一致性修复 | `tools/llm_quality_deep_check.py` LLM 增强 |
| `fix_worldview.py` | 世界观统一修复 | `lingwen.py repair --track worldview` |
| `generate_chapter_outlines.py` | 章节大纲生成(脚本) | `infra/agent_system/agents/outline_master/` |
| `llm_character_arc_analyzer.py` | 角色弧光 LLM 分析 | `tools/llm_quality_deep_check.py` 内置 |
| `llm_outline_quality_check.py` | 大纲 LLM 质检(独立工具) | 合并入 `tools/llm_quality_deep_check.py` |
| `llm_polish_chapters.py` | LLM 章节润色 | `tools/claude_key_chapter_polisher.py` |
| `llm_protagonist_charm_analyzer.py` | 主角魅力 LLM 分析 | `tools/llm_quality_deep_check.py` 内置 |
| `llm_readability_analyzer.py` | 可读性 LLM 分析 | `tools/llm_quality_deep_check.py` 内置 |
| `minimax_batch_review.py` | 批量审核(MiniMax 私有) | 已替换为通用 LLM 工具 |
| `minimax_chapter_review.py` | 单章审核(MiniMax 私有) | 已替换为通用 LLM 工具 |
| `parallel_batch.py` | 并行批处理(早期) | `tools/batch_repair.py` |
| `regression_test.py` | 回归测试(脚本式) | `pytest tests/` |
| `test_api.py` | API 调试脚本 | 不应放在 tools/ |
| `test_cross_chapter_checker.py` | 跨章检测器调试 | 不应放在 tools/ |
| `verify_repair_quality.py` | 修复后验证(独立工具) | `lingwen.py verify` |
| `whitelist_manager.py` | 白名单管理 | 已无引用需求 |

## 如何恢复

如果某个工具确实需要复活:

```bash
git mv tools/legacy/<file>.py tools/
# 修复 import 路径(可能需要适配 v9.x API 变化)
```

历史通过 `git mv` 保留 — `git log --follow tools/legacy/<file>.py`
可以看到完整的修改历史,`git blame` 也能正常工作。

## 归档原则

满足以下**所有**条件的 tools/*.py 文件视为可归档:

1. 无 `from tools.X import` / `import tools.X` 外部 import
   (排除 `tools/__init__.py` 自身 re-export)
2. 无任何测试文件 `tests/**/test_X.py` 引用
3. 无 `*.sh` 脚本调用
4. 无 `.md` / `.yaml` 文档引用
5. 不在 `tools/__init__.py` 的 `__all__` 中
6. 不属于 `tools/<subpkg>/` 子包成员

满足 1-4 即"无外部依赖" + 满足 5-6 即"非公开 API" = 死代码。

# infra/tools/legacy/consistency/ — 归档的旧检测器

> 2026-06-03 归档:这 16 个 0 外部 import 的 check/fix 脚本在 v9.x 重构后
> 没有任何运行时引用(无 `from infra.tools.consistency.X` 引用,无
> 测试调用,无文档/脚本通过路径触发)。它们的工作被
> `infra/consistency/checkers/`(类基检测器)+ `tools/verify_quality.py`
> + `tools/llm_quality_deep_check.py` 替代。

## 归档列表(16 个)

| 文件 | 原职责 | 替代方案 |
|------|--------|----------|
| `check_battle_density.py` | 战斗场景密度(3-tier 关键词) | `infra/consistency/checkers/battle_checker.py` |
| `check_character_activity.py` | 角色"工具人"检测 | `tools/llm_quality_deep_check.py` LLM 增强 |
| `check_character_arc_llm.py` | 角色弧光 LLM 提示词生成 | `tools/llm_quality_deep_check.py` 内置 |
| `check_dialogue_style.py` | 对话风格一致性 | `infra/consistency/checkers/dialogue_authenticity_checker.py` |
| `check_duplicate.py` | 章节重复检测 | `tools/llm_quality_deep_check.py` 整合 |
| `check_emotional_rhythm.py` | 情感节奏 | `infra/consistency/checkers/pacing_checker.py` |
| `check_faction_relations.py` | 阵营关系抽取 | 无明确替代,需用 LLM |
| `check_plot_device_tracking.py` | 伏笔回收率(2.x 版本) | `infra/consistency/checkers/foreshadow_checker.py` (class 基) |
| `check_realm_system.py` | 境界系统校验 | 无明确替代(自定义规则) |
| `check_scene_density.py` | 场景密度 | `infra/consistency/checkers/scene_transition_checker.py` |
| `check_scene_logic.py` | 场景逻辑(仅被已归档的 fix_island 引用) | `infra/consistency/checkers/scene_transition_checker.py` |
| `check_segment_relevance.py` | 段落关联度 | `tools/llm_quality_deep_check.py` 整合 |
| `check_template_sentences.py` | 模板句检测 | `tools/template_substitute.py` + `tools/llm_quality_deep_check.py` |
| `fix_island_chapters_v2.py` | 孤岛章节修复 | 已废弃(无引用) |
| `fix_naming.py` | 命名修复 | `tools/llm_quality_deep_check.py` 整合 |
| `quality_engine.py` | 独立 quality orchestrator | `infra/quality/coordinator.py` 统一 |

## 留下的 3 个文件

`infra/tools/consistency/` 当前保留 4 个文件:

- `__init__.py` — 包初始化
- `check_naming.py` — 被 `tests/test_quality_checker.py:14` bare-import
- `integrity_checker.py` — 被 `tests/test_quality_checker.py:15` bare-import
- `run_quality_checks.py` — 被 `infra/hooks/actions/run_checker.py:158` 引用
  (P5-1 同时修复了 broken import 路径 `tools.consistency.*` → `infra.tools.consistency.*`)

## 如何恢复

如果某个文件确实需要复活:

```bash
git mv infra/tools/legacy/consistency/<file>.py infra/tools/consistency/
# 修复 import 路径(可能需要适配 v9.x API 变化)
```

历史通过 `git mv` 保留 — `git log --follow infra/tools/legacy/consistency/<file>.py`
可以看到完整的修改历史,`git blame` 也能正常工作。

## 归档原则

满足以下**所有**条件的 `infra/tools/consistency/*.py` 文件视为可归档:

1. 无 `from infra.tools.consistency.X import` / `import infra.tools.consistency.X`
   外部 import
2. 无 `from X import` + `sys.path` 注入形式的 bare import 测试
3. 无 `.yaml` / `.sh` 文档引用(纯描述性 doc 不算)
4. 不在 `infra/tools/consistency/__init__.py` 的 `__all__` 中
5. 非 `tests/test_quality_checker.py` 等关键测试的 fixture 依赖
6. 非 `infra/hooks/actions/` 任何 Action 触发的 runtime 依赖

满足 1-3 即"无外部依赖",满足 4-6 即"非基础设施"。

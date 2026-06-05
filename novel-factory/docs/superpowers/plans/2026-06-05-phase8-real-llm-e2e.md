# Phase 8 Implementation Plan — Real LLM E2E (polish_merge S1-S8 验证)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 加 2 个 opt-in 真实 LLM 测试, 验证 Phase 7.5 polish_merge S1-S8 评分在生产路径下产出真实分数. 默认 SKIP (无 API key), opt-in 跑 (`ANTHROPIC_API_KEY=... pytest ...`).

**Architecture:**
- 1 新文件: `tests/agent_system/test_novel_writing_real_llm.py` (~120L)
- HAIKU 模型 (`claude-haiku-4-5-20251001`) + timeout=180 + max_retries=1 + tmp_path 隔离
- Skip pattern: `@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"))` (跟 test_e2e_workflow.py 一致)
- 复用 `tests/agent_system/_e2e_helpers.py::make_master_with_router` (Phase 7.1 已就位)

**Tech Stack:** Python 3.13, pytest 9, Anthropic API, HAIKU 4.5

---

## Task 1: RED — 写测试文件 (默认 SKIP)

**Files:**
- Create: `tests/agent_system/test_novel_writing_real_llm.py` (NEW, ~120L)

### Step 1.1: 写完整测试文件

**Create** `tests/agent_system/test_novel_writing_real_llm.py`:

```python
"""Phase 8: Real LLM E2E — 验证 polish_merge S1-S8 评分在生产路径下产出真实分数.

默认 SKIP (无 ANTHROPIC_API_KEY), opt-in 跑:
    export ANTHROPIC_API_KEY=sk-ant-...
    pytest tests/agent_system/test_novel_writing_real_llm.py -v

成本: HAIKU × 6 LLM calls ≈ $0.005-0.020 per test.

跟 tests/agent_system/test_master_controller_e2e_real_llm.py 区别:
- test_master_controller_e2e_real_llm.py: 文件名误导, 实际用 StubProvider
- test_novel_writing_real_llm.py (本文件): 真实 Anthropic API 调用
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

_REQUIRES_ANTHROPIC_KEY = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="Phase 8 real LLM test requires ANTHROPIC_API_KEY env var",
)


def _make_real_router():
    """构造单 Anthropic provider 的 AIRouter, 用 HAIKU 模型 (Phase 7.5 spec 锁 S1-S8 评分用 HAIKU).

    Returns:
        AIRouter: 单 anthropic provider 的 router, primary=anthropic, failover=False
    """
    from infra.ai_service import ProviderConfig
    from infra.ai_service.anthropic_provider import AnthropicProvider
    from infra.ai_service.router import AIRouter

    provider = AnthropicProvider(ProviderConfig(
        api_key=os.environ["ANTHROPIC_API_KEY"],
        model="claude-haiku-4-5-20251001",
        timeout=180,  # 留够 6 LLM call headroom
        max_retries=1,  # fail-fast, 不阻塞
    ))
    return AIRouter(
        config={"anthropic": provider.config},
        primary_provider="anthropic",
        enable_failover=False,  # 单 provider, 失败立即 raise
    )


def _assert_s1_s8_score_dict(scores: dict, label: str) -> None:
    """验证 S1-S8 评分 dict 合法: 8 keys + int + 0-10 范围"""
    assert set(scores.keys()) == {"S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"}, (
        f"{label} keys 不完整: {set(scores.keys())}"
    )
    for s1_s8, score in scores.items():
        assert isinstance(score, int), (
            f"{label}[{s1_s8}] 应为 int, 实际 {type(score).__name__}: {score!r}"
        )
        assert 0 <= score <= 10, f"{label}[{s1_s8}]={score} 超出 0-10 范围"


@_REQUIRES_ANTHROPIC_KEY
class TestNovelWritingRealLLM:
    """Phase 8: novel_writing.yaml 7 节点端到端, 验证 polish_merge S1-S8 真实评分."""

    def test_novel_writing_yaml_polish_merge_produces_s1_s8_scores(self, tmp_path: Path) -> None:
        """novel_writing.yaml 端到端跑通, 验证 polish_merge.output 含 S1-S8 真实评分.

        跑 6 LLM calls: write + audit + 2 emotional_pacing + 1 ai_trace_removal + 1 polish_merge.
        """
        from tests.agent_system._e2e_helpers import make_master_with_router

        router = _make_real_router()
        master = make_master_with_router(state_dir=tmp_path, router=router)

        result = master.run_workflow(
            workflow_name="novel_writing",
            initial_inputs={
                "chapter_num": 1,
                "outline": {"chapters": [{
                    "num": 1, "title": "第一章 测试", "events": ["e1"],
                    "word_count_target": 800,  # 短内容加速 HAIKU 处理
                }]},
                "characters": [],
                "memory_context": {},
                "style_guide": {},
                "timeline": [],
                "use_llm": True,
            },
            max_backtracks=0,  # fail fast, 不重试 (避免 6×2=12 LLM calls 成本 +10x)
        )

        # 1. workflow 跑通
        summary = result["summary"]
        assert summary.completed >= 6, f"期望 ≥6 节点完成, 实际 {summary.completed}"
        assert summary.failed == 0, f"期望 0 失败, 实际 {summary.failed}"

        # 2. polish_merge 节点走 LLM 路径 (非 fallback)
        merge_exec = result["executions"]["polish_merge"]
        merge_output = merge_exec.output
        assert merge_output["fallback"] is None, (
            f"polish_merge 应走 LLM 路径, 但 fallback={merge_output['fallback']!r}. "
            f"可能上游 polish variant 内容相同导致 identical fallback"
        )

        # 3. S1-S8 8 维评分真实
        _assert_s1_s8_score_dict(merge_output["scores_a"], "scores_a")
        _assert_s1_s8_score_dict(merge_output["scores_b"], "scores_b")

        # 4. winner + totals 合理
        assert merge_output["winner"] in merge_output["_labels"], (
            f"winner={merge_output['winner']!r} 不在 _labels={merge_output['_labels']!r}"
        )
        assert 0.0 <= merge_output["scores_total_a"] <= 10.0
        assert 0.0 <= merge_output["scores_total_b"] <= 10.0
        assert abs(
            merge_output["scores_total_a"]
            - merge_output["scores_total_b"]
            - merge_output["scores_delta"]
        ) < 1e-6, (
            f"scores_delta={merge_output['scores_delta']} 不等于 "
            f"total_a - total_b={merge_output['scores_total_a'] - merge_output['scores_total_b']}"
        )

        # 5. labels 透传 (Phase 7.6 dashboard 雷达图依赖)
        assert merge_output["_labels"] == ["polish_emotional_pacing", "polish_ai_trace_removal"]


@_REQUIRES_ANTHROPIC_KEY
class TestPolishMergeSynthesisRealLLM:
    """Phase 8: 直接调 polish_merge_synthesis, 1 LLM call 快速验证 Phase 7.5 核心 (~5-10s)."""

    def test_polish_merge_synthesis_with_distinct_contents(self, tmp_path: Path) -> None:
        """2 个不同内容 → 走 LLM 评分路径, 产出 S1-S8 真实分数.

        单独跑: pytest -k PolishMergeSynthesis 5-10s 验证 Phase 7.5 核心.
        """
        from tests.agent_system._e2e_helpers import make_master_with_router

        router = _make_real_router()
        master = make_master_with_router(state_dir=tmp_path, router=router)

        # 2 个不同内容 (短段落, ~400 chars each)
        content_a = "少年握紧拳头, 眼中燃烧着不甘。寒风刺骨, 但他咬牙前行。" * 20
        content_b = "林夕深吸一口气, 心中暗自立下誓言。纵然前路艰险, 亦不退缩。" * 20

        result = master.polish_merge_synthesis(
            content_a, content_b, labels=("emotional", "motivation"),
        )

        # 跟 TestNovelWritingRealLLM 同样的 5 步断言
        assert result["fallback"] is None, (
            f"polish_merge_synthesis 应走 LLM 路径, 但 fallback={result['fallback']!r}"
        )
        _assert_s1_s8_score_dict(result["scores_a"], "scores_a")
        _assert_s1_s8_score_dict(result["scores_b"], "scores_b")
        assert result["winner"] in result["_labels"]
        assert 0.0 <= result["scores_total_a"] <= 10.0
        assert 0.0 <= result["scores_total_b"] <= 10.0
        assert abs(
            result["scores_total_a"] - result["scores_total_b"] - result["scores_delta"]
        ) < 1e-6
        assert result["_labels"] == ["emotional", "motivation"]
```

### Step 1.2: 验证默认 SKIP

```bash
# 默认 (无 ANTHROPIC_API_KEY) — 跑应全 SKIP
unset ANTHROPIC_API_KEY
pytest tests/agent_system/test_novel_writing_real_llm.py -v
# Expected: 2 skipped
```

### Step 1.3: 全量回归验证 (默认 SKIP 不影响其他)

```bash
pytest tests/ -q
# Expected: 2073 passed, 19 skipped (17 原有 + 2 新增 opt-in)
```

---

## Task 2: GREEN (opt-in 验证) — 需要主公手动跑

**WARNING**: 这步需要真实 `ANTHROPIC_API_KEY` 和 6 次 HAIKU 调用 (~30-60s, ~$0.01-0.02), **不在 subagent 跑**.

主公需手动跑:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
pytest tests/agent_system/test_novel_writing_real_llm.py -v
# Expected: 2 passed, 成本 ~$0.01-0.02
```

如果失败, subagent 修代码, 主公再跑直到 pass.

---

## Task 3: ruff 0 + 1 commit + push

### Step 3.1: ruff 检查

```bash
ruff check tests/agent_system/test_novel_writing_real_llm.py
# Expected: All checks passed!
```

### Step 3.2: 1 commit + push

```bash
git add tests/agent_system/test_novel_writing_real_llm.py
git commit -m "feat(agent_system): phase 8 — real LLM E2E (polish_merge S1-S8)

加 2 个 opt-in 真实 LLM 测试, 验证 Phase 7.5 polish_merge S1-S8 评分
在生产路径下产出真实分数:
- TestNovelWritingRealLLM.test_novel_writing_yaml_polish_merge_produces_s1_s8_scores
  (novel_writing.yaml 7 节点端到端, 6 LLM calls, 30-60s, ~\$0.01-0.02)
- TestPolishMergeSynthesisRealLLM.test_polish_merge_synthesis_with_distinct_contents
  (直接调 polish_merge_synthesis, 1 LLM call, 5-10s, ~\$0.003)

默认 SKIP (无 ANTHROPIC_API_KEY), opt-in 跑:
  export ANTHROPIC_API_KEY=sk-ant-...
  pytest tests/agent_system/test_novel_writing_real_llm.py -v

设计:
- HAIKU 模型 (claude-haiku-4-5-20251001) — Phase 7.5 spec 锁 S1-S8 评分用
- timeout=180 (6 LLM calls headroom), max_retries=1 (fail-fast)
- tmp_path 状态隔离 (跟现有 E2E 测试一致)
- 复用 make_master_with_router (Phase 7.1 已就位)
- 9 步断言覆盖: workflow 跑通 + fallback is None + S1-S8 完整 +
  int 范围 0-10 + winner 合法 + totals 一致 + _labels 透传

验证生产路径: JSON parse 正常 + prompt 标签对齐 + 评分范围 + _labels 透传.
不修生产代码 — 失败暴露问题留 Phase 8.1 处理.

Baseline 2073 + 19 skipped (新增 2 skipped)."

git push origin master
```

---

## Task 4: MEMORY.md + 1 行 Phase 8 entry

**File**: `~/.claude/projects/-home-ailearn-projects-AI-Incursion-domains-IP---projects-LingWen/memory/MEMORY.md`

### Step 4.1: 查行数

```bash
wc -l MEMORY.md
# Expected: 196 (Phase 7.6 末)
```

### Step 4.2: 在 Phase 7.6 之后**插入** Phase 8 entry

```markdown
- **Phase 8 (2026-06-05)**: Doc 4 §11 Phase 8 — Real LLM E2E (polish_merge S1-S8 验证) — 加 2 opt-in 真实 LLM 测试 tests/agent_system/test_novel_writing_real_llm.py (NEW, ~120L): TestNovelWritingRealLLM.test_novel_writing_yaml_polish_merge_produces_s1_s8_scores (novel_writing.yaml 7 节点端到端, 6 LLM calls 30-60s) + TestPolishMergeSynthesisRealLLM.test_polish_merge_synthesis_with_distinct_contents (直接调 polish_merge_synthesis, 1 LLM call 5-10s) + _make_real_router helper (HAIKU claude-haiku-4-5-20251001, timeout=180, max_retries=1) + _assert_s1_s8_score_dict 共享断言 (8 keys + int + 0-10 范围); 默认 SKIP (无 ANTHROPIC_API_KEY) 跟 test_e2e_workflow.py 模式一致, opt-in 跑 (export ANTHROPIC_API_KEY=sk-ant-... pytest ...); 9 步断言: workflow 跑通 (completed≥6, failed=0) + fallback is None + S1-S8 完整 + int 范围 0-10 + winner in _labels + totals 0-10 + delta 一致性 (< 1e-6) + _labels 透传 Phase 7.6 dashboard 雷达图依赖; 复用 make_master_with_router (Phase 7.1 已就位) + tmp_path 状态隔离 + max_backtracks=0 fail-fast (避免 6×2=12 LLM calls 成本 +10x); YAGNI: 不改 _e2e_helpers.py / 不加 real_llm marker / 不引入 .env / 不 rename 误导性 test_master_controller_e2e_real_llm.py; 2073 + 19 skipped (新增 2 skipped opt-in), ruff 0; spec docs/superpowers/specs/2026-06-05-phase8-real-llm-e2e-design.md (commit 3bc88a5); plan docs/superpowers/plans/2026-06-05-phase8-real-llm-e2e.md; impl commit <hash> 推送 origin/master
```

### Step 4.3: 验证 < 200 行

```bash
wc -l MEMORY.md
# Expected: < 200 lines
```

---

## 完成定义 (DoD)

- [ ] `tests/agent_system/test_novel_writing_real_llm.py` 新文件 (~120L)
- [ ] `_REQUIRES_ANTHROPIC_KEY` skipif 装饰器 (跟 test_e2e_workflow.py 一致)
- [ ] `_make_real_router()` helper (HAIKU, timeout=180, max_retries=1)
- [ ] `_assert_s1_s8_score_dict()` 共享断言 helper
- [ ] `TestNovelWritingRealLLM.test_novel_writing_yaml_polish_merge_produces_s1_s8_scores` (1 test)
- [ ] `TestPolishMergeSynthesisRealLLM.test_polish_merge_synthesis_with_distinct_contents` (1 test)
- [ ] 默认 (无 API key) 跑全 SKIP, `pytest tests/ -q` 2073 passed + 19 skipped
- [ ] opt-in (有 API key) 跑全 PASS, 6 LLM calls 端到端
- [ ] `ruff check .` 0 warnings
- [ ] 1 impl commit pushed to origin/master
- [ ] MEMORY.md < 200 lines (+ 1 行 Phase 8 entry)

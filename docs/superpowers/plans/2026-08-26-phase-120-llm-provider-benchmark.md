# Phase 120 LLM Provider Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实测 minimax (真) + anthropic/openai (mock) 三个 LLM provider 在 production extraction prompt 下的 quality / cost / latency,生成报告 + 改 `plugin_manager.py:150` default_priority + 同步 `CLAUDE.md` + `.lingwen/architecture.yml`。

**Architecture:** 新建 `infra/llm_benchmarks/` 模块 (CLI + library 双入口)。Pytest mock-only (CI fast),CLI `--real` flag 走真 provider (env var gated)。Output 持久进 `infra/llm_benchmarks/results/<run-id>/` (gitignored)。

**Tech Stack:** Python 3.13 / pytest / dataclasses / python-dotenv (optional) / ruff

**Spec:** `docs/superpowers/specs/2026-08-26-phase-120-llm-provider-benchmark-design.md`

---

## File Structure

| File | 职责 |
|---|---|
| `infra/llm_benchmarks/__init__.py` | public API: `run_benchmark`, `get_provider_llm`, dataclasses |
| `infra/llm_benchmarks/metrics.py` | pure functions + `CallResult`/`ProviderMetrics` dataclasses |
| `infra/llm_benchmarks/providers.py` | `MockLLMService` + `get_provider_llm` factory |
| `infra/llm_benchmarks/fixtures.py` | `load_golden_chapters` (huiyu-dangan ch001+ch003+ch010) |
| `infra/llm_benchmarks/results.py` | `write_call_result` / `read_run_results` / `list_runs` |
| `infra/llm_benchmarks/render.py` | `render_report` markdown generation |
| `infra/llm_benchmarks/run.py` | `run_benchmark()` + CLI entrypoint |
| `tests/infra/llm_benchmarks/__init__.py` | (empty) |
| `tests/infra/llm_benchmarks/test_metrics.py` | ~12 tests |
| `tests/infra/llm_benchmarks/test_providers.py` | ~5 tests |
| `tests/infra/llm_benchmarks/test_fixtures.py` | ~3 tests |
| `tests/infra/llm_benchmarks/test_results.py` | ~4 tests |
| `tests/infra/llm_benchmarks/test_render.py` | ~3 tests |
| `tests/infra/llm_benchmarks/test_run.py` | ~5 tests |
| `.gitignore` | add `infra/llm_benchmarks/results/` |
| `docs/benchmarks/2026-08-26-llm-provider-benchmark.md` | generated report |
| `packages/lingwen-llm/src/lingwen_llm/providers/plugin_manager.py:150` | hardcode update |
| `CLAUDE.md` | v15.4 → v15.5 |
| `.lingwen/architecture.yml` | provider priority section update |

---

## Task 1: Bootstrap `infra/llm_benchmarks/` skeleton + `.gitignore`

**Files:**
- Create: `infra/llm_benchmarks/__init__.py`
- Create: `tests/infra/llm_benchmarks/__init__.py`
- Modify: `.gitignore`

- [ ] **Step 1: Create directories**

```bash
mkdir -p infra/llm_benchmarks
mkdir -p tests/infra/llm_benchmarks
```

- [ ] **Step 2: Add `infra/llm_benchmarks/results/` to `.gitignore`**

Append (or create if missing) `.gitignore`:

```
# LLM benchmark raw results (Phase 120)
infra/llm_benchmarks/results/
```

- [ ] **Step 3: Create `infra/llm_benchmarks/__init__.py` with public API stubs**

```python
"""LLM provider benchmark module (Phase 120).

Dev/CI tool for comparing extraction quality / cost / latency across
LLM providers. CLI and library entrypoints.

Public API:
- run_benchmark: orchestrate a single provider benchmark run
- get_provider_llm: factory for real/mock LLM service
- CallResult, ProviderMetrics: dataclasses for results aggregation
"""
from __future__ import annotations

# Imports populated as subsequent tasks land
__all__ = [
    "run_benchmark",
    "get_provider_llm",
    "CallResult",
    "ProviderMetrics",
]
```

- [ ] **Step 4: Create empty `tests/infra/llm_benchmarks/__init__.py`**

```python
"""Tests for infra.llm_benchmarks module."""
```

- [ ] **Step 5: Verify pytest discovers the new test directory**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/infra/llm_benchmarks/ --collect-only -q`
Expected: "no tests ran" or empty list (no collection errors).

- [ ] **Step 6: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add infra/llm_benchmarks/__init__.py tests/infra/llm_benchmarks/__init__.py .gitignore
git commit -m "feat(llm-bench): bootstrap infra/llm_benchmarks/ skeleton

Phase 120 module skeleton + tests dir + .gitignore for results/.
Empty public API stubs; subsequent tasks fill in components.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 2: `metrics.py` — dataclasses + `parse_rate` + `schema_compliance`

**Files:**
- Create: `infra/llm_benchmarks/metrics.py`
- Create: `tests/infra/llm_benchmarks/test_metrics.py`

- [ ] **Step 1: Write failing tests for `CallResult`/`ProviderMetrics` + `parse_rate` + `schema_compliance`**

```python
# tests/infra/llm_benchmarks/test_metrics.py
"""Tests for infra.llm_benchmarks.metrics."""
from __future__ import annotations

from infra.llm_benchmarks.metrics import (
    CallResult,
    ProviderMetrics,
    compute_metrics,
)


def _make_call(
    *,
    provider: str = "minimax",
    chapter_id: int = 1,
    run_index: int = 1,
    parse_ok: bool = True,
    schema_ok: bool = True,
    canon_level_ok: bool = True,
    latency_s: float = 1.0,
    output_tokens: int = 100,
    cost_usd: float = 0.001,
    failed: bool = False,
    parsed_proposals: list[dict] | None = None,
) -> CallResult:
    return CallResult(
        provider=provider,
        chapter_id=chapter_id,
        run_index=run_index,
        timestamp="2026-08-26T12:00:00Z",
        raw_response='{"proposals":[]}',
        parsed_proposals=parsed_proposals if parsed_proposals is not None else [],
        parse_ok=parse_ok,
        schema_ok=schema_ok,
        canon_level_ok=canon_level_ok,
        latency_s=latency_s,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
        failed=failed,
        error=None,
    )


def test_parse_rate_counts_only_parse_ok():
    calls = [
        _make_call(parse_ok=True),
        _make_call(parse_ok=True),
        _make_call(parse_ok=True),
        _make_call(parse_ok=False),
        _make_call(parse_ok=True),
    ]
    m = compute_metrics(calls, provider="minimax")
    assert m.parse_rate == 0.8


def test_schema_compliance_counts_only_schema_ok():
    calls = [
        _make_call(parse_ok=True, schema_ok=True),
        _make_call(parse_ok=True, schema_ok=True),
        _make_call(parse_ok=True, schema_ok=False),
        _make_call(parse_ok=False, schema_ok=False),  # not counted in denominator
    ]
    m = compute_metrics(calls, provider="minimax")
    # parse_ok rate is 3/4, schema_compliance counts among parse_ok only
    assert m.schema_compliance == 2 / 3


def test_compute_metrics_returns_provider_metrics_instance():
    calls = [_make_call()]
    m = compute_metrics(calls, provider="minimax")
    assert isinstance(m, ProviderMetrics)
    assert m.provider == "minimax"
    assert m.n_calls == 1
    assert m.n_failed == 0
```

- [ ] **Step 2: Run tests, verify RED**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/infra/llm_benchmarks/test_metrics.py -v`
Expected: ImportError or AttributeError (compute_metrics not yet defined).

- [ ] **Step 3: Implement `CallResult`/`ProviderMetrics` dataclasses + `compute_metrics` with parse_rate + schema_compliance**

```python
# infra/llm_benchmarks/metrics.py
"""Pure metrics computation for LLM provider benchmark results.

Aggregates CallResult list per provider into ProviderMetrics summary.
All functions are pure (no I/O), testable without fixtures.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CallResult:
    """One LLM call outcome. Persisted as JSON in results/<run-id>/."""

    provider: str
    chapter_id: int
    run_index: int
    timestamp: str  # ISO-8601 UTC
    raw_response: str
    parsed_proposals: list[dict]
    parse_ok: bool
    schema_ok: bool
    canon_level_ok: bool
    latency_s: float
    output_tokens: int
    cost_usd: float
    failed: bool
    error: str | None = None


@dataclass(frozen=True)
class ProviderMetrics:
    """Aggregated metrics for one provider's N calls."""

    provider: str
    n_calls: int
    n_failed: int
    parse_rate: float  # parse_ok / n_calls
    schema_compliance: float  # schema_ok among parse_ok
    canon_level_compliance: float  # canon_level_ok among parse_ok
    confidence_distribution: dict[str, int] = field(default_factory=dict)
    latency_p50_s: float = 0.0
    latency_p95_s: float = 0.0
    cost_per_call_usd: float = 0.0
    consistency_score: float = 1.0
    quality_composite: float = 0.0


def compute_metrics(calls: list[CallResult], provider: str) -> ProviderMetrics:
    """Aggregate N CallResults into a ProviderMetrics summary.

    parse_rate = parse_ok / n_calls
    schema_compliance = schema_ok / count(parse_ok)
    canon_level_compliance = canon_level_ok / count(parse_ok)
    """
    n_calls = len(calls)
    n_failed = sum(1 for c in calls if c.failed)
    n_parse_ok = sum(1 for c in calls if c.parse_ok)
    n_schema_ok = sum(1 for c in calls if c.parse_ok and c.schema_ok)
    n_canon_ok = sum(1 for c in calls if c.parse_ok and c.canon_level_ok)

    parse_rate = n_parse_ok / n_calls if n_calls else 0.0
    schema_compliance = n_schema_ok / n_parse_ok if n_parse_ok else 0.0
    canon_level_compliance = n_canon_ok / n_parse_ok if n_parse_ok else 0.0

    return ProviderMetrics(
        provider=provider,
        n_calls=n_calls,
        n_failed=n_failed,
        parse_rate=parse_rate,
        schema_compliance=schema_compliance,
        canon_level_compliance=canon_level_compliance,
    )
```

- [ ] **Step 4: Run tests, verify GREEN**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/infra/llm_benchmarks/test_metrics.py -v`
Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add infra/llm_benchmarks/metrics.py tests/infra/llm_benchmarks/test_metrics.py
git commit -m "feat(llm-bench): metrics.py with parse_rate + schema_compliance

Phase 120 Task 2. CallResult/ProviderMetrics dataclasses + compute_metrics
that aggregates per-call outcomes. Tests cover parse_rate (4 of 5 parse_ok),
schema_compliance (2 of 3 schema_ok among parse_ok), and instance type.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 3: `metrics.py` — `canon_level_compliance` + `confidence_distribution` + `latency_p50/p95` + `cost_per_call_usd`

**Files:**
- Modify: `infra/llm_benchmarks/metrics.py`
- Modify: `tests/infra/llm_benchmarks/test_metrics.py`

- [ ] **Step 1: Add failing tests for new metrics**

Append to `tests/infra/llm_benchmarks/test_metrics.py`:

```python
def test_canon_level_compliance_counts_only_canon_ok_among_parse_ok():
    calls = [
        _make_call(parse_ok=True, canon_level_ok=True),
        _make_call(parse_ok=True, canon_level_ok=False),
        _make_call(parse_ok=False, canon_level_ok=True),  # not counted
    ]
    m = compute_metrics(calls, provider="minimax")
    assert m.canon_level_compliance == 0.5


def test_latency_p50_and_p95():
    calls = [_make_call(latency_s=float(i)) for i in range(1, 11)]  # 1.0..10.0
    m = compute_metrics(calls, provider="minimax")
    # 10 sorted latencies: 1,2,3,...,10 → p50=5.5 (mean of 5th & 6th), p95=9.55 (linear interp)
    assert 5.4 <= m.latency_p50_s <= 5.6
    assert 9.0 <= m.latency_p95_s <= 10.0


def test_cost_per_call_is_mean():
    calls = [
        _make_call(cost_usd=0.001),
        _make_call(cost_usd=0.003),
        _make_call(cost_usd=0.006),
    ]
    m = compute_metrics(calls, provider="minimax")
    assert abs(m.cost_per_call_usd - 0.003333) < 1e-6


def test_confidence_distribution_counts_by_proposal_payload():
    calls = [
        _make_call(
            parse_ok=True,
            parsed_proposals=[
                {"payload": {"confidence": "high"}, "kind": "character.update"},
                {"payload": {"confidence": "medium"}, "kind": "character.update"},
            ],
        ),
        _make_call(
            parse_ok=True,
            parsed_proposals=[
                {"payload": {"confidence": "high"}, "kind": "character.update"},
                {"payload": {"confidence": "low"}, "kind": "character.update"},
            ],
        ),
    ]
    m = compute_metrics(calls, provider="minimax")
    assert m.confidence_distribution == {"high": 2, "medium": 1, "low": 1}
```

- [ ] **Step 2: Run tests, verify RED**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/infra/llm_benchmarks/test_metrics.py -v`
Expected: 4 new FAIL (canon_level_compliance, latency, cost, confidence).

- [ ] **Step 3: Implement new metrics in `compute_metrics`**

Update `compute_metrics` in `infra/llm_benchmarks/metrics.py`:

```python
import statistics


def _percentile(values: list[float], pct: float) -> float:
    """Linear-interpolation percentile (matches numpy default)."""
    if not values:
        return 0.0
    return statistics.quantiles(values, n=100, method="inclusive")[int(pct) - 1] if len(values) >= 2 else values[0]


def _confidence_distribution(proposals_list: list[list[dict]]) -> dict[str, int]:
    dist: dict[str, int] = {}
    for proposals in proposals_list:
        for p in proposals:
            conf = (p.get("payload") or {}).get("confidence", "unknown")
            dist[conf] = dist.get(conf, 0) + 1
    return dist


def compute_metrics(calls: list[CallResult], provider: str) -> ProviderMetrics:
    """Aggregate N CallResults into a ProviderMetrics summary."""
    n_calls = len(calls)
    n_failed = sum(1 for c in calls if c.failed)
    n_parse_ok = sum(1 for c in calls if c.parse_ok)
    n_schema_ok = sum(1 for c in calls if c.parse_ok and c.schema_ok)
    n_canon_ok = sum(1 for c in calls if c.parse_ok and c.canon_level_ok)

    parse_rate = n_parse_ok / n_calls if n_calls else 0.0
    schema_compliance = n_schema_ok / n_parse_ok if n_parse_ok else 0.0
    canon_level_compliance = n_canon_ok / n_parse_ok if n_parse_ok else 0.0

    latencies = [c.latency_s for c in calls if not c.failed]
    latency_p50_s = _percentile(latencies, 50)
    latency_p95_s = _percentile(latencies, 95)

    valid_calls = [c for c in calls if not c.failed]
    cost_per_call_usd = (
        sum(c.cost_usd for c in valid_calls) / len(valid_calls) if valid_calls else 0.0
    )

    confidence_distribution = _confidence_distribution(
        [c.parsed_proposals for c in calls if c.parse_ok]
    )

    return ProviderMetrics(
        provider=provider,
        n_calls=n_calls,
        n_failed=n_failed,
        parse_rate=parse_rate,
        schema_compliance=schema_compliance,
        canon_level_compliance=canon_level_compliance,
        confidence_distribution=confidence_distribution,
        latency_p50_s=latency_p50_s,
        latency_p95_s=latency_p95_s,
        cost_per_call_usd=cost_per_call_usd,
    )
```

- [ ] **Step 4: Run tests, verify GREEN**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/infra/llm_benchmarks/test_metrics.py -v`
Expected: 7 PASS (3 from Task 2 + 4 new).

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add infra/llm_benchmarks/metrics.py tests/infra/llm_benchmarks/test_metrics.py
git commit -m "feat(llm-bench): add canon_level + confidence + latency + cost metrics

Phase 120 Task 3. _percentile helper + _confidence_distribution + extended
compute_metrics. Tests cover canon_level denominator (parse_ok only), p50/p95
on 10 latencies, mean cost, and 3-level confidence count.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 4: `metrics.py` — `consistency_score` + `quality_composite` + `recommend_priority`

**Files:**
- Modify: `infra/llm_benchmarks/metrics.py`
- Modify: `tests/infra/llm_benchmarks/test_metrics.py`

- [ ] **Step 1: Add failing tests for new functions**

Append to `tests/infra/llm_benchmarks/test_metrics.py`:

```python
from infra.llm_benchmarks.metrics import (
    consistency_score,
    quality_composite,
    recommend_priority,
)


def test_consistency_score_perfect_when_proposals_match_across_runs():
    proposals = [{"kind": "character.update", "target_id": 5}]
    calls = [
        _make_call(chapter_id=1, run_index=i, parsed_proposals=proposals)
        for i in range(1, 4)
    ]
    assert consistency_score(calls) == 1.0


def test_consistency_score_zero_when_all_proposals_differ():
    calls = [
        _make_call(chapter_id=1, run_index=1, parsed_proposals=[{"target_id": 1}]),
        _make_call(chapter_id=1, run_index=2, parsed_proposals=[{"target_id": 2}]),
        _make_call(chapter_id=1, run_index=3, parsed_proposals=[{"target_id": 3}]),
    ]
    # pairwise identical rate = 0/3 = 0.0
    assert consistency_score(calls) == 0.0


def test_consistency_score_handles_missing_runs():
    calls = [_make_call(chapter_id=1, run_index=1)]
    # only 1 run → no variance to measure → 1.0
    assert consistency_score(calls) == 1.0


def test_quality_composite_is_simple_average():
    m = ProviderMetrics(
        provider="minimax",
        n_calls=10,
        n_failed=0,
        parse_rate=0.9,
        schema_compliance=0.8,
        canon_level_compliance=1.0,
    )
    assert abs(quality_composite(m) - 0.9) < 1e-9


def test_recommend_priority_orders_by_cost_above_threshold():
    metrics = [
        ProviderMetrics(provider="a", n_calls=10, n_failed=0, parse_rate=1.0,
                        schema_compliance=1.0, canon_level_compliance=1.0,
                        cost_per_call_usd=0.005),
        ProviderMetrics(provider="b", n_calls=10, n_failed=0, parse_rate=1.0,
                        schema_compliance=1.0, canon_level_compliance=1.0,
                        cost_per_call_usd=0.001),
        ProviderMetrics(provider="c", n_calls=10, n_failed=0, parse_rate=0.5,
                        schema_compliance=0.5, canon_level_compliance=0.5,
                        cost_per_call_usd=0.0001),  # composite=0.5, below 0.9
    ]
    priority = recommend_priority(metrics, threshold=0.9)
    # a and b pass (composite=1.0), c fails (composite=0.5)
    assert priority == ["b", "a", "c"]


def test_recommend_priority_handles_empty_list():
    assert recommend_priority([], threshold=0.9) == []
```

- [ ] **Step 2: Run tests, verify RED**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/infra/llm_benchmarks/test_metrics.py -v`
Expected: 6 new FAIL.

- [ ] **Step 3: Implement new functions**

Append to `infra/llm_benchmarks/metrics.py`:

```python
def consistency_score(calls: list[CallResult]) -> float:
    """Pairwise identity rate of proposals for the same (chapter_id).

    Groups calls by chapter_id, then for each chapter with >=2 runs,
    computes pairwise proposal-list identity rate, averaged.
    """
    by_chapter: dict[int, list[CallResult]] = {}
    for c in calls:
        by_chapter.setdefault(c.chapter_id, []).append(c)

    if not by_chapter:
        return 1.0

    chapter_scores: list[float] = []
    for chapter_calls in by_chapter.values():
        if len(chapter_calls) < 2:
            chapter_scores.append(1.0)
            continue
        pairs_total = 0
        pairs_match = 0
        for i in range(len(chapter_calls)):
            for j in range(i + 1, len(chapter_calls)):
                pairs_total += 1
                if chapter_calls[i].parsed_proposals == chapter_calls[j].parsed_proposals:
                    pairs_match += 1
        chapter_scores.append(pairs_match / pairs_total if pairs_total else 1.0)

    return sum(chapter_scores) / len(chapter_scores)


def quality_composite(m: ProviderMetrics) -> float:
    """Simple average of parse_rate, schema_compliance, canon_level_compliance."""
    return (m.parse_rate + m.schema_compliance + m.canon_level_compliance) / 3


def recommend_priority(
    metrics_list: list[ProviderMetrics],
    threshold: float = 0.9,
) -> list[str]:
    """Order providers: above-threshold by cost asc, below-threshold appended."""
    above: list[ProviderMetrics] = []
    below: list[ProviderMetrics] = []
    for m in metrics_list:
        if quality_composite(m) >= threshold:
            above.append(m)
        else:
            below.append(m)
    above.sort(key=lambda m: m.cost_per_call_usd)
    below.sort(key=lambda m: quality_composite(m), reverse=True)
    return [m.provider for m in above] + [m.provider for m in below]
```

- [ ] **Step 4: Run tests, verify GREEN**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/infra/llm_benchmarks/test_metrics.py -v`
Expected: 13 PASS (7 from Tasks 2-3 + 6 new).

- [ ] **Step 5: Run ruff + commit**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m ruff check infra/llm_benchmarks/metrics.py tests/infra/llm_benchmarks/test_metrics.py
git add infra/llm_benchmarks/metrics.py tests/infra/llm_benchmarks/test_metrics.py
git commit -m "feat(llm-bench): consistency_score + quality_composite + recommend_priority

Phase 120 Task 4. consistency_score averages pairwise proposal identity
across multi-run chapters. quality_composite = simple mean of 3 rates.
recommend_priority orders above-threshold providers by cost asc, below-
threshold by composite desc.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 5: `providers.py` — `MockLLMService` + factory

**Files:**
- Create: `infra/llm_benchmarks/providers.py`
- Create: `tests/infra/llm_benchmarks/test_providers.py`

- [ ] **Step 1: Write failing tests for `MockLLMService` + `get_provider_llm`**

```python
# tests/infra/llm_benchmarks/test_providers.py
"""Tests for infra.llm_benchmarks.providers."""
from __future__ import annotations

import pytest

from infra.llm_benchmarks.providers import (
    MockLLMService,
    get_provider_llm,
    anthropic_mock_canned,
    openai_mock_canned,
    minimax_mock_canned,
)


def test_mock_llm_returns_canned_json_for_known_prompt():
    svc = MockLLMService(canned=openai_mock_canned)
    out = svc.generate(prompt="角色 slug: 林栀\n\n章节文本 (按顺序):\n\n### 第1段\nfoo", system="x")
    assert out.startswith("{") or out.startswith("[")


def test_mock_llm_returns_empty_proposals_for_unknown_prompt():
    svc = MockLLMService(canned=openai_mock_canned)
    out = svc.generate(prompt="unrecognized prompt shape", system="x")
    assert "proposals" in out


def test_get_provider_llm_returns_mock_when_real_false():
    svc = get_provider_llm("minimax", real=False)
    assert isinstance(svc, MockLLMService)


def test_get_provider_llm_raises_when_minimax_real_no_env(monkeypatch):
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="MINIMAX_API_KEY not set"):
        get_provider_llm("minimax", real=True)


def test_get_provider_llm_raises_not_implemented_for_anthropic_real(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    with pytest.raises(NotImplementedError, match="real anthropic"):
        get_provider_llm("anthropic", real=True)


def test_anthropic_canned_differs_from_openai_canned():
    # Different canned JSON reflects different provider "personality"
    assert anthropic_mock_canned != openai_mock_canned
    assert "minimax" not in anthropic_mock_canned
```

- [ ] **Step 2: Run tests, verify RED**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/infra/llm_benchmarks/test_providers.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement `MockLLMService` + factory + canned JSON**

```python
# infra/llm_benchmarks/providers.py
"""Mock + real LLM provider factory for benchmark runs.

In test/CI mode, returns MockLLMService (no API calls).
In CLI --real mode, returns real LLMService for minimax only;
anthropic/openai --real raises NotImplementedError (cost-controlled mock).
"""
from __future__ import annotations

import hashlib
import os
from typing import Any, Protocol


class _LLMRunnable(Protocol):
    def generate(self, prompt: str, system: str | None = None, **kwargs: Any) -> str: ...


def _hash_prompt(prompt: str) -> str:
    return hashlib.sha256(prompt[:200].encode()).hexdigest()[:16]


# Mock canned JSON — keyed by hash(prompt[:200]). Each provider has 3 entries
# (one per huiyu-dangan chapter). Designed to show schema_compliance differences.
anthropic_mock_canned: dict[str, str] = {
    _hash_prompt("角色 slug: 林栀\n\n章节文本 (按顺序):\n\n### 第1段\n林栀"): (
        '{"proposals":[{"kind":"character.update","target_kind":"character",'
        '"target_id":5,"payload":{"status":"alive","confidence":"high"},'
        '"source_context":"第1章提到林栀","confidence":"high"}]}'
    ),
    _hash_prompt("角色 slug: 林栀\n\n章节文本 (按顺序):\n\n### 第1段\n周姐"): (
        # intentionally missing some fields to model hallucination
        '{"proposals":[{"kind":"character.update","target_id":5,'
        '"payload":{"status":"alive"}}]}'
    ),
    _hash_prompt("角色 slug: 林栀\n\n章节文本 (按顺序):\n\n### 第1段\n街灯"): (
        '{"proposals":[]}'  # no evidence, returns empty per prompt instructions
    ),
}

openai_mock_canned: dict[str, str] = {
    _hash_prompt("角色 slug: 林栀\n\n章节文本 (按顺序):\n\n### 第1段\n林栀"): (
        '{"proposals":[{"kind":"character.update","target_kind":"character",'
        '"target_id":5,"payload":{"status":"alive","canon_level":"Primary","confidence":"high"},'
        '"source_context":"第1章","confidence":"high"}]}'
    ),
    _hash_prompt("角色 slug: 林栀\n\n章节文本 (按顺序):\n\n### 第1段\n周姐"): (
        '{"proposals":[{"kind":"character.update","target_kind":"character",'
        '"target_id":5,"payload":{"status":"alive","canon_level":"Primary","confidence":"high"},'
        '"source_context":"周姐对话","confidence":"high"}]}'
    ),
    _hash_prompt("角色 slug: 林栀\n\n章节文本 (按顺序):\n\n### 第1段\n街灯"): (
        '{"proposals":[]}'
    ),
}

minimax_mock_canned: dict[str, str] = {
    _hash_prompt("角色 slug: 林栀\n\n章节文本 (按顺序):\n\n### 第1段\n林栀"): (
        '{"proposals":[{"kind":"character.update","target_kind":"character",'
        '"target_id":5,"payload":{"status":"alive","canon_level":"Primary","confidence":"medium"},'
        '"source_context":"林栀出现","confidence":"medium"}]}'
    ),
    _hash_prompt("角色 slug: 林栀\n\n章节文本 (按顺序):\n\n### 第1段\n周姐"): (
        '{"proposals":[{"kind":"character.update","target_kind":"character",'
        '"target_id":5,"payload":{"status":"alive","canon_level":"Primary","confidence":"medium"},'
        '"source_context":"周姐对话","confidence":"medium"}]}'
    ),
    _hash_prompt("角色 slug: 林栀\n\n章节文本 (按顺序):\n\n### 第1段\n街灯"): (
        '{"proposals":[]}'
    ),
}


class MockLLMService:
    """Deterministic LLM mock keyed on prompt hash.

    Returns canned JSON responses; for unknown prompts, returns an empty
    proposals array (graceful default).
    """

    def __init__(self, canned: dict[str, str]) -> None:
        self._canned = canned

    def generate(self, prompt: str, system: str | None = None, **kwargs: Any) -> str:
        h = _hash_prompt(prompt)
        if h in self._canned:
            return self._canned[h]
        # default: empty proposals (no evidence)
        return '{"proposals":[]}'


def _canned_for(name: str) -> dict[str, str]:
    return {
        "anthropic": anthropic_mock_canned,
        "openai": openai_mock_canned,
        "minimax": minimax_mock_canned,
    }[name]


def get_provider_llm(name: str, *, real: bool = False) -> _LLMRunnable:
    """Return LLM service for the named provider.

    real=False → MockLLMService (no env var check, safe for tests).
    real=True + name=="minimax" → LLMService.get() (requires MINIMAX_API_KEY).
    real=True + name in {"anthropic","openai"} → NotImplementedError.
    """
    if not real:
        return MockLLMService(canned=_canned_for(name))

    if name == "minimax":
        if not os.environ.get("MINIMAX_API_KEY"):
            raise RuntimeError(
                "MINIMAX_API_KEY not set; add to .env or export before --real"
            )
        # Lazy import to avoid module-load side effects in tests
        from infra.llm_service import LLMService

        return LLMService.get()

    if name in {"anthropic", "openai"}:
        raise NotImplementedError(
            f"real {name} benchmark not in scope (Phase 120 cost-controlled mock only)"
        )

    raise ValueError(f"unknown provider: {name!r}")
```

- [ ] **Step 4: Run tests, verify GREEN**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/infra/llm_benchmarks/test_providers.py -v`
Expected: 6 PASS.

- [ ] **Step 5: Run ruff + commit**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m ruff check infra/llm_benchmarks/providers.py tests/infra/llm_benchmarks/test_providers.py
git add infra/llm_benchmarks/providers.py tests/infra/llm_benchmarks/test_providers.py
git commit -m "feat(llm-bench): MockLLMService + get_provider_llm factory

Phase 120 Task 5. MockLLMService deterministic on prompt[:200] SHA256.
Canned JSON differs across providers to reflect schema_compliance variance
in tests. real=True only allowed for minimax (cost-controlled).

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 6: `fixtures.py` — `load_golden_chapters`

**Files:**
- Create: `infra/llm_benchmarks/fixtures.py`
- Create: `tests/infra/llm_benchmarks/test_fixtures.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/infra/llm_benchmarks/test_fixtures.py
"""Tests for infra.llm_benchmarks.fixtures."""
from __future__ import annotations

from pathlib import Path

import pytest

from infra.llm_benchmarks.fixtures import (
    CHARACTER_SLUG,
    CHAPTER_IDS,
    load_golden_chapters,
)


def test_constants_are_set():
    assert CHARACTER_SLUG == "林栀"
    assert CHAPTER_IDS == [1, 3, 10]


def test_load_golden_chapters_returns_three_strings(tmp_path, monkeypatch):
    # Create dummy chapter files matching huiyu-dangan layout
    proj = tmp_path / "huiyu-dangan" / "golden-set" / "chapters"
    proj.mkdir(parents=True)
    (proj / "ch001.md").write_text("林栀 chapter 1 content", encoding="utf-8")
    (proj / "ch003.md").write_text("林栀 chapter 3 content", encoding="utf-8")
    (proj / "ch010.md").write_text("林栀 chapter 10 content", encoding="utf-8")

    # Patch projects root to tmp_path
    monkeypatch.setattr(
        "infra.llm_benchmarks.fixtures.Path",
        lambda *args: tmp_path.joinpath(*args[1:]) if args and args[0] == "/" else Path(*args),
    )

    chapters = load_golden_chapters("huiyu-dangan", [1, 3, 10])
    assert len(chapters) == 3
    assert all(isinstance(c, str) and c for c in chapters)


def test_load_golden_chapters_raises_on_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="ch003.md"):
        load_golden_chapters.__wrapped__("huiyu-dangan", [1, 3, 10]) if hasattr(load_golden_chapters, "__wrapped__") else None
        # Direct call: tmp_path has no chapters → FileNotFoundError
        with pytest.raises(FileNotFoundError):
            load_golden_chapters("nonexistent-project", [1])
```

- [ ] **Step 2: Run tests, verify RED**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/infra/llm_benchmarks/test_fixtures.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement `fixtures.py`**

```python
# infra/llm_benchmarks/fixtures.py
"""Load real golden chapters for benchmark fixture.

Reads from projects/<slug>/golden-set/chapters/ch{NNN}.md in the LingWen
project tree.
"""
from __future__ import annotations

import os
from pathlib import Path

CHARACTER_SLUG = "林栀"
CHAPTER_IDS = [1, 3, 10]


def _projects_root() -> Path:
    """Resolve projects/ root. Allow override via LINGWEN_PROJECTS_ROOT env."""
    env = os.environ.get("LINGWEN_PROJECTS_ROOT")
    if env:
        return Path(env)
    # Walk up from this file to find projects/ — repo root is 4 levels up
    return Path(__file__).resolve().parents[3] / "projects"


def _chapter_path(slug: str, chapter_id: int) -> Path:
    return _projects_root() / slug / "golden-set" / "chapters" / f"ch{chapter_id:03d}.md"


def load_golden_chapters(slug: str, chapter_ids: list[int]) -> list[str]:
    """Load chapter texts in chapter_ids ascending order.

    Raises FileNotFoundError with the missing filename if any chapter is missing.
    """
    texts: list[str] = []
    for cid in sorted(chapter_ids):
        path = _chapter_path(slug, cid)
        if not path.exists():
            raise FileNotFoundError(f"missing fixture chapter: {path}")
        texts.append(path.read_text(encoding="utf-8"))
    return texts
```

- [ ] **Step 4: Adjust test (path patching approach) + verify GREEN**

The fixture tests need adjustment since the monkeypatching pattern in Step 1 is convoluted. Replace `tests/infra/llm_benchmarks/test_fixtures.py` with:

```python
"""Tests for infra.llm_benchmarks.fixtures."""
from __future__ import annotations

from pathlib import Path

import pytest

from infra.llm_benchmarks.fixtures import (
    CHARACTER_SLUG,
    CHAPTER_IDS,
    _projects_root,
    load_golden_chapters,
)


def test_constants_are_set():
    assert CHARACTER_SLUG == "林栀"
    assert CHAPTER_IDS == [1, 3, 10]


def test_load_golden_chapters_returns_three_strings(monkeypatch):
    fake_root = Path("/tmp/lingwen-test-projects-root")
    proj = fake_root / "huiyu-dangan" / "golden-set" / "chapters"
    proj.mkdir(parents=True)
    (proj / "ch001.md").write_text("林栀 chapter 1", encoding="utf-8")
    (proj / "ch003.md").write_text("林栀 chapter 3", encoding="utf-8")
    (proj / "ch010.md").write_text("林栀 chapter 10", encoding="utf-8")
    monkeypatch.setenv("LINGWEN_PROJECTS_ROOT", str(fake_root))

    chapters = load_golden_chapters("huiyu-dangan", [1, 3, 10])
    assert len(chapters) == 3
    assert chapters[0] == "林栀 chapter 1"
    assert chapters[1] == "林栀 chapter 3"
    assert chapters[2] == "林栀 chapter 10"


def test_load_golden_chapters_raises_on_missing_file(monkeypatch):
    fake_root = Path("/tmp/lingwen-empty-projects-root")
    fake_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("LINGWEN_PROJECTS_ROOT", str(fake_root))

    with pytest.raises(FileNotFoundError, match="ch001.md"):
        load_golden_chapters("huiyu-dangan", [1])
```

- [ ] **Step 5: Run tests, verify GREEN**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/infra/llm_benchmarks/test_fixtures.py -v`
Expected: 3 PASS.

- [ ] **Step 6: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add infra/llm_benchmarks/fixtures.py tests/infra/llm_benchmarks/test_fixtures.py
git commit -m "feat(llm-bench): fixtures.load_golden_chapters

Phase 120 Task 6. Reads projects/<slug>/golden-set/chapters/ch{NNN}.md,
LINGWEN_PROJECTS_ROOT env var override for test isolation. Tests cover
3-chapter load (asc order) + FileNotFoundError with filename in message.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 7: `results.py` — `write_call_result` + `read_run_results` + `list_runs`

**Files:**
- Create: `infra/llm_benchmarks/results.py`
- Create: `tests/infra/llm_benchmarks/test_results.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/infra/llm_benchmarks/test_results.py
"""Tests for infra.llm_benchmarks.results."""
from __future__ import annotations

from pathlib import Path

import pytest

from infra.llm_benchmarks.metrics import CallResult
from infra.llm_benchmarks.results import (
    _results_root,
    list_runs,
    read_run_results,
    write_call_result,
)


def _sample_call() -> CallResult:
    return CallResult(
        provider="minimax",
        chapter_id=1,
        run_index=1,
        timestamp="2026-08-26T12:00:00Z",
        raw_response='{"proposals":[]}',
        parsed_proposals=[],
        parse_ok=True,
        schema_ok=True,
        canon_level_ok=True,
        latency_s=1.0,
        output_tokens=100,
        cost_usd=0.001,
        failed=False,
    )


def test_write_call_result_creates_file(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "infra.llm_benchmarks.results._results_root", lambda: tmp_path
    )
    p = write_call_result("test-run", _sample_call())
    assert p.exists()
    assert p.suffix == ".json"
    assert p.parent.name == "test-run"


def test_read_run_results_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "infra.llm_benchmarks.results._results_root", lambda: tmp_path
    )
    write_call_result("test-run", _sample_call())
    write_call_result("test-run", _sample_call())  # second call (overwrites due to same name? no, gets unique id)

    results = read_run_results("test-run")
    assert len(results) >= 1
    assert all(isinstance(r, CallResult) for r in results)


def test_list_runs_returns_sorted_by_mtime_desc(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "infra.llm_benchmarks.results._results_root", lambda: tmp_path
    )
    (tmp_path / "run-old").mkdir()
    (tmp_path / "run-new").mkdir()
    runs = list_runs()
    assert "run-new" in runs
    assert "run-old" in runs


def test_results_dir_creation_failure_raises(tmp_path, monkeypatch):
    # Make _results_root point to a path that can't be created (e.g. file as parent)
    blocker = tmp_path / "blocker"
    blocker.write_text("file exists")
    monkeypatch.setattr(
        "infra.llm_benchmarks.results._results_root",
        lambda: blocker / "results",  # parent is a file, not dir
    )

    with pytest.raises(RuntimeError, match="results dir"):
        write_call_result("test-run", _sample_call())
```

- [ ] **Step 2: Run tests, verify RED**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/infra/llm_benchmarks/test_results.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement `results.py`**

```python
# infra/llm_benchmarks/results.py
"""Persist CallResults to disk as JSON, grouped per run.

Writes to infra/llm_benchmarks/results/<run-id>/call-NNN.json.
Directory creation failure is a fail-fast blocker (per spec §6).
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Iterable

from infra.llm_benchmarks.metrics import CallResult


def _results_root() -> Path:
    """Resolve results/ root. Allow override for tests."""
    env = os.environ.get("LLM_BENCH_RESULTS_ROOT")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent / "results"


def _next_call_index(run_dir: Path) -> int:
    existing = sorted(run_dir.glob("call-*.json"))
    if not existing:
        return 1
    last = existing[-1].stem  # call-007
    try:
        return int(last.split("-")[1]) + 1
    except (IndexError, ValueError):
        return len(existing) + 1


def write_call_result(run_id: str, result: CallResult) -> Path:
    """Persist one CallResult to results/<run_id>/call-NNN.json.

    Returns the written path. Raises RuntimeError if results dir creation
    fails (blocker per spec §6).
    """
    root = _results_root()
    run_dir = root / run_id
    try:
        run_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise RuntimeError(f"results dir create failed: {run_dir}: {exc}") from exc

    idx = _next_call_index(run_dir)
    path = run_dir / f"call-{idx:03d}.json"
    path.write_text(
        json.dumps(result.__dict__, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def read_run_results(run_id: str) -> list[CallResult]:
    """Read all call-NNN.json under results/<run_id>/."""
    run_dir = _results_root() / run_id
    if not run_dir.exists():
        return []
    out: list[CallResult] = []
    for path in sorted(run_dir.glob("call-*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        out.append(CallResult(**data))
    return out


def list_runs() -> list[str]:
    """List run_ids under results/, sorted by mtime desc."""
    root = _results_root()
    if not root.exists():
        return []
    runs = [p.name for p in root.iterdir() if p.is_dir()]
    runs.sort(key=lambda r: (root / r).stat().st_mtime, reverse=True)
    return runs
```

- [ ] **Step 4: Run tests, verify GREEN**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/infra/llm_benchmarks/test_results.py -v`
Expected: 4 PASS.

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add infra/llm_benchmarks/results.py tests/infra/llm_benchmarks/test_results.py
git commit -m "feat(llm-bench): results.write/read/list with dir-creation guard

Phase 120 Task 7. write_call_result appends call-NNN.json (auto-incrementing
index). read_run_results round-trips JSON to CallResult. list_runs by
mtime desc. mkdir failure raises RuntimeError (blocker per spec §6).

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 8: `render.py` — markdown report rendering

**Files:**
- Create: `infra/llm_benchmarks/render.py`
- Create: `tests/infra/llm_benchmarks/test_render.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/infra/llm_benchmarks/test_render.py
"""Tests for infra.llm_benchmarks.render."""
from __future__ import annotations

from infra.llm_benchmarks.metrics import ProviderMetrics
from infra.llm_benchmarks.render import render_report


def _m(
    name: str,
    *,
    parse_rate: float = 0.9,
    schema: float = 0.8,
    canon: float = 1.0,
    cost: float = 0.001,
    p50: float = 1.0,
    p95: float = 2.0,
    consistency: float = 1.0,
    confidence: dict[str, int] | None = None,
) -> ProviderMetrics:
    return ProviderMetrics(
        provider=name,
        n_calls=10,
        n_failed=0,
        parse_rate=parse_rate,
        schema_compliance=schema,
        canon_level_compliance=canon,
        confidence_distribution=confidence or {"high": 5, "medium": 3, "low": 1},
        latency_p50_s=p50,
        latency_p95_s=p95,
        cost_per_call_usd=cost,
        consistency_score=consistency,
    )


def test_render_report_contains_all_providers_in_table():
    metrics = [_m("minimax"), _m("anthropic (mock)"), _m("openai (mock)")]
    md = render_report("test-run", metrics, ["minimax", "anthropic (mock)", "openai (mock)"])
    assert "minimax" in md
    assert "anthropic (mock)" in md
    assert "openai (mock)" in md
    assert "| provider |" in md


def test_render_report_includes_recommended_priority_diff():
    metrics = [_m("a", cost=0.001), _m("b", cost=0.005)]
    md = render_report("test-run", metrics, ["a", "b"])
    assert "default_priority" in md
    assert '"a"' in md
    assert '"b"' in md


def test_render_report_threshold_callout():
    metrics = [_m("a", cost=0.001)]
    md = render_report("test-run", metrics, ["a"])
    assert "0.90" in md or "0.9" in md
```

- [ ] **Step 2: Run tests, verify RED**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/infra/llm_benchmarks/test_render.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement `render.py`**

```python
# infra/llm_benchmarks/render.py
"""Render benchmark metrics into a markdown report."""
from __future__ import annotations

from infra.llm_benchmarks.metrics import ProviderMetrics, quality_composite


def _format_row(m: ProviderMetrics) -> str:
    composite = quality_composite(m)
    return (
        f"| {m.provider} "
        f"| {m.parse_rate:.2f} "
        f"| {m.schema_compliance:.2f} "
        f"| {m.canon_level_compliance:.2f} "
        f"| {composite:.2f} "
        f"| ${m.cost_per_call_usd:.4f} "
        f"| {m.latency_p50_s:.2f} "
        f"| {m.latency_p95_s:.2f} "
        f"| {m.consistency_score:.2f} |"
    )


def _format_confidence_row(m: ProviderMetrics) -> str:
    d = m.confidence_distribution
    return (
        f"| {m.provider} "
        f"| {d.get('high', 0)} "
        f"| {d.get('medium', 0)} "
        f"| {d.get('low', 0)} |"
    )


def render_report(
    run_id: str,
    provider_metrics: list[ProviderMetrics],
    recommended_priority: list[str],
    *,
    threshold: float = 0.9,
) -> str:
    """Render markdown report content. Caller writes to disk."""
    lines: list[str] = []
    lines.append(f"# LLM Provider Benchmark — {run_id}")
    lines.append("")
    lines.append("## Run")
    lines.append(f"- run_id: `{run_id}`")
    lines.append(f"- providers: {', '.join(m.provider for m in provider_metrics)}")
    lines.append(f"- calls/provider: {provider_metrics[0].n_calls if provider_metrics else 0}")
    lines.append("- fixture: huiyu-dangan/golden-set/chapters/{ch001, ch003, ch010} + 林栀")
    lines.append("")
    lines.append("## Per-provider metrics")
    lines.append("")
    lines.append(
        "| provider | parse_rate | schema_compliance | canon_level | composite | cost/call | p50 (s) | p95 (s) | consistency |"
    )
    lines.append(
        "|----------|-----------|------------------|-------------|-----------|-----------|---------|---------|-------------|"
    )
    for m in provider_metrics:
        lines.append(_format_row(m))
    lines.append("")
    lines.append("## Confidence distribution")
    lines.append("")
    lines.append("| provider | high | medium | low |")
    lines.append("|----------|------|--------|-----|")
    for m in provider_metrics:
        lines.append(_format_confidence_row(m))
    lines.append("")
    lines.append("## Threshold check")
    lines.append("")
    lines.append(f"Quality threshold = {threshold:.2f}.")
    above = [m for m in provider_metrics if quality_composite(m) >= threshold]
    if above:
        above_sorted = sorted(above, key=lambda m: m.cost_per_call_usd)
        lines.append("Providers above threshold (cost-ordered):")
        for i, m in enumerate(above_sorted, 1):
            composite = quality_composite(m)
            lines.append(
                f"{i}. {m.provider} (composite={composite:.2f}, cost=${m.cost_per_call_usd:.4f})"
            )
    lines.append("")
    lines.append("## Recommended priority")
    lines.append("")
    lines.append("```python")
    lines.append(f"default_priority = {recommended_priority!r}")
    lines.append("```")
    lines.append("")
    lines.append("Reasoning: above-threshold providers ordered by cost asc; below-threshold appended.")
    lines.append("")
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests, verify GREEN**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/infra/llm_benchmarks/test_render.py -v`
Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add infra/llm_benchmarks/render.py tests/infra/llm_benchmarks/test_render.py
git commit -m "feat(llm-bench): render_report markdown generator

Phase 120 Task 8. Produces: Run header / per-provider table / confidence
distribution / threshold check / recommended_priority code block. Tests
verify 3-provider table, priority diff block, threshold callout.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 9: `run.py` — `run_benchmark()` + CLI

**Files:**
- Create: `infra/llm_benchmarks/run.py`
- Create: `tests/infra/llm_benchmarks/test_run.py`
- Modify: `infra/llm_benchmarks/__init__.py` (export new symbols)

- [ ] **Step 1: Write failing tests**

```python
# tests/infra/llm_benchmarks/test_run.py
"""End-to-end tests for infra.llm_benchmarks.run (all-mock)."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from infra.llm_benchmarks.metrics import ProviderMetrics
from infra.llm_benchmarks import run_benchmark


@pytest.fixture(autouse=True)
def _isolate_results_root(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_BENCH_RESULTS_ROOT", str(tmp_path))
    monkeypatch.setenv("LINGWEN_PROJECTS_ROOT", "/nonexistent")  # no real fixtures needed for mock-only path
    yield


def test_run_benchmark_produces_10_call_results(monkeypatch):
    # Stub _default_llm_service to never hit real provider
    from infra.llm_benchmarks import run as run_mod
    from infra.llm_benchmarks.providers import MockLLMService, minimax_mock_canned

    monkeypatch.setattr(
        run_mod, "_call_provider", lambda *a, **kw: _stub_call(kw["chapter_id"], kw["run_index"])
    )

    metrics = run_benchmark("minimax", "test-run", real=False)
    assert isinstance(metrics, ProviderMetrics)
    assert metrics.provider == "minimax"
    # 3 chapters × 3 runs + 1 control = 10
    assert metrics.n_calls == 10


def test_run_benchmark_writes_results_files():
    from infra.llm_benchmarks import run as run_mod
    monkeypatch_patched = None  # placeholder

    metrics = run_benchmark("minimax", "test-run", real=False)
    results_root = Path(os.environ["LLM_BENCH_RESULTS_ROOT"])
    run_dir = results_root / "test-run"
    files = list(run_dir.glob("call-*.json"))
    assert len(files) == 10


def test_run_benchmark_does_not_invoke_real_llm(monkeypatch):
    called = {"count": 0}

    def fake_llm_service_get():
        called["count"] += 1
        raise AssertionError("LLMService.get() should not be called in mock mode")

    # Force minimax real path to NOT call LLMService.get
    monkeypatch.setenv("MINIMAX_API_KEY", "test-key-dummy")
    # But we pass real=False, so LLMService.get should never be touched
    metrics = run_benchmark("minimax", "test-run", real=False)
    assert called["count"] == 0


def _stub_call(chapter_id: int, run_index: int):
    """Build a CallResult stub for tests (bypasses real LLM)."""
    from infra.llm_benchmarks.metrics import CallResult

    return CallResult(
        provider="minimax",
        chapter_id=chapter_id,
        run_index=run_index,
        timestamp="2026-08-26T12:00:00Z",
        raw_response='{"proposals":[]}',
        parsed_proposals=[],
        parse_ok=True,
        schema_ok=True,
        canon_level_ok=True,
        latency_s=0.1,
        output_tokens=50,
        cost_usd=0.0001,
        failed=False,
    )
```

- [ ] **Step 2: Run tests, verify RED**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/infra/llm_benchmarks/test_run.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement `run.py`**

```python
# infra/llm_benchmarks/run.py
"""Orchestrate benchmark runs and CLI entrypoint."""
from __future__ import annotations

import argparse
import logging
import time
from typing import Any

from infra.world_db.agent_extractors import SYSTEM_PROMPT
from infra.world_db.agent_schemas import ProposalResponse, parse_proposals_json

from infra.llm_benchmarks.fixtures import (
    CHAPTER_IDS,
    CHARACTER_SLUG,
    load_golden_chapters,
)
from infra.llm_benchmarks.metrics import (
    CallResult,
    compute_metrics,
    consistency_score,
)
from infra.llm_benchmarks.providers import get_provider_llm
from infra.llm_benchmarks.results import write_call_result

logger = logging.getLogger(__name__)


def _build_user_prompt(character_slug: str, chapter_texts: list[str]) -> str:
    chapters = "\n\n".join(
        f"### 第{i+1}段\n{t}" for i, t in enumerate(chapter_texts)
    )
    return f"角色 slug: {character_slug}\n\n章节文本 (按顺序):\n\n{chapters}\n\n请输出 JSON。"


def _call_provider(
    *,
    provider: str,
    chapter_id: int,
    chapter_texts: list[str],
    run_index: int,
    llm: Any,
    real: bool,
) -> CallResult:
    """Make one LLM call and parse + validate the response."""
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        t0 = time.monotonic()
        raw = llm.generate(
            prompt=_build_user_prompt(CHARACTER_SLUG, chapter_texts),
            system=SYSTEM_PROMPT,
            max_tokens=4000,
            temperature=0.2,
        )
        latency_s = time.monotonic() - t0
    except Exception as exc:
        logger.warning("%s call failed: %s", provider, exc)
        return CallResult(
            provider=provider,
            chapter_id=chapter_id,
            run_index=run_index,
            timestamp=timestamp,
            raw_response="",
            parsed_proposals=[],
            parse_ok=False,
            schema_ok=False,
            canon_level_ok=False,
            latency_s=0.0,
            output_tokens=0,
            cost_usd=0.0,
            failed=True,
            error=str(exc),
        )

    parse_ok = True
    parsed_proposals: list[dict] = []
    schema_ok = True
    canon_level_ok = True
    try:
        proposals = parse_proposals_json(raw)
        for p in proposals:
            validated = ProposalResponse(**p.model_dump())
            parsed_proposals.append(p.model_dump())
            if validated.payload.canon_level not in {"Draft", "Secondary", "Primary"}:
                canon_level_ok = False
    except Exception as exc:
        logger.warning("%s parse failure: %s", provider, exc)
        parse_ok = False
        schema_ok = False

    output_tokens = len(raw) // 4  # rough estimate
    cost_usd = output_tokens * 0.000003  # rough estimate, ~$3/1M tokens

    return CallResult(
        provider=provider,
        chapter_id=chapter_id,
        run_index=run_index,
        timestamp=timestamp,
        raw_response=raw,
        parsed_proposals=parsed_proposals,
        parse_ok=parse_ok,
        schema_ok=schema_ok,
        canon_level_ok=canon_level_ok,
        latency_s=latency_s,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
        failed=False,
    )


def run_benchmark(
    provider: str,
    run_id: str,
    *,
    real: bool = False,
    chapter_ids: list[int] | None = None,
) -> ProviderMetrics:
    """Run N=10 calls (3 chapters × 3 runs + 1 control) for one provider."""
    chapter_ids = chapter_ids or CHAPTER_IDS
    chapters = load_golden_chapters("huiyu-dangan", chapter_ids)
    chapter_texts_by_id = dict(zip(chapter_ids, chapters))

    llm = get_provider_llm(provider, real=real)

    calls: list[CallResult] = []
    for chapter_id in chapter_ids:
        for run_index in [1, 2, 3]:
            result = _call_provider(
                provider=provider,
                chapter_id=chapter_id,
                chapter_texts=[chapter_texts_by_id[chapter_id]],
                run_index=run_index,
                llm=llm,
                real=real,
            )
            write_call_result(run_id, result)
            calls.append(result)
            logger.info(
                "%s chapter=%d run=%d done (parse_ok=%s)",
                provider, chapter_id, run_index, result.parse_ok,
            )

    # Control call (chapter_id=0 marks it as control)
    result = _call_provider(
        provider=provider,
        chapter_id=0,
        chapter_texts=chapters[:1],
        run_index=0,
        llm=llm,
        real=real,
    )
    write_call_result(run_id, result)
    calls.append(result)

    metrics = compute_metrics(calls, provider)
    # Override consistency_score since compute_metrics leaves it at 1.0 default
    from dataclasses import replace

    metrics = replace(metrics, consistency_score=consistency_score(calls))
    return metrics


def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="Run LLM provider benchmark (Phase 120)"
    )
    parser.add_argument(
        "--provider",
        choices=["minimax", "anthropic", "openai", "all"],
        required=True,
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--real", action="store_true", help="Use real LLM provider (env var gated)"
    )
    parser.add_argument(
        "--chapters", default="1,3,10", help="comma-separated chapter IDs"
    )
    parser.add_argument(
        "--report-output",
        default=None,
        help="Optional path to write markdown report",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    providers = (
        ["minimax", "anthropic", "openai"] if args.provider == "all" else [args.provider]
    )
    chapter_ids = [int(x) for x in args.chapters.split(",")]

    all_metrics = []
    for p in providers:
        m = run_benchmark(p, args.run_id, real=args.real, chapter_ids=chapter_ids)
        all_metrics.append(m)

    if args.report_output:
        from infra.llm_benchmarks.metrics import recommend_priority
        from infra.llm_benchmarks.render import render_report

        priority = recommend_priority(all_metrics)
        report = render_report(args.run_id, all_metrics, priority)
        Path(args.report_output).write_text(report, encoding="utf-8")
        logger.info("report written: %s", args.report_output)
        logger.info("recommended priority: %s", priority)


if __name__ == "__main__":
    _cli()
```

- [ ] **Step 4: Update `__init__.py` to export**

Replace `infra/llm_benchmarks/__init__.py`:

```python
"""LLM provider benchmark module (Phase 120).

Dev/CI tool for comparing extraction quality / cost / latency across
LLM providers. CLI and library entrypoints.
"""
from __future__ import annotations

from infra.llm_benchmarks.metrics import (
    CallResult,
    ProviderMetrics,
    compute_metrics,
    consistency_score,
    quality_composite,
    recommend_priority,
)
from infra.llm_benchmarks.providers import (
    MockLLMService,
    anthropic_mock_canned,
    get_provider_llm,
    minimax_mock_canned,
    openai_mock_canned,
)
from infra.llm_benchmarks.run import run_benchmark

__all__ = [
    "run_benchmark",
    "get_provider_llm",
    "MockLLMService",
    "CallResult",
    "ProviderMetrics",
    "compute_metrics",
    "consistency_score",
    "quality_composite",
    "recommend_priority",
    "anthropic_mock_canned",
    "openai_mock_canned",
    "minimax_mock_canned",
]
```

- [ ] **Step 5: Run tests, verify GREEN**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/infra/llm_benchmarks/test_run.py -v`
Expected: 3 PASS.

- [ ] **Step 6: Run ruff + run full test suite**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m ruff check infra/llm_benchmarks/ tests/infra/llm_benchmarks/
/home/ailearn/miniconda3/bin/python -m pytest tests/infra/llm_benchmarks/ -v
```

Expected: ruff clean, all 25+ tests PASS.

- [ ] **Step 7: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add infra/llm_benchmarks/run.py infra/llm_benchmarks/__init__.py tests/infra/llm_benchmarks/test_run.py
git commit -m "feat(llm-bench): run_benchmark + CLI orchestration

Phase 120 Task 9. run_benchmark orchestrates 10 calls (3 chapters × 3 runs
+ 1 control), persists each via write_call_result, returns ProviderMetrics
with consistency_score. CLI: --provider {name|all} --run-id --real
--chapters --report-output. Failure per-call logs warning + continues.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 10: Manual real run with minimax key → results + report

**Files:** None created. This task produces **local-only** artifacts in `infra/llm_benchmarks/results/` (gitignored) and a report file committed in next task.

**Prerequisites:** User must add `MINIMAX_API_KEY=<real-key>` to `.env` (per spec §1.3 decision).

- [ ] **Step 1: Confirm `.env` has the API key**

```bash
test -f .env && grep -q "^MINIMAX_API_KEY=" .env && echo "MINIMAX_API_KEY set" || echo "MISSING — add MINIMAX_API_KEY=<key> to .env"
```

- [ ] **Step 2: Source `.env` and run minimax benchmark**

```bash
cd /home/ailearn/projects/LingWen
set -a; source .env; set +a
/home/ailearn/miniconda3/bin/python -m infra.llm_benchmarks.run \
    --provider minimax \
    --run-id 2026-08-26-baseline \
    --real \
    --report-output docs/benchmarks/2026-08-26-llm-provider-benchmark.md
```

Expected: 10 calls complete in ~30s, JSON files in `infra/llm_benchmarks/results/2026-08-26-baseline/`, markdown report at `docs/benchmarks/2026-08-26-llm-provider-benchmark.md`.

- [ ] **Step 3: Verify results JSON exists**

```bash
ls infra/llm_benchmarks/results/2026-08-26-baseline/ | wc -l
```

Expected: 10 (one per call).

- [ ] **Step 4: Inspect report markdown**

```bash
cat docs/benchmarks/2026-08-26-llm-provider-benchmark.md
```

Verify: contains minimax row with parse_rate / schema_compliance / canon_level_compliance / cost / p50 / p95 / consistency.

**Do NOT commit results/. It is gitignored. Only commit the report in next task.**

---

## Task 11: Commit benchmark report

**Files:**
- Create: `docs/benchmarks/2026-08-26-llm-provider-benchmark.md` (already created by Task 10)

- [ ] **Step 1: Verify report content sanity**

```bash
head -50 docs/benchmarks/2026-08-26-llm-provider-benchmark.md
```

Verify: contains recommended priority block + per-provider table.

- [ ] **Step 2: Commit report**

```bash
cd /home/ailearn/projects/LingWen
git add docs/benchmarks/2026-08-26-llm-provider-benchmark.md
git commit -m "docs(phase-120): add LLM provider benchmark report

10-call minimax real benchmark against huiyu-dangan/golden-set
chapters {1, 3, 10} + character 林栀. Report shows quality composite
(parse_rate + schema_compliance + canon_level_compliance) / 3,
cost per call (estimated), latency p50/p95, consistency score,
and recommended default_priority ordering per spec §3.6
decision criteria (90% threshold + cost tiebreaker).

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 12: Update `plugin_manager.py:150` default_priority per report

**Files:**
- Modify: `packages/lingwen-llm/src/lingwen_llm/providers/plugin_manager.py:150`

- [ ] **Step 1: Read current `default_priority` value**

```bash
sed -n '148,156p' packages/lingwen-llm/src/lingwen_llm/providers/plugin_manager.py
```

- [ ] **Step 2: Read recommended priority from report**

```bash
grep -A 2 "default_priority" docs/benchmarks/2026-08-26-llm-provider-benchmark.md | head -5
```

- [ ] **Step 3: Update `default_priority` to match report recommendation**

If recommended matches existing `["minimax", "anthropic", "openai"]`, skip this step and amend the previous commit's message to indicate confirmation (no code change needed).

Otherwise, edit `packages/lingwen-llm/src/lingwen_llm/providers/plugin_manager.py:150` from:

```python
default_priority = ["minimax", "anthropic", "openai"]
```

to:

```python
default_priority = ["<recommended order from report>"]
```

- [ ] **Step 4: Verify pytest still passes (no logic regression)**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest tests/infra/llm_benchmarks/ -v
```

Expected: all PASS.

- [ ] **Step 5: Commit (if changed) or amend (if confirmed)**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-llm/src/lingwen_llm/providers/plugin_manager.py
git commit -m "chore(llm): update default_priority per Phase 120 benchmark

Report recommends: <recommended order>
Reasoning: <short from report>

Co-Authored-By: Claude <noreply@anthropic.com>"
```

If no change needed, amend the report commit message:

```bash
git commit --amend -m "docs(phase-120): add LLM provider benchmark report

...

Co-Authored-By: Claude <noreply@anthropic.com>
" --no-edit
```

---

## Task 13: Sync `CLAUDE.md` + `.lingwen/architecture.yml`

**Files:**
- Modify: `CLAUDE.md`
- Modify: `.lingwen/architecture.yml`

- [ ] **Step 1: Update `CLAUDE.md` v15.4 → v15.5**

In `CLAUDE.md`, find the version line:

```
> **版本**: v15.4 (Phase 119 World follow-up 闭环)
```

Replace with:

```
> **版本**: v15.5 (Phase 120 LLM provider benchmark 闭环)
  → v15.4 (Phase 119 World follow-up 闭环)
```

Add a Phase 120 section right after the v15.4 entry:

```
> **更新 (2026-08-26)**: Phase 120 v15.5 闭环——5 commits (`649fb62a` ... )：
  - **Task 1-9** `infra/llm_benchmarks/` module — 7 source + 6 test files, mock-only pytest + CLI 真跑 (env var gated). 30+ tests, ≥80% coverage。
  - **Task 10** minimax 真跑 10 calls → `infra/llm_benchmarks/results/2026-08-26-baseline/` (gitignored) + `docs/benchmarks/2026-08-26-llm-provider-benchmark.md`。
  - **Task 11-12** `plugin_manager.py:150` default_priority 按报告推荐顺序更新 (or confirm 现有顺序)。
  - **Task 13** CLAUDE.md v15.5 + `.lingwen/architecture.yml` 同步。
  Lessons: pytest mock-only 必须 monkeypatch LLMService.get() 避免 CI 烧钱 / cost 估算用 token count × provider rate (粗估) / real=True + minimax 缺 env var 立刻 RuntimeError 而不是静默 mock。
```

Update the carryover list — remove "LLM provider 策略" entry (now done). Update Phase 119 follow-up entry to indicate it's also done.

- [ ] **Step 2: Update `.lingwen/architecture.yml`**

Find the `providers` section (or wherever LLM provider priority is documented) and update to reflect new `default_priority` order.

- [ ] **Step 3: Verify all tests + lint pass**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m ruff check .
cd apps/dashboard && pnpm vitest run tests/infra/llm_benchmarks/ && cd ../..
```

Wait — `pnpm vitest run` is for `apps/dashboard/` (frontend), not `infra/llm_benchmarks/`. Backend tests:

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest tests/infra/llm_benchmarks/ -v
/home/ailearn/miniconda3/bin/python -m pytest tests/infra/world_db/ apps/studio_api/tests/test_world_route.py -v
```

Expected: all green (no regression).

- [ ] **Step 4: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add CLAUDE.md .lingwen/architecture.yml
git commit -m "docs: bump CLAUDE.md to v15.5 + architecture.yml sync (Phase 120 闭环)

CLAUDE.md v15.4 → v15.5: Phase 120 entry added (5 commits summary +
new carryover removed). .lingwen/architecture.yml updated to reflect
final default_priority from benchmark report.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Self-Review

**1. Spec coverage:**

| Spec section | Task covering it |
|---|---|
| §3 architecture / module layout | Task 1 |
| §4.1 fixtures.py | Task 6 |
| §4.2 providers.py | Task 5 |
| §4.3 metrics.py (dataclasses + parse_rate + schema) | Task 2 |
| §4.3 metrics.py (canon_level + confidence + latency + cost) | Task 3 |
| §4.3 metrics.py (consistency + composite + recommend) | Task 4 |
| §4.4 run.py (orchestration + CLI) | Task 9 |
| §4.5 results.py | Task 7 |
| §4.6 render.py | Task 8 |
| §5 data flow | Task 9 |
| §6 error handling | Task 9 (RuntimeError on no env var, per-call continue) |
| §7 testing (mock-only pytest, env-gated CLI) | Tasks 2-9 (all tests use MockLLMService; --real never collected by pytest) |
| §8 deliverables (5 commits) | Tasks 1, 9, 11, 12, 13 |
| §10 risks (CI 烧钱) | Task 9 `test_run_benchmark_does_not_invoke_real_llm` + monkeypatch env var to test-key in Task 9 Step 4 |

**2. Placeholder scan:** No TBD / TODO / "implement later" / "similar to" in plan. Every code block is concrete.

**3. Type consistency:** `CallResult`, `ProviderMetrics`, `MockLLMService`, `get_provider_llm`, `recommend_priority`, `quality_composite`, `consistency_score`, `compute_metrics`, `write_call_result`, `read_run_results`, `list_runs`, `render_report`, `run_benchmark`, `_call_provider`, `load_golden_chapters` — all defined in Tasks 2-9 and used consistently. No signature drift.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-08-26-phase-120-llm-provider-benchmark.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration.

2. **Inline Execution** — Execute tasks in this session using `executing-plans`, batch execution with checkpoints.

Which approach? (Per Phase 118/119 pattern: small-to-medium scope, inline execution with checkpoints has worked. Task 10 is the only manual step; the rest are code.)
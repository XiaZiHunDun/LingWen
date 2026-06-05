# Phase 8 Design — Real LLM E2E (polish_merge S1-S8 验证)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this design.

## Context

Phase 7.5 (`polish_merge_synthesis` S1-S8 LLM 评分) + Phase 7.6 (dashboard 雷达图) 都已完成, 但**所有相关测试都用 StubProvider 模拟 LLM**:
- `tests/agent_system/test_master_controller.py::TestPolishMergeSynthesis` (5 tests) 调 `_merge_synthesis_llm` 但 polisher 是 stub
- `tests/agent_system/test_master_controller_stub_router_e2e.py` 文件名误导 (实际用 StubProvider, "real" 指 LLM 形接口不是真实 API)
- 真实 API 路径从未在 CI 或开发机器上跑过

**风险**: 真实 LLM 路径可能有问题但未被发现:
1. **JSON parse 失败**: `_merge_synthesis_llm` 用 `parse_response(format_type="json")` 解析真实 LLM 输出, HAIKU 可能包 code fence 或额外 prose
2. **Prompt 标签对齐**: 真实 LLM 可能不按 prompt 要求的 `scores_{label}` 格式输出, e.g. 标签 = "polish_emotional_pacing" 期望 key = "scores_polish_emotional_pacing"
3. **Content truncation**: prompts.py:121-148 截断到 3000 字符, 真实长内容可能丢关键信息
4. **Score range**: 真实 LLM 可能给 0-100 范围或负数

**当前 baseline**: 2073 passed, 0 failed, 17 skipped
**目标 baseline**: 2073 + 2 skipped (默认, opt-in 跑时 +2 passed)
**TDD 风格**: RED (SKIP 默认) → GREEN (opt-in 跑) → commit

---

## Feature A: 真实 LLM Router helper (`_make_real_router`)

**模块**: `tests/agent_system/test_novel_writing_real_llm.py` (新文件)

**设计**:
```python
def _make_real_router() -> AIRouter:
    """构造单 Anthropic provider 的 AIRouter, 用 HAIKU 模型 (Phase 7.5 spec 锁 S1-S8 评分用 HAIKU)"""
    from infra.ai_service import ProviderConfig
    from infra.ai_service.anthropic_provider import AnthropicProvider
    from infra.ai_service.router import AIRouter

    provider = AnthropicProvider(ProviderConfig(
        api_key=os.environ["ANTHROPIC_API_KEY"],
        model="claude-haiku-4-5-20251001",
        timeout=180,  # 留够 6 LLM call headroom
        max_retries=1,  # fail-fast
    ))
    return AIRouter(
        config={"anthropic": provider.config},
        primary_provider="anthropic",
        enable_failover=False,
    )
```

**为什么 HAIKU**:
- Phase 7.5 spec 锁 S1-S8 评分用 HAIKU (T=0.2, max_tokens=2000)
- 成本: $1/$5 per 1M tokens (input/output) vs Sonnet $3/$15 — 3-3.3x 便宜
- 单 test 跑完 ~$0.005-0.020 (6 LLM calls × 短 prompt)

**为什么 max_retries=1**:
- 默认 3 retries × 指数 backoff (1+2+4=7s) 在 rate limit 时阻塞测试
- real LLM 测试目标 fail-fast
- 持久性 API 错误应立即 raise 让开发者修

**为什么 timeout=180**:
- 6 LLM calls × HAIKU 单 call ~10-30s = 60-180s wall time
- 默认 60s 不够, 180s 留 headroom
- 单 provider 不需要 failover, fail-fast on timeout

---

## Feature B: Skip decorator + 1 个完整 pipeline test

**Skip pattern** (跟 `tests/agent_system/test_e2e_workflow.py:25-32` 一致):
```python
_REQUIRES_ANTHROPIC_KEY = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="Phase 8 real LLM test requires ANTHROPIC_API_KEY env var",
)
```

**Test 1: `TestNovelWritingRealLLM.test_novel_writing_yaml_polish_merge_produces_s1_s8_scores`**

完整跑 `novel_writing.yaml` 7 节点, 验证:
1. workflow 跑通 (`summary.completed >= 6, failed == 0`)
2. `polish_merge.output.fallback is None` (走 LLM 路径, 非 identical/llm_fail/empty_content)
3. S1-S8 8 维评分完整 (`set(scores_a.keys()) == {"S1", ..., "S8"}`)
4. 评分 0-10 int 范围 (`isinstance(score, int) and 0 <= score <= 10`)
5. `winner in _labels` + `scores_delta == scores_total_a - scores_total_b`
6. `_labels` 字段 = `["polish_emotional_pacing", "polish_ai_trace_removal"]` (Phase 7.6 透传)

**关键参数**:
- `word_count_target=800` (短内容, 加速 HAIKU 处理, 减少 70% token 成本)
- `max_backtracks=0` (fail-fast, 不重试; 重试会多花 12 LLM calls, 成本 +10x)
- `tmp_path` 状态隔离 (跟现有 E2E 测试一致, 不污染 `infra/.state/`)

**复用的模式** (Phase 7.1 已建立):
- `tests/agent_system/_e2e_helpers.py:106-115` — `make_master_with_router(state_dir, router)`
- `infra/agent_system/master_controller.py:48-99` — `MasterController.__init__(state_dir, router=, config=)`

---

## Feature C: 1 个快速直接 test (TestPolishMergeSynthesisRealLLM)

**理由**: 完整 pipeline 测试慢 (6 LLM calls ~30-60s), 直接调 `polish_merge_synthesis` 是 1 LLM call, ~5-10s. **更聚焦**测试 Phase 7.5 核心.

**Test 2: `TestPolishMergeSynthesisRealLLM.test_polish_merge_synthesis_with_distinct_contents`**

直接调 `master.polish_merge_synthesis(content_a, content_b, labels=("emotional", "motivation"))`, 跟 Test 1 同样的 6 步断言.

**内容设计**:
- `content_a = "少年握紧拳头, 眼中燃烧着不甘。" * 20` (~400 chars, 模拟 emotional 风格)
- `content_b = "林夕深吸一口气, 心中暗自立下誓言。" * 20` (~400 chars, 模拟 motivation 风格)
- 不同内容 → 不会触发 identical fallback → 走 LLM 路径

**好处**:
- 快 (1 LLM call vs 6)
- 便宜 (~$0.003 vs $0.015)
- 单独可跑: `pytest -k PolishMergeSynthesis` 5-10s 验证 Phase 7.5 核心

---

## YAGNI 显式排除

- **CI 集成**: real LLM 测试不跑 CI (成本 + 密钥管理), 留给本地 opt-in
- **多 provider matrix**: 只测 Anthropic, OpenAI/MiniMax 留给 Phase 8.x
- **Cost tracking 集成**: 不接 `CostTracker` (范围是验证 S1-S8 评分, 不是成本归因)
- **Rename `test_master_controller_stub_router_e2e.py`**: 误导性命名问题已知, Phase 8.x 单独处理
- **`.env` 文件模式**: 项目传统是 shell env, 不引入 python-dotenv
- **加 `pytest.mark.real_llm` marker**: 用 skipif 足够, marker 需要 `pytest.ini` 注册
- **改 `_e2e_helpers.py`**: YAGNI, 真实 LLM 构造只 1 个文件用

---

## Tests (8 步断言覆盖)

**TestNovelWritingRealLLM (Test 1)**:
1. `summary.completed >= 6` (允许 read_snapshot/emit_chapter 旁路)
2. `summary.failed == 0`
3. `merge_output["fallback"] is None` (走 LLM 路径, 非任何兜底)
4. `set(scores_a.keys()) == set(scores_b.keys()) == {"S1"..."S8"}` (8 维完整)
5. `isinstance(score, int) and 0 <= score <= 10` (int 范围)
6. `winner in _labels` (合法 winner)
7. `0.0 <= scores_total_a, scores_total_b <= 10.0` (mean 范围)
8. `abs(scores_total_a - scores_total_b - scores_delta) < 1e-6` (delta 一致性)
9. `_labels == ["polish_emotional_pacing", "polish_ai_trace_removal"]` (Phase 7.6 透传)

**TestPolishMergeSynthesisRealLLM (Test 2)**: 跟 Test 1 同样 9 步, 但只调 1 次 LLM.

---

## Critical files (modified)

- `tests/agent_system/test_novel_writing_real_llm.py` (NEW, ~120L) — `_make_real_router` helper + 2 test classes + skipif decorator

## Critical files (referenced / 复用)

- `tests/agent_system/_e2e_helpers.py:106-115` — `make_master_with_router` (Phase 7.1 已就位)
- `infra/agent_system/master_controller.py:48-99` — `MasterController.__init__` router 注入
- `infra/agent_system/master_controller.py:627-681` — `polish_merge_synthesis` 公共方法 (Phase 7.5 已就位)
- `infra/ai_service/anthropic_provider.py:25-44` — `AnthropicProvider(ProviderConfig)`
- `infra/ai_service/router.py:32-44` — `AIRouter(config=, primary_provider=, enable_failover=)`
- `infra/ai_service/base.py:42-62` — `ProviderConfig(api_key, model, timeout, max_retries)`
- `infra/agent_system/agents/polisher/prompts.py:121-155` — `build_merge_synthesis_prompt` + `get_merge_synthesis_system_prompt`
- `infra/got/workflows/novel_writing.yaml` — 7 节点 workflow (Phase 7.4 + 7.5 升级)
- `tests/agent_system/test_e2e_workflow.py:25-32` — `_REQUIRES_API_KEY` skip 模式参考

## Critical files (NOT 修改)

- `tests/agent_system/test_master_controller_stub_router_e2e.py` — 误导性命名, 实际是 StubProvider; **不**改名
- `tests/agent_system/_e2e_helpers.py` — **不**加 `_make_real_router()` helper, YAGNI
- `config/api_config.yaml` — **不**加示例 key 值, 模板已存在
- `pytest.ini` / `pyproject.toml` — **不**加 `real_llm` marker
- `conftest.py` — **不**加全局 fixture, YAGNI

---

## Commits

1. `docs(spec): add Phase 8 design — real LLM E2E (polish_merge S1-S8)` (本文件)
2. `docs(plan): add Phase 8 implementation plan`
3. `feat(agent_system): phase 8 — real LLM E2E (polish_merge S1-S8)` (1 new test file)

**预计**: 3 commits, 0 state DB changes, 0 production code changes

---

## Risks + 缓解

| 风险 | 缓解 |
|------|------|
| 真实 HAIKU 输出非 JSON, `_merge_synthesis_llm` 走 llm_fail fallback | `assert fallback is None` 直接 fail, 暴露问题; Phase 8.x 修复 `parse_response` |
| 上游 polish variant 内容相同 → identical fallback | production LLM temperature > 0 (dialogue T=0.5, pacing T=0.4) → 内容自然不同; 测试不 mock 上游, 跑完整 6 LLM calls |
| HAIKU 不按 prompt 输出 `scores_{label}` 完整 8 维 | `assert set(scores.keys()) == {S1, ..., S8}` 直接 fail, 暴露 prompt 问题 |
| HAIKU 给 score 0-100 或负数 | `assert 0 <= score <= 10` 暴露, Phase 8.x 加范围 clamp |
| API rate limit 429 | `max_retries=1` 限制重试, fail-fast; 本地 opt-in 跑不阻塞 CI |
| 6 LLM calls 慢 (~30-60s) | 接受 — opt-in 测试, 跑本地不在 CI; 文档说明 |
| 成本失控 | HAIKU 模型 (vs Sonnet 3-3.3x 便宜) + `max_retries=1` + tmp_path 状态隔离 |
| Test 结果 flaky (HAIKU 偶尔返回意外格式) | 1-2 次重跑 (本地) 接受; Phase 8.x 加 retry tolerance |
| ANTHROPIC_API_KEY 泄漏到 git | `.env` 已在 `.gitignore`, 不 commit; 显式 skip 装饰器; 复用 `test_logic_audit_no_api_key_leak.py:63-78` 保护 |
| Subagent 误用真实 API key 跑测试 | 显式声明 "Do NOT set ANTHROPIC_API_KEY in subagent env"; 默认 SKIP 是安全网 |

---

## 完成后下一步 (后续 phases)

- **Phase 8.1**: 修真实 LLM 暴露的问题 (JSON parse / score range / 标签对齐)
- **Phase 8.2**: 加 OpenAI + MiniMax provider 矩阵
- **Phase 8.3**: CI 集成 (GitHub Actions secrets + 定时跑, 不在 PR 跑)
- **Phase 8.4**: Rename `test_master_controller_stub_router_e2e.py` → `_stub_router_e2e.py`
- **Phase 8.5**: 接 `CostTracker` 进 `AgentComputeFn` (real cost 归因)
- **Phase 9**: 跨卷涟漪 (独立大方向, 跟当前 polish 路线分叉)

---

## DoD

- [ ] `tests/agent_system/test_novel_writing_real_llm.py` 创建 (1 file, ~120L)
- [ ] `_REQUIRES_ANTHROPIC_KEY` skipif 装饰器
- [ ] `_make_real_router()` helper (HAIKU, timeout=180, max_retries=1)
- [ ] `TestNovelWritingRealLLM.test_novel_writing_yaml_polish_merge_produces_s1_s8_scores` (1 test)
- [ ] `TestPolishMergeSynthesisRealLLM.test_polish_merge_synthesis_with_distinct_contents` (1 test)
- [ ] 默认 (无 API key) 全 SKIP, 跑 `pytest tests/ -q` 2073 passed + 2 skipped (新增 2 个)
- [ ] opt-in (有 API key) 全 PASS, 跑通 6 LLM calls 端到端
- [ ] `ruff check .` 0 warnings
- [ ] 1 impl commit pushed to origin/master
- [ ] MEMORY.md < 200 lines (+ 1 行 Phase 8 entry)

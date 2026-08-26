# Phase 120 — LLM Provider 实测对比 + 优先级决策 Design

> **目的**: 实测三个 LLM provider (minimax / anthropic / openai) 在当前 agent_extractors 中文 system prompt 下的 extraction quality / cost / latency,生成对比报告,确定 `plugin_manager.py:150` `default_priority` 的最终顺序 + 同步更新 `CLAUDE.md` + `.lingwen/architecture.yml`。
> **生成时间**: 2026-08-26 (master @ `5b181949`, Phase 119 闭环)
> **前置阅读**: `CLAUDE.md` v15.4 → Phase 119 handoff → Phase 118 handoff §2 priority D
> **Supersedes**: Phase 118 handoff §2.D (LLM provider 策略 中长期项)

---

## 0. TL;DR

- 1 真 provider (minimax) + 2 mock (anthropic, openai)
- 30 calls 总 (10/provider): 3 chapters × 3 runs + 1 control
- 7 评估维度: JSON parse / schema / canon_level / confidence / latency p50+p95 / cost / consistency
- 90% quality threshold + simple average composite + cost tiebreaker
- 决策: 达标 + cost 最低 = 主用,其余按 cost 排
- 交付物: 报告 + 改 `plugin_manager.py:150` default_priority + 更新 `CLAUDE.md` + `.lingwen/architecture.yml`
- 测试: pytest mock-only (CI fast),CLI manual 真跑 (env var gated)

---

## 1. Context / Background

### 1.1 现状 (master @ `5b181949`)

- `packages/lingwen-llm/src/lingwen_llm/providers/plugin_manager.py:150` 已 hardcode `default_priority = ["minimax", "anthropic", "openai"]`
- 三个 env vars (`MINIMAX_API_KEY` / `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`) 全 UNSET
- `infra/llm_service.py` 已实现多 provider 自动 failover (loop through providers + warn log + try next)
- `infra/world_db/agent_extractors.py` 已用真实 LLM 调用 (`SYSTEM_PROMPT` 47-55 行,7 条要求 + JSON 示例)
- 测试 fixtures 现成: `projects/huiyu-dangan/golden-set/chapters/ch001.md + ch003.md + ch010.md` (3 章真实小说), `docs/character-bible/` 有角色档案

### 1.2 现有 carryover

| 优先级 | 内容 | 状态 |
|---|---|---|
| Phase 118 §2.D | LLM provider 策略 (minimax/anthropic/openai 主用+备用顺序) | **本 spec 闭环** |
| Phase 119 §2.B | Prod preview regression (Phase 114 accepted debt) | 不动 |
| Phase 119 §2.C | 历史 ruff/knip/pytest collection errors | 不动 |

### 1.3 用户决策 (本次 brainstorming 收集)

| 维度 | 选择 |
|---|---|
| Provider 数量 | 1 真 + 2 mock (混合) |
| 真 provider | minimax (自家,成本最低,验证 hardcode 首位是否正确) |
| API key 来源 | 写进 `.env` 文件 (默认 `.gitignore`,持久复用) |
| 测试输入 | 现成 golden chapters (`huiyu-dangan` ch001+ch003+ch010) + 角色 `林栀` |
| 评估维度 | 全 7 维度 (parse/schema/canon_level/confidence/latency/cost/consistency) |
| 每 provider 调用次数 | N=10 (3 chapters × 3 runs + 1 control) |
| Output 存储 | `infra/llm_benchmarks/results/<run-id>/` (gitignore 整个 results/) |
| 决策标准 | 90% quality threshold + simple average composite + cost tiebreaker |
| Threshold + formula | 90% threshold, composite = (parse_rate + schema + canon_level) / 3 |
| 报告交付物 | 报告 + 改 hardcode + 文档 (一气饱成) |
| 脚本位置 | `infra/llm_benchmarks/` module (CLI + library,pytest mock-only) |
| 角色选定 | 林栀 (ch001+ch010 都出现,跨章节 consistency 能量化) |
| Approach | Hybrid Full (Approach A,推荐) |

---

## 2. Goals / Non-Goals

### 2.1 Goals

- **G1**: 实测三个 provider 在 production prompt + 真实 fixture 下的 extraction 表现
- **G2**: 量化 quality (parse + schema + canon_level) / cost / latency / consistency
- **G3**: 基于 data-driven 决策定 `default_priority` 最终顺序
- **G4**: 决策落地:`plugin_manager.py:150` 改 hardcode + 文档化
- **G5**: benchmark 工具可重复运行 (rerun regression check)

### 2.2 Non-Goals

- **NG1**: 不做 prompt engineering / system prompt 调优 (本 phase 只对比不改 prompt)
- **NG2**: 不跑真 anthropic / openai (mock only,成本控制)
- **NG3**: 不加新 provider (只对比已注册的 minimax/anthropic/openai)
- **NG4**: 不改 `infra/llm_service.py` failover 逻辑 (Phase 118 已闭环)
- **NG5**: 不进 production code path (`infra/llm_benchmarks/` 仅 dev/CI tool)
- **NG6**: 不做 cross-character consistency (用户未选此维度)

---

## 3. Architecture (Module Layout)

新建 `infra/llm_benchmarks/` 作为 dev/CI 工具模块 (与 `infra/world_db/` 同级,但不通过 production code path):

```
infra/llm_benchmarks/
├── __init__.py        # public API: run_benchmark(), get_provider_llm()
├── run.py             # CLI: python -m infra.llm_benchmarks.run
├── metrics.py         # pure functions: parse_rate, schema_compliance, ...
├── fixtures.py        # 读 huiyu-dangan golden chapters
├── providers.py       # MockLLMService + get_provider_llm(name) factory
├── results.py         # write/read JSON per call
└── render.py          # markdown 报告渲染

tests/infra/llm_benchmarks/      # mirror 测试目录
├── test_metrics.py
├── test_providers.py
├── test_fixtures.py
├── test_results.py
├── test_render.py
└── test_run.py
```

**`.gitignore`** 加 `infra/llm_benchmarks/results/` (持久但不入库,避免 git 噪音)。

### 3.1 入口

- **Library**: `from infra.llm_benchmarks import run_benchmark; run_benchmark("minimax", run_id="2026-08-26-baseline", real=True)`
- **CLI**: `python -m infra.llm_benchmarks.run --provider all --run-id 2026-08-26-baseline --real`

### 3.2 复用 vs 新增

- **复用**: `infra/world_db/agent_schemas.parse_proposals_json` (验证 raw → proposals)
- **复用**: `infra/world_db/agent_schemas.ProposalResponse` (Pydantic schema 验证)
- **复用**: `infra/world_db/agent_extractors.SYSTEM_PROMPT` (直接 import 字符串)
- **不复用**: `infra/world_db/agent_extractors.extract_proposals_from_chapters` (其内部 lazy import `LLMService.get()`,会 hit 真 provider)
- **不复用**: `infra.llm_service.LLMService` 真 provider 实例化逻辑 (`providers.py` 改用 `LLMService.get()` 但只在 minimax 真跑分支)

---

## 4. Components

### 4.1 fixtures.py

| 接口 | 说明 |
|---|---|
| `CHARACTER_SLUG = "林栀"` | 角色常量 |
| `CHAPTER_IDS = [1, 3, 10]` | 章节 id 常量 |
| `load_golden_chapters(slug: str, chapter_ids: list[int]) -> list[str]` | 读 `projects/huiyu-dangan/golden-set/chapters/ch{NNN}.md`,返回 chapter 文本 list (按 id 升序) |

错误处理: 任一 chapter 文件缺失 → `FileNotFoundError` + 明确文件名。

### 4.2 providers.py

| 接口 | 说明 |
|---|---|
| `class MockLLMService` | mock provider, deterministic output |
| `MockLLMService(canned_responses: dict[str, str])` | keyed by hash(prompt[:200]),返回 canned JSON |
| `get_provider_llm(name: str, *, real: bool = False) -> MockLLMService \| LLMService` | factory:<br>- `name == "minimax"` + `real=True` + env var set → `LLMService.get()`<br>- `name == "minimax"` + `real=True` + env var unset → raise `RuntimeError("MINIMAX_API_KEY not set")`<br>- `name in {"anthropic", "openai"}` + `real=True` → raise `NotImplementedError("real anthropic/openai not in scope")`<br>- 任意 + `real=False` → `MockLLMService(canned_for(name))` |

**MockLLMService.canned JSON 设计**:
- `anthropic_mock_canned`: 3 chapters × 1 response,简化 JSON (偶尔缺字段,模拟典型 hallucination)
- `openai_mock_canned`: 3 chapters × 1 response,标准 JSON,所有字段正确
- `minimax_mock_canned`: 3 chapters × 1 response,正常 JSON (备用,用于 pytest 默认不依赖 env var)
- **差异是 design choice**: 让 schema_compliance metric 在 mock 间有区分度,反映 provider 典型"性格"

### 4.3 metrics.py

```python
@dataclass(frozen=True)
class CallResult:
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
    error: str | None

@dataclass(frozen=True)
class ProviderMetrics:
    provider: str
    n_calls: int
    n_failed: int
    parse_rate: float              # parse_ok / n_calls
    schema_compliance: float       # schema_ok / n_calls
    canon_level_compliance: float  # canon_level_ok / n_calls
    confidence_distribution: dict[str, int]  # {"high": N, "medium": M, "low": K}
    latency_p50_s: float
    latency_p95_s: float
    cost_per_call_usd: float       # mean
    consistency_score: float       # 同 chapter 3 runs proposals 一致率
    quality_composite: float       # (parse + schema + canon_level) / 3
```

| 接口 | 说明 |
|---|---|
| `compute_metrics(calls: list[CallResult]) -> ProviderMetrics` | 聚合 10 calls → 1 ProviderMetrics |
| `quality_composite(m: ProviderMetrics) -> float` | simple average |
| `recommend_priority(metrics: list[ProviderMetrics], threshold: float = 0.9) -> list[str]` | 达标 (composite ≥ threshold) 按 cost 排;未达标 append 末尾 |

edge cases:
- 空 calls list → all metrics = 0, `n_failed = 0`, `confidence_distribution = {}`
- 全 failed → `parse_rate = 0`, 仍计入 quality composite (会拉低分数)
- `consistency_score` 仅当同 chapter 有 ≥2 runs 时计算;否则 = 1.0 (no variance to measure)

### 4.4 run.py

```python
def run_benchmark(
    provider: str,
    run_id: str,
    *,
    real: bool = False,
    chapter_ids: list[int] | None = None,
) -> ProviderMetrics:
    """Run N=10 calls (3 chapters × 3 runs + 1 control) for one provider."""
```

CLI:
```bash
python -m infra.llm_benchmarks.run \
    --provider {minimax|anthropic|openai|all} \
    --run-id <id> \
    [--real] [--chapters 1,3,10]
```

`--provider all` 串行跑 3 providers,每个 10 calls,共 30 calls。

**Loop**:
```
for chapter_id in [1, 3, 10]:
    for run_index in [1, 2, 3]:
        call_provider(provider, chapter_id, run_index, real=real)
call_provider(provider, chapter_id=0, run_index=0)  # control
```

`call_provider` 流程:
1. `llm = get_provider_llm(provider, real=real)`
2. `t0 = time.monotonic()`
3. `raw = llm.generate(prompt=user_prompt, system=SYSTEM_PROMPT, max_tokens=4000, temperature=0.2)`
4. `latency_s = time.monotonic() - t0`
5. 尝试 `parse_proposals_json(raw)`,validate via `ProposalResponse`
6. 计算 `parse_ok / schema_ok / canon_level_ok` per proposal
7. 计算 `output_tokens` (从 raw 长度估算,或 provider 返回 usage if available) + `cost_usd`
8. 构造 `CallResult`,`results.write(run_id, result)`
9. return CallResult (异常 → mark failed=True + continue)

**Rate limit**: 不打 `_AgentRateLimiter` (那是 agent routes 的),benchmark 自己 10/provider 固定,无 limit。

### 4.5 results.py

| 接口 | 说明 |
|---|---|
| `write_call_result(run_id: str, result: CallResult) -> Path` | 写 `infra/llm_benchmarks/results/<run-id>/call-{N}.json`,返回 Path |
| `read_run_results(run_id: str) -> list[CallResult]` | 读整个 run 目录,返回 list |
| `list_runs() -> list[str]` | 列出所有 run_id (按 mtime desc) |

**目录创建**: 第一次 write 前 `mkdir -p`;创建失败 → fail entire run (blocker)。
**单 file write 失败**: log warning + skip,continue。

### 4.6 render.py

```python
def render_report(
    run_id: str,
    provider_metrics: list[ProviderMetrics],
    recommended_priority: list[str],
) -> str:
    """Render markdown report content. Caller writes to docs/benchmarks/."""
```

**报告 structure** (`docs/benchmarks/<date>-llm-provider-benchmark.md`):

```markdown
# LLM Provider Benchmark — <date>

## Run
- run_id: <id>
- providers: minimax (real) / anthropic (mock) / openai (mock)
- calls/provider: 10 (3 chapters × 3 runs + 1 control)
- fixture: huiyu-dangan/golden-set/chapters/{ch001, ch003, ch010} + 林栀

## Per-provider metrics

| provider | parse_rate | schema_compliance | canon_level | composite | cost/call | p50 (s) | p95 (s) | consistency |
|----------|-----------|------------------|-------------|-----------|-----------|---------|---------|-------------|
| minimax  | 0.9       | 0.8              | 1.0         | 0.90      | $0.0012   | 2.1     | 3.5     | 0.85        |
| anthropic (mock) | ... | ... | ... | ... | n/a | 0.05 | 0.08 | 1.0 |
| openai (mock) | ... | ... | ... | ... | n/a | 0.04 | 0.06 | 1.0 |

## Confidence distribution

| provider | high | medium | low |
|----------|------|--------|-----|
| minimax  | 5    | 3      | 1   |
| ...      |      |        |     |

## Threshold check

Quality threshold = 0.90. Providers above threshold and cost-ordered:
1. minimax (composite=0.90, cost=$0.0012)
2. ...

## Recommended priority

`default_priority = ["minimax", "anthropic", "openai"]`

Reasoning: <short summary>

## Diff to apply

```diff
- default_priority = ["minimax", "anthropic", "openai"]
+ default_priority = ["<new order>"]
```
```

---

## 5. Data Flow

```
CLI: python -m infra.llm_benchmarks.run --provider all --run-id 2026-08-26-baseline --real
  │
  ▼
run_benchmark(provider, run_id, real=True) × 3 (serial, per --provider all)
  │
  ├─ fixtures.load_golden_chapters(slug="huiyu-dangan", chapter_ids=[1,3,10])
  │   → list[str] (chapter texts)
  │
  ├─ providers.get_provider_llm(provider, real=real)
  │   → LLMService (minimax real) | MockLLMService (anthropic/openai mock)
  │
  ├─ for chapter_id in [1,3,10]:           ← 3 chapters
  │     for run_index in [1,2,3]:            ← 3 runs each (consistency)
  │       call_provider(provider, chapter_id, run_index)
  │   call_provider(provider, chapter_id=0, run_index=0)  ← 1 control
  │
  ├─ call_provider():
  │     t0 = time.monotonic()
  │     raw = llm.generate(prompt=build_user_prompt(...), system=SYSTEM_PROMPT)
  │     latency = time.monotonic() - t0
  │     proposals = parse_proposals_json(raw)
  │     parse_ok = True (no exception)
  │     schema_ok = all(ProposalResponse(**p) for p in proposals)
  │     canon_level_ok = all(p.payload.canon_level in {"Draft","Secondary","Primary"} for p)
  │     result = CallResult(...)
  │     results.write_call_result(run_id, result)  → JSON file
  │     return result
  │
  ├─ metrics.compute_metrics([call_1, ..., call_10]) → ProviderMetrics
  │
  ├─ for 3 providers: render combines 3 ProviderMetrics → markdown
  │     render.recommend_priority([m1, m2, m3], threshold=0.9) → list[str]
  │
  ▼
docs/benchmarks/<date>-llm-provider-benchmark.md (written by run.py orchestrator)
plugin_manager.py:150 default_priority (updated via follow-up commit if needed)
CLAUDE.md + .lingwen/architecture.yml (sync via follow-up commit)
```

---

## 6. Error Handling

| 失败场景 | 处理策略 | 可见性 |
|---|---|---|
| `MINIMAX_API_KEY` 缺失 | fail entire run, exit 2 + clear stderr | 高 (立即) |
| `MINIMAX_API_KEY` 无效 (401) | fail entire run, exit 2 | 高 |
| minimax timeout / 5xx | log warning + mark `failed=True` + continue | 中 (per-call log) |
| minimax rate limit (429) | retry once with 5s sleep,再 fail → mark `failed=True` + continue | 中 |
| Mock provider 失败 (deterministic,理论不应发生) | pytest mode → raise + fail test;CLI mode → raise + exit 1 | 高 |
| `parse_proposals_json` 失败 (raw 不可解析) | mark `parse_ok=False`,proposals=[] → 影响 `parse_rate` | 低 |
| ProposalResponse schema 失败 | mark `schema_ok=False`,proposal 不进 result list → 影响 `schema_compliance` | 低 |
| canon_level 非法值 | mark `canon_level_ok=False`,其他字段仍记 → 影响 `canon_level_compliance` | 低 |
| results/ 写盘失败 (disk full / permission) | log warning + skip write,benchmark continue | 中 |
| results/ 目录创建失败 | fail entire run, exit 1 (blocker) | 高 |
| CLI arg 错 | argparse exit 2 + usage | 高 |
| fixture 文件缺失 | `FileNotFoundError` + 明确文件名,exit 1 | 高 |

**Fail-fast boundary**: auth/CLI/fixture/results-mkdir 类 blocker fail-fast;运行时网络异常 continue(数据更全)。

**Log level**:
- `logger.error` — fail-fast blocker (exit 非 0)
- `logger.warning` — per-call 失败 (continue)
- `logger.info` — 进度 ("minimax/3 anthropic/10 call done")
- `logger.debug` — 每 call raw JSON (debug LLM 行为)

---

## 7. Testing

### 7.1 测试目录

```
tests/infra/llm_benchmarks/
├── test_metrics.py        # pure function tests
├── test_providers.py      # MockLLMService + factory
├── test_fixtures.py       # chapter loader (tmp_path fixture)
├── test_results.py        # write/read round-trip
├── test_render.py         # markdown 报告 rendering
└── test_run.py            # end-to-end orchestration (all-mock)
```

### 7.2 TDD workflow (per Phase 119 §4.9)

- RED: 先写 test, verify fail
- GREEN: 最小实现, verify pass
- REFACTOR: ruff + coverage check

### 7.3 Mock 策略

- pytest 默认**全 mock** (不依赖 env var)
- `test_run.py` 用 monkeypatch 把 `LLMService.get()` 替换成 `MockLLMService` (确保真 provider **永不** 在 CI 跑)
- CLI 真跑 (`--real`) 是 manual,**不**在 pytest default collection 里
- 任何 `os.environ.get("MINIMAX_API_KEY")` 在 tests 里都 patch 成 `"test-key"` (避免意外 hit)

### 7.4 Coverage 目标

≥ 80% per `common/testing.md`

### 7.5 关键 test cases

**test_metrics.py** (~12 tests):
- `parse_rate`: 5 calls 4 parse ok → 0.8
- `schema_compliance`: parse ok 中 3 schema ok → 0.6
- `latency_p50/p95`: 10 latencies sorted → 中位数 + 95th
- `consistency_score`: 同 chapter 3 runs proposals 100% 一致 → 1.0
- `quality_composite`: (parse + schema + canon_level) / 3 sanity
- `recommend_priority`: composite ≥ threshold 按 cost 排,未达标 append 末尾
- edge: empty calls → all zeros, no division by zero
- edge: 全 failed → parse_rate = 0, 仍 composite

**test_providers.py** (~5 tests):
- MockLLMService returns canned for known hash
- `get_provider_llm("anthropic", real=False)` → MockLLMService
- `get_provider_llm("minimax", real=True)` + env unset → RuntimeError
- `get_provider_llm("minimax", real=False)` → MockLLMService (no env check)

**test_fixtures.py** (~3 tests):
- `load_golden_chapters("huiyu-dangan", [1,3,10])` returns 3 non-empty strings
- 缺文件 → FileNotFoundError with filename in message
- 排序按 chapter_id asc

**test_run.py** (~5 tests):
- `run_benchmark("minimax", "test-run", real=False)`:
  - 10 CallResults 产生 (3 chapters × 3 runs + 1 control)
  - ProviderMetrics returned with sane defaults
  - results/<run-id>/ 有 10 JSON files
  - monkeypatched LLMService.get() NEVER called (mock only path)
- `--real` flag in test mode raises (env-gated)

**test_results.py** (~4 tests):
- `write_call_result` → file exists with correct JSON schema
- `read_run_results` round-trip preserves CallResult fields
- `list_runs` returns run_ids sorted by mtime desc
- mkdir failure → RuntimeError (blocker)

**test_render.py** (~3 tests):
- 3 mock ProviderMetrics → markdown 含 3-row table + recommended priority
- recommended priority in diff block matches `recommend_priority()` output
- threshold = 0.9 不达标 provider 在末尾

---

## 8. Deliverables

| 交付物 | 路径 | commit message |
|---|---|---|
| Spec doc | `docs/superpowers/specs/2026-08-26-phase-120-llm-provider-benchmark-design.md` | `docs(phase-120): add design doc` |
| Implementation | `infra/llm_benchmarks/` + `tests/infra/llm_benchmarks/` | `feat(llm-bench): Phase 120 LLM provider benchmark module` |
| Benchmark run results | `infra/llm_benchmarks/results/2026-08-26-baseline/*.json` (gitignored) | (本地, 不 commit) |
| Markdown 报告 | `docs/benchmarks/2026-08-26-llm-provider-benchmark.md` | `docs(phase-120): add LLM provider benchmark report` |
| Hardcode 更新 | `packages/lingwen-llm/src/lingwen_llm/providers/plugin_manager.py:150` | `chore(llm): update default_priority per benchmark` |
| 文档 sync | `CLAUDE.md` (v15.4 → v15.5) + `.lingwen/architecture.yml` | `docs: bump CLAUDE.md to v15.5 (Phase 120 闭环)` |

**Commit strategy** (per Phase 119 handoff §4.6 inline execution over subagent):
- 5 commits sequential (spec → impl → run+report → hardcode → doc sync)
- 不开 feature branch (跟 Phase 118/119 一致)

---

## 9. Out of Scope

- **OOS1**: prompt engineering (system prompt 调优) — 本 phase 只对比不改
- **OOS2**: 跑真 anthropic / openai — cost 控制, mock only
- **OOS3**: 加新 provider (e.g. DeepSeek, Qwen, Mistral) — 只对比已注册 3 个
- **OOS4**: 改 `infra/llm_service.py` failover 逻辑 — Phase 118 已闭环
- **OOS5**: cross-character consistency — 用户未选此维度
- **OOS6**: cost calculation accuracy 深度校准 — 用 provider 公开 rate 估算, 不接真实 billing API
- **OOS7**: benchmark results 入库 (e.g. SQLite) — gitignore 本地足够, 后续如需 audit 再 migrate

---

## 10. Risks

| 风险 | 缓解 |
|---|---|
| minimax 真 provider 临时不可用 (network blip) | per-call fail + continue, report 标记 `n_failed > 0` |
| minimax output token 计费模式不公开 | 用估算 (raw_response 长度 / 4 chars ≈ tokens) + provider 公开 rate, 文档注明 "estimated" |
| Mock canned JSON 过于偏离真 provider 输出 | minimax 真跑 + mock 对照,report 注明 mock 不能代表真 quality |
| `default_priority` 推荐顺序与 hardcode 现有顺序不同 | report 单独列 "diff to apply" 段,让 reviewer 显式 review 后再 commit |
| benchmark rerun 结果 drift (LLM temperature=0.2 不是 0) | consistency_score metric 量化 drift, report 列出 |
| pytest 中意外 hit minimax 真 provider (CI 烧钱) | monkeypatch LLMService.get() + tests 里 env var patch 为 "test-key" |

---

## 11. References

- **Phase 119 handoff** §2 priority 1: `docs/superpowers/specs/2026-08-26-phase-119-handoff.md` (this phase supersedes §2.A)
- **Phase 118 handoff** §1.4 (Task #17): `docs/superpowers/specs/2026-08-26-phase-118-handoff.md` (LLM agent 第一次集成)
- **Plugin manager hardcode**: `packages/lingwen-llm/src/lingwen_llm/providers/plugin_manager.py:150`
- **Agent extractor prompt**: `infra/world_db/agent_extractors.py:43-55` (SYSTEM_PROMPT)
- **Schema validation**: `infra/world_db/agent_schemas.py` (ProposalResponse + parse_proposals_json)
- **LLM service failover**: `infra/llm_service.py:103-119` (_init_providers)
- **Test fixture**: `projects/huiyu-dangan/golden-set/chapters/ch001.md + ch003.md + ch010.md`
- **Conventions**: `.lingwen/architecture.yml` + `.lingwen/constraints.yml` + Phase 119 handoff §4-§5

---

> **Spec written**. 等用户 review → 自审 → 启动 `superpowers:writing-plans` skill 生成 implementation plan。
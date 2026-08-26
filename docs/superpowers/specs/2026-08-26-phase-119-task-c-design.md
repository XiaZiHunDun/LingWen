# Phase 119 — Task C 设计: Rate Limiter per-IP Scoping

> **目的**: 闭环 Phase 118 follow-up — 把 `_AgentRateLimiter` 从 process-global counter 升级为 per-IP dict + lazy TTL,防止单进程多 client 共享 quota。
> **生成时间**: 2026-08-26
> **状态**: 设计已批准,待 writing-plans 出实施计划
> **承接**: `docs/superpowers/specs/2026-08-26-phase-118-handoff.md` §2 优先级 2.C

---

## 0. TL;DR

`_AgentRateLimiter` 当前是单 counter (`self._count`);单进程多 tab/多 user 共享 5-call quota。Task C 改为 dict-per-key,key 用 `request.client.host`(FastAPI Request dependency 注入)。Lazy TTL eviction 防 dict unbounded。Approach A。2 文件改动 / +2 tests / ~1 小时。**0 frontend 改动**。

---

## 1. 背景与动机

### 1.1 Phase 118 现状

```python
# apps/studio_api/routes/world.py lines 282-303
class _AgentRateLimiter:
    def __init__(self, max_calls: int = 5):
        self._max_calls = max_calls
        self._count = 0

    def allow(self) -> bool:
        if self._count >= self._max_calls:
            return False
        self._count += 1
        return True

    def reset(self) -> None:
        self._count = 0
```

**Gap**: 单 counter 跨所有 client 共享:
- User A 触发 5 次 → User B 直接 429
- 单 user 多 tab 同 quota
- 单进程跑 100 个 client → 全 process 共享 5 次/启动

### 1.2 用户已选 Approach A

**Dict-based per-key counter + lazy TTL eviction + FastAPI Request inject**:
- `allow(key: str, *, now: float | None = None) -> bool` (key 用 `request.client.host`)
- 每次 `allow()` 调一次 `_evict()` 清掉过期 entries(基于 `time.monotonic()`)
- 现有 `test_agent_extract_rate_limit` 行为不变(TestClient 默认 `("testclient", 50000)` host,共享 quota)

**Why not B (background cleanup)**: 多 asyncio task,scope 拉大,1h 估时会被打穿。lazy eviction 在请求路径上做足够简单。

---

## 2. 文件改动清单

| 文件 | 类型 | 改动 |
|------|------|------|
| `apps/studio_api/routes/world.py` | Modify | + `Request` import;改写 `_AgentRateLimiter` (dict + lazy TTL);routes 加 `request: Request` param + 传 `client.host` |
| `apps/studio_api/tests/test_world_route.py` | Modify | +2 tests (per-IP 隔离 + TTL eviction);**保留** 现有 `test_agent_extract_rate_limit`(行为不变) |

---

## 3. Backend Design — `_AgentRateLimiter` refactor

### 3.1 New class shape

```python
class _AgentRateLimiter:
    """Per-key counter for agent extraction calls.

    Phase 119 Task C: replaces process-global counter with per-key dict
    (typically keyed by client IP). Lazy TTL cleanup evicts entries that
    have not been touched in `ttl_seconds` to bound memory growth.
    """

    def __init__(self, max_calls: int = 5, ttl_seconds: int = 3600):
        self._max_calls = max_calls
        self._ttl_seconds = ttl_seconds
        self._counters: dict[str, int] = {}
        self._last_access: dict[str, float] = {}

    def allow(self, key: str, *, now: float | None = None) -> bool:
        import time
        if now is None:
            now = time.monotonic()
        self._evict(now)
        if self._counters.get(key, 0) >= self._max_calls:
            return False
        self._counters[key] = self._counters.get(key, 0) + 1
        self._last_access[key] = now
        return True

    def reset(self, key: str | None = None) -> None:
        if key is None:
            self._counters.clear()
            self._last_access.clear()
        else:
            self._counters.pop(key, None)
            self._last_access.pop(key, None)

    def _evict(self, now: float) -> None:
        threshold = now - self._ttl_seconds
        expired = [k for k, t in self._last_access.items() if t < threshold]
        for k in expired:
            self._counters.pop(k, None)
            self._last_access.pop(k, None)
```

### 3.2 Why `time.monotonic` not `time.time`

- Monotonic 不受系统时钟调整 (sleep / NTP) 影响
- `_evict()` 用 monotonic 比较,稳定
- Test 注入 `now=` 参数时用 float 即可

### 3.3 Why lazy TTL

- 每次 `allow()` 调一次 `_evict()` 是 O(n) over current keys
- Keys 通常 < 100(client IP 集合实际不会爆),O(n) 不是瓶颈
- 无 asyncio background task 复杂度
- `ttl_seconds=3600` (1 hour) 默认: 1 小时没访问 → 计数清零

### 3.4 Imports

Add `Request` to existing fastapi import line:

```python
from fastapi import Body, FastAPI, HTTPException, Query, Request
```

---

## 4. Routes — FastAPI Request injection

### 4.1 Both agent endpoints updated

**Before** (line 217):
```python
@app.post("/api/world/agent/extract-from-chapters")
def agent_extract_from_chapters(payload: dict = Body(...)):
    ...
    if not agent_rate_limiter.allow():
        raise HTTPException(429, detail="agent extraction rate limit exceeded (5 calls per session)")
```

**After**:
```python
@app.post("/api/world/agent/extract-from-chapters")
def agent_extract_from_chapters(
    request: Request,
    payload: dict = Body(...),
):
    client_host = request.client.host if request.client else "unknown"
    if not agent_rate_limiter.allow(client_host):
        raise HTTPException(429, detail="agent extraction rate limit exceeded (5 calls per session per IP)")
```

(Same pattern for `agent_extract_from_prompt` line 250.)

### 4.2 Why `request.client` can be None

- TestClient 在某些 transport 下没 client info
- Unix socket transport 没 client info
- Fallback `"unknown"` 让无 IP 的 caller 走 1 quota(比 raise 更友好)

### 4.3 TestClient compatibility

TestClient 默认 `request.client = ("testclient", 50000)`,所以 `host="testclient"`。

现有 `test_agent_extract_rate_limit` 在 TestClient 上跑,所有 5 calls 都来自 "testclient" host → 共享 quota → 行为不变。

---

## 5. Tests

3 tests total in `test_world_route.py`:

### 5.1 Existing — `test_agent_extract_rate_limit` (KEEP)

No change. Already tests: 5 calls pass, 6th returns 429 with "rate limit" in detail.

### 5.2 NEW — `test_agent_rate_limiter_isolates_per_key` (unit test on class)

```python
def test_agent_rate_limiter_isolates_per_key():
    """Two keys have independent counters; one hitting cap does not block the other."""
    import apps.studio_api.routes.world as wmod
    rl = wmod._AgentRateLimiter(max_calls=5)

    # IP1 hits cap
    for _ in range(5):
        assert rl.allow("1.2.3.4") is True
    assert rl.allow("1.2.3.4") is False  # 6th call from IP1 blocked

    # IP2 starts independent
    for _ in range(5):
        assert rl.allow("5.6.7.8") is True
    assert rl.allow("5.6.7.8") is False  # IP2 also at cap
    # IP1 still blocked
    assert rl.allow("1.2.3.4") is False

    # reset(IP1) frees IP1's quota
    rl.reset("1.2.3.4")
    assert rl.allow("1.2.3.4") is True
```

### 5.3 NEW — `test_agent_rate_limiter_ttl_evicts_old_keys`

```python
def test_agent_rate_limiter_ttl_evicts_old_keys():
    """Keys not accessed within ttl_seconds are evicted; counter freed."""
    import apps.studio_api.routes.world as wmod
    rl = wmod._AgentRateLimiter(max_calls=5, ttl_seconds=10)

    # IP1: 5 successful calls at t=100..104
    for t in (100.0, 101.0, 102.0, 103.0, 104.0):
        assert rl.allow("1.2.3.4", now=t) is True
    assert rl.allow("1.2.3.4", now=105.0) is False  # cap reached

    # At t=200 (> ttl=10 from last_access=105.0), IP1 evicted on next call
    assert rl.allow("1.2.3.4", now=200.0) is True
```

**Why inject `now=`**: 让 test 不依赖真实时间,deterministic。生产代码 `now=None` 走 `time.monotonic()`。

---

## 6. 验收 gates

```bash
# Backend tests pass
cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_world_route.py -v
# Expected: 11 (was) → 13 PASS (+2 new unit tests)

# Ruff clean
cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m ruff check apps/studio_api/routes/world.py apps/studio_api/tests/test_world_route.py
# Expected: clean
```

**无 frontend 测试**(0 改动)。

---

## 7. Scope 守卫 (不做)

继承 Phase 118 handoff §5 + 本 Task 限定:

- ❌ 不加 sliding window / token bucket (超出 scope,YAGNI)
- ❌ 不动 frontend (`useWorldAgent` 已经处理 429 message,无需改)
- ❌ 不加 background cleanup task (lazy TTL 够,scope 拉大不值)
- ❌ 不动 `agent_extractors.py` / `queries.proposals.py` (纯 hardening)
- ❌ 不加 per-user scoping (auth 未接,per-IP 是当下合理代理)
- ❌ 不动 `extractFromPrompt` 路径 logic (只加 `request` param)
- ❌ 不改 max_calls 默认值 (5 calls/session 维持)
- ❌ 不加 cleanup metric / observability (后续 v15.4+ 再考虑)

---

## 8. 风险评估

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| `request.client` 为 None (test / Unix socket) | 低 | 低 | fallback `"unknown"` |
| TestClient host 与 prod host 不一致 → 测试过 prod 错 | 中 | 低 | TestClient 默认 "testclient" host;新 unit test 直接测 class,不依赖 FastAPI Request |
| Lazy eviction 性能 | 极低 | 低 | dict size 实际 < 100,O(n) 不是瓶颈 |
| 改 `_AgentRateLimiter` signature 破坏现有 caller | 低 | 中 | routes 是唯一 caller,在同一文件内同步改 |
| `import time` 每次调用 | 低 | 低 | 可移到 module 顶部;本设计放函数内避免 module-level 副作用,符合 handoff §5 "lazy import" 风格 |

---

## 9. 后续 (Phase 119 收尾)

Task C 闭环后 Phase 119 carryover 全清。可选收尾:

- **Phase 117 遗留 ruff I001** in `test_markdown_roundtrip.py` (1 行,独立 commit)
- **Phase 119 cleanup**: bump CLAUDE.md v15.3 → v15.4 / 更新 MEMORY.md

---

> **设计完成**。下一步: writing-plans skill 出 Task C 实施计划。
# Phase 119 — World Follow-up 闭环 会话交接文档

> **目的**: 新会话从这个 doc 衔接 — 当前 master 状态、Phase 119 闭环内容、未做 carryover、下一步推荐。
> **生成时间**: 2026-08-26 (master @ `1e5cd283`)
> **前置阅读** (按顺序): `CLAUDE.md` v15.4 段 → Phase 118 handoff `2026-08-26-phase-118-handoff.md` → Phase 117 handoff `2026-08-26-phase-117-handoff.md` → 本文档
> **Supersedes**: Phase 118 handoff §2 优先级 1.A + 1.B + 2.C (Tasks A, B, C 全部闭环)

---

## 0. TL;DR

Phase 119 v15.4 在 master 上**已闭环**。16 commits ahead of `37343188` (Phase 118 baseline):

| Commit 范围 | 内容 |
|------|------|
| `8fcae6eb` ... `38c62579` | Phase 119 Task A (LoreEditor/TimelineEditor 接入) — 4 commits |
| `c25a1855` ... `4cc3c456` | Phase 119 Task B (chapterRange → chapterTexts 接线) — 7 commits |
| `993907bb` ... `ae374afb` | Phase 119 Task C (Rate limiter per-IP scoping) — 3 commits |
| `fbc99da2` | style: fix Phase 117 ruff I001 (1 行 import order) |
| `1e5cd283` | docs: CLAUDE.md v15.3 → v15.4 |

**所有 gate green**:
- backend tests: **38/38 PASS** (was 35, +3 new in Phase 119)
- frontend tests: **1731 passed + 1 skipped** (was 1724+1, +20 new in Phase 119)
- vue-tsc: **0 errors**
- ESLint: **0 errors / 0 warnings**
- ruff: **全部 clean** (Phase 117 I001 已 fix)

---

## 1. 已完成 (本会话)

### 1.1 Task A — LoreEditor / TimelineEditor 接入 Detail 页面

**改动**: `apps/dashboard/src/components/world/lore/LoreDetail.vue` + `timeline/TimelineEventDetail.vue`

- 加 `editing` ref + inline `<XxxEditor v-if="editing" />`
- 按钮文案 "新增条目" / "新增事件" (semantic 清晰,Editor 仍 create-only 不带 props)
- 镜像 `CharacterDetail.vue` pattern (line 28-34)
- + 1 scoped CSS rule per file

**Tests**: 8 new component tests (4 per detail),stub Editor via `vi.mock('@/.../XxxEditor.vue')`

**Lesson**: spec 用 `@/` alias import 即可 (不要 `../../../../` 数相对路径)

### 1.2 Task B — chapterRange → chapterTexts UI 接线

**改动**: backend + frontend 双层

**Backend**: `apps/studio_api/routes/world.py` +`GET /api/world/chapters?project=X&start=N&end=M` endpoint
- 读 `projects/<slug>/golden-set/chapters/ch{NNN}.md` (canonical, 无 frontmatter)
- Missing chapters silently skip,response 含 `found` vs `requested`
- 3 tests in `test_world_route.py`

**Frontend**: `useWorldAgent.js` +`fetchChapterTexts(projectSlug, chapterRange)` helper
- 包装 endpoint,throws on non-OK (caller-side display;unlike `extractFromChapters` silent return)
- 2 new tests in `use-world-agent.spec.js`

**UI**: `WorldProposalInbox.vue` 加 extract section (character dropdown + start/end inputs + 提取按钮 + result 行)
- 嵌在 `v-if="open"` panel 内 (toggle 之后)
- + scoped CSS
- 5 component tests,stub 3 composables (useWorldReview / useWorldDb / useWorldAgent)
- Helper: `mountAndOpen()` 在 test 里先 click toggle 再断言

**Lesson**: extract section 在 `v-if="open"` panel 内 → test 需先 click toggle。testid-class-sync 要求 kebab + BEM 双 class。

### 1.3 Task C — Rate limiter per-IP scoping

**改动**: `apps/studio_api/routes/world.py` refactor

- `_AgentRateLimiter` 从 process-global counter 改 dict-per-key
- `allow(key, *, now=None) -> bool` evicts entries with `last_access < now - ttl_seconds`
- TTL 默认 1h (`ttl_seconds=3600`),lazy eviction (无 background task)
- Routes inject FastAPI `Request`,pass `request.client.host` (fallback `"unknown"`)
- `time.monotonic()` for production,`now=` kwarg for deterministic tests
- `reset(key=None)` API:key 时清单个 entry,None 时清全部

**Tests**: 2 new unit tests (per-IP isolation, TTL eviction)。现有 `test_agent_extract_rate_limit` 行为不变 (TestClient 默认 `request.client.host="testclient"`)。

**Lesson**: TestClient 默认 host 是 `"testclient"`,所以同一 test client 内所有 calls 共享 quota — 现有 5-call 测试不需要改。

### 1.4 副产物 — CLAUDE.md 升级 + ruff 清理

- CLAUDE.md v15.3 → v15.4:加 Phase 119 段,清 done carryover,加 Phase 119 路径
- ruff I001 in `test_markdown_roundtrip.py` fix:2 个 `from infra.world_db.*` imports 改 alphabetical (markdown_roundtrip before schema)

---

## 2. 已知遗留 (Phase 120+ 候选)

### 优先级 1: LLM provider 策略 (Phase 118 follow-up,用户决策)

**A. LLM provider 主用+备用顺序**
- 决策: minimax / anthropic / openai 哪个作为主要 provider
- 现有 `infra/llm_service.py` 已支持多 provider 自动 failover,但顺序未决策
- 需要: 测三个 provider 的实际响应质量, 决定主用 + 备用顺序
- 估计: 半天 (config + 3 个 provider 对比测试 + prompt iteration)

### 优先级 2: 其他 carryover (从 Phase 118 handoff 继承,accepted)

**B. Prod preview regression** (Phase 114 accepted debt, **不要尝试修复**)
- cytoscape-fcose CJS + rollup commonjs 不兼容, 5 phase 投入失败, dev baseline 仍 authoritative
- E2E Playwright runtime 阻塞

### 优先级 3: 历史遗留 (不动)

- 232 个 ruff 错误 (历史,本 phase 文件外) — 不修, 不影响 CI
- 38+ knip unused exports (历史) — 不修
- 15 个 pytest collection errors (历史, 引用不存在的模块) — 不修

---

## 3. 推荐优先级 (新会话)

**短期 (Phase 120)**:
1. **Task A** (LLM provider 策略) — 半天,需用户决策

**中长期 (v15.5+)**:
- 暂无明确需求,可走 Phase 117/118/119 模式 (发现 → brainstorming → plan → TDD)

---

## 4. 用户策略 (重要)

### 已批准且有效 (继承自 Phase 117/118 handoff)

**1. Inline apply small fixes 政策**
- 触发: plan 有 bug (typo/矛盾/过时)
- 行动: controller inline fix + commit with detailed message
- 跳过: BLOCKED → escalate → re-dispatch cycle

**2. Subagent workflow** (per `superpowers:subagent-driven-development`)
- 流程: implementer → spec reviewer → code quality reviewer
- 每 task 3 个 subagent dispatch
- 简化 (本会话实际做法): 机械任务 (单一文件/单一函数) → controller 直接做 + inline review (测试覆盖 + ruff + vitest 充当 review)
- 复杂任务 (multi-file schema, route + composable + tests) → controller 直接做但每个组件都过 TDD RED→GREEN

**3. Architecture invariants** (per AGENTS.md, 仍 valid)
- `infra/` 禁止依赖 `dashboard/` / `apps/`
- 检查器 = 纯函数规则引擎
- L3/L4 禁止引用 L2
- 写审分离
- 创作流必须支持 checkpoint 恢复
- Phase 117 加入: `infra/world_db/` 是 `infra/persistence/` 姊妹模块, 不允许被 dashboard/ 直接依赖 (只走 FastAPI)
- Phase 118 加入: `infra/world_db/agent_schemas.py` 是 `agent_extractors.py` 的 sibling, 同模块内 import OK
- Phase 119 无新模块

**4. 优先级源**
- `.lingwen/architecture.yml` 是 AI-readable 真源 (Phase 117 加入 `world_db`, Phase 118-119 无变更)
- AGENTS.md 文字版 backup
- CLAUDE.md v15.4 是新会话入口 (2026-08-26 升级,反映 Phase 119 闭环)

### 新会话应当遵守的项目约定 (Phase 119 强化)

**5. testid-class-sync 规则** (Phase 8.36, v15.0+)
- 每个 `data-testid="X"` 必须有 `class` 含 `X` 的 kebab-case token
- 双 class pattern:kebab + BEM (e.g. `class="world-proposal-inbox-extract world-proposal-inbox__extract"`)
- Phase 119 fix:Task B UI 初版只 BEM 没 kebab,ESLint 报 4 warnings → fixup commit `8b3052a8`

**6. no-class-selector-in-test 规则** (Phase 8.31, v15.0+)
- 测试中禁止 `wrapper.find('.classname')`
- 用 `data-testid` 或 `wrapper.text()` 替代

**7. vi.hoisted() 限制** (v15.0+)
- hoisted callback 只能访问 `vi`, 不能访问 Vue/JS imports
- Vue `ref()` / `computed()` 必须在 top-level, hoisted 之外

**8. vite-auto-imported globals**
- 测试环境无自动导入, 需要在 `globalThis` 上 stub (Phase 118 useWorldAgent test 用 `globalThis.fetch = vi.fn()`)

**9. TDD per task** (per `superpowers:test-driven-development`)
- Write failing test → verify RED → implement → verify GREEN → commit
- Phase 119 严格 RED→GREEN 模式 (Task A / B / C 全遵循)

**10. Pydantic v2 模式** (Phase 118 加入)
- 项目用 pydantic v2, 用 `BaseModel` + `Field` + `field_validator`

**11. Test injection for external services** (Phase 118 加入)
- 任何调用 LLM/外部 API 的模块都要支持 kwarg 注入 mock (避免测试打真 API)
- `extract_*(..., llm_service=None)` 默认走 `LLMService.get()`, 测试传 `FakeLLMService`

**12. TestClient 默认 host** (Phase 119 加入)
- TestClient 的 `request.client.host` 默认 `"testclient"`,所以 rate limiter 测试行为可保持 (同一 client 共享 quota)
- 想测 per-IP 隔离,直接在 `_AgentRateLimiter` class 上 unit test,不走 FastAPI Request

**13. Spec 自审 规则** (Phase 119 加入)
- 写完 spec 后 self-review:扫 TBD/TODO,check 内部一致性,check scope,消除 ambiguity (e.g. button placement "之后或文末" → "文末,接在 pre body 之后")
- 然后问 user review spec → writing-plans

---

## 5. 避免 (Don't Do)

继承自 Phase 117/118 handoff, 加上本会话发现:

- ❌ **不要尝试 prod preview fix** (Phase 114 accepted debt, 5 phase 投入失败, ROI 不匹配)
- ❌ **不要主动开第九本书 / 星陨 wave / SaaS / 录屏**
- ❌ **不要恢复 llm×7 每次 push 全跑** (改 `projects/**`/`infra/**` 或 label `llm-check` 才跑)
- ❌ **不要把 spec/plan/audit 文档归档到 docs/archive/** — 让历史可见
- ❌ **不要自作主张重命名 `lingwen` 命名空间** — 品牌字符串真源在 `apps/dashboard/src/config/brand.js`
- ❌ **不要加 `@ts-ignore` / `as any` / 空 catch** — 见 `.lingwen/constraints.yml`
- ❌ **不要直接 import `infra/` 在 `apps/dashboard/`** — 必须走 FastAPI
- ❌ **不要在 query 模块里 mutate `cur.rowcount` / 静默吞错** — 见 Phase 117 修复的 `update_proposal_status` silent failure bug
- ❌ **不要用 cytoscape-fcose** — Phase 114 已 accept, 用 vis-network 替代
- ❌ **不要 commit `.claude/worktrees/`** — subagent worktrees, 不属于本仓库
- ❌ **不要在 agent_extractors.py 顶层 import `infra.llm_service`** — 必须 lazy import, 避免 module load 时触发 API key check / provider plugin loading
- ❌ **不要在 component test 里直接 spec 算相对路径** — 用 `@/` alias (`vi.mock('@/.../XxxEditor.vue')` `import Xxx from '@/.../Xxx.vue'`)
- ❌ **不要给 testid 元素只 BEM class** — testid-class-sync 要求 kebab + BEM 双 class
- ❌ **不要假设 TestClient host 是真实 IP** — 默认 `"testclient"`,per-IP rate limit 测试要走 unit test on class

---

## 6. 项目入口

| 任务 | 命令 |
|------|------|
| 前端测试 (world only) | `cd apps/dashboard && pnpm vitest run tests/unit/components/world/ tests/unit/composables/use-world-agent.spec.js tests/unit/pages/world-page.spec.ts tests/unit/stores/useWorldStore.spec.js` |
| 前端测试 (全) | `cd apps/dashboard && pnpm vitest run` |
| 前端类型检查 | `cd apps/dashboard && pnpm tsc --noEmit` |
| 前端 lint | `cd apps/dashboard && pnpm eslint src/components/world src/pages/WorldPage.vue src/composables/world src/stores/useWorldStore.js` |
| 死代码检测 | `cd apps/dashboard && pnpm exec knip` |
| 构建 | `cd apps/dashboard && pnpm build` |
| Dev 启动 | `cd apps/dashboard && pnpm dev` |
| **后端测试 (Phase 119)** | `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/infra/world_db/ apps/studio_api/tests/test_world_route.py -v` |
| 后端测试 (全) | `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/ apps/studio_api/tests/ -v` |
| Ruff (全部) | `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m ruff check .` |
| **前端 install (fresh clone)** | `cd apps/dashboard && pnpm install` ← **必需**, 否则 world-page.spec.ts 全部失败 |

**注意**:
1. 后端必须用 `/home/ailearn/miniconda3/bin/python` (Python 3.13 + fastapi)。系统 `pytest` (Python 3.10) 缺 fastapi/sqlite3。
2. **Fresh checkout 必须 `pnpm install`** — 详 §5。

---

## 7. 关键文件指针

### Phase 119 新增

| 文件 | 用途 |
|------|------|
| `apps/dashboard/src/composables/world/useWorldAgent.js` | + `fetchChapterTexts(projectSlug, chapterRange)` helper |
| `apps/dashboard/src/components/world/lore/LoreDetail.vue` | + editing ref + toggle button + `<LoreEditor v-if="editing" />` |
| `apps/dashboard/src/components/world/timeline/TimelineEventDetail.vue` | + editing ref + toggle button + `<TimelineEditor v-if="editing" />` |
| `apps/dashboard/src/components/world/WorldProposalInbox.vue` | + extract section (UI 触发 chapter range → chapter texts) |
| `tests/unit/components/world/lore/LoreDetail.spec.ts` | 4 component tests (NEW Phase 119) |
| `tests/unit/components/world/timeline/TimelineEventDetail.spec.ts` | 4 component tests (NEW Phase 119) |
| `tests/unit/components/world/WorldProposalInbox.spec.ts` | 5 component tests (NEW Phase 119) |

### Phase 119 修改

| 文件 | 修改 |
|------|------|
| `apps/studio_api/routes/world.py` | + `GET /api/world/chapters` endpoint;`Request` import;both agent routes take `request: Request`;`_AgentRateLimiter` refactor (dict + TTL) |
| `apps/studio_api/tests/test_world_route.py` | +3 endpoint tests (chapter texts) + 2 limiter unit tests |
| `apps/dashboard/src/composables/world/useWorldAgent.js` | + `fetchChapterTexts` helper + update return shape |
| `apps/dashboard/tests/unit/composables/use-world-agent.spec.js` | +2 tests for `fetchChapterTexts` |
| `apps/dashboard/src/components/world/WorldProposalInbox.vue` | + extract section (template + script + scoped CSS);replace `onMounted(refresh)` with concurrent `refresh + loadCharacters` |
| `tests/infra/world_db/test_markdown_roundtrip.py` | 2 imports 改 alphabetical (ruff I001 fix) |
| `CLAUDE.md` | v15.3 → v15.4 (Phase 119 段 + paths 更新 + done carryover 清理) |

### 测试 (Phase 119 合计)

| 文件 | 测试数 | 状态 |
|------|--------|------|
| `apps/studio_api/tests/test_world_route.py` | 13 (was 11) | +2 limiter unit tests |
| `apps/dashboard/tests/unit/components/world/lore/LoreDetail.spec.ts` | 4 (new) | Phase 119 Task A |
| `apps/dashboard/tests/unit/components/world/timeline/TimelineEventDetail.spec.ts` | 4 (new) | Phase 119 Task A |
| `apps/dashboard/tests/unit/components/world/WorldProposalInbox.spec.ts` | 5 (new) | Phase 119 Task B |
| `apps/dashboard/tests/unit/composables/use-world-agent.spec.js` | 7 (was 5) | +2 fetchChapterTexts tests |
| **Phase 119 合计 new** | **+15 tests** (3 backend + 13 frontend) | |

### Spec + Plan + Handoff (Phase 119)

| 文件 | 用途 |
|------|------|
| `docs/superpowers/specs/2026-08-26-phase-119-task-a-design.md` | Task A design |
| `docs/superpowers/specs/2026-08-26-phase-119-task-b-design.md` | Task B design |
| `docs/superpowers/specs/2026-08-26-phase-119-task-c-design.md` | Task C design |
| `docs/superpowers/plans/2026-08-26-phase-119-task-a.md` | Task A implementation plan |
| `docs/superpowers/plans/2026-08-26-phase-119-task-b.md` | Task B implementation plan |
| `docs/superpowers/plans/2026-08-26-phase-119-task-c.md` | Task C implementation plan |
| `docs/superpowers/specs/2026-08-26-phase-119-handoff.md` | **本会话入口** (新) |
| `docs/superpowers/specs/2026-08-26-phase-118-handoff.md` | Phase 118 handoff (历史) |

### 项目配置

| 文件 | 用途 |
|------|------|
| `CLAUDE.md` | **新会话入口** — v15.4,Phase 119 闭环已加 |
| `AGENTS.md` | 5 条架构不变量 |
| `.lingwen/architecture.yml` | 模块边界 (Phase 117 加入 `world_db`, Phase 118-119 无变更) |
| `.lingwen/constraints.yml` | 9 个 A00X 反反模式 |
| `~/.claude/projects/-home-ailearn-projects-LingWen/memory/MEMORY.md` | 跨 session 记忆 (Phase 119 已 sync) |

---

## 8. 历史背景

### 项目维护模式 (持续)

- v15.0 (Phase 115) Immersive Write Workspace v1
- v15.1 (Phase 116) follow-up 闭环
- v15.2 (Phase 117) World Visualization v1 — 第一次做产品侧添加 (23-task subagent-driven-development)
- v15.3 (Phase 118) World LLM Agent + cleanup — 第一次做**LLM 后端**集成
- v15.4 (Phase 119, 本次) — 3 个 world follow-up 闭环 (UI wiring + chapter texts + rate limiter hardening) + ruff 清理 + CLAUDE.md 升级

### Phase 119 关键决策 (已闭环, 不要重审)

1. **Editor 语义 = create-only**: Task A 用户选 "镜像 + 改名",按钮文案从误导的 "编辑" 改为 "新增条目" / "新增事件"。Editor 内部不变。
2. **chapter source = `golden-set/chapters/`**: canonical published chapters (vs `03_内容仓库/04_正文/` workspace authoring)。避免 frontmatter 噪声给 LLM。
3. **Bulk-fetch endpoint**: 不用前端 N 次 `/api/write/:id` 轮询。一次性 bulk 走 `/api/world/chapters`。
4. **Rate limiter per-IP (not per-user)**: auth 未接,per-IP 是当下合理代理。Lazy TTL eviction 防 dict unbounded。
5. **Spec self-review**: 写完 spec 后内嵌 review,扫 TBD/TODO + 消除 ambiguity,避免 implementation 阶段才发现矛盾。
6. **Inline execution over subagent-driven**: 跟 Phase 118 handoff §4.2 推荐一致 (multi-file + tests → controller 直接做,过 TDD)。
7. **Direct on master over branch**: 跟 Phase 118 闭环模式一致 (3 commits direct → push 一次),小/中 scope 不开 feature branch。

### 已知技术约束 (新会话须知)

1. **vis-network bundle**: lazy-loaded, ~150kb gzipped, 只在 /world graph tab 激活时加载 (Phase 117)
2. **prod preview regression** (Phase 114): cytoscape-fcose CJS + rollup commonjs 不兼容, 5 phase 投入失败, dev baseline 仍 authoritative; E2E Playwright runtime 阻塞
3. **Python 环境**: 后端必须用 `/home/ailearn/miniconda3/bin/python` (Python 3.13), 系统 `pytest` (Python 3.10) 缺 fastapi/sqlite3
4. **CLAUDE.md v15.4**: 是当前会话入口 (2026-08-26 升级)
5. **fresh install 需要 `pnpm install`**: Phase 117 merge 没跑 install 导致 regression, 详见 §5
6. **TestClient 默认 host = "testclient"**: per-IP rate limit 测试要走 unit test on class,不走 FastAPI Request

---

## 9. 下次会话快速启动清单

新会话第一件事:

1. 读 `CLAUDE.md` (v15.4)
2. 读 `docs/superpowers/specs/2026-08-26-phase-118-handoff.md` (Phase 118 状态)
3. 读 `docs/superpowers/specs/2026-08-26-phase-117-handoff.md` (Phase 117 状态)
4. **读本文档** (Phase 119 状态)
5. 跑验收:
   ```bash
   # Fresh clone 或 vis-network 缺的情况下:
   cd apps/dashboard && pnpm install

   # 后端 (Phase 119 全套)
   cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/infra/world_db/ apps/studio_api/tests/test_world_route.py -v
   # 预期: 13 PASS (chapter texts endpoint + 2 limiter unit + 5 phase 118 agent routes + 5 misc)
   
   # 前端 (world subtree)
   cd apps/dashboard && pnpm vitest run tests/unit/components/world/ tests/unit/composables/use-world-agent.spec.js tests/unit/pages/world-page.spec.ts tests/unit/stores/useWorldStore.spec.js
   # 预期: 26 PASS (8 Lore/Timeline detail + 5 WorldProposalInbox + 7 useWorldAgent + 3 page + 3 store)
   
   # ruff 全 check
   cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m ruff check .
   # 预期: 全 clean (Phase 117 I001 已 fix)
   ```
6. 决定下一步: **Task A** (LLM provider 策略 — 用户决策) 或 Phase 120 (新需求)

---

## 10. 备忘 (本会话发现的可复用模式)

### TDD per component pattern (Phase 119 强化)

- **stub 整个 Editor**: `vi.mock('@/.../LoreEditor.vue', () => ({ default: { name: 'LoreEditor', template: '<div data-testid="lore-editor-stub" />' } }))`
- **stub 多个 composable**: 在 spec 顶部 `vi.mock('@/composables/world/useX.js', () => ({ useX: () => ({...}) }))` × N
- **mountAndOpen helper for v-if panel**: 测试 `v-if="open"` 内 element 时,先 click toggle,再断言
- **`now=` kwarg for time injection**: rate limiter unit test 用 `rl.allow(key, now=t)` 注入 deterministic time

### Testid-class-sync 双 class pattern (Phase 119 加入)

```vue
<!-- WRONG: only BEM class -->
<section class="world-proposal-inbox__extract" data-testid="world-proposal-inbox-extract">

<!-- CORRECT: kebab + BEM dual class -->
<section class="world-proposal-inbox-extract world-proposal-inbox__extract" data-testid="world-proposal-inbox-extract">

<!-- WRONG: select/inputs with testid but no class -->
<select data-testid="world-proposal-inbox-extract-slug">

<!-- CORRECT: select with kebab class -->
<select class="world-proposal-inbox-extract-slug" data-testid="world-proposal-inbox-extract-slug">
```

### Dict-based rate limiter pattern (Phase 119 加入)

```python
class _RateLimiter:
    def __init__(self, max_calls=5, ttl_seconds=3600):
        self._max = max_calls
        self._ttl = ttl_seconds
        self._counters: dict[str, int] = {}
        self._last: dict[str, float] = {}

    def allow(self, key, *, now=None):
        if now is None: now = time.monotonic()
        self._evict(now)  # lazy cleanup
        if self._counters.get(key, 0) >= self._max: return False
        self._counters[key] = self._counters.get(key, 0) + 1
        self._last[key] = now
        return True

    def _evict(self, now):
        threshold = now - self._ttl
        for k in [k for k, t in self._last.items() if t < threshold]:
            self._counters.pop(k, None)
            self._last.pop(k, None)
```

- Lazy eviction: O(n) over current keys (实际 < 100)
- `time.monotonic()` 不受系统时钟调整影响
- Test 注入 `now=` 给确定性
- Fallback `"unknown"` 当 `request.client` 为 None

### Spec self-review pattern (Phase 119 加入)

写完 spec 后:
1. 扫 TBD/TODO/vague (无 placeholder)
2. 检查内部一致性 (definition vs usage)
3. Check scope (single plan-scope vs 需要 decompose)
4. 消除 ambiguity (e.g. "之后或文末" → "文末,接在 <pre> body 之后,镜像 X lines Y-Z")
5. Fix inline, 不重新 review

然后问 user review spec → writing-plans。

### Self-review 找出的真实 bug (本会话)

- **Task A spec**: button placement "之后或文末" → 明确 "文末,接在 <pre> body 之后"
- **Task B spec**: onMounted 改动 "在 refresh() 之后加:" → 明确 "替换原 onMounted(refresh)"
- 这两个 ambiguity fixup commit 分别是 `38c62579` (Task A) + `4cc3c456` (Task B)

### Frontend path resolution lesson (Phase 119 加入)

- ✗ `import X from '../../../../src/components/world/X.vue'` — 数错深度,易错
- ✓ `import X from '@/components/world/X.vue'` — Vite `@/` alias for `src/`,所有 spec 一致用
- Phase 119 全 6 个新建/修改 spec 全部用 `@/`,no relative path counting needed

### testid-class-sync 早期预防 (本会话发现)

写新 template 时,**直接**给每个 `data-testid` 元素加 kebab class,不要等 ESLint 报 warning 再 fix。
- 写完 → 跑 `pnpm eslint src/...` → 0 warnings 一次过
- 不要先写 BEM-only 然后追加 fixup (multi-commit 噪声)

### Bash session 教训 (Phase 118 继承)

- bash session **不持久 cwd**, 每次 Bash tool call 默认 `/home/ailearn/projects/LingWen`, 即使之前用过 `cd apps/dashboard`
- 必须在**同一个 command 里**链 `cd ... && cmd`, 不能假设上次 cd 还在
- 调试时用 `pwd` 先确认 cwd 再跑命令

### 工程问题 (不属于本 phase)

- 232 个 ruff 错误 (历史, 本 phase 文件外) — 不修, 不影响 CI
- 38+ knip unused exports (历史) — 不修
- 15 个 pytest collection errors (历史, 引用不存在的模块) — 不修
- 1 个 Phase 117 I001 in `test_markdown_roundtrip.py` — 本 phase fixup (`fbc99da2`)

---

> **交接完成**。Phase 119 已合入 master (`1e5cd283`), 新会话可从 Phase 120 (LLM provider 决策) 或后续 spec 启动。
> **CLAUDE.md**: v15.3 → v15.4 已升级 (commit `1e5cd283`), 反映 Phase 119 闭环。
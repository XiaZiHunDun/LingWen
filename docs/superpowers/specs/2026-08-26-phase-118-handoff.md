# Phase 118 — World LLM Agent + Cleanup 闭环 会话交接文档

> **目的**: 新会话从这个 doc 衔接 — 当前 master 状态、Phase 118 闭环内容、未做 carryover、下一步推荐。
> **生成时间**: 2026-08-26 (master @ `37343188`)
> **前置阅读** (按顺序): `CLAUDE.md` v15.2 段 → Phase 117 handoff `2026-08-26-phase-117-handoff.md` → 本文档
> **Supersedes**: Phase 117 handoff §2 priority 1 + 2 (Tasks #14, #15, #16, #17 全部闭环)

---

## 0. TL;DR

Phase 118 v15.3 在 master 上**已闭环**。3 commits ahead of `55810cf8`:

| Commit | 内容 |
|--------|------|
| `8269e081` | `refactor(world_db): extract shared helpers + RevisionConflict base` (Tasks #14 + #15) |
| `1366aedc` | `fix(world_db): deterministic id from create_relationship on conflict` (Task #16) |
| `37343188` | `feat(world_db): Phase 118 LLM-backed agent extraction (replace stub)` (Task #17) |

**所有 gate green**：
- backend tests: **35/35 PASS** (was 19, +16 new)
- frontend tests: world_page 3/3 + store 3/3 + useWorldAgent 5/5 (新增 5)
- vue-tsc: **0 errors**
- ESLint: **0 errors / 0 warnings**
- ruff: Phase 118 files clean (I001 in `test_markdown_roundtrip.py` 是 Phase 117 遗留，未触碰)

---

## 1. 已完成 (本会话)

### 1.1 vis-network install regression 修复 + 文档化 (副产物)

**问题**: Phase 117 merge 在 `apps/dashboard/package.json` 加了 `vis-network@^10.1.2`，但**没跑过 `pnpm install`**。Fresh checkout 下 `apps/dashboard/node_modules/` 缺 vis-network，frontend test 全失败**：
```
Failed to resolve import "vis-network/standalone" from FactionGraphCanvas.vue
```

**修复**: `cd apps/dashboard && pnpm install` — populate node_modules. workspace root 的 `pnpm-lock.yaml` 本来就有 vis-network 条目，sub-workspace `node_modules/` 才是缺的。

**文档化**: `~/.claude/projects/.../memory/debugging.md` 新增条目 "world-page.spec.ts: Failed to resolve import vis-network/standalone"。**Lesson**: 加 frontend dep 后**必须** `pnpm install`，package.json + lockfile entry alone 不够。

### 1.2 Task #14 + #15 — DRY helpers + RevisionConflict base

**新增**: `infra/world_db/queries/_helpers.py`
- `now_iso() -> str` — ISO-8601 UTC timestamp
- `row_to_dict(row, json_fields=())` — 参数化 sqlite3.Row → dict，按 json_fields 解码 JSON 列
- `class RevisionConflict(Exception)` — 优化并发冲突基类

**迁移**: 6 个 query 文件 (`characters.py`, `factions.py`, `lore.py`, `timeline.py`, `proposals.py`, `relationships.py`) 移除本地 `_now()` + `_row_to_dict()`, 改为 import 自 `_helpers`。

**基类继承**: `CharacterRevisionConflict` / `LoreRevisionConflict` / `TimelineRevisionConflict` 现在 `class XxxRevisionConflict(RevisionConflict): ...`。`CHARACTER_REVISION_CONFLICT = CharacterRevisionConflict` alias 保留 (test 还在 import)。

**净效果**: 6 文件 -49 行。所有现有 19 backend tests PASS。

### 1.3 Task #16 — create_relationship deterministic id

**问题**: SQLite `INSERT OR IGNORE` 冲突时 `cur.lastrowid` 行为 implementation-defined — 可能 0、已存在 id、或 None。Python 3.13 + sqlite3 巧合下返回正确 id，但**不保证跨 driver 版本稳定**。

**修法**: 替换 `return cur.lastrowid` 为 follow-up SELECT on UNIQUE key。**防御性**: 加 `if row is None: raise RuntimeError(...)` 兜底 (理论上 INSERT OR IGNORE 不可能让 row 消失)。

**测试**: `test_create_relationship_idempotent_returns_same_id` — 同 data 调两次, assert 返回相同 id 且只 1 行。

### 1.4 Task #17 — LLM-backed agent extraction

**新增**: `infra/world_db/agent_schemas.py`
- `CharacterUpdatePayload` — Pydantic v2 schema, 字段匹配 `accept_proposal` 的 `character.update` 接口
- `ProposalResponse` — 单个 proposal 的完整 shape (kind / target_kind / target_id / payload / source / source_context / confidence)
- `ExtractionResult` — wrapper, 默认 `proposals=[]`
- `parse_proposals_json(raw)` — 接受 top-level array / wrapped `{proposals: []}` / markdown-fenced JSON

**重写**: `infra/world_db/agent_extractors.py`
- `extract_proposals_from_chapters(slug, chapter_texts, *, llm_service=None, max_chapters=10, max_tokens=4000, temperature=0.2) -> list[dict]`
- `extract_proposals_from_prompt(slug, user_prompt, *, llm_service=None, ...) -> list[dict]`
- 中文 system prompt 明确要求: 只输出有证据的变更, canon_level 限制枚举, confidence 必填
- **错误语义**: 解析 / 验证失败 → logger.warning + 返回 [] (不 raise, 调用方视为 no-op)
- **测试友好**: `llm_service` kwarg 注入 mock, 不打真 LLM
- Lazy import `infra.llm_service.LLMService` 避免 module load 时触发 API key 检查

**新 routes**: `apps/studio_api/routes/world.py`
- `POST /api/world/agent/extract-from-chapters` body: `{character_slug, chapter_texts}` → `{proposals_created, ids}`
- `POST /api/world/agent/extract-from-prompt` body: `{character_slug, prompt}` → 同上
- `_AgentRateLimiter` (module-level class): in-process counter, 5 calls/session, 第 6 次返回 HTTP 429

**Frontend 重写**: `apps/dashboard/src/composables/world/useWorldAgent.js`
- 替换 stub 为真实 `fetch('/api/world/agent/extract-from-chapters|prompt', {POST, JSON})`
- 返回 `{proposals_created, ids, message}` — 错误时返回 friendly message 而不抛 (调用方契约不变)

**Tests**:
- 11 new backend tests (extractor + schema)
- 5 new route tests (注册, happy path × 2, 400 验证, 429 rate limit)
- 5 new frontend tests (URL/body/headers/error paths)

---

## 2. 已知遗留 (Phase 119+ 候选)

### 优先级 1: UI 集成 (handoff §3 已有)

**A. LoreEditor / TimelineEditor 接入页面** (Phase 117 任务 #18/19 的输出)
- `apps/dashboard/src/components/world/lore/LoreEditor.vue` 是 standalone, 未被任何页面引用
- 同理 `apps/dashboard/src/components/world/timeline/TimelineEditor.vue`
- 需要: 在 `LoreDetail` + `TimelineEventDetail` 加 "编辑" toggle button, 类似 CharacterDetail → CharacterEditor 的 wiring pattern (Phase 117 Task 15)
- 估计: 1-2 小时

**B. chapterRange → chapterTexts 接线** (Phase 118 follow-up)
- 前端 `extractFromChapters(slug, chapterRange)` 的 `chapterRange = {start, end}` 当前**未被 resolve 成实际章节文本**
- 需要在 `WorldProposalInbox.vue` 加 wiring: 给定 start/end, 读项目里的章节文件 → 转成 list[str] → 传给 backend
- 这是 useWorldAgent 在 UI 路径里能真正被调用的前提

### 优先级 2: 防护 hardening

**C. Rate limiter per-IP / per-user scoping** (Phase 118 follow-up)
- 现行 `_AgentRateLimiter` 是 process-global counter (5 calls/session = per-process, 不是 per-client)
- 单进程多 tab 用同一个 user 会共享 quota, 多 user 共享一个 process quota
- 方案: 加 FastAPI dependency 取 `request.client.host` 作 key, 用 dict 计数
- 估计: 1 小时

**D. LLM provider 策略** (handoff §3 中长期 v15.3+)
- 决策: 选 minimax (优先) / anthropic / openai 哪个作为主要 provider
- 现有 `infra/llm_service.py` 已支持多 provider 自动 failover (minimax → anthropic → openai)
- 需要: 测试三个 provider 的实际响应质量, 决定主用 + 备用顺序
- prompt engineering: 当前 system prompt 是中文 editor 角色, 需要更多 prompt iteration

### 优先级 3: 其他 carryover (从 handoff 继承)

**E. Prod preview regression** (Phase 114 accepted debt, **不要尝试修复**)
- cytoscape-fcose CJS + rollup commonjs 不兼容, 5 phase 投入失败, dev baseline 仍 authoritative
- E2E Playwright runtime 阻塞 (handoff §6 "已知遗留")

---

## 3. 推荐优先级 (新会话)

**短期 (Phase 119)**:
1. **Task A** (LoreEditor/TimelineEditor 接入) — 1-2 小时, 立即可见收益
2. **Task B** (chapterRange → chapterTexts 接线) — 2-3 小时, 完成 useWorldAgent UI 路径
3. **Task C** (Rate limiter per-IP) — 1 小时, 防护 hardening

**短期 (清理)**:
4. Phase 117 遗留 ruff I001 in `test_markdown_roundtrip.py` (1 行, 顺手修)

**中长期 (v15.4+)**:
6. **Task D** (LLM provider 策略 + prompt engineering) — 用户策略决策
7. **Task E** (prod preview) — 不做 (accepted debt)

---

## 4. 用户策略 (重要)

### 已批准且有效 (继承自 Phase 117 handoff §4)

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

**4. 优先级源**
- `.lingwen/architecture.yml` 是 AI-readable 真源 (Phase 117 已更新加入 `world_db` 模块, Phase 118 无新模块)
- AGENTS.md 文字版 backup
- CLAUDE.md 是新会话入口 (仍是 v15.2, Phase 118 handoff 之后建议升级到 v15.3)

### 新会话应当遵守的项目约定 (Phase 118 强化)

**5. testid-class-sync 规则** (Phase 8.36, v15.0+)
- 每个 `data-testid="X"` 必须有 `class` 含 `X` 的 kebab-case token
- Phase 117 修复 13 个 ESLint warnings; Phase 118 没动 world/ components → 保持 0 warnings

**6. no-class-selector-in-test 规则** (Phase 8.31, v15.0+)
- 测试中禁止 `wrapper.find('.classname')`
- 用 `data-testid` 或 `wrapper.text()` 替代
- Phase 118 useWorldAgent test 无 component, 不受影响

**7. vi.hoisted() 限制** (v15.0+)
- hoisted callback 只能访问 `vi`, 不能访问 Vue/JS imports
- Vue `ref()` / `computed()` 必须在 top-level, hoisted 之外

**8. vite-auto-imported globals**
- 测试环境无自动导入, 需要在 `globalThis` 上 stub (Phase 118 useWorldAgent test 用 `globalThis.fetch = vi.fn()`)

**9. TDD per task** (per `superpowers:test-driven-development`)
- Write failing test → verify RED → implement → verify GREEN → commit
- Phase 118 实际做法: agent_extractors 11 个测试先写后跑 (但与实现同步, 没严格 RED), routes 5 个测试在实现后加 (GREEN 立即通过)

**10. Pydantic v2 模式** (Phase 118 加入)
- 项目用 pydantic v2, 用 `BaseModel` + `Field` + `field_validator`
- 已在 `apps/studio_api/models/*.py` 广泛使用
- Phase 118 复用同 pattern for `agent_schemas.py`

**11. Test injection for external services** (Phase 118 加入)
- 任何调用 LLM/外部 API 的模块都要支持 kwarg 注入 mock (避免测试打真 API)
- `extract_proposals_from_chapters(..., llm_service=None)` 默认走 `LLMService.get()`, 测试传 `FakeLLMService`
- 同样 pattern 应该用于其他外部依赖

---

## 5. 避免 (Don't Do)

继承自 Phase 117 handoff §5, 加上本会话发现:

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
- ❌ **不要 fix Phase 117 遗留 lint debt** (e.g. `test_markdown_roundtrip.py` I001) — Phase 118 commit 严格只改本 phase 范围
- ❌ **不要在 agent_extractors.py 顶层 import `infra.llm_service`** — 必须 lazy import, 避免 module load 时触发 API key check / provider plugin loading

---

## 6. 项目入口

| 任务 | 命令 |
|------|------|
| 前端测试 (world only) | `cd apps/dashboard && pnpm vitest run tests/unit/composables/use-world-agent.spec.js tests/unit/pages/world-page.spec.ts tests/unit/stores/useWorldStore.spec.js` |
| 前端测试 (全) | `cd apps/dashboard && pnpm vitest run` |
| 前端类型检查 | `cd apps/dashboard && pnpm tsc --noEmit` |
| 前端 lint | `cd apps/dashboard && pnpm eslint src/components/world src/pages/WorldPage.vue src/composables/world src/stores/useWorldStore.js` |
| 死代码检测 | `cd apps/dashboard && pnpm exec knip` |
| 构建 | `cd apps/dashboard && pnpm build` |
| Dev 启动 | `cd apps/dashboard && pnpm dev` |
| **后端测试 (Phase 118)** | `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/infra/world_db/ apps/studio_api/tests/test_world_route.py -v` |
| 后端测试 (全) | `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/ apps/studio_api/tests/ -v` |
| 后端 import 检查 | `/home/ailearn/miniconda3/bin/python -c "from apps.studio_api.routes.world import register_world; from infra.world_db.agent_extractors import extract_proposals_from_chapters"` |
| Ruff (Phase 118 files) | `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m ruff check infra/world_db/ apps/studio_api/routes/world.py apps/studio_api/tests/test_world_route.py` |
| **前端 install (fresh clone)** | `cd apps/dashboard && pnpm install` ← **必需**, 否则 world-page.spec.ts 全部失败 |

**注意**:
1. 后端必须用 `/home/ailearn/miniconda3/bin/python` (Python 3.13 + fastapi)。系统 `pytest` (Python 3.10) 缺 fastapi/sqlite3。
2. **Fresh checkout 必须 `pnpm install`** — 详 [[debugging#world-pagespects-failed-to-resolve-import-vis-networkstandalone]].

---

## 7. 关键文件指针

### Phase 118 新增

| 文件 | 用途 |
|------|------|
| `infra/world_db/queries/_helpers.py` | DRY helpers: `now_iso()` + `row_to_dict(row, json_fields)` + `RevisionConflict` |
| `infra/world_db/agent_schemas.py` | Pydantic v2: `CharacterUpdatePayload` + `ProposalResponse` + `ExtractionResult` + `parse_proposals_json()` |

### Phase 118 重写

| 文件 | 修改 |
|------|------|
| `infra/world_db/agent_extractors.py` | Stub → 真实 LLM 调用 (Chapter + Prompt 两条路) |
| `infra/world_db/queries/characters.py` | 移除本地 `_now` + `_row_to_dict`, import helpers |
| `infra/world_db/queries/factions.py` | 同上 |
| `infra/world_db/queries/lore.py` | 同上 + `LoreRevisionConflict(RevisionConflict)` |
| `infra/world_db/queries/timeline.py` | 同上 + `TimelineRevisionConflict(RevisionConflict)` |
| `infra/world_db/queries/proposals.py` | 同上 |
| `infra/world_db/queries/relationships.py` | 移除 `_now`, 加 follow-up SELECT 拿真实 id |
| `apps/studio_api/routes/world.py` | +2 routes (`agent_extract_from_chapters` / `agent_extract_from_prompt`) + `_AgentRateLimiter` |
| `apps/dashboard/src/composables/world/useWorldAgent.js` | Stub → 真实 fetch |

### 测试

| 文件 | 测试数 | 状态 |
|------|--------|------|
| `tests/infra/world_db/test_agent_extractors.py` | 11 (was 1) | Phase 118 |
| `tests/infra/world_db/test_other_queries.py` | 6 (was 5) | +1 idempotency |
| `apps/studio_api/tests/test_world_route.py` | 8 (was 3) | +5 agent routes |
| `apps/dashboard/tests/unit/composables/use-world-agent.spec.js` | 5 (new) | Phase 118 |
| **Phase 118 合计 new** | **21 tests** | |

### Spec + Handoff

| 文件 | 用途 |
|------|------|
| `docs/superpowers/specs/2026-08-26-phase-117-handoff.md` | Phase 117 v15.2 handoff (历史, superseded by 本 doc) |
| `docs/superpowers/specs/2026-08-26-phase-118-handoff.md` | **新会话入口** — 本文档 |
| `docs/superpowers/specs/2026-08-26-world-visualization-design.md` | Phase 117 v1 设计稿 |
| `docs/superpowers/plans/2026-08-26-world-visualization.md` | Phase 117 v1 实施计划 |

### 项目配置

| 文件 | 用途 |
|------|------|
| `CLAUDE.md` | 新会话入口 — v15.2, Phase 118 之后建议升 v15.3 |
| `AGENTS.md` | 5 条架构不变量 |
| `.lingwen/architecture.yml` | 模块边界 (Phase 117 加入 `world_db`, Phase 118 无变更) |
| `.lingwen/constraints.yml` | 9 个 A00X 反反模式 |

---

## 8. 历史背景

### 项目维护模式 (持续)

- v15.2 (Phase 117) World Visualization v1
- v15.3 (Phase 118, 本次) — DRY cleanup (#14/15) + bug fix (#16) + LLM agent (#17) **三件事一起闭环**
- 之前 50+ phases 都是 dashboard 工程 (perf / knip / ESLint / maintenance)
- Phase 117 第一次做产品侧添加 (23-task subagent-driven-development)
- Phase 118 第一次做**LLM 后端**集成 (Phase 117 是 UI-only v1)

### Phase 118 关键决策 (已闭环, 不要重审)

1. **LLM provider**: 复用现有 `infra/llm_service.py` 的多 provider failover (minimax → anthropic → openai), 不引入新依赖
2. **Schema 验证**: Pydantic v2 (项目已用), 不引入新依赖
3. **Rate limiter scope**: Phase 118 v1 选 process-global (简单, 5 calls/session 够用); per-IP 留 Phase 119
4. **chapterRange 处理**: 前端传 `chapter_texts`, 不在 backend resolve (路由层只接收 list[str])
5. **错误语义**: 解析/验证失败返回 `[]` 不 raise, 调用方视为 no-op extraction

### 已知技术约束 (新会话须知)

1. **vis-network bundle**: lazy-loaded, ~150kb gzipped, 只在 /world graph tab 激活时加载 (Phase 117)
2. **prod preview regression** (Phase 114): cytoscape-fcose CJS + rollup commonjs 不兼容, 5 phase 投入失败, dev baseline 仍 authoritative; E2E Playwright runtime 阻塞
3. **Python 环境**: 后端必须用 `/home/ailearn/miniconda3/bin/python` (Python 3.13), 系统 `pytest` (Python 3.10) 缺 fastapi/sqlite3
4. **CLAUDE.md v15.2**: 是当前会话入口, Phase 118 之后**应该升级到 v15.3** (新会话接手时如果时间允许, 顺手升)
5. **fresh install 需要 `pnpm install`**: Phase 117 merge 没跑 install 导致 regression, 详见 §5

---

## 9. 下次会话快速启动清单

新会话第一件事:

1. 读 `CLAUDE.md` (v15.2 或升级后 v15.3)
2. 读 `docs/superpowers/specs/2026-08-26-phase-117-handoff.md` (历史背景)
4. **读本文档** (Phase 118 状态)
3. 跑验收:
   ```bash
   # Fresh clone 或 vis-network 缺的情况下:
   cd apps/dashboard && pnpm install

   # 后端
   cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/infra/world_db/ apps/studio_api/tests/test_world_route.py -v
   # 前端 (world 部分)
   cd apps/dashboard && pnpm vitest run tests/unit/composables/use-world-agent.spec.js tests/unit/pages/world-page.spec.ts tests/unit/stores/useWorldStore.spec.js
   ```
5. 决定下一步: Task A/B/C (UI 集成 + rate limiter hardening) 或 Phase 119 (LLM provider 决策) 或 Task D (ruff Phase 117 清理)

---

## 10. 备忘 (本会话发现的可复用模式)

### LLM 集成模式 (新增)

- **Test injection via kwarg**: `extract_*(..., llm_service=None)` — mock pass-through, 避免测试打真 API
- **Lazy import for singleton-with-side-effects**: `infra.llm_service.LLMService.get()` 触发 API key 检查 + provider plugin 加载, 不能 module-level import
- **错误语义 = silent empty**: 解析失败返回 `[]` 不 raise, 调用方无需 try/except, UI 视为"没提案"
- **Cost guards 三层**: max_chapters (输入 cap) + max_tokens (输出 cap) + rate limit (per-process counter)

### Pydantic v2 schema 设计 (新增)

- **Top-level array + wrapped object 都接受**: LLM 输出不稳定, `parse_proposals_json()` 三种 shape 都接受
- **Markdown fence 剥离**: 复用 `LLMService.parse_json_response()` 风格的 ```json ... ``` 处理
- **Field validator for normalization**: `aliases` 字段 `_strip_aliases` validator 移除空字符串
- **exclude_none in model_dump**: 输出到 `create_proposal` 时不传 None 字段, 避免 JSON 里 `null`

### Rate limiter 设计 (新增)

- **Module-level class, instance in closure**: `_AgentRateLimiter` 在 module 顶层定义, `register_world` 里实例化作为 closure variable — 单元测试独立, 集成测试 per-app fresh state
- **HTTP 429 + friendly detail**: 不要 raise generic exception, 给前端 friendly message ("rate limit exceeded (5 calls per session)")

### Vitest mocking (继承自 memory/patterns.md)

- `globalThis.fetch = vi.fn()` 用于 stub 全局 fetch, beforeEach/afterEach 还原
- vi.hoisted 不能访问 Vue imports — `ref()` 必须 top-level
- composable 测试不需要 wrapper, 直接调函数

### ESLint / vue-tsc / ruff (本会话验证)

- vue-tsc 严格 type check, Pydantic-style dict 转换要明确 `dict[str, Any]` 类型
- ESLint 0 warnings 是 Phase 117 + 118 维护目标
- ruff --fix 处理 trailing newline (W292), 不要手动加
- 严格隔离: Phase 118 不修 Phase 117 遗留 lint (e.g. `test_markdown_roundtrip.py` I001), 留给未来独立 commit

### Bash session 教训 (新发现)

- bash session **不持久 cwd**, 每次 Bash tool call 默认 `/home/ailearn/projects/LingWen`, 即使之前用过 `cd apps/dashboard`
- 必须在**同一个 command 里**链 `cd ... && cmd`, 不能假设上次 cd 还在
- 调试时用 `pwd` 先确认 cwd 再跑命令

### 工程问题 (不属于本 phase)

- 232 个 ruff 错误 (历史, 本 phase 文件外) — 不修, 不影响 CI
- 38+ knip unused exports (历史) — 不修
- 15 个 pytest collection errors (历史, 引用不存在的模块) — 不修
- 1 个 Phase 117 I001 in `test_markdown_roundtrip.py` — 本 phase 不修, 留 Phase 119+ 清理

---

> **交接完成**。Phase 118 已合入 master (`37343188`), 新会话可从 Phase 119 (UI 集成 + rate limiter hardening) 或 v15.4 (LLM provider 决策) 启动。
> **CLAUDE.md 建议升级**: v15.2 → v15.3 (加入 Phase 118 段落)。如果时间允许, 新会话可以顺手做。
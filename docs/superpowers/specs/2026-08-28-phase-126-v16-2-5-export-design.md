# Phase 126 v16.2.5 — Export Subdomain 拆分 设计方案

> **状态**: ✅ 设计已批准,待 writing-plans
> **承接**:
> - `docs/superpowers/specs/2026-08-27-phase-126-v16-2-creator-subdomain-split-design.md` (母 spec, §2.1 export 子域定义 + §3.5 export 任务)
> - `docs/superpowers/plans/2026-08-27-phase-126-v16-2-creator-subdomain-split-plan.md` (§8 export 任务, renumbered to v16.2.5 per 实际执行顺序)
> - `docs/superpowers/handoffs/2026-08-28-phase-126-v16-2-4-content-handoff.md` (前置 sub-phase 闭环 + 5 lessons)
> **前置**:
> - v16.2.4 content 闭环 (`f01aaf2d`) — 8 content files 迁完 + shared/mode.py 抽取 + onboarding T4 closure
> - v16.2.3 onboarding 闭环 (`a82cc4de`) — 9 onboarding files 迁完
> - v16.2.2 settings 闭环 (`1fb9baed`) — 3 settings files 迁完
> - v16.2.1 volume 闭环 (`5733505b`) — 6 volume files 迁完
> - v16.2.0 shared 闭环 (`5bc35f1b`) — skeleton + shared/{revision,check,mode}.py
> **下一步**: v16.2.6 memory (3 files Round 2 leaf) + v16.2.7 cleanup (36 shims + typed wrapper `/api/` fix + import-linter)

---

## 0. TL;DR

**v16.2.5 = export subdomain 拆分**,8 commits / ~20 files / 0.5-1 天。

**Export 是 Phase 126 v16.2 creator 6-subdomain 拆分的 Round 2 leaf 第一个**,**依赖模式最简单**:
- **5 files** (export_common 92L + export_docx 111L + export_epub 181L + publish 90L + publish_adapters 159L) → `packages/lingwen-creator/src/lingwen_creator/export/`
- **跨 subdomain 依赖**:`export_common → creator_dashboard (content) + creator_settings_docs (settings)` — 已迁的子域,verbatim copy 时需改 intra-package import
- **无 shared extraction**:与 v16.2.4 不同 (mode logic 在 content/mode.py 不是 cross-subdomain utility)
- **无 forward-reference**:content + settings 已迁,v16.2.5 是真正 leaf
- **8 DTOs** 全部已在 `apps/studio_api/models/creator_settings.py` (5 top-level + 2 nested + 1 nested helper)
- **1 typed wrapper** (`apps/dashboard/src/api/export.ts`)+ 6 现有 legacy aliases in `api/index.js`
- **2 composables** refactor (useProductExport.ts + useProductPublish.ts) — 删 `api/publish.js` shim (raw fetch, 不 typed wrapper)

**关键决策**:
- **Verbatim copy 5 files**:与 v16.2.1..4 一致 pattern,shim re-export 保 4 consumer files 兼容
- **intra-package import**:verbatim copy 时把 `from infra.creator_dashboard import creator_chapter_preview` → `from lingwen_creator.content.dashboard import creator_chapter_preview` (per v16.2.4 lesson 1 + spec §12.2)
- **typed wrapper no zod / no /api/ prefix**:与 v16.2.1..4 严格一致
- **api/publish.js shim 删除**:Phase 62.4 legacy shim,已被 typed wrapper 完全替代,v16.2.5 T5 删
- **5 routes T4 migration**:epub / docx / publish / publish/platforms / publish/history — 全部在 `creator_core.py`

**8 commits** (T1-T7 + T8):
```
T1: 5 export files verbatim copy + 5 shims + test_export.py (8 files)
T2: 8 DTOs to lingwen-shared + TS codegen + tests (3 files)
T3: export.ts typed wrapper + re-export + URL contract (5 files)
T4: routes imports migration (1 file: creator_core.py)
T5: composable refactor + delete api/publish.js shim (3-4 files)
T6: cross-subdomain check + intra-package import fixup (1-3 files)
T7: fixups (test mock paths + ruff I001) (5-10 files)
T8: handoff + CLAUDE.md + architecture.yml/migration_log (4 files)
```

**总计 8 commits**,每 commit ≤4 files (DP-06 严格)。

---

## 1. 背景与动机

### 1.1 v16.2.5 解决的 carryover

| Carryover 来源 | 描述 | v16.2.5 修复方式 |
|---|---|---|
| (无新增 carryover) | export 是 leaf,无 forward-reference / spec violation / project_X import 遗留 | n/a |
| v16.2.5 自身 closing | 完成后 `infra/creator_export_*` + `infra/creator_publish*` 变 shim (5 个) | T1 + T6 + v16.2.7 cleanup |

**v16.2.5 单纯完成 Round 2 leaf 拆分**,无 inherited debt。复杂度低于 v16.2.4 (no shared extraction, no forward-reference close, no project_X import migration)。

### 1.2 Export subdomain scope

| 维度 | 数据 |
|---|---|
| Python files | 5 (export_common 92L + export_docx 111L + export_epub 181L + publish 90L + publish_adapters 159L) = 633 LOC |
| Routes | 5 endpoints (`/api/creator/export/{epub,docx}` POST + `/api/creator/publish` POST + `/api/creator/publish/{platforms,history}` GET) |
| Composables | 2 (useProductExport.ts + useProductPublish.ts) — 各自 3 个 raw fetch calls |
| DTOs | 8 (CreatorEpubExportRequest + CreatorDocxExportRequest + CreatorPublishRequest + CreatorPublishEntry + CreatorPublishPlatformsResponse + CreatorPublishHistoryResponse + CreatorPublishPlatform + CreatorPublishPlatformCapabilities) |
| Frontend wrapper | 6 legacy aliases in `api/index.js` (exportCreatorEpub + exportCreatorDocx + submitCreatorPublish + fetchCreatorPublishHistory + fetchCreatorPublishPlatforms + `api/publish.js` shim) |

### 1.3 为什么 v16.2.5 是最简 sub-phase

| 推力 | 后果 |
|---|---|
| **所有依赖子域已迁完** | export_common 依赖 creator_dashboard (content, v16.2.4) + creator_settings_docs (settings, v16.2.2)。两者都可直接 import 新路径,无 forward-reference |
| **publish_adapters 无依赖** | pure Python dataclass + Protocol + stub adapters,zero infra import |
| **publish (logging) 无依赖** | 只 import publish_adapters (intra-subdomain) + studio_registry |
| **无 shared extraction** | mode logic 不需抽 (不在 export),shared module 已稳定 |
| **小文件** | 5 files 总 633L,最大 epub 181L — 远小于 v16.2.4 agent.py 598L。T1 不需 split,1 commit 即可 |

---

## 2. 目标架构

### 2.1 Export subdomain 结构

```
packages/lingwen-creator/src/lingwen_creator/
├── shared/                       # v16.2.0 + v16.2.4 (unchanged)
│   ├── mode.py
│   ├── revision.py
│   └── check.py
├── content/                      # v16.2.4 (UPDATE: dashboard.py 提供 creator_chapter_preview 给 export)
├── settings/                     # v16.2.2 (UPDATE: docs.py 提供 creator_settings_docs_payload 给 export)
├── volume/                       # v16.2.1 (unchanged)
├── onboarding/                   # v16.2.3 (unchanged)
└── export/                       # v16.2.5 NEW
    ├── __init__.py               # star-imports from all 5 submodules
    ├── common.py                 # verbatim from infra/creator_export_common.py (92L)
    ├── docx.py                   # verbatim from infra/creator_export_docx.py (111L)
    ├── epub.py                   # verbatim from infra/creator_export_epub.py (181L)
    ├── publish.py                # verbatim from infra/creator_publish.py (90L)
    └── publish_adapters.py       # verbatim from infra/creator_publish_adapters.py (159L)
```

### 2.2 Intra-package imports (per spec §12.2)

Verbatim copy 后需改的 imports:

| File | 原 import | 改为 |
|---|---|---|
| `export/common.py:9` | `from infra.creator_dashboard import creator_chapter_preview` | `from lingwen_creator.content.dashboard import creator_chapter_preview` |
| `export/common.py:10` | `from infra.creator_settings_docs import creator_settings_docs_payload` | `from lingwen_creator.settings.docs import creator_settings_docs_payload` |
| `export/docx.py:9-15` | `from infra.creator_export_common import ...` + `from infra.creator_settings_docs import ...` | intra-subdomain: `from lingwen_creator.export.common import ...` + `from lingwen_creator.settings.docs import ...` |
| `export/epub.py:9-16` | 同 docx.py | 同 docx.py |
| `export/publish.py:10` | `from infra.creator_publish_adapters import ...` | intra-subdomain: `from lingwen_creator.export.publish_adapters import ...` |

**Pattern (per v16.2.4 §5.3 lesson 1)**: Intra-package import 走新 path 让 package 自包含,避免 shim 间接。`infra.creator_X` reserved for cross-boundary consumers (routes, scripts, etc.)。

### 2.3 Frontend Layout (新增)

```
apps/dashboard/src/api/
├── export.ts                       # v16.2.5 NEW (6 wrapper functions)
├── publish.js                      # T5 DELETED (legacy Phase 62.4 shim with raw fetch)
└── index.js                        # UPDATE: keep 6 legacy aliases pointing to export.ts

apps/dashboard/src/composables/
└── useCreatorProductTools/
    ├── useProductExport.ts         # UPDATE: 3 export calls → typed wrapper
    └── useProductPublish.ts        # UPDATE: 3 publish calls → typed wrapper
```

### 2.4 Per-Subdomain 依赖矩阵 (spec §2.4 update)

| Subdomain | 允许 import (v16.2.5) | 禁止 import |
|---|---|---|
| shared | (unchanged from v16.2.4) | (unchanged) |
| content | (unchanged) | (unchanged) |
| settings | (unchanged) | (unchanged) |
| volume | (unchanged) | (unchanged) |
| onboarding | (unchanged) | (unchanged) |
| export | `infra.paths`, `infra.project_config`, `infra.studio_registry`, **`lingwen_creator.content.dashboard` (NEW v16.2.5)**, **`lingwen_creator.settings.docs` (NEW v16.2.5)** | shared / volume / onboarding / memory |

**关键变更**:
- export → 增加 2 个跨子域依赖 (content.dashboard.creator_chapter_preview + settings.docs.creator_settings_docs_payload)。这些是 **真正跨子域** 调用,不是 forward-reference。
- 无 spec violation — export 不 import 其他子域的内部细节,只用其 public API。
- 无 shared extraction 需要 — mode logic 不在 export。

### 2.5 Routes 改造

`apps/studio_api/routes/creator_core.py` 5 export/publish endpoints (line 283-366):

```python
# Before (v16.2.4):
@ app.post("/api/creator/export/epub")
def creator_export_epub(req: CreatorEpubExportRequest) -> Response:
    from infra.creator_export_epub import build_creator_epub_bytes  # ← T4 migrate

@ app.post("/api/creator/export/docx")
def creator_export_docx(req: CreatorDocxExportRequest) -> Response:
    from infra.creator_export_docx import build_creator_docx_bytes  # ← T4 migrate

@ app.post("/api/creator/publish")
def creator_publish_submit(req: CreatorPublishRequest) -> CreatorPublishEntry:
    from infra.creator_publish import submit_creator_publish  # ← T4 migrate

@ app.get("/api/creator/publish/platforms")
def creator_publish_platforms() -> CreatorPublishPlatformsResponse:
    from infra.creator_publish import list_publish_platforms  # ← T4 migrate

@ app.get("/api/creator/publish/history")
def creator_publish_history(limit: int = 10) -> CreatorPublishHistoryResponse:
    from infra.creator_publish import list_creator_publish_history  # ← T4 migrate

# After (v16.2.5 T4):
from lingwen_creator.export.epub import build_creator_epub_bytes
from lingwen_creator.export.docx import build_creator_docx_bytes
from lingwen_creator.export.publish import (
    submit_creator_publish,
    list_publish_platforms,
    list_creator_publish_history,
)
```

**T4 scope**: 1 file, 5 lazy import migrations.

**注**: model imports (`from apps.studio_api.models.creator_settings import CreatorEpubExportRequest`) **不动** — DTO 在 T2 迁到 `lingwen_shared` 后,routes 仍可继续用本地 import (back-compat) 或切到 shared imports。**保守做法**: routes 用本地 import (test compat preserved),T2 + T4 完成后,DTO 在 shared + local models 两边都有,routes 暂不切 shared paths — 减少 T4 scope。**激进做法**: T4 同时切 DTO import 到 shared — 风险高 (refactor scope 膨胀)。**spec 决定**: 保守做法,T4 只改 function imports。

---

## 3. 迁移计划 (T1-T8)

### 3.1 T1: 5 export files verbatim copy + 5 shims + tests

**Files:**
- Create: `packages/lingwen-creator/src/lingwen_creator/export/{__init__.py,common.py,docx.py,epub.py,publish.py,publish_adapters.py}`
- Modify: 5 `infra/creator_export_*.py` + 2 `infra/creator_publish*.py` → 1-line shim
- Create: `packages/lingwen-creator/tests/test_export.py` (≥5 tests + legacy import path back-compat)

**T1.1**: 写 `test_export.py` failing test (RED):
```python
def test_export_package_imports(): ...  # import lingwen_creator.export
def test_common_module_exports(): ...  # export_metadata + load_export_chapters
def test_docx_module_exports(): ...  # build_creator_docx_bytes
def test_epub_module_exports(): ...  # build_creator_epub_bytes
def test_publish_module_exports(): ...  # submit_creator_publish + list_creator_publish_history
def test_publish_adapters_module_exports(): ...  # PublishAdapter + FanqiePublishAdapter + get_publish_adapter
def test_legacy_import_paths_still_work(): ...  # back-compat for 5 infra.creator_* imports
```

**T1.2**: 创建 `packages/lingwen-creator/src/lingwen_creator/export/` 6 files
- `__init__.py`: 5 star-imports (noqa: F403)
- `common.py`: verbatim from `infra/creator_export_common.py`,调整 2 个 infra imports (line 9-10 → lingwen_creator.content.dashboard + lingwen_creator.settings.docs per §2.2)
- `docx.py`: verbatim from `infra/creator_export_docx.py`,调整 2 个 infra imports (intra-subdomain: export.common + cross-subdomain: settings.docs)
- `epub.py`: verbatim from `infra/creator_export_epub.py`,同 docx.py
- `publish.py`: verbatim from `infra/creator_publish.py`,调整 1 个 infra import (intra-subdomain: export.publish_adapters)
- `publish_adapters.py`: verbatim from `infra/creator_publish_adapters.py`,**no infra import** (pure stdlib + infra.studio_registry which stays as is)

**T1.3**: 改 5 infra shim files → `from lingwen_creator.export.X import * # noqa: F403`

**T1.4**: 验证 GREEN: `pytest packages/lingwen-creator/tests/test_export.py -v` → ≥7 PASSED

**T1.5**: 验证 no regression: `pytest tests/ -q` → baseline + new tests PASS

**T1.6**: ruff check + commit (8 files total — within DP-06 ≤4 files? NO! Split needed)

**T1 split logic** (DP-06 enforcement):
- T1.a (4 files): `__init__.py + common.py + docx.py + epub.py + 2 shims (common + docx + epub)` = 7 files? 

Wait, let me count properly:
- T1.a (3 files in new pkg + 3 shims): `export/__init__.py + export/common.py + infra/creator_export_common.py (shim)` + `infra/creator_export_docx.py (shim)` + `infra/creator_export_epub.py (shim)` = 5 files (2 new + 3 shim)
- T1.b (3 files new + 2 shims): `export/docx.py + export/epub.py + infra/creator_export_docx.py shim → already done in T1.a? Wait, I confused myself.

Let me restart T1 split:
- **T1.a** (4 files): `export/__init__.py + export/common.py` + 2 shims (`infra/creator_export_common.py + infra/creator_publish_adapters.py`)
  - common.py: smallest (92L), no infra import migration needed beyond §2.2 (content.dashboard + settings.docs — both already exist)
  - publish_adapters.py: pure Python, no intra-package import, simplest migration
- **T1.b** (4 files): `export/docx.py + export/epub.py` + 2 shims (`infra/creator_export_docx.py + infra/creator_export_epub.py`)
  - docx.py + epub.py both depend on common.py (intra-subdomain import) — need T1.a's common.py to exist first
- **T1.c** (2 files): `export/publish.py + infra/creator_publish.py` (shim) + `test_export.py` = 3 files
  - publish.py depends on publish_adapters (intra-subdomain) — needs T1.a's publish_adapters.py

**Revised T1 = 3 sub-commits (T1.a, T1.b, T1.c)** with 4-5 files each, DP-06 ≤4 strict:
- T1.a (4 files): __init__.py + common.py + creator_export_common.py shim + creator_publish_adapters.py shim
- T1.b (4 files): docx.py + epub.py + creator_export_docx.py shim + creator_export_epub.py shim
- T1.c (3 files): publish.py + creator_publish.py shim + test_export.py

Actually, looking at v16.2.4 pattern (T2a-d split by semantic), the simpler approach is:
- T1.a (4 files): __init__.py + common.py + 1 shim + 1 test
- T1.b (4 files): docx.py + epub.py + 2 shims
- T1.c (3 files): publish.py + publish_adapters.py + 1 shim

Let me simplify: **T1 = 3 commits (T1.a, T1.b, T1.c)** by file-group semantic:
- T1.a: common + docx (the 2 files using export_metadata + creator_settings_docs_payload) + their shims (4 files: __init__.py + common.py + creator_export_common.py shim + creator_export_docx.py shim)
- T1.b: epub (181L, largest single file) + its shim + 1 test file (3 files)
- T1.c: publish + publish_adapters + their shims + 1 test file (4 files)

Hmm this is getting complex. Let me just say T1 = single commit with 11 files = **violation of DP-06**. So must split.

**Final T1 plan** (3 commits):
- **T1.a** (4 files): `export/__init__.py + export/common.py + infra/creator_export_common.py shim + infra/creator_export_docx.py shim` (shim create-only, no impl yet — common.py needed first, docx shim created in pre-emptive migration)

  Wait — we CAN'T create docx shim before docx.py exists (shim imports from lingwen_creator.export.docx). So docx shim must come AFTER docx.py.

  Alternative: **shim-first pattern** (per v16.2.3 handoff §5.1 lesson: shim is 1-line, can be created BEFORE impl)
  - shim points to lingwen_creator.export.docx (doesn't exist yet)
  - when docx.py created, shim "lights up" automatically
  - tests pass at end

  This is what v16.2.1..4 did — shim first, impl second. Let me apply this.

- **T1.a** (4 files): `infra/creator_export_common.py (shim) + infra/creator_export_docx.py (shim) + infra/creator_export_epub.py (shim) + infra/creator_publish_adapters.py (shim)` — all 4 shims first, pointing to non-existent modules. Tests will fail until T1.b/c/d land. **NO** — tests in test_export.py would fail with ImportError.

OK this is over-thinking. Let me look at v16.2.4's actual split:

From v16.2.4 handoff:
- T2a (4 files): agent + agent shim + batch_history + batch_history shim
- T2b (4 files): dashboard + dashboard shim + logic_check + logic_check shim  
- T2c (4 files): mode shim + mode shim (infra) + models + models shim
- T2d (4 files): preferences + preferences shim + ui_profile + ui_profile shim + __init__ + tests

So pattern is: pair impl + shim in each commit. 2 impls + 2 shims = 4 files per commit.

For export (5 files):
- T1.a (4 files): common + common shim + docx + docx shim (group 1)
- T1.b (4 files): epub + epub shim + publish + publish shim (group 2)
- T1.c (3 files): publish_adapters + publish_adapters shim + __init__.py (with 5 star-imports) + test_export.py = 4 files

Wait, publish_adapters.py has NO infra dependencies within creator_X (only infra.studio_registry), so it's safe to be in own commit.

Final T1 plan (3 commits):
- **T1.a** (4 files): `export/common.py + export/docx.py + infra/creator_export_common.py (shim) + infra/creator_export_docx.py (shim)`
  - common.py: 92L, simple, adjust 2 infra imports (intra-package to settings.docs + content.dashboard)
  - docx.py: 111L, depends on common.py (intra-subdomain) — needs T1.a's common.py to exist first, OK in same commit
- **T1.b** (4 files): `export/epub.py + export/publish.py + infra/creator_export_epub.py (shim) + infra/creator_publish.py (shim)`
  - epub.py: 181L, depends on common.py (intra-subdomain)
  - publish.py: 90L, depends on publish_adapters (intra-subdomain, but publish_adapters not yet migrated)
  - **PROBLEM**: publish.py imports from publish_adapters which still in infra. We have 2 options:
    1. T1.b: only epub.py (3 files: epub + shim + common adjustments)
    2. Move publish to T1.c with publish_adapters
- **T1.b** (3 files): `export/epub.py + infra/creator_export_epub.py (shim) + (intra-package import adjustment to common.py if needed)` 
- **T1.c** (4 files): `export/publish.py + export/publish_adapters.py + infra/creator_publish.py (shim) + infra/creator_publish_adapters.py (shim)`
- **T1.d** (4 files): `export/__init__.py (5 star-imports) + test_export.py + (knip allowlist if needed)`

So T1 = 4 commits. Let me re-plan:
- T1.a (4): common.py + docx.py + 2 shims
- T1.b (3): epub.py + 1 shim (common adjustments if any)
- T1.c (4): publish.py + publish_adapters.py + 2 shims
- T1.d (3): __init__.py + test_export.py + (optional ruff fixup)

Actually `__init__.py` star-imports + tests can be in T1.d, and T1.d also handles intra-package imports. So T1 = 4 commits totaling 14 files.

Hmm, that's a lot. Let me check v16.2.4 to see how they did it — they had 8 files in 4 commits (T2a-d, each 4 files).

For v16.2.5 export with 5 files (5 impls + 5 shims + 1 __init__ + 1 test = 12 files), 4 commits of 3-4 files each works:

- **T1.a** (4 files): common.py (impl) + docx.py (impl, depends on common) + creator_export_common.py shim + creator_export_docx.py shim
- **T1.b** (3 files): epub.py (impl, depends on common) + creator_export_epub.py shim + creator_publish_adapters.py shim (no infra deps, simple migration)
- **T1.c** (3 files): publish.py (impl, depends on publish_adapters) + creator_publish.py shim + __init__.py (5 star-imports + noqa: F403)
- **T1.d** (2 files): test_export.py + (optional ruff fixup)

Total: 4 commits, 12 files, all ≤4 per commit. ✓

### 3.2 T2: 8 DTOs to lingwen-shared + TS codegen + tests

**Files:**
- Modify: `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` (+8 DTOs)
- Auto-generated: `packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts`
- Modify: `packages/lingwen-shared/tests/test_creator_dto.py` (+8 DTO tests)

**DTO list** (from `apps/studio_api/models/creator_settings.py:113-192`):
1. `CreatorEpubExportRequest` (mode + start_chapter + end_chapter + title + author + description + submission_sample_count)
2. `CreatorDocxExportRequest` (same as Epub)
3. `CreatorPublishRequest` (platform + include_outline + intro + mode)
4. `CreatorPublishEntry` (id + platform + include_outline + intro + mode + status + message + created_at + adapter_id + connection + external_url + package_hint)
5. `CreatorPublishPlatformCapabilities` (nested: supports_submission_pack + supports_full_book + oauth_required + max_intro_chars)
6. `CreatorPublishPlatform` (nested: id + label + connection + capabilities)
7. `CreatorPublishPlatformsResponse` (slug + platforms: list[CreatorPublishPlatform])
8. `CreatorPublishHistoryResponse` (slug + entries: list[CreatorPublishEntry])

**T2.1**: Write 8 failing tests in `test_creator_dto.py`
**T2.2**: Add 8 Pydantic models to `creator.py` (Export + Publish sections)
**T2.3**: Run `tooling/contracts/generate.py` → `creator.ts` regenerated
**T2.4**: Run `tooling/contracts/zod_revalidate.py` → 0 drift
**T2.5**: Commit (3 files)

### 3.3 T3: export.ts typed wrapper + URL contract + knip allowlist

**Files:**
- Create: `apps/dashboard/src/api/export.ts` (6 wrapper functions)
- Create: `packages/dashboard-contracts/src/shared/export.ts` (re-export shim)
- Modify: `packages/dashboard-contracts/src/shared/creator.ts` (add export types to re-export list)
- Modify: `apps/dashboard/knip.json` (+2 allowlist entries)
- Create: `apps/dashboard/tests/unit/api-export-typed-wrapper.spec.ts` (≥6 URL contract tests)

**6 wrapper functions:**
```typescript
export async function exportCreatorEpub(body: CreatorEpubExportRequest): Promise<Blob>
export async function exportCreatorDocx(body: CreatorDocxExportRequest): Promise<Blob>
export async function submitCreatorPublish(body: CreatorPublishRequest): Promise<CreatorPublishEntry>
export async function fetchCreatorPublishHistory(limit?: number): Promise<CreatorPublishHistoryResponse>
export async function fetchCreatorPublishPlatforms(): Promise<CreatorPublishPlatformsResponse>
```

**Style** (per v16.2.1 lesson 4 + 5):
- NO zod runtime validation (zod is T5/CI drift, not wrapper layer)
- NO `/api/` prefix (BASE_URL 已是 `/api` from core.js)

**URL paths** (from creator_core.py routes):
- `POST /creator/export/epub`
- `POST /creator/export/docx`
- `POST /creator/publish`
- `GET /creator/publish/platforms`
- `GET /creator/publish/history?limit=N`

**Knip allowlist**: add `export.ts` + `export.ts (dashboard-contracts)` + update creator.ts re-export list

**Commit** (5 files): all in one, all ≤4? NO — 5 files > 4. Split:
- T3.a (4 files): export.ts + dashboard-contracts re-export + creator.ts re-export update + knip.json
- T3.b (1 file): api-export-typed-wrapper.spec.ts (URL contract)

### 3.4 T4: routes imports migration

**Files:**
- Modify: `apps/studio_api/routes/creator_core.py` (5 lazy imports)

**Scope**: 1 file, 5 line changes.

```python
# Lines 285, 311, 337, 351, 363 — change imports
from infra.creator_export_epub import build_creator_epub_bytes
# →
from lingwen_creator.export.epub import build_creator_epub_bytes

# Similarly for docx (line 311), publish (337), publish list_publish_platforms (351), 
# publish list_creator_publish_history (363)
```

**T4.1**: Update 5 lazy imports in creator_core.py
**T4.2**: Run pytest `tests/infra/test_creator_*.py` → no regression (shims provide back-compat)
**T4.3**: ruff check
**T4.4**: Commit (1 file)

### 3.5 T5: composable refactor + delete api/publish.js shim

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorProductTools/useProductExport.ts` (3 import changes)
- Modify: `apps/dashboard/src/composables/useCreatorProductTools/useProductPublish.ts` (3 import changes)
- Delete: `apps/dashboard/src/api/publish.js` (legacy Phase 62.4 shim)
- Modify: `apps/dashboard/src/api/index.js` (replace 5 publish.js imports + 6 legacy aliases)

**T5.1**: Refactor useProductExport.ts:
- Change `import { ... exportCreatorEpub, exportCreatorDocx, fetchCreatorChapterPreview } from '../../api/index.js'`
- To: `import { exportCreatorEpub, exportCreatorDocx } from '@/api/export'` + `import { fetchCreatorChapterPreview } from '@/api/content'` (fetchCreatorChapterPreview 已在 content.ts 中,per v16.2.4)

**T5.2**: Refactor useProductPublish.ts:
- Change `import { submitCreatorPublish, fetchCreatorPublishHistory, fetchCreatorPublishPlatforms } from '../../api/index.js'`
- To: `import { submitCreatorPublish, fetchCreatorPublishHistory, fetchCreatorPublishPlatforms } from '@/api/export'`

**T5.3**: Update api/index.js:
- Remove the `publish.js` re-export block
- Keep 6 legacy aliases (exportCreatorEpub, exportCreatorDocx, submitCreatorPublish, fetchCreatorPublishHistory, fetchCreatorPublishPlatforms) but point them to `@/api/export` instead of `./publish.js`

**T5.4**: Delete `apps/dashboard/src/api/publish.js`

**T5.5**: Run vitest → no regression (per v16.2.4 lesson 5: orphan test files linger after shim deletion — must `grep -r "api/publish" apps/dashboard/tests/` BEFORE deletion)

**T5.6**: Commit (4 files modified/deleted)

### 3.6 T6: cross-subdomain check + intra-package imports

**Files:**
- Modify: 1-3 files (depending on grep findings)

**T6.1**: `grep -rln "infra.creator_export\|infra.creator_publish" apps/ packages/ --include="*.py"` to find any remaining consumer outside routes

**Expected findings**: 
- routes already migrated in T4
- export module itself uses intra-package imports (handled in T1)
- nothing else (5 export files are pure backend helpers, no other consumers)

**T6.2**: If findings: update those files
**T6.3**: ruff check
**T6.4**: Commit

### 3.7 T7: fixups (test mock paths + ruff I001)

**Per v16.2.4 lessons 2 + 5** (will be discovered during verification):

**T7.1**: grep `patch.*infra.creator_export\|patch.*infra.creator_publish` in apps/dashboard/tests/ — likely 0 (publish.js uses raw fetch, not mocked functions)

**T7.2**: Run ruff `--fix` on new files (likely 0 I001 violations if intra-package imports are clean from T1)

**T7.3**: Run all verification gates:
- pytest: 6+ (packages/lingwen-creator/tests/test_export.py + packages/lingwen-shared/tests/test_creator_dto.py Export/Publish tests) + baseline
- vitest: 1778+ (URL contract test adds 6) + baseline
- vue-tsc: 0 errors
- knip: 0 errors (5 unrelated hints)
- ruff: 0 errors
- zod reverse: 0 drift
- codegen: OK

**T7.4**: Commit fixups

### 3.8 T8: handoff + CLAUDE.md + architecture.yml + migration_log

**Files:**
- Create: `docs/superpowers/handoffs/2026-08-28-phase-126-v16-2-5-export-handoff.md`
- Modify: `CLAUDE.md` (bump v16.2.4 → v16.2.5)
- Modify: `.lingwen/architecture.yml` (add export module exports)
- Modify: `.lingwen/migration_log.yml` (v16.2.5 entry)

**T8.1**: Write handoff doc (10 sections per v16.2.4 template)
**T8.2**: Update CLAUDE.md v16.2.5 entry
**T8.3**: Update architecture.yml export module_boundaries
**T8.4**: Update migration_log.yml
**T8.5**: Final verification (all gates)
**T8.6**: Commit (4 files)

---

## 4. DTOs 设计

### 4.1 8 DTOs 详细 schema

```python
# CreatorEpubExportRequest — POST /api/creator/export/epub
class CreatorEpubExportRequest(BaseModel):
    mode: str = "full"  # "full" | "range" | "submission"
    start_chapter: Optional[int] = None
    end_chapter: Optional[int] = None
    title: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    submission_sample_count: Optional[int] = 3

# CreatorDocxExportRequest — POST /api/creator/export/docx
# (same as CreatorEpubExportRequest — duplicated for clarity, both used in routes)

# CreatorPublishRequest — POST /api/creator/publish
class CreatorPublishRequest(BaseModel):
    platform: str  # "fanqie" | "qidian" | "jjwxc" | "custom"
    include_outline: bool = True
    intro: str = ""
    mode: str = "submission"

# CreatorPublishEntry — return type of POST /api/creator/publish + items in history
class CreatorPublishEntry(BaseModel):
    id: str
    platform: str
    include_outline: bool
    intro: str = ""
    mode: str
    status: str
    message: str
    created_at: str
    adapter_id: Optional[str] = None
    connection: Optional[str] = None
    external_url: Optional[str] = None
    package_hint: Optional[str] = None

# CreatorPublishPlatformCapabilities — nested helper
class CreatorPublishPlatformCapabilities(BaseModel):
    supports_submission_pack: bool = True
    supports_full_book: bool = False
    oauth_required: bool = True
    max_intro_chars: int = 2000

# CreatorPublishPlatform — nested helper
class CreatorPublishPlatform(BaseModel):
    id: str
    label: str
    connection: str
    capabilities: CreatorPublishPlatformCapabilities

# CreatorPublishPlatformsResponse — GET /api/creator/publish/platforms
class CreatorPublishPlatformsResponse(BaseModel):
    slug: str
    platforms: list[CreatorPublishPlatform]

# CreatorPublishHistoryResponse — GET /api/creator/publish/history
class CreatorPublishHistoryResponse(BaseModel):
    slug: str
    entries: list[CreatorPublishEntry]
```

### 4.2 Optional: CreatorPublishMode enum?

Currently `mode` is `str` literal. **Q5 decision**: keep as str (matches existing route + LLM-style "loose typing"). Do not over-engineer with Enum.

### 4.3 Optional: CreatorPublishAdapterId enum?

Same — keep as str. Platform validation done in `creator_publish.py:_VALID_PLATFORMS = frozenset({"fanqie", "qidian", "jjwxc", "custom"})`.

---

## 5. Lessons (从 v16.2.1..4 沿用)

### 5.1 v16.2.5 应用 lessons

1. **Intra-package imports after verbatim copy** (v16.2.4 §5.1 lesson 1): export_common imports creator_dashboard + creator_settings_docs — verbatim copy 必须改为 `from lingwen_creator.content.dashboard import ...` + `from lingwen_creator.settings.docs import ...`。Failure mode: import cycle via shim (per v16.2.4 verification T8 fixup A)。

2. **Shim mocks don't propagate** (v16.2.4 §5.1 lesson 2): publish.js uses raw fetch, not mocked functions — tests likely don't patch infra.creator_publish.* directly. Low risk but must grep before T5 shim deletion。

3. **Typed wrapper params forwarding** (v16.2.4 §5.1 lesson 4): `exportCreatorEpub/Docx` return Blob — verify body is forwarded correctly。已有 precedent in content.ts。

4. **Orphan test files linger after shim deletion** (v16.2.4 §5.1 lesson 5): publish.js is in apps/dashboard/src/api/, not in tests/. But `api/index.js` has 6 legacy aliases pointing to publish.js — T5 must update index.js to point to export.ts before deleting publish.js.

5. **DP-06 commit-level**: T1 with 11 files (5 impl + 5 shim + 1 __init__) MUST split. v16.2.4 T2a-d split pattern (pair impl+shim per commit) is the precedent。

### 5.2 v16.2.1..4 lessons 沿用 (确认有效)

- T1 verbatim copy + intra-package import adjustments (5.1 lesson 1 from v16.2.4) — applied in T1.a
- shim private name re-exports for test compat (5.1 lesson 3 from v16.2.1) — N/A (no private symbols used in export)
- typed wrapper 无 zod (5.1 lesson 4 from v16.2.1) — T3 严格遵循
- `/api/` prefix 不 in code (5.1 lesson 5 from v16.2.1) — T3 严格遵循
- hyphen name + underscore module, ruff `# noqa: F403` inline, knip allowlist, verbatim copy integrity

---

## 6. 验证门

### 6.1 v16.2.5 验证 gates

| Gate | 命令 | 期望 |
|---|---|---|
| Backend tests | `pytest tests/ packages/lingwen-creator/tests/ packages/lingwen-shared/tests/ -q` | baseline + ≥6 export + ≥8 DTO |
| Frontend tests | `pnpm vitest run --reporter=dot` | 1778 + ≥6 URL contract |
| vue-tsc | `pnpm exec vue-tsc --noEmit` | 0 errors |
| knip | `pnpm exec knip` | 0 errors (allowlist updated) |
| ruff | `ruff check .` | 0 errors |
| codegen | `uv run python tooling/contracts/generate.py` | creator.ts regenerated (+8 types) |
| zod reverse | `uv run python tooling/contracts/zod_revalidate.py` | 0 drift |

### 6.2 v16.2.5 final state

```bash
$ ls packages/lingwen-creator/src/lingwen_creator/export/*.py | wc -l
6  # 5 modules + __init__.py

$ grep -cE "infra\.creator_export|infra\.creator_publish" apps/studio_api/routes/creator_core.py
0  # T4 migrated

$ ls infra/creator_export_*.py infra/creator_publish*.py | wc -l
5  # shims (still exist, v16.2.7 will delete)

$ grep -cE "infra\.creator_export|infra\.creator_publish" apps/ packages/ --include="*.py" -r | grep -v "^0:" | wc -l
0  # no remaining infra imports (except shims themselves)
```

---

## 7. Carryover to v16.2.6+ / v16.2.7

| 任务 | 阶段 | 来源 |
|---|---|---|
| **v16.2.6 memory** | 3 files (annotations + assets + query) — Round 2 leaf | per plan §7 |
| **v16.2.7 cleanup** | 36 shim deletions + 4 typed wrapper `/api/` prefix fix (world/workspace/quality + onboarding from v16.2.3) + 22 vitest debt + import-linter DP-01..06 | per plan §9 |
| **api/publish.js shim** | ✅ DELETED in T5 — no carryover | resolved |
| **`api/index.js` 6 legacy aliases** | ✅ Updated in T5 to point to @/api/export | resolved (delete in v16.2.7 with shim sweep) |
| **3 export consumer files** | ✅ All migrated (routes in T4 + composables in T5) | resolved |
| **Pre-existing vitest debt** | 22 v16.2.1 `useCreatorVolumePlan*.spec.ts` failures — unchanged | v16.2.7 cleanup |
| **intra-package imports** | ✅ All adjusted in T1.a/b/c (per v16.2.4 lesson 1) | resolved |
| **Typed wrapper defects** | Will be fixed in T3 if discovered (per v16.2.4 lesson 4) | TBD during execution |

---

**Spec complete and saved to `docs/superpowers/specs/2026-08-28-phase-126-v16-2-5-export-design.md`.**

**Next step**: writing-plans skill to convert spec → task-by-task plan with DP-06 ≤4 files/commit splits.

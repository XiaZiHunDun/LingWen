# Phase 126 v16.2.5 — Export Subdomain 拆分 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 5 个 `infra/creator_export_*.py` + 2 个 `infra/creator_publish*.py` 按 DDD bounded context 拆到 `packages/lingwen-creator/src/lingwen_creator/export/`,加 typed wrapper + 2 composables 切换 + 5 routes migration。Round 2 leaf,无 shared extraction,无 forward-reference closure。

**Architecture:** Strangler Fig migration v16.2.5 single sub-phase,8 commits(每 commit ≤4 files,DP-06 严格),shim re-export 保 4 consumer files 兼容。Export 依赖 content.dashboard + settings.docs (都已迁,直接 intra-package import 走新 path)。

**Tech Stack:** Python 3.12+ / Pydantic v2 / uv workspaces / FastAPI / Pydantic → TS hand-rolled codegen / Vue 3 + Pinia + TypeScript strict / Vitest / pytest / ruff / vue-tsc / knip / zod (reverse validation CI)

**Spec:** [`docs/superpowers/specs/2026-08-28-phase-126-v16-2-5-export-design.md`](../specs/2026-08-28-phase-126-v16-2-5-export-design.md) (用户已批准 2026-08-28)

---

## 0. Pre-flight 检查 (Phase 开始前必过)

| 检查 | 命令 | 期望 |
|---|---|---|
| uv workspace 健康 | `uv sync` | 0 errors |
| v16.2.4 baseline tests | `pytest tests/ packages/lingwen-creator/tests/ packages/lingwen-shared/tests/ -q` | 370+ passing |
| Frontend baseline | `pnpm vitest run --reporter=dot` | 1778 passed |
| Type check | `pnpm exec vue-tsc --noEmit` | 0 errors |
| Lint | `ruff check .` | 0 |
| Dead code | `pnpm exec knip` | 0 (5 advisory hints) |
| zod reverse | `uv run python tooling/contracts/zod_revalidate.py` | 0 drift |
| master HEAD | `git log --oneline -1` | `f01aaf2d docs(phase-126): v16.2.4 handoff` |
| working tree clean | `git status` | nothing to commit |

**任何一项不通过就不开 v16.2.5**。

---

## 1. Sub-phase 概览

| Task | 范围 | Files | Commit |
|---|---|---|---|
| **T1.a** | export/common.py + export/docx.py + 2 shims | 4 | 1 |
| **T1.b** | export/epub.py + shim + creator_publish_adapters.py shim | 3 | 2 |
| **T1.c** | export/publish.py + export/publish_adapters.py + 1 shim + __init__.py | 4 | 3 |
| **T1.d** | test_export.py + (intra-package import adjustments) | 2 | 4 |
| **T2** | 8 DTOs to creator.py + test_creator_dto.py + TS codegen | 3 | 5 |
| **T3.a** | export.ts typed wrapper + re-export + knip allowlist | 4 | 6 |
| **T3.b** | api-export-typed-wrapper.spec.ts (URL contract) | 1 | 7 |
| **T4** | routes imports migration (creator_core.py 5 lazy imports) | 1 | 8 |
| **T5.a** | composable refactor (useProductExport.ts + useProductPublish.ts) | 2 | 9 |
| **T5.b** | api/index.js update + delete api/publish.js | 2 | 10 |
| **T6** | cross-subdomain check (likely skip — only routes consumers) | 1-3 | 11 |
| **T7** | fixups (test mocks + ruff I001, likely 0-2 fixups) | 2-5 | 12-13 |
| **T8** | handoff + CLAUDE.md + architecture.yml + migration_log | 4 | 14 |
| **总计** | — | ~30 files | **~12 commits** |

**Note**: v16.2.5 比 v16.2.4 简单 — Round 2 leaf,无 shared extraction,无 forward-reference closure,无 project_X import migration,无 T8 fixup A 类缺陷 (intra-package import 已在 T1 处理)。预计 12-14 commits 完成。

---

## 2. T1.a — common.py + docx.py + 2 shims

**Files:**
- Create: `packages/lingwen-creator/src/lingwen_creator/export/common.py` (verbatim from `infra/creator_export_common.py`, 92L)
- Create: `packages/lingwen-creator/src/lingwen_creator/export/docx.py` (verbatim from `infra/creator_export_docx.py`, 111L)
- Modify: `infra/creator_export_common.py` → 1-line shim
- Modify: `infra/creator_export_docx.py` → 1-line shim

**Steps:**

- [ ] **Step 1: 读 `infra/creator_export_common.py` 当前内容**

读 `infra/creator_export_common.py` (92 lines per spec §2.2),完整复制粘贴到 `packages/lingwen-creator/src/lingwen_creator/export/common.py`,**调整 line 9-10 imports** (intra-package per §2.2):
  ```python
  # Before (verbatim from infra/creator_export_common.py):
  from infra.creator_dashboard import creator_chapter_preview
  from infra.creator_settings_docs import creator_settings_docs_payload
  
  # After (intra-package):
  from lingwen_creator.content.dashboard import creator_chapter_preview
  from lingwen_creator.settings.docs import creator_settings_docs_payload
  ```

- [ ] **Step 2: 读 `infra/creator_export_docx.py` 当前内容**

读 `infra/creator_export_docx.py` (111 lines per spec §2.2),完整复制粘贴到 `packages/lingwen-creator/src/lingwen_creator/export/docx.py`,**调整 line 9-15 imports** (intra-package + cross-subdomain):
  ```python
  # Before (verbatim from infra/creator_export_docx.py):
  from infra.creator_export_common import (
      export_metadata,
      load_export_chapters,
      resolve_export_chapter_nums,
      split_paragraphs,
  )
  from infra.creator_settings_docs import creator_settings_docs_payload
  
  # After:
  from lingwen_creator.export.common import (
      export_metadata,
      load_export_chapters,
      resolve_export_chapter_nums,
      split_paragraphs,
  )
  from lingwen_creator.settings.docs import creator_settings_docs_payload
  ```

- [ ] **Step 3: 把 `infra/creator_export_common.py` 改为 shim**

完全替换 `infra/creator_export_common.py` 内容为:
```python
"""Phase 126 v16.2.5 shim: re-export from lingwen_creator.export.common.

Migrated to packages/lingwen-creator/src/lingwen_creator/export/common.py.
This shim maintains backwards compat for consumers using:
    from infra.creator_export_common import export_metadata, load_export_chapters, ...

Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.export.common import *  # noqa: F403
```

- [ ] **Step 4: 把 `infra/creator_export_docx.py` 改为 shim**

完全替换为:
```python
"""Phase 126 v16.2.5 shim: re-export from lingwen_creator.export.docx.

Migrated to packages/lingwen-creator/src/lingwen_creator/export/docx.py.
This shim maintains backwards compat for consumers using:
    from infra.creator_export_docx import build_creator_docx_bytes, ...

Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.export.docx import *  # noqa: F403
```

- [ ] **Step 5: 验证 T1.a 范围内所有 import 解析 OK**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -c "from lingwen_creator.export.common import export_metadata, load_export_chapters, resolve_export_chapter_nums, split_paragraphs, written_chapter_nums, utc_modified_iso; print('common OK')"
/home/ailearn/miniconda3/bin/python -c "from lingwen_creator.export.docx import build_creator_docx_bytes; print('docx OK')"
/home/ailearn/miniconda3/bin/python -c "from infra.creator_export_common import export_metadata; print('shim common OK')"
/home/ailearn/miniconda3/bin/python -c "from infra.creator_export_docx import build_creator_docx_bytes; print('shim docx OK')"
```

Expected: 4 OK (no ImportError)。

- [ ] **Step 6: ruff check**

```bash
cd /home/ailearn/projects/LingWen
ruff check packages/lingwen-creator/src/lingwen_creator/export/ infra/creator_export_common.py infra/creator_export_docx.py 2>&1 | tail -3
```

Expected: `All checks passed!` (shim files have inline `# noqa: F403`)

- [ ] **Step 7: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-creator/src/lingwen_creator/export/common.py packages/lingwen-creator/src/lingwen_creator/export/docx.py infra/creator_export_common.py infra/creator_export_docx.py
git commit -m "feat(creator): Phase 126 v16.2.5 T1.a — export/common + export/docx migration

迁移 infra/creator_export_common.py + infra/creator_export_docx.py 到 packages/lingwen-creator/src/lingwen_creator/export/。

迁移内容:
- export/common.py — export_metadata + written_chapter_nums + resolve_export_chapter_nums + load_export_chapters + split_paragraphs + utc_modified_iso
- export/docx.py — build_creator_docx_bytes

Intra-package imports 调整 (per spec §2.2 + v16.2.4 §5.1 lesson 1):
- infra.creator_dashboard.creator_chapter_preview → lingwen_creator.content.dashboard.creator_chapter_preview
- infra.creator_settings_docs.creator_settings_docs_payload → lingwen_creator.settings.docs.creator_settings_docs_payload
- infra.creator_export_common.* → lingwen_creator.export.common.* (intra-subdomain)

Shim pattern (2 shim files):
- infra/creator_export_common.py 变 1-line re-export
- infra/creator_export_docx.py 同

Lessons applied:
- v16.2.4: intra-package imports after verbatim copy (避免 shim cycle)

后续 T1.b: epub + publish_adapters + 1 shim。"
```

---

## 3. T1.b — epub.py + shim + creator_publish_adapters.py shim

**Files:**
- Create: `packages/lingwen-creator/src/lingwen_creator/export/epub.py` (verbatim from `infra/creator_export_epub.py`, 181L)
- Modify: `infra/creator_export_epub.py` → 1-line shim
- Modify: `infra/creator_publish_adapters.py` → 1-line shim (pre-emptive — file doesn't exist yet in new package, but shim points to it for T1.c)

**Steps:**

- [ ] **Step 1: 读 `infra/creator_export_epub.py` 当前内容**

读 181 lines,完整复制粘贴到 `packages/lingwen-creator/src/lingwen_creator/export/epub.py`,**调整 line 9-16 imports**:
  ```python
  # Before:
  from infra.creator_export_common import (
      export_metadata,
      load_export_chapters,
      resolve_export_chapter_nums,
      split_paragraphs,
      utc_modified_iso,
  )
  from infra.creator_settings_docs import creator_settings_docs_payload
  
  # After:
  from lingwen_creator.export.common import (
      export_metadata,
      load_export_chapters,
      resolve_export_chapter_nums,
      split_paragraphs,
      utc_modified_iso,
  )
  from lingwen_creator.settings.docs import creator_settings_docs_payload
  ```

- [ ] **Step 2: 把 `infra/creator_export_epub.py` 改为 shim**

完全替换为:
```python
"""Phase 126 v16.2.5 shim: re-export from lingwen_creator.export.epub.

Migrated to packages/lingwen-creator/src/lingwen_creator/export/epub.py.
This shim maintains backwards compat for consumers using:
    from infra.creator_export_epub import build_creator_epub_bytes, ...

Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.export.epub import *  # noqa: F403
```

- [ ] **Step 3: 把 `infra/creator_publish_adapters.py` 改为 shim**

完全替换为:
```python
"""Phase 126 v16.2.5 shim: re-export from lingwen_creator.export.publish_adapters.

Migrated to packages/lingwen-creator/src/lingwen_creator/export/publish_adapters.py.
This shim maintains backwards compat for consumers using:
    from infra.creator_publish_adapters import (
        PublishAdapter, PublishCapabilities, PublishSubmitResult,
        FanqiePublishAdapter, QidianPublishAdapter, JjwxcPublishAdapter, CustomPublishAdapter,
        get_publish_adapter, list_publish_platforms,
    )

Shim will be deleted in v16.2.7 final cleanup.

NOTE: publish_adapters.py is pure Python (zero infra.creator_X imports).
The actual migration to lingwen_creator.export.publish_adapters.py happens in T1.c.
This shim is created early so it can be referenced from the migrated publish.py in T1.c.
"""
from lingwen_creator.export.publish_adapters import *  # noqa: F403
```

- [ ] **Step 4: 验证 T1.b 范围 + shim pre-emptive**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -c "from lingwen_creator.export.epub import build_creator_epub_bytes; print('epub OK')"
/home/ailearn/miniconda3/bin/python -c "from infra.creator_export_epub import build_creator_epub_bytes; print('shim epub OK')"
```

Expected: 2 OK (epub OK + shim epub OK)
Note: creator_publish_adapters shim **WILL FAIL** until T1.c creates publish_adapters.py. That's expected — verify in T1.c.

- [ ] **Step 5: ruff check**

```bash
cd /home/ailearn/projects/LingWen
ruff check packages/lingwen-creator/src/lingwen_creator/export/epub.py infra/creator_export_epub.py infra/creator_publish_adapters.py 2>&1 | tail -3
```

Expected: `All checks passed!`

- [ ] **Step 6: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-creator/src/lingwen_creator/export/epub.py infra/creator_export_epub.py infra/creator_publish_adapters.py
git commit -m "feat(creator): Phase 126 v16.2.5 T1.b — export/epub + creator_publish_adapters shim

迁移 infra/creator_export_epub.py 到 packages/lingwen-creator/src/lingwen_creator/export/。

迁移内容:
- export/epub.py — build_creator_epub_bytes (EPUB 3 zip output)

Intra-package imports 调整 (per spec §2.2):
- infra.creator_export_common.* → lingwen_creator.export.common.* (intra-subdomain)
- infra.creator_settings_docs.* → lingwen_creator.settings.docs.* (cross-subdomain)

Shim pattern (2 shim files):
- infra/creator_export_epub.py → 1-line re-export
- infra/creator_publish_adapters.py → 1-line re-export (pre-emptive, lights up in T1.c)

后续 T1.c: publish.py + publish_adapters.py + 1 shim + __init__.py。"
```

---

## 4. T1.c — publish.py + publish_adapters.py + 1 shim + __init__.py

**Files:**
- Create: `packages/lingwen-creator/src/lingwen_creator/export/publish.py` (verbatim from `infra/creator_publish.py`, 90L)
- Create: `packages/lingwen-creator/src/lingwen_creator/export/publish_adapters.py` (verbatim from `infra/creator_publish_adapters.py`, 159L)
- Modify: `infra/creator_publish.py` → 1-line shim
- Create: `packages/lingwen-creator/src/lingwen_creator/export/__init__.py` (5 star-imports)

**Steps:**

- [ ] **Step 1: 读 `infra/creator_publish_adapters.py` 当前内容**

读 159 lines,完整复制粘贴到 `packages/lingwen-creator/src/lingwen_creator/export/publish_adapters.py`,**no infra.creator_X imports** — pure Python (only `from infra.studio_registry import StudioProject` which stays as is, NOT a creator_X import)。

- [ ] **Step 2: 读 `infra/creator_publish.py` 当前内容**

读 90 lines,完整复制粘贴到 `packages/lingwen-creator/src/lingwen_creator/export/publish.py`,**调整 line 10 import** (intra-subdomain):
  ```python
  # Before:
  from infra.creator_publish_adapters import get_publish_adapter, list_publish_platforms
  
  # After:
  from lingwen_creator.export.publish_adapters import (
      get_publish_adapter,
      list_publish_platforms,
  )
  ```

- [ ] **Step 3: 把 `infra/creator_publish.py` 改为 shim**

完全替换为:
```python
"""Phase 126 v16.2.5 shim: re-export from lingwen_creator.export.publish.

Migrated to packages/lingwen-creator/src/lingwen_creator/export/publish.py.
This shim maintains backwards compat for consumers using:
    from infra.creator_publish import submit_creator_publish, list_creator_publish_history, ...

Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.export.publish import *  # noqa: F403
```

- [ ] **Step 4: 创建 `packages/lingwen-creator/src/lingwen_creator/export/__init__.py`**

```python
"""Phase 126 v16.2.5: export/ subdomain (creator DOCX/EPUB/Publish).

Bounded context: chapter assembly + DOCX/EPUB packaging + publish platform adapters.
Migrated from infra/creator_export_*.py + infra/creator_publish*.py.

Architecture:
- common: shared helpers (export_metadata, resolve_export_chapter_nums, load_export_chapters, split_paragraphs, utc_modified_iso)
- docx: DOCX builder (stdlib zip only)
- epub: EPUB 3 builder (stdlib zip only)
- publish: publish job log + adapter dispatch
- publish_adapters: PublishAdapter Protocol + 4 platform stubs (fanqie/qidian/jjwxc/custom)
"""
from lingwen_creator.export.common import *  # noqa: F403
from lingwen_creator.export.docx import *  # noqa: F403
from lingwen_creator.export.epub import *  # noqa: F403
from lingwen_creator.export.publish import *  # noqa: F403
from lingwen_creator.export.publish_adapters import *  # noqa: F403
```

- [ ] **Step 5: 验证 T1.c + 完整 export package**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -c "import lingwen_creator.export; print('package OK')"
/home/ailearn/miniconda3/bin/python -c "from lingwen_creator.export import export_metadata, build_creator_docx_bytes, build_creator_epub_bytes, submit_creator_publish, list_creator_publish_history, list_publish_platforms, get_publish_adapter, FanqiePublishAdapter; print('all exports OK')"
/home/ailearn/miniconda3/bin/python -c "from infra.creator_publish_adapters import get_publish_adapter; print('shim publish_adapters OK')"
/home/ailearn/miniconda3/bin/python -c "from infra.creator_publish import submit_creator_publish; print('shim publish OK')"
```

Expected: 4 OK

- [ ] **Step 6: ruff check**

```bash
cd /home/ailearn/projects/LingWen
ruff check packages/lingwen-creator/src/lingwen_creator/export/ infra/creator_publish.py infra/creator_publish_adapters.py 2>&1 | tail -3
```

Expected: `All checks passed!`

- [ ] **Step 7: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-creator/src/lingwen_creator/export/publish.py packages/lingwen-creator/src/lingwen_creator/export/publish_adapters.py packages/lingwen-creator/src/lingwen_creator/export/__init__.py infra/creator_publish.py
git commit -m "feat(creator): Phase 126 v16.2.5 T1.c — export/publish + publish_adapters + __init__

迁移 infra/creator_publish.py + infra/creator_publish_adapters.py 到 packages/lingwen-creator/src/lingwen_creator/export/。

迁移内容:
- export/publish.py — submit_creator_publish + list_creator_publish_history + list_publish_platforms
- export/publish_adapters.py — PublishAdapter Protocol + 4 platform stubs + PublishCapabilities/PublishSubmitResult dataclasses
- export/__init__.py — 5 star-imports (noqa: F403)

Intra-package imports 调整:
- infra.creator_publish_adapters.* → lingwen_creator.export.publish_adapters.* (intra-subdomain)

Shim pattern (1 shim file):
- infra/creator_publish.py → 1-line re-export
- infra/creator_publish_adapters.py 已 in T1.b (shim 灯亮)

后续 T1.d: test_export.py + ruff fixup。"
```

---

## 5. T1.d — test_export.py + ruff fixup

**Files:**
- Create: `packages/lingwen-creator/tests/test_export.py` (≥5 tests + legacy import path back-compat)
- Modify: (possibly) any ruff violations from accumulated imports

**Steps:**

- [ ] **Step 1: 写 `test_export.py` failing test (RED → GREEN)**

```python
# packages/lingwen-creator/tests/test_export.py
"""Phase 126 v16.2.5: tests for export/ subdomain (5 modules)."""
from __future__ import annotations

import pytest


def test_export_package_imports() -> None:
    """lingwen_creator.export package is importable."""
    import lingwen_creator.export
    assert lingwen_creator.export.__name__ == "lingwen_creator.export"


def test_common_module_exports() -> None:
    """lingwen_creator.export.common exports export_metadata + load_export_chapters."""
    from lingwen_creator.export.common import (
        export_metadata,
        load_export_chapters,
        resolve_export_chapter_nums,
        split_paragraphs,
        written_chapter_nums,
        utc_modified_iso,
    )
    assert callable(export_metadata)
    assert callable(load_export_chapters)
    assert callable(resolve_export_chapter_nums)


def test_docx_module_exports() -> None:
    """lingwen_creator.export.docx exports build_creator_docx_bytes."""
    from lingwen_creator.export.docx import build_creator_docx_bytes
    assert callable(build_creator_docx_bytes)


def test_epub_module_exports() -> None:
    """lingwen_creator.export.epub exports build_creator_epub_bytes."""
    from lingwen_creator.export.epub import build_creator_epub_bytes
    assert callable(build_creator_epub_bytes)


def test_publish_module_exports() -> None:
    """lingwen_creator.export.publish exports submit + list_history + list_platforms."""
    from lingwen_creator.export.publish import (
        submit_creator_publish,
        list_creator_publish_history,
    )
    assert callable(submit_creator_publish)
    assert callable(list_creator_publish_history)


def test_publish_adapters_module_exports() -> None:
    """lingwen_creator.export.publish_adapters exports Protocol + 4 stubs + get_publish_adapter."""
    from lingwen_creator.export.publish_adapters import (
        PublishAdapter,
        PublishCapabilities,
        PublishSubmitResult,
        FanqiePublishAdapter,
        QidianPublishAdapter,
        JjwxcPublishAdapter,
        CustomPublishAdapter,
        get_publish_adapter,
        list_publish_platforms,
    )
    assert callable(get_publish_adapter)
    assert callable(list_publish_platforms)
    assert FanqiePublishAdapter.platform_id == "fanqie"
    assert QidianPublishAdapter.platform_id == "qidian"
    assert JjwxcPublishAdapter.platform_id == "jjwxc"
    assert CustomPublishAdapter.platform_id == "custom"


def test_legacy_import_paths_still_work() -> None:
    """Backwards compat: `from infra.creator_export_X import ...` and `from infra.creator_publish_X import ...`."""
    # Shim equivalence checks
    from infra.creator_export_common import (
        export_metadata as LegacyExportMeta,
        load_export_chapters as LegacyLoadChapters,
    )
    from infra.creator_export_docx import build_creator_docx_bytes as LegacyDocx
    from infra.creator_export_epub import build_creator_epub_bytes as LegacyEpub
    from infra.creator_publish import submit_creator_publish as LegacyPublish
    from infra.creator_publish_adapters import (
        get_publish_adapter as LegacyGetAdapter,
        FanqiePublishAdapter as LegacyFanqie,
    )

    from lingwen_creator.export.common import export_metadata, load_export_chapters
    from lingwen_creator.export.docx import build_creator_docx_bytes
    from lingwen_creator.export.epub import build_creator_epub_bytes
    from lingwen_creator.export.publish import submit_creator_publish
    from lingwen_creator.export.publish_adapters import (
        get_publish_adapter,
        FanqiePublishAdapter,
    )

    assert LegacyExportMeta is export_metadata
    assert LegacyLoadChapters is load_export_chapters
    assert LegacyDocx is build_creator_docx_bytes
    assert LegacyEpub is build_creator_epub_bytes
    assert LegacyPublish is submit_creator_publish
    assert LegacyGetAdapter is get_publish_adapter
    assert LegacyFanqie is FanqiePublishAdapter


def test_intra_package_imports_no_cycle() -> None:
    """Intra-package imports (export.common + export.publish_adapters) work without shim detour."""
    # Per v16.2.4 §5.1 lesson 1: intra-package imports must use new path,
    # not infra shim, to avoid cycle via shim proxy.
    from lingwen_creator.export.docx import build_creator_docx_bytes
    from lingwen_creator.export.epub import build_creator_epub_bytes
    from lingwen_creator.export.publish import submit_creator_publish
    # All callable, no ImportError
    assert callable(build_creator_docx_bytes)
    assert callable(build_creator_epub_bytes)
    assert callable(submit_creator_publish)
```

- [ ] **Step 2: 运行测试,验证 PASSED**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-creator/tests/test_export.py -v 2>&1 | tail -15
```

Expected: **8 PASSED**

- [ ] **Step 3: 验证现有 tests 无 regression**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest tests/ packages/lingwen-creator/tests/ packages/lingwen-shared/tests/ -q 2>&1 | tail -5
```

Expected: baseline + 8 = 378+ passing (per v16.2.4 baseline 370 + 8 new tests)

- [ ] **Step 4: ruff --fix (清理可能 I001 violations)**

```bash
cd /home/ailearn/projects/LingWen
ruff check --fix packages/lingwen-creator/src/lingwen_creator/export/ packages/lingwen-creator/tests/test_export.py 2>&1 | tail -5
```

Expected: 0 violations (or auto-fixed)

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-creator/tests/test_export.py
git commit -m "feat(creator): Phase 126 v16.2.5 T1.d — test_export.py + ruff fixup

Tests:
- packages/lingwen-creator/tests/test_export.py (8 tests)
  - test_export_package_imports
  - test_common/docx/epub/publish/publish_adapters_module_exports
  - test_legacy_import_paths_still_work (back-compat for 5 infra shims)
  - test_intra_package_imports_no_cycle (per v16.2.4 §5.1 lesson 1)

Lessons applied:
- v16.2.4 §5.1 lesson 1: intra-package imports must use new path (avoid shim cycle)
- v16.2.4 §5.1 lesson 2: legacy import path tests for back-compat verification

后续 T2: 8 DTOs to lingwen-shared + TS codegen + tests。"
```

---

## 6. T2 — 8 Export/Publish DTOs to lingwen-shared

**Files:**
- Modify: `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` (+8 DTOs in Export + Publish sections)
- Auto-generated: `packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts` (auto-generated, +8 TS interfaces)
- Modify: `packages/lingwen-shared/tests/test_creator_dto.py` (+8 tests for Export/Publish DTOs)

**Steps:**

- [ ] **Step 1: 写 8 failing tests in `test_creator_dto.py` (RED)**

```python
# Append to packages/lingwen-shared/tests/test_creator_dto.py
"""Phase 126 v16.2.5: tests for Export + Publish DTOs (8 models)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from lingwen_shared.contracts.python.creator import (
    CreatorEpubExportRequest,
    CreatorDocxExportRequest,
    CreatorPublishRequest,
    CreatorPublishEntry,
    CreatorPublishPlatformCapabilities,
    CreatorPublishPlatform,
    CreatorPublishPlatformsResponse,
    CreatorPublishHistoryResponse,
)


def test_epub_export_request_defaults() -> None:
    req = CreatorEpubExportRequest()
    assert req.mode == "full"
    assert req.submission_sample_count == 3
    assert req.start_chapter is None
    assert req.end_chapter is None


def test_epub_export_request_full() -> None:
    req = CreatorEpubExportRequest(
        mode="range",
        start_chapter=1,
        end_chapter=10,
        title="林栀",
        author="灵文作者",
        description="测试导出",
    )
    assert req.start_chapter == 1
    assert req.end_chapter == 10


def test_docx_export_request_matches_epub() -> None:
    """DocxExportRequest schema is identical to EpubExportRequest."""
    epub = CreatorEpubExportRequest(mode="submission", submission_sample_count=5)
    docx = CreatorDocxExportRequest(mode="submission", submission_sample_count=5)
    assert epub.mode == docx.mode
    assert epub.submission_sample_count == docx.submission_sample_count


def test_publish_request_defaults() -> None:
    req = CreatorPublishRequest(platform="fanqie")
    assert req.platform == "fanqie"
    assert req.include_outline is True
    assert req.intro == ""
    assert req.mode == "submission"


def test_publish_entry_round_trip() -> None:
    entry = CreatorPublishEntry(
        id="abc123",
        platform="fanqie",
        include_outline=True,
        mode="submission",
        status="adapter_stub",
        message="已入队",
        created_at="2026-08-28T10:00:00Z",
        adapter_id="fanqie",
        connection="stub",
    )
    assert entry.id == "abc123"
    assert entry.external_url is None
    assert entry.package_hint is None


def test_publish_platform_capabilities_defaults() -> None:
    caps = CreatorPublishPlatformCapabilities()
    assert caps.supports_submission_pack is True
    assert caps.supports_full_book is False
    assert caps.oauth_required is True
    assert caps.max_intro_chars == 2000


def test_publish_platform_nested_capabilities() -> None:
    """Platform embeds capabilities (nested helper)."""
    caps = CreatorPublishPlatformCapabilities(supports_full_book=True, max_intro_chars=500)
    platform = CreatorPublishPlatform(
        id="fanqie", label="番茄小说", connection="stub", capabilities=caps,
    )
    assert platform.capabilities.max_intro_chars == 500


def test_publish_platforms_response_has_slug() -> None:
    caps = CreatorPublishPlatformCapabilities()
    platform = CreatorPublishPlatform(id="custom", label="自定义", connection="disconnected", capabilities=caps)
    resp = CreatorPublishPlatformsResponse(slug="test-project", platforms=[platform])
    assert resp.slug == "test-project"
    assert len(resp.platforms) == 1


def test_publish_history_response_has_entries() -> None:
    entry = CreatorPublishEntry(
        id="x1", platform="qidian", include_outline=False, mode="full",
        status="queued", message="OK", created_at="2026-08-28",
    )
    resp = CreatorPublishHistoryResponse(slug="test-project", entries=[entry])
    assert resp.entries[0].platform == "qidian"
```

- [ ] **Step 2: 验证 FAIL (RED)**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/test_creator_dto.py -v 2>&1 | tail -15
```

Expected: **9 ImportError FAILED** (DTOs not yet in creator.py)

- [ ] **Step 3: 在 `creator.py` 加 8 Pydantic DTOs**

读 `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` 当前末尾,append:

```python
# =============================================================================
# Export + Publish DTOs (Phase 126 v16.2.5)
# =============================================================================


class CreatorEpubExportRequest(BaseModel):
    """POST /api/creator/export/epub request body."""
    model_config = ConfigDict(extra="ignore")

    mode: str = "full"  # "full" | "range" | "submission"
    start_chapter: Optional[int] = None
    end_chapter: Optional[int] = None
    title: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    submission_sample_count: Optional[int] = 3


class CreatorDocxExportRequest(BaseModel):
    """POST /api/creator/export/docx request body."""
    model_config = ConfigDict(extra="ignore")

    mode: str = "full"
    start_chapter: Optional[int] = None
    end_chapter: Optional[int] = None
    title: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    submission_sample_count: Optional[int] = 3


class CreatorPublishRequest(BaseModel):
    """POST /api/creator/publish request body."""
    model_config = ConfigDict(extra="ignore")

    platform: str  # "fanqie" | "qidian" | "jjwxc" | "custom"
    include_outline: bool = True
    intro: str = ""
    mode: str = "submission"


class CreatorPublishEntry(BaseModel):
    """Single publish job entry (response item + history row)."""
    model_config = ConfigDict(extra="ignore")

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


class CreatorPublishPlatformCapabilities(BaseModel):
    """Capability descriptor for a publish platform (nested helper)."""
    model_config = ConfigDict(extra="ignore")

    supports_submission_pack: bool = True
    supports_full_book: bool = False
    oauth_required: bool = True
    max_intro_chars: int = 2000


class CreatorPublishPlatform(BaseModel):
    """Single publish platform descriptor (nested helper)."""
    model_config = ConfigDict(extra="ignore")

    id: str
    label: str
    connection: str
    capabilities: CreatorPublishPlatformCapabilities


class CreatorPublishPlatformsResponse(BaseModel):
    """GET /api/creator/publish/platforms response."""
    model_config = ConfigDict(extra="ignore")

    slug: str
    platforms: list[CreatorPublishPlatform] = Field(default_factory=list)


class CreatorPublishHistoryResponse(BaseModel):
    """GET /api/creator/publish/history response."""
    model_config = ConfigDict(extra="ignore")

    slug: str
    entries: list[CreatorPublishEntry] = Field(default_factory=list)
```

- [ ] **Step 4: 验证 GREEN**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/test_creator_dto.py -v 2>&1 | tail -15
```

Expected: **9 PASSED** (1 existing memory test + 8 new Export/Publish tests, but actually all 9 are new — confirm count)

- [ ] **Step 5: TS codegen**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python tooling/contracts/generate.py 2>&1 | tail -5
```

Expected: `WROTE .../ts/creator.ts (XXXXX bytes)` — size increased by ~2-3KB from 8 new interfaces

- [ ] **Step 6: 验证 TS codegen 输出**

```bash
cd /home/ailearn/projects/LingWen
grep -cE "CreatorEpubExportRequest|CreatorDocxExportRequest|CreatorPublishRequest|CreatorPublishEntry|CreatorPublishPlatformCapabilities|CreatorPublishPlatform|CreatorPublishPlatformsResponse|CreatorPublishHistoryResponse" packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts
```

Expected: 8 (one match per DTO interface)

- [ ] **Step 7: zod reverse validation**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python tooling/contracts/zod_revalidate.py 2>&1 | tail -3
```

Expected: `zod reverse validation OK (no drift detected)`

- [ ] **Step 8: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts packages/lingwen-shared/tests/test_creator_dto.py
git commit -m "feat(contracts): Phase 126 v16.2.5 T2 — Export/Publish DTOs in lingwen-shared

新增 8 Export/Publish DTOs to creator.py:
- CreatorEpubExportRequest + CreatorDocxExportRequest (mode + range + metadata)
- CreatorPublishRequest + CreatorPublishEntry (publish job lifecycle)
- CreatorPublishPlatformCapabilities + CreatorPublishPlatform (nested helpers)
- CreatorPublishPlatformsResponse + CreatorPublishHistoryResponse (list endpoints)

Pydantic v2 + ConfigDict(extra='ignore') forward-compat pattern (v16.1 lesson)。

TDD:
- packages/lingwen-shared/tests/test_creator_dto.py (+9 tests, 含 1 nested + 1 round-trip)
- defaults / nested / round-trip 三类覆盖

TS codegen:
- tooling/contracts/generate.py → creator.ts regenerated (+8 interfaces)
- zod reverse validation CI: 0 drift

后续 T3: typed wrapper + knip allowlist。"
```

---

## 7. T3.a — export.ts typed wrapper + re-export + knip allowlist

**Files:**
- Create: `apps/dashboard/src/api/export.ts` (5 wrapper functions)
- Create: `packages/dashboard-contracts/src/shared/export.ts` (re-export shim)
- Modify: `packages/dashboard-contracts/src/shared/creator.ts` (add 8 Export/Publish types to re-export list)
- Modify: `apps/dashboard/knip.json` (+2 allowlist entries)

**Steps:**

- [ ] **Step 1: 创建 `packages/dashboard-contracts/src/shared/export.ts` re-export shim**

```typescript
// packages/dashboard-contracts/src/shared/export.ts
// Phase 126 v16.2.5: re-export Export/Publish DTOs from lingwen-shared TS codegen.
//
// pnpm workspace 不知道 lingwen-shared Python 包存在,但 TS codegen 输出到
// packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts 可直接 import。
//
// v16.2.1 lesson: TS re-export shim 在 dashboard-contracts/,不直接跨包 import Python 模块。

export type {
  CreatorEpubExportRequest,
  CreatorDocxExportRequest,
  CreatorPublishRequest,
  CreatorPublishEntry,
  CreatorPublishPlatformCapabilities,
  CreatorPublishPlatform,
  CreatorPublishPlatformsResponse,
  CreatorPublishHistoryResponse,
} from '../../lingwen-shared/src/lingwen_shared/contracts/ts/creator';
```

- [ ] **Step 2: 更新 `packages/dashboard-contracts/src/shared/creator.ts` re-export list**

读 `packages/dashboard-contracts/src/shared/creator.ts` 当前 re-export list,在末尾加 8 个 export type aliases:

```typescript
// Add to existing creator.ts re-export list:
export type {
  CreatorEpubExportRequest,
  CreatorDocxExportRequest,
  CreatorPublishRequest,
  CreatorPublishEntry,
  CreatorPublishPlatformCapabilities,
  CreatorPublishPlatform,
  CreatorPublishPlatformsResponse,
  CreatorPublishHistoryResponse,
} from '../../lingwen-shared/src/lingwen_shared/contracts/ts/creator';
```

- [ ] **Step 3: 创建 `apps/dashboard/src/api/export.ts` typed wrapper**

```typescript
// apps/dashboard/src/api/export.ts
// Phase 126 v16.2.5: typed wrapper for creator export + publish endpoints.
//
// Style: NO zod runtime validation (v16.2.1 lesson 4), NO /api/ prefix (v16.2.1 lesson 5).
// core.js BASE_URL 已是 /api, paths in this file 不带 /api/.

import { request } from './core.js';
import type {
  CreatorEpubExportRequest,
  CreatorDocxExportRequest,
  CreatorPublishRequest,
  CreatorPublishEntry,
  CreatorPublishPlatformsResponse,
  CreatorPublishHistoryResponse,
} from '@lingwen/dashboard-contracts/shared/creator';

const BASE_URL = import.meta.env.VITE_API_BASE || '/api';

async function fetchBlob(path: string, body: unknown): Promise<Blob> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => 'Unknown error');
    throw new Error(`API Error ${res.status}: ${text}`);
  }
  return res.blob();
}

/** POST /creator/export/epub — generate EPUB zip bytes */
export async function exportCreatorEpub(body: CreatorEpubExportRequest): Promise<Blob> {
  return fetchBlob('/creator/export/epub', body);
}

/** POST /creator/export/docx — generate DOCX zip bytes */
export async function exportCreatorDocx(body: CreatorDocxExportRequest): Promise<Blob> {
  return fetchBlob('/creator/export/docx', body);
}

/** POST /creator/publish — submit publish job */
export async function submitCreatorPublish(body: CreatorPublishRequest): Promise<CreatorPublishEntry> {
  return request('/creator/publish', { method: 'POST', body });
}

/** GET /creator/publish/platforms — list available platforms */
export async function fetchCreatorPublishPlatforms(): Promise<CreatorPublishPlatformsResponse> {
  return request('/creator/publish/platforms');
}

/** GET /creator/publish/history?limit=N — list recent publish jobs */
export async function fetchCreatorPublishHistory(limit = 10): Promise<CreatorPublishHistoryResponse> {
  const q = limit != null ? `?limit=${limit}` : '';
  return request(`/creator/publish/history${q}`);
}
```

- [ ] **Step 4: 更新 `apps/dashboard/knip.json` allowlist**

读 `apps/dashboard/knip.json`,加 2 entries:

```json
{
  "ignore": [
    "apps/dashboard/src/api/export.ts",
    "packages/dashboard-contracts/src/shared/export.ts"
  ]
}
```

(注意: `packages/dashboard-contracts/src/shared/creator.ts` 已在 v16.2.1 allowlist — 复用)

- [ ] **Step 5: 验证 TypeScript 类型检查**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm exec vue-tsc --noEmit 2>&1 | tail -5
```

Expected: `0 errors`

- [ ] **Step 6: knip 检查**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm exec knip 2>&1 | tail -10
```

Expected: 0 errors (allowlist 已加)

- [ ] **Step 7: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add packages/dashboard-contracts/src/shared/export.ts packages/dashboard-contracts/src/shared/creator.ts apps/dashboard/src/api/export.ts apps/dashboard/knip.json
git commit -m "feat(dashboard): Phase 126 v16.2.5 T3.a — export typed wrapper + re-export + knip

新增 typed wrapper:
- apps/dashboard/src/api/export.ts — 5 wrapper functions:
  exportCreatorEpub, exportCreatorDocx, submitCreatorPublish,
  fetchCreatorPublishPlatforms, fetchCreatorPublishHistory
  (含 Blob 返回 for export endpoints + request for publish endpoints;
   风格与 v16.1 T4 world.ts / workspace.ts / quality.ts 一致, NO zod, NO /api/)

Re-export chain update:
- packages/dashboard-contracts/src/shared/export.ts NEW (8 Export/Publish types)
- packages/dashboard-contracts/src/shared/creator.ts UPDATE (add 8 types to explicit list)

knip.json 加 2 allowlist (export.ts + dashboard-contracts/export.ts)。

v16.1 lessons applied:
- TS re-export shim 在 dashboard-contracts/, 不直接跨包 import Python 模块
- knip allowlist 与 typed wrapper 同步加

后续 T3.b: URL contract tests。"
```

---

## 8. T3.b — URL contract test

**Files:**
- Create: `apps/dashboard/tests/unit/api-export-typed-wrapper.spec.ts` (5+ URL contract tests)

**Steps:**

- [ ] **Step 1: 创建 `api-export-typed-wrapper.spec.ts`**

```typescript
// apps/dashboard/tests/unit/api-export-typed-wrapper.spec.ts
// Phase 126 v16.2.5: URL contract regression lock for export.ts typed wrapper.
// Verifies typed wrappers use /creator/export/* + /creator/publish/* paths
// (NOT /api/creator/export/* — BASE_URL already provides /api/).
import { describe, it, expect, vi, beforeEach } from 'vitest';

import {
  exportCreatorEpub,
  exportCreatorDocx,
  submitCreatorPublish,
  fetchCreatorPublishPlatforms,
  fetchCreatorPublishHistory,
} from '@/api/export';

describe('export typed wrapper — URL contract', () => {
  let mockFetch: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockFetch = vi.fn();
    globalThis.fetch = mockFetch as unknown as typeof fetch;
  });

  it('exportCreatorEpub hits /creator/export/epub (no /api/ prefix)', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      blob: async () => new Blob([new Uint8Array([1, 2, 3])], { type: 'application/epub+zip' }),
    });
    await exportCreatorEpub({ mode: 'full' });
    expect(mockFetch).toHaveBeenCalledWith(
      '/api/creator/export/epub',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: 'full' }),
      }),
    );
  });

  it('exportCreatorDocx hits /creator/export/docx', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      blob: async () => new Blob([new Uint8Array([1, 2, 3])], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' }),
    });
    await exportCreatorDocx({ mode: 'range', start_chapter: 1, end_chapter: 10 });
    expect(mockFetch).toHaveBeenCalledWith(
      '/api/creator/export/docx',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ mode: 'range', start_chapter: 1, end_chapter: 10 }),
      }),
    );
  });

  it('submitCreatorPublish uses /creator/publish', async () => {
    const { request } = await import('@/api/core');
    const requestSpy = vi.spyOn({ request }, 'request');
    // (Mocked via core.js request function)
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        id: 'p1', platform: 'fanqie', include_outline: true, mode: 'submission',
        status: 'queued', message: 'OK', created_at: '2026-08-28',
      }),
    });
    const entry = await submitCreatorPublish({ platform: 'fanqie', intro: 'test' });
    expect(entry.platform).toBe('fanqie');
  });

  it('fetchCreatorPublishPlatforms uses /creator/publish/platforms', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        slug: 'test',
        platforms: [{ id: 'fanqie', label: '番茄小说', connection: 'stub', capabilities: {} }],
      }),
    });
    const resp = await fetchCreatorPublishPlatforms();
    expect(resp.slug).toBe('test');
    expect(resp.platforms).toHaveLength(1);
  });

  it('fetchCreatorPublishHistory with limit uses query string', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ slug: 'test', entries: [] }),
    });
    await fetchCreatorPublishHistory(30);
    expect(mockFetch.mock.calls[0][0]).toContain('/creator/publish/history?limit=30');
  });

  it('fetchCreatorPublishHistory without limit omits query string', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ slug: 'test', entries: [] }),
    });
    await fetchCreatorPublishHistory();
    expect(mockFetch.mock.calls[0][0]).toContain('/creator/publish/history');
    expect(mockFetch.mock.calls[0][0]).not.toContain('?limit');
  });
});
```

- [ ] **Step 2: 运行 URL contract tests**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm vitest run tests/unit/api-export-typed-wrapper.spec.ts --reporter=verbose 2>&1 | tail -20
```

Expected: **6 PASSED**

- [ ] **Step 3: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/tests/unit/api-export-typed-wrapper.spec.ts
git commit -m "feat(dashboard): Phase 126 v16.2.5 T3.b — export URL contract tests

URL contract regression lock:
- apps/dashboard/tests/unit/api-export-typed-wrapper.spec.ts (6 tests)
  - exportCreatorEpub → /creator/export/epub (NO /api/ prefix)
  - exportCreatorDocx → /creator/export/docx
  - submitCreatorPublish → /creator/publish
  - fetchCreatorPublishPlatforms → /creator/publish/platforms
  - fetchCreatorPublishHistory (?limit=N) → /creator/publish/history?limit=N

Per v16.2.1 lesson 5 + v16.2.4 lesson 4 (typed wrapper params forwarding fragility):
- Body 转发到 fetch call (exportCreatorEpub/Docx + submitCreatorPublish)
- Query string 拼接 (fetchCreatorPublishHistory)
- Blob 返回 (export endpoints)

后续 T4: routes imports migration。"
```

---

## 9. T4 — routes imports migration

**Files:**
- Modify: `apps/studio_api/routes/creator_core.py` (5 lazy imports)

**Steps:**

- [ ] **Step 1: 读 `creator_core.py` line 283-366 (export/publish endpoints)**

读 5 lazy imports:
- Line 285: `from infra.creator_export_epub import build_creator_epub_bytes`
- Line 311: `from infra.creator_export_docx import build_creator_docx_bytes`
- Line 337: `from infra.creator_publish import submit_creator_publish`
- Line 351: `from infra.creator_publish import list_publish_platforms`
- Line 363: `from infra.creator_publish import list_creator_publish_history`

- [ ] **Step 2: 替换 5 imports**

```python
# Line 285:
from infra.creator_export_epub import build_creator_epub_bytes
# →
from lingwen_creator.export.epub import build_creator_epub_bytes

# Line 311:
from infra.creator_export_docx import build_creator_docx_bytes
# →
from lingwen_creator.export.docx import build_creator_docx_bytes

# Line 337:
from infra.creator_publish import submit_creator_publish
# →
from lingwen_creator.export.publish import submit_creator_publish

# Line 351:
from infra.creator_publish import list_publish_platforms
# →
from lingwen_creator.export.publish import list_publish_platforms

# Line 363:
from infra.creator_publish import list_creator_publish_history
# →
from lingwen_creator.export.publish import list_creator_publish_history
```

- [ ] **Step 3: 验证 routes 仍 work (smoke test)**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -c "from apps.studio_api.routes.creator_core import router; print('routes import OK')"
/home/ailearn/miniconda3/bin/python -m pytest tests/infra/test_creator_*.py -q 2>&1 | tail -3
```

Expected: routes import OK + 241+ tests passing (no regression)

- [ ] **Step 4: grep verification**

```bash
cd /home/ailearn/projects/LingWen
grep -cE "infra\.creator_export|infra\.creator_publish" apps/studio_api/routes/creator_core.py
```

Expected: `0`

- [ ] **Step 5: ruff check**

```bash
cd /home/ailearn/projects/LingWen
ruff check apps/studio_api/routes/creator_core.py 2>&1 | tail -3
```

Expected: `All checks passed!`

- [ ] **Step 6: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/studio_api/routes/creator_core.py
git commit -m "feat(routes): Phase 126 v16.2.5 T4 — export/publish routes imports migration

Migration of 5 lazy imports in apps/studio_api/routes/creator_core.py:
- infra.creator_export_epub → lingwen_creator.export.epub (line 285)
- infra.creator_export_docx → lingwen_creator.export.docx (line 311)
- infra.creator_publish.submit_creator_publish → lingwen_creator.export.publish (line 337)
- infra.creator_publish.list_publish_platforms → lingwen_creator.export.publish (line 351)
- infra.creator_publish.list_creator_publish_history → lingwen_creator.export.publish (line 363)

Verified:
- pytest tests/infra/test_creator_*.py: 241+ PASS (no regression)
- grep infra.creator_export|infra.creator_publish: 0 occurrences
- ruff: 0 errors

后续 T5: composable refactor + delete api/publish.js shim。"
```

---

## 10. T5.a — composable refactor (useProductExport + useProductPublish)

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorProductTools/useProductExport.ts` (3 import changes)
- Modify: `apps/dashboard/src/composables/useCreatorProductTools/useProductPublish.ts` (3 import changes)

**Steps:**

- [ ] **Step 1: Refactor `useProductExport.ts`**

读当前 file (line 15-20):

```javascript
// Before:
import {
  fetchChapters,
  fetchCreatorChapterPreview,
  exportCreatorEpub,
  exportCreatorDocx,
} from '../../api/index.js';
```

改为:

```javascript
// After:
import { fetchChapters } from '../../api/index.js';
import { fetchCreatorChapterPreview } from '@/api/content';
import {
  exportCreatorEpub,
  exportCreatorDocx,
} from '@/api/export';
```

(注: `fetchCreatorChapterPreview` 已在 v16.2.4 content.ts typed wrapper 中 — 直接用新路径)

- [ ] **Step 2: Refactor `useProductPublish.ts`**

读当前 file (line 15-19):

```javascript
// Before:
import {
  submitCreatorPublish,
  fetchCreatorPublishHistory,
  fetchCreatorPublishPlatforms,
} from '../../api/index.js';
```

改为:

```javascript
// After:
import {
  submitCreatorPublish,
  fetchCreatorPublishHistory,
  fetchCreatorPublishPlatforms,
} from '@/api/export';
```

- [ ] **Step 3: vue-tsc check**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm exec vue-tsc --noEmit 2>&1 | tail -5
```

Expected: `0 errors`

- [ ] **Step 4: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/composables/useCreatorProductTools/useProductExport.ts apps/dashboard/src/composables/useCreatorProductTools/useProductPublish.ts
git commit -m "feat(dashboard): Phase 126 v16.2.5 T5.a — export/publish composables refactor

Refactor:
- useProductExport.ts (Phase 19 拆出): 3 export calls → typed wrapper
  - exportCreatorEpub + exportCreatorDocx → @/api/export
  - fetchCreatorChapterPreview → @/api/content (per v16.2.4, was 仍在 api/index.js alias)

- useProductPublish.ts (Phase 19 拆出): 3 publish calls → typed wrapper
  - submitCreatorPublish + fetchCreatorPublishHistory + fetchCreatorPublishPlatforms → @/api/export

@/ alias (not ../../api) per v16.2.4 spec §12.2.

Verified:
- vue-tsc: 0 errors

后续 T5.b: api/index.js update + delete api/publish.js shim。"
```

---

## 11. T5.b — api/index.js update + delete api/publish.js

**Files:**
- Modify: `apps/dashboard/src/api/index.js` (replace 5 publish.js imports + 6 legacy aliases)
- Delete: `apps/dashboard/src/api/publish.js`

**Steps:**

- [ ] **Step 1: grep orphan test (per v16.2.4 §5.1 lesson 5)**

```bash
cd /home/ailearn/projects/LingWen
grep -rln "api/publish\|publish.js" apps/dashboard/tests/ 2>&1 | head -10
```

Expected: 0 files (publish.js uses raw fetch in components, not direct test mocks)

- [ ] **Step 2: 读 `apps/dashboard/src/api/index.js` 当前结构**

读 file,找到:
- `from './publish.js'` import (T5.b 替换)
- 6 legacy aliases: `exportCreatorEpub, exportCreatorDocx, submitCreatorPublish, fetchCreatorPublishHistory, fetchCreatorPublishPlatforms` (从 publish.js re-export)

- [ ] **Step 3: Update `api/index.js`**

```javascript
// Before (re-exports from publish.js):
export {
  fetchCreatorChapterPreview,
  saveCreatorChapterBody,
  saveCreatorChapterOutline,
  generateCreatorVolumeSummary,
  exportCreatorEpub,
  exportCreatorDocx,
  submitCreatorPublish,
  fetchCreatorPublishHistory,
  fetchCreatorPublishPlatforms,
} from './publish.js';

// After (re-exports from typed wrapper):
export { fetchCreatorChapterPreview, saveCreatorChapterBody, saveCreatorChapterOutline } from '@/api/content';
export { generateCreatorVolumeSummary } from '@/api/volume';
export {
  exportCreatorEpub,
  exportCreatorDocx,
  submitCreatorPublish,
  fetchCreatorPublishHistory,
  fetchCreatorPublishPlatforms,
} from '@/api/export';
```

(注: `generateCreatorVolumeSummary` 已在 v16.2.1 volume.ts typed wrapper 中 — 顺势切到 typed wrapper)

- [ ] **Step 4: Delete `apps/dashboard/src/api/publish.js`**

```bash
cd /home/ailearn/projects/LingWen
git rm apps/dashboard/src/api/publish.js
```

- [ ] **Step 5: 验证 vue-tsc + vitest (no orphan import)**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm exec vue-tsc --noEmit 2>&1 | tail -5
pnpm vitest run --reporter=dot 2>&1 | tail -5
```

Expected: vue-tsc 0 + vitest baseline (1778+) PASS

- [ ] **Step 6: grep verification**

```bash
cd /home/ailearn/projects/LingWen
grep -rln "from.*api/publish\|from.*publish\.js" apps/dashboard/src/ 2>&1 | head -5
```

Expected: 0 files (publish.js 已删,无 orphan import)

- [ ] **Step 7: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/api/index.js apps/dashboard/src/api/publish.js
git commit -m "feat(dashboard): Phase 126 v16.2.5 T5.b — api/index.js update + delete publish.js shim

Refactor:
- apps/dashboard/src/api/index.js: 5 publish.js re-exports → @/api/export typed wrapper
- 6 legacy Creator-prefixed aliases preserved (exportCreatorEpub/Docx + submit/fetchCreatorPublish*)
- Bonus: generateCreatorVolumeSummary → @/api/volume (per v16.2.1, was 仍在 publish.js)
- Bonus: fetchCreatorChapterPreview + saveCreatorChapterBody + saveCreatorChapterOutline → @/api/content (per v16.2.4)

Delete:
- apps/dashboard/src/api/publish.js (legacy Phase 62.4 shim with raw fetch)

Verified:
- vue-tsc 0 errors
- vitest 1778+ PASS (no orphan import)
- grep 'from.*api/publish': 0 occurrences
- per v16.2.4 §5.1 lesson 5: orphan test files grep BEFORE deletion (0 found)

后续 T6: cross-subdomain check + intra-package imports。"
```

---

## 12. T6 — cross-subdomain check + intra-package imports

**Files:**
- Modify: 1-3 files (depending on grep findings, likely 0)

**Steps:**

- [ ] **Step 1: grep remaining `infra.creator_export|infra.creator_publish` imports**

```bash
cd /home/ailearn/projects/LingWen
grep -rln "infra\.creator_export\|infra\.creator_publish" apps/ packages/ --include="*.py" 2>&1 | head -10
```

Expected: 只 5 shim files (infra/creator_export_common.py + creator_export_docx.py + creator_export_epub.py + creator_publish.py + creator_publish_adapters.py)。No consumers left.

- [ ] **Step 2: grep frontend consumer check**

```bash
cd /home/ailearn/projects/LingWen
grep -rln "infra\.creator_export\|infra\.creator_publish" apps/dashboard/src/ --include="*.ts" --include="*.vue" --include="*.js" 2>&1 | head -10
```

Expected: 0 files (frontend uses typed wrapper via @/api/export, never touches infra.creator_* directly)

- [ ] **Step 3: 验证 intra-package imports 都用了新 path**

```bash
cd /home/ailearn/projects/LingWen
grep -nE "from infra\.creator_export|from infra\.creator_publish" packages/lingwen-creator/src/lingwen_creator/export/*.py 2>&1 | head -10
```

Expected: 0 (intra-package imports 都用 `from lingwen_creator.export.*` 或 `from lingwen_creator.content.dashboard` / `from lingwen_creator.settings.docs`)

- [ ] **Step 4: If no findings, skip commit. If findings, fix and commit.**

If T6.1-3 all return 0: skip commit (no changes needed). Document in T8 handoff.

If any finding: fix and commit as T6 fixup.

- [ ] **Step 5: ruff check (full)**

```bash
cd /home/ailearn/projects/LingWen
ruff check . 2>&1 | tail -3
```

Expected: `All checks passed!`

---

## 13. T7 — fixups (test mock paths + ruff I001)

**Files:**
- Modify: 0-5 files (depending on verification gates)

**Per v16.2.4 lessons 2 + 5** (will be discovered during verification):

- [ ] **Step 1: grep test patches targeting infra.creator_export|infra.creator_publish**

```bash
cd /home/ailearn/projects/LingWen
grep -rln "patch.*infra\.creator_export\|patch.*infra\.creator_publish\|patch.*infra/creator_export\|patch.*infra/creator_publish" apps/ packages/ --include="*.py" --include="*.ts" 2>&1 | head -10
```

Expected: 0 files (publish.js uses raw fetch, no Python-level mocks)

- [ ] **Step 2: ruff --fix I001 violations**

```bash
cd /home/ailearn/projects/LingWen
ruff check --fix . 2>&1 | tail -5
```

Expected: 0 or auto-fixed

- [ ] **Step 3: 完整 verification gates 跑**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest tests/ packages/lingwen-creator/tests/ packages/lingwen-shared/tests/ -q 2>&1 | tail -3
cd apps/dashboard && pnpm vitest run --reporter=dot 2>&1 | tail -3 && pnpm exec vue-tsc --noEmit 2>&1 | tail -3 && pnpm exec knip 2>&1 | tail -3 && cd ../..
ruff check . 2>&1 | tail -3
/home/ailearn/miniconda3/bin/python tooling/contracts/zod_revalidate.py 2>&1 | tail -3
/home/ailearn/miniconda3/bin/python tooling/contracts/generate.py 2>&1 | tail -3
```

Expected: 全 0 errors

- [ ] **Step 4: If any fixup needed, commit. If clean, skip.**

---

## 14. T8 — handoff + CLAUDE.md + architecture.yml + migration_log

**Files:**
- Create: `docs/superpowers/handoffs/2026-08-28-phase-126-v16-2-5-export-handoff.md`
- Modify: `CLAUDE.md` (bump v16.2.4 → v16.2.5)
- Modify: `.lingwen/architecture.yml` (add export module exports)
- Modify: `.lingwen/migration_log.yml` (v16.2.5 entry)

**Steps:**

- [ ] **Step 1: 写 handoff doc (10 sections per v16.2.4 template)**

仿 `docs/superpowers/handoffs/2026-08-28-phase-126-v16-2-4-content-handoff.md` 模板:

```markdown
# Phase 126 v16.2.5 — Export Subdomain 拆分 Handoff

> **状态**: ✅ 闭环
> **承接**: [spec](../specs/2026-08-28-phase-126-v16-2-5-export-design.md) + [plan](../plans/2026-08-28-phase-126-v16-2-5-export-plan.md)
> **前置**: v16.2.4 content (`f01aaf2d`)
> **下一步**: v16.2.6 memory (3 files Round 2 leaf) + v16.2.7 cleanup

## 0. TL;DR
[brief summary]

## 1. v16.2.5 完成的 N 件事
[table of T1-T8 tasks]

## 2. 决策实现
[Q1-Q5 decisions]

## 3. Plan deviations
[D1-D3]

## 4. v16.2.5 副作用
[impact summary]

## 5. Lessons
[lessons learned]

## 6. Carryover to v16.2.6+
[carryover list]

## 7. 验证证据
[test output]

## 8. 新工具总结
[before/after table]

## 9. v16.2.5 完整 commit 时间线
[commit log]

## 10. Closing Notes
[summary]
```

- [ ] **Step 2: 更新 CLAUDE.md**

读 `CLAUDE.md` line 1-10,更新版本号 + v16.2.5 闭环 entry (per v16.2.4 模板)。

- [ ] **Step 3: 更新 `.lingwen/architecture.yml`**

读 `.lingwen/architecture.yml` `module_boundaries.creator.exports` section,加 export module exports:

```yaml
# Add to creator.exports:
# Export (v16.2.5)
export_metadata, written_chapter_nums, resolve_export_chapter_nums,
load_export_chapters, split_paragraphs, utc_modified_iso,
build_creator_docx_bytes, build_creator_epub_bytes,
submit_creator_publish, list_creator_publish_history,
PublishAdapter, PublishCapabilities, PublishSubmitResult,
FanqiePublishAdapter, QidianPublishAdapter, JjwxcPublishAdapter, CustomPublishAdapter,
get_publish_adapter, list_publish_platforms,
```

- [ ] **Step 4: 更新 `.lingwen/migration_log.yml`**

```yaml
# Prepend v16.2.5 entry:
- phase: v16.2.5
  date: 2026-08-28
  summary: "Export subdomain migration (5 files: export_common + export_docx + export_epub + publish + publish_adapters)"
  files_added:
    - packages/lingwen-creator/src/lingwen_creator/export/__init__.py
    - packages/lingwen-creator/src/lingwen_creator/export/common.py
    - packages/lingwen-creator/src/lingwen_creator/export/docx.py
    - packages/lingwen-creator/src/lingwen_creator/export/epub.py
    - packages/lingwen-creator/src/lingwen_creator/export/publish.py
    - packages/lingwen-creator/src/lingwen_creator/export/publish_adapters.py
    - packages/lingwen-creator/tests/test_export.py
    - apps/dashboard/src/api/export.ts
    - packages/dashboard-contracts/src/shared/export.ts
  files_modified:
    - infra/creator_export_common.py  # → shim
    - infra/creator_export_docx.py    # → shim
    - infra/creator_export_epub.py    # → shim
    - infra/creator_publish.py        # → shim
    - infra/creator_publish_adapters.py  # → shim
    - packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py  # +8 DTOs
    - packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts     # auto-generated
    - packages/lingwen-shared/tests/test_creator_dto.py                       # +9 tests
    - packages/dashboard-contracts/src/shared/creator.ts                      # +8 re-exports
    - apps/dashboard/knip.json                                              # +2 allowlist
    - apps/dashboard/src/api/index.js                                        # publish.js re-exports → typed wrapper
    - apps/dashboard/src/composables/useCreatorProductTools/useProductExport.ts  # composable refactor
    - apps/dashboard/src/composables/useCreatorProductTools/useProductPublish.ts # composable refactor
    - apps/studio_api/routes/creator_core.py                                 # 5 routes imports migrated
  files_deleted:
    - apps/dashboard/src/api/publish.js  # legacy Phase 62.4 shim
  tests_added: 23 (8 export pkg + 9 DTO + 6 URL contract)
  shim_remaining: 41  # 36 (v16.2.4) + 5 new export shims
  status: closed
```

- [ ] **Step 5: 验证 yaml 格式**

```bash
cd /home/ailearn/projects/LingWen
python -c "import yaml; yaml.safe_load(open('.lingwen/architecture.yml')); yaml.safe_load(open('.lingwen/migration_log.yml')); print('OK')"
```

Expected: `OK`

- [ ] **Step 6: Final verification gates**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest tests/ packages/lingwen-creator/tests/ packages/lingwen-shared/tests/ -q 2>&1 | tail -3
cd apps/dashboard && pnpm vitest run --reporter=dot 2>&1 | tail -3 && pnpm exec vue-tsc --noEmit 2>&1 | tail -3 && pnpm exec knip 2>&1 | tail -3 && cd ../..
ruff check . 2>&1 | tail -3
/home/ailearn/miniconda3/bin/python tooling/contracts/zod_revalidate.py 2>&1 | tail -3
/home/ailearn/miniconda3/bin/python tooling/contracts/generate.py 2>&1 | tail -3
```

Expected: 全 0 errors,baseline + 23 tests added

- [ ] **Step 7: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add docs/superpowers/handoffs/2026-08-28-phase-126-v16-2-5-export-handoff.md CLAUDE.md .lingwen/architecture.yml .lingwen/migration_log.yml
git commit -m "docs(phase-126): v16.2.5 handoff — export subdomain split 闭环

Handoff:
- docs/superpowers/handoffs/2026-08-28-phase-126-v16-2-5-export-handoff.md (10 sections)
- CLAUDE.md: bump v16.2.4 → v16.2.5
- .lingwen/architecture.yml: add export module exports (17 symbols)
- .lingwen/migration_log.yml: v16.2.5 entry (14 files added/modified/deleted + 23 tests + 41 shims)

Final verification:
- pytest: baseline + 23 = 393+ passing
- vitest: baseline + 6 URL contract = 1784+ passing
- vue-tsc 0 / ruff 0 / knip 0 (5 advisory hints) / zod 0 drift / codegen OK

Phase 126 v16.2 series: 5 of 7 sub-phases closed (shared + volume + settings + onboarding + content + export)。下一步 v16.2.6 memory (Round 2 leaf last) + v16.2.7 cleanup。"
```

---

## 15. Verification Gates Summary

### 15.1 Per Task Gates (每次必过)

| Task | Gate | 命令 | 期望 |
|---|---|---|---|
| T1.a-d | import 解析 OK | `python -c "from lingwen_creator.export.X import ..."` | OK |
| T1.d | unit tests | `pytest packages/lingwen-creator/tests/test_export.py -v` | 8 PASSED |
| T2 | DTO tests | `pytest packages/lingwen-shared/tests/test_creator_dto.py -v` | 9 PASSED |
| T2 | TS codegen | `python tooling/contracts/generate.py` | creator.ts regenerated |
| T2 | zod reverse | `python tooling/contracts/zod_revalidate.py` | 0 drift |
| T3.a | vue-tsc | `pnpm exec vue-tsc --noEmit` | 0 errors |
| T3.a | knip | `pnpm exec knip` | 0 errors |
| T3.b | URL contract | `pnpm vitest run tests/unit/api-export-typed-wrapper.spec.ts` | 6 PASSED |
| T4 | routes smoke | `pytest tests/infra/test_creator_*.py -q` | 241+ PASS |
| T5.a | vue-tsc | `pnpm exec vue-tsc --noEmit` | 0 errors |
| T5.b | vitest baseline | `pnpm vitest run --reporter=dot` | 1778+ PASS |
| T8 | yaml valid | `python -c "import yaml; yaml.safe_load(open('architecture.yml')); yaml.safe_load(open('migration_log.yml'))"` | OK |

### 15.2 v16.2.5 Final Gate (T8 必过)

| Gate | 命令 | 期望 |
|---|---|---|
| Backend tests | `pytest tests/ packages/lingwen-creator/tests/ packages/lingwen-shared/tests/ -q` | baseline + ≥23 |
| Frontend tests | `pnpm vitest run --reporter=dot` | 1778 + ≥6 |
| vue-tsc | `pnpm exec vue-tsc --noEmit` | 0 |
| knip | `pnpm exec knip` | 0 |
| ruff | `ruff check .` | 0 |
| zod reverse | `python tooling/contracts/zod_revalidate.py` | 0 drift |
| Handoff doc | `docs/superpowers/handoffs/2026-08-28-phase-126-v16-2-5-export-handoff.md` exists | ✓ |
| import count | `grep -rl "from infra\.creator_export\|from infra\.creator_publish" apps/ packages/ --include="*.py" \| wc -l` | 5 (only shims) |
| shim count | `ls infra/creator_export_*.py infra/creator_publish*.py \| wc -l` | 5 |

---

## 16. Carryover (to v16.2.6+)

| 任务 | 阶段 |
|---|---|
| v16.2.6 memory | 3 files (annotations + assets + query) — Round 2 leaf last |
| v16.2.7 cleanup | 36 shim deletions + 4 typed wrapper `/api/` prefix fix + 22 vitest debt + import-linter DP-01..06 |
| import-linter enforcement | v16.4 (per master plan §11) |
| StoragePort enforcement | v16.5 |
| LLMServicePort enforcement | v16.4 |

---

## 17. Execution Notes

- **本项目不用 worktree** (per CLAUDE.md): 直接在 master commit
- **attribution disabled**: 不要加 `Co-Authored-By: Claude`
- **commit message**: 沿用 v16.2.0..4 风格 — conventional commits + 中文 lessons section
- **DP-06 commit-level**: 每 commit ≤4 files,跨多个 commits 完成 sub-phase
- **shim pattern**: `# noqa: F403` inline (v15.7.1 lesson)
- **typed wrapper style**: 与 v16.1 T4 (world.ts / workspace.ts / quality.ts) 一致
- **knip allowlist**: 加 typed wrapper 时立即同步(v16.1 T4 lesson)

### 17.1 Python File Copy + Import Adjustment Rule (沿用 v16.2.4 §12.1)

每个 sub-phase 移 Python 文件时,统一规则:

1. **Read** `infra/creator_<file>.py` 当前内容
2. **检查 import lines** (`grep "^from infra\." <file>`)
3. **如果 import target 是已迁出的 submodule**:
   - `from infra.creator_<X> import Y` → `from lingwen_creator.<subdomain>.<X> import Y`
   - 例 (v16.2.5 T1.a): `from infra.creator_dashboard import creator_chapter_preview` → `from lingwen_creator.content.dashboard import creator_chapter_preview`
4. **如果 import target 是 infra/ 其他(非 creator)**: 保留原路径 (infra.persistence, infra.studio_registry, infra.paths, infra.project_config)
5. **如果 import target 是 stdlib / 3rd party**: 保留
6. **如果该 file 内部还有相对 import** (e.g., `from ._helpers import ...`): 保留
7. **复制到新 path**:`packages/lingwen-creator/src/lingwen_creator/<subdomain>/<file>.py`,只改 module-level docstring 引用新 location
8. **不要改函数签名 / 内部逻辑 / 函数体** — 只改 import + docstring

### 17.2 Per-Subdomain Import Adjustment Examples (v16.2.5 export)

```python
# export/common.py — 原 import 改:
# Before: from infra.creator_dashboard import creator_chapter_preview
# After:  from lingwen_creator.content.dashboard import creator_chapter_preview

# export/docx.py — 跨子域 + intra-subdomain:
# Before: from infra.creator_export_common import ...
# After:  from lingwen_creator.export.common import ...  (intra-subdomain)
# Before: from infra.creator_settings_docs import creator_settings_docs_payload
# After:  from lingwen_creator.settings.docs import creator_settings_docs_payload

# export/publish.py — intra-subdomain:
# Before: from infra.creator_publish_adapters import get_publish_adapter, list_publish_platforms
# After:  from lingwen_creator.export.publish_adapters import ...

# export/publish_adapters.py — no infra.creator_X imports, only infra.studio_registry (保留)
```

---

**Plan complete and saved to `docs/superpowers/plans/2026-08-28-phase-126-v16-2-5-export-plan.md`.**

**Next step**: Execute T1-T8 task-by-task (推荐 subagent-driven-development 或 inline executing-plans)。每 commit 验证 gate 后 commit,不积累。

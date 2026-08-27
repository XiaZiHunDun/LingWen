# Phase 126 v16.2 — Creator 6-Subdomain 拆分 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 36 个 `infra/creator_*.py` 按 DDD bounded context 拆为 6 个 subdomains,迁到新 `packages/lingwen-creator/` uv workspace package + 加 typed wrappers + 35 composables 切换。

**Architecture:** Strangler Fig migration,v16.2.0..7 共 8 sub-phases,每 sub-phase 3-6 focused commits(DP-06 ≤4 files/commit),shim re-export 模式保 118 consumer files 兼容。依赖 bottom-up 顺序: memory → settings → export → volume → onboarding → content。

**Tech Stack:** Python 3.12+ / Pydantic v2 / uv workspaces / FastAPI / Pydantic → TS hand-rolled codegen / Vue 3 + Pinia + TypeScript strict / Vitest / pytest / ruff / vue-tsc / knip / zod (reverse validation CI)

**Spec:** [`docs/superpowers/specs/2026-08-27-phase-126-v16-2-creator-subdomain-split-design.md`](../specs/2026-08-27-phase-126-v16-2-creator-subdomain-split-design.md) (用户已批准 2026-08-27)

---

## 0. Pre-flight 检查 (Phase 开始前必过)

| 检查 | 命令 | 期望 |
|---|---|---|
| uv workspace 健康 | `uv sync` | 0 errors |
| v16.1.1 baseline tests | `pytest tests/ -q` | 3758 tests collected |
| Frontend baseline | `pnpm vitest run --reporter=dot` | 1731 passed, 1 skipped |
| Type check | `pnpm exec vue-tsc --noEmit` | 0 errors |
| Lint | `ruff check .` + `pnpm lint:all` | 0 |
| Dead code | `pnpm exec knip` | 0 (2 advisory) |
| zod reverse | `uv run python tooling/contracts/zod_revalidate.py` | 0 drift |
| master HEAD | `git log --oneline -1` | `a53a3b1e docs(phase-126): v16.2 spec DP-06 clarifications` |
| working tree clean | `git status` | nothing to commit |

**任何一项不通过就不开 v16.2**。

---

## 1. Sub-phase 概览

| Sub-phase | 范围 | Commits | Files touched | 估计 |
|---|---|---|---|---|
| **v16.2.0** | skeleton + shared | 3 | ~6 | 0.5 天 |
| **v16.2.1** | memory subdomain | 4 | ~14 | 0.5 天 |
| **v16.2.2** | settings subdomain | 4 | ~12 | 0.5 天 |
| **v16.2.3** | export subdomain | 4 | ~16 | 0.5 天 |
| **v16.2.4** | volume subdomain | 5 | ~18 | 1 天 |
| **v16.2.5** | onboarding subdomain | 5 | ~20 | 1 天 |
| **v16.2.6** | content subdomain | 6 | ~25 | 1.5 天 |
| **v16.2.7** | shim cleanup + final gate | 13 | ~40 (split per commit ≤4) | 0.5 天 |
| **总计** | — | 44 | — | **5.5 天** |

**依赖关系**:
- v16.2.0 是其他 sub-phase 的前置
- v16.2.1 (memory) 不依赖其他,可最先
- v16.2.5 (onboarding) 依赖 v16.2.1 (memory) (cross-ref annotation)
- v16.2.6 (content) 依赖 v16.2.1 (memory)
- 其他 settings/export/volume 之间不直接依赖

---

## 2. v16.2.0 — Skeleton + Shared Migration (3 commits, ~6 files)

**目的**: 建 `packages/lingwen-creator/` uv workspace member + 把 `infra/creator_revision.py` + `infra/creator_check.py` 迁到 `lingwen_creator/shared/`,shim re-export 保兼容。

### Task 2.1: 加 lingwen-creator package 到 uv workspace

**Files:**
- Modify: `pyproject.toml` (root, add `[tool.uv.workspace]` member)
- Create: `packages/lingwen-creator/pyproject.toml`

- [ ] **Step 1: 修改 root `pyproject.toml` 加 uv workspace member**

打开 `/home/ailearn/projects/LingWen/pyproject.toml`,找到 `[tool.uv.workspace]` section,加 `packages/lingwen-creator` 到 `members` list。现有 root `pyproject.toml` 已经包含 9 个 packages,加第 10 个:

```toml
[tool.uv.workspace]
members = [
    "packages/lingwen-cli",
    "packages/lingwen-core",
    "packages/lingwen-quality",
    "packages/lingwen-shared",
    "packages/lingwen-storage",
    "packages/lingwen-world-db",
    "packages/dashboard-contracts",
    "apps/studio_api",
    "packages/lingwen-creator",  # NEW (v16.2.0)
]
```

- [ ] **Step 2: 创建 `packages/lingwen-creator/pyproject.toml`**

```toml
[project]
name = "lingwen-creator"
version = "16.2.0"
description = "Creator subdomain bounded contexts (memory / settings / export / volume / onboarding / content)"
requires-python = ">=3.12,<3.14"
dependencies = [
    "pydantic>=2.5",
    "lingwen-shared",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/lingwen_creator"]

# ruff / import-linter 继承 root (v16.0 lesson: 不加 empty section override root)
```

**Note**: `lingwen-creator` (hyphen) 是 packaging name,`lingwen_creator` 是 Python module name (v16.0 lesson 严格分离)。

- [ ] **Step 3: 创建 package skeleton directories**

```bash
mkdir -p packages/lingwen-creator/src/lingwen_creator/shared
mkdir -p packages/lingwen-creator/contracts/python
mkdir -p packages/lingwen-creator/tests
touch packages/lingwen-creator/src/lingwen_creator/__init__.py
touch packages/lingwen-creator/src/lingwen_creator/shared/__init__.py
touch packages/lingwen-creator/contracts/__init__.py
touch packages/lingwen-creator/contracts/python/__init__.py
touch packages/lingwen-creator/tests/__init__.py
```

- [ ] **Step 4: 验证 uv workspace 识别新 package**

```bash
cd /home/ailearn/projects/LingWen
uv sync --all-packages
```

Expected: `Built lingwen-creator @ file:///.../packages/lingwen-creator` + `Installed lingwen-creator==16.2.0`

**Note (v16.2.0 review fix)**: plain `uv sync` **不会**装 workspace member (uv sync 只装 root project + direct deps)。新加 workspace member 必须显式 `uv sync --all-packages`。

- [ ] **Step 5: 验证 `lingwen_creator` 可 import**

```bash
cd /home/ailearn/projects/LingWen
uv run python -c "import lingwen_creator; print(lingwen_creator.__file__)"
```

Expected: 输出 `/home/ailearn/projects/LingWen/packages/lingwen-creator/src/lingwen_creator/__init__.py`

**Note (v16.2.0 review fix)**: `/home/ailearn/miniconda3/bin/python` 是 conda Python 3.13,**不在 uv venv 内**。Miniconda Python 无法 import `lingwen_creator` (uv sync 装在 `.venv/`)。必须用 `uv run python` 让 uv venv 解析 import path。后续所有 v16.2 sub-phase 的 verification commands 都用 `uv run python` 而非 miniconda。

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml packages/lingwen-creator/pyproject.toml packages/lingwen-creator/src/lingwen_creator/ packages/lingwen-creator/contracts/ packages/lingwen-creator/tests/
git commit -m "feat(monorepo): Phase 126 v16.2.0 T1 — lingwen-creator package skeleton

uv workspace 第 10 个 member。hyphen name 'lingwen-creator' (packaging) + underscore module 'lingwen_creator' (Python module),严格分离(v16.0 lesson)。

Skeleton 包含:
- packages/lingwen-creator/pyproject.toml (hatchling, deps: pydantic + lingwen-shared)
- src/lingwen_creator/ (空 + shared/ 待 v16.2.0 T2 填)
- contracts/python/ (空 + 待各 sub-phase 填 DTO)
- tests/ (空 + 待 test_lingwen_creator_layout.py)

继承 root ruff + import-linter config (v16.0 lesson: empty [tool.ruff] override root)。

uv sync OK + import 验证 OK。"
```

### Task 2.2: 迁移 `creator_revision.py` + `creator_check.py` 到 shared/

**Files:**
- Create: `packages/lingwen-creator/src/lingwen_creator/shared/revision.py`
- Create: `packages/lingwen-creator/src/lingwen_creator/shared/check.py`
- Create: `packages/lingwen-creator/tests/test_shared_revision.py`
- Create: `packages/lingwen-creator/tests/test_shared_check.py`
- Create: `packages/lingwen-creator/tests/test_lingwen_creator_layout.py`
- Modify: `infra/creator_revision.py` (变 shim)
- Modify: `infra/creator_check.py` (变 shim)

- [ ] **Step 1: 写 `test_lingwen_creator_layout.py` failing test (RED)**

```python
# packages/lingwen-creator/tests/test_lingwen_creator_layout.py
"""Phase 126 v16.2.0: verify lingwen-creator package layout (5 tests).

仿 v16.1 T1 (`tests/test_lingwen_shared_layout.py`) — uv sync 不验证 member 目录,
需要显式 gate 测试 package layout 与 import path 正确性。
"""
from __future__ import annotations

from pathlib import Path

import pytest

LINGWEN_CREATOR_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PYPROJECT = LINGWEN_CREATOR_ROOT / "packages" / "lingwen-creator" / "pyproject.toml"
PACKAGE_SRC = LINGWEN_CREATOR_ROOT / "packages" / "lingwen-creator" / "src" / "lingwen_creator"


def test_package_pyproject_exists() -> None:
    assert PACKAGE_PYPROJECT.exists(), f"missing {PACKAGE_PYPROJECT}"


def test_package_pyproject_has_hyphen_name() -> None:
    """Packaging name 必须是 hyphen ('lingwen-creator'),不是 underscore."""
    content = PACKAGE_PYPROJECT.read_text(encoding="utf-8")
    assert 'name = "lingwen-creator"' in content, "packaging name must be 'lingwen-creator' (hyphen)"


def test_module_imports_with_underscore_name() -> None:
    """Python module name 必须是 underscore ('lingwen_creator'),不是 hyphen."""
    import lingwen_creator
    assert lingwen_creator.__name__ == "lingwen_creator"


def test_shared_subpackage_exists() -> None:
    assert (PACKAGE_SRC / "shared" / "__init__.py").exists()


def test_uv_workspace_member_declared() -> None:
    root_pyproject = LINGWEN_CREATOR_ROOT / "pyproject.toml"
    content = root_pyproject.read_text(encoding="utf-8")
    assert '"packages/lingwen-creator"' in content or "'packages/lingwen-creator'" in content, (
        "lingwen-creator not declared as uv workspace member in root pyproject.toml"
    )
```

- [ ] **Step 2: 运行测试,验证 FAIL (RED)**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-creator/tests/test_lingwen_creator_layout.py -v
```

Expected: **5 FAILED** (Step 1 中第 2 个文件还没创建,test_package_pyproject_exists FAIL;test_module_imports_with_underscore_name FAIL 等)

- [ ] **Step 3: 创建 `packages/lingwen-creator/src/lingwen_creator/shared/revision.py`**

读 `infra/creator_revision.py` 当前内容(34 lines,includes `CreatorDocConflictError` + `content_revision` util), 复制到 `packages/lingwen-creator/src/lingwen_creator/shared/revision.py`:

```python
# packages/lingwen-creator/src/lingwen_creator/shared/revision.py
"""Shared cross-subdomain utility: revision tracking + conflict exception.

Migrated from infra/creator_revision.py in Phase 126 v16.2.0.
Used by settings/docs, volume/plan, volume/templates — see spec §2.1.
"""
from __future__ import annotations


class CreatorDocConflictError(Exception):
    """Raised when a creator document save fails due to revision mismatch (HTTP 409)."""


def content_revision(text: str) -> str:
    """Compute a content-based revision hash for optimistic concurrency control."""
    import hashlib
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]
```

- [ ] **Step 4: 创建 `packages/lingwen-creator/src/lingwen_creator/shared/check.py`**

读 `infra/creator_check.py` 当前内容(grep exports: `load_creator_check_context`, `apply_creator_check_defaults`, `format_check_mode_banner`), 复制到 `packages/lingwen-creator/src/lingwen_creator/shared/check.py`(保留原 import + 函数体,只调整 module-level docstring 引用 `lingwen_creator.shared`):

```python
# packages/lingwen-creator/src/lingwen_creator/shared/check.py
"""Shared cross-subdomain utility: check context loading + banner formatting.

Migrated from infra/creator_check.py in Phase 126 v16.2.0.
Used primarily by content/agent but available to any subdomain needing check state.
"""
from __future__ import annotations

# 注: 实际函数体从 infra/creator_check.py 复制, 保留所有 imports + 内部逻辑
# (load_creator_check_context, apply_creator_check_defaults, format_check_mode_banner)
#
# 函数体不在本 plan 中 verbatim copy — 执行时 read infra/creator_check.py 复制粘贴
# 内部 import 路径(如 `from infra.project_config import ...`)保留,后续 v16.4 port 时再换
```

- [ ] **Step 5: 写 `test_shared_revision.py` (RED → GREEN 链)**

```python
# packages/lingwen-creator/tests/test_shared_revision.py
"""Phase 126 v16.2.0: tests for shared/revision.py migrated utilities."""
from __future__ import annotations

import pytest

from lingwen_creator.shared.revision import CreatorDocConflictError, content_revision


def test_creator_doc_conflict_error_is_exception() -> None:
    with pytest.raises(CreatorDocConflictError):
        raise CreatorDocConflictError("test conflict")


def test_content_revision_deterministic() -> None:
    rev1 = content_revision("hello world")
    rev2 = content_revision("hello world")
    assert rev1 == rev2


def test_content_revision_differs_on_content_change() -> None:
    rev1 = content_revision("hello world")
    rev2 = content_revision("hello WORLD")
    assert rev1 != rev2


def test_legacy_import_path_still_works() -> None:
    """Backwards compat: old `from infra.creator_revision import CreatorDocConflictError`."""
    from infra.creator_revision import CreatorDocConflictError as LegacyConflict
    assert LegacyConflict is CreatorDocConflictError
```

- [ ] **Step 6: 写 `test_shared_check.py` (RED → GREEN 链)**

```python
# packages/lingwen-creator/tests/test_shared_check.py
"""Phase 126 v16.2.0: tests for shared/check.py migrated utilities."""
from __future__ import annotations

from lingwen_creator.shared.check import (
    apply_creator_check_defaults,
    format_check_mode_banner,
    load_creator_check_context,
)


def test_load_creator_check_context_returns_dict() -> None:
    """load_creator_check_context accepts a project root and returns context dict."""
    result = load_creator_check_context(project_root=None)
    assert isinstance(result, dict)


def test_apply_creator_check_defaults_returns_dict() -> None:
    """apply_creator_check_defaults merges defaults into the passed config."""
    config = {"enabled": False}
    result = apply_creator_check_defaults(config)
    assert isinstance(result, dict)


def test_format_check_mode_banner_returns_string() -> None:
    """format_check_mode_banner formats ProjectConfig + CreatorSettings into display string."""
    banner = format_check_mode_banner(config=None, settings=None)
    assert isinstance(banner, str)


def test_legacy_import_path_still_works() -> None:
    """Backwards compat: old `from infra.creator_check import ...`."""
    from infra.creator_check import load_creator_check_context as LegacyLoad
    assert LegacyLoad is load_creator_check_context
```

- [ ] **Step 7: 把 `infra/creator_revision.py` 改为 shim**

```bash
cd /home/ailearn/projects/LingWen
```

读取 `infra/creator_revision.py` 当前 34 lines,**完全替换**为:

```python
"""Phase 126 v16.2.0 shim: re-export from lingwen_creator.shared.revision.

Migrated to packages/lingwen-creator/src/lingwen_creator/shared/revision.py.
This shim maintains backwards compat for 118 consumer files using:
    from infra.creator_revision import CreatorDocConflictError, content_revision

Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.shared.revision import *  # noqa: F403
```

- [ ] **Step 8: 把 `infra/creator_check.py` 改为 shim**

读取 `infra/creator_check.py` 当前内容,**完全替换**为:

```python
"""Phase 126 v16.2.0 shim: re-export from lingwen_creator.shared.check.

Migrated to packages/lingwen-creator/src/lingwen_creator/shared/check.py.
This shim maintains backwards compat for consumers using:
    from infra.creator_check import load_creator_check_context, ...

Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.shared.check import *  # noqa: F403
```

- [ ] **Step 9: 运行所有新测试,验证 GREEN**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-creator/tests/ -v
```

Expected: **13 PASSED** (5 layout + 4 revision + 4 check)

- [ ] **Step 10: 验证现有 3758 tests 无 regression**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest tests/ -q 2>&1 | tail -3
```

Expected: `3758 passed` (baseline)

- [ ] **Step 11: ruff check + lint**

```bash
cd /home/ailearn/projects/LingWen
ruff check . 2>&1 | tail -3
```

Expected: `All checks passed!`

如果 F403 (star-import) 警告:`--add-noqa F403` 是 v15.7.1 lesson 处理 `__init__.py` star-import 的标准做法,但 `infra/creator_revision.py` + `infra/creator_check.py` 不是 `__init__.py`,需要 `# noqa: F403` inline 已经在 shim 内容中加。

- [ ] **Step 12: Commit**

```bash
git add packages/lingwen-creator/src/lingwen_creator/shared/ packages/lingwen-creator/tests/ infra/creator_revision.py infra/creator_check.py
git commit -m "feat(creator): Phase 126 v16.2.0 T2 — shared/ migration + shim re-export

迁移 infra/creator_revision.py + infra/creator_check.py 到 packages/lingwen-creator/src/lingwen_creator/shared/。

迁移内容:
- shared/revision.py — CreatorDocConflictError + content_revision util
- shared/check.py — load_creator_check_context + apply_creator_check_defaults + format_check_mode_banner

Shim pattern:
- infra/creator_revision.py 变 1-line shim `from lingwen_creator.shared.revision import * # noqa: F403`
- infra/creator_check.py 同
- 0 consumer files 改动 (backwards compat,118 consumers 不变)

测试:
- packages/lingwen-creator/tests/test_lingwen_creator_layout.py (5 tests, layout gate)
- packages/lingwen-creator/tests/test_shared_revision.py (4 tests, 含 legacy import path)
- packages/lingwen-creator/tests/test_shared_check.py (4 tests, 含 legacy import path)

Lessons applied:
- v15.7.1: ruff F403 noqa 是 star-import 标准做法 (inline in shim)
- v15.7.1: tests/__init__.py 解决 pytest module-namespace 冲突 (root tests/ + packages/lingwen-creator/tests/ 双 __init__.py)
- v16.0: hyphen name + underscore module 严格分离 (已在 T1 commit)

Verified: pytest 3758+13 = 3771 passed, ruff 0, no regression。"
```

### Task 2.3: 加 `creator` 进 `.lingwen/architecture.yml` module_boundaries + `migration_log`

**Files:**
- Modify: `.lingwen/architecture.yml`
- Modify: `.lingwen/migration_log.yml`

- [ ] **Step 1: 在 `.lingwen/architecture.yml` 加 `creator` module_boundaries 新位置**

打开 `.lingwen/architecture.yml`,找到 `module_boundaries.creator` section (line 47-50), 修改 `path: infra/creator/` 为 `path: packages/lingwen-creator/src/lingwen_creator/`,并扩 exports + allowed_imports:

```yaml
  creator:
    path: packages/lingwen-creator/src/lingwen_creator/  # v16.2.0 迁移
    exports: [
      # Shared
      CreatorDocConflictError, content_revision,
      load_creator_check_context, apply_creator_check_defaults, format_check_mode_banner,
      # Memory (v16.2.1)
      upsert_memory_annotation, creator_memory_assets_payload, creator_memory_query,
      # Settings (v16.2.2) — 待添加
      # Export (v16.2.3) — 待添加
      # Volume (v16.2.4) — 待添加
      # Onboarding (v16.2.5) — 待添加
      # Content (v16.2.6) — 待添加
    ]
    allowed_imports: [
      infra/persistence, infra/project_config, infra/errors,
      lingwen_shared,
    ]
    notes:
      - "v16.2.0: skeleton + shared migration (4 files)"
      - "v16.2.1: memory subdomain (3 files)"
      - "v16.2.2-6: settings/export/volume/onboarding/content (依次)"
      - "v16.2.7: shim cleanup, infra/creator_* removed"
```

**注意**: `infra/creator_*` (旧 location) 在 v16.2.0..6 期间保留作为 shim。删除在 v16.2.7。

- [ ] **Step 2: 加 `v16.2.0` entry 到 `.lingwen/migration_log.yml`**

打开 `.lingwen/migration_log.yml`,如不存在则创建。Prepend v16.2.0 entry:

```yaml
version: "1.0"  # Phase 126 migration log

migrations:
  - phase: v16.2.0
    date: 2026-08-27
    summary: "lingwen-creator package skeleton + shared/ migration (2 files: creator_revision + creator_check)"
    files_added:
      - packages/lingwen-creator/pyproject.toml
      - packages/lingwen-creator/src/lingwen_creator/__init__.py
      - packages/lingwen-creator/src/lingwen_creator/shared/__init__.py
      - packages/lingwen-creator/src/lingwen_creator/shared/revision.py
      - packages/lingwen-creator/src/lingwen_creator/shared/check.py
      - packages/lingwen-creator/contracts/__init__.py
      - packages/lingwen-creator/contracts/python/__init__.py
      - packages/lingwen-creator/tests/__init__.py
      - packages/lingwen-creator/tests/test_lingwen_creator_layout.py
      - packages/lingwen-creator/tests/test_shared_revision.py
      - packages/lingwen-creator/tests/test_shared_check.py
    files_modified:
      - infra/creator_revision.py  # → shim
      - infra/creator_check.py     # → shim
    tests_added: 13
    shim_remaining: 34  # infra/creator_*.py except shared (which now in shared/)
    status:  closed

  - phase: v16.0
    date: 2026-08-26
    summary: "uv workspaces + turbo + import-linter skeleton (Phase 124)"
    # ... (existing entry from v16.0)
```

- [ ] **Step 3: 验证 yaml 格式正确**

```bash
cd /home/ailearn/projects/LingWen
python -c "import yaml; yaml.safe_load(open('.lingwen/architecture.yml')); yaml.safe_load(open('.lingwen/migration_log.yml')); print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add .lingwen/architecture.yml .lingwen/migration_log.yml
git commit -m "docs(architecture): Phase 126 v16.2.0 T3 — module_boundaries + migration_log

更新 .lingwen/architecture.yml:
- creator module path: infra/creator/ → packages/lingwen-creator/src/lingwen_creator/
- exports 列出 v16.2.0 已迁入的 shared/ symbols
- allowed_imports 显式 infra/persistence + infra/project_config + infra/errors + lingwen_shared
- notes 记 v16.2.0..6 sub-phase 计划

更新 .lingwen/migration_log.yml:
- v16.2.0 entry: 11 files added + 2 modified + 13 tests + 34 shims remaining
- v16.0 entry 保留 (history audit)

Lessons applied:
- v16.0: module_boundaries 声明是新 package 必须做的 documentation update
- v16.0: migration_log append-prepend pattern (v16.0 handoff §D8)"
```

### Task 2.4: v16.2.0 验证门

- [ ] **Step 1: 全套 v16.1 baseline verification gates**

```bash
cd /home/ailearn/projects/LingWen
uv sync --all-packages 2>&1 | tail -3
uv run python -m pytest tests/ packages/lingwen-creator/tests/ -q 2>&1 | tail -3
ruff check . 2>&1 | tail -3
cd apps/dashboard && pnpm vitest run --reporter=dot 2>&1 | tail -3 && pnpm exec vue-tsc --noEmit 2>&1 | tail -3 && pnpm exec knip 2>&1 | tail -3 && cd ../..
uv run python tooling/contracts/zod_revalidate.py 2>&1 | tail -3
```

Expected: 全 0 errors,baseline +13 tests

- [ ] **Step 2: Verify v16.2.0 final state**

```bash
cd /home/ailearn/projects/LingWen
echo "=== packages/lingwen-creator files ==="
ls packages/lingwen-creator/src/lingwen_creator/
ls packages/lingwen-creator/src/lingwen_creator/shared/
ls packages/lingwen-creator/tests/
echo ""
echo "=== shim count (should be 34 = 36 - 2 migrated) ==="
ls infra/creator_*.py | wc -l
echo ""
echo "=== git log for v16.2.0 ==="
git log --oneline -5
```

Expected: 3 commits for v16.2.0, 34 shims remaining (out of 36 original creator_*.py)

- [ ] **Step 3: Mark v16.2.0 完成**

```bash
# In plan doc, check off v16.2.0 完成
```

- [ ] **Step 4: 如果要继续 v16.2.1,进入 Section 3**

---

## 3. v16.2.1 — Memory Subdomain (4 commits, ~14 files)

**目的**: 迁 `infra/creator_memory_{annotations,assets,query}.py` 到 `lingwen_creator/memory/`,加 DTO + TS codegen + typed wrapper + 3 composables 切换。

### Task 3.1: 创建 `lingwen_creator/memory/` package + 移 Python files

**Files:**
- Create: `packages/lingwen-creator/src/lingwen_creator/memory/__init__.py`
- Create: `packages/lingwen-creator/src/lingwen_creator/memory/annotations.py`
- Create: `packages/lingwen-creator/src/lingwen_creator/memory/assets.py`
- Create: `packages/lingwen-creator/src/lingwen_creator/memory/query.py`
- Modify: `infra/creator_memory_annotations.py` (→ shim)
- Modify: `infra/creator_memory_assets.py` (→ shim)
- Modify: `infra/creator_memory_query.py` (→ shim)
- Create: `packages/lingwen-creator/tests/test_memory.py`

- [ ] **Step 1: 写 `test_memory.py` failing test (RED)**

```python
# packages/lingwen-creator/tests/test_memory.py
"""Phase 126 v16.2.1: tests for memory/ subdomain (3 modules)."""
from __future__ import annotations

from pathlib import Path

import pytest


def test_memory_package_imports() -> None:
    """lingwen_creator.memory package is importable."""
    import lingwen_creator.memory
    assert lingwen_creator.memory.__name__ == "lingwen_creator.memory"


def test_annotations_module_exports() -> None:
    """lingwen_creator.memory.annotations exports upsert_memory_annotation."""
    from lingwen_creator.memory.annotations import upsert_memory_annotation
    assert callable(upsert_memory_annotation)


def test_assets_module_exports() -> None:
    """lingwen_creator.memory.assets exports creator_memory_assets_payload."""
    from lingwen_creator.memory.assets import creator_memory_assets_payload
    assert callable(creator_memory_assets_payload)


def test_query_module_exports() -> None:
    """lingwen_creator.memory.query exports creator_memory_query."""
    from lingwen_creator.memory.query import creator_memory_query
    assert callable(creator_memory_query)


def test_legacy_import_paths_still_work() -> None:
    """Backwards compat: `from infra.creator_memory_X import ...` works."""
    from infra.creator_memory_annotations import upsert_memory_annotation as LegacyUpsert
    from infra.creator_memory_assets import creator_memory_assets_payload as LegacyPayload
    from infra.creator_memory_query import creator_memory_query as LegacyQuery

    from lingwen_creator.memory.annotations import upsert_memory_annotation
    from lingwen_creator.memory.assets import creator_memory_assets_payload
    from lingwen_creator.memory.query import creator_memory_query

    assert LegacyUpsert is upsert_memory_annotation
    assert LegacyPayload is creator_memory_assets_payload
    assert LegacyQuery is creator_memory_query
```

- [ ] **Step 2: 运行测试,验证 FAIL**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-creator/tests/test_memory.py -v 2>&1 | tail -10
```

Expected: **5 FAILED** (ImportError on lingwen_creator.memory)

- [ ] **Step 3: 创建 `packages/lingwen-creator/src/lingwen_creator/memory/__init__.py`**

```python
"""Phase 126 v16.2.1: memory/ subdomain (creator knowledge base / RAG).

Bounded context: knowledge assets + annotations + semantic query.
Migrated from infra/creator_memory_*.py.
"""
from lingwen_creator.memory.annotations import *  # noqa: F403
from lingwen_creator.memory.assets import *  # noqa: F403
from lingwen_creator.memory.query import *  # noqa: F403
```

- [ ] **Step 4: 创建 `packages/lingwen-creator/src/lingwen_creator/memory/annotations.py`**

读 `infra/creator_memory_annotations.py` 当前内容(grep `^def \|^class \|^[A-Z_]+ =`), 复制到新文件。原 import 路径中如 `from infra.creator_revision import CreatorDocConflictError` 改为 `from lingwen_creator.shared.revision import CreatorDocConflictError`(但 memory/annotations 不需要 revision,可保留 `from infra.errors import ...`)。

```python
# packages/lingwen-creator/src/lingwen_creator/memory/annotations.py
"""Memory annotations — pin + note on creator knowledge assets.

Migrated from infra/creator_memory_annotations.py in Phase 126 v16.2.1.
"""
from __future__ import annotations

# 注: 实际函数体从 infra/creator_memory_annotations.py 复制,
# 调整内部 import: infra.X → lingwen_creator.shared.X (如需要) 或保留 infra.X (back-compat 期间)
#
# 主要 export: upsert_memory_annotation(root, asset_id, *, note=None, pinned=None) -> dict
#
# 执行时 read infra/creator_memory_annotations.py 复制 + 调整 import
```

- [ ] **Step 5: 创建 `packages/lingwen-creator/src/lingwen_creator/memory/assets.py`**

读 `infra/creator_memory_assets.py`,同上复制。

- [ ] **Step 6: 创建 `packages/lingwen-creator/src/lingwen_creator/memory/query.py`**

读 `infra/creator_memory_query.py`,同上复制。

- [ ] **Step 7: 把 `infra/creator_memory_*.py` 改为 shim**

```bash
cd /home/ailearn/projects/LingWen
```

每个 `infra/creator_memory_*.py` 文件内容替换为:

```python
"""Phase 126 v16.2.1 shim: re-export from lingwen_creator.memory.X.

Migrated to packages/lingwen-creator/src/lingwen_creator/memory/X.py.
Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.memory.<X> import *  # noqa: F403
```

(3 个 shim 文件,每个 5 行)

- [ ] **Step 8: 运行 test_memory.py + 现有 tests,验证 GREEN + no regression**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-creator/tests/test_memory.py -v 2>&1 | tail -10
/home/ailearn/miniconda3/bin/python -m pytest tests/ -q 2>&1 | tail -3
```

Expected: 5 PASSED (test_memory.py) + 3758 baseline passed

- [ ] **Step 9: ruff check**

```bash
cd /home/ailearn/projects/LingWen
ruff check packages/lingwen-creator/ infra/creator_memory_*.py 2>&1 | tail -5
```

Expected: `All checks passed!` (shim files have inline `# noqa: F403`)

- [ ] **Step 10: Commit**

```bash
git add packages/lingwen-creator/src/lingwen_creator/memory/ packages/lingwen-creator/tests/test_memory.py infra/creator_memory_annotations.py infra/creator_memory_assets.py infra/creator_memory_query.py
git commit -m "feat(creator): Phase 126 v16.2.1 T1 — memory subdomain migration

迁移 infra/creator_memory_{annotations,assets,query}.py → packages/lingwen-creator/src/lingwen_creator/memory/。

迁移内容:
- memory/annotations.py — upsert_memory_annotation
- memory/assets.py — creator_memory_assets_payload
- memory/query.py — creator_memory_query

Shim pattern (3 shim files):
- infra/creator_memory_X.py 变 1-line re-export
- 0 consumer files 改动 (backwards compat)

测试:
- packages/lingwen-creator/tests/test_memory.py (5 tests)
- 含 legacy import path backwards compat 测试

Verified: pytest 3758+5+13(v16.2.0)+N(new tests) passed, ruff 0, no regression。

v16.2.1 后续 T2-T4: DTO + TS codegen + typed wrapper + composable refactor。"
```

### Task 3.2: 加 Memory DTO 到 `lingwen-shared` + TS codegen

**Files:**
- Modify: `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` (NEW)
- Modify: `packages/lingwen-shared/pyproject.toml` (add `creator` to Pydantic sources)
- Auto-generated: `packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts`
- Modify: `packages/lingwen-shared/tests/test_creator_dto.py` (NEW)

- [ ] **Step 1: 写 `test_creator_dto.py` failing test (RED) — Memory 部分**

```python
# packages/lingwen-shared/tests/test_creator_dto.py
"""Phase 126 v16.2.1: tests for creator/ DTOs (memory + future subdomains)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from lingwen_shared.contracts.python.creator import (
    CreatorMemoryAsset,
    CreatorMemoryAnnotation,
    CreatorMemoryQueryRequest,
    CreatorMemoryQueryResponse,
    CreatorMemoryAssetsResponse,
)


def test_memory_asset_minimal() -> None:
    asset = CreatorMemoryAsset(id="asset-1", kind="character_bible", title="林栀")
    assert asset.id == "asset-1"
    assert asset.kind == "character_bible"


def test_memory_asset_id_optional() -> None:
    """TDD-driven: id Optional (matches v16.1 ChapterDTO.id optional lesson)."""
    asset = CreatorMemoryAsset(id=None, kind="lore", title="世界观")
    assert asset.id is None


def test_memory_annotation_requires_note_or_pinned() -> None:
    """Annotation requires note or pinned (matches route validation)."""
    with pytest.raises(ValidationError):
        CreatorMemoryAnnotation(asset_id="a-1", note=None, pinned=None)


def test_memory_query_request_validation() -> None:
    req = CreatorMemoryQueryRequest(query="林栀的力量体系", top_k=5)
    assert req.top_k == 5


def test_memory_query_response_has_results() -> None:
    resp = CreatorMemoryQueryResponse(query="test", results=[])
    assert resp.results == []


def test_memory_assets_response_wrapper() -> None:
    resp = CreatorMemoryAssetsResponse(assets=[])
    assert resp.assets == []
```

- [ ] **Step 2: 验证 FAIL**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/test_creator_dto.py -v 2>&1 | tail -10
```

Expected: ImportError (creator.py 不存在) → 6 FAILED

- [ ] **Step 3: 创建 `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py`**

```python
# packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py
"""Phase 126 v16.2.1: creator/ DTOs (memory subdomain starter, more in v16.2.2..6).

Pydantic v2 source of truth. TS codegen via tooling/contracts/generate.py.
v16.1 lessons applied:
- ConfigDict(extra="ignore") for forward-compat
- id fields Optional where route accepts omitted
- Note: 实际 import field from existing Pydantic models in apps/studio_api/models.py
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CreatorMemoryAsset(BaseModel):
    """A knowledge asset in creator memory (e.g., character bible, lore note)."""
    model_config = ConfigDict(extra="ignore")

    id: Optional[str] = None  # v16.1 lesson: Optional like ChapterDTO.id
    kind: str  # "character_bible" | "lore" | "outline" | ...
    title: str
    excerpt: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CreatorMemoryAnnotation(BaseModel):
    """User note + pinned flag on a memory asset."""
    model_config = ConfigDict(extra="ignore")

    asset_id: str
    note: Optional[str] = None
    pinned: Optional[bool] = None
    updated_at: Optional[datetime] = None


class CreatorMemoryQueryRequest(BaseModel):
    """Semantic query request for creator memory."""
    model_config = ConfigDict(extra="ignore")

    query: str
    top_k: int = 5
    scope: Optional[str] = None


class CreatorMemoryQueryHit(BaseModel):
    """Single result from memory query."""
    model_config = ConfigDict(extra="ignore")

    asset_id: str
    score: float
    excerpt: str


class CreatorMemoryQueryResponse(BaseModel):
    """Semantic query response with hits."""
    model_config = ConfigDict(extra="ignore")

    query: str
    results: list[CreatorMemoryQueryHit] = Field(default_factory=list)


class CreatorMemoryAssetsResponse(BaseModel):
    """List of memory assets for current project."""
    model_config = ConfigDict(extra="ignore")

    assets: list[CreatorMemoryAsset] = Field(default_factory=list)
```

- [ ] **Step 4: 验证 GREEN**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/test_creator_dto.py -v 2>&1 | tail -10
```

Expected: **6 PASSED**

- [ ] **Step 5: 跑 TS codegen**

```bash
cd /home/ailearn/projects/LingWen
uv run python tooling/contracts/generate.py 2>&1 | tail -10
```

Expected: `WROTE packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts (XXX bytes)`

- [ ] **Step 6: 验证 TS codegen 输出**

```bash
cd /home/ailearn/projects/LingWen
cat packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts | head -40
```

Expected: TS interface declarations for CreatorMemoryAsset, CreatorMemoryAnnotation, etc.

- [ ] **Step 7: 验证 zod reverse 不 drift**

```bash
cd /home/ailearn/projects/LingWen
uv run python tooling/contracts/zod_revalidate.py 2>&1 | tail -3
```

Expected: `zod reverse validation OK (no drift detected)`

- [ ] **Step 8: Commit**

```bash
git add packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts packages/lingwen-shared/tests/test_creator_dto.py
git commit -m "feat(contracts): Phase 126 v16.2.1 T2 — Memory DTO in lingwen-shared

新增 creator.py DTO module (6 DTOs):
- CreatorMemoryAsset (id Optional per v16.1 lesson)
- CreatorMemoryAnnotation
- CreatorMemoryQueryRequest / Response / Hit
- CreatorMemoryAssetsResponse

Pydantic v2 + ConfigDict(extra='ignore') forward-compat pattern (v16.1 lesson)。

Test-first TDD:
- packages/lingwen-shared/tests/test_creator_dto.py (6 tests)
- test_memory_asset_id_optional 显式验证 v16.1 Optional lesson 应用

TS codegen:
- tooling/contracts/generate.py → creator.ts 生成
- zod reverse validation CI 验证 0 drift

后续 T3-T4: typed wrapper + composable refactor。"
```

### Task 3.3: 加 typed wrapper `apps/dashboard/src/api/memory.ts` + knip allowlist

**Files:**
- Create: `apps/dashboard/src/api/memory.ts`
- Create: `packages/dashboard-contracts/src/shared/creator.ts` (re-export shim)
- Modify: `apps/dashboard/knip.json`

- [ ] **Step 1: 创建 `packages/dashboard-contracts/src/shared/creator.ts` re-export shim**

```typescript
// packages/dashboard-contracts/src/shared/creator.ts
// Phase 126 v16.2.1: re-export creator DTOs from lingwen-shared TS codegen.
//
// pnpm workspace 不知道 lingwen-shared Python 包存在,但 TS codegen 输出到
// packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts 可直接 import。
//
// v16.1 lesson: TS re-export shim 在 dashboard-contracts/,不直接跨包 import Python 模块。

export type {
  CreatorMemoryAsset,
  CreatorMemoryAnnotation,
  CreatorMemoryQueryRequest,
  CreatorMemoryQueryResponse,
  CreatorMemoryQueryHit,
  CreatorMemoryAssetsResponse,
} from '../../lingwen-shared/src/lingwen_shared/contracts/ts/creator';
```

- [ ] **Step 2: 创建 `apps/dashboard/src/api/memory.ts` typed wrapper**

```typescript
// apps/dashboard/src/api/memory.ts
// Phase 126 v16.2.1: typed wrapper for creator memory endpoints.
//
// 替换 composables 中的 raw fetch。zod runtime validation 在 typed wrapper 入口。
// v16.1 pattern: typed wrapper = typed fetch + zod schema + typed return。
//
// 与 v16.1 T4 typed wrappers (world.ts / workspace.ts / quality.ts) 一致 style。

import { z } from 'zod';
import type {
  CreatorMemoryAsset,
  CreatorMemoryAnnotation,
  CreatorMemoryQueryRequest,
  CreatorMemoryQueryResponse,
  CreatorMemoryAssetsResponse,
} from '@lingwen/dashboard-contracts/shared/creator';

const MemoryAssetSchema = z.object({
  id: z.string().nullable().optional(),
  kind: z.string(),
  title: z.string(),
  excerpt: z.string().nullable().optional(),
  tags: z.array(z.string()).optional(),
});

const MemoryAssetsResponseSchema = z.object({
  assets: z.array(MemoryAssetSchema),
});

async function fetchTyped<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export async function getMemoryAssets(): Promise<CreatorMemoryAssetsResponse> {
  const raw = await fetchTyped<unknown>('/api/creator/memory-assets');
  return MemoryAssetsResponseSchema.parse(raw) as CreatorMemoryAssetsResponse;
}

export async function upsertMemoryAnnotation(
  assetId: string,
  body: { note?: string | null; pinned?: boolean | null },
): Promise<CreatorMemoryAnnotation> {
  const raw = await fetchTyped<unknown>(
    `/api/creator/memory-assets/${assetId}/annotation`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    },
  );
  return MemoryAssetSchema.parse(raw) as unknown as CreatorMemoryAnnotation;
}

export async function queryMemory(
  body: CreatorMemoryQueryRequest,
): Promise<CreatorMemoryQueryResponse> {
  const raw = await fetchTyped<unknown>('/api/creator/memory/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return raw as CreatorMemoryQueryResponse;
}
```

- [ ] **Step 3: 更新 `apps/dashboard/knip.json` 加 allowlist**

读 `apps/dashboard/knip.json`,找到 `ignore` 或 `allowlist` section(在 v16.1 T4 已有 typed wrappers 的 allowlist)。加:

```json
{
  "ignore": [
    "apps/dashboard/src/api/memory.ts",
    "packages/dashboard-contracts/src/shared/creator.ts"
  ]
}
```

**Note**: 这些文件会在 v16.2.1 T4 composable refactor 后才被使用,knip 提前 allowlist 防 false positive。

- [ ] **Step 4: 验证 TypeScript 类型检查**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm exec vue-tsc --noEmit 2>&1 | tail -5
```

Expected: `0 errors`

- [ ] **Step 5: knip 检查**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm exec knip 2>&1 | tail -10
```

Expected: 0 errors (allowlist 已加)

- [ ] **Step 6: Commit**

```bash
git add packages/dashboard-contracts/src/shared/creator.ts apps/dashboard/src/api/memory.ts apps/dashboard/knip.json
git commit -m "feat(dashboard): Phase 126 v16.2.1 T3 — memory typed wrapper + knip allowlist

新增 typed wrapper:
- apps/dashboard/src/api/memory.ts — getMemoryAssets, upsertMemoryAnnotation, queryMemory
  (含 zod runtime validation, 风格与 v16.1 T4 world.ts / workspace.ts / quality.ts 一致)
- packages/dashboard-contracts/src/shared/creator.ts — re-export shim

knip.json 加 2 条 allowlist (memory.ts + creator.ts), 防 v16.2.1 T4 composable 切换前的 false positive。

v16.1 lessons applied:
- TS re-export shim 在 dashboard-contracts/, 不直接跨包 import Python 模块 (pnpm workspace 限制)
- knip allowlist 与 typed wrapper 同步加 (v16.1 T4 lesson)

Verified: vue-tsc 0 errors, knip 0 errors。"
```

### Task 3.4: Refactor memory composables 用 typed wrapper + routes 改 import

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorMemory.js`(如存在) + `apps/dashboard/src/composables/useCreatorMemory.ts` (refactor)
- Modify: `apps/studio_api/routes/creator_core.py`(memory routes 改 import)
- Create: `apps/dashboard/src/composables/useCreatorMemory.spec.ts`(如需要)

- [ ] **Step 1: 找到 memory composables**

```bash
cd /home/ailearn/projects/LingWen
ls apps/dashboard/src/composables/ | grep -i memory 2>&1
grep -rln "creator.*memory\|/api/creator/memory" apps/dashboard/src/ 2>&1 | head -10
```

Expected: 找到 1-3 个 composables 使用 memory endpoints

**注**: v16.1 handoff §6 提到 composables 用 raw fetch,本 sub-phase 切换到 typed wrapper。

- [ ] **Step 2: Refactor composables 用 typed wrapper**

打开找到的 composable,把 `fetch('/api/creator/memory-assets')` 替换为:

```javascript
// Before (raw fetch):
const response = await fetch('/api/creator/memory-assets');
const data = await response.json();

// After (typed wrapper):
import { getMemoryAssets } from '@/api/memory';
const data = await getMemoryAssets();
```

类似替换 `upsertMemoryAnnotation`, `queryMemory` 的 raw fetch calls。

- [ ] **Step 3: Routes import path update**

打开 `apps/studio_api/routes/creator_core.py`,找到 memory 相关 3 个 routes (line 226-278 估计,基于 v16.1 explore 结果):

```python
# Before:
from infra.creator_memory_assets import creator_memory_assets_payload
from infra.creator_memory_annotations import upsert_memory_annotation
from infra.creator_memory_query import creator_memory_query

# After:
from lingwen_creator.memory.assets import creator_memory_assets_payload
from lingwen_creator.memory.annotations import upsert_memory_annotation
from lingwen_creator.memory.query import creator_memory_query
```

**测试 routes 仍 work** (因 shim re-export 等价)。

- [ ] **Step 4: 添加 composable spec test (如有 vitest spec)**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
ls src/composables/useCreatorMemory.spec.* 2>&1
```

如不存在,创建 `src/composables/useCreatorMemory.spec.ts`:

```typescript
import { describe, it, expect, vi } from 'vitest';
import { getMemoryAssets } from '@/api/memory';

describe('useCreatorMemory composable', () => {
  it('fetches memory assets via typed wrapper', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ assets: [] }),
    });
    const result = await getMemoryAssets();
    expect(result.assets).toEqual([]);
  });
});
```

- [ ] **Step 5: 验证所有 gates**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest tests/ packages/lingwen-creator/tests/ packages/lingwen-shared/tests/ -q 2>&1 | tail -3
cd apps/dashboard && pnpm vitest run --reporter=dot 2>&1 | tail -3 && pnpm exec vue-tsc --noEmit 2>&1 | tail -3 && pnpm exec knip 2>&1 | tail -3 && cd ../..
ruff check . 2>&1 | tail -3
uv run python tooling/contracts/zod_revalidate.py 2>&1 | tail -3
```

Expected: 全 0 errors,baseline + N tests passed

- [ ] **Step 6: Commit**

```bash
git add apps/dashboard/src/composables/useCreatorMemory* apps/dashboard/src/api/memory.ts apps/studio_api/routes/creator_core.py
git commit -m "feat(dashboard): Phase 126 v16.2.1 T4 — memory composable refactor + route import update

Refactor:
- useCreatorMemory.js (如有) 改 import '@/api/memory' + 用 getMemoryAssets/upsertMemoryAnnotation/queryMemory
- apps/studio_api/routes/creator_core.py 改 3 个 memory route import path:
  from infra.creator_memory_X import → from lingwen_creator.memory.X import

Tests:
- useCreatorMemory.spec.ts (new) 验证 typed wrapper 调用

Lessons applied:
- v18.0 (proposed): @/ alias for composable imports (不数相对路径)
- v15.7.1: vitest + globalThis stubs for fetch mock
- v15.7.1: pages + composables 都走 typed wrapper (v16.1 T4 lesson)

Verified: pytest + vitest + vue-tsc + knip + ruff + zod 全 0 errors。

v16.2.1 闭环 (4 commits total)。下一步 v16.2.2 settings。"
```

### Task 3.5: v16.2.1 验证门

- [ ] **Step 1: 全套 gates**

(同 Task 3.4 Step 5)

- [ ] **Step 2: Verify v16.2.1 final state**

```bash
cd /home/ailearn/projects/LingWen
echo "=== git log for v16.2.1 ==="
git log --oneline -5
echo ""
echo "=== memory files in lingwen_creator ==="
ls packages/lingwen-creator/src/lingwen_creator/memory/
echo ""
echo "=== memory shim count (should be 3) ==="
ls infra/creator_memory_*.py | wc -l
```

Expected: 4 commits for v16.2.1,3 shims remaining

- [ ] **Step 3: Continue to v16.2.2 (Section 4)**

---

## 4. v16.2.2 — Settings Subdomain (4 commits, ~12 files)

**Pattern**: 与 v16.2.1 完整 analog,迁 `infra/creator_{settings_docs,settings_history,merge_preferences}.py` 到 `lingwen_creator/settings/{docs,history,merge_preferences}.py`。

### Task 4.1: 移 Python files + shim

**Files**: 类似 v16.2.1 Task 3.1,但目标是 settings/。

- [ ] **Step 1-9**: 同 v16.2.1 pattern,创建 `packages/lingwen-creator/src/lingwen_creator/settings/{__init__.py,docs.py,history.py,merge_preferences.py}`,3 shim files,`test_settings.py` (≥5 tests)。

迁移内容来自:
- `infra/creator_settings_docs.py` (351 lines, 含 save_creator_settings_docs + preview_settings_docs_diff + preview_settings_three_way + preview_settings_merge_strategy)
- `infra/creator_settings_history.py` (查)
- `infra/creator_merge_preferences.py` (1355 lines,最大 — 需注意 DP-06 ≤4 files per commit,所以本 sub-phase 5 commits)

### Task 4.2: 加 Settings DTOs 到 creator.py

- [ ] **Step 1-7**: 加 ~8 DTOs:
  - `CreatorSettingsDocsResponse`, `CreatorSettingsDocsSaveRequest`, `CreatorSettingsDiffResponse`
  - `CreatorSettingsThreeWayResponse`, `CreatorSettingsMergePreviewResponse`
  - `CreatorSettingsHistoryResponse`, `CreatorSettingsRestoreRequest`
  - `CreatorMergePreferencesResponse`, `CreatorMergePreferencesExportResponse`, `CreatorMergePreferencesImportRequest`/`Response`
  - `CreatorMergePresetPackage`, `CreatorMergePresetConflict`, etc. (~8 DTOs total,基于 routes/creator_settings.py imports)

### Task 4.3: typed wrapper `apps/dashboard/src/api/settings.ts`

### Task 4.4: composable refactor + routes update

- [ ] **Step 1-5**: Refactor `useCreatorSettings.js` (~1 composable per spec)+ 改 routes/creator_settings.py 30 endpoints import

### Task 4.5: v16.2.2 验证门

(同 Task 3.5)

---

## 5. v16.2.3 — Export Subdomain (4 commits, ~16 files)

### Task 5.1: 移 Python files + shim

迁移 5 files: `infra/creator_{export_common,export_docx,export_epub,publish,publish_adapters}.py` → `lingwen_creator/export/{common,docx,epub,publish,publish_adapters}.py`。

### Task 5.2: 加 Export DTOs (~6 DTOs)

### Task 5.3: typed wrapper `apps/dashboard/src/api/export.ts`

### Task 5.4: composable refactor (3 composables: useCreatorExportDocx, useCreatorExportEpub, useCreatorPublish) + routes update

(creator_core.py 中 export/publish routes 改 import)

---

## 6. v16.2.4 — Volume Subdomain (5 commits, ~18 files)

最大 DTO 集合 (~10 DTOs)。

### Task 6.1-6.5: 同 v16.2.1 pattern

迁移 6 files + 10 DTOs + typed wrapper + 6 composables + creator_volume.py 24 endpoints 改 import。

**注意**: `creator_volume_plan_share.py` 与 `creator_volume_pulse.py` 较小可一次 commit。`creator_volume_templates.py` (1022 lines) 与 `creator_template_approvals.py` (692 lines) 各 1 commit。

---

## 7. v16.2.5 — Onboarding Subdomain (5 commits, ~20 files)

9 files (最多),含 8 onboarding_X sub-modules + diff_collab。

### Task 7.1-7.5: 同 v16.2.1 pattern

迁移 9 files + 10 DTOs + typed wrapper + 4 composables + creator_onboarding.py 24 endpoints 改 import。

**Cross-ref**: onboarding 可能 import memory.annotations (`upsert_memory_annotation` for cross-context annotation),可走 lingwen_creator.memory.annotations — 但仅在 onboarding 内使用,符合 DP-01 (cross-context import via contract)。

---

## 8. v16.2.6 — Content Subdomain (6 commits, ~25 files)

最大 sub-phase,10 files + ~15 DTOs + 19 composables。

### Task 8.1-8.6: 同 v16.2.1 pattern

迁移 10 files (agent + dashboard + batch_history + check + logic_check + models + mode + preferences + revision + ui_profile)+ 15 DTOs + typed wrapper + 19 composables (useCreatorAgent + useCreatorBatchHistory + useCreatorModeGuide + useCreatorPage* + useCreatorPulse + useCreatorProductTools + useCreatorWorkspace + useCreatorWrite* + useCreatorWriteWorkbench 等)+ creator_core.py 中 content routes 改 import。

**Decomposition for DP-06**:
- T1: agent + check + logic_check + models (4 files)
- T2: dashboard + batch_history + mode (3 files)
- T3: preferences + revision + ui_profile (3 files)

每 T 独立 commit,每个 ≤4 files。

---

## 9. v16.2.7 — Final Cleanup (13 commits, 每 commit ≤4 files)

v16.2.7 = 删除 36 shim + 加 lint check, **多 commit 强制 DP-06**。

### Task 9.1: Delete 2 shared shims (2 commits)

- [ ] **Step 1: 删除 `infra/creator_revision.py`**

```bash
cd /home/ailearn/projects/LingWen
git rm infra/creator_revision.py
git commit -m "chore(cleanup): Phase 126 v16.2.7 T1 — delete creator_revision shim

shim 已无用处 (所有 consumer 已在 v16.2.0 期间切到 lingwen_creator.shared.revision 或保留)。"
```

- [ ] **Step 2: 删除 `infra/creator_check.py`** (同 Step 1 pattern)

### Task 9.2: Delete 3 memory shims (1 commit)

- [ ] **Step 1: 删除 3 memory shims**

```bash
cd /home/ailearn/projects/LingWen
git rm infra/creator_memory_annotations.py infra/creator_memory_assets.py infra/creator_memory_query.py
git commit -m "chore(cleanup): Phase 126 v16.2.7 T2 — delete 3 memory shims

v16.2.1 起的 shim 现在无用处 (composables 已切 typed wrapper)。"
```

### Task 9.3: Delete 3 settings shims (1 commit)

### Task 9.4: Delete 5 export shims (2 commits, 4+1)

- [ ] **Step 1**: 删 4 files (common + docx + epub + publish)
- [ ] **Step 2**: 删 1 file (publish_adapters)

### Task 9.5: Delete 6 volume shims (2 commits, 4+2)

### Task 9.6: Delete 9 onboarding shims (3 commits, 4+4+1)

### Task 9.7: Delete 10 content shims (3 commits, 4+4+2)

### Task 9.8: Final gate (1 commit)

- [ ] **Step 1: 加 test_infra_init_no_deferred_re_exports forbidden pattern check**

打开 `tests/test_infra_init_no_deferred_re_exports.py`,加新 forbidden pattern:

```python
FORBIDDEN_PATTERNS: tuple[tuple[str, str], ...] = (
    # ... existing 7 patterns ...
    ("infra.creator_X re-import",     r"^\s*from\s+infra\.creator_\w+\s+import"),
)
```

- [ ] **Step 2: 更新 `.lingwen/architecture.yml` 完全切到新位置**

打开 `.lingwen/architecture.yml`,移除 `infra/creator_X` 旧 references:

```yaml
  creator:
    path: packages/lingwen-creator/src/lingwen_creator/  # final
    exports: [
      # ... 全部 6 subdomains + shared symbols ...
    ]
```

- [ ] **Step 3: 全套 final verification gates**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest tests/ packages/lingwen-creator/tests/ packages/lingwen-shared/tests/ -q
cd apps/dashboard && pnpm vitest run --reporter=dot && pnpm exec vue-tsc --noEmit && pnpm exec knip && cd ../..
ruff check .
uv run python tooling/contracts/generate.py
uv run python tooling/contracts/zod_revalidate.py
```

Expected: 全 0 errors,baseline + ≥13 (v16.2.0) + ≥5 (per sub-phase) = ≥43 tests added

- [ ] **Step 4: Verify infra/creator_*.py = 0**

```bash
cd /home/ailearn/projects/LingWen
ls infra/creator_*.py 2>&1 | wc -l
# Expected: 0
```

- [ ] **Step 5: Commit final gate**

```bash
git add .lingwen/architecture.yml tests/test_infra_init_no_deferred_re_exports.py
git commit -m "chore(cleanup): Phase 126 v16.2.7 final — architecture.yml + lint check

Final state:
- .lingwen/architecture.yml: creator module 完全切到 packages/lingwen-creator/
- test_infra_init_no_deferred_re_exports.py: 加 infra.creator_X forbidden pattern (防止未来重新加 shim)

Verified:
- infra/creator_*.py = 0 files
- pytest ≥3768 + 5×6 sub-phase tests = ≥3768 + 30
- vitest ≥1731 + 35 composables = ≥1766
- vue-tsc 0 | ruff 0 | knip 0 | zod 0 drift"
```

### Task 9.9: v16.2 Handoff doc

- [ ] **Step 1: 写 `docs/superpowers/handoffs/2026-08-27-phase-126-v16-2-creator-subdomain-split-handoff.md`**

仿 v16.1 handoff 模板:
- §1 v16.2 完成的 8 件事
- §2 决策实现 (Q1..Q8)
- §3 Plan deviations
- §4 v16.2 副作用
- §5 Lessons
- §6 Carryover (v16.3+)
- §7 验证证据
- §8 新工具总结

- [ ] **Step 2: 更新 CLAUDE.md bump v16.1 → v16.2**

- [ ] **Step 3: Commit handoff + CLAUDE.md**

```bash
git add docs/superpowers/handoffs/2026-08-27-phase-126-v16-2-creator-subdomain-split-handoff.md CLAUDE.md
git commit -m "docs(phase-126): v16.2 handoff — creator 6-subdomain 拆分 闭环"
```

---

## 10. Verification Gates Summary

### 10.1 Per Sub-phase Gates (每次必过)

| Gate | 命令 | 期望 |
|---|---|---|
| uv sync | `uv sync` | 0 errors |
| Backend tests | `pytest tests/ packages/lingwen-creator/tests/ packages/lingwen-shared/tests/ -q` | baseline + ≥N per sub-phase |
| Frontend tests | `pnpm vitest run --reporter=dot` | 1731 + ≥N per sub-phase |
| ruff | `ruff check .` | 0 |
| vue-tsc | `pnpm exec vue-tsc --noEmit` | 0 |
| knip | `pnpm exec knip` | 0 (allowlist 跟 typed wrappers 同步) |
| codegen | `uv run python tooling/contracts/generate.py` | ts/creator.ts regenerated |
| zod reverse | `uv run python tooling/contracts/zod_revalidate.py` | 0 drift |

### 10.2 v16.2 Final Gate (v16.2.7 必过)

| Gate | 命令 | 期望 |
|---|---|---|
| import count | `grep -rl "from infra\.creator_" --include="*.py" apps/ packages/ \| wc -l` | 0 |
| shim file count | `ls infra/creator_*.py 2>&1 \| wc -l` | 0 |
| All gates above | (combined) | 全 0 |
| Handoff doc | `docs/superpowers/handoffs/2026-08-27-phase-126-*.md` exists | ✓ |

---

## 11. Carryover (to v16.3+)

| 任务 | 阶段 |
|---|---|
| import-linter enforcement(allowed_imports / forbidden_imports §2.4 in spec) | v16.4 |
| pydantic-to-typescript 库真实集成(可选,替换 hand-rolled converter) | v16.4 |
| StoragePort enforcement(DP-03) | v16.5 |
| yoyo-migrations | v16.5 |
| workspace members exist gate(v16.0 lesson) | v16.5 |
| **world + workspace 拆分 + application service 层提取** | v16.3 (与 v16.2 并行) |
| **LLMServicePort enforcement** | v16.4 |

---

## 12. Execution Notes

- **本项目不用 worktree** (per CLAUDE.md): 直接在 master commit
- **attribution disabled**: 不要加 `Co-Authored-By: Claude`
- **commit message**: 沿用 v16.0/v16.1 风格 — conventional commits + 中文 lessons section
- **DP-06 commit-level**: 每 commit ≤4 files,跨多个 commits 完成 sub-phase
- **shim pattern**: `# noqa: F403` inline (v15.7.1 lesson)
- **typed wrapper style**: 与 v16.1 T4 (world.ts / workspace.ts / quality.ts) 一致
- **knip allowlist**: 加 typed wrapper 时立即同步(v16.1 T4 lesson)

### 12.1 Python File Copy + Import Adjustment Rule (各 sub-phase 通用)

每个 sub-phase 移 Python 文件时,统一规则:

1. **Read** `infra/creator_<file>.py` 当前内容
2. **检查 import lines** (`grep "^from infra\." <file>`)
3. **如果 import target 是已迁出的 submodule**(v16.2.0 起为 shared.revision / shared.check;v16.2.1+ 起的其他 subdomains):
   - `from infra.creator_<X> import Y` → `from lingwen_creator.<subdomain>.<X> import Y`
   - 例: `from infra.creator_revision import CreatorDocConflictError` → `from lingwen_creator.shared.revision import CreatorDocConflictError`
4. **如果 import target 是 infra/ 其他(非 creator)**: 保留原路径(infra.persistence, infra.errors, infra.project_config, infra.llm_service 等)
5. **如果 import target 是 stdlib / 3rd party**: 保留
6. **如果该 file 内部还有相对 import** (e.g., `from ._helpers import ...`): 保留
7. **复制到新 path**:`packages/lingwen-creator/src/lingwen_creator/<subdomain>/<file>.py`,只改 module-level docstring 引用新 location
8. **不要改函数签名 / 内部逻辑 / 函数体** — 只改 import + docstring

### 12.2 Per-Subdomain Import Adjustment Examples

```python
# Settings/docs.py — 原 import 改:
# Before: from infra.creator_revision import CreatorDocConflictError
# After:  from lingwen_creator.shared.revision import CreatorDocConflictError

# Memory/annotations.py — 原 import 不变(只 import infra.persistence):
# Before: from infra.persistence import ...
# After:  from infra.persistence import ...  (no change)

# Onboarding/onboarding.py — 可能 import memory.annotations (v16.2.5+ 起):
# Before: from infra.creator_memory_annotations import upsert_memory_annotation
# After:  from lingwen_creator.memory.annotations import upsert_memory_annotation
```

---

**Plan complete and saved to `docs/superpowers/plans/2026-08-27-phase-126-v16-2-creator-subdomain-split-plan.md`.**

**Next step**: 选择执行模式 — subagent-driven (recommended) 或 inline executing-plans。
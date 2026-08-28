# Phase 126 v16.2.4 — Content Subdomain 拆分 + Onboarding T4 闭环 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 8 个 `infra/creator_*.py` (content subdomain) + 抽 `shared/mode.py` (修 spec violation + close forward-reference) + onboarding T4 composable refactor (drop 21 Creator-prefixed aliases) 全部迁到 `packages/lingwen-creator/src/lingwen_creator/content/` + `shared/mode.py`,shim re-export 保兼容,加 Content DTO + TS codegen + typed wrapper + URL contract tests。

**Architecture:** Strangler Fig migration,11 commits (T1 + T2a-d + T3-T8),每 commit ≤5 files (DP-06 严格),verbatim copy 纪律 (除 module-level docstring + intra-package imports)。Spec §2.4 依赖矩阵更新 (shared/onboarding/content 允许 `lingwen_creator.shared.mode`)。Onboarding forward-reference closure + infra/project_X migration 在 T1 + T5 同步完成。

**Tech Stack:** Python 3.12+ / Pydantic v2 / uv workspaces / FastAPI / Pydantic → TS hand-rolled codegen / Vue 3 + Pinia + TypeScript strict / Vitest / pytest / ruff / vue-tsc / knip / zod (reverse validation CI)

**Spec:** [`docs/superpowers/specs/2026-08-28-phase-126-v16-2-4-content-design.md`](../specs/2026-08-28-phase-126-v16-2-4-content-design.md) (用户已批准 2026-08-28, commit `3f21513a`)

---

## 0. Pre-flight 检查 (T1 开始前必过)

| 检查 | 命令 | 期望 |
|---|---|---|
| uv workspace 健康 | `uv sync` | 0 errors |
| v16.2.3 baseline tests | `/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-creator/tests/ packages/lingwen-shared/tests/ -q` | 24 + 50 + 16 + 13 = 103 passed |
| Frontend baseline | `cd apps/dashboard && pnpm vitest run --reporter=dot` | 1731+ passed, 22 pre-existing skip |
| Type check | `pnpm exec vue-tsc --noEmit` | 0 errors |
| Lint | `ruff check .` | 0 |
| Dead code | `pnpm exec knip` | 0 (2 advisory) |
| zod reverse | `/home/ailearn/miniconda3/bin/python tooling/contracts/zod_revalidate.py` | 0 drift |
| master HEAD | `git log --oneline -1` | `3f21513a docs(phase-126): v16.2.4 spec` |
| working tree clean | `git status` | nothing to commit |

**任何一项不通过就不开 v16.2.4**。

---

## 1. T1: shared/mode.py extraction + creator_mode shim + check.py + onboarding forward-ref close (4 files, 1 commit)

**目的**: 抽 `CreatorSettings + CREATION_MODE_* + settings_from_project_config` 到 `shared/mode.py`(cross-subdomain utility, per spec §2.4),`infra/creator_mode.py` 变 shim,修 `shared/check.py` spec violation,关 onboarding forward-reference。

### Task 1.1: 创建 `shared/mode.py` + shim + spec violation fix + onboarding close

**Files:**
- Create: `packages/lingwen-creator/src/lingwen_creator/shared/mode.py` (verbatim from `infra/creator_mode.py`, 108 lines)
- Create: `packages/lingwen-creator/tests/test_shared_mode.py` (≥4 tests)
- Modify: `infra/creator_mode.py` (变 1-line shim)
- Modify: `packages/lingwen-creator/src/lingwen_creator/shared/check.py` (12: `from infra.creator_mode import ...` → `from lingwen_creator.shared.mode import ...`)
- Modify: `packages/lingwen-creator/src/lingwen_creator/onboarding/onboarding.py` (8: `from infra.creator_mode import ...` → `from lingwen_creator.shared.mode import ...`,删 `# noqa: F401  # v16.2.4 will replace` 注释)

- [ ] **Step 1: 写 `test_shared_mode.py` failing test (RED)**

```python
# packages/lingwen-creator/tests/test_shared_mode.py
"""Phase 126 v16.2.4 T1: tests for shared/mode.py migrated utilities."""
from __future__ import annotations

from lingwen_creator.shared.mode import (
    CREATION_MODE_ADVANCE,
    CREATION_MODE_COMPANION,
    CREATION_MODE_STUDIO,
    CREATION_MODES,
    CreatorSettings,
    QUALITY_CREATOR_RELAXED,
    QUALITY_PROFILES,
    QUALITY_STUDIO_FULL,
    normalize_creation_mode,
    normalize_quality_profile,
    resolve_creator_settings,
    settings_from_project_config,
)


def test_creation_mode_constants() -> None:
    """CREATION_MODE_* constants frozen + non-empty."""
    assert CREATION_MODE_COMPANION == "companion"
    assert CREATION_MODE_ADVANCE == "advance"
    assert CREATION_MODE_STUDIO == "studio"
    assert CREATION_MODES == frozenset({"companion", "advance", "studio"})


def test_creator_settings_dataclass_fields() -> None:
    """CreatorSettings has all 8 fields (frozen dataclass)."""
    s = CreatorSettings(
        creation_mode=CREATION_MODE_STUDIO,
        quality_profile=QUALITY_STUDIO_FULL,
        fail_severity="P0",
        run_prose_calibration=True,
        run_llm_judge=True,
        run_golden_set=True,
        notify_per_chapter=True,
        advance_volume_summary=False,
    )
    assert s.creation_mode == CREATION_MODE_STUDIO
    assert s.run_llm_judge is True


def test_normalize_creation_mode_validation() -> None:
    """normalize_creation_mode rejects invalid mode."""
    import pytest
    with pytest.raises(ValueError):
        normalize_creation_mode("invalid_mode")


def test_settings_from_project_config_accepts_any() -> None:
    """settings_from_project_config accepts duck-typed ProjectConfig (Any)."""
    class FakeConfig:
        creation_mode = CREATION_MODE_ADVANCE
        quality_profile = None

    settings = settings_from_project_config(FakeConfig())
    assert settings.creation_mode == CREATION_MODE_ADVANCE
    assert settings.advance_volume_summary is True


def test_legacy_import_path_still_works() -> None:
    """Backwards compat: old `from infra.creator_mode import ...` works via shim."""
    from infra.creator_mode import CreatorSettings as LegacyCreatorSettings
    assert LegacyCreatorSettings is CreatorSettings
```

- [ ] **Step 2: 运行测试,验证 FAIL (RED)**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-creator/tests/test_shared_mode.py -v 2>&1 | tail -10
```

Expected: **5 FAILED** (ImportError on `lingwen_creator.shared.mode`)

- [ ] **Step 3: 读 `infra/creator_mode.py` 当前内容**

```bash
cd /home/ailearn/projects/LingWen
cat infra/creator_mode.py
```

记录完整 108 lines (含 `CREATION_MODE_*` + `QUALITY_*` + `CreatorSettings` + `normalize_creation_mode` + `normalize_quality_profile` + `resolve_creator_settings` + `settings_from_project_config`)。

- [ ] **Step 4: 创建 `packages/lingwen-creator/src/lingwen_creator/shared/mode.py`**

```python
# packages/lingwen-creator/src/lingwen_creator/shared/mode.py
"""Creator product line mode + quality profile resolution.

Migrated from infra/creator_mode.py in Phase 126 v16.2.4.
Used by:
  - shared.check.format_check_mode_banner (composition helper)
  - content.preferences (resolve_creator_settings for save)
  - onboarding.onboarding (validate creation_mode in wizard)
  - infra.project_config / project_init (YAML resolution)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CREATION_MODE_COMPANION = "companion"
CREATION_MODE_ADVANCE = "advance"
CREATION_MODE_STUDIO = "studio"

CREATION_MODES = frozenset(
    {CREATION_MODE_COMPANION, CREATION_MODE_ADVANCE, CREATION_MODE_STUDIO},
)

QUALITY_CREATOR_RELAXED = "creator_relaxed"
QUALITY_STUDIO_FULL = "studio_full"

QUALITY_PROFILES = frozenset({QUALITY_CREATOR_RELAXED, QUALITY_STUDIO_FULL})


@dataclass(frozen=True)
class CreatorSettings:
    """Resolved quality / notification defaults for a project."""

    creation_mode: str
    quality_profile: str
    fail_severity: str | None
    run_prose_calibration: bool
    run_llm_judge: bool
    run_golden_set: bool
    notify_per_chapter: bool
    advance_volume_summary: bool


def normalize_creation_mode(value: str | None) -> str:
    mode = (value or CREATION_MODE_STUDIO).strip().lower()
    if mode not in CREATION_MODES:
        raise ValueError(
            f"invalid creation_mode {value!r}; "
            f"expected one of {sorted(CREATION_MODES)}",
        )
    return mode


def normalize_quality_profile(value: str | None, *, creation_mode: str) -> str:
    if value:
        profile = value.strip().lower()
        if profile not in QUALITY_PROFILES:
            raise ValueError(
                f"invalid quality_profile {value!r}; "
                f"expected one of {sorted(QUALITY_PROFILES)}",
            )
        return profile
    if creation_mode == CREATION_MODE_STUDIO:
        return QUALITY_STUDIO_FULL
    return QUALITY_CREATOR_RELAXED


def resolve_creator_settings(
    *,
    creation_mode: str | None = None,
    quality_profile: str | None = None,
) -> CreatorSettings:
    """Map project.yaml creator fields to check / notify behavior."""
    mode = normalize_creation_mode(creation_mode)
    profile = normalize_quality_profile(quality_profile, creation_mode=mode)

    if mode == CREATION_MODE_COMPANION:
        return CreatorSettings(
            creation_mode=mode,
            quality_profile=profile,
            fail_severity="P0",
            run_prose_calibration=False,
            run_llm_judge=False,
            run_golden_set=False,
            notify_per_chapter=True,
            advance_volume_summary=False,
        )

    if mode == CREATION_MODE_ADVANCE:
        return CreatorSettings(
            creation_mode=mode,
            quality_profile=profile,
            fail_severity="P0",
            run_prose_calibration=False,
            run_llm_judge=False,
            run_golden_set=False,
            notify_per_chapter=False,
            advance_volume_summary=True,
        )

    return CreatorSettings(
        creation_mode=CREATION_MODE_STUDIO,
        quality_profile=QUALITY_STUDIO_FULL,
        fail_severity="P0",
        run_prose_calibration=True,
        run_llm_judge=True,
        run_golden_set=True,
        notify_per_chapter=True,
        advance_volume_summary=False,
    )


def settings_from_project_config(config: Any) -> CreatorSettings:
    return resolve_creator_settings(
        creation_mode=getattr(config, "creation_mode", CREATION_MODE_STUDIO),
        quality_profile=getattr(config, "quality_profile", None),
    )
```

- [ ] **Step 5: 验证 GREEN**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-creator/tests/test_shared_mode.py -v 2>&1 | tail -10
```

Expected: **5 PASSED**

- [ ] **Step 6: 把 `infra/creator_mode.py` 改为 shim**

读取 `infra/creator_mode.py` 当前 108 lines,**完全替换**为:

```python
# infra/creator_mode.py
"""Phase 126 v16.2.4 shim: re-export from lingwen_creator.shared.mode.

Migrated to packages/lingwen-creator/src/lingwen_creator/shared/mode.py.
This shim maintains backwards compat for consumers using:
    from infra.creator_mode import CreatorSettings, settings_from_project_config, ...

Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.shared.mode import *  # noqa: F401,F403
```

**重要**: `# noqa: F401` 防止 ruff 报 unused-import (因为 star-import 全部 re-export)。

- [ ] **Step 7: 修 `packages/lingwen-creator/src/lingwen_creator/shared/check.py` import**

打开 `packages/lingwen-creator/src/lingwen_creator/shared/check.py`,找到 line 12-15:

```python
from infra.creator_mode import (  # ← 改这个
    CREATION_MODE_STUDIO,
    CreatorSettings,
    settings_from_project_config,
)
```

替换为:

```python
from lingwen_creator.shared.mode import (
    CREATION_MODE_STUDIO,
    CreatorSettings,
    settings_from_project_config,
)
```

**验证 spec violation 修复**:
```bash
cd /home/ailearn/projects/LingWen
grep -nE "infra\.creator_mode" packages/lingwen-creator/src/lingwen_creator/shared/check.py
```
Expected: 无输出 (0 lines)

- [ ] **Step 8: 修 `packages/lingwen-creator/src/lingwen_creator/onboarding/onboarding.py` forward-reference**

打开文件,找到 line 8 周围:

```python
from infra.creator_mode import (  # noqa: F401  # v16.2.4 will replace
    CREATION_MODE_ADVANCE,
    CREATION_MODE_COMPANION,
    CREATION_MODE_STUDIO,
    settings_from_project_config,
)
```

替换为:

```python
from lingwen_creator.shared.mode import (
    CREATION_MODE_ADVANCE,
    CREATION_MODE_COMPANION,
    CREATION_MODE_STUDIO,
    settings_from_project_config,
)
```

**验证 forward-reference closure**:
```bash
cd /home/ailearn/projects/LingWen
grep -nE "infra\.creator_mode" packages/lingwen-creator/src/lingwen_creator/onboarding/onboarding.py
```
Expected: 无输出 (0 lines)

- [ ] **Step 9: 验证现有 tests 无 regression**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-creator/tests/ -v 2>&1 | tail -20
```

Expected: 24 (onboarding) + 5 (shared_mode 新增) + 其他 shared tests = ~32 passed

- [ ] **Step 10: ruff check**

```bash
cd /home/ailearn/projects/LingWen
ruff check packages/lingwen-creator/src/lingwen_creator/shared/mode.py \
          packages/lingwen-creator/src/lingwen_creator/shared/check.py \
          packages/lingwen-creator/src/lingwen_creator/onboarding/onboarding.py \
          infra/creator_mode.py 2>&1 | tail -5
```

Expected: `All checks passed!`

- [ ] **Step 11: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-creator/src/lingwen_creator/shared/mode.py \
        packages/lingwen-creator/src/lingwen_creator/shared/check.py \
        packages/lingwen-creator/src/lingwen_creator/onboarding/onboarding.py \
        packages/lingwen-creator/tests/test_shared_mode.py \
        infra/creator_mode.py
git commit -m "feat(creator): Phase 126 v16.2.4 T1 — shared/mode.py extraction + spec violation fix

抽 CreatorSettings + CREATION_MODE_* + settings_from_project_config 到
packages/lingwen-creator/src/lingwen_creator/shared/mode.py。Cross-subdomain
utility (per spec §2.4),被 shared.check / content.preferences / onboarding /
infra.project_X 使用。

迁移内容 (108 lines verbatim):
- shared/mode.py — CREATION_MODE_* + QUALITY_* + CreatorSettings + normalize +
  resolve + settings_from_project_config

修复 3 类 carryover:
1. infra/creator_mode.py → 1-line shim re-export from lingwen_creator.shared.mode
2. shared/check.py:12-15 — spec violation fix (infra.creator_mode import →
   lingwen_creator.shared.mode,符合 spec §2.4 'shared 不 import 其他 subdomain')
3. onboarding/onboarding.py:8 — forward-reference closure (删 # noqa: F401 注释
   + 改 import 为 lingwen_creator.shared.mode)

测试:
- packages/lingwen-creator/tests/test_shared_mode.py (5 tests, 含 legacy import
  backwards compat via shim)

Verified: pytest 32+ passed (含 onboarding 24 tests + shared_mode 5 tests),
ruff 0, no regression。

Lessons applied:
- v15.7.1: ruff F403 noqa 是 shim star-import 标准 (inline in shim)
- v16.2.3: spec §2 import list completeness check (spec violation 在 production
  code path 必须同 commit 修)
- v16.2.3: forward-reference closure (删 noqa: F401 注释 = 关闭 carryover)"
```

### Task 1.2: T1 验证门

- [ ] **Step 1: 全套 T1 gates**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-creator/tests/test_shared_mode.py -v 2>&1 | tail -3
ruff check packages/lingwen-creator/src/lingwen_creator/shared/mode.py infra/creator_mode.py 2>&1 | tail -3
grep -cE "infra\.creator_mode" packages/lingwen-creator/src/lingwen_creator/shared/check.py packages/lingwen-creator/src/lingwen_creator/onboarding/onboarding.py
```

Expected: 5 PASSED / All checks passed! / 0 (both files)

- [ ] **Step 2: Verify shared/mode.py imports work via both paths**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -c "from lingwen_creator.shared.mode import CreatorSettings, CREATION_MODE_STUDIO; print('OK')"
/home/ailearn/miniconda3/bin/python -c "from infra.creator_mode import CreatorSettings, CREATION_MODE_STUDIO; print('OK (shim)')"
```

Expected: 两个 `OK` 都成功输出

---

## 2. T2: content/ subdomain Python file migration (4 sub-commits, 16 files total)

**目的**: 迁 8 content files (verbatim copy) 到 `packages/lingwen-creator/src/lingwen_creator/content/`,其中 `mode.py` 是 shim (re-export from `shared/mode.py`)。8 个 `infra/creator_X.py` 变 shim。**DP-06 严格**: 每 commit ≤4 files,所以拆 T2a-d 4 commits。

### Task 2.1: T2a — agent.py + batch_history.py + 2 shims (4 files)

**Files:**
- Create: `packages/lingwen-creator/src/lingwen_creator/content/__init__.py` (empty placeholder,待 T2d 后填充 star-imports)
- Create: `packages/lingwen-creator/src/lingwen_creator/content/agent.py` (verbatim from `infra/creator_agent.py`, 598 lines)
- Create: `packages/lingwen-creator/src/lingwen_creator/content/batch_history.py` (verbatim from `infra/creator_batch_history.py`, 28 lines)
- Modify: `infra/creator_agent.py` → shim
- Modify: `infra/creator_batch_history.py` → shim

- [ ] **Step 1: 读 `infra/creator_agent.py` 与 `infra/creator_batch_history.py` 当前内容**

```bash
cd /home/ailearn/projects/LingWen
wc -l infra/creator_agent.py infra/creator_batch_history.py
```

记录 line count: agent.py 598 lines, batch_history.py 28 lines。

- [ ] **Step 2: 检查 `infra/creator_agent.py` 内部 imports**

```bash
cd /home/ailearn/projects/LingWen
grep -nE "^from infra\.|^from lingwen_creator" infra/creator_agent.py infra/creator_batch_history.py
```

记录所有 `from infra.X` / `from lingwen_creator.X` 引用。

**intra-package import 调整规则** (per plan §12.2):
- `from infra.creator_revision import CreatorDocConflictError` → `from lingwen_creator.shared.revision import CreatorDocConflictError` (target 已迁到 shared)
- `from infra.creator_volume_plan import load_volume_plan` → `from lingwen_creator.volume.plan import load_volume_plan` (target 已迁到 volume)
- `from infra.creator_settings_docs import creator_settings_docs_payload` → `from lingwen_creator.settings.docs import creator_settings_docs_payload`
- `from infra.creator_onboarding_X import ...` → `from lingwen_creator.onboarding.X import ...`
- `from infra.creator_mode import ...` → `from lingwen_creator.shared.mode import ...` (per T1)

**保留原路径**: `from infra.persistence / infra.llm_service / infra.errors / infra.project_config` 等

- [ ] **Step 3: 创建 `packages/lingwen-creator/src/lingwen_creator/content/__init__.py`**

```python
# packages/lingwen-creator/src/lingwen_creator/content/__init__.py
"""Phase 126 v16.2.4: content/ subdomain (creator main loop).

Bounded context: agent + dashboard + preferences + ui_profile + batch history +
models + logic check + mode (shim from shared.mode).

Submodules populated incrementally via T2a-d. Star-imports added in T2d final commit.
"""
```

- [ ] **Step 4: 创建 `packages/lingwen-creator/src/lingwen_creator/content/agent.py`**

完整复制 `infra/creator_agent.py` 内容(598 lines),调整内部 imports per Step 2 规则,改 module-level docstring 为:

```python
"""Creator agent plan + streaming — main loop orchestrator.

Migrated from infra/creator_agent.py in Phase 126 v16.2.4.
Uses:
  - infra.persistence (storage)
  - infra.llm_service (LLM calls)
  - lingwen_creator.shared.mode (resolve_creator_settings)
  - lingwen_creator.volume.plan (load_volume_plan for context)
"""
from __future__ import annotations
```

- [ ] **Step 5: 创建 `packages/lingwen-creator/src/lingwen_creator/content/batch_history.py`**

完整复制 `infra/creator_batch_history.py` 内容(28 lines),改 module-level docstring 为:

```python
"""Creator batch history helpers — failure reason labels for dashboard.

Migrated from infra/creator_batch_history.py in Phase 126 v16.2.4.
"""
from __future__ import annotations
```

(此文件 import 只 stdlib typing,无 infra import,所以 verbatim copy 无变化)

- [ ] **Step 6: 把 `infra/creator_agent.py` 改为 shim**

```python
# infra/creator_agent.py (after T2a)
"""Phase 126 v16.2.4 shim: re-export from lingwen_creator.content.agent.

Migrated to packages/lingwen-creator/src/lingwen_creator/content/agent.py.
Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.content.agent import *  # noqa: F401,F403
```

- [ ] **Step 7: 把 `infra/creator_batch_history.py` 改为 shim**

```python
# infra/creator_batch_history.py (after T2a)
"""Phase 126 v16.2.4 shim: re-export from lingwen_creator.content.batch_history.

Migrated to packages/lingwen-creator/src/lingwen_creator/content/batch_history.py.
Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.content.batch_history import *  # noqa: F401,F403
```

- [ ] **Step 8: 验证 imports work via both paths**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -c "from lingwen_creator.content.agent import run_creator_agent_plan; print('OK')"
/home/ailearn/miniconda3/bin/python -c "from infra.creator_agent import run_creator_agent_plan; print('OK (shim)')"
/home/ailearn/miniconda3/bin/python -c "from lingwen_creator.content.batch_history import enrich_batch_history_job; print('OK')"
/home/ailearn/miniconda3/bin/python -c "from infra.creator_batch_history import enrich_batch_history_job; print('OK (shim)')"
```

Expected: 4 个 `OK` 输出

- [ ] **Step 9: ruff check**

```bash
cd /home/ailearn/projects/LingWen
ruff check packages/lingwen-creator/src/lingwen_creator/content/ \
          infra/creator_agent.py infra/creator_batch_history.py 2>&1 | tail -5
```

Expected: `All checks passed!` (shim 文件 inline `# noqa: F403`)

- [ ] **Step 10: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-creator/src/lingwen_creator/content/__init__.py \
        packages/lingwen-creator/src/lingwen_creator/content/agent.py \
        packages/lingwen-creator/src/lingwen_creator/content/batch_history.py \
        infra/creator_agent.py \
        infra/creator_batch_history.py
git commit -m "feat(creator): Phase 126 v16.2.4 T2a — content/agent.py + batch_history.py migration

迁移 infra/creator_agent.py (598L) + infra/creator_batch_history.py (28L) verbatim
到 packages/lingwen-creator/src/lingwen_creator/content/。

agent.py intra-package import 调整 (per plan §12.2):
- infra.creator_revision → lingwen_creator.shared.revision
- infra.creator_volume_plan → lingwen_creator.volume.plan
- infra.creator_settings_docs → lingwen_creator.settings.docs
- infra.creator_mode → lingwen_creator.shared.mode (T1 已迁)
- infra.persistence / infra.llm_service / infra.errors / infra.project_config 保留原路径

Shim pattern:
- infra/creator_agent.py 变 1-line shim re-export from lingwen_creator.content.agent
- infra/creator_batch_history.py 同

agent.py 598L 单文件 verbatim copy (per spec §2.1 + brainstorming Q2 decision,
precedent: v16.2.3 digest_schedule.py 526L 单文件)。

Verified: 4 imports OK (new path + shim), ruff 0。

下一步 T2b — dashboard.py + logic_check.py + 2 shims。"
```

### Task 2.2: T2b — dashboard.py + logic_check.py + 2 shims (4 files)

**Files:**
- Create: `packages/lingwen-creator/src/lingwen_creator/content/dashboard.py` (verbatim from `infra/creator_dashboard.py`, 228 lines)
- Create: `packages/lingwen-creator/src/lingwen_creator/content/logic_check.py` (verbatim from `infra/creator_logic_check.py`, 114 lines)
- Modify: `infra/creator_dashboard.py` → shim
- Modify: `infra/creator_logic_check.py` → shim

- [ ] **Step 1: 读 source files + 检查 imports**

```bash
cd /home/ailearn/projects/LingWen
grep -nE "^from infra\." infra/creator_dashboard.py infra/creator_logic_check.py
```

intra-package imports 调整 per §12.2。

- [ ] **Step 2: 创建 `content/dashboard.py`**

复制 228 lines verbatim from `infra/creator_dashboard.py`,调整 imports。改 docstring 为:

```python
"""Creator dashboard — overview + chapter preview + save outline/body.

Migrated from infra/creator_dashboard.py in Phase 126 v16.2.4.
Uses:
  - infra.persistence (storage)
  - lingwen_creator.shared.mode (settings_from_project_config)
  - lingwen_creator.volume.plan (load_volume_plan for context)
"""
from __future__ import annotations
```

- [ ] **Step 3: 创建 `content/logic_check.py`**

复制 114 lines verbatim from `infra/creator_logic_check.py`,调整 imports。改 docstring 为:

```python
"""Creator logic check — narrative consistency validation.

Migrated from infra/creator_logic_check.py in Phase 126 v16.2.4.
"""
from __future__ import annotations
```

- [ ] **Step 4: `infra/creator_dashboard.py` 变 shim**

```python
"""Phase 126 v16.2.4 shim: re-export from lingwen_creator.content.dashboard.

Migrated to packages/lingwen-creator/src/lingwen_creator/content/dashboard.py.
Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.content.dashboard import *  # noqa: F401,F403
```

- [ ] **Step 5: `infra/creator_logic_check.py` 变 shim**

```python
"""Phase 126 v16.2.4 shim: re-export from lingwen_creator.content.logic_check.

Migrated to packages/lingwen-creator/src/lingwen_creator/content/logic_check.py.
Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.content.logic_check import *  # noqa: F401,F403
```

- [ ] **Step 6: 验证 + ruff + commit**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -c "from lingwen_creator.content.dashboard import creator_overview, creator_chapter_preview, save_creator_chapter_outline, save_creator_chapter_body; print('OK')"
/home/ailearn/miniconda3/bin/python -c "from lingwen_creator.content.logic_check import run_creator_logic_check; print('OK')"
ruff check packages/lingwen-creator/src/lingwen_creator/content/dashboard.py \
          packages/lingwen-creator/src/lingwen_creator/content/logic_check.py 2>&1 | tail -3
```

Expected: 2 `OK` 输出 + `All checks passed!`

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-creator/src/lingwen_creator/content/dashboard.py \
        packages/lingwen-creator/src/lingwen_creator/content/logic_check.py \
        infra/creator_dashboard.py \
        infra/creator_logic_check.py
git commit -m "feat(creator): Phase 126 v16.2.4 T2b — content/dashboard.py + logic_check.py migration

迁移 infra/creator_dashboard.py (228L) + infra/creator_logic_check.py (114L)
verbatim 到 packages/lingwen-creator/src/lingwen_creator/content/。

dashboard.py intra-package import 调整:
- infra.creator_volume_plan → lingwen_creator.volume.plan
- infra.creator_mode → lingwen_creator.shared.mode (T1)
- infra.persistence / infra.errors 保留

Verified: imports OK + ruff 0。"
```

### Task 2.3: T2c — mode.py (shim) + models.py + 2 shims (4 files)

**Files:**
- Create: `packages/lingwen-creator/src/lingwen_creator/content/mode.py` (SHIM re-export from `lingwen_creator.shared.mode`)
- Create: `packages/lingwen-creator/src/lingwen_creator/content/models.py` (verbatim from `infra/creator_models.py`, 61 lines)
- Modify: `infra/creator_mode.py` → (已 T1 变 shim, **本任务 NO-OP**)
- Modify: `infra/creator_models.py` → shim

**注意**: `infra/creator_mode.py` 在 T1 已变 shim re-export `shared/mode.py`。T2c 不再动它,但需要新创建 `content/mode.py` (per spec §2.1 + §2.3) 是 `shared/mode.py` 的第二个 shim layer。

- [ ] **Step 1: 创建 `content/mode.py` SHIM**

```python
# packages/lingwen-creator/src/lingwen_creator/content/mode.py
"""Phase 126 v16.2.4 shim: re-export from lingwen_creator.shared.mode.

Creator mode utilities (CreatorSettings + CREATION_MODE_* + settings_from_project_config)
live in lingwen_creator.shared.mode because they are cross-subdomain utilities
used by:
  - shared.check.format_check_mode_banner
  - onboarding.onboarding (wizard validation)
  - infra.project_config / project_init (YAML resolution)

This content/mode.py shim maintains backwards compat for spec §2.1
(content/mode.py canonical path) + any code using:
    from lingwen_creator.content.mode import CreatorSettings, ...

Will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.shared.mode import *  # noqa: F401,F403
```

- [ ] **Step 2: 读 `infra/creator_models.py` + 检查 imports**

```bash
cd /home/ailearn/projects/LingWen
grep -nE "^from infra\." infra/creator_models.py
wc -l infra/creator_models.py
```

- [ ] **Step 3: 创建 `content/models.py`**

复制 61 lines verbatim from `infra/creator_models.py`,调整 imports。改 docstring 为:

```python
"""Creator models — list available LLM models per provider.

Migrated from infra/creator_models.py in Phase 126 v16.2.4.
Uses:
  - infra.llm_service (provider list)
"""
from __future__ import annotations
```

- [ ] **Step 4: `infra/creator_models.py` 变 shim**

```python
"""Phase 126 v16.2.4 shim: re-export from lingwen_creator.content.models.

Migrated to packages/lingwen-creator/src/lingwen_creator/content/models.py.
Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.content.models import *  # noqa: F401,F403
```

- [ ] **Step 5: 验证 + ruff + commit**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -c "from lingwen_creator.content.mode import CreatorSettings; print('OK (shim → shared.mode)')"
/home/ailearn/miniconda3/bin/python -c "from lingwen_creator.content.models import list_creator_models_payload; print('OK')"
ruff check packages/lingwen-creator/src/lingwen_creator/content/mode.py \
          packages/lingwen-creator/src/lingwen_creator/content/models.py 2>&1 | tail -3
```

Expected: 2 `OK` + `All checks passed!`

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-creator/src/lingwen_creator/content/mode.py \
        packages/lingwen-creator/src/lingwen_creator/content/models.py \
        infra/creator_models.py
git commit -m "feat(creator): Phase 126 v16.2.4 T2c — content/mode.py shim + models.py migration

特殊 pattern: content/mode.py 是 shim 不是 verbatim copy (per spec §2.1 + §2.3
+ brainstorming Q1 decision)。CreatorSettings + CREATION_MODE_* 真实住在
shared/mode.py (T1 已迁)。content/mode.py re-export 提供 spec §2.1 规定的
content/mode.py canonical path。

infra/creator_mode.py 在 T1 已变 shim re-export shared/mode.py,本任务 NO-OP
(shim layer count 不变,符合 v16.2.3 handoff §5.1 lesson 2: 'shim count 不增加
when migrating existing files to shim form')。

models.py (61L) verbatim copy + intra-package import 调整。

Verified: imports OK + ruff 0。"
```

### Task 2.4: T2d — preferences.py + ui_profile.py + 2 shims + content/__init__.py star-imports + test_content.py (5 files)

**Files:**
- Create: `packages/lingwen-creator/src/lingwen_creator/content/preferences.py` (verbatim from `infra/creator_preferences.py`, 116 lines)
- Create: `packages/lingwen-creator/src/lingwen_creator/content/ui_profile.py` (verbatim from `infra/creator_ui_profile.py`, 327 lines)
- Modify: `packages/lingwen-creator/src/lingwen_creator/content/__init__.py` (T2a 空 placeholder → star-imports + test_content.py)
- Modify: `infra/creator_preferences.py` → shim
- Modify: `infra/creator_ui_profile.py` → shim
- Create: `packages/lingwen-creator/tests/test_content.py` (≥5 tests)

- [ ] **Step 1: 读 source files + 检查 imports**

```bash
cd /home/ailearn/projects/LingWen
grep -nE "^from infra\." infra/creator_preferences.py infra/creator_ui_profile.py
wc -l infra/creator_preferences.py infra/creator_ui_profile.py
```

intra-package imports 调整 per §12.2。

- [ ] **Step 2: 创建 `content/preferences.py`**

复制 116 lines verbatim from `infra/creator_preferences.py`,调整 imports (`infra.creator_mode` → `lingwen_creator.shared.mode`)。改 docstring 为:

```python
"""Creator preferences — creator-level config persistence.

Migrated from infra/creator_preferences.py in Phase 126 v16.2.4.
Uses:
  - infra.persistence (storage)
  - lingwen_creator.shared.mode (resolve_creator_settings)
"""
from __future__ import annotations
```

- [ ] **Step 3: 创建 `content/ui_profile.py`**

复制 327 lines verbatim from `infra/creator_ui_profile.py`,调整 imports。改 docstring 为:

```python
"""Creator UI profile — UI state resolution from settings.

Migrated from infra/creator_ui_profile.py in Phase 126 v16.2.4.
Uses:
  - infra.persistence (storage)
  - lingwen_creator.shared.mode (settings_from_project_config)
"""
from __future__ import annotations
```

- [ ] **Step 4: `infra/creator_preferences.py` 变 shim**

```python
"""Phase 126 v16.2.4 shim: re-export from lingwen_creator.content.preferences.

Migrated to packages/lingwen-creator/src/lingwen_creator/content/preferences.py.
Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.content.preferences import *  # noqa: F401,F403
```

- [ ] **Step 5: `infra/creator_ui_profile.py` 变 shim**

```python
"""Phase 126 v16.2.4 shim: re-export from lingwen_creator.content.ui_profile.

Migrated to packages/lingwen-creator/src/lingwen_creator/content/ui_profile.py.
Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.content.ui_profile import *  # noqa: F401,F403
```

- [ ] **Step 6: 填充 `content/__init__.py` star-imports**

```python
# packages/lingwen-creator/src/lingwen_creator/content/__init__.py
"""Phase 126 v16.2.4: content/ subdomain (creator main loop).

Bounded context: agent + dashboard + preferences + ui_profile + batch history +
models + logic check + mode (shim from shared.mode).

8 submodules:
  - agent            — run_creator_agent_plan + iter_creator_agent_plan_stream (598L, v16.2.4 largest)
  - batch_history    — enrich_batch_history_job (28L)
  - dashboard        — creator_overview + chapter preview + save outline/body (228L)
  - logic_check      — run_creator_logic_check (114L)
  - mode             — SHIM re-export from shared.mode (per spec §2.3)
  - models           — list_creator_models_payload (61L)
  - preferences      — creator_preferences_payload + load/save (116L)
  - ui_profile       — resolve_creator_ui_profile + ui_profile_from_project_config (327L)
"""
from lingwen_creator.content.agent import *  # noqa: F403
from lingwen_creator.content.batch_history import *  # noqa: F403
from lingwen_creator.content.dashboard import *  # noqa: F403
from lingwen_creator.content.logic_check import *  # noqa: F403
from lingwen_creator.content.mode import *  # noqa: F403
from lingwen_creator.content.models import *  # noqa: F403
from lingwen_creator.content.preferences import *  # noqa: F403
from lingwen_creator.content.ui_profile import *  # noqa: F403
```

- [ ] **Step 7: 写 `test_content.py` failing test (RED)**

```python
# packages/lingwen-creator/tests/test_content.py
"""Phase 126 v16.2.4: tests for content/ subdomain (8 modules + __init__ star-imports)."""
from __future__ import annotations

import pytest


def test_content_package_imports() -> None:
    """lingwen_creator.content package is importable."""
    import lingwen_creator.content
    assert lingwen_creator.content.__name__ == "lingwen_creator.content"


def test_content_star_imports_all_8_submodules() -> None:
    """content/__init__.py star-imports re-export from 8 submodules."""
    # Each submodule's primary function should be accessible via package root
    from lingwen_creator.content import (
        run_creator_agent_plan,
        enrich_batch_history_job,
        creator_overview,
        run_creator_logic_check,
        CreatorSettings,  # via mode.py shim → shared.mode
        list_creator_models_payload,
        creator_preferences_payload,
        resolve_creator_ui_profile,
    )
    assert callable(run_creator_agent_plan)
    assert callable(enrich_batch_history_job)
    assert callable(creator_overview)
    assert callable(run_creator_logic_check)
    assert callable(list_creator_models_payload)
    assert callable(creator_preferences_payload)
    assert callable(resolve_creator_ui_profile)


def test_content_mode_shim_re_exports_shared() -> None:
    """content/mode.py is a shim → lingwen_creator.shared.mode."""
    from lingwen_creator.content.mode import CreatorSettings as ContentCreatorSettings
    from lingwen_creator.shared.mode import CreatorSettings as SharedCreatorSettings
    assert ContentCreatorSettings is SharedCreatorSettings


def test_content_dashboard_chapter_preview_exists() -> None:
    """content.dashboard exports creator_chapter_preview."""
    from lingwen_creator.content.dashboard import (
        creator_chapter_preview,
        save_creator_chapter_outline,
        save_creator_chapter_body,
    )
    assert callable(creator_chapter_preview)
    assert callable(save_creator_chapter_outline)
    assert callable(save_creator_chapter_body)


def test_content_preferences_uses_shared_mode() -> None:
    """content.preferences imports from lingwen_creator.shared.mode (intra-package)."""
    # Indirect test: if preferences uses resolve_creator_settings correctly,
    # it should be importable and resolve a creation mode
    from lingwen_creator.content.preferences import creator_preferences_payload
    assert callable(creator_preferences_payload)


def test_legacy_import_paths_still_work() -> None:
    """Backwards compat: 8 infra.creator_X.py shims re-export."""
    from infra.creator_agent import run_creator_agent_plan as LegacyRun
    from infra.creator_batch_history import enrich_batch_history_job as LegacyEnrich
    from infra.creator_dashboard import creator_overview as LegacyOverview
    from infra.creator_logic_check import run_creator_logic_check as LegacyLogic
    from infra.creator_mode import CreatorSettings as LegacySettings
    from infra.creator_models import list_creator_models_payload as LegacyModels
    from infra.creator_preferences import creator_preferences_payload as LegacyPrefs
    from infra.creator_ui_profile import resolve_creator_ui_profile as LegacyUI

    from lingwen_creator.content.agent import run_creator_agent_plan
    from lingwen_creator.content.batch_history import enrich_batch_history_job
    from lingwen_creator.content.dashboard import creator_overview
    from lingwen_creator.content.logic_check import run_creator_logic_check
    from lingwen_creator.content.mode import CreatorSettings
    from lingwen_creator.content.models import list_creator_models_payload
    from lingwen_creator.content.preferences import creator_preferences_payload
    from lingwen_creator.content.ui_profile import resolve_creator_ui_profile

    assert LegacyRun is run_creator_agent_plan
    assert LegacyEnrich is enrich_batch_history_job
    assert LegacyOverview is creator_overview
    assert LegacyLogic is run_creator_logic_check
    assert LegacySettings is CreatorSettings
    assert LegacyModels is list_creator_models_payload
    assert LegacyPrefs is creator_preferences_payload
    assert LegacyUI is resolve_creator_ui_profile
```

- [ ] **Step 8: 验证 GREEN**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-creator/tests/test_content.py -v 2>&1 | tail -15
```

Expected: **6 PASSED**

- [ ] **Step 9: ruff check + commit**

```bash
cd /home/ailearn/projects/LingWen
ruff check packages/lingwen-creator/src/lingwen_creator/content/ \
          packages/lingwen-creator/tests/test_content.py \
          infra/creator_preferences.py \
          infra/creator_ui_profile.py 2>&1 | tail -3
```

Expected: `All checks passed!`

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-creator/src/lingwen_creator/content/preferences.py \
        packages/lingwen-creator/src/lingwen_creator/content/ui_profile.py \
        packages/lingwen-creator/src/lingwen_creator/content/__init__.py \
        packages/lingwen-creator/tests/test_content.py \
        infra/creator_preferences.py \
        infra/creator_ui_profile.py
git commit -m "feat(creator): Phase 126 v16.2.4 T2d — content/ completion + tests + __init__

完成 content/ subdomain 最后 2 files:
- content/preferences.py (116L verbatim) + intra-package import (infra.creator_mode → lingwen_creator.shared.mode)
- content/ui_profile.py (327L verbatim)

填充 content/__init__.py 8 star-imports (per v16.2.1..3 T1d precedent)。

测试:
- packages/lingwen-creator/tests/test_content.py (6 tests):
  - test_content_package_imports
  - test_content_star_imports_all_8_submodules
  - test_content_mode_shim_re_exports_shared (验证 content/mode.py shim 透明)
  - test_content_dashboard_chapter_preview_exists
  - test_content_preferences_uses_shared_mode
  - test_legacy_import_paths_still_work (8 shim backwards compat)

content/ 完成度: 8/8 modules + star-imports + 6 tests。

Verified: pytest 6 PASSED + ruff 0 + shim backwards compat all 8 paths OK。"
```

### Task 2.5: T2 验证门

- [ ] **Step 1: 全套 T2 gates**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-creator/tests/test_content.py -v 2>&1 | tail -10
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-creator/tests/ -q 2>&1 | tail -3
ruff check packages/lingwen-creator/src/lingwen_creator/content/ 2>&1 | tail -3
```

Expected: 6 PASSED / 30+ total passed (含 T1) / `All checks passed!`

- [ ] **Step 2: Verify content/ structure**

```bash
cd /home/ailearn/projects/LingWen
ls packages/lingwen-creator/src/lingwen_creator/content/
echo "---"
wc -l packages/lingwen-creator/src/lingwen_creator/content/*.py
```

Expected: 8 .py files (agent + batch_history + dashboard + logic_check + mode + models + preferences + ui_profile)

- [ ] **Step 3: Verify infra/ shim count for content files**

```bash
cd /home/ailearn/projects/LingWen
ls infra/creator_*.py | wc -l
grep -cE "from lingwen_creator\.content\.|from lingwen_creator\.shared\.mode" infra/creator_*.py | head -10
```

Expected: 36 shims (8 content + 其他已迁移, total 不变)

---

## 3. T3: Content DTOs (~15 Pydantic models) + TS codegen + tests (3 files)

**Files:**
- Modify: `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` (add Content section, ~15 Pydantic models)
- Auto-generated: `packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts` (run `tooling/contracts/generate.py`)
- Create: `packages/lingwen-shared/tests/test_content_dto.py` (≥10 tests)

### Task 3.1: 写 `test_content_dto.py` failing test (RED)

- [ ] **Step 1: 创建 `test_content_dto.py`**

```python
# packages/lingwen-shared/tests/test_content_dto.py
"""Phase 126 v16.2.4: tests for Content DTOs (15 Pydantic models)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from lingwen_shared.contracts.python.creator import (
    # Overview
    CreatorOverviewResponse,
    # Agent
    CreatorAgentPlanRequest,
    CreatorAgentPlanResponse,
    # Batch history
    CreatorBatchHistoryResponse,
    CreatorBatchHistoryExportRequest,
    # Preferences
    CreatorPreferencesResponse,
    CreatorPreferencesSaveRequest,
    # Models
    CreatorModelsResponse,
    # Logic check
    CreatorLogicCheckResponse,
    # Dashboard
    CreatorChapterPreview,
    CreatorOutlineSaveRequest,
    CreatorBodySaveRequest,
    # UI profile
    CreatorUiProfileState,
    CreatorUiProfileSaveRequest,
)


# --- Overview ---

def test_overview_response_minimal() -> None:
    ov = CreatorOverviewResponse(project_slug="proj-1", overview={})
    assert ov.project_slug == "proj-1"
    assert ov.overview == {}


# --- Agent ---

def test_agent_plan_request_requires_action_label() -> None:
    with pytest.raises(ValidationError):
        CreatorAgentPlanRequest(action_label="")


def test_agent_plan_response_has_results() -> None:
    resp = CreatorAgentPlanResponse(results=[])
    assert resp.results == []


# --- Batch history ---

def test_batch_history_response_empty() -> None:
    resp = CreatorBatchHistoryResponse(jobs=[])
    assert resp.jobs == []


def test_batch_history_export_request_format() -> None:
    req = CreatorBatchHistoryExportRequest(format="csv")
    assert req.format == "csv"


# --- Preferences ---

def test_preferences_response_has_creation_mode() -> None:
    resp = CreatorPreferencesResponse(creation_mode="studio", quality_profile="studio_full")
    assert resp.creation_mode == "studio"


def test_preferences_save_request_optional_mode() -> None:
    req = CreatorPreferencesSaveRequest()
    assert req.creation_mode is None


# --- Models ---

def test_models_response_has_providers() -> None:
    resp = CreatorModelsResponse(providers=[])
    assert resp.providers == []


# --- Logic check ---

def test_logic_check_response_has_violations() -> None:
    resp = CreatorLogicCheckResponse(violations=[])
    assert resp.violations == []


# --- Dashboard ---

def test_chapter_preview_minimal() -> None:
    prev = CreatorChapterPreview(chapter_id=42, project_slug="proj-1", outline="", body="")
    assert prev.chapter_id == 42


def test_outline_save_request_required_content() -> None:
    with pytest.raises(ValidationError):
        CreatorOutlineSaveRequest(chapter_id=1, outline="")


def test_body_save_request_optional_metadata() -> None:
    req = CreatorBodySaveRequest(chapter_id=1, body="text")
    assert req.metadata is None


# --- UI profile ---

def test_ui_profile_state_has_mode() -> None:
    state = CreatorUiProfileState(creation_mode="companion", quality_profile="creator_relaxed")
    assert state.creation_mode == "companion"


def test_ui_profile_save_request_validates_mode() -> None:
    with pytest.raises(ValidationError):
        CreatorUiProfileSaveRequest(creation_mode="invalid_mode")
```

- [ ] **Step 2: 验证 FAIL**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/test_content_dto.py -v 2>&1 | tail -20
```

Expected: **13 FAILED** (ImportError on new DTO classes)

### Task 3.2: 创建 Content DTOs in `creator.py`

- [ ] **Step 1: 读现有 `creator.py` 末尾**

```bash
cd /home/ailearn/projects/LingWen
tail -50 packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py
```

找到最后一个 `Onboarding*` DTO 的位置。

- [ ] **Step 2: 在 `creator.py` 末尾 append Content DTOs**

```python
# Append to packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py
# (在现有 Onboarding DTOs 之后)

# =====================================================================
# Content Subdomain (Phase 126 v16.2.4 T3)
# =====================================================================

class CreatorOverviewResponse(BaseModel):
    """Creator dashboard overview payload."""
    model_config = ConfigDict(extra="ignore")

    project_slug: str
    overview: dict[str, Any] = Field(default_factory=dict)
    last_updated: Optional[datetime] = None


class CreatorAgentPlanRequest(BaseModel):
    """Creator agent plan request (action label + optional context)."""
    model_config = ConfigDict(extra="ignore")

    action_label: str = Field(min_length=1)
    base_text: Optional[str] = None
    lens: Optional[str] = None
    provider_mode: Optional[str] = None


class CreatorAgentPlanResponse(BaseModel):
    """Creator agent plan response with results."""
    model_config = ConfigDict(extra="ignore")

    results: list[dict[str, Any]] = Field(default_factory=list)
    annotations: list[dict[str, Any]] = Field(default_factory=list)
    advice: Optional[str] = None


class CreatorBatchHistoryResponse(BaseModel):
    """Batch history jobs list response."""
    model_config = ConfigDict(extra="ignore")

    jobs: list[dict[str, Any]] = Field(default_factory=list)


class CreatorBatchHistoryExportRequest(BaseModel):
    """Batch history export request (format + filter)."""
    model_config = ConfigDict(extra="ignore")

    format: str  # "csv" | "json"
    start: Optional[datetime] = None
    end: Optional[datetime] = None


class CreatorPreferencesResponse(BaseModel):
    """Creator-level preferences payload."""
    model_config = ConfigDict(extra="ignore")

    creation_mode: str
    quality_profile: str
    fail_severity: Optional[str] = None
    run_prose_calibration: bool = False
    run_llm_judge: bool = False
    run_golden_set: bool = False
    notify_per_chapter: bool = False
    advance_volume_summary: bool = False


class CreatorPreferencesSaveRequest(BaseModel):
    """Creator preferences save request (all fields optional for partial save)."""
    model_config = ConfigDict(extra="ignore")

    creation_mode: Optional[str] = None
    quality_profile: Optional[str] = None
    fail_severity: Optional[str] = None
    run_prose_calibration: Optional[bool] = None
    run_llm_judge: Optional[bool] = None
    run_golden_set: Optional[bool] = None
    notify_per_chapter: Optional[bool] = None
    advance_volume_summary: Optional[bool] = None


class CreatorModelsResponse(BaseModel):
    """Available LLM models grouped by provider."""
    model_config = ConfigDict(extra="ignore")

    providers: list[dict[str, Any]] = Field(default_factory=list)


class CreatorLogicCheckResponse(BaseModel):
    """Creator logic check violations response."""
    model_config = ConfigDict(extra="ignore")

    violations: list[dict[str, Any]] = Field(default_factory=list)
    summary: Optional[str] = None


class CreatorChapterPreview(BaseModel):
    """Chapter preview with outline + body."""
    model_config = ConfigDict(extra="ignore")

    chapter_id: int
    project_slug: str
    outline: str
    body: str
    last_modified: Optional[datetime] = None


class CreatorOutlineSaveRequest(BaseModel):
    """Save chapter outline request (content required)."""
    model_config = ConfigDict(extra="ignore")

    chapter_id: int
    outline: str = Field(min_length=1)
    revision: Optional[str] = None


class CreatorBodySaveRequest(BaseModel):
    """Save chapter body request."""
    model_config = ConfigDict(extra="ignore")

    chapter_id: int
    body: str
    revision: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class CreatorUiProfileState(BaseModel):
    """UI profile resolved state."""
    model_config = ConfigDict(extra="ignore")

    creation_mode: str
    quality_profile: str
    advanced_visible: Optional[bool] = None
    wizard_visible: Optional[bool] = None
    dashboard_visible: Optional[bool] = None


class CreatorUiProfileSaveRequest(BaseModel):
    """UI profile save request."""
    model_config = ConfigDict(extra="ignore")

    creation_mode: Optional[str] = None
    quality_profile: Optional[str] = None
    advanced_visible: Optional[bool] = None
    wizard_visible: Optional[bool] = None
    dashboard_visible: Optional[bool] = None
```

**注意**: 顶部需要 import `Any` 和 `Field`,如果还没 import,加:
```python
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field
```

- [ ] **Step 3: 验证 GREEN**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/test_content_dto.py -v 2>&1 | tail -20
```

Expected: **13 PASSED**

### Task 3.3: TS codegen + zod reverse

- [ ] **Step 1: 跑 codegen**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python tooling/contracts/generate.py 2>&1 | tail -10
```

Expected: `WROTE .../ts/creator.ts (XXXXX bytes)` — 应该 +5343 bytes from onboarding precedent (per v16.2.3 handoff §7)

- [ ] **Step 2: 验证 TS codegen 输出**

```bash
cd /home/ailearn/projects/LingWen
grep -E "^export interface Creator(Overview|Agent|Batch|Preferences|Models|Logic|Chapter|Outline|Body|UiProfile)" packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts | head -20
```

Expected: 15 个 Content interface declarations

- [ ] **Step 3: 跑 zod reverse validation**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python tooling/contracts/zod_revalidate.py 2>&1 | tail -5
```

Expected: `zod reverse validation OK (no drift detected)` 或 `0 drift`

- [ ] **Step 4: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py \
        packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts \
        packages/lingwen-shared/tests/test_content_dto.py
git commit -m "feat(shared): Phase 126 v16.2.4 T3 — Content DTOs (15 Pydantic models) + TS codegen

新增 Content section 到 packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py
(15 Pydantic models per spec §3.7):

- CreatorOverviewResponse
- CreatorAgentPlanRequest + CreatorAgentPlanResponse
- CreatorBatchHistoryResponse + CreatorBatchHistoryExportRequest
- CreatorPreferencesResponse + CreatorPreferencesSaveRequest
- CreatorModelsResponse
- CreatorLogicCheckResponse
- CreatorChapterPreview + CreatorOutlineSaveRequest + CreatorBodySaveRequest
- CreatorUiProfileState + CreatorUiProfileSaveRequest

Pydantic v2 + ConfigDict(extra='ignore') forward-compat pattern (v16.1 lesson)。

Test-first TDD:
- packages/lingwen-shared/tests/test_content_dto.py (13 tests, RED → GREEN)
- 包含 validation tests (action_label required, outline required, etc.)

TS codegen:
- tooling/contracts/generate.py → creator.ts regenerated (15 new Content interfaces)
- zod reverse validation CI 验证 0 drift

Verified: pytest 13 PASSED + codegen OK + zod 0 drift。

下一步 T4 — content.ts typed wrapper。"
```

### Task 3.4: T3 验证门

- [ ] **Step 1: 全套 T3 gates**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/test_content_dto.py -v 2>&1 | tail -3
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/ -q 2>&1 | tail -3
/home/ailearn/miniconda3/bin/python tooling/contracts/zod_revalidate.py 2>&1 | tail -3
```

Expected: 13 PASSED / 50 + 13 = 63 total passed / `0 drift`

---

## 4. T4: content.ts typed wrapper + re-export + index.ts + knip + URL contract test (5 files)

**Files:**
- Create: `apps/dashboard/src/api/content.ts` (≥10 wrapper functions)
- Modify: `packages/dashboard-contracts/src/shared/creator.ts` (re-export list update,加 15 Content DTOs)
- Modify: `packages/dashboard-contracts/src/shared/index.ts` (re-export content per v16.2.1..3 T3 5-file precedent)
- Modify: `apps/dashboard/knip.json` (allowlist add content.ts + content DTOs)
- Create: `apps/dashboard/tests/unit/api/use-content-typed-wrapper.spec.ts` (URL contract regression lock, ≥10 tests)

### Task 4.1: 创建 `content.ts` typed wrapper

- [ ] **Step 1: 读现有 typed wrapper precedent (volume.ts)**

```bash
cd /home/ailearn/projects/LingWen
ls apps/dashboard/src/api/
head -50 apps/dashboard/src/api/volume.ts
```

了解 v16.2.1 T3 typed wrapper 风格 (无 zod,纯 typed fetch)。

- [ ] **Step 2: 创建 `apps/dashboard/src/api/content.ts`**

```typescript
// apps/dashboard/src/api/content.ts
// Phase 126 v16.2.4: typed wrapper for content endpoints.
// Replaces raw fetch in content composables. v16.2.1/2/3 lesson: no zod
// (zod is CI drift, not wrapper layer). URL contract regression lock in
// tests/unit/api/use-content-typed-wrapper.spec.ts.

import type {
  CreatorOverviewResponse,
  CreatorAgentPlanRequest,
  CreatorAgentPlanResponse,
  CreatorBatchHistoryResponse,
  CreatorBatchHistoryExportRequest,
  CreatorPreferencesResponse,
  CreatorPreferencesSaveRequest,
  CreatorModelsResponse,
  CreatorLogicCheckResponse,
  CreatorChapterPreview,
  CreatorOutlineSaveRequest,
  CreatorBodySaveRequest,
  CreatorUiProfileState,
  CreatorUiProfileSaveRequest,
} from '@lingwen/dashboard-contracts/shared/creator';

async function fetchTyped<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

// --- Overview + Models ---

export async function fetchCreatorOverview(
  project: string,
): Promise<CreatorOverviewResponse> {
  return fetchTyped<CreatorOverviewResponse>(
    `/creator/overview?project=${encodeURIComponent(project)}`,
  );
}

export async function fetchCreatorModels(): Promise<CreatorModelsResponse> {
  return fetchTyped<CreatorModelsResponse>('/creator/models');
}

// --- Preferences ---

export async function fetchCreatorPreferences(
  project: string,
): Promise<CreatorPreferencesResponse> {
  return fetchTyped<CreatorPreferencesResponse>(
    `/creator/preferences?project=${encodeURIComponent(project)}`,
  );
}

export async function saveCreatorPreferences(
  project: string,
  body: CreatorPreferencesSaveRequest,
): Promise<CreatorPreferencesResponse> {
  return fetchTyped<CreatorPreferencesResponse>(
    `/creator/preferences?project=${encodeURIComponent(project)}`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    },
  );
}

// --- UI Profile ---

export async function fetchCreatorUiProfile(
  project: string,
): Promise<CreatorUiProfileState> {
  return fetchTyped<CreatorUiProfileState>(
    `/creator/ui-profile?project=${encodeURIComponent(project)}`,
  );
}

export async function saveCreatorUiProfile(
  project: string,
  body: CreatorUiProfileSaveRequest,
): Promise<CreatorUiProfileState> {
  return fetchTyped<CreatorUiProfileState>(
    `/creator/ui-profile?project=${encodeURIComponent(project)}`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    },
  );
}

// --- Dashboard (Chapter Preview / Outline / Body) ---

export async function fetchCreatorChapterPreview(
  project: string,
  chapterId: number,
): Promise<CreatorChapterPreview> {
  return fetchTyped<CreatorChapterPreview>(
    `/creator/chapter-preview?project=${encodeURIComponent(project)}&chapter=${chapterId}`,
  );
}

export async function saveCreatorChapterOutline(
  project: string,
  body: CreatorOutlineSaveRequest,
): Promise<CreatorChapterPreview> {
  return fetchTyped<CreatorChapterPreview>(
    `/creator/chapter-outline?project=${encodeURIComponent(project)}`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    },
  );
}

export async function saveCreatorChapterBody(
  project: string,
  body: CreatorBodySaveRequest,
): Promise<CreatorChapterPreview> {
  return fetchTyped<CreatorChapterPreview>(
    `/creator/chapter-body?project=${encodeURIComponent(project)}`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    },
  );
}

// --- Agent Plan ---

export async function runCreatorAgentPlan(
  body: CreatorAgentPlanRequest,
): Promise<CreatorAgentPlanResponse> {
  return fetchTyped<CreatorAgentPlanResponse>('/creator/agent/plan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

// --- Batch History ---

export async function fetchCreatorBatchHistory(
  project: string,
): Promise<CreatorBatchHistoryResponse> {
  return fetchTyped<CreatorBatchHistoryResponse>(
    `/creator/batch-history?project=${encodeURIComponent(project)}`,
  );
}

export async function exportCreatorBatchHistory(
  project: string,
  body: CreatorBatchHistoryExportRequest,
): Promise<Blob> {
  const response = await fetch(
    `/creator/batch-history/export?project=${encodeURIComponent(project)}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    },
  );
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  return response.blob();
}

// --- Logic Check ---

export async function runCreatorLogicCheck(
  project: string,
): Promise<CreatorLogicCheckResponse> {
  return fetchTyped<CreatorLogicCheckResponse>(
    `/creator/logic-check?project=${encodeURIComponent(project)}`,
  );
}
```

**重要**: 所有 URL 不含 `/api/` prefix(per v16.2.1 §5.1 lesson 5: `BASE_URL` 已是 `/api`)。URL contract test 验证。

### Task 4.2: 更新 `dashboard-contracts/src/shared/creator.ts` re-export list

- [ ] **Step 1: 读当前 re-export list**

```bash
cd /home/ailearn/projects/LingWen
grep -E "^export type" packages/dashboard-contracts/src/shared/creator.ts | head -30
```

- [ ] **Step 2: Append Content DTOs to re-export list**

打开 `packages/dashboard-contracts/src/shared/creator.ts`,在末尾 append:

```typescript
// Phase 126 v16.2.4 T4: Content DTOs (added per v16.2.3 §5.1 lesson 3 —
// explicit re-export list fragility)
export type {
  CreatorOverviewResponse,
  CreatorAgentPlanRequest,
  CreatorAgentPlanResponse,
  CreatorBatchHistoryResponse,
  CreatorBatchHistoryExportRequest,
  CreatorPreferencesResponse,
  CreatorPreferencesSaveRequest,
  CreatorModelsResponse,
  CreatorLogicCheckResponse,
  CreatorChapterPreview,
  CreatorOutlineSaveRequest,
  CreatorBodySaveRequest,
  CreatorUiProfileState,
  CreatorUiProfileSaveRequest,
} from '../../../lingwen-shared/src/lingwen_shared/contracts/ts/creator';
```

### Task 4.3: 更新 `dashboard-contracts/src/shared/index.ts`

- [ ] **Step 1: 读 index.ts**

```bash
cd /home/ailearn/projects/LingWen
cat packages/dashboard-contracts/src/shared/index.ts
```

- [ ] **Step 2: Append content re-export**

```typescript
// Phase 126 v16.2.4 T4: re-export content creator DTOs
export * from './creator';
// (creator.ts already re-exports all 6 subdomains' DTOs)
```

### Task 4.4: 更新 `apps/dashboard/knip.json` allowlist

- [ ] **Step 1: 读 knip.json**

```bash
cd /home/ailearn/projects/LingWen
cat apps/dashboard/knip.json
```

- [ ] **Step 2: 添加 content.ts allowlist**

在 `ignore` 数组中 append:

```json
"apps/dashboard/src/api/content.ts",
"packages/dashboard-contracts/src/shared/creator.ts"
```

(如已存在则 skip — v16.2.1 T3 已经把 creator.ts 加过,只需加 content.ts)

### Task 4.5: 创建 URL contract regression lock test

- [ ] **Step 1: 创建 `tests/unit/api/use-content-typed-wrapper.spec.ts`**

```typescript
// apps/dashboard/tests/unit/api/use-content-typed-wrapper.spec.ts
// Phase 126 v16.2.4 T4: URL contract regression lock for content typed wrapper.
// Prevents accidental /api/ prefix or path drift (v16.2.1 §5.1 lesson 5).

import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  fetchCreatorOverview,
  fetchCreatorModels,
  fetchCreatorPreferences,
  saveCreatorPreferences,
  fetchCreatorUiProfile,
  saveCreatorUiProfile,
  fetchCreatorChapterPreview,
  saveCreatorChapterOutline,
  saveCreatorChapterBody,
  runCreatorAgentPlan,
  fetchCreatorBatchHistory,
  exportCreatorBatchHistory,
  runCreatorLogicCheck,
} from '@/api/content';

describe('content typed wrapper URL contract', () => {
  beforeEach(() => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({}),
      blob: async () => new Blob(),
    });
  });

  it('fetchCreatorOverview has NO /api/ prefix', async () => {
    await fetchCreatorOverview('proj-1');
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringMatching(/^\/creator\/overview/),
      expect.any(Object),
    );
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.not.stringMatching(/^\/api\//),
      expect.any(Object),
    );
  });

  it('fetchCreatorModels has NO /api/ prefix', async () => {
    await fetchCreatorModels();
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringMatching(/^\/creator\/models/),
      expect.any(Object),
    );
  });

  it('fetchCreatorPreferences has NO /api/ prefix', async () => {
    await fetchCreatorPreferences('proj-1');
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringMatching(/^\/creator\/preferences/),
      expect.any(Object),
    );
  });

  it('saveCreatorPreferences uses PUT method', async () => {
    await saveCreatorPreferences('proj-1', { creation_mode: 'studio' });
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringMatching(/^\/creator\/preferences/),
      expect.objectContaining({ method: 'PUT' }),
    );
  });

  it('fetchCreatorUiProfile has NO /api/ prefix', async () => {
    await fetchCreatorUiProfile('proj-1');
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringMatching(/^\/creator\/ui-profile/),
      expect.any(Object),
    );
  });

  it('fetchCreatorChapterPreview URL has chapter query', async () => {
    await fetchCreatorChapterPreview('proj-1', 42);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringMatching(/chapter=42/),
      expect.any(Object),
    );
  });

  it('saveCreatorChapterOutline uses PUT', async () => {
    await saveCreatorChapterOutline('proj-1', { chapter_id: 1, outline: 'text' });
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringMatching(/^\/creator\/chapter-outline/),
      expect.objectContaining({ method: 'PUT' }),
    );
  });

  it('saveCreatorChapterBody uses PUT', async () => {
    await saveCreatorChapterBody('proj-1', { chapter_id: 1, body: 'text' });
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringMatching(/^\/creator\/chapter-body/),
      expect.objectContaining({ method: 'PUT' }),
    );
  });

  it('runCreatorAgentPlan uses POST', async () => {
    await runCreatorAgentPlan({ action_label: 'plan' });
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringMatching(/^\/creator\/agent\/plan/),
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('fetchCreatorBatchHistory has NO /api/ prefix', async () => {
    await fetchCreatorBatchHistory('proj-1');
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringMatching(/^\/creator\/batch-history/),
      expect.any(Object),
    );
  });

  it('exportCreatorBatchHistory returns Blob', async () => {
    const blob = await exportCreatorBatchHistory('proj-1', { format: 'csv' });
    expect(blob).toBeInstanceOf(Blob);
  });

  it('runCreatorLogicCheck has NO /api/ prefix', async () => {
    await runCreatorLogicCheck('proj-1');
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringMatching(/^\/creator\/logic-check/),
      expect.any(Object),
    );
  });
});
```

- [ ] **Step 2: 跑测试,验证 GREEN**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm vitest run tests/unit/api/use-content-typed-wrapper.spec.ts --reporter=dot 2>&1 | tail -10
```

Expected: **12 PASSED**

### Task 4.6: vue-tsc + knip + commit

- [ ] **Step 1: vue-tsc 检查**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm exec vue-tsc --noEmit 2>&1 | tail -5
```

Expected: `0 errors`

- [ ] **Step 2: knip 检查**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm exec knip 2>&1 | tail -10
```

Expected: `0 errors` (allowlist 已加)

- [ ] **Step 3: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/api/content.ts \
        apps/dashboard/tests/unit/api/use-content-typed-wrapper.spec.ts \
        packages/dashboard-contracts/src/shared/creator.ts \
        packages/dashboard-contracts/src/shared/index.ts \
        apps/dashboard/knip.json
git commit -m "feat(dashboard): Phase 126 v16.2.4 T4 — content typed wrapper + re-export + URL contract

新增 typed wrapper apps/dashboard/src/api/content.ts (13 functions, NO zod per
v16.2.1 §5.1 lesson 4):
- fetchCreatorOverview / fetchCreatorModels
- fetchCreatorPreferences / saveCreatorPreferences
- fetchCreatorUiProfile / saveCreatorUiProfile
- fetchCreatorChapterPreview / saveCreatorChapterOutline / saveCreatorChapterBody
- runCreatorAgentPlan
- fetchCreatorBatchHistory / exportCreatorBatchHistory
- runCreatorLogicCheck

5 files per DP-06 precedent (mirrors v16.2.1 T3 + v16.2.2 T3 + v16.2.3 T3):
1. content.ts (NEW)
2. dashboard-contracts/src/shared/creator.ts (re-export 15 Content DTOs)
3. dashboard-contracts/src/shared/index.ts (re-export content)
4. apps/dashboard/knip.json (allowlist content.ts)
5. tests/unit/api/use-content-typed-wrapper.spec.ts (12 URL contract tests)

URL contract regression lock (v16.2.1 §5.1 lesson 5):
- 12 tests verify NO /api/ prefix on all wrapper URLs
- PUT/POST method assertions
- Blob return type for exportCreatorBatchHistory

Verified: vue-tsc 0 + knip 0 + vitest 12 PASSED。

下一步 T5 — routes imports migration。"
```

---

## 5. T5: routes imports migration + infra/project_X.py cleanup (3 files)

**Files:**
- Modify: `apps/studio_api/routes/creator_core.py` (~12 content endpoint lazy imports migrated)
- Modify: `infra/project_init.py` (line 10: `from infra.creator_mode import ...` → `from lingwen_creator.shared.mode import ...`)
- Modify: `infra/project_config.py` (line 11: same migration)

### Task 5.1: grep content imports in creator_core.py

- [ ] **Step 1: 列出所有 content-related imports**

```bash
cd /home/ailearn/projects/LingWen
grep -nE "from infra\.creator_(agent|dashboard|logic_check|batch_history|models|preferences|ui_profile|mode)" apps/studio_api/routes/creator_core.py
```

Expected output (12 imports based on actual file inspection):
```
69: from infra.creator_dashboard import creator_overview
76: from infra.creator_dashboard import creator_overview
88: from infra.creator_logic_check import run_creator_logic_check
101: from infra.creator_agent import run_creator_agent_plan
126: from infra.creator_agent import iter_creator_agent_plan_stream
158: from infra.creator_batch_history import enrich_batch_history_job
167: from infra.creator_batch_history import enrich_batch_history_job
194: from infra.creator_preferences import creator_preferences_payload
203: from infra.creator_preferences import ... (multiple)
373: from infra.creator_dashboard import creator_chapter_preview
396: from infra.creator_dashboard import save_creator_chapter_outline
414: from infra.creator_dashboard import save_creator_chapter_body
```

(实际 line numbers 以 grep 结果为准)

### Task 5.2: 替换 imports

- [ ] **Step 1: 对每一处 import,做 find/replace**

```
from infra.creator_dashboard import ... → from lingwen_creator.content.dashboard import ...
from infra.creator_logic_check import ... → from lingwen_creator.content.logic_check import ...
from infra.creator_agent import ... → from lingwen_creator.content.agent import ...
from infra.creator_batch_history import ... → from lingwen_creator.content.batch_history import ...
from infra.creator_models import ... → from lingwen_creator.content.models import ...
from infra.creator_preferences import ... → from lingwen_creator.content.preferences import ...
from infra.creator_ui_profile import ... → from lingwen_creator.content.ui_profile import ...
from infra.creator_mode import ... → from lingwen_creator.shared.mode import ...  (per T1)
```

**注意**: `infra.creator_mode` 不在 creator_core.py 中(per Step 1 grep),所以不需要管。

- [ ] **Step 2: 验证 0 stale imports**

```bash
cd /home/ailearn/projects/LingWen
grep -cE "infra\.creator_(agent|dashboard|logic_check|batch_history|models|preferences|ui_profile)" apps/studio_api/routes/creator_core.py
```

Expected: `0`

### Task 5.3: 修改 `infra/project_init.py` + `infra/project_config.py`

- [ ] **Step 1: 读 import lines**

```bash
cd /home/ailearn/projects/LingWen
sed -n '8,15p' infra/project_init.py
echo "==="
sed -n '9,16p' infra/project_config.py
```

- [ ] **Step 2: 替换 imports**

`infra/project_init.py:10`:
```python
# Before:
from infra.creator_mode import (
    CREATION_MODE_COMPANION,
    CREATION_MODE_STUDIO,
    CreatorSettings,
)

# After:
from lingwen_creator.shared.mode import (
    CREATION_MODE_COMPANION,
    CREATION_MODE_STUDIO,
    CreatorSettings,
)
```

`infra/project_config.py:11`:
```python
# Before:
from infra.creator_mode import (
    CREATION_MODE_COMPANION,
    CREATION_MODE_STUDIO,
    CreatorSettings,
    normalize_creation_mode,
)

# After:
from lingwen_creator.shared.mode import (
    CREATION_MODE_COMPANION,
    CREATION_MODE_STUDIO,
    CreatorSettings,
    normalize_creation_mode,
)
```

- [ ] **Step 3: 验证 0 stale imports in infra/**

```bash
cd /home/ailearn/projects/LingWen
grep -cE "from infra\.creator_mode" infra/project_init.py infra/project_config.py
```

Expected: `0` (both files)

### Task 5.4: pytest + ruff + commit

- [ ] **Step 1: 跑相关 tests**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest tests/infra/test_project_init.py tests/infra/test_project_config.py tests/apps/studio_api/test_creator_routes.py -q 2>&1 | tail -10
```

Expected: 全 PASSED (no regression)

- [ ] **Step 2: ruff check**

```bash
cd /home/ailearn/projects/LingWen
ruff check apps/studio_api/routes/creator_core.py \
          infra/project_init.py \
          infra/project_config.py 2>&1 | tail -3
```

Expected: `All checks passed!`

- [ ] **Step 3: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/studio_api/routes/creator_core.py \
        infra/project_init.py \
        infra/project_config.py
git commit -m "feat(routes): Phase 126 v16.2.4 T5 — content routes + project_X migration

迁移 ~12 content endpoint lazy imports 从 infra.creator_X → lingwen_creator.content.X:
- creator_dashboard → content.dashboard (overview + chapter preview + outline + body)
- creator_logic_check → content.logic_check
- creator_agent → content.agent (plan + streaming)
- creator_batch_history → content.batch_history
- creator_preferences → content.preferences

Per plan §12.1 rule 4 + §12.2 intra-package import pattern。

同步修复 infra/project_init.py + infra/project_config.py:
- 2 imports of infra.creator_mode → lingwen_creator.shared.mode (per T1)

Verified: pytest routes/project tests PASSED + ruff 0 + 0 stale infra imports。

下一步 T6 — onboarding T4 composables refactor。"
```

---

## 6. T6: onboarding T4 composables refactor + delete api/onboarding.js shim (5 files)

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorOnboarding.js` (refactor 21 Creator-prefixed aliases → new typed wrapper names)
- Modify: `apps/dashboard/src/composables/useCreatorOnboarding/useWizardSteps.ts`
- Modify: `apps/dashboard/src/composables/useCreatorOnboarding/useOnboardingProgress.ts`
- Modify: `apps/dashboard/src/composables/useCreatorOnboarding/useOnboardingNotifications.ts`
- Delete: `apps/dashboard/src/api/onboarding.js`

### Task 6.1: grep legacy aliases in composables

- [ ] **Step 1: 列出所有 Creator-prefixed aliases 使用情况**

```bash
cd /home/ailearn/projects/LingWen
grep -nE "fetchCreatorOnboarding|saveCreatorOnboarding|ackCreatorOnboarding|fetchCreatorDiffCollab|saveCreatorDiffCollab|fetchCreatorOnboardingNotification|fetchCreatorOnboardingDigest|saveCreatorOnboardingDigest|fetchCreatorOnboardingWebhook|saveCreatorOnboardingWebhook|fetchCreatorOnboardingEmail|saveCreatorOnboardingEmail|applyCreatorOnboardingShare|saveCreatorWizardPanelCollapsed|dismissCreatorWizardPanel|replayCreatorOnboardingDigest|fetchCreatorOnboardingDigestDeadLetter|processCreatorOnboardingDigestRetries|dispatchCreatorOnboardingDigest" apps/dashboard/src/composables/useCreatorOnboarding*.{js,ts} 2>&1 | head -50
```

记录所有 alias → new name 映射 (per `apps/dashboard/src/api/onboarding.js` shim):

| Legacy alias | New typed wrapper name |
|---|---|
| `fetchCreatorOnboarding` | `fetchOnboardingWizard` |
| `saveCreatorOnboardingProgress` | `saveOnboardingProgress` |
| `saveCreatorOnboardingNotes` | `saveOnboardingNotes` |
| `applyCreatorOnboardingShare` | `applyWizardShareDone` |
| `saveCreatorWizardPanelCollapsed` | `collapseOnboardingWizard` |
| `dismissCreatorWizardPanel` | `dismissOnboardingWizard` |
| `fetchCreatorDiffCollabNotes` | `fetchDiffCollabNotes` |
| `saveCreatorDiffCollabNotes` | `saveDiffCollabNotes` |
| `fetchCreatorOnboardingNotifications` | `fetchOnboardingNotifications` |
| `ackCreatorOnboardingNotifications` | `ackOnboardingNotifications` |
| `fetchCreatorOnboardingNotificationDigest` | `buildOnboardingNotificationDigest` |
| `fetchCreatorOnboardingDigestSchedule` | `fetchDigestSchedule` |
| `saveCreatorOnboardingDigestSchedule` | `saveDigestSchedule` |
| `fetchCreatorOnboardingDigestDeadLetter` | `fetchDigestDeadLetter` |
| `replayCreatorOnboardingDigestDeadLetter` | `replayDigestDeadLetter` |
| `fetchCreatorOnboardingDigestStats` | `fetchDigestStats` |
| `fetchCreatorOnboardingDigestRetryQueue` | `fetchDigestRetryQueue` |
| `processCreatorOnboardingDigestRetries` | `processDigestRetries` |
| `dispatchCreatorOnboardingDigest` | `dispatchDigestNow` |
| `fetchCreatorOnboardingWebhook` | `fetchOnboardingWebhookConfig` |
| `saveCreatorOnboardingWebhook` | `saveOnboardingWebhookConfig` |
| `fetchCreatorOnboardingEmail` | `fetchOnboardingEmailConfig` |
| `saveCreatorOnboardingEmail` | `saveOnboardingEmailConfig` |

(21 个 aliases 总数,per v16.2.3 handoff §5.1 lesson 1)

### Task 6.2: refactor composables

- [ ] **Step 1: 改 `useCreatorOnboarding.js`**

打开文件,找到 import section:

```javascript
// Before (v16.2.3 T4-partial):
import { fetchCreatorOnboarding, saveCreatorOnboardingProgress, ... } from '@/api/onboarding.js';
// (or via api/creator.js → api/onboarding.js shim)
```

替换为:

```javascript
// After (v16.2.4 T6):
import {
  fetchOnboardingWizard,
  saveOnboardingProgress,
  saveOnboardingNotes,
  applyWizardShareDone,
  collapseOnboardingWizard,
  dismissOnboardingWizard,
  fetchDiffCollabNotes,
  saveDiffCollabNotes,
  fetchOnboardingNotifications,
  ackOnboardingNotifications,
  buildOnboardingNotificationDigest,
  fetchDigestSchedule,
  saveDigestSchedule,
  fetchDigestDeadLetter,
  replayDigestDeadLetter,
  fetchDigestStats,
  fetchDigestRetryQueue,
  processDigestRetries,
  dispatchDigestNow,
  fetchOnboardingWebhookConfig,
  saveOnboardingWebhookConfig,
  fetchOnboardingEmailConfig,
  saveOnboardingEmailConfig,
} from '@/api/onboarding';
```

(注意: import from `@/api/onboarding` 不带 `.js` — 走 typed wrapper directly)

然后,在 file body 中 find/replace 每个 legacy alias → new name (per Step 1 mapping)。

- [ ] **Step 2: 改 `useCreatorOnboarding/useWizardSteps.ts`**

同样 find/replace legacy aliases → new names。改 import from `@/api/onboarding.js` → `@/api/onboarding`。

- [ ] **Step 3: 改 `useCreatorOnboarding/useOnboardingProgress.ts`**

同上。

- [ ] **Step 4: 改 `useCreatorOnboarding/useOnboardingNotifications.ts`**

同上。

### Task 6.3: 跑 composables tests + 删除 shim

- [ ] **Step 1: 跑 onboarding composable tests**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm vitest run tests/unit/composables/use-creator-onboarding.spec.ts tests/unit/composables/useCreatorOnboarding --reporter=dot 2>&1 | tail -10
```

Expected: 全 PASSED (no regression)

- [ ] **Step 2: 验证 legacy aliases 不再被引用**

```bash
cd /home/ailearn/projects/LingWen
grep -rE "fetchCreatorOnboarding|saveCreatorOnboarding|ackCreatorOnboarding|fetchCreatorDiffCollab|saveCreatorDiffCollab|fetchCreatorOnboardingNotification|fetchCreatorOnboardingDigest|saveCreatorOnboardingDigest|fetchCreatorOnboardingWebhook|saveCreatorOnboardingWebhook|fetchCreatorOnboardingEmail|saveCreatorOnboardingEmail|applyCreatorOnboardingShare|saveCreatorWizardPanelCollapsed|dismissCreatorWizardPanel|replayCreatorOnboardingDigest|fetchCreatorOnboardingDigestDeadLetter|processCreatorOnboardingDigestRetries|dispatchCreatorOnboardingDigest" apps/dashboard/src/composables/ 2>&1 | wc -l
```

Expected: `0` (所有 21 aliases 都已 refactor)

- [ ] **Step 3: 删除 `apps/dashboard/src/api/onboarding.js` shim**

```bash
cd /home/ailearn/projects/LingWen
git rm apps/dashboard/src/api/onboarding.js 2>&1
```

- [ ] **Step 4: vue-tsc + vitest verify**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm exec vue-tsc --noEmit 2>&1 | tail -5
pnpm vitest run --reporter=dot 2>&1 | tail -5
```

Expected: `0 errors` / 1731+ passed (no regression)

### Task 6.4: Commit

- [ ] **Step 1: Commit T6**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/composables/useCreatorOnboarding.js \
        apps/dashboard/src/composables/useCreatorOnboarding/ \
        -A apps/dashboard/src/api/onboarding.js
# (实际 git rm 已 stage 删除)
git status 2>&1 | head -15
git commit -m "feat(dashboard): Phase 126 v16.2.4 T6 — onboarding T4 composables refactor + delete shim

Refactor 5 onboarding composable files 用新 typed wrapper names (drop 21
Creator-prefixed aliases):
- useCreatorOnboarding.js
- useCreatorOnboarding/useWizardSteps.ts
- useCreatorOnboarding/useOnboardingProgress.ts
- useCreatorOnboarding/useOnboardingNotifications.ts
- (useCreatorOnboarding/index.ts — pure re-export,无 legacy aliases 可改)

Alias → new name mapping (21 个 per v16.2.3 handoff §5.1 lesson 1):
- fetchCreatorOnboarding → fetchOnboardingWizard
- saveCreatorOnboardingProgress → saveOnboardingProgress
- ... (其余 19 个,见 plan §6.1 table)

Import path:
- 从 '@/api/onboarding.js' (v16.2.3 shim) 改为 '@/api/onboarding' (typed wrapper directly)

删除 apps/dashboard/src/api/onboarding.js shim (obsolete after composables refactor)。

验证:
- 0 legacy aliases remaining (grep verify)
- vitest composable tests PASSED (no regression)
- vue-tsc 0 errors

v16.2.3 T4-partial carryover closed。T6 是 onboarding composables 真正完成 typed
wrapper 切换的 commit。

下一步 T7 — cross-subdomain cleanup。"
```

---

## 7. T7: cross-subdomain cleanup (1-4 files, conditional)

**Files (TBD by grep):**
- 可能: `packages/lingwen-creator/src/lingwen_creator/{volume,onboarding,settings,shared}/*.py` 有 stale `infra.creator_X` imports (volume/templates.py 已知需要)
- 可能: `apps/studio_api/routes/{creator_volume,creator_onboarding,creator_settings}.py` 有 stale `infra.creator_*` imports

### Task 7.1: grep + migrate stale imports

- [ ] **Step 1: 列出所有 stale infra.creator_X imports in 已迁 subdomains**

```bash
cd /home/ailearn/projects/LingWen
grep -rE "from infra\.creator_" packages/lingwen-creator/src/lingwen_creator/{volume,onboarding,settings,shared}/ 2>&1 | head -30
echo "==="
grep -rE "from infra\.creator_" apps/studio_api/routes/{creator_volume,creator_onboarding,creator_settings}.py 2>&1 | head -30
```

记录所有 findings。

- [ ] **Step 2: per finding,migrate to new path (per plan §12.2)**

例如 `volume/templates.py` 可能 import `infra.creator_settings_docs` → `lingwen_creator.settings.docs` (per v16.2.2 handoff §6 carryover)。

- [ ] **Step 3: 验证 0 stale imports**

```bash
cd /home/ailearn/projects/LingWen
grep -rE "from infra\.creator_" packages/lingwen-creator/src/lingwen_creator/{volume,onboarding,settings,shared}/ 2>&1 | wc -l
grep -rE "from infra\.creator_" apps/studio_api/routes/{creator_volume,creator_onboarding,creator_settings}.py 2>&1 | wc -l
```

Expected: `0` (both files = 0)

### Task 7.2: pytest + ruff + commit (conditional)

- [ ] **Step 1: 跑相关 tests**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-creator/tests/ packages/lingwen-shared/tests/ tests/infra/ -q 2>&1 | tail -3
```

Expected: 全 PASSED

- [ ] **Step 2: ruff check + commit (如有 changes)**

```bash
cd /home/ailearn/projects/LingWen
ruff check packages/lingwen-creator/src/lingwen_creator/{volume,onboarding,settings,shared}/ 2>&1 | tail -3
```

如有 changes:
```bash
git add <modified_files>
git commit -m "refactor: Phase 126 v16.2.4 T7 — cross-subdomain cleanup (volume/onboarding/settings → content)

清理 volume/onboarding/settings/shared 中的 stale infra.creator_X imports:
- [列出 per-file changes]

Grep verify 0 stale imports remaining。

Per v16.2.1 T6 + v16.2.2 §6 + v16.2.3 T6 precedent。

Verified: pytest PASSED + ruff 0。"
```

**如果 grep findings 为 0,skip T7 commit**,继续 T8。

---

## 8. T8: validation gates + handoff doc (3 files)

**Files:**
- Create: `docs/superpowers/handoffs/2026-08-28-phase-126-v16-2-4-content-handoff.md` (10 sections per v16.2.3 template)
- Modify: `CLAUDE.md` (bump v16.2.3 → v16.2.4)
- Modify: `.lingwen/architecture.yml` (creator exports list add Content + Mode symbols)
- Modify: `.lingwen/migration_log.yml` (v16.2.4 entry)

### Task 8.1: 全套验证门

- [ ] **Step 1: Backend tests**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-creator/tests/test_content.py packages/lingwen-creator/tests/test_shared_mode.py -v 2>&1 | tail -10
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/test_content_dto.py -v 2>&1 | tail -5
/home/ailearn/miniconda3/bin/python -m pytest tests/infra/test_creator_*.py -q 2>&1 | tail -3
```

Expected: 6 + 5 + 13 + 16 + baseline PASSED

- [ ] **Step 2: Frontend tests**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm vitest run tests/unit/api/use-content-typed-wrapper.spec.ts --reporter=dot 2>&1 | tail -5
pnpm vitest run --reporter=dot 2>&1 | tail -5
```

Expected: 12 + 1731+ passed (22 pre-existing skip acceptable)

- [ ] **Step 3: ruff + vue-tsc + knip + zod + codegen**

```bash
cd /home/ailearn/projects/LingWen
ruff check . 2>&1 | tail -3
cd apps/dashboard && pnpm exec vue-tsc --noEmit 2>&1 | tail -3 && pnpm exec knip 2>&1 | tail -3 && cd ../..
/home/ailearn/miniconda3/bin/python tooling/contracts/zod_revalidate.py 2>&1 | tail -3
/home/ailearn/miniconda3/bin/python tooling/contracts/generate.py 2>&1 | tail -3
```

Expected: 全 0 errors / 0 drift

- [ ] **Step 4: Final state verify**

```bash
cd /home/ailearn/projects/LingWen
echo "=== content/ files ==="
ls packages/lingwen-creator/src/lingwen_creator/content/
echo "=== shared/ files ==="
ls packages/lingwen-creator/src/lingwen_creator/shared/
echo "=== shim count ==="
ls infra/creator_*.py | wc -l
echo "=== git log ==="
git log --oneline -12
```

Expected: 8 content files / 3 shared files (mode + revision + check) / 36 shims / 11 commits v16.2.4

### Task 8.2: 写 handoff doc

- [ ] **Step 1: 创建 `docs/superpowers/handoffs/2026-08-28-phase-126-v16-2-4-content-handoff.md`**

仿 v16.2.3 handoff 模板,11 sections + commit timeline:

```markdown
# Phase 126 v16.2.4 — Content Subdomain 拆分 + Onboarding T4 闭环 Handoff

> **状态**: ✅ 闭环
> **承接**: [spec/plan links + v16.2.3 handoff]
> **前置**: v16.2.3 (`a82cc4de`) + v16.2.2 + v16.2.1 + v16.2.0
> **下一步**: v16.2.5 export

## 0. TL;DR
v16.2.4 = content subdomain 拆分 (8 files) + onboarding T4 closure + shared/mode.py
extraction + infra/project_X migration。N commits / ~25 files / 1.5 天。

## 1. v16.2.4 完成的 11 件事
(列出 T1 + T2a-d + T3-T7 + handoff 每 commit 的 file changes)

## 2. 决策实现
(Q1-Q5 per spec §8 — shared/mode.py placement / agent.py 单文件 / shim pattern / 11 commits / etc.)

## 3. Plan deviations
(audit table with # / plan / actual / reason,mirror v16.2.3 handoff §3 format)

## 4. v16.2.4 副作用
(列出所有 file changes 的 effect: Python package + DTO + TS + typed wrapper + composables + routes + cross-subdomain + shim deletion)

## 5. Lessons
### 5.1 v16.2.4 新增 lessons
(spec §5 中标 NEW 的 4 项 + 沿用 lessons)

## 6. Carryover to v16.2.5+
| 任务 | 阶段 | 来源 |
|---|---|---|
| v16.2.5 export (5 files) | Round 2 leaf | plan §7 |
| v16.2.6 memory (3 files) | Round 2 leaf | plan §7 |
| v16.2.7 cleanup | final | plan §9 |
| Content composables refactor (19) | deferred | v16.2.7 |

## 7. 验证证据
(bash commands + expected outputs,mirror v16.2.3 handoff §7 format)

## 8. 新工具总结
(table: 工具 / 旧 / 新)

## 9. v16.2.4 完整 commit 时间线
(master: 3f21513a → ... → HEAD: 11 commits listed)

## 10. Closing Notes
(0 test regressions + 4 carryover closures summary)
```

**Implementer notes**: 写 handoff 时,具体 commit hashes、test counts、file size 数应填入实际执行结果(不是模板 placeholder)。所有 N values 从 T8 Step 1 verify 命令拿。

### Task 8.3: CLAUDE.md + .lingwen/architecture.yml + migration_log.yml update

- [ ] **Step 1: CLAUDE.md bump**

打开 `/home/ailearn/projects/LingWen/CLAUDE.md`,找到 v16.2.3 entry,更新为 v16.2.4:

```markdown
> **版本**: v16.2.4 (Phase 126 content subdomain 拆分 + onboarding T4 闭环)
  → v16.2.3 (Phase 126 onboarding 闭环)
  → ...
```

加 v16.2.4 update section,描述:
- 11 commits
- 8 content files + shared/mode.py 迁完
- 15 Content DTOs + 13 wrapper functions
- 4 carryover closures

- [ ] **Step 2: .lingwen/architecture.yml update**

打开 `.lingwen/architecture.yml`,找到 `creator` module_boundaries 的 exports list (line 47-90 估计):

找到 `# Memory (v16.2.5) — 待添加` 等 placeholder 注释,替换为:

```yaml
      # Content (v16.2.4) ✅ — 8 files + shared/mode.py extraction
      CreatorSettings, CREATION_MODE_STUDIO, CREATION_MODE_ADVANCE, CREATION_MODE_COMPANION,
      settings_from_project_config, normalize_creation_mode, normalize_quality_profile,
      resolve_creator_settings,
      run_creator_agent_plan, iter_creator_agent_plan_stream,
      enrich_batch_history_job,
      creator_overview, creator_chapter_preview, save_creator_chapter_outline, save_creator_chapter_body,
      run_creator_logic_check,
      list_creator_models_payload,
      creator_preferences_payload, save_creator_preferences,
      resolve_creator_ui_profile, ui_profile_from_project_config,
      # Export (v16.2.5) — 待添加
      # Memory (v16.2.6) — Round 2 leaf 待添加
      # Onboarding (v16.2.3) ✅
```

(注意: 实际顺序按 plan §1 表 — content → export → memory → onboarding)

- [ ] **Step 3: .lingwen/migration_log.yml update**

打开 `.lingwen/migration_log.yml`,prepend v16.2.4 entry:

```yaml
  - phase: v16.2.4
    date: 2026-08-28
    summary: "content subdomain 拆分 + onboarding T4 闭环 (8 content files + shared/mode.py extraction + onboarding composables refactor)"
    files_added:
      - packages/lingwen-creator/src/lingwen_creator/shared/mode.py
      - packages/lingwen-creator/src/lingwen_creator/content/__init__.py
      - packages/lingwen-creator/src/lingwen_creator/content/agent.py
      - packages/lingwen-creator/src/lingwen_creator/content/batch_history.py
      - packages/lingwen-creator/src/lingwen_creator/content/dashboard.py
      - packages/lingwen-creator/src/lingwen_creator/content/logic_check.py
      - packages/lingwen-creator/src/lingwen_creator/content/mode.py
      - packages/lingwen-creator/src/lingwen_creator/content/models.py
      - packages/lingwen-creator/src/lingwen_creator/content/preferences.py
      - packages/lingwen-creator/src/lingwen_creator/content/ui_profile.py
      - packages/lingwen-creator/tests/test_shared_mode.py
      - packages/lingwen-creator/tests/test_content.py
      - packages/lingwen-shared/tests/test_content_dto.py
      - apps/dashboard/src/api/content.ts
      - apps/dashboard/tests/unit/api/use-content-typed-wrapper.spec.ts
    files_modified:
      - infra/creator_mode.py  # → shim (T1)
      - infra/creator_agent.py  # → shim (T2a)
      - infra/creator_batch_history.py  # → shim (T2a)
      - infra/creator_dashboard.py  # → shim (T2b)
      - infra/creator_logic_check.py  # → shim (T2b)
      - infra/creator_models.py  # → shim (T2c)
      - infra/creator_preferences.py  # → shim (T2d)
      - infra/creator_ui_profile.py  # → shim (T2d)
      - packages/lingwen-creator/src/lingwen_creator/shared/check.py  # import fix (T1)
      - packages/lingwen-creator/src/lingwen_creator/onboarding/onboarding.py  # forward-ref close (T1)
      - infra/project_init.py  # → lingwen_creator.shared.mode (T5)
      - infra/project_config.py  # → lingwen_creator.shared.mode (T5)
      - apps/studio_api/routes/creator_core.py  # ~12 imports migrated (T5)
      - apps/dashboard/src/composables/useCreatorOnboarding.js  # T6 refactor
      - apps/dashboard/src/composables/useCreatorOnboarding/*.ts  # T6 refactor
      - apps/dashboard/knip.json  # allowlist (T4)
      - packages/dashboard-contracts/src/shared/creator.ts  # Content DTOs re-export (T4)
      - packages/dashboard-contracts/src/shared/index.ts  # content re-export (T4)
      - packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py  # 15 Content DTOs (T3)
      - packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts  # auto-generated (T3)
    files_deleted:
      - apps/dashboard/src/api/onboarding.js  # shim obsolete (T6)
    tests_added: 31 (5 shared_mode + 6 content + 13 content_dto + 12 URL contract)
    shim_remaining: 35  (36 - 0 = 35,因 creator_check.py + creator_revision.py 已 v16.2.0 迁 shared,所以 v16.2.0 起 shim count 是 34,v16.2.4 增加 0 因 onboarding 9 + volume 6 + settings 3 已迁完)
    status: closed
```

(实际 shim count 需 verify:`ls infra/creator_*.py | wc -l`)

### Task 8.4: Commit + push

- [ ] **Step 1: Commit handoff + meta updates**

```bash
cd /home/ailearn/projects/LingWen
git add docs/superpowers/handoffs/2026-08-28-phase-126-v16-2-4-content-handoff.md \
        CLAUDE.md \
        .lingwen/architecture.yml \
        .lingwen/migration_log.yml
git commit -m "docs(phase-126): v16.2.4 handoff — content subdomain split complete + carryover closures

v16.2.4 闭环: content subdomain 8 files + shared/mode.py extraction + onboarding
T4 composables refactor + infra/project_X migration。11 commits / ~25 files
/ 1.5 天。

承接 v16.2.0..3 闭环 (shared/volume/settings/onboarding 已迁)。下一步 v16.2.5
export + v16.2.6 memory + v16.2.7 cleanup。

4 carryover closures:
1. onboarding forward-reference to infra.creator_mode (T1)
2. shared/check.py spec violation (T1)
3. infra/project_init + infra/project_config imports of infra.creator_mode (T5)
4. onboarding T4-partial composables + api/onboarding.js shim (T6)

Carryover to v16.2.5+:
- v16.2.5 export (5 files Round 2 leaf)
- v16.2.6 memory (3 files Round 2 leaf)
- v16.2.7 cleanup (36 shim deletions + 4 typed wrapper /api/ prefix fix
  for world/workspace/quality/onboarding + 22 vitest debt +
  import-linter DP-01..06)
- Content composables (19 per spec §3.7) refactor deferred to v16.2.7

Updated:
- CLAUDE.md: v16.2.3 → v16.2.4
- .lingwen/architecture.yml: creator exports + Content + shared.mode symbols
- .lingwen/migration_log.yml: v16.2.4 entry

Verified: pytest + vitest + vue-tsc + knip + ruff + zod + codegen 全 0 errors。
"
```

- [ ] **Step 2: Push to origin**

```bash
cd /home/ailearn/projects/LingWen
git push origin master 2>&1 | tail -10
```

Expected: 11 commits pushed to origin/master

---

## 9. Verification Gates Summary

### 9.1 Per Sub-phase Gates (T1-T8 必过)

| Gate | 命令 | 期望 |
|---|---|---|
| uv sync | `uv sync` | 0 errors |
| Backend tests | `/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-creator/tests/test_content.py packages/lingwen-creator/tests/test_shared_mode.py packages/lingwen-shared/tests/test_content_dto.py tests/infra/test_creator_*.py -q` | baseline + 5 + 6 + 13 PASSED |
| Frontend tests | `cd apps/dashboard && pnpm vitest run tests/unit/api/use-content-typed-wrapper.spec.ts --reporter=dot` | 12 PASSED |
| ruff | `ruff check packages/lingwen-creator/src/lingwen_creator/content/ packages/lingwen-creator/src/lingwen_creator/shared/mode.py` | 0 |
| vue-tsc | `pnpm exec vue-tsc --noEmit` | 0 errors |
| knip | `pnpm exec knip` | 0 (allowlist 同步) |
| codegen | `/home/ailearn/miniconda3/bin/python tooling/contracts/generate.py` | ts/creator.ts regenerated |
| zod reverse | `/home/ailearn/miniconda3/bin/python tooling/contracts/zod_revalidate.py` | 0 drift |

### 9.2 v16.2.4 Final Gate (T8 必过)

| Gate | 命令 | 期望 |
|---|---|---|
| content imports clean | `grep -cE "infra\.creator_(agent\|dashboard\|logic_check\|batch_history\|models\|preferences\|ui_profile)" apps/studio_api/routes/creator_core.py` | 0 |
| forward-reference closed | `grep -cE "infra\.creator_mode" packages/lingwen-creator/src/lingwen_creator/onboarding/onboarding.py` | 0 |
| spec violation fixed | `grep -cE "infra\.creator_mode" packages/lingwen-creator/src/lingwen_creator/shared/check.py` | 0 |
| project_X migrated | `grep -cE "infra\.creator_mode" infra/project_init.py infra/project_config.py` | 0 |
| onboarding shim deleted | `ls apps/dashboard/src/api/onboarding.js 2>&1` | not exist |
| content module count | `ls packages/lingwen-creator/src/lingwen_creator/content/*.py \| wc -l` | 8 |
| Handoff doc | `docs/superpowers/handoffs/2026-08-28-phase-126-v16-2-4-content-handoff.md` | exists |

---

## 10. Carryover to v16.2.5+

| 任务 | 阶段 | 来源 |
|---|---|---|
| **v16.2.5 export** | 5 files (common, docx, epub, publish, publish_adapters) | per spec §3.4 + plan §7 (renumbered) |
| **v16.2.6 memory** | 3 files (annotations, assets, query) | per spec §3.5 + plan §7 (Round 2 leaf) |
| **v16.2.7 cleanup** | 36 shim deletions + 4 typed wrapper `/api/` prefix fix (world/workspace/quality/onboarding) + 22 vitest debt + import-linter DP-01..06 | per plan §9 |
| **Content composables refactor** | 19 composables (useCreatorAgent/Page*/Pulse/ProductTools/Workspace/Write*) typed wrapper switchover | deferred to v16.2.7 |
| **Pre-existing vitest debt** | 22 v16.2.1 `useCreatorVolumePlan*.spec.ts` failures + collection errors for `tests/infra` (Phase 125 module-namespace conflict) | v16.2.7 cleanup responsibility |
| **dashboard-contracts/src/shared/creator.ts explicit re-export list** | Each new DTO submodule needs explicit addition here (TS fragility noted in v16.2.3 §5.1 lesson 3) | pattern for v16.2.5+ |
| **import-linter enforcement** | allowed_imports / forbidden_imports DP-01..06 | v16.4 |
| **StoragePort enforcement** | DP-03 | v16.5 |
| **LLMServicePort enforcement** | DP-04 | v16.4 |
| **yoyo-migrations** | — | v16.5 |
| **workspace members exist gate** | — | v16.5 |

---

## 11. Execution Notes

- **本项目不用 worktree** (per CLAUDE.md): 直接在 master commit
- **attribution disabled**: 不要加 `Co-Authored-By: Claude`
- **commit message**: 沿用 v16.2.1..3 风格 — conventional commits + 中文 lessons section
- **DP-06 commit-level**: 每 commit ≤5 files,跨多个 commits 完成 sub-phase (T1+T2a-d+T3-T8 = 11 commits)
- **shim pattern**: `# noqa: F403` inline (v15.7.1 lesson) + `# noqa: F401` for shim star-imports (per v16.2.3 precedent)
- **typed wrapper style**: 与 v16.2.1 T3 (volume.ts) + v16.2.2 T3 (settings.ts) + v16.2.3 T3 (onboarding.ts) 一致 (NO zod)
- **knip allowlist**: 加 typed wrapper 时立即同步(v16.2.1 T4 lesson)
- **intra-package import**: T2a-d 严格按 plan §12.2 规则,目标已迁 → 用 lingwen_creator.{subdomain}.X
- **T1 spec violation + forward-reference closure**: 必须同 commit 修,不可拆(per v16.2.2 §5.1 lesson 1 H1 lesson)
- **T6 onboarding T4 composables refactor**: 用 mapping table (Step 1) 系统性 find/replace 21 aliases
- **T7 conditional skip**: grep findings 为 0 时 skip commit
- **uv venv**: T1 验证用 `/home/ailearn/miniconda3/bin/python` (per v16.2.0 review fix),不是 `uv run python`(因 creator 包通过 root pyproject 的 editable install,miniconda Python 也能 import)
- **shim count expectations**: v16.2.0..3 已迁 18 files (2 shared + 6 volume + 3 settings + 9 onboarding),v16.2.4 迁 9 files (1 shared/mode + 8 content 但其中 1 是 content/mode shim,实际 verbatim 7 + 2 shim). Total shim count: 35 - 1 (creator_mode 变 shim 不算) - 7 content verbatim shim = 36 - 7 = 29 shims? 需 verify at T8 Step 1.

---

**Plan complete and saved to `docs/superpowers/plans/2026-08-28-phase-126-v16-2-4-content-plan.md`.**

**Next step**: 选择执行模式 — subagent-driven (recommended) 或 inline executing-plans。

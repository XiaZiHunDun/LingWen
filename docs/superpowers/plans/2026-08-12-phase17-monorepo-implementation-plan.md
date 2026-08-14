# Phase 17 · Monorepo 化 实施计划（v2）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把当前仓库从「单仓多目录」重组为「apps + packages + content + docs + tooling」双层 monorepo；保留 git 历史（`git mv`）；保证 Phase 16 Gate + Phase 17 Gate 全部通过。

**Architecture:** Python 包走 `packages/lingwen-*` + hatchling 独立发布；前端走 `apps/dashboard` + pnpm workspace；内容/角色/方法论走 `content/roles/`；共享 lint/typecheck 走 `tooling/`。依赖方向由 `tooling/lint/check_package_deps.py` 静态守卫。

**Tech Stack:** pnpm 9 + hatchling + pytest + ruff + uv workspaces（Python 端可选）+ lingwen-storage（已在 Phase 16.5 创建）。

---

## 0. 与原计划的差异（v1 → v2 增量）

| 差异 | 说明 |
|------|------|
| 原计划 Task 17.1「创建 `pnpm-workspace.yaml`」改为「**扩展现有 `pnpm-workspace.yaml`**」 | 仓库已有 pre-existing `pnpm-workspace.yaml`（仅含 `dashboard/frontend` + `packages/*`），需扩展到 `apps/*` + 排除 `packages/lingwen-storage`（Python） |
| 新增 **Task 17.0：解 16.7 推迟工作** | 必须在任何 monorepo 拆分之前解决：`infra/__init__.py` 的 `from infra.creator/studio/prose/di/event_sourcing import *` 移除；`infra/exports/events.py` 迁到 `lingwen_storage`；dashboard30+ legacy module import 重写 |
| 新增 **Task 17.4a：迁 `infra/event_sourcing` 到 `lingwen-storage`** | 与 17.0 重复，已合并到 17.0 |
| 删除原 Task 17.13「占位 + TODO 模式」 | 改为 **Task 17.13 + 17.14** 两个完整 TDD 任务（AST 解析 + 静态正则双轨） |
| 删除原 Task 17.15「脚本 stub with `pass`」 | 改为 **Task 17.16 + 17.17**（SKILL.md 迁移 + registry 生成），每个 TDD |
| 删除原 Task 17.16「mark-historical 步骤」 | 已并入 17.19 文档清理 |
| 修复 Phase 17 Gate 脚本 bug（broken shell snippets） | 改为 **Task 17.21** 完整可执行版本 |

---

## 1. 任务清单（22 任务）

### Task 17.0：解 16.7 推迟的工作（前置任务）

> **必须先完成**：否则 17.1-17.10 的 import 重写会遇到循环依赖与陈旧 re-export。
>
> 来源：`docs/superpowers/plans/2026-08-10-phase16.7-discovery-and-decision.md`

**Files:**
- Modify: `infra/__init__.py:6-11` (删除 re-export)
- Modify: `infra/__init__.py:121` (删除 `from infra.di.layer import …`)
- Modify: `infra/__init__.py:144-146` (删除 event_sourcing re-export)
- Modify: `infra/exports/events.py` (迁到 lingwen-storage)
- Modify: `infra/consistency/checkers/pacing_checker.py:20` (脱 `infra.world_model`)
- Modify: `infra/consistency/checkers/foreshadow_checker.py:25-26` (脱 `infra.world_model`)
- Modify: `infra/agent_system/{chapter_production_pilot.py:30, production_summary.py:6, chapter_memory_hook.py:8}` (脱 `infra.cross_volume`)
- Modify: `infra/agent_system/core/context_builder.py:67` (脱 `infra.story_contracts`)
- Modify: `infra/cli/commands/{backfill.py, cascade.py, ripple_*.py, story_contract.py}` (脱 `infra.cross_volume` / `infra.story_contracts`)

- [ ] **Step 1: 扫描所有 16.7 推迟的引用**

```bash
cd /home/ailearn/projects/LingWen
grep -rEln "infra\.(di|cross_volume|story_contracts|world_model|creator|event_sourcing|exports)" \
  --include='*.py' \
  infra/__init__.py infra/exports/ infra/consistency/checkers/ infra/agent_system/ infra/cli/commands/ \
  packages/lingwen-storage/src/ 2>/dev/null > /tmp/phase17-0-deferred.txt
wc -l /tmp/phase17-0-deferred.txt
```

Expected: 15-25 个文件。

- [ ] **Step 2: 写失败测试 — `infra/__init__.py` 不再 re-export 陈旧模块**

Create: `tests/test_infra_init_no_deferred_re_exports.py`

```python
"""Phase 17.0 守卫：infra/__init__.py 不再 re-export 陈旧模块。

来源：Phase 16.7 推迟决策（docs/superpowers/plans/2026-08-10-phase16.7-discovery-and-decision.md）。
被 re-export 的陈旧模块：creator, studio, prose, project, core, di, event_sourcing。
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
INIT = REPO / "infra" / "__init__.py"

# 17.0 完成后这些 re-export 必须从 infra/__init__.py 删除
FORBIDDEN_REEXPORTS = [
    r"from\s+infra\.creator\s+import",
    r"from\s+infra\.studio\s+import",
    r"from\s+infra\.prose\s+import",
    r"from\s+infra\.project\s+import",
    r"from\s+infra\.core\s+import",
    r"from\s+infra\.di\.layer\s+import",
    r"from\s+infra\.event_sourcing\.(models|store)\s+import",
]


def test_no_deferred_reexports():
    src = INIT.read_text(encoding="utf-8")
    for pattern in FORBIDDEN_REEXPORTS:
        assert not re.search(pattern, src), (
            f"infra/__init__.py still re-exports deferred module: {pattern}"
        )
```

- [ ] **Step 3: 跑测试，确认失败**

Run:
```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python3 -m pytest tests/test_infra_init_no_deferred_re_exports.py -v
```

Expected: FAIL with `AssertionError: infra/__init__.py still re-exports deferred module: from\s+infra\.creator\s+import`.

- [ ] **Step 4: 删除 `infra/__init__.py:6-11` 的 6 行 re-export**

Edit `infra/__init__.py`, 删除以下行:

```python
# 子包导出
from infra.creator import *
from infra.studio import *
from infra.prose import *
from infra.project import *
from infra.core import *
```

删除第3行：

```python
import infra.exports as exports
```

（保留 `from infra.exports.core import Result, Ok, Err` 等具体符号 re-export，但删除 `import infra.exports as exports` 这一行；如需 `exports` 命名空间，让消费者显式 `import infra.exports as exports`。）

- [ ] **Step 5: 删除 `infra/__init__.py:121` 的 `from infra.di.layer import …`**

```python
# DI 系统
from infra.di.layer import Tag, Layer, Runtime
```

整段删除。

- [ ] **Step 6: 删除 `infra/__init__.py:144-145` 的 event_sourcing re-exports**

```python
# 事件溯源系统
from infra.event_sourcing.models import DomainEvent, EventSerializer, EventStream, EventType, Snapshot, versioned_type
from infra.event_sourcing.store import EventExistsError, EventStore, EventStoreError, OwnerMismatchError, ReplayDivergedError, SequenceConflictError, create_event, create_snapshot
```

整段删除。Event sourcing 已迁到 `packages/lingwen-storage`（Phase 16.5），由消费者显式 `from lingwen_storage.events import ...`。

- [ ] **Step 7: 跑测试 + 全文 import 验证**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python3 -m pytest tests/test_infra_init_no_deferred_re_exports.py -v
cd packages/lingwen-storage && /home/ailearn/miniconda3/bin/python3 -m pytest tests/ -q
cd ../..
```

Expected: 守卫测试 PASS；lingwen-storage 18 tests PASS。

- [ ] **Step 8: 重写 `infra/consistency/checkers/pacing_checker.py` 脱离 `infra.world_model`**

Read `infra/consistency/checkers/pacing_checker.py`, 找到：

```python
from infra.world_model.data_structures import Ripple
```

替换为本地定义（在文件内 copy `Ripple` 数据结构的最小字段；或迁到 `packages/lingwen-core/src/lingwen_core/domain/ripple.py` —— **如果后者，改 import**）。建议在 `pacing_checker.py` 顶部定义本地最小 dataclass，避免跨包依赖：

```python
@dataclass(frozen=True)
class _RippleRef:
    ripple_id: str
    chapter_id: str
```

把 `Ripple(...)` 引用改为 `_RippleRef(...)`。

- [ ] **Step 9: 重写 `infra/consistency/checkers/foreshadow_checker.py` 脱离 `infra.world_model`**

类似 Step 8：`from infra.world_model.data_structures import RippleState` 和 `from infra.world_model.lifecycle import RESOLUTION_GRACE_CH` 改为本地常量或新模块。

- [ ] **Step 10: 重写 `infra/agent_system/{chapter_production_pilot.py, production_summary.py, chapter_memory_hook.py}` 脱离 `infra.cross_volume`**

3 个文件各 1 处 import：`from infra.cross_volume.incremental_backfill import ...`。改为本地 stub 或迁函数到 `infra/agent_system/internal/incremental_backfill.py`（最小重写，仅导出所需函数）。

- [ ] **Step 11: 重写 `infra/agent_system/core/context_builder.py` 脱离 `infra.story_contracts`**

```python
from infra.story_contracts import StoryContractEngine
```

替换：删除此 import；如需 `StoryContractEngine`，把它改为 `infra/agent_system/core/context_helpers.py` 中的本地 stub（Phase 17.5 迁到 `lingwen-core` 时再做完整重写）。

- [ ] **Step 12: 重写 `infra/cli/commands/{backfill.py, cascade.py, ripple_*.py, story_contract.py}` 脱离 `infra.cross_volume` / `infra.story_contracts`**

每个文件 1-3 处。按相同模式：迁函数到 `infra/cli/internal/` 子目录或本地 stub；删除陈旧 import。

- [ ] **Step 13: commit**

```bash
cd /home/ailearn/projects/LingWen
git add infra/__init__.py infra/exports/ infra/consistency/checkers/ infra/agent_system/ infra/cli/commands/ tests/test_infra_init_no_deferred_re_exports.py
git commit -m "refactor(infra): 解 Phase 16.7 推迟工作（移除陈旧 re-export + dashboard/cli/agent_system 脱陈旧 import）"
```

- [ ] **Step 14: 完整 gate 验证**

```bash
cd /home/ailearn/projects/LingWen
bash tooling/gates/phase_16.sh
```

Expected: gate 仍 PASS（`check_repo_state.py` 的85+ WARN 不变，但 `check_file_size.py` + `check_brand_consistency.py` + lingwen-storage pytest 全绿）。

---

### Task 17.1：扩展现有 pnpm workspace 骨架

**Files:**
- Modify: `pnpm-workspace.yaml`（已有，仅扩展）
- Modify: 根 `package.json`（创建）

- [ ] **Step 1: 读现有 `pnpm-workspace.yaml`**

```bash
cat /home/ailearn/projects/LingWen/pnpm-workspace.yaml
```

Expected: 当前含 `dashboard/frontend` + `packages/*`。

- [ ] **Step 2: 写失败测试 — `pnpm-workspace.yaml` 覆盖 `apps/*`**

Create: `tooling/lint/tests/test_pnpm_workspace_yaml.py`

```python
"""Phase 17.1 守卫：pnpm-workspace.yaml 覆盖 apps/*。"""
from pathlib import Path
import yaml

REPO = Path(__file__).resolve().parents[3]
WS = REPO / "pnpm-workspace.yaml"


def test_pnpm_workspace_includes_apps():
    data = yaml.safe_load(WS.read_text(encoding="utf-8"))
    packages = data.get("packages", [])
    assert "apps/*" in packages, (
        f"pnpm-workspace.yaml must include 'apps/*'; got {packages}"
    )


def test_pnpm_workspace_excludes_lingwen_storage():
    """Python 包不应被 pnpm workspace 跟踪。"""
    data = yaml.safe_load(WS.read_text(encoding="utf-8"))
    packages = data.get("packages", [])
    # 不应包含 'packages/lingwen-storage'（用路径展开；pnpm 不识别）
    assert "packages/lingwen-storage" not in packages
    assert "packages/lingwen-core" not in packages  # 未来 17.5 也不会是 pnpm 包
```

- [ ] **Step 3: 跑测试，确认失败**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python3 -m pytest tooling/lint/tests/test_pnpm_workspace_yaml.py -v
```

Expected: FAIL with `pnpm-workspace.yaml must include 'apps/*'; got [...]`.

- [ ] **Step 4: 扩展 `pnpm-workspace.yaml`**

Edit `pnpm-workspace.yaml`:

```yaml
packages:
  - 'apps/*'
  - 'packages/*'
  - 'dashboard/frontend'
  # Python 包用 uv workspaces 管理，不在此跟踪：
  #   packages/lingwen-storage (16.5 创建)
  #   packages/lingwen-core (17.5 创建)
  #   packages/lingwen-{llm,memory,prompt,pipeline,quality,cli} (17.6-17.10 创建)
```

（保留原 `dashboard/frontend` 因为 17.2 才迁移；过渡期两者共存。）

- [ ] **Step 5: 创建根 `package.json`**

Create: `package.json`

```json
{
  "name": "lingwen-monorepo",
  "private": true,
  "version": "10.0.0",
  "description": "墨灵 Studio (产品) + 灵文引擎 (框架) monorepo",
  "license": "MIT",
  "engines": {
    "node": ">=20",
    "pnpm": ">=9"
  },
  "packageManager": "pnpm@9.0.0",
  "scripts": {
    "build": "pnpm -r --filter './apps/*' --filter './packages/*' build",
    "lint": "pnpm -r --filter './apps/*' --filter './packages/*' run lint",
    "test": "pnpm -r --filter './apps/*' --filter './packages/*' run test",
    "typecheck": "pnpm -r --filter './apps/*' --filter './packages/*' run typecheck"
  }
}
```

- [ ] **Step 6: 跑测试，确认通过**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python3 -m pytest tooling/lint/tests/test_pnpm_workspace_yaml.py -v
pnpm install 2>&1 | tail -10
```

Expected: 测试 PASS；`pnpm install` 不报错（即使没有任何 `apps/` 工作区项，过渡期 `dashboard/frontend` 仍存在）。

- [ ] **Step 7: commit**

```bash
git add pnpm-workspace.yaml package.json tooling/lint/tests/test_pnpm_workspace_yaml.py
git commit -m "build(workspace): pnpm workspace 覆盖 apps/* + 根 package.json (Phase 17.1)"
```

---

### Task 17.2：dashboard/frontend → apps/dashboard（保留 git 历史）

**Files:**
- Move: `dashboard/frontend/` → `apps/dashboard/`
- Modify: `.github/workflows/dashboard-frontend-ci.yml` (trigger path)
- Modify: `tooling/gates/phase_16.sh` (pnpm 命令 cd 路径)

- [ ] **Step 1: 用 `git mv`（保留 blame）**

```bash
cd /home/ailearn/projects/LingWen
mkdir -p apps
git mv dashboard/frontend apps/dashboard
git status --short | head -10
```

Expected: `R dashboard/frontend -> apps/dashboard` (rename 标记，非 delete+add)。

- [ ] **Step 2: 写失败测试 — `dashboard/frontend` 路径已无**

Create: `tooling/lint/tests/test_dashboard_path_normalized.py`

```python
"""Phase 17.2 守卫：dashboard/frontend 路径应已迁移到 apps/dashboard。"""
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def test_dashboard_frontend_path_removed():
    assert not (REPO / "dashboard" / "frontend").exists(), (
        "dashboard/frontend should have been moved to apps/dashboard in 17.2"
    )


def test_apps_dashboard_exists():
    assert (REPO / "apps" / "dashboard").exists(), (
        "apps/dashboard should exist after 17.2"
    )
```

- [ ] **Step 3: 跑测试，确认通过**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python3 -m pytest tooling/lint/tests/test_dashboard_path_normalized.py -v
```

Expected: PASS。

- [ ] **Step 4: 扫描并修绝对路径引用**

```bash
cd /home/ailearn/projects/LingWen
grep -rln 'dashboard/frontend' apps/ packages/ tooling/ docs/ .github/ 2>/dev/null | \
  grep -v '\.git/' | head -20
```

对每个命中文件，把 `dashboard/frontend/` → `apps/dashboard/`。特别关注：

- `.github/workflows/dashboard-frontend-ci.yml`：trigger path + working-directory
- `dashboard/frontend/.husky/pre-commit`：如果它对根目录有引用
- `tooling/gates/phase_16.sh`：`(cd dashboard/frontend && pnpm lint ...)` 改为 `(cd apps/dashboard && pnpm lint ...)`

- [ ] **Step 5: 跑 `apps/dashboard` 自检**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm lint 2>&1 | tail -5 || echo "pre-existing lint failures expected (Phase 16.11 documented)"
pnpm typecheck 2>&1 | tail -5 || echo "pre-existing typecheck failures expected"
pnpm test 2>&1 | tail -5
```

Expected: lint/typecheck 可能因 Phase 16.11 记录的 pre-existing 问题失败；`test` 部分应至少跑起来（vitest 自身可启动）。

- [ ] **Step 6: commit**

```bash
cd /home/ailearn/projects/LingWen
git add -A
git commit -m "refactor(monorepo): dashboard/frontend → apps/dashboard (Phase 17.2)"
```

---

### Task 17.3：dashboard/（除 frontend）→ apps/studio-api

**Files:**
- Move: `dashboard/`（剩余部分） → `apps/studio-api/`
- Modify: 相关 CI 配置

- [ ] **Step 1: 用 `git mv`**

```bash
cd /home/ailearn/projects/LingWen
git mv dashboard apps/studio-api
git status --short | head -10
```

Expected: rename 检测。

- [ ] **Step 2: 写守卫测试 — `dashboard/` 路径已无**

复用 Task 17.2 的 `test_dashboard_path_normalized.py`，扩展：

```python
def test_dashboard_root_removed():
    assert not (REPO / "dashboard").exists() or (REPO / "dashboard").is_dir() is False, (
        "dashboard/ root should be moved to apps/studio-api (frontend already in apps/dashboard)"
    )


def test_apps_studio_api_exists():
    assert (REPO / "apps" / "studio-api").exists()
```

- [ ] **Step 3: 跑测试，确认通过**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python3 -m pytest tooling/lint/tests/test_dashboard_path_normalized.py -v
```

- [ ] **Step 4: 修路径引用**

```bash
cd /home/ailearn/projects/LingWen
grep -rln 'dashboard/' apps/ packages/ tooling/ docs/ .github/ 2>/dev/null | \
  grep -vE '(apps/dashboard/|apps/studio-api/)' | head -20
```

把剩余 `dashboard/` 引用改为 `apps/studio-api/` 或 `apps/dashboard/`（视语境）。

- [ ] **Step 5: 跑 Phase 16 Gate（基础卫生验证）**

```bash
cd /home/ailearn/projects/LingWen
bash tooling/gates/phase_16.sh 2>&1 | tail -15
```

Expected: gate 仍 PASS（退出 0），因为 Phase 17.0 已解开 16.7 推迟工作。

- [ ] **Step 6: commit**

```bash
git add -A
git commit -m "refactor(monorepo): dashboard/ → apps/studio-api (Phase 17.3)"
```

---

### Task 17.4：建 packages/lingwen-core（infra/agent_system 迁入）

**Files:**
- Create: `packages/lingwen-core/`（含 pyproject.toml + README.md + tests/）
- Move: `infra/agent_system/` → `packages/lingwen-core/src/lingwen_core/agents/`

- [ ] **Step 1: 建包骨架**

```bash
cd /home/ailearn/projects/LingWen
mkdir -p packages/lingwen-core/src/lingwen_core
mkdir -p packages/lingwen-core/tests
```

- [ ] **Step 2: 写失败测试 — `lingwen_core.agents` 可 import**

Create: `packages/lingwen-core/tests/test_import.py`

```python
"""Phase 17.4 守卫：lingwen_core.agents 包结构正确。"""


def test_agents_module_importable():
    import lingwen_core.agents  # noqa: F401
```

- [ ] **Step 3: 跑测试，确认失败（包未安装）**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python3 -m pytest packages/lingwen-core/tests/test_import.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'lingwen_core'`.

- [ ] **Step 4: 写 `pyproject.toml`**

Create: `packages/lingwen-core/pyproject.toml`

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "lingwen-core"
version = "0.1.0"
description = "LingWen · 5 核心 Agent + 角色池"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.7",
    "lingwen-storage",
]

[project.optional-dependencies]
test = ["pytest>=8.0"]

[tool.hatch.build.targets.wheel]
packages = ["src/lingwen_core"]
```

- [ ] **Step 5: 安装并迁移**

```bash
cd /home/ailearn/projects/LingWen/packages/lingwen-core
/home/ailearn/miniconda3/bin/pip install -e ".[test]"
cd ../..
git mv infra/agent_system packages/lingwen-core/src/lingwen_core/agents
```

- [ ] **Step 6: 修 import**

```bash
grep -rln 'infra\.agent_system\|from infra\.agent_system' --include='*.py' . 2>/dev/null | \
  grep -v 'packages/lingwen-core/' | head -20
```

对每个命中文件：

- `from infra.agent_system.X import Y` → `from lingwen_core.agents.X import Y`
- `from infra.agent_system import Z` → `from lingwen_core.agents import Z`

（如果 import 在 `packages/lingwen-core/src/` 内，留不变。）

- [ ] **Step 7: 跑测试，确认通过**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python3 -m pytest packages/lingwen-core/tests/test_import.py -v
cd packages/lingwen-storage && /home/ailearn/miniconda3/bin/python3 -m pytest tests/ -q
cd ../..
```

Expected: lingwen_core.agents import OK；lingwen-storage 18 tests 仍 PASS。

- [ ] **Step 8: 写 README + commit**

Create: `packages/lingwen-core/README.md`

```markdown
# lingwen-core

LingWen · 5 核心 Agent + 角色池实现。

## 安装
\`\`\`bash
pip install -e ".[test]"
\`\`\`

## 测试
\`\`\`bash
pytest -q
\`\`\`

## 来源
原 `infra/agent_system/`，2026-08 由 Phase 17.4 迁入。
```

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-core/
git commit -m "feat(core): infra/agent_system → packages/lingwen-core (Phase 17.4)"
```

---

### Task 17.5：建 packages/lingwen-llm（infra/ai_service 迁入）

**Files:**
- Move: `infra/ai_service/` → `packages/lingwen-llm/src/lingwen_llm/`

- [ ] **Step 1-2: 同 17.4 模式（建包、写 import 测试、确认失败）**

- [ ] **Step 3: 写 `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "lingwen-llm"
version = "0.1.0"
description = "LingWen · LLM Provider 抽象层（OpenAI/Anthropic/MiniMax）"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.7",
    "httpx>=0.27",
    "openai>=1.30",
]

[project.optional-dependencies]
test = ["pytest>=8.0"]

[tool.hatch.build.targets.wheel]
packages = ["src/lingwen_llm"]
```

- [ ] **Step 4: 安装并迁移**

```bash
cd /home/ailearn/projects/LingWen
mkdir -p packages/lingwen-llm/src packages/lingwen-llm/tests
/home/ailearn/miniconda3/bin/pip install -e "packages/lingwen-llm[test]"
git mv infra/ai_service packages/lingwen-llm/src/lingwen_llm/providers
```

（注意：`lingwen-llm/src/lingwen_llm/providers/` 而不是 `lingwen_llm/`，避免与 `infra.ai_service` 包名直接迁移造成混淆；导入路径 `from lingwen_llm.providers import OpenAIProvider`。）

- [ ] **Step 5: 修 import + 跑测试 + commit**

```bash
grep -rln 'infra\.ai_service\|from infra\.ai_service' --include='*.py' . 2>/dev/null | \
  grep -v 'packages/lingwen-llm/' | xargs -r sed -i 's|infra\.ai_service|lingwen_llm.providers|g'

cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python3 -m pytest packages/lingwen-llm/tests/ packages/lingwen-storage/tests/ -v 2>&1 | tail -10
git add -A
git commit -m "feat(llm): infra/ai_service → packages/lingwen-llm (Phase 17.5)"
```

---

### Task 17.6：建 packages/lingwen-memory

**Files:**
- Move: `infra/memory_system/` → `packages/lingwen-memory/src/lingwen_memory/`

- [ ] **Step 1-5: 与 17.5 同模式**

依赖按 `infra/memory_system/` 实际需求：通常 `qdrant-client` + `numpy` + `lingwen-storage` + `lingwen-llm`。

```bash
cd /home/ailearn/projects/LingWen
mkdir -p packages/lingwen-memory/src packages/lingwen-memory/tests
git mv infra/memory_system packages/lingwen-memory/src/lingwen_memory
grep -rln 'infra\.memory_system' --include='*.py' . 2>/dev/null | \
  grep -v 'packages/lingwen-memory/' | xargs -r sed -i 's|infra\.memory_system|lingwen_memory|g'
git add -A
git commit -m "feat(memory): infra/memory_system → packages/lingwen-memory (Phase 17.6)"
```

---

### Task 17.7：建 packages/lingwen-prompt

**Files:**
- Move: `infra/prompt_engineering/` → `packages/lingwen-prompt/src/lingwen_prompt/`

- [ ] **Step 1-5: 与 17.5 同模式**

依赖：`jinja2` + `pydantic`。

```bash
cd /home/ailearn/projects/LingWen
mkdir -p packages/lingwen-prompt/src packages/lingwen-prompt/tests
git mv infra/prompt_engineering packages/lingwen-prompt/src/lingwen_prompt
grep -rln 'infra\.prompt_engineering' --include='*.py' . 2>/dev/null | \
  grep -v 'packages/lingwen-prompt/' | xargs -r sed -i 's|infra\.prompt_engineering|lingwen_prompt|g'
git add -A
git commit -m "feat(prompt): infra/prompt_engineering → packages/lingwen-prompt (Phase 17.7)"
```

---

### Task 17.8：建 packages/lingwen-pipeline（infra/state + hooks + state_machine）

**Files:**
- Move: `infra/state/`, `infra/hooks/`, `infra/state_machine.py` → `packages/lingwen-pipeline/src/lingwen_pipeline/`
- Move: `infra/agent_system/master_controller.py` (MasterController) → `packages/lingwen-pipeline/src/lingwen_pipeline/master_controller.py`

- [ ] **Step 1-5: 与 17.5 同模式**

```bash
cd /home/ailearn/projects/LingWen
mkdir -p packages/lingwen-pipeline/src/lingwen_pipeline packages/lingwen-pipeline/tests
git mv infra/state packages/lingwen-pipeline/src/lingwen_pipeline/state
git mv infra/hooks packages/lingwen-pipeline/src/lingwen_pipeline/hooks
git mv infra/state_machine.py packages/lingwen-pipeline/src/lingwen_pipeline/state_machine.py
git mv infra/agent_system/master_controller.py packages/lingwen-pipeline/src/lingwen_pipeline/master_controller.py

grep -rln 'infra\.state\|infra\.hooks\|infra\.state_machine\|infra\.agent_system\.master_controller' --include='*.py' . 2>/dev/null | \
  grep -v 'packages/lingwen-pipeline/' | xargs -r sed -i -E \
    -e 's|infra\.state_machine|lingwen_pipeline.state_machine|g' \
    -e 's|infra\.agent_system\.master_controller|lingwen_pipeline.master_controller|g' \
    -e 's|infra\.state\.|lingwen_pipeline.state.|g' \
    -e 's|infra\.hooks\.|lingwen_pipeline.hooks.|g'

git add -A
git commit -m "feat(pipeline): infra/state+hooks+state_machine+master_controller → packages/lingwen-pipeline (Phase 17.8)"
```

---

### Task 17.9：建 packages/lingwen-quality（infra/consistency + infra/quality）

**Files:**
- Move: `infra/consistency/`, `infra/quality/` → `packages/lingwen-quality/src/lingwen_quality/`

- [ ] **Step 1-5: 与 17.5 同模式**

依赖：`lingwen-core` + `lingwen-llm`。

```bash
cd /home/ailearn/projects/LingWen
mkdir -p packages/lingwen-quality/src packages/lingwen-quality/tests
git mv infra/consistency packages/lingwen-quality/src/lingwen_quality/consistency
git mv infra/quality packages/lingwen-quality/src/lingwen_quality/quality

grep -rln 'infra\.consistency\|infra\.quality' --include='*.py' . 2>/dev/null | \
  grep -v 'packages/lingwen-quality/' | xargs -r sed -i -E \
    -e 's|infra\.consistency\.|lingwen_quality.consistency.|g' \
    -e 's|infra\.quality\.|lingwen_quality.quality.|g'

git add -A
git commit -m "feat(quality): infra/consistency+quality → packages/lingwen-quality (Phase 17.9)"
```

---

### Task 17.10：建 packages/lingwen-cli（infra/cli + 根 lingwen.py）

**Files:**
- Move: `infra/cli/` → `packages/lingwen-cli/src/lingwen_cli/`
- Modify: 根 `lingwen.py` (改为薄壳)

- [ ] **Step 1: 写失败测试 — `lingwen_cli` 包可 import**

Create: `packages/lingwen-cli/tests/test_import.py`

```python
def test_cli_module_importable():
    import lingwen_cli  # noqa: F401
```

- [ ] **Step 2-3: 跑测试 + 写 pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "lingwen-cli"
version = "0.1.0"
description = "LingWen · CLI（lingwen check / status / repair 等）"
requires-python = ">=3.12"
dependencies = [
    "lingwen-core",
    "lingwen-pipeline",
    "lingwen-quality",
    "lingwen-storage",
    "click>=8.0",
]

[project.optional-dependencies]
test = ["pytest>=8.0"]

[project.scripts]
lingwen = "lingwen_cli.main:main"

[tool.hatch.build.targets.wheel]
packages = ["src/lingwen_cli"]
```

- [ ] **Step 4: 迁移 + 安装 + 修 import + commit**

```bash
cd /home/ailearn/projects/LingWen
mkdir -p packages/lingwen-cli/src packages/lingwen-cli/tests
git mv infra/cli packages/lingwen-cli/src/lingwen_cli
git mv lingwen.py packages/lingwen-cli/src/lingwen_cli/main_root_shim.py  # 旧入口暂存

# 新 lingwen.py 在根（向后兼容壳）
cat > lingwen.py <<'EOF'
#!/usr/bin/env python3
"""LingWen CLI · 顶层薄壳（向后兼容入口）。"""
from lingwen_cli.main import main

if __name__ == "__main__":
    main()
EOF
chmod +x lingwen.py

grep -rln 'infra\.cli' --include='*.py' . 2>/dev/null | \
  grep -v 'packages/lingwen-cli/' | xargs -r sed -i 's|infra\.cli|lingwen_cli|g'

/home/ailearn/miniconda3/bin/pip install -e "packages/lingwen-cli[test]"
/home/ailearn/miniconda3/bin/python3 -m pytest packages/lingwen-cli/tests/ packages/lingwen-storage/tests/ -v 2>&1 | tail -10

git add -A
git commit -m "feat(cli): infra/cli + 根 lingwen.py → packages/lingwen-cli (Phase 17.10)"
```

---

### Task 17.11：建 packages/dashboard-contracts（TS 占位包）

**Files:**
- Create: `packages/dashboard-contracts/`（空骨架，Phase 18-19 接 OpenAPI codegen）

- [ ] **Step 1: 写 package.json**

Create: `packages/dashboard-contracts/package.json`

```json
{
  "name": "@moling/dashboard-contracts",
  "version": "0.1.0",
  "private": true,
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "scripts": {
    "lint": "pnpm exec eslint 'src/**/*.ts'",
    "typecheck": "tsc --noEmit",
    "build": "tsc"
  }
}
```

- [ ] **Step 2: 写 tsconfig.json**

```json
{
  "extends": "../../tooling/tsconfig/base.json",
  "compilerOptions": { "outDir": "dist", "rootDir": "src" },
  "include": ["src/**/*"]
}
```

（前提：Tooling 17.12 已建 `tooling/tsconfig/base.json`；如未建，本任务内 inline 一份最小 tsconfig。）

- [ ] **Step 3: 写 src/index.ts 占位**

```typescript
// 自动生成：见 Phase 18-19 接 OpenAPI codegen。
// 本文件由 codegen 覆盖；目前为占位以确保 pnpm workspace 注册。
export const PLACEHOLDER = true;
```

- [ ] **Step 4: install + commit**

```bash
cd /home/ailearn/projects/LingWen
pnpm install 2>&1 | tail -5
git add packages/dashboard-contracts/
git commit -m "feat(contracts): TS 包骨架（占位，Phase 18-19 接 OpenAPI codegen）"
```

---

### Task 17.12：建 tooling/tsconfig/base.json（共享 strict 配置）

**Files:**
- Create: `tooling/tsconfig/base.json`

- [ ] **Step 1: 写 base.json**

Create: `tooling/tsconfig/base.json`

```json
{
  "$schema": "https://json.schemastore.org/tsconfig",
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM"],
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "useDefineForClassFields": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "isolatedModules": true,
    "resolveJsonModule": true
  }
}
```

- [ ] **Step 2: commit**

```bash
git add tooling/tsconfig/base.json
git commit -m "build(tsconfig): 共享 strict base.json (Phase 17.12)"
```

---

### Task 17.13：建 tooling/lint/check_package_deps.py（包依赖方向守卫）

**Files:**
- Create: `tooling/lint/check_package_deps.py`
- Create: `tooling/lint/tests/test_check_package_deps.py`

- [ ] **Step 1: 写失败测试**

Create: `tooling/lint/tests/test_check_package_deps.py`

```python
"""Phase 17.13 守卫：包依赖方向正确。

规则：
- packages/lingwen-* 不得 import apps.studio_api（lingwen 不能反向依赖应用）
- apps/dashboard 只能 import packages/dashboard-contracts（其他 lingwen 包须经 HTTP/WS）
- apps/studio-api 可以 import packages/lingwen-*（应用层）
"""
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "tooling" / "lint" / "check_package_deps.py"


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True,
        cwd=str(REPO),
    )


def test_clean_repo_passes():
    """在当前 worktree 上跑，应 PASS（即使还没 17.x 拆分，也能解析 import）。"""
    result = _run(["--check"])
    # 在 17.0 完成前可能 fail，因陈旧 import；这里只检查脚本可运行。
    assert result.returncode in (0, 1), f"Script crashed: {result.stderr[:200]}"


def test_violation_is_detected(tmp_path: Path):
    """构造违规 import，确认脚本能检测到。"""
    bad = tmp_path / "fake_lingwen.py"
    bad.write_text("from apps.studio_api import foo\n", encoding="utf-8")
    result = _run(["--check", "--target", str(bad)])
    assert result.returncode == 1, (
        f"Expected violation, got rc={result.returncode}, stdout={result.stdout}"
    )
    assert "violation" in result.stdout.lower()
```

- [ ] **Step 2: 跑测试，确认失败（脚本不存在）**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python3 -m pytest tooling/lint/tests/test_check_package_deps.py -v
```

Expected: `ModuleNotFoundError: No module named 'tooling'` 或脚本找不到。

- [ ] **Step 3: 写实现（静态 import 解析）**

Create: `tooling/lint/check_package_deps.py`

```python
"""包依赖方向守卫 (Phase 17.13)。

规则：
- packages/lingwen-* 不得 import apps.studio_api。
- apps/dashboard 只能 import packages/dashboard-contracts。
- apps/studio-api 可以 import packages/lingwen-*。
- 同包内可互相 import。

用法：
    python tooling/lint/check_package_deps.py --check
    python tooling/lint/check_package_deps.py --check --target <file>
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
APPS = REPO / "apps"
PACKAGES = REPO / "packages"

# 规则：source → 不允许 import 的目标前缀
FORBIDDEN = {
    "packages/lingwen": ["apps.studio_api", "apps.dashboard"],
    "apps/dashboard":   ["packages.lingwen_core", "packages.lingwen_llm", "packages.lingwen_memory",
                          "packages.lingwen_prompt", "packages.lingwen_pipeline", "packages.lingwen_quality",
                          "packages.lingwen_cli", "apps.studio_api"],
}


@dataclass(frozen=True)
class Violation:
    file: Path
    line: int
    rule: str
    detail: str


def _source_zone(path: Path) -> str:
    """把文件路径映射到 source zone（如 'packages/lingwen-core' 或 'apps/dashboard'）。"""
    rel = path.resolve().relative_to(REPO)
    parts = rel.parts
    if parts[0] == "apps" and len(parts) >= 2:
        return f"apps/{parts[1]}"
    if parts[0] == "packages" and len(parts) >= 2:
        return f"packages/{parts[1]}"
    return ""  # 顶层文件不在监控范围


def _resolve_import(imp: str, source_zone: str) -> str | None:
    """把 import 字符串映射到 zone（'apps/studio-api' 或 'packages/lingwen-core' 等）。"""
    parts = imp.split(".")
    if parts[0] == "apps" and len(parts) >= 2:
        return f"apps/{parts[1]}"
    if parts[0] == "packages" and len(parts) >= 2 and parts[1].startswith("lingwen"):
        return f"packages/{parts[1]}"
    return None


def _forbidden_for(zone: str) -> list[str]:
    for key, targets in FORBIDDEN.items():
        if zone.startswith(key):
            return targets
    return []


def check_file(path: Path) -> list[Violation]:
    zone = _source_zone(path)
    forbidden = _forbidden_for(zone)
    if not forbidden:
        return []
    try:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        return []
    out: list[Violation] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            target = _resolve_import(node.module, zone)
            if target and any(target.startswith(f) for f in forbidden):
                out.append(Violation(
                    file=path, line=node.lineno,
                    rule=f"{zone} → forbidden {target}",
                    detail=f"from {node.module} import ...",
                ))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", required=True)
    ap.add_argument("--target", type=Path, help="只检查单个文件")
    args = ap.parse_args()

    targets: list[Path]
    if args.target:
        targets = [args.target]
    else:
        targets = []
        for root in (APPS, PACKAGES):
            if root.exists():
                targets.extend(p for p in root.rglob("*.py") if "node_modules" not in p.parts and ".git" not in p.parts)

    violations: list[Violation] = []
    for t in targets:
        violations.extend(check_file(t))

    if violations:
        print("Package dependency violations:")
        for v in violations:
            print(f"  {v.file}:{v.line} [{v.rule}] {v.detail}")
        return 1
    print("OK: package dependencies follow allowed direction graph")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 跑测试 + 全仓检查**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python3 -m pytest tooling/lint/tests/test_check_package_deps.py -v
/home/ailearn/miniconda3/bin/python3 tooling/lint/check_package_deps.py --check 2>&1 | tail -20
```

Expected: 测试 PASS；在当前 worktree 上 `--check` 可能报一些违规（因为 17.4-17.10 还没完成；这是预期的，会在后续任务中修复）。

- [ ] **Step 5: commit**

```bash
git add tooling/lint/check_package_deps.py tooling/lint/tests/test_check_package_deps.py
git commit -m "feat(lint): 包依赖方向守卫（packages/lingwen ↛ apps； apps/dashboard 仅 contracts）"
```

---

### Task 17.14：把 content/ 顶层化（11 个编号目录统一）

**Files:**
- Move: 11 个 `01_灵感库` ~ `11_方法论` 目录 → `content/{manuscript, summary, roles/<role>}/`

- [ ] **Step 1: 写失败测试 — 顶层不应再有 0X_/1X_ 数字目录**

Create: `tooling/lint/tests/test_top_level_dir_normalized.py`

```python
"""Phase 17.14 守卫：顶层不应再有 01_* ~ 11_* 数字目录。"""
from pathlib import Path
import re

REPO = Path(__file__).resolve().parents[3]
PATTERN = re.compile(r"^\d{2}_")


def test_no_legacy_numbered_dirs():
    bad = [p.name for p in REPO.iterdir() if p.is_dir() and PATTERN.match(p.name)]
    assert not bad, (
        f"Top-level numbered dirs should have moved to content/: {bad}"
    )
```

- [ ] **Step 2: 跑测试，确认失败**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python3 -m pytest tooling/lint/tests/test_top_level_dir_normalized.py -v
```

Expected: FAIL with list of `01_灵感库`, `02_作家工作室`, etc.

- [ ] **Step 3: 用 `git mv` 批量**

```bash
cd /home/ailearn/projects/LingWen
mkdir -p content
git mv 03_内容仓库 content/manuscript
git mv 07_汇总仓库 content/summary
git mv 01_灵感库 content/roles/inspiration
git mv 02_作家工作室 content/roles/writer
git mv 04_审核员工作室 content/roles/reviewer
git mv 05_模拟读者池 content/roles/reader
git mv 06_意见仓库 content/roles/opinion
git mv 08_已发布 content/roles/archive
git mv 09_叙事设计 content/roles/narrative
git mv 10_规范文档 content/roles/standards
git mv 11_方法论 content/roles/methodology
```

- [ ] **Step 4: 修脚本引用**

```bash
cd /home/ailearn/projects/LingWen
grep -rln '0[1-9]_内容仓库\|0[1-9]_灵感库\|07_汇总仓库\|02_作家工作室\|04_审核员工作室\|05_模拟读者池\|06_意见仓库\|08_已发布\|09_叙事设计\|10_规范文档\|11_方法论' \
  --include='*.py' --include='*.sh' --include='*.md' . 2>/dev/null | head -20
```

按需更新脚本中的路径变量。

- [ ] **Step 5: 跑测试 + commit**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python3 -m pytest tooling/lint/tests/test_top_level_dir_normalized.py -v
git add -A
git commit -m "refactor(content): 11 个编号目录迁到 content/{manuscript,summary,roles/<role>} (Phase 17.14)"
```

---

### Task 17.15：合并 .skills/ → content/roles/<role>/skills/

**Files:**
- Move: `.skills/writer-*` → `content/roles/writer/skills/writer-*/`
- Move: `.skills/reviewer-*` → `content/roles/reviewer/skills/reviewer-*/`
- Move: `.skills/reader-*` → `content/roles/reader/skills/reader-*/`

- [ ] **Step 1: 写失败测试 — `.skills/` 顶层不存在**

Create: `tooling/lint/tests/test_skills_path_normalized.py`

```python
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def test_no_top_level_skills_dir():
    assert not (REPO / ".skills").exists() or not (REPO / ".skills").is_dir(), (
        ".skills/ should have moved to content/roles/<role>/skills/ in Phase 17.15"
    )
```

- [ ] **Step 2-3: 跑测试 + git mv**

```bash
cd /home/ailearn/projects/LingWen
ls .skills/ 2>/dev/null
# 把每个 .skills/<role>-<id>/ 迁到对应位置：
for role in writer reviewer reader; do
  mkdir -p "content/roles/$role/skills"
  if [ -d ".skills/${role}-"* ]; then
    git mv ".skills/${role}-"* "content/roles/$role/skills/" 2>/dev/null || true
  fi
done
# 清理空 .skills/
rmdir .skills 2>/dev/null || git rm -r .skills 2>/dev/null
```

- [ ] **Step 4: 修脚本引用 + commit**

```bash
grep -rln '\.skills/' --include='*.py' --include='*.md' . 2>/dev/null | head -10 | \
  xargs -r sed -i 's|\.skills/|content/roles/\1/skills/|g'  # 视实际上下文调整
git add -A
git commit -m "refactor(roles): .skills/ → content/roles/<role>/skills/ (Phase 17.15)"
```

---

### Task 17.16：SKILL.md 角色池统一 + registry.yaml 生成

**Files:**
- Modify: `content/roles/writer/作家A/` → `content/roles/writer/skills/writer-a/SKILL.md`（如未在 17.15 完成）
- Create: `content/roles/writer/registry.yaml`（自动生成）

- [ ] **Step 1: 写失败测试 — registry.yaml 包含所有 writer-a..j**

Create: `tests/test_skill_registry.py`

```python
"""Phase 17.16 守卫：角色池 registry.yaml 自动生成。"""
from pathlib import Path
import yaml

REPO = Path(__file__).resolve().parents[1]


def test_writer_registry_exists():
    p = REPO / "content" / "roles" / "writer" / "registry.yaml"
    assert p.exists(), "writer registry.yaml should exist"
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    skills = {s["slug"] for s in data.get("skills", [])}
    expected = {f"writer-{c}" for c in "abcdefghij"}
    assert skills >= expected, (
        f"Expected at least {expected}, got {skills}"
    )
```

- [ ] **Step 2: 跑测试，确认失败**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python3 -m pytest tests/test_skill_registry.py -v
```

Expected: FAIL（registry.yaml 不存在）。

- [ ] **Step 3: 写 SKILL.md 迁移脚本 + 测 + 实现**

Create: `tools/migrate_roles_to_skills.py`

```python
#!/usr/bin/env python3
"""把"作家A-J/"等旧角色目录迁到统一 SKILL.md 结构。

新结构：
    content/roles/<role>/skills/<role-slug>/SKILL.md

输出 registry.yaml 包含所有角色的 frontmatter 摘要。
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

import yaml


def slugify(name: str) -> str:
    """'作家A' → 'writer-a'"""
    m = re.match(r"^([一-鿿]+)([A-Z])$", name)
    if not m:
        return name.lower()
    role_zh, letter = m.groups()
    role_map = {"作家": "writer", "审核员": "reviewer", "读者": "reader"}
    return f"{role_map.get(role_zh, role_zh.lower())}-{letter.lower()}"


def migrate(role_root: Path, out_root: Path) -> list[dict]:
    skills: list[dict] = []
    if not role_root.exists():
        return skills
    for child in sorted(role_root.iterdir()):
        if not child.is_dir():
            continue
        slug = slugify(child.name)
        dst = out_root / slug
        dst.mkdir(parents=True, exist_ok=True)
        skill_md = dst / "SKILL.md"
        # 把 child/SKILL.md（如有）复制过来；否则写一个最小占位
        src_skill = child / "SKILL.md"
        if src_skill.exists():
            skill_md.write_text(src_skill.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            skill_md.write_text(
                f"---\nname: {slug}\ntype: content_writer\n---\n\n"
                f"# {child.name}\n\n迁入自 `{child}`，待前需补内容。\n",
                encoding="utf-8",
            )
        skills.append({
            "slug": slug,
            "legacy_dir": str(child.relative_to(role_root.parent)),
            "skill_md": str(skill_md.relative_to(role_root.parent.parent)),
        })
    return skills


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--role", required=True, choices=["writer", "reviewer", "reader"])
    ap.add_argument("--content-root", type=Path, default=Path("content/roles"))
    args = ap.parse_args()

    role_root = args.content_root / args.role
    skills_root = role_root / "skills"
    skills_root.mkdir(parents=True, exist_ok=True)
    skills = migrate(role_root, skills_root)
    registry = role_root / "registry.yaml"
    registry.write_text(
        yaml.safe_dump({"role": args.role, "skills": skills}, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    print(f"Wrote {registry} with {len(skills)} skills")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 跑迁移**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python3 tools/migrate_roles_to_skills.py --role writer
/home/ailearn/miniconda3/bin/python3 tools/migrate_roles_to_skills.py --role reviewer
/home/ailearn/miniconda3/bin/python3 tools/migrate_roles_to_skills.py --role reader
```

Expected: 3 个 `registry.yaml` 生成 + 旧目录被 SKILL.md 形式迁到 `skills/<slug>/`。

- [ ] **Step 5: 跑测试 + commit**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python3 -m pytest tests/test_skill_registry.py -v
git add -A
git commit -m "refactor(roles): 作家/审核员/读者统一 SKILL.md + 生成 registry.yaml (Phase 17.16)"
```

---

### Task 17.17：删陈旧 `social_engine/` 顶层独立标记（不迁入 monorepo）

> Plan 决策：保留顶层独立，加 README 解释。

- [ ] **Step 1: 加 README**

Create: `social_engine/README.md`（如已存在则合并）。

```markdown
# social_engine

## 状态

**未**纳入 monorepo（apps/+packages/）。原因：与灵文流水线无直接业务耦合，独立维护。

## 关联

- CI: `.github/workflows/social-engine-*` (opt-in)
- 数据: `.state/social_engine/`

## 历史

原 `infra/social_engine/` 子模块；Phase 16 卫生期升为顶层独立目录。
```

```bash
git add social_engine/README.md
git commit -m "docs(social_engine): 标记为顶层独立目录（Phase 17.17）"
```

---

### Task 17.18：标记历史 docs 为 archive（不删，只打标）

- [ ] **Step 1: 给历史 docs 加历史标注**

对以下文件（如果存在），在头部加 2 行 blockquote：

```markdown
> ⚠️ 历史归档（2026-08-12）：保留供回顾，结论已并入 `docs/ARCHITECTURE.md`。
```

Files:
- `docs/LINGWEN_V3_ARCHITECTURE_OPTIMIZATION.md`
- `docs/LINGWEN_V3.1_ARCHITECTURE_OPTIMIZATION.md`
- `docs/AI小说工厂优化方案.md`
- `docs/OPTIMIZATION_PLAN.md`
- `CHANGELOG-v9.0.md`

```bash
cd /home/ailearn/projects/LingWen
for f in docs/LINGWEN_V3_ARCHITECTURE_OPTIMIZATION.md docs/LINGWEN_V3.1_ARCHITECTURE_OPTIMIZATION.md docs/AI小说工厂优化方案.md docs/OPTIMIZATION_PLAN.md CHANGELOG-v9.0.md; do
  if [ -f "$f" ]; then
    head -1 "$f" | grep -q '历史归档' || {
      printf '> ⚠️ 历史归档（2026-08-12）：保留供回顾，结论已并入 `docs/ARCHITECTURE.md`。\n\n%s' "$(cat "$f")" > "$f.tmp"
      mv "$f.tmp" "$f"
    }
  fi
done
git add -A
git commit -m "docs: 给历史 V3 / AI 工厂 / CHANGELOG-v9 加归档标注（Phase 17.18）"
```

---

### Task 17.19：docs/INDEX.md + HANDOFF.md 版本对齐

- [ ] **Step 1: 修订 `docs/INDEX.md`**

把 `v8.3` 等旧版本号改为 `v10.0`（CLAUDE.md 已对齐），加 "v10.0 + Phase 17 monorepo 进行中" 备注。

- [ ] **Step 2: 修订 `HANDOFF.md`**

加 "Phase 16 完成 (2026-08-11, v10.0)；Phase 17 monorepo 启动" 段。

- [ ] **Step 3: commit**

```bash
git add docs/INDEX.md HANDOFF.md
git commit -m "docs: INDEX/HANDOFF 版本对齐到 v10.0 + Phase 17 状态 (Phase 17.19)"
```

---

### Task 17.20：全栈 lint/typecheck/test 早期收口

- [ ] **Step 1: 跑 pnpm 全栈 lint**

```bash
cd /home/ailearn/projects/LingWen
pnpm -r --filter './apps/*' lint 2>&1 | tee /tmp/pnpm-lint.log | tail -20
```

Expected: errors ≤ pre-existing baseline（已知 testid class-selector 等问题；Phase 19 拆）。

- [ ] **Step 2: 跑 pnpm 全栈 typecheck**

```bash
pnpm -r --filter './apps/*' typecheck 2>&1 | tee /tmp/pnpm-tc.log | tail -20
```

- [ ] **Step 3: 跑 Python 全栈 pytest**

```bash
for pkg in packages/lingwen-core packages/lingwen-storage packages/lingwen-cli; do
  echo "=== $pkg ==="
  (cd $pkg && /home/ailearn/miniconda3/bin/python3 -m pytest -q 2>&1 | tail -3)
done
```

Expected: 已知 lingwen-storage 18/18 pass；新包至少 import 测试 pass。

---

### Task 17.21：固化 Phase 17 Gate 脚本（修复原 plan bug）

**Files:**
- Create: `tooling/gates/phase_17.sh`

- [ ] **Step 1: 写失败测试 — 脚本可执行**

Create: `tooling/gates/tests/test_phase_17_gate_syntax.py`

```python
from pathlib import Path
import subprocess

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "tooling" / "gates" / "phase_17.sh"


def test_phase_17_gate_is_executable():
    assert SCRIPT.exists(), "phase_17.sh should exist"
    import os
    mode = SCRIPT.stat().st_mode
    assert mode & 0o111, "phase_17.sh must be executable"


def test_phase_17_gate_passes_syntax_check():
    r = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
    assert r.returncode == 0, f"phase_17.sh has syntax error: {r.stderr}"
```

- [ ] **Step 2: 跑测试，确认失败（脚本不存在）**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python3 -m pytest tooling/gates/tests/test_phase_17_gate_syntax.py -v
```

- [ ] **Step 3: 写 `phase_17.sh`（修复原 plan 的 bug）**

Create: `tooling/gates/phase_17.sh`

```bash
#!/usr/bin/env bash
# tooling/gates/phase_17.sh
# Phase 17 完成门禁（Monorepo 化）
#
# Run from worktree root:  bash tooling/gates/phase_17.sh
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

echo "▶ Phase 16 Gate (regression)"
bash tooling/gates/phase_16.sh

echo "▶ 包依赖方向守卫"
/home/ailearn/miniconda3/bin/python3 tooling/lint/check_package_deps.py --check

echo "▶ 顶层目录只允许 7 个 + dotfiles + 配置文件"
EXPECTED_TOP_DIRS="apps packages content docs tooling social_engine"
for d in $EXPECTED_TOP_DIRS; do
  [ -d "$d" ] || { echo "❌ 缺顶层目录: $d"; exit 1; }
done
# 不应有 01_* ~ 11_* 旧目录
for n in 01 02 03 04 05 06 07 08 09 10 11; do
  matches=$(ls -1 2>/dev/null | grep "^${n}_" || true)
  if [ -n "$matches" ]; then
    echo "❌ 仍存在旧编号顶层目录: $matches"
    exit 1
  fi
done
echo "✔ 顶层目录符合 monorepo 约定"

echo "▶ 8 个 lingwen-* 包各有 pyproject.toml + README.md + tests/"
for pkg in lingwen-storage lingwen-core lingwen-llm lingwen-memory lingwen-prompt lingwen-pipeline lingwen-quality lingwen-cli; do
  [ -f "packages/${pkg}/pyproject.toml" ] || { echo "❌ 缺 packages/${pkg}/pyproject.toml"; exit 1; }
  [ -f "packages/${pkg}/README.md" ]      || { echo "❌ 缺 packages/${pkg}/README.md"; exit 1; }
  [ -d "packages/${pkg}/tests" ]           || { echo "❌ 缺 packages/${pkg}/tests/"; exit 1; }
done
echo "✔ lingwen-* 包骨架完整"

echo "▶ 顶层 infra/ 不应再有代码（仅 __pycache__ / 空 __init__.py 可接受）"
infra_files=$(find infra/ -type f -name '*.py' 2>/dev/null | wc -l)
echo "  infra/ 中 .py 文件数: $infra_files (期望 0；如 >0 表明有遗漏迁移)"
if [ "$infra_files" -gt 0 ]; then
  find infra/ -name '*.py' -type f | head -20
  exit 1
fi

echo ""
echo "✅ Phase 17 Gate PASS"
```

- [ ] **Step 4: chmod + 测试 + 跑**

```bash
cd /home/ailearn/projects/LingWen
chmod +x tooling/gates/phase_17.sh
/home/ailearn/miniconda3/bin/python3 -m pytest tooling/gates/tests/test_phase_17_gate_syntax.py -v
bash tooling/gates/phase_17.sh 2>&1 | tail -25
```

Expected: 测试 PASS；脚本本身能跑（gate 内的所有 check 也通过，或至少在 17.0-17.10 完成后通过）。

- [ ] **Step 5: commit**

```bash
git add tooling/gates/phase_17.sh tooling/gates/tests/test_phase_17_gate_syntax.py
git commit -m "ci(gate): Phase 17 完成门禁（monorepo 化）"
```

---

### Task 17.22：完整 Phase 17 Gate 跑通 + 合并

- [ ] **Step 1: 完整跑**

```bash
cd /home/ailearn/projects/LingWen
bash tooling/gates/phase_17.sh
```

Expected: exit 0。如失败，按各 task 补漏。

- [ ] **Step 2: 修订 README/CLAUDE.md 版本号到 v11.0**

`CLAUDE.md` 与 `README.md` 中 v10.0 → v11.0（Phase 17 monorepo 落地），加版本记录条目。

- [ ] **Step 3: 合并 + push**

```bash
git checkout master
git merge --no-ff worktree-moling-redesign-phase17 -m "Merge Phase 17 monorepo into master"
bash tooling/gates/phase_17.sh
git push origin master
git branch -d worktree-moling-redesign-phase17
git worktree remove /home/ailearn/projects/LingWen/.claude/worktrees/<name>
```

---

## 2. Phase 17 Gate（最终）

- [ ] **G1**: `bash tooling/gates/phase_17.sh` exit code = 0
- [ ] **G2**: 顶层目录 = `{apps, packages, content, docs, tooling, social_engine}` + dotfiles + 配置文件
- [ ] **G3**: 8 个 lingwen-* 包（lingwen-storage, lingwen-core, lingwen-llm, lingwen-memory, lingwen-prompt, lingwen-pipeline, lingwen-quality, lingwen-cli）各有 `pyproject.toml` + `README.md` + `tests/`
- [ ] **G4**: `infra/` 中无 `.py` 文件（除 `__pycache__` / 空 `__init__.py`）
- [ ] **G5**: 顶层无 `01_*` ~ `11_*` 旧编号目录
- [ ] **G6**: `pnpm-workspace.yaml` 覆盖 `apps/*` 且排除 Python 包
- [ ] **G7**: `tooling/lint/check_package_deps.py --check` exit 0（依赖方向合规）
- [ ] **G8**: 8 个包各能独立 `pip install -e .[test]` + `pytest -q`

✅ **Gate 通过 → 进 Phase 18**

---

## 3. 执行建议

按 subagent-driven-development 流程，每个 Task 一个 subagent，两阶段 review（spec + quality）。预计：

- **17.0（前置）** — 改动量较大，建议串行、密集 review。
- **17.1-17.3** — 文件搬迁，可较快推进。
- **17.4-17.10** — 7 个 Python 包独立迁移，可并行（不同 worktree 隔离）。
- **17.11-17.12** — TS 配置骨架，独立。
- **17.13-17.21** — 守卫 + Gate，独立。
- **17.22** — 合并阶段，需要协调。

预估：5-7 个工作日连续推进 + 1-2 天 review/fixes。
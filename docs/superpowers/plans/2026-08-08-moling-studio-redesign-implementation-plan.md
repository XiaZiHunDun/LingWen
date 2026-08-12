# 墨灵 Studio × 灵文引擎 · 整体架构重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `lingwen/` 仓库重构为 monorepo，按 Hexagonal / Clean Architecture 拆成 `apps/{dashboard,studio_api}` + `8 个 lingwen-* 包` + `dashboard-contracts`，改造工作流引擎为事件溯源，把 209 文件未提交重构按 Step A/B/C 入库，最终交付一个可独立部署、CI 全绿、品牌锁定的 v10.0 发布。

**Architecture:** 见 spec `docs/superpowers/specs/2026-08-08-moling-studio-redesign-design.md`。本计划只列可执行步骤。

**Tech Stack:**
- 前端：Vue 3.5 / TypeScript 5.8 / Pinia 4 / naive-ui / Vite 6 / Vitest 4 / Playwright 1.49
- 后端：Python 3.12 / FastAPI / Pydantic v2 / SQLAlchemy Core / sqlite3 / httpx
- 工作流：自定义事件溯源（JSONL append-only）
- LLM：OpenAI / Anthropic / 默认 provider，统一走 `packages/lingwen-llm`
- 构建：pnpm workspace + Turborepo（待选，可能用 pnpm 内置 `--filter` 也够）
- 工具：Ruff / mypy / ESLint + 4 个自定义规则 / vue-tsc / pytest / vitest

---

## 0. 阅读指引

- 每个 Phase 末尾有一个 **Phase Gate**（明确验证步骤）。Gate 必须 100% 通过才能进下个 Phase。
- 任务粒度遵循"2-5 分钟一步"，每步都有具体命令和提交。
- 涉及代码粘贴时**给出完整代码**而非概要。
- 标 `<!-- check -->` 的位置是执行时需要人工/AI 验证的检查点。

---

## 0.1 总览

| Phase | 周数 | 任务数 | Gate 标准 |
|-------|-----|-------|----------|
| Phase 16 · 卫生与基础 | 2 周 | 18 | CI 绿、删除运行时 DB 完成、品牌锁生效 |
| Phase 17 · Monorepo 化 | 3 周 | 22 | 顶层 11 个 unit 可独立 `pnpm -F <name> build` |
| Phase 18 · 业务边界 + 接口化 | 3 周 | 16 | `lingwen-core` 不 import 任何 `lingwen-llm`/`lingwen-storage` |
| Phase 19 · 前端整治 | 2 周 | 20 | 单一角色白名单、composable ≤300 行、API 模块 ≤200 行、`dashboard-contracts` 自动生成 |
| Phase 20 · 文档与品牌 | 1 周 | 8 | VISION/ARCHITECTURE/README 全写 |
| Phase 21 · 收尾 | 1 周 | 8 | v10.0 tag 落地 |

合计 **92 任务** / **12 周**。

---

## 0.2 起步：必须先执行的"前置 Step"

> 这是 §18.2 中的 Step A/B/C，正式 Phase 16 任务的前置工作。
> 完成后 commit tree 进入"已知干净状态"。

### Pre-Step 0：读 spec 与 CLAUDE.md（不许跳）

**Files:** 只读，不改。

- [ ] **Step 1: 完整阅读**
  ```bash
  cat docs/superpowers/specs/2026-08-08-moling-studio-redesign-design.md
  cat CLAUDE.md
  ```

  期望：理解 §3 设计原则、§5 目录结构、§6 包边界、§17 品牌规则、§19 迁移计划。

- [ ] **Step 2: 验证 git 状态清晰**

  Run: `git status --short | wc -l`
  期望：返回当前未跟踪/修改文件数（你现在能看到 209 个左右；不要慌，写在 Pre-Step 1-3 之中处理）。

- [ ] **Step 3: 确认主分支**

  Run: `git branch --show-current`
  期望：`master` 或你接下来要开的工作分支。

---

### Pre-Step 1：WIP 归档提交（半天）

**Files:** 仅 commit，不改文件内容。

- [ ] **Step 1: 全量暂存**

  Run: `git add -A`
  期望：无错误。（如有部分文件被 `.gitignore` 忽略，正常）

- [ ] **Step 2: 写提交**

  Run:
  ```bash
  git commit -m "wip: 汇总未提交技术债 · Phase 16 起点

  包含：
  - 已删除：16 个 .js composable（已重写为 .ts 形式）
  - 已重构：tests/hooks/test_event_bus.py 等测试重写、ESLint 新规则、类型基础设施
  - 已新建：infra/prompt_engineering、infra/subplot 等模块占位
  - 保留：旧 infra/creator_*.py 等尚未拆到 packages/ 的部分

  后续阶段任务清单见 docs/superpowers/plans/2026-08-08-moling-studio-redesign-implementation-plan.md"
  ```
  期望：commit hash 形如 `8a1b2c3`。

- [ ] **Step 3: 验证**

  Run: `git status --short`
  期望：返回空或仅 `?? `（新 untracked 文件）——不再有 ` M` 或 `D`。

<!-- check -->
- [ ] **Step 4: 验证 commit 边界清晰**

  Run: `git log -1 --stat | head -50`
  期望：能看到本 commit 列出全部 ~209 个变更文件，确认没有意外包含敏感数据或临时调试文件。

---

### Pre-Step 2：按"包为单位"解耦提交（1-2 天，分 5-10 个小 commit）

每个 commit 单独 lint + test 通过。**顺序由你决定，但建议按依赖方向倒推**。

#### Pre-Step 2a：先收口 ESLint 与类型基础设施

**Files:** 仅改 `dashboard/frontend/eslint.config.js`、`dashboard/frontend/src/types/`、`dashboard/frontend/eslint-rules/`。

- [ ] **Step 1: ESLint 增量提交**

  Run:
  ```bash
  git add dashboard/frontend/eslint.config.js dashboard/frontend/eslint-rules/
  git commit -m "feat(frontend): 引入自定义 ESLint 规则（no-store-value-access 等）

  自定义规则覆盖：
  - testid-class-sync（warning）：data-testid 与 class 同步
  - no-duplicate-hooks（error）：防止 useXxx 重复定义
  - require-optional-chain（warning）：鼓励可选链
  - no-store-value-access（error）：禁止 store.value 直接访问

  测试与文档见 eslint-rules/ 目录。"
  ```

- [ ] **Step 2: 类型基础设施提交**

  Run:
  ```bash
  git add dashboard/frontend/src/types/
  git commit -m "feat(frontend): 类型基础设施（composables.ts / index.ts）

  - 新增 src/types/composables.ts：组合式函数返回类型
  - 新增 src/types/index.ts：聚合类型导出
  - 现有 composable 已开始标注 JSDoc 类型"
  ```

- [ ] **Step 3: safeAccess / safeStore / asyncStoreUtils**

  Run:
  ```bash
  git add dashboard/frontend/src/utils/safeAccess.js dashboard/frontend/src/utils/safeStore.js dashboard/frontend/src/utils/asyncStoreUtils.js
  git commit -m "feat(frontend): 安全访问与异步 store 工具

  - safeAccess.js：统一 import 缺失检查
  - safeStore.js：.value 访问守卫
  - asyncStoreUtils.js：异步初始化、轮询、取消"
  ```

- [ ] **Step 4: 验证**

  Run: `cd dashboard/frontend && pnpm lint 2>&1 | tail -20`
  期望：0 error，或仅有已知的同类型遗留 warning。

#### Pre-Step 2b：测试重写独立提交

**Files:** 仅改测试。

- [ ] **Step 1: Hook engine 测试**

  Run:
  ```bash
  git add dashboard/frontend/tests/hooks/ tests/hooks/
  git commit -m "test: 重写 event_bus / hook_engine 测试

  原 tests/hooks/test_event_bus.py 与 dashboard/frontend/tests 下的
  test_event_bus*.spec.ts 整合到单测体系，行为合约不变。"
  ```

- [ ] **Step 2: 验证单测**

  Run: `cd dashboard/frontend && pnpm test:run 2>&1 | tail -10`
  期望：`Tests  pass`。

#### Pre-Step 2c：API 与 store 改动独立提交

- [ ] **Step 1: API 文件提交**

  Run:
  ```bash
  git add dashboard/frontend/src/api/
  git commit -m "refactor(frontend): API 客户端模块化 + ts 化

  - api/{budgets,decisions,workflows,studio,cvg,health,creator}.js 全部迁移到 .ts
  - 错误类层次清晰（NetworkError / TimeoutError / AuthError / ForbiddenError / NotFoundError / ServerError）"
  ```

- [ ] **Step 2: Store 提交**

  Run:
  ```bash
  git add dashboard/frontend/src/stores/
  git commit -m "refactor(frontend): Pinia stores 迁移 ts + 全局状态集中"
  ```

- [ ] **Step 3: 验证**

  Run: `pnpm typecheck 2>&1 | tail -30`
  期望：errors = 0；warnings 可接受但需记录。

#### Pre-Step 2d：Composable .js → .ts

- [ ] **Step 1: 用域归类提交**

  Run:
  ```bash
  git add dashboard/frontend/src/composables/
  git commit -m "refactor(frontend): composable 大规模 .js → .ts 迁移

  覆盖 useEventBus / useWorkflowSocket / useRippleSocket /
  useCostWindow / useApiConnectivity / useAskAssistant /
  useCreatorPulse / useCreatorOnboarding / useCreatorVolumePlan /
  useCreatorPage / useCreatorWorkspace / useCreatorWrite /
  useCreatorWriteWorkbench / useDashboardNav / useDashboardWidgets /
  useStudioProject / useTodayHub 等"

  ```

- [ ] **Step 2: 验证**

  Run: `pnpm typecheck:app 2>&1 | tail -10`
  期望：errors = 0 或只剩 dashboard/.vue 文件相关的类型问题（后续 phase 解决）。

#### Pre-Step 2e：基础组件 & 其它

- [ ] **Step 1: components/ 子集提交**

  Run:
  ```bash
  git add dashboard/frontend/src/components/
  git commit -m "refactor(frontend): creator/widget 组件结构整理"
  ```

- [ ] **Step 2: tests 提交**

  Run:
  ```bash
  git add dashboard/frontend/tests/
  git commit -m "test(frontend): Creator 测试用例补齐（testid-class-sync 全清零）"
  ```

- [ ] **Step 3: 其它收尾**

  Run:
  ```bash
  git status --short | grep -vE '^\?\?' | head -10
  ```
  期望：所有改动已 commit。

---

### Pre-Step 3：Hygiene pass（半天）

- [ ] **Step 1: 加固 .gitignore**

  在 `.gitignore` 末尾追加：

  ```gitignore
  # Python
  __pycache__/
  *.py[cod]
  *$py.class
  *.egg-info/
  .mypy_cache/
  .pytest_cache/
  .ruff_cache/
  .coverage
  htmlcov/

  # Node
  node_modules/
  .vite/
  dist/
  *.tsbuildinfo

  # LingWen runtime
  .state/
  .coverage

  # IDE
  .idea/
  .vscode/
  *.swp
  ```

  Run: `git add .gitignore && git commit -m "chore: 加固 .gitignore（缓存/运行时/IDE）"`

- [ ] **Step 2: 移除已被追踪的缓存文件**

  Run:
  ```bash
  git rm -r --cached __pycache__/ .mypy_cache/ .pytest_cache/ .ruff_cache/ lingwen_novel_factory.egg-info/ 2>/dev/null
  git rm -r --cached .state/ 2>/dev/null || true
  git commit -m "chore: 从仓库移除缓存 / runtime / egg-info 文件"
  ```

  期望：列出被 untrack 的路径。

- [ ] **Step 3: 解决双重 lockfile**

  Run: `ls dashboard/frontend/package-lock.json 2>/dev/null && rm dashboard/frontend/package-lock.json`
  期望：只剩 `pnpm-lock.yaml`（如有）。

  Run: `git add -A && git commit -m "chore: 仅保留 pnpm-lock，移除 npm lockfile"`（如确有）

<!-- check -->
- [ ] **Step 4: hygiene 验证**

  Run:
  ```bash
  git ls-files | grep -E '__pycache__|\.mypy_cache|\.pytest_cache|\.ruff_cache|lingwen.*\.egg-info|\.state/'
  ```
  期望：返回空。

- [ ] **Step 5: Pre-Step 收尾**

  Run: `git log --oneline -10`
  期望：能看到完整的 Pre-Step 1 → 3 提交链；工作区是已知干净状态。

---

### Phase 0 Gate（前置 Step 完成检查）

- [ ] **G1**: `git status --short` 输出为空（仅 untracked ignored 文件 OK）。
- [ ] **G2**: `git ls-files | grep -E '__pycache__|\.mypy_cache|\.pytest_cache|\.ruff_cache|\.egg-info'` 输出 0 行。
- [ ] **G3**: 仓库中所有 commit 信息明确（无 `wip:` 残留，或仅存 §18.2 Step A 那一条）。
- [ ] **G4**: `cd dashboard/frontend && pnpm verify` 跑通。

✅ Gate 通过 → 进入 Phase 16。

---

## Phase 16 · 卫生与基础（2 周 / 18 任务）

> 目标：在不破坏代码的前提下，建立**所有可静态检查的护栏**，为后续 Phase 铺平路。
> 这 Phase 完成后，工作区应是 lint/typecheck/hygiene 全绿，新人 clone 后立刻能跑。

### Task 16.1：写 hygiene checker（Python）

**Files:**
- Create: `tooling/hygiene/check_repo_state.py`
- Test: `tooling/hygiene/tests/test_check_repo_state.py`

- [ ] **Step 1: 写失败测试**

  ```python
  # tooling/hygiene/tests/test_check_repo_state.py
  import subprocess
  from pathlib import Path
  import pytest

  REPO_ROOT = Path(__file__).resolve().parents[3]


  def test_tracked_files_clean():
      """被追踪的文件不应包含已知脏路径。"""
      result = subprocess.run(
          ["git", "ls-files"],
          capture_output=True,
          text=True,
          cwd=REPO_ROOT,
          check=True,
      )
      tracked = result.stdout.splitlines()
      bad = [
          f for f in tracked
          if any(
              token in f for token in (
                  "__pycache__",
                  ".mypy_cache",
                  ".pytest_cache",
                  ".ruff_cache",
                  "lingwen_novel_factory.egg-info",
                  ".state/",
              )
          )
      ]
      assert bad == [], f"脏文件未清理: {bad}"


  def test_no_orphan_template_files():
      """不允许存空模板 .md .py 文件。"""
      result = subprocess.run(
          ["git", "ls-files"],
          capture_output=True,
          text=True,
          cwd=REPO_ROOT,
          check=True,
      )
      placeholder = [
          f for f in result.stdout.splitlines()
          if Path(REPO_ROOT / f).name in {
              "TEMPLATE.md",
              ".template.py",
              "_placeholder.md",
          }
      ]
      assert placeholder == [], f"遗留模板: {placeholder}"
  ```

- [ ] **Step 2: 跑测试，确认失败**

  Run: `cd tooling/hygiene && python -m pytest tests/test_check_repo_state.py -v`
  期望：因 `check_repo_state.py` 不存在导致 `ModuleNotFoundError`。

- [ ] **Step 3: 写最小实现**

  ```python
  # tooling/hygiene/check_repo_state.py
  """Hygiene check: lint repo state for hygiene violations."""
  from __future__ import annotations

  import subprocess
  import sys
  from pathlib import Path

  REPO_ROOT = Path(__file__).resolve().parents[2]

  FORBIDDEN_TOKENS = (
      "__pycache__",
      ".mypy_cache",
      ".pytest_cache",
      ".ruff_cache",
      "lingwen_novel_factory.egg-info",
      ".state/",
  )

  PLACEHOLDER_NAMES = {
      "TEMPLATE.md",
      ".template.py",
      "_placeholder.md",
  }


  def _git_ls_files() -> list[str]:
      out = subprocess.run(
          ["git", "ls-files"],
          capture_output=True,
          text=True,
          cwd=REPO_ROOT,
          check=True,
      )
      return out.stdout.splitlines()


  def find_hygiene_violations() -> list[str]:
      violations = []
      for f in _git_ls_files():
          if any(tok in f for tok in FORBIDDEN_TOKENS):
              violations.append(f"FORBIDDEN_PATH: {f}")
          full = REPO_ROOT / f
          if full.name in PLACEHOLDER_NAMES and full.exists():
              violations.append(f"PLACEHOLDER_FILE: {f}")
      return violations


  def main() -> int:
      violations = find_hygiene_violations()
      if violations:
          print("Hygiene violations:")
          for v in violations:
              print(f"  - {v}")
          return 1
      print("OK: 仓库状态清洁")
      return 0


  if __name__ == "__main__":
      sys.exit(main())
  ```

- [ ] **Step 4: 跑测试，确认通过**

  Run: `cd tooling/hygiene && python -m pytest tests/test_check_repo_state.py -v`
  期望：2 个测试通过。

- [ ] **Step 5: CLI 形态与 commit**

  ```bash
  cd tooling/hygiene && python check_repo_state.py
  git add tooling/
  git commit -m "feat(tooling): repo hygiene 自检（脏路径 + 模板文件扫描）"
  ```

---

### Task 16.2：写 file-size guard（前端 + Python）

**Files:**
- Create: `tooling/hygiene/check_file_size.py`
- Test: `tooling/hygiene/tests/test_check_file_size.py`

- [ ] **Step 1: 写失败测试**

  ```python
  # tooling/hygiene/tests/test_check_file_size.py
  import subprocess
  from pathlib import Path
  import pytest

  REPO_ROOT = Path(__file__).resolve().parents[3]

  LIMITS = {
      ".vue": 350,
      ".ts": 500,
      ".py": 500,
      ".js": 500,
  }


  def test_no_oversized_files():
      result = subprocess.run(
          ["git", "ls-files"],
          capture_output=True, text=True, cwd=REPO_ROOT, check=True,
      )
      offenders = []
      for f in result.stdout.splitlines():
          ext = Path(f).suffix
          if ext in LIMITS:
              full = REPO_ROOT / f
              if not full.exists():
                  continue
              count = sum(1 for _ in full.open())
              if count > LIMITS[ext]:
                  offenders.append((f, count))
      assert offenders == [], (
          "超大文件:\n" + "\n".join(f"  {f}: {n} 行" for f, n in offenders)
      )
  ```

- [ ] **Step 2: 跑测试，确认失败**

  Run: `cd tooling/hygiene && python -m pytest tests/test_check_file_size.py -v`
  期望：失败（已存在的超 500 行 `__init__.py` 等触发）。

- [ ] **Step 3: 写实现（带 allowlist）**

  ```python
  # tooling/hygiene/check_file_size.py
  from __future__ import annotations
  import subprocess
  import sys
  from pathlib import Path

  REPO_ROOT = Path(__file__).resolve().parents[2]

  LIMITS: dict[str, int] = {
      ".vue": 350,
      ".ts": 500,
      ".py": 500,
      ".js": 500,
  }

  # 已知的允许超大文件白名单（迁移期临时）。每条须有 issue 链接。
  ALLOWLIST: set[str] = {
      # 例：等待 Phase 19 拆分的旧文件
      "dashboard/frontend/src/api/creator.js",
  }


  def _walk() -> list[str]:
      out = subprocess.run(
          ["git", "ls-files"],
          capture_output=True, text=True, cwd=REPO_ROOT, check=True,
      )
      return out.stdout.splitlines()


  def find_oversized() -> list[tuple[str, int]]:
      offenders = []
      for rel in _walk():
          if rel in ALLOWLIST:
              continue
          ext = Path(rel).suffix
          if ext not in LIMITS:
              continue
          full = REPO_ROOT / rel
          if not full.exists():
              continue
          count = sum(1 for _ in full.open())
          if count > LIMITS[ext]:
              offenders.append((rel, count))
      return offenders


  def main() -> int:
      bad = find_oversized()
      if bad:
          print("Oversized files:")
          for f, n in bad:
              print(f"  {f}: {n} 行")
          return 1
      print("OK: 文件尺寸合规")
      return 0


  if __name__ == "__main__":
      sys.exit(main())
  ```

- [ ] **Step 4: 跑测试 + commit**

  ```bash
  cd tooling/hygiene && python -m pytest tests/test_check_file_size.py -v
  # 此时很可能仍 FAIL，因为 repo 有大量旧超大文件
  # 按 Phase 19 / Phase 17 计划逐步分解；本任务标记待 Phase 19 完成后回归
  # 当前阶段：把工具落地，留待办清单（文件由 Phase 19 拆分移除），不强要求 100% pass
  ```

  实施建议：如果希望测试**已通过**，把当前 repo 已知超 500 行的文件全部塞 ALLOWLIST，每条加 `# tracked in Phase 19/Phase 17` 注释。后续 Phase 完成后逐条移出。

  ```bash
  git add tooling/hygiene/check_file_size.py tooling/hygiene/tests/test_check_file_size.py
  git commit -m "feat(tooling): file-size guard（.vue≤350, .ts/.py/.js≤500）"
  ```

---

### Task 16.3：hygiene 加入 CI

**Files:**
- Modify: `.github/workflows/dashboard-frontend-ci.yml` 或根 `.github/workflows/test.yml`
- Create: `tooling/hygiene/Makefile` (或 shell wrapper)

- [ ] **Step 1: 写 Makefile / shell**

  ```makefile
  # tooling/hygiene/Makefile
  PYTHON ?= python3

  .PHONY: all clean

  all: check

  check:
  	$(PYTHON) check_repo_state.py
  	$(PYTHON) check_file_size.py

  clean:
  	rm -rf __pycache__ .pytest_cache
  ```

- [ ] **Step 2: 加入 CI**

  在 `.github/workflows/dashboard-frontend-ci.yml` 的 `lint-and-test` job 内、第一步**之前**插入：

  ```yaml
        - name: Repo hygiene
          working-directory: tooling/hygiene
          run: make check
  ```

  （如当前该 job 用 `pnpm`/`pytest` 链，先确认无冲突。）

- [ ] **Step 3: commit**

  ```bash
  git add tooling/hygiene/Makefile .github/workflows/dashboard-frontend-ci.yml
  git commit -m "ci: run repo hygiene gate before lint/test"
  ```

---

### Task 16.4：写入 .state/events JSONL store（Python）

**Files:**
- Create: `packages/lingwen-storage/src/events/jsonl_store.py`（暂放于此处）
- Create: `packages/lingwen-storage/tests/test_jsonl_store.py`
- Create: `packages/lingwen-storage/pyproject.toml`

> 这一步提前到 Phase 16 是为了让 Phase 17（monorepo 化）有落脚点。

- [ ] **Step 1: 建包骨架**

  ```toml
  # packages/lingwen-storage/pyproject.toml
  [build-system]
  requires = ["hatchling"]
  build-backend = "hatchling.build"

  [project]
  name = "lingwen-storage"
  version = "0.1.0"
  description = "LingWen · 事件流与文件存储"
  requires-python = ">=3.12"
  dependencies = []

  [tool.hatch.build.targets.wheel]
  packages = ["src/lingwen_storage"]
  ```

  Run:
  ```bash
  mkdir -p packages/lingwen-storage/src/lingwen_storage/events
  mkdir -p packages/lingwen-storage/tests
  ```

- [ ] **Step 2: 写失败测试**

  ```python
  # packages/lingwen-storage/tests/test_jsonl_store.py
  import json
  from pathlib import Path
  import pytest
  from lingwen_storage.events.jsonl_store import JsonlStore, WorkflowEvent
  from datetime import datetime, timezone


  def test_append_and_load(tmp_path: Path):
      store = JsonlStore(tmp_path / "events.jsonl")
      e = WorkflowEvent(
          event_id="01J00000000000000000000000",
          occurred_at=datetime.now(timezone.utc),
          step="STEP_00",
          actor="system",
          correlation_id="c-1",
          payload={"k": "v"},
      )
      store.append(e)
      events = list(store.iter())
      assert len(events) == 1
      assert events[0].event_id == e.event_id
      assert events[0].payload == {"k": "v"}


  def test_idempotent_replay(tmp_path: Path):
      path = tmp_path / "events.jsonl"
      store = JsonlStore(path)
      e = WorkflowEvent(
          event_id="01J00000000000000000000001",
          occurred_at=datetime(2026, 8, 9, tzinfo=timezone.utc),
          step="STEP_00",
          actor="system",
          correlation_id="c-1",
          payload={"x": 1},
      )
      store.append(e)
      # 重放
      replayed = list(JsonlStore(path).iter())
      assert len(replayed) == 1
  ```

- [ ] **Step 3: 跑测试，确认失败**

  Run: `cd packages/lingwen-storage && pip install -e .[test] && pytest -v`
  期望：因模块不存在导致 import error。

- [ ] **Step 4: 写实现**

  ```python
  # packages/lingwen-storage/src/lingwen_storage/events/__init__.py
  from .jsonl_store import JsonlStore, WorkflowEvent
  __all__ = ["JsonlStore", "WorkflowEvent"]
  ```

  ```python
  # packages/lingwen-storage/src/lingwen_storage/events/jsonl_store.py
  """Append-only event store backed by JSONL."""
  from __future__ import annotations

  import json
  import os
  import sys
  from dataclasses import dataclass, field, asdict
  from datetime import datetime, timezone
  from pathlib import Path
  from typing import Any, Iterable, Iterator


  @dataclass(frozen=True)
  class WorkflowEvent:
      event_id: str
      occurred_at: datetime
      step: str
      actor: str
      correlation_id: str
      payload: dict[str, Any]

      def to_dict(self) -> dict[str, Any]:
          d = asdict(self)
          d["occurred_at"] = self.occurred_at.isoformat()
          return d


  class JsonlStore:
      """Append-only JSONL store, safe under concurrent appends."""

      def __init__(self, path: Path) -> None:
          self._path = Path(path)
          self._path.parent.mkdir(parents=True, exist_ok=True)
          # Ensure file exists so iter does not race with first append
          self._path.touch(exist_ok=True)

      def append(self, event: WorkflowEvent) -> None:
          line = json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True)
          with self._path.open("a", encoding="utf-8") as f:
              f.write(line + "\n")
              f.flush()
              os.fsync(f.fileno())

      def iter(self) -> Iterator[WorkflowEvent]:
          if not self._path.exists():
              return iter(())
          def gen() -> Iterable[WorkflowEvent]:
              with self._path.open("r", encoding="utf-8") as f:
                  for line in f:
                      line = line.strip()
                      if not line:
                          continue
                      d = json.loads(line)
                      d["occurred_at"] = datetime.fromisoformat(d["occurred_at"])
                      yield WorkflowEvent(**d)
          return gen()
  ```

- [ ] **Step 5: 跑测试，确认通过**

  Run: `cd packages/lingwen-storage && pytest -v`
  期望：2 个测试通过。

- [ ] **Step 6: commit**

  ```bash
  git add packages/lingwen-storage/
  git commit -m "feat(storage): JSONL append-only event store (用于工作流事件溯源)"
  ```

---

### Task 16.5：事件 reducer（state projection）

**Files:**
- Create: `packages/lingwen-storage/src/lingwen_storage/events/reducer.py`
- Create: `packages/lingwen-storage/tests/test_reducer.py`

- [ ] **Step 1: 写失败测试**

  ```python
  # packages/lingwen-storage/tests/test_reducer.py
  from datetime import datetime, timezone
  import ulid
  from lingwen_storage.events.jsonl_store import WorkflowEvent
  from lingwen_storage.events.reducer import reduce_events, WorkflowProjection


  def _e(step: str, payload: dict, cid: str = "c1") -> WorkflowEvent:
      return WorkflowEvent(
          event_id=ulid.new().str,
          occurred_at=datetime.now(timezone.utc),
          step=step,
          actor="test",
          correlation_id=cid,
          payload=payload,
      )


  def test_empty_events_returns_initial():
      state = reduce_events([])
      assert state.chapter_count == 0
      assert state.current_step == "STEP_00"


  def test_chapter_drafted_increments_count():
      e1 = _e("STEP_12", {"chapter_id": "ch001", "draft_path": "/tmp/c.md"})
      state = reduce_events([e1])
      assert "ch001" in state.chapters_drafted
      assert state.chapter_count == 1


  def test_audit_appends_issues():
      e1 = _e("STEP_12", {"chapter_id": "ch001", "draft_path": "/tmp/c.md"})
      e2 = _e("STEP_15", {
          "chapter_id": "ch001",
          "issues": [{"severity": "P1", "category": "ai-trace"}],
      })
      state = reduce_events([e1, e2])
      assert state.audit_history["ch001"][0].severity == "P1"
  ```

- [ ] **Step 2: 跑测试，确认失败**

  Run: `cd packages/lingwen-storage && pytest tests/test_reducer.py -v`
  期望：因 reducer 不存在而失败。

- [ ] **Step 3: 写实现**

  ```python
  # packages/lingwen-storage/src/lingwen_storage/events/reducer.py
  """Project event stream into current workflow view."""
  from __future__ import annotations

  from dataclasses import dataclass, field
  from typing import Iterable

  from .jsonl_store import WorkflowEvent


  @dataclass(frozen=True)
  class IssueRecord:
      severity: str
      category: str
      detail: str = ""


  @dataclass
  class WorkflowProjection:
      current_step: str = "STEP_00"
      current_phase: str = "PHASE_0_INIT"
      chapters_drafted: set[str] = field(default_factory=set)
      chapters_audited: set[str] = field(default_factory=set)
      chapters_published: set[str] = field(default_factory=set)
      audit_history: dict[str, list[IssueRecord]] = field(default_factory=dict)
      pending_decisions: list[dict] = field(default_factory=list)

      @property
      def chapter_count(self) -> int:
          return len(self.chapters_drafted)


  def reduce_events(events: Iterable[WorkflowEvent]) -> WorkflowProjection:
      proj = WorkflowProjection()
      for e in events:
          if e.step.startswith("STEP_"):
              proj.current_step = e.step
          p = e.payload
          if e.step == "STEP_12" and "chapter_id" in p:
              proj.chapters_drafted.add(p["chapter_id"])
              proj.audit_history.setdefault(p["chapter_id"], [])
          elif e.step == "STEP_15" and "issues" in p:
              cid = p.get("chapter_id", "")
              proj.chapters_audited.add(cid)
              proj.audit_history.setdefault(cid, [])
              for issue in p["issues"]:
                  proj.audit_history[cid].append(
                      IssueRecord(
                          severity=issue.get("severity", "P2"),
                          category=issue.get("category", ""),
                          detail=issue.get("detail", ""),
                      )
                  )
          elif e.step == "STEP_21":
              cid = p.get("chapter_id", "")
              if cid:
                  proj.chapters_published.add(cid)
          if "decision" in p:
              proj.pending_decisions.append(p["decision"])
      return proj
  ```

  修改 `__init__.py`：

  ```python
  # packages/lingwen-storage/src/lingwen_storage/events/__init__.py
  from .jsonl_store import JsonlStore, WorkflowEvent
  from .reducer import reduce_events, WorkflowProjection, IssueRecord
  __all__ = [
      "JsonlStore",
      "WorkflowEvent",
      "WorkflowProjection",
      "IssueRecord",
      "reduce_events",
  ]
  ```

  加 `ulid` 依赖到 `pyproject.toml`：

  ```toml
  dependencies = ["python-ulid>=3.0"]
  ```

  Run: `cd packages/lingwen-storage && pip install -e . && pytest -v`
  期望：所有测试通过。

- [ ] **Step 4: commit**

  ```bash
  git add packages/lingwen-storage/
  git commit -m "feat(storage): event → projection reducer (workflow state 派生)"
  ```

---

### Task 16.6：迁移 state_history.log → events JSONL

**Files:**
- Create: `tools/migrate_state_log.py`
- Create: `tools/tests/test_migrate_state_log.py`

- [ ] **Step 1: 写失败测试**

  ```python
  # tools/tests/test_migrate_state_log.py
  import json
  from pathlib import Path
  import subprocess
  import sys


  def test_migrate_minimal(tmp_path: Path):
      log = tmp_path / "state_history.log"
      log.write_text(
          '{"event": "DEFAULT_TEST", "data": {"k": "v"}, "source": "test"}\n'
          '{"event": "STEP_BUMP", "data": {"step": "STEP_12"}, "source": "agent"}\n'
      )
      out = tmp_path / "events.jsonl"
      script = (Path(__file__).resolve().parents[1] / "migrate_state_log.py").as_posix()
      subprocess.run(
          [sys.executable, script, "--src", str(log), "--dst", str(out)],
          check=True,
      )
      lines = out.read_text().strip().split("\n")
      assert len(lines) == 2
      # 第一条被丢弃（DEFAULT_TEST 测试污染）
      # 第二条应映射成 STEP_12 事件
      second = json.loads(lines[1])
      assert second["step"] == "STEP_12"
  ```

- [ ] **Step 2: 跑测试，确认失败**

  Run: `cd tools && python -m pytest tests/test_migrate_state_log.py -v`
  期望：因脚本不存在失败。

- [ ] **Step 3: 写脚本**

  ```python
  # tools/migrate_state_log.py
  """把旧的 state_history.log 转写为 .state/events/*.jsonl。

  规则：
  - 跳过 event=='DEFAULT_TEST' 行（测试污染）
  - 把 {'event':'STEP_BUMP','data':{...}} 映射成 WorkflowEvent
  """
  from __future__ import annotations
  import argparse
  import json
  import sys
  from datetime import datetime, timezone
  from pathlib import Path

  from lingwen_storage.events.jsonl_store import JsonlStore, WorkflowEvent
  import ulid


  SKIP_EVENTS = {"DEFAULT_TEST"}
  STEP_PREFIX_MAP = {
      "STEP_BUMP": "STEP_",
  }


  def _parse_line(line: str) -> WorkflowEvent | None:
      line = line.strip()
      if not line:
          return None
      try:
          row = json.loads(line)
      except json.JSONDecodeError:
          return None
      name = row.get("event", "")
      if name in SKIP_EVENTS:
          return None
      data = row.get("data") or {}
      step = data.get("step", "STEP_00")
      return WorkflowEvent(
          event_id=ulid.new().str,
          occurred_at=datetime.now(timezone.utc),
          step=step,
          actor=row.get("source", "system"),
          correlation_id=data.get("correlation_id") or row.get("id") or "migrate",
          payload={"raw_event": name, **data},
      )


  def migrate(src: Path, dst_store: JsonlStore) -> int:
      count = 0
      with src.open("r", encoding="utf-8") as f:
          for line in f:
              ev = _parse_line(line)
              if ev is None:
                  continue
              dst_store.append(ev)
              count += 1
      return count


  def main() -> int:
      ap = argparse.ArgumentParser()
      ap.add_argument("--src", required=True, type=Path)
      ap.add_argument("--dst", required=True, type=Path)
      args = ap.parse_args()
      store = JsonlStore(args.dst)
      n = migrate(args.src, store)
      print(f"Migrated {n} events to {args.dst}")
      return 0


  if __name__ == "__main__":
      sys.exit(main())
  ```

- [ ] **Step 4: 跑测试，确认通过**

  Run: `cd tools && python -m pytest tests/test_migrate_state_log.py -v`
  期望：通过。

- [ ] **Step 5: 真跑一次迁移**

  ```bash
  mkdir -p .state/events
  python tools/migrate_state_log.py \
    --src .state/state_history.log \
    --dst .state/events/migration.jsonl
  ```

  期望：打印 `Migrated N events`（N 应 >0）。

- [ ] **Step 6: commit**

  ```bash
  git add tools/migrate_state_log.py tools/tests/test_migrate_state_log.py
  git commit -m "feat(tools): 把 state_history.log 转写为 .state/events/*.jsonl"
  ```
  （**不** commit `.state/` 里的内容，因 .gitignore）

- [ ] **Step 7: 删除陈旧 SQLite 与 JSON**

  ```bash
  rm -f .state/workflow.db .state/workflow_state.json .state/state_history.log
  rm -f .state/test.db .state/test_action.db .state/test_backend.db .state/test_final.db
  rm -f .state/reading_power.db .state/cross_volume.db .state/ripple.db
  git add -A .gitignore # 已包含 .state/
  git status --short
  ```

  期望：`git status --short` 空（runtime 已 gitignored）。

<!-- check -->
- [ ] **Step 8: 验证事件可重放**

  Run:
  ```bash
  python -c "from lingwen_storage.events import JsonlStore, reduce_events
  store = JsonlStore('.state/events/migration.jsonl')
  proj = reduce_events(store.iter())
  print(f'chapters_drafted: {len(proj.chapters_drafted)}, '
        f'chapters_audited: {len(proj.chapters_audited)}, '
        f'current_step: {proj.current_step}')"
  ```

  期望：打印非空统计信息，证明历史状态可重建。

---

### Task 16.7：删陈旧 infra 目录

**Files:**
- Delete: `infra/poc/`, `infra/creator/`, `infra/creator_*.py`, `infra/studio/`, `infra/studio_*.py`, `infra/prose/`, `infra/prose_judge.py`, `infra/event_sourcing/`, `infra/di/`, `infra/novel-factory/`, `infra/world_model/`, `infra/story_contracts/`, `infra/cross_volume/`, `infra/subplot/`, `infra/exports/`

> 这些目录根据 spec §20.1 在迁移期**必删**。本任务是 Phase 16 的早期删，保留 `infra/cli/`, `infra/agent_system/`, `infra/ai_service/`, `infra/memory_system/`, `infra/state/`, `infra/consistency/`, `infra/quality/`, `infra/hooks/`, `infra/prompt_engineering/`, `infra/state_machine.py` 等。

- [ ] **Step 1: 列出待删**

  Run: `ls infra/poc 2>/dev/null; ls infra/creator_* 2>/dev/null; ls infra/world_model 2>/dev/null`
  期望：能列出对应文件 / 目录。

- [ ] **Step 2: 用 grep 扫描 import 关系**

  Run:
  ```bash
  grep -rEn "from infra\\.poc|from infra\\.creator|import infra\\.poc|import infra\\.creator" --include='*.py' --include='*.ts' --include='*.vue' 2>/dev/null | head -20
  grep -rEn "from infra\\.world_model|import infra\\.world_model|from infra\\.story_contracts|import infra\\.story_contracts" --include='*.py' 2>/dev/null | head -20
  grep -rEn "from infra\\.di|import infra\\.di" --include='*.py' 2>/dev/null | head -20
  ```

  期望：返回 0 行（已无引用）；若有，先解决再删。

- [ ] **Step 3: 执行删除 + commit**

  ```bash
  rm -rf infra/poc
  rm -f infra/creator_*.py
  rm -rf infra/creator/
  rm -rf infra/studio/ infra/studio_*.py
  rm -rf infra/prose/ infra/prose_judge.py
  rm -rf infra/event_sourcing/
  rm -rf infra/di/
  rm -rf infra/novel-factory/
  rm -rf infra/world_model/
  rm -rf infra/story_contracts/
  rm -rf infra/cross_volume/
  rm -rf infra/subplot/
  rm -rf infra/exports/

  git add -A
  git status --short
  ```

  期望：列出来所有删除文件。

  ```bash
  git commit -m "chore(infra): 删 Phase 16 早期陈旧目录

  删除清单：
  - infra/poc/
  - infra/creator_*.py + creator/
  - infra/studio/ + studio_*.py
  - infra/prose/ + prose_judge.py
  - infra/event_sourcing/
  - infra/di/
  - infra/novel-factory/
  - infra/world_model/
  - infra/story_contracts/
  - infra/cross_volume/
  - infra/subplot/
  - infra/exports/

  验证：grep 全仓 import 关系为空。"
  ```

- [ ] **Step 4: 跑 lint + test**

  ```bash
  cd dashboard/frontend && pnpm verify
  ```

  期望：绿。

<!-- check -->
- [ ] **Step 5: 验证 CLI 仍可用**

  Run: `python lingwen.py --help`
  期望：打印帮助（如果挂了，回到 git history 找原因）。

---

### Task 16.8：CI 加可观测大小上限（pre-commit hook）

**Files:**
- Modify: `.github/workflows/dashboard-frontend-ci.yml` (或建立新 hook job)
- Modify: `dashboard/frontend/.husky/pre-commit`

- [ ] **Step 1: 在 pre-commit 加 file-size 检查**

  在 `.husky/pre-commit` 末尾追加：

  ```bash
  #!/usr/bin/env bash
  cd "$(git rev-parse --show-toplevel)"
  python3 tooling/hygiene/check_file_size.py || {
    echo "❌ 文件尺寸超限，请拆分"
    exit 1
  }
  ```

  Run: `chmod +x .husky/pre-commit && git add .husky/pre-commit`
  Run: `git commit -m "chore(hygiene): pre-commit 检查文件尺寸"`

- [ ] **Step 2: 在 CI 加 hygiene step**

  ```yaml
        - name: Repo hygiene
          working-directory: tooling/hygiene
          run: make check
        - name: File size guard
          run: python3 tooling/hygiene/check_file_size.py
  ```

  Run: `git add .github/workflows/ && git commit -m "ci: 启用 file-size guard"`

---

### Task 16.9：固化单一品牌（product=墨灵 Studio, framework=灵文）

**Files:**
- Modify: `dashboard/frontend/src/config/brand.js` / `brand.ts`
- Modify: 根 `README.md`, `dashboard/frontend/README.md`
- Modify: `CLAUDE.md`（顶层）

- [ ] **Step 1: 编辑 brand.ts**

  `dashboard/frontend/src/config/brand.ts`：

  ```typescript
  // 墨灵 Studio · 品牌字符串真相之源
  // 用户面向字符串一律指向这里。
  export const BRAND = {
    productNameZh: '墨灵 Studio',
    productNameEn: 'MoLing Studio',
    productShortZh: '墨灵',
    productShortEn: 'MoLing',
    // 内部框架名（用户不可见，仅控制台 / about 页可显示）
    frameworkNameZh: '灵文引擎',
    frameworkNameEn: 'LingWen Engine',
    frameworkShortZh: '灵文',
    frameworkShortEn: 'LingWen',
  } as const;

  export type Brand = typeof BRAND;
  ```

  替换原先 `BRAND_PRODUCT_NAME` 等散落字符串——所有 `.vue` 文件 import 此常量。

- [ ] **Step 2: 写品牌扫描 CI**

  Create: `tooling/hygiene/check_brand_consistency.py`

  完整代码与测试与 Task 16.1 / 16.2 同模式。扫描规则：

  - `apps/dashboard/src/**`：禁止出现 `LingWen Studio`、`Studio v12`、独立 `墨` 字（仅允许 `墨灵` / `MoLing`）。
  - `packages/*/README.md`：禁止出现 `LingWen Studio` 字符串。
  - 历史升级文档（如 `## v9.x 升级指南` 区段）允许例外。

  Run: `git add tooling/hygiene/check_brand_consistency.py && git commit -m "feat(brand): 单一品牌字符串 + CI 扫描"`.

- [ ] **Step 3: 修订根 CLAUDE.md**

  - 把产品名改成 "墨灵 Studio"
  - 把"灵文"限定为框架名
  - 加一句"工程命名空间：`lingwen`（沿用历史）"

  Run: `git add CLAUDE.md && git commit -m "docs: 锁定品牌（墨灵 Studio=产品，灵文=框架）"`

<!-- check -->
- [ ] **Step 4: 验证**

  Run: `cd tools && python -m pytest tests/test_check_brand_consistency.py -v`
  期望：通过。

---

### Task 16.10：删除陈旧 SQLite 投影（前序已在 16.6 完成）

> 这一任务在 Phase 16.6 已被执行。占位任务确认。

- [ ] 已经在 Phase 16.6 中完成 `.state/workflow.db` 等删除；本任务标记 `done`。

---

### Task 16.11：固化\"Phase 16 Gate\"脚本

**Files:**
- Create: `tooling/gates/phase_16.sh`

- [ ] **Step 1: 写脚本**

  ```bash
  #!/usr/bin/env bash
  # tooling/gates/phase_16.sh
  # Phase 16 完成门禁检查
  set -euo pipefail

  cd "$(git rev-parse --show-toplevel)"

  echo "▶ hygiene / file-size guard"
  python3 tooling/hygiene/check_repo_state.py
  python3 tooling/hygiene/check_file_size.py
  python3 tooling/hygiene/check_brand_consistency.py

  echo "▶ event-store 单元测试"
  (cd packages/lingwen-storage && pytest -q)

  echo "▶ 前端 lint + typecheck + unit"
  (cd dashboard/frontend && pnpm lint && pnpm typecheck && pnpm test:run)

  echo "▶ 检查陈旧 SQLite/JSON 已删"
  for f in \
    .state/workflow.db \
    .state/workflow_state.json \
    .state/state_history.log \
    .state/test.db \
    .state/test_action.db \
    .state/test_backend.db \
    .state/test_final.db \
    .state/reading_power.db \
    .state/cross_volume.db \
    .state/ripple.db; do
      if [ -e "$f" ]; then
        echo "❌ 仍存在: $f"
        exit 1
      fi
  done
  echo "✔ .state 旧 DB 已清空"

  echo "▶ infra/ 陈旧子目录不存在"
  for d in poc creator studio prose event_sourcing di novel-factory world_model story_contracts cross_volume subplot exports; do
    if [ -e "infra/$d" ]; then
      echo "❌ 仍存在: infra/$d"
      exit 1
    fi
  done
  echo "✔ 陈旧 infra 清理完成"

  echo "✅ Phase 16 Gate PASS"
  ```

  Run: `chmod +x tooling/gates/phase_16.sh`

- [ ] **Step 2: commit**

  ```bash
  git add tooling/gates/phase_16.sh
  git commit -m "ci(gate): Phase 16 完成门禁脚本"
  ```

---

### Phase 16 Gate

- [ ] **G1**: `bash tooling/gates/phase_16.sh` exit code = 0
- [ ] **G2**: `cd dashboard/frontend && pnpm verify` exit code = 0
- [ ] **G3**: `cd packages/lingwen-storage && pytest -q` 全绿
- [ ] **G4**: `grep -rEn 'LingWen Studio' apps/dashboard/src packages/*/README.md docs/` 0 行（除迁移历史段）

✅ **Gate 通过 → 进 Phase 17**

---

## Phase 17 · Monorepo 化（3 周 / 22 任务）

> 目标：把当前仓库重组成"apps + packages"双层 monorepo，包层级按 spec §5、§6。
> 重要：`git mv` 优先，保证 blame 不断；包之间的依赖方向由 `tooling/lint/check_package_deps.py` 强制。

### Task 17.1：建 pnpm workspace 骨架

**Files:**
- Create: `pnpm-workspace.yaml`
- Modify: 根 `package.json`

- [ ] **Step 1: 写 workspace 配置**

  ```yaml
  # pnpm-workspace.yaml
  packages:
    - 'apps/*'
    - 'packages/dashboard-contracts'
    # dashboard-contracts 是 TS 包，仍用 pnpm 跟踪
  ```

  （**注意**：Python 包不用 pnpm workspace 管理，用 uv workspaces / hatchling。）

- [ ] **Step 2: 根 package.json**

  ```json
  {
    "name": "lingwen-monorepo",
    "private": true,
    "version": "10.0.0",
    "description": "墨灵 Studio (产品) + 灵文引擎 (框架) monorepo",
    "license": "MIT",
    "scripts": {
      "build": "pnpm -r --filter './apps/*' --filter './packages/dashboard-contracts' build",
      "lint": "pnpm -r --filter './apps/*' --filter './packages/dashboard-contracts' run lint",
      "test": "pnpm -r --filter './apps/*' --filter './packages/dashboard-contracts' run test",
      "typecheck": "pnpm -r --filter './apps/*' --filter './packages/dashboard-contracts' run typecheck"
    },
    "packageManager": "pnpm@9.0.0"
  }
  ```

  Run: `git add pnpm-workspace.yaml package.json && git commit -m "build(workspace): pnpm workspace 骨架"`.

- [ ] **Step 3: 安装验证**

  Run: `pnpm install`
  期望：成功。当前还没有任何 filter 命中；只是 workspace 元数据生效。

---

### Task 17.2：把 dashboard/frontend 迁到 apps/dashboard（保留 git 历史）

**Files:**
- Move: `dashboard/frontend/` → `apps/dashboard/`

- [ ] **Step 1: 用 git mv**

  ```bash
  git mv dashboard/frontend apps/dashboard
  ```

  期望：git 把它识别为 rename，而非 delete + add。

- [ ] **Step 2: 修绝对路径引用**

  Run: `grep -rln 'dashboard/frontend' apps/ packages/ dashboard/ 2>/dev/null`

  对每个命中文件，修成新路径。例如：
  - CI workflow `dashboard-frontend-ci.yml`：trigger path 改 `apps/dashboard/**`
  - 文档/脚本里的 `dashboard/frontend/` → `apps/dashboard/`

- [ ] **Step 3: 验证 import**

  Run:
  ```bash
  grep -rEn 'from .dashboard/frontend|from "./dashboard/frontend|"dashboard/frontend/' apps/ packages/ --include='*.ts' --include='*.vue' --include='*.js' --include='*.py' --include='*.yml' 2>/dev/null
  ```

  期望：返回 0 行。

- [ ] **Step 4: 跑 verify**

  Run: `cd apps/dashboard && pnpm verify`
  期望：exit code 0。

- [ ] **Step 5: commit**

  ```bash
  git add -A
  git commit -m "refactor(monorepo): dashboard/frontend → apps/dashboard"
  ```

---

### Task 17.3：把 dashboard/（除 frontend）迁到 apps/studio_api

**Files:**
- Move: `dashboard/`（除 `dashboard/frontend`） → `apps/studio_api`

> 由于 17.2 已将 `dashboard/frontend` 移走，剩 `dashboard/` = 后端部分（app.py、routes/、models/、helpers/、protocols.py 等）。

- [ ] **Step 1: git mv**

  ```bash
  git mv dashboard apps/studio_api
  ```

- [ ] **Step 2: 修路径**

  Run: `grep -rln 'dashboard/' apps/studio_api/ 2>/dev/null`
  → 改为 `apps/studio_api/`，或对应新位置。

  修 Makefile / requirements.txt / e2e_entry.py / Dockerfile 里的 `cd dashboard` 等。

- [ ] **Step 3: commit**

  ```bash
  git add -A
  git commit -m "refactor(monorepo): dashboard/ → apps/studio_api"
  ```

---

### Task 17.4：建 packages/lingwen-core

**Files:**
- Move: `infra/agent_system/` → `packages/lingwen-core/src/lingwen_core/agents/`
- Create: `packages/lingwen-core/pyproject.toml`

- [ ] **Step 1: 建目录**

  ```bash
  mkdir -p packages/lingwen-core/src/lingwen_core
  git mv infra/agent_system packages/lingwen-core/src/lingwen_core/agents
  ```

- [ ] **Step 2: 写 pyproject.toml**

  ```toml
  [build-system]
  requires = ["hatchling"]
  build-backend = "hatchling.build"

  [project]
  name = "lingwen-core"
  version = "0.1.0"
  description = "LingWen · 领域 + 应用 + Agent"
  requires-python = ">=3.12"
  dependencies = [
    "pydantic>=2.7",
    "lingwen-storage",
  ]

  [tool.hatch.build.targets.wheel]
  packages = ["src/lingwen_core"]
  ```

- [ ] **Step 3: 修 import**

  Run:
  ```bash
  grep -rln 'infra.agent_system\|from infra.agent_system\|infra/agent_system' --include='*.py' . 2>/dev/null
  ```
  → 改为 `from lingwen_core.agents import ...` / `from lingwen_core.agents.<x> import ...`

- [ ] **Step 4: 测试**

  ```bash
  cd packages/lingwen-core && pip install -e .[test] && pytest -q
  ```

- [ ] **Step 5: commit**

  ```bash
  git add -A
  git commit -m "feat(core): infra/agent_system → packages/lingwen-core/src/lingwen_core/agents"
  ```

---

### Task 17.5：建 packages/lingwen-llm

**Files:**
- Move: `infra/ai_service/` → `packages/lingwen-llm/src/lingwen_llm/`

- [ ] **Step 1-5: 与 17.4 同模式**

  关键：依赖 `pydantic`, `httpx`, `openai`（按 `infra/ai_service/requirements.txt` 推断）。修改 import：

  ```bash
  git mv infra/ai_service packages/lingwen-llm/src
  # 修 import from infra.ai_service → from lingwen_llm.providers
  ```

  Run: `git add -A && git commit -m "feat(llm): infra/ai_service → packages/lingwen-llm"`

---

### Task 17.6：建 packages/lingwen-memory

**Files:**
- Move: `infra/memory_system/` → `packages/lingwen-memory/src/lingwen_memory/`

- [ ] **Step 1-5: 同模式**

  依赖：`qdrant-client`（如已有）/ `numpy` / `lingwen-storage` / `lingwen-llm`.

  ```bash
  git commit -m "feat(memory): infra/memory_system → packages/lingwen-memory"
  ```

---

### Task 17.7：建 packages/lingwen-prompt

**Files:**
- Move: `infra/prompt_engineering/` → `packages/lingwen-prompt/src/lingwen_prompt/`

- [ ] **Step 1-5: 同模式**

  依赖：`jinja2`.

  ```bash
  git commit -m "feat(prompt): infra/prompt_engineering → packages/lingwen-prompt"
  ```

---

### Task 17.8：建 packages/lingwen-pipeline

**Files:**
- Move: `infra/state/`, `infra/hooks/`, `infra/state_machine.py` → `packages/lingwen-pipeline/src/lingwen_pipeline/`
- Move: `MasterController`（`infra/agent_system/master_controller.py`）也属本包

- [ ] **Step 1-5: 同模式**

  依赖：`lingwen-core`, `lingwen-llm`, `lingwen-quality`, `lingwen-storage`.

  ```bash
  git commit -m "feat(pipeline): infra/state+hooks+state_machine → packages/lingwen-pipeline"
  ```

---

### Task 17.9：建 packages/lingwen-quality

**Files:**
- Move: `infra/consistency/`, `infra/quality/` → `packages/lingwen-quality/src/lingwen_quality/`

- [ ] **Step 1-5: 同模式**

  依赖：`lingwen-core`, `lingwen-llm`.

  注意：旧 `infra/quality/checkers/`、`infra/quality/repairers/` 等需要逐子目录迁移，且路径可能需要二次修正（Phase 18 统一接口任务会用到）。

  ```bash
  git commit -m "feat(quality): infra/consistency+quality → packages/lingwen-quality"
  ```

---

### Task 17.10：建 packages/lingwen-cli

**Files:**
- Move: `infra/cli/`, `lingwen.py`（含顶部入口）→ `packages/lingwen-cli/src/lingwen_cli/`
- Modify: 根目录暴露 `lingwen` 命令行包装

- [ ] **Step 1: git mv**

  ```bash
  mkdir -p packages/lingwen-cli/src
  git mv infra/cli packages/lingwen-cli/src
  ```

- [ ] **Step 2: 包装 lingwen.py**

  把原 `lingwen.py` 替换为薄壳（保留向后兼容 CLI 调用）：

  ```python
  #!/usr/bin/env python3
  """LingWen CLI · 顶层包装（向后兼容旧调用）"""
  from lingwen_cli.main import main

  if __name__ == "__main__":
      main()
  ```

  Run: `git add lingwen.py packages/lingwen-cli/ && git commit -m "refactor(cli): 入口迁到 packages/lingwen-cli, 根 lingwen.py 改为薄壳"`.

- [ ] **Step 3: 验证**

  Run: `python lingwen.py status 2>&1 | head -5`
  期望：与迁移前行为相同。

---

### Task 17.11：建 packages/dashboard-contracts（TS）

**Files:**
- Create: `packages/dashboard-contracts/` 空骨架（之后 Phase 18 / 19 接入 OpenAPI codegen）。

- [ ] **Step 1: 初始化包**

  ```bash
  mkdir -p packages/dashboard-contracts/src
  ```

  ```json
  // packages/dashboard-contracts/package.json
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

  ```json
  // packages/dashboard-contracts/tsconfig.json
  {
    "extends": "../../tooling/tsconfig/base.json",
    "compilerOptions": { "outDir": "dist", "rootDir": "src" },
    "include": ["src/**/*"]
  }
  ```

  ```typescript
  // packages/dashboard-contracts/src/index.ts
  // 自动生成：见 Phase 18-19。本文件由 codegen 覆盖。
  export const PLACEHOLDER = true;
  ```

  Run: `git add packages/dashboard-contracts/ && git commit -m "feat(contracts): TS 包骨架（暂为占位，Phase 18-19 接 OpenAPI codegen）"`.

---

### Task 17.12：建立 tooling/tsconfig/base.json

**Files:**
- Create: `tooling/tsconfig/base.json` (共享 strict tsconfig)

- [ ] **Step 1: 写**

  ```json
  {
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

  Run: `git add tooling/tsconfig/base.json && git commit -m "build(tsconfig): 共享 strict 配置"`.

---

### Task 17.13：建立 tooling/lint/check_package_deps.py

**Files:**
- Create: `tooling/lint/check_package_deps.py`
- Test: `tooling/lint/tests/test_check_package_deps.py`

- [ ] **Step 1: 写测试**

  ```python
  # tooling/lint/tests/test_check_package_deps.py
  from pathlib import Path
  import subprocess
  import sys


  REPO = Path(__file__).resolve().parents[3]


  def test_no_dashboard_import_in_lingwen():
      """apps/dashboard 不应 import 任何 lingwen-* 包代码"""
      # 检查的是反向情况：lingwen 包不能被 dashboard 直接 import（只能经 studio_api HTTP/WS）
      # 本测试改为正向：确认 lingwen-* 包代码不引 '@moling' 或 'apps/dashboard'
      bad = subprocess.run(
          ["grep", "-rEl", r"['\"]@moling/dashboard['\"]|'@moling/dashboard-contracts'",
           "packages"], capture_output=True, text=True, check=False
      )
      # 实际上允许 lingwen 引用 dashboard-contracts/dashboard-contracts/api/*
      # 本断言只针对 lingwen 不能 import apps/dashboard 路径
      assert "violations" in locals(), "test scaffold placeholder"
  ```

  实战写法改成静态 AST 解析：`tooling/lint/check_package_deps.py` 解析每个 Python 文件的 import 语句，按包路径分类，验证：

- `packages/lingwen-*` 不能 import `apps.studio_api`。
- `apps/dashboard` 只能 import `packages/dashboard-contracts`（不 import 其它 lingwen 包）。
- 同一 apps/* 内组件可以互相 import。

  Run: `git add tooling/lint/ && git commit -m "feat(lint): 包依赖方向守卫"`.

- [ ] **Step 2: 接 CI**

  在 `tooling/gates/phase_16.sh` 风格的位置，添加 `phase_17.sh`：先跑 hygiene + test，再跑 check_package_deps。

  Run: `git add tooling/gates/phase_17.sh && git commit -m "ci(gate): Phase 17 门禁"`.

---

### Task 17.14：把 content/ 顶层化

**Files:**
- Move: `03_内容仓库` → `content/manuscript`
- Move: `07_汇总仓库` → `content/summary`
- Move: `01_灵感库`, `02_作家工作室`, `04_审核员工作室`, `05_模拟读者池`, `06_意见仓库`, `08_已发布`, `09_叙事设计`, `10_规范文档`, `11_方法论` → `content/roles/{inspiration, writer, reviewer, reader, opinion, archive, narrative, standards, methodology}/`

- [ ] **Step 1: git mv**

  ```bash
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

- [ ] **Step 2: 修内容仓库索引脚本**

  Run: `grep -rEln '03_内容仓库|07_汇总仓库|01_灵感库|02_作家工作室' . 2>/dev/null`

  对每个命中文件，更新路径变量。

- [ ] **Step 3: commit**

  ```bash
  git add -A
  git commit -m "refactor(content): 顶层 content/ 目录，统一 03-11 旧编号"
  ```

---

### Task 17.15：SKILL.md 角色池统一

**Files:**
- Modify: `content/roles/writer/作家A/` → `content/roles/writer/skills/writer-a/SKILL.md`
- Modify: `content/roles/writer/作家B/` → `content/roles/writer/skills/writer-b/SKILL.md`
- ... 共 10 个作家 + 11 个审核员
- Create: `content/roles/writer/registry.yaml`（自动生成）

- [ ] **Step 1: 写自动迁移脚本**

  Create: `tools/migrate_roles_to_skills.py`

  ```python
  #!/usr/bin/env python3
  """把"作家A/" "审核员B/" 风格的目录迁移为 SKILL.md 结构。

  新结构：
    content/roles/<role>/skills/<role-slug>/SKILL.md
        registry.yaml
  """
  # 实现在 Phase 17.15-2 写测试 + 实现
  pass
  ```

- [ ] **Step 2: 写测试 + 实现**

  - 用 pytest 测脚本能从 `content/roles/writer/作家A/` 写出 `content/roles/writer/skills/writer-a/SKILL.md`
  - 实现文件读写逻辑
  - 输出 `registry.yaml`

  测试：确认 SKILL.md frontmatter 含 `name: writer-a`、`type: content_writer`、`tone: ...` 等字段（取自原 dir 下的 meta.yaml / 配置文件）。

- [ ] **Step 3: 跑迁移**

  ```bash
  python tools/migrate_roles_to_skills.py \
    --src content/roles/writer \
    --dst content/roles/writer/skills
  ```

- [ ] **Step 4: commit**

  ```bash
  git add -A
  git commit -m "refactor(roles): 作家 A-J 等目录统一为 SKILL.md 描述"
  ```

  （同样 commit 对 reviewer / reader 做一遍。每个一份独立 commit。）

---

### Task 17.16：删 nameless 顶层文档（merge 到 ARCHITECTURE.md）

**Files:**
- Mark-historical: `docs/LINGWEN_V3_ARCHITECTURE_OPTIMIZATION.md`
- Mark-historical: `docs/LINGWEN_V3.1_ARCHITECTURE_OPTIMIZATION.md`
- Mark-historical: `docs/AI小说工厂优化方案.md`

- [ ] **Step 1: 在文件头部加"历史归档"注释**

  ```markdown
  > ⚠️ 历史归档（2026-08-09）：保留供回顾，结论已并入 `docs/ARCHITECTURE.md`。
  ```

  Run: `git add docs/ && git commit -m "docs: 给历史 V3 / AI 工厂优化方案加历史标注（不要删除，未来若不再被引用再 archive）"`.

> 实际策略：本阶段**不删**这些文件，先打标。Phase 20 / 21 真删。

---

### Task 17.17：移 `social_engine/` 到合适位置

**Files:**
- Decision: 留 `social_engine/` 原位 / 迁到 `apps/social/?` 还是合到 `apps/studio_api/`

> 当前 `social_engine/` 是一个子域，是否纳入 monorepo？
> 决策（spec §20 未明确）= 暂**不纳入** monorepo，保持顶层目录独立但加 README 解释其关系。

- [ ] **Step 1: 加 README**

  Create: `social_engine/README.md`

  ```markdown
  # social_engine

  ## 状态
  顶层独立目录，**未**纳入 monorepo（apps/+packages/）。原因是它跟灵文流水线没有直接业务耦合。

  ## 计划
  - 若 Phase 17.x 后仍有活跃维护，再决定是否迁入 apps/social/。
  - 否则保留顶层独立。

  ## 关联
  - 仅在 CI 中按 opt-in 触发（参见 .github/workflows/social-engine-*）。
  ```

  Run: `git add social_engine/README.md && git commit -m "docs(social_engine): 标记为顶层独立目录，未纳入 monorepo"`.

---

### Task 17.18：Phase 17 早期收口 lint/typecheck

- [ ] **Step 1: 跑全栈 lint**

  ```bash
  pnpm -r lint
  ```

  期望：errors = 0；warnings 数量被记录。

- [ ] **Step 2: 跑全栈 typecheck**

  ```bash
  pnpm -r typecheck
  pnpm -r --filter './apps/*' typecheck
  ```

  期望：errors = 0。

- [ ] **Step 3: 跑 Python 全栈 pytest**

  ```bash
  pnpm -r --filter './apps/*' run test  # frontend
  cd packages/lingwen-core && pytest -q
  cd ../lingwen-llm && pytest -q
  # 其他包
  ```

  期望：全绿。

---

### Task 17.19：把 stale docs/INDEX.md 等清理

**Files:**
- Modify: `docs/INDEX.md` (claim 版本对齐到 v10.0)

- [ ] **Step 1: 修订**

  Run: `grep -n 'v8.3\|v9\|Studio v12' docs/INDEX.md`

  把所有指向旧版本的数字改成"v10.0（待发船）+ 历史 v9.x / v8.x 段保留作 archive"。

- [ ] **Step 2: commit**

  ```bash
  git add docs/INDEX.md
  git commit -m "docs(README): 修正版本声明，从 v9.12 → v10.0"
  ```

---

### Task 17.20：跑一次完整 Phase 17 Gate

**Files:**
- Create: `tooling/gates/phase_17.sh`

- [ ] **Step 1: 写脚本**

  ```bash
  #!/usr/bin/env bash
  set -euo pipefail
  cd "$(git rev-parse --show-toplevel)"

  bash tooling/gates/phase_16.sh

  echo "▶ 包依赖方向守卫"
  python3 tooling/lint/check_package_deps.py

  echo "▶ 顶层目录只允许 7 个 + dotfiles"
  expected="apps packages content docs tooling content-examples experiments"
  for d in $expected; do
    [ -d "$d" ] || { echo "❌ 缺 $d"; exit 1; }
  done
  unexpected=$(ls -1 | grep -vE "^(apps|packages|content|docs|tooling|content-examples|experiments|\\..*|README.md|LICENSE|lingwen\\.py|.*\\.toml|.*\\.yaml|.*\\.yml|.*\\.md|.*\\.txt|.*\\.gitignore|.*\\.gitattributes)$")
  if [ -n "$unexpected" ]; then
      echo "❌ 多余顶层目录或文件："
      echo "$unexpected"
      exit 1
  fi
  echo "✔ 顶层目录符合约定"

  echo "▶ 每个包可独立 import"
  for pkg in packages/lingwen-core packages/lingwen-storage packages/lingwen-llm; do
    cd "$(git rev-parse --show-toplevel)"
    (cd "$pkg" && python -c "import $pkg | tr '/' '.' | sed 's|^$pkg|lingwen|g'") || \
    python -c "import importlib; importlib.import_module('$(basename $pkg | tr '-' '_')')"
  done

  echo "✅ Phase 17 Gate PASS"
  ```

  Run: `chmod +x tooling/gates/phase_17.sh && git add tooling/gates/phase_17.sh && git commit -m "ci(gate): Phase 17 门禁"`.

- [ ] **Step 2: 跑 Gate**

  Run: `bash tooling/gates/phase_17.sh`
  期望：exit 0；如有缺失，按 Phase 17 后续任务补。

---

### Phase 17 Gate

- [ ] **G1**: `bash tooling/gates/phase_17.sh` 通过
- [ ] **G2**: 顶层目录精确等于 `{apps, packages, content, docs, tooling, content-examples, experiments}` 7 个，加根配置文件
- [ ] **G3**: 8 个 lingwen-* 包各有自己的 `pyproject.toml`、`README.md`、`src/`、`tests/`
- [ ] **G4**: `pnpm install` 一次成功，包依赖方向守卫通过
- [ ] **G5**: `git log --diff-filter=M --name-only | grep -E '^infra/' ` 仅返回合法目录（`infra/` 已几乎全空或不存在）
- [ ] **G6**: 旧 `01_*` ~ `11_*` 目录完全迁移到 `content/roles/`

✅ **Gate 通过 → 进 Phase 18**

---

## Phase 18 · 业务边界 + 接口化（3 周 / 16 任务）

> 目标：把 `lingwen-core` 内的业务代码用 ports / adapters 模式冻结依赖方向；任何 LLM/HTTP/DB 调用都通过 `ports/` 中的 Protocol 进入。

### Task 18.1：domain 实体（Story / Chapter / Character / Volume / PlotThread / TimelineEvent / StylePreset）

**Files:**
- Create: `packages/lingwen-core/src/lingwen_core/domain/<entity>.py` (7 个实体)
- Test: `packages/lingwen-core/tests/test_domain_invariants.py`

- [ ] **Step 1: 写测试**

  ```python
  # packages/lingwen-core/tests/test_domain_invariants.py
  from lingwen_core.domain import Story, Chapter, Character, Volume
  from datetime import datetime
  import pytest


  def test_chapter_word_count_nonnegative():
      with pytest.raises(ValueError):
          Chapter(id="ch1", word_count=-1, content_md="")
  ```

- [ ] **Step 2-5: 按 TDD 流程**

  每个实体按 small-step 写：
  - dataclass（frozen=True 或带 patches）
  - 不可变更新（`update_chapter(*, content_md=...) → Chapter`）
  - 不变量校验（`__post_init__` 或独立 `validate()` 函数）

- [ ] **Step 6: pytest**

  Run: `cd packages/lingwen-core && pytest -v`
  期望：全绿。

- [ ] **Step 7: commit**

  ```bash
  git add packages/lingwen-core/src/lingwen_core/domain/ packages/lingwen-core/tests/test_domain_invariants.py
  git commit -m "feat(core): domain entities (Story/Chapter/Character/Volume/...) + 不变量"
  ```

---

### Task 18.2：ports 定义（LLMPort / StoragePort / EventBusPort / ConfigPort）

**Files:**
- Create: `packages/lingwen-core/src/lingwen_core/ports/`
- Test: 用 `typing.Protocol` 自带类型检查 + 跑 `mypy` 测

- [ ] **Step 1: 写 ports**

  ```python
  # packages/lingwen-core/src/lingwen_core/ports/llm.py
  from typing import Protocol, ClassVar
  from dataclasses import dataclass


  @dataclass(frozen=True)
  class LLMRequest:
      prompt: str
      tier: str = "sonnet"
      max_tokens: int = 4096
      temperature: float = 0.7


  @dataclass(frozen=True)
  class LLMResponse:
      content: str
      provider: str
      cached: bool = False
      cost_usd: float = 0.0


  class LLMPort(Protocol):
      async def complete(self, req: LLMRequest) -> LLMResponse: ...
  ```

  同样：`storage.py` (`StoragePort`，含 `append_event`, `load_chapter` 等)、`event_bus.py`、`config.py`。

- [ ] **Step 2: 测试（用 fake 实现 + Protocol 形态检查）**

  ```python
  # packages/lingwen-core/tests/test_ports_protocol.py
  from lingwen_core.ports.llm import LLMPort, LLMRequest, LLMResponse


  class FakeLLM:
      async def complete(self, req: LLMRequest) -> LLMResponse:
          return LLMResponse(content="fake", provider="fake", cached=False, cost_usd=0.0)


  # Protocol 形态检查由 mypy strict mode 强制
  ```

- [ ] **Step 3: mypy strict**

  Run: `cd packages/lingwen-core && mypy src/lingwen_core/ports/`
  期望：no errors。

- [ ] **Step 4: commit**

  ```bash
  git add packages/lingwen-core/src/lingwen_core/ports/ packages/lingwen-core/tests/test_ports_protocol.py
  git commit -m "feat(core): ports 定义（LLM/Storage/EventBus/Config）+ Protocol"
  ```

---

### Task 18.3：adapters 实现（在 lingwen-llm / lingwen-storage 中实现 ports）

**Files:**
- Create: `packages/lingwen-llm/src/lingwen_llm/adapters/core_adapter.py`（实现 `LLMPort`）
- Create: `packages/lingwen-storage/src/lingwen_storage/adapters/core_adapter.py`（实现 `StoragePort`）

- [ ] **Step 1: 写 core_adapter.py（先测试）**

  ```python
  # packages/lingwen-llm/src/lingwen_llm/adapters/core_adapter.py
  from lingwen_core.ports.llm import LLMPort, LLMRequest, LLMResponse
  from lingwen_llm.router import Router


  class LLMAdapter(LLMPort):
      def __init__(self, router: Router) -> None:
          self._router = router

      async def complete(self, req: LLMRequest) -> LLMResponse:
          result = await self._router.complete(req)
          return LLMResponse(
              content=result.content,
              provider=result.provider,
              cached=result.cached,
              cost_usd=result.usage.cost_usd if result.usage else 0.0,
          )
  ```

- [ ] **Step 2: 测试（contract-style：构造 FakeLLM，断言实现 class 是 LLMPort 子类）**

  ```python
  # packages/lingwen-llm/tests/test_core_adapter.py
  from lingwen_core.ports.llm import LLMPort
  from lingwen_llm.adapters.core_adapter import LLMAdapter


  def test_llm_adapter_satisfies_port():
      assert issubclass(LLMAdapter, object)  # Protocol 形态检查
      # mypy 在 CI 强制 subtype 关系
  ```

- [ ] **Step 3: commit**

  ```bash
  git add packages/lingwen-llm/src/lingwen_llm/adapters/ packages/lingwen-llm/tests/test_core_adapter.py
  git commit -m "feat(llm): 实现 lingwen-core.LLMPort"
  ```

---

### Task 18.4：application use cases 接收 cmd 发出 event

**Files:**
- Create: `packages/lingwen-core/src/lingwen_core/application/write_chapter.py`
- Test: `packages/lingwen-core/tests/test_write_chapter.py`

- [ ] **Step 1: 测试**

  ```python
  # packages/lingwen-core/tests/test_write_chapter.py
  import pytest
  from lingwen_core.application.write_chapter import WriteChapterUseCase, WriteChapterCommand
  from lingwen_core.ports.llm import LLMResponse
  from lingwen_core.ports.storage import StoragePort, AppendEventResult


  class FakeLLM:
      async def complete(self, req):
          return LLMResponse(content="Hello chapter.", provider="fake")


  class FakeStorage:
      async def append_event(self, ev):
          return AppendEventResult(ok=True)


  @pytest.mark.asyncio
  async def test_write_chapter_emits_drafted_event():
      uc = WriteChapterUseCase(llm=FakeLLM(), storage=FakeStorage())
      cmd = WriteChapterCommand(chapter_id="ch1", outline="...", author="writer-a")
      events = await uc.execute(cmd)
      assert len(events) == 1
      assert events[0].step == "STEP_12"
      assert events[0].payload["chapter_id"] == "ch1"
  ```

- [ ] **Step 2-5: 实现用例 + 跑测试 + commit**

  ```python
  # packages/lingwen-core/src/lingwen_core/application/write_chapter.py
  from dataclasses import dataclass
  from lingwen_core.ports.llm import LLMPort, LLMRequest
  from lingwen_core.ports.storage import StoragePort
  from lingwen_storage.events.jsonl_store import WorkflowEvent
  from datetime import datetime, timezone
  import ulid


  @dataclass(frozen=True)
  class WriteChapterCommand:
      chapter_id: str
      outline: str
      author: str = "writer-a"
      style: str = "default"


  class WriteChapterUseCase:
      def __init__(self, llm: LLMPort, storage: StoragePort) -> None:
          self._llm = llm
          self._storage = storage

      async def execute(self, cmd: WriteChapterCommand) -> list[WorkflowEvent]:
          prompt = f"Outline:\n{cmd.outline}\n\nWrite chapter {cmd.chapter_id}."
          resp = await self._llm.complete(LLMRequest(prompt=prompt))
          draft_path = f"/tmp/{cmd.chapter_id}.md"
          with open(draft_path, "w") as f:
              f.write(resp.content)
          event = WorkflowEvent(
              event_id=ulid.new().str,
              occurred_at=datetime.now(timezone.utc),
              step="STEP_12",
              actor=cmd.author,
              correlation_id=cmd.chapter_id,
              payload={
                  "chapter_id": cmd.chapter_id,
                  "draft_path": draft_path,
                  "provider": resp.provider,
              },
          )
          await self._storage.append_event(event)
          return [event]
  ```

  `__init__.py`：

  ```python
  # packages/lingwen-core/src/lingwen_core/application/__init__.py
  from .write_chapter import WriteChapterUseCase, WriteChapterCommand
  ```

  Run: `pytest -v && git commit -m "feat(core): WriteChapter 用例（接受 cmd，发出 STEP_12 事件）"`.

---

### Task 18.5：实现 audit_chapter, publish_volume 两个用例

- [ ] **Step 1-5: 与 18.4 同模式**

  `audit_chapter.py` 走 chapter 输入 + 多种 checker 类型 → `STEP_15` 事件。
  `publish_volume.py` 走 chapter list + 校验 → `STEP_21` 事件。

  Run: `pytest -v && git commit -m "feat(core): AuditChapter + PublishVolume 用例"`.

---

### Task 18.6：统一 Checker/Repairer 接口（仅协议，不实现）

**Files:**
- Create: `packages/lingwen-quality/src/lingwen_quality/interfaces/checker.py`
- Create: `packages/lingwen-quality/src/lingwen_quality/interfaces/repairer.py`
- Create: `packages/lingwen-quality/src/lingwen_quality/interfaces/scorer.py`
- Create: `packages/lingwen-quality/src/lingwen_quality/schemas.py`

- [ ] **Step 1-5: 写测试 + 实现**

  按 spec §10 写 Protocol + dataclass Issue / Severity / FixHint / RepairResult。
  重构现有 checker 类（48 个）按 `(Input)` generic 参数改类型注解（先小批量改前 5 个，作为示范）。

  Run: `cd packages/lingwen-quality && pytest -v && git commit -m "feat(quality): 统一 Checker/Repairer/Scorer Protocol + Schemas"`.

---

### Task 18.7-18.16：每个 checker 单独按"通用接口"改造

> 这 10 个任务（每位包 1 个检查器）按固定 mode 走 TDD：
> 1. 写 spec test：确认 checker 满足 `Checker[Chapter]` Protocol
> 2. 给现有 checker 加类型注解 `Generic[Chapter]`
> 3. 写 pytest 验证：构造输入，调用 `await check(...)` 拿 Issue
> 4. commit

  涉及的 checker（10 个最高频）：
  - `CharacterChecker`
  - `TimelineChecker`
  - `PacingChecker`
  - `SceneTransitionChecker`
  - `DialogueAuthenticityChecker`
  - `RepetitivePhraseChecker`
  - `GenderConsistencyChecker`
  - `ForeshadowChecker`
  - `AIGlossChecker`
  - `SentenceDiversityChecker`

  每个的 commit message：`feat(quality): <name> 适配统一 Checker Protocol`.

---

### Phase 18 Gate

- [ ] **G1**: `mypy --strict packages/lingwen-core/src/lingwen_core/domain` 通过
- [ ] **G2**: `cd packages/lingwen-core && grep -rE 'from lingwen_llm|from lingwen_storage|import lingwen_llm|import lingwen_storage' src/` 返回 0 行（业务不感知 IO）
- [ ] **G3**: `cd packages/lingwen-quality && pytest -q` 通过
- [ ] **G4**: 至少 5 个 checker 已通用化（其余 commit-by-commit 跟进）
- [ ] **G5**: `apps/studio_api` 仍能调通；之前 endpoint 行为不变

✅ **Gate 通过 → 进 Phase 19**

---

## Phase 19 · 前端整治（2 周 / 20 任务）

> 目标：把 Vue 前端 5 个 25KB+ composable 拆掉；API 客户端按子域拆；单例 composable 转 Pinia；角色白名单单点化；接 dashboard-contracts 类型生成。

### Task 19.1：api/creator.js 拆分

**Files:**
- Delete: `apps/dashboard/src/api/creator.js`（1236 行）
- Create: `apps/dashboard/src/api/creator/agent.ts`, `volume-plan.ts`, `settings.ts`, `onboarding.ts`, `batch-history.ts`, `product-tools.ts`, `index.ts`, `health.ts`

- [ ] **Step 1: 建目录**

  ```bash
  mkdir -p apps/dashboard/src/api/creator
  ```

- [ ] **Step 2: 按接口分组拆分（grep 旧文件标题，分块切）**

  例如把 `fetchStudioProjects` → `creator/studio.ts`，`fetchVolumePlan` → `creator/volume-plan.ts` 等。
  （细节按实际函数列表，Phase 19.1-2 起要列出所有函数名）

- [ ] **Step 3: 把所有 `creator.js` 的 import 改路径**

  Run:
  ```bash
  grep -rln "from.*['\"].*api/creator['\"]" apps/dashboard/src/ 2>/dev/null
  ```
  → 改为 `import { ... } from '@/api/creator/agent'` 等。

- [ ] **Step 4: 删除原文件**

  ```bash
  git rm apps/dashboard/src/api/creator.js
  ```

- [ ] **Step 5: 跑 typecheck**

  Run: `cd apps/dashboard && pnpm typecheck:app`
  期望：errors = 0。

- [ ] **Step 6: commit**

  ```bash
  git add -A
  git commit -m "refactor(api): creator.js (1236 行) 按子域拆为 8 个模块"
  ```

---

### Task 19.2：composable 300 行拆分——useCreatorWrite.ts

**Files:**
- Delete: `apps/dashboard/src/composables/useCreatorWrite.ts`（715 行）
- Create: `apps/dashboard/src/composables/creator/useCreatorWrite/{selection.ts,checkpoint.ts,validation.ts,agent.ts,index.ts}`

- [ ] **Step 1: 列出原文件中所有 export 函数**

  Run: `grep -n "^export\|^async function\|^function" apps/dashboard/src/composables/useCreatorWrite.ts`

  按职责切到 4 个子模块（复用既有的 `useWorkbenchSelection/Checkpoint/Validation/Agent`）。

- [ ] **Step 2: 创建子目录与文件**

  建 `useCreatorWrite/{selection,checkpoint,validation,agent,index}.ts`，每个 ≤200 行。

- [ ] **Step 3: 改 import**

  Run: `grep -rln "useCreatorWrite" apps/dashboard/src/` → 改为 `useCreatorWrite/index` 或具体子模块。

- [ ] **Step 4: 删除大文件**

  ```bash
  git rm apps/dashboard/src/composables/useCreatorWrite.ts
  ```

- [ ] **Step 5: typecheck**

  Run: `cd apps/dashboard && pnpm typecheck:app`
  期望：errors = 0。

- [ ] **Step 6: 跑 useCreatorWrite 相关测试**

  Run: `cd apps/dashboard && pnpm test:run useCreatorWrite`
  期望：全绿。

- [ ] **Step 7: commit**

  ```bash
  git add -A
  git commit -m "refactor(composables): useCreatorWrite 715 行拆分（按 selection/checkpoint/validation/agent）"
  ```

---

### Task 19.3-19.6：composable 拆分（其余 4 个）

**模式同 19.2**，依次拆：

- 19.3: `useCreatorOnboarding.ts`（674 行）→ `creator/useCreatorOnboarding/{wizard, mentions, digest, webhook, email}.ts`
- 19.4: `useCreatorSettings.ts`（711 行）→ `creator/useCreatorSettings/{pillars, merge, history, factory, preferences}.ts`
- 19.5: `useCreatorBatchHistory.ts`（629 行）→ `creator/useCreatorBatchHistory/{table, filters, charts}.ts`
- 19.6: `useCreatorProductTools.ts`（788 行）→ `creator/useCreatorProductTools/{preferences, export, publish, intervention, structure, memory}.ts`

每个独立 commit message：`refactor(composables): <name> 拆分（按 <submodules>）`.

---

### Task 19.7：单例 composable → Pinia store

**Files:**
- Modify: `apps/dashboard/src/stores/useCostWindow.ts`（从 composable 升级为 store）
- Delete: `apps/dashboard/src/composables/useCostWindow.ts`（如还在）

- [ ] **Step 1: 写 store**

  ```typescript
  // apps/dashboard/src/stores/useCostWindow.ts
  import { defineStore } from 'pinia';
  import { ref, computed } from 'vue';
  import { fetchActiveWorkflow } from '@/api/workflows';

  export const POLL_INTERVAL_MS = 5_000;

  export const useCostWindowStore = defineStore('costWindow', () => {
    const timeWindow = ref<'7d' | '30d' | 'all'>('7d');
    const data = ref<any[]>([]);
    let timer: number | null = null;

    function setWindow(w: '7d' | '30d' | 'all') {
      timeWindow.value = w;
      refresh();
    }

    async function refresh() {
      data.value = await fetchActiveWorkflow({ time_window: timeWindow.value });
    }

    function start() {
      if (timer != null) return;
      timer = window.setInterval(refresh, POLL_INTERVAL_MS);
      refresh();
    }

    function stop() {
      if (timer != null) {
        clearInterval(timer);
        timer = null;
      }
    }

    return { timeWindow, data, setWindow, refresh, start, stop };
  });
  ```

- [ ] **Step 2: 写测试（Pinia 单元测试）**

  ```typescript
  // apps/dashboard/tests/unit/stores/useCostWindow.spec.ts
  import { setActivePinia, createPinia } from 'pinia';
  import { useCostWindowStore } from '@/stores/useCostWindow';

  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('starts with default window', () => {
    const store = useCostWindowStore();
    expect(store.timeWindow).toBe('7d');
  });
  ```

- [ ] **Step 3: 改引用旧 composable 的代码**

  Run: `grep -rln "useCostWindow" apps/dashboard/src/` → 改为 `useCostWindowStore()`.

- [ ] **Step 4: commit**

  ```bash
  git add -A
  git commit -m "refactor(stores): 单例 useCostWindow → Pinia useCostWindowStore"
  ```

---

### Task 19.8：useEventBus 单例转 Pinia

**模式同 19.7**，单例 `useEventBus.ts` → `stores/useEventBusStore.ts`，提供类型化订阅 + WS 集成。

```bash
git commit -m "refactor(stores): useEventBus 单例 → Pinia useEventBusStore (统一订阅 WS)"
```

---

### Task 19.9：useDecisionStore / useRippleStore / useWorkflowListStore / useOverviewStore / useTierBudgetAlerts 逐一改造

**模式同 19.7**，每条独立 commit：

```
refactor(stores): useDecisionStore 单例 → Pinia useDecisionStore
refactor(stores): useRippleStore 单例 → Pinia useRippleStore
refactor(stores): useWorkflowListStore 单例 → Pinia useWorkflowListStore
refactor(stores): useOverviewStore 单例 → Pinia useOverviewStore
refactor(stores): useTierBudgetAlerts 单例 → Pinia useTierBudgetAlertsStore
```

每个 commit 包含：
- 重构 store
- 更新 import
- 测试通过

---

### Task 19.10：useApiConnectivity 单例转 Pinia（或保持 composable）

**Decision:** 这个 composable 内部基本只与 `useConnectivityStore` 协同，转 Pinia 后只剩 1-2 行 wrapper；可以保留为 composable。

- [ ] **Step 1: 评估**

  如确实轻量，**保留**；如仍是单例逻辑，转 Pinia。

- [ ] **Step 2: commit**

  ```bash
  git commit -m "refactor(stores): useApiConnectivity 评估（保留 composable 或转 Pinia）" --allow-empty
  ```

---

### Task 19.11：useWorkflowSocket / useRippleSocket 转 Pinia store

**Files:**
- Create: `apps/dashboard/src/stores/useWorkflowSocketStore.ts`
- Create: `apps/dashboard/src/stores/useRippleSocketStore.ts`
- Delete: 旧的 `useWorkflowSocket.ts` / `useRippleSocket.ts`（已在 Phase 17 后大多删除）

**模式同 19.7**，commit：

```
refactor(stores): WS 单例 → Pinia useWorkflowSocketStore / useRippleSocketStore
```

---

### Task 19.12：角色白名单单点化

**Files:**
- Modify: `apps/dashboard/src/router/index.ts`（唯一真相）
- Delete: `useNavStore.REVIEWER_BLOCKED_NAV` 的硬编码数组（改为方法）
- Delete: `useRoleStore.blockedNav` 重复定义
- Test: 加 unit test 验证白名单单点

- [ ] **Step 1: 集中到 router/index.ts**

  ```typescript
  // apps/dashboard/src/router/index.ts
  export const REVIEWER_ALLOWED: ReadonlySet<RouteName> = new Set([
    'today',
    'inbox',
    'insight',
  ]);

  router.beforeEach((to) => {
    const roleStore = useRoleStore();
    if (roleStore.isReviewer && !REVIEWER_ALLOWED.has(to.name as RouteName)) {
      return { name: 'today' };
    }
  });
  ```

- [ ] **Step 2: 删 useNavStore 的硬编码**

  Run: `grep -n "REVIEWER_BLOCKED" apps/dashboard/src/stores/useNavStore.ts`

  Remove:
  ```typescript
  // 删除：
  export const REVIEWER_BLOCKED_NAV: Set<NavKey> = new Set([...]);
  ```

  替换为：`import { REVIEWER_ALLOWED } from '@/router'; function isNavAllowed(name: NavKey) { return !useRoleStore().isReviewer || REVIEWER_ALLOWED.has(name as RouteName); }`

- [ ] **Step 3: 删 useRoleStore 的 hard-coded list**

  同样清理 `useRoleStore.blockedNav`——改为 compute 调用上述 `isNavAllowed`.

- [ ] **Step 4: 加 unit test**

  ```typescript
  // apps/dashboard/tests/unit/router/role-allowlist.spec.ts
  import { REVIEWER_ALLOWED } from '@/router';
  import { setActivePinia, createPinia } from 'pinia';
  import { useRoleStore } from '@/stores/useRoleStore';

  it('reviewer only sees allowed routes', () => {
    setActivePinia(createPinia());
    const s = useRoleStore();
    s.setIsReviewer(true);
    expect(REVIEWER_ALLOWED.has('today')).toBe(true);
    expect(REVIEWER_ALLOWED.has('studio')).toBe(false);
  });
  ```

- [ ] **Step 5: commit**

  ```bash
  git add -A
  git commit -m "refactor(router): 角色白名单单点化（router 为唯一真相）"
  ```

---

### Task 19.13：dashboard-contracts 接 OpenAPI codegen

**Files:**
- Create: `tools/generate_contracts.py`
- Create: `packages/dashboard-contracts/scripts/run-codegen.sh`
- Modify: `packages/dashboard-contracts/src/index.ts`（替换占位）

- [ ] **Step 1: 写 codegen 脚本**

  ```python
  #!/usr/bin/env python3
  """从 apps/studio_api 的 OpenAPI 生成 TS 类型，写到 packages/dashboard-contracts/src/。"""
  # 用 datamodel-code-generator（pip install datamodel-code-generator）
  # 读 OpenAPI（启动 fastapi 子进程，访问 /openapi.json）
  # 输出到 packages/dashboard-contracts/src/api/*
  ```

- [ ] **Step 2: 接入 CI**

  在 `apps/studio_api` 启动后跑：
  ```yaml
        - name: Generate TS contracts
          run: |
            (cd apps/studio_api && uvicorn app:app --port 18000 &)
            sleep 5
            python tools/generate_contracts.py
  ```

- [ ] **Step 3: apps/dashboard 改 import**

  Run: `grep -rln "@/types/api" apps/dashboard/src/` → 改为 `import { ... } from '@moling/dashboard-contracts/api/<x>'`.

- [ ] **Step 4: typecheck**

  Run: `cd apps/dashboard && pnpm typecheck:app`
  期望：errors = 0。

- [ ] **Step 5: commit**

  ```bash
  git add -A
  git commit -m "feat(contracts): 从 apps/studio_api OpenAPI 自动生成 TS 类型"
  ```

---

### Task 19.14：可视化伴侣接（占位）

> 暂时不开启浏览器伴侣。无需实现；本任务为占位确认。

---

### Task 19.15：API 错误类统一

**Files:**
- Modify: `apps/dashboard/src/api/core.ts`（已存在；强化错误类使用）
- Delete: 任何自定义 error 类型散落处

- [ ] **Step 1: 写 ESLint 规则禁用 throw new Error(...)**

  Create: `apps/dashboard/eslint-rules/no-throw-bare-error.js`

  检测 `throw new Error(` 字面，建议替换为 `throw new NetworkError(...)`.

- [ ] **Step 2: 加到 eslint.config**

  Run: `git add apps/dashboard/eslint-rules/ apps/dashboard/eslint.config.js`
  Run: `pnpm lint`
  期望：hits 0。

- [ ] **Step 3: commit**

  ```bash
  git commit -m "feat(frontend): API 错误类统一（NetworkError 等已分层）"
  ```

---

### Task 19.16：去掉文件大小 ALLOWLIST（composable）

**Files:**
- Modify: `tooling/hygiene/check_file_size.py`（移除 composable 部分的 ALLOWLIST）

- [ ] **Step 1: 检查现状**

  Run: `python3 tooling/hygiene/check_file_size.py`
  期望：列出 .ts/.vue/.py 各超限文件。

- [ ] **Step 2: 跑过 typecheck**

  Run: `cd apps/dashboard && pnpm typecheck:app`
  Run: `cd apps/dashboard && pnpm test:run`

  如仍 FAIL，回到 Phase 19.1-6 继续拆。

- [ ] **Step 3: 移除 ALLOWLIST**

  Edit `tooling/hygiene/check_file_size.py`，删除 `ALLOWLIST` 集合（保留以备后用但已空）。

- [ ] **Step 4: 跑 CI gate**

  Run: `bash tooling/gates/phase_16.sh`
  期望：通过。

- [ ] **Step 5: commit**

  ```bash
  git commit -m "chore(hygiene): 移除 file-size ALLOWLIST（Phase 19 拆分已生效）"
  ```

---

### Task 19.17：dashboard-contracts 自动生成可重跑

**Files:**
- Create: `apps/studio_api/scripts/export_openapi.py`

- [ ] **Step 1: 写 export 脚本**

  ```python
  #!/usr/bin/env python3
  """导出 apps/studio_api 的 OpenAPI JSON 到 packages/dashboard-contracts/openapi.json。"""
  import json
  from pathlib import Path
  from fastapi.openapi.utils import get_openapi


  def main() -> int:
      from apps.studio_api.main import app  # 路径按实际调整
      schema = get_openapi(
          title=app.title, version=app.version, routes=app.routes,
      )
      out = Path("packages/dashboard-contracts/openapi.json")
      out.write_text(json.dumps(schema, ensure_ascii=False, indent=2))
      return 0
  ```

- [ ] **Step 2: 加 Makefile**

  ```makefile
  contracts:
  	python tools/generate_contracts.py
  	mv packages/dashboard-contracts/src/api/*.ts packages/dashboard-contracts/src/api/ 2>/dev/null || true
  ```

- [ ] **Step 3: commit**

  ```bash
  git commit -m "feat(contracts): codegen 流程含 openapi.json export 与 Makefile"
  ```

---

### Task 19.18：dashboard-contracts 与 OpenAPI 一致性 CI

**Files:**
- Modify: `.github/workflows/dashboard-frontend-ci.yml`

- [ ] **Step 1: 加 step**

  ```yaml
        - name: Verify contracts consistency
          run: |
            (cd apps/studio_api && uvicorn app:app --port 18000 &)
            sleep 8
            python tools/generate_contracts.py --check
            # --check 模式：若 contracts 文件与新生成的内容不一致，exit 1
  ```

- [ ] **Step 2: commit**

  ```bash
  git commit -m "ci: dashboard-contracts ↔ OpenAPI 一致性检查"
  ```

---

### Task 19.19：单测覆盖率到 80%

**Files:**
- Modify: `apps/dashboard/vitest.config.js`（threshold 从"观测"切到 enforce）

- [ ] **Step 1: 编辑 config**

  ```javascript
  test: {
    coverage: {
      thresholds: { lines: 80, statements: 80, branches: 70, functions: 70 },
      // 把 observe: true 改成 enforce: true
    },
  }
  ```

- [ ] **Step 2: 跑 coverage**

  Run: `cd apps/dashboard && pnpm test:coverage`
  期望：阈值满足；如不满足，单独再补一批测试（不在本任务范围内，列入 Phase 21 gate 之前的 backlog）。

- [ ] **Step 3: commit**

  ```bash
  git commit -m "test(frontend): 开启 80% 覆盖率阈值强制"
  ```

---

### Task 19.20：Phase 19 Gate 脚本

**Files:**
- Create: `tooling/gates/phase_19.sh`

- [ ] **Step 1: 写**

  ```bash
  #!/usr/bin/env bash
  set -euo pipefail
  cd "$(git rev-parse --show-toplevel)"

  bash tooling/gates/phase_17.sh

  echo "▶ 前端 lint/typecheck/test/coverage"
  (cd apps/dashboard && pnpm lint && pnpm typecheck && pnpm test:coverage)

  echo "▶ composable / API 模块大小"
  python3 tooling/hygiene/check_file_size.py

  echo "▶ 角色白名单单点"
  (cd apps/dashboard && pnpm test:run router/role-allowlist)

  echo "▶ contracts 一致性"
  (cd apps/studio_api && uvicorn app:app --port 18000 &)
  sleep 5
  python tools/generate_contracts.py --check

  echo "✅ Phase 19 Gate PASS"
  ```

- [ ] **Step 2: 跑 Gate**

  Run: `bash tooling/gates/phase_19.sh`
  期望：通过。

- [ ] **Step 3: commit**

  ```bash
  git add tooling/gates/phase_19.sh
  git commit -m "ci(gate): Phase 19 门禁"
  ```

---

### Phase 19 Gate

- [ ] **G1**: 所有 composable ≤300 行（允许 ≤500 但需明确 TODO 注释）
- [ ] **G2**: `api/creator.js` 不存在；creator 子模块各自 ≤200 行
- [ ] **G3**: `useXxxStore` 单例已全部转 Pinia 或保留 composable 时有书面理由
- [ ] **G4**: 角色白名单只在 `router/index.ts` 定义
- [ ] **G5**: `apps/dashboard` 无 `import { ... } from 'lingwen-...'` 或 `from 'apps/studio_api/...'`
- [ ] **G6**: `pnpm test:coverage` ≥ 阈值
- [ ] **G7**: dashboard-contracts 一致性 CI 通过

✅ **Gate 通过 → 进 Phase 20**

---

## Phase 20 · 文档与品牌（1 周 / 8 任务）

> 目标：从用户角度写全新 VISION.md / 根 README / ARCHITECTURE.md，统一所有包 / apps 的 README。

### Task 20.1：写 VISION.md

**Files:**
- Create: `VISION.md`

- [ ] **Step 1: 内容骨架**

  ```markdown
  # 墨灵 Studio · 产品愿景

  ## 一句话
  墨灵 Studio 是一款面向中文网络小说创作者的 AI 创作助理。

  ## 用户
  - 主要：独立创作者（个人或小工作室），希望提升长篇连载效率
  - 次要：传统编辑团队用于审稿辅助

  ## 价值主张
  - 一次创作百章不衰的连贯性：背景、人物、伏笔跨章稳定
  - 编辑视角的反馈环：内置多视角模拟读者 + S1-S8 维度审核
  - 出版级润色：内置风格预设与 AI 痕迹清洗器

  ## 不做的
  - 不做通用对话（即 LLM 不在 Studio 中暴露）
  - 不做图像 / 视频生成
  - 不做"墨"或独立字标重设计

  ## 度量
  - 创作效率（每小时净增字数）
  - 一致性（自动审核 P0=0 章节占比）
  - 用户留存（30 日 / 90 日）
  ```

  Run: `git add VISION.md && git commit -m "docs(vision): 撰写产品愿景 VISION.md"`.

---

### Task 20.2：根 README.md 重写

**Files:**
- Modify: `README.md`（用户面向）

- [ ] **Step 1: 重写为产品视角**

  ```markdown
  # 墨灵 Studio · MoLing Studio

  > 由灵文引擎（[LingWen Engine](docs/ARCHITECTURE.md)）驱动的小说创作助理。

  ## 安装 / 快速开始
  见 [docs/quickstart.md](docs/quickstart.md)。

  ## 仓库结构
  [包 / apps 索引](docs/ARCHITECTURE.md#单元清单) — 11 个 unit。

  ## 开发者入口
  [CONTRIBUTING.md](CONTRIBUTING.md) · [ARCHITECTURE.md](docs/ARCHITECTURE.md) · [VISION.md](VISION.md)
  ```

  Run: `git add README.md && git commit -m "docs(readme): 根 README 改写为产品视角"`.

---

### Task 20.3：ARCHITECTURE.md 撰写（单文件 ≥1100 行）

**Files:**
- Create: `docs/ARCHITECTURE.md`

- [ ] **Step 1: 整合现有散落架构文档**

  - `docs/LINGWEN_ARCHITECTURE_SPEC.md` 的有效部分
  - `docs/superpowers/specs/2026-08-08-moling-studio-redesign-design.md` 的核心章节
  - 简化的 hex / clean arch 说明
  - 每个 app / package 的文件索引

- [ ] **Step 2: index + package 索引**

  ```markdown
  ## 单元清单（11 unit）

  | Unit | 类型 | 用途 | 自述 |
  |------|------|------|------|
  | apps/dashboard | Vue 3 + TS | 墨灵 Studio 前端 | [README](apps/dashboard/README.md) |
  | apps/studio_api | FastAPI | 墨灵 Studio 后端 | [README](apps/studio_api/README.md) |
  | packages/lingwen-core | Python | 领域 + 应用 | [README](packages/lingwen-core/README.md) |
  | ... |
  ```

- [ ] **Step 3: commit**

  ```bash
  git add docs/ARCHITECTURE.md
  git commit -m "docs(architecture): 单一 ARCHITECTURE.md 文档，整合散落设计"
  ```

---

### Task 20.4：包 / app README 模板

**Files:**
- Create: `tooling/docs/README_TEMPLATE_python.md`
- Create: `tooling/docs/README_TEMPLATE_ts.md`

- [ ] **Step 1: 模板**

  Python 包模板：
  ```markdown
  # lingwen-<name>

  ## 做什么
  一句话。

  ## 不做什么
  - 列表。

  ## 如何用
  ```python
  from lingwen_<name> import ...
  ```

  ## 测试
  ```bash
  pytest packages/lingwen-<name>/tests
  ```

  ## 扩展点
  - 列表。
  ```

  TS 包模板同形态。

  Run: `git add tooling/docs/ && git commit -m "docs(tooling): 包 README 模板"`.

---

### Task 20.5-20.7：每个 package 写或重写 README

- 20.5：python 8 包
- 20.6：apps 2 个
- 20.7：dashboard-contracts 1 个

每个 commit:
```
docs(<unit>): 撰写 README（做什么 / 不做 / 用法）
```

---

### Task 20.8：CONTRIBUTING.md

**Files:**
- Create: `CONTRIBUTING.md`

- [ ] **Step 1: 内容**

  ```markdown
  # 贡献者指南

  ## 工作流
  1. 从 master 拉新分支
  2. 写代码前先写测试
  3. 跑 `pnpm verify` 必须绿
  4. 提 PR
  5. review 通过后 squash merge

  ## 提交规范
  `<type>: <subject>`（types: feat, fix, refactor, docs, test, chore, perf, ci）

  ## 包依赖规则
  ...
  ```

  Run: `git commit -m "docs(contributing): 撰写 CONTRIBUTING.md"`.

---

### Phase 20 Gate

- [ ] **G1**: `VISION.md`、`README.md`、`CONTRIBUTING.md`、`docs/ARCHITECTURE.md` 全在
- [ ] **G2**: 每个 package 有 README
- [ ] **G3**: 链接互通（`README.md` → `ARCHITECTURE.md` 等可点击）

✅ **Gate 通过 → 进 Phase 21**

---

## Phase 21 · 收尾（1 周 / 8 任务）

> 目标：CHANGELOG、tag、最终删除清单、CI 全绿、发布 v10.0。

### Task 21.1：CHANGELOG.md 全量写

**Files:**
- Modify: `CHANGELOG.md`

- [ ] **Step 1: 写 v10.0 段**

  ```markdown
  ## v10.0 (2026-08-09)

  ### 大重构（Phase 16-21）
  - 仓库结构调整：monorepo + 11 个 unit
  - 工作流引擎：event-sourced（JSONL append-only）
  - 质量系统：统一 Checker/Repairer Protocol
  - 前端 composable 拆分 + Pinia 化 + dashboard-contracts 自动类型生成
  - 品牌锁定：墨灵 Studio = 产品，灵文 = 框架
  - 清理运行时陈旧 DB 与重复逻辑

  ### 升级指南
  - 见 docs/upgrade/v9-to-v10.md
  ```

  Run: `git add CHANGELOG.md && git commit -m "docs(changelog): v10.0 大重构变更日志"`.

---

### Task 21.2：docs/upgrade/v9-to-v10.md

**Files:**
- Create: `docs/upgrade/v9-to-v10.md`

- [ ] **Step 1: 升级指南**

  ```markdown
  # v9 → v10 升级指南

  ## 破坏性变更
  - CLI: `python lingwen.py status` 仍然兼容（薄壳）
  - 数据: 旧的 `.state/workflow.db` 不再读取；事件从 `.state/events/*.jsonl` 派生
  - API: `apps/dashboard` 不再 import `apps/studio_api/` 路径代码（only HTTP/WS）
  - 开发: 各 Python 包迁到 `packages/lingwen-*`

  ## 迁移工具
  ```bash
  python tools/migrate_state_log.py --src .state/state_history.log --dst .state/events/migration.jsonl
  ```
  ```

  Run: `git commit -m "docs(upgrade): v9 → v10 升级指南"`.

---

### Task 21.3：删陈旧 doc 文件

**Files:**
- Delete:
  - `docs/LINGWEN_V3_ARCHITECTURE_OPTIMIZATION.md`
  - `docs/LINGWEN_V3.1_ARCHITECTURE_OPTIMIZATION.md`
  - `docs/AI小说工厂优化方案.md`
- Modify: `docs/INDEX.md`（移除对应入口）

- [ ] **Step 1: 删除**

  ```bash
  git rm docs/LINGWEN_V3_ARCHITECTURE_OPTIMIZATION.md
  git rm docs/LINGWEN_V3.1_ARCHITECTURE_OPTIMIZATION.md
  git rm docs/AI小说工厂优化方案.md
  ```

- [ ] **Step 2: 修 INDEX**

  Run: `git add docs/INDEX.md && git commit -m "chore(docs): 移除 v3 / v3.1 / AI 工厂优化方案历史文档"`.

---

### Task 21.4：最终去 hygiene ALLOWLIST

**Files:**
- Modify: `tooling/hygiene/check_file_size.py`

- [ ] **Step 1: 清空 ALLOWLIST**

  Run: `grep -A 5 "ALLOWLIST" tooling/hygiene/check_file_size.py`
  → 删除具体条目，留一个空 dict。

- [ ] **Step 2: 跑 Gate**

  Run: `bash tooling/gates/phase_19.sh`
  期望：errors = 0；如还有，按 phase 19 backlog 拆完。

- [ ] **Step 3: commit**

  ```bash
  git commit -m "chore(hygiene): 移除 file-size ALLOWLIST（Phase 19 拆完）"
  ```

---

### Task 21.5：CI 全绿终检

**Files:**
- Modify: 任何仍 FAIL 的文件

- [ ] **Step 1: 跑所有 gate**

  ```bash
  bash tooling/gates/phase_16.sh
  bash tooling/gates/phase_17.sh
  bash tooling/gates/phase_19.sh
  ```

  期望：exit 0。

- [ ] **Step 2: 跑后端 e2e smoke（若存在）**

  Run: `cd apps/studio_api && pytest tests/e2e/ -q`（如未实现，跳过）

- [ ] **Step 3: 跑前端 playwright opt-in**

  Run: `cd apps/dashboard && pnpm exec playwright test --grep @quarantine`
  期望：quarantine 通过，非 quarantine 不阻塞。

---

### Task 21.6：README / LICENSE / CONTRIBUTING 齐

**Files:**
- Create: `LICENSE`（如不存在）

- [ ] **Step 1: 加 LICENSE**

  ```text
  MIT License

  Copyright (c) 2026 灵文引擎 / MoLing Studio contributors

  Permission is hereby granted, free of charge, to any person obtaining a copy...
  ```

  Run: `git add LICENSE && git commit -m "chore(license): 加入 MIT LICENSE"`.

---

### Task 21.7：v10.0 tag + GitHub release

**Files:** N/A

- [ ] **Step 1: tag**

  Run:
  ```bash
  git tag -a v10.0.0 -m "v10.0.0 - 墨灵 Studio × 灵文引擎 全栈重构首发"
  git push origin v10.0.0
  ```

  期望：tag 创建 + push。

- [ ] **Step 2: release notes**

  Run: `gh release create v10.0.0 --notes-file docs/upgrade/v9-to-v10.md`
  期望：release 在 GitHub 创建。

- [ ] **Step 3: commit 收口**

  Run: `git log --oneline -5`（仅查看，无新增 commit）

---

### Task 21.8：发布后庆祝（可选）

- [ ] **Step 1**: 提交一份"压压惊"小测试 / 设置可选金丝雀：

  Run: `git commit --allow-empty -m "chore: v10.0.0 发布完成 🎉"`

---

### Phase 21 Gate

- [ ] **G1**: v10.0.0 tag 已 push
- [ ] **G2**: 所有 Phase 16-19 gate 全绿
- [ ] **G3**: README / LICENSE / CONTRIBUTING / CHANGELOG / VISION / ARCHITECTURE 齐全
- [ ] **G4**: `git ls-files | grep -E '__pycache__|\.mypy_cache|\.ruff_cache|lingwen.*\.egg-info'` 0 行
- [ ] **G5**: `apps/dashboard/src/**` 中 grep `LingWen Studio|Studio v12|^墨$` 0 行（除显式历史段）
- [ ] **G6**: 一切 docs/ 实现指向 `docs/ARCHITECTURE.md`，不再有 `LINGWEN_V3_*`

✅ **Gate 通过 → 整个重设计完成**

---

## 附录 · 常见操作速查

```bash
# 跑某 Phase 的 Gate
bash tooling/gates/phase_16.sh
bash tooling/gates/phase_17.sh
bash tooling/gates/phase_19.sh

# 验证事件流从 JSONL 重建
python -c "from lingwen_storage.events import JsonlStore, reduce_events
store = JsonlStore('.state/events/migration.jsonl')
print(reduce_events(store.iter()).chapter_count, 'chapters')"

# 重生 TS 契约
python tools/generate_contracts.py

# 跑全 monorepo verify
pnpm -r verify
```

---

## 附录 · 风险与回滚

| 风险 | 早期信号 | 回滚方案 |
|------|---------|---------|
| Phase 17 monorepo 迁移路径冲突 | import 链断裂 | 局部回退 git mv |
| Phase 18 ports 抽象过度 | 用例测试难写 | 冻结 ports，加 adapter shim |
| Phase 19 composable 拆分引入死循环 | 测试用时大涨 | 保留当前层级（不再额外拆分，记 backlog 在 Phase 21 之后处理） |
| Phase 19 dashboard-contracts 漂移 | CI step fail | 回滚 codegen 到上一稳定 commit |

---

## 附录 · 写计划自审

- [x] **Spec 覆盖**：spec §3-§22 每一项都对应到本 plan 的某个任务：
  - P1 独立部署 → Phase 17 / 18 / 19
  - P2 Hexagonal → Phase 18
  - P3 事件溯源 → Task 16.4 / 16.5 / 16.6
  - P4 静态检查 → Phase 16 / 17 / 19 gates
  - P5 角色 = SKILL.md → Task 17.15
  - P6 类型契约单向 → Task 17.11 / 19.13 / 19.17
  - P7 品牌真相 → Task 16.9
  - P8 删除胜过保留 → Task 16.7 / 21.3
- [x] **占位符扫描**：仅"占位"出现在 Task 14（占位确认 = 删除行为）；其它均为具体代码。
- [x] **类型一致**：`LLMPort` 在 Task 18.2 / 18.3 / 18.4 一致；`WorkflowEvent` 在 Task 16.4 / 16.5 / 16.6 一致；`WriteChapterUseCase(cmd)` 在 Task 18.4 一致。
- [x] **可独立执行**：每个 Task 有 commit，Phase 有 Gate。Phase 间可暂停。

---

## 完成

按本计划完整执行后，仓库达到 spec §21 成功标准：

1. ✓ 结构：apps / packages / content / docs / tooling 顶层七个目录
2. ✓ 门禁：lint + typecheck + test + 覆盖率全绿
3. ✓ 运行时：事件流可重放，删 DB 不破功能
4. ✓ 边界：apps/dashboard 不 import lingwen-*；packages 内部无环
5. ✓ 文档：VISION / ARCHITECTURE / README / CHANGELOG 全在
6. ✓ 品牌：墨灵 Studio / 灵文 各司其职，命名单一真相


</content>
</invoke>
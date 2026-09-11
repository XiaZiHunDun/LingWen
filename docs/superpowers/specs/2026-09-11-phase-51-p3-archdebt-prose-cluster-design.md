# Phase 51 P3-ARCHDEBT — prose 簇收尾 (design)

> **Branch**: `phase-51-p3-archdebt-prose-cluster`
> **Base**: `master@348df7f4` (Phase 50 closed)
> **承接**: Phase 42-50 P3-ARCHDEBT pipeline（14/14 已闭环）；本 phase 清空 `infra/` **顶层最后 4 个 .py**
> **模式**: MIGRATE ×3（新包）+ MERGE ×1（并入既有包）+ DELETE ×2（零消费 barrel）

---

## 1. 范围

`infra/` 顶层在 Phase 50 后仅剩 4 个 `.py`（不含 `__init__.py`），构成一个自然的 **prose 质量子系统簇** + 1 个孤立模块。本 phase 全部迁走，此后 `infra/` 顶层只剩 `__init__.py`。

| 模块 | LOC | 公开符号（实测）| workspace deps | LEAF |
|------|-----|----------------|----------------|------|
| `infra/prose_judge.py` | 734 | **28**（7 consts + 21 funcs）| prose_calibration · llm · shared · full_check_report · **overrides** | ❌ |
| `infra/prose_snapshot.py` | 195 | **8**（2 consts + 6 funcs）| prose_calibration | ❌（1 dep）|
| `infra/prose_calibration_overrides.py` | 174 | **9**（0 consts + 9 funcs）| — 仅 PyYAML | ✅ **TRUE LEAF** |
| `infra/project_characters.py` | 89 | **2**（0 consts + 2 funcs）| paths · project_config | ❌ |

**合计 47 个公开符号。**

> **符号数取得方式**（Phase 34/35 教训「spec 会撒谎」）：
> ```bash
> .venv/bin/python -c "import importlib, inspect; ..."   # 见 §7 复现命令
> ```
> 4 个模块**均无 `__all__`**，wildcard 导出的是���全部非下划线模块级名」——**包括 import 进来的第三方名**（如 `Path`/`Any`/`json`）。这是 §4 barrel 必须整删而非改写的根因。

### 明确不在范围

- `infra/` 的 **21 个子目录**（21349 LOC / 134 文件，tools 7.5K · cross_volume 4.5K · persistence 1.6K …）—— 全新战场，需独立审计（建议 Phase 52 做 residual audit，类似 Phase 41+++）
- `tests/test_phase32_shim_cleanup.py:37` 的**预存在失败**（见 §6 baseline）

---

## 2. 包划分决策

| 源模块 | 去向 | 理由 |
|--------|------|------|
| `prose_calibration_overrides` | **MERGE** → 既有 `packages/lingwen-prose-calibration/` | 语义上就是 prose calibration 的 override 层；两者均只依赖 PyYAML，**合并后 TRUE LEAF 状态保持不变**。先例：Phase 46 `filter` MERGE 进 `lingwen-quality` |
| `prose_judge` | **NEW** `packages/lingwen-prose-judge/` | 734 LOC + LLM 依赖；若并入 prose-calibration 会**摧毁其 TRUE LEAF 状态**，故必须独立 |
| `prose_snapshot` | **NEW** `packages/lingwen-prose-snapshot/` | 对 `prose_judge` **零依赖**；做成 prose-judge 的子模块属命名失实。先例：Phase 45/50 一模块一包 |
| `project_characters` | **NEW** `packages/lingwen-project-characters/` | 与 prose 簇无关，独立业务语义（项目角色名抽取）|

迁移后：**31 → 34 个 `lingwen-*` 包**。

### `lingwen-prose-judge` 子模块拆分

`.py` 体积上限是 **500**（`tooling/hygiene/check_file_size.py:16 LIMITS`，非 CLAUDE.md 所述的 800），`prose_judge.py` 734 行超限、靠 `ALLOWLIST` 豁免。拆成 5 个子模块后**每个均 <500，白名单条目可直接摘除**。先例：Phase 40a（5 子模块）· Phase 42（3 子模块）。

| 子模块 | 源行段 | ~LOC | 内容 |
|--------|--------|------|------|
| `constants.py` | 1-68 | 68 | 7 个 consts + `JUDGE_SYSTEM_PROMPT` |
| `report_io.py` | 71-140 | 70 | `report_path_for` · `golden_*` · `load/save_judge_report` · `_action_for_score` · `map_issue_type_to_dimension` |
| `ratings.py` | 141-366 + 705-734 | ~255 | offline 推导 + LLM judge + `_normalize_ratings` + `validate_judge_report` + `run_prose_judge` 编排 |
| `analysis.py` | 368-482 | 115 | `cross_reference_signals` · `summarize_judge_report` |
| `calibration.py` | 483-703 | 220 | 校准包采样 / verdict / 统计 / log 文档渲染 |

`__init__.py` 做 barrel，`__all__` 显式列 **28** 项（Phase 42 教训：smoke test 必须 `assert len(__all__) == 28`）。

---

## 3. 消费点清单（9-pattern 审计实测）

未锚定 grep（MEMORY「`^from` 会漏缩进 import」教训），排除 `__pycache__` / `.claude/worktrees/` / `docs/superpowers/archive/`。

### ① 字面 dotted import — 4 处
| 文件 | 模块 |
|------|------|
| `tests/infra/test_prose_judge.py:10` | prose_judge |
| `tests/infra/test_prose_snapshot.py:5` | prose_snapshot |
| `tests/infra/test_prose_calibration_overrides.py:7` | prose_calibration_overrides |
| `tests/infra/test_project_characters.py:7` | project_characters |

### ② 函数体内缩进 import — 3 处 ⚠️ `^from` 锚定必漏
| 文件 | 行 | 模块 |
|------|----|------|
| `packages/lingwen-studio-registry/src/lingwen_studio_registry/reports.py` | 19 | prose_snapshot |
| `packages/lingwen-studio-registry/src/lingwen_studio_registry/reports.py` | 71 | prose_judge |
| `packages/lingwen-quality/src/lingwen_quality/consistency/checkers/character_agency.py` | 137 | project_characters |

### ④ 文件系统路径字面量 — 1 处
- `tooling/hygiene/check_file_size.py:51` — `ALLOWLIST.add("infra/prose_judge.py")`

### ⑤ wildcard barrel — 2 文件 / 4 行
- `infra/prose/__init__.py` — 4 行（`lingwen_prose_calibration` + overrides + judge + snapshot）
- `infra/project/__init__.py` — 3 行（`lingwen_paths` + `lingwen_project_init` + project_characters）

### ⑥ monkeypatch 字符串靶点 — 2 处 ⚠️
| 文件 | 行 | 靶点 |
|------|----|------|
| `tests/dashboard/test_studio_endpoints.py` | 88 | `"infra.prose_snapshot.load_snapshot"` |
| `tests/infra/test_prose_judge.py` | 146 | `"infra.prose_judge.report_path_for"` |

> 两处 patch 的都是**源模块**，而真实消费方 `reports.py` 用的是**函数体内惰性 import**——正因惰性，patch 源模块才生效。迁移后靶点字符串必须同步改成 canonical 包路径，否则 patch 静默失效、测试假绿。

### ⑦ shell heredoc 内 import — 7 脚本 / 8 行
| 脚本 | 行 | 模块 |
|------|----|------|
| `scripts/run-prose-judge.sh` | 22 | prose_judge |
| `scripts/run-prose-calibration-sample.sh` | 17 | prose_judge |
| `scripts/run-prose-calibration-fill.sh` | 16, 17 | overrides + prose_judge |
| `scripts/run-prose-diff.sh` | 24 | prose_snapshot |
| `scripts/run-prose-calibration-override.sh` | 21 | overrides |
| `scripts/verify-studio-maintenance-track.sh` | 18 | overrides |
| `scripts/verify-onboarding.sh` | 48 | project_characters |

### ⑨ 前序 phase guard 反向锁死 — 1 文件 / 4 处 🔴 **最高风险**

`tests/test_phase44_lingwen_prose_calibration.py`（Phase 44 留下）**显式断言旧路径必须保留**：

```python
# :314-321
"""infra/prose/__init__.py:2 prose_calibration_overrides import must be unchanged."""
assert "from infra.prose_calibration_overrides import *" in content, (
    "infra/prose/__init__.py:2 prose_calibration_overrides import should be preserved ")
```

外加 `:141-143` 与 `:182` 两段注释说明 audit 正则用 `\b` 边界**刻意排除** `prose_calibration_overrides`（当时它不在 Phase 44 范围内）。本 phase 迁走该模块后：

- `:314-321` 的断言**必然变红** → 必须**反转方向**（改为「旧路径必须已消失」）
- `:141/182` 的 `\b` 排除注释**失去前提** → 必须重写，否则误导后人

这是 N.14 lesson 1 pattern ⑨ 的**第 10 次变体**，也是本 phase 唯一会「合法地弄红既有测试」的改动。

### ③ 相对 import / ⑧ 文档注释 — 0 处
无。

**消费点总计：4 + 3 + 1 + 4 + 2 + 8 = 22 行，跨 17 文件。**

---

## 4. barrel 处置：整删而非改写

`infra/prose/__init__.py` 与 `infra/project/__init__.py` **零运行时消费者**——全仓仅 `tests/test_infra_init_no_deferred_re_exports.py` 的**文档字符串与正则表**提及，而该 guard 只检查 `infra/__init__.py` 是否 re-export 它们，**不要求它们存在**。

迁移后两个 barrel 的每一行 wildcard 都会指向 canonical 包，沦为纯粹的转发空壳；加之无 `__all__` 导致 wildcard 会连 `Path`/`Any` 一并泄漏（§1），保留反而制造污染。故 **整个目录删除**（`infra/prose/` · `infra/project/`）。先例：Phase 32 / Phase 50 的零消费者死代码删除。

删除后 `tests/test_infra_init_no_deferred_re_exports.py` 的两条 forbidden pattern（`infra.prose` / `infra.project`）**自动永久满足**，无需改动该文件。

---

## 5. 顺带清理（Phase 50 残留）

`tooling/hygiene/check_file_size.py` 的 `ALLOWLIST` 含 **3 条指向 Phase 50 已删文件**的死条目：

| 条目 | 文件现存 |
|------|---------|
| `ALLOWLIST.add("infra/health.py")` | ❌ Phase 50 迁走 |
| `ALLOWLIST.add("infra/llm_cache.py")` | ❌ Phase 50 删除 |
| `ALLOWLIST.add("infra/permission.py")` | ❌ Phase 50 删除 |
| `ALLOWLIST.add("infra/prose_judge.py")` | ✅ 本 phase 拆子模块后移除 |

4 条一并清除。白名单收窄会让下一次超限**真的报错**，而不是被死条目掩护。

---

## 6. Baseline（改动前实测）

```
tests/infra/test_prose_{judge,snapshot,calibration_overrides}.py
tests/infra/test_project_characters.py
tests/dashboard/test_studio_endpoints.py
tests/test_phase3*.py tests/test_phase4*.py tests/test_phase50*.py
tests/test_infra_init_no_deferred_re_exports.py
→ 252 passed, 5 skipped, 1 failed  (13.13s)
```

**预存在失败（不在本 phase 范围）**：
`test_phase32_shim_cleanup.py::test_phase32_shim_consumer_migrated[tests/agent_system/test_got_bridge.py]`
—— 该 guard 在 `:37` 要求 `tests/agent_system/test_got_bridge.py` 存在，但 `git ls-files tests/ | grep got_bridge` **无任何结果**：该文件从未提交或已被删除。Phase 32 guard 指向了一个不存在的文件。属独立缺陷，本 phase **不静默修改**，记入 handoff carryover。

---

## 7. 复现命令

```bash
# 符号数实测（勿信 spec / 文档）
.venv/bin/python -c "
import importlib, inspect
for m in ['infra.prose_judge','infra.prose_snapshot','infra.prose_calibration_overrides','infra.project_characters']:
    mod=importlib.import_module(m)
    fn=[n for n,v in vars(mod).items() if not n.startswith('_') and getattr(v,'__module__',m)==m and (inspect.isfunction(v) or inspect.isclass(v))]
    cs=[n for n,v in vars(mod).items() if not n.startswith('_') and n.isupper() and not inspect.ismodule(v)]
    print(m, len(fn)+len(cs))
"

# 9-pattern 未锚定审计
for f in prose_judge prose_snapshot prose_calibration_overrides project_characters; do
  grep -rn "infra[./]$f" . --include="*.py" --include="*.sh" --include="*.md" --include="*.yml" \
    | grep -v __pycache__ | grep -v "^\./\.claude/worktrees/" | grep -v "^\./docs/superpowers/archive/"
done
```

---

## 8. Atomic commit 计划

| # | Commit | 内容 |
|---|--------|------|
| C0 | `docs(phase-51)` | 本 spec + plan |
| C1 | `feat(infra)` | scaffold 3 新包（prose-judge 拆 5 子模块）+ overrides MERGE 进 lingwen-prose-calibration；root `pyproject.toml [tool.uv.workspace]` 声明**必须先于** `uv sync`（Phase 34 教训）|
| C2 | `refactor(consumers)` | 22 消费点迁移（含 3 函数体内 + 2 monkeypatch 字符串 + 8 shell heredoc + 1 ALLOWLIST 路径）|
| C3 | `chore(infra)` | FULL DELETE 4 源文件 + 2 barrel 目录 + 清 4 条 ALLOWLIST |
| C4 | `docs(arch)` | CLAUDE.md 新增 I071-I073 + 扩写 I058 + 版本 v48.0 → v49.0 |
| C5 | `test(phase-51)` | 反转 phase44 guard + 新增 `test_phase51_*.py` + handoff + MEMORY |

> ⚠️ **C4 强制校验**（Phase 47 / 48 / 50 **连续三次**同一失败）：Python 正则插入不变量会**静默失败**。提交前必须
> `grep -c "^| I07[123] " CLAUDE.md` 断言 **=3**，`grep -c "I058" CLAUDE.md` 断言含 overrides 字样，确认写入成功再 commit。

---

## 9. 验收门

1. ✅ ruff clean（改动文件）
2. ✅ 4 个候选模块的原测试全绿（迁移后路径）
3. ✅ Phase 36-50 既有 guard 保持（**phase44 除外——本 phase 合法反转**）
4. ✅ baseline 252 passed 不回退（预存在的 phase32 failure 仍为 1）
5. ✅ 新增 phase51 regression guards
6. ✅ 旧路径审计归零：`infra.{prose_judge,prose_snapshot,prose_calibration_overrides,project_characters}` 运行时引用 = 0
7. ✅ `infra/` 顶层仅剩 `__init__.py`
8. ✅ `check_file_size.py` 对 `packages/lingwen-prose-judge/**` 无需白名单即通过

---

## 10. 新增不变量

| ID | 约束 |
|----|------|
| I071 | `packages/lingwen-prose-judge/` 是 prose judge 报告 + 校准（28 符号）的唯一实包；`infra.prose_judge.*` 路径非法 |
| I072 | `packages/lingwen-prose-snapshot/` 是 prose snapshot + diff（8 符号）的唯一实包；`infra.prose_snapshot.*` 路径非法 |
| I073 | `packages/lingwen-project-characters/` 是项目角色名抽取（2 符号）的唯一实包；`infra.project_characters.*` 路径非法 |
| I058（扩写）| `packages/lingwen-prose-calibration/` 同时是 calibration **overrides**（9 符号）的唯一实包；`infra.prose_calibration_overrides.*` 路径非法 |

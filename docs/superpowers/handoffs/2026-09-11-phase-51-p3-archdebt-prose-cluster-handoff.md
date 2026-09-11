# Phase 51 P3-ARCHDEBT — prose 簇收尾 (handoff)

> **Branch**: `phase-51-p3-archdebt-prose-cluster`
> **Base**: `master@348df7f4` (Phase 50 closed)
> **Commits**: 6 atomic (`142bbe50` spec / `ea7457de` C1 / `3a21ce6e` C2 / `05f24db1` C3 / `ebf0a598` C4 / C5)
> **Version**: v48.0 → v49.0
> **Invariants**: I071 + I072 + I073 NEW; I058 EXTENDED

---

## 1. 最终汇总

`infra/` 顶层在 Phase 50 后仅剩 4 个 `.py`（1192 LOC）；本 phase 把它们全部迁移 / MERGE / 删除。**Phase 51 之后，`infra/` 顶层只剩 `__init__.py`**。

| # | 模块 | LOC | 去向 | 模式 |
|---|------|-----|------|------|
| 1 | `prose_calibration_overrides.py` | 174 | `lingwen-prose-calibration` (sub-module `overrides.py`) | **MERGE** (Phase 46 filter 前例) |
| 2 | `prose_judge.py` | 734 | `packages/lingwen-prose-judge/` (5 子模块) | **NEW package** |
| 3 | `prose_snapshot.py` | 195 | `packages/lingwen-prose-snapshot/` | **NEW package** |
| 4 | `project_characters.py` | 89 | `packages/lingwen-project-characters/` | **NEW package** |

**合计 47 个公开符号**（实测，不信 spec）。**包生态**：31 → 34 个 `lingwen-*` 包。

---

## 2. 6 atomic commits

| SHA | Type | Scope |
|-----|------|-------|
| `142bbe50` | docs(phase-51) | spec + 9-pattern audit + 47 符号实测 |
| `ea7457de` | feat(infra) | scaffold 3 新包 + overrides MERGE |
| `3a21ce6e` | refactor(consumers) | 14 消费点迁移（4 test + 2 monkeypatch + 3 函数体 + 7 shell + 1 docstring 修正）|
| `05f24db1` | chore(infra) | FULL DELETE 4 源文件 + 2 barrel + 清 4 条 stale ALLOWLIST |
| `ebf0a598` | docs(arch) | I071-I073 + I058 扩写 + v48.0 → v49.0 |
| (this) | test(phase-51) | 18 guards + handoff |

---

## 3. Quality gates

| Gate | Result |
|------|--------|
| 18 phase51 新 guards | ✅ 18/18 GREEN |
| Phase 36-50 既有 guards | ✅ preserved (1 stale docstring 已修) |
| **Phase 44 反向断言** | ✅ 2 处断言**合法反转**（spec 锁死 8→17；反向 guard 改为"必须已删除"） |
| Phase 38 representative_files | ✅ 替换 `infra/project_characters.py` → `apps/studio_api/routes/creator_core.py` |
| Baseline 252 passed + 5 skipped | ✅ **270 passed + 5 skipped**（+18 新增 guard） |
| Pre-existing `phase32 got_bridge` 失败 | ✅ 仍为 1（Phase 51 之前就存在，未回退） |
| ruff | ✅ clean on changed files |
| Runtime audit `infra.{prose_judge,prose_snapshot,prose_calibration_overrides,project_characters}.*` | ✅ 0 hits（仅历史 docstring 引用）|
| `infra/` 顶层文件 | ✅ 仅 `__init__.py` |

---

## 4. 4 lessons

### 4.1 snapshot.py spec 漂移（Phase 34/35 教训第 3 次实锤）

第一次 scaffold `lingwen-prose-snapshot/snapshot.py` 时**自作主张重塑了 schema**（`summary.total_p1_issue_types` 等），导致 5 个测试失败。**修正**：直接 `git show HEAD:infra/prose_snapshot.py` 取原文件逐字照搬。

教训：spec 描述的 schema 永远要**对照 git show** 验证。本 phase spec §1 写了"build_snapshot / save / load / diff / format_diff_report" 5 个函数，但**完全没列出它们的字段名**。这就是 spec 漂移的典型入口——**下游依赖 schema 而不是依赖符号名**时，spec 必须给出完整 schema 或显式声明"待 git show 验证"。

### 4.2 infra/ 顶层清零 ≠ infra/ 子目录清零

Phase 51 完成后 `infra/` 顶层只剩 `__init__.py`，但 **21 个子目录仍存 21349 LOC / 134 文件**（tools 7.5K · cross_volume 4.5K · persistence 1.6K · world_db 1.3K · reading_power 1.0K …）。**这是 Phase 52+ 的新战场**，与 Phase 41+++ 的 Top 5 候选完全不同的形态：

- 候选不再是**孤立 .py 文件**，而是**子目录 + 多个关联文件**（如 `infra/tools/` 是 7.5K LOC 的脚本群）
- 每个子目录有自己的 `__init__.py` 和子模块结构，迁移模式可能从「MOVE 单文件」变成「MOVE 子目录 + 拆 workspace deps」
- 推荐 Phase 52 先做一次**子目录级审计**（类似 Phase 41+++），输出"subdir-level Top 5"候选

### 4.3 前序 phase guard 的"反向锁死"是 N.14 lesson 1 pattern ⑨ 的第 10 次变体

本 phase 有 2 处前序 guard 锁死了旧路径：

- `test_phase44:314-321` 显式断言 `from infra.prose_calibration_overrides import *` 必须保留
- `test_phase44:107` 显式断言 `__all__ == 8`

两处都因本 phase 的迁移而**必然变红**。处理：合法**反转方向**（从"必须保留"改为"必须已删除" / 从 `== 8` 改为 `== 17`），并在 docstring 里引用本 phase 名字以让后人能追源。

教训：**Phase 36+ 后，所有 P3-ARCHDEBT phase 都应该预期有 1-3 处前序 guard 需要反转方向**。可以在 spec 的 §3 「9-pattern audit」里增加子节「prior-phase guard impact」，预先列出哪些断言会红。

### 4.4 ALLOWLIST 静默掩盖回归

`tooling/hygiene/check_file_size.py` 的 ALLOWLIST 含 4 条死条目（Phase 50 已删 3 + 本 phase 拆 1），**全部 silently 通过**——`check_file_size.py` 自身只检查列在白名单中的文件，**对白名单以外的文件照常检查**，所以死条目不直接报错。但**白名单条目指向的文件如果不再超限，就会「死条目占据配额」**，导致下一次真有超限的 .py 想加白名单时，可能被忽略（"不在白名单中反正也报错"），或将死条目复活。

本 phase 顺手清 4 条，使 500-line .py 限额重新生效。Phase 52 子目录审计时可以再加 `test_phase51` 里 G6 同样的"dead ALLOWLIST entries"检查作为模板。

---

## 5. Carryover closure — P3-ARCHDEBT 15/14+1 ALL CLOSED

| # | Phase | Module | Status |
|---|-------|--------|--------|
| 2 | Phase 37 | paths | ✅ |
| 3 | Phase 38 | project_config | ✅ |
| 4 | Phase 39 | logging_config | ✅ |
| 5 | Phase 40a+40b | studio_registry | ✅ |
| 6 | Phase 42 | project_init | ✅ |
| 7 | Phase 43 | llm_service | ✅ |
| 8 | Phase 44 | prose_calibration | ✅ |
| 9 | Phase 45 | utilities batch (cache+coverage_gate+patterns+result) | ✅ |
| 10 | Phase 46 | filter MERGE | ✅ |
| 11 | Phase 47 | studio_batch batch (runner+templates+streamer) | ✅ |
| 12 | Phase 48 | full_check_report | ✅ |
| 13 | Phase 49 | memory_service | ✅ |
| 14 | Phase 50 | utilities batch v2 (schema+health + delete 4 dead) | ✅ |
| **15** | **Phase 51** | **prose 簇 (prose_judge + prose_snapshot + project_characters + prose_calibration_overrides MERGE)** | ✅ |

---

## 6. 包生态总览

- **`lingwen-*` packages**: 31 → 34（+3: prose-judge / prose-snapshot / project-characters; overrides MERGE 不计新增）
- **`infra/` top-level .py**: 5 → 1（仅 `__init__.py`）
- **`infra/` 子目录**: 21 个仍在（**Phase 52 战场**）
- **不变量总数**: 22 → 25（I071-I073 NEW + I058 EXTENDED）
- **本次 session 累计范围**（2026-09-10 至 2026-09-11）：4 mini-phases + 10 P3-ARCHDEBT phases + 24 lingwen-* packages

---

## 7. 后续建议

### 7.1 Phase 52 — infra/ 子目录审计

按 `infra/*/` LOC 排序的 top 子目录：

| LOC | 子目录 | 备注 |
|-----|--------|------|
| 7485 | `infra/tools/` | 7.5K，**最大头**；多半是脚本群，可能拆 studio-tools / creator-tools |
| 4493 | `infra/cross_volume/` | 跨卷业务逻辑 |
| 1578 | `infra/persistence/` | 数据持久化层 |
| 1291 | `infra/world_db/` | Phase 117 world_db 已独立；可能冗余 |
| 1006 | `infra/reading_power/` | 阅读力分析 |
| 992 | `infra/event_sourcing/` | 事件溯源 |
| 848 | `infra/story_contracts/` | 故事契约 |
| 751 | `infra/llm_benchmarks/` | LLM 基准 |
| 508 | `infra/subplot/` | 副图（剧情子图）|
| 439 | `infra/poc/` | POC 验证代码 |

建议 Phase 52 优先级：**tools + cross_volume + persistence**（3 个占 13.5K / 63% 子目录总 LOC）。

### 7.2 Phase 53 — `infra.world_db` 冗余消解

Phase 117 已经把 World DB 迁到独立 SQLite + FastAPI 路由（`infra/world_db/` 很可能成了孤儿代码）。Audit + 删 dead code 是低风险高 ROI 的延续。

### 7.3 修 `test_phase32_shim_cleanup.py:37` 预存在 failure

`tests/agent_system/test_got_bridge.py` 文件从未 commit 但 guard 期望其存在。属于独立的 stale-reference 缺陷，与 P3-ARCHDEBT 无关，但每次跑 baseline 都会显示 1 failed。可以删 guard 或 git mv 真实存在的 got_bridge 测试。

---

## 8. 复现命令

```bash
# 基线（修改前后均要跑）
uv run pytest tests/test_phase{3,4,5}*.py tests/infra/test_prose_*.py \
    tests/infra/test_project_characters.py tests/dashboard/test_studio_endpoints.py \
    tests/test_infra_init_no_deferred_re_exports.py

# 4 个公开符号数实测
.venv/bin/python -c "
import importlib
for m in ['lingwen_prose_judge', 'lingwen_prose_snapshot', 'lingwen_project_characters', 'lingwen_prose_calibration']:
    print(m, len(importlib.import_module(m).__all__))
"

# runtime audit
grep -rn "infra\.\(prose_judge\|prose_snapshot\|prose_calibration_overrides\|project_characters\)" \
    --include="*.py" --include="*.sh" . | \
    grep -v __pycache__ | grep -v "\.claude/worktrees/" | grep -v "^./docs/"
```

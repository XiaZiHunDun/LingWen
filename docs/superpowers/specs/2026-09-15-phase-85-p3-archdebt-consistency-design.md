# Phase 85 P3-ARCHDEBT Design — `infra/tools/consistency/run_quality_checks.py` → MERGE into `packages/lingwen-quality` + DELETE dead files

> **版本**: 草稿 v1 (C0 spec + 9-pattern audit + §A test files migration plan)
> **日期**: 2026-09-15
> **承接**: Phase 84 P3-ARCHDEBT infra/tools/workflow/lib → packages/lingwen-workflow (v54.16)
> **模式**: ARCHDEBT-MIXED 第 2 例 (Phase 50 utilities batch v2 第 1 例) — 1 MIGRATE + 8 DELETE files
> **引用模板**: `@template: docs/superpowers/specs/_P3_ARCHDEBT_TEMPLATE.md` (I079 invariant enforced)

---

## §1. 背景

### §1.1 触发条件

Phase 84 ff-merge 后 master 已是 v54.16 (Phase 84 tip)。infra/tools/ 残留审查发现 `infra/tools/consistency/` 集群包含 1 active file + 8 dead files。

### §1.2 MERGE vs NEW package 决策

**Decision**: **MERGE** into existing `packages/lingwen-quality/src/lingwen_quality/consistency/` subdir (extends I063 FalsePositiveFilter + ProblemClassifier cluster, Phase 46 precedent).

Rationale:
- `packages/lingwen-quality` 已有 `consistency/` 子目录 (3 files: ai_tells_blacklist.py + checker_feedback.py + creative_whitelist.py = 876 LOC, LLM-related)
- `infra/tools/consistency/run_quality_checks.py` (6181 bytes) 是 file-level integrity checks — 名字含 "quality_checks" 与 `lingwen-quality.consistency` 同语义簇
- I063 was extended in Phase 46 (filter MERGE) — 同样模式 (小 module 进入 lingwen-quality)
- NEW package 会增加 maintenance overhead — MERGE 减少 1 个 package
- Total LOC MERGE 范围 ~6KB — 小到不需要独立 package

---

## §2. 9-pattern audit (per N.14 lesson 1)

### §2.1 P1 — literal dotted-path imports

| Site | File | Line | Style |
|------|------|------|-------|
| Production | `packages/lingwen-pipeline/src/lingwen_pipeline/hooks/actions/run_checker.py` | 148 | function-body (`\s+from`) |
| Test (Phase 53 ref) | `tests/test_phase53_p3_archdebt_dead_code_cleanup.py` | 173 | historical (Phase 53 reference) |
| Test (monkeypatch) | `tests/hooks/test_actions.py` | 222-241 | docstring + monkeypatch indirection (3 sites) |

**Verdict**: 5 sites total (1 prod + 4 test). Test sites include docstring narrative + monkeypatch indirection.

### §2.2 P2 — function-body imports

**100%** of production import (run_checker.py:148). Test imports are importlib + MagicMock pattern (no rewrite needed for the test_phase53 reference — historical).

### §2.3 P3 — relative imports

**0 sites**. `run_quality_checks.py` self-contained.

### §2.4 P4 — filesystem path string literals

**0 sites**. No filesystem path literals in run_quality_checks.py.

### §2.5 P5 — wildcard imports

**0 sites**.

### §2.6 P6 — monkeypatch indirection

| Site | File:Line | Target |
|------|-----------|--------|
| Test | `tests/hooks/test_actions.py:234` | `"infra.tools.consistency.run_quality_checks.run_quality_checks"` (string-based mock target) |
| Test | `tests/hooks/test_actions.py:241` | `{"infra.tools.consistency.run_quality_checks": MagicMock(...)}` (dict key) |

**Verdict**: 2 sites. Both in `tests/hooks/test_actions.py`.

### §2.7 P7 — `import X as Y` re-exports

**0 sites**.

### §2.8 P8 — docstring/narrative references

| Site | File:Line | Quote |
|------|-----------|-------|
| Test | `tests/hooks/test_actions.py:222` | "质量门禁应走正确的 import path: infra.tools.consistency.run_quality_checks" |
| Test | `tests/hooks/test_actions.py:225` | "infra/tools/consistency/,旧路径从来 import 不通。这是 P4-2 删" |
| Docs | `docs/模块重复问题分析-v1.0.md:23,26,97,132,160` | Historical analysis doc (Phase 85 will leave as historical archive) |

**Verdict**: 2 test docstring sites (in-place rewrite). Historical docs preserved as archive (commit blame).

### §2.9 P9 — prior-phase guard references

| Site | File | Note |
|------|------|------|
| Phase 53 reference | `tests/test_phase53_p3_archdebt_dead_code_cleanup.py:5,173` | Historical Phase 53 reason — pre-existing (Phase 53 rewrote run_quality_checks as no-op stub). NOT Phase 85 scope. |

**Verdict**: Phase 53 reference is historical. Phase 85 will leave it as-is (it's a regression test of Phase 53's no-op stub rewrite).

---

## §3. Files in scope

### §3.1 MIGRATE (1 file)

| Source | Target |
|--------|--------|
| `infra/tools/consistency/run_quality_checks.py` (6181 bytes) | `packages/lingwen-quality/src/lingwen_quality/consistency/run_quality_checks.py` |

### §3.2 DELETE (8 files, ~22KB total)

| File | LOC | Reason |
|------|-----|--------|
| `infra/tools/consistency/__init__.py` | 0 (empty) | Empty file |
| `infra/tools/consistency/check_naming.py` | 4903 | 0 consumers (verified P1 audit) |
| `infra/tools/consistency/integrity_checker.py` | 8616 | 0 consumers (verified P1 audit) |
| `infra/tools/consistency/run_consistency_check.sh` | shell | Orphan (no shell scripts call it) |
| `infra/tools/consistency/arc-analyze-skill.md` | doc | Orphan skill doc |
| `infra/tools/consistency/quality-check-skill.md` | doc | Orphan skill doc |
| `infra/tools/consistency/template_synonyms.yaml` | data | Orphan data file |
| `infra/tools/consistency/consistency_check_report.json` | data | Orphan report artifact |
| `infra/tools/consistency/consistency_check_report.md` | doc | Orphan report artifact |
| `infra/tools/consistency/检测器开发规范.md` | doc | Orphan dev spec |

**Total**: 9 files DELETE (~30KB), 1 file MIGRATE (6KB).

### §3.3 IN-PLACE rewrites (2 sites)

| Site | File | Line | Rewrite |
|------|------|------|---------|
| Production | `packages/lingwen-pipeline/src/lingwen_pipeline/hooks/actions/run_checker.py` | 148 | `from infra.tools.consistency.run_quality_checks import run_quality_checks` → `from lingwen_quality.consistency.run_quality_checks import run_quality_checks` |
| Test | `tests/hooks/test_actions.py` | 234, 241 | 2 monkeypatch indirection paths + 1 dict key + docstring narrative |

---

## §4. 配套 stale refs

### §4.1 I063 invariant extension

Current I063 text:
> `packages/lingwen-quality/`（扩展）是 FalsePositiveFilter + ProblemClassifier 的唯一实包

Extended I063 text:
> `packages/lingwen-quality/`（扩展）是 FalsePositiveFilter + ProblemClassifier + RunQualityChecks (run_quality_checks 函数, file-level integrity checks) 的唯一实包; `infra.consistency.*` 和 `infra/tools/consistency/`` 路径非法

(Per Phase 46 + Phase 85 MERGE precedent.)

### §4.2 infra/__init__.py wildcard check

**0 wildcard**. `infra/__init__.py` has no `from infra.tools.consistency` re-export.

### §4.3 __pycache__ residue cleanup

Per Phase 53d/78/79/80/82/84 lesson, C3 must `rm -rf infra/tools/consistency/__pycache__/` to avoid G1 false-positive.

### §4.4 pre-C1 fixups (intra-package absolute imports)

`infra/tools/consistency/__init__.py` is empty (0 bytes). No fixups needed.

`infra/tools/consistency/run_quality_checks.py` — sed audit: `grep '^from infra\.tools\.consistency\.' infra/tools/consistency/` = 0 hits (clean).

---

## §5. Plan — 5-column commit table (per template §B)

| Commit | Subject | Files | +/- | Risk |
|--------|---------|-------|-----|------|
| **C0** | spec + 9-pattern audit | `docs/superpowers/specs/2026-09-15-phase-85-...md` (new) | +~250 / 0 | none |
| **C1** | scaffold `packages/lingwen-quality/src/lingwen_quality/consistency/run_quality_checks.py` | single file copy | +185 / 0 | low |
| **C2** | MIGRATE 1 prod consumer + IN-PLACE rewrite 3 monkeypatch sites + docstring fixups | `run_checker.py` + `test_actions.py` | +3 / -3 | low |
| **C3** | FULL DELETE `infra/tools/consistency/` (9 files) + I086 NEW invariant (extended I063) | `infra/tools/consistency/*` (delete) + `.lingwen/architecture.yml` | +3 / -30000 bytes | low (post-§A verification) |
| **C4** | prior-phase guards fixup (test_phase53d add `assert not (infra/tools/consistency/run_quality_checks.py).exists()` + test_phase18_8 docstring) — N.14 v22 defense | 2 prior-phase guards | +5 / -3 | low |
| **C5** | 12 regression guards G1-G12 | `tests/test_phase85_p3_archdebt_consistency.py` (new) | +250 / 0 | low |
| **C6** | CLAUDE.md v54.17 + I063 extension + handoff sync | `CLAUDE.md` + `collaboration/CURRENT_STATUS.md` + `collaboration/BACKLOG.md` + `docs/superpowers/handoffs/2026-09-15-phase-85-...md` (new) | +200 / -3 | low |

**Total**: 7 atomic commits (C0-C6), +~895 LOC / -30030 bytes (MIGRATE 6KB + DELETE 22KB + guard 250 + doc 200).

---

## §6. §A. test files migration plan (MANDATORY per template §A)

### §A.1 test files inventory

```
$ grep -rln "infra\.tools\.consistency" tests/
tests/test_phase53_p3_archdebt_dead_code_cleanup.py   # historical Phase 53 ref (NOT Phase 85)
tests/hooks/test_actions.py                           # monkeypatch indirection (3 sites — IN-PLACE rewrite)
```

| File | Action | Reason |
|------|--------|--------|
| `tests/test_phase53_p3_archdebt_dead_code_cleanup.py` | **RETAIN-AS-IS** | Historical Phase 53 reference. The test checks that infra.tools.consistency.run_quality_checks was rewritten as no-op stub by Phase 53. Module still exists post-Phase 85 C3 because Phase 53's stub is preserved — but actually Phase 85 will DELETE the module entirely. This breaks the test. **DECISION**: Update this test in C2 to reference the new location lingwen_quality.consistency.run_quality_checks OR delete the test entirely if no longer meaningful. |

Wait — let me re-read Phase 53's intent. Phase 53 made run_quality_checks a no-op stub (line 5 says "rewritten as no-op stub"). Phase 85 deletes the file entirely. The test at line 173 does `importlib.import_module("infra.tools.consistency.run_quality_checks")` which would fail post-Phase 85.

**DECISION**: After C3, the importlib.import_module will ModuleNotFoundError. Either:
- (A) Update test_phase53 to import the new location lingwen_quality.consistency.run_quality_checks
- (B) Delete test_phase53 entirely (it's a historical Phase 53 dead-code guard, not a current functional test)

Option (A) is more conservative. Let me plan to update test_phase53 in C4 (alongside prior-phase guards fixup).

### §A.2 IN-PLACE rewrite 路径

- **Target location**: tests/hooks/test_actions.py + tests/test_phase53_p3_archdebt_dead_code_cleanup.py (NOT MIGRATE to packages/, just rewrite imports)
- **Step**: sed `infra\.tools\.consistency\.run_quality_checks` → `lingwen_quality.consistency.run_quality_checks` (single commit, no git mv needed)
- **Imports rewrite**: 
  - `from infra.tools.consistency.run_quality_checks import run_quality_checks` → `from lingwen_quality.consistency.run_quality_checks import run_quality_checks`
  - `"infra.tools.consistency.run_quality_checks.run_quality_checks"` (string) → `"lingwen_quality.consistency.run_quality_checks.run_quality_checks"`
- **Functional gate**: `pytest tests/hooks/test_actions.py tests/test_phase53_p3_archdebt_dead_code_cleanup.py` must pass

### §A.3 DELETE 路径

N/A — no test files are deleted in Phase 85.

### §A.4 RETAIN-ORPHAN 路径

**0 sites**. No orphan tests allowed.

### §A.5 Half-migration defense (per template §A.5)

- ✅ C2 commit pathspec 含 BOTH `run_checker.py` prod + `test_actions.py` monkeypatch
- ✅ C3 (FULL DELETE) atomic per I079 §A5
- ✅ C3 commit message 含 "infra/tools/consistency/run_quality_checks.py MIGRATE + 8 supporting files DELETE + I063 extension"

---

## §7. 验证 gates (per template §B)

| Gate | Command | Expected |
|------|---------|----------|
| MIGRATE functional | `pytest packages/lingwen-quality/tests/ -v` | All existing tests preserved |
| Production regression | `pytest packages/lingwen-pipeline/tests/ -v` | run_checker.py consumer works |
| Test regression | `pytest tests/hooks/test_actions.py -v` | monkeypatch indirection rewrites work |
| ruff | `ruff check packages/lingwen-quality/ packages/lingwen-pipeline/hooks/actions/run_checker.py tests/hooks/test_actions.py` | clean |
| 9-pattern audit | `grep -rn "infra\.tools\.consistency" --include="*.py" apps/ packages/ tests/` | 0 hits (except Phase 53 historical) |
| Phase 85 regression guards | `pytest tests/test_phase85_p3_archdebt_consistency.py -v` | 12/12 PASS |
| Phase 53d prior-phase | `pytest tests/test_phase53d_event_sourcing.py -v` | All preserved |
| Phase 77 invariant sync | `pytest tests/test_phase77_architecture_invariant_sync.py -v` | All preserved (I063 extended to 44) |

---

## §8. 风险评估 (per template §B)

| 风险 | 等级 | 缓解 |
|------|------|------|
| MERGE 增加 lingwen-quality 复杂度 | low | 单文件 MIGRATE (185 LOC) + lingwen-quality 已有 consistency/ 子目录 |
| run_quality_checks.py 有未声明 deps | medium | 需 C1 audit 依赖 (pre-C1 fixup if needed) |
| test_phase53 historical reference 失效 | medium | C2 IN-PLACE rewrite OR delete test (decided in §A.1) |
| infra/tools/consistency/ DELETE 中 __pycache__ 残留 | low | C3 `rm -rf infra/tools/consistency/__pycache__/` per Phase 78/84 lesson |
| 文档 (4 docs/data files) 引用 deleted infra path | low | 2 sites (historical analysis docs) — leave as archive per CLAUDE.md "archive 保护" rule |
| I063 invariant grammar 扩展 (Phase 60 orphan bug recurrence) | low | explicit parsed-value test in Phase 77 G3 family |

---

## §9. 不在范围 (per template §B)

- ❌ `infra/tools/consistency/check_naming.py` + `integrity_checker.py` 单独 MIGRATE — 这 2 个是 0 consumer dead code,Phase 85 直接 DELETE (cleanup)
- ❌ `infra/tools/{workflow,publish,content,check_stale_tasks,issue_tracker,migrate_to_sqlite,regression_tracker,heartbeat}.py` 等其他 infra/tools/ 残留 — Phase 86 ARCHDEBT-MINI scope
- ❌ 重构 `lingwen-quality.consistency` 现有 3 files (ai_tells_blacklist, checker_feedback, creative_whitelist) — 现有 LLM-related 代码不重构,只 ADD run_quality_checks
- ❌ `tests/consistency/test_consistency_engine.py` 等已有 consistency tests — 不需要为 run_quality_checks 写新 tests (因为 Phase 53 已 rewrite 为 no-op stub,Phase 85 关注 MIGRATE 不是新增功能)

---

## §10. 完工标准 (per template §B)

- [ ] C0 spec committed with `@template:` reference + §A plan
- [ ] C1 scaffold creates 1 new file in `packages/lingwen-quality/src/lingwen_quality/consistency/run_quality_checks.py`
- [ ] C2 MIGRATE 1 prod consumer + IN-PLACE rewrite 3 monkeypatch sites + 2 docstring fixups
- [ ] C3 FULL DELETE `infra/tools/consistency/` (9 files) + I063 extended to I086 + __pycache__ cleanup
- [ ] C4 prior-phase guards fixup (test_phase53d + test_phase18_8 — N.14 v22 defense + test_phase53 historical ref update)
- [ ] C5 12 regression guards G1-G12
- [ ] C6 CLAUDE.md v54.17 + I063 extended + handoff doc sync
- [ ] All 7 validation gates GREEN
- [ ] 0 ruff errors
- [ ] 0 9-pattern audit hits (except Phase 53 historical ref if retained)

---

## §11. Lessons from prior phases (per template §C)

**Phase 50 (utilities batch v2)**: ARCHDEBT-MIXED first precedent — 2 packages scaffold + 4 dead modules DELETE in single phase
**Phase 46 (filter MERGE)**: I063 was extended to include FalsePositiveFilter + ProblemClassifier — same pattern for Phase 85
**Phase 84 (workflow)**: empty dir residue lesson (N.14 v23 v3) — apply to consistency/ too
**Phase 78 (ARCHDEBT-MINI saturation)**: provides pattern for DELETE 8 dead files
**Phase 84 (workflow)**: forward-only workspace dep — NOT needed for Phase 85 (lingwen-quality already has lingwen-core + lingwen-llm + lingwen-storage deps)

---

## §12. Anti-patterns (per template §D)

- ❌ C2 只写 "+ I086" 跳过 test_files migration (Phase 56b/56c/57b lesson)
- ❌ C3 DELETE 时跳过 __pycache__ 清理 (N.14 v23 v3 lesson)
- ❌ 让 test_phase53 historical ref 在 C3 后保留 broken importlib import (test would fail silently OR error)
- ❌ MERGE 到错误的子目录 (run_quality_checks 应放 consistency/, 不是 quality/)
- ❌ 假设 lingwen-quality 自动可用 — pyproject.toml workspace dep 已存在 lingwen-core/llm/storage,无需新增
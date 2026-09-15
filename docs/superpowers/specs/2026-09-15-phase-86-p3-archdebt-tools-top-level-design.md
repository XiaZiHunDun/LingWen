# Phase 86 P3-ARCHDEBT Design — infra/tools/ top-level ARCHDEBT-MINI cleanup + shell scripts

> **版本**: 草稿 v1 (C0 spec + 9-pattern audit + §A test files migration plan)
> **日期**: 2026-09-15
> **承接**: Phase 85 P3-ARCHDEBT infra/tools/consistency MERGE into lingwen-quality (v54.17)
> **模式**: ARCHDEBT-MINI second example (Phase 78 was first) — zero-consumer dead code cleanup
> **引用模板**: `@template: docs/superpowers/specs/_P3_ARCHDEBT_TEMPLATE.md` (I079 invariant enforced)

---

## §1. 背景

### §1.1 触发条件

Phase 84-85 ff-merge 后 master 是 v54.17。infra/tools/ 残留审查发现:
- 5 zero-consumer .py files at top-level (Phase 86 scope)
- 3 shell scripts in subdirs (Phase 86 scope)
- 2 stale shell scripts in tools/workflow/ (Phase 86 scope)
- infra/tools/__init__.py with stale narrative (Phase 86 cleanup)

### §1.2 闭环 ARCHDEBT-MINI saturation

Phase 78 saturated ARCHDEBT-MINI (8 zero-consumer dirs). Phase 86 是 post-saturation cleanup — 闭环 Phase 41+++ mini audit (`docs/superpowers/infra-residual-audit.md`) 中 `infra/tools/` top-level 的 zero-consumer .py files.

### §1.3 ARCHDEBT-MINI second example

Phase 78 模式 (Phase 53c 顶级 `tools/legacy/` 删 6149 LOC + 21 files) — single commit pathspec BOTH infra + tests per I079 §A5. Phase 86 是第二个 ARCHDEBT-MINI after saturation.

---

## §2. 9-pattern audit

### §2.1 P1 — 字面 dotted-path imports

```bash
$ grep -rn "infra\.tools\.\(check_stale_tasks\|issue_tracker\|migrate_to_sqlite\|regression_tracker\|heartbeat\|publish\|content\)" --include="*.py" apps/ packages/ tests/ tools/ infra/ 2>/dev/null | grep -v "__pycache__\|archive\|specs\|plans\|handoffs"
```

**Verdict**: 0 hits. All 5 .py files are dead.

### §2.2 P2 — function-body imports

**0 hits** (no consumers).

### §2.3 P3 — relative imports

**0 hits** (no consumers).

### §2.4 P4 — filesystem path literals

**0 hits** in production. test_phase78_archdebt_llm_benchmarks_poc.py has `"infra/tools/legacy/"` in docstring (PRE-EXISTING Phase 78 issue, NOT Phase 86).

### §2.5 P5 — wildcard imports

**0 hits**.

### §2.6 P6 — monkeypatch indirection

**0 hits** (no consumers).

### §2.7 P7 — `import X as Y` re-exports

**0 hits**.

### §2.8 P8 — docstring / narrative references

| Site | File | Reference |
|------|------|-----------|
| docstring | `infra/tools/__init__.py` | Lists `consistency/` + `workflow/` subdirs — DELETED in Phase 84/85 |
| docs | `docs/模块重复问题分析-v1.0.md` | Historical analysis (archive) |
| scripts | `tools/workflow/{restore_sqlite.sh,revert_to_json.sh,backup_json.sh}` | Reference `infra/tools/workflow/lib/` in commands (stale, post Phase 84 lib DELETE) |

**Verdict**: 4 sites — 1 in scope (infra/tools/__init__.py stale docstring), 3 historical (docs archive + stale shell scripts that ARE in scope for Phase 86 DELETE).

### §2.9 P9 — prior-phase guard references

| Site | File | Status |
|------|------|--------|
| test_phase53 | `tests/test_phase53_p3_archdebt_dead_code_cleanup.py` | No infra/tools/check_stale_tasks etc. refs (Phase 53 deleted legacy/cluster, not top-level .py files) |

**Verdict**: 0 hits. No prior-phase guard references.

---

## §3. Files in scope

### §3.1 DELETE (10 files: 5 .py + 3 shell + 1 __init__.py + 1 stale tools/workflow/ shell)

**`infra/tools/` top-level .py files** (5 zero-consumer CLI tools):
| File | LOC | Reason |
|------|-----|--------|
| `infra/tools/check_stale_tasks.py` | 76 | 0 consumers, CLI tool — Phase 40-era stale tasks detection |
| `infra/tools/issue_tracker.py` | 166 | 0 consumers, CLI tool — Phase 40-era issue tracking |
| `infra/tools/migrate_to_sqlite.py` | 109 | 0 consumers, one-shot migration — supersedes by Phase 54 lingwen-persistence |
| `infra/tools/regression_tracker.py` | 361 | 0 consumers, CLI tool — Phase 40-era regression tracking |
| `infra/tools/heartbeat.py` | 34 | 0 consumers, CLI tool — Phase 40-era heartbeat timestamp updater |
| `infra/tools/__init__.py` | 11 | Stale docstring mentions deleted subdirs |

Total .py LOC: 757 LOC

**`infra/tools/` subdir shell scripts** (3 zero-consumer):
| File | Reason |
|------|--------|
| `infra/tools/publish/run_publish.sh` | 0 consumers, Phase 40-era publish script |
| `infra/tools/content/run_check_naming.sh` | 0 consumers, Phase 40-era naming checker |
| `infra/tools/content/run_fix_naming.sh` | 0 consumers, Phase 40-era naming fixer |

**`tools/workflow/` stale shell scripts** (3 stale Phase 54 era):
| File | Reason |
|------|--------|
| `tools/workflow/backup_json.sh` | 0 consumers, post-Phase 54 |
| `tools/workflow/restore_sqlite.sh` | 0 consumers, references deleted `infra/tools/workflow/lib/` (Phase 84 C3) |
| `tools/workflow/revert_to_json.sh` | 0 consumers, references deleted `infra/tools/workflow/lib/` (Phase 84 C3) |

### §3.2 `infra/tools/workflow/` (lingwen-workflow migration residue)

After Phase 84 C3 deleted `infra/tools/workflow/lib/`, only 2 shell scripts remain:
- `infra/tools/workflow/run_workflow.sh` (294 LOC, 1 ref to lib/)
- `infra/tools/workflow/logging.sh` (Phase 40-era workflow shell logging)

**Out of scope for Phase 86** — Phase 86 is ARCHDEBT-MINI for top-level only. These shell scripts can be Phase 87 or future phase.

### §3.3 IN-PLACE rewrites

**0 sites** — no consumers, all DELETE.

---

## §4. 配套 stale refs

### §4.1 I074 invariant extension

Current I074 lists 8 zero-consumer dirs:
```
infra/tools/legacy/ + 顶层 tools/legacy/ + infra/event_sourcing/ + infra/core/ + infra/studio/ + infra/novel-factory/ + infra/llm_benchmarks/ + infra/poc/
```

For Phase 86, since we're deleting 5 .py files at `infra/tools/` top-level (not a subdir), I074 doesn't need extension. The .py files aren't a "directory" — they're individual files at the canonical `infra/tools/` location which still exists.

**Decision**: No new invariant. Phase 86 cleanup is logical continuation of I074 (infra/tools/ top-level cleanup of zero-consumer files, not new subdir).

### §4.2 infra/__init__.py wildcard check

**0 wildcard**. `infra/__init__.py` has no re-export from infra.tools.* modules.

### §4.3 __pycache__ residue cleanup

Per Phase 53d/78/79/80/82/84 lesson, C3 must `rm -rf infra/tools/__pycache__/` + `rm -rf infra/tools/workflow/__pycache__/` + `rm -rf infra/tools/publish/__pycache__/` + `rm -rf infra/tools/content/__pycache__/` to avoid G1 false-positive.

### §4.4 pre-C1 fixups

**0 sites** (no file MIGRATE, pure DELETE).

### §4.5 Empty directory cleanup

After C3 git rm, empty dirs `infra/tools/workflow/`, `infra/tools/publish/`, `infra/tools/content/` may remain as empty. Need `rmdir` per N.14 v23 v3 (Phase 84 lesson applied).

Also `tools/workflow/` after deleting the 3 shell scripts may become empty — rmdir needed.

---

## §5. Plan — atomic commits (per template §B)

| Commit | Subject | Files | +/- | Risk |
|--------|---------|-------|-----|------|
| **C0** | spec + 9-pattern audit | `docs/superpowers/specs/2026-09-15-phase-86-...md` (new) | +~200 / 0 | none |
| **C1** | git rm infra/tools/ 5 zero-consumer .py + 3 shell + __init__.py + tools/workflow/ 3 shell + __pycache__ + empty dir cleanup | 12 file deletes + 5 rmdir | 0 / -1670 bytes | low (post-§A verification) |
| **C2** | prior-phase guards fixup (test_phase53d add assert not exists for 5 .py files + test_phase18_8 docstring) | 2 prior-phase guards | +8 / -2 | low |
| **C3** | 12 regression guards G1-G12 | `tests/test_phase86_p3_archdebt_tools_top_level.py` (new) | +250 / 0 | low |
| **C4** | CLAUDE.md v54.18 + I074 invariant count note + handoff sync | `CLAUDE.md` + `collaboration/CURRENT_STATUS.md` + `collaboration/BACKLOG.md` + `docs/superpowers/handoffs/2026-09-15-phase-86-...md` (new) | +200 / -3 | low |

**Total**: 5 atomic commits (C0-C4), +~858 LOC / -1675 bytes (10 files DELETE + 5 rmdir + I074 note).

---

## §6. §A. test files migration plan (MANDATORY per template §A)

### §A.1 test files inventory

```
$ grep -rln "infra\.tools\.\(check_stale_tasks\|issue_tracker\|migrate_to_sqlite\|regression_tracker\|heartbeat\)" tests/
```

**0 hits** — no test files reference these CLI tools.

### §A.2 MIGRATE 路径

N/A — no test files for these CLI tools.

### §A.3 DELETE 路径

N/A — no test files to delete.

### §A.4 RETAIN-ORPHAN 路径

N/A.

### §A.5 Half-migration defense (per template §A.5)

- ✅ C1 (FULL DELETE) commit pathspec 含 BOTH infra/tools/* + tools/workflow/* + .lingwen/architecture.yml (no I074 change) + rmdir cleanups
- ✅ C1 commit message 含 "infra/tools/ 5 zero-consumer .py + 3 shell + tools/workflow/ 3 stale shell" (single sentence summary)

---

## §7. 验证 gates (per template §B)

| Gate | Command | Expected |
|------|---------|----------|
| pytest functional | `pytest tests/test_phase86_p3_archdebt_tools_top_level.py -v` | 12/12 PASS |
| 9-pattern audit | `grep -rn "infra\.tools\.(check_stale_tasks\|issue_tracker\|migrate_to_sqlite\|regression_tracker\|heartbeat\|publish\|content)" --include="*.py" apps/ packages/ tests/ tools/` | 0 hits |
| ruff | `ruff check packages/ tests/` | clean |
| Phase 53d prior-phase | `pytest tests/test_phase53d_event_sourcing.py -v` | All preserved + new consistency assert |
| Phase 18_8 prior-phase | `pytest tests/test_phase18_8_infra_init_simplified.py -v` | All preserved |
| Phase 77 invariant sync | `pytest tests/test_phase77_architecture_invariant_sync.py -v` | All preserved |

---

## §8. 风险评估 (per template §B)

| 风险 | 等级 | 缓解 |
|------|------|------|
| 误删有隐藏消费者的文件 | low | C0 spec 已完整 9-pattern audit (0 hits 验证 zero-consumer) |
| __pycache__/ 空目录残留 | low | C1 rmdir cleanup per N.14 v23 v3 lesson (Phase 84 applied) |
| tools/workflow/ 删 3 shell 后变成空目录 | low | C1 rmdir after git rm |
| historical 分析 docs 引用 deleted path | low | 历史 archive 保留 (commit blame) |
| I074 invariant grammar 漏洞 (Phase 60 orphan bug) | low | Phase 86 不新增 I074 entry, 无 orphan scope 风险 |

---

## §9. 不在范围 (per template §B)

- ❌ `infra/tools/workflow/{run_workflow.sh,logging.sh}` — Phase 87 ARCHDEBT-MINI scope (post Phase 86 saturation)
- ❌ `infra/tools/{publish,content,workflow}` subdirs (保留 empty directories 或保留 shell scripts)
- ❌ `infra/__init__.py` (已查无 wildcard, 不需修改)
- ❌ `tools/workflow/backup_json.sh` — 实际未引用 `infra/tools/`, 保留作为 Phase 86 DELETE 范围 (它本身 stale)
- ❌ 重构 `infra/tools/__init__.py` narrative — Phase 86 是 DELETE 整个文件 (包括 stale docstring), 不保留 partial

---

## §10. 完工标准 (per template §B)

- [ ] C0 spec committed with `@template:` reference + §A plan
- [ ] C1 git rm 10 files + 5 rmdir (3 subdirs + 1 __pycache__ + tools/workflow/)
- [ ] C2 prior-phase guards fixup (test_phase53d + test_phase18_8 docstring)
- [ ] C3 12 regression guards G1-G12
- [ ] C4 CLAUDE.md v54.18 + handoff doc sync
- [ ] All 6 validation gates GREEN
- [ ] 0 ruff errors
- [ ] 0 9-pattern audit hits

---

## §11. Lessons from prior phases (per template §C)

**Phase 78** (ARCHDEBT-MINI saturation): single commit pathspec BOTH infra + tests per I079 §A5 half-migration defense
**Phase 53c** (top-level tools/legacy/): 21 files DELETE in single commit, I074 extended
**Phase 84** (workflow empty dir): N.14 v23 v3 lesson — rmdir after git rm
**Phase 85** (consistency MERGE): ARCHDEBT-MIXED 2nd example, ruff --fix followup

---

## §12. Anti-patterns (per template §D)

- ❌ 让 tools/workflow/ 删 3 shell 后变 orphan 空目录 (rmdir needed)
- ❌ 让 infra/tools/{publish,content,workflow} 删 shell 后变 orphan 空目录 (rmdir needed)
- ❌ 假设 .py 文件自动 rmdir empty subdirs (Phase 78 lesson — explicit rmdir required)
- ❌ 假设 I074 需要新增 invariant (Phase 86 不新增 I074 entry — 文件不是 subdir, 不需要 invariant)
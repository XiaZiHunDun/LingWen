# Phase 87 P3-ARCHDEBT Design — `infra/tools/workflow/` residue cleanup (final ARCHDEBT-MINI)

> **版本**: 草稿 v1 (C0 spec + 9-pattern audit + §A test files migration plan)
> **日期**: 2026-09-15
> **承接**: Phase 86 P3-ARCHDEBT-MINI infra/tools/ top-level cleanup (v54.18)
> **模式**: ARCHDEBT-MINI 第 3 例 (Phase 78 + Phase 86) — final saturation
> **引用模板**: `@template: docs/superpowers/specs/_P3_ARCHDEBT_TEMPLATE.md` (I079 invariant enforced)

---

## §1. 背景

### §1.1 触发条件

Phase 84-86 cycle 后, `infra/tools/workflow/` 还剩 2 shell scripts (Phase 84 C3 删 `infra/tools/workflow/lib/` 时遗留):
- `run_workflow.sh` (294 LOC, 1 ref to deleted `infra/tools/workflow/lib.py`)
- `logging.sh` (19 LOC, Phase 40-era workflow shell logging)

### §1.2 闭环 ARCHDEBT cycle saturation

Phase 87 是 ARCHDEBT cycle 最后一例 — 删除 `infra/tools/workflow/` 整个目录 (2 shell scripts + empty dir cleanup)。完成后 `infra/tools/` 只剩 `__init__.py` 1 file (or 0 if Phase 87 也删),ARCHDEBT cycle essentially complete。

### §1.3 NON-INVASIVE ARCHDEBT-MINI pattern (Phase 86 lineage)

Phase 87 复用 Phase 86 NON-INVASIVE 模式:
- No MIGRATE / MERGE (pure DELETE only)
- No I0XX new invariant (no new subdir)
- No G9 CLAUDE.md sync expected-fail (no doc changes needed)
- 12 regression guards G1-G12 (similar to Phase 86)

---

## §2. 9-pattern audit (per N.14 lesson 1)

### §2.1 P1 — 字面 dotted-path imports

```bash
$ grep -rn "infra\.tools\.workflow\.\(run_workflow\|logging\)" --include="*.py" --include="*.sh" apps/ packages/ tests/ tools/ infra/ 2>/dev/null | grep -v "infra/tools/workflow/"
```

**Verdict**: 0 hits (no Python imports of these shell scripts).

### §2.2 P2 — function-body imports

**0 hits** (no consumers).

### §2.3 P3 — relative imports

**0 hits**.

### §2.4 P4 — filesystem path literals

| Site | File | Reference |
|------|------|-----------|
| docstring | `infra/tools/workflow/run_workflow.sh:4` | "核心逻辑委托给 infra/tools/workflow/lib.py" (deleted in Phase 84) |

**Verdict**: 1 site in scope — delete entire file (Phase 87 scope).

### §2.5 P5 — wildcard imports

**0 hits**.

### §2.6 P6 — monkeypatch indirection

**0 hits**.

### §2.7 P7 — `import X as Y` re-exports

**0 hits**.

### §2.8 P8 — docstring / narrative references

| Site | File | Reference |
|------|------|-----------|
| docstring | `infra/tools/workflow/run_workflow.sh:4` | "核心逻辑委托给 infra/tools/workflow/lib.py" |
| Phase 84 guard | `tests/test_phase84_p3_archdebt_workflow.py:11` | "infra/tools/workflow/lib/ directory gone" (G7 grep excludes run_workflow.sh per docstring note) |

**Verdict**: 1 site in scope (Phase 87 deletes run_workflow.sh entirely). 1 historical (Phase 84 guard G7 docstring note).

### §2.9 P9 — prior-phase guard references

| Site | File | Status |
|------|------|--------|
| test_phase84 | `tests/test_phase84_p3_archdebt_workflow.py:11,17` | Mentions `infra/tools/workflow/lib/` (Phase 84 lib DELETE target, NOT Phase 87 run_workflow.sh) |

**Verdict**: Phase 84 G7 specifically excludes `infra/tools/workflow/{run_workflow.sh,logging.sh}` per its docstring (line 12-13: "Excludes tests/ + __pycache__/ + infra/tools/workflow/{run_workflow.sh,logging.sh} (which legitimately reference 'from infra.tools.workflow.lib import' as the Python entry path — Phase 86 ARCHDEBT-MINI scope)."). After Phase 87, this exclusion is no longer needed (no more shell scripts in infra/tools/workflow/). Need C4 fixup to update Phase 84 G7 docstring.

---

## §3. Files in scope

### §3.1 DELETE (2 files + 1 empty dir)

**`infra/tools/workflow/` shell scripts** (2 zero-consumer post-Phase 84 C3):
| File | LOC | Reason |
|------|-----|--------|
| `infra/tools/workflow/run_workflow.sh` | 294 | Only ref is to deleted `infra/tools/workflow/lib.py` (Phase 84 C3). Phase 84 created `packages/lingwen-workflow/` as canonical — bash wrapper obsolete |
| `infra/tools/workflow/logging.sh` | 19 | Phase 40-era workflow shell logging, no consumers post-Phase 84 |

Total: -313 LOC + empty `infra/tools/workflow/` directory

### §3.2 IN-PLACE rewrites

| Site | File | Update |
|------|------|--------|
| docstring | `tests/test_phase84_p3_archdebt_workflow.py:11-13` | Remove "Excludes infra/tools/workflow/{run_workflow.sh,logging.sh}" exclusion note (no longer relevant post-Phase 87) |

---

## §4. 配套 stale refs

### §4.1 I074 invariant

I074 NOT extended (Phase 87 deletes individual files at infra/tools/workflow/, NOT new subdir — same as Phase 86).

### §4.2 __pycache__ residue cleanup

```bash
rm -rf infra/tools/workflow/__pycache__/
```

### §4.3 Empty directory cleanup

```bash
rmdir infra/tools/workflow/  # after git rm removes 2 tracked files
```

N.14 v23 v3 lesson: empty dir residue after git rm.

### §4.4 pre-C1 fixups

**0 sites** (pure DELETE, no MIGRATE).

---

## §5. Plan — atomic commits (per template §B)

| Commit | Subject | Files | +/- | Risk |
|--------|---------|-------|-----|------|
| **C0** | spec + 9-pattern audit | `docs/superpowers/specs/2026-09-15-phase-87-...md` (new) | +~200 / 0 | none |
| **C1** | git rm 2 shell scripts + __pycache__ cleanup + rmdir empty `infra/tools/workflow/` | 2 file deletes + 1 rmdir | 0 / -313 LOC | low |
| **C2** | prior-phase guards fixup (test_phase84 G7 docstring note removal — no longer need to exclude deleted files) | 1 prior-phase guard | +1 / -2 | low |
| **C3** | 12 regression guards G1-G12 | `tests/test_phase87_p3_archdebt_tools_workflow_residue.py` (new) | +250 / 0 | low |
| **C4** | CLAUDE.md v54.19 + I074 saturation note + handoff sync | `CLAUDE.md` + `collaboration/CURRENT_STATUS.md` + `collaboration/BACKLOG.md` + `docs/superpowers/handoffs/2026-09-15-phase-87-...md` (new) | +200 / -3 | low |
| | C5 ruff --fix (Phase 31 lesson) | minor | +/= | low |

**Total**: 5-6 atomic commits, +~850 LOC / -316 LOC (2 files DELETE + 1 rmdir).

---

## §6. §A test files migration plan (MANDATORY per template §A)

### §A.1 test files inventory

```
$ grep -rln "infra\.tools\.workflow\.\(run_workflow\|logging\)\|infra/tools/workflow/\(run_workflow\|logging\)" tests/
```

**0 hits** — no test files directly reference these shell scripts.

### §A.2 MIGRATE 路径

N/A — no test files for these shell scripts.

### §A.3 DELETE 路径

N/A.

### §A.5 Half-migration defense (per template §A.5)

- ✅ C1 (FULL DELETE) commit pathspec 含 `infra/tools/workflow/{run_workflow.sh,logging.sh}` + empty dir cleanup
- ✅ C1 commit message: "infra/tools/workflow/ residue cleanup — 2 shell scripts DELETE + rmdir empty directory" (single sentence summary)

---

## §7. 验证 gates (per template §B)

| Gate | Command | Expected |
|------|---------|----------|
| pytest functional | `pytest tests/test_phase87_p3_archdebt_tools_workflow_residue.py -v` | 12/12 PASS |
| pytest Phase 84 regression | `pytest tests/test_phase84_p3_archdebt_workflow.py -v` | 43/43 PASS (G7 still 0 infra.tools.workflow refs post-Phase 87) |
| pytest Phase 53d | `pytest tests/test_phase53d_event_sourcing.py -v` | 8/8 PASS |
| pytest Phase 18_8 | `pytest tests/test_phase18_8_infra_init_simplified.py -v` | 6/6 PASS |
| pytest Phase 77 | `pytest tests/test_phase77_architecture_invariant_sync.py -v` | 12/12 PASS |
| pytest Phase 60 | `pytest tests/test_phase60_p3_archdebt_template.py -v` | 6/6 PASS |
| 9-pattern audit | `grep -rn "infra\.tools\.workflow\.\(run_workflow\|logging\)" --include="*.py" --include="*.sh" apps/ packages/ tests/ tools/ infra/` | 0 hits |
| ruff | `ruff check packages/ tests/` | clean on Phase 87 files |

---

## §8. 风险评估 (per template §B)

| 风险 | 等级 | 缓解 |
|------|------|------|
| Phase 84 G7 grep pattern needs update after Phase 87 | low | C2 update removes the "Excludes run_workflow.sh/logging.sh" docstring note (no longer relevant — files deleted) |
| __pycache__/ residue | low | C1 `rm -rf infra/tools/workflow/__pycache__/` per N.14 v23 v3 lesson |
| Empty `infra/tools/workflow/` dir | low | C1 `rmdir infra/tools/workflow/` after git rm |
| ARCHDEBT cycle essentially complete | n/a | Phase 87 is final saturation — future ARCHDEBT work would need new candidates (out of scope) |

---

## §9. 不在范围 (per template §B)

- ❌ `infra/tools/__init__.py` (likely stale docstring mentioning deleted subdirs) — could be Phase 88 if needed (post-Phase 87 saturation review)
- ❌ `infra/.state/` orphan runtime artifacts — already gitignored (Phase 53e precedent)
- ❌ `tools/` directory other shell scripts (post Phase 86 saturation review)
- ❌ Non-ARCHDEBT 工作 (feature work, bug fixes, etc.) — out of scope

---

## §10. 完工标准 (per template §B)

- [ ] C0 spec committed with `@template:` reference + §A plan
- [ ] C1 git rm 2 shell scripts + __pycache__ cleanup + rmdir empty dir
- [ ] C2 prior-phase guards fixup (test_phase84 G7 docstring update)
- [ ] C3 12 regression guards G1-G12
- [ ] C4 CLAUDE.md v54.19 + handoff doc sync
- [ ] C5 ruff --fix trailing newlines
- [ ] All 7 validation gates GREEN
- [ ] 0 ruff errors
- [ ] 0 9-pattern audit hits

---

## §11. Lessons from prior phases (per template §C)

**Phase 86** (ARCHDEBT-MINI NON-INVASIVE): cleanup of individual files at canonical location doesn't break prior-phase guards. Phase 87 reuses this pattern for infra/tools/workflow/ subdir.

**Phase 84** (workflow MIGRATE): Phase 84 C3 deleted infra/tools/workflow/lib/ (8 Python modules) but left 2 shell scripts (run_workflow.sh + logging.sh) as residue. Phase 87 closes this residue 3 phases later.

**Phase 84 G7 docstring note** (line 12-13): "Excludes infra/tools/workflow/{run_workflow.sh,logging.sh} ... Phase 86 ARCHDEBT-MINI scope" — this exclusion was created in anticipation of Phase 86 cleanup. Phase 86 didn't actually need the exclusion (the .sh files don't match Python grep `--include=*.py`). Phase 87 removes the exclusion note entirely.

---

## §12. Anti-patterns (per template §D)

- ❌ 让 Phase 84 G7 docstring 仍 mention deleted shell scripts (Phase 87 update removes the note)
- ❌ 让 empty `infra/tools/workflow/` dir 残留 (rmdir required after git rm)
- ❌ 让 `__pycache__/` 残留 (rm -rf per N.14 v23 v3 lesson)
- ❌ 假设 Phase 86 已经做了 Phase 87 工作 — Phase 86 明确 out-of-scope infra/tools/workflow/{run_workflow.sh,logging.sh} (handoff §8)
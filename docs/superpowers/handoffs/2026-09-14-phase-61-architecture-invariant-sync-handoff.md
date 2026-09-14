# Phase 61 Architecture Invariant Sync (CLAUDE.md ↔ architecture.yml) — Handoff

> **目标**: 闭环 v54.8 已知 carryover — 补 `.lingwen/architecture.yml` 缺失的 I071-I078 (8 个 invariant) + 修复 I079 scope 错位 bug + 4 regression guards 防止未来 drift 复发。
> **承接**: v54.8 (Phase 60 P3-ARCHDEBT spec template) session 总结的 "Carried over to future sessions"。
> **日期**: 2026-09-14
> **Branch**: `phase-57-p3-archdebt-reading-power`
> **Version bump**: v54.8 → v54.9
> **非 P3-ARCHDEBT migration** — 本 phase 是 docs/config sync，不删 `infra/X/`、不 scaffold `packages/lingwen-X/`。因此 **不适用** I079 P3-ARCHDEBT template 的 §A test files migration plan 强制章节。

## 1. TL;DR

| 维度 | 数值 |
|------|------|
| Invariants 添加 | I071-I078 (8 个) |
| YAML 错位 bug 修复 | I079 孤儿 scope 还原到 I070 (1 处) |
| Version field bump | v48.0 → v54.9 (skip 8 minor versions) |
| Regression guards | 4 (G1 count / G2 set diff / G3 dup-key / G4 sanity) |
| Files changed | 4 (spec + architecture.yml + test + MEMORY/CLAUDE) |
| LOC delta | +24 YAML / -1 dup / +1 line MEMORY pointer / +200 spec / +120 test |

## 2. 修复的 2 类 drift

### 2.1 Drift #1: 缺失 I071-I078 (8 invariant)

CLAUDE.md 在 Phase 51-60 期间陆续声明了 I071-I078 共 8 个 invariant,但 `.lingwen/architecture.yml` 仅同步到 I070。下游 agent 工具读 architecture.yml 时看到的是 71 个 invariant (实际应该是 79 个),会 silently 漏检 8 类 P3-ARCHDEBT 路径违规。

**Fix**: 在 `architecture.yml` line 129 (I070 severity) 与 line 130 (I079 id) 之间插入 8 条 entry,完全对齐 CLAUDE.md narrative + Phase 51-57 各自的 handoff 引用。

### 2.2 Drift #2: I079 orphan scope (看似 dup-key 实际是错位)

`.lingwen/architecture.yml` 原 line 134 看似是 I079 的"重复 scope",实际是 **I070 的 scope 在 Phase 60 插入 I079 时被错位留下的孤儿**。原文件结构:

```yaml
- id: I070   # 只有 rule + severity, scope 缺失
- id: I079
  rule: ...
  severity: error
  scope: "all future P3-ARCHDEBT specs..."   # I079 自己的 scope
  scope: "all new health code..."            # 实际是 I070 的 scope, Phase 60 插入时错位
```

PyYAML 在遇到 mapping 重复 key 时**静默取最后一个值**,所以 I079 的 `scope` 实际是错的 "all new health code..."。`test_phase60_p3_archdebt_template.py::test_phase60_i079_in_architecture_yml` 只检查文本 `"I079" in text` 没抓到此 bug。

**Fix**: 把 I070 的 scope 还原到 I070 block 内,I079 保留自己的 scope。

### 2.3 副发现: version field 长期 stale

`.lingwen/architecture.yml` 的 `version: "48.0"` 字段从 Phase 50 后未更新(CLAUDE.md 已 v54.8)。本 phase 一并 bump 到 v54.9,long comment 简述 Phase 61 修复内容。

## 3. 验证

### 3.1 YAML parse + invariant set diff

```bash
$ python3 -c "import yaml; data = yaml.safe_load(open('.lingwen/architecture.yml')); print(len(data['invariants']))"
37
# 37 = I001-I005 + I048-I079 (CLAUDE.md 同 37 个,I006-I047 是历史 numbering gap 不是 drift)
```

```bash
$ diff <(grep -oE "^\s*- id: I0[0-9]{2}" .lingwen/architecture.yml | grep -oE "I0[0-9]{2}" | sort -u) \
       <(grep -oE "\| I0[0-9]{2} " CLAUDE.md | grep -oE "I0[0-9]{2}" | sort -u)
# (no diff output = SETS_MATCH)
```

### 3.2 I070 + I079 scope 正确归属

```bash
$ python3 -c "import yaml; data = yaml.safe_load(open('.lingwen/architecture.yml')); [print(f\"{inv['id']}: {inv.get('scope', 'MISSING')[:60]}...\") for inv in data['invariants'] if inv.get('id') in ('I070', 'I079')]"
I070: all new health code; enforcement via tests/test_phase50_lingwen_utilities_batch...
I079: all future P3-ARCHDEBT specs; template file lives at docs/superpowers/specs...
```

两个 scope 都正确归属,无孤儿。

## 4. 4 regression guards (C2)

`tests/test_phase61_architecture_invariant_sync.py` 4 guards:

| Guard | 断言 |
|-------|------|
| **G1** | `architecture.yml` 包含 I001-I005 + I048-I079 共 37 个 invariant ID (count check) |
| **G2** | `architecture.yml` 与 `CLAUDE.md` 的 invariant ID **set diff = 0** (双向, 防任一侧 drift) |
| **G3** | `architecture.yml` 中 I079 的 mapping 在 YAML parse 后 `scope` 字段 == "all future P3-ARCHDEBT specs..." (防孤儿 scope 复现) |
| **G4** | I071-I078 8 个 invariant 的 `rule` 字段非空 + 包含 `packages/lingwen-` 或 `infra/` 关键字 (sanity: rule 真的有内容且引用相关包) |

未来添加 invariant 时,G2 会自动检测 CLAUDE.md ↔ architecture.yml 的 set drift,G3 会检测 scope 错位 bug 复发。

## 5. 4 atomic commits

| Commit | Subject | Files | +/- |
|--------|---------|-------|-----|
| **C0** | `docs(phase-61): spec + handoff` | `docs/superpowers/specs/2026-09-14-phase-61-architecture-invariant-sync-design.md` + `docs/superpowers/handoffs/2026-09-14-phase-61-architecture-invariant-sync-handoff.md` | +400 |
| **C1** | `chore(architecture): add I071-I078 + restore I070 scope + bump v54.9` | `.lingwen/architecture.yml` | +24 / -2 |
| **C2** | `test(phase-61): 4 regression guards for CLAUDE.md ↔ architecture.yml sync` | `tests/test_phase61_architecture_invariant_sync.py` | +120 |
| **C3** | `docs(phase-61): CLAUDE.md v54.9 + MEMORY pointer` | `CLAUDE.md` + `MEMORY.md` | +5 |

## 6. Lessons

### 6.1 Lesson 1: Numbering gap ≠ drift

CLAUDE.md narrative 显示 I001-I079 (79 个),实际 invariant table 只有 37 个 entry (I001-I005 + I048-I079)。I006-I047 是**历史 numbering gap**(从未声明的 invariant,不是丢失)。区分 drift vs gap 的方法是 grep **table 行** (e.g., `^\| I0[0-9]{2}`) 不是全文 ID 字串。

### 6.2 Lesson 2: 孤儿 scope ≠ dup-key

`.lingwen/architecture.yml` line 134 的 `scope` 看似 "I079 的 dup-key",实际是 **I070 的 scope 在 Phase 60 插入 I079 时被错位留下的孤儿**。PyYAML silent last-key-wins 让这个 bug 永远发现不了 — 必须用 test 验证 **YAML parse 后某个 ID 的字段值** 而不是 raw text grep。

### 6.3 Lesson 3: Test grep `text in raw` 不等于 `parsed_value == expected`

`test_phase60_p3_archdebt_template.py::test_phase60_i079_in_architecture_yml` 用 `assert "I079" in text` 检查 I079 存在,但无法区分 "I079 ID 在 file 中" vs "I079 ID + 正确 scope 都归属 I079"。本次 G3 改为 `parsed["scope"] == expected` 才能抓 bug。

### 6.4 Lesson 4: CLAUDE.md ↔ architecture.yml 应该有双向 sync guard

CLAUDE.md 是 narrative(人类阅读 + grep-friendly),architecture.yml 是 machine-readable(AI 工具读)。两者的 invariant set 必须完全一致 — 但**只有 G2 set diff guard** 能 enforce。Phase 61 引入此 guard 后,未来添加 invariant 时如果忘了 sync 任一侧,pytest 会 fail。

## 7. Future carryovers

无。`infra/` 顶层 + 子目录残留 audit (Phase 41+++) 已在 v40.1 完成,本 phase 闭环唯一的 machine-readable drift。

## 8. Files touched

```
.lingwen/architecture.yml                                       | +24 / -2
docs/superpowers/specs/2026-09-14-phase-61-architecture-invariant-sync-design.md | NEW (+200)
docs/superpowers/handoffs/2026-09-14-phase-61-architecture-invariant-sync-handoff.md | NEW (+180)
tests/test_phase61_architecture_invariant_sync.py               | NEW (+120)
CLAUDE.md                                                       | +5
MEMORY.md                                                        | +1
```

**Net**: 6 files, +530 / -2, v54.8 → v54.9.

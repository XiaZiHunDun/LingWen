# Phase 77 Architecture Invariant Sync (CLAUDE.md ↔ architecture.yml) — Design

> **目标**: 闭环 v54.8 已知 carryover — CLAUDE.md 已声明 I001-I079 (79 个 invariant) 但 `.lingwen/architecture.yml` 仅 I001-I070 + I079 (71 个 invariant)，**缺 I071-I078 (8 个)**。本次 phase 修复此 machine-readable drift 并附 4 个 regression guards 防止再发生。
> **承接**: v54.8 Phase 60 session 总结的 "Carried over to future sessions" 明确列出。
> **日期**: 2026-09-14
> **Branch**: `phase-57-p3-archdebt-reading-power`
> **非 P3-ARCHDEBT migration** — 本 phase 是 docs/config sync，不删除 `infra/X/`，不 scaffold `packages/lingwen-X/`。因此 **不适用** I079 P3-ARCHDEBT template (§A test files migration plan 强制章节)。

## 1. 背景

### 1.1 Session carryover 来源

v54.8 (Phase 60 P3-ARCHDEBT spec template) 完成的 session 总结明确 carryover:

> **Carried over to future sessions**: infra/I071-I078 declared in CLAUDE.md but missing from architecture.yml (machine-readable drift — minor)

**机器可读层 (`.lingwen/architecture.yml`)** 是 invariant 声明的 source of truth — 所有 AI/agent 工具读它。**人类可读层 (`CLAUDE.md`)** 是 invariant 的 narrative 描述。当两者 drift 时:

1. Agent 工具看到的 invariant 数 ≠ CLAUDE.md 列的数 → 工具会 missed-check 8 个 invariant 范围
2. 新 phase 添加 invariant 时, AI 只看 `architecture.yml` last ID (I079) 增量 → 会与 CLAUDE.md 已经声明的 I071-I078 冲突编号
3. 测试守卫 (e.g., `test_phase5X_*.py`) 用 `assert "I077" in architecture_yml_text` 类型检查会失败

### 1.2 当前 drift 详细 (2026-09-14 fresh audit)

```bash
$ grep -E "I071|I072|I073|I074|I075|I076|I077|I078" .lingwen/architecture.yml
# (0 results — 8 个 invariant 完全缺失)

$ grep -cE "I079" .lingwen/architecture.yml
2  # id + comment, 但 I079 自身有 bug
```

| Invariant | 阶段 | CLAUDE.md | architecture.yml | 声明内容摘要 |
|-----------|------|-----------|------------------|---------------|
| I071 | Phase 51 | ✅ | ❌ MISSING | `packages/lingwen-prose-judge/` 是 prose rubric v2 judge 唯一实包 |
| I072 | Phase 51 | ✅ | ❌ MISSING | `packages/lingwen-prose-snapshot/` 是 snapshot+diff 唯一实包 |
| I073 | Phase 51 | ✅ | ❌ MISSING | `packages/lingwen-project-characters/` 是角色名抽取唯一实包 |
| I074 | Phase 53+53c+53d+53e | ✅ | ❌ MISSING | 6 个零消费者目录已删 (`infra/tools/legacy/` + `tools/legacy/` + `infra/event_sourcing/` + `infra/core/` + `infra/studio/` + `infra/novel-factory/`) |
| I075 | Phase 54 | ✅ | ❌ MISSING | `packages/lingwen-persistence/` 是 SQLite 持久化唯一实包 |
| I076 | Phase 56 | ✅ | ❌ MISSING | `packages/lingwen-world-db/` 是 World DB 唯一实包 |
| I077 | Phase 57 | ✅ | ❌ MISSING | `packages/lingwen-reading-power/` 是 Reading Power 唯一实包 |
| I078 | Phase 55 | ✅ | ❌ MISSING | `packages/lingwen-cross-volume/` 是 Cross-Volume Ripple 唯一实包 |

### 1.3 副发现: I079 dup-key bug

`.lingwen/architecture.yml` line 130-134:

```yaml
  - id: I079   # ★ Phase 60 NEW
    rule: "..."
    severity: error
    scope: "all future P3-ARCHDEBT specs; template file lives at docs/superpowers/specs/_P3_ARCHDEBT_TEMPLATE.md"
    scope: "all new health code; enforcement via tests/test_phase50_lingwen_utilities_batch.py + grep -rln \"infra\\.health\\b\" --include=\"*.py\" packages/ apps/ tests/ infra/ → 0 行"
```

第 4 行 (line 134) 是 I070 的 `scope` 错粘到 I079 (Phase 60 创建时 sed/copy-paste error)。YAML 解析时后者**静默覆盖**前者 (PyYAML `yaml.safe_load` 取 last 值) — **不报错**。`test_phase60_p3_archdebt_template.py::test_phase60_i079_in_architecture_yml` 只检查文本 `"I079" in text` 没抓到此 bug。

### 1.4 修复路径

3 类修复:
1. **Insert**: 在 line 129 (I070 scope) 与 line 130 (I079 id) 之间插入 I071-I078 8 条 entries
2. **Fix dup-key**: 删除 line 134 (I079 的错粘 scope — I079 应该只保留 I070-style enforcement scope 或更简单无 scope)
3. **Guards**: 在 `tests/test_phase77_architecture_invariant_sync.py` 加 4 guards 防止未来 drift

## 2. 9-pattern 审计 (2026-09-14)

| Pattern | Verdict |
|---------|---------|
| `architecture.yml` 现有 invariant IDs | I001-I070 + I079 = 71 个 (期望 79 个) |
| CLAUDE.md 现有 invariant IDs | I001-I079 = 79 个 ✅ |
| Set diff (CLAUDE.md − architecture.yml) | {I071, I072, I073, I074, I075, I076, I077, I078} = 8 个 |
| Set diff (architecture.yml − CLAUDE.md) | {} 0 个 |
| YAML dup-key 检查 | line 134 I079 scope 重复 1 次 |
| 已有的 invariant regression test | `test_phase60_p3_archdebt_template.py` 仅 G4 检 I079 in architecture.yml 文本存在 |
| 已有 invariant 一致性 test | ❌ 无 — 本 phase 引入 |
| Production code impact | NONE — 仅 YAML + 新 test file |
| Test runner impact | NONE — 新 test file 默认会被 pytest 发现 |

## 3. 计划

| Commit | Subject | Files | +/- |
|--------|---------|-------|-----|
| C0 | spec + plan handoff (this doc) | 1 | +200 |
| C1 | `chore(architecture): add I071-I078 + fix I079 dup-scope` | 1 | +24 lines / -1 line |
| C2 | `test(phase-77): 4 regression guards` | 1 | +120 |
| C3 | `docs(phase-77): v54.8→v54.9 + handoff + MEMORY sync` | 4 | +150 |

**Net**: +24 YAML lines, +1 dup-key fix, +120 test LOC, v54.8 → v54.9, 8 invariant drift 闭环。

### C1 详细: `.lingwen/architecture.yml` 修改

在 line 129 (I070 scope 终止) 与 line 130 (I079 id 起始) 之间插入 8 个 invariant 条目。**新增 entries 格式对齐 line 119-128 I068-I070 既有结构**:

```yaml
  - id: I071   # ★ Phase 51 NEW
    rule: "packages/lingwen-prose-judge/ ... infra.prose_judge.* 路径非法 (Phase 51 P3-ARCHDEBT prose 簇)"
    severity: error
  - id: I072   # ★ Phase 51 NEW
    rule: "packages/lingwen-prose-snapshot/ ... infra.prose_snapshot.* 路径非法 (Phase 51 P3-ARCHDEBT prose 簇)"
    severity: error
  - id: I073   # ★ Phase 51 NEW
    rule: "packages/lingwen-project-characters/ ... infra.project_characters.* 路径非法 (Phase 51 P3-ARCHDEBT prose 簇)"
    severity: error
  - id: I074   # ★ Phase 53+53c+53d+53e NEW
    rule: "infra/tools/legacy/ + tools/legacy/ + infra/event_sourcing/ + infra/core/ + infra/studio/ + infra/novel-factory/ 6 个零消费者目录已删；其下任何路径非法 (Phase 53 + 53c + 53d + 53e P3-ARCHDEBT 残留清理，~12868 LOC dead code)"
    severity: error
  - id: I075   # ★ Phase 54 NEW
    rule: "packages/lingwen-persistence/ 是 SQLite 持久化层唯一实包；infra.persistence.* 和 infra/persistence/ 路径非法 (Phase 54 P3-ARCHDEBT infra/persistence 全量迁移)"
    severity: error
  - id: I076   # ★ Phase 56 NEW
    rule: "packages/lingwen-world-db/ 是 World DB 唯一实包；infra.world_db.* 和 infra/world_db/ 路径非法 (Phase 56 P3-ARCHDEBT infra/world_db 全量迁移)"
    severity: error
  - id: I077   # ★ Phase 57 NEW
    rule: "packages/lingwen-reading-power/ 是 Reading Power System 唯一实包；infra.reading_power.* 和 infra/reading_power/ 路径非法 (Phase 57 P3-ARCHDEBT infra/reading_power 全量迁移)"
    severity: error
  - id: I078   # ★ Phase 55 NEW
    rule: "packages/lingwen-cross-volume/ 是 Cross-Volume Ripple System 唯一实包；infra.cross_volume.* 和 infra/cross_volume/ 路径非法 (Phase 55 P3-ARCHDEBT infra/cross_volume 全量迁移)"
    severity: error
```

**Dup-key fix**: 删除 line 134 (`scope: "all new health code..."`)，保留 line 133 (I079 自身 scope)。最终 I079 block:

```yaml
  - id: I079   # ★ Phase 60 NEW
    rule: "..."
    severity: error
    scope: "all future P3-ARCHDEBT specs; template file lives at docs/superpowers/specs/_P3_ARCHDEBT_TEMPLATE.md"
```

### C2 详细: `tests/test_phase77_architecture_invariant_sync.py`

| Guard | Assertion |
|-------|-----------|
| G1 | `architecture.yml` 包含 I001-I079 全部 79 个 ID (count ≥ 79) |
| G2 | `architecture.yml` 与 `CLAUDE.md` 的 invariant ID set **完全相等** (set diff = 0) |
| G3 | `architecture.yml` 中 I079 的 `scope` key **只出现一次** (PyYAML parses without duplicate-key warning — Python 3.12+ duplicate-key silent override 检查) |
| G4 | `architecture.yml` 中 I071-I078 8 个 ID 各自的 `rule` 字段非空 + 含 `packages/lingwen-` 或 `infra/` 关键字 (sanity: rule 字段真的有内容 + 引用了相关包) |

### C3 详细: docs sync

1. `CLAUDE.md` line 1: `v54.8 (Phase 60 ...)` 之前插入 `v54.9 (Phase 77 architecture invariant sync — 补 I071-I078 8 个 invariant 进 architecture.yml + fix I079 dup-scope key + 4 regression guards 防止 CLAUDE.md ↔ architecture.yml drift 复发)` + 加 v54.9 phase-77 entry 到 "已知遗留" 列表
2. `MEMORY.md`: 添加 `phase-77-architecture-invariant-sync.md` 指针 (under "Topic Files" → Phase 53c-60 系列扩展)
3. `docs/superpowers/handoffs/2026-09-14-phase-77-architecture-invariant-sync-handoff.md`: 完整 handoff
4. `.lingwen/architecture.yml` line 1 注释: `version: v54.9` (如有 version field — 2026-09-14 fresh audit)

## 4. 验证 gates

```bash
# 1. YAML 解析无 dup-key (PyYAML 检测)
python -c "import yaml; yaml.safe_load(open('.lingwen/architecture.yml').read().split('invariants:')[1].split('#')[0])" 

# 2. 新 guards 全过
uv run pytest tests/test_phase77_architecture_invariant_sync.py -v

# 3. 既有 Phase 5x/6x guards 不回归 (no_false_neg)
uv run pytest tests/test_phase5X_*.py tests/test_phase6X_*.py -v --tb=no -q

# 4. set diff 实测
diff <(grep -oE "I0[0-9]{2}" .lingwen/architecture.yml | sort -u) \
     <(grep -oE "I0[0-9]{2}" CLAUDE.md | sort -u)
# Expected: (no output = identical sets)
```

## 5. 风险评估

| 变更 | 风险 | 缓解 |
|------|------|------|
| architecture.yml +24 lines | LOW — 新增 entry 不改既有, 仅 fill gap | grep pre-existing ID count = 71, post-add = 79 |
| I079 dup-scope fix | LOW — 删 line 134 (错粘的 I070 scope), 保留 line 133 (I079 真 scope) | G3 explicitly 检查 dup-key, G1 still passes (I079 ID 仍在) |
| 新 test file | NONE — additive | existing pytest collection 不影响 |
| CLAUDE.md version bump | NONE — 纯文本改 | grep pre/post version 字串 |
| MEMORY.md +1 line pointer | NONE — 已留 59 行裕量 (< 200) | `wc -l MEMORY.md` 检查 |

## 6. 不在范围

- ❌ 修改 I001-I070 既有 invariant 的 rule 文本 (drift 修复 ≠ 文本重写)
- ❌ 添加 I080+ 新 invariant (本 phase 仅 sync, 不新增)
- ❌ 改 CLAUDE.md invariant table 的 narrative (人类可读层已正确, 只机器层缺)
- ❌ P3-ARCHDEBT template 不适用本 phase (I079 template 强制 §A test files migration plan — 本 phase 无 infra/X → packages/X 迁移)

## 7. 完工标准 checklist

- [ ] C1: 8 个 invariant (I071-I078) 插入 line 129 与 line 130 之间
- [ ] C1: I079 block 中 dup-scope (line 134) 删除, 只保留 I079 自身 scope
- [ ] C2: `tests/test_phase77_architecture_invariant_sync.py` 4 guards 全过
- [ ] C3: CLAUDE.md version line 加 v54.9 + handoff 指针
- [ ] C3: `docs/superpowers/handoffs/2026-09-14-phase-77-architecture-invariant-sync-handoff.md` 写完
- [ ] C3: MEMORY.md +1 指针 (line count < 200)
- [ ] Phase 5x/6x 既有 guards GREEN 不回归
- [ ] 4 atomic commits + ff-merge to master

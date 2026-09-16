# Phase 91 — P2-ILLUSTRATIONS-BIBLE-CANONICAL Handoff

> **状态**: ✅ 完成 (2026-09-16)
> **版本**: v55.1
> **Branch**: master (direct commit, per simplified workflow 2026-09-15)
> **Spec**: `docs/superpowers/specs/2026-09-16-phase-91-illustrations-bible-canonical-design.md`
> **Plan**: `docs/superpowers/plans/2026-09-16-phase-91-illustrations-bible-canonical.md`

---

## 执行摘要

闭环 Phase 90 carryover P2-ILLUSTRATIONS-BIBLE-CANONICAL（deviation 2）— 替换 v1 dead path `<root>/config/characters.json` → 新 rich bible JSON `<root>/config/illustrations/characters.json`。**Full closure**：删 v1 `_load_character_bible` 函数 + 删 v1 path 字符串引用 + 重写 pipeline.py docstring。新 `bible_loader.py` submodule（lingwen-illustrations 内部）+ 19 unit tests (13 base + 6 parametrized) + 2 regression guards (G8 + G9)。I087 invariant 不变。

**MILESTONE**: REQ-002 v1 第 1 个 v2 sub-project 闭环。brainstorming-decided path: 新文件 + 最小 schema + permissive + silent missing + Full closure。

---

## §1. Commits (按时间顺序)

6 atomic commits (per plan; C0 spec / C0.5 self-review / C1 plan 在 phase 91 开始前已合入):

| # | SHA | Type | Subject |
|---|-----|------|---------|
| 1 | `feb7db17` | docs | P2-ILLUSTRATIONS-BIBLE-CANONICAL design spec (含 self-review fixup) |
| 2 | `2461d031` | docs | implementation plan (TDD task list) |
| 3 | `f048ab79` | feat | bible_loader + test_bible_loader (TDD) |
| 4 | `1048eb2b` | test | parametrized non-str name cases (defensive) |
| 5 | `aadfbf4c` | refactor | pipeline integrates bible_loader (delete v1 path) |
| 6 | `a320c398` | test | G8 + G9 regression guards |

---

## §2. 验证结果

### 后端
- pytest packages/lingwen-illustrations/tests/ (rootdir=packages/lingwen-illustrations): **72 passed** (53 baseline + 13 new + 6 parametrized)
- pytest tests/test_phase90_illustrations.py: **17 passed** (15 existing G1-G7 + G8 + G9)
- ruff check pipeline.py + bible_loader.py: **All checks passed!**

### Regression guards
- G8 (v1 path gone in src/): **GREEN** (src/ 中 0 references to `<root>/config/characters.json`, strip docstring per N.14 v21)
- G9 (bible_loader public): **GREEN** (`load_character_bible` in `__all__`)

### Cluster cumulative
- 34 lingwen-* packages (unchanged from Phase 90)
- I087 invariant 保留（bible_loader 是内部 submodule，invariant 边界未动）

---

## §3. 交付物

### Backend
- 新 submodule: `packages/lingwen-illustrations/src/lingwen_illustrations/bible_loader.py` (~95 LOC)
  - 1 public function: `load_character_bible(project_root) -> list[dict[str, str]]`
  - Permissive schema validation
  - Standard library only (json, logging, pathlib) + `LoadError` from exceptions
- 修改: `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py`
  - 删 `_load_character_bible` 函数 (lines 54-70, ~17 LOC)
  - 删 v1 path 字符串 (`<root>/config/characters.json`)
  - 重写 module docstring（Phase 91 P2-ILLUSTRATIONS-BIBLE-CANONICAL 解释）
  - 加 import `bible_loader.load_character_bible`
- 新 test: `packages/lingwen-illustrations/tests/test_bible_loader.py` (~180 LOC, 14 tests / 19 cases)
- 修改: `tests/test_phase90_illustrations.py` (G8 + G9, ~30 LOC)

### Docs
- 删 `collaboration/BACKLOG.md` P2-ILLUSTRATIONS-BIBLE-CANONICAL row
- CLAUDE.md v55.0 → v55.1
- CURRENT_STATUS.md 新增 Phase 91 row

---

## §4. Carryover closed

- ✅ P2-ILLUSTRATIONS-BIBLE-CANONICAL (Phase 90 §4 deviation 2) — 闭环
- 📋 剩余 carryover: P2-EXTRACT-ENUM (独立 sub-project, lingwen-shared TaskType enum)

---

## §5. Future work (REQ-002 v2 candidates)

- Image provider adapters (Phase 94+)
- Reference image i2i (Phase 93+)
- LRU archive (Phase 95+)
- Notification center (Phase 96+)
- Per-project settings (Phase 92+)
- Real-API b64_json decoding (Phase 94+)
- regenerate PUT atomic (Phase 94+)
- P2-EXTRACT-ENUM (Phase 92+)

---

## §6. Lessons

### 1. Pre-spec code reading catches hidden scope

Phase 90 handoff §4 deviation 2 描述"API mismatch" — 读 actual code 后发现 v1 path 永远空（0 hits），permissive 哲学下 LLM 永远收到 "(无角色档案)"。这比 handoff 描述的 mismatch 更严重 — bible 实际是"完全不存在的数据源"。

**Future**: handoff 中描述的 "carryover" 需要 pre-spec grep + read actual code 验证，hypothesis 可能过/低估真实问题。

### 2. Per-item validation strictness trade-off

Brainstorming 时 debate: strict all 3 fields vs permissive only name。最终 permissive + silent missing。

**Trade-off**:
- Permissive: 用户手填门槛低, LLM 拿到 name 也能推 description
- Strict: 质量保证, 但"先占位后补" workflow 被阻断

本 phase 选 permissive。Future i2i phase 可能需要 strict (key_visual 必填)。

### 3. Full closure vs add-only

"Add-only" 选项保留 v1 函数 + 加新 loader。会留下 2 个 loader (v1 + v2) 并存，API surface 膨胀。

"Full closure" 选项删 v1 函数 + dead path 字符串 + docstring 段落。一锤定音。

本 phase 选 Full closure — 验证 v1 path 真 0 hits 后，back-compat 价值 = 0，留 v1 = 技术债。

### 4. .venv/bin/python over miniconda python for editable packages

Pre-flight 时 conda python 报 `ModuleNotFoundError: No module named 'lingwen_illustrations'`。`.venv/bin/python` (uv-managed, 已装 editable) 正确解析。

**Future**: LingWen 后端测试默认 `.venv/bin/python`，conda 是 fallback。

### 5. pytest multi-path rootdir conflict (Phase 89 lesson)

C5 后跑 `pytest packages/X/ tests/Y.py` with single rootdir 报 8 collection errors（rootdir conflict）。分开跑两个 rootdir 各自 PASS。

**Future**: LingWen 后端测试 commands 保持 `--rootdir=<pkg>` 单包模式，多包用 separate commands (Phase 56b2 / 89 lessons)。

---

## §7. Validation gates summary

| Gate | Result |
|------|--------|
| pytest lingwen-illustrations | 72/72 PASS |
| pytest illustrations_api | 8/8 PASS (unchanged) |
| pytest phase90 guards | 17/17 PASS (15 baseline + G8 + G9) |
| ruff check | clean |
| 9-pattern audit | 0 `infra.illustrations.*` refs (G5 still GREEN) |
| I087 invariant | unchanged |

**ALL GREEN** — Phase 91 P2-ILLUSTRATIONS-BIBLE-CANONICAL READY。

---

> See also: spec `2026-09-16-phase-91-illustrations-bible-canonical-design.md` + plan `2026-09-16-phase-91-illustrations-bible-canonical.md` + `tests/test_phase90_illustrations.py` (G8+G9) + `.lingwen/architecture.yml` (I087 unchanged)

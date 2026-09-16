# Phase 91 — P2-ILLUSTRATIONS-BIBLE-CANONICAL 设计

> **状态**: 待审（2026-09-16 brainstorming 完成）
> **范围**: 替换 v1 dead path `<root>/config/characters.json` → 新 rich bible JSON `<root>/config/illustrations/characters.json`
> **不属于本 phase**: 角色头像 / reference image / i2i / provider adapters / LRU archive / notification center / CLI scaffolding / frontend bible editor / bible status API（均为独立 v2 子项目）
> **依赖基线**: v55.0 (Phase 90 REQ-002 v1 闭环) + I087 (lingwen-illustrations canonical 包)

## 0. 决策摘要

| 维度 | 决策 |
|------|------|
| 触发源 | BACKLOG P2-ILLUSTRATIONS-BIBLE-CANONICAL (Phase 90 §4 deviation 2 闭环) |
| 数据源 | 新 rich bible JSON，**单一后端**（无 dual backend / 无 env var 切换） |
| 文件位置 | `<project_root>/config/illustrations/characters.json` |
| Schema | `list[{name: str, role: str, description: str}]`（最小 schema，forward-compat 容忍 extra fields） |
| Per-item 验证 | Permissive：仅 `name` 必填（非空 str），`role`/`description` 缺省为 `''` |
| Missing 文件 | `return []` + `logger.info()`（同 v1 沉默哲学） |
| Malformed 文件 | `raise LoadError`（同 v1） |
| Loader 位置 | `packages/lingwen-illustrations/src/lingwen_illustrations/bible_loader.py`（包内 submodule，不新建 lingwen-* 包） |
| Pipeline 集成 | `pipeline._load_character_bible` 删除 → `bible_loader.load_character_bible` 替换 |
| V1 dead path 处置 | Full closure：删 v1 函数 + 删 `<root>/config/characters.json` 字符串引用 + 删 docstring 段落 |
| I087 invariant | 不变（loader 是 lingwen-illustrations 内部细节，invariant 边界未动） |
| 范围估算 | ~280 LOC（1 module 50 + 1 test file 150 + 2 regression guards 30 + pipeline 改动 30 + docs 20） |
| Commit 模式 | 8 atomic (C0 spec / C0.5 self-review / C1 plan / C2 feat / C3 fixup / C4 refactor / C5 test / C6 docs) — per Phase 90 pattern, direct master |

---

## 1. 背景与动机

### 1.1 Phase 90 v1 现状

Phase 90 handoff §4 deviation 2 明确指出：
> `pipeline.py:extract_scene` 直接读 `<root>/config/characters.json` 而非用 I073 `load_agency_target_characters`
> **API mismatch**: `load_agency_target_characters` returns `list[str]` (names only); `extract_scene` needs `list[dict]` (with descriptions / key_visual)

### 1.2 实测发现（v1 实际更糟）

通过 grep + 读 `lingwen-project-characters` 实现 + 读 `prompt_builder.build_extraction_prompt` 真实代码：

1. **v1 path 永远空**：`pipeline._load_character_bible` 读 `<root>/config/characters.json`，全工作区 **0 个项目** 有此文件（grep 验证）。LLM prompt 永远是 `"(无角色档案)"`。
2. **I073 真实能力有限**：`load_agency_target_characters` 返回 `list[str]`，**不返回** description/key_visual。`lingwen_project_characters.characters` 内部用 `_names_from_profiles` 从 `character_profiles.json` 提取 name 字段，跳过 description。
3. **Canonical schema 不含 description**：`03_内容仓库/角色设定/character_profiles.json` schema 为 `{characters: [{name, role, ...}]}`，无 `description` / `key_visual` 字段。
4. **Prompt 实际只用 name + description**：`build_extraction_prompt` 仅取 `c.get('name', '?')` 和 `c.get('description', '')`。`key_visual` 在 LLM 输出模板中 mention，但**输入端不传**。

### 1.3 P2-ILLUSTRATIONS-BIBLE-CANONICAL 原始设计（已修订）

Phase 90 handoff 原文：
> **修**: 新 `bible_loader.py` adapter, direct/canonical 双 backend, env var 切换。I073 invariant 不动 (其他 consumer 依赖)。

**本次 brainstorming 修订**：
- ❌ "双 backend + env var 切换" 废除（v1 path 全工作区 0 hits，无 back-compat 价值）
- ❌ "canonical backend 读 character_profiles.json" 废除（无 description 字段，强制耦合）
- ✅ "新 rich bible JSON + permissive schema"（最小有效解，I073 不变）
- ✅ "Full closure"（删 v1 函数 + 删 dead path 字符串 + 删 docstring 段落）

### 1.4 关键解耦决策

新 bible 与 `character_profiles.json` / I073 / `ProjectPaths` **零耦合**：
- 不读 `character_profiles.json`（避免破坏 I073 invariant + 8 consumers）
- 不调用 I073 任何函数（避免 list[str] → list[dict] 类型不匹配）
- 不引入 `ProjectPaths`（v1 注释已解释：illustration 路径不匹配 canonical layout）
- 不强制 name 出现在 character_profiles.json（用户可独立管理 bible）

理由：illustration 是独立能力域，character data 唯一负责方是 bible 本身。

---

## 2. 架构与组件

### 2.1 新增 module：`bible_loader.py`

**位置**：`packages/lingwen-illustrations/src/lingwen_illustrations/bible_loader.py`

**Public surface**：
```python
def load_character_bible(project_root: Path) -> list[dict[str, str]]:
    """Load character bible from <project_root>/config/illustrations/characters.json.

    Schema (permissive):
        list of {name: str, role: str, description: str}
        - name: required (non-empty str) — used as key in extraction prompt
        - role: optional (defaults to '') — cross-ref hint
        - description: optional (defaults to '') — primary visual cue for LLM
        - extra fields: silently ignored (forward-compat for future schema extensions)

    Returns:
        Validated list of {name, role, description} dicts.
        Empty list if file is missing.

    Raises:
        LoadError: JSON parse error, non-list root, or item with
        missing/empty/non-str name field.

    Examples:
        >>> bible = load_character_bible(Path("/proj"))
        >>> bible
        [{'name': '林夜', 'role': '主角', 'description': '身穿黑色风衣的青年剑客'}]
        >>> # missing file
        >>> load_character_bible(Path("/empty-proj"))
        []
    """
```

**Error handling table**：

| 情况 | 行为 | 理由 |
|------|------|------|
| File missing | `return []` + `logger.info("character bible not found at <path>")` | v1 同哲学，零手填门槛 |
| File 是 `[]` | `return []` | 等价于 missing |
| JSON parse error | `raise LoadError(f"failed to load character bible <path>: <e>")` | v1 一致，operator 必须修 |
| Root 非 list | `raise LoadError(f"character bible must be a list, got <type>")` | v1 一致 |
| Item 缺 name | `raise LoadError(f"item <i> missing required 'name' field")` | 锚点字段，唯一必填 |
| Item name 是 `""` | `raise LoadError(f"item <i> 'name' is empty")` | 与缺 name 等价 |
| Item name 非 str | `raise LoadError(f"item <i> 'name' must be str, got <type>")` | 类型保护 |
| Item 缺 role | `default to ''` | permissive，silent |
| Item 缺 description | `default to ''` | permissive，silent |
| Item 有 extra fields | `ignore` (forward-compat) | 允许未来 schema 扩展不破坏 v2 |
| OSError (e.g. perm denied) | `raise LoadError` wrapped | 与 v1 一致 |

### 2.2 修改 module：`pipeline.py`

**删除**：
- `pipeline._load_character_bible` 函数（行 54-70，约 17 LOC）
- module docstring 第 12-20 行「Why direct paths instead of ProjectPaths」段落

**新增**：
- `from lingwen_illustrations.bible_loader import load_character_bible`
- `character_bible = load_character_bible(project_root)` 替换 `_load_character_bible` 调用

**修改 docstring**：
```python
"""Pipeline orchestrator: load -> extract -> compose -> generate -> store.

Single entry point for the 4-stage illustration generation pipeline.
Each stage raises a stage-specific exception on failure; the orchestrator
propagates without wrapping.

Layout assumptions (tested + canonical for Phase 90/91):
    <project_root>/chapters/<NNN>.md                       — chapter markdown
    <project_root>/config/illustrations/characters.json    — character bible (Phase 91)
    <project_root>/assets/...                              — written by storage

Character bible (Phase 91, P2-ILLUSTRATIONS-BIBLE-CANONICAL):
    Loaded via bible_loader.load_character_bible. Permissive schema:
    list[{name, role, description}]. Missing file silently returns []
    (LLM proceeds with empty prompt). Malformed file raises LoadError.

    Why not ProjectPaths: ProjectPaths enforces canonical layout
    (03_内容仓库/角色设定/character_profiles.json) which doesn't carry
    visual descriptions. Bible is illustration-specific; independent
    of character_profiles.json (no cross-ref).
"""
```

### 2.3 新增 test file：`test_bible_loader.py`

**位置**：`packages/lingwen-illustrations/tests/test_bible_loader.py`

**Test cases**（13 tests）：

| # | Test | Expected |
|---|------|----------|
| T1 | file missing | `return []` + `caplog` captures INFO log |
| T2 | file 是 `[]` | `return []` |
| T3 | file 有 1 valid character | `return [{name, role, description}]` |
| T4 | file 有 3 valid characters | `return all 3` |
| T5 | file malformed JSON | `raise LoadError` |
| T6 | file root 是 `{}`（非 list） | `raise LoadError` |
| T7 | item 缺 name field | `raise LoadError` |
| T8 | item name 是 `""` | `raise LoadError` |
| T9 | item name 是 `123` (int) | `raise LoadError` |
| T10 | item 缺 role | `role == ''`（default） |
| T11 | item 缺 description | `description == ''`（default） |
| T12 | item 有 extra field `image_url` | ignore，仍 valid |
| T13 | OSError (perm denied) | `raise LoadError` wrapped |

### 2.4 回归守门：`tests/test_phase90_illustrations.py` 扩展

**v1 test impact 评估**：
- `test_pipeline.py` 是否测 `_load_character_bible`？需 C0.5 verify。**若存在**，需同步迁移到 `test_bible_loader.py` 或删除。
- `test_prompt_builder.py` 仅传 `character_bible` 参数（已用 `list[dict]` mock），不受影响。
- `test_storage.py` / `test_image_generator.py` / `test_metadata.py` / `test_style_templates.py` / `test_exceptions.py` 与 bible 无关，不受影响。

**新增 G8 + G9**（parametrized 形式）：

```python
# G8: v1 dead path 不再被引用 (strip docstring per N.14 lesson v21)
def test_v1_path_not_referenced():
    """v1 <root>/config/characters.json must be gone after Phase 91.

    Strip docstrings (which legitimately mention the path in narrative
    before deletion) before regex search — N.14 lesson 1 v21.
    """
    illus_src = Path("packages/lingwen-illustrations/src")
    violations = []
    for py_file in illus_src.rglob("*.py"):
        if py_file.name.startswith("test_"):
            continue
        text = py_file.read_text(encoding="utf-8")
        # strip module/class/function docstrings (N.14 v21)
        stripped = re.sub(r'"""[\s\S]*?"""', "", text)
        stripped = re.sub(r"'''[\s\S]*?'''", "", stripped)
        if re.search(r"config/characters\.json", stripped):
            violations.append(str(py_file.relative_to(illus_src.parent.parent)))
    assert not violations, f"v1 path still referenced: {violations}"


# G9: bible_loader 存在 + load_character_bible 是 public
@pytest.mark.parametrize("symbol", [
    "bible_loader.load_character_bible",
])
def test_bible_loader_public(symbol):
    """bible_loader submodule + load_character_bible must be public."""
    import lingwen_illustrations.bible_loader as bl
    assert hasattr(bl, "load_character_bible")
    assert "load_character_bible" in bl.__all__
```

**G8 关键**: 只扫 `src/` 排除 test 文件，**strip docstring 后再 regex search**（N.14 lesson 1 v21 — pipeline.py module docstring 第 9 行合法 mention v1 path narrative，会 false-positive）。

### 2.5 I087 invariant 影响

**I087 不变**：
```yaml
- id: I087
  rule: "packages/lingwen-illustrations/ 是图片生成（封面 + 章节插图）的唯一实包；infra.illustrations.* 路径非法"
  severity: error
  scope: "all future REQ-002 multimodal code"
```

理由：bible_loader 是 lingwen-illustrations 内部 submodule，invariant 边界未动。**无新 invariant 需要**。

---

## 3. 数据流

### 3.1 Pipeline 完整流（不变）

```
[WriteWorkspacePage.vue] click "生成插图"
  ↓
[POST /api/illustrations/generate]
  ↓
[studio_api: pipeline.generate_illustration()]
  ↓
  Stage 1a: _load_chapter_text(project_root, type, chapter_num)  ← unchanged
  Stage 1b: bible_loader.load_character_bible(project_root)      ← CHANGED (Phase 91)
  Stage 2:  extract_scene(chapter_text, character_bible)         ← unchanged
  Stage 3:  compose_prompt(preset, scene_json, custom_prompt)    ← unchanged
  Stage 4:  image_generator.generate(prompt, api_key, api_host)  ← unchanged
  Stage 5:  storage.save_asset(project_root, image_bytes, meta)  ← unchanged
  ↓
[return IllustrationMetadata]
```

### 3.2 Bible 加载详细流

```
bible_loader.load_character_bible(project_root)
  │
  ├─ bible_path = project_root / "config" / "illustrations" / "characters.json"
  │
  ├─ if not bible_path.exists():
  │    logger.info("character bible not found at <path>")
  │    return []
  │
  ├─ try:
  │    raw = bible_path.read_text(encoding="utf-8")
  │    data = json.loads(raw)
  │  except (OSError, json.JSONDecodeError) as e:
  │    raise LoadError(f"failed to load character bible {bible_path}: {e}") from e
  │
  ├─ if not isinstance(data, list):
  │    raise LoadError(f"character bible must be a list, got {type(data).__name__}")
  │
  ├─ result = []
  │  for i, item in enumerate(data):
  │    if not isinstance(item, dict):
  │      raise LoadError(f"item {i} must be a dict, got {type(item).__name__}")
  │    if "name" not in item:
  │      raise LoadError(f"item {i} missing required 'name' field")
  │    name = item["name"]
  │    if not isinstance(name, str):
  │      raise LoadError(f"item {i} 'name' must be str, got {type(name).__name__}")
  │    if not name:  # empty string
  │      raise LoadError(f"item {i} 'name' is empty")
  │    role = item.get("role", "")
  │    description = item.get("description", "")
  │    # type check role/description if present (defensive)
  │    if not isinstance(role, str):
  │      raise LoadError(f"item {i} 'role' must be str, got {type(role).__name__}")
  │    if not isinstance(description, str):
  │      raise LoadError(f"item {i} 'description' must be str, got {type(description).__name__}")
  │    result.append({
  │      "name": name,
  │      "role": role,
  │      "description": description,
  │    })
  │
  └─ return result
```

### 3.3 Error propagation 链

```
bible_loader.LoadError  ←  pipeline  ←  studio_api  ←  frontend
   (new module)            (unchanged)   (unchanged)   (unchanged)
```

`LoadError` 已在 `lingwen_illustrations.exceptions` 定义（Phase 90），bible_loader 复用同 exception class。`pipeline.generate_illustration` docstring 已声明 `LoadError` 是可能异常（"Project / chapter / character bible missing or malformed"），无需新增。

---

## 4. 测试策略

### 4.1 单元测试（test_bible_loader.py）

**Framework**: pytest（与 Phase 90 一致）

**Fixture**:
```python
@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Empty project root, no config/illustrations/ directory."""
    return tmp_path


@pytest.fixture
def bible_dir(tmp_project: Path) -> Path:
    """Pre-created config/illustrations/ directory."""
    d = tmp_project / "config" / "illustrations"
    d.mkdir(parents=True)
    return d
```

**Parametrized malformed tests** (pytest.mark.parametrize for compactness):
```python
@pytest.mark.parametrize("bad_data,error_match", [
    ('{not json}', "JSON"),
    ('{"characters": {}}', "must be a list"),
    ('[{"role": "x"}]', "missing required 'name'"),
    ('[{"name": ""}]', "'name' is empty"),
    ('[{"name": 123}]', "'name' must be str"),
    ('[{"name": "x", "role": 123}]', "'role' must be str"),
    ('[{"name": "x", "description": []}]', "'description' must be str"),
    ('["not a dict"]', "must be a dict"),
])
def test_malformed_raises(bible_dir, bad_data, error_match):
    (bible_dir / "characters.json").write_text(bad_data)
    with pytest.raises(LoadError, match=error_match):
        load_character_bible(bible_dir.parent.parent)
```

### 4.2 Pipeline 集成测试

**T13**: pipeline 完整跑（end-to-end with real bible）
- 准备 tmp project with bible + chapter
- 跑 `pipeline.generate_illustration(...)` 用 mock LLM service + mock image generator
- 验证返回 metadata.scene_json 反映 bible 内容
- **不测** API 层（Phase 90 test_illustrations_api.py 已有 8 tests，已覆盖）

### 4.3 回归守门

| Guard | 目的 | 实现 |
|-------|------|------|
| G8 | v1 path 不被源码引用 | grep `config/characters.json` in src/，exclude test files |
| G9 | bible_loader public | import + hasattr + `__all__` 检查 |
| Phase 90 G1-G7 | 全部保留 | 既有 7 guards 不变 |

### 4.4 5 quality gates

| Gate | Command | 期望 |
|------|---------|------|
| pytest lingwen-illustrations | `pytest packages/lingwen-illustrations/tests/ --rootdir=packages/lingwen-illustrations` | 53 + 13 + T13 = **67 passed** |
| pytest illustrations_api | `pytest apps/studio_api/tests/test_illustrations_api.py` | 8 passed (unchanged) |
| pytest phase90 guards | `pytest tests/test_phase90_illustrations.py` | 15 + G8 + G9 = **17+ passed** |
| ruff | `ruff check packages/lingwen-illustrations/ apps/studio_api/` | clean |
| 9-pattern audit | `grep -rn "infra\.illustrations\." packages/ apps/` | 0 hits (Phase 90 G5 仍 GREEN) |

---

## 5. Out of scope (显式不做)

| 项目 | 理由 | 后续 |
|------|------|------|
| CLI `lingwen-illustrations init-bible` | Phase 91 范围最小化，手填 JSON 已足够 | Phase 92+ candidate |
| Frontend bible editor (ProjectSettingsIllustration section) | UI 改动需独立 brainstorm | Phase 92+ |
| `GET /api/illustrations/bible/status` endpoint | missing UX 决策已选 "silent + log" | Phase 92+ |
| Reference image path / i2i schema 字段 | i2i 是独立 v2 子项目 | Phase 93+ (i2i) |
| Cross-validation with character_profiles.json | "零耦合" 决策 | N/A |
| `LINGWEN_ILLUSTRATIONS_BIBLE_BACKEND` env var | "Full closure" 决策，v1 path 物理不可访问 | N/A |
| P2-EXTRACT-ENUM (TaskType.STRUCTURED_EXTRACTION) | 独立 sub-project | Phase 92+ |
| 角色/地点头像 | REQ-002 v3 候选 | Future |
| Image provider adapters (DALL-E / Replicate / Stability) | 独立 v2 子项目 | Phase 94+ |
| LRU archive (per-project storage cap) | 独立 v2 子项目 | Phase 95+ |
| Notification center | 独立 v2 子项目 | Phase 96+ |

---

## 6. Risks & lessons

### 6.1 风险

| Risk | Mitigation |
|------|------------|
| 用户已有 v1 `<root>/config/characters.json` 数据丢失 | grep 验证：全工作区 0 hits。Full closure 决策已接受此风险（BACKLOG 显式说明） |
| 引入新 schema 后 prompt 行为变化 | bible 现永远空 → 启用后 LLM 拿到真实 character context，prompt 语义提升（正向变化） |
| bible_loader 与 lingwen-project-characters (I073) 边界混淆 | 显式 docstring + 回归 guard G8 防止 v1 path 回潮 |
| `load_character_bible` 名字与 I073 `load_project_character_names` 相似 | docstring 明确 "illustration-specific, independent of I073" |

### 6.2 Lessons applied

- **N.14 lesson 1 v18 (Phase 53c)**: prior-phase guard 引用 deleted path 需 strip docstring — G8 排除 src/ 下的 docstring narrative（handoff/BACKLOG 仍合法 mention v1 path）
- **Phase 57b lesson**: 测试文件名 `test_*.py` 排除，gating 只看 prod code
- **Phase 77 lesson (architecture invariant)**: parsed-value check (PyYAML) — I087 不变，无需重新验证
- **Phase 78 lesson (NON-INVASIVE++)**: v1 path 物理删除而非 soft-deprecate
- **Phase 90 lesson 1 (N.14 v24)**: Plan 不能假定 API shape — `load_character_bible` 通过 `grep -rn "def load_agency_target_characters" packages/lingwen-project-characters/` 验证过 I073 真实签名

### 6.3 Open questions（已决议）

- ✅ 视觉数据来源 → 新 rich bible JSON
- ✅ schema 范围 → `[{name, role, description}]` 最小
- ✅ per-item 严格度 → permissive (only name required)
- ✅ missing 行为 → silent `[]` + INFO log
- ✅ deliverable 边界 → Full closure (删 v1 函数 + dead path 字符串 + docstring 段落)
- ✅ loader 位置 → `bible_loader.py` in `lingwen-illustrations` (not new package)

---

## 7. Acceptance criteria

✅ **Functional**:
- `bible_loader.load_character_bible(project_root)` 工作如 §2.1 契约
- `pipeline.generate_illustration(...)` 调用新 loader，行为除 bible 数据外与 Phase 90 一致
- 全 13 unit tests + 1 integration test PASS

✅ **Regression**:
- 既有 7 phase90 guards (G1-G7) 仍 GREEN
- 新增 G8 (v1 path gone) + G9 (bible_loader public) GREEN
- 9-pattern audit 仍 0 hits
- 53 既有 lingwen-illustrations tests 仍 PASS

✅ **Code quality**:
- ruff clean
- tsc 0 new errors (本 phase 不动 frontend)
- knip clean (新 bible_loader 是 public symbol,被 pipeline 引用)

✅ **Docs**:
- `collaboration/BACKLOG.md` 删 P2-ILLUSTRATIONS-BIBLE-CANONICAL row（已闭环）
- `pipeline.py` docstring 重写（移除 "Why direct paths" 段落）
- 新 handoff: `docs/superpowers/handoffs/2026-09-16-phase-91-illustrations-bible-canonical-handoff.md`
- CLAUDE.md v55.0 → v55.1
- CURRENT_STATUS.md 状态更新

---

## 8. Commit plan (5-6 atomic, direct master per 2026-09-15 workflow)

| # | Type | Subject | 估算 LOC |
|---|------|---------|----------|
| 1 | docs | phase 91 spec | +280 |
| 2 | docs | spec self-review (placeholder/consistency/scope/ambiguity) | (inline) |
| 3 | docs | implementation plan (TDD task list) | +200 |
| 4 | feat | bible_loader.py + test_bible_loader.py (TDD: tests RED first, then GREEN) | +200 |
| 5 | fix | review fixup (e.g. type-check role/description if present) | +20 |
| 6 | refactor | pipeline.py: delete _load_character_bible, integrate bible_loader, rewrite docstring | -15 +15 |
| 7 | test | G8 + G9 regression guards | +30 |
| 8 | docs | BACKLOG close + handoff + CLAUDE.md v55.1 + CURRENT_STATUS | +100 |

**Total**: 8 commits, ~830 LOC delta (含 docs)，prod code 净 +250 LOC。

---

## 9. References

- **Phase 90 handoff**: `docs/superpowers/handoffs/2026-09-15-phase-90-illustrations-handoff.md` §4 deviation 2
- **Phase 90 spec**: `docs/superpowers/specs/2026-09-15-phase-90-illustrations-design.md`
- **Phase 90 plan**: `docs/superpowers/plans/2026-09-15-phase-90-illustrations.md`
- **I073 invariant**: `.lingwen/architecture.yml` line 161 (lingwen-project-characters)
- **I087 invariant**: `.lingwen/architecture.yml` line 220 (lingwen-illustrations)
- **BACKLOG row**: `collaboration/BACKLOG.md` P2 section
- **I073 source**: `packages/lingwen-project-characters/src/lingwen_project_characters/characters.py`
- **v1 dead path source**: `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py:54-70`
- **prompt_builder (consumer, unchanged)**: `packages/lingwen-illustrations/src/lingwen_illustrations/prompt_builder.py:25-54`

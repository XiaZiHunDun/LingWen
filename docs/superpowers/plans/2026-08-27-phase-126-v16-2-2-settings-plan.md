# Phase 126 v16.2.2 — Settings Subdomain 拆分 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) per project convention.

**Goal:** Migrate `infra/creator_settings_docs.py` + `infra/creator_settings_history.py` + `infra/creator_merge_preferences.py` (1842 lines total) to `packages/lingwen-creator/src/lingwen_creator/settings/{docs,history,merge_preferences}.py`, add ~20 DTOs + typed wrapper + composable refactor + 32 routes imports migration + shim underscore re-exports + cross-subdomain lazy import cleanup.

**Architecture:** Strangler Fig — 1-line shim re-export keeps 36 existing infra consumers working. New package path is source of truth. Intra-package imports follow plan §12.2 (volume already migrated, shared already migrated, no cross-subdomain cycle). Typed wrapper follows v16.1 T4 reference (world.ts/workspace.ts/quality.ts) + v16.2.1 volume.ts style (no zod, no `/api/` prefix).

**Tech Stack:** Python 3.12+ (FastAPI + Pydantic v2) backend / Vue 3 + TypeScript strict + Pinia frontend / pnpm + uv workspaces / pytest + vitest + vue-tsc + ruff + knip / zod CI drift gate.

**Predecessor phase:** v16.2.1 (`5733505b`) volume subdomain closed. v16.2.0 (`5bc35f1b`) shared closed. v16.1 (`e6927159`) lingwen-shared closed.

**Design spec:** `docs/superpowers/specs/2026-08-27-phase-126-v16-2-2-settings-design.md` (450 lines, approved at `f9e74a38`).

**Carryover to future phases:** `infra/creator_export_*.py` (4 imports) → v16.2.5 / `infra/creator_memory_assets.py` (1 import) → v16.2.6 / `infra/creator_mode.py` → shared/mode.py → v16.2.6 / shared/check.py spec violation → v16.2.6 / shim cleanup → v16.2.7 / typed wrappers (world/workspace/quality) /api/ fix → v16.2.7.

---

## §0. Pre-flight Checks (Task 0 — must pass before Task 1)

**Files:** None (read-only)

**Pre-conditions:**
- v16.2.1 closed at HEAD (`5733505b`)
- `packages/lingwen-creator/src/lingwen_creator/volume/` exists with 6 files
- `packages/lingwen-creator/src/lingwen_creator/shared/` exists with 2 files
- `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` has Volume DTOs

**Approach:**

- [ ] **Step 1: Verify v16.2.1 closed**
  ```bash
  git log --oneline -1
  # Expected: 5733505b ... or later (latest commit on master)
  git log --oneline origin/master..HEAD | wc -l
  # Expected: ≥ 39 (v16.2.0 + v16.2.1 closed commits + spec commits)
  ```

- [ ] **Step 2: Verify volume + shared subdomains exist**
  ```bash
  ls packages/lingwen-creator/src/lingwen_creator/volume/
  # Expected: __init__.py plan.py plan_share.py pulse.py summary.py templates.py template_approvals.py
  ls packages/lingwen-creator/src/lingwen_creator/shared/
  # Expected: __init__.py revision.py check.py
  ```

- [ ] **Step 3: Verify backend tests baseline passes**
  ```bash
  uv run python -m pytest packages/lingwen-creator/tests/test_volume.py -v
  # Expected: 14 passed
  uv run python -m pytest tests/infra/test_creator_settings_*.py -q
  # Expected: all 12 test files passing
  ```

- [ ] **Step 4: Verify frontend baseline passes**
  ```bash
  cd apps/dashboard && pnpm vitest run --reporter=dot
  # Expected: ≥ 1781 passing, 0 failing
  pnpm exec vue-tsc --noEmit
  # Expected: 0 errors
  pnpm exec knip
  # Expected: 0 errors
  ```

- [ ] **Step 5: Verify spec violation carryover is intact**
  ```bash
  grep -n "infra.creator_mode" packages/lingwen-creator/src/lingwen_creator/shared/check.py
  # Expected: ≥ 1 match (spec violation still pending v16.2.6 fix — DO NOT touch in v16.2.2)
  ```

**Verification:** All 5 steps PASS. If any FAIL, STOP and report to user.

**Subagent:** Self (no subagent dispatch for pre-flight).

---

## §1. Task 1 — T1a: Migrate settings/docs.py + shim

**Files:**
- Create: `packages/lingwen-creator/src/lingwen_creator/settings/docs.py` (verbatim copy of `infra/creator_settings_docs.py` with 3 import adjustments)
- Modify: `infra/creator_settings_docs.py` → 1-line shim

**Pre-conditions:** Task 0 passed.

**Approach:**

- [ ] **Step 1: Create settings package directory**
  ```bash
  mkdir -p packages/lingwen-creator/src/lingwen_creator/settings/tests
  touch packages/lingwen-creator/src/lingwen_creator/settings/__init__.py
  ```

- [ ] **Step 2: Read source file fully**
  ```bash
  cat infra/creator_settings_docs.py
  # Read entire 351-line file. Identify the 3 imports to adjust (see §2 spec for details):
  # - from infra.creator_revision import CreatorDocConflictError, content_revision
  #   → from lingwen_creator.shared.revision import CreatorDocConflictError, content_revision
  # - from infra.creator_settings_history import append_settings_snapshot
  #   → from lingwen_creator.settings.history import append_settings_snapshot
  # - from infra.creator_volume_plan import global_outline_path
  #   → from lingwen_creator.volume.plan import global_outline_path
  ```

- [ ] **Step 3: Write failing test (RED)**
  ```python
  # packages/lingwen-creator/tests/test_settings.py
  def test_settings_docs_module_exists():
      """settings/docs.py must exist and expose key functions after migration."""
      from lingwen_creator.settings.docs import (
          creator_settings_docs_payload,
          save_creator_settings_docs,
          preview_settings_docs_diff,
          preview_settings_three_way,
          preview_settings_merge_strategy,
          assert_settings_revisions,
          resolve_merged_settings,
          text_diff_summary,
      )
      # If import fails, this test fails (RED)
  ```

- [ ] **Step 4: Run test to verify it fails**
  ```bash
  uv run python -m pytest packages/lingwen-creator/tests/test_settings.py::test_settings_docs_module_exists -v
  # Expected: FAIL with "ModuleNotFoundError: No module named 'lingwen_creator.settings.docs'"
  ```

- [ ] **Step 5: Copy infra/creator_settings_docs.py → settings/docs.py (verbatim + 3 import adjustments)**
  ```bash
  cp infra/creator_settings_docs.py packages/lingwen-creator/src/lingwen_creator/settings/docs.py
  ```
  Then edit the 3 import lines per Step 2 mapping (use Edit tool with exact line match).

- [ ] **Step 6: Run test to verify it passes (GREEN)**
  ```bash
  uv run python -m pytest packages/lingwen-creator/tests/test_settings.py::test_settings_docs_module_exists -v
  # Expected: PASS
  ```

- [ ] **Step 7: Verify existing infra consumer tests still pass**
  ```bash
  uv run python -m pytest tests/infra/test_creator_settings_docs.py -v
  # Expected: all passing (infra file still original)
  ```

- [ ] **Step 8: Convert infra/creator_settings_docs.py to 1-line shim**
  ```python
  # infra/creator_settings_docs.py (REPLACE entire file)
  from lingwen_creator.settings.docs import *  # noqa: F403
  ```

- [ ] **Step 9: Verify shim backwards compat**
  ```bash
  /home/ailearn/miniconda3/bin/python -c "from infra.creator_settings_docs import creator_settings_docs_payload, MERGE_SOURCES"
  # Expected: OK (shim works)
  uv run python -c "from infra.creator_settings_docs import creator_settings_docs_payload, MERGE_SOURCES"
  # Expected: OK
  uv run python -m pytest tests/infra/test_creator_settings_docs.py -v
  # Expected: all passing
  ```

- [ ] **Step 10: Run lint**
  ```bash
  ruff check packages/lingwen-creator/src/lingwen_creator/settings/docs.py infra/creator_settings_docs.py packages/lingwen-creator/tests/test_settings.py
  # Expected: All checks passed (F403 in shim is no-op via noqa)
  ```

- [ ] **Step 11: Commit**
  ```bash
  git add packages/lingwen-creator/src/lingwen_creator/settings/__init__.py \
          packages/lingwen-creator/src/lingwen_creator/settings/docs.py \
          packages/lingwen-creator/tests/test_settings.py \
          infra/creator_settings_docs.py
  git commit -m "feat(creator): T1a settings/docs.py migration + shim
  
  verbatim copy of infra/creator_settings_docs.py (351 lines) to
  packages/lingwen-creator/src/lingwen_creator/settings/docs.py
  with 3 intra-package import adjustments (shared.revision + settings.history + volume.plan per spec §2.1).
  
  infra/creator_settings_docs.py 变 1-line shim re-export.
  tests/infra/test_creator_settings_docs.py 经 shim 继续 pass (zero consumer change)."
  ```

**Verification:** Test passes + shim works + lint clean + 1 commit.

**Subagent dispatches (per project convention):**
1. **Implementer** (general-purpose or code-architect): execute Steps 1-11
2. **Spec reviewer** (general-purpose): verify against spec §1.1 + §2.1 — file exists, imports adjusted, shim pattern correct
3. **Code quality reviewer** (python-reviewer): check verbatim copy preserves all logic, imports minimal changes, no unintended side effects

---

## §2. Task 2 — T1b: Migrate settings/history.py + shim

**Files:**
- Create: `packages/lingwen-creator/src/lingwen_creator/settings/history.py`
- Modify: `infra/creator_settings_history.py` → shim
- Modify: `packages/lingwen-creator/tests/test_settings.py` (add 1 test)

**Pre-conditions:** Task 1 committed.

**Approach:**

- [ ] **Step 1: Extend failing test (RED)**
  ```python
  # Add to packages/lingwen-creator/tests/test_settings.py
  def test_settings_history_module_exists():
      from lingwen_creator.settings.history import (
          settings_history_payload,
          append_settings_snapshot,
          restore_settings_snapshot,
      )
  ```

- [ ] **Step 2: Run test to verify it fails**
  ```bash
  uv run python -m pytest packages/lingwen-creator/tests/test_settings.py::test_settings_history_module_exists -v
  # Expected: FAIL (settings/history.py not yet created)
  ```

- [ ] **Step 3: Read source + identify 1 import to adjust**
  ```bash
  cat infra/creator_settings_history.py | head -30
  # Find: from infra.creator_volume_plan import global_outline_path
  # Map to: from lingwen_creator.volume.plan import global_outline_path
  ```

- [ ] **Step 4: Copy + adjust 1 import**
  ```bash
  cp infra/creator_settings_history.py packages/lingwen-creator/src/lingwen_creator/settings/history.py
  # Edit the 1 import line (use Edit tool with exact match)
  ```

- [ ] **Step 5: Run tests (GREEN)**
  ```bash
  uv run python -m pytest packages/lingwen-creator/tests/test_settings.py -v
  # Expected: 2 passed (docs + history module tests)
  uv run python -m pytest tests/infra/test_creator_settings_history.py -v
  # Expected: all passing (infra file still original)
  ```

- [ ] **Step 6: Convert infra/creator_settings_history.py to shim**
  ```python
  from lingwen_creator.settings.history import *  # noqa: F403
  ```

- [ ] **Step 7: Verify shim + commit**
  ```bash
  /home/ailearn/miniconda3/bin/python -c "from infra.creator_settings_history import settings_history_payload, append_settings_snapshot"
  ruff check packages/lingwen-creator/src/lingwen_creator/settings/history.py infra/creator_settings_history.py
  git add packages/lingwen-creator/src/lingwen_creator/settings/history.py \
          packages/lingwen-creator/tests/test_settings.py \
          infra/creator_settings_history.py
  git commit -m "feat(creator): T1b settings/history.py migration + shim
  
  verbatim copy of infra/creator_settings_history.py (136 lines) to
  packages/lingwen-creator/src/lingwen_creator/settings/history.py
  with 1 intra-package import adjustment (volume.plan per spec §2.2).
  
  infra/creator_settings_history.py 变 shim."
  ```

**Verification:** 2 module tests pass + shim works + lint clean + 1 commit.

**Subagent dispatches:** Same pattern as Task 1.

---

## §3. Task 3 — T1c: Migrate settings/merge_preferences.py + shim (largest file)

**Files:**
- Create: `packages/lingwen-creator/src/lingwen_creator/settings/merge_preferences.py` (1355 lines, ~50 functions)
- Modify: `infra/creator_merge_preferences.py` → shim
- Modify: `packages/lingwen-creator/tests/test_settings.py` (add 1 test)

**Pre-conditions:** Task 2 committed.

**Approach:**

- [ ] **Step 1: Extend failing test (RED)**
  ```python
  # Add to packages/lingwen-creator/tests/test_settings.py
  def test_settings_merge_preferences_module_exists():
      """settings/merge_preferences.py is largest (1355 lines, ~50 functions)."""
      from lingwen_creator.settings.merge_preferences import (
          load_merge_preferences,
          save_merge_preferences,
          load_global_merge_preferences,
          save_global_merge_preferences,
          export_merge_preferences,
          import_merge_preferences,
          list_factory_merge_preset_packages,
          list_merge_preset_packages,
          get_merge_preset_package,
          save_merge_preset_package,
          publish_merge_preset_to_factory,
          pull_factory_merge_presets_to_project,
          delete_factory_merge_preset_package,
          export_merge_preset_packages,
          import_merge_preset_packages,
          build_merge_preset_graph,
          detect_merge_preset_conflicts,
          suggest_merge_preset_fixes,
          apply_merge_preset_fix,
          apply_all_merge_preset_fixes,
          preview_merge_preset_import_diff,
          toposort_merge_preset_packages,
          apply_toposort_merge_preset_order,
          detect_factory_merge_preset_conflicts,
          resolve_factory_merge_preset_conflict,
          list_merge_preset_changelog,
          preflight_factory_merge_preset_pull,
          preview_merge_preset_changelog_diff,
          preflight_merge_preset_import,
      )
  ```

- [ ] **Step 2: Run test to verify it fails**
  ```bash
  uv run python -m pytest packages/lingwen-creator/tests/test_settings.py::test_settings_merge_preferences_module_exists -v
  # Expected: FAIL
  ```

- [ ] **Step 3: Read source + identify 1 import to adjust**
  ```bash
  grep -n "from infra.creator_" infra/creator_merge_preferences.py
  # Expected: 1 match — from infra.creator_volume_templates import is_valid_version_label, validate_version_label
  # Map to: from lingwen_creator.volume.templates import is_valid_version_label, validate_version_label
  ```

- [ ] **Step 4: Copy + adjust 1 import (verbatim except that 1 line)**
  ```bash
  cp infra/creator_merge_preferences.py packages/lingwen-creator/src/lingwen_creator/settings/merge_preferences.py
  # Edit 1 import line via Edit tool with exact match
  ```

- [ ] **Step 5: Run tests (GREEN)**
  ```bash
  uv run python -m pytest packages/lingwen-creator/tests/test_settings.py -v
  # Expected: 3 passed (docs + history + merge_preferences)
  uv run python -m pytest tests/infra/test_creator_merge_preferences.py tests/infra/test_creator_merge_preset_*.py -v
  # Expected: all passing
  ```

- [ ] **Step 6: Convert infra/creator_merge_preferences.py to shim**
  ```python
  from lingwen_creator.settings.merge_preferences import *  # noqa: F403
  ```

- [ ] **Step 7: Verify shim + lint + commit**
  ```bash
  /home/ailearn/miniconda3/bin/python -c "from infra.creator_merge_preferences import load_merge_preferences, _semver_tuple, _conflicts_from_packages"
  # Expected: OK (underscore names need explicit re-export — may fail here)
  # If fails, note for Task 12 (shim underscore re-export audit)
  ruff check packages/lingwen-creator/src/lingwen_creator/settings/merge_preferences.py infra/creator_merge_preferences.py
  git add packages/lingwen-creator/src/lingwen_creator/settings/merge_preferences.py \
          packages/lingwen-creator/tests/test_settings.py \
          infra/creator_merge_preferences.py
  git commit -m "feat(creator): T1c settings/merge_preferences.py migration + shim
  
  verbatim copy of infra/creator_merge_preferences.py (1355 lines, ~50 functions) to
  packages/lingwen-creator/src/lingwen_creator/settings/merge_preferences.py
  with 1 intra-package import adjustment (volume.templates per spec §2.3).
  
  infra/creator_merge_preferences.py 变 shim.
  Note: settings/merge_preferences.py has ~20 underscore-prefixed helpers (e.g. _semver_tuple, _conflicts_from_packages).
  Task 12 (shim underscore re-export audit) will audit + add explicit re-exports if any test uses private symbols."
  ```

**Verification:** 3 module tests pass + shim works (or noted for Task 12) + lint clean + 1 commit.

**Subagent dispatches:** Same pattern + extra attention to verbatim copy integrity for largest file.

---

## §4. Task 4 — T1d: settings/__init__.py star-imports + test extension

**Files:**
- Modify: `packages/lingwen-creator/src/lingwen_creator/settings/__init__.py` (add 3 star-imports)
- Modify: `packages/lingwen-creator/tests/test_settings.py` (add layout + intra-import tests)

**Pre-conditions:** Task 3 committed.

**Approach:**

- [ ] **Step 1: Add star-imports to settings/__init__.py**
  ```python
  # packages/lingwen-creator/src/lingwen_creator/settings/__init__.py
  from lingwen_creator.settings.docs import *  # noqa: F403
  from lingwen_creator.settings.history import *  # noqa: F403
  from lingwen_creator.settings.merge_preferences import *  # noqa: F403
  ```

- [ ] **Step 2: Add layout + intra-import tests**
  ```python
  # Append to packages/lingwen-creator/tests/test_settings.py

  def test_settings_package_layout():
      """All 3 modules must be importable via package."""
      from lingwen_creator.settings import docs, history, merge_preferences
      assert docs.__file__.endswith("settings/docs.py")
      assert history.__file__.endswith("settings/history.py")
      assert merge_preferences.__file__.endswith("settings/merge_preferences.py")

  def test_settings_intra_package_imports_terminates():
      """Intra-package imports must not introduce circular dependency."""
      # If circular, this import would fail or hang
      from lingwen_creator.settings.docs import creator_settings_docs_payload
      from lingwen_creator.settings.history import append_settings_snapshot
      from lingwen_creator.settings.merge_preferences import load_merge_preferences
      # All 3 should be callable (import chain terminates via sys.modules)

  def test_settings_intra_imports_use_new_path():
      """Verify no stale infra paths in settings package."""
      import subprocess
      result = subprocess.run(
          ["grep", "-rn", "from infra.creator_",
           "packages/lingwen-creator/src/lingwen_creator/settings/"],
          capture_output=True, text=True,
      )
      assert result.stdout == "", f"Found stale infra imports:\n{result.stdout}"
  ```

- [ ] **Step 3: Run all settings tests**
  ```bash
  uv run python -m pytest packages/lingwen-creator/tests/test_settings.py -v
  # Expected: 6 passed (3 module + 1 layout + 1 intra-import + 1 stale-import check)
  ```

- [ ] **Step 4: Lint + commit**
  ```bash
  ruff check packages/lingwen-creator/src/lingwen_creator/settings/
  # Expected: All checks passed
  git add packages/lingwen-creator/src/lingwen_creator/settings/__init__.py \
          packages/lingwen-creator/tests/test_settings.py
  git commit -m "feat(creator): T1d settings/__init__.py star-imports + tests
  
  - settings/__init__.py: 3 star-imports re-export from docs + history + merge_preferences
  - test_settings.py: extend 3 → 6 tests (3 module + 1 layout + 1 intra-import + 1 stale-import check)
  
  Intra-package imports verified terminate (no circular dep).
  Stale infra.creator_ imports in settings/ = 0."
  ```

**Verification:** 6 tests pass + lint clean + 1 commit.

**Subagent dispatches:** Implementer + spec reviewer (verify spec §1.1 + §2.4 mapping) + code quality reviewer.

---

## §5. Task 5 — T2: Add ~20 Settings DTOs to creator.py + TS codegen

**Files:**
- Modify: `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` (add Settings section with ~20 DTOs)
- Modify: `packages/lingwen-shared/tests/test_creator_dto.py` (add Settings tests)
- Generated: `packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts` (auto)

**Pre-conditions:** Task 4 committed. v16.1 lingwen-shared package exists.

**Approach:**

- [ ] **Step 1: Identify exact DTO field sets**
  ```bash
  # Read each Python function's return shape + FastAPI route Pydantic model.
  # Sources:
  # - infra/creator_settings_docs.py: creator_settings_docs_payload + save_creator_settings_docs + preview_X
  # - infra/creator_settings_history.py: settings_history_payload + restore_settings_snapshot
  # - infra/creator_merge_preferences.py: ~20 functions (load/save/import/export + presets + graph/conflict/fix/toposort/changelog)
  # - apps/studio_api/routes/creator_settings.py: existing Pydantic models for each endpoint
  # Use the spec §3 DTO table as starting list; implementer fills in exact field types.
  ```

- [ ] **Step 2: Write failing test for Settings DTOs (RED)**
  ```python
  # Append to packages/lingwen-shared/tests/test_creator_dto.py

  def test_settings_dtos_importable():
      """All Settings DTOs from spec §3 must be importable."""
      from lingwen_shared.contracts.python.creator import (
          # Docs (5)
          CreatorSettingsDocsResponse,
          CreatorSettingsDocsSaveRequest,
          CreatorSettingsDocsDiffResponse,
          CreatorSettingsThreeWayDiffResponse,
          CreatorSettingsMergeStrategyResponse,
          # History (2)
          CreatorSettingsHistoryResponse,
          CreatorSettingsHistoryRestoreRequest,
          # Merge preferences (3)
          CreatorMergePreferencesResponse,
          CreatorMergePreferencesExportResponse,
          CreatorMergePreferencesImportRequest,
          # Merge presets (10)
          CreatorMergePresetPackageSummary,
          CreatorMergePresetPackageDetail,
          CreatorMergePresetGraphResponse,
          CreatorMergePresetConflictsResponse,
          CreatorMergePresetConflictFix,
          CreatorMergePresetImportPreviewResponse,
          CreatorMergePresetChangelogResponse,
          CreatorMergePresetPublishRequest,
          CreatorFactoryMergePresetOperationResponse,
          CreatorMergePresetToposortResponse,
      )
  ```

- [ ] **Step 3: Run test to verify it fails**
  ```bash
  uv run python -m pytest packages/lingwen-shared/tests/test_creator_dto.py::test_settings_dtos_importable -v
  # Expected: FAIL (Settings DTOs not yet added)
  ```

- [ ] **Step 4: Add Settings section to creator.py**
  ```python
  # Append to packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py
  # (After the Volume section, before the closing if-block or end of file)

  # === Settings Subdomain (Phase 126 v16.2.2) ===

  class CreatorSettingsDocsResponse(BaseModel):
      """Return shape of creator_settings_docs_payload()."""
      project_slug: str
      docs: dict[str, Any]  # actual structure depends on docs_payload
      revision: int
      updated_at: str

  class CreatorSettingsDocsSaveRequest(BaseModel):
      """Input of save_creator_settings_docs()."""
      docs: dict[str, Any]
      expected_revision: int | None = None

  class CreatorSettingsDocsDiffResponse(BaseModel):
      """Return shape of preview_settings_docs_diff()."""
      summary: dict[str, Any]
      sections: list[dict[str, Any]]

  class CreatorSettingsThreeWayDiffResponse(BaseModel):
      """Return shape of preview_settings_three_way()."""
      base: dict[str, Any]
      ours: dict[str, Any]
      theirs: dict[str, Any]
      merged: dict[str, Any]

  class CreatorSettingsMergeStrategyResponse(BaseModel):
      """Return shape of preview_settings_merge_strategy()."""
      strategy: str
      conflicts: list[dict[str, Any]]
      resolution_preview: dict[str, Any]

  class CreatorSettingsHistoryResponse(BaseModel):
      """Return shape of settings_history_payload()."""
      entries: list[dict[str, Any]]  # actually CreatorSettingsHistoryEntry shape

  class CreatorSettingsHistoryRestoreRequest(BaseModel):
      """Input of restore_settings_snapshot()."""
      snapshot_id: str

  class CreatorMergePreferencesResponse(BaseModel):
      """Return shape of load_merge_preferences() + load_global_merge_preferences()."""
      preferences: dict[str, Any]
      scope: str  # "project" or "global"

  class CreatorMergePreferencesExportResponse(BaseModel):
      """Return shape of export_merge_preferences()."""
      data: dict[str, Any]
      exported_at: str

  class CreatorMergePreferencesImportRequest(BaseModel):
      """Input of import_merge_preferences()."""
      data: dict[str, Any]
      conflict_strategy: str = "abort"

  class CreatorMergePresetPackageSummary(BaseModel):
      """Items in list_merge_preset_packages()."""
      package_id: str
      name: str
      version: str
      scope: str  # "factory" or "project"
      builtin: bool

  class CreatorMergePresetPackageDetail(BaseModel):
      """Return shape of get_merge_preset_package()."""
      package_id: str
      name: str
      version: str
      content: dict[str, Any]
      changelog: list[dict[str, Any]]

  class CreatorMergePresetGraphResponse(BaseModel):
      """Return shape of build_merge_preset_graph()."""
      nodes: list[dict[str, Any]]
      edges: list[dict[str, Any]]

  class CreatorMergePresetConflictsResponse(BaseModel):
      """Return shape of detect_merge_preset_conflicts() + factory variant."""
      conflicts: list[dict[str, Any]]
      scope: str  # "project" or "factory"

  class CreatorMergePresetConflictFix(BaseModel):
      """Items in suggest_merge_preset_fixes() + input of apply_merge_preset_fix()."""
      conflict_id: str
      fix_type: str
      payload: dict[str, Any]

  class CreatorMergePresetImportPreviewResponse(BaseModel):
      """Return shape of preview_merge_preset_import_diff() + preflight_merge_preset_import()."""
      to_import: list[str]
      conflicts: list[dict[str, Any]]
      virtual_packages: list[dict[str, Any]]

  class CreatorMergePresetChangelogResponse(BaseModel):
      """Return shape of list_merge_preset_changelog() + preview_merge_preset_changelog_diff()."""
      entries: list[dict[str, Any]]
      diff: dict[str, Any] | None = None

  class CreatorMergePresetPublishRequest(BaseModel):
      """Input of publish_merge_preset_to_factory()."""
      package_id: str
      version: str

  class CreatorFactoryMergePresetOperationResponse(BaseModel):
      """Return shape of publish + pull + delete + resolve_factory_conflict."""
      operation: str
      package_id: str
      result: dict[str, Any]

  class CreatorMergePresetToposortResponse(BaseModel):
      """Return shape of toposort_merge_preset_packages() + apply_toposort_merge_preset_order()."""
      order: list[str]
      cycles: list[list[str]] | None = None
  ```

  **IMPORTANT**: The actual DTO field types in Step 4 must be derived from reading `infra/creator_settings_*.py` + `apps/studio_api/routes/creator_settings.py` carefully. The spec §3 lists DTO names + source functions, but exact fields are implementation-stage discovery. Use `Any` for complex nested structures initially, refine after first compile attempt.

- [ ] **Step 5: Run DTO test (GREEN)**
  ```bash
  uv run python -m pytest packages/lingwen-shared/tests/test_creator_dto.py -v
  # Expected: all passing (new Settings DTOs importable)
  ```

- [ ] **Step 6: Generate TS**
  ```bash
  uv run python tooling/contracts/generate.py
  # Expected: creator.ts updated with ~20 new Settings interfaces
  grep -c "^export interface" packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts
  # Expected: ~79 (was 59 volume + 20 settings)
  ```

- [ ] **Step 7: Add behavioral DTO tests**
  ```python
  # Append to packages/lingwen-shared/tests/test_creator_dto.py

  def test_settings_docs_response_roundtrip():
      from lingwen_shared.contracts.python.creator import CreatorSettingsDocsResponse
      r = CreatorSettingsDocsResponse(
          project_slug="test",
          docs={"format_version": 1, "sections": {}},
          revision=1,
          updated_at="2026-08-27T00:00:00Z",
      )
      assert r.project_slug == "test"
      assert r.revision == 1

  def test_settings_history_entry_serialization():
      from lingwen_shared.contracts.python.creator import CreatorSettingsHistoryResponse
      r = CreatorSettingsHistoryResponse(entries=[{"id": "snap-1", "ts": "2026-08-27T00:00:00Z"}])
      d = r.model_dump()
      assert d["entries"][0]["id"] == "snap-1"

  def test_merge_preset_package_detail_changelog_optional():
      from lingwen_shared.contracts.python.creator import CreatorMergePresetPackageDetail
      pkg = CreatorMergePresetPackageDetail(
          package_id="p1",
          name="Test",
          version="1.0.0",
          content={"x": 1},
          changelog=[],
      )
      assert pkg.changelog == []

  # Add 2-3 more for top DTOs (CreatorMergePresetGraphResponse, CreatorMergePresetConflictsResponse)
  # Total ~5 behavioral tests
  ```

- [ ] **Step 8: Run all tests + lint**
  ```bash
  uv run python -m pytest packages/lingwen-shared/tests/ -v
  # Expected: all passing (Settings + existing)
  ruff check packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py
  ```

- [ ] **Step 9: Commit**
  ```bash
  git add packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py \
          packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts \
          packages/lingwen-shared/tests/test_creator_dto.py
  git commit -m "feat(shared): T2 Settings DTOs (~20 Pydantic models) + TS codegen
  
  Phase 126 v16.2.2 settings subdomain — 20 DTOs added to
  packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py:
  - 5 docs (CreatorSettingsDocsResponse + SaveRequest + 3 Diff/Strategy responses)
  - 2 history (HistoryResponse + RestoreRequest)
  - 3 merge preferences (Response + Export + Import)
  - 10 merge presets (Package Summary/Detail/Graph/Conflicts/Fix/ImportPreview/Changelog/Publish/Factory/Toposort)
  
  tooling/contracts/generate.py: regenerate TS, ~20 new interfaces (total ~79).
  test_creator_dto.py: +6 tests (1 importable + 5 behavioral)."
  ```

**Verification:** DTOs importable + behavioral tests pass + TS generated + lint clean + 1 commit.

**Subagent dispatches:** Implementer (DTO design) + spec reviewer (verify spec §3 mapping) + code quality reviewer (Pydantic best practices).

---

## §6. Task 6 — T3: typed wrapper settings.ts + re-export shim + knip

**Files:**
- Create: `apps/dashboard/src/api/settings.ts` (~15 wrapper functions)
- Create: `packages/dashboard-contracts/src/shared/settings.ts` (re-export shim)
- Modify: `apps/dashboard/knip.json` (add settings.ts allowlist)

**Pre-conditions:** Task 5 committed (DTOs available in `packages/dashboard-contracts`).

**Approach:**

- [ ] **Step 1: Read v16.1 T4 reference**
  ```bash
  cat apps/dashboard/src/api/quality.ts | head -80
  # Pattern: import Creator* from '@lingwen/dashboard-contracts'
  # import { BASE_URL } from '@/lib/core'
  # No zod runtime validation
  # No '/api/' prefix in URL paths
  ```

- [ ] **Step 2: Write typed wrapper (TS, no zod, no /api/ prefix)**
  ```typescript
  // apps/dashboard/src/api/settings.ts
  import type {
      CreatorSettingsDocsResponse,
      CreatorSettingsDocsSaveRequest,
      CreatorSettingsDocsDiffResponse,
      CreatorSettingsThreeWayDiffResponse,
      CreatorSettingsMergeStrategyResponse,
      CreatorSettingsHistoryResponse,
      CreatorSettingsHistoryRestoreRequest,
      CreatorMergePreferencesResponse,
      CreatorMergePreferencesExportResponse,
      CreatorMergePreferencesImportRequest,
      CreatorMergePresetPackageSummary,
      CreatorMergePresetPackageDetail,
      CreatorMergePresetGraphResponse,
      CreatorMergePresetConflictsResponse,
      CreatorMergePresetConflictFix,
      CreatorMergePresetImportPreviewResponse,
      CreatorMergePresetChangelogResponse,
      CreatorMergePresetPublishRequest,
      CreatorFactoryMergePresetOperationResponse,
      CreatorMergePresetToposortResponse,
  } from '@lingwen/dashboard-contracts';

  import { apiFetch } from '@/lib/apiFetch';  // or use fetch directly with BASE_URL

  const BASE = (await import('@/lib/core')).BASE_URL;  // already includes /api

  // Docs (5)
  export async function getSettingsDocs(projectId: string): Promise<CreatorSettingsDocsResponse> {
      return apiFetch(`${BASE}/creator/settings/${projectId}/docs`);
  }

  export async function saveSettingsDocs(
      projectId: string,
      req: CreatorSettingsDocsSaveRequest,
  ): Promise<CreatorSettingsDocsResponse> {
      return apiFetch(`${BASE}/creator/settings/${projectId}/docs`, {
          method: 'PUT',
          body: JSON.stringify(req),
      });
  }

  export async function previewSettingsDocsDiff(
      projectId: string,
      before: string,
      after: string,
  ): Promise<CreatorSettingsDocsDiffResponse> {
      return apiFetch(`${BASE}/creator/settings/${projectId}/docs/diff`, {
          method: 'POST',
          body: JSON.stringify({ before, after }),
      });
  }

  export async function previewSettingsThreeWay(
      projectId: string,
      base: string,
      ours: string,
      theirs: string,
  ): Promise<CreatorSettingsThreeWayDiffResponse> {
      return apiFetch(`${BASE}/creator/settings/${projectId}/docs/three-way`, {
          method: 'POST',
          body: JSON.stringify({ base, ours, theirs }),
      });
  }

  export async function previewSettingsMergeStrategy(
      projectId: string,
      base: string,
      ours: string,
      theirs: string,
  ): Promise<CreatorSettingsMergeStrategyResponse> {
      return apiFetch(`${BASE}/creator/settings/${projectId}/docs/merge-strategy`, {
          method: 'POST',
          body: JSON.stringify({ base, ours, theirs }),
      });
  }

  // History (2)
  export async function getSettingsHistory(projectId: string): Promise<CreatorSettingsHistoryResponse> {
      return apiFetch(`${BASE}/creator/settings/${projectId}/history`);
  }

  export async function restoreSettingsSnapshot(
      projectId: string,
      req: CreatorSettingsHistoryRestoreRequest,
  ): Promise<void> {
      await apiFetch(`${BASE}/creator/settings/${projectId}/history/restore`, {
          method: 'POST',
          body: JSON.stringify(req),
      });
  }

  // Merge preferences (3)
  export async function getMergePreferences(projectId: string): Promise<CreatorMergePreferencesResponse> {
      return apiFetch(`${BASE}/creator/settings/${projectId}/merge-preferences`);
  }

  export async function exportMergePreferences(projectId: string): Promise<CreatorMergePreferencesExportResponse> {
      return apiFetch(`${BASE}/creator/settings/${projectId}/merge-preferences/export`, {
          method: 'POST',
      });
  }

  export async function importMergePreferences(
      projectId: string,
      req: CreatorMergePreferencesImportRequest,
  ): Promise<CreatorMergePreferencesResponse> {
      return apiFetch(`${BASE}/creator/settings/${projectId}/merge-preferences/import`, {
          method: 'POST',
          body: JSON.stringify(req),
      });
  }

  // Merge presets (5 of ~10; cover remaining in iteration if endpoints exceed)
  export async function listMergePresetPackages(projectId: string): Promise<CreatorMergePresetPackageSummary[]> {
      return apiFetch(`${BASE}/creator/settings/${projectId}/merge-presets`);
  }

  export async function getMergePresetPackage(
      projectId: string,
      packageId: string,
  ): Promise<CreatorMergePresetPackageDetail> {
      return apiFetch(`${BASE}/creator/settings/${projectId}/merge-presets/${packageId}`);
  }

  export async function buildMergePresetGraph(projectId: string): Promise<CreatorMergePresetGraphResponse> {
      return apiFetch(`${BASE}/creator/settings/${projectId}/merge-presets/graph`);
  }

  export async function detectMergePresetConflicts(projectId: string): Promise<CreatorMergePresetConflictsResponse> {
      return apiFetch(`${BASE}/creator/settings/${projectId}/merge-presets/conflicts`);
  }

  export async function publishMergePresetToFactory(
      projectId: string,
      req: CreatorMergePresetPublishRequest,
  ): Promise<CreatorFactoryMergePresetOperationResponse> {
      return apiFetch(`${BASE}/creator/settings/${projectId}/merge-presets/publish`, {
          method: 'POST',
          body: JSON.stringify(req),
      });
  }
  ```

  **IMPORTANT**: 
  - NO `/api/` prefix in URL paths (v16.2.1 lesson — `BASE_URL` is already `/api`)
  - NO zod runtime validation (v16.2.1 lesson — zod is T5/CI drift)
  - Wrapper function count should match endpoints in `creator_settings.py` (~15-30 endpoints)
  - If actual routes have different paths, implementer must `grep` `creator_settings.py` for `@router.` decorators

- [ ] **Step 3: Verify URL contract**
  ```bash
  grep "/api/api" apps/dashboard/src/api/settings.ts
  # Expected: 0 matches (no double /api/)
  ```

- [ ] **Step 4: Create re-export shim**
  ```typescript
  // packages/dashboard-contracts/src/shared/settings.ts
  export * from '@lingwen/dashboard-contracts/src/shared/settings';
  ```
  *(Note: if re-export path is wrong, check v16.2.1 `packages/dashboard-contracts/src/shared/creator.ts` for correct pattern)*

- [ ] **Step 5: Update knip.json allowlist**
  ```json
  // apps/dashboard/knip.json — add settings.ts to existing allowlist
  {
    "files": [
      "apps/dashboard/src/api/{world,workspace,quality,volume,settings}.ts"
    ]
  }
  ```

- [ ] **Step 6: Verify TypeScript + knip**
  ```bash
  pnpm exec vue-tsc --noEmit
  # Expected: 0 errors
  pnpm exec knip
  # Expected: 0 errors (settings.ts + re-export shim allowed)
  ```

- [ ] **Step 7: Add URL contract test (v16.2.1 pattern — 18 tests regression lock)**
  ```typescript
  // apps/dashboard/tests/unit/api/use-settings-typed-wrapper.spec.ts
  import { describe, it, expect, vi } from 'vitest';
  import * as settingsApi from '@/api/settings';

  describe('settings.ts URL contract', () => {
      // Each wrapper function should NOT contain '/api/' prefix (BASE_URL handles it)
      const wrappers = Object.entries(settingsApi);
      for (const [name, fn] of wrappers) {
          if (typeof fn !== 'function') continue;
          it(`${name} has no /api/ prefix`, () => {
              const src = fn.toString();
              expect(src).not.toMatch(/\/api\/creator/);
          });
      }
  });
  ```

- [ ] **Step 8: Run frontend tests**
  ```bash
  cd apps/dashboard && pnpm vitest run tests/unit/api/use-settings-typed-wrapper.spec.ts
  # Expected: ≥15 passed
  ```

- [ ] **Step 9: Commit**
  ```bash
  git add apps/dashboard/src/api/settings.ts \
          packages/dashboard-contracts/src/shared/settings.ts \
          apps/dashboard/knip.json \
          apps/dashboard/tests/unit/api/use-settings-typed-wrapper.spec.ts
  git commit -m "feat(dashboard): T3 settings.ts typed wrapper + re-export shim + knip
  
  Phase 126 v16.2.2 — typed wrapper for settings subdomain:
  - apps/dashboard/src/api/settings.ts: ~15 wrapper functions (no zod, no /api/ prefix)
  - packages/dashboard-contracts/src/shared/settings.ts: re-export shim
  - apps/dashboard/knip.json: add settings.ts allowlist
  - use-settings-typed-wrapper.spec.ts: 15 URL-contract tests (regression lock for /api/ prefix bug)
  
  Pattern follows v16.1 T4 (world.ts/workspace.ts/quality.ts) + v16.2.1 volume.ts.
  Verified: 0 '/api/api/' duplicates, vue-tsc 0 errors, knip 0 errors."
  ```

**Verification:** vue-tsc 0 / knip 0 / URL contract tests pass + 1 commit.

**Subagent dispatches:** Implementer (TS wrapper) + spec reviewer (verify v16.1 T4 + v16.2.1 style — no zod, no /api/) + code quality reviewer (typescript-reviewer for type safety).

---

## §7. Task 7 — T4a: useCreatorSettings composable refactor part 1

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorSettings.{js,ts}` (whichever exists)
- Possibly add new test files

**Pre-conditions:** Task 6 committed.

**Approach:**

- [ ] **Step 1: Locate composable file(s)**
  ```bash
  ls apps/dashboard/src/composables/useCreatorSettings*
  grep -l "creator_settings_docs\|creator_settings_history\|creator_merge_preferences" apps/dashboard/src/composables/*.js apps/dashboard/src/composables/*.ts 2>/dev/null
  # Identify all composables that touch settings
  ```

- [ ] **Step 2: Read composable(s) + identify fetch calls to replace**
  ```bash
  cat <composable-file>
  # Look for: fetch(BASE_URL + '/api/creator/settings/...')
  # Replace with: getSettingsDocs(projectId), saveSettingsDocs(...), etc.
  ```

- [ ] **Step 3: Write failing test for composable behavior preservation**
  ```typescript
  // apps/dashboard/tests/unit/composables/use-creator-settings.spec.ts
  import { describe, it, expect, vi } from 'vitest';
  import { useCreatorSettings } from '@/composables/useCreatorSettings';

  describe('useCreatorSettings', () => {
      it('uses typed wrapper (not raw fetch)', async () => {
          const spy = vi.spyOn(globalThis, 'fetch');
          const { loadDocs } = useCreatorSettings('test-project');
          await loadDocs();
          // Should NOT have called raw fetch with /api/creator/settings/docs
          // (typed wrapper uses apiFetch internally)
          const calls = spy.mock.calls.filter((c) => String(c[0]).includes('/creator/settings/'));
          expect(calls.length).toBe(0);
      });
  });
  ```

- [ ] **Step 4: Refactor composable part 1 (subset of functions)**
  ```javascript
  // Replace ~half of fetch calls with typed wrapper imports
  // E.g. loadSettingsDocs, saveSettingsDocs, getHistory (only the simpler ones first)
  ```

- [ ] **Step 5: Run tests**
  ```bash
  cd apps/dashboard && pnpm vitest run tests/unit/composables/use-creator-settings.spec.ts
  # Expected: passing
  ```

- [ ] **Step 6: Verify TypeScript + commit**
  ```bash
  pnpm exec vue-tsc --noEmit
  # Expected: 0 errors
  git add <files>
  git commit -m "feat(dashboard): T4a useCreatorSettings composable refactor part 1
  
  Replace ~half of raw fetch calls in useCreatorSettings composable
  with typed wrapper functions from '@/api/settings'.
  
  Pattern: fetch(BASE_URL + '/api/creator/settings/X', ...) → settingsX(projectId, ...)
  Avoid /api/ prefix bug per v16.2.1 lesson."
  ```

**Verification:** Composable tests pass + vue-tsc 0 + 1 commit.

**Subagent dispatches:** Implementer + code quality reviewer (typescript-reviewer).

---

## §8. Task 8 — T4b: useCreatorSettings part 2 + routes chunk 1 (docs imports)

**Files:**
- Modify: composable file(s) — finish remaining fetch replacements
- Modify: `apps/studio_api/routes/creator_settings.py` (chunk 1: docs.py imports only, ~5 imports)

**Pre-conditions:** Task 7 committed.

**Approach:**

- [ ] **Step 1: Finish composable refactor**
  ```javascript
  // Replace remaining fetch calls (more complex ones: merge preferences, presets, etc.)
  ```

- [ ] **Step 2: Routes chunk 1 — docs.py imports**
  ```bash
  grep -n "from infra.creator_settings_docs" apps/studio_api/routes/creator_settings.py
  # Expected: ~5 matches (lines 83, 93, 122, 142, possibly more)
  ```
  Replace each with `from lingwen_creator.settings.docs import ...`

- [ ] **Step 3: Verify routes tests pass**
  ```bash
  uv run python -m pytest apps/studio_api/tests/test_creator_settings*.py -v
  # Expected: all passing (routes now import from new package, shim still works for other imports)
  ```

- [ ] **Step 4: Verify backend import smoke**
  ```bash
  /home/ailearn/miniconda3/bin/python -c "from apps.studio_api.routes.creator_settings import router; print('OK')"
  # Expected: OK
  ```

- [ ] **Step 5: Run all settings tests**
  ```bash
  uv run python -m pytest tests/infra/test_creator_settings_*.py tests/infra/test_creator_merge_preferences.py tests/infra/test_creator_merge_preset_*.py -q
  # Expected: all passing
  ```

- [ ] **Step 6: Commit**
  ```bash
  git add <composable-file> apps/studio_api/routes/creator_settings.py
  git commit -m "feat(routes): T4b useCreatorSettings part 2 + creator_settings.py docs imports
  
  - useCreatorSettings: complete refactor (all raw fetch → typed wrapper)
  - apps/studio_api/routes/creator_settings.py: 5 lazy imports migrated
    from infra.creator_settings_docs → lingwen_creator.settings.docs
  - routes tests + infra tests still passing."
  ```

**Verification:** Composable + routes tests pass + 1 commit.

**Subagent dispatches:** Implementer + spec reviewer (verify spec §6 chunk 1) + code quality reviewer.

---

## §9. Task 9 — T5a: routes chunk 2 (merge_preferences imports first half)

**Files:**
- Modify: `apps/studio_api/routes/creator_settings.py` (chunk 2: first ~10 merge_preferences imports)

**Pre-conditions:** Task 8 committed.

**Approach:**

- [ ] **Step 1: Identify first half of merge_preferences imports**
  ```bash
  grep -n "from infra.creator_merge_preferences" apps/studio_api/routes/creator_settings.py
  # Expected: ~25 matches (split into 2 chunks for DP-06 ≤4 files/commit, but routes is single file so chunks are commits not file splits)
  ```

- [ ] **Step 2: Replace first half (lines 159 to ~280)**
  ```python
  # Before: from infra.creator_merge_preferences import load_merge_preferences
  # After:  from lingwen_creator.settings.merge_preferences import load_merge_preferences
  ```

- [ ] **Step 3: Verify**
  ```bash
  uv run python -m pytest apps/studio_api/tests/test_creator_settings*.py tests/infra/test_creator_merge_preferences.py -q
  # Expected: all passing
  grep "^from infra.creator_merge_preferences" apps/studio_api/routes/creator_settings.py | wc -l
  # Expected: ~12 (was 25)
  ```

- [ ] **Step 4: Commit**
  ```bash
  git add apps/studio_api/routes/creator_settings.py
  git commit -m "feat(routes): T5a creator_settings.py merge_preferences imports chunk 1
  
  Migrate ~10 lazy imports from infra.creator_merge_preferences → lingwen_creator.settings.merge_preferences.
  Routes tests passing. Shim back-compat preserved."
  ```

**Verification:** routes tests pass + 1 commit.

**Subagent dispatches:** Implementer + code quality reviewer.

---

## §10. Task 10 — T5b: routes chunk 3 (merge_preferences finalize)

**Files:**
- Modify: `apps/studio_api/routes/creator_settings.py` (chunk 3: remaining merge_preferences imports + history imports)

**Pre-conditions:** Task 9 committed.

**Approach:**

- [ ] **Step 1: Replace remaining imports**
  ```bash
  grep -n "from infra.creator_merge_preferences\|from infra.creator_settings_history" apps/studio_api/routes/creator_settings.py
  # Expected: ~15 remaining
  ```

- [ ] **Step 2: Verify zero infra imports remain**
  ```bash
  grep "^from infra.creator_settings_\|^from infra.creator_merge_preferences" apps/studio_api/routes/creator_settings.py
  # Expected: 0 matches (all 32 imports migrated)
  ```

- [ ] **Step 3: Run full backend test suite**
  ```bash
  uv run python -m pytest tests/ apps/studio_api/tests/ packages/lingwen-creator/tests/ -q
  # Expected: 0 regressions
  ```

- [ ] **Step 4: Commit**
  ```bash
  git add apps/studio_api/routes/creator_settings.py
  git commit -m "feat(routes): T5b creator_settings.py finalize (all 32 imports migrated)
  
  Migrate remaining ~15 lazy imports from infra.creator_settings_history + infra.creator_merge_preferences.
  Total: 32 imports migrated from creator_settings.py (per spec §6).
  Full backend test suite: 0 regressions."
  ```

**Verification:** 0 infra imports + 0 regressions + 1 commit.

**Subagent dispatches:** Implementer + code quality reviewer.

---

## §11. Task 11 — T6: Cross-subdomain cleanup (volume/templates + template_approvals)

**Files:**
- Modify: `packages/lingwen-creator/src/lingwen_creator/volume/templates.py:144` (1 lazy import)
- Modify: `packages/lingwen-creator/src/lingwen_creator/volume/template_approvals.py:667` (1 lazy import)

**Pre-conditions:** Task 10 committed.

**Approach:**

- [ ] **Step 1: Verify the 2 stale lazy imports**
  ```bash
  grep -n "from infra.creator_settings_docs" packages/lingwen-creator/src/lingwen_creator/volume/templates.py packages/lingwen-creator/src/lingwen_creator/volume/template_approvals.py
  # Expected:
  # templates.py:144: from infra.creator_settings_docs import text_diff_summary
  # template_approvals.py:667: from infra.creator_settings_docs import text_diff_summary
  ```

- [ ] **Step 2: Replace both**
  ```python
  # templates.py:144
  # Before: from infra.creator_settings_docs import text_diff_summary
  # After:  from lingwen_creator.settings.docs import text_diff_summary

  # template_approvals.py:667
  # Before: from infra.creator_settings_docs import text_diff_summary
  # After:  from lingwen_creator.settings.docs import text_diff_summary
  ```

- [ ] **Step 3: Verify volume tests pass**
  ```bash
  uv run python -m pytest packages/lingwen-creator/tests/test_volume.py tests/infra/test_creator_volume_*.py -v
  # Expected: all passing (lazy imports now use new path, settings.shim still works as fallback)
  ```

- [ ] **Step 4: Verify no stale infra imports in volume**
  ```bash
  grep -rn "from infra.creator_" packages/lingwen-creator/src/lingwen_creator/volume/ | grep -v "import \*\s*# noqa"
  # Expected: 0 matches (other than shim patterns)
  ```

- [ ] **Step 5: Commit**
  ```bash
  git add packages/lingwen-creator/src/lingwen_creator/volume/templates.py \
          packages/lingwen-creator/src/lingwen_creator/volume/template_approvals.py
  git commit -m "refactor(volume): T6 cross-subdomain lazy import cleanup
  
  v16.2.1 volume migration left 2 stale infra.creator_settings_docs lazy imports
  in volume package. Now that settings has migrated, update to:
  
  - volume/templates.py:144: infra.creator_settings_docs.text_diff_summary → lingwen_creator.settings.docs.text_diff_summary
  - volume/template_approvals.py:667: same
  
  Lesson: 已迁 subdomain 的 cross-subdomain lazy imports 应在 target 迁出后立即清理,
  避免留 stale infra paths. (To be added to v16.2.2 lessons.)"
  ```

**Verification:** Volume tests pass + 0 stale infra imports + 1 commit.

**Subagent dispatches:** Implementer + code quality reviewer.

---

## §12. Task 12 — T7: Shim underscore re-export audit

**Files:**
- Modify: `infra/creator_settings_docs.py` (add underscore re-exports if audit finds)
- Modify: `infra/creator_settings_history.py` (add underscore re-exports if audit finds)
- Modify: `infra/creator_merge_preferences.py` (likely need ~15-20 underscore re-exports)

**Pre-conditions:** Task 11 committed.

**Approach:**

- [ ] **Step 1: Audit tests for private symbol usage**
  ```bash
  # Find tests that import underscore-prefixed names from settings
  grep -rn "from infra.creator_settings_\|from infra.creator_merge_preferences" tests/ 2>/dev/null | grep -v "^Binary" | head -30
  # Look for any line like: from infra.creator_merge_preferences import _semver_tuple
  ```

- [ ] **Step 2: Find underscore-prefixed symbols in settings package**
  ```bash
  grep -hn "^def _\|^_[a-z]" packages/lingwen-creator/src/lingwen_creator/settings/*.py | grep "^def _" | head -30
  # List all underscore-prefixed functions
  ```

- [ ] **Step 3: Cross-reference tests using those symbols**
  ```bash
  # For each underscore function, check if any test imports it
  # If yes, add explicit re-export to shim
  ```

- [ ] **Step 4: Update shim files with explicit re-exports**
  ```python
  # infra/creator_settings_docs.py (after audit)
  from lingwen_creator.settings.docs import *  # noqa: F403
  # Add explicit re-exports if any underscore name needed:
  # from lingwen_creator.settings.docs import _some_private_helper  # noqa: F401

  # infra/creator_merge_preferences.py (after audit — likely many)
  from lingwen_creator.settings.merge_preferences import *  # noqa: F403
  from lingwen_creator.settings.merge_preferences import (
      _semver_tuple,
      _conflicts_from_packages,
      _prefs_path,
      _prefs_export_block,
      _custom_preset_packages_path,
      _load_custom_preset_packages,
      _factory_preset_packages_path,
      _load_factory_preset_store,
      _save_factory_preset_store,
      _normalize_factory_preset_id,
      _normalize_preset_version,
      _preset_row,
      _preset_import_fields,
      _preset_content_signature,
      _preset_changelog_path,
      _load_preset_changelog_store,
      _append_merge_preset_changelog,
      _virtual_packages_after_import,
      _now_iso,
      _normalize_prefs,
      _global_prefs_path,
  )  # explicit re-exports for test compat (per v16.2.1 lesson)
  ```

- [ ] **Step 5: Verify all shim backwards-compat**
  ```bash
  /home/ailearn/miniconda3/bin/python -c "from infra.creator_settings_docs import creator_settings_docs_payload, text_diff_summary"
  /home/ailearn/miniconda3/bin/python -c "from infra.creator_settings_history import settings_history_payload, append_settings_snapshot"
  /home/ailearn/miniconda3/bin/python -c "from infra.creator_merge_preferences import load_merge_preferences, _semver_tuple, _conflicts_from_packages"
  # All 3: OK

  uv run python -m pytest tests/infra/test_creator_settings_*.py tests/infra/test_creator_merge_*.py -q
  # Expected: all passing
  ```

- [ ] **Step 6: Lint + commit**
  ```bash
  ruff check infra/creator_settings_docs.py infra/creator_settings_history.py infra/creator_merge_preferences.py
  # Expected: All checks passed (F403 + F401 both noqa'd)
  git add infra/creator_settings_docs.py infra/creator_settings_history.py infra/creator_merge_preferences.py
  git commit -m "feat(creator): T7 shim underscore re-exports for test compat
  
  Per v16.2.1 lesson: 任何 shim 必须 audit existing tests for private symbol imports,
  如果有, 加 explicit re-exports.
  
  Audit findings:
  - creator_settings_docs.py: 0 underscore names need re-export
  - creator_settings_history.py: 0 underscore names need re-export
  - creator_merge_preferences.py: ~20 underscore helpers need re-export
    (per §7.2 estimate: _semver_tuple, _conflicts_from_packages, _prefs_*, _normalize_*, _preset_*, _factory_*, etc.)
  
  shim back-compat verified: /home/ailearn/miniconda3/bin/python imports work."
  ```

**Verification:** All shim back-compat verified + tests pass + lint clean + 1 commit.

**Subagent dispatches:** Implementer + code quality reviewer (python-reviewer for shim pattern correctness).

---

## §13. Task 13 — T8: Final verification gates + handoff doc

**Files:**
- Modify: `.lingwen/architecture.yml` (add Settings exports to creator module_boundaries)
- Modify: `.lingwen/migration_log.yml` (add v16.2.2 entry)
- Create: `docs/superpowers/handoffs/2026-08-27-phase-126-v16-2-2-settings-handoff.md`

**Pre-conditions:** All previous tasks committed.

**Approach:**

- [ ] **Step 1: Update .lingwen/architecture.yml**
  ```yaml
  # In .lingwen/architecture.yml, find `creator` module_boundaries exports list
  # Add new section after Volume exports:

  # Memory (v16.2.2) — 待添加
  # Settings (v16.2.3) — 待添加
  # ... (existing comment lines)
  
  # Replace "Settings (v16.2.3) — 待添加" with:
  # Settings (v16.2.2) ✅ — creator_settings_docs + creator_settings_history + creator_merge_preferences
  creator_settings_docs_payload, save_creator_settings_docs, preview_settings_docs_diff,
  preview_settings_three_way, preview_settings_merge_strategy, assert_settings_revisions,
  resolve_merged_settings, text_diff_summary,
  settings_history_payload, append_settings_snapshot, restore_settings_snapshot,
  load_merge_preferences, save_merge_preferences, load_global_merge_preferences,
  save_global_merge_preferences, export_merge_preferences, import_merge_preferences,
  list_factory_merge_preset_packages, list_merge_preset_packages, get_merge_preset_package,
  save_merge_preset_package, publish_merge_preset_to_factory,
  pull_factory_merge_presets_to_project, delete_factory_merge_preset_package,
  export_merge_preset_packages, import_merge_preset_packages, build_merge_preset_graph,
  detect_merge_preset_conflicts, suggest_merge_preset_fixes, apply_merge_preset_fix,
  apply_all_merge_preset_fixes, preview_merge_preset_import_diff,
  toposort_merge_preset_packages, apply_toposort_merge_preset_order,
  detect_factory_merge_preset_conflicts, resolve_factory_merge_preset_conflict,
  list_merge_preset_changelog, preflight_factory_merge_preset_pull,
  preview_merge_preset_changelog_diff, preflight_merge_preset_import,
  ```
  Also update the `notes` section:
  ```yaml
  notes:
    - "v16.2.0: skeleton + shared/ migration"
    - "v16.2.1 ✅: Volume subdomain 闭环"
    - "v16.2.2 ✅: Settings subdomain 闭环 (3 files + ~20 DTOs + typed wrapper + 1 composable + 32 routes imports + 2 cross-imports cleanup)"
    - "v16.2.3..6: 4 subdomains (onboarding/content/export/memory) 依次迁入"
    - "v16.2.7: shim cleanup"
    - "⚠️ v16.2.0 review 发现: shared/check.py 当前依赖 infra.creator_mode.CreatorSettings (违反 spec §2.4)。v16.2.6 content migration 时修。carryover 到 v16.2.6 Task 5.1."
    - "v16.2.1 review: typed wrappers (world.ts/workspace.ts/quality.ts) 仍有 /api/api/ URL 重复 bug。carryover 到 v16.2.7 cleanup。"
  ```

- [ ] **Step 2: Update .lingwen/migration_log.yml**
  ```yaml
  # Add new entry after v16.2.1 entry:

  - phase: 126
    version: 16.2.2
    date: 2026-08-27
    scope: Creator 6-subdomain 拆分 Phase 3/8 — Settings subdomain 闭环
    files_added:
      - packages/lingwen-creator/src/lingwen_creator/settings/docs.py (351 lines)
      - packages/lingwen-creator/src/lingwen_creator/settings/history.py (136 lines)
      - packages/lingwen-creator/src/lingwen_creator/settings/merge_preferences.py (1355 lines)
      - packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts (~20 new Settings interfaces)
      - apps/dashboard/src/api/settings.ts (~15 wrapper functions)
      - packages/dashboard-contracts/src/shared/settings.ts (re-export shim)
      - packages/lingwen-creator/tests/test_settings.py (6 tests)
      - apps/dashboard/tests/unit/api/use-settings-typed-wrapper.spec.ts (~15 URL-contract tests)
      - docs/superpowers/handoffs/2026-08-27-phase-126-v16-2-2-settings-handoff.md
    files_modified:
      - packages/lingwen-creator/src/lingwen_creator/settings/__init__.py (3 star-imports)
      - packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py (~20 Settings DTOs)
      - packages/lingwen-shared/tests/test_creator_dto.py (+6 tests)
      - apps/studio_api/routes/creator_settings.py (32 lazy imports migrated)
      - apps/dashboard/src/composables/useCreatorSettings.{js,ts} (typed wrapper refactor)
      - apps/dashboard/knip.json (settings.ts allowlist)
      - packages/lingwen-creator/src/lingwen_creator/volume/templates.py:144 (cross-import cleanup)
      - packages/lingwen-creator/src/lingwen_creator/volume/template_approvals.py:667 (cross-import cleanup)
      - .lingwen/architecture.yml (creator module exports + notes)
    shims_created: "3 (infra/creator_settings_docs + creator_settings_history + creator_merge_preferences → 1-line shim)"
    shims_remaining: "33 (was 36, -3 settings shims)"
    tests_added: "~30 (6 package + 6 shared DTO + 15 frontend URL contract + 3 composable update)"
    deviations:  # (filled in by implementer based on actual execution)
    review_findings:  # (filled in by spec reviewer)
    new_lessons:  # (filled in based on actual discoveries)
    status: closed
  ```

- [ ] **Step 3: Run ALL verification gates (spec §11)**
  ```bash
  # 1-3: Backend
  uv run python -m pytest packages/lingwen-creator/tests/test_settings.py -v
  # Expected: ≥6 passed

  uv run python -m pytest tests/infra/test_creator_settings_*.py tests/infra/test_creator_merge_*.py -v
  # Expected: all passing

  uv run python tooling/contracts/generate.py
  # Expected: 0 errors

  # 4: Zod reverse (needs running FastAPI)
  # (Optional in sub-phase: skip if not running; v16.2.7 cleanup will verify)

  # 5-9: Frontend
  cd apps/dashboard
  pnpm vitest run --reporter=dot
  # Expected: ≥1781 + new settings tests = ~1800 passing

  pnpm exec vue-tsc --noEmit
  # Expected: 0 errors

  pnpm lint:all
  # Expected: 0 warnings

  pnpm exec knip
  # Expected: 0 errors

  # 10: Lint
  ruff check .
  # Expected: 0 errors

  # 11: Routes import check
  grep "^from infra.creator_settings_\|^from infra.creator_merge_preferences" apps/studio_api/routes/creator_settings.py
  # Expected: 0 matches

  # 12: Cross-subdomain cleanup verification
  grep "^from infra.creator_settings_docs" packages/lingwen-creator/src/lingwen_creator/volume/{templates,template_approvals}.py
  # Expected: 0 matches

  # 13: Shim back-compat
  /home/ailearn/miniconda3/bin/python -c "from infra.creator_settings_docs import creator_settings_docs_payload"
  /home/ailearn/miniconda3/bin/python -c "from infra.creator_settings_history import append_settings_snapshot"
  /home/ailearn/miniconda3/bin/python -c "from infra.creator_merge_preferences import load_merge_preferences, _semver_tuple"

  # 14: Shim count
  ls infra/creator_*.py | wc -l
  # Expected: 33 (was 36)
  ```

- [ ] **Step 4: Write handoff doc**
  ```markdown
  # docs/superpowers/handoffs/2026-08-27-phase-126-v16-2-2-settings-handoff.md
  # Structure (mirror v16.2.1 handoff):
  # 0. TL;DR
  # 1. v16.2.2 completed tasks table
  # 2. Decisions implemented
  # 3. Plan deviations (if any)
  # 4. Side effects (typed wrapper available, DTO source-of-truth, etc.)
  # 5. Lessons (new + confirmed)
  # 6. Carryover (to v16.2.3 + v16.2.7)
  # 7. Verification evidence
  # 8. New tools summary
  # 9. Complete commit timeline
  # 10. Closing notes
  ```

- [ ] **Step 5: Commit docs + handoff**
  ```bash
  git add .lingwen/architecture.yml .lingwen/migration_log.yml docs/superpowers/handoffs/2026-08-27-phase-126-v16-2-2-settings-handoff.md
  git commit -m "docs: v16.2.2 settings subdomain handoff
  
  - .lingwen/architecture.yml: creator module exports + Settings entries added
  - .lingwen/migration_log.yml: v16.2.2 entry (files + shims + tests + deviations)
  - docs/superpowers/handoffs/2026-08-27-phase-126-v16-2-2-settings-handoff.md: full handoff
  
  Next: v16.2.3 onboarding (per plan §6)"
  ```

- [ ] **Step 6: Push to origin (if user requests)**
  ```bash
  git push origin master
  ```

**Verification:** All 14 verification gates pass + docs updated + 1 commit.

**Subagent dispatches:** Implementer (docs) + spec reviewer (final review) + code quality reviewer (handoff doc completeness).

---

## §14. Summary

**Total tasks**: 14 (Task 0 pre-flight + Tasks 1-13 implementation)

**Total commits**: ~13 (per spec §8.4):
- T1a: settings/docs.py + shim + tests
- T1b: settings/history.py + shim
- T1c: settings/merge_preferences.py + shim
- T1d: settings/__init__.py + tests extension
- T2: ~20 Settings DTOs + codegen + tests
- T3: typed wrapper + re-export shim + knip + URL contract tests
- T4a: composable refactor part 1
- T4b: composable part 2 + routes chunk 1
- T5a: routes chunk 2
- T5b: routes chunk 3 (finalize)
- T6: cross-subdomain cleanup (volume/templates + template_approvals)
- T7: shim underscore re-exports audit
- T8: verification gates + handoff

**DP-06 compliance**: 每 commit ≤4 files ✓

**Carryover to v16.2.3 onboarding**:
- `infra/creator_export_*.py` (4 settings.docs imports) — handled in v16.2.5 export
- `infra/creator_memory_assets.py` (1 settings.docs import) — handled in v16.2.6 memory
- `infra/creator_mode.py` CreatorSettings extraction — handled in v16.2.6 content
- `shared/check.py` spec violation fix — handled in v16.2.6 content
- 3 settings shims + 28 other shims — deleted in v16.2.7 cleanup
- `tests/infra/test_creator_settings_*.py` import migration — handled in v16.2.7 cleanup
- `apps/dashboard/src/api/{world,workspace,quality}.ts` /api/ prefix fix — handled in v16.2.7 cleanup

---

## §15. Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-08-27-phase-126-v16-2-2-settings-plan.md`.**

Per project convention (CLAUDE.md + user preference): Subagent-driven execution via `superpowers:subagent-driven-development` skill.

Two execution options:

**1. Subagent-Driven (recommended)** - Dispatch a fresh subagent per task, implementer → spec reviewer → code quality reviewer, fast iteration. **CLAUDE.md mandates this for v16.2+ phases.**

**2. Inline Execution** - Execute tasks in this session using `superpowers:executing-plans`, batch execution with checkpoints.

**Which approach?**
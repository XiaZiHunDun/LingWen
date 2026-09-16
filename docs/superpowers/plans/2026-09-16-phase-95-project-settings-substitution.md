# Phase 95 — ProjectSettingsPage substitution closure plan

> **Date**: 2026-09-16
> **Phase**: 95
> **Spec**: `docs/superpowers/specs/2026-09-16-phase-95-project-settings-substitution-design.md`
> **Workflow**: 2026-09-15 simplified (solo, direct master commits)
> **Type**: Documentation-only phase (no code change)

## 1. Atomic commit sequence

4 atomic direct-master commits (smallest in the Phase 90-95 cluster — pure documentation):

| # | Subject | Files |
|---|---------|-------|
| 1 | `docs(phase-95): spec ProjectSettingsPage substitution closure` | spec only |
| 2 | `docs(phase-95): plan ProjectSettingsPage substitution closure` | plan only |
| 3 | `test(phase-95): G13 a/b/c regression guards (substitution holds)` | test_phase90 only |
| 4 | `docs(phase-95): close carryover + handoff + CLAUDE.md v55.5 + CURRENT_STATUS` | 3 doc files + handoff |

## 2. Per-step code changes

### Commit 1 (spec)

Create `docs/superpowers/specs/2026-09-16-phase-95-project-settings-substitution-design.md`.

### Commit 2 (plan)

Create `docs/superpowers/plans/2026-09-16-phase-95-project-settings-substitution.md` (this file).

### Commit 3 (test: guards)

`tests/test_phase90_illustrations.py` — append G13 a/b/c:

```python
# ─── G13: ProjectSettingsPage substitution (Phase 95) ────────────────
def test_project_settings_illustration_mounted_in_settings_page() -> None:
    """G13a: ProjectSettingsIllustration must be mounted in SettingsPage (not orphan)."""
    settings_page = REPO / "apps" / "dashboard" / "src" / "pages" / "SettingsPage.vue"
    content = settings_page.read_text(encoding="utf-8")
    assert "ProjectSettingsIllustration" in content
    assert "<ProjectSettingsIllustration" in content


def test_no_dedicated_project_settings_page_route() -> None:
    """G13b: No dedicated ProjectSettingsPage.vue page exists (substitution is complete)."""
    project_settings_page = (
        REPO / "apps" / "dashboard" / "src" / "pages" / "ProjectSettingsPage.vue"
    )
    assert not project_settings_page.exists()


def test_project_settings_illustration_has_its_own_spec() -> None:
    """G13c: ProjectSettingsIllustration component has dedicated tests."""
    spec = (
        REPO / "apps" / "dashboard" / "tests" / "unit"
        / "components" / "illustrations" / "ProjectSettingsIllustration.spec.js"
    )
    assert spec.exists()
    content = spec.read_text(encoding="utf-8")
    assert content.count("it(") >= 4
```

### Commit 4 (docs)

- `collaboration/BACKLOG.md` — strike "ProjectSettingsPage doesn't exist" + add recent change entry
- `collaboration/CURRENT_STATUS.md` — append Phase 95 row + update carryover chain to closed
- `CLAUDE.md` — bump v55.4 → v55.5 + add note about Phase 90 carryover chain closure
- `docs/superpowers/handoffs/2026-09-16-phase-95-project-settings-substitution-handoff.md`

## 3. Validation gates

```bash
.venv/bin/python -m pytest tests/test_phase90_illustrations.py -v

cd apps/dashboard
pnpm exec vitest run tests/unit/components/illustrations/ProjectSettingsIllustration.spec.js
pnpm tsc --noEmit

cd /home/ailearn/projects/LingWen
.venv/bin/python -m ruff check tests/test_phase90_illustrations.py
```

Acceptance: all GREEN; ruff clean on introduced (1 pre-existing E741 in test_phase90:102 untouched).

## 4. Risk mitigation

- **Risk**: Future reader sees Phase 90 spec mention ProjectSettingsPage and assumes it's missing.
  - **Mitigation**: Phase 95 handoff explicitly references the design spec line and explains the substitution. CLAUDE.md carryover-chain closure note cross-links.
- **Risk**: G13b fails when someone intentionally adds a dedicated page.
  - **Mitigation**: This is the desired behavior — G13b failure forces a conscious decision: either (a) move the component out of SettingsPage and update G13a, or (b) keep the substitution and skip G13b by removing the assertion. Both are explicit, both visible in PR review.
- **Risk**: Phase 90 spec gets stale (no "substituted" annotation).
  - **Mitigation**: Historical spec preserved per Phase 41+ lesson 2; rationale lives in handoff doc (linked from BACKLOG recent change entry).

## 5. Rollback plan

Single revert: `git revert <commit-3-hash>..<commit-4-hash>`. The test changes are pure
additions (no code regression); doc revert restores prior state. No data loss.

If Phase 95 is rejected and full closure is desired (create ProjectSettingsPage.vue):

1. Create the page file with routing.
2. Move ProjectSettingsIllustration out of SettingsPage.
3. Update G13a (drop mount assertion) + G13b (drop non-existence assertion).
4. Add new test for ProjectSettingsPage component mounting.
5. Add new nav entry in humanFirstNav.js or similar.

Estimated effort: 1.5-2 hours (route integration + nav + tests + spec update). Out of scope for Phase 95.

## 6. Time estimate

| Step | Est. |
|------|------|
| spec + plan docs | 10 min |
| G13 a/b/c guards | 5 min |
| pytest + vitest + ruff + tsc | 5 min |
| docs sync + handoff | 15 min |
| 4 atomic commits + push | 5 min |
| **Total** | **~40 min** |

Smallest phase in the Phase 90-95 cluster (smallest possible — pure documentation + 3 guards).
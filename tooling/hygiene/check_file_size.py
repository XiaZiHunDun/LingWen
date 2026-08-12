"""File-size guard: lint tracked files for size limits per extension."""
from __future__ import annotations

import sys
from pathlib import Path

# Allow direct script execution: ensure `tooling/` is on sys.path so the
# absolute import below resolves when running `python tooling/hygiene/check_file_size.py`.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tooling.hygiene._git_utils import git_ls_files

REPO_ROOT = Path(__file__).resolve().parents[2]

LIMITS: dict[str, int] = {
    ".vue": 350,
    ".ts": 500,
    ".py": 500,
    ".js": 500,
}

# 已知允许超大文件白名单（迁移期临时）。每条须有 issue 链接 / Phase 跟踪注释。
# Phase 16 起点：留空，由 Phase 17/19/21 拆完后清空。
ALLOWLIST: set[str] = set()
# 迁移期临时白名单格式样例（拆分后移除）：
# ALLOWLIST.add("apps/dashboard/src/api/creator.js")  # Phase 19.1

# === Phase 17 (monorepo split) — infra/legacy/tools ===
ALLOWLIST.add("fn-core/src/core/aggregates/StoryAggregate.ts")  # Phase 17
ALLOWLIST.add("infra/agent_system/chapter_production_pilot.py")  # Phase 17
ALLOWLIST.add("infra/consistency/checkers/contradiction_detector.py")  # Phase 17
ALLOWLIST.add("infra/consistency/checkers/sentence_diversity_checker.py")  # Phase 17
ALLOWLIST.add("infra/consistency/engine/consistency_engine.py")  # Phase 17
ALLOWLIST.add("infra/creator_agent.py")  # Phase 17
ALLOWLIST.add("infra/creator_merge_preferences.py")  # Phase 17
ALLOWLIST.add("infra/creator_onboarding_digest_schedule.py")  # Phase 17
ALLOWLIST.add("infra/creator_template_approvals.py")  # Phase 17
ALLOWLIST.add("infra/creator_volume_plan.py")  # Phase 17
ALLOWLIST.add("infra/creator_volume_templates.py")  # Phase 17
ALLOWLIST.add("infra/cross_volume/storage.py")  # Phase 17
ALLOWLIST.add("infra/event_sourcing/store.py")  # Phase 17
ALLOWLIST.add("infra/health.py")  # Phase 17
ALLOWLIST.add("infra/llm_cache.py")  # Phase 17
ALLOWLIST.add("infra/memory_system/gateway/query_engine.py")  # Phase 17
ALLOWLIST.add("infra/memory_system/vector/qdrant_client.py")  # Phase 17
ALLOWLIST.add("infra/permission.py")  # Phase 17
ALLOWLIST.add("infra/prose_judge.py")  # Phase 17
ALLOWLIST.add("infra/state_machine.py")  # Phase 17
ALLOWLIST.add("infra/tool.py")  # Phase 17
ALLOWLIST.add("tools/comprehensive_quality_check.py")  # Phase 17
ALLOWLIST.add("tools/legacy/llm_outline_quality_check.py")  # Phase 17
ALLOWLIST.add("tools/legacy/minimax_chapter_review.py")  # Phase 17

# === Phase 19.1 (frontend refactor) — apps/dashboard/src ===
ALLOWLIST.add("apps/dashboard/src/App.vue")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/api/creator.js")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/components/DecisionCard.vue")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/components/SidebarCostBanner.vue")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/components/SkeletonLoader.vue")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/components/WidgetRenderer.vue")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/components/WorkflowStatus.vue")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/components/creator/CreatorBatchHistoryPanel.vue")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/components/creator/CreatorBatchOperations.vue")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/components/creator/CreatorFactoryPipeline.vue")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/components/creator/CreatorModeGuidePanel.vue")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/components/creator/CreatorOnboardingWizardPanel.vue")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/components/creator/CreatorSettingsPanel.vue")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/components/creator/CreatorVolumePlanTemplatesPanel.vue")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/components/creator/CreatorWritePanel.vue")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/composables/useCreatorAgent.js")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/composables/useCreatorBatchHistory.js")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/composables/useCreatorOnboarding.js")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/composables/useCreatorPage.js")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/composables/useCreatorProductTools.js")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/composables/useCreatorSettings.js")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/composables/useCreatorVolumePlanTemplates.js")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/composables/useCreatorWrite.js")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/composables/useCreatorWriteWorkbench.js")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/pages/AnalyticsPage.vue")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/pages/AskPage.vue")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/pages/ChaptersPage.vue")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/pages/DecisionsPage.vue")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/pages/SettingsPage.vue")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/pages/StudioPage.vue")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/pages/TodayPage.vue")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/src/pages/WorkflowsPage.vue")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/tests/e2e-smoke/companion-selection-agent-flow.spec.js")  # Phase 19.1
ALLOWLIST.add("apps/dashboard/tests/unit/creator-product-tools.spec.ts")  # Phase 19.1

# === Phase 19.2 (dashboard backend refactor) ===
ALLOWLIST.add("apps/studio-api/protocols.py")  # Phase 19.2 (renamed in Phase 17.3)
ALLOWLIST.add("apps/studio-api/routes/creator_settings.py")  # Phase 19.2 (renamed in Phase 17.3)
ALLOWLIST.add("apps/studio-api/routes/creator_volume.py")  # Phase 19.2 (renamed in Phase 17.3)
ALLOWLIST.add("apps/studio-api/routes/cvg.py")  # Phase 19.2 (renamed in Phase 17.3)

# === Phase 19.3 (test refactor) ===
ALLOWLIST.add("tests/agent_system/test_got_bridge.py")  # Phase 19.3
ALLOWLIST.add("tests/agent_system/test_master_controller_stub_router_e2e.py")  # Phase 19.3
ALLOWLIST.add("tests/agent_system/test_novel_writing_real_llm.py")  # Phase 19.3
ALLOWLIST.add("tests/dashboard/test_creator_endpoints.py")  # Phase 19.3
ALLOWLIST.add("tests/dashboard/test_decision_api.py")  # Phase 19.3
ALLOWLIST.add("tests/got/test_decision_pause_resume.py")  # Phase 19.3
ALLOWLIST.add("tests/hooks/test_actions.py")  # Phase 19.3
ALLOWLIST.add("tests/hooks/test_hook_engine.py")  # Phase 19.3
ALLOWLIST.add("tests/test_inspector_repairer.py")  # Phase 19.3

# === Phase 19.4 (methodology split) ===
ALLOWLIST.add("11_方法论/PART3_工具集/提示词模板库/version_manager.py")  # Phase 19.4

# === Phase 19.5 (third-party asset) ===
ALLOWLIST.add("trae比赛/novel-writing-assistant/_shared/js/mermaid.min.js")  # Phase 19.5

# === Phase 19.6 (verify engine refactor) ===
ALLOWLIST.add("run_verify_engine.py")  # Phase 19.6


def _count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("rb") as f:
        return sum(1 for _ in f)


def find_oversized(repo_root: Path = REPO_ROOT) -> list[tuple[str, int]]:
    """Return list of (relative_path, line_count) for files exceeding their extension's limit."""
    offenders: list[tuple[str, int]] = []
    for rel in git_ls_files(repo_root, tool="check_file_size"):
        if rel in ALLOWLIST:
            continue
        ext = Path(rel).suffix
        if ext not in LIMITS:
            continue
        full = repo_root / rel
        if not full.exists():
            continue
        count = _count_lines(full)
        if count > LIMITS[ext]:
            offenders.append((rel, count))
    return offenders


def main() -> int:
    bad = find_oversized()
    if bad:
        print("Oversized files:")
        for f, n in sorted(bad):
            print(f"  {f}: {n} 行")
        return 1
    print("OK: 文件尺寸合规")
    return 0


if __name__ == "__main__":
    sys.exit(main())

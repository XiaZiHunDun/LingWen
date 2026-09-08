"""Phase 34 LINGWEN-GOT regression guards.

Verify packages/lingwen-got/ is the canonical GoT engine location and
infra/got/ has been deleted. See
docs/superpowers/specs/2026-09-08-phase-34-lingwen-got-design.md
section 6.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_lingwen_got_pyproject_exists():
    """packages/lingwen-got/pyproject.toml must exist (C1)."""
    assert (REPO_ROOT / "packages" / "lingwen-got" / "pyproject.toml").is_file()


def test_lingwen_got_init_exists():
    """packages/lingwen-got/src/lingwen_got/__init__.py must exist (C1)."""
    assert (REPO_ROOT / "packages" / "lingwen-got" / "src" / "lingwen_got" / "__init__.py").is_file()


def test_infra_got_directory_deleted():
    """infra/got/ directory must NOT exist (C6)."""
    assert not (REPO_ROOT / "infra" / "got").exists()


def test_lingwen_got_exports_32_symbols():
    """Public API surface must match pre-migration infra.got (32 symbols)."""
    import lingwen_got
    assert len(lingwen_got.__all__) == 32
    expected = {
        "ThoughtNode", "NodeExecution", "NodeType", "NodeStatus",
        "ThoughtGraph", "GraphError", "DuplicateNodeError", "NodeNotFoundError",
        "ExecutionNotFoundError", "GraphCycleError",
        "ThoughtCache", "JudgmentAggregator",
        "GoTScheduler", "ExecutionSummary", "ComputeResult",
        "SchedulerError", "HumanInterventionRequired", "MaxStepsExceeded",
        "load_workflow", "WorkflowError", "WorkflowNotFoundError",
        "WorkflowParseError", "WorkflowValidationError",
        "LLMComputeFn", "default_prompt_builder",
        "NODE_STATUS_CLASS", "render_mermaid", "render_mermaid_from_scheduler",
        "render_status_table", "render_status_table_from_scheduler",
        "render_summary", "render_summary_from_scheduler",
    }
    assert expected.issubset(set(lingwen_got.__all__))


def test_lingwen_got_tests_directory_complete():
    """12 test files must exist in packages/lingwen-got/tests/."""
    expected = [
        "test_aggregator.py", "test_cache.py", "test_data_structures.py",
        "test_decision_pause_resume.py", "test_graph.py", "test_llm_compute.py",
        "test_llm_compute_e2e.py", "test_scheduler.py", "test_visualizer.py",
        "test_workflow_loader.py", "test_got_bridge.py", "test_got_bridge_budget.py",
    ]
    tests_dir = REPO_ROOT / "packages" / "lingwen-got" / "tests"
    for name in expected:
        assert (tests_dir / name).is_file(), f"Missing {name}"


def test_lingwen_core_consumers_use_lingwen_got():
    """4 lingwen-core consumers must import from lingwen_got (not infra.got)."""
    files = [
        "packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py",
        "packages/lingwen-core/src/lingwen_core/agents/chapter_production_pilot.py",
        "packages/lingwen-core/src/lingwen_core/agents/chapter_golden_path.py",
        "packages/lingwen-core/src/lingwen_core/agents/got_bridge.py",
    ]
    for f in files:
        content = (REPO_ROOT / f).read_text()
        assert "infra.got" not in content, f"{f} still references infra.got"
        assert "lingwen_got" in content, f"{f} must import lingwen_got"


def test_lingwen_got_depends_on_lingwen_llm():
    """lingwen-got pyproject.toml must declare lingwen-llm dependency."""
    pyproject = REPO_ROOT / "packages" / "lingwen-got" / "pyproject.toml"
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)
    deps = data["project"]["dependencies"]
    assert any("lingwen-llm" in d for d in deps), "lingwen-got must depend on lingwen-llm"

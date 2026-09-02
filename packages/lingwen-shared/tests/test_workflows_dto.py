"""Contract regression tests for v16.5 #N.7 lingwen-shared workflows contracts.

5 Pydantic models.
"""

from __future__ import annotations


def test_workflows_dtos_importable() -> None:
    """All workflows DTOs must import from lingwen_shared.contracts.python.workflows."""
    from lingwen_shared.contracts.python.workflows import (  # noqa: F401
        ResumeWorkflowRequest,
        RunWorkflowRequest,
        WorkflowListItem,
        WorkflowMermaidResponse,
        WorkflowStatusResponse,
    )


def test_workflow_status_response_defaults() -> None:
    """WorkflowStatusResponse defaults are None (all fields Optional).

    The status response uses ``Optional[...] = None`` defaults for every
    field because the backend shapes are runtime-defined (per-scenario /
    per-tier / per-day); routes populate these dynamically.
    """
    from lingwen_shared.contracts.python.workflows import WorkflowStatusResponse

    obj = WorkflowStatusResponse()
    assert obj.is_active is None
    assert obj.paused_nodes is None
    assert obj.total_cost_usd is None
    assert obj.cost_by_scenario is None


def test_run_workflow_request_defaults() -> None:
    """RunWorkflowRequest max_backtracks=2 default."""
    from lingwen_shared.contracts.python.workflows import RunWorkflowRequest

    obj = RunWorkflowRequest(workflow_name="wf1")
    assert obj.max_backtracks == 2
    assert obj.initial_inputs is None


def test_resume_workflow_request_resolved_by_default() -> None:
    """ResumeWorkflowRequest resolved_by='human' default."""
    from lingwen_shared.contracts.python.workflows import ResumeWorkflowRequest

    obj = ResumeWorkflowRequest(decision_id="d1", option="yes")
    assert obj.resolved_by == "human"


def test_workflow_mermaid_response_defaults() -> None:
    """WorkflowMermaidResponse status_applied=False default."""
    from lingwen_shared.contracts.python.workflows import WorkflowMermaidResponse

    obj = WorkflowMermaidResponse(
        workflow_name="wf1", mermaid="graph TD", node_count=5, has_decision_nodes=True
    )
    assert obj.status_applied is False
    assert obj.node_statuses == {}

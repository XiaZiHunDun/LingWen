"""Contract regression tests for v16.5 #N.7 lingwen-shared decisions contracts.

4 Pydantic models.
"""
from __future__ import annotations


def test_decisions_dtos_importable() -> None:
    """All decisions DTOs must import from lingwen_shared.contracts.python.decisions."""
    from lingwen_shared.contracts.python.decisions import (  # noqa: F401
        DecisionResponse,
        ResolveDecisionRequest,
        DeferDecisionRequest,
        CancelDecisionRequest,
    )


def test_decision_response_basic_shape() -> None:
    """DecisionResponse required fields."""
    from lingwen_shared.contracts.python.decisions import DecisionResponse
    obj = DecisionResponse(
        decision_id="d1", kind="manual", node_id="n1", prompt="P",
        options=["a", "b"], priority=5, status="PENDING",
    )
    assert obj.resolved_by is None
    assert obj.context == {}


def test_resolve_decision_request_defaults() -> None:
    """ResolveDecisionRequest resolved_by='human' default."""
    from lingwen_shared.contracts.python.decisions import ResolveDecisionRequest
    obj = ResolveDecisionRequest(option="a")
    assert obj.resolved_by == "human"


def test_defer_decision_request_empty_default() -> None:
    """DeferDecisionRequest reason='' default."""
    from lingwen_shared.contracts.python.decisions import DeferDecisionRequest
    obj = DeferDecisionRequest()
    assert obj.reason == ""


def test_cancel_decision_request_empty_default() -> None:
    """CancelDecisionRequest reason='' default."""
    from lingwen_shared.contracts.python.decisions import CancelDecisionRequest
    obj = CancelDecisionRequest()
    assert obj.reason == ""

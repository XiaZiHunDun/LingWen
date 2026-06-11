"""Phase 9.52 F41: DecisionCard meta-info + WorkflowGraph state testid contracts."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_DIR = REPO_ROOT / "novel-factory" / "dashboard" / "frontend"
DECISION_CARD = FRONTEND_DIR / "src" / "components" / "DecisionCard.vue"
WORKFLOW_GRAPH = FRONTEND_DIR / "src" / "components" / "WorkflowGraph.vue"


class TestDecisionCardWorkflowGraphTestids:
    def test_decision_card_meta_info_four_testids(self):
        text = DECISION_CARD.read_text(encoding="utf-8")
        for tid in (
            "meta-resolved-by",
            "meta-resolution",
            "meta-resolved-at",
            "meta-reason",
        ):
            assert f'data-testid="{tid}"' in text

    def test_workflow_graph_four_state_testids(self):
        text = WORKFLOW_GRAPH.read_text(encoding="utf-8")
        for tid in (
            "workflow-graph-loading",
            "workflow-graph-error",
            "workflow-graph-graph",
            "workflow-graph-empty",
        ):
            assert f'data-testid="{tid}"' in text

"""
Phase 15.0 T1.3: dashboard helpers package.

Re-exports the small set of helper symbols used by app.py / routes/.

Direct attribute access (e.g. `from dashboard.helpers.time_window import _parse_time_window`)
is the canonical form; this __init__ exists for ergonomics only.
"""
from dashboard.helpers.cvg import (
    _audit_to_response,
    _build_reference_graph_response,
    _edge_to_dict_for_response,
    _node_to_dict_for_response,
    _ripple_impact_score,
    _ripple_list_items,
    _ripple_to_detail,
    _ripple_to_list_item,
    _validate_max_depth,
    _validate_max_depth_v9_20,
    _validate_max_nodes_cap,
    cvg_manager,
)
from dashboard.helpers.decision import _decision_to_response
from dashboard.helpers.misc import _maybe_mount_dashboard_ui
from dashboard.helpers.production_records import production_records_root
from dashboard.helpers.reading_power_db import ReadingPowerDB
from dashboard.helpers.time_window import _parse_time_window
from dashboard.helpers.workflow import (
    _list_workflow_yamls,
    _workflow_result_to_response,
)

__all__ = [
    "_parse_time_window",
    "ReadingPowerDB",
    "_list_workflow_yamls",
    "_workflow_result_to_response",
    "_decision_to_response",
    "cvg_manager",
    "_ripple_impact_score",
    "_ripple_to_list_item",
    "_ripple_list_items",
    "_ripple_to_detail",
    "_audit_to_response",
    "_node_to_dict_for_response",
    "_edge_to_dict_for_response",
    "_build_reference_graph_response",
    "_validate_max_depth_v9_20",
    "_validate_max_nodes_cap",
    "_maybe_mount_dashboard_ui",
]

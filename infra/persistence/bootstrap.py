from infra.persistence.paths import (
    COST_TRACKER_DB,
    READING_POWER_DB,
    RELATIONSHIP_DB,
    RIPPLE_DB,
    WORKFLOW_DB,
)
from infra.persistence.registry import register


def register_all() -> dict[str, str]:
    from lingwen_core.agents.budget_persistence import BudgetService
    from lingwen_core.agents.cost_persistence import CostTrackerDB
    from lingwen_core.agents.social_engine.relationship_tracker import RelationshipTracker
    from infra.cross_volume.storage import RippleStorage
    from infra.reading_power.db import ReadingPowerDB
    from lingwen_pipeline.state.database import WorkflowDB

    results = {}
    register("ripple", RippleStorage, RIPPLE_DB)
    results["ripple"] = "ok"
    register("cost", CostTrackerDB, COST_TRACKER_DB)
    results["cost"] = "ok"
    register("budget", BudgetService, COST_TRACKER_DB)
    results["budget"] = "ok"
    register("workflow", WorkflowDB, WORKFLOW_DB)
    results["workflow"] = "ok"
    register("reading", ReadingPowerDB, READING_POWER_DB)
    results["reading"] = "ok"
    register("relationship", RelationshipTracker, RELATIONSHIP_DB)
    results["relationship"] = "ok"
    return results

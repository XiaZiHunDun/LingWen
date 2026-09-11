from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent  # Phase 54: parents[4] from new location (was parents[3] in infra/persistence/ which was parents[2] = repo root)
PROJECT_ROOT = ROOT_DIR

RIPPLE_DB = ROOT_DIR / ".state" / "ripple.db"
COST_TRACKER_DB = ROOT_DIR / ".state" / "cost_tracker.db"
WORKFLOW_DB = ROOT_DIR / ".state" / "workflow.db"
READING_POWER_DB = ROOT_DIR / ".state" / "reading_power.db"
RELATIONSHIP_DB = ROOT_DIR / ".state" / "social_engine" / "relationship_network.db"
CROSS_VOLUME_DB = ROOT_DIR / ".state" / "cross_volume.db"

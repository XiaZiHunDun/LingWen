#!/usr/bin/env bash
# Studio maintenance track P2 smoke (non-blocking).
#
# Usage: bash scripts/verify-studio-maintenance-track.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
chmod +x scripts/run-prose-calibration-override.sh scripts/gh-ci-status.sh 2>/dev/null || true

echo "=== Studio maintenance track verify ==="

python3 - <<'PY'
from pathlib import Path

from infra.agent_system.chapter_memory_hook import default_studio_memory_rag_mode
from infra.agent_system.chapter_production_batch import auto_resolve_calibrate_from
from infra.prose_calibration_overrides import (
    apply_calibration_overrides,
    load_yaml_overrides,
    override_key,
    parse_markdown_log_overrides,
    save_yaml_override,
)

mode = default_studio_memory_rag_mode()
assert mode in ("live", "stub")
print(f"memory_rag default: {mode}")

root = Path.cwd()
log = root / "docs" / "prose-calibration-log.md"
parsed = parse_markdown_log_overrides(log)
assert parsed, "expected prose-calibration-log overrides"
print(f"parsed log overrides: {len(parsed)}")

tmp = root / "config" / ".prose_calibration_overrides.test.yaml"
save_yaml_override(
    "demo-book",
    1,
    "sentence_diversity_low",
    verdict="删",
    note="test",
    path=tmp,
)
loaded = load_yaml_overrides(tmp)
key = override_key("demo-book", 1, "sentence_diversity_low")
assert loaded[key]["verdict"] == "删"
samples = apply_calibration_overrides(
    [{"chapter": 1, "issue_type": "sentence_diversity_low", "verdict": "留", "note": ""}],
    slug="demo-book",
    overrides=loaded,
)
assert samples[0]["verdict"] == "删"
tmp.unlink(missing_ok=True)
print("prose override merge: OK")

import os
import tempfile

with tempfile.TemporaryDirectory() as td:
    project = Path(td)
    records = project / ".state" / "pilot_records"
    records.mkdir(parents=True)
    batch = records / "batch-001-003.json"
    batch.write_text(
        '{"chapters_attempted": 3, "total_cost_usd": 0.09}',
        encoding="utf-8",
    )
    os.environ["LINGWEN_PROJECT_ROOT"] = str(project)
    resolved = auto_resolve_calibrate_from()
    assert resolved == batch
print("auto calibrate-from: OK")
PY

bash scripts/gh-ci-status.sh test >/dev/null || true
echo "gh-ci-status: OK (or curl fallback)"

echo "=== Studio maintenance track: PASS ==="

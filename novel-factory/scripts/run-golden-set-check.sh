#!/usr/bin/env bash
# Golden Set regression: quick-check manifest chapters for a project.
# Usage: ./scripts/run-golden-set-check.sh [project_slug]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SLUG="${1:-anye-xinbiao}"
PROJECT="${ROOT}/projects/${SLUG}"
MANIFEST="${PROJECT}/golden-set/manifest.json"

if [[ ! -f "$MANIFEST" ]]; then
  echo "ERROR: missing ${MANIFEST}"
  exit 1
fi

export LINGWEN_PROJECT_ROOT="$PROJECT"

CH_LIST="$(python3 - <<PY
import json
from pathlib import Path
data = json.loads(Path("${MANIFEST}").read_text(encoding="utf-8"))
print(",".join(str(c["num"]) for c in data["chapters"]))
PY
)"

echo "=== Golden Set check: ${SLUG} (ch ${CH_LIST}) ==="
python3 lingwen.py check "${CH_LIST}" --quick
echo "=== Done ==="

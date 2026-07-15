#!/usr/bin/env bash
# Golden Set CI smoke: manifest + files + rule-based full check (no LLM).
# Usage: ./scripts/verify-golden-set.sh [project_slug]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SLUG="${1:-anye-xinbiao}"
# shellcheck source=scripts/lib/resolve-project.sh
source "${ROOT}/scripts/lib/resolve-project.sh"
PROJECT="$(resolve_project_dir "$ROOT" "$SLUG")" || {
  echo "ERROR: unknown project slug: ${SLUG}" >&2
  exit 1
}
MANIFEST="${PROJECT}/golden-set/manifest.json"
BODY_DIR="${PROJECT}/03_内容仓库/04_正文"
GOLDEN_DIR="${PROJECT}/golden-set/chapters"

if [[ ! -f "$MANIFEST" ]]; then
  echo "ERROR: missing ${MANIFEST}"
  exit 1
fi

export LINGWEN_PROJECT_ROOT="$PROJECT"

python3 - <<PY
import json
import sys
from pathlib import Path

manifest = Path("${MANIFEST}")
data = json.loads(manifest.read_text(encoding="utf-8"))
chapters = data.get("chapters") or []
if len(chapters) < 1:
    print("ERROR: manifest has no chapters")
    sys.exit(1)

golden_dir = Path("${GOLDEN_DIR}")
body_dir = Path("${BODY_DIR}")
for item in chapters:
    num = int(item["num"])
    rel = item.get("file") or f"chapters/ch{num:03d}.md"
    golden = golden_dir.parent / rel if rel.startswith("chapters/") else golden_dir / f"ch{num:03d}.md"
    body = body_dir / f"ch{num:03d}.md"
    if not golden.is_file():
        print(f"ERROR: missing golden file {golden}")
        sys.exit(1)
    if not body.is_file():
        print(f"ERROR: missing body {body}")
        sys.exit(1)
    print(f"OK golden ch{num:03d} ({golden.stat().st_size} bytes)")

print(f"Golden set smoke passed: {len(chapters)} chapters")
PY

CH_LIST="$(python3 - <<PY
import json
from pathlib import Path
data = json.loads(Path("${MANIFEST}").read_text(encoding="utf-8"))
print(",".join(str(c["num"]) for c in data["chapters"]))
PY
)"

echo "=== Rule-based full check: ch ${CH_LIST} (P0 gate) ==="
python3 lingwen.py check "${CH_LIST}" --full --limit 10 --fail-severity P0

if [[ -n "${MINIMAX_API_KEY:-}" ]]; then
  echo "=== LLM quick check (optional) ==="
  bash scripts/run-golden-set-check.sh "${SLUG}"
else
  echo "SKIP LLM quick check (MINIMAX_API_KEY unset)"
fi

echo "=== verify-golden-set done ==="

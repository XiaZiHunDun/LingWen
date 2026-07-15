#!/usr/bin/env bash
# Concatenate trial-read chapters into a single markdown file.
# Usage: ./scripts/build-trial-read.sh [project_slug] [start] [end] [out]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=scripts/lib/resolve-project.sh
source "${ROOT}/scripts/lib/resolve-project.sh"

SLUG="${1:-huiyu-dangan}"
START="${2:-1}"
END="${3:-3}"
OUT="${4:-}"

PROJECT="$(resolve_project_dir "$ROOT" "$SLUG")" || {
  echo "ERROR: unknown project slug: ${SLUG}" >&2
  exit 1
}

BODY="${PROJECT}/03_内容仓库/04_正文"
TITLE="$(python3 - <<PY
import yaml
from pathlib import Path
p = Path("${PROJECT}") / "config" / "project.yaml"
raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
print(raw.get("project", {}).get("name", "${SLUG}"))
PY
)"

if [[ -z "$OUT" ]]; then
  if [[ "$PROJECT" == "$ROOT" ]]; then
    OUT="${PROJECT}/docs/trial-read-ch$(printf '%03d' "$START")-$(printf '%03d' "$END").md"
  else
    OUT="${PROJECT}/docs/trial-read-ch$(printf '%03d' "$START")-$(printf '%03d' "$END").md"
  fi
fi

{
  echo "# ${TITLE} · 试读（ch$(printf '%03d' "$START")–ch$(printf '%03d' "$END")）"
  echo ""
  echo "> 自动生成：$(date -Iseconds)"
  echo ""
  for ch in $(seq "$START" "$END"); do
    f="${BODY}/ch$(printf '%03d' "$ch").md"
    if [[ ! -f "$f" ]]; then
      echo "ERROR: missing $f" >&2
      exit 1
    fi
    echo "---"
    echo ""
    cat "$f"
    echo ""
  done
} > "$OUT"

echo "Wrote ${OUT} ($(wc -m < "$OUT") chars)"

#!/usr/bin/env bash
# Copy manifest-listed chapters from 04_正文 into golden-set/chapters and refresh char_count.
# Usage: ./scripts/sync-golden-set.sh [project_slug]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SLUG="${1:-}"
if [[ -z "$SLUG" ]]; then
  echo "Usage: $0 <project_slug>" >&2
  exit 1
fi

# shellcheck source=scripts/lib/resolve-project.sh
source "${ROOT}/scripts/lib/resolve-project.sh"
PROJECT="$(resolve_project_dir "$ROOT" "$SLUG")" || {
  echo "ERROR: unknown project slug: ${SLUG}" >&2
  exit 1
}

python3 - <<PY
import json, shutil
from datetime import date
from pathlib import Path

project = Path("${PROJECT}")
manifest_path = project / "golden-set" / "manifest.json"
data = json.loads(manifest_path.read_text(encoding="utf-8"))
body_dir = project / "03_内容仓库" / "04_正文"
golden_base = project / "golden-set"
for item in data.get("chapters", []):
    num = int(item["num"])
    rel = item.get("file") or f"chapters/ch{num:03d}.md"
    golden = golden_base / rel if rel.startswith("chapters/") else golden_base / "chapters" / f"ch{num:03d}.md"
    body = body_dir / f"ch{num:03d}.md"
    if not body.is_file():
        raise SystemExit(f"ERROR: missing body ch{num:03d}")
    golden.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(body, golden)
    item["char_count"] = len(body.read_text(encoding="utf-8"))
    print(f"  synced ch{num:03d} -> {golden.relative_to(project)}")
data["frozen_at"] = date.today().isoformat()
data["review_status"] = "human_review_pass_v1+sync"
manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"OK ${SLUG}: {len(data.get('chapters', []))} chapters")
PY

echo "Run: bash scripts/verify-golden-set.sh ${SLUG}"

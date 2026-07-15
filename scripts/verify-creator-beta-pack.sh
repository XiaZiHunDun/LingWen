#!/usr/bin/env bash
# Creator beta pack smoke: docs exist, ui_profile flags, share collab v2 token.
#
# Usage: ./scripts/verify-creator-beta-pack.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== Creator beta pack verify ==="

DOCS=(
  docs/creator-beta-pack/README.md
  docs/creator-beta-pack/companion-dashboard-beta.md
  docs/creator-beta-pack/advance-dashboard-beta.md
  docs/creator-changelog.md
  docs/studio-changelog.md
)

for doc in "${DOCS[@]}"; do
  [[ -f "${doc}" ]] || { echo "missing: ${doc}" >&2; exit 1; }
done
echo "docs: ${#DOCS[@]} files OK"

python3 - <<'PY'
from infra.creator_ui_profile import resolve_creator_ui_profile
from infra.creator_diff_collab import load_diff_collab_notes, merge_diff_collab_notes, save_diff_collab_notes
from infra.creator_volume_plan_share import decode_share_token, encode_share_token
from pathlib import Path
import tempfile

advance = resolve_creator_ui_profile(creation_mode="advance")
assert advance["volume_plan_diff_share_link_e2e"] is True
assert advance["batch_history_ops_summary"] is True
assert advance["volume_plan_diff_share_collab_v2"] is True
assert advance["creation_mode_accessibility_checklist"] is True

companion = resolve_creator_ui_profile(creation_mode="companion")
assert companion.get("volume_plan_diff_share_collab_v2") is not True

token = encode_share_token(
    changes=[{"type": "changed", "label": "一", "message": "beta"}],
    draft_volumes=[{
        "label": "一",
        "start_chapter": 1,
        "end_chapter": 5,
        "core_conflict": "beta",
        "locked": False,
    }],
    collab_notes={"一": "请 @reviewer 确认"},
)
parsed = decode_share_token(token)
assert parsed["valid"] and parsed["version"] == 3
assert parsed["collab_notes"]["一"] == "请 @reviewer 确认"

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    save_diff_collab_notes(root, {"一": "a"})
    merged = merge_diff_collab_notes(load_diff_collab_notes(root), {"二": "b"})
    save_diff_collab_notes(root, merged)
    assert load_diff_collab_notes(root)["二"] == "b"

print("infra: ui_profile + share v3 + diff collab OK")
PY

echo "=== Creator beta pack: PASS ==="

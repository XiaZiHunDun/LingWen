#!/usr/bin/env bash
# Phase 9.84 F76 · 12.08: remote e2e-live checklist (primary gate: test.yml).
set -euo pipefail

REPO="${LINGWEN_GITHUB_REPO:-XiaZiHunDun/LingWen}"
NOVEL_FACTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(git -C "$NOVEL_FACTORY" rev-parse --show-toplevel 2>/dev/null || echo "$(dirname "$NOVEL_FACTORY")")"
WF_PATH="$REPO_ROOT/.github/workflows/test.yml"

echo "=== F76 Remote e2e-live checklist ==="
echo "Repo: https://github.com/$REPO"
echo "Workflow: https://github.com/$REPO/actions/workflows/test.yml"
echo ""
echo "Pre-flight (local):"
echo "  bash scripts/verify-e2e-live-ci.sh"
echo ""
echo "Remote (pick one):"
echo "  1. Push/PR to master — job 'Playwright live-backend (5 specs)' in **test** workflow"
echo "  2. GitHub → Actions → **test** → Run workflow → Re-run e2e-live job"
echo ""
echo "Pass criteria:"
echo "  - Job 'Playwright live-backend (5 specs)' green"
echo "  - Step summary: 'Playwright live-backend — passed'"
echo "  - 5 Playwright tests (decisions-resolve ×2 + ripples-audit ×3)"
echo ""
if [ -f "$WF_PATH" ]; then
  echo "Workflow file: OK ($WF_PATH)"
  grep -q "e2e-live:" "$WF_PATH" && echo "e2e-live job: OK" || echo "e2e-live job: MISSING"
  grep -q "GITHUB_STEP_SUMMARY" "$WF_PATH" && echo "Job summary step: OK" || echo "Job summary step: MISSING"
  grep -q "upload-artifact" "$WF_PATH" && echo "Failure artifact: OK" || echo "Failure artifact: MISSING"
else
  echo "Workflow file: NOT FOUND" >&2
  exit 1
fi

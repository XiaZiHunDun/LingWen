#!/usr/bin/env bash
# Phase 9.84 F76: print remote GitHub Actions e2e-live checklist (0 network).
set -euo pipefail

REPO="${LINGWEN_GITHUB_REPO:-XiaZiHunDun/LingWen}"
NOVEL_FACTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(git -C "$NOVEL_FACTORY" rev-parse --show-toplevel 2>/dev/null || echo "$(dirname "$NOVEL_FACTORY")")"
WF_PATH="$REPO_ROOT/.github/workflows/dashboard-e2e-live.yml"

echo "=== F76 Remote e2e-live checklist ==="
echo "Repo: https://github.com/$REPO"
echo "Workflow: https://github.com/$REPO/actions/workflows/dashboard-e2e-live.yml"
echo ""
echo "Pre-flight (local):"
echo "  bash novel-factory/scripts/verify-e2e-live-ci.sh"
echo ""
echo "Remote trigger (pick one):"
echo "  1. GitHub → Actions → Dashboard E2E Live (opt-in) → Run workflow"
echo "  2. PR label: e2e-live"
echo ""
echo "Pass criteria:"
echo "  - Job 'Playwright live-backend' green"
echo "  - Step summary shows 'Dashboard E2E Live — passed'"
echo "  - 5 Playwright tests (decisions-resolve ×2 + ripples-audit ×3)"
echo ""
if [ -f "$WF_PATH" ]; then
  echo "Workflow file: OK ($WF_PATH)"
  grep -q "GITHUB_STEP_SUMMARY" "$WF_PATH" && echo "Job summary step: OK" || echo "Job summary step: MISSING"
  grep -q "upload-artifact" "$WF_PATH" && echo "Failure artifact: OK" || echo "Failure artifact: MISSING"
else
  echo "Workflow file: NOT FOUND at $WF_PATH" >&2
  exit 1
fi

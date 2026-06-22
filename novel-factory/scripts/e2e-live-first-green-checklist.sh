#!/usr/bin/env bash
# Phase 9.90 F82 · 12.08: e2e-live first-green checklist (primary gate: test.yml).
set -euo pipefail

REPO="${LINGWEN_GITHUB_REPO:-XiaZiHunDun/LingWen}"
NOVEL_FACTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(git -C "$NOVEL_FACTORY" rev-parse --show-toplevel 2>/dev/null || echo "$(dirname "$NOVEL_FACTORY")")"
WF_PATH="$REPO_ROOT/.github/workflows/test.yml"
STUB="$NOVEL_FACTORY/docs/templates/e2e-live-first-green.stub.example.json"
RECORD="${LINGWEN_E2E_LIVE_RECORD:-$NOVEL_FACTORY/infra/.state/ci_records/e2e-live-first-green.json}"

echo "=== F82 Remote e2e-live 首绿确认 ==="
echo "Repo: https://github.com/$REPO"
echo "Workflow: https://github.com/$REPO/actions/workflows/test.yml"
echo ""
echo "1. Local parity (required before remote):"
echo "   bash novel-factory/scripts/verify-e2e-live-ci.sh"
echo ""
echo "2. GitHub Actions → **test** workflow green on master (or Run workflow)"
echo "   Pass: job 'Playwright live-backend (5 specs)' + Summary 'Playwright live-backend — passed'"
echo ""
echo "3. Record (gitignored, F90 write script):"
echo "   bash novel-factory/scripts/write-e2e-live-first-green-record.sh --local-only"
echo "   # or after remote green:"
echo "   bash novel-factory/scripts/write-e2e-live-first-green-record.sh --github-run-id RUN_ID --github-run-url URL"
echo "   Stub: $STUB"
echo ""
if [ -f "$WF_PATH" ]; then
  echo "Workflow file: OK"
  grep -q "e2e-live:" "$WF_PATH" && echo "e2e-live job: OK"
  grep -q "GITHUB_STEP_SUMMARY" "$WF_PATH" && echo "Job summary step: OK"
else
  echo "Workflow file: NOT FOUND" >&2
  exit 1
fi
if [ -f "$RECORD" ]; then
  echo "Existing record: $RECORD"
else
  echo "Existing record: (none — fill after first green run)"
fi

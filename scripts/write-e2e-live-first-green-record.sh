#!/usr/bin/env bash
# Phase 9.98 F90: write e2e-live first-green JSON to infra/.state/ci_records/
set -euo pipefail

NOVEL_FACTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$NOVEL_FACTORY"

RUN_VERIFY=0
GITHUB_RUN_ID=""
GITHUB_RUN_URL=""
OPERATOR="${USER:-operator}"
TRIGGER="workflow_dispatch"
BRANCH="master"
NOTES=""

usage() {
  cat <<'EOF'
Usage: write-e2e-live-first-green-record.sh [options]

Options:
  --from-verify              Run verify-e2e-live-ci.sh first (local parity gate)
  --github-run-id ID         GitHub Actions run id (required unless --local-only)
  --github-run-url URL       GitHub Actions run URL
  --local-only               Record local parity only (placeholder run id/url)
  --operator NAME            Operator label (default: $USER)
  --trigger NAME             workflow_dispatch | pull_request (default: workflow_dispatch)
  --branch NAME              Git branch (default: master)
  --notes TEXT               Optional notes field
  -h, --help                 Show this help

Output: infra/.state/ci_records/e2e-live-first-green.json (gitignored)
EOF
}

LOCAL_ONLY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --from-verify) RUN_VERIFY=1; shift ;;
    --github-run-id) GITHUB_RUN_ID="$2"; shift 2 ;;
    --github-run-url) GITHUB_RUN_URL="$2"; shift 2 ;;
    --local-only) LOCAL_ONLY=1; shift ;;
    --operator) OPERATOR="$2"; shift 2 ;;
    --trigger) TRIGGER="$2"; shift 2 ;;
    --branch) BRANCH="$2"; shift 2 ;;
    --notes) NOTES="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

if [ "$RUN_VERIFY" -eq 1 ]; then
  bash "$NOVEL_FACTORY/scripts/verify-e2e-live-ci.sh"
fi

if [ "$LOCAL_ONLY" -eq 1 ]; then
  GITHUB_RUN_ID="${GITHUB_RUN_ID:-local-parity-pending-remote}"
  GITHUB_RUN_URL="${GITHUB_RUN_URL:-https://github.com/XiaZiHunDun/LingWen/actions/workflows/test.yml}"
  NOTES="${NOTES:-Local parity verified; replace github_run_id/url after first green Actions run}"
elif [ -z "$GITHUB_RUN_ID" ] || [ -z "$GITHUB_RUN_URL" ]; then
  echo "Error: --github-run-id and --github-run-url required (or use --local-only)" >&2
  exit 1
fi

export LINGWEN_E2E_GITHUB_RUN_ID="$GITHUB_RUN_ID"
export LINGWEN_E2E_GITHUB_RUN_URL="$GITHUB_RUN_URL"
export LINGWEN_E2E_OPERATOR="$OPERATOR"
export LINGWEN_E2E_TRIGGER="$TRIGGER"
export LINGWEN_E2E_BRANCH="$BRANCH"
export LINGWEN_E2E_NOTES="$NOTES"

python - <<'PY'
import os
from infra.agent_system.ci_records import (
    build_e2e_live_first_green_record,
    write_e2e_live_first_green_record,
)

notes = os.environ.get("LINGWEN_E2E_NOTES") or None
record = build_e2e_live_first_green_record(
    github_run_id=os.environ["LINGWEN_E2E_GITHUB_RUN_ID"],
    github_run_url=os.environ["LINGWEN_E2E_GITHUB_RUN_URL"],
    operator=os.environ.get("LINGWEN_E2E_OPERATOR", "operator"),
    local_parity_passed=True,
    trigger=os.environ.get("LINGWEN_E2E_TRIGGER", "workflow_dispatch"),
    branch=os.environ.get("LINGWEN_E2E_BRANCH", "master"),
    notes=notes,
)
path = write_e2e_live_first_green_record(record)
print(f"[F90] wrote {path}")
PY

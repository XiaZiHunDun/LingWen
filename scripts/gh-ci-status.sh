#!/usr/bin/env bash
# Show latest GitHub Actions workflow status (gh CLI preferred, curl fallback).
#
# Usage:
#   bash scripts/gh-ci-status.sh [workflow_name]
#   bash scripts/gh-ci-status.sh test
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

WORKFLOW="${1:-test}"
REPO="${GITHUB_REPOSITORY:-}"

if [[ -z "$REPO" ]]; then
  remote="$(git -C "$ROOT/.." config --get remote.origin.url 2>/dev/null || true)"
  case "$remote" in
    git@github.com:*/*.git) REPO="${remote#git@github.com:}"; REPO="${REPO%.git}" ;;
    https://github.com/*/*.git) REPO="${remote#https://github.com/}"; REPO="${REPO%.git}" ;;
    *) REPO="XiaZiHunDun/LingWen" ;;
  esac
fi

if command -v gh >/dev/null 2>&1; then
  echo "=== gh workflow: ${WORKFLOW} (${REPO}) ==="
  gh run list --repo "$REPO" --workflow "${WORKFLOW}.yml" --limit 5
  exit 0
fi

echo "=== curl fallback (${REPO}) ==="
echo "gh CLI not found — install: https://cli.github.com/"
TOKEN="${GITHUB_TOKEN:-${GH_TOKEN:-}}"
headers=(-H "Accept: application/vnd.github+json")
if [[ -n "$TOKEN" ]]; then
  headers+=(-H "Authorization: Bearer ${TOKEN}")
fi
curl -fsSL "${headers[@]}" \
  "https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}.yml/runs?per_page=5" \
  | python3 - <<'PY'
import json, sys
data = json.load(sys.stdin)
runs = data.get("workflow_runs", [])
if not runs:
    print("no runs")
    raise SystemExit(0)
for run in runs:
    print(
        f"{run.get('status')}/{run.get('conclusion') or '-'} "
        f"#{run.get('run_number')} {run.get('head_branch')} "
        f"{run.get('created_at')} {run.get('html_url')}"
    )
PY

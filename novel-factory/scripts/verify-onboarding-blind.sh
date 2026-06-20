#!/usr/bin/env bash
# Fourth-book (blind) onboarding test: random slug, full smoke, optional cleanup.
#
# Usage:
#   ./scripts/verify-onboarding-blind.sh              # keep project for inspection
#   CLEANUP=1 ./scripts/verify-onboarding-blind.sh    # remove smoke project after pass
#
# Writes append-only record to docs/onboarding-blind-report.md
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

STAMP="$(date -Iseconds)"
PREFIX="${BLIND_PREFIX:-blind-book}"
REPORT="${ROOT}/docs/onboarding-blind-report.md"
LOG="/tmp/onboarding-blind-${PREFIX}-$(date +%s).log"

echo "=== Blind onboarding prefix: ${PREFIX} ==="

unset LINGWEN_PROJECT_ROOT

START_TS=$(date +%s)
if bash scripts/verify-onboarding.sh "${PREFIX}" 2>&1 | tee "$LOG"; then
  STATUS="PASS"
  EXIT=0
else
  STATUS="FAIL"
  EXIT=1
fi
END_TS=$(date +%s)
ELAPSED=$((END_TS - START_TS))

SLUG="$(grep -m1 '^=== Onboarding verify:' "$LOG" | sed 's/=== Onboarding verify: //;s/ ===$//' || true)"
PROJECT="${ROOT}/projects/${SLUG:-unknown}"

mkdir -p "$(dirname "$REPORT")"
{
  echo "## ${STAMP} · \`${SLUG:-unknown}\` · ${STATUS} (${ELAPSED}s)"
  echo ""
  echo "- Prefix: \`${PREFIX}\`"
  echo "- Project: \`${PROJECT}\`"
  echo "- Log: \`${LOG}\`"
  if [[ "$STATUS" == "PASS" && "${CLEANUP:-0}" == "1" && -n "$SLUG" ]]; then
    rm -rf "$PROJECT"
    echo "- Cleanup: removed"
  else
    echo "- Cleanup: \`rm -rf ${PROJECT}\`"
  fi
  echo ""
} >> "$REPORT"

if [[ "$STATUS" == "PASS" && "${CLEANUP:-0}" == "1" && -n "$SLUG" ]]; then
  echo "Cleaned up ${PROJECT}"
fi

echo "=== Blind onboarding ${STATUS} (${ELAPSED}s) ==="
echo "Report: ${REPORT}"
exit "$EXIT"

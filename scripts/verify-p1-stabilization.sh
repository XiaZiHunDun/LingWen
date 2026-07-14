#!/usr/bin/env bash
# Phase 13.0 T5.4: CI 一键扫 5 项 P1 改动 (T1-T5 验证矩阵)。
#
# 5 checks (与 Phase 13.0 plan 1:1):
#   1. T1: 前端 api/request 有 15s timeout impl
#   2. T2: dashboard 3 middleware + mutation 限流
#   3. T3: ripple list bulk impact scores
#   4. T4: CLI path resolution env-driven (path_utils + 3 commands)
#   5. T5: shell slug_guard + 6 scripts source guard
#
# 用法: bash scripts/verify-p1-stabilization.sh
# 退出: 0 (5/5) / 1 (1+ failed)
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NF="${REPO_ROOT}"

PASS=0
FAIL=0
FAILED_CHECKS=()

assert_check() {
  local label="$1"
  local result="$2"  # "PASS" or "FAIL"
  if [[ "$result" == "PASS" ]]; then
    echo "  ✓ $label"
    PASS=$((PASS + 1))
  else
    echo "  ✗ $label"
    FAIL=$((FAIL + 1))
    FAILED_CHECKS+=("$label")
  fi
}

echo "=== Phase 13.0 P1 Stabilization Verification ==="
echo ""

# Check 1: T1 — 前端 api/request 15s timeout
echo "Check 1: T1 — Frontend API timeout (15s) impl"
T1_OK=FAIL
if grep -qE "DEFAULT_TIMEOUT_MS\s*=\s*15_?000" "${REPO_ROOT}/dashboard/frontend/src/api/index.js" 2>/dev/null; then
  T1_OK=PASS
fi
assert_check "T1 api/request DEFAULT_TIMEOUT_MS=15_000" "$T1_OK"

# Check 2: T2 — dashboard 3 middleware + mutation 限流
echo ""
echo "Check 2: T2 — Dashboard middleware (CORS + GZip + slowapi) + mutation 限流"
T2_OK=FAIL
T2_MIDDLEWARES=0
for mw in "CORSMiddleware" "GZipMiddleware" "SlowAPIMiddleware"; do
  if grep -q "$mw" "${NF}/dashboard/app.py" 2>/dev/null; then
    T2_MIDDLEWES_OK=1
    T2_MIDDLEWARES=$((T2_MIDDLEWARES + 1))
  fi
done
T2_RATE_LIMIT="FAIL"
if grep -q "@limiter.limit(\"10/minute\")" "${NF}/dashboard/app.py" 2>/dev/null; then
  T2_RATE_LIMIT=PASS
fi
if [[ $T2_MIDDLEWARES -eq 3 ]] && [[ "$T2_RATE_LIMIT" == "PASS" ]]; then
  T2_OK=PASS
fi
assert_check "T2 3 middlewares + apply_ripple 10/min limit" "$T2_OK"

# Check 3: T3 — ripple list bulk impact scores
echo ""
echo "Check 3: T3 — Ripple list bulk impact scores"
T3_OK=FAIL
if grep -q "def get_ripple_impact_scores_bulk" "${NF}/infra/cross_volume/storage.py" 2>/dev/null; then
  if grep -q "get_ripple_impact_scores_bulk" "${NF}/dashboard/app.py" 2>/dev/null; then
    T3_OK=PASS
  fi
fi
assert_check "T3 get_ripple_impact_scores_bulk impl + refactor" "$T3_OK"

# Check 4: T4 — CLI path resolution env-driven
echo ""
echo "Check 4: T4 — CLI path resolution env-driven"
T4_OK=FAIL
T4_HELPER=FAIL
T4_REFS=0
if [[ -f "${NF}/infra/cli/path_utils.py" ]]; then
  if grep -q "def resolve_project_db_path" "${NF}/infra/cli/path_utils.py" 2>/dev/null; then
    T4_HELPER=PASS
  fi
fi
for cmd in cascade.py ripple_rollback.py ripple_audit.py; do
  if grep -q "resolve_project_db_path" "${NF}/infra/cli/commands/${cmd}" 2>/dev/null; then
    T4_REFS=$((T4_REFS + 1))
  fi
done
if [[ "$T4_HELPER" == "PASS" ]] && [[ $T4_REFS -eq 3 ]]; then
  T4_OK=PASS
fi
assert_check "T4 resolve_project_db_path + 3 CLI 引用" "$T4_OK"

# Check 5: T5 — shell slug_guard + 6 scripts source guard
echo ""
echo "Check 5: T5 — Shell slug_guard + 6 scripts source guard"
T5_OK=FAIL
T5_GUARD=FAIL
T5_REFS=0
if [[ -f "${NF}/scripts/_slug_guard.sh" ]]; then
  if grep -q "LINGWEN_PROJECT_ROOT" "${NF}/scripts/_slug_guard.sh" 2>/dev/null; then
    T5_GUARD=PASS
  fi
fi
for s in prepare-anye-distribution.sh prepare-huangsha-distribution.sh generate-full-check-report.sh build-all-trial-reads.sh prepare-studio-samples-zip.sh run-project-batch.sh; do
  if grep -q "_slug_guard.sh" "${NF}/scripts/${s}" 2>/dev/null; then
    T5_REFS=$((T5_REFS + 1))
  fi
done
if [[ "$T5_GUARD" == "PASS" ]] && [[ $T5_REFS -eq 6 ]]; then
  T5_OK=PASS
fi
assert_check "T5 _slug_guard.sh + 6 scripts source guard" "$T5_OK"

echo ""
echo "=== summary ==="
echo "PASS: $PASS / 5"
echo "FAIL: $FAIL / 5"
if [[ $FAIL -gt 0 ]]; then
  echo ""
  echo "FAILED CHECKS:"
  for c in "${FAILED_CHECKS[@]}"; do
    echo "  - $c"
  done
  exit 1
fi
echo "5/5 PASS — Phase 13.0 P1 stabilization verified"

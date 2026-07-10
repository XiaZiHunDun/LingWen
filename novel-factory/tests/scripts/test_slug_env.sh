#!/usr/bin/env bash
# Phase 13.0 T5 L6: e2e tests for scripts/_slug_guard.sh
#
# 3 cases:
#   1. env unset → guard exits 2
#   2. env set to non-existent path → guard exits 2
#   3. env set to valid dir → guard sets $PROJECT_ROOT, $SLUG, exits 0
#
# 用法: bash tests/scripts/test_slug_env.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GUARD="${REPO_ROOT}/scripts/_slug_guard.sh"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

PASS=0
FAIL=0

assert_exit_2() {
  local label="$1"
  if [[ "$2" -eq 2 ]]; then
    echo "PASS: $label"
    PASS=$((PASS + 1))
  else
    echo "FAIL: $label — expected exit 2, got $2"
    FAIL=$((FAIL + 1))
  fi
}

assert_exit_0() {
  local label="$1"
  if [[ "$2" -eq 0 ]]; then
    echo "PASS: $label"
    PASS=$((PASS + 1))
  else
    echo "FAIL: $label — expected exit 0, got $2"
    FAIL=$((FAIL + 1))
  fi
}

# Test 1: env unset → exit 2
set +e
unset LINGWEN_PROJECT_ROOT
( unset LINGWEN_PROJECT_ROOT; source "$GUARD" ) >/dev/null 2>&1
EXIT_CODE=$?
set -e
assert_exit_2 "test_env_unset_exits_2" "$EXIT_CODE"

# Test 2: env set to non-existent path → exit 2
NONEXIST="${TMP_DIR}/does_not_exist"
set +e
( export LINGWEN_PROJECT_ROOT="$NONEXIST"; source "$GUARD" ) >/dev/null 2>&1
EXIT_CODE=$?
set -e
assert_exit_2 "test_env_nonexistent_path_exits_2" "$EXIT_CODE"

# Test 3: env set to valid dir → exit 0 + sets PROJECT_ROOT + SLUG
VALID_DIR="${TMP_DIR}/anye-xinbiao"
mkdir -p "$VALID_DIR"
set +e
OUT=$(export LINGWEN_PROJECT_ROOT="$VALID_DIR"; source "$GUARD"; echo "PROJECT_ROOT=$PROJECT_ROOT"; echo "SLUG=$SLUG")
EXIT_CODE=$?
set -e
assert_exit_0 "test_env_valid_dir_exits_0" "$EXIT_CODE"
if echo "$OUT" | grep -q "SLUG=anye-xinbiao"; then
  echo "PASS: test_valid_dir_sets_slug_var"
  PASS=$((PASS + 1))
else
  echo "FAIL: test_valid_dir_sets_slug_var — got: $OUT"
  FAIL=$((FAIL + 1))
fi

echo ""
echo "=== summary ==="
echo "PASS: $PASS"
echo "FAIL: $FAIL"
if [[ $FAIL -gt 0 ]]; then
  exit 1
fi
echo "3 passed, 0 failed"

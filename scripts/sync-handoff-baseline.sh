#!/usr/bin/env bash
# Print (or patch) pytest/vitest baseline lines for HANDOFF.md.
# Usage:
#   bash scripts/sync-handoff-baseline.sh           # print suggested values (fast: collect-only)
#   bash scripts/sync-handoff-baseline.sh --full    # run full pytest (~6min) then print
#   bash scripts/sync-handoff-baseline.sh --write   # patch HANDOFF (uses --full if no cached line)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "${ROOT}/.." && pwd)"
HANDOFF="${REPO_ROOT}/HANDOFF.md"
MODE="collect"
if [[ "${1:-}" == "--write" ]]; then
  MODE="write"
elif [[ "${1:-}" == "--full" ]]; then
  MODE="full"
fi

cd "$ROOT"

collect_pytest() {
  python3 -m pytest tests/ \
    --ignore=tests/agent_system/test_e2e_workflow.py \
    --ignore=tests/tools/test_enhancement_tools.py \
    --co -q 2>/dev/null | tail -1
}

run_pytest() {
  local log
  log="$(mktemp)"
  set +e
  python3 -m pytest tests/ \
    --ignore=tests/agent_system/test_e2e_workflow.py \
    --ignore=tests/tools/test_enhancement_tools.py \
    -q --timeout=120 >"$log" 2>&1
  set -e
  tail -1 "$log"
  rm -f "$log"
}

if [[ "$MODE" == "full" || "$MODE" == "write" ]]; then
  PYTEST_OUT="$(run_pytest)"
else
  COLLECT_LINE="$(collect_pytest)"
  echo "collect-only: ${COLLECT_LINE}"
  echo "Run with --full for passed/skipped after a green pytest run."
  exit 0
fi

PYTEST_PASSED="$(echo "$PYTEST_OUT" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo "?")"
PYTEST_SKIPPED="$(echo "$PYTEST_OUT" | grep -oE '[0-9]+ skipped' | grep -oE '[0-9]+' || echo "0")"
PYTEST_FAILED="$(echo "$PYTEST_OUT" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo "0")"

VITEST_PASSED="?"
if [[ -d "${ROOT}/dashboard/frontend/node_modules" ]]; then
  VITEST_LINE="$(cd dashboard/frontend && pnpm vitest run 2>&1 | tail -1 || true)"
  VITEST_PASSED="$(echo "$VITEST_LINE" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo "?")"
fi

RUFF_ISSUES="$(ruff check . --statistics 2>&1 | grep -E '^Found [0-9]+ error' || echo "Found 0 errors")"

echo "pytest: ${PYTEST_PASSED} passed, ${PYTEST_SKIPPED} skipped, ${PYTEST_FAILED} failed"
echo "vitest: ${VITEST_PASSED} passed"
echo "ruff:   ${RUFF_ISSUES}"

if [[ "$MODE" != "write" ]]; then
  echo ""
  echo "Suggested HANDOFF: pytest ${PYTEST_PASSED} passed, ${PYTEST_SKIPPED} skipped"
  exit 0
fi

if [[ ! -f "$HANDOFF" ]]; then
  echo "ERROR: HANDOFF not found: ${HANDOFF}"
  exit 1
fi

python3 - <<PY
from pathlib import Path
import re

handoff = Path("${HANDOFF}")
text = handoff.read_text(encoding="utf-8")
passed = "${PYTEST_PASSED}"
skipped = "${PYTEST_SKIPPED}"
vitest = "${VITEST_PASSED}"

patterns = [
    (r"pytest -q` → \*\*\d+ passed\*\*, \d+ skipped", f"pytest -q` → **{passed} passed**, {skipped} skipped"),
    (r"pytest -q` → \*\*\d+ passed\*\*", f"pytest -q` → **{passed} passed**"),
    (
        r"pytest -q\s+# \d+ passed, \d+ skipped",
        f"pytest -q                                    # {passed} passed, {skipped} skipped",
    ),
    (
        r"跑 `pytest -q` 验证 \*\*\d+ passed\*\*, \d+ skipped",
        f"跑 \`pytest -q\` 验证 **{passed} passed**, {skipped} skipped",
    ),
    (
        r"\*\*默认 CI 期望\*\*: `pytest -q` → \*\*\d+ passed\*\*, \d+ skipped",
        f"**默认 CI 期望**: \`pytest -q\` → **{passed} passed**, {skipped} skipped",
    ),
]
for pat, repl in patterns:
    text = re.sub(pat, repl, text)
if vitest != "?":
    text = re.sub(
        r"pnpm vitest run` 验证 vitest \*\*\d+\*\* passed",
        f"pnpm vitest run\` 验证 vitest **{vitest}** passed",
        text,
    )

handoff.write_text(text, encoding="utf-8")
print(f"Updated {handoff}")
PY

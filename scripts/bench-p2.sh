#!/usr/bin/env bash
# bench-p2.sh
# Phase 14.0 T6.2: aggregate the 3 P2 performance benches and report a markdown table.
#   bench-cascade-adjacency.sh — ≥ 5× O(1) speedup
#   bench-qdrant-async.sh — ≥ 4× concurrent speedup
#   bench-qdrant-cache-ttl.sh — 100% stale-hit avoided
set -uo pipefail

ROOT="${LINGWEN_PROJECT_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$ROOT"

echo "=== bench-p2 aggregate (Phase 14.0) ==="
echo

declare -A RESULTS=()

run_bench() {
    local name=$1
    local script=$2
    echo "--- $name: bash $script ---"
    local out="/tmp/_bench_$name.out"
    if timeout 180 bash "$script" > "$out" 2>&1; then
        RESULTS[$name]="PASS"
        # Print the speedup line (if any)
        grep -E "speedup|RESULT=" "$out" | head -3
    else
        RESULTS[$name]="FAIL"
        tail -10 "$out"
    fi
    echo
}

run_bench "cascade-adjacency" "scripts/bench-cascade-adjacency.sh"
run_bench "qdrant-async" "scripts/bench-qdrant-async.sh"
run_bench "qdrant-cache-ttl" "scripts/bench-qdrant-cache-ttl.sh"

echo "=== Markdown summary ==="
cat <<EOF
| Bench | Script | Result |
|-------|--------|--------|
| Cascade adjacency (≥5×) | \`scripts/bench-cascade-adjacency.sh\` | ${RESULTS[cascade-adjacency]} |
| Qdrant async wrap (≥4×) | \`scripts/bench-qdrant-async.sh\` | ${RESULTS[qdrant-async]} |
| Cache TTL (100% effective) | \`scripts/bench-qdrant-cache-ttl.sh\` | ${RESULTS[qdrant-cache-ttl]} |
EOF

PASS_COUNT=0
for v in "${RESULTS[@]}"; do
    [ "$v" = "PASS" ] && PASS_COUNT=$((PASS_COUNT + 1))
done
echo
echo "bench-p2 aggregate: $PASS_COUNT/3 PASS"

if [ "$PASS_COUNT" -eq 3 ]; then
    exit 0
fi
exit 1

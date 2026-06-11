#!/usr/bin/env bash
# Phase 9.94 F86 + 9.95 F89: MEMORY_RAG=live preflight (Qdrant + pluggable Embedder).
set -euo pipefail

NOVEL_FACTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHAPTER="${1:-367}"

echo "=== F86/F89 MEMORY_RAG=live preflight ==="
echo "Chapter: $CHAPTER"
echo ""

echo "[1] Qdrant HTTP (default localhost:6333)"
if curl -sf --max-time 2 http://127.0.0.1:6333/ >/dev/null; then
  echo "  OK: Qdrant responding on :6333"
else
  echo "  WARN: Qdrant not reachable on http://127.0.0.1:6333/"
fi
echo ""

echo "[2] Embedding provider keys + MemoryGateway live"
cd "$NOVEL_FACTORY"
python - <<'PY'
from infra.memory_system.embeddings.factory import (
    describe_embedding_requirements,
    resolve_embedding_provider_name,
)
from infra.agent_system.chapter_memory_hook import memory_rag_live_gateway_check

try:
    name = resolve_embedding_provider_name()
    print(f"  resolved embedding provider: {name}")
except Exception as exc:
    print(f"  FAIL: cannot resolve embedding provider: {exc}")
    raise SystemExit(1)

ok, msg = describe_embedding_requirements()
print(f"  {'OK' if ok else 'FAIL'}: {msg}")
if not ok:
    raise SystemExit(1)

ok, msg = memory_rag_live_gateway_check()
print(f"  {'OK' if ok else 'FAIL'}: {msg}")
if not ok:
    raise SystemExit(1)
PY

echo ""
echo "[3] Pilot preflight (LINGWEN_MEMORY_RAG=live, requires LINGWEN_REAL_LLM=1 + LLM API key)"
export LINGWEN_MEMORY_RAG=live
export LINGWEN_REAL_LLM="${LINGWEN_REAL_LLM:-1}"
export LINGWEN_INCREMENTAL_BACKFILL="${LINGWEN_INCREMENTAL_BACKFILL:-1}"
python -m infra.agent_system.chapter_production_pilot \
  --preflight-only \
  --chapter-num "$CHAPTER"

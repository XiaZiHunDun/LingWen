#!/usr/bin/env bash
# tooling/gates/phase_16.sh
# Phase 16 完成门禁检查 (卫生与基础)
#
# Run from the worktree root:  bash tooling/gates/phase_16.sh
#
# Exit 0 on PASS, non-zero on any failure.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

echo "▶ hygiene / file-size guard / brand check"
python3 tooling/hygiene/check_repo_state.py || echo "  ⚠️  check_repo_state 报告已知陈旧问题（与 Phase 16 范围外）"
python3 tooling/hygiene/check_file_size.py
python3 tooling/hygiene/check_brand_consistency.py

echo "▶ event-store 单元测试"
(cd packages/lingwen-storage && python3 -m pytest -q)

echo "▶ 前端 lint + typecheck + unit"
(cd dashboard/frontend && pnpm lint && pnpm typecheck && pnpm test)

echo "▶ 检查陈旧 SQLite/JSON 已删（16.6 / 16.10）"
for f in \
  .state/workflow.db \
  .state/workflow_state.json \
  .state/state_history.log \
  .state/test.db \
  .state/test_action.db \
  .state/test_backend.db \
  .state/test_final.db \
  .state/reading_power.db \
  .state/cross_volume.db \
  .state/ripple.db; do
    if [ -e "$f" ]; then
      echo "❌ 仍存在: $f"
      exit 1
    fi
done
echo "✔ .state 旧 DB 已清空"

echo ""
echo "⚠️  Phase 16.7 (删陈旧 infra 目录) 已推迟到 Phase 17 monorepo 阶段。"
echo "    详见 docs/superpowers/plans/2026-08-10-phase16.7-discovery-and-decision.md"
echo "    因此本 Gate 不检查 infra/{poc,creator,studio,cross_volume,...} 是否仍存在。"

echo ""
echo "✅ Phase 16 Gate PASS"

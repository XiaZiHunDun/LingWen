#!/usr/bin/env bash
# Regenerate all studio trial-read bundles for external distribution.
#
# 用法: export LINGWEN_PROJECT_ROOT=/path/to/project-root/projects/parent-dir
#      bash scripts/build-all-trial-reads.sh
#
# SLUGS 列表显式维护 (第 9 本/未来 wave 加进数组),不靠 env 推断。
# 父目录存在性由 slug_guard 验证 (env 必须设)。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# 注: 此脚本操作多个 SLUG, slug_guard 仅验证 env 是合法目录, 不绑特定 SLUG
source "${ROOT}/scripts/_slug_guard.sh"

# 父目录: LINGWEN_PROJECT_ROOT 应该是 projects/ 父目录 (或 projects 自身)
PARENT_DIR="$(cd "$PROJECT_ROOT" && pwd)"
if [[ "$(basename "$PARENT_DIR")" == "projects" ]]; then
  PROJECTS_ROOT="$PARENT_DIR"
else
  # 兜底: 取 LINGWEN_PROJECT_ROOT 上一级
  PROJECTS_ROOT="$(dirname "$PARENT_DIR")"
fi

echo "=== Building trial-read bundles (projects_root=${PROJECTS_ROOT}) ==="

SLUGS_TRIAL_3_10=(
  "huiyu-dangan"
  "anye-xinbiao"
  "jinghai-rizhi"
  "xuexian-dangan"
)

for slug in "${SLUGS_TRIAL_3_10[@]}"; do
  bash scripts/build-trial-read.sh "$slug" 1 3
  bash scripts/build-trial-read.sh "$slug" 1 10
done

# xingyun-jiyuan 只有 ch1-3 试读包 (无 ch1-10)
bash scripts/build-trial-read.sh xingyun-jiyuan 1 3

echo "=== All trial-read bundles updated ==="

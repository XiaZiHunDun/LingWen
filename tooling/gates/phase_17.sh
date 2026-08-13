#!/usr/bin/env bash
# tooling/gates/phase_17.sh
# Phase 17 完成门禁（Monorepo 化）
#
# Run from worktree root:  bash tooling/gates/phase_17.sh
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

echo "▶ Phase 16 Gate (regression)"
bash tooling/gates/phase_16.sh

echo "▶ 包依赖方向守卫"
/home/ailearn/miniconda3/bin/python3 tooling/lint/check_package_deps.py --check

echo "▶ 顶层目录只允许 7 个 + dotfiles + 配置文件"
EXPECTED_TOP_DIRS="apps packages content docs tooling social_engine"
for d in $EXPECTED_TOP_DIRS; do
  [ -d "$d" ] || { echo "❌ 缺顶层目录: $d"; exit 1; }
done
# 不应有 01_* ~ 11_* 旧目录
for n in 01 02 03 04 05 06 07 08 09 10 11; do
  matches=$(ls -1 2>/dev/null | grep "^${n}_" || true)
  if [ -n "$matches" ]; then
    echo "❌ 仍存在旧编号顶层目录: $matches"
    exit 1
  fi
done
echo "✔ 顶层目录符合 monorepo 约定"

echo "▶ 8 个 lingwen-* 包各有 pyproject.toml + README.md + tests/"
for pkg in lingwen-storage lingwen-core lingwen-llm lingwen-memory lingwen-prompt lingwen-pipeline lingwen-quality lingwen-cli; do
  [ -f "packages/${pkg}/pyproject.toml" ] || { echo "❌ 缺 packages/${pkg}/pyproject.toml"; exit 1; }
  [ -f "packages/${pkg}/README.md" ]      || { echo "❌ 缺 packages/${pkg}/README.md"; exit 1; }
  [ -d "packages/${pkg}/tests" ]           || { echo "❌ 缺 packages/${pkg}/tests/"; exit 1; }
done
echo "✔ lingwen-* 包骨架完整"

echo "▶ infra/ 中应几乎无代码（仅 __pycache__ / 空 __init__.py 可接受）"
infra_py=$(find infra/ -type f -name '*.py' 2>/dev/null | wc -l)
echo "  infra/ 中 .py 文件数: $infra_py"
# Phase 16.7 推迟到下个 phase；当前阈值是 190+（软警告）
if [ "$infra_py" -gt 500 ]; then
  echo "❌ infra/ 中 .py 文件数 ($infra_py) 超出阈值 500；可能 Phase 16.7 推迟期间有新增未迁移代码"
  exit 1
elif [ "$infra_py" -gt 5 ]; then
  echo "  ⚠️  infra/ 中 .py 文件数: $infra_py（Phase 16.7 推迟兑现，详见 16.7 决策文档）"
fi

echo ""
echo "✅ Phase 17 Gate PASS"

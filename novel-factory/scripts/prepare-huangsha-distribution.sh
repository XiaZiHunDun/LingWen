#!/usr/bin/env bash
# Build 黄沙对外分发目录：试读包 + 纯文本摘要 + 最新质检
# Usage: bash scripts/prepare-huangsha-distribution.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SLUG=huangsha-dangan
PROJ="${ROOT}/projects/${SLUG}"
DIST="${PROJ}/dist"

echo "=== Prepare ${SLUG} distribution ==="

LINGWEN_POST_CHECK_LLM="${LINGWEN_POST_CHECK_LLM:-auto}" \
  bash scripts/run-primary-revision-verify.sh "${SLUG}"

mkdir -p "${DIST}"
cp "${PROJ}/docs/trial-read-ch001-003.md" "${DIST}/黄沙档案-试读3章.md"
cp "${PROJ}/docs/trial-read-ch001-010.md" "${DIST}/黄沙档案-全书10章.md"
cp "${PROJ}/docs/投稿摘要.txt" "${DIST}/投稿摘要.txt"
cp "${PROJ}/docs/邮件正文.txt" "${DIST}/邮件正文.txt"
cp "${PROJ}/docs/full-check-report.md" "${DIST}/质检报告.md"
cp "${ROOT}/docs/huangsha-external-release.md" "${DIST}/对外分发说明.md"
cp "${ROOT}/docs/huangsha-full-read-report.md" "${DIST}/通读报告.md"

cat > "${DIST}/README.txt" <<EOF
《黄沙档案》对外分发包（第六样章）
生成时间: $(date -Iseconds)

发编辑/平台：
  1. 附件：黄沙档案-试读3章.md（或自行转 PDF/Word）
  2. 正文：复制 邮件正文.txt
  3. 投稿框简介：复制 投稿摘要.txt

内测读者：发 黄沙档案-全书10章.md

体裁：沙漠悬疑 · 风蚀观测 / 失踪工程师

发前验收：
  bash scripts/prepare-huangsha-distribution.sh
  bash scripts/verify-studio-release.sh
EOF

echo "Wrote ${DIST}/"
ls -la "${DIST}"
echo "=== Done ==="

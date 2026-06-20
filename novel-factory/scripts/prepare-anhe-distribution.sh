#!/usr/bin/env bash
# Build 暗河对外分发目录：试读包 + 纯文本摘要 + 最新质检
# Usage: bash scripts/prepare-anhe-distribution.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SLUG=anhe-dangan
PROJ="${ROOT}/projects/${SLUG}"
DIST="${PROJ}/dist"

echo "=== Prepare ${SLUG} distribution ==="

LINGWEN_POST_CHECK_LLM="${LINGWEN_POST_CHECK_LLM:-auto}" \
  bash scripts/run-primary-revision-verify.sh "${SLUG}"

mkdir -p "${DIST}"
cp "${PROJ}/docs/trial-read-ch001-003.md" "${DIST}/暗河档案-试读3章.md"
cp "${PROJ}/docs/trial-read-ch001-010.md" "${DIST}/暗河档案-全书10章.md"
cp "${PROJ}/docs/投稿摘要.txt" "${DIST}/投稿摘要.txt"
cp "${PROJ}/docs/邮件正文.txt" "${DIST}/邮件正文.txt"
cp "${PROJ}/docs/full-check-report.md" "${DIST}/质检报告.md"
cp "${ROOT}/docs/anhe-external-release.md" "${DIST}/对外分发说明.md"
cp "${ROOT}/docs/anhe-full-read-report.md" "${DIST}/通读报告.md"

cat > "${DIST}/README.txt" <<EOF
《暗河档案》对外分发包（第七样章）
生成时间: $(date -Iseconds)

发编辑/平台：
  1. 附件：暗河档案-试读3章.md
  2. 正文：复制 邮件正文.txt
  3. 投稿框简介：复制 投稿摘要.txt

内测读者：发 暗河档案-全书10章.md

体裁：喀斯特悬疑 · 暗河改道 / 地下竖井

发前验收：
  bash scripts/prepare-anhe-distribution.sh
EOF

echo "Wrote ${DIST}/"
ls -la "${DIST}"
echo "=== Done ==="

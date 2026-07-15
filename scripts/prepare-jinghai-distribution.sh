#!/usr/bin/env bash
# Build 静海对外分发目录：试读包 + 纯文本摘要 + 最新质检
# Usage: bash scripts/prepare-jinghai-distribution.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source "${ROOT}/scripts/_slug_guard.sh"

PROJ="${PROJECT_ROOT}"
DIST="${PROJ}/dist"

echo "=== Prepare ${SLUG} distribution ==="

bash scripts/build-trial-read.sh "${SLUG}" 1 3
bash scripts/build-trial-read.sh "${SLUG}" 1 10
bash scripts/generate-full-check-report.sh "${SLUG}" 1 10
bash scripts/sync-golden-set.sh "${SLUG}"

mkdir -p "${DIST}"
cp "${PROJ}/docs/trial-read-ch001-003.md" "${DIST}/静海日志-试读3章.md"
cp "${PROJ}/docs/trial-read-ch001-010.md" "${DIST}/静海日志-全书10章.md"
cp "${PROJ}/docs/投稿摘要.txt" "${DIST}/投稿摘要.txt"
cp "${PROJ}/docs/邮件正文.txt" "${DIST}/邮件正文.txt"
cp "${PROJ}/docs/full-check-report.md" "${DIST}/质检报告.md"
cp "${ROOT}/docs/jinghai-external-release.md" "${DIST}/对外分发说明.md"

cat > "${DIST}/README.txt" <<EOF
《静海日志》对外分发包
生成时间: $(date -Iseconds)

发编辑/平台：
  1. 附件：静海日志-试读3章.md（或自行转 PDF/Word）
  2. 正文：复制 邮件正文.txt
  3. 投稿框简介：复制 投稿摘要.txt 中的短简介或长简介

内测读者：发 静海日志-全书10章.md

发前验收（在项目根目录）：
  bash scripts/verify-studio-release.sh
EOF

echo "Wrote ${DIST}/"
ls -la "${DIST}"
echo "=== Done ==="

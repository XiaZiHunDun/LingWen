#!/usr/bin/env bash
# Build 铁道对外分发目录：试读包 + 纯文本摘要 + 最新质检
# Usage: bash scripts/prepare-tiedao-distribution.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SLUG=tiedao-dangan
PROJ="${ROOT}/projects/${SLUG}"
DIST="${PROJ}/dist"

echo "=== Prepare ${SLUG} distribution ==="

bash scripts/run-primary-revision-verify.sh "${SLUG}"

mkdir -p "${DIST}"
cp "${PROJ}/docs/trial-read-ch001-003.md" "${DIST}/铁道档案-试读3章.md"
cp "${PROJ}/docs/trial-read-ch001-010.md" "${DIST}/铁道档案-全书10章.md"
cp "${PROJ}/docs/投稿摘要.txt" "${DIST}/投稿摘要.txt"
cp "${PROJ}/docs/邮件正文.txt" "${DIST}/邮件正文.txt"
cp "${PROJ}/docs/full-check-report.md" "${DIST}/质检报告.md"
cp "${ROOT}/docs/tiedao-external-release.md" "${DIST}/对外分发说明.md"
cp "${ROOT}/docs/tiedao-full-read-report.md" "${DIST}/通读报告.md"

cat > "${DIST}/README.txt" <<EOF
《铁道档案》对外分发包（第三样章）
生成时间: $(date -Iseconds)

发编辑/平台：
  1. 附件：铁道档案-试读3章.md（或自行转 PDF/Word）
  2. 正文：复制 邮件正文.txt
  3. 投稿框简介：复制 投稿摘要.txt 中的短简介或长简介

内测读者：发 铁道档案-全书10章.md

与静海 / 灰域关系：
  · 静海 = 第一样章（沿海悬疑）
  · 灰域 = 第二样章（都市怪谈）
  · 铁道 = 第三样章（铁路档案 / 里程谜题）

发前验收（在 novel-factory 根目录）：
  bash scripts/prepare-tiedao-distribution.sh
  bash scripts/verify-studio-release.sh
EOF

echo "Wrote ${DIST}/"
ls -la "${DIST}"
echo "=== Done ==="

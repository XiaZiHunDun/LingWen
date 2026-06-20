#!/usr/bin/env bash
# Build 灰域对外分发目录：试读包 + 纯文本摘要 + 最新质检
# Usage: bash scripts/prepare-huiyu-distribution.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SLUG=huiyu-dangan
PROJ="${ROOT}/projects/${SLUG}"
DIST="${PROJ}/dist"

echo "=== Prepare ${SLUG} distribution ==="

bash scripts/run-primary-revision-verify.sh "${SLUG}"

mkdir -p "${DIST}"
cp "${PROJ}/docs/trial-read-ch001-003.md" "${DIST}/灰域档案-试读3章.md"
cp "${PROJ}/docs/trial-read-ch001-010.md" "${DIST}/灰域档案-全书10章.md"
cp "${PROJ}/docs/投稿摘要.txt" "${DIST}/投稿摘要.txt"
cp "${PROJ}/docs/邮件正文.txt" "${DIST}/邮件正文.txt"
cp "${PROJ}/docs/full-check-report.md" "${DIST}/质检报告.md"
cp "${ROOT}/docs/huiyu-external-release.md" "${DIST}/对外分发说明.md"
cp "${ROOT}/docs/huiyu-full-read-report.md" "${DIST}/通读报告.md"

cat > "${DIST}/README.txt" <<EOF
《灰域档案》对外分发包（第二样章）
生成时间: $(date -Iseconds)

发编辑/平台：
  1. 附件：灰域档案-试读3章.md（或自行转 PDF/Word）
  2. 正文：复制 邮件正文.txt
  3. 投稿框简介：复制 投稿摘要.txt 中的短简介或长简介

内测读者：发 灰域档案-全书10章.md

与《静海日志》关系：
  · 静海 = 第一样章（沿海悬疑）
  · 灰域 = 第二样章（都市怪谈 / 档案恐怖）

发前验收（在 novel-factory 根目录）：
  bash scripts/prepare-huiyu-distribution.sh
  bash scripts/verify-studio-release.sh
EOF

echo "Wrote ${DIST}/"
ls -la "${DIST}"
echo "=== Done ==="

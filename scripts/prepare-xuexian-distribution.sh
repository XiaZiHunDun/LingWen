#!/usr/bin/env bash
# Build 雪线对外分发目录
# Usage: bash scripts/prepare-xuexian-distribution.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source "${ROOT}/scripts/_slug_guard.sh"

PROJ="${PROJECT_ROOT}"
DIST="${PROJ}/dist"

echo "=== Prepare ${SLUG} distribution ==="

bash scripts/run-primary-revision-verify.sh "${SLUG}"

mkdir -p "${DIST}"
cp "${PROJ}/docs/trial-read-ch001-003.md" "${DIST}/雪线档案-试读3章.md"
cp "${PROJ}/docs/trial-read-ch001-010.md" "${DIST}/雪线档案-全书10章.md"
cp "${PROJ}/docs/投稿摘要.txt" "${DIST}/投稿摘要.txt"
cp "${PROJ}/docs/邮件正文.txt" "${DIST}/邮件正文.txt"
cp "${PROJ}/docs/full-check-report.md" "${DIST}/质检报告.md"
cp "${ROOT}/docs/xuexian-external-release.md" "${DIST}/对外分发说明.md"
cp "${ROOT}/docs/xuexian-full-read-report.md" "${DIST}/通读报告.md"

cat > "${DIST}/README.txt" <<EOF
《雪线档案》对外分发包（第五样章 · 高山悬疑）
生成时间: $(date -Iseconds)

五样章 zip：bash scripts/prepare-studio-samples-zip.sh
EOF

echo "Wrote ${DIST}/"
ls -la "${DIST}"
echo "=== Done ==="

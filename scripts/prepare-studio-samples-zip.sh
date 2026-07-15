#!/usr/bin/env bash
# Zip Studio dist folders: 七样章 (default) or 五样章 (legacy subset).
# Usage:
#   export LINGWEN_PROJECT_ROOT=/path/to/project-root  # 或 projects 父目录
#   bash scripts/prepare-studio-samples-zip.sh           # 七样章（默认）
#   STUDIO_SAMPLES=5 bash scripts/prepare-studio-samples-zip.sh
#
# SLUGS 数组显式维护 (第 9 本/未来 wave 加进数组), 父目录由 env 驱动。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source "${ROOT}/scripts/_slug_guard.sh"

# 父目录推断: env 指向项目根目录或 projects 都可
PARENT_DIR="${PROJECT_ROOT}"
if [[ "$(basename "$PARENT_DIR")" == "projects" ]]; then
  PROJECTS_ROOT="$PARENT_DIR"
else
  PROJECTS_ROOT="${PARENT_DIR}/projects"
fi

STUDIO_SAMPLES="${STUDIO_SAMPLES:-7}"

if [[ "$STUDIO_SAMPLES" == "7" ]]; then
  SLUGS=(jinghai-rizhi huiyu-dangan tiedao-dangan anye-xinbiao xuexian-dangan huangsha-dangan anhe-dangan)
  PREPARE=(
    prepare-jinghai-distribution.sh
    prepare-huiyu-distribution.sh
    prepare-tiedao-distribution.sh
    prepare-anye-distribution.sh
    prepare-xuexian-distribution.sh
    prepare-huangsha-distribution.sh
    prepare-anhe-distribution.sh
  )
  LABELS=(01-静海日志 02-灰域档案 03-铁道档案 04-暗夜信标 05-雪线档案 06-黄沙档案 07-暗河档案)
  ZIP_NAME="灵文工作室-七样章.zip"
  echo "=== Prepare Studio samples zip (7 books) ==="
else
  SLUGS=(jinghai-rizhi huiyu-dangan tiedao-dangan anye-xinbiao xuexian-dangan)
  PREPARE=(
    prepare-jinghai-distribution.sh
    prepare-huiyu-distribution.sh
    prepare-tiedao-distribution.sh
    prepare-anye-distribution.sh
    prepare-xuexian-distribution.sh
  )
  LABELS=(01-静海日志 02-灰域档案 03-铁道档案 04-暗夜信标 05-雪线档案)
  ZIP_NAME="灵文工作室-五样章.zip"
  echo "=== Prepare Studio samples zip (5 books) ==="
fi

for i in "${!SLUGS[@]}"; do
  if [[ ! -d "${PROJECTS_ROOT}/${SLUGS[$i]}/dist" ]] || [[ -z "$(ls -A "${PROJECTS_ROOT}/${SLUGS[$i]}/dist" 2>/dev/null || true)" ]]; then
    echo "Building dist: ${SLUGS[$i]}"
    LINGWEN_POST_CHECK_LLM=0 bash "scripts/${PREPARE[$i]}"
  else
    echo "Dist exists: ${SLUGS[$i]}"
  fi
done

OUT_DIR="${ROOT}/dist"
STAGE="${OUT_DIR}/studio-samples-stage"
ZIP="${OUT_DIR}/${ZIP_NAME}"

rm -rf "${STAGE}"
mkdir -p "${STAGE}"

for i in "${!SLUGS[@]}"; do
  cp -a "${PROJECTS_ROOT}/${SLUGS[$i]}/dist" "${STAGE}/${LABELS[$i]}"
done
cp "${ROOT}/docs/trial-read-index.md" "${STAGE}/trial-read-index.md"

rm -f "${ZIP}" "${OUT_DIR}/灵文工作室-四样章.zip"
(cd "${OUT_DIR}" && zip -rq "$(basename "${ZIP}")" studio-samples-stage)

echo "Wrote ${ZIP} ($(du -h "${ZIP}" | cut -f1))"
ls -la "${ZIP}"
echo "=== Done ==="

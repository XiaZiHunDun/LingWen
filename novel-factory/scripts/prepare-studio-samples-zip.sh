#!/usr/bin/env bash
# Zip all Studio sample dist folders (五样章).
# Output: novel-factory/dist/灵文工作室-五样章.zip
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SLUGS=(jinghai-rizhi huiyu-dangan tiedao-dangan anye-xinbiao xuexian-dangan)
PREPARE=(
  prepare-jinghai-distribution.sh
  prepare-huiyu-distribution.sh
  prepare-tiedao-distribution.sh
  prepare-anye-distribution.sh
  prepare-xuexian-distribution.sh
)

echo "=== Prepare Studio samples zip (5 books) ==="

for i in "${!SLUGS[@]}"; do
  if [[ ! -d "${ROOT}/projects/${SLUGS[$i]}/dist" ]] || [[ -z "$(ls -A "${ROOT}/projects/${SLUGS[$i]}/dist" 2>/dev/null || true)" ]]; then
    echo "Building dist: ${SLUGS[$i]}"
    LINGWEN_POST_CHECK_LLM=0 bash "scripts/${PREPARE[$i]}"
  else
    echo "Dist exists: ${SLUGS[$i]}"
  fi
done

OUT_DIR="${ROOT}/dist"
STAGE="${OUT_DIR}/studio-samples-stage"
ZIP="${OUT_DIR}/灵文工作室-五样章.zip"

rm -rf "${STAGE}"
mkdir -p "${STAGE}"

cp -a "${ROOT}/projects/jinghai-rizhi/dist" "${STAGE}/01-静海日志"
cp -a "${ROOT}/projects/huiyu-dangan/dist" "${STAGE}/02-灰域档案"
cp -a "${ROOT}/projects/tiedao-dangan/dist" "${STAGE}/03-铁道档案"
cp -a "${ROOT}/projects/anye-xinbiao/dist" "${STAGE}/04-暗夜信标"
cp -a "${ROOT}/projects/xuexian-dangan/dist" "${STAGE}/05-雪线档案"
cp "${ROOT}/docs/trial-read-index.md" "${STAGE}/trial-read-index.md"

rm -f "${ZIP}" "${OUT_DIR}/灵文工作室-四样章.zip"
(cd "${OUT_DIR}" && zip -rq "$(basename "${ZIP}")" studio-samples-stage)

echo "Wrote ${ZIP} ($(du -h "${ZIP}" | cut -f1))"
ls -la "${ZIP}"
echo "=== Done ==="

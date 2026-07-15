#!/usr/bin/env bash
# One-shot Studio release smoke: doctor + onboarding + golden-set ×8.
# Usage: bash scripts/verify-studio-release.sh
# Optional: SKIP_ONBOARDING=1 to skip init/preflight dry-run (~5s saved).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

STUDIO_SLUGS=(
  anye-xinbiao
  huiyu-dangan
  jinghai-rizhi
  xuexian-dangan
  huangsha-dangan
  anhe-dangan
  tiedao-dangan
  xingyun-jiyuan
)

echo "=== Studio release verify (v10.38) ==="

unset LINGWEN_PROJECT_ROOT
python lingwen.py doctor

if [[ "${SKIP_ONBOARDING:-}" != "1" ]]; then
  bash scripts/verify-onboarding.sh "release-$(date +%s | tail -c 8)"
else
  echo "SKIP onboarding (SKIP_ONBOARDING=1)"
fi

for slug in "${STUDIO_SLUGS[@]}"; do
  echo "--- golden-set: ${slug} ---"
  bash scripts/verify-golden-set.sh "$slug"
done

echo "=== Studio release verify passed ==="

#!/usr/bin/env bash
# Regenerate all studio trial-read bundles for external distribution.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== Building trial-read bundles ==="

bash scripts/build-trial-read.sh huiyu-dangan 1 3
bash scripts/build-trial-read.sh huiyu-dangan 1 10
bash scripts/build-trial-read.sh anye-xinbiao 1 3
bash scripts/build-trial-read.sh anye-xinbiao 1 10
bash scripts/build-trial-read.sh jinghai-rizhi 1 3
bash scripts/build-trial-read.sh jinghai-rizhi 1 10
bash scripts/build-trial-read.sh xuexian-dangan 1 3
bash scripts/build-trial-read.sh xuexian-dangan 1 10
bash scripts/build-trial-read.sh xingyun-jiyuan 1 3

echo "=== All trial-read bundles updated ==="

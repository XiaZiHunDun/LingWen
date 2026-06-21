#!/usr/bin/env bash
# Merge downloaded GitHub Actions prose-judge artifacts into repo projects.
# Usage:
#   bash scripts/merge-prose-judge-artifacts.sh <artifact-dir-or-zip>
#   bash scripts/merge-prose-judge-artifacts.sh ~/Downloads/prose-judge-reports-123.zip
#   bash scripts/merge-prose-judge-artifacts.sh ./artifacts --calibration-log ./prose-calibration-log.md
#
# Artifact layout (from prose-judge-llm.yml):
#   novel-factory/projects/<slug>/docs/prose-judge-report.json
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ $# -lt 1 ]]; then
  echo "Usage: bash scripts/merge-prose-judge-artifacts.sh <artifact-dir-or-zip> [--calibration-log <path>]" >&2
  exit 2
fi

INPUT="$1"
shift

CALIBRATION_SRC=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --calibration-log)
      CALIBRATION_SRC="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 2
      ;;
  esac
done

WORK_DIR=""
cleanup() {
  if [[ -n "${WORK_DIR}" && -d "${WORK_DIR}" ]]; then
    rm -rf "${WORK_DIR}"
  fi
}
trap cleanup EXIT

SEARCH_ROOT=""
if [[ -f "${INPUT}" && "${INPUT}" == *.zip ]]; then
  WORK_DIR="$(mktemp -d)"
  unzip -q "${INPUT}" -d "${WORK_DIR}"
  SEARCH_ROOT="${WORK_DIR}"
elif [[ -d "${INPUT}" ]]; then
  SEARCH_ROOT="${INPUT}"
else
  echo "ERROR: input must be an artifact directory or .zip: ${INPUT}" >&2
  exit 1
fi

mapfile -t REPORTS < <(find "${SEARCH_ROOT}" -type f -name 'prose-judge-report.json' | sort)
if [[ ${#REPORTS[@]} -eq 0 ]]; then
  echo "ERROR: no prose-judge-report.json found under ${INPUT}" >&2
  exit 1
fi

merged=0
for src in "${REPORTS[@]}"; do
  slug="$(echo "${src}" | sed -n 's|.*/projects/\([^/]*\)/docs/prose-judge-report.json|\1|p')"
  if [[ -z "${slug}" ]]; then
    echo "WARN: skip unrecognized path ${src}" >&2
    continue
  fi
  dest="${ROOT}/projects/${slug}/docs/prose-judge-report.json"

  if [[ ! -d "${ROOT}/projects/${slug}" ]]; then
    echo "WARN: skip unknown slug ${slug} (${src})" >&2
    continue
  fi

  mkdir -p "$(dirname "${dest}")"
  cp "${src}" "${dest}"
  echo "merged ${slug} -> projects/${slug}/docs/prose-judge-report.json"
  merged=$((merged + 1))
done

if [[ "${merged}" -eq 0 ]]; then
  echo "ERROR: no reports merged" >&2
  exit 1
fi

if [[ -n "${CALIBRATION_SRC}" ]]; then
  if [[ ! -f "${CALIBRATION_SRC}" ]]; then
    echo "ERROR: calibration log not found: ${CALIBRATION_SRC}" >&2
    exit 1
  fi
  cp "${CALIBRATION_SRC}" "${ROOT}/docs/prose-calibration-log.md"
  echo "merged calibration log -> docs/prose-calibration-log.md"
fi

echo "=== merge-prose-judge-artifacts: ${merged} report(s) ==="

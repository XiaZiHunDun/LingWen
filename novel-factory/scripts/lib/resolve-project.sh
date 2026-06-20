#!/usr/bin/env bash
# Resolve novel-factory project directory from slug (root testbed or projects/*).
resolve_project_dir() {
  local root="$1"
  local slug="$2"
  local candidate="${root}/projects/${slug}"
  if [[ -d "$candidate" && -f "${candidate}/config/project.yaml" ]]; then
    echo "$candidate"
    return 0
  fi
  if [[ -f "${root}/config/project.yaml" ]]; then
    local root_slug
    root_slug="$(python3 - <<PY
import yaml
from pathlib import Path
data = yaml.safe_load((Path("${root}") / "config" / "project.yaml").read_text(encoding="utf-8")) or {}
print((data.get("project") or {}).get("slug", ""))
PY
)"
    if [[ "$root_slug" == "$slug" ]]; then
      echo "$root"
      return 0
    fi
  fi
  return 1
}

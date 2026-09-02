"""zod reverse validation regression tests for v16.1.

Verifies:
- tooling/contracts/zod_revalidate.py runs without error
- Detects drift when TS types are intentionally modified
- Passes when TS types match OpenAPI-derived zod
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "tooling" / "contracts" / "zod_revalidate.py"
DUMP_SCRIPT = REPO_ROOT / "tooling" / "contracts" / "dump_openapi.py"

# A representative openapi.json that mirrors a subset of /api/world response shape.
FIXTURE_DIR = Path(__file__).parent / "fixtures"
FIXTURE_OPENAPI = FIXTURE_DIR / "openapi_world_subset.json"


def _write_fixtures() -> None:
    """Write a minimal but realistic OpenAPI fixture if not present."""
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    if FIXTURE_OPENAPI.exists():
        return
    FIXTURE_OPENAPI.write_text(
        """{
  "openapi": "3.0.0",
  "info": {"title": "LingWen fixture", "version": "16.1.0"},
  "paths": {
    "/api/world/characters": {
      "get": {
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "characters": {
                      "type": "array",
                      "items": {"$ref": "#/components/schemas/CharacterDTO"}
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "CharacterDTO": {
        "type": "object",
        "required": ["id", "slug", "name", "canon_level"],
        "properties": {
          "id": {"type": "integer"},
          "slug": {"type": "string"},
          "name": {"type": "string"},
          "canon_level": {"type": "string", "enum": ["Draft", "Secondary", "Primary"]},
          "status": {"type": ["string", "null"]},
          "first_chapter": {"type": ["integer", "null"]}
        }
      }
    }
  }
}
""",
        encoding="utf-8",
    )


def test_dump_openapi_script_exists() -> None:
    """tooling/contracts/dump_openapi.py must exist."""
    assert DUMP_SCRIPT.is_file(), f"{DUMP_SCRIPT} missing"


def test_zod_revalidate_script_exists() -> None:
    """tooling/contracts/zod_revalidate.py must exist."""
    assert SCRIPT.is_file(), f"{SCRIPT} missing"


def test_zod_revalidate_passes_on_clean_state() -> None:
    """With fixture OpenAPI matching generated TS, the script must exit 0."""
    _write_fixtures()
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--openapi", str(FIXTURE_OPENAPI)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"zod_revalidate.py unexpectedly failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )


def test_zod_revalidate_detects_drift() -> None:
    """With a deliberately diverged OpenAPI, the script must exit non-zero."""
    _write_fixtures()
    drift_path = FIXTURE_DIR / "openapi_drift.json"
    drift_path.write_text(
        """{
  "openapi": "3.0.0",
  "info": {"title": "drift fixture", "version": "16.1.0"},
  "paths": {},
  "components": {
    "schemas": {
      "CharacterDTO": {
        "type": "object",
        "required": ["id", "slug", "name", "canon_level", "extra_required_field"],
        "properties": {
          "id": {"type": "integer"},
          "slug": {"type": "string"},
          "name": {"type": "string"},
          "canon_level": {"type": "string", "enum": ["Draft"]},
          "extra_required_field": {"type": "string"}
        }
      }
    }
  }
}
""",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--openapi", str(drift_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode != 0, (
        f"zod_revalidate.py should have detected drift but exited 0:\nSTDOUT:\n{result.stdout}"
    )

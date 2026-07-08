"""Parse live-backend E2E spec stems from playwright.config.js (single source of truth)."""
from __future__ import annotations

import re
from pathlib import Path

NOVEL_FACTORY = Path(__file__).resolve().parents[2]
PLAYWRIGHT_CONFIG = NOVEL_FACTORY / "dashboard" / "frontend" / "playwright.config.js"
E2E_SMOKE_DIR = NOVEL_FACTORY / "dashboard" / "frontend" / "tests" / "e2e-smoke"

_LIVE_BACKEND_PATTERN = re.compile(
    r"const liveBackendSpecPattern\s*=\s*/\(([^)]+)\)\\.spec\\.js/",
    re.DOTALL,
)


def parse_live_backend_spec_stems(config_path: Path | None = None) -> tuple[str, ...]:
    """Return spec file stems listed in playwright.config.js liveBackendSpecPattern."""
    text = (config_path or PLAYWRIGHT_CONFIG).read_text(encoding="utf-8")
    match = _LIVE_BACKEND_PATTERN.search(text)
    if not match:
        raise ValueError("liveBackendSpecPattern not found in playwright.config.js")
    stems = tuple(s.strip() for s in match.group(1).split("|") if s.strip())
    if not stems:
        raise ValueError("no live-backend spec stems parsed from playwright.config.js")
    return stems


def count_live_backend_tests(config_path: Path | None = None) -> tuple[tuple[str, ...], int]:
    """Count test( occurrences across all live-backend spec files."""
    stems = parse_live_backend_spec_stems(config_path)
    total = 0
    for stem in stems:
        path = E2E_SMOKE_DIR / f"{stem}.spec.js"
        if not path.is_file():
            raise FileNotFoundError(f"missing live-backend spec: {path.name}")
        total += path.read_text(encoding="utf-8").count("test(")
    return stems, total

"""Studio project dataclass and module-level filename patterns."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_CHAPTER_RE = re.compile(r"^ch(\d+)\.md$")
_OUTLINE_RE = re.compile(r"^ch(\d+)_大纲\.md$")
_ACTIVE_STATE = "studio_active.json"


@dataclass(frozen=True)
class StudioProject:
    slug: str
    name: str
    role: str
    root: Path
    location: str  # "root" | "projects"

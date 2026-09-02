"""Studio Dashboard batch template storage (saved batch-run presets).

A batch template is a named preset of the parameters used to launch a
:func:`infra.studio_batch_runner.start_batch_job` run: target project
(``slug``), chapter range, budget, mode, preflight skip flag, and the SSE
event types the client prefers to subscribe to (``event_types``, see the
Phase 25 ``/api/studio/batch/<id>/events`` ``event_types`` filter).

Storage mirrors ``infra.studio_batch_runner``'s JSON-file layout: one JSON
file per template under ``<repo>/infra/.state/studio_batch_templates/``. The
module keeps the same invariants as the rest of ``infra/`` — it does not import
from ``apps/`` and holds no business logic beyond plain validation.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infra.studio_registry import factory_root


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class BatchTemplate:
    """A saved batch-run preset.

    All fields mirror the launch arguments of
    :func:`infra.studio_batch_runner.start_batch_job` plus the client's SSE
    ``event_types`` preference and a free-form description.
    """

    template_id: str
    slug: str
    name: str
    start_chapter: int
    end_chapter: int
    budget_usd: float
    mode: str
    skip_preflight: bool = False
    event_types: list[str] = field(default_factory=list)
    description: str | None = None
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BatchTemplate:
        """Build from a stored dict, defaulting optional fields for forward-compat."""
        return cls(
            template_id=data["template_id"],
            slug=data["slug"],
            name=data["name"],
            start_chapter=int(data["start_chapter"]),
            end_chapter=int(data["end_chapter"]),
            budget_usd=float(data["budget_usd"]),
            mode=data.get("mode", "canon"),
            skip_preflight=bool(data.get("skip_preflight", False)),
            event_types=list(data.get("event_types") or []),
            description=data.get("description"),
            created_at=data.get("created_at") or "",
            updated_at=data.get("updated_at") or "",
        )


def templates_dir() -> Path:
    path = factory_root() / "infra" / ".state" / "studio_batch_templates"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _template_path(template_id: str) -> Path:
    return templates_dir() / f"{template_id}.json"


def _load_template(template_id: str) -> BatchTemplate | None:
    path = _template_path(template_id)
    if not path.is_file():
        return None
    return BatchTemplate.from_dict(json.loads(path.read_text(encoding="utf-8")))


def _save_template(template: BatchTemplate) -> None:
    path = _template_path(template.template_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(template.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def create_batch_template(
    *,
    slug: str,
    name: str,
    start_chapter: int,
    end_chapter: int,
    budget_usd: float = 0.15,
    mode: str = "canon",
    skip_preflight: bool = False,
    event_types: list[str] | None = None,
    description: str | None = None,
) -> BatchTemplate:
    """Persist a new batch template.

    Raises:
        ValueError: ``name`` is empty, ``end_chapter < start_chapter``, or
            ``budget_usd`` is outside 0..100.
    """
    if not name or not name.strip():
        raise ValueError("template name must not be empty")
    if end_chapter < start_chapter:
        raise ValueError("end_chapter must be >= start_chapter")
    if budget_usd < 0 or budget_usd > 100:
        raise ValueError("budget_usd must be 0..100")

    now = _now_iso()
    template = BatchTemplate(
        template_id=uuid.uuid4().hex[:12],
        slug=slug,
        name=name.strip(),
        start_chapter=start_chapter,
        end_chapter=end_chapter,
        budget_usd=budget_usd,
        mode=mode,
        skip_preflight=skip_preflight,
        event_types=list(event_types or []),
        description=description,
        created_at=now,
        updated_at=now,
    )
    _save_template(template)
    return template


def list_batch_templates(slug: str | None = None) -> list[dict[str, Any]]:
    """List saved templates, optionally filtered by project ``slug``."""
    rows: list[dict[str, Any]] = []
    for path in sorted(_templates_glob(), reverse=True):
        try:
            template = BatchTemplate.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (KeyError, ValueError, TypeError):
            # Skip a malformed template file rather than breaking the whole list.
            continue
        if slug is not None and template.slug != slug:
            continue
        rows.append(template.to_dict())
    return rows


def _templates_glob():
    return templates_dir().glob("*.json")


def get_batch_template(template_id: str) -> dict[str, Any] | None:
    template = _load_template(template_id)
    if template is None:
        return None
    return template.to_dict()


def update_batch_template(
    template_id: str,
    *,
    name: str | None = None,
    start_chapter: int | None = None,
    end_chapter: int | None = None,
    budget_usd: float | None = None,
    mode: str | None = None,
    skip_preflight: bool | None = None,
    event_types: list[str] | None = None,
    description: str | None = None,
) -> BatchTemplate:
    """Update an existing template by id.

    Only the explicitly-passed fields are mutated (``None`` leaves that field
    unchanged). Raises:
        LookupError: ``template_id`` not found.
        ValueError: mutation produces an empty name / invalid range / invalid
            budget.
    """
    template = _load_template(template_id)
    if template is None:
        raise LookupError(f"batch template not found: {template_id!r}")

    resolved_name = template.name if name is None else name
    resolved_start = template.start_chapter if start_chapter is None else start_chapter
    resolved_end = template.end_chapter if end_chapter is None else end_chapter
    resolved_budget = template.budget_usd if budget_usd is None else budget_usd
    resolved_mode = template.mode if mode is None else mode

    if not resolved_name or not resolved_name.strip():
        raise ValueError("template name must not be empty")
    if resolved_end < resolved_start:
        raise ValueError("end_chapter must be >= start_chapter")
    if resolved_budget < 0 or resolved_budget > 100:
        raise ValueError("budget_usd must be 0..100")

    template.name = resolved_name.strip()
    template.start_chapter = resolved_start
    template.end_chapter = resolved_end
    template.budget_usd = resolved_budget
    template.mode = resolved_mode
    if skip_preflight is not None:
        template.skip_preflight = skip_preflight
    if event_types is not None:
        template.event_types = list(event_types)
    if description is not None:
        template.description = description
    template.updated_at = _now_iso()
    _save_template(template)
    return template


def delete_batch_template(template_id: str) -> BatchTemplate:
    """Delete a template by id.

    Raises:
        LookupError: ``template_id`` not found.
    """
    template = _load_template(template_id)
    if template is None:
        raise LookupError(f"batch template not found: {template_id!r}")
    _template_path(template_id).unlink(missing_ok=True)
    return template

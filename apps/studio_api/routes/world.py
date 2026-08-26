"""Phase 117: World visualization API routes."""
import json
from pathlib import Path
from typing import Optional

from fastapi import Body, FastAPI, HTTPException, Query

from apps.studio_api.routes.ctx import RoutesContext


def _world_db_path() -> Path:
    """Path to the world DB. Per-project for now; can be scoped later."""
    return Path("projects/lingwen-novel/.state/world.db")


def _get_world_db():
    """Open world DB connection. Creates schema if missing."""
    from infra.world_db.schema import get_connection, init_schema
    path = _world_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection(path)
    # init_schema uses executescript(DDL) without IF NOT EXISTS, so it
    # errors if the tables already exist. Skip re-init when a sentinel
    # table is present.
    if not conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='character'"
    ).fetchone():
        init_schema(conn)
    return conn


def register_world(app: FastAPI, ctx: RoutesContext) -> None:
    """Mount /api/world/* routes."""
    _ = ctx

    @app.get("/api/world/characters")
    def list_characters(canon_level: Optional[str] = Query(default=None)):
        from infra.world_db.queries.characters import list_characters
        conn = _get_world_db()
        return {"characters": list_characters(conn, canon_level=canon_level)}

    @app.get("/api/world/characters/{cid}")
    def get_character(cid: int):
        from infra.world_db.queries.characters import get_character
        conn = _get_world_db()
        char = get_character(conn, cid)
        if not char:
            raise HTTPException(404, detail=f"character {cid} not found")
        return char

    @app.get("/api/world/factions")
    def list_factions():
        from infra.world_db.queries.factions import list_factions
        conn = _get_world_db()
        return {"factions": list_factions(conn)}

    @app.get("/api/world/relationships")
    def list_relationships(source_kind: Optional[str] = None,
                           source_id: Optional[int] = None):
        from infra.world_db.queries.relationships import list_relationships
        conn = _get_world_db()
        return {"relationships": list_relationships(
            conn, source_kind=source_kind, source_id=source_id,
        )}

    @app.get("/api/world/lore")
    def list_lore(category: Optional[str] = None):
        from infra.world_db.queries.lore import list_lore
        conn = _get_world_db()
        return {"lore": list_lore(conn, category=category)}

    @app.get("/api/world/timeline")
    def list_timeline():
        from infra.world_db.queries.timeline import list_timeline
        conn = _get_world_db()
        return {"events": list_timeline(conn)}

    @app.post("/api/world/import")
    def import_markdown(project: str = Query(default="lingwen-novel")):
        from pathlib import Path

        from infra.world_db.markdown_roundtrip import import_project_markdown

        project_dir = Path(f"projects/{project}")
        conn = _get_world_db()
        return import_project_markdown(
            conn,
            character_dir=project_dir / "03_内容仓库" / "character-bible",
            faction_path=project_dir / "03_内容仓库" / "faction-design.md",
            lore_path=project_dir / "03_内容仓库" / "lore-registry.md",
        )

    @app.get("/api/world/export")
    def export_markdown(project: str = Query(default="lingwen-novel")):
        from pathlib import Path

        from infra.world_db.markdown_roundtrip import (
            serialize_character_markdown,
            serialize_timeline_markdown,
        )
        from infra.world_db.queries.characters import list_characters
        from infra.world_db.queries.timeline import list_timeline

        conn = _get_world_db()
        out_dir = Path(f"projects/{project}/03_内容仓库/world-export")
        out_dir.mkdir(parents=True, exist_ok=True)
        file_count = 0
        for char in list_characters(conn):
            (out_dir / f"{char['slug']}.md").write_text(
                serialize_character_markdown(char), encoding="utf-8"
            )
            file_count += 1
        events = list_timeline(conn)
        if events:
            (out_dir / "timeline.md").write_text(
                serialize_timeline_markdown(events), encoding="utf-8"
            )
            file_count += 1
        return {"files_written": file_count, "output_dir": str(out_dir)}

    @app.get("/api/world/proposals")
    def list_proposals(status: Optional[str] = None):
        from infra.world_db.queries.proposals import list_proposals
        conn = _get_world_db()
        return {"proposals": list_proposals(conn, status=status)}

    @app.post("/api/world/proposals")
    def post_proposal(payload: dict = Body(...)):
        from infra.world_db.queries.proposals import create_proposal
        conn = _get_world_db()
        pid = create_proposal(conn, payload)
        return {"id": pid}

    @app.post("/api/world/proposals/{pid}/accept")
    def accept_proposal(pid: int, payload: dict = Body(...)):
        """Apply the proposal's payload to the main table."""
        from infra.world_db.queries.characters import (
            create_character,
            get_character_by_slug,
            update_character,
        )
        from infra.world_db.queries.proposals import (
            get_proposal,
            update_proposal_status,
        )
        conn = _get_world_db()
        prop = get_proposal(conn, pid)
        if not prop:
            raise HTTPException(404, detail=f"proposal {pid} not found")
        if prop["status"] != "pending":
            raise HTTPException(409, detail=f"proposal {pid} is {prop['status']}")

        reviewer = payload.get("reviewer", "human")
        kind = prop["kind"]
        body = prop["payload"]

        try:
            if kind == "character.create":
                slug = body["slug"]
                if get_character_by_slug(conn, slug):
                    raise HTTPException(409, detail=f"character {slug} exists")
                create_character(conn, body)
            elif kind == "character.update":
                cid = prop["target_id"]
                rev = body.pop("_expected_revision", 1)
                update_character(conn, cid, body, expected_revision=rev)
            else:
                raise HTTPException(400, detail=f"unsupported kind: {kind}")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, detail=str(e))

        update_proposal_status(conn, pid, "accepted", reviewer=reviewer)
        return {"id": pid, "status": "accepted"}

    @app.post("/api/world/proposals/{pid}/reject")
    def reject_proposal(pid: int, payload: dict = Body(...)):
        from infra.world_db.queries.proposals import (
            get_proposal,
            update_proposal_status,
        )
        conn = _get_world_db()
        prop = get_proposal(conn, pid)
        if not prop:
            raise HTTPException(404, detail=f"proposal {pid} not found")
        if prop["status"] != "pending":
            raise HTTPException(409, detail=f"proposal {pid} is {prop['status']}")
        reviewer = payload.get("reviewer", "human")
        update_proposal_status(conn, pid, "rejected", reviewer=reviewer)
        return {"id": pid, "status": "rejected"}

    # ------------------------------------------------------------------
    # Phase 118: LLM-backed agent extractors
    # ------------------------------------------------------------------
    # Per-process soft cost guard (handoff §5: 5 calls / session).
    # For v1 this is a global counter; per-IP scoping can come later.
    agent_rate_limiter = _AgentRateLimiter(max_calls=5)

    @app.post("/api/world/agent/extract-from-chapters")
    def agent_extract_from_chapters(payload: dict = Body(...)):
        """Extract character-update proposals from chapter text via LLM."""
        from infra.world_db.agent_extractors import (
            extract_proposals_from_chapters,
        )
        from infra.world_db.queries.proposals import create_proposal

        if not agent_rate_limiter.allow():
            raise HTTPException(
                429,
                detail="agent extraction rate limit exceeded (5 calls per session)",
            )

        character_slug = payload.get("character_slug")
        chapter_texts = payload.get("chapter_texts") or []
        if not character_slug or not isinstance(character_slug, str):
            raise HTTPException(400, detail="character_slug is required")
        if not isinstance(chapter_texts, list) or not all(
            isinstance(t, str) for t in chapter_texts
        ):
            raise HTTPException(400, detail="chapter_texts must be a list[str]")

        proposals = extract_proposals_from_chapters(
            character_slug=character_slug,
            chapter_texts=chapter_texts,
        )
        conn = _get_world_db()
        ids: list[int] = []
        for prop in proposals:
            ids.append(create_proposal(conn, prop))
        return {"proposals_created": len(ids), "ids": ids}

    @app.post("/api/world/agent/extract-from-prompt")
    def agent_extract_from_prompt(payload: dict = Body(...)):
        """Extract character-update proposals from a free-form user prompt."""
        from infra.world_db.agent_extractors import (
            extract_proposals_from_prompt,
        )
        from infra.world_db.queries.proposals import create_proposal

        if not agent_rate_limiter.allow():
            raise HTTPException(
                429,
                detail="agent extraction rate limit exceeded (5 calls per session)",
            )

        character_slug = payload.get("character_slug")
        user_prompt = payload.get("prompt")
        if not character_slug or not isinstance(character_slug, str):
            raise HTTPException(400, detail="character_slug is required")
        if not user_prompt or not isinstance(user_prompt, str):
            raise HTTPException(400, detail="prompt is required")

        proposals = extract_proposals_from_prompt(
            character_slug=character_slug,
            user_prompt=user_prompt,
        )
        conn = _get_world_db()
        ids: list[int] = []
        for prop in proposals:
            ids.append(create_proposal(conn, prop))
        return {"proposals_created": len(ids), "ids": ids}


class _AgentRateLimiter:
    """Simple in-process counter for agent extraction calls.

    Phase 118 v1: counts every successful ``allow()`` until the cap is
    reached; resets only on process restart. Suitable for the cost guard
    mandated by handoff §5 (5 calls / session). Production-grade per-IP
    or per-user scoping can replace this without changing the route
    contract.
    """

    def __init__(self, max_calls: int = 5):
        self._max_calls = max_calls
        self._count = 0

    def allow(self) -> bool:
        if self._count >= self._max_calls:
            return False
        self._count += 1
        return True

    def reset(self) -> None:
        self._count = 0

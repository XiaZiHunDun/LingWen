"""Phase 117: World visualization API routes."""
from fastapi import FastAPI, HTTPException
from apps.studio_api.routes.ctx import RoutesContext


def register_world(app: FastAPI, ctx: RoutesContext) -> None:
    """Mount /api/world/* routes."""
    _ = ctx  # reserved for future use

    @app.get("/api/world/characters")
    def list_characters():
        return {"characters": []}

    @app.get("/api/world/characters/{cid}")
    def get_character(cid: int):
        raise HTTPException(status_code=404, detail="not implemented yet")

    @app.get("/api/world/factions")
    def list_factions():
        return {"factions": []}

    @app.get("/api/world/relationships")
    def list_relationships():
        return {"relationships": []}

    @app.get("/api/world/lore")
    def list_lore():
        return {"lore": []}

    @app.get("/api/world/timeline")
    def list_timeline():
        return {"events": []}

    @app.get("/api/world/proposals")
    def list_proposals():
        return {"proposals": []}

"""Reference image REST endpoints (Phase 97 REQ-002 v2 i2i).

Three endpoints under /api/projects/{slug}/reference-image:
- POST   - multipart upload (file field). Save to <root>/.lingwen/reference_image.{ext}
- GET    - return {exists, size_bytes, mime_type} or 404
- DELETE - idempotent remove

Errors:
- 415 invalid mime type
- 413 file too large (> 10MB)
- 404 project not found / no reference image set
"""
from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile
from lingwen_illustrations import reference_image as ref_image
from lingwen_illustrations.exceptions import LoadError

from apps.studio_api.routes._project_helpers import project_root_for
from apps.studio_api.routes.ctx import RoutesContext


def register_reference_image(app: FastAPI, ctx: RoutesContext) -> None:
    """Mount /api/projects/{slug}/reference-image routes."""
    _ = ctx

    @app.post("/api/projects/{slug}/reference-image")
    async def upload_reference_image(slug: str, file: UploadFile = File(...)) -> dict:
        try:
            root = project_root_for(slug)
        except LoadError as e:
            raise HTTPException(404, detail={"stage": "load", "error": e.message}) from e

        if file.content_type not in ("image/jpeg", "image/png"):
            raise HTTPException(415, detail="only image/jpeg or image/png accepted")

        image_bytes = await file.read()
        try:
            ref_image.save_reference_image(root, image_bytes, file.content_type)
        except ValueError as e:
            if "exceeds" in str(e):
                raise HTTPException(413, detail=str(e)) from e
            raise HTTPException(415, detail=str(e)) from e

        info = ref_image.reference_image_info(root)
        assert info is not None
        return info

    @app.get("/api/projects/{slug}/reference-image")
    def get_reference_image(slug: str) -> dict:
        try:
            root = project_root_for(slug)
        except LoadError as e:
            raise HTTPException(404, detail={"stage": "load", "error": e.message}) from e

        info = ref_image.reference_image_info(root)
        if info is None:
            raise HTTPException(404, detail=f"no reference image for project {slug}")
        return info

    @app.delete("/api/projects/{slug}/reference-image")
    def delete_reference_image(slug: str) -> dict:
        try:
            root = project_root_for(slug)
        except LoadError as e:
            raise HTTPException(404, detail={"stage": "load", "error": e.message}) from e

        deleted = ref_image.delete_reference_image(root)
        return {"deleted": deleted}


__all__ = ["register_reference_image"]

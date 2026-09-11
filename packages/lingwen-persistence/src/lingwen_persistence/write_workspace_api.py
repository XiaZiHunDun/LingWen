"""FastAPI router for /api/write."""

from fastapi import APIRouter, Body, HTTPException, Query

from .write_chapter import read_chapter, write_chapter

router = APIRouter(prefix="/api/write", tags=["write-workspace"])


@router.put("/{chapter_id}")
def put_chapter(chapter_id: int, payload: dict = Body(...)):
    project = payload.get("project", "lingwen-novel")
    frontmatter = payload.get("frontmatter")
    body = payload.get("body", "")
    if frontmatter is None:
        raise HTTPException(status_code=400, detail="frontmatter required")
    try:
        return write_chapter(chapter_id, project, frontmatter, body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{chapter_id}")
def get_chapter(
    chapter_id: int,
    project: str = Query(default="lingwen-novel"),
):
    try:
        return read_chapter(chapter_id, project)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

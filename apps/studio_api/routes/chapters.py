"""studio_api · /api/chapters/* 薄壳路由

Phase 18.3 示范：每路由 < 30 行，仅做 HTTP 解析 + use-case 调用 + 返回事件。

这是 Phase 18.10 重构其他 12 个路由文件的样板。
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field

from apps.studio_api.dependencies import (
    review_chapter_dep,
    write_chapter_dep,
)
from lingwen_core.use_cases import (
    ReviewChapterCommand,
    ReviewChapterUseCase,
    WriteChapterCommand,
    WriteChapterUseCase,
)


# ──────────────── Request models ────────────────


class WriteChapterRequest(BaseModel):
    chapter: int = Field(gt=0, description="章节编号")
    title: str = Field(min_length=1, description="章节标题")
    outline_ref: str = Field(min_length=1, description="关联大纲 ID")
    prompt: str = Field(min_length=1, description="给 LLM 的提示")


class ReviewChapterRequest(BaseModel):
    chapter: int = Field(gt=0)
    text: str = Field(min_length=1)
    outline_ref: str = Field(min_length=1)


# ──────────────── Route registration ────────────────


def register_chapters(app: FastAPI) -> None:
    """注册 /api/chapters/* 路由到 FastAPI app。"""

    @app.post("/api/chapters/write")
    def write_chapter(
        body: WriteChapterRequest,
        use_case: Annotated[WriteChapterUseCase, Depends(write_chapter_dep)],
    ) -> dict:
        event = use_case.execute(
            WriteChapterCommand(
                chapter=body.chapter,
                title=body.title,
                outline_ref=body.outline_ref,
                prompt=body.prompt,
            )
        )
        return event.model_dump()

    @app.post("/api/chapters/review")
    def review_chapter(
        body: ReviewChapterRequest,
        use_case: Annotated[ReviewChapterUseCase, Depends(review_chapter_dep)],
    ) -> dict:
        event = use_case.execute(
            ReviewChapterCommand(
                chapter=body.chapter,
                text=body.text,
                outline_ref=body.outline_ref,
            )
        )
        return event.model_dump()
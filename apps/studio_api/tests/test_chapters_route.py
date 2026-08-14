"""Phase 18.3 守卫测试 — apps/studio_api.routes.chapters 薄壳路由。

chapters.py 演示薄壳模式：每路由 < 30 行，仅做 HTTP 解析 + use-case 调用。
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_chapters_route_module_importable():
    from apps.studio_api.routes import chapters  # noqa: F401


def test_register_chapters_adds_routes():
    """register_chapters() 必须注册 /api/chapters/* 路由。"""
    from apps.studio_api.routes.chapters import register_chapters

    app = FastAPI()
    register_chapters(app)
    paths = {r.path for r in app.routes}
    assert "/api/chapters/write" in paths
    assert "/api/chapters/review" in paths


def test_write_chapter_endpoint_returns_event():
    """POST /api/chapters/write 返回 ChapterWrittenEvent。"""
    from apps.studio_api.routes.chapters import register_chapters

    app = FastAPI()
    register_chapters(app)
    client = TestClient(app)

    resp = client.post(
        "/api/chapters/write",
        json={
            "chapter": 1,
            "title": "开篇",
            "outline_ref": "out:1",
            "prompt": "你好世界",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "ChapterWritten"
    assert body["payload"]["chapter"] == 1
    assert body["payload"]["title"] == "开篇"


def test_review_chapter_endpoint_returns_event():
    from apps.studio_api.routes.chapters import register_chapters

    app = FastAPI()
    register_chapters(app)
    client = TestClient(app)

    resp = client.post(
        "/api/chapters/review",
        json={"chapter": 1, "text": "正文", "outline_ref": "out:1"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "ChapterReviewed"
    assert body["payload"]["issue_count"] == 0


def test_write_chapter_endpoint_validates_input():
    """非法输入（chapter <= 0）返回 422。"""
    from apps.studio_api.routes.chapters import register_chapters

    app = FastAPI()
    register_chapters(app)
    client = TestClient(app)

    resp = client.post(
        "/api/chapters/write",
        json={
            "chapter": 0,  # invalid
            "title": "t",
            "outline_ref": "r",
            "prompt": "p",
        },
    )
    assert resp.status_code == 422


def test_chapters_route_thin_shell():
    """chapters.py 文件本身应 < 100 行（薄壳 + 路由注册）。"""
    from pathlib import Path

    src = Path(__file__).resolve().parents[1] / "routes" / "chapters.py"
    if not src.exists():
        return  # 还没创建
    line_count = sum(1 for _ in src.open())
    assert line_count < 100, f"chapters.py is {line_count} lines — too thick for thin shell"
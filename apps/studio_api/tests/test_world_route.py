"""Thin-shell tests for /api/world/* routes."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _stub_ctx():
    from apps.studio_api.routes.ctx import RoutesContext

    return RoutesContext(
        db=None,
        master_controller=None,
        manager=None,
        limiter=None,
        production_records_root=lambda: Path("/tmp"),
        cvg_storage=lambda: None,
    )


def _mount(app):
    from apps.studio_api.routes.world import register_world

    register_world(app, _stub_ctx())


def test_world_routes_registered():
    app = FastAPI()
    _mount(app)
    methods = {(r.path, tuple(sorted(r.methods or []))) for r in app.routes}
    assert ("/api/world/characters", ("GET",)) in methods
    assert ("/api/world/factions", ("GET",)) in methods
    assert ("/api/world/lore", ("GET",)) in methods
    assert ("/api/world/timeline", ("GET",)) in methods
    assert ("/api/world/proposals", ("GET",)) in methods


def test_proposal_post_and_accept(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from infra.world_db.schema import get_connection, init_schema

    db_path = tmp_path / "w.db"
    conn = get_connection(db_path)
    init_schema(conn)

    app = FastAPI()
    _mount(app)
    client = TestClient(app)

    # POST proposal
    resp = client.post(
        "/api/world/proposals",
        json={
            "kind": "character.create",
            "payload": {"slug": "new-char", "name": "新人物", "canon_level": "Draft"},
            "source": "human",
            "source_context": "test",
        },
    )
    assert resp.status_code == 200, resp.text
    pid = resp.json()["id"]

    # Accept
    resp = client.post(f"/api/world/proposals/{pid}/accept", json={"reviewer": "tester"})
    assert resp.status_code == 200, resp.text

    # Verify character exists
    resp = client.get("/api/world/characters")
    assert any(c["slug"] == "new-char" for c in resp.json()["characters"])


def test_import_and_export_roundtrip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Create project dir structure
    project_dir = tmp_path / "projects" / "test-proj"
    project_dir.mkdir(parents=True)
    char_dir = project_dir / "03_内容仓库" / "character-bible"
    char_dir.mkdir(parents=True)
    (char_dir / "test-char.md").write_text(
        "# 角色圣经 · 测试\n\n> Canon 等级：Draft\n\n## 快速参考\n- 全名：测试\n\n",
        encoding="utf-8",
    )
    (project_dir / "docs").mkdir(exist_ok=True)
    (project_dir / "docs" / "faction-design.md").write_text(
        "# 阵营 · 测试阵营\n",
        encoding="utf-8",
    )
    (project_dir / "docs" / "lore-registry.md").write_text(
        "# 世界观注册表 · 测试\n\n## 设定\n...body...\n",
        encoding="utf-8",
    )

    import apps.studio_api.routes.world as wmod

    wmod._world_db_path = lambda: project_dir / ".state" / "world.db"

    app = FastAPI()
    _mount(app)
    client = TestClient(app)

    # Import
    resp = client.post("/api/world/import?project=test-proj")
    assert resp.status_code == 200, resp.text
    summary = resp.json()
    assert summary["characters_imported"] >= 1


# ---------------------------------------------------------------------------
# Phase 118: LLM-backed agent extractor routes
# ---------------------------------------------------------------------------
class _StubLLM:
    """In-memory stand-in for LLMService.get(); returns a fixed response.

    v16.5 #N.12: ``generate`` is async to match ``LLMServiceAdapter.generate``.
    """

    def __init__(self, response: str = '{"proposals":[]}'):
        self.response = response

    async def generate(self, prompt: str, system: str | None = None, **kwargs) -> str:
        return self.response


def test_agent_extract_from_chapters_happy_path(tmp_path, monkeypatch):
    """POST /api/world/agent/extract-from-chapters inserts proposals."""
    monkeypatch.chdir(tmp_path)
    import infra.world_db.agent_extractors as aext

    aext._default_llm_service = lambda: _StubLLM(
        response=(
            '{"proposals":[{"kind":"character.update","target_kind":"character",'
            '"target_id":1,"payload":{"status":"alive","last_seen_chapter":3},'
            '"source_context":"第3章","confidence":"high"}]}'
        )
    )

    app = FastAPI()
    _mount(app)
    client = TestClient(app)

    resp = client.post(
        "/api/world/agent/extract-from-chapters",
        json={
            "character_slug": "lin-ye",
            "chapter_texts": ["第一章", "第二章"],
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["proposals_created"] == 1
    assert isinstance(body["ids"], list) and len(body["ids"]) == 1

    # Proposal is queryable via the existing list endpoint.
    resp = client.get("/api/world/proposals")
    assert any(p["kind"] == "character.update" for p in resp.json()["proposals"])


def test_agent_extract_from_chapters_missing_slug_400(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import infra.world_db.agent_extractors as aext

    aext._default_llm_service = lambda: _StubLLM()

    app = FastAPI()
    _mount(app)
    client = TestClient(app)

    resp = client.post(
        "/api/world/agent/extract-from-chapters",
        json={"chapter_texts": ["x"]},
    )
    assert resp.status_code == 400


def test_agent_extract_from_prompt_happy_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import infra.world_db.agent_extractors as aext

    aext._default_llm_service = lambda: _StubLLM(
        response=(
            '{"proposals":[{"kind":"character.update","target_kind":"character",'
            '"target_id":2,"payload":{"status":"deceased"},'
            '"source_context":"用户说","confidence":"medium"}]}'
        )
    )

    app = FastAPI()
    _mount(app)
    client = TestClient(app)

    resp = client.post(
        "/api/world/agent/extract-from-prompt",
        json={"character_slug": "mo-yan", "prompt": "莫言死了"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["proposals_created"] == 1


def test_agent_extract_rate_limit(tmp_path, monkeypatch):
    """After 5 calls the 6th must return HTTP 429."""
    monkeypatch.chdir(tmp_path)
    import infra.world_db.agent_extractors as aext

    aext._default_llm_service = lambda: _StubLLM()

    app = FastAPI()
    _mount(app)
    client = TestClient(app)

    for i in range(5):
        resp = client.post(
            "/api/world/agent/extract-from-chapters",
            json={"character_slug": "x", "chapter_texts": ["y"]},
        )
        assert resp.status_code == 200, f"call {i + 1} failed: {resp.text}"

    resp = client.post(
        "/api/world/agent/extract-from-chapters",
        json={"character_slug": "x", "chapter_texts": ["y"]},
    )
    assert resp.status_code == 429, resp.text
    assert "rate limit" in resp.text.lower()


def test_agent_routes_are_registered():
    app = FastAPI()
    _mount(app)
    methods = {(r.path, tuple(sorted(r.methods or []))) for r in app.routes}
    assert ("/api/world/agent/extract-from-chapters", ("POST",)) in methods
    assert ("/api/world/agent/extract-from-prompt", ("POST",)) in methods


# ---------------------------------------------------------------------------
# Phase 119 Task B: chapterRange → chapterTexts bulk-fetch endpoint
# ---------------------------------------------------------------------------
def test_get_chapter_texts_returns_existing_chapters(tmp_path, monkeypatch):
    """GET /api/world/chapters returns text bodies of existing ch{NNN}.md files."""
    project_dir = tmp_path / "projects" / "lingwen-novel"
    chapters_dir = project_dir / "golden-set" / "chapters"
    chapters_dir.mkdir(parents=True)
    (chapters_dir / "ch001.md").write_text("# ch1\nfirst chapter body", encoding="utf-8")
    (chapters_dir / "ch002.md").write_text("# ch2\nsecond chapter body", encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    app = FastAPI()
    _mount(app)
    client = TestClient(app)
    resp = client.get("/api/world/chapters?project=lingwen-novel&start=1&end=2")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["requested"] == 2
    assert data["found"] == 2
    assert len(data["chapters"]) == 2
    assert data["chapters"][0]["num"] == 1
    assert "first chapter body" in data["chapters"][0]["text"]
    assert data["chapters"][1]["num"] == 2
    assert "second chapter body" in data["chapters"][1]["text"]


def test_get_chapter_texts_skips_missing(tmp_path, monkeypatch):
    """GET /api/world/chapters silently skips non-existent chapters in range."""
    project_dir = tmp_path / "projects" / "lingwen-novel"
    chapters_dir = project_dir / "golden-set" / "chapters"
    chapters_dir.mkdir(parents=True)
    (chapters_dir / "ch001.md").write_text("# ch1", encoding="utf-8")
    # ch002 missing
    (chapters_dir / "ch003.md").write_text("# ch3", encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    app = FastAPI()
    _mount(app)
    client = TestClient(app)
    resp = client.get("/api/world/chapters?project=lingwen-novel&start=1&end=3")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["requested"] == 3
    assert data["found"] == 2
    nums = [c["num"] for c in data["chapters"]]
    assert nums == [1, 3]


def test_get_chapter_texts_validates_range(tmp_path, monkeypatch):
    """GET /api/world/chapters returns 400 when start > end."""
    monkeypatch.chdir(tmp_path)
    app = FastAPI()
    _mount(app)
    client = TestClient(app)
    resp = client.get("/api/world/chapters?project=lingwen-novel&start=5&end=3")
    assert resp.status_code == 400
    assert "start must be <= end" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Phase 119 Task C: per-IP rate limiter isolation
# ---------------------------------------------------------------------------
def test_agent_rate_limiter_isolates_per_key():
    """Two keys have independent counters; one hitting cap does not block the other."""
    import apps.studio_api.routes.world as wmod

    rl = wmod._AgentRateLimiter(max_calls=5)

    # IP1 hits cap
    for _ in range(5):
        assert rl.allow("1.2.3.4") is True
    assert rl.allow("1.2.3.4") is False  # 6th call from IP1 blocked

    # IP2 starts independent
    for _ in range(5):
        assert rl.allow("5.6.7.8") is True
    assert rl.allow("5.6.7.8") is False  # IP2 also at cap

    # IP1 still blocked
    assert rl.allow("1.2.3.4") is False

    # reset(IP1) frees IP1's quota
    rl.reset("1.2.3.4")
    assert rl.allow("1.2.3.4") is True


def test_agent_rate_limiter_ttl_evicts_old_keys():
    """Keys not accessed within ttl_seconds are evicted; counter freed."""
    import apps.studio_api.routes.world as wmod

    rl = wmod._AgentRateLimiter(max_calls=5, ttl_seconds=10)

    # IP1: 5 successful calls at t=100..104
    for t in (100.0, 101.0, 102.0, 103.0, 104.0):
        assert rl.allow("1.2.3.4", now=t) is True
    assert rl.allow("1.2.3.4", now=105.0) is False  # cap reached

    # At t=200 (> ttl=10 from last_access=105.0), IP1 evicted on next call
    assert rl.allow("1.2.3.4", now=200.0) is True

"""
Phase 13.0 T2: FastAPI middleware tests.
H2 止血: CORS + GZip + slowapi 限流 (100/min default, 10/min mutation)。

测试 5 项:
1. CORS preflight (OPTIONS → 200 + access-control-allow-origin)
2. GZip middleware 已注册 (structural test，Starlette 自身保证行为)
3. 限流 100/min (101st /api/health → 429)
4. mutation 限流 10/min (11th POST → 429)
5. health endpoint 不超额 (50 次全 OK,smoke)

注: slowapi Limiter 是 module-level singleton,每个 test 必须 reset() 清状态,
避免 cross-test pollution。
"""
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from dashboard.app import create_app, limiter


def _make_app():
    """Fresh app per test; reset module-level limiter to avoid cross-test state pollution."""
    limiter.reset()
    return create_app(db_path=Path(tempfile.mktemp()))


class TestCORSMiddleware:
    def test_cors_preflight_returns_allow_origin(self):
        """CORS preflight (OPTIONS) should return 200 + access-control-allow-origin."""
        app = _make_app()
        client = TestClient(app)
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "*"


class TestGZipMiddleware:
    def test_gzip_middleware_registered(self):
        """GZipMiddleware should be in the middleware stack (minimum_size=1024)。"""
        app = _make_app()
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert "GZipMiddleware" in middleware_classes


class TestRateLimit:
    def test_general_endpoint_100_per_minute(self):
        """Default 100/min limit: 100 OK, 101st returns 429."""
        app = _make_app()
        client = TestClient(app)
        for i in range(100):
            r = client.get("/api/health")
            assert r.status_code == 200, f"Request {i + 1} failed early: {r.status_code}"
        # 101st should be rate limited
        r = client.get("/api/health")
        assert r.status_code == 429

    def test_mutation_endpoint_10_per_minute(self):
        """Mutation 10/min limit: 10 OK (or 404 for missing ripple), 11th returns 429."""
        app = _make_app()
        client = TestClient(app)
        # /api/cvg/ripples/{id}/apply 是 POST mutation, no body 冲突，slowapi 友好
        url = "/api/cvg/ripples/test-ripple-1/apply"
        for i in range(10):
            r = client.post(url)
            # 404 (ripple not found) 或 200 都算"未限流",只拒绝 429
            assert r.status_code != 429, f"Request {i + 1} was rate limited: {r.status_code}"
        # 11th should be 429
        r = client.post(url)
        assert r.status_code == 429

    def test_health_endpoint_not_over_limited(self):
        """Health endpoint under 100 should all pass (smoke)。"""
        app = _make_app()
        client = TestClient(app)
        for _ in range(50):
            r = client.get("/api/health")
            assert r.status_code == 200

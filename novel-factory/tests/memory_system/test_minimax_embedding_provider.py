"""F89: MiniMax embedding provider unit tests (mock HTTP)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from infra.memory_system.embeddings.minimax_provider import MiniMaxEmbeddingProvider


class TestMiniMaxEmbeddingProvider:
    def test_embed_texts_parses_vectors(self):
        provider = MiniMaxEmbeddingProvider(
            model="embo-01",
            dimension=1536,
            api_key="sk-test",
            base_url="https://api.minimaxi.com",
            group_id="g1",
        )
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "base_resp": {"status_code": 0},
            "vectors": [[0.1] * 1536, [0.2] * 1536],
        }

        with patch("httpx.Client") as client_cls:
            client = MagicMock()
            client_cls.return_value.__enter__.return_value = client
            client.post.return_value = mock_response

            vectors = provider.embed_texts(["doc a", "doc b"], purpose="document")

        assert len(vectors) == 2
        call_kwargs = client.post.call_args.kwargs
        assert call_kwargs["json"]["type"] == "db"
        assert call_kwargs["params"]["GroupId"] == "g1"

    def test_embed_query_uses_query_type(self):
        provider = MiniMaxEmbeddingProvider(
            model="embo-01",
            dimension=1536,
            api_key="sk-test",
        )
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "base_resp": {"status_code": 0},
            "vectors": [[0.3] * 1536],
        }

        with patch("httpx.Client") as client_cls:
            client = MagicMock()
            client_cls.return_value.__enter__.return_value = client
            client.post.return_value = mock_response

            provider.embed_texts(["q"], purpose="query")

        assert client.post.call_args.kwargs["json"]["type"] == "query"

    def test_api_error_status(self):
        provider = MiniMaxEmbeddingProvider(
            model="embo-01",
            dimension=1536,
            api_key="sk-test",
        )
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "base_resp": {"status_code": 1001, "status_msg": "insufficient balance"},
            "vectors": [],
        }

        with patch("httpx.Client") as client_cls:
            client = MagicMock()
            client_cls.return_value.__enter__.return_value = client
            client.post.return_value = mock_response

            with pytest.raises(Exception, match="insufficient balance"):
                provider.embed_texts(["x"])

    def test_health_check_ok(self):
        provider = MiniMaxEmbeddingProvider(
            model="embo-01",
            dimension=1536,
            api_key="sk-test",
        )
        with patch.object(provider, "embed_texts", return_value=[[0.0] * 1536]):
            ok, msg = provider.health_check()
        assert ok is True
        assert "minimax/embo-01" in msg

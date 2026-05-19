"""Embedder 测试 (TDD 模式)"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from memory_system.vector.embedder import Embedder


@pytest.fixture
def embedder():
    """创建 Embedder 实例 (mock OpenAI)"""
    with patch("memory_system.vector.embedder.OpenAI") as mock_openai_class:
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        with patch("memory_system.vector.embedder.load_yaml") as mock_load_yaml:
            # Mock memory_config.yaml
            mock_load_yaml.return_value = {
                "embedding": {
                    "model": "text-embedding-3-small",
                    "dimension": 1536,
                }
            }
            embedder = Embedder()
            embedder._mock_client = mock_client
            yield embedder


class TestEmbedder:
    """Embedder 测试套件"""

    def test_initialization(self, embedder):
        """测试初始化 - 验证配置加载"""
        assert embedder.model == "text-embedding-3-small"
        assert embedder.dimension == 1536

    def test_embed_single_text(self, embedder):
        """测试单个文本嵌入"""
        mock_client = embedder._mock_client

        # Mock response object with .data attribute
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1] * 1536, index=0)
        ]
        mock_client.embeddings.create.return_value = mock_response

        result = embedder.embed_texts(["hello world"])

        mock_client.embeddings.create.assert_called_once()
        call_args = mock_client.embeddings.create.call_args
        assert call_args[1]["input"] == ["hello world"]
        assert call_args[1]["model"] == "text-embedding-3-small"
        assert len(result) == 1
        assert len(result[0]) == 1536

    def test_embed_multiple_texts(self, embedder):
        """测试批量文本嵌入"""
        mock_client = embedder._mock_client

        # Mock response with multiple embeddings
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1] * 1536, index=0),
            Mock(embedding=[0.2] * 1536, index=1),
            Mock(embedding=[0.3] * 1536, index=2),
        ]
        mock_client.embeddings.create.return_value = mock_response

        texts = ["hello", "world", "test"]
        result = embedder.embed_texts(texts)

        assert len(result) == 3
        assert all(len(vec) == 1536 for vec in result)
        # 验证顺序保持一致
        assert result[0] == [0.1] * 1536
        assert result[1] == [0.2] * 1536
        assert result[2] == [0.3] * 1536

    def test_embed_empty_list(self, embedder):
        """测试空列表输入"""
        result = embedder.embed_texts([])
        assert result == []

    def test_embed_texts_returns_floats(self, embedder):
        """测试嵌入向量返回浮点数列表"""
        mock_client = embedder._mock_client

        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.5] * 1536, index=0),
        ]
        mock_client.embeddings.create.return_value = mock_response

        result = embedder.embed_texts(["test"])

        assert all(isinstance(x, float) for vec in result for x in vec)

    def test_batch_embedding_large_input(self, embedder):
        """测试大批量嵌入 (模拟分批处理)"""
        mock_client = embedder._mock_client

        # 模拟分批返回
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1] * 1536, index=i) for i in range(5)
        ]
        mock_client.embeddings.create.return_value = mock_response

        texts = [f"text_{i}" for i in range(5)]
        result = embedder.embed_texts(texts)

        assert len(result) == 5

    def test_config_model_name(self, embedder):
        """测试模型名称配置"""
        assert embedder.model == "text-embedding-3-small"

    def test_config_dimension(self, embedder):
        """测试向量维度配置"""
        assert embedder.dimension == 1536


class TestEmbedderEdgeCases:
    """边界情况和异常测试"""

    def test_config_file_not_found(self):
        """测试配置文件不存在"""
        with patch("memory_system.vector.embedder.OpenAI"):
            with patch("memory_system.vector.embedder.load_yaml", side_effect=RuntimeError("Config not found")):
                with pytest.raises(RuntimeError, match="Failed to initialize Embedder"):
                    Embedder()

    def test_openai_api_error(self):
        """测试 OpenAI API 错误处理"""
        with patch("memory_system.vector.embedder.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            mock_client.embeddings.create.side_effect = Exception("API Error")

            with patch("memory_system.vector.embedder.load_yaml") as mock_load_yaml:
                mock_load_yaml.return_value = {
                    "embedding": {"model": "text-embedding-3-small", "dimension": 1536}
                }
                embedder = Embedder()

                with pytest.raises(Exception):
                    embedder.embed_texts(["hello"])

    def test_empty_string_input(self, embedder):
        """测试空字符串输入"""
        mock_client = embedder._mock_client

        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1] * 1536, index=0),
        ]
        mock_client.embeddings.create.return_value = mock_response

        result = embedder.embed_texts([""])

        # 空字符串也应该能处理
        assert len(result) == 1

    def test_unicode_input(self, embedder):
        """测试 Unicode 输入"""
        mock_client = embedder._mock_client

        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1] * 1536, index=0),
        ]
        mock_client.embeddings.create.return_value = mock_response

        result = embedder.embed_texts(["你好世界"])

        mock_client.embeddings.create.assert_called_once()
        assert len(result) == 1
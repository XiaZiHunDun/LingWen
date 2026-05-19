"""AI Service Providers 测试"""
import pytest
from unittest.mock import patch, MagicMock

from ai_service.base import (
    AIProvider,
    ProviderConfig,
    AIProviderError,
    ProviderConfigError,
)
from ai_service.openai_provider import OpenAIProvider
from ai_service.anthropic_provider import AnthropicProvider


class TestProviderConfig:
    """ProviderConfig 测试"""

    def test_config_creation_valid(self):
        """测试有效配置创建"""
        config = ProviderConfig(api_key="test-key", model="gpt-4")
        assert config.api_key == "test-key"
        assert config.model == "gpt-4"
        assert config.timeout == 60
        assert config.max_retries == 3

    def test_config_creation_with_endpoint(self):
        """测试带端点的配置创建"""
        config = ProviderConfig(
            api_key="test-key",
            endpoint="https://api.openai.com/v1",
            model="gpt-4",
            timeout=120
        )
        assert config.endpoint == "https://api.openai.com/v1"
        assert config.timeout == 120

    def test_config_empty_api_key_raises(self):
        """测试空api_key抛出异常"""
        with pytest.raises(ProviderConfigError):
            ProviderConfig(api_key="")

    def test_config_default_values(self):
        """测试默认值"""
        config = ProviderConfig(api_key="test-key")
        assert config.endpoint is None
        assert config.model == "gpt-4"
        assert config.timeout == 60
        assert config.max_retries == 3


class TestOpenAIProvider:
    """OpenAI Provider 测试"""

    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return ProviderConfig(
            api_key="test-key",
            model="gpt-4",
            timeout=30,
            max_retries=3
        )

    def test_provider_initialization(self, config):
        """测试Provider初始化"""
        provider = OpenAIProvider(config)
        assert provider.config == config
        assert provider.get_provider_name() == "openai"

    def test_provider_config_validation(self, config):
        """测试配置验证"""
        provider = OpenAIProvider(config)
        assert provider.config.api_key == "test-key"

    def test_generate_success(self, config):
        """测试成功生成文本"""
        with patch("openai.OpenAI") as mock_client:
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "测试生成结果"
            mock_client.return_value.chat.completions.create.return_value = mock_response

            provider = OpenAIProvider(config)
            result = provider.generate("你好")
            assert result == "测试生成结果"
            mock_client.return_value.chat.completions.create.assert_called_once()

    def test_embed_success(self, config):
        """测试成功生成嵌入"""
        with patch("openai.OpenAI") as mock_client:
            mock_response = MagicMock()
            mock_response.data[0].embedding = [0.1, 0.2, 0.3]
            mock_client.return_value.embeddings.create.return_value = mock_response

            provider = OpenAIProvider(config)
            result = provider.embed("测试文本")
            assert result == [0.1, 0.2, 0.3]

    def test_generate_with_system_message(self, config):
        """测试带系统消息的生成"""
        with patch("openai.OpenAI") as mock_client:
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "回复"
            mock_client.return_value.chat.completions.create.return_value = mock_response

            provider = OpenAIProvider(config)
            result = provider.generate("用户问题", system="你是一个助手")
            call_args = mock_client.return_value.chat.completions.create.call_args
            messages = call_args.kwargs["messages"]
            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert messages[1]["role"] == "user"

    def test_batch_generate(self, config):
        """测试批量生成"""
        with patch("openai.OpenAI") as mock_client:
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "回复"
            mock_client.return_value.chat.completions.create.return_value = mock_response

            provider = OpenAIProvider(config)
            prompts = ["问题1", "问题2", "问题3"]
            results = provider.batch_generate(prompts)
            assert len(results) == 3
            assert mock_client.return_value.chat.completions.create.call_count == 3

    def test_generate_retry_on_timeout(self, config):
        """测试超时重试"""
        import openai
        with patch("openai.OpenAI") as mock_client:
            mock_client.return_value.chat.completions.create.side_effect = [
                openai.APITimeoutError("Timeout"),
                openai.APITimeoutError("Timeout"),
                MagicMock(choices=[MagicMock(message=MagicMock(content="成功"))])
            ]

            provider = OpenAIProvider(config)
            result = provider.generate("测试")
            assert result == "成功"
            assert mock_client.return_value.chat.completions.create.call_count == 3


class TestAnthropicProvider:
    """Anthropic Provider 测试"""

    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return ProviderConfig(
            api_key="test-key",
            model="claude-sonnet-4-20250514",
            timeout=30,
            max_retries=3
        )

    def test_provider_initialization(self, config):
        """测试Provider初始化"""
        provider = AnthropicProvider(config)
        assert provider.config == config
        assert provider.get_provider_name() == "anthropic"

    def test_generate_success(self, config):
        """测试成功生成文本"""
        with patch("anthropic.Anthropic") as mock_client:
            mock_response = MagicMock()
            mock_response.content[0].text = "Claude的回复"
            mock_client.return_value.messages.create.return_value = mock_response

            provider = AnthropicProvider(config)
            result = provider.generate("你好")
            assert result == "Claude的回复"

    def test_embed_not_supported(self, config):
        """测试嵌入不支持"""
        provider = AnthropicProvider(config)
        with pytest.raises(AIProviderError) as exc_info:
            provider.embed("测试文本")
        assert "does not support embedding" in str(exc_info.value)

    def test_batch_generate(self, config):
        """测试批量生成"""
        with patch("anthropic.Anthropic") as mock_client:
            mock_response = MagicMock()
            mock_response.content[0].text = "回复"
            mock_client.return_value.messages.create.return_value = mock_response

            provider = AnthropicProvider(config)
            prompts = ["问题1", "问题2"]
            results = provider.batch_generate(prompts)
            assert len(results) == 2
            assert mock_client.return_value.messages.create.call_count == 2


class TestAIProviderAbstract:
    """AIProvider抽象类测试"""

    def test_cannot_instantiate_abstract_class(self):
        """测试不能直接实例化抽象类"""
        config = ProviderConfig(api_key="test")

        with pytest.raises(TypeError) as exc_info:
            AIProvider(config)
        assert "abstract" in str(exc_info.value).lower() or "can't instantiate" in str(exc_info.value).lower()

    def test_provider_must_implement_generate(self):
        """测试子类必须实现generate"""
        config = ProviderConfig(api_key="test")

        class IncompleteProvider(AIProvider):
            def embed(self, text: str) -> list[float]:
                return []

            def batch_generate(self, prompts: list[str], **kwargs) -> list[str]:
                return []

        with pytest.raises(TypeError):
            IncompleteProvider(config)
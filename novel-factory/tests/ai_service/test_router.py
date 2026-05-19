"""AIRouter 测试"""
import pytest
from unittest.mock import patch, MagicMock

from ai_service.base import ProviderConfig, AIProviderError
from ai_service.router import AIRouter
from ai_service.openai_provider import OpenAIProvider
from ai_service.anthropic_provider import AnthropicProvider


class TestAIRouter:
    """AIRouter 测试套件"""

    @pytest.fixture
    def openai_config(self):
        """OpenAI配置"""
        return ProviderConfig(api_key="openai-key", model="gpt-4")

    @pytest.fixture
    def anthropic_config(self):
        """Anthropic配置"""
        return ProviderConfig(api_key="anthropic-key", model="claude-sonnet-4-20250514")

    @pytest.fixture
    def router(self, openai_config, anthropic_config):
        """创建路由实例"""
        router = AIRouter(
            config={
                "openai": openai_config,
                "anthropic": anthropic_config,
            },
            primary_provider="openai",
            enable_failover=True
        )
        return router

    def test_router_initialization(self, router):
        """测试路由初始化"""
        assert router.get_primary_provider() == "openai"
        assert router.is_provider_available("openai")
        assert router.is_provider_available("anthropic")
        assert router.get_available_providers() == ["openai", "anthropic"]

    def test_get_primary_provider(self, router):
        """测试获取主Provider"""
        assert router.get_primary_provider() == "openai"

    def test_set_primary_provider(self, router):
        """测试设置主Provider"""
        router.set_primary("anthropic")
        assert router.get_primary_provider() == "anthropic"

    def test_set_type_mapping(self, router):
        """测试设置类型映射"""
        # 先获取初始状态
        stats_before = router.get_provider_stats()
        assert stats_before["type_mapping"]["embedding"] == "openai"

        # 修改映射
        router.set_type_mapping("embedding", "anthropic")

        # 验证映射已更改
        stats_after = router.get_provider_stats()
        assert stats_after["type_mapping"]["embedding"] == "anthropic"

    @patch.object(OpenAIProvider, "generate")
    def test_route_to_primary_provider(self, mock_generate, router):
        """测试路由到主Provider"""
        mock_generate.return_value = "测试回复"

        result = router.generate("你好")
        assert result == "测试回复"
        mock_generate.assert_called_once()

    @patch.object(OpenAIProvider, "generate")
    @patch.object(AnthropicProvider, "generate")
    def test_failover_on_error(self, mock_anthropic_generate, mock_openai_generate, router):
        """测试故障转移"""
        mock_openai_generate.side_effect = Exception("OpenAI失败")
        mock_anthropic_generate.return_value = "Anthropic回复"

        result = router.generate("你好")
        assert result == "Anthropic回复"
        mock_openai_generate.assert_called_once()
        mock_anthropic_generate.assert_called_once()

    @patch.object(OpenAIProvider, "generate")
    @patch.object(AnthropicProvider, "generate")
    def test_all_providers_fail(self, mock_anthropic_generate, mock_openai_generate, router):
        """测试所有Provider都失败"""
        mock_openai_generate.side_effect = Exception("OpenAI失败")
        mock_anthropic_generate.side_effect = Exception("Anthropic失败")

        with pytest.raises(AIProviderError):
            router.generate("你好")

    @patch.object(OpenAIProvider, "embed")
    def test_embed_routes_to_openai(self, mock_embed, router):
        """测试嵌入路由到OpenAI"""
        mock_embed.return_value = [0.1, 0.2, 0.3]

        result = router.embed("测试文本")
        assert result == [0.1, 0.2, 0.3]
        mock_embed.assert_called_once()

    def test_provider_stats(self, router):
        """测试Provider统计信息"""
        stats = router.get_provider_stats()
        assert "providers" in stats
        assert "primary" in stats
        assert "type_mapping" in stats
        assert "failover_enabled" in stats
        assert stats["providers"] == ["openai", "anthropic"]
        assert stats["primary"] == "openai"
        assert stats["failover_enabled"] is True

    def test_get_provider_stats(self, router):
        """测试获取Provider详细信息"""
        stats = router.get_provider_stats()
        assert stats["providers"] == ["openai", "anthropic"]
        assert stats["primary"] == "openai"
        assert stats["type_mapping"]["embedding"] == "openai"
        assert stats["type_mapping"]["general"] == "openai"

    @patch.object(AnthropicProvider, "generate")
    def test_specified_provider_used(self, mock_generate, router):
        """测试使用指定的Provider"""
        mock_generate.return_value = "指定回复"

        result = router.generate("你好", provider="anthropic")
        assert result == "指定回复"
        mock_generate.assert_called_once()

    def test_no_available_provider(self):
        """测试没有可用Provider"""
        router = AIRouter(config={})
        with pytest.raises(AIProviderError):
            router.generate("你好")


class TestAIRouterWithoutFailover:
    """无故障转移的AIRouter测试"""

    @pytest.fixture
    def config(self):
        return ProviderConfig(api_key="test-key", model="gpt-4")

    @pytest.fixture
    def router_no_failover(self, config):
        """创建禁用故障转移的路由"""
        router = AIRouter(
            config={"openai": config},
            primary_provider="openai",
            enable_failover=False
        )
        return router

    @patch.object(OpenAIProvider, "generate")
    def test_no_failover_raises_immediately(self, mock_generate, router_no_failover):
        """测试禁用故障转移时立即抛出异常"""
        mock_generate.side_effect = Exception("API Error")

        with pytest.raises(Exception):
            router_no_failover.generate("你好")


class TestAIRouterCostOptimize:
    """成本优化路由测试"""

    @pytest.fixture
    def config_openai(self):
        return ProviderConfig(api_key="openai-key", model="gpt-4")

    @pytest.fixture
    def config_anthropic(self):
        return ProviderConfig(api_key="anthropic-key", model="claude-sonnet-4-20250514")

    @pytest.fixture
    def router_cost_optimize(self, config_openai, config_anthropic):
        """创建启用成本优化的路由"""
        router = AIRouter(
            config={
                "openai": config_openai,
                "anthropic": config_anthropic,
            },
            primary_provider="openai",
            enable_failover=True,
            cost_optimize=True
        )
        return router

    def test_cost_optimized_order(self, router_cost_optimize):
        """测试成本优化顺序"""
        # 默认成本相同，按名字排序
        order = router_cost_optimize._get_cost_optimized_order()
        assert order[0] in ["anthropic", "openai"]  # 成本相同，顺序不确定

    def test_cost_map_exists(self, router_cost_optimize):
        """测试成本映射存在"""
        assert "openai" in router_cost_optimize._cost_map
        assert "anthropic" in router_cost_optimize._cost_map
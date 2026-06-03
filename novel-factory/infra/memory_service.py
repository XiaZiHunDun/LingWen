"""记忆服务单例 - 全局记忆系统访问点

提供全局唯一的 MemoryGateway 实例，确保记忆系统在整个应用生命周期中只有一个实例。
当 Qdrant 不可用或配置缺失时，返回一个安全的 NoOp 降级网关，避免系统崩溃。

使用方式：
    from infra.memory_service import get_memory_gateway

    gateway = get_memory_gateway()
    context = gateway.auto_push_context(chapter_num=5)
"""
import logging
from typing import Any, Dict, List, Optional

from infra.logging_config import logger
from infra.memory_system.config import load_yaml
from infra.memory_system.embeddings.batch_embed import BatchEmbedder
from infra.memory_system.gateway.memory_gateway import MemoryGateway
from infra.memory_system.state.character_tracker import CharacterTracker
from infra.memory_system.state.fact_base import FactBase
from infra.memory_system.state.plot_thread_tracker import PlotThreadTracker
from infra.memory_system.state.timeline_manager import TimelineManager
from infra.memory_system.vector.embedder import Embedder
from infra.memory_system.vector.qdrant_client import QdrantClientWrapper

# 全局单例实例
_memory_gateway: Optional[MemoryGateway] = None
_initialization_error: Optional[str] = None


class NoOpMemoryGateway:
    """NoOp 降级网关

    当 Qdrant 不可用或配置缺失时使用此降级网关。
    所有方法均返回安全默认值，不会抛出异常。
    """

    def __init__(self, error_message: str):
        self._error_message = error_message
        logger.warning(f"MemoryGateway 降级为 NoOp 模式: {error_message}")

    def auto_push_context(self, chapter_num: int) -> Dict[str, Any]:
        """返回空上下文"""
        return {
            "chapter": chapter_num,
            "character_states": {},
            "pending_foreshadows": {},
            "recent_events": [],
            "related_segments": [],
        }

    def query(
        self,
        query: str,
        scope: Optional[str] = "all",
        filters: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """返回空结果"""
        return []

    def update_character_state(self, character: str, state: Dict[str, Any]) -> None:
        """静默忽略"""
        pass

    def get_character_state(self, character: str) -> Optional[Dict[str, Any]]:
        """返回 None"""
        return None

    def get_all_characters(self) -> Dict[str, Dict[str, Any]]:
        """返回空字典"""
        return {}

    def plant_foreshadow(self, fp_id: str, metadata: Dict[str, Any]) -> None:
        """静默忽略"""
        pass

    def update_foreshadow(
        self,
        fp_id: str,
        event_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        chapter: Optional[int] = None,
    ) -> None:
        """静默忽略"""
        pass

    def get_pending_foreshadows(self) -> Dict[str, Dict[str, Any]]:
        """返回空字典"""
        return {}

    def check_consistency(
        self, chapter_content: str, chapter: Optional[int] = None
    ) -> Dict[str, Any]:
        """返回通过结果"""
        return {
            "is_consistent": True,
            "consistency_score": 1.0,
            "issues": [],
        }

    def get_relationship_network(
        self, character: str, depth: int = 1
    ) -> List[Dict[str, Any]]:
        """返回空列表"""
        return []

    @property
    def is_noop(self) -> bool:
        """标记为 NoOp 模式"""
        return True


def _load_default_config() -> Dict[str, Any]:
    """加载默认配置

    从 memory_config.yaml 加载配置，如果加载失败则使用内联默认值。

    Returns:
        配置字典
    """
    try:
        config = load_yaml("config/memory_config.yaml")
        return config
    except FileNotFoundError as e:
        logger.warning(f"memory_config.yaml 未找到，使用内联默认配置: {e}")
        # 内联默认配置
        return {
            "qdrant": {
                "host": "localhost",
                "port": 6333,
                "grpc_port": 6334,
            },
            "embedding": {
                "model": "text-embedding-3-small",
                "dimension": 1536,
            },
            "storage": {
                "state_file": "state/state_tracker.json",
                "plot_threads_file": "state/plot_threads.yaml",
                "timeline_file": "state/timeline.json",
            },
            "retrieval": {
                "default_top_k": 5,
                "hybrid_alpha": 0.7,
            },
        }
    except Exception as e:
        logger.error(f"加载 memory_config.yaml 失败: {e}", exc_info=True)
        return {
            "qdrant": {
                "host": "localhost",
                "port": 6333,
                "grpc_port": 6334,
            },
            "embedding": {
                "model": "text-embedding-3-small",
                "dimension": 1536,
            },
            "storage": {
                "state_file": "state/state_tracker.json",
                "plot_threads_file": "state/plot_threads.yaml",
                "timeline_file": "state/timeline.json",
            },
            "retrieval": {
                "default_top_k": 5,
                "hybrid_alpha": 0.7,
            },
        }


def _check_qdrant_availability(qdrant_wrapper: QdrantClientWrapper) -> bool:
    """检查 Qdrant 是否可用

    Args:
        qdrant_wrapper: QdrantClientWrapper 实例

    Returns:
        Qdrant 是否可用
    """
    try:
        # 尝试获取集合列表来验证连接
        collections = qdrant_wrapper.client.get_collections()
        return collections is not None
    except (ConnectionError, TimeoutError, OSError) as e:
        logger.warning(f"Qdrant 连接检查失败: {e}")
        return False
    except Exception as e:
        logger.error(f"Qdrant 连接检查时发生未预期错误: {e}", exc_info=True)
        return False


def _create_memory_gateway() -> MemoryGateway:
    """创建 MemoryGateway 实例

    初始化所有组件并创建 MemoryGateway。
    如果任何步骤失败，抛出异常由调用者处理。

    Returns:
        MemoryGateway 实例

    Raises:
        RuntimeError: 初始化失败
    """
    # 1. 加载配置
    config = _load_default_config()

    # 2. 初始化 QdrantClientWrapper
    try:
        qdrant_wrapper = QdrantClientWrapper()
    except (ConnectionError, TimeoutError, OSError) as e:
        raise RuntimeError(f"Failed to initialize QdrantClientWrapper: {e}") from e
    except Exception as e:
        logger.error(f"初始化 QdrantClientWrapper 时发生未预期错误: {e}", exc_info=True)
        raise RuntimeError(f"Failed to initialize QdrantClientWrapper: {e}") from e

    # 3. 检查 Qdrant 是否可用
    if not _check_qdrant_availability(qdrant_wrapper):
        raise RuntimeError("Qdrant is not available. Please ensure Qdrant server is running.")

    # 4. 初始化 Embedder
    try:
        embedder = Embedder()
    except (ConnectionError, TimeoutError, OSError) as e:
        raise RuntimeError(f"Failed to initialize Embedder: {e}") from e
    except Exception as e:
        logger.error(f"初始化 Embedder 时发生未预期错误: {e}", exc_info=True)
        raise RuntimeError(f"Failed to initialize Embedder: {e}") from e

    # 5. 初始化 BatchEmbedder
    BatchEmbedder(
        qdrant_wrapper=qdrant_wrapper,
        embedder=embedder,
    )

    # 6. 初始化状态管理组件（使用 storage 配置）
    storage_config = config.get("storage", {})

    # 为 StateManager 构建配置格式
    state_config = {"storage": storage_config}

    character_tracker = CharacterTracker(state_config)
    plot_thread_tracker = PlotThreadTracker(state_config)
    timeline_manager = TimelineManager(state_config)
    fact_base = FactBase(state_config)

    # 7. 创建 MemoryGateway
    gateway = MemoryGateway(
        qdrant_wrapper=qdrant_wrapper,
        embedder=embedder,
        character_tracker=character_tracker,
        plot_thread_tracker=plot_thread_tracker,
        timeline_manager=timeline_manager,
        fact_base=fact_base,
    )

    return gateway


def get_memory_gateway() -> MemoryGateway:
    """获取全局 MemoryGateway 单例

    首次调用时初始化 MemoryGateway，之后返回同一实例。
    如果初始化失败（Qdrant 不可用或配置缺失），返回一个 NoOpMemoryGateway 降级实例。

    Returns:
        MemoryGateway 实例（正常模式或 NoOp 降级模式）
    """
    global _memory_gateway, _initialization_error

    if _memory_gateway is not None:
        return _memory_gateway

    # 首次初始化
    try:
        _memory_gateway = _create_memory_gateway()
        logger.info("MemoryGateway 初始化成功")
    except (ConnectionError, TimeoutError, OSError, RuntimeError) as e:
        error_msg = str(e)
        _initialization_error = error_msg
        logger.warning(f"MemoryGateway 初始化失败（预期异常），使用 NoOp 降级模式: {error_msg}")
        _memory_gateway = NoOpMemoryGateway(error_msg)
    except Exception as e:
        error_msg = str(e)
        _initialization_error = error_msg
        logger.error(f"MemoryGateway 初始化时发生未预期错误: {e}", exc_info=True)
        _memory_gateway = NoOpMemoryGateway(error_msg)

    return _memory_gateway


def is_memory_gateway_available() -> bool:
    """检查记忆网关是否可用（未降级）

    Returns:
        True 如果是正常模式，False 如果是 NoOp 降级模式
    """
    gateway = get_memory_gateway()
    return not getattr(gateway, "is_noop", False)


def get_initialization_error() -> Optional[str]:
    """获取初始化错误信息

    如果 MemoryGateway 初始化失败且正在使用 NoOp 模式，返回错误信息。

    Returns:
        错误信息，如果无错误则返回 None
    """
    return _initialization_error

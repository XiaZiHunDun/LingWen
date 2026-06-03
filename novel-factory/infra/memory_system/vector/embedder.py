"""嵌入模型管理

管理文本嵌入模型，提供 embed_texts() 方法生成向量。
支持批量嵌入，从 memory_config.yaml 读取配置。
"""
from typing import Optional

from openai import OpenAI

from infra.memory_system.config import load_yaml


class Embedder:
    """嵌入模型管理类

    管理文本嵌入模型，提供向量生成接口。
    配置从 memory_config.yaml 的 embedding 部分读取。
    """

    MEMORY_CONFIG_PATH = "config/memory_config.yaml"

    def __init__(self):
        """初始化嵌入模型

        从 memory_config.yaml 加载 embedding.model 和 embedding.dimension 配置。

        Raises:
            RuntimeError: 配置文件不存在或解析失败
        """
        try:
            config = load_yaml(self.MEMORY_CONFIG_PATH)
            embedding_config = config["embedding"]

            self.model = embedding_config["model"]
            self.dimension = embedding_config["dimension"]

            self._client = OpenAI()

        except KeyError as e:
            raise RuntimeError(f"Missing required config key in {self.MEMORY_CONFIG_PATH}: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Embedder: {e}")

    @property
    def client(self):
        """获取 OpenAI 客户端实例"""
        return self._client

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """将文本列表转换为嵌入向量列表

        Args:
            texts: 文本列表

        Returns:
            嵌入向量列表，每个向量为 dimension 维浮点数列表

        Raises:
            Exception: API 调用失败时抛出异常
        """
        if not texts:
            return []

        response = self._client.embeddings.create(
            input=texts,
            model=self.model,
        )

        # 按 index 排序确保顺序一致
        embeddings = sorted(response.data, key=lambda x: x.index)
        return [embedding.embedding for embedding in embeddings]

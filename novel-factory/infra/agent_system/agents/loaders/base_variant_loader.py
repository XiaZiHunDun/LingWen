# novel-factory/infra/agent_system/agents/loaders/base_variant_loader.py
"""
BaseVariantLoader - 变体配置加载器基类

提供三个角色池（writer/auditor/polisher）的共享变体加载逻辑：
- YAML配置文件加载和缓存
- 变体ID规范化
- 单例模式实现

Usage:
    from infra.agent_system.agents.loaders.base_variant_loader import BaseVariantLoader

    class AuditorVariantLoader(BaseVariantLoader):
        def __init__(self):
            super().__init__(
                variants_dir=Path(__file__).parent / "auditor" / "variants",
                id_prefix="AUD",
                id_mapping={...}
            )
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional, List, Union, Callable
import yaml
import re


class BaseVariantLoader(ABC):
    """变体配置加载器基类

    提供通用的变体加载、缓存和查询功能。
    子类需要实现特定的方法来定制行为。
    """

    _instance: Optional["BaseVariantLoader"] = None

    def __init__(
        self,
        variants_dir: Path,
        id_prefix: str = "",
        id_mapping: Optional[Dict[str, str]] = None,
        numeric_mapping: Optional[Dict[int, str]] = None,
        aliases: Optional[Dict[str, str]] = None,
    ):
        """初始化变体加载器

        Args:
            variants_dir: 变体配置目录路径
            id_prefix: ID前缀（如 "variant_"）
            id_mapping: ID到文件的映射 dict
            numeric_mapping: 数字到ID的映射 dict
            aliases: 别名到标准ID的映射 dict
        """
        self._variants_dir = variants_dir
        self._id_prefix = id_prefix
        self._id_mapping = id_mapping or {}
        self._numeric_mapping = numeric_mapping or {}
        self._aliases = aliases or {}
        self._cache: Dict[str, Dict] = {}
        self._loaded = False

    @property
    def variants_dir(self) -> Path:
        return self._variants_dir

    def _load_all_variants(self) -> None:
        """加载所有变体配置"""
        if not self._variants_dir.exists():
            return

        for yaml_file in self._variants_dir.glob(f"{self._id_prefix}*.yaml"):
            variant_id = self._extract_variant_id(yaml_file.stem)
            if variant_id:
                self._cache[variant_id.upper()] = self._load_yaml(yaml_file)

        self._loaded = True

    def _extract_variant_id(self, stem: str) -> str:
        """从文件名提取变体ID

        Args:
            stem: 文件名（不含扩展名），如 "variant_a"

        Returns:
            标准化后的ID，如 "A"
        """
        # 默认实现：去掉前缀，取剩余部分并转为大写
        if self._id_prefix and stem.startswith(self._id_prefix):
            stem = stem[len(self._id_prefix):]
        return stem.upper()

    def _load_yaml(self, path: Path) -> Dict:
        """加载单个YAML文件

        Args:
            path: YAML文件路径

        Returns:
            配置字典
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data or {}
        except Exception as e:
            print(f"[{self.__class__.__name__}] Failed to load {path}: {e}")
            return {}

    def _normalize_id(self, variant_id: Union[str, int]) -> str:
        """标准化变体ID

        Args:
            variant_id: 原始ID（支持多种格式）

        Returns:
            标准化后的ID（如 "A"）
        """
        # 数字处理
        if isinstance(variant_id, int):
            mapped = self._numeric_mapping.get(variant_id)
            if mapped:
                return mapped.upper()
            # 数字超出范围时尝试直接作为索引
            return chr(ord('A') + variant_id - 1)

        # 字符串处理
        vid = str(variant_id).strip().lower()

        # 检查别名
        if vid in self._aliases:
            return self._aliases[vid].upper()

        # 检查是否已经是标准ID
        if vid.upper() in self._id_mapping.values():
            return vid.upper()

        # 去除常见前缀
        for prefix in [f"{self._id_prefix}", "_"]:
            if vid.startswith(prefix):
                vid = vid[len(prefix):]
                if vid.upper() in self._id_mapping.values():
                    return vid.upper()

        # 检查数字字符串
        if vid.isdigit():
            mapped = self._numeric_mapping.get(int(vid))
            if mapped:
                return mapped.upper()

        # 中文支持（如"作家A" -> "A"）
        if len(vid) == 2 and vid[0] in '作家审核润色':
            return vid[1].upper()

        return vid.upper()

    def get_variant(self, variant_id: Union[str, int]) -> Optional[Dict]:
        """获取指定变体配置

        Args:
            variant_id: 变体ID（支持多种格式）

        Returns:
            变体配置字典，如果不存在返回None
        """
        if not self._loaded:
            self._load_all_variants()

        normalized = self._normalize_id(variant_id)
        return self._cache.get(normalized)

    def get_config(self, variant_id: Union[str, int]) -> Optional[Dict]:
        """获取配置（get_variant的别名）"""
        return self.get_variant(variant_id)

    def list_variants(self) -> List[str]:
        """列出所有可用变体

        Returns:
            变体ID列表
        """
        if not self._loaded:
            self._load_all_variants()
        return sorted(self._cache.keys())

    def get_all_variants(self) -> Dict[str, Dict]:
        """获取所有变体配置

        Returns:
            {变体ID: 配置字典}
        """
        if not self._loaded:
            self._load_all_variants()
        return self._cache.copy()

    def reload(self) -> None:
        """重新加载配置"""
        self._cache = {}
        self._loaded = False
        self._load_all_variants()

    @classmethod
    def get_instance(cls) -> "BaseVariantLoader":
        """获取单例实例（子类需要重写）

        Returns:
            单例实例
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


class SimpleVariantLoader(BaseVariantLoader):
    """简化版变体加载器

    用于不需要复杂ID映射的场景。
    直接使用文件名作为变体ID。
    """

    def _extract_variant_id(self, stem: str) -> str:
        """从文件名提取变体ID"""
        if self._id_prefix and stem.startswith(self._id_prefix):
            stem = stem[len(self._id_prefix):]
        return stem.upper()


# 工厂函数用于创建标准变体加载器
def create_variant_loader(
    loader_type: str,
    base_dir: Optional[Path] = None
) -> BaseVariantLoader:
    """创建变体加载器

    Args:
        loader_type: 加载器类型 ("writer", "auditor", "polisher")
        base_dir: 基础目录，默认为 agents 目录

    Returns:
        对应类型的变体加载器实例
    """
    if base_dir is None:
        base_dir = Path(__file__).parent

    if loader_type == "writer":
        # Writer使用模块函数模式，保持兼容性
        # 这里返回None，让调用者使用原有的模块函数
        return None

    elif loader_type == "auditor":
        from ..auditor.variant_loader import VariantLoader
        return VariantLoader()

    elif loader_type == "polisher":
        from ..polisher.variant_loader import VariantLoader
        return VariantLoader()

    else:
        raise ValueError(f"Unknown loader type: {loader_type}")
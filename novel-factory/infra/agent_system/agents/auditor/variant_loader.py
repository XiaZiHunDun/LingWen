# novel-factory/infra/agent_system/agents/auditor/variant_loader.py
"""
Auditor Variant Loader
审核员A-J变体配置加载器

与 writer-dept variant_loader 模式一致：
- 扫描 variants/ 目录下的 YAML 配置
- 按 variant_id 缓存配置
- 支持动态切换审核员角色
"""

import yaml
import re
from pathlib import Path
from typing import Dict, Optional


class VariantLoader:
    """审核员变体配置加载器

    负责加载和管理审核员A-J的YAML配置文件，
    提供配置查询和动态切换能力。
    """

    _instance: Optional["VariantLoader"] = None
    _cache: Dict[str, Dict] = {}
    _loaded: bool = False

    def __new__(cls) -> "VariantLoader":
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化加载器"""
        if not self._loaded:
            self._variants_dir = Path(__file__).parent / "variants"
            self._load_all_variants()
            VariantLoader._loaded = True

    def _load_all_variants(self) -> None:
        """加载所有变体配置"""
        if not self._variants_dir.exists():
            return

        for yaml_file in self._variants_dir.glob("variant_*.yaml"):
            variant_id = yaml_file.stem.replace("variant_", "").upper()
            if variant_id:
                self._cache[variant_id] = self._load_yaml(yaml_file)

    def _load_yaml(self, path: Path) -> Dict:
        """加载单个YAML文件"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data or {}
        except Exception as e:
            print(f"[VariantLoader] Failed to load {path}: {e}")
            return {}

    def get_variant(self, reviewer_id: str) -> Optional[Dict]:
        """获取指定审核员配置

        Args:
            reviewer_id: 审核员ID (A-J 或 a-j)

        Returns:
            审核员配置字典，如果不存在返回None
        """
        key = reviewer_id.upper()
        return self._cache.get(key)

    def get_weight(self, reviewer_id: str, dimension: str) -> float:
        """获取指定审核员在指定维度的权重

        Args:
            reviewer_id: 审核员ID (A-J 或 a-j)
            dimension: 维度名称 (S1-S8)

        Returns:
            权重值，默认为0.125
        """
        variant = self.get_variant(reviewer_id)
        if not variant:
            return 0.125

        weight_key = f"{dimension.lower()}_weight"
        return variant.get(weight_key, 0.125)

    def get_weights(self, reviewer_id: str) -> Dict[str, float]:
        """获取指定审核员的完整权重配置

        Args:
            reviewer_id: 审核员ID (A-J 或 a-j)

        Returns:
            {S1: 0.x, S2: 0.x, ...} 权重字典
        """
        variant = self.get_variant(reviewer_id)
        if not variant:
            # 默认均衡权重
            return {f"S{i}": 0.125 for i in range(1, 9)}

        dimensions = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"]
        weights = {}
        for dim in dimensions:
            weight_key = f"{dim.lower()}_weight"
            weights[dim] = variant.get(weight_key, 0.125)
        return weights

    def get_specialty_dimensions(self, reviewer_id: str) -> list:
        """获取审核员专长维度

        Args:
            reviewer_id: 审核员ID (A-J 或 a-j)

        Returns:
            专长维度列表，如 ["S1", "S8"]
        """
        variant = self.get_variant(reviewer_id)
        if not variant:
            return []
        return variant.get("specialty_dimensions", [])

    def get_audit_style(self, reviewer_id: str) -> Dict:
        """获取审核员审核风格

        Args:
            reviewer_id: 审核员ID (A-J 或 a-j)

        Returns:
            审核风格配置 {strictness, focus, verbosity}
        """
        variant = self.get_variant(reviewer_id)
        if not variant:
            return {"strictness": "moderate", "focus": "macro", "verbosity": "concise"}
        return variant.get("audit_style", {})

    def get_prompt_enhancements(self, reviewer_id: str) -> list:
        """获取审核员提示词增强配置

        Args:
            reviewer_id: 审核员ID (A-J 或 a-j)

        Returns:
            提示词增强列表
        """
        variant = self.get_variant(reviewer_id)
        if not variant:
            return []
        return variant.get("prompt_enhancements", [])

    def get_expertise_types(self, reviewer_id: str) -> list:
        """获取审核员擅长类型

        Args:
            reviewer_id: 审核员ID (A-J 或 a-j)

        Returns:
            擅长类型列表
        """
        variant = self.get_variant(reviewer_id)
        if not variant:
            return []
        return variant.get("expertise_types", [])

    def build_weighted_prompt(
        self,
        reviewer_id: str,
        base_prompt: str,
        content: str,
        characters: list,
        context: dict
    ) -> str:
        """构建加权审核提示

        根据审核员权重配置增强提示词。

        Args:
            reviewer_id: 审核员ID
            base_prompt: 基础提示词
            content: 章节内容
            characters: 角色列表
            context: 审核上下文

        Returns:
            增强后的提示词
        """
        weights = self.get_weights(reviewer_id)
        specialties = self.get_specialty_dimensions(reviewer_id)
        enhancements = self.get_prompt_enhancements(reviewer_id)
        style = self.get_audit_style(reviewer_id)

        # 按权重排序维度
        sorted_dims = sorted(weights.items(), key=lambda x: x[1], reverse=True)

        # 构建增强指令
        enhancement_parts = []
        if specialties:
            dim_str = ", ".join(specialties)
            enhancement_parts.append(f"【专长维度】：{dim_str}，需重点审核")
        if enhancements:
            enhancement_parts.extend([f"• {e}" for e in enhancements[:3]])

        # 加入风格说明
        style_note = f"审核风格：{style.get('strictness', 'moderate')}/{style.get('focus', 'macro')}"

        # 构建完整提示
        weight_info = "\n".join([f"- {dim}: 权重{weight:.1%}" for dim, weight in sorted_dims])

        full_prompt = f"""{base_prompt}

## 审核员{reviewer_id.upper()}配置
{chr(10).join(enhancement_parts)}

{style_note}

## S1-S8权重配置
{weight_info}
"""
        return full_prompt

    def list_variants(self) -> list:
        """列出所有可用审核员

        Returns:
            审核员ID列表
        """
        return sorted(self._cache.keys())

    def get_all_variants(self) -> Dict[str, Dict]:
        """获取所有变体配置

        Returns:
            {审核员ID: 配置字典}
        """
        return self._cache.copy()


# 全局实例
_loader = None

def get_variant_loader() -> VariantLoader:
    """获取变体加载器单例

    Returns:
        VariantLoader实例
    """
    global _loader
    if _loader is None:
        _loader = VariantLoader()
    return _loader
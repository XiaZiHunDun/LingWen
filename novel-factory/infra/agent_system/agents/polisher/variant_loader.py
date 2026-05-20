# novel-factory/infra/agent_system/agents/polisher/variant_loader.py
"""
Polisher Variant Loader
润色优化师A-T变体配置加载器

与 auditor/writer variant_loader 模式一致：
- 扫描 variants/ 目录下的 YAML 配置
- 按 variant_id 缓存配置
- 支持动态切换润色师角色
"""

import yaml
from pathlib import Path
from typing import Dict, Optional, List


class VariantLoader:
    """润色优化师变体配置加载器

    负责加载和管理润色优化师A-T的YAML配置文件，
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

    def get_variant(self, polisher_id: str) -> Optional[Dict]:
        """获取指定润色师配置

        Args:
            polisher_id: 润色师ID (A-T 或 a-t)

        Returns:
            润色师配置字典，如果不存在返回None
        """
        key = polisher_id.upper()
        return self._cache.get(key)

    def get_style(self, polisher_id: str) -> Dict:
        """获取润色师风格配置

        Args:
            polisher_id: 润色师ID (A-T 或 a-t)

        Returns:
            风格配置 {tone, edit_level, focus_areas}
        """
        variant = self.get_variant(polisher_id)
        if not variant:
            return {"tone": "neutral", "edit_level": "medium", "focus_areas": ["可读性"]}
        return variant.get("style", {})

    def get_edit_level(self, polisher_id: str) -> str:
        """获取润色师编辑深度

        Args:
            polisher_id: 润色师ID

        Returns:
            edit_level: light / medium / heavy
        """
        style = self.get_style(polisher_id)
        return style.get("edit_level", "medium")

    def get_specialty_areas(self, polisher_id: str) -> List[str]:
        """获取润色师专长领域

        Args:
            polisher_id: 润色师ID

        Returns:
            专长领域列表
        """
        variant = self.get_variant(polisher_id)
        if not variant:
            return []
        return variant.get("specialty_areas", [])

    def get_focus_areas(self, polisher_id: str) -> List[str]:
        """获取润色师审核重点

        Args:
            polisher_id: 润色师ID

        Returns:
            审核重点列表
        """
        variant = self.get_variant(polisher_id)
        if not variant:
            return ["可读性", "情感共鸣"]
        # 兼容不同的字段名
        focus = variant.get("focus_areas", [])
        if not focus:
            focus = variant.get("feedback_preference", {}).get("focus_areas", [])
        return focus

    def get_tone(self, polisher_id: str) -> str:
        """获取润色师语气风格

        Args:
            polisher_id: 润色师ID

        Returns:
            语气: 细腻 / 燃系 / 悬疑 / 轻松
        """
        style = self.get_style(polisher_id)
        return style.get("tone", "neutral")

    def build_polish_prompt(
        self,
        polisher_id: str,
        base_prompt: str,
        content: str,
        context: dict
    ) -> str:
        """构建润色提示

        根据润色师配置增强提示词。

        Args:
            polisher_id: 润色师ID
            base_prompt: 基础提示词
            content: 章节内容
            context: 润色上下文

        Returns:
            增强后的提示词
        """
        variant = self.get_variant(polisher_id)
        if not variant:
            return base_prompt

        style = self.get_style(polisher_id)
        focus_areas = self.get_focus_areas(polisher_id)
        specialty_areas = self.get_specialty_areas(polisher_id)

        # 构建增强指令
        enhancement_parts = []
        if focus_areas:
            focus_str = ", ".join(focus_areas[:3])
            enhancement_parts.append(f"【审核重点】：{focus_str}")
        if specialty_areas:
            specialty_str = ", ".join(specialty_areas[:3])
            enhancement_parts.append(f"【专长领域】：{specialty_str}")

        style_note = f"编辑深度：{style.get('edit_level', 'medium')}，语气：{style.get('tone', 'neutral')}"

        # 构建完整提示
        full_prompt = f"""{base_prompt}

## 润色师{polisher_id.upper()}配置
{chr(10).join(enhancement_parts)}

{style_note}
"""
        return full_prompt

    def list_variants(self) -> List[str]:
        """列出所有可用润色师

        Returns:
            润色师ID列表
        """
        return sorted(self._cache.keys())

    def get_all_variants(self) -> Dict[str, Dict]:
        """获取所有变体配置

        Returns:
            {润色师ID: 配置字典}
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
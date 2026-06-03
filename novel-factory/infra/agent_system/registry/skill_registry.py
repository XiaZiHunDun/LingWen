# Skill Registry - Agent Variant Configuration Loader
# 技能注册表 - Agent变体配置加载器
"""
SkillRegistry provides a centralized registry for all agent variants
in the novel factory system.

Usage:
    registry = SkillRegistry()

    # Get default variant for a role
    default = registry.get_default_variant("polisher")

    # Get specific variant config
    config = registry.get_variant("polisher", "reader-a")

    # List all variants for a role
    variants = registry.list_variants("polisher")

    # Query by role_id (e.g., "reader-a", "writer-b", "auditor-c")
    reader_a_config = registry.query_by_role_id("reader-a")
"""

import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class SkillRegistry:
    """Skill Registry - Agent Variant Configuration Loader

    Loads and provides access to agent variant configurations from
    skill_registry.yaml and individual variant YAML files.
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        base_path: Optional[str] = None
    ):
        """Initialize the Skill Registry.

        Args:
            config_path: Path to skill_registry.yaml.
                        Defaults to novel-factory/config/skill_registry.yaml
            base_path: Base path for resolving relative config_file paths.
                        Defaults to novel-factory/
        """
        if config_path is None:
            config_path = self._find_config_path()

        self.config_path = Path(config_path)
        self.base_path = base_path or self._find_base_path()

        self._registry: Dict[str, Any] = {}
        self._variant_configs: Dict[str, Dict[str, Any]] = {}
        self._load_registry()

    def _find_config_path(self) -> Path:
        """Find skill_registry.yaml in standard locations."""
        possible_paths = [
            Path(__file__).parent.parent.parent / "config" / "skill_registry.yaml",
            Path(__file__).parent.parent.parent.parent / "config" / "skill_registry.yaml",
        ]

        for path in possible_paths:
            if path.exists():
                return path

        raise FileNotFoundError(
            f"skill_registry.yaml not found in any of: {possible_paths}"
        )

    def _find_base_path(self) -> Path:
        """Find the novel-factory base path."""
        return self.config_path.parent.parent

    def _load_registry(self) -> None:
        """Load the skill registry from YAML."""
        with open(self.config_path, "r", encoding="utf-8") as f:
            self._registry = yaml.safe_load(f)

    def get_default_variant(self, role: str) -> Optional[str]:
        """Get the default variant ID for a role.

        Args:
            role: Role name (e.g., "polisher", "content_writer", "auditor")

        Returns:
            Default variant ID or None if role not found
        """
        agents = self._registry.get("agents", {})
        role_config = agents.get(role, {})
        return role_config.get("default_variant")

    def get_variant(self, role: str, variant_id: str) -> Optional[Dict[str, Any]]:
        """Get variant configuration for a specific role and variant.

        Args:
            role: Role name (e.g., "polisher", "content_writer", "auditor")
            variant_id: Variant ID (e.g., "reader-a", "writer-b")

        Returns:
            Variant configuration dict or None if not found
        """
        agents = self._registry.get("agents", {})
        role_config = agents.get(role, {})
        variant_details = role_config.get("variant_details", {})

        return variant_details.get(variant_id)

    def list_variants(self, role: str) -> List[str]:
        """List all variant IDs for a role.

        Args:
            role: Role name (e.g., "polisher", "content_writer", "auditor")

        Returns:
            List of variant IDs
        """
        agents = self._registry.get("agents", {})
        role_config = agents.get(role, {})
        return role_config.get("variants", [])

    def query_by_role_id(self, role_id: str) -> Optional[Dict[str, Any]]:
        """Query variant config by role_id (e.g., "reader-a", "writer-b").

        This is a convenience method that auto-detects the role from
        the role_id format.

        Args:
            role_id: Role ID like "reader-a", "writer-b", "auditor-c"

        Returns:
            Variant configuration dict or None if not found
        """
        if "-" not in role_id:
            return None

        role_part, variant_part = role_id.rsplit("-", 1)

        # Map role_id prefixes to role names
        role_map = {
            "reader": "polisher",
            "writer": "content_writer",
            "auditor": "auditor",
        }

        role = role_map.get(role_part)
        if not role:
            # Try treating the whole thing as role ID
            return None

        # Try to find the variant
        variant_id = f"{role_part}-{variant_part}"
        return self.get_variant(role, variant_id)

    def load_variant_yaml(self, variant_id: str) -> Optional[Dict[str, Any]]:
        """Load the full variant YAML config file for a reader variant.

        For polisher variants, this loads the detailed config from
        infra/agent_system/agents/polisher/variants/variant_{letter}.yaml

        Args:
            variant_id: Variant ID like "reader-a"

        Returns:
            Full variant configuration dict or None if not found
        """
        cache_key = f"polisher_{variant_id}"
        if cache_key in self._variant_configs:
            return self._variant_configs[cache_key]

        # Check if it's a polisher variant
        if variant_id.startswith("reader-"):
            letter = variant_id.split("-", 1)[1]
            variant_path = (
                self.base_path
                / "infra"
                / "agent_system"
                / "agents"
                / "polisher"
                / "variants"
                / f"variant_{letter}.yaml"
            )

            if variant_path.exists():
                with open(variant_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    self._variant_configs[cache_key] = config
                    return config

        return None

    def get_variant_score_dimensions(
        self, variant_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Get score dimensions for a specific variant.

        Args:
            variant_id: Variant ID like "reader-a"

        Returns:
            List of score dimension configs or None
        """
        config = self.load_variant_yaml(variant_id)
        if config:
            return config.get("score_dimensions")
        return None

    def get_feedback_preference(
        self, variant_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get feedback preferences for a specific variant.

        Args:
            variant_id: Variant ID like "reader-a"

        Returns:
            Feedback preference config or None
        """
        config = self.load_variant_yaml(variant_id)
        if config:
            return config.get("feedback_preference")
        return None

    def list_all_agents(self) -> Dict[str, Any]:
        """List all agent configurations.

        Returns:
            Dict of all agent configs from registry
        """
        return self._registry.get("agents", {})

    def get_metadata(self) -> Dict[str, Any]:
        """Get registry metadata.

        Returns:
            Metadata dict (version, total_agents, etc.)
        """
        return self._registry.get("metadata", {})

    def __repr__(self) -> str:
        return (
            f"SkillRegistry(registry={self.config_path}, "
            f"agents={len(self._registry.get('agents', {}))})"
        )


# Global singleton instance
_registry_instance: Optional[SkillRegistry] = None
# R2-017: 单例 init + reset 都加锁,防止多线程下重复实例化 / 撕裂
_registry_lock = threading.RLock()


def get_registry() -> SkillRegistry:
    """Get the global SkillRegistry singleton instance.

    R2-017: 双重检查锁,避免并发线程同时进入 None 分支重复创建实例。
    """
    global _registry_instance
    if _registry_instance is None:
        with _registry_lock:
            if _registry_instance is None:
                _registry_instance = SkillRegistry()
    return _registry_instance


def reset_registry() -> None:
    """Reset the global registry instance (for testing).

    R2-017: 加锁,避免与正在 init 的线程产生 race。
    """
    global _registry_instance
    with _registry_lock:
        _registry_instance = None

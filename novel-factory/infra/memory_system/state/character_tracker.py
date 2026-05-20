"""角色状态追踪模块

追踪角色的：
- 当前位置 (current_location)
- 当前形态 (current_form)
- 生死状态 (alive)
- 最后更新章节 (last_updated_chapter)
- 情绪状态 (emotion_state)
- 首次出现章节 (first_appearance_chapter)
"""
from typing import Any, Dict, Optional

from infra.memory_system.state.state_manager import StateManager


class CharacterTracker:
    """角色状态追踪器

    管理所有角色的状态信息，基于 StateManager 提供持久化存储。
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化角色状态追踪器

        Args:
            config: 配置字典，需包含 storage 字段
        """
        self.state_manager = StateManager(config)

    def update_character_state(
        self, character: str, state: Dict[str, Any]
    ) -> None:
        """更新角色状态

        Args:
            character: 角色名称
            state: 状态字典，包含以下字段（均为可选）：
                - current_location: str - 当前位置
                - current_form: str - 当前形态
                - alive: bool - 是否存活
                - last_updated_chapter: int - 最后更新章节
                - emotion_state: str - 情绪状态
        """
        # 加载现有数据
        all_data = self.state_manager.load("state_file")

        # 获取或初始化角色数据
        if "characters" not in all_data:
            all_data["characters"] = {}

        character_data = all_data["characters"].get(character, {})

        # 如果是首次出现，记录首次出现章节
        if character not in all_data["characters"]:
            if "first_appearance_chapter" in state:
                character_data["first_appearance_chapter"] = state["last_updated_chapter"]

        # 更新角色状态（保留已有字段，只更新提供的字段）
        for key, value in state.items():
            character_data[key] = value

        # 保存回状态文件
        all_data["characters"][character] = character_data
        self.state_manager.save("state_file", all_data)

    def get_character_state(self, character: str) -> Optional[Dict[str, Any]]:
        """获取角色状态

        Args:
            character: 角色名称

        Returns:
            角色状态字典，如果角色不存在则返回 None
        """
        all_data = self.state_manager.load("state_file")
        characters = all_data.get("characters", {})
        return characters.get(character)

    def get_all_characters(self) -> Dict[str, Dict[str, Any]]:
        """获取所有角色状态

        Returns:
            所有角色状态字典，键为角色名称，值为角色状态
        """
        all_data = self.state_manager.load("state_file")
        return all_data.get("characters", {})